"""Herramientas de registros finitos para los programas de Sistemas I y II."""
import math
import numpy as np
from scipy import signal as sp
from scipy.fft import fft,ifft,fftshift,fftfreq,next_fast_len
from .model import Signal
from .resources import ensure_working_set
from .operations import convolution_clock
from .jobs import checkpoint
from .signal_semantics import require_temporal
from .spectral_scaling import bounded, restore_scale


def analytic_signal(source):
    from .distributions import regular_only
    require_temporal(source)
    regular_only(source,'La transformada de Hilbert numérica')
    if source.domain not in ('continuous','discrete') or source.step<=0:raise ValueError('Ingresá una señal temporal con paso positivo.')
    if np.any(source.values.imag):raise ValueError('Hilbert requiere una entrada real. No se descarta la parte imaginaria.')
    ensure_working_set(int(source.values.size),live_arrays=12);checkpoint(0)
    scale=float(np.max(abs(source.values.real)))
    analytic=sp.hilbert(source.values.real/scale)*scale if scale else source.values.copy()
    analytic.real=source.values.real
    checkpoint(.8)
    metadata=dict(source.metadata,operation='hilbert_fft',extension='periodic',input_length=int(source.values.size))
    outputs=[]
    for values,name in [(analytic,'Señal analítica x + jH{x}'),(analytic.imag,'Transformada de Hilbert'),(abs(analytic),'Envolvente |x + jH{x}|')]:
        outputs.append(Signal(values,source.origin,source.step,source.units,name,source.domain,metadata=metadata.copy()))
    return outputs


def block_convolution(source,kernel,length,method):
    if source.domain!='discrete' or kernel.domain!='discrete':raise ValueError('La convolución por bloques requiere dos secuencias discretas.')
    if isinstance(length,bool) or int(length)!=length or length<1:raise ValueError('Las muestras nuevas por bloque deben ser un entero positivo.')
    if method not in ('ola','ols'):raise ValueError('Método de bloques no admitido.')
    require_temporal(source);require_temporal(kernel)
    clock=convolution_clock(source,kernel)
    length=int(length);m=kernel.values.size;n=source.values.size;total=n+m-1
    size=next_fast_len(length+m-1)
    ensure_working_set(int(total+size+length),live_arrays=12)
    samples, source_exponent=bounded(source.values)
    coefficients, kernel_exponent=bounded(kernel.values)
    response=fft(coefficients,size);output=np.zeros(total,dtype=complex)
    count=math.ceil((n if method=='ola' else total)/length)
    for block in range(count):
        checkpoint(block/count);start=block*length
        if method=='ola':
            chunk=samples[start:start+length];part=ifft(fft(chunk,size)*response)
            end=min(total,start+chunk.size+m-1);output[start:end]+=part[:end-start]
        else:
            # M−1 muestras de historia y L nuevas. Fuera del registro se usa cero.
            chunk=np.zeros(length+m-1,dtype=complex);left=start-(m-1);lo=max(0,left);hi=min(n,start+length)
            if hi>lo:chunk[lo-left:hi-left]=samples[lo:hi]
            part=ifft(fft(chunk,size)*response);valid=min(length,total-start)
            output[start:start+valid]=part[m-1:m-1+valid]
    output=restore_scale(output,source_exponent+kernel_exponent)
    if not np.any(source.values.imag) and not np.any(kernel.values.imag):output=output.real
    if not np.all(np.isfinite(output)):raise FloatingPointError('La convolución excede el rango numérico finito.')
    metadata={**clock,'operation':'block_convolution','method':method,'block_new_samples':length,'fft_length':size,'blocks':count,'kernel_length':int(m),'input_length':int(n),'zero_extension':True,'overlap':int(m-1)}
    return Signal(output,source.origin+kernel.origin,1,'n','Convolución por '+('solapamiento-suma' if method=='ola' else 'solapamiento-almacenamiento'),'discrete',metadata=metadata)


def time_frequency(source,length,overlap,nfft,window,beta=5,*,boundary='tail'):
    from .stft_tools import analyze
    return analyze(source,length,overlap,nfft,window,beta,boundary=boundary)


def spectrum_slice(result,index):
    from .stft_tools import spectrum
    return spectrum(result,index)
