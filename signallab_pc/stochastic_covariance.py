"""Correlation in time and complex covariance across matched observations."""

import math

import numpy as np
from scipy.signal import correlate

from .communications_data import integer
from .execution import ExecutionContext
from .model import Signal
from .operation_provenance import content_digest, verify_inputs
from .probability import _scalar
from .resources import ResourceLimitError
from .signal_semantics import require_temporal
from .spectral_scaling import bounded, centered_bounded, finite_real_mean, restore_scalar, restore_scale
from .system_clock import common_rate, lag_clock, validate_discrete_clocks


_BLOCK = 131_072
METHODS = ('auto', 'direct', 'fft')


def _align(records):
    for record in records:
        if not isinstance(record, Signal) or record.domain != 'discrete':
            raise ValueError('La operación requiere registros discretos.')
        require_temporal(record)
    known = [item for item in records if item.metadata.get('sample_rate_hz') is not None]
    reference = next((item for item in known if item.metadata.get('time_start_s') is not None), known[0] if known else None)
    known_rate = common_rate(reference) if reference is not None else None
    for item in known:
        if item is not reference:
            validate_discrete_clocks(reference, item)
    rate = known_rate if len(known) == len(records) else None
    start = max(item.origin for item in records)
    end = min(item.origin + len(item.values) for item in records)
    if end <= start:
        raise ValueError('Los registros no tienen índices observados en común. Revisá sus orígenes.')
    return start, end, rate


def _average(values, checkpoint):
    return [finite_real_mean(values.real, checkpoint), finite_real_mean(values.imag, checkpoint)]


def _dot(x, y, checkpoint):
    partial = []
    for offset in range(0, len(x), _BLOCK):
        checkpoint()
        stop = min(offset+_BLOCK, len(x))
        partial.append(complex(np.vdot(y[offset:stop], x[offset:stop])))
    return complex(math.fsum(item.real for item in partial), math.fsum(item.imag for item in partial))


def _overlap(x, y, shift):
    if shift < 0:
        return x[:shift], y[-shift:]
    return x[shift:], y[:len(y)-shift]


def estimate_correlation(first, second=None, *, max_lag=None, remove_mean=False,
                         denominator='N', normalize=False, method='auto', execution=None):
    """Calculate Rxy[k] = mean(x[n+k] conj(y[n])) using the shared interval."""
    if method not in METHODS or denominator not in ('N', 'overlap'):
        raise ValueError('Método o divisor de correlación desconocido.')
    auto = second is None
    inputs = (first,) if auto else (first, second)
    start, end, rate = _align(inputs)
    count = end-start
    lag = min(50,count-1) if max_lag is None else integer(max_lag, 'Retardo máximo', minimum=0, maximum=count-1)
    if method == 'auto':
        # Direct only evaluates the requested neighborhood. FFT is for broad lag ranges.
        method = 'direct' if lag <= 8 else 'fft'
    x = first.values[start-first.origin:end-first.origin]
    y = x if auto else second.values[start-second.origin:end-second.origin]
    context = execution or ExecutionContext()
    estimate = (480 if method == 'fft' else 160)*count + 32*(2*lag+1)
    with context.reserve(estimate):
        hashes = tuple(content_digest(source, context.checkpoint) for source in inputs)
        mean = _average(x, context.checkpoint) if auto else None
        if remove_mean:
            left, ex = centered_bounded(x)
            right, ey = (left, ex) if auto else centered_bounded(y)
        else:
            left, ex = bounded(x, normalize=True)
            right, ey = (left, ex) if auto else bounded(y, normalize=True)
        power = float(np.mean(abs(left)**2))
        if normalize:
            factor = power if auto else math.sqrt(power) * math.sqrt(float(np.mean(abs(right)**2)))
            if factor == 0:
                raise ValueError('No se puede normalizar con potencia o varianza cero en el intervalo común.')
        if method == 'fft':
            context.checkpoint()
            raw = correlate(left, right, mode='full', method='fft')[count-1-lag:count+lag].copy()
            context.checkpoint()
        else:
            raw = np.zeros(2*lag+1, dtype=complex)
            for shift in range(1 if auto else -lag, lag+1):
                if shift:
                    raw[lag+shift] = _dot(*_overlap(left,right,shift), context.checkpoint)
        raw[lag] = power*count if auto else _dot(left,right,context.checkpoint)
        if auto:
            raw[:lag] = np.conj(raw[:lag:-1])
        sizes = count-np.abs(np.arange(-lag,lag+1))
        normalized = raw / (count if denominator == 'N' else sizes)
        if auto:
            normalized[lag] = power
        if normalize:
            values = normalized / factor
            dropped = 0
            if auto:
                values[lag] = 1.
        else:
            values = restore_scale(normalized, ex+ey)
            dropped = int(np.count_nonzero((values == 0) & (normalized != 0)))
        if not np.all(np.isfinite(values)):
            raise ValueError('La correlación excede el rango de float64.')
        verify_inputs(inputs, hashes, context.checkpoint)
        scope = ('Se usan los índices observados en común. Los retardos grandes tienen menos pares. '
                 'Al restar la media muestral, dividir por N−|k| no elimina en general el sesgo.')
        if dropped:
            scope += f' {dropped} retardos no nulos se redondearon a cero por el rango de float64.'
        meta = {'schema': 1, 'input_samples': count, 'input_hashes': list(hashes), 'maximum_lag': lag,
                'common_origin': start, 'common_last_index': end-1, 'remove_sample_mean': bool(remove_mean),
                'denominator': 'N' if denominator == 'N' else 'N−|k|', 'pair_count_rule': 'N−|k|',
                'method': 'FFT; finite precision' if method == 'fft' else 'direct; finite precision',
                'convention': 'sum x[n+k]*conj(y[n]) over the overlap, divided by N or N−|k|',
                'scope': scope, **lag_clock(rate,-lag,len(values))}
        if dropped:
            meta['underflowed_samples'] = dropped
        if auto:
            title = 'Autocovarianza estimada' if remove_mean else 'Autocorrelación estimada'
            meta.update(operation='estimated_autocovariance' if remove_mean else 'estimated_autocorrelation',
                        sample_mean=mean, divide_by_zero_lag=bool(normalize))
        else:
            title = 'Covarianza cruzada estimada' if remove_mean else 'Correlación cruzada estimada'
            meta.update(operation='estimated_cross_covariance' if remove_mean else 'estimated_cross_correlation',
                        first_samples=len(first.values),
                        second_samples=len(second.values),
                        normalization='sqrt(Px*Py) on common interval' if normalize else 'none')
        if normalize:
            title += ' normalizada'
        return Signal(values, -lag, 1, 'retardo k', title, 'discrete', metadata=meta)


def _complex_document(values):
    re, im = np.asarray(values).real, np.asarray(values).imag
    ok = np.isfinite(re) & np.isfinite(im)

    def safe(part):
        result = part.astype(object)
        result[~ok] = None
        return result.tolist()

    return {'real': safe(re), 'imag': safe(im)}


def _matrix_moments(columns, size, count, divisor, context):
    data = np.empty((size,count), dtype=complex)
    powers, means = [], []
    for i, column in enumerate(columns):
        context.checkpoint()
        data[i], power = centered_bounded(column)
        powers.append(power)
        means.append(_average(column, context.checkpoint))
    covariance = (data @ data.conj().T) / divisor
    pseudo = (data @ data.T) / divisor
    degrees = np.sqrt(np.maximum(covariance.diagonal().real,0))
    factors = degrees[:,None]*degrees
    with np.errstate(divide='ignore', invalid='ignore'):
        correlation = np.divide(covariance, factors, out=np.full(covariance.shape, np.nan+0j), where=factors>0)
    diagonal = np.diag_indices(size)
    covariance.imag[diagonal] = 0.
    correlation[diagonal] = np.where(degrees > 0, 1., np.nan)
    lower, upper = np.tril_indices(size, k=-1)
    shift = np.add.outer(powers, powers)
    with np.errstate(over='ignore', under='ignore'):
        for matrix in (covariance, pseudo):
            np.ldexp(matrix.real, shift, out=matrix.real)
            np.ldexp(matrix.imag, shift, out=matrix.imag)
    covariance[lower,upper] = covariance[upper,lower].conj()
    correlation[lower,upper] = correlation[upper,lower].conj()
    pseudo[lower,upper] = pseudo[upper,lower]
    context.checkpoint()
    return means, covariance, pseudo, correlation


def covariance_matrix(records, *, sample=True, execution=None):
    """Estimate C = E[(X−μ)(X−μ)ᴴ] and its nonconjugated counterpart."""
    records = tuple(records)
    if not records:
        raise ValueError('Seleccioná al menos un registro para la matriz.')
    start, end, rate = _align(records)
    count = end-start
    divisor = count - int(sample)
    if divisor < 1:
        raise ValueError('La covarianza con divisor N−1 requiere al menos dos observaciones comunes.')
    size = len(records)
    context = execution or ExecutionContext()
    with context.reserve(96*size*count + 384*size**2):
        hashes = tuple(content_digest(item, context.checkpoint) for item in records)
        columns = (item.values[start-item.origin:end-item.origin] for item in records)
        means, covariance, pseudo, correlation = _matrix_moments(columns, size, count, divisor, context)
        result = {'schema': 1, 'operation': 'covariance_matrix', 'covariance': _complex_document(covariance),
                  'pseudocovariance': _complex_document(pseudo), 'correlation': _complex_document(correlation),
                  'means': means, 'input_hashes': list(hashes), 'observations': count, 'divisor': divisor,
                  'common_origin': start, 'common_last_index': end-1, 'sample_rate_hz': rate,
                  'channels': [item.name for item in records],
                  'amplitude_units': [item.metadata.get('amplitude_units','') for item in records],
                  'scope': 'Producto exterior de cada observación centrada. N/D indica una escala fuera de rango o un coeficiente indefinido.'}
        verify_inputs(records, hashes, context.checkpoint)
        return result


def ensemble_moments(records, first, second, *, sample=True, execution=None):
    """Estimate cross-time moments of independent, aligned paths at two offsets."""
    records = tuple(records)
    if not records:
        raise ValueError('Seleccioná un conjunto de trayectorias.')
    if len(records) != len({id(item) for item in records}):
        raise ValueError('El conjunto contiene registros repetidos. Elegí realizaciones independientes.')
    start, end, rate = _align(records)
    if any(item.origin != start or len(item.values) != end-start for item in records):
        raise ValueError('Las trayectorias deben tener el mismo eje para comparar un instante físico.')
    if rate is not None and any(item.metadata.get('time_start_s') != records[0].metadata.get('time_start_s') for item in records):
        raise ValueError('Las trayectorias deben compartir su tiempo inicial.')
    if rate is None and any(item.metadata.get('sample_rate_hz') is not None for item in records):
        raise ValueError('El conjunto debe tener un reloj común o estar expresado completamente en muestras.')
    if len({item.metadata.get('amplitude_units','') for item in records}) > 1:
        raise ValueError('Las trayectorias del conjunto requieren las mismas unidades de amplitud.')
    offsets = [integer(value, 'Posición desde el inicio', minimum=0, maximum=end-start-1) for value in (first,second)]
    count = len(records)
    divisor = count-int(sample)
    if divisor < 1:
        raise ValueError('El divisor R−1 requiere dos o más realizaciones independientes.')
    context = execution or ExecutionContext()
    with context.reserve(320*count):
        hashes = tuple(content_digest(item, context.checkpoint) for item in records)
        substreams = set()
        for record in records:
            meta = record.metadata
            stream, seed = meta.get('substream'), meta.get('seed')
            model_key, generator = meta.get('settings_sha256'), meta.get('generator')
            if (isinstance(stream, (list, tuple)) and all(type(index) is int for index in stream)
                    and type(seed) is int and isinstance(model_key, str) and isinstance(generator, str)):
                identity = (model_key, generator, seed, tuple(stream))
                if identity in substreams:
                    raise ValueError('Dos trayectorias registran el mismo subflujo aleatorio.')
                substreams.add(identity)
        values = [np.asarray([record.values[index] for record in records]) for index in offsets]
        common_values, exponent = bounded(np.asarray(values), normalize=True)
        difference = common_values[1] - common_values[0]
        means, covariance, _, _ = _matrix_moments(values, 2, count, divisor, context)
        delta, delta_exponent = centered_bounded(difference)
        normalized_mean = _average(difference, context.checkpoint)
        increment_mean = [restore_scalar(value, exponent) for value in normalized_mean]
        increment_variance = restore_scalar(np.sum(abs(delta)**2)/divisor, 2*(exponent+delta_exponent))
        result = {'schema': 1, 'operation': 'ensemble_moments', 'input_hashes': list(hashes), 'replicas': count,
                  'offsets': offsets, 'divisor': divisor, 'sample_rate_hz': rate,
                  'means': means, 'covariance': _complex_document(covariance),
                  'increment_mean': [_scalar(value) for value in increment_mean],
                  'increment_variance': _scalar(increment_variance),
                  'scope': 'Estadísticas entre trayectorias a posiciones fijas. Se presupone independencia entre realizaciones.'}
        document = records[0].metadata.get('model')
        if (isinstance(document, dict) and set(document) == {'schema', 'process', 'parameters'} and document['schema'] == 1
                and all(item.metadata.get('operation') == 'stochastic_process'
                        and item.metadata.get('model') == document for item in records)):
            from .stochastic_processes import Process, process_moments
            try:
                model = Process(document['process'], document['parameters'])
                result['recorded_model_reference'] = process_moments(model, *offsets, rate=rate, execution=context)
            except (ValueError, TypeError, ArithmeticError, ResourceLimitError) as error:
                result['reference_notice'] = f'La referencia teórica no está disponible. {error}'
        verify_inputs(records, hashes, context.checkpoint)
        return result
