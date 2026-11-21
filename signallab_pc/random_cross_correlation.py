"""Cross-correlation estimates on the common observed time interval."""
import numpy as np
from scipy.signal import correlate
from .model import Signal
from .filters import positive_integer
from .resources import ensure_working_set
from .spectral_scaling import bounded, centered_bounded, restore_scale


def cross_correlation(first,second,max_lag=None,remove_mean=False,denominator='N',normalize=False):
    if first.domain!='discrete' or second.domain!='discrete':raise ValueError('Se requieren dos registros discretos.')
    from .operations import _discrete
    from .system_clock import validate_discrete_clocks, lag_clock
    _discrete(first);_discrete(second)
    rate = validate_discrete_clocks(first,second)
    start=max(first.origin,second.origin);stop=min(first.origin+len(first.values),second.origin+len(second.values));n=int(stop-start)
    if n<1:raise ValueError('Los registros no tienen índices observados en común. Revisá sus orígenes.')
    lag=min(50,n-1) if max_lag is None else positive_integer(max_lag+1,'Cantidad de retardos')-1
    if lag>=n:raise ValueError('El retardo máximo debe ser menor que las '+str(n)+' muestras del intervalo común.')
    if denominator not in ('N','overlap'):raise ValueError('Divisor de correlación desconocido.')
    ensure_working_set(2*n,live_arrays=16)
    x=first.values[start-first.origin:stop-first.origin];y=second.values[start-second.origin:stop-second.origin]
    if remove_mean:
        x, ex = centered_bounded(x)
        y, ey = centered_bounded(y)
    else:
        x, ex = bounded(x, normalize=True)
        y, ey = bounded(y, normalize=True)
    px=float(np.mean(abs(x)**2));py=float(np.mean(abs(y)**2))
    factor=np.sqrt(px)*np.sqrt(py)
    if normalize and factor==0:raise ValueError('No se puede normalizar si una potencia o varianza del intervalo común es cero.')
    raw=correlate(x,y,mode='full',method='fft')[n-1-lag:n+lag]
    delays=np.arange(-lag,lag+1);values=raw/(n if denominator=='N' else n-abs(delays))
    values[lag]=np.mean(x*np.conj(y))
    underflow = 0
    if normalize:values/=factor
    else:
        normalized = values
        values = restore_scale(normalized, ex+ey)
        underflow = int(np.count_nonzero((values == 0) & (normalized != 0)))
    if not np.isfinite(values).all():raise ValueError('La correlación excede el rango numérico disponible.')
    title=('Covarianza cruzada' if remove_mean else 'Correlación cruzada')+' estimada'
    if normalize:title+=' normalizada'
    metadata={'operation':'estimated_cross_covariance' if remove_mean else 'estimated_cross_correlation','common_origin':int(start),'input_samples':n,'common_last_index':int(stop-1),'first_samples':len(first.values),'second_samples':len(second.values),'remove_sample_mean':bool(remove_mean),'maximum_lag':lag,'denominator':'N' if denominator=='N' else 'N−|k|','normalization':'sqrt(Px*Py) on common interval' if normalize else 'none','convention':'Rxy[k]=sum x[n+k]*conj(y[n]) over observed pairs, divided by N or N−|k|','scope':'Se recorta cada registro al intervalo de índices observado en ambos. Las medias y potencias se estiman en ese intervalo. No se inventan muestras para cubrir regiones sin observación. N−|k| no garantiza insesgamiento al estimar las medias. La correlación cruzada puede no ser par ni real. Su valor en cero no es la potencia de una señal.'}
    if underflow:
        metadata['scope'] += f' {underflow} retardos no nulos se redondearon a cero por el rango de float64.'
        metadata['underflowed_samples'] = underflow
    metadata.update(lag_clock(rate, -lag, values.size))
    return Signal(values,-lag,1,'retardo k',title,'discrete',metadata=metadata)
