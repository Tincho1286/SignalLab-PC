"""Optional plot samples must not invalidate an exact transform result."""
import math


class NumericSamplingError(ValueError):
    """A computed expression cannot be represented reliably as plot samples."""


def sample_pair(value):
    try:
        value = complex(value)
    except OverflowError as exc:
        raise NumericSamplingError('Las muestras exceden el rango numérico. Reducí el intervalo o la amplitud para graficarlas.') from exc
    if not math.isfinite(value.real) or not math.isfinite(value.imag):
        raise NumericSamplingError('Las muestras exceden el rango numérico. Reducí el intervalo o la amplitud para graficarlas.')
    return [value.real, value.imag]
