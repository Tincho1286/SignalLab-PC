"""Joint Gaussian and multinomial laws with explicit covariance conventions."""

from dataclasses import dataclass, field
import math

import numpy as np
from scipy import stats

from .communications_data import integer
from .execution import ExecutionContext
from .probability import Distribution, _MAX_EXACT_INTEGER, _sample_records, _scalar, probability_vector


def _array(values, ndim, label, complex_allowed):
    try:
        data = np.asarray(values, dtype=np.complex128)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(f'{label}: se esperaba un arreglo numérico.') from exc
    if data.ndim != ndim or not data.size or not np.isfinite(data).all():
        raise ValueError(f'{label}: dimensiones o valores no válidos.')
    if complex_allowed:
        return data
    if np.any(data.imag):
        raise ValueError(f'{label}: el modelo real requiere valores reales.')
    return data.real


def _snapshot(values):
    copy = np.asarray(values)
    return np.frombuffer(copy.tobytes(), dtype=copy.dtype).reshape(copy.shape)


def _parts(values):
    if values.dtype.kind == 'c':
        return {'real': values.real.tolist(), 'imag': values.imag.tolist()}
    return values.tolist()


def _scale(values):
    return float(max(np.max(abs(values.real)), np.max(abs(values.imag))))


def _symmetric(values, *, hermitian):
    transposed = values.conj().T if hermitian else values.T
    scale = _scale(values)
    tolerance = 16 * max(values.shape) * np.finfo(float).eps
    if scale and np.max(abs(values / scale - transposed / scale)) > tolerance:
        raise ValueError('La covarianza debe ser hermítica y la pseudocovarianza, simétrica.')
    return values * .5 + transposed * .5 if scale > 1 else (values + transposed) * .5


def _factor(covariance):
    scale = _scale(covariance)
    if scale == 0:
        return np.zeros((len(covariance), 0)), np.empty(0), np.zeros((len(covariance), 0))
    values, vectors = np.linalg.eigh(covariance / scale)
    tolerance = 8 * len(covariance) * np.finfo(float).eps * max(abs(values))
    if values[0] < -tolerance:
        raise ValueError('La covarianza debe ser semidefinida positiva.')
    active = values > tolerance
    sigmas = np.sqrt(values[active]) * math.sqrt(scale)
    directions = vectors[:, active]
    return directions * sigmas, sigmas, directions


@dataclass(frozen=True, slots=True, eq=False)
class Gaussian:
    mean: object
    covariance: object
    complex_model: bool = False
    pseudocovariance: object = None
    _location: np.ndarray = field(init=False, repr=False)
    _root: np.ndarray = field(init=False, repr=False)
    _standard_deviation: np.ndarray = field(init=False, repr=False)
    _directions: np.ndarray = field(init=False, repr=False)

    def __post_init__(self):
        if type(self.complex_model) is not bool:
            raise ValueError('Indicá si el modelo gaussiano es real o complejo.')
        mean = _array(self.mean, 1, 'Media', self.complex_model)
        covariance = _array(self.covariance, 2, 'Covarianza', self.complex_model)
        shape = (mean.size, mean.size)
        if covariance.shape != shape:
            raise ValueError('La covarianza debe tener una fila y columna por componente.')
        covariance = _symmetric(covariance, hermitian=True)
        pseudo = None
        if self.complex_model:
            pseudo = (np.zeros(shape, dtype=np.complex128) if self.pseudocovariance is None
                      else _array(self.pseudocovariance, 2, 'Pseudocovarianza', True))
            if pseudo.shape != shape:
                raise ValueError('La pseudocovarianza debe tener la misma forma que la covarianza.')
            pseudo = _symmetric(pseudo, hermitian=False)
            cross = (pseudo.imag * .5 - covariance.imag * .5)
            real_covariance = np.block([
                [covariance.real * .5 + pseudo.real * .5, cross],
                [cross.T, covariance.real * .5 - pseudo.real * .5],
            ])
            location = np.r_[mean.real, mean.imag]
        else:
            if self.pseudocovariance is not None:
                raise ValueError('La pseudocovarianza corresponde a un modelo complejo.')
            real_covariance, location = covariance, mean
        with ExecutionContext().reserve(80 * real_covariance.size):
            root, sigmas, directions = _factor(real_covariance)
        object.__setattr__(self, 'mean', _snapshot(mean))
        object.__setattr__(self, 'covariance', _snapshot(covariance))
        object.__setattr__(self, 'pseudocovariance', None if pseudo is None else _snapshot(pseudo))
        object.__setattr__(self, '_location', _snapshot(location))
        object.__setattr__(self, '_root', _snapshot(root))
        object.__setattr__(self, '_standard_deviation', _snapshot(sigmas))
        object.__setattr__(self, '_directions', _snapshot(directions))

    def document(self):
        pseudo = self.pseudocovariance
        return {'schema': 1, 'family': 'multivariate_normal', 'complex': self.complex_model,
                'mean': _parts(self.mean), 'covariance': _parts(self.covariance),
                'pseudocovariance': None if pseudo is None else _parts(pseudo),
                'dimension': self.mean.size, 'real_rank': self._root.shape[1]}


def _indices(indices, dimension):
    try:
        output = tuple(integer(value, 'Componente', minimum=0, maximum=dimension - 1) for value in indices)
    except TypeError as exc:
        raise ValueError('Indicá los índices de las componentes.') from exc
    if not output or len(set(output)) != len(output):
        raise ValueError('Seleccioná componentes distintas.')
    return list(output)


def _coordinates(model, observation, size):
    vector = _array(observation, 1, 'Observación', model.complex_model)
    if vector.size != size:
        raise ValueError('La observación debe coincidir con las componentes elegidas.')
    return np.r_[vector.real, vector.imag] if model.complex_model else vector


def gaussian_density(model: Gaussian, observation):
    """Density with respect to Lebesgue measure in real coordinates."""
    vector = _coordinates(model, observation, model.mean.size)
    if model._root.shape[1] != vector.size:
        return {'density': {'value': None, 'status': 'singular_measure'},
                'log_density': {'value': None, 'status': 'singular_measure'}}
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        whitened = ((vector - model._location) @ model._directions) / model._standard_deviation
        log_density = float(-.5 * (vector.size * math.log(math.tau) + whitened @ whitened)
                            - np.log(model._standard_deviation).sum())
        density = float(np.exp(log_density))
    return {'density': _scalar(density) if density else {'value': 0.0, 'status': 'underflow'},
            'log_density': _scalar(log_density)}


def gaussian_marginal(model: Gaussian, components):
    indices = _indices(components, model.mean.size)
    pairs = np.ix_(indices, indices)
    pseudo = model.pseudocovariance
    return Gaussian(model.mean[indices], model.covariance[pairs], model.complex_model,
                    None if pseudo is None else pseudo[pairs])


def _from_real_location(location, covariance, complex_model):
    if not complex_model:
        return Gaussian(location, covariance)
    size = len(location) // 2
    real, imag = covariance[:size, :size], covariance[size:, size:]
    cross = covariance[:size, size:]
    return Gaussian(location[:size] + 1j * location[size:],
                    (real + imag) + 1j * (cross.T - cross), True,
                    (real - imag) + 1j * (cross + cross.T))


def gaussian_condition(model: Gaussian, observed, values, execution: ExecutionContext | None = None):
    """Condition using the null space of the observed rows of a covariance factor."""
    dimension = model.mean.size
    selected = _indices(observed, dimension)
    remaining = [index for index in range(dimension) if index not in selected]
    if not remaining:
        raise ValueError('Debe quedar al menos una componente por estimar.')
    observation = _coordinates(model, values, len(selected))
    if model.complex_model:
        selected += [dimension + index for index in selected]
        remaining += [dimension + index for index in remaining]
    context = execution or ExecutionContext()
    with context.reserve(80 * model._root.size):
        design, target = model._root[selected], model._root[remaining]
        delta = observation - model._location[selected]
        left, singular, right = np.linalg.svd(design, full_matrices=True)
        tolerance = max(design.shape) * np.finfo(float).eps * (singular[0] if singular.size else 0)
        rank = int(np.count_nonzero(singular > tolerance))
        projected = left[:, :rank].T @ delta
        residual = delta - left[:, :rank] @ projected
        threshold = 32 * np.finfo(float).eps * max(design.shape) * max(
            _scale(delta), _scale(model._location[selected]), _scale(observation)
        )
        if _scale(residual) > threshold:
            raise ValueError('La observación está fuera del soporte del modelo.')
        location = model._location[remaining] + (target @ right[:rank].T) @ (projected / singular[:rank])
        residual_factor = target @ right[rank:].T
        covariance = residual_factor @ residual_factor.T
        context.checkpoint()
    return _from_real_location(location, covariance, model.complex_model)


def gaussian_transform(model: Gaussian, matrix, offset=None):
    linear = _array(matrix, 2, 'Transformación', model.complex_model)
    if linear.shape[1] != model.mean.size:
        raise ValueError('La transformación debe tener una columna por componente.')
    shift = 0 if offset is None else _array(offset, 1, 'Desplazamiento', model.complex_model)
    if offset is not None and len(shift) != linear.shape[0]:
        raise ValueError('El desplazamiento debe tener la dimensión de salida.')
    covariance = linear @ model.covariance @ linear.conj().T
    pseudo = model.pseudocovariance
    return Gaussian(linear @ model.mean + shift, covariance, model.complex_model,
                    None if pseudo is None else linear @ pseudo @ linear.T)


def generate_gaussian(model: Gaussian, count, seed, *, replicas=1, origin=0, rate=None,
                      execution: ExecutionContext | None = None):
    dimension = model.mean.size

    def draw(rng, size):
        coordinates = rng.standard_normal((size, model._root.shape[1])) @ model._root.T + model._location
        if model.complex_model:
            return coordinates[:, :dimension] + 1j * coordinates[:, dimension:]
        return coordinates

    return _sample_records(draw, model.document(), 'Normal multivariada', count, seed, replicas,
                           origin, rate, execution, dimensions=dimension, discrete=False,
                           dtype=np.complex128 if model.complex_model else np.float64)


@dataclass(frozen=True, slots=True)
class Multinomial:
    trials: int
    probabilities: tuple[float, ...]

    def __post_init__(self):
        object.__setattr__(self, 'trials', integer(self.trials, 'Ensayos', minimum=0,
                                                   maximum=_MAX_EXACT_INTEGER - 1))
        object.__setattr__(self, 'probabilities', probability_vector(self.probabilities))

    def document(self):
        return {'schema': 1, 'family': 'multinomial', 'trials': self.trials,
                'probabilities': self.probabilities}

    def population(self):
        p = np.asarray(self.probabilities)
        return {'distribution': self.document(), 'mean': (self.trials * p).tolist(),
                'covariance': (self.trials * (np.diag(p) - np.outer(p, p))).tolist()}

    def mass(self, counts):
        counts = _counts(counts, len(self.probabilities), self.trials)
        log_mass = stats.multinomial.logpmf(counts, self.trials, self.probabilities)
        return {'mass': _scalar(np.exp(log_mass)), 'log_mass': _scalar(log_mass, infinite='zero_probability')}

    def marginal(self, component):
        index = _indices([component], len(self.probabilities))[0]
        return Distribution('binomial', {'trials': self.trials, 'p': self.probabilities[index]})

    def condition(self, observed, counts):
        selected = _indices(observed, len(self.probabilities))
        remaining = tuple(p for i, p in enumerate(self.probabilities) if i not in selected)
        counts = _counts(counts, len(selected), self.trials)
        trials = self.trials - sum(counts)
        mass = math.fsum(remaining)
        if not remaining:
            raise ValueError('Debe quedar al menos una categoría por estimar.')
        if trials < 0 or trials and not mass or any(
            count and not self.probabilities[index] for index, count in zip(selected, counts)
        ):
            raise ValueError('La observación está fuera del soporte multinomial.')
        probabilities = tuple(p / mass for p in remaining) if mass else (1.,) + (0.,) * (len(remaining) - 1)
        return Multinomial(trials, probabilities)


def _counts(values, dimension, trials):
    try:
        counts = tuple(integer(value, 'Recuento', minimum=0, maximum=trials) for value in values)
    except TypeError as exc:
        raise ValueError('Indicá un recuento por categoría.') from exc
    if len(counts) != dimension:
        raise ValueError('Indicá un recuento por categoría.')
    return counts


def generate_multinomial(model: Multinomial, count, seed, *, replicas=1, origin=0, rate=None,
                         execution: ExecutionContext | None = None):
    def draw(rng, size):
        return rng.multinomial(model.trials, model.probabilities, size=size)

    return _sample_records(draw, model.document(), 'Multinomial', count, seed, replicas, origin,
                           rate, execution, dimensions=len(model.probabilities), discrete=True,
                           dtype=np.float64)
