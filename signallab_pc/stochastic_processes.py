"""Exact sampled transitions and theory for elementary stochastic processes."""

from collections.abc import Mapping
from dataclasses import dataclass
import math
from types import MappingProxyType

import numpy as np
from scipy.signal import lfilter

from .communications_data import MAX_SEED, integer, real
from .execution import ExecutionContext
from .model import Signal
from .operation_provenance import content_digest, settings_digest
from .probability import _scalar, probability_vector
from .realization_batch import store_batch
from .resources import ensure_working_set
from .spectral_scaling import bounded, restore_scalar
from .system_clock import CLOCK_MAPPING, validate_clock_resolution


PROCESSES = {
    'random_walk': ('Caminata gaussiana', ('initial', 'drift', 'std')),
    'wiener': ('Wiener con deriva', ('initial', 'drift', 'std')),
    'poisson_process': ('Proceso de Poisson', ('initial', 'event_rate')),
    'ornstein_uhlenbeck': ('Ornstein–Uhlenbeck', ('initial', 'mean', 'reversion', 'std')),
    'telegraph': ('Telegráfico', ('initial', 'low', 'high', 'rate_up', 'rate_down')),
    'markov': ('Cadena de Markov', ('initial', 'transition')),
}
PHYSICAL_PROCESSES = frozenset(('wiener', 'poisson_process', 'ornstein_uhlenbeck', 'telegraph'))
_MAX_INDEX = (1 << 63) - 1
_MAX_COUNT = (1 << 53) - 1
_BLOCK = 8192


def _stationary(transition):
    size = len(transition)
    system = np.vstack((transition.T - np.eye(size), np.ones(size)))
    target = np.zeros(size + 1)
    target[-1] = 1.
    probabilities, _, rank, _ = np.linalg.lstsq(system, target, rcond=None)
    if rank < size or min(probabilities) < -1e-12:
        return None
    probabilities = np.maximum(probabilities, 0)
    probabilities /= np.sum(probabilities)
    if not np.allclose(probabilities @ transition, probabilities, rtol=0, atol=1e-12):
        return None
    return probabilities


def _markov_parameters(parameters):
    matrix = parameters['transition']
    if (not isinstance(matrix, (list, tuple, np.ndarray))
            or isinstance(matrix, np.ndarray) and matrix.ndim != 2 or len(matrix) < 2):
        raise ValueError('La cadena requiere una matriz de al menos dos estados.')
    ensure_working_set(len(matrix)**2, bytes_per_sample=32, live_arrays=6)
    if any(not isinstance(row, (list, tuple, np.ndarray)) or np.ndim(row) != 1 or len(row) != len(matrix) for row in matrix):
        raise ValueError('La matriz de transición debe ser cuadrada.')
    matrix = tuple(probability_vector(row) for row in matrix)
    initial = parameters['initial']
    if isinstance(initial, str) and initial == 'stationary':
        if _stationary(np.asarray(matrix)) is None:
            raise ValueError('Indicá un estado o distribución inicial. La cadena no tiene una estacionaria única resoluble.')
    elif isinstance(initial, (list, tuple, np.ndarray)):
        if np.ndim(initial) != 1 or len(initial) != len(matrix):
            raise ValueError('La distribución inicial debe cubrir todos los estados.')
        initial = probability_vector(initial)
    else:
        initial = integer(initial, 'Estado inicial', minimum=0, maximum=len(matrix)-1)
    return {'initial': initial, 'transition': matrix}


@dataclass(frozen=True, slots=True)
class Process:
    family: str
    parameters: Mapping

    def __post_init__(self):
        if self.family not in PROCESSES:
            raise ValueError('Proceso estocástico desconocido.')
        _, keys = PROCESSES[self.family]
        if not isinstance(self.parameters, Mapping) or set(self.parameters) != set(keys):
            raise ValueError('Parámetros requeridos: ' + ', '.join(keys))
        if self.family == 'markov':
            parameters = _markov_parameters(self.parameters)
        else:
            parameters = {}
            for key in keys:
                value = self.parameters[key]
                if key == 'initial' and self.family in ('telegraph', 'ornstein_uhlenbeck') and value is None:
                    parameters[key] = None
                elif key == 'initial' and self.family in ('telegraph', 'poisson_process'):
                    maximum = 1 if self.family == 'telegraph' else _MAX_COUNT
                    parameters[key] = integer(value, 'Estado inicial', minimum=0, maximum=maximum)
                else:
                    lower = 0 if key in ('std', 'event_rate', 'rate_up', 'rate_down') else None
                    parameters[key] = real(value, key, minimum=lower, positive=key == 'reversion')
            if self.family == 'telegraph':
                if parameters['low'] >= parameters['high']:
                    raise ValueError('El nivel bajo debe ser menor que el alto.')
                real(parameters['rate_up'] + parameters['rate_down'], 'Suma de tasas', positive=True)
        object.__setattr__(self, 'parameters', MappingProxyType(parameters))

    def document(self):
        parameters = dict(self.parameters)
        if self.family == 'markov':
            parameters['transition'] = [list(row) for row in parameters['transition']]
            if isinstance(parameters['initial'], tuple):
                parameters['initial'] = list(parameters['initial'])
        return {'schema': 1, 'process': self.family, 'parameters': parameters}


def _sampling_rate(model, rate):
    if not isinstance(model, Process):
        raise ValueError('Seleccioná un modelo de proceso estocástico.')
    if rate is None and model.family not in PHYSICAL_PROCESSES:
        return None
    return real(rate, 'Frecuencia de muestreo (Hz)', positive=True)


def _time(step, rate):
    return real(step / rate if rate is not None else step, 'Tiempo transcurrido', minimum=0)


def _decay(reversion, span):
    product = reversion * span
    return math.exp(-product), -math.expm1(-product)


def _ou_spread(parameters, span=None):
    reversion, spread = parameters['reversion'], parameters['std']
    if span is None:
        return spread / (math.sqrt(2) * math.sqrt(reversion))
    product = reversion * span
    if product == 0:
        return spread * math.sqrt(span)
    if product < .5:
        return spread * math.sqrt(span) * math.sqrt(-math.expm1(-2 * product) / (2 * product))
    return (spread / (math.sqrt(2) * math.sqrt(reversion))) * math.sqrt(-math.expm1(-2 * product))


def _unit_state(index, size):
    weights = np.zeros(size)
    weights[index] = 1.
    return weights


def _state_config(model):
    p = model.parameters
    if model.family == 'telegraph':
        total = p['rate_up'] + p['rate_down']
        equilibrium = np.asarray([p['rate_down']/total, p['rate_up']/total])
        initial = equilibrium if p['initial'] is None else _unit_state(p['initial'], 2)
        return np.asarray([p['low'], p['high']]), initial, equilibrium
    matrix = np.asarray(p['transition'])
    equilibrium = _stationary(matrix)
    initial = p['initial']
    if isinstance(initial, tuple):
        weights = np.asarray(initial)
    elif initial == 'stationary':
        weights = equilibrium
    else:
        weights = _unit_state(initial, len(matrix))
    return np.arange(len(matrix), dtype=float), weights, equilibrium


def _transition(model, steps, rate, checkpoint):
    p = model.parameters
    if model.family == 'telegraph':
        total = p['rate_up'] + p['rate_down']
        _, loss = _decay(total, _time(steps, rate))
        up, down = (p[key]/total * loss for key in ('rate_up', 'rate_down'))
        return np.asarray([[1-up, up], [down, 1-down]])
    base = np.asarray(p['transition'])
    power = np.eye(len(base))
    while steps:
        checkpoint()
        if steps & 1:
            power = power @ base
            power /= power.sum(axis=1, keepdims=True)
        steps >>= 1
        if steps:
            base = base @ base
            base /= base.sum(axis=1, keepdims=True)
    return power


def _state_memory(model):
    return 192 * len(model.parameters['transition'])**2 if model.family == 'markov' else 4096


def process_transition(model, steps, *, rate=None, execution=None):
    """Describe the conditional law after a specified number of sampled steps."""
    rate = _sampling_rate(model, rate)
    steps = integer(steps, 'Pasos de transición', minimum=0, maximum=_MAX_INDEX)
    p, name = model.parameters, model.family
    context = execution or ExecutionContext()
    context.checkpoint()
    result = {'schema': 1, 'steps': steps, 'sample_rate_hz': rate}
    if name in ('telegraph', 'markov'):
        with context.reserve(_state_memory(model)):
            levels, initial, invariant = _state_config(model)
            result.update(model=model.document(), transition=_transition(model, steps, rate, context.checkpoint).tolist(),
                          state_values=levels.tolist(), initial_distribution=initial.tolist(),
                          stationary_distribution=None if invariant is None else invariant.tolist())
    else:
        result['model'] = model.document()
        span = _time(steps, rate if name != 'random_walk' else None)
        if name == 'ornstein_uhlenbeck':
            phi, loss = _decay(p['reversion'], span)
            result.update(law='normal', state_coefficient=phi, location_increment=_scalar(loss*p['mean']),
                          conditional_std=_scalar(_ou_spread(p, span)), stationary_std=_scalar(_ou_spread(p)))
        elif name == 'poisson_process':
            result.update(law='poisson_increment', event_mean=_scalar(p['event_rate']*span))
        else:
            result.update(law='normal', state_coefficient=1., location_increment=_scalar(p['drift']*span),
                          conditional_std=_scalar(p['std']*math.sqrt(span)))
    context.checkpoint()
    return result


def _finite_state_moments(model, first, second, rate, checkpoint):
    values, initial, _ = _state_config(model)
    p1 = initial @ _transition(model, first, rate, checkpoint)
    transition = _transition(model, second - first, rate, checkpoint)
    p2 = p1 @ transition
    scaled, exponent = bounded(values, normalize=True)
    coordinate = scaled.real
    mean1, mean2 = float(p1 @ coordinate), float(p2 @ coordinate)
    x, y = coordinate - mean1, coordinate - mean2
    var1, var2 = float(p1 @ (x*x)), float(p2 @ (y*y))
    covariance = float((p1*x) @ (transition @ y))
    if model.family == 'telegraph':
        stationary = (model.parameters['initial'] is None or
                      model.parameters['initial'] == 0 and model.parameters['rate_up'] == 0 or
                      model.parameters['initial'] == 1 and model.parameters['rate_down'] == 0)
    else:
        stationary = np.allclose(initial @ _transition(model, 1, rate, checkpoint), initial, atol=1e-13, rtol=0)
    means = [restore_scalar(value, exponent) for value in (mean1, mean2)]
    return means, [restore_scalar(value, 2*exponent) for value in (var1, var2)], restore_scalar(covariance, 2*exponent), stationary


def process_moments(model, first, second, *, rate=None, execution=None):
    """Marginal moments and cross-time covariance at zero-based path offsets."""
    rate = _sampling_rate(model, rate)
    offsets = [integer(i, 'Desplazamiento temporal', minimum=0, maximum=_MAX_INDEX) for i in (first, second)]
    a, b = sorted(offsets)
    p, family = model.parameters, model.family
    context = execution or ExecutionContext()
    context.checkpoint()
    if family in ('telegraph', 'markov'):
        with context.reserve(_state_memory(model)):
            document = model.document()
            means, variances, covariance, stationary = _finite_state_moments(model, a, b, rate, context.checkpoint)
    else:
        document = model.document()
        times = [_time(k, rate if family != 'random_walk' else None) for k in (a, b)]
        if family == 'ornstein_uhlenbeck':
            stationary = p['initial'] is None or p['std'] == 0 and p['initial'] == p['mean']
            mean = p['mean']
            spread = [_ou_spread(p, None if p['initial'] is None else t) for t in times]
            means = ([mean, mean] if p['initial'] is None else
                     [math.fsum((phi*p['initial'], loss*mean)) for phi, loss in
                      (_decay(p['reversion'], t) for t in times)])
            variances = [sigma*sigma for sigma in spread]
            root_phi = math.exp(-.5*p['reversion']*_time(b-a, rate))
            scaled_spread = spread[0]*root_phi if root_phi else 0.
            covariance = scaled_spread*scaled_spread
        elif family == 'poisson_process':
            variances = [p['event_rate']*t for t in times]
            means = [p['initial']+value for value in variances]
            covariance, stationary = variances[0], p['event_rate'] == 0
        else:
            means = [math.fma(p['drift'], t, p['initial']) for t in times]
            spreads = [p['std']*math.sqrt(t) for t in times]
            variances = [sigma*sigma for sigma in spreads]
            covariance, stationary = variances[0], p['drift'] == 0 and p['std'] == 0
    if a != offsets[0]:
        means.reverse()
        variances.reverse()
    context.checkpoint()
    return {'schema': 1, 'model': document, 'offsets': offsets, 'sample_rate_hz': rate,
            'means': list(map(_scalar, means)), 'variances': list(map(_scalar, variances)),
            'covariance': _scalar(covariance), 'stationary_initialization': bool(stationary),
            'scope': 'Propiedades teóricas del modelo. La estacionariedad y la ergodicidad empíricas requieren supuestos adicionales.'}


def _simulate(model, count, rate, rng, context, state_config):
    family, p = model.family, model.parameters
    values = np.empty(count, dtype=float)
    if family in ('telegraph', 'markov'):
        levels, initial, cdf = state_config
        state = int(rng.choice(len(initial), p=initial))
        values[0] = levels[state]
        for start in range(1, count, _BLOCK):
            context.checkpoint()
            stop = min(count, start + _BLOCK)
            for i, draw in enumerate(rng.random(stop-start), start):
                state = int(np.searchsorted(cdf[state], draw, side='right'))
                values[i] = levels[state]
        return values

    step = _time(1, rate if family != 'random_walk' else None)
    if family == 'ornstein_uhlenbeck':
        phi, _ = _decay(p['reversion'], step)
        spread = real(_ou_spread(p, step), 'Desviación de la transición', minimum=0)
        mean = p['mean']
        current = (0. if p['initial'] is not None else
                   rng.normal(scale=real(_ou_spread(p), 'Desviación estacionaria', minimum=0)))
        values[0] = current+mean if p['initial'] is None else p['initial']
    elif family == 'poisson_process':
        intensity = real(p['event_rate']*step, 'Media por incremento', minimum=0, maximum=_MAX_COUNT)
        current = values[0] = p['initial']
    else:
        drift = real(p['drift']*step, 'Deriva por incremento')
        spread = real(p['std']*math.sqrt(step), 'Desviación por incremento', minimum=0)
        current = values[0] = p['initial']
    for start in range(1, count, _BLOCK):
        context.checkpoint()
        stop = min(count, start + _BLOCK)
        length = stop-start
        if family == 'ornstein_uhlenbeck':
            block, _ = lfilter([1.], [1., -phi], spread*rng.standard_normal(length), zi=[phi*current])
            current = block[-1]
            if p['initial'] is None or p['initial'] == mean:
                expected = mean
            else:
                # Evolve the deterministic mean separately so a tiny return
                # rate is visible even when the one-step coefficient rounds to 1.
                times = np.arange(start, stop, dtype=float)*step
                elapsed = p['reversion']*times
                expected = np.exp(-elapsed)*p['initial'] - np.expm1(-elapsed)*mean
            values[start:stop] = block + expected
        else:
            increments = (rng.poisson(intensity, length) if family == 'poisson_process'
                          else drift + spread*rng.standard_normal(length))
            values[start:stop] = current + np.cumsum(increments, dtype=float)
            current = values[stop-1]
            if family == 'poisson_process' and current > _MAX_COUNT:
                raise FloatingPointError('El recuento acumulado excede la representación entera exacta.')
    return values


def generate_process(model, count, seed, *, replicas=1, origin=0, rate=None, execution=None):
    """Generate complete paths with the initial state at the first sample."""
    context = execution or ExecutionContext()
    rate = _sampling_rate(model, rate)
    count = integer(count, 'Observaciones', maximum=_MAX_INDEX)
    replicas = integer(replicas, 'Réplicas', maximum=_MAX_INDEX)
    seed = integer(seed, 'Semilla', minimum=0, maximum=MAX_SEED)
    origin = integer(origin, 'Índice inicial', minimum=-_MAX_INDEX-1, maximum=_MAX_INDEX-count+1)
    if rate is not None:
        validate_clock_resolution(0., rate, count)
    output = []
    estimate = (16*count*replicas + 32*count + 96*min(count, _BLOCK) + _state_memory(model) + 2048*replicas)
    with context.reserve(estimate):
        document = model.document()
        metadata = {'schema': 1, 'operation': 'stochastic_process', 'model': document,
                    'settings_sha256': settings_digest(document), 'generator': 'PCG64', 'seed': seed,
                    'numpy_version': np.__version__, 'draw_block_size': _BLOCK}
        if rate is not None:
            metadata.update(sample_rate_hz=rate, time_start_s=0., time_mapping=CLOCK_MAPPING)
        state_config = None
        if model.family in ('markov', 'telegraph'):
            levels, initial, _ = _state_config(model)
            cdf = np.maximum.accumulate(np.minimum(1., np.cumsum(_transition(model, 1, rate, context.checkpoint), axis=1)), axis=1)
            cdf[:, -1] = 1.
            state_config = levels, initial, cdf
        for index in range(replicas):
            context.checkpoint()
            rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(seed, spawn_key=(index,))))
            with np.errstate(over='ignore', invalid='ignore'):
                values = _simulate(model, count, rate, rng, context, state_config)
            title = f'{PROCESSES[model.family][0]} · realización {index+1}'
            record = Signal(values, origin=origin, name=title, metadata={**metadata, 'substream': [index]})
            record._realization_digest = content_digest(record, context.checkpoint)
            output.append(record)
        context.checkpoint()
    return tuple(output)


def store_processes(project, document, records, execution=None, *, tool=None):
    return store_batch(project, document, records, execution, title='Proceso generador',
                       operation='Modelo de proceso estocástico', tool=tool)
