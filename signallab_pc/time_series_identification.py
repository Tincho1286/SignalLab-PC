"""Stable recursions shared by real-valued time-series estimators."""

import math

import numpy as np

from .communications_data import integer
from .execution import ExecutionContext


def burg_coefficients(centered, order, *, checkpoint):
    """One-step denominator and log innovation variance from the Burg recursion."""
    count = len(centered)
    if order >= count-1:
        raise ValueError('Burg requiere al menos dos pares al completar el orden elegido.')
    variance = float(np.mean(centered**2))
    if variance == 0 and order:
        raise ValueError('Un registro constante no identifica coeficientes Burg.')
    innovation = math.log(variance) if variance else -math.inf
    coefficients = np.asarray([1.0])
    reflection = []
    forward, backward = centered[1:], centered[:-1]
    for level in range(1, order+1):
        checkpoint(level/(order+1))
        norm = float(np.dot(forward,forward) + np.dot(backward,backward))
        if norm <= 0:
            raise ValueError('Burg agotó la varianza antes del orden pedido.')
        k = -2*float(np.dot(forward,backward))/norm
        if not math.isfinite(k) or abs(k) >= 1-8*np.finfo(float).eps:
            raise ValueError('Burg encontró una reflexión unitaria o un orden sin información suficiente.')
        coefficients = np.r_[coefficients,0.] + k*np.r_[0.,coefficients[::-1]]
        reflection.append(k)
        innovation += math.log1p(-k*k)
        if level < order:
            forward, backward = (forward+k*backward)[1:], (backward+k*forward)[:-1]
    return coefficients, innovation, tuple(reflection)


def partial_autocorrelation(covariance, max_lag=None, *, execution=None):
    """Real PACF from nonnegative lags of a positive-definite covariance."""
    values = np.asarray(covariance)
    if values.ndim != 1 or not len(values) or np.any(values.imag) or not np.all(np.isfinite(values)):
        raise ValueError('La PACF requiere covarianzas reales, finitas y ordenadas desde el retardo cero.')
    lag = len(values)-1 if max_lag is None else integer(max_lag, 'Retardos de la PACF', minimum=0, maximum=len(values)-1)
    if values[0].real <= 0:
        raise ValueError('La PACF es indefinida con varianza nula.')
    context = execution or ExecutionContext()
    with context.reserve(80*(lag+1)):
        if np.max(abs(values[:lag+1].real)) > values[0].real:
            raise ValueError('La covarianza excede su valor de retardo cero.')
        scale = float(values[0].real)
        covariance = values[:lag+1].real / scale
        partial = np.empty(lag+1)
        partial[0] = 1.
        prediction = np.empty(0)
        innovation = 1.
        for order in range(1, lag+1):
            context.checkpoint()
            k = (covariance[order] - np.dot(prediction,covariance[order-1:0:-1])) / innovation
            if abs(k) >= 1-8*np.finfo(float).eps or not math.isfinite(k):
                raise ValueError('La secuencia de covarianzas no identifica una PACF de ese orden.')
            prediction = np.r_[prediction-k*prediction[::-1], k]
            innovation *= (1-k)*(1+k)
            if innovation == 0:
                raise ValueError('La varianza de predicción no es representable para ese orden.')
            partial[order] = k
        context.checkpoint()
        return partial
