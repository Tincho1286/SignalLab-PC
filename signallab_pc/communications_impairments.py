"""Timing, sampling-clock, Wiener phase and frequency-flat I/Q impairments."""

from copy import deepcopy
from dataclasses import asdict, dataclass
import cmath
import math

import numpy as np

from .communications_channel import channel_clock, discrete_channel_size
from .communications_data import MAX_SEED, integer, real
from .execution import ExecutionContext
from .model import Signal
from .operation_provenance import content_digest, verify_inputs
from .system_clock import validate_clock_resolution


_BLOCK = 65_536
_SINC_BLOCK = 2048
_SINC_HALF_WIDTH = 32


def _finish(signal, values, specification, operation, name, source_hash, metadata, ctx, *, evidence=None):
    metadata.pop('core_provenance', None)
    metadata.update(operation=operation)
    metadata[operation] = {'schema': 1, 'specification': asdict(specification), 'source_sha256': source_hash}
    if evidence is not None:
        metadata[operation].update(evidence)
    result = signal.copy_with(values=values, metadata=metadata, expression='', name=name)
    result._core_verification = (content_digest(result, ctx.checkpoint), (source_hash,), None)
    verify_inputs((signal,), (source_hash,), ctx.checkpoint)
    ctx.checkpoint(100)
    return result


@dataclass(frozen=True, slots=True)
class TimingOffset:
    """Delay in input samples and sampling frequency error relative to input Fs."""

    delay_samples: float = 0.0
    sfo_ppm: float = 0.0

    def __post_init__(self):
        delay = real(self.delay_samples, 'El retardo en muestras')
        ppm = real(self.sfo_ppm, 'El error de muestreo en ppm')
        ratio = 1 + ppm / 1_000_000
        if ratio <= 0 or (ppm != 0 and ratio == 1):
            raise ValueError('El error en ppm debe producir una tasa de salida positiva y distinguible.')
        object.__setattr__(self, 'delay_samples', delay)
        object.__setattr__(self, 'sfo_ppm', ppm)


def _integer_offset(source, delay):
    size = source.size
    values = np.zeros_like(source)
    overlap = size - abs(delay)
    if overlap > 0:
        take = max(0, -delay)
        place = max(0, delay)
        values[place:place + overlap] = source[take:take + overlap]
    return values


def _sample_lanczos(source, ratio, delay, cutoff, half_width, ctx):
    size = source.size
    values = np.zeros_like(source)
    offsets = np.arange(1 - half_width, half_width + 1)
    for first in range(0, size, _SINC_BLOCK):
        ctx.checkpoint(85 * first // size)
        stop = min(size, first + _SINC_BLOCK)
        times = np.arange(first, stop)/ratio - delay
        # Avoid converting out-of-range coordinates to integer indices.
        keep = np.flatnonzero((times > -half_width) & (times < size + half_width))
        if not keep.size:
            continue
        positions = times[keep]
        indices = np.floor(positions).astype(np.int64)[:, None] + offsets
        lags = positions[:, None] - indices
        weights = np.sinc(cutoff*lags)*np.sinc(lags/half_width)
        normalization = weights.sum(axis=1)
        valid = (indices >= 0) & (indices < size)
        weights[~valid] = 0
        samples = source[np.clip(indices, 0, size-1)]
        values[first + keep] = np.sum(samples * weights, axis=1) / normalization
    return values


def apply_timing_offset(signal: Signal, spec: TimingOffset,
                        execution: ExecutionContext | None = None) -> Signal:
    """Observe the delayed waveform through the same count at the altered receiver clock."""
    if not isinstance(spec, TimingOffset):
        raise ValueError('Indicá una configuración de retardo y reloj.')
    ctx = execution or ExecutionContext()
    size = discrete_channel_size(signal, 0)
    ratio = 1 + spec.sfo_ppm / 1_000_000
    exact = spec.sfo_ppm == 0 and spec.delay_samples.is_integer()
    cutoff = min(1.0, ratio)
    estimate = 48 * size
    half_width = 0
    if not exact:
        width = _SINC_HALF_WIDTH/cutoff
        if not math.isfinite(width) or width >= (1 << 61):
            raise ValueError('La semilongitud de interpolación excede el rango numérico.')
        half_width = math.ceil(width)
        estimate += 96 * min(size, _SINC_BLOCK) * 2 * half_width

    with ctx.reserve(estimate):
        digest = content_digest(signal, ctx.checkpoint)
        metadata = deepcopy(signal.metadata)
        clock = channel_clock(signal, 0, size)
        if spec.sfo_ppm:
            rate = real(clock.get('sample_rate_hz'), 'La frecuencia de muestreo Fs', positive=True)
            output_rate = rate * ratio
            if output_rate == rate:
                raise ValueError('El error en ppm no se distingue a la tasa de muestreo registrada.')
            validate_clock_resolution(clock.get('time_start_s', 0.0), output_rate, size)
            clock['sample_rate_hz'] = output_rate
            old_sps = metadata.pop('samples_per_symbol', None)
            symbol_rate = metadata.get('symbol_rate_hz')
            if symbol_rate is None and old_sps is not None:
                symbol_rate = rate / integer(old_sps, 'Las muestras por símbolo')
            if symbol_rate is not None:
                symbol_rate = real(symbol_rate, 'La tasa de símbolos', positive=True)
                metadata['symbol_rate_hz'] = symbol_rate
                sps = real(output_rate / symbol_rate, 'Las muestras efectivas por símbolo', positive=True)
                nearest = round(sps)
                if nearest >= 1 and abs(sps-nearest) <= 4*math.ulp(sps):
                    metadata['samples_per_symbol'] = nearest
        metadata.update(clock)
        try:
            with np.errstate(over='raise', invalid='raise', under='ignore'):
                if exact:
                    values = _integer_offset(signal.values, int(spec.delay_samples))
                else:
                    values = _sample_lanczos(signal.values, ratio, spec.delay_samples, cutoff, half_width, ctx)
        except FloatingPointError as exc:
            raise FloatingPointError('La interpolación de reloj excede el rango numérico finito.') from exc
        evidence = {'ratio': ratio, 'method': 'integer' if exact else 'lanczos_sinc',
                    'half_width': half_width, 'normalized_cutoff': cutoff}
        return _finish(signal, values, spec, 'communications_timing_offset', 'Salida con error de reloj',
                       digest, metadata, ctx, evidence=evidence)


@dataclass(frozen=True, slots=True)
class PhaseNoiseSpec:
    """Sampled Wiener phase with a Lorentzian full width at half maximum in Hz."""

    linewidth_hz: float
    seed: int

    def __post_init__(self):
        object.__setattr__(self, 'linewidth_hz', real(self.linewidth_hz, 'El ancho de línea en Hz', minimum=0))
        object.__setattr__(self, 'seed', integer(self.seed, 'La semilla', minimum=0, maximum=MAX_SEED))


@dataclass(frozen=True, slots=True, eq=False)
class PhaseNoiseResult:
    signal: Signal
    phase: Signal
    step_variance_rad2: float


def apply_phase_noise(signal: Signal, spec: PhaseNoiseSpec,
                      execution: ExecutionContext | None = None) -> PhaseNoiseResult:
    if not isinstance(spec, PhaseNoiseSpec):
        raise ValueError('Indicá una configuración de ruido de fase.')
    ctx = execution or ExecutionContext()
    size = discrete_channel_size(signal, 0)
    with ctx.reserve(72 * size + 64 * min(size, _BLOCK)):
        clock = channel_clock(signal, 0, size)
        variance = 0.0
        if spec.linewidth_hz:
            rate = real(clock.get('sample_rate_hz'), 'La frecuencia de muestreo Fs', positive=True)
            variance = math.tau * (spec.linewidth_hz / rate)
            real(variance, 'La varianza del incremento de fase', positive=True)
        digest = content_digest(signal, ctx.checkpoint)
        phase = np.zeros(size)
        if variance:
            rng = np.random.Generator(np.random.PCG64(spec.seed))
            sigma = math.sqrt(variance)
            for start in range(1, size, _BLOCK):
                ctx.checkpoint(45 * start // size)
                stop = min(size, start + _BLOCK)
                phase[start:stop] = phase[start-1] + np.cumsum(sigma * rng.standard_normal(stop-start))
        values = np.empty_like(signal.values)
        for start in range(0, size, _BLOCK):
            ctx.checkpoint(45 + 45 * start // size)
            stop = min(size, start + _BLOCK)
            values[start:stop] = signal.values[start:stop] * np.exp(1j * phase[start:stop])
        auxiliary = Signal(phase, signal.origin, units=signal.units, name='Trayectoria de fase',
                           metadata={**clock, 'amplitude_units': 'rad', 'operation': 'communications_wiener_phase',
                                     'linewidth_hz': spec.linewidth_hz, 'seed': spec.seed})
        metadata = {**deepcopy(signal.metadata), **clock}
        result = _finish(signal, values, spec, 'communications_phase_noise', 'Salida con ruido de fase',
                         digest, metadata, ctx, evidence={
                             'generator': 'PCG64', 'numpy_version': np.__version__, 'step_variance_rad2': variance,
                         })
    return PhaseNoiseResult(result, auxiliary, variance)


@dataclass(frozen=True, slots=True)
class IQImbalance:
    """Q gain relative to I, Q angle error, and additive DC in input amplitude units."""

    q_gain_db: float = 0.0
    q_phase_rad: float = 0.0
    dc_i: float = 0.0
    dc_q: float = 0.0

    def __post_init__(self):
        for name, label in (('q_gain_db', 'La ganancia de Q en dB'), ('q_phase_rad', 'La fase de Q en radianes'),
                            ('dc_i', 'El nivel DC de I'), ('dc_q', 'El nivel DC de Q')):
            object.__setattr__(self, name, real(getattr(self, name), label))


@dataclass(frozen=True, slots=True)
class IQStatistics:
    desired_real: float
    desired_imag: float
    image_real: float
    image_imag: float
    image_rejection_db: float | None
    image_rejection_state: str


@dataclass(frozen=True, slots=True, eq=False)
class IQImbalanceResult:
    signal: Signal
    statistics: IQStatistics


def apply_iq_imbalance(signal: Signal, spec: IQImbalance,
                       execution: ExecutionContext | None = None) -> IQImbalanceResult:
    if not isinstance(spec, IQImbalance):
        raise ValueError('Indicá una configuración de desequilibrio I/Q.')
    ctx = execution or ExecutionContext()
    size = discrete_channel_size(signal, 0)
    try:
        gain = 10.0 ** (spec.q_gain_db/20)
    except OverflowError as exc:
        raise ValueError('La ganancia de Q excede el rango de amplitud lineal.') from exc
    real(gain, 'La ganancia lineal de Q', positive=True)
    effective_angle = math.remainder(spec.q_phase_rad, math.tau)
    branch = cmath.rect(gain, effective_angle)
    # Cardinal angles give exact identity or conjugation at unit gain.
    if abs(effective_angle) == math.pi:
        branch = complex(-gain, 0)
    desired, image = 0.5 + branch/2, 0.5 - branch/2
    rejection = 20*(math.log10(abs(desired)) - math.log10(abs(image))) if desired and image else None
    state = 'finite' if rejection is not None else 'no_image' if desired else 'no_desired'
    statistics = IQStatistics(desired.real, desired.imag, image.real, image.imag, rejection, state)
    with ctx.reserve(48 * size + 64 * min(size, _BLOCK)):
        digest = content_digest(signal, ctx.checkpoint)
        metadata = {**deepcopy(signal.metadata), **channel_clock(signal, 0, size)}
        values = np.empty_like(signal.values)
        try:
            with np.errstate(over='raise', invalid='raise'):
                for start in range(0, size, _BLOCK):
                    ctx.checkpoint(90 * start // size)
                    stop = min(start + _BLOCK, size)
                    block = signal.values[start:stop]
                    values.real[start:stop] = block.real - branch.imag*block.imag + spec.dc_i
                    values.imag[start:stop] = branch.real*block.imag + spec.dc_q
        except FloatingPointError as exc:
            raise FloatingPointError('El desequilibrio I/Q excede el rango numérico finito.') from exc
        result = _finish(signal, values, spec, 'communications_iq_imbalance', 'Salida con desequilibrio I/Q',
                         digest, metadata, ctx, evidence={'statistics': asdict(statistics)})
    return IQImbalanceResult(result, statistics)
