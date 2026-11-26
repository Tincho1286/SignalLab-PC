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


def channel_record_power(values, domain, ctx):
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
        measured_power = channel_record_power(values, spec.domain, ctx)
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


@dataclass(frozen=True, slots=True)
class MultipathSpec:
    """Finite LTI baseband channel, with optional unit impulse energy."""

    paths: tuple[ChannelPath, ...]
    normalize_power: bool = False

    def __post_init__(self):
        paths = tuple(self.paths)
        if not paths or any(not isinstance(path, ChannelPath) for path in paths):
            raise ValueError('Indicá al menos una trayectoria con retardo y ganancia.')
        if type(self.normalize_power) is not bool:
            raise ValueError('Indicá explícitamente si se normaliza la potencia del canal.')
        object.__setattr__(self, 'paths', paths)


def _effective_taps(spec, ctx):
    grouped = {}
    for path in spec.paths:
        ctx.checkpoint()
        grouped.setdefault(path.delay_samples, []).append(path)
    try:
        taps = tuple(ChannelPath(delay, math.fsum(p.gain_real for p in paths),
                                 math.fsum(p.gain_imag for p in paths))
                     for delay, paths in sorted(grouped.items()))
    except OverflowError as exc:
        raise FloatingPointError('La ganancia coherente excede el rango numérico finito.') from exc
    if not spec.normalize_power:
        return taps
    scale = max(max(abs(p.gain_real), abs(p.gain_imag)) for p in taps)
    if scale == 0:
        raise ValueError('La respuesta al impulso nula no admite normalización de potencia.')
    norm = math.sqrt(math.fsum((p.gain_real / scale)**2 + (p.gain_imag / scale)**2 for p in taps))
    return tuple(ChannelPath(p.delay_samples, p.gain_real / scale / norm, p.gain_imag / scale / norm)
                 for p in taps)


@dataclass(frozen=True, slots=True)
class PowerDelayTap:
    delay_samples: int
    power: float


@dataclass(frozen=True, slots=True)
class SymbolSpacedISI:
    samples_per_symbol: int
    reference_delay_samples: int
    interfering_lags_symbols: tuple[int, ...]
    interference_to_reference_power: float


@dataclass(frozen=True, slots=True)
class MultipathAnalysis:
    taps: tuple[ChannelPath, ...]
    power_delay_profile: tuple[PowerDelayTap, ...]
    total_power: float
    mean_delay_samples: float | None
    rms_delay_spread_samples: float | None
    symbol_spaced_isi: SymbolSpacedISI | None


def analyze_multipath(spec: MultipathSpec, *, samples_per_symbol: int | None = None,
                      execution: ExecutionContext | None = None) -> MultipathAnalysis:
    """Analyze coherent taps, with an optional channel-only symbol-spaced ISI measure."""
    if not isinstance(spec, MultipathSpec):
        raise ValueError('El análisis requiere una configuración multitrayecto.')
    if samples_per_symbol is not None:
        samples_per_symbol = integer(samples_per_symbol, 'Las muestras por símbolo')
    ctx = execution or ExecutionContext()
    with ctx.reserve(640 * len(spec.paths)):
        taps = _effective_taps(spec, ctx)
        try:
            profile = tuple(PowerDelayTap(tap.delay_samples, tap.gain_real**2 + tap.gain_imag**2)
                            for tap in taps)
            total = math.fsum(row.power for row in profile)
        except OverflowError as exc:
            raise FloatingPointError('La potencia del canal excede el rango numérico finito.') from exc
        if not math.isfinite(total):
            raise FloatingPointError('La potencia del canal excede el rango numérico finito.')
        if any(row.power == 0 and tap.gain for tap, row in zip(taps, profile)):
            raise FloatingPointError('La potencia de una trayectoria no nula es menor que el rango numérico.')
        mean = spread = isi = None
        if total:
            # Work with relative delays so a large shared delay does not erase the spread.
            base = next(row.delay_samples for row in profile if row.power > 0)
            remaining = tuple((row.delay_samples - base, row.power / total) for row in profile if row.power > 0)
            relative_mean = math.fsum(delay * weight for delay, weight in remaining)
            mean = base + relative_mean
            spread = math.sqrt(math.fsum((delay - relative_mean)**2 * weight for delay, weight in remaining))
            if samples_per_symbol is not None:
                main = max(profile, key=lambda row: row.power)
                echoes = tuple(row for row in profile if row.power > 0 and row is not main
                               and (row.delay_samples - main.delay_samples) % samples_per_symbol == 0)
                isi = SymbolSpacedISI(
                    samples_per_symbol, main.delay_samples,
                    tuple((row.delay_samples - main.delay_samples) // samples_per_symbol for row in echoes),
                    math.fsum(row.power / main.power for row in echoes),
                )
        ctx.checkpoint()
    return MultipathAnalysis(taps, profile, total, mean, spread, isi)


def multipath_frequency(analysis: MultipathAnalysis, points: int = 2048,
                        execution: ExecutionContext | None = None) -> Signal:
    """Evaluate H on a centered periodic grid in rad/sample."""
    if not isinstance(analysis, MultipathAnalysis):
        raise ValueError('Calculá primero la respuesta al impulso del canal.')
    points = integer(points, 'Los puntos de frecuencia', minimum=2, maximum=(1 << 31) - 1)
    ctx = execution or ExecutionContext()
    origin_bin = -(points // 2)
    step = math.tau / points
    with ctx.reserve(36 * points + 80 * min(_BLOCK, points)):
        values = np.zeros(points, dtype=np.complex128)
        for start in range(0, points, _BLOCK):
            stop = min(points, start + _BLOCK)
            indices = np.arange(origin_bin + start, origin_bin + stop, dtype=np.int64)
            for tap in analysis.taps:
                ctx.checkpoint()
                if tap.gain:
                    turns = np.remainder(indices * (tap.delay_samples % points), points) / points
                    values[start:stop] += tap.gain * np.exp(-1j * math.tau * turns)
        result = Signal(values, origin_bin * step, step, 'rad/muestra', 'H(eʲω)', 'frequency',
                        metadata={'operation': 'frequency_response'})
        ctx.checkpoint()
    return result


def discrete_channel_size(signal, max_delay):
    """Validate a finite temporal record and its expanded output geometry."""
    if not isinstance(signal, Signal) or signal.domain != 'discrete' or signal.data_kind != 'temporal':
        raise ValueError('El canal requiere una señal temporal discreta.')
    count = signal.values.size + max_delay
    if count > sys.maxsize // 16 or signal.origin + count - 1 >= 1 << 63:
        raise ValueError('El soporte de salida excede los índices o el espacio de direcciones.')
    return count


def channel_clock(signal, offset, count):
    clock = reindex_clock(signal.metadata, offset, count)
    if 'sample_rate_hz' in clock and 'time_start_s' not in clock:
        validate_clock_resolution(0, clock['sample_rate_hz'], count)
    return clock


def apply_multipath(signal: Signal, paths: tuple[ChannelPath, ...] | MultipathSpec,
                    execution: ExecutionContext | None = None) -> Signal:
    """Sum delayed copies of a record, retaining the full finite response."""
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    spec = paths if isinstance(paths, MultipathSpec) else MultipathSpec(paths)
    count = discrete_channel_size(signal, max(path.delay_samples for path in spec.paths))
    length = signal.values.size
    with ctx.reserve(48 * count + 32 * min(length, _BLOCK) + 640 * len(spec.paths)):
        taps = _effective_taps(spec, ctx)
        source = content_digest(signal, ctx.checkpoint)
        clock = channel_clock(signal, 0, count)
        for start in range(0, length, _BLOCK):
            ctx.checkpoint()
            if not np.isfinite(signal.values[start:start + _BLOCK]).all():
                raise ValueError('El canal requiere un registro con muestras finitas.')
        output = np.zeros(count, dtype=np.complex128)
        work = len(taps) * length
        try:
            with np.errstate(over='raise', invalid='raise', under='ignore'):
                for index, path in enumerate(taps):
                    gain = path.gain if path.gain_imag else path.gain_real
                    if not gain:
                        ctx.checkpoint(10 + 80 * index // len(taps))
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
            'schema': 2, 'paths': [asdict(path) for path in spec.paths],
            'normalize_power': spec.normalize_power, 'source_sha256': source,
            'first_active_delay_samples': next((tap.delay_samples for tap in taps if tap.gain), None),
        })
        result = signal.copy_with(values=output, metadata=metadata, expression='', name='Salida multitrayecto')
        result._core_verification = (content_digest(result, ctx.checkpoint), (source,), None)
        ctx.checkpoint(100)
        verify_inputs((signal,), (source,), ctx.checkpoint)
    return result
