"""Likelihood and Bayesian estimation in a real linear Gaussian observation model."""

import math

import numpy as np
from scipy.linalg import cholesky, solve_triangular

from .execution import ExecutionContext
from .multivariate_probability import _array, _symmetric
from .operation_provenance import settings_digest
from .probability import _scalar


def _covariance_factor(values, size, label):
    matrix = _array(values, 2, label, False)
    if matrix.shape != (size, size):
        raise ValueError(f'{label}: se esperaba una matriz de {size} por {size}.')
    try:
        return cholesky(_symmetric(matrix, hermitian=True), lower=True, check_finite=False)
    except np.linalg.LinAlgError as exc:
        raise ValueError(f'{label}: se requiere una matriz positiva definida.') from exc


def _vector(values, size, label):
    vector = _array(values, 1, label, False)
    if vector.size != size:
        raise ValueError(f'{label}: se esperaban {size} elementos.')
    return vector


def _numbers(values):
    """Keep matrices and estimates safe for finite JSON interchange."""
    if not np.isfinite(values).all():
        raise FloatingPointError('Las magnitudes de este modelo exceden la precisión disponible.')
    return values.tolist()


def linear_gaussian(observations, design, measurement_covariance, *,
                    prior_mean=None, prior_covariance=None, parameter=None, execution=None):
    """Estimate θ in y = Aθ + v, with v real normal and known covariance.

    A positive definite prior gives an identifiable posterior even when ML
    cannot identify all parameters. The optional parameter evaluates the
    likelihood and repeated-measurement risks at a fixed true value.
    """
    matrix = _array(design, 2, 'Matriz de observación', False)
    rows, columns = matrix.shape
    context = execution or ExecutionContext()
    with context.reserve(160 * (rows * rows + columns * columns + rows * columns)):
        data = _vector(observations, rows, 'Observaciones')
        noise = _covariance_factor(measurement_covariance, rows, 'Covarianza del ruido')
        if (prior_mean is None) != (prior_covariance is None):
            raise ValueError('Para calcular el posterior indicá media y covarianza a priori.')
        truth = None if parameter is None else _vector(parameter, columns, 'Parámetro de referencia')
        white = solve_triangular(noise, matrix, lower=True, check_finite=False)
        target = solve_triangular(noise, data, lower=True, check_finite=False)
        if not np.isfinite(white).all() or not np.isfinite(target).all():
            raise FloatingPointError('El blanqueo del ruido excede el rango numérico.')
        log_constant = -.5 * rows * math.log(math.tau) - np.log(noise.diagonal()).sum()
        left, singular, right = np.linalg.svd(white, full_matrices=False)
        threshold = max(white.shape) * np.finfo(float).eps * singular[0]
        rank = int(np.count_nonzero(singular > threshold))
        with np.errstate(over='ignore', invalid='ignore'):
            information = white.T @ white
        result = {'schema': 1, 'model': 'real linear Gaussian observations', 'samples': rows,
                  'parameters': columns, 'rank': rank, 'fisher_information': _numbers(information),
                  'observation_model': {'design': _numbers(matrix), 'observation': _numbers(data),
                                        'measurement_covariance': _numbers(noise @ noise.T)},
                  'ml': None, 'prior': None, 'posterior': None, 'reference': None,
                  'scope': 'Covarianza de medición conocida. La cota clásica corresponde a estimadores insesgados.'}
        if rank == columns:
            inverse_factor = right.T / singular
            estimate = inverse_factor @ (left.T @ target)
            residual = target - white @ estimate
            covariance = inverse_factor @ inverse_factor.T
            result['ml'] = {'estimate': _numbers(estimate), 'variance': _numbers(covariance.diagonal()),
                            'bias': [0.] * columns, 'mse': _scalar(float(np.trace(covariance))),
                            'cramer_rao': _numbers(covariance),
                            'log_likelihood': _scalar(float(log_constant - .5 * (residual @ residual)))}
        if truth is not None:
            residual = target - white @ truth
            result['reference'] = {'parameter': _numbers(truth),
                                   'log_likelihood': _scalar(float(log_constant - .5 * (residual @ residual)))}
        if prior_mean is not None:
            context.checkpoint(50)
            mean = _vector(prior_mean, columns, 'Media a priori')
            root = _covariance_factor(prior_covariance, columns, 'Covarianza a priori')
            with np.errstate(over='ignore', invalid='ignore'):
                effect = white @ root
            if not np.isfinite(effect).all():
                raise FloatingPointError('El modelo previo en coordenadas blanqueadas excede el rango numérico.')
            # Thin SVD plus a null-space factor when observations are fewer than parameters.
            left, scales, right = np.linalg.svd(effect, full_matrices=rows < columns)
            scale_count = scales.size
            shrink = 1 / np.hypot(1, scales)
            posterior_root = root @ right.T
            gain = (posterior_root[:, :scale_count] * (scales * shrink * shrink)) @ left[:, :scale_count].T
            posterior_root[:, :scale_count] *= shrink
            covariance = posterior_root @ posterior_root.T
            mean_post = mean + gain @ (target - white @ mean)
            estimate = _numbers(mean_post)
            result['prior'] = {'mean': _numbers(mean), 'covariance': _numbers(root @ root.T)}
            result['posterior'] = {'map': estimate, 'mmse': estimate, 'lmmse': estimate,
                                   'covariance': _numbers(covariance), 'bayes_mse': _scalar(float(np.trace(covariance))),
                                   'scope': 'Media y moda coinciden en este posterior gaussiano.'}
            if truth is not None:
                delta = mean - truth
                bias = delta - gain @ (white @ delta)
                measurement_variance = np.sum(gain**2, axis=1)
                result['reference'].update(posterior_estimator_bias=_numbers(bias),
                                           posterior_estimator_variance=_numbers(measurement_variance),
                                           posterior_estimator_mse=_scalar(float(bias @ bias + measurement_variance.sum())))
        context.checkpoint(100)
        return result


def store_gaussian_estimate(project, result, *, execution=None, tool=None):
    context = execution or ExecutionContext()
    with project.stage_records(before_commit=context.checkpoint) as staged:
        return staged.add(result, title='Estimación gaussiana lineal', operation='Estimación ML y bayesiana',
                          tool=tool, verification=(settings_digest(['calculation', result]), (), context.checkpoint))
