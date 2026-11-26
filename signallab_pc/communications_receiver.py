"""Receive already filtered I/Q with known, assisted or pilot-based alignment."""

from copy import deepcopy
from dataclasses import asdict, dataclass, replace
import math
import sys

import numpy as np

from .communications_data import clock_from_signal, integer, iq_signal, real
from .execution import ExecutionContext
from .model import Signal
from .operation_provenance import content_digest, verify_inputs
from .resources import ResourceLimitError


_CORRELATION_BLOCK_TERMS = 65_536
_MAX_CORRELATION_TERMS = 16_777_216


@dataclass(frozen=True, slots=True)
class SynchronizationSpec:
    mode: str = 'ideal'
    sample_offset: int | None = None
    phase_rad: float | None = None
    search_first: int = 0
    search_last: int | None = None
    minimum_score: float = 0.7
    minimum_margin: float = 0.01

    def __post_init__(self):
        if self.mode not in ('ideal', 'assisted', 'estimated'):
            raise ValueError('Seleccioná sincronización ideal, asistida o estimada.')
        first = integer(self.search_first, 'El primer índice de búsqueda', minimum=0, maximum=sys.maxsize)
        last = None if self.search_last is None else integer(
            self.search_last, 'El último índice de búsqueda', minimum=first, maximum=sys.maxsize,
        )
        score = real(self.minimum_score, 'La correlación mínima', positive=True, maximum=1)
        margin = real(self.minimum_margin, 'El margen de correlación', minimum=0, maximum=1)
        if self.mode == 'estimated':
            if self.sample_offset is not None or self.phase_rad is not None:
                raise ValueError('La estimación requiere un piloto y un intervalo de búsqueda.')
        else:
            if self.mode == 'assisted' and self.sample_offset is None:
                raise ValueError('Indicá el índice de muestreo para la sincronización asistida.')
            if first != 0 or last is not None:
                raise ValueError('El intervalo de búsqueda corresponde a la estimación con piloto.')
            offset = 0 if self.sample_offset is None else integer(
                self.sample_offset, 'El inicio de los símbolos', minimum=0, maximum=sys.maxsize,
            )
            phase = 0.0 if self.phase_rad is None else math.remainder(real(self.phase_rad, 'La fase'), math.tau)
            object.__setattr__(self, 'sample_offset', offset)
            object.__setattr__(self, 'phase_rad', phase)
        object.__setattr__(self, 'search_first', first)
        object.__setattr__(self, 'search_last', last)
        object.__setattr__(self, 'minimum_score', score)
        object.__setattr__(self, 'minimum_margin', margin)


@dataclass(frozen=True, slots=True)
class Synchronization:
    state: str
    method: str
    sample_offset: int | None = None
    source_index: int | None = None
    phase_rad: float | None = None
    score: float | None = None
    runner_up: float | None = None
    searched_offsets: tuple[int, int] | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True, eq=False)
class ReceiveResult:
    synchronization: Synchronization
    symbols: Signal | None
    applied_sample_gain: float


def _provided_sync(signal, spec, valid_last):
    method = 'known_reference' if spec.mode == 'ideal' else 'supplied_alignment'
    if spec.sample_offset > valid_last:
        return Synchronization('unavailable', method, reason='El registro no contiene todos los símbolos solicitados.')
    return Synchronization(spec.mode, method, spec.sample_offset,
                           int(signal.origin) + spec.sample_offset, spec.phase_rad)


def _normalized_pilot_search(values, pilot, first, last, sps, ctx):
    """Compare each decimated phase using independently scaled windows."""
    pilot_scale = max(float(np.max(np.abs(pilot.real))), float(np.max(np.abs(pilot.imag))))
    if pilot_scale == 0:
        raise ValueError('El piloto debe tener energía positiva.')
    ref_i, ref_q = pilot.real / pilot_scale, pilot.imag / pilot_scale
    energy = float(np.dot(ref_i, ref_i) + np.dot(ref_q, ref_q))
    width = last - first + 1
    scores = np.zeros(width)
    phases = np.zeros(width)
    phase_count = min(width, sps)
    window = pilot.size
    block_windows = max(1, _CORRELATION_BLOCK_TERMS // window)
    scanned = 0
    for phase in range(phase_count):
        start = first + phase
        segment = values[start:last + (window-1)*sps + 1:sps]
        windows = np.lib.stride_tricks.sliding_window_view(segment, window)
        for index in range(0, len(windows), block_windows):
            ctx.checkpoint(10 + 55*scanned//width)
            stop = min(len(windows), index+block_windows)
            block = windows[index:stop]
            scale = np.maximum(np.max(np.abs(block.real), axis=1), np.max(np.abs(block.imag), axis=1))
            scale[scale == 0] = 1
            normalized_i = block.real / scale[:, None]
            normalized_q = block.imag / scale[:, None]
            corr_i = normalized_i @ ref_i + normalized_q @ ref_q
            corr_q = normalized_q @ ref_i - normalized_i @ ref_q
            local_energy = np.einsum('ij,ij->i', normalized_i, normalized_i)
            local_energy += np.einsum('ij,ij->i', normalized_q, normalized_q)
            denominator = np.sqrt(energy * local_energy)
            estimates = np.divide(np.hypot(corr_i, corr_q), denominator, out=np.zeros_like(denominator),
                                  where=denominator > 0)
            target = slice(phase + index*sps, phase + stop*sps, sps)
            scores[target] = np.minimum(estimates, 1.0)
            phases[target] = np.arctan2(corr_q, corr_i)
            scanned += stop - index
    return scores, phases


def _estimate_sync(signal, spec, pilot, valid_last, sps, ctx):
    method = 'pilot_normalized_correlation'
    first = spec.search_first
    last = valid_last if spec.search_last is None else min(valid_last, spec.search_last)
    if last < first:
        return Synchronization('unavailable', method, reason='El registro no alcanza para el intervalo de búsqueda.')
    if pilot is None:
        return Synchronization('unavailable', method, reason='Cargá un piloto conocido para estimar el instante y la fase.')
    scores, phases = _normalized_pilot_search(signal.values, pilot.values, first, last, sps, ctx)
    best = int(np.argmax(scores))
    score = float(scores[best])
    scores[best] = 0
    runner_up = float(scores.max())
    evidence = {'score': score, 'runner_up': runner_up, 'searched_offsets': (first, last)}
    if score < spec.minimum_score:
        return Synchronization('unavailable', method, reason='La correlación con el piloto es insuficiente.', **evidence)
    if scores.size > 1 and (score == runner_up or score - runner_up < spec.minimum_margin):
        return Synchronization('unavailable', method, reason='Hay más de un instante de muestreo compatible.', **evidence)
    offset = first + best
    return Synchronization('estimated', method, offset, int(signal.origin) + offset,
                           float(phases[best]), **evidence)


def _temporal_signal(signal):
    if not isinstance(signal, Signal) or signal.domain != 'discrete' or signal.data_kind != 'temporal':
        raise ValueError('La recepción requiere una señal temporal discreta.')


def recover_symbols(signal: Signal, count: int, samples_per_symbol: int, spec: SynchronizationSpec,
                    *, pilot: Signal | None = None, sample_gain=1.0,
                    execution: ExecutionContext | None = None) -> ReceiveResult:
    """Sample a finite record. The gain is the number divided out of each symbol."""
    _temporal_signal(signal)
    if not isinstance(spec, SynchronizationSpec):
        raise TypeError('Indicá una configuración de sincronización.')
    count = integer(count, 'La cantidad de símbolos', maximum=sys.maxsize)
    sps = integer(samples_per_symbol, 'Las muestras por símbolo', maximum=sys.maxsize)
    gain = real(sample_gain, 'La ganancia de muestreo', positive=True)
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    clock = clock_from_signal(signal, sps)
    values = signal.values
    valid_last = values.size - 1 - (count-1)*sps
    width = 0
    pilot_size = 0
    if pilot is not None:
        _temporal_signal(pilot)
        clock_from_signal(pilot, 1)
        pilot_size = pilot.values.size
        if spec.mode != 'estimated' or not 2 <= pilot_size <= count:
            raise ValueError('La estimación requiere un piloto de 2 a la cantidad de símbolos solicitados.')
    if spec.mode == 'estimated' and pilot is not None:
        last = valid_last if spec.search_last is None else min(spec.search_last, valid_last)
        width = max(0, last - spec.search_first + 1)
    terms = width*pilot_size
    if terms > _MAX_CORRELATION_TERMS:
        raise ResourceLimitError('Acotá el intervalo o la longitud del piloto para la búsqueda de sincronización.')
    scratch_terms = min(terms, max(_CORRELATION_BLOCK_TERMS, pilot_size))
    with ctx.reserve(48*min(count, values.size) + 32*width + 64*scratch_terms + 64*pilot_size):
        sources = (signal,) if pilot is None else (signal, pilot)
        digests = tuple(content_digest(source, ctx.checkpoint) for source in sources)
        if spec.mode == 'estimated':
            sync = _estimate_sync(signal, spec, pilot, valid_last, sps, ctx)
        else:
            sync = _provided_sync(signal, spec, valid_last)
        ctx.checkpoint(70)
        observed = None
        if sync.sample_offset is not None:
            offset = sync.sample_offset
            stop = offset + count*sps
            with np.errstate(over='ignore', invalid='ignore'):
                selected = values[offset:stop:sps]
                samples = np.empty_like(selected)
                samples.real = selected.real / gain
                samples.imag = selected.imag / gain
                samples *= np.exp(-1j*sync.phase_rad)
            if not np.isfinite(samples).all():
                raise ValueError('Las muestras corregidas exceden el rango numérico.')
            fields = deepcopy(signal.metadata)
            fields.pop('core_provenance', None)
            fields.update(operation='recover_symbols', samples_per_symbol=1,
                          communications_reception={
                              'schema': 1, 'specification': asdict(spec), 'alignment': asdict(sync),
                              'sample_gain': gain, 'inputs_sha256': list(digests),
                          })
            if clock is None:
                observed = Signal(samples, name='Símbolos recibidos I/Q', metadata=fields)
            else:
                start = None if clock.time_start_s is None else clock.time_start_s + offset/clock.sample_rate_hz
                symbol_clock = replace(clock, samples_per_symbol=1, time_start_s=start)
                observed = iq_signal(samples, symbol_clock, name='Símbolos recibidos I/Q',
                                     amplitude_units=fields.get('amplitude_units', '1'), metadata=fields)
            observed._core_verification = (content_digest(observed, ctx.checkpoint), digests, None)
        ctx.checkpoint(100)
        verify_inputs(sources, digests, ctx.checkpoint)
    return ReceiveResult(sync, observed, gain)
