"""Probability laws and reproducible sampled records, independent of Qt."""

from collections.abc import Mapping
from dataclasses import dataclass, field
import math
from types import MappingProxyType

import numpy as np
from scipy import __version__ as scipy_version, stats

from .communications_data import MAX_SEED, integer, real
from .execution import ExecutionContext
from .model import Signal
from .operation_provenance import content_digest, settings_digest
from .realization_batch import store_batch
from .system_clock import CLOCK_MAPPING, validate_clock_resolution


_BLOCK = 65_536
_MAX_EXACT_INTEGER = 1 << 53
_MAX_AXIS_INDEX = (1 << 63) - 1


@dataclass(frozen=True, slots=True)
class Family:
    label: str
    backend: str
    parameters: tuple[tuple[str, str, str], ...]
    discrete: bool = False


# Each parameter has a public name, a SciPy keyword and a domain.
FAMILIES = MappingProxyType({
    'bernoulli': Family('Bernoulli', 'bernoulli', (('p', 'p', 'probability'),), True),
    'binomial': Family('Binomial', 'binom', (('trials', 'n', 'count'), ('p', 'p', 'probability')), True),
    'negative_binomial': Family('Binomial negativa', 'nbinom', (
        ('successes', 'n', 'positive_count'), ('p', 'p', 'positive_probability')), True),
    'poisson': Family('Poisson', 'poisson', (('rate', 'mu', 'nonnegative'),), True),
    'geometric': Family('Geométrica', 'geom', (('p', 'p', 'positive_probability'),), True),
    'hypergeometric': Family('Hipergeométrica', 'hypergeom', (
        ('population', 'M', 'positive_count'), ('successes', 'n', 'count'), ('draws', 'N', 'count')), True),
    'discrete_uniform': Family('Uniforme discreta', 'randint', (
        ('low', 'low', 'integer'), ('high', 'high', 'integer')), True),
    'categorical': Family('Categórica', 'rv_discrete', (('probabilities', 'probabilities', 'vector'),), True),
    'uniform': Family('Uniforme continua', 'uniform', (('low', 'loc', 'real'), ('high', 'scale', 'real'))),
    'normal': Family('Normal', 'norm', (('mean', 'loc', 'real'), ('std', 'scale', 'positive'))),
    'exponential': Family('Exponencial', 'expon', (('scale', 'scale', 'positive'),)),
    'gamma': Family('Gamma', 'gamma', (('shape', 'a', 'positive'), ('scale', 'scale', 'positive'))),
    'beta': Family('Beta', 'beta', (('alpha', 'a', 'positive'), ('beta', 'b', 'positive'))),
    'rayleigh': Family('Rayleigh', 'rayleigh', (('scale', 'scale', 'positive'),)),
    'rician': Family('Rician', 'rice', (('ratio', 'b', 'nonnegative'), ('scale', 'scale', 'positive'))),
    'nakagami': Family('Nakagami', 'nakagami', (('shape', 'nu', 'nakagami'), ('scale', 'scale', 'positive'))),
    'weibull': Family('Weibull', 'weibull_min', (('shape', 'c', 'positive'), ('scale', 'scale', 'positive'))),
    'lognormal': Family('Lognormal', 'lognorm', (
        ('log_mean', 'scale', 'real'), ('log_std', 's', 'positive'))),
    'chi_square': Family('Chi-cuadrado', 'chi2', (('df', 'df', 'positive'),)),
    'student_t': Family('Student t', 't', (('df', 'df', 'positive'),)),
    'f': Family('F', 'f', (('df_num', 'dfn', 'positive'), ('df_den', 'dfd', 'positive'))),
    'laplace': Family('Laplace', 'laplace', (('location', 'loc', 'real'), ('scale', 'scale', 'positive'))),
    'cauchy': Family('Cauchy', 'cauchy', (('location', 'loc', 'real'), ('scale', 'scale', 'positive'))),
})


def probability_vector(values):
    if not isinstance(values, (list, tuple, np.ndarray)) or np.ndim(values) != 1 or not len(values):
        raise ValueError('Indicá un vector de probabilidades.')
    values = tuple(real(value, 'Cada probabilidad', minimum=0, maximum=1) for value in values)
    total = math.fsum(values)
    if not math.isclose(total, 1, rel_tol=0, abs_tol=8 * math.ulp(1.0)):
        raise ValueError('Las probabilidades deben sumar uno.')
    return tuple(value / total for value in values)


def _parameter(value, label, rule):
    if rule == 'vector':
        return probability_vector(value)
    if rule in {'integer', 'count', 'positive_count'}:
        lower = {'integer': -_MAX_EXACT_INTEGER + 1, 'count': 0, 'positive_count': 1}[rule]
        return integer(value, label, minimum=lower, maximum=_MAX_EXACT_INTEGER - 1)
    minimum = {'probability': 0, 'nonnegative': 0, 'nakagami': .5}.get(rule)
    return real(value, label, minimum=minimum,
                maximum=1 if rule.endswith('probability') else None,
                positive=rule in {'positive', 'positive_probability'})


def _law(name, family, values):
    kwargs = {target: values[key] for key, target, _ in family.parameters}
    if name == 'categorical':
        masses = values['probabilities']
        points = np.flatnonzero(masses)
        return stats.rv_discrete(values=(points, np.asarray(masses)[points]))
    if name == 'hypergeometric' and max(values['draws'], values['successes']) > values['population']:
        raise ValueError('Los éxitos y las extracciones deben caber en la población.')
    if name in {'uniform', 'discrete_uniform'}:
        if values['high'] < values['low'] or name == 'uniform' and values['high'] == values['low']:
            raise ValueError('Los límites de la distribución uniforme no son válidos.')
        if family.discrete:
            kwargs['high'] += 1  # The public upper end is inclusive.
        else:
            kwargs['scale'] = real(values['high'] - values['low'], 'Ancho', positive=True)
    if name == 'lognormal':
        try:
            kwargs['scale'] = math.exp(values['log_mean'])
        except OverflowError:
            raise ValueError('La escala lognormal excede el rango numérico.') from None
        if not kwargs['scale']:
            raise ValueError('La escala lognormal queda por debajo del rango numérico.')
    if name == 'rician' and values['ratio'] == 0:
        return stats.rayleigh(scale=values['scale'])
    return getattr(stats, family.backend)(**kwargs)


@dataclass(frozen=True, slots=True)
class Distribution:
    family: str
    parameters: Mapping
    _backend: object = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        if not isinstance(self.family, str) or self.family not in FAMILIES:
            raise ValueError('Familia de distribución desconocida.')
        family = FAMILIES[self.family]
        if not isinstance(self.parameters, Mapping) or set(self.parameters) != {row[0] for row in family.parameters}:
            raise ValueError('Parámetros requeridos: ' + ', '.join(row[0] for row in family.parameters))
        values = {key: _parameter(self.parameters[key], key, rule) for key, _, rule in family.parameters}
        object.__setattr__(self, '_backend', _law(self.family, family, values))
        object.__setattr__(self, 'parameters', MappingProxyType(values))

    @property
    def discrete(self):
        return FAMILIES[self.family].discrete

    def document(self):
        return {'schema': 1, 'family': self.family, 'parameters': dict(self.parameters),
                'kind': 'mass' if self.discrete else 'density'}


def _scalar(value, *, infinite=None, nan='numerically_unavailable'):
    value = float(value)
    if math.isfinite(value):
        return {'value': value, 'status': 'finite'}
    if math.isnan(value):
        return {'value': None, 'status': nan}
    return {'value': None, 'status': infinite or 'out_of_range', 'sign': 1 if value > 0 else -1}


def _support(distribution):
    law, values = distribution._backend, distribution.parameters
    family = distribution.family
    low, high = law.support()
    if family in {'bernoulli', 'binomial'}:
        if values['p'] == 0:
            return 0, 0
        if values['p'] == 1:
            return high, high
    if (family in {'negative_binomial', 'geometric'} and values['p'] == 1) or (
        family == 'poisson' and values['rate'] == 0
    ):
        return low, low
    return low, high


def _tail(distribution, method, value):
    law = distribution._backend
    low, high = _support(distribution)
    upper = method in {'sf', 'logsf'}
    if value < low or value >= high or not distribution.discrete and value == low:
        probability = float((value >= high) != upper)
        if method.startswith('log'):
            return 0.0 if probability else -np.inf
        return probability
    if distribution.family == 'rician' and distribution.parameters['ratio']:
        # The Rice default survival subtracts the rounded CDF from one.
        # Its squared standardized radius follows noncentral chi-square.
        ratio, scale = distribution.parameters['ratio'], distribution.parameters['scale']
        with np.errstate(over='ignore', invalid='ignore'):
            square = np.square(np.float64(value) / scale)
            return getattr(stats.ncx2, method)(square, df=2, nc=np.square(ratio))
    return getattr(law, method)(value)


def distribution_value(distribution: Distribution, operation: str, argument):
    """Evaluate a scalar. The return document has no NaN or infinite JSON numbers."""
    law = distribution._backend
    if operation == 'quantile':
        probability = real(argument, 'Probabilidad', minimum=0, maximum=1)
        low, high = _support(distribution)
        if low == high:
            return _scalar(low)
        if probability in (0, 1):
            return _scalar(low if probability == 0 else high, infinite='unbounded')
        method, q = ('ppf', probability) if probability <= .5 else ('isf', 1 - probability)
        if distribution.family == 'rician' and distribution.parameters['ratio']:
            ratio, scale = distribution.parameters['ratio'], distribution.parameters['scale']
            with np.errstate(over='ignore', invalid='ignore'):
                return _scalar(scale * np.sqrt(getattr(stats.ncx2, method)(q, df=2, nc=np.square(ratio))))
        return _scalar(getattr(law, method)(q))
    value = real(argument, 'Punto de evaluación')
    if operation in ('density', 'log_density'):
        function = law.pmf if distribution.discrete else law.pdf
        low, high = _support(distribution)
        if operation == 'log_density':
            function = law.logpmf if distribution.discrete else law.logpdf
        result = function(value)
        reason = None
        if np.isposinf(result) and not distribution.discrete and value in (low, high):
            reason = 'singular_density'
        if np.isneginf(result) and operation == 'log_density':
            reason = 'zero_density' if value < low or value > high else 'zero_or_underflow'
        return _scalar(result, infinite=reason)
    methods = {'cdf': 'cdf', 'survival': 'sf', 'log_cdf': 'logcdf', 'log_survival': 'logsf'}
    if operation not in methods:
        raise ValueError('Operación de distribución desconocida.')
    result = _tail(distribution, methods[operation], value)
    if np.isneginf(result) and operation.startswith('log_'):
        low, high = _support(distribution)
        exact_zero = (value < low or not distribution.discrete and value == low
                      if operation == 'log_cdf' else value >= high)
        return _scalar(result, infinite='zero_probability' if exact_zero else 'zero_or_underflow')
    return _scalar(result)


def interval_probability(distribution: Distribution, low, high):
    """Closed interval, with the discrete lower tail evaluated below its first atom."""
    low = real(low, 'Extremo inferior')
    high = real(high, 'Extremo superior')
    if high < low:
        raise ValueError('El intervalo debe estar ordenado.')
    if distribution.discrete:
        low = math.ceil(low) - 1
        high = math.floor(high)
    support_low, support_high = _support(distribution)
    if high <= low or high < support_low or low >= support_high or (
        not distribution.discrete and high == support_low
    ):
        return {'value': 0.0, 'status': 'finite', 'log_value': None}
    if _tail(distribution, 'cdf', high) <= .5:
        first, second = _tail(distribution, 'logcdf', high), _tail(distribution, 'logcdf', low)
    else:
        first, second = _tail(distribution, 'logsf', low), _tail(distribution, 'logsf', high)
    if not (first <= 0 and second <= first):
        return {'value': None, 'status': 'numerically_unavailable', 'log_value': None}
    if first == second:
        return {'value': 0.0, 'status': 'zero_or_underflow', 'log_value': None}
    log_value = float(first + np.log(-np.expm1(second - first)))
    value = math.exp(log_value)
    return {'value': value, 'status': 'finite' if value else 'underflow', 'log_value': log_value}


def _moment_status(distribution, order):
    family, parameters = distribution.family, distribution.parameters
    if family == 'cauchy' or family == 'student_t' and parameters['df'] <= order:
        return 'undefined' if order % 2 else 'divergent'
    if family == 'f' and parameters['df_den'] <= 2 * order:
        return 'divergent'
    return None


def moment(distribution: Distribution, order):
    """Raw moment up to order four, with explicit divergence and numerical states."""
    order = integer(order, 'Orden del momento', minimum=0, maximum=4)
    if order == 0:
        return _scalar(1)
    low, high = _support(distribution)
    if low == high:
        return _scalar(float(low)**order)
    if reason := _moment_status(distribution, order):
        return {'value': None, 'status': reason}
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        return _scalar(distribution._backend.moment(order))


def population(distribution: Distribution):
    mean = moment(distribution, 1)
    low, high = _support(distribution)
    if low == high:
        variance = _scalar(0)
    elif mean['status'] in {'undefined', 'divergent'}:
        variance = {'value': None, 'status': 'undefined'}
    elif reason := _moment_status(distribution, 2):
        variance = {'value': None, 'status': reason}
    else:
        with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
            variance = _scalar(distribution._backend.var())
    return {'distribution': distribution.document(), 'mean': mean, 'variance': variance,
            'support': [_scalar(low, infinite='unbounded'), _scalar(high, infinite='unbounded')]}


def _sample_records(draw, document, label, count, seed, replicas, origin, rate, execution, *,
                    dimensions, discrete, dtype):
    count = integer(count, 'Cantidad de muestras', maximum=_MAX_AXIS_INDEX)
    seed = integer(seed, 'Semilla', minimum=0, maximum=MAX_SEED)
    replicas = integer(replicas, 'Réplicas', maximum=_MAX_AXIS_INDEX)
    origin = integer(origin, 'Índice inicial', minimum=-_MAX_AXIS_INDEX - 1, maximum=_MAX_AXIS_INDEX)
    if origin + count - 1 > _MAX_AXIS_INDEX:
        raise ValueError('El eje excede el rango de índices de 64 bits.')
    clock = {}
    if rate is not None:
        rate = real(rate, 'Frecuencia de muestreo', positive=True)
        validate_clock_resolution(0.0, rate, count)
        clock.update(sample_rate_hz=rate, time_start_s=0.0, time_mapping=CLOCK_MAPPING)
    context = execution or ExecutionContext()
    metadata = {'operation': 'probability_realization', 'schema': 1, 'distribution': document,
                'settings_sha256': settings_digest(document), 'seed': seed, 'generator': 'PCG64',
                'numpy_version': np.__version__, 'scipy_version': scipy_version,
                'draw_block_size': _BLOCK, **clock}
    output = []
    estimate = dimensions * (16 * count * (replicas + 2) + 64 * min(count, _BLOCK) + 2048 * replicas)
    with context.reserve(estimate):
        for index in range(replicas):
            rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(seed, spawn_key=(index,))))
            samples = np.empty((dimensions, count), dtype=dtype)
            for start in range(0, count, _BLOCK):
                context.checkpoint()
                stop = min(start + _BLOCK, count)
                block = draw(rng, stop - start)
                if discrete and np.any((block < -_MAX_EXACT_INTEGER) | (block > _MAX_EXACT_INTEGER)):
                    raise FloatingPointError('Una muestra discreta excede la representación entera exacta.')
                samples[:, start:stop] = block.reshape(-1, dimensions).T
            for column in range(dimensions):
                name = f'{label} · realización {index + 1}'
                if dimensions > 1:
                    name += f' · componente {column + 1}'
                record = Signal(samples[column], origin=origin, name=name,
                                metadata={**metadata, 'substream': [index], 'component': column})
                record._realization_digest = content_digest(record, context.checkpoint)
                output.append(record)
        context.checkpoint()
    return tuple(output)


def generate_realizations(distribution: Distribution, count, seed, *, replicas=1,
                          origin=0, rate=None, execution: ExecutionContext | None = None):
    """Draw independent records using addressable PCG64 substreams."""
    def draw(rng, size):
        return distribution._backend.rvs(size=size, random_state=rng)

    return _sample_records(draw, distribution.document(), FAMILIES[distribution.family].label,
                           count, seed, replicas, origin, rate, execution,
                           dimensions=1, discrete=distribution.discrete, dtype=np.float64)


def store_realizations(project, document, records, execution: ExecutionContext | None = None, *, tool=None):
    """Register the law and its complete batch with verified parent links."""
    return store_batch(project, document, records, execution, title='Distribución generadora',
                       operation='Modelo de probabilidad', tool=tool)
