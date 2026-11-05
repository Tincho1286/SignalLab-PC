"""Realizaciones pseudoaleatorias y estadísticas de registros finitos."""
import numpy as np
from .model import Signal
from .resources import ensure_working_set

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
    scale=float(max(np.max(np.abs(values.real)),np.max(np.abs(values.imag))))
    scaled=values/scale if scale else values
    average=np.mean(scaled);centered=scaled-average
    with np.errstate(over='ignore',invalid='ignore'):
        mean=average*scale;variance=float(np.mean(np.abs(centered)**2)*scale*scale);power=float(np.mean(np.abs(scaled)**2)*scale*scale)
    corrected_variance=variance*(n/(n-1)) if n>1 else None
    if not np.isfinite([mean.real,mean.imag,variance,power,corrected_variance if n>1 else 0.]).all():raise ValueError('Las estadísticas exceden la precisión numérica disponible. Reducí la escala de amplitudes.')
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
    result,notice=optional('Histograma',histogram)
    density,edges=result if result is not None else (np.array([]),np.array([]))
    return {'samples':n,'mean_real':float(mean.real),'mean_imag':float(mean.imag),'variance_N':variance,'variance_N_minus_1':corrected_variance,'mean_square':power,'rms':float(np.sqrt(power)),
        'histogram_notice':notice,'histogram_component':component,'histogram_edges':edges.tolist(),'histogram_density':density.tolist(),
        'scope':'Estadísticas del registro: varianza = promedio de |x−media|². N−1 es la corrección habitual bajo hipótesis de muestras independientes e idénticamente distribuidas; no demuestra esas hipótesis.'}


def autocorrelation(source,max_lag=None,remove_mean=False,denominator='N',normalize=False):
    from scipy.signal import correlate
    if source.domain!='discrete':raise ValueError('Se requiere un registro discreto.')
    n=source.values.size;lag=min(50,n-1) if max_lag is None else max_lag
    if lag<0 or lag>=n:raise ValueError(f'El retardo máximo debe estar entre 0 y {n-1}.')
    if denominator not in ('N','overlap'):raise ValueError('Normalización desconocida.')
    ensure_working_set(2*n,live_arrays=16)
    scale=float(max(np.max(np.abs(source.values.real)),np.max(np.abs(source.values.imag))))
    values=source.values/scale if scale else source.values.copy()
    average=np.mean(values)
    if remove_mean:values=values-average
    zero=float(np.mean(np.abs(values)**2))
    if normalize and zero==0:raise ValueError('No se puede normalizar: la potencia o varianza del registro es cero.')
    raw=correlate(values,values,mode='full',method='fft')
    delays=np.arange(-lag,lag+1);counts=n-np.abs(delays)
    result=raw[n-1-lag:n+lag]/(n if denominator=='N' else counts)
    result[lag]=zero
    if normalize:result=result/zero;result[lag]=1
    else:
        with np.errstate(over='ignore',invalid='ignore'):result=(result*scale)*scale
    if not np.isfinite(result).all():raise ValueError('La correlación excede la precisión numérica disponible.')
    measured_mean=average*scale
    title='Autocovarianza estimada' if remove_mean else 'Autocorrelación estimada'
    if normalize:title+=' normalizada'
    metadata={'operation':'estimated_autocovariance' if remove_mean else 'estimated_autocorrelation','input_samples':int(n),'maximum_lag':int(lag),'remove_sample_mean':bool(remove_mean),'sample_mean':[float(measured_mean.real),float(measured_mean.imag)],'denominator':'N' if denominator=='N' else 'N−|k|','divide_by_zero_lag':bool(normalize),'convention':'sum x[n+k]*conj(x[n]) over the overlap, divided by N or N−|k|; optional subtraction of the sample mean','method':'FFT; finite precision','scope':'Estimación sobre un registro finito. Restar la media muestral altera el sesgo; N−|k| no garantiza insesgamiento cuando la media se estima con este registro. Los retardos grandes usan menos pares.'}
    return Signal(result,-lag,1,'retardo k',title,'discrete','',metadata)
