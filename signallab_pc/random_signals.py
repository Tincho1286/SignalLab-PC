"""Realizaciones pseudoaleatorias y estadísticas de registros finitos."""
import math
import numpy as np
from .model import Signal
from .resources import ensure_working_set
from .spectral_scaling import bounded, centered_bounded, range_status, restore_scalar, restore_scale

def generate(kind,count,mean,std,probability,seed,origin=0):
    if count<1:raise ValueError('La cantidad de muestras debe ser positiva.')
    ensure_working_set(count,live_arrays=6)
    if seed<0:raise ValueError('La semilla debe ser un entero no negativo.')
    rng=np.random.Generator(np.random.PCG64(seed))
    if kind=='bernoulli':
        if not np.isfinite(probability) or not 0<=probability<=1:raise ValueError('La probabilidad debe estar entre 0 y 1.')
        values=rng.binomial(1,probability,count);expected_mean=probability;expected_variance=probability*(1-probability)
    else:
        if not np.isfinite([mean,std]).all() or std<0:raise ValueError('La media debe ser finita y la desviación estándar no negativa.')
        with np.errstate(over='ignore',invalid='ignore'):
            values=mean+std*(rng.standard_normal(count) if kind=='gaussian' else rng.uniform(-np.sqrt(3),np.sqrt(3),count))
            expected_mean=mean;expected_variance=std*std
        if not np.isfinite(expected_variance):raise ValueError('La varianza teórica excede la precisión numérica disponible.')
    if not np.isfinite(values).all():raise ValueError('Las amplitudes exceden la precisión numérica disponible.')
    return Signal(values,origin,1,'n',{'gaussian':'Ruido gaussiano','uniform':'Ruido uniforme','bernoulli':'Secuencia Bernoulli'}[kind],'discrete','',
        {'operation':'random_generation','distribution':kind,'seed':seed,'generator':'PCG64','numpy_version':np.__version__,'theoretical_mean':expected_mean,'theoretical_variance':expected_variance,'scope':'Una realización finita de muestras pseudoaleatorias independientes; no prueba estacionariedad ni ergodicidad.'})

def statistics(source,component,bins,*,histogram_notice=None):
    values=source.values;n=len(values)
    ensure_working_set(n,live_arrays=10)
    scaled, exponent = bounded(values, normalize=True)
    from .record_measurements import _average
    average = _average(values, True)
    centered, centered_exponent = centered_bounded(values)
    variance_normalized = float(np.sum(centered.real**2 + centered.imag**2))
    power_normalized = float(np.mean(scaled.real**2 + scaled.imag**2))
    result = {'samples': n, 'mean_real': average.real, 'mean_imag': average.imag}
    statuses = {}
    for key, value, shift in (
        ('variance_N', variance_normalized/n, 2*centered_exponent),
        ('variance_N_minus_1', variance_normalized/(n-1) if n > 1 else None, 2*centered_exponent),
        ('mean_square', power_normalized, 2*exponent),
        ('rms', math.sqrt(power_normalized), exponent),
    ):
        magnitude = restore_scalar(value, shift) if value is not None else None
        status = range_status(magnitude, value) if value is not None else 'undefined'
        result[key] = magnitude if status != 'overflow' else None
        statuses[key] = status
    from .auxiliary import optional
    def histogram():
        if histogram_notice:raise ValueError(histogram_notice)
        if isinstance(bins,bool) or not isinstance(bins,(int,np.integer)) or bins<1:
            raise ValueError('La cantidad de intervalos del histograma debe ser un entero positivo.')
        ensure_working_set(n+int(bins),live_arrays=10)
        data={'real':values.real,'imag':values.imag,'magnitude':np.abs(values)}[component]
        with np.errstate(all='ignore'):density,edges=np.histogram(data,bins=bins,density=True)
        if not np.isfinite(density).all() or not np.isfinite(edges).all():
            raise ValueError('El histograma no es representable con esta escala de amplitudes.')
        return density,edges
    histogram_data,notice=optional('Histograma',histogram)
    density,edges=histogram_data if histogram_data is not None else (np.array([]),np.array([]))
    return {**result,'range_status':statuses,
        'histogram_notice':notice,'histogram_component':component,'histogram_edges':edges.tolist(),'histogram_density':density.tolist(),
        'scope':'Estadísticas del registro: varianza = promedio de |x−media|². N−1 es la corrección habitual bajo hipótesis de muestras independientes e idénticamente distribuidas; no demuestra esas hipótesis.'}


def autocorrelation(source,max_lag=None,remove_mean=False,denominator='N',normalize=False):
    from scipy.signal import correlate
    from .system_clock import common_rate, lag_clock
    if source.domain!='discrete':raise ValueError('Se requiere un registro discreto.')
    n=source.values.size;lag=min(50,n-1) if max_lag is None else max_lag
    if lag<0 or lag>=n:raise ValueError(f'El retardo máximo debe estar entre 0 y {n-1}.')
    if denominator not in ('N','overlap'):raise ValueError('Normalización desconocida.')
    ensure_working_set(2*n,live_arrays=16)
    from .record_measurements import _average
    measured_mean = _average(source.values, True)
    values, exponent = (centered_bounded(source.values) if remove_mean
                        else bounded(source.values, normalize=True))
    zero=float(np.mean(np.abs(values)**2))
    if normalize and zero==0:raise ValueError('No se puede normalizar: la potencia o varianza del registro es cero.')
    raw=correlate(values,values,mode='full',method='fft')
    delays=np.arange(-lag,lag+1);counts=n-np.abs(delays)
    result=raw[n-1-lag:n+lag]/(n if denominator=='N' else counts)
    result[lag]=zero
    underflow = 0
    if normalize:result=result/zero;result[lag]=1
    else:
        normalized = result
        result = restore_scale(normalized, 2*exponent)
        underflow = int(np.count_nonzero((result == 0) & (normalized != 0)))
    if not np.isfinite(result).all():raise ValueError('La correlación excede la precisión numérica disponible.')
    title='Autocovarianza estimada' if remove_mean else 'Autocorrelación estimada'
    if normalize:title+=' normalizada'
    metadata={'operation':'estimated_autocovariance' if remove_mean else 'estimated_autocorrelation','input_samples':int(n),'maximum_lag':int(lag),'remove_sample_mean':bool(remove_mean),'sample_mean':[float(measured_mean.real),float(measured_mean.imag)],'denominator':'N' if denominator=='N' else 'N−|k|','divide_by_zero_lag':bool(normalize),'convention':'sum x[n+k]*conj(x[n]) over the overlap, divided by N or N−|k|; optional subtraction of the sample mean','method':'FFT; finite precision','scope':'Estimación sobre un registro finito. Restar la media muestral altera el sesgo; N−|k| no garantiza insesgamiento cuando la media se estima con este registro. Los retardos grandes usan menos pares.'}
    if underflow:
        metadata['scope'] += f' {underflow} retardos no nulos se redondearon a cero por el rango de float64.'
        metadata['underflowed_samples'] = underflow
    metadata.update(lag_clock(common_rate(source), -lag, result.size))
    return Signal(result,-lag,1,'retardo k',title,'discrete','',metadata)
