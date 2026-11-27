"""Linear discrete Kalman estimator using covariance factors."""

from dataclasses import dataclass

import numpy as np

from .execution import ExecutionContext
from .model import Signal
from .communications_data import integer
from .multivariate_probability import _array, _factor, _parts, _scale, _symmetric
from .operation_provenance import content_digest, settings_digest
from .state_space import StateModel
from .system_clock import lag_clock


def _root(covariance, size, name):
    matrix = _array(covariance, 2, name, True)
    if matrix.shape != (size, size):
        raise ValueError(f'{name}: se esperaba una matriz de {size} por {size}.')
    try:
        root, _, _ = _factor(_symmetric(matrix, hermitian=True))
    except ValueError as error:
        raise ValueError(f'{name}: {error}') from error
    return root.astype(complex, copy=False)


def _compact(factor):
    if not np.isfinite(factor).all():
        raise FloatingPointError('La propagación de covarianza excede el rango numérico.')
    if factor.shape[1] <= factor.shape[0]:
        return factor
    return np.linalg.qr(factor.conj().T, mode='r').conj().T


def _covariance(root):
    return root @ root.conj().T


def _correct(root, sensor, measurement_root, innovation, prediction, observation):
    # Joint representation of the state error and the measurement innovation.
    design = np.hstack((sensor @ root, measurement_root))
    if not np.isfinite(design).all():
        raise FloatingPointError('El modelo de observación excede el rango numérico.')
    left, singular, right_h = np.linalg.svd(design, full_matrices=True)
    leading = singular[0] if singular.size else 0.
    cutoff = max(design.shape)*np.finfo(float).eps*leading
    rank = np.count_nonzero(singular > cutoff)
    directions = left[:, :rank]
    projected = directions.conj().T @ innovation
    tail = innovation - directions @ projected
    tolerance = 32*np.finfo(float).eps*max(design.shape) * max(_scale(innovation), _scale(prediction), _scale(observation))
    if _scale(tail) > tolerance:
        raise ValueError('Una medición contradice una restricción determinista del modelo.')
    state_basis = root @ right_h.conj().T[:root.shape[1]]
    gain = (state_basis[:, :rank]/singular[:rank]) @ directions.conj().T
    return gain, _compact(state_basis[:, rank:])


@dataclass(frozen=True, slots=True)
class KalmanResult:
    predicted: np.ndarray
    corrected: np.ndarray
    prior_covariance: np.ndarray
    posterior_covariance: np.ndarray
    innovations: np.ndarray
    gains: np.ndarray
    observed: np.ndarray
    measurements: np.ndarray
    controls: np.ndarray | None
    report: dict


def kalman_filter(model, observations, process_covariance, measurement_covariance,
                  initial_mean, initial_covariance, *, controls=None, mask=None, execution=None):
    """Estimate states in x[n+1]=Ax[n]+Bu[n]+w[n], y[n]=Cx[n]+Du[n]+v[n].

    The initial prior is at the first observation. The mask marks observed
    components. Zero placeholders in the missing innovations have no meaning.
    Covariances are for independent white process and measurement noise.
    """
    if not isinstance(model, StateModel) or model.dt is None or not model.states:
        raise ValueError('Kalman requiere un modelo discreto con al menos un estado.')
    data = _array(observations, 2, 'Observaciones', True)
    count, outputs = data.shape
    if outputs != model.outputs:
        raise ValueError('Cargá una columna por salida del modelo.')
    states, inputs = model.states, model.inputs
    context = execution or ExecutionContext()
    estimate = (224*states**2 + 160*states*outputs + 96*(states+outputs+inputs))*count
    estimate += 192*(states+outputs+inputs)**2
    with context.reserve(estimate):
        stamp = content_digest(model, context.checkpoint)
        a, b, c, d = (getattr(model, key).copy() for key in ('A', 'B', 'C', 'D'))
        prior = _array(initial_mean, 1, 'Media inicial', True)
        if prior.shape != (states,):
            raise ValueError('Cargá un valor de media inicial por estado.')
        if controls is not None:
            controls = _array(controls, 2, 'Controles conocidos', True)
            if controls.shape != (count, inputs):
                raise ValueError('Cargá los controles conocidos en cada instante, con una columna por entrada.')
        if mask is None:
            measured = np.ones(data.shape, dtype=bool)
        else:
            measured = np.asarray(mask).copy()
            if measured.shape != data.shape or measured.dtype.kind != 'b':
                raise ValueError('La máscara debe tener un valor booleano por observación.')
        q = _root(process_covariance, states, 'Covarianza de proceso Q')
        r = _root(measurement_covariance, outputs, 'Covarianza de medición R')
        uncertainty = _root(initial_covariance, states, 'Covarianza inicial P₀')
        model_parameters = {'process_covariance': _parts(_covariance(q)),
                            'measurement_covariance': _parts(_covariance(r)),
                            'initial_covariance': _parts(_covariance(uncertainty)),
                            'initial_mean': _parts(prior)}
        predicted = np.empty((count, states), complex)
        corrected = np.empty_like(predicted)
        prior_covariance = np.empty((count, states, states), complex)
        posterior_covariance = np.empty_like(prior_covariance)
        gains = np.zeros((count, states, outputs), complex)
        innovations = np.zeros_like(data)
        with np.errstate(over='ignore', invalid='ignore'):
            for index, available in enumerate(measured):
                context.checkpoint(95*index//count)
                predicted[index], prior_covariance[index] = prior, _covariance(uncertainty)
                posterior = prior
                if available.any():
                    sensor = c[available]
                    predicted_observation = sensor @ prior
                    if controls is not None:
                        predicted_observation += d[available] @ controls[index]
                    observed = data[index, available]
                    innovation = observed - predicted_observation
                    if not np.isfinite(innovation).all():
                        raise FloatingPointError('La innovación excede el rango numérico.')
                    gain, uncertainty = _correct(uncertainty, sensor, r[available], innovation,
                                                 predicted_observation, observed)
                    posterior = prior + gain @ innovation
                    gains[index][:, available] = gain
                    innovations[index, available] = innovation
                corrected[index], posterior_covariance[index] = posterior, _covariance(uncertainty)
                if index+1 < count:
                    prior = a @ posterior
                    if controls is not None:
                        prior += b @ controls[index]
                    uncertainty = _compact(np.hstack((a @ uncertainty, q)))
        if not all(np.isfinite(value).all() for value in
                   (predicted, corrected, prior_covariance, posterior_covariance, gains)):
            raise FloatingPointError('La estimación o la covarianza excede el rango numérico.')
        if content_digest(model, context.checkpoint) != stamp:
            raise ValueError('El modelo cambió durante la estimación.')
        report = {'schema': 1, 'method': 'discrete_linear_kalman', 'model_hash': stamp,
                  'samples': count, 'states': states, 'observations_per_sample': outputs,
                  'observed_components': int(measured.sum()), 'missing_components': int((~measured).sum()),
                  'prediction_only_steps': int(np.count_nonzero(~measured.any(axis=1))),
                  'sample_period_s': model.dt, 'parameters': model_parameters,
                  'scope': 'Modelo lineal con ruidos blancos independientes. Para señales complejas se presupone ruido propio.'}
        context.checkpoint(100)
        measurements = np.where(measured, data, 0.)
        return KalmanResult(predicted, corrected, prior_covariance, posterior_covariance, innovations,
                            gains, measured, measurements, controls, report)


def store_kalman(project, model, result, *, model_id=None, origin=0, execution=None, tool=None):
    """Persist the model, diagnostics, and state trajectories with their clock."""
    origin = integer(origin, 'Índice inicial', minimum=-2**53, maximum=2**53)
    context = execution or ExecutionContext()
    count, states = result.corrected.shape
    clock = lag_clock(1/model.dt, origin, count)
    payload_items = (result.measurements, result.innovations, result.gains,
                     result.prior_covariance, result.posterior_covariance)
    estimate = 220*sum(item.size for item in payload_items) + 192*count*(states+model.inputs+model.outputs)
    with context.reserve(estimate):
        parent_hash = result.report['model_hash']
        if content_digest(model, context.checkpoint) != parent_hash:
            raise ValueError('El modelo cambió antes de guardar la estimación.')
        payload = {**result.report, 'origin': origin, 'clock': clock, 'mask': result.observed.tolist(),
                   'controls': None if result.controls is None else _parts(result.controls)}
        for title, values in zip(('observations', 'innovations', 'gains', 'prior_covariance', 'posterior_covariance'),
                                 payload_items, strict=True):
            context.checkpoint()
            payload[title] = _parts(values)
        proof = settings_digest(['calculation',payload])
        outputs = []
        with project.stage_records(before_commit=context.checkpoint) as staged:
            if model_id is None:
                model_id = staged.add(model, operation='Modelo discreto para Kalman', tool=tool,
                                      verification=(parent_hash, (), context.checkpoint))
            parent = staged.add(payload, title='Filtrado de Kalman', operation='Estimar estados',
                                parents=(model_id,), tool=tool, verification=(proof, (parent_hash,), context.checkpoint))
            for index in range(states):
                for label, data in (('Predicción',result.predicted), ('Corrección',result.corrected),
                                    ('Varianza posterior',result.posterior_covariance.diagonal(axis1=1,axis2=2).real)):
                    signal = Signal(data[:, index], origin, name=f'{label} · estado {index+1}',
                                    metadata={**clock, 'state_index': index, 'operation': 'kalman_state'})
                    digest = content_digest(signal, context.checkpoint)
                    key = staged.add(signal, operation=signal.name, parents=(parent,), tool=tool,
                                     verification=(digest, (proof,), context.checkpoint))
                    outputs.append((key, signal))
        return {'model': model_id, 'report': parent, 'outputs': outputs}
