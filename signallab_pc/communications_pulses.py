"""Finite pulse shaping, exact zero insertion and matched filtering."""

from copy import deepcopy
from dataclasses import asdict, dataclass, replace
import math
import sys

import numpy as np
from scipy import signal as scipy_signal

from .communications_data import clock_from_signal, immutable_array, integer, iq_signal, real
from .dsp_application import FIRRequest, apply_fir, verify_dsp_signal
from .execution import ExecutionContext
from .filters import Transfer
from .model import Signal
from .operation_provenance import content_digest, verify_inputs


_BLOCK = 65_536


@dataclass(frozen=True, slots=True)
class PulseSpec:
    family: str = 'rrc'
    samples_per_symbol: int = 8
    span_symbols: int = 10
    rolloff: float | None = None
    normalization: str = 'unit_energy'

    def __post_init__(self):
        if self.family not in ('rectangular', 'rc', 'rrc'):
            raise ValueError('Seleccioná un pulso rectangular, RC o RRC.')
        sps = integer(self.samples_per_symbol, 'Las muestras por símbolo', maximum=sys.maxsize)
        span = integer(self.span_symbols, 'El span en símbolos', maximum=sys.maxsize)
        rolloff = self.rolloff
        if self.family == 'rectangular':
            if rolloff is not None:
                raise ValueError('El pulso rectangular usa duración en símbolos. El roll-off corresponde a RC y RRC.')
        else:
            rolloff = real(0.35 if rolloff is None else rolloff, 'El roll-off', minimum=0, maximum=1)
        if self.normalization not in ('unit_energy', 'unit_peak'):
            raise ValueError('Seleccioná energía unitaria o amplitud teórica unitaria en el centro.')
        object.__setattr__(self, 'samples_per_symbol', sps)
        object.__setattr__(self, 'span_symbols', span)
        object.__setattr__(self, 'rolloff', rolloff)

    @property
    def tap_count(self):
        return self.span_symbols * self.samples_per_symbol + (self.family != 'rectangular')


def _sinc(t):
    # Preserve analytical zeros at integer symbol offsets.
    return np.where((t != 0) & (t == np.trunc(t)), 0.0, np.sinc(t))


def _rrc_regular(t, z, beta):
    top = (1-beta) * _sinc((1-beta)*t) + (4*beta/math.pi)*np.cos(math.pi*(1+beta)*t)
    return top / ((1-z)*(1+z))


def _rrc_near_pole(t, z, beta):
    """Factor the numerator's exact zero before cancelling the denominator."""
    pole = 1 / (4*beta)
    midpoint = (t + pole) / 2
    delta = (t - pole) / 2
    a = math.pi*(1-beta)
    b = math.pi*(1+beta)
    factored = (math.cos(b*pole)
                + (a*pole)*np.cos(a*midpoint)*_sinc((1-beta)*delta)
                - (z*b*pole)*np.sin(b*midpoint)*_sinc((1+beta)*delta))
    return -factored / (math.pi*t*(1+z))


def _raised_cosine_samples(t, beta, *, root):
    t = np.abs(np.asarray(t, dtype=np.float64))
    if beta == 0:
        return _sinc(t)
    if not root:
        z = (2*beta)*t
        # cos(pi*z/2)/(1-z) = (pi/2) sinc((1-z)/2), including z=1.
        return _sinc(t)*(math.pi/2)*_sinc((1-z)/2)/(1+z)
    z = (4*beta)*t
    near = np.abs(1-z) < 0.125
    values = np.empty_like(t)
    values[~near] = _rrc_regular(t[~near], z[~near], beta)
    if near.any():
        values[near] = _rrc_near_pole(t[near], z[near], beta)
    return values


@dataclass(frozen=True, slots=True, eq=False)
class Pulse:
    specification: PulseSpec
    taps: np.ndarray
    energy: float
    center_amplitude: float

    @property
    def group_delay_samples(self):
        return (self.taps.size - 1) / 2

    def transfer(self, sample_rate_hz=None, *, matched=False):
        sample_period = None if sample_rate_hz is None else 1 / real(sample_rate_hz, 'Fs', positive=True)
        taps = self.taps[::-1] if matched else self.taps
        name = f'Pulso {self.specification.family.upper()}'
        return Transfer(taps, [1.0], name=f'Adaptado de {name}' if matched else name,
                        sample_period_s=sample_period)


def design_pulse(spec: PulseSpec, execution: ExecutionContext | None = None) -> Pulse:
    if not isinstance(spec, PulseSpec):
        raise TypeError('Indicá una configuración de pulso.')
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    count = spec.tap_count
    bound = 16 * count + 160 * min(count, _BLOCK)
    if count > sys.maxsize // 16:
        raise ValueError('El span excede el espacio de direcciones.')
    with ctx.reserve(bound):
        taps = np.empty(count, dtype=np.float64)
        center = 1.0
        if spec.family == 'rectangular':
            taps.fill(1)
        else:
            root = spec.family == 'rrc'
            beta = spec.rolloff
            if root:
                center = 1 + (4/math.pi - 1)*beta
            delay = (count-1)/2
            for start in range(0, count, _BLOCK):
                ctx.checkpoint(100 * start // count)
                stop = min(count, start + _BLOCK)
                t = (np.arange(start, stop, dtype=np.float64)-delay)/spec.samples_per_symbol
                taps[start:stop] = _raised_cosine_samples(t, beta, root=root)
        gain = 1 / (math.sqrt(float(np.dot(taps, taps))) if spec.normalization == 'unit_energy' else center)
        taps *= gain
        result = Pulse(spec, immutable_array(taps, np.float64), float(np.dot(taps, taps)), center*gain)
        ctx.checkpoint(100)
    return result


def _check_iq(signal):
    if not isinstance(signal, Signal) or signal.domain != 'discrete' or signal.data_kind != 'temporal':
        raise ValueError('Esta operación requiere una señal temporal discreta.')


def _support(origin, count):
    if count > sys.maxsize // 16 or origin < -(1 << 63) or origin + count - 1 >= 1 << 63:
        raise ValueError('El soporte de salida excede los índices o el espacio de direcciones.')


def upsample_symbols(symbols: Signal, samples_per_symbol: int,
                     execution: ExecutionContext | None = None) -> Signal:
    """Insert exactly L-1 zeros between symbols and keep the finite support."""
    _check_iq(symbols)
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    samples_per_symbol = integer(samples_per_symbol, 'Las muestras por símbolo', maximum=sys.maxsize)
    old_clock = clock_from_signal(symbols, 1)
    clock = None if old_clock is None else replace(old_clock, samples_per_symbol=samples_per_symbol)
    length = symbols.values.size
    count = (length-1)*samples_per_symbol + 1
    origin = symbols.origin*samples_per_symbol
    _support(origin, count)
    with ctx.reserve(48 * count):
        digest = content_digest(symbols, ctx.checkpoint)
        values = np.zeros(count, dtype=np.complex128)
        for start in range(0, length, _BLOCK):
            ctx.checkpoint(100 * start // length)
            stop = min(length, start + _BLOCK)
            values[start*samples_per_symbol:stop*samples_per_symbol:samples_per_symbol] = symbols.values[start:stop]
        fields = {
            **deepcopy(symbols.metadata),
            'operation': 'symbol_upsampling',
            'samples_per_symbol': samples_per_symbol,
            'communications_upsampling': {'schema': 1, 'input_symbols': length, 'input_origin': symbols.origin,
                                          'input_sha256': digest, 'stride': samples_per_symbol},
        }
        fields.pop('core_provenance', None)
        name = 'Tren de símbolos I/Q'
        if clock is None:
            result = Signal(values, origin=origin, name=name, metadata=fields)
        else:
            result = iq_signal(values, clock, origin=origin, name=name,
                               amplitude_units=fields.get('amplitude_units', '1'), metadata=fields)
        result._core_verification = (content_digest(result, ctx.checkpoint), (digest,), None)
        ctx.checkpoint(100)
        verify_inputs((symbols,), (digest,), ctx.checkpoint)
    return result


def apply_pulse(signal: Signal, pulse: Pulse, *, matched=False,
                execution: ExecutionContext | None = None) -> Signal:
    _check_iq(signal)
    if not isinstance(pulse, Pulse) or type(matched) is not bool:
        raise ValueError('Indicá un pulso y si se aplica su filtro adaptado.')
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    clock = clock_from_signal(signal, pulse.specification.samples_per_symbol)
    count = signal.values.size + pulse.taps.size - 1
    _support(signal.origin, count)
    with ctx.reserve(144 * count + 384 * pulse.taps.size):
        clock_fields = {} if clock is None else clock.metadata(count)
        model = pulse.transfer(None if clock is None else clock.sample_rate_hz, matched=matched)
        child = replace(ctx, pool=None, progress=None)
        shaped = apply_fir(FIRRequest(signal, model, 'full'), child)
        _, sources, auxiliary = verify_dsp_signal(shaped)
        shaped.metadata = deepcopy(shaped.metadata)
        shaped.metadata.update(clock_fields)
        shaped.metadata.update(
            samples_per_symbol=pulse.specification.samples_per_symbol,
            communications_pulse={
                'schema': 1, 'specification': asdict(pulse.specification), 'matched': matched,
                'tap_count': pulse.taps.size, 'tap_energy': pulse.energy,
                'group_delay_samples': pulse.group_delay_samples,
            },
        )
        shaped._core_verification = (content_digest(shaped, ctx.checkpoint), sources, auxiliary)
        ctx.checkpoint(100)
        verify_inputs((signal, model), sources, ctx.checkpoint)
    return shaped


@dataclass(frozen=True, slots=True, eq=False)
class InterSymbolInterference:
    lags_symbols: np.ndarray
    relative_amplitudes: np.ndarray
    peak: float
    rms: float
    main_tap: float


def matched_pulse_isi(pulse: Pulse, execution: ExecutionContext | None = None) -> InterSymbolInterference:
    """Evaluate the combined TX/RX response at integer symbol offsets."""
    if not isinstance(pulse, Pulse):
        raise TypeError('La medición de ISI requiere un pulso.')
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    delay = pulse.taps.size - 1
    sps = pulse.specification.samples_per_symbol
    span = delay // sps
    with ctx.reserve(320 * pulse.taps.size):
        combined = scipy_signal.correlate(pulse.taps, pulse.taps, mode='full', method='auto')
        ctx.checkpoint(85)
        main = float(combined[delay])
        lags = np.arange(-span, span+1, dtype=np.int64)
        relative = combined[delay + lags*sps] / main
        side = relative[lags != 0]
        result = InterSymbolInterference(
            immutable_array(lags, np.int64), immutable_array(relative, np.float64),
            float(np.max(np.abs(side), initial=0)), float(np.sqrt(np.mean(side**2))) if side.size else 0.0, main,
        )
        ctx.checkpoint(100)
    return result
