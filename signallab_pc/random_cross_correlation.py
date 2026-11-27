"""Compatibility entry point for cross-correlation of discrete records."""

from .filters import positive_integer
from .stochastic_covariance import estimate_correlation


def cross_correlation(first,second,max_lag=None,remove_mean=False,denominator='N',normalize=False,*,method='fft',execution=None):
    if max_lag is not None:
        max_lag = positive_integer(max_lag+1, 'Cantidad de retardos')-1
    return estimate_correlation(first, second, max_lag=max_lag, remove_mean=remove_mean,
                                denominator=denominator, normalize=normalize, method=method, execution=execution)
