"""Marginal empirical and theoretical densities for one fading path."""

import cmath
from dataclasses import dataclass
import math

import numpy as np
from scipy.special import erfcx, i0e, ndtr

from .communications_data import integer
from .execution import ExecutionContext
from .operation_provenance import content_digest, verify_inputs


_BLOCK = 65_536
_PRECISION = 1024 * np.finfo(float).eps


@dataclass(frozen=True, slots=True, eq=False)
class DensityComparison:
    edges: np.ndarray
    empirical: np.ndarray
    reference_axis: np.ndarray
    theoretical: np.ndarray

    def document(self):
        return {name: getattr(self, name).tolist() for name in (
            'edges', 'empirical', 'reference_axis', 'theoretical',
        )}


@dataclass(frozen=True, slots=True, eq=False)
class FadingDistributions:
    envelope: DensityComparison
    phase: DensityComparison
    sample_count: int
    average_power: float
    k_linear: float
    phase_reference_rad: float
    source_sha256: str
    notes: tuple[str, ...]

    def document(self):
        return {
            'schema': 1, 'operation': 'communications_fading_distributions',
            'sample_count': self.sample_count, 'average_power': self.average_power,
            'k_linear': self.k_linear, 'phase_reference_rad': self.phase_reference_rad,
            'source_sha256': self.source_sha256, 'notes': list(self.notes),
            'envelope': self.envelope.document(), 'phase': self.phase.document(),
        }


def _envelope_density(radius, mean, sigma):
    standardized = radius / sigma
    return (standardized / sigma * np.exp(-0.5 * ((radius - mean) / sigma)**2)
            * i0e(standardized * (mean / sigma)))


def _phase_density(angle, k):
    baseline = math.exp(-k) / math.tau
    eta = (math.sqrt(2) * math.sqrt(k)) * np.cos(angle)
    same_half = eta >= 0
    density = np.empty_like(angle)
    aligned = eta[same_half]
    density[same_half] = baseline + (
        aligned * np.exp(-k * np.sin(angle[same_half])**2) * ndtr(aligned) / math.sqrt(math.tau)
    )
    opposite = eta[~same_half]
    density[~same_half] = baseline * (1 + opposite * math.sqrt(math.pi / 2) * erfcx(-opposite / math.sqrt(2)))
    return density


def _comparison(samples, bins, observed_domain, reference_domain, density, ctx):
    # Locate the empirical and theoretical resolutions independently. An outlier
    # must not make the theoretical grid miss a narrow peak around the LOS.
    edges = np.linspace(*observed_domain, bins + 1)
    counts = np.zeros(bins, dtype=np.int64)
    for start in range(0, samples.size, _BLOCK):
        ctx.checkpoint()
        counts += np.histogram(samples[start:start + _BLOCK], bins=edges)[0]
    empirical = counts / samples.size / np.diff(edges)
    grid = np.linspace(*reference_domain, 513) if density is not None else np.empty(0)
    theoretical = density(grid) if density is not None else np.empty(0)
    for array in edges, empirical, grid, theoretical:
        array.setflags(write=False)
    return DensityComparison(edges, empirical, grid, theoretical)


def analyze_fading_distributions(realization, execution: ExecutionContext | None = None, *, bins=48):
    """Compare |a|/sqrt(P) and angle relative to the LOS with model marginals."""
    path, source = realization.path, realization.coefficients
    if not path.average_power:
        raise ValueError('Una trayectoria de potencia nula no tiene distribución normalizada ni fase.')
    bins = integer(bins, 'La cantidad de intervalos', minimum=4, maximum=128)
    ctx = execution or ExecutionContext()
    size = source.values.size
    k = path.k_linear
    sigma = 1 / math.sqrt(2) / math.sqrt(1 + k)
    mean = math.sqrt(k / (1 + k))
    phase_reference = path.los_phase_rad if k else 0.0
    reference = cmath.rect(1, phase_reference)
    notes = []
    fd = source.metadata.get('max_doppler_hz')
    if fd == 0:
        notes.append('Doppler máximo cero. La distribución teórica describe el conjunto de realizaciones, '
                     'mientras que el registro repite un único coeficiente.')
    elif fd is not None:
        notes.append('El registro contiene muestras correlacionadas. Su histograma puede apartarse de la distribución marginal.')

    with ctx.reserve(16 * size + 72 * min(_BLOCK, size) + 32_768):
        digest = content_digest(source, ctx.checkpoint)
        envelope, phase = np.empty(size), np.empty(size)
        scale = math.sqrt(path.average_power)
        for start in range(0, size, _BLOCK):
            ctx.checkpoint(50 * start // size)
            span = slice(start, start + _BLOCK)
            values = source.values[span]
            envelope[span] = np.abs(values) / scale
            angles = np.angle(values * reference.conjugate())
            phase[span] = np.where(angles >= math.pi, angles - math.tau, angles)
        if not np.isfinite(envelope).all() or not np.isfinite(phase).all():
            raise ValueError('El diagnóstico requiere coeficientes normalizados finitos.')
        ctx.checkpoint(50)
        radial_width = max(8 * sigma, _PRECISION)
        radial_domain = max(0.0, mean - radial_width), mean + radial_width
        angular_width = math.pi if k <= 10 else min(math.pi, max(8 * sigma / mean, _PRECISION))
        angular_domain = -angular_width, angular_width
        resolved = 8 * sigma >= _PRECISION
        if not resolved:
            notes.append('La dispersión del modelo queda por debajo de la resolución de esta representación. '
                         'Se conserva el histograma observado.')
        radius = _comparison(envelope, bins,
                             (min(radial_domain[0], float(envelope.min())),
                              max(radial_domain[1], float(envelope.max()))), radial_domain,
                             (lambda grid: _envelope_density(grid, mean, sigma)) if resolved else None, ctx)
        ctx.checkpoint(75)
        angle = _comparison(phase, bins,
                            (min(angular_domain[0], float(phase.min())),
                             max(angular_domain[1], float(phase.max()))), angular_domain,
                            (lambda grid: _phase_density(grid, k)) if resolved else None, ctx)
        verify_inputs((source,), (digest,), ctx.checkpoint)
        ctx.checkpoint(100)
    return FadingDistributions(radius, angle, size, path.average_power, k, phase_reference, digest, tuple(notes))
