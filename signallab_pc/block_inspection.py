"""Inspect one executed block, retaining the alignment of history and valid output."""
from copy import deepcopy
import numpy as np
from scipy.fft import fft,ifft
from .model import Signal
from .spectral_scaling import bounded,restore_scale
from .resources import ensure_working_set
from .jobs import checkpoint


def capture(source,kernel,result):
    return dict(source=source.copy_with(metadata=deepcopy(source.metadata)),kernel=kernel.copy_with(metadata=deepcopy(kernel.metadata)),result=result.copy_with(metadata=deepcopy(result.metadata)))


def inspect(trace,index):
    source,kernel,result=(trace[k] for k in ('source','kernel','result'));meta=result.metadata
    if isinstance(index,bool) or int(index)!=index or not 0<=index<meta['blocks']:raise ValueError('El bloque seleccionado no existe.')
    length=meta['block_new_samples'];m=meta['kernel_length'];size=meta['fft_length'];start=int(index)*length;method=meta['method'];n=len(source.values)
    ensure_working_set(size+length+m,live_arrays=14);checkpoint()
    if method=='ola':chunk=source.values[start:start+length].copy();offset=start
    else:
        offset=start-m+1;chunk=np.zeros(length+m-1,complex);lo=max(0,offset);hi=min(n,start+length)
        if hi>lo:chunk[lo-offset:hi-offset]=source.values[lo:hi]
    a,ea=bounded(chunk);b,eb=bounded(kernel.values);raw=restore_scale(ifft(fft(a,size)*fft(b,size)),ea+eb)
    if not np.all(np.isfinite(raw)):raise ValueError('La salida FFT de ese bloque excede el rango numérico.')
    if method=='ola':raw=raw[:len(chunk)+m-1];valid=raw;valid_start=start
    else:
        count=min(length,len(result.values)-start);valid=raw[m-1:m-1+count];valid_start=start
    def make(values,origin,name,reference):
        clock={k:v for k,v in reference.metadata.items() if k in ('sample_rate_hz','time_start_s')}
        if 'sample_rate_hz' in clock:
            rate=float(clock['sample_rate_hz']);clock['time_start_s']=float(clock.get('time_start_s',reference.origin/rate))+(origin-reference.origin)/rate
        return Signal(values,origin,1,'n',name,'discrete',metadata=dict(clock,operation='block_inspection',block=int(index),method=method))
    input_signal=make(chunk,source.origin+offset,'Entrada del bloque con historia' if method=='ols' else 'Entrada del bloque',source)
    raw_signal=make(raw,result.origin+offset,'Convolución circular FFT' if method=='ols' else 'Convolución del bloque',result)
    valid_signal=make(valid,result.origin+valid_start,'Salida válida del bloque' if method=='ols' else 'Contribución para sumar',result)
    stop=min(len(result.values),valid_start+len(valid));final=make(result.values[valid_start:stop],result.origin+valid_start,'Salida total en ese intervalo',result)
    return dict(signals=[input_signal,raw_signal,valid_signal,final],discard=m-1 if method=='ols' else 0,unused=len(raw)-(m-1)-len(valid) if method=='ols' else 0,
                new_samples=length,fft_size=size,block=int(index),blocks=meta['blocks'],method=method,
                explanation=('Se descartan las primeras M−1 salidas circulares. Se conservan las L nuevas, o las que faltan de la cola. La historia es parte de la entrada, no una salida adicional.' if method=='ols' else 'Esta contribución debe sumarse con las contribuciones de los otros bloques que caen en los mismos índices. Su cola puede diferir de la salida total; no se descarta.'))
