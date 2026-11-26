"""Qt-independent Gaussian fading with a specular component per path."""

from copy import deepcopy
from dataclasses import asdict, dataclass
import cmath
import math

import numpy as np
from scipy import __version__ as scipy_version

from .communications_channel import channel_clock, channel_record_power, discrete_channel_size
from .communications_data import MAX_SEED, integer, real
from .communications_doppler import ClarkeGrid, analyze_clarke
from .execution import ExecutionContext
from .model import Signal
from .operation_provenance import content_digest, verify_inputs


_BLOCK = 65_536


@dataclass(frozen=True, slots=True)
class FadingPath:
    """An arrival path with mean power E[|a|²] and a linear power ratio K."""

    delay_samples: int = 0
    average_power: float = 1.0
    k_linear: float = 0.0
    los_phase_rad: float = 0.0

    def __post_init__(self):
        object.__setattr__(self, 'delay_samples', integer(
            self.delay_samples, 'El retardo en muestras', minimum=0, maximum=(1 << 63) - 1,
        ))
        object.__setattr__(self, 'average_power', real(self.average_power, 'La potencia media', minimum=0))
        object.__setattr__(self, 'k_linear', real(self.k_linear, 'El factor K lineal', minimum=0))
        object.__setattr__(self, 'los_phase_rad', real(self.los_phase_rad, 'La fase LOS en radianes'))

    @classmethod
    def from_k_db(cls, k_db: float, *, delay_samples=0, average_power=1.0, los_phase_rad=0.0):
        level = real(k_db, 'El factor K en dB')
        try:
            ratio = 10.0 ** (level/10)
        except OverflowError as exc:
            raise ValueError('El factor K en dB excede el rango lineal finito.') from exc
        if not ratio:
            raise ValueError('El factor K en dB es demasiado pequeño para el rango lineal finito.')
        return cls(delay_samples, average_power, ratio, los_phase_rad)


def parse_fading_path(text: str, *, k_scale='linear') -> FadingPath:
    from .scalar_expression import integer_value, real_value

    delay, separator, values = text.partition('=')
    parts = values.split(',')
    if not separator or not 1 <= len(parts) <= 3:
        raise ValueError('Escribí retardo=potencia[,K[,fase_LOS]] por trayectoria.')
    if k_scale not in ('linear', 'db'):
        raise ValueError('Elegí K lineal o en dB.')
    parameters = {'delay_samples': integer_value(delay), 'average_power': real_value(parts[0]),
                  'los_phase_rad': real_value(parts[2]) if len(parts) == 3 else 0.0}
    if len(parts) == 1:
        return FadingPath(**parameters)
    ratio = real_value(parts[1])
    if k_scale == 'db':
        return FadingPath.from_k_db(ratio, **parameters)
    return FadingPath(k_linear=ratio, **parameters)


@dataclass(frozen=True, slots=True)
class FadingSpec:
    """Complex fading with independent path streams and optional Clarke Doppler."""

    paths: tuple[FadingPath, ...]
    seed: int
    max_doppler_hz: float | None = None

    def __post_init__(self):
        paths = tuple(self.paths)
        if not paths or any(not isinstance(path, FadingPath) for path in paths):
            raise ValueError('Indicá al menos una trayectoria de fading.')
        object.__setattr__(self, 'paths', paths)
        object.__setattr__(self, 'seed', integer(self.seed, 'La semilla', minimum=0, maximum=MAX_SEED))
        if self.max_doppler_hz is not None:
            object.__setattr__(self, 'max_doppler_hz', real(
                self.max_doppler_hz, 'El Doppler máximo en Hz', minimum=0,
            ))


@dataclass(frozen=True, slots=True)
class FadingStatistics:
    expected_power: float
    observed_power: float
    expected_mean_real: float
    expected_mean_imag: float
    observed_mean_real: float
    observed_mean_imag: float


@dataclass(frozen=True, slots=True, eq=False)
class FadingRealization:
    path: FadingPath
    coefficients: Signal
    statistics: FadingStatistics

    def doppler_diagnostics(self, execution: ExecutionContext | None = None):
        fd = self.coefficients.metadata.get('max_doppler_hz')
        if fd is None:
            raise ValueError('El modo independiente no tiene un espectro Clarke asociado.')
        mean = complex(self.statistics.expected_mean_real, self.statistics.expected_mean_imag)
        return analyze_clarke(self.coefficients, fd, mean=mean, execution=execution)


@dataclass(frozen=True, slots=True, eq=False)
class FadingResult:
    signal: Signal
    specification: FadingSpec
    realizations: tuple[FadingRealization, ...]


def _realize_path(source, destination, path, stream, ctx, index, work, grid, prepared):
    size = source.size
    scale = math.sqrt(path.average_power)
    sigma = scale / math.sqrt(2) / math.sqrt(1 + path.k_linear)
    mean = cmath.rect(scale * math.sqrt(path.k_linear / (1 + path.k_linear)), path.los_phase_rad)
    rng = np.random.Generator(np.random.PCG64(stream))
    ctx.checkpoint(10 + 75 * index * size // work)
    values = np.empty(size, dtype=np.complex128) if grid is None else grid.draw(rng, prepared, ctx)
    delay = path.delay_samples
    for start in range(0, size, _BLOCK):
        ctx.checkpoint(10 + 75 * (index * size + start) // work)
        stop = min(size, start + _BLOCK)
        block = values[start:stop]
        if grid is None:
            normal = rng.standard_normal((stop - start, 2))
            real_part, imag_part = normal[:, 0], normal[:, 1]
        else:
            real_part, imag_part = block.real, block.imag
        block.real = mean.real + sigma * real_part
        block.imag = mean.imag + sigma * imag_part
        destination[start + delay:stop + delay] += block * source[start:stop]
    observed = complex(np.mean(values))
    statistics = FadingStatistics(path.average_power, channel_record_power(values, 'complex', ctx),
                                  mean.real, mean.imag, observed.real, observed.imag)
    return values, statistics


def apply_fading(signal: Signal, spec: FadingSpec, execution: ExecutionContext | None = None) -> FadingResult:
    """Apply y[n] = sum(a_k[n] x[n-d_k]) and retain each coefficient record."""
    if not isinstance(spec, FadingSpec):
        raise ValueError('Indicá una configuración de fading.')
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    count = discrete_channel_size(signal, max(path.delay_samples for path in spec.paths))
    size = signal.values.size
    work = size * len(spec.paths)
    grid = None if spec.max_doppler_hz is None else ClarkeGrid.for_signal(signal, spec.max_doppler_hz)
    extra = 0 if grid is None else grid.work_bytes
    with ctx.reserve(48 * count + 32 * work + 96 * min(size, _BLOCK) + 768 * len(spec.paths) + extra):
        source_hash = content_digest(signal, ctx.checkpoint)
        clock = channel_clock(signal, 0, count)
        for start in range(0, size, _BLOCK):
            ctx.checkpoint()
            if not np.isfinite(signal.values[start:start + _BLOCK]).all():
                raise ValueError('El fading requiere muestras finitas.')
        result = np.zeros(count, dtype=np.complex128)
        realizations = []
        streams = np.random.SeedSequence(spec.seed).spawn(len(spec.paths))
        prepared = None if grid is None else grid.prepare(ctx)
        process = 'iid' if grid is None else 'clarke_spectral_v1'
        try:
            with np.errstate(over='raise', invalid='raise', under='ignore'):
                for index, (path, stream) in enumerate(zip(spec.paths, streams, strict=True)):
                    values, statistics = _realize_path(signal.values, result, path, stream, ctx, index, work,
                                                       grid, prepared)
                    metadata = channel_clock(signal, path.delay_samples, size)
                    metadata.update(operation='communications_fading_coefficients', amplitude_units='1',
                                    root_seed=spec.seed, spawn_key=list(stream.spawn_key), path=asdict(path),
                                    process=process, max_doppler_hz=spec.max_doppler_hz)
                    coefficients = Signal(values, signal.origin + path.delay_samples, units=signal.units,
                                          name=f'Coeficientes de fading {index + 1}', metadata=metadata)
                    realizations.append(FadingRealization(path, coefficients, statistics))
        except FloatingPointError as exc:
            raise FloatingPointError('El fading excede el rango numérico finito.') from exc

        ctx.checkpoint(90)
        metadata = deepcopy(signal.metadata)
        metadata.pop('core_provenance', None)
        metadata.update(clock)
        metadata.update(operation='communications_fading', communications_fading={
            'schema': 2, 'process': process, 'generator': 'PCG64', 'numpy_version': np.__version__,
            'spectral_bins': None if grid is None else grid.bins,
            'coherence_seconds': None if grid is None else grid.coherence_seconds,
            'scipy_version': None if grid is None else scipy_version,
            'specification': asdict(spec), 'source_sha256': source_hash,
        })
        output = signal.copy_with(values=result, metadata=metadata, expression='', name='Salida con fading')
        output._core_verification = (content_digest(output, ctx.checkpoint), (source_hash,), None)
        ctx.checkpoint(100)
        verify_inputs((signal,), (source_hash,), ctx.checkpoint)
    return FadingResult(output, spec, tuple(realizations))
