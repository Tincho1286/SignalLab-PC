"""Herramientas de registros finitos para los programas de Sistemas I y II."""
import math
import numpy as np
from scipy import signal as sp
from scipy.fft import fft,ifft,fftshift,fftfreq,next_fast_len
from .model import Signal
from .resources import ensure_working_set
from .jobs import checkpoint


def analytic_signal(source):
    from .distributions import regular_only
    regular_only(source,'La transformada de Hilbert numérica')
    if source.domain not in ('continuous','discrete') or source.step<=0:raise ValueError('Ingresá una señal temporal con paso positivo.')
    if np.any(source.values.imag):raise ValueError('Hilbert requiere una entrada real. No se descarta la parte imaginaria.')
    ensure_working_set(int(source.values.size),live_arrays=12);checkpoint(0)
    analytic=sp.hilbert(source.values.real);checkpoint(.8)
    metadata=dict(source.metadata,operation='hilbert_fft',extension='periodic',input_length=int(source.values.size))
    outputs=[]
    for values,name in [(analytic,'Señal analítica x + jH{x}'),(analytic.imag,'Transformada de Hilbert'),(abs(analytic),'Envolvente |x + jH{x}|')]:
        outputs.append(Signal(values,source.origin,source.step,source.units,name,source.domain,metadata=metadata.copy()))
    return outputs


def block_convolution(source,kernel,length,method):
    if source.domain!='discrete' or kernel.domain!='discrete':raise ValueError('La convolución por bloques requiere dos secuencias discretas.')
    if isinstance(length,bool) or int(length)!=length or length<1:raise ValueError('Las muestras nuevas por bloque deben ser un entero positivo.')
    if method not in ('ola','ols'):raise ValueError('Método de bloques no admitido.')
    length=int(length);m=kernel.values.size;n=source.values.size;total=n+m-1
    size=next_fast_len(length+m-1)
    ensure_working_set(int(total+size+length),live_arrays=12)
    response=fft(kernel.values,size);output=np.zeros(total,dtype=complex)
    count=math.ceil((n if method=='ola' else total)/length)
    for block in range(count):
        checkpoint(block/count);start=block*length
        if method=='ola':
            chunk=source.values[start:start+length];part=ifft(fft(chunk,size)*response)
            end=min(total,start+chunk.size+m-1);output[start:end]+=part[:end-start]
        else:
            # M−1 muestras de historia y L nuevas. Fuera del registro se usa cero.
            chunk=np.zeros(length+m-1,dtype=complex);left=start-(m-1);lo=max(0,left);hi=min(n,start+length)
            if hi>lo:chunk[lo-left:hi-left]=source.values[lo:hi]
            part=ifft(fft(chunk,size)*response);valid=min(length,total-start)
            output[start:start+valid]=part[m-1:m-1+valid]
    if not np.any(source.values.imag) and not np.any(kernel.values.imag):output=output.real
    metadata={'operation':'block_convolution','method':method,'block_new_samples':length,'fft_length':size,'blocks':count,'kernel_length':int(m),'input_length':int(n),'zero_extension':True,'overlap':int(m-1)}
    return Signal(output,source.origin+kernel.origin,1,'n','Convolución por '+('solapamiento-suma' if method=='ola' else 'solapamiento-almacenamiento'),'discrete',metadata=metadata)


def time_frequency(source,length,overlap,nfft,window,beta=5):
    from .distributions import regular_only
    regular_only(source,'La STFT de muestras')
    if source.domain not in ('continuous','discrete') or source.step<=0:raise ValueError('Se necesita una señal temporal con paso positivo.')
    n=int(source.values.size)
    if not 2<=length<=n:raise ValueError('La ventana debe tener entre 2 muestras y la longitud de la entrada.')
    if not 0<=overlap<length:raise ValueError('El solapamiento debe ser menor que la longitud de ventana y no negativo.')
    if nfft<length:raise ValueError('Los puntos FFT deben ser al menos la longitud de ventana.')
    if window not in ('boxcar','hann','hamming','blackman','bartlett','kaiser'):raise ValueError('Ventana no admitida.')
    if not np.isfinite(beta) or beta<0:raise ValueError('β debe ser finito y no negativo.')
    hop=length-overlap;frames=1+math.ceil((n-length)/hop)
    ensure_working_set(int(nfft*frames+n+nfft),live_arrays=5)
    weights=sp.get_window(('kaiser',beta) if window=='kaiser' else window,length,fftbins=True)
    gain=weights.sum()
    if not np.isfinite(gain) or gain<=0:raise ValueError('La ventana no tiene ganancia coherente positiva.')
    values=np.empty((nfft,frames),dtype=complex)
    for column in range(frames):
        checkpoint(column/frames);start=column*hop;chunk=np.zeros(length,dtype=complex);part=source.values[start:start+length];chunk[:len(part)]=part
        values[:,column]=fftshift(fft(chunk*weights,nfft))/gain
    dt=source.step if source.domain=='continuous' else 1.
    frequency=fftshift(fftfreq(nfft,d=dt))*2*np.pi
    centers=source.origin+(np.arange(frames)*hop+(length-1)/2)*source.step
    metadata={'operation':'stft','window':window,'beta':beta if window=='kaiser' else None,'window_length':length,'overlap':overlap,'hop':hop,'nfft':nfft,'frames':frames,'input_length':n,'input_origin':source.origin,'input_step':source.step,'input_domain':source.domain,'normalization':'FFT(x_segment * window) / sum(window)','phase_reference':'local segment index starts at zero','last_frame_zeros':max(0,(frames-1)*hop+length-n),'frequency_units':'rad/s' if source.domain=='continuous' else 'rad/muestra','time_units':source.units}
    return {'values':values,'frequency':frequency,'centers':centers,'metadata':metadata}


def spectrum_slice(result,index):
    meta=dict(result['metadata'],frame=int(index),frame_center=float(result['centers'][index]))
    f=result['frequency'];return Signal(result['values'][:,index],float(f[0]),float(f[1]-f[0]),meta['frequency_units'],f"Espectro de ventana {index+1}",'frequency',metadata=meta)
