"""Descriptive statistics for an explicitly selected projection of a record."""

import math

import numpy as np

from .communications_data import integer, real
from .execution import ExecutionContext
from .model import Signal
from .operation_provenance import content_digest, verify_inputs
from .probability import Distribution, distribution_value
from .spectral_scaling import bounded, centered_bounded, range_status, restore_scalar


PROJECTIONS = ('real', 'imag', 'magnitude', 'phase')


def project_samples(source: Signal, component):
    """Return finite real observations and the count excluded by the projection."""
    if not isinstance(source, Signal):
        raise ValueError('Se requiere un registro SignalLab.')
    values = source.values
    if component == 'real':
        return values.real, 0
    if component == 'imag':
        return values.imag, 0
    if component == 'magnitude':
        with np.errstate(over='ignore'):
            result = np.hypot(values.real, values.imag)
        if not np.isfinite(result).all():
            raise ValueError('El módulo de algunas observaciones excede el rango de float64.')
        return result, 0
    if component == 'phase':
        valid = values != 0
        if not np.any(valid):
            raise ValueError('El registro no contiene muestras con fase definida.')
        result = np.angle(values[valid])
        return result, len(values) - len(result)
    raise ValueError('Componente estadística desconocida.')


def _measure(value, exponent=0, *factors):
    real_value = restore_scalar(value, exponent, *factors)
    status = range_status(real_value, value)
    return {'value': real_value if status != 'overflow' else None,
            'status': 'finite' if status == 'ok' else status}


def _quantile(sorted_values, probability):
    rank = probability * (len(sorted_values) - 1)
    left, right = math.floor(rank), math.ceil(rank)
    fraction = rank - left
    a, b = float(sorted_values[left]), float(sorted_values[right])
    if a == b:
        return a
    _, scale = math.frexp(max(abs(a), abs(b)))
    lower, upper = math.ldexp(a, -scale), math.ldexp(b, -scale)
    weighted = (math.fma(fraction, upper - lower, lower) if fraction <= .5
                else math.fma(1 - fraction, lower - upper, upper))
    return restore_scalar(weighted, scale)


def _boxplot(sorted_values, lower, middle, upper):
    width = upper - lower
    first = int(np.searchsorted(sorted_values, lower - 1.5 * width, side='left'))
    end = int(np.searchsorted(sorted_values, upper + 1.5 * width, side='right'))
    return {
        'quartiles': [_measure(value) for value in (lower, middle, upper)],
        'whiskers': [_measure(sorted_values[index]) for index in (first, end - 1)],
        'outliers': first + len(sorted_values) - end,
        'rule': 'Tukey, 1.5 IQR',
    }


def _circular(values):
    phase_vector = np.exp(1j * values).mean()
    length = min(1., abs(phase_vector))
    direction = (_measure(np.angle(phase_vector)) if length > 16 * np.finfo(float).eps
                 else {'value': None, 'status': 'undefined'})
    return {'mean_direction_rad': direction, 'resultant_length': _measure(length),
            'circular_variance': _measure(1 - length)}


def _empirical(values, counts, count, context, reference, reference_points):
    cumulative = np.cumsum(counts)
    data = {'x': values.tolist(), 'cdf': (cumulative / count).tolist(),
            'survival': ((count - cumulative) / count).tolist()}
    if reference is not None:
        indices = np.rint(np.linspace(0, len(values) - 1, min(reference_points, len(values)))).astype(np.int64)
        x = values[indices]
        cdf, survival = [], []
        for value in x:
            context.checkpoint()
            cdf.append(distribution_value(reference, 'cdf', value))
            survival.append(distribution_value(reference, 'survival', value))
        data.update(reference_axis=x.tolist(), reference_cdf=cdf, reference_survival=survival)
    return data


def _qq(values, counts, reference, count, limit, context):
    ranks = np.unique(np.rint(np.linspace(0, count - 1, min(limit, count))).astype(np.int64))
    positions = (ranks + .5) / count
    observed = values[np.searchsorted(np.cumsum(counts), ranks, side='right')]
    theoretical = []
    for probability in positions:
        context.checkpoint()
        theoretical.append(distribution_value(reference, 'quantile', probability))
    return {'probabilities': positions.tolist(), 'observed': observed.tolist(),
            'theoretical': theoretical, 'total_order_statistics': count,
            'plotting_position': '(i + 0.5)/N, zero-based rank i'}


def describe_record(source: Signal, component='real', *,
                    probabilities=(.05, .25, .5, .75, .95), diagnostics=False,
                    reference: Distribution | None = None, qq_points=257,
                    execution: ExecutionContext | None = None):
    """Population-divisor moments of a finite observation, with optional diagnostics."""
    if not isinstance(source, Signal):
        raise ValueError('Se requiere un registro SignalLab.')
    probabilities = tuple(real(value, 'Cuantil', minimum=0, maximum=1) for value in probabilities)
    if not probabilities:
        raise ValueError('Se requiere al menos una probabilidad para los cuantiles.')
    if reference is not None and not isinstance(reference, Distribution):
        raise ValueError('La referencia debe ser una distribución univariada.')
    qq_points = integer(qq_points, 'Puntos Q–Q')
    context = execution or ExecutionContext()
    size = len(source.values)
    estimate = (112 if not diagnostics else 240) * size + 512 * (len(probabilities) + min(qq_points, size))
    with context.reserve(estimate):
        checksum = content_digest(source, context.checkpoint)
        observed, missing = project_samples(source, component)
        samples = observed.astype(np.complex128)
        scaled, exponent = bounded(samples, normalize=True)
        centered, center_exponent = centered_bounded(samples)
        count = len(observed)
        scaled, centered = scaled.real, centered.real
        baseline = float(np.mean(centered**2))
        raw_std = math.sqrt(baseline)
        moments = [1., 0., baseline, float(np.mean(centered**3)), float(np.mean(centered**4))]
        population_variance = _measure(baseline, 2 * center_exponent)
        sample_variance = (_measure(baseline, 2 * center_exponent, count / (count - 1))
                           if count > 1 else {'value': None, 'status': 'undefined'})
        context.checkpoint()
        sorted_observed = np.sort(observed)
        lower, median, upper = (_quantile(sorted_observed, q) for q in (.25, .5, .75))
        with np.errstate(over='ignore'):
            deviations = abs(observed - median)
        if np.isfinite(deviations).all():
            mad = _measure(_quantile(np.sort(deviations), .5))
        else:
            deviations = abs(scaled - math.ldexp(median, -exponent))
            mad = _measure(_quantile(np.sort(deviations), .5), exponent)
        try:
            mean = _measure(math.fsum(observed) / count)
        except OverflowError:
            mean = _measure(math.fsum(scaled) / count, exponent)
        unique, multiplicities = np.unique(observed, return_counts=True)
        largest = int(multiplicities.max())
        modes = unique[multiplicities == largest] if largest > 1 else np.empty(0)
        result = {
            'schema': 1, 'operation': 'descriptive_statistics', 'component': component,
            'units': 'rad' if component == 'phase' else source.metadata.get('amplitude_units', ''),
            'sample_count': count, 'excluded': missing, 'input_sha256': checksum,
            'clock_sample_rate_hz': source.metadata.get('sample_rate_hz'),
            'mean': mean,
            'median': _measure(median),
            'variance_N': population_variance, 'variance_N_minus_1': sample_variance,
            'standard_deviation_N': _measure(raw_std, center_exponent),
            'rms': _measure(math.sqrt(float(np.mean(scaled**2))), exponent),
            'raw_moments': [_measure(1.), mean] + [
                _measure(float(np.mean(scaled**power)), exponent * power) for power in range(2, 5)
            ],
            'central_moments': [_measure(value, center_exponent * power) for power, value in enumerate(moments)],
            'skewness': _measure(moments[3] / raw_std**3) if raw_std else {'value': None, 'status': 'undefined'},
            'excess_kurtosis': (_measure(moments[4] / baseline**2 - 3)
                                if baseline else {'value': None, 'status': 'undefined'}),
            'quantiles': [{'probability': q, **_measure(_quantile(sorted_observed, q))}
                          for q in probabilities],
            'quantile_method': 'linear',
            'iqr': _measure(upper - lower), 'mad': mad,
            'mode': {'values': modes.tolist(), 'multiplicity': largest,
                     'status': 'finite' if largest > 1 else 'no_repeated_value'},
            'scope': ('Estadísticas de la proyección observada. Los momentos usan divisor N. '
                      'El divisor N−1 estima varianza bajo el modelo de observaciones IID.'),
        }
        if component == 'phase':
            result['circular'] = _circular(observed)
            result['scope'] += (' La fase usa la rama principal en radianes. Se excluyen los ceros '
                                'y se informan aparte las medidas circulares.')
        if diagnostics:
            result['empirical'] = _empirical(unique, multiplicities, count, context, reference, qq_points)
            result['boxplot'] = _boxplot(sorted_observed, lower, median, upper)
            if reference is not None:
                result['reference'] = reference.document()
                result['qq'] = _qq(unique, multiplicities, reference, count, qq_points, context)
        verify_inputs((source,), (checksum,), context.checkpoint)
        context.checkpoint()
    return result
