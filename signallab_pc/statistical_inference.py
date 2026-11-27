"""Inference for explicit real projections of SignalLab records."""

from dataclasses import dataclass
from fractions import Fraction
import math

import numpy as np
from scipy import stats
from scipy.special import betaincinv, betainccinv

from .communications_data import integer, real
from .descriptive_statistics import project_samples
from .execution import ExecutionContext
from .model import Signal
from .operation_provenance import content_digest, verify_inputs
from .probability import Distribution, _scalar, _tail
from .random_signals import autocorrelation
from .spectral_scaling import bounded, centered_bounded, exact_real_mean, finite_real_mean, restore_scalar


METHODS = {
    'z': 'Media · Z con σ conocida', 't': 'Media · t de Student', 'variance': 'Varianza · χ²',
    'proportion': 'Proporción · binomial exacta', 'welch': 'Diferencia de medias · t de Welch',
    'f': 'Cociente de varianzas · F', 'ks': 'Kolmogorov–Smirnov · referencia conocida',
    'ad': 'Anderson–Darling · normalidad', 'shapiro': 'Shapiro–Wilk · normalidad',
    'ljung_box': 'Ljung–Box · autocorrelación', 'mann_whitney': 'Mann–Whitney · rangos',
}
TWO_SAMPLES = frozenset(('welch', 'f', 'mann_whitney'))
NULL_PARAMETER = frozenset(('z', 't', 'variance', 'proportion', 'welch', 'f'))
FIT_FAMILIES = {
    'normal': ('ml', 'moments'), 'lognormal': ('ml',), 'exponential': ('ml', 'moments'),
    'rayleigh': ('ml', 'moments'), 'uniform': ('ml', 'moments'), 'gamma': ('ml', 'moments'),
    'beta': ('ml', 'moments'), 'bernoulli': ('ml', 'moments'), 'binomial': ('ml', 'moments'),
    'poisson': ('ml', 'moments'), 'laplace': ('ml', 'moments'),
}
FIT_INTERVALS = frozenset(('normal', 'lognormal', 'exponential', 'rayleigh', 'poisson', 'bernoulli', 'binomial'))


@dataclass(frozen=True, slots=True)
class _Spread:
    mean: float
    square_sum: float
    exponent: int
    count: int

    @property
    def std_scaled(self):
        return math.sqrt(self.square_sum / (self.count - 1))


def _spread(values, checkpoint):
    mean = finite_real_mean(values, checkpoint)
    centered, exponent = centered_bounded(values)
    return _Spread(mean, float(np.sum(centered.real**2)), exponent, len(values))


def _unit(value, label, *, open_interval=True):
    value = real(value, label, minimum=0, maximum=1)
    if open_interval and value in (0, 1):
        raise ValueError(f'{label} debe estar estrictamente entre 0 y 1.')
    return value


def _sum_quantities(*terms, divide=1):
    """Sum at most four binary quantities without losing terms during cancellation."""
    total = sum(Fraction(value) * Fraction(2)**exponent for value, exponent in terms) / Fraction(divide)
    try:
        return float(total)
    except OverflowError:
        return math.inf if total > 0 else -math.inf


def _ratio(numerator, denominator, exponent):
    fraction, shift = math.frexp(denominator)
    return restore_scalar(numerator / fraction, exponent - shift)


def _tail_test(law, statistic, alternative):
    if alternative == 'less':
        return float(law.logcdf(statistic))
    if alternative == 'greater':
        return float(law.logsf(statistic))
    left, right = float(law.logcdf(statistic)), float(law.logsf(statistic))
    if math.isnan(left) or math.isnan(right):
        return math.nan
    return min(0., math.log(2) + min(left, right))


def _mean_case(data, other, method, null, known_std, tail, observations, checkpoint):
    if method == 'z':
        std, exponent = math.frexp(real(known_std, 'Desviación conocida', positive=True))
        error = std / math.sqrt(data.count)
        law, degrees = stats.norm(), None
    elif method == 't':
        error = data.std_scaled / math.sqrt(data.count)
        exponent, degrees = data.exponent, data.count - 1
        law = stats.t(degrees)
    else:
        first_scale = data.std_scaled / math.sqrt(data.count)
        second_scale = other.std_scaled / math.sqrt(other.count)
        exponent = max(e for s, e in ((first_scale, data.exponent), (second_scale, other.exponent)) if s) if (
            first_scale or second_scale
        ) else 0
        first = math.ldexp(first_scale, data.exponent - exponent)
        second = math.ldexp(second_scale, other.exponent - exponent)
        error = math.hypot(first, second)
        if not error:
            raise ValueError('La diferencia de medias tiene error estándar nulo.')
        degrees = 1 / ((first / error)**4 / (data.count - 1) + (second / error)**4 / (other.count - 1))
        law = stats.t(degrees)
    if not error:
        raise ValueError('La varianza muestral es nula. La prueba t no tiene estadístico definido.')
    baseline = ((data.mean, 0),) if other is None else ((data.mean, 0), (-other.mean, 0))
    # Rounding a mean before subtracting H₀ can erase a real contrast.
    offset = _sum_quantities(*baseline, (-null, 0))
    uncertainty = 4 * max(math.ulp(value) for value, _ in baseline)
    if abs(offset) <= uncertainty:
        baseline = tuple(((-1)**index * exact_real_mean(sample, checkpoint), 0)
                         for index, sample in enumerate(observations))
    normalized = [(value, power - exponent) for value, power in (*baseline, (-null, 0))]
    statistic = _sum_quantities(*normalized, divide=error)
    margin = float(law.isf(tail)) * error
    return (law, statistic, _sum_quantities(*baseline),
            [_sum_quantities(*baseline, ((-1)**sign * margin, exponent)) for sign in (1, 0)], degrees)


def _variance_case(data, other, null, tail):
    if other is None:
        law, degrees = stats.chi2(data.count - 1), [data.count - 1]
        denominator = null
        numerator = data.square_sum
        exponent = 2 * data.exponent
        factor = numerator
        estimate = restore_scalar(numerator / degrees[0], exponent)
    else:
        if not other.square_sum or not data.square_sum:
            raise ValueError('El cociente F requiere dos varianzas muestrales positivas.')
        degrees = [data.count - 1, other.count - 1]
        law = stats.f(*degrees)
        numerator = data.square_sum / degrees[0]
        denominator = other.square_sum / degrees[1]
        exponent = 2 * (data.exponent - other.exponent)
        factor = numerator / denominator
        estimate = restore_scalar(factor, exponent)
        numerator = factor
        denominator = null
    statistic = _ratio(numerator, denominator, exponent)
    bounds = [_ratio(factor, float(critical), exponent) for critical in (law.isf(tail), law.ppf(tail))]
    return law, statistic, estimate, bounds, degrees


def _binomial_interval(successes, count, tail):
    lower = 0. if successes == 0 else float(betaincinv(successes, count - successes + 1, tail))
    upper = 1. if successes == count else float(betainccinv(successes + 1, count - successes, tail))
    return lower, upper


def _proportion(values, null, alternative, tail):
    if np.any((values != 0) & (values != 1)):
        raise ValueError('La proporción requiere observaciones Bernoulli 0 o 1.')
    count, successes = len(values), int(np.count_nonzero(values))
    lower, upper = _binomial_interval(successes, count, tail)
    test = stats.binomtest(successes, count, p=_unit(null, 'Proporción nula', open_interval=False),
                          alternative=alternative)
    return {'statistic': _scalar(successes), 'estimate': _scalar(test.statistic),
            'interval': [_scalar(lower), _scalar(upper)], 'successes': successes,
            'p_value': float(test.pvalue), 'calibration': 'binomial exacta; intervalo Clopper–Pearson bilateral'}


def _distribution_test(values, method, reference, context):
    if method == 'ks':
        if not isinstance(reference, Distribution) or reference.discrete:
            raise ValueError('KS requiere una distribución continua con parámetros fijados antes del muestreo.')
        if np.unique(values).size != values.size:
            raise ValueError('El KS continuo exacto requiere una muestra sin empates.')
        probabilities = []
        for value in np.sort(values):
            context.checkpoint()
            probabilities.append(_tail(reference, 'cdf', value))
        if not np.isfinite(probabilities).all():
            raise ValueError('La CDF de referencia no pudo evaluarse en toda la muestra.')
        positions = np.arange(1, len(values) + 1)
        statistic = max(np.max(positions / len(values) - probabilities),
                        np.max(np.asarray(probabilities) - (positions - 1) / len(values)))
        return float(statistic), float(stats.kstwo.sf(statistic, len(values))), 'KS bilateral exacto'
    if np.all(values == values[0]):
        raise ValueError('Las pruebas de normalidad requieren un registro no constante.')
    centered, _ = centered_bounded(values)
    # Both normality statistics are invariant to shifts and positive rescaling.
    if method == 'ad':
        test = stats.anderson(centered.real, dist='norm', method='interpolate')
        return float(test.statistic), float(test.pvalue), 'normal con parámetros libres; p interpolado'
    test = stats.shapiro(centered.real)
    note = 'normal con parámetros libres; para N > 5000, p tiene exactitud limitada'
    return float(test.statistic), float(test.pvalue), note


def _coordinates(source, component):
    return {'amplitude_units': 'rad' if component == 'phase' else source.metadata.get('amplitude_units', ''),
            'axis_units': source.units, 'domain': source.domain, 'origin': source.origin, 'step': source.step,
            'sample_rate_hz': source.metadata.get('sample_rate_hz')}


def infer_record(source: Signal, method: str, *, iid: bool, component='real', second=None,
                 null=None, level=.95, alternative='two-sided', known_std=None,
                reference=None, lags=None, fitted_parameters=None, execution=None):
    """Inference about declared independent observations. Ljung–Box tests a white-noise null."""
    if method not in METHODS or alternative not in ('two-sided', 'less', 'greater'):
        raise ValueError('Método o alternativa estadística desconocida.')
    if iid is not True:
        raise ValueError('Confirmá el modelo de observaciones independientes para interpretar el valor p.')
    if method not in NULL_PARAMETER and method != 'mann_whitney' and alternative != 'two-sided':
        raise ValueError('Este diagnóstico global usa una alternativa bilateral fija.')
    if (null is not None and method not in NULL_PARAMETER or known_std is not None and method != 'z'
        or reference is not None and method != 'ks'
        or (lags is not None or fitted_parameters is not None) and method != 'ljung_box'):
        raise ValueError('Un parámetro indicado no corresponde al contraste seleccionado.')
    if not isinstance(source, Signal) or ((method in TWO_SAMPLES) != (second is not None)) or (
        second is not None and not isinstance(second, Signal)
    ):
        raise ValueError('Seleccioná la cantidad de registros que requiere el método.')
    if method in NULL_PARAMETER:
        null = real(null, 'Valor de la hipótesis nula', positive=method in ('variance', 'f'))
    level = _unit(level, 'Nivel de confianza')
    alpha = 1 - level
    context = execution or ExecutionContext()
    inputs = (source,) if second is None else (source, second)
    with context.reserve(128 * sum(len(item.values) for item in inputs)):
        hashes = tuple(content_digest(item, context.checkpoint) for item in inputs)
        coordinates = [_coordinates(item, component) for item in inputs]
        if second is source:
            raise ValueError('Los contrastes de dos muestras requieren registros distintos e independientes.')
        if second is not None and coordinates[0]['amplitude_units'] != coordinates[1]['amplitude_units']:
            raise ValueError('Compará dos registros con las mismas unidades de amplitud.')
        projected = [project_samples(item, component) for item in inputs]
        values, excluded = projected[0]
        other = projected[1][0] if second is not None else None
        minimum = {'t': 2, 'welch': 2, 'f': 2, 'variance': 2, 'shapiro': 3, 'ad': 5}.get(method, 1)
        if any(len(data) < minimum for data, _ in projected):
            raise ValueError(f'El método requiere al menos {minimum} observaciones por registro.')
        result = {
            'schema': 1, 'operation': 'statistical_inference', 'method': method,
            'component': component, 'input_hashes': list(hashes), 'sample_counts': [len(x) for x, _ in projected],
            'excluded': [n for _, n in projected], 'iid_assumed': True, 'level': level, 'alpha': alpha,
            'null_value': null, 'alternative': alternative, 'inputs': coordinates,
        }
        if method in ('z', 't', 'welch', 'variance', 'f'):
            data = _spread(values, context.checkpoint)
            compare = _spread(other, context.checkpoint) if other is not None else None
            case = (_mean_case(data, compare, method, null, known_std, alpha / 2,
                               [sample for sample, _ in projected], context.checkpoint)
                    if method in ('z', 't', 'welch') else _variance_case(data, compare, null, alpha / 2))
            law, statistic, estimate, bounds, degrees = case
            log_p = _tail_test(law, statistic, alternative)
            result.update(statistic=_scalar(statistic), estimate=_scalar(estimate), interval=list(map(_scalar, bounds)),
                          p_value=math.exp(log_p), log_p_value=_scalar(log_p, infinite='zero_or_underflow'),
                          degrees_of_freedom=degrees, calibration='normalidad IID; intervalo bilateral con grados de libertad aproximados'
                          if method == 'welch' else 'normalidad IID; intervalo bilateral')
            if method == 'z':
                result['known_std'] = float(known_std)
        elif method == 'proportion':
            result.update(_proportion(values, null, alternative, alpha / 2))
        elif method == 'mann_whitney':
            combined = np.r_[values, other]
            exact = min(len(values), len(other)) <= 8 and np.unique(combined).size == combined.size
            test = stats.mannwhitneyu(values, other, alternative=alternative, method='exact' if exact else 'asymptotic')
            result.update(statistic=_scalar(test.statistic), p_value=float(test.pvalue),
                          calibration='rangos exactos sin empates' if exact else 'aproximación con corrección de empates',
                          null_description='ambas poblaciones tienen la misma distribución')
        elif method == 'ljung_box':
            if excluded or source.domain != 'discrete':
                raise ValueError('Ljung–Box requiere un registro discreto contiguo sin observaciones excluidas.')
            lag = integer(10 if lags is None else lags, 'Retardos', maximum=len(values) - 1)
            fitted = integer(0 if fitted_parameters is None else fitted_parameters, 'Parámetros ajustados', minimum=0, maximum=lag - 1)
            rho = autocorrelation(Signal(values), lag, remove_mean=True, normalize=True, method='auto', execution=context)
            # autocorrelation returns a symmetric Signal centered at lag zero.
            positive = rho.values[lag + 1:].real
            statistic = len(values) * (len(values) + 2) * np.sum(positive**2 / (len(values) - np.arange(1, lag + 1)))
            result.update(statistic=_scalar(statistic), p_value=float(stats.chi2.sf(statistic, lag - fitted)),
                          lags=lag, fitted_parameters=fitted, degrees_of_freedom=lag - fitted,
                          calibration='χ² asintótica; en muestras cortas puede ser pobre',
                          null_description='autocorrelaciones nulas para los retardos examinados')
        else:
            statistic, probability, calibration = _distribution_test(values, method, reference, context)
            result.update(statistic=_scalar(statistic), p_value=probability, calibration=calibration,
                          null_description='referencia continua con parámetros conocidos' if method == 'ks'
                          else 'normalidad con parámetros libres')
            if method == 'ks':
                result['reference'] = reference.document()
            if method == 'ad' and probability in (.01, .15):
                # SciPy's asymptotic table clamps both tails of its interpolation.
                result['p_value_relation'] = 'at_most' if probability == .01 else 'at_least'
        if not 0 <= result['p_value'] <= 1:
            raise ValueError('El valor p no pudo evaluarse en este rango numérico.')
        result['reject_null'] = result['p_value'] < alpha
        if result.get('p_value_relation') == 'at_most' and not result['reject_null'] or (
            result.get('p_value_relation') == 'at_least' and result['reject_null']
        ):
            result['reject_null'] = None
        result['scope'] = ('El valor p se calcula suponiendo la hipótesis nula y el modelo de muestreo. '
                           'La falta de rechazo no demuestra la hipótesis nula.')
        if component == 'phase':
            result['scope'] += ' El contraste usa los valores lineales de fase en la rama principal.'
        verify_inputs(inputs, hashes, context.checkpoint)
        context.checkpoint()
    return result


def _fit_parameters(values, family, estimator, trials, checkpoint):
    data = _spread(values, checkpoint)
    scale = restore_scalar(math.sqrt(data.square_sum / data.count), data.exponent)
    if family == 'normal':
        return {'mean': data.mean, 'std': scale}
    if family in ('bernoulli', 'binomial', 'poisson'):
        if np.any((values < 0) | (values != np.floor(values))):
            raise ValueError('El ajuste de recuentos requiere enteros no negativos.')
        if family == 'poisson':
            return {'rate': data.mean}
        maximum = 1 if family == 'bernoulli' else integer(trials, 'Ensayos binomiales')
        if np.any(values > maximum):
            raise ValueError('Un recuento excede la cantidad de ensayos por observación.')
        estimate = {'p': data.mean / maximum}
        return estimate if family == 'bernoulli' else {'trials': maximum, **estimate}
    if family == 'uniform':
        if estimator == 'ml':
            return {'low': float(np.min(values)), 'high': float(np.max(values))}
        width = math.sqrt(3) * scale
        return {'low': data.mean - width, 'high': data.mean + width}
    if family == 'laplace':
        if estimator == 'moments':
            return {'location': data.mean, 'scale': scale / math.sqrt(2)}
        scaled, power = bounded(values, normalize=True)
        median = float(np.median(scaled.real))
        width = math.fsum(abs(scaled.real - median)) / len(values)
        return {'location': restore_scalar(median, power), 'scale': restore_scalar(width, power)}
    strictly_positive = family in ('lognormal', 'gamma', 'beta') or family == 'rayleigh' and estimator == 'ml'
    if np.any(values < 0) or strictly_positive and np.any(values == 0):
        raise ValueError('Las observaciones están fuera del soporte del ajuste.')
    if family == 'exponential':
        return {'scale': data.mean}
    if family == 'rayleigh':
        if estimator == 'moments':
            return {'scale': data.mean / math.sqrt(math.pi / 2)}
        scaled, power = bounded(values, normalize=True)
        return {'scale': restore_scalar(math.sqrt(float(np.mean(scaled.real**2)) / 2), power)}
    if family == 'lognormal':
        logs = _spread(np.log(values), checkpoint)
        return {'log_mean': logs.mean, 'log_std': restore_scalar(math.sqrt(logs.square_sum / logs.count), logs.exponent)}

    if family == 'beta' and np.any(values >= 1):
        raise ValueError('El ajuste Beta requiere observaciones estrictamente entre 0 y 1.')
    if scale == 0:
        raise ValueError('El ajuste de forma y escala requiere un registro no constante.')
    if estimator == 'moments':
        if family == 'gamma':
            relative = data.mean / scale
            return {'shape': relative * relative, 'scale': scale / relative}
        concentration = data.mean * (1 - data.mean) / (scale * scale) - 1
        return {'alpha': data.mean * concentration, 'beta': (1 - data.mean) * concentration}
    if family == 'beta':
        alpha, beta, _, _ = stats.beta.fit(values, floc=0, fscale=1)
        return {'alpha': alpha, 'beta': beta}
    scaled, power = bounded(values, normalize=True)
    shape, _, width = stats.gamma.fit(scaled.real, floc=0)
    return {'shape': shape, 'scale': restore_scalar(width, power)}


def _parameter_intervals(model, values, level, context):
    family = model.family
    tail = (1 - level) / 2
    count = len(values)
    if family in ('normal', 'lognormal'):
        values = np.log(values) if family == 'lognormal' else values
        data = _spread(values, context.checkpoint)
        degrees = count - 1
        margin = float(stats.t.isf(tail, degrees)) * data.std_scaled / math.sqrt(count)
        location = [_sum_quantities((data.mean, 0), (sign * margin, data.exponent)) for sign in (-1, 1)]
        scale = [restore_scalar(math.sqrt(data.square_sum / bound), data.exponent)
                 for bound in (stats.chi2.isf(tail, degrees), stats.chi2.ppf(tail, degrees))]
        prefix = 'log_' if family == 'lognormal' else ''
        bounds = {prefix+'mean': location, prefix+'std': scale}
        method = 'pivotes t y χ² para observaciones normales'
    elif family in ('exponential', 'rayleigh'):
        quantiles = (stats.chi2.isf(tail, 2 * count), stats.chi2.ppf(tail, 2 * count))
        if family == 'exponential':
            bounds = {'scale': [restore_scalar(model.parameters['scale'], 0, 2 * count / q) for q in quantiles]}
        else:
            scaled, exponent = bounded(values, normalize=True)
            sum_squares = float(np.sum(scaled.real**2))
            bounds = {'scale': [restore_scalar(math.sqrt(2 * sum_squares / q), exponent) for q in quantiles]}
        method = 'pivote χ² con ubicación cero conocida'
    else:
        successes = 0
        for offset in range(0, count, 8192):
            context.checkpoint()
            successes += sum(map(int, values[offset:offset + 8192]))
        total_trials = count * model.parameters.get('trials', 1)
        if max(successes, total_trials) >= 2**53:
            raise ValueError('El recuento agregado excede el rango entero exacto del intervalo.')
        if family == 'poisson':
            lower = stats.chi2.ppf(tail, 2 * successes) / (2 * count) if successes else 0.
            upper = stats.chi2.isf(tail, 2 * (successes + 1)) / (2 * count)
            bounds = {'rate': (lower, upper)}
            method = 'intervalo exacto de Garwood para una tasa por observación'
        else:
            bounds = {'p': _binomial_interval(successes, total_trials, tail)}
            method = 'intervalo exacto de Clopper–Pearson para los ensayos agregados'
    return {'level': level, 'method': method,
            'parameters': {key: list(map(_scalar, limits)) for key, limits in bounds.items()}}


def fit_distribution(source: Signal, family, *, component='real', estimator='ml',
                     trials=None, level=None, iid=False, execution=None):
    """Fit one supported marginal, keeping estimated parameters separate from a fixed null."""
    if family not in FIT_FAMILIES or estimator not in FIT_FAMILIES[family]:
        raise ValueError('La familia y el estimador elegidos no tienen un ajuste implementado.')
    if trials is not None and family != 'binomial':
        raise ValueError('La cantidad de ensayos solo corresponde al ajuste binomial.')
    if level is not None:
        if family not in FIT_INTERVALS or iid is not True:
            raise ValueError('El intervalo requiere una familia compatible y observaciones independientes.')
        level = _unit(level, 'Nivel de confianza')
    if not isinstance(source, Signal):
        raise ValueError('Seleccioná un registro de observaciones.')
    context = execution or ExecutionContext()
    with context.reserve(112 * len(source.values)):
        checksum = content_digest(source, context.checkpoint)
        values, excluded = project_samples(source, component)
        if len(values) < 2:
            raise ValueError('El ajuste requiere al menos dos observaciones.')
        try:
            parameters = _fit_parameters(values, family, estimator, trials, context.checkpoint)
            model = Distribution(family, parameters)
        except (RuntimeError, ArithmeticError) as error:
            raise ValueError('El ajuste no convergió dentro del rango numérico.') from error
        context.checkpoint()
        log_value = model._backend.logpmf if model.discrete else model._backend.logpdf
        term = np.asarray(log_value(values))
        if np.any(np.isneginf(term)):
            likelihood = {'value': None, 'status': 'zero_joint_likelihood'}
        elif np.isfinite(term).all():
            likelihood = _scalar(math.fsum(term))
        else:
            likelihood = {'value': None, 'status': 'numerically_unavailable'}
        report = {'schema': 1, 'operation': 'distribution_fit', 'component': component,
                  'input_hashes': [checksum], 'sample_counts': [len(values)], 'excluded': [excluded],
                  'inputs': [_coordinates(source, component)],
                  'estimator': estimator, 'estimated_distribution': model.document(),
                  'log_likelihood': likelihood, 'parameters_from_same_sample': True,
                  'scope': ('Estimación sobre la muestra elegida. La referencia ajustada no cumple '
                            'el supuesto de parámetros fijados de antemano del KS exacto.')}
        if component == 'phase':
            report['scope'] += ' El ajuste usa los valores lineales de fase en la rama principal.'
        if level is not None:
            report['confidence_intervals'] = _parameter_intervals(model, values, level, context)
        verify_inputs((source,), (checksum,), context.checkpoint)
        context.checkpoint()
        return report
