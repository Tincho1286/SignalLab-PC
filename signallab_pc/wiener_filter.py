"""Causal Wiener FIR from a stationary model or a pair of sampled records."""

import math

import numpy as np
from scipy.linalg import toeplitz

from .communications_data import integer, real
from .execution import ExecutionContext
from .filters import Transfer
from .model import Signal
from .multivariate_probability import _array, _parts
from .operation_provenance import content_digest, settings_digest, verify_inputs
from .probability import _scalar
from .spectral_scaling import bounded, range_status, restore_scalar, restore_scale
from .statistics_results import store_statistics
from .stochastic_covariance import _align
from .system_clock import reindex_clock


def _power(value, exponent=0):
    restored = restore_scalar(value, exponent)
    status = range_status(restored, value)
    return _scalar(restored) if status == 'ok' else {'value': None, 'status': status}


def _output(values, exponent):
    restored = restore_scale(values, exponent)
    if not np.isfinite(restored).all() or np.any((values != 0) & (restored == 0)):
        raise FloatingPointError('Los coeficientes o las muestras exceden el rango numérico.')
    return restored


def wiener_hopf(autocorrelation, cross_correlation, target_power, *, execution=None):
    """Solve the causal normal equations from Rxx[k] and Rdx[k], k ≥ 0.

    Moments can be centered covariances if the caller handles the means
    separately. For singular observations the solver returns minimum-norm taps.
    """
    x = _array(autocorrelation, 1, 'Autocorrelación Rxx', True)
    p = _array(cross_correlation, 1, 'Correlación cruzada Rdx', True)
    length = len(x)
    if len(p) != length or x[0].imag != 0 or x[0].real < 0:
        raise ValueError('Las correlaciones deben tener igual longitud y Rxx[0] real no negativa.')
    target = real(target_power, 'Potencia de la señal buscada')
    if target < 0:
        raise ValueError('La potencia de la señal buscada debe ser no negativa.')
    context = execution or ExecutionContext()
    with context.reserve(192 * (length+1)**2):
        input_std, target_std = math.sqrt(x[0].real), math.sqrt(target)
        if not input_std or not target_std:
            if np.any(p) or (not input_std and np.any(x)):
                raise ValueError('Las correlaciones contradicen una de las potencias nulas.')
        if input_std:
            fraction, shift = math.frexp(x[0].real)
            correlations = restore_scale(x, -shift, 1/fraction)
        else:
            correlations = x
        matrix = toeplitz(correlations)
        if input_std and target_std:
            a, ea = math.frexp(input_std)
            b, eb = math.frexp(target_std)
            p_scaled, ex = bounded(p, normalize=True)
            cross = _output(p_scaled / (a*b), ex-ea-eb)
        else:
            cross = p
        if not np.isfinite(matrix).all():
            raise ValueError('La autocorrelación excede la escala de su potencia.')
        eig, vectors = np.linalg.eigh(matrix)
        cutoff = 16 * np.finfo(float).eps * length * max(1., eig[-1])
        if eig[0] < -cutoff:
            raise ValueError('La autocorrelación no define una matriz semidefinida positiva.')
        active = eig > cutoff
        rotated = vectors.conj().T @ cross
        normalized = vectors[:, active] @ (rotated[active] / eig[active])
        explained = float(np.sum(abs(rotated[active])**2/eig[active]))
        if np.max(abs(rotated[~active]), initial=0.) > cutoff or explained > 1 + 8*cutoff:
            raise ValueError('Las correlaciones y la potencia no forman un modelo conjunto válido.')
        taps = _output(normalized / a * b, eb-ea) if input_std and target_std else normalized
        context.checkpoint(100)
        return {'schema': 1, 'method': 'wiener_hopf', 'coefficients': _parts(taps),
                'autocorrelation': _parts(x), 'cross_correlation': _parts(p), 'target_power': target,
                'rank': int(np.count_nonzero(active)), 'theoretical_mse': _power(max(0., 1-explained)*target),
                'convention': 'Rdx[k] = E(d[n] conj(x[n-k])); taps multiply x[n-k]'}


def _record(values, start, desired, title):
    clock = reindex_clock(desired.metadata, start-desired.origin, len(values))
    units = desired.metadata.get('amplitude_units')
    if units:
        clock['amplitude_units'] = units
    return Signal(values, start, 1, desired.units, title, 'discrete', metadata=clock)


def wiener_fir(observed, desired, length, *, fit_offset=False, reserve=0, execution=None):
    """Fit a causal FIR with complete input windows, then evaluate a holdout."""
    if type(fit_offset) is not bool:
        raise ValueError('Indicá si se ajusta un término constante.')
    start, end, rate = _align((observed, desired))
    length = integer(length, 'Longitud del filtro', maximum=end-observed.origin)
    start = max(start, observed.origin+length-1)
    count = end-start
    reserve = integer(reserve, 'Muestras de validación', minimum=0, maximum=max(0,count-1))
    training = count-reserve
    if training < length + int(fit_offset):
        raise ValueError('No hay suficientes ventanas completas en el tramo de entrenamiento.')
    context = execution or ExecutionContext()
    with context.reserve(128*count*length + 96*length**2 + 160*count):
        digests = tuple(content_digest(item, context.checkpoint) for item in (observed, desired))
        x, ex = bounded(observed.values[start-length+1-observed.origin:end-observed.origin], normalize=True)
        target, ed = bounded(desired.values[start-desired.origin:end-desired.origin], normalize=True)
        design = np.lib.stride_tricks.sliding_window_view(x, length)[:, ::-1]
        a, y = design[:training], target[:training]
        means, location = (a.mean(axis=0), y.mean()) if fit_offset else (0., 0.)
        context.checkpoint(25)
        coefficients, _, rank, _ = np.linalg.lstsq(a-means, y-location, rcond=None)
        offset = location - means @ coefficients if fit_offset else 0j
        taps = _output(coefficients, ed-ex)
        estimate = np.empty(count, dtype=complex)
        block_size = max(1, 262_144//length)
        for first in range(0, count, block_size):
            context.checkpoint()
            block = slice(first, first+block_size)
            estimate[block] = design[block] @ coefficients + offset
        error = target - estimate
        predicted = _record(_output(estimate, ed), start, desired, 'Estimación de Wiener')
        residual = _record(_output(error, ed), start, desired, 'Error residual de Wiener')
        reference = _record(desired.values[start-desired.origin:end-desired.origin], start, desired, 'Señal de referencia')
        measurement = _record(observed.values[start-observed.origin:end-observed.origin], start, observed, 'Señal observada')
        report = {'schema': 1, 'method': 'wiener_fir', 'input_hashes': list(digests),
                  'coefficients': _parts(taps), 'offset': _parts(_output(np.asarray(offset), ed)),
                  'fit_offset': bool(fit_offset), 'length': length, 'rank': int(rank),
                  'first_index': start, 'last_index': end-1, 'training_samples': training,
                  'validation_samples': reserve, 'training_mse': _power(float(np.mean(abs(error[:training])**2)), 2*ed),
                  'validation_mse': _power(float(np.mean(abs(error[training:])**2)), 2*ed) if reserve else None,
                  'scope': 'MSE observado con ventanas causales completas. El tramo final se excluye del ajuste.'}
        system = Transfer(taps, [1.], name='Filtro FIR de Wiener', sample_period_s=None if rate is None else 1/rate)
        verify_inputs((observed, desired), digests, context.checkpoint)
        context.checkpoint(100)
        return report, system, predicted, residual, reference, measurement


def store_wiener(project, result, inputs, *, execution=None, tool=None):
    """Register the report, reusable FIR and signal results in one transaction."""
    context = execution or ExecutionContext()
    report, system, prediction, error, reference, measurement = result
    proof = settings_digest(['calculation', report])
    with project.stage_records(before_commit=context.checkpoint) as staged:
        sources, key = store_statistics(staged, report, inputs, 'Filtro FIR de Wiener', execution=context, tool=tool)
        output = {'sources': sources, 'report': key}
        for label, value in (('system', system), ('estimate', prediction), ('error', error),
                             ('reference', reference), ('observed', measurement)):
            output[label] = staged.add(value, operation=value.name, parents=(key,), tool=tool,
                                       verification=(content_digest(value, context.checkpoint), (proof,), context.checkpoint))
    return output


def store_wiener_model(project, result, *, execution=None, tool=None):
    context = execution or ExecutionContext()
    taps = result['coefficients']
    transfer = Transfer(np.asarray(taps['real']) + 1j*np.asarray(taps['imag']), [1.], 'digital',
                        'Filtro FIR de Wiener–Hopf')
    proof = settings_digest(['calculation', result])
    with project.stage_records(before_commit=context.checkpoint) as staged:
        parent = staged.add(result, title='Ecuaciones de Wiener–Hopf', operation='Diseño estadístico',
                            tool=tool, verification=(proof, (), context.checkpoint))
        record = staged.add(transfer, operation=transfer.name, parents=(parent,), tool=tool,
                            verification=(content_digest(transfer, context.checkpoint), (proof,), context.checkpoint))
    return {'report': parent, 'system': record}
