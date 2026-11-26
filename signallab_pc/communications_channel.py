"""Baseband communication channels for finite sampled records."""

from copy import deepcopy
from dataclasses import asdict, dataclass
import math
import sys

import numpy as np

from .communications_data import MAX_SEED, integer, real
from .execution import ExecutionContext
from .model import Signal
from .operation_provenance import content_digest, verify_inputs
from .system_clock import reindex_clock, validate_clock_resolution


_BLOCK = 65_536
_LOG_POWER_DB = math.log(10) / 10
_LOG_TWO = math.log(2)


@dataclass(frozen=True, slots=True)
class AWGNSpec:
    reference: str
    level_db: float
    seed: int
    domain: str = 'complex'
    symbol_energy: float | None = None
    bits_per_symbol: int | None = None
    signal_power: float | None = None

    def __post_init__(self):
        if self.reference not in ('snr', 'es_n0', 'eb_n0'):
            raise ValueError('Seleccioná SNR, Es/N0 o Eb/N0.')
        if self.domain not in ('real', 'complex'):
            raise ValueError('Seleccioná ruido real o complejo circular.')
        level = real(self.level_db, 'La relación en dB')
        seed = integer(self.seed, 'La semilla', minimum=0, maximum=MAX_SEED)
        energy = None if self.symbol_energy is None else real(self.symbol_energy, 'Es', positive=True)
        power = None if self.signal_power is None else real(self.signal_power, 'La potencia', positive=True)
        width = None if self.bits_per_symbol is None else integer(
            self.bits_per_symbol, 'Los bits por símbolo', maximum=32,
        )
        if self.reference != 'snr' and energy is None:
            raise ValueError('Indicá la energía discreta Es para Es/N0 o Eb/N0.')
        if self.reference == 'eb_n0' and width is None:
            raise ValueError('Indicá la cantidad de bits por símbolo para Eb/N0.')
        object.__setattr__(self, 'level_db', level)
        object.__setattr__(self, 'seed', seed)
        object.__setattr__(self, 'symbol_energy', energy)
        object.__setattr__(self, 'signal_power', power)
        object.__setattr__(self, 'bits_per_symbol', width)


@dataclass(frozen=True, slots=True)
class NoiseStatistics:
    samples: int
    reference_power: float
    measured_signal_power: float
    symbol_energy: float | None
    bit_energy: float | None
    n0: float
    snr_db: float | None
    es_n0_db: float | None
    eb_n0_db: float | None
    nominal_variance_i: float
    nominal_variance_q: float
    measured_variance_i: float
    measured_variance_q: float
    measured_mean_i: float
    measured_mean_q: float
    measured_covariance_iq: float


@dataclass(frozen=True, slots=True, eq=False)
class AWGNResult:
    signal: Signal
    specification: AWGNSpec
    statistics: NoiseStatistics


def _power(values, domain, ctx):
    scale = 0.0
    count = values.size
    for start in range(0, count, _BLOCK):
        ctx.checkpoint()
        block = values[start:start+_BLOCK]
        if not np.isfinite(block).all():
            raise ValueError('El canal requiere muestras finitas.')
        if domain == 'real' and np.any(block.imag):
            raise ValueError('El canal real requiere muestras con componente imaginaria nula.')
        scale = max(scale, float(np.max(np.abs(block.real))), float(np.max(np.abs(block.imag))))
    if scale == 0:
        return 0.0
    relative = 0.0
    for start in range(0, count, _BLOCK):
        ctx.checkpoint()
        block = values[start:start+_BLOCK]
        relative += float(np.sum((block.real/scale)**2 + (block.imag/scale)**2))
    rms = math.sqrt(relative/count) * scale
    power = rms*rms
    if not math.isfinite(power) or power == 0:
        raise ValueError('La potencia de las muestras excede la representación numérica finita.')
    return power


def _positive_exp(value):
    try:
        result = math.exp(value)
    except OverflowError as exc:
        raise ValueError('La potencia de ruido excede el rango numérico.') from exc
    if result == 0 or not math.isfinite(result):
        raise ValueError('La potencia de ruido excede el rango numérico.')
    return result


def _nominal(spec, power):
    log_ratio = _LOG_POWER_DB * spec.level_db
    real_channel = spec.domain == 'real'
    energy = spec.symbol_energy
    bits = spec.bits_per_symbol
    bit_energy = energy/bits if energy is not None and bits is not None else None
    if bit_energy == 0:
        raise ValueError('La energía por bit excede el rango numérico.')
    if spec.reference == 'snr':
        if power <= 0:
            raise ValueError('SNR por muestra necesita potencia de referencia positiva.')
        log_total = math.log(power) - log_ratio
        log_n0 = log_total + (_LOG_TWO if real_channel else 0)
        log_component = log_total - (0 if real_channel else _LOG_TWO)
    else:
        reference = energy if spec.reference == 'es_n0' else bit_energy
        log_n0 = math.log(reference) - log_ratio
        log_component = log_n0 - _LOG_TWO
        log_total = log_component if real_channel else log_n0
    n0, variance = _positive_exp(log_n0), _positive_exp(log_component)
    snr = spec.level_db if spec.reference == 'snr' else (
        (math.log(power) - log_total)/_LOG_POWER_DB if power > 0 else None
    )
    es_n0 = spec.level_db if spec.reference == 'es_n0' else (
        (math.log(energy) - log_n0)/_LOG_POWER_DB if energy is not None else None
    )
    eb_n0 = spec.level_db if spec.reference == 'eb_n0' else (
        (math.log(bit_energy) - log_n0)/_LOG_POWER_DB if bit_energy is not None else None
    )
    return variance, n0, snr, es_n0, eb_n0, bit_energy


def add_awgn(signal: Signal, spec: AWGNSpec, execution: ExecutionContext | None = None) -> AWGNResult:
    """Perturb a finite sampled record; report per-sample and per-symbol quantities."""
    if not isinstance(signal, Signal) or not isinstance(spec, AWGNSpec):
        raise TypeError('El canal requiere una señal y una configuración AWGN.')
    if signal.data_kind != 'temporal':
        raise ValueError('El canal requiere muestras temporales.')
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    values = signal.values
    if not isinstance(values, np.ndarray) or values.ndim != 1 or not values.size:
        raise ValueError('El canal requiere un vector de muestras.')
    count = values.size
    dimensions = 1 if spec.domain == 'real' else 2
    with ctx.reserve(48 * count + 96 * min(count, _BLOCK)):
        source = content_digest(signal, ctx.checkpoint)
        measured_power = _power(values, spec.domain, ctx)
        power = measured_power if spec.signal_power is None else spec.signal_power
        variance, n0, snr, es_n0, eb_n0, bit_energy = _nominal(spec, power)
        std = math.sqrt(variance)
        out = np.empty(count, dtype=np.complex128)
        means = np.zeros(dimensions)
        squares = np.zeros(dimensions)
        mixed = 0.0
        rng = np.random.Generator(np.random.PCG64(spec.seed))
        for start in range(0, count, _BLOCK):
            ctx.checkpoint(20 + 70*start//count)
            stop = min(count, start + _BLOCK)
            z = rng.standard_normal((stop-start, dimensions))
            means += z.sum(axis=0)
            squares += (z*z).sum(axis=0)
            out[start:stop] = values[start:stop]
            out.real[start:stop] += std*z[:, 0]
            if dimensions == 2:
                out.imag[start:stop] += std*z[:, 1]
                mixed += float(np.dot(z[:, 0], z[:, 1]))
        means /= count
        actual = variance*np.maximum(0.0, squares/count - means**2)
        covariance = variance*(mixed/count - float(means[0]*means[1])) if dimensions == 2 else 0.0
        if not np.isfinite(actual).all() or not math.isfinite(covariance):
            raise FloatingPointError('La varianza medida excede el rango numérico finito.')
        statistics = NoiseStatistics(
            count, power, measured_power, spec.symbol_energy, bit_energy, n0, snr, es_n0, eb_n0,
            variance, variance if dimensions == 2 else 0.0,
            float(actual[0]), float(actual[1]) if dimensions == 2 else 0.0,
            float(std*means[0]), float(std*means[1]) if dimensions == 2 else 0.0, covariance,
        )
        metadata = deepcopy(signal.metadata)
        metadata.pop('core_provenance', None)
        metadata.update(operation='communications_awgn', communications_noise={
            'schema': 1, 'generator': 'PCG64', 'numpy_version': np.__version__,
            'specification': asdict(spec), 'statistics': asdict(statistics), 'source_sha256': source,
        })
        noisy = signal.copy_with(values=out, metadata=metadata, expression='', name='I/Q con AWGN')
        noisy._core_verification = (content_digest(noisy, ctx.checkpoint), (source,), None)
        ctx.checkpoint(100)
        verify_inputs((signal,), (source,), ctx.checkpoint)
    return AWGNResult(noisy, spec, statistics)


@dataclass(frozen=True, slots=True)
class ChannelPath:
    """A causal path with delay in samples and a constant complex gain."""

    delay_samples: int
    gain_real: float = 1.0
    gain_imag: float = 0.0

    def __post_init__(self):
        object.__setattr__(self, 'delay_samples', integer(
            self.delay_samples, 'El retardo en muestras', minimum=0, maximum=(1 << 63) - 1,
        ))
        object.__setattr__(self, 'gain_real', real(self.gain_real, 'La parte real de la ganancia'))
        object.__setattr__(self, 'gain_imag', real(self.gain_imag, 'La parte imaginaria de la ganancia'))

    @property
    def gain(self):
        return complex(self.gain_real, self.gain_imag)


def parse_channel_path(text: str) -> ChannelPath:
    from .scalar_expression import constant_value, integer_value

    delay, separator, gain = text.partition('=')
    if not separator or not delay.strip() or not gain.strip():
        raise ValueError('Escribí cada trayectoria como retardo = ganancia. Por ejemplo, 4 = 0.35*i.')
    coefficient = constant_value(gain.strip())
    return ChannelPath(integer_value(delay.strip()), coefficient.real, coefficient.imag)


def apply_multipath(signal: Signal, paths: tuple[ChannelPath, ...],
                    execution: ExecutionContext | None = None) -> Signal:
    """Sum delayed copies of a record, retaining the full finite response."""
    if not isinstance(signal, Signal) or signal.domain != 'discrete' or signal.data_kind != 'temporal':
        raise ValueError('El canal multitrayecto requiere una señal temporal discreta.')
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    paths = tuple(paths)
    if not paths or any(not isinstance(path, ChannelPath) for path in paths):
        raise ValueError('Indicá al menos una trayectoria con retardo y ganancia.')
    length = signal.values.size
    max_delay = max(path.delay_samples for path in paths)
    count = length + max_delay
    if count > sys.maxsize // 16 or signal.origin + count - 1 >= 1 << 63:
        raise ValueError('El soporte de salida excede los índices o el espacio de direcciones.')

    with ctx.reserve(48 * count + 32 * min(length, _BLOCK) + 512 * len(paths)):
        source = content_digest(signal, ctx.checkpoint)
        clock = reindex_clock(signal.metadata, 0, count)
        if 'sample_rate_hz' in clock and 'time_start_s' not in clock:
            validate_clock_resolution(0, clock['sample_rate_hz'], count)
        for start in range(0, length, _BLOCK):
            ctx.checkpoint()
            if not np.isfinite(signal.values[start:start + _BLOCK]).all():
                raise ValueError('El canal requiere un registro con muestras finitas.')
        output = np.zeros(count, dtype=np.complex128)
        work = len(paths) * length
        try:
            with np.errstate(over='raise', invalid='raise', under='ignore'):
                for index, path in enumerate(paths):
                    gain = path.gain if path.gain_imag else path.gain_real
                    if not gain:
                        ctx.checkpoint(10 + 80 * index // len(paths))
                        continue
                    delay = path.delay_samples
                    for start in range(0, length, _BLOCK):
                        ctx.checkpoint(10 + 80 * (index * length + start) // work)
                        stop = min(length, start + _BLOCK)
                        output[start + delay:stop + delay] += gain * signal.values[start:stop]
        except FloatingPointError as exc:
            raise FloatingPointError('La suma de trayectorias excede el rango numérico finito.') from exc

        ctx.checkpoint(90)
        metadata = deepcopy(signal.metadata)
        metadata.pop('core_provenance', None)
        metadata.update(clock)
        metadata.update(operation='communications_multipath', communications_multipath={
            'schema': 1, 'paths': [asdict(path) for path in paths], 'source_sha256': source,
        })
        result = signal.copy_with(values=output, metadata=metadata, expression='', name='Salida multitrayecto')
        result._core_verification = (content_digest(result, ctx.checkpoint), (source,), None)
        ctx.checkpoint(100)
        verify_inputs((signal,), (source,), ctx.checkpoint)
    return result
