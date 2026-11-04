"""Frequency evaluation of state models with channel-specific pole handling."""
from fractions import Fraction
import warnings

import numpy as np
from scipy.linalg import LinAlgWarning, get_lapack_funcs, lu_factor, lu_solve

from .jobs import checkpoint
from .rational_frequency import RationalModel
from .resources import ensure_working_set


def _matrix(value):
    import sympy as sp

    return sp.Matrix(value.shape[0], value.shape[1],
                     lambda i,j: sp.Rational(float(value[i,j].real)) + sp.I*sp.Rational(float(value[i,j].imag)))


def _rational(value):
    real, imag = value.as_real_imag()
    return Fraction(int(real.p), int(real.q)), Fraction(int(imag.p), int(imag.q))


def _channel_models(model, input_index=None, output_index=None):
    """Build C adj(zI-A) B + D det(zI-A) without rounding state coefficients."""
    inputs = slice(None) if input_index is None else slice(input_index,input_index+1)
    outputs = slice(None) if output_index is None else slice(output_index,output_index+1)
    matrices = (model.A, model.B[:,inputs], model.C[outputs,:], model.D[outputs,inputs])
    count_outputs,count_inputs = matrices[-1].shape
    ensure_working_set(model.states**2 + (model.states+1)*count_outputs*count_inputs,
                       bytes_per_sample=256, live_arrays=8)
    A, B, C, D = (_matrix(matrix) for matrix in matrices)
    denominator = A.charpoly().all_coeffs()
    coefficients = [D]
    block = B
    for index in range(model.states):
        checkpoint()
        coefficients.append(C*block + denominator[index+1]*D)
        if index+1 < model.states:
            block = A*block + denominator[index+1]*B
    den = tuple(map(_rational, denominator))
    return [[RationalModel(tuple(_rational(coefficient[i,j]) for coefficient in coefficients), den)
             for j in range(count_inputs)] for i in range(count_outputs)]


def _point(angle, digital):
    if not digital:
        return 1j*angle, True
    quarter = round(angle/(np.pi/2))
    if quarter*(np.pi/2) == angle and abs(quarter) < 2**52:
        return (1+0j, 1j, -1+0j, -1j)[quarter % 4], True
    return np.exp(1j*angle), False


def response(model, omega, *, normalized=False):
    """Use a direct solve where reliable and exact channel limits at singularities."""
    omega = np.asarray(omega, dtype=float)
    if omega.ndim != 1 or not np.isfinite(omega).all():
        raise ValueError('Las frecuencias deben formar un vector real finito.')
    digital = model.dt is not None
    if normalized and not digital:
        raise ValueError('La frecuencia normalizada sólo corresponde al modelo discreto.')
    if digital and not normalized:
        with np.errstate(over='ignore', invalid='ignore'):
            omega = omega*model.dt
        if not np.isfinite(omega).all():
            raise ValueError('La frecuencia digital excede el rango numérico.')
    shape = (omega.size, model.outputs, model.inputs)
    ensure_working_set(max(1, int(omega.size)*model.outputs*model.inputs+model.states**2), live_arrays=12)
    if model.states == 0:
        return np.broadcast_to(model.D, shape).copy()
    result = np.empty(shape, dtype=complex)
    identity = np.eye(model.states)
    estimate_condition = get_lapack_funcs('gecon', dtype=complex)
    channels = None
    cutoff = np.finfo(float).eps*max(64,8*model.states)
    for k, angle in enumerate(omega):
        if k % 128 == 0:
            checkpoint(k/max(1, len(omega)))
        point, exact_coordinate = _point(float(angle), digital)
        with np.errstate(all='ignore'), warnings.catch_warnings():
            warnings.simplefilter('ignore', LinAlgWarning)
            matrix = point*identity-model.A
            try:
                if not np.isfinite(matrix).all():
                    raise FloatingPointError
                lu, pivots = lu_factor(matrix, check_finite=False)
                reciprocal, info = estimate_condition(lu, float(np.linalg.norm(matrix, 1)))
                if info == 0 and reciprocal > cutoff:
                    evaluated = model.C@lu_solve((lu,pivots), model.B, check_finite=False)+model.D
                    if np.isfinite(evaluated).all():
                        result[k] = evaluated
                        continue
            except (np.linalg.LinAlgError, ValueError, FloatingPointError):
                pass
        if channels is None:
            channels = _channel_models(model)
        for i, row in enumerate(channels):
            for j, channel in enumerate(row):
                result[k,i,j] = channel.pair(point, exact_coordinate=exact_coordinate)[0]
    checkpoint(1)
    return result
