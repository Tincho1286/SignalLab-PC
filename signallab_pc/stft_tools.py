"""Finite-record STFT, explicit clocks, calibrated density and weighted synthesis."""
from copy import deepcopy
from fractions import Fraction
import math
import numpy as np
from scipy import signal as sp
from scipy.fft import fft,ifft,fftshift,ifftshift,fftfreq
from .model import Signal
from .resources import ensure_working_set
from .jobs import checkpoint
from .spectral_scaling import bounded,restore_scale


def integer(value,label,minimum=0):
    if isinstance(value,(bool,np.bool_)) or int(value)!=value or value<minimum:
        raise ValueError(label+' debe ser un entero '+('positivo.' if minimum else 'no negativo.'))
    return int(value)


def analyze(source,length,overlap,nfft,window,beta=5,*,boundary='tail'):
    from .distributions import regular_only
    from .signal_semantics import require_temporal
    require_temporal(source);regular_only(source,'La STFT de muestras')
    if source.domain not in ('continuous','discrete') or source.step<=0:raise ValueError('Se necesita una señal temporal con paso positivo.')
    length=integer(length,'La longitud de ventana',2);overlap=integer(overlap,'El solapamiento');nfft=integer(nfft,'Los puntos FFT',2)
    n=len(source.values)
    if length>n:raise ValueError('La ventana no puede superar la longitud de la entrada.')
    if overlap>=length:raise ValueError('El solapamiento debe ser menor que la longitud de ventana.')
    if nfft<length:raise ValueError('Los puntos FFT deben ser al menos la longitud de ventana.')
    if boundary not in ('tail','centered'):raise ValueError('Tratamiento de extremos no admitido.')
    if window not in ('boxcar','hann','hamming','blackman','bartlett','kaiser'):raise ValueError('Ventana no admitida.')
    if not np.isfinite(beta) or beta<0:raise ValueError('β debe ser finito y no negativo.')
    hop=length-overlap;left=length//2 if boundary=='centered' else 0
    right=length//2 if boundary=='centered' else 0
    frames=1+math.ceil((n+left+right-length)/hop)
    ensure_working_set(int(nfft*frames+n+nfft),live_arrays=9)
    weights=sp.get_window(('kaiser',beta) if window=='kaiser' else window,length,fftbins=True)
    gain=float(weights.sum());energy=float(np.sum(weights**2))
    if not math.isfinite(gain) or gain<=0 or not energy>0:raise ValueError('La ventana no tiene ganancia y energía positivas.')
    values=np.empty((nfft,frames),complex)
    for column in range(frames):
        checkpoint(column/frames);offset=column*hop-left;chunk=np.zeros(length,complex)
        lo=max(0,offset);hi=min(n,offset+length)
        if hi>lo:chunk[lo-offset:hi-offset]=source.values[lo:hi]
        scaled,exponent=bounded(chunk)
        values[:,column]=restore_scale(fftshift(fft(scaled*weights,nfft))/gain,exponent)
        if not np.all(np.isfinite(values[:,column])):raise ValueError('El espectro de una ventana supera el rango numérico disponible.')
    dt=source.step if source.domain=='continuous' else 1.
    frequency=fftshift(fftfreq(nfft,d=dt))*math.tau
    offsets=np.arange(frames)*hop-left
    centers=source.origin+(offsets+(length-1)/2)*source.step
    if not np.all(np.isfinite(frequency)) or not np.all(np.isfinite(centers)) or frames>1 and np.any(np.diff(centers)<=0):
        raise ValueError('El eje de la STFT excede la resolución o el rango numérico.')
    metadata=dict(operation='stft',window=window,beta=float(beta) if window=='kaiser' else None,
        window_length=length,window_gain=gain,window_energy=energy,overlap=overlap,hop=hop,nfft=nfft,frames=frames,
        input_length=n,input_origin=source.origin,input_step=source.step,input_domain=source.domain,input_units=source.units,
        input_name=source.name,input_clock={key:deepcopy(source.metadata[key]) for key in ('sample_rate_hz','time_start_s') if key in source.metadata},
        boundary=boundary,left_padding=left,last_frame_zeros=max(0,(frames-1)*hop-left+length-n),
        normalization='FFT(x_segment * window) / sum(window)',phase_reference='local segment index starts at zero',
        frequency_units='rad/s' if source.domain=='continuous' else 'rad/muestra',time_units=source.units)
    return dict(values=values,frequency=frequency,centers=centers,metadata=metadata,weights=weights,source=source.copy_with(metadata=deepcopy(source.metadata)))


def axes(result,physical=False):
    m=result['metadata'];frequency=result['frequency'];centers=result['centers']
    if not physical or m['input_domain']=='continuous':return frequency,centers,m['frequency_units'],m['time_units'],1/m['input_step']
    from .system_clock import validate_clock_resolution
    clock=m.get('input_clock',{});rate=clock.get('sample_rate_hz')
    if rate is None:raise ValueError('Para ver segundos y rad/s, la secuencia debe tener Fs registrada.')
    from .sampling import positive_finite
    rate=positive_finite(rate,'Fs registrada');start=float(clock.get('time_start_s',m['input_origin']/rate))
    validate_clock_resolution(start,rate,m['input_length'])
    offsets=np.arange(m['frames'])*m['hop']-m['left_padding']+(m['window_length']-1)/2
    with np.errstate(over='ignore',invalid='ignore'):
        centers=start+offsets/rate;frequency=frequency*rate
    if not np.all(np.isfinite(centers)) or not np.all(np.isfinite(frequency)) or len(centers)>1 and np.any(np.diff(centers)<=0):
        raise ValueError('El reloj no permite distinguir los ejes físicos de esta STFT.')
    return frequency,centers,'rad/s','s',rate


def logarithmic_magnitude(values):
    a=np.abs(values.real);b=np.abs(values.imag);high=np.maximum(a,b);low=np.minimum(a,b)
    with np.errstate(divide='ignore',invalid='ignore',under='ignore'):
        return np.where(high>0,np.log(high)+.5*np.log1p((low/high)**2),-np.inf)


def map_values(result,scale='relative_db',physical=False,dynamic_range=100):
    if not math.isfinite(dynamic_range) or dynamic_range<=0:raise ValueError('El rango visible en dB debe ser positivo y finito.')
    _,_,frequency_units,_,rate=axes(result,physical)
    if result['metadata']['input_domain']=='discrete' and not physical:rate=1.
    logamp=logarithmic_magnitude(result['values']);m=result['metadata'];finite=logamp[np.isfinite(logamp)]
    peak=float(np.max(finite)) if finite.size else 0.
    if scale=='relative_db':
        data=np.maximum(20/math.log(10)*(logamp-peak),-dynamic_range)
        return data,'Nivel relativo visible (dB; piso recortado)',(-dynamic_range,0)
    if scale=='amplitude':logdata=logamp;label='Amplitud |FFT(x·w)/Σw|'
    elif scale in ('density','density_db'):
        logdata=2*logamp+2*math.log(m['window_gain'])-math.log(math.tau)-math.log(rate)-math.log(m['window_energy'])
        label='Densidad bilateral (unidad² / '+frequency_units+')'
        if scale=='density_db':
            data=10/math.log(10)*logdata;finite=data[np.isfinite(data)];top=float(np.max(finite)) if finite.size else 0.
            return np.maximum(data,top-dynamic_range),'Densidad en dB respecto de 1 unidad² / '+frequency_units+' (piso recortado)',(top-dynamic_range,top)
    else:raise ValueError('Escala de espectrograma no admitida.')
    if np.any(logdata>math.log(np.finfo(float).max)):raise ValueError('La escala lineal excede float64. Elegí la escala en dB.')
    with np.errstate(under='ignore'):data=np.exp(logdata)
    top=float(data.max())
    return data,label,(0,top if top>0 else 1)


def frame_signals(result,index):
    m=result['metadata'];index=integer(index,'La ventana seleccionada')
    if index>=m['frames']:raise ValueError('No existe esa ventana en el resultado.')
    source=result['source'];length=m['window_length'];offset=index*m['hop']-m['left_padding'];lo=max(0,offset);hi=min(m['input_length'],offset+length)
    chunk=np.zeros(length,complex)
    if hi>lo:chunk[lo-offset:hi-offset]=source.values[lo:hi]
    origin=m['input_origin']+offset if m['input_domain']=='discrete' else m['input_origin']+offset*m['input_step'];clock=deepcopy(m['input_clock'])
    if m['input_domain']=='discrete' and 'sample_rate_hz' in clock:
        rate=float(clock['sample_rate_hz']);start=float(clock.get('time_start_s',m['input_origin']/rate));clock['time_start_s']=start+offset/rate
    common=dict(clock,operation='stft_frame',frame=index,zero_padding_left=max(0,-offset),zero_padding_right=max(0,offset+length-m['input_length']),phase_reference='original temporal coordinates')
    return [Signal(values,origin,m['input_step'],m['input_units'],title,m['input_domain'],metadata=deepcopy(common))
            for values,title in ((chunk,'Tramo de entrada'),(result['weights'],'Ventana aplicada'),(chunk*result['weights'],'Tramo enventanado'))]


def density_spectrum(result,index,physical=False):
    reference=spectrum(result,index,physical=physical)
    data,_,_=map_values(dict(result,values=result['values'][:,index:index+1]),'density',physical)
    reference=reference.copy_with(values=data[:,0],name='Densidad bilateral de la ventana',metadata=dict(reference.metadata,operation='spectral_density',density_convention='per_coordinate',normalization='|FFT(x*w)|² / (2*pi*Fs*sum(w²)); Fs=1 for rad/sample',remove_mean=False))
    return reference


def spectrum(result,index,*,physical=False,phase='local'):
    m=result['metadata'];index=integer(index,'La ventana seleccionada')
    if index>=m['frames']:raise ValueError('No existe esa ventana en el resultado.')
    frequency,centers,unit,time_unit,_=axes(result,physical);values=result['values'][:,index].copy()
    meta=deepcopy(m);meta.update(frame=index,frame_center=float(centers[index]),frame_center_units=time_unit)
    if phase not in ('local','global'):raise ValueError('Referencia de fase no admitida.')
    if phase=='global':
        offset=index*m['hop']-m['left_padding']
        if physical and m['input_domain']=='discrete':
            clock=m['input_clock'];rate=Fraction(str(clock['sample_rate_hz']));start=clock.get('time_start_s')
            base=Fraction(str(start))*rate if start is not None else Fraction(m['input_origin'])
        elif m['input_domain']=='continuous':base=Fraction(str(m['input_origin']))/Fraction(str(m['input_step']))
        else:base=Fraction(m['input_origin'])
        reduced=float((base+offset)%m['nfft']);bins=np.rint(fftshift(fftfreq(m['nfft']))*m['nfft'])
        values*=np.exp(-1j*math.tau*(bins*reduced/m['nfft']))
        meta['phase_reference']='original temporal coordinates'
    return Signal(values,float(frequency[0]),float(frequency[1]-frequency[0]),unit,f'Espectro de ventana {index+1}','frequency',metadata=meta)


def synthesize(result):
    m=result['metadata'];n=m['input_length'];length=m['window_length'];nfft=m['nfft'];weights=np.asarray(result['weights'])
    values=np.asarray(result['values'])
    if values.shape!=(nfft,m['frames']) or not np.all(np.isfinite(values)):raise ValueError('La matriz STFT no coincide con sus parámetros o contiene valores no finitos.')
    ensure_working_set(n+nfft,live_arrays=12);coverage=np.zeros(n);accumulated=np.zeros(n,complex)
    bounded_values,exponent=bounded(values)
    for column in range(m['frames']):
        checkpoint(column/m['frames']);offset=column*m['hop']-m['left_padding'];lo=max(0,offset);hi=min(n,offset+length)
        if hi<=lo:continue
        part=ifft(ifftshift(bounded_values[:,column]))[:length]*m['window_gain'];win=weights[lo-offset:hi-offset]
        accumulated[lo:hi]+=part[lo-offset:hi-offset]*win;coverage[lo:hi]+=win**2
    threshold=np.finfo(float).eps*max(float(coverage.max()),np.finfo(float).tiny)*32
    missing=np.flatnonzero(coverage<=threshold)
    if missing.size:
        positions=', '.join(str(m['input_origin']+int(k) if m['input_domain']=='discrete' else m['input_origin']+int(k)*m['input_step']) for k in missing[:6])
        raise ValueError('La STFT no conserva información suficiente en '+str(len(missing))+' muestras ('+positions+'). Activá completar ambos extremos o aumentá el solapamiento. No se inventan esos valores.')
    reconstructed=restore_scale(accumulated/coverage,exponent)
    if not np.all(np.isfinite(reconstructed)):raise ValueError('La reconstrucción excede el rango numérico.')
    metadata=deepcopy(m['input_clock']);metadata.update(operation='inverse_stft',window=m['window'],hop=m['hop'],nfft=nfft,coverage_min=float(coverage.min()),coverage_max=float(coverage.max()),method='IFFT, weighted overlap-add and division by sum of squared windows')
    return Signal(reconstructed,m['input_origin'],m['input_step'],m['input_units'],'Reconstrucción STFT','discrete' if m['input_domain']=='discrete' else 'continuous',metadata=metadata)
