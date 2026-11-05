"""Optional plot samples must not invalidate an exact transform result."""
import math


class NumericSamplingError(ValueError):
    """A computed expression cannot be represented reliably as plot samples."""


def sample_budget(count, **options):
    from .resources import ensure_working_set, ResourceLimitError
    try:
        ensure_working_set(count, **options)
    except ResourceLimitError as exc:
        raise NumericSamplingError('El registro de muestras excede la memoria disponible. '+str(exc)) from exc


def sample_pair(value):
    if hasattr(value, 'as_real_imag'):
        real, imaginary = value.as_real_imag()
    else:
        real, imaginary = value.real, value.imag
    try:
        number = complex(value)
    except OverflowError as exc:
        raise NumericSamplingError('Las muestras exceden el rango numérico. Reducí el intervalo para graficarlas.') from exc
    if not math.isfinite(number.real) or not math.isfinite(number.imag):
        raise NumericSamplingError('Las muestras exceden el rango numérico. Reducí el intervalo para graficarlas.')
    for original, converted in ((real, number.real), (imaginary, number.imag)):
        zero = getattr(original, 'is_zero', None)
        nonzero = zero is False if zero is not None else original != 0
        if converted == 0 and nonzero:
            raise NumericSamplingError('Una componente no nula es menor que el rango numérico de las muestras; no se representa como cero.')
    return [number.real, number.imag]
