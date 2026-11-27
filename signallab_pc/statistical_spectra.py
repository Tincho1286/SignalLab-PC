"""Statistical interpretation of calibrated spectral estimates."""

from dataclasses import dataclass
import math

import numpy as np
from scipy.signal import correlate, lombscargle
from scipy.signal.windows import dpss
from scipy.stats import chi2

from .communications_data import integer, real
from .execution import ExecutionContext
from .model import Signal
from .operation_provenance import content_digest, settings_digest, verify_inputs
from .spectral_scaling import bounded, centered_bounded, restore_scale
from .stochastic_covariance import _align
from .system_clock import common_rate
from .window_signals import generate_window


def white_noise_confidence(spectrum, *, model, coverage=.95, execution=None):
    """Pointwise chi-square bounds for disjoint rectangular white-noise estimates."""
    if not isinstance(spectrum, Signal) or spectrum.data_kind != 'density' or spectrum.units != 'Hz':
        raise ValueError('Cargá una PSD calibrada en Hz.')
    metadata = spectrum.metadata
    estimator = metadata.get('estimator')
    if estimator not in ('bartlett','periodogram','welch') or metadata.get('window') != 'boxcar' or metadata.get('overlap') != 0:
        raise ValueError('Las bandas exactas para ruido blanco requieren bloques rectangulares disjuntos.')
    if model not in ('real_gaussian_white','proper_complex_gaussian_white'):
        raise ValueError('Declarar ruido blanco gaussiano real o complejo propio, con media cero.')
    real_input = model == 'real_gaussian_white'
    if metadata.get('real_input') is not real_input:
        raise ValueError('El modelo de ruido no corresponde al tipo de señal registrado.')
    coverage = real(coverage,'Cobertura',minimum=0,maximum=1,positive=True)
    if coverage == 1:
        raise ValueError('La cobertura debe ser menor que uno.')
    length = integer(metadata.get('segment'),'Longitud de segmento')
    blocks = integer(metadata.get('segments_used'),'Segmentos usados')
    unilateral = metadata.get('sidedness','').startswith('one-sided')
    size = length//2+1 if unilateral else length
    if len(spectrum.values) != size or np.any(spectrum.values.imag) or np.any(spectrum.values.real<0):
        raise ValueError('La grilla o los valores de la PSD no corresponden al estimador declarado.')
    tail = (1-coverage)/2
    context = execution or ExecutionContext()
    with context.reserve(160*size):
        digest = content_digest(spectrum, context.checkpoint)
        ordinary_df = 2*blocks
        degree = np.full(size,ordinary_df,dtype=int)
        dc = 0 if unilateral else length//2
        used = np.ones(size,dtype=bool)
        if real_input:
            degree[dc] = blocks
            if length%2==0:
                degree[-1 if unilateral else 0] = blocks
        if metadata.get('remove_segment_mean'):
            used[dc] = False
        lower = np.empty(size)
        upper = np.empty(size)
        for degrees in (blocks,ordinary_df):
            context.checkpoint()
            mask = degree==degrees
            power = spectrum.values.real[mask]
            with np.errstate(over='ignore',under='ignore'):
                lower[mask] = power*(degrees/chi2.isf(tail,degrees))
                upper[mask] = power*(degrees/chi2.ppf(tail,degrees))
        used &= np.isfinite(lower) & np.isfinite(upper)
        verify_inputs((spectrum,),(digest,),context.checkpoint)
        return {'schema':1,'operation':'white_noise_spectral_confidence','input_hashes':[digest],
                'model':model,'coverage':coverage,'estimator':estimator,'segments':blocks,'start_hz':spectrum.origin,
                'step_hz':spectrum.step,'density_units':metadata.get('density_units','amplitud²/Hz'),
                'bounds':[{'lower':float(lo),'upper':float(hi),'degrees_of_freedom':int(df)} if ok else None
                          for lo,hi,df,ok in zip(lower,upper,degree,used,strict=True)],
                'scope':'Intervalo marginal por bin para ruido blanco gaussiano de media cero. La media retirada excluye DC.'}


@dataclass(frozen=True, slots=True)
class CrossSpectra:
    cross: Signal | None
    first: Signal | None
    second: Signal | None
    coherence: dict


def cross_spectra(first, second, *, rate=None, segment=None, overlap=None, window='hann', beta=5.,
                  remove_mean=False, execution=None):
    """Bilateral Welch products with Sxy = average(X conj(Y))."""
    start,end,_ = _align((first,second))
    recorded = common_rate(first,second)
    rate = real(recorded if rate is None else rate,'Frecuencia de muestreo (Hz)',positive=True)
    if recorded is not None and not math.isclose(rate,recorded,rel_tol=1e-12,abs_tol=0):
        raise ValueError('La frecuencia de muestreo no coincide con los registros.')
    count = end-start
    segment = min(256,count) if segment is None else integer(segment,'Longitud de segmento',maximum=count)
    overlap = segment//2 if overlap is None else integer(overlap,'Solape',minimum=0,maximum=segment-1)
    hop = segment-overlap
    blocks = 1+(count-segment)//hop
    spacing = real(rate/segment,'Separación entre bins',positive=True)
    origin = -((segment//2)/segment)*rate
    context = execution or ExecutionContext()
    x = first.values[start-first.origin:end-first.origin]
    y = second.values[start-second.origin:end-second.origin]
    with context.reserve(88*count + 480*segment):
        digests = tuple(content_digest(source,context.checkpoint) for source in (first,second))
        left, px = bounded(x,normalize=True)
        right, py = bounded(y,normalize=True)
        taper = generate_window(window,segment,beta=beta).values.real
        energy = real(float(np.dot(taper,taper)),'Energía de ventana',positive=True)
        cross = np.zeros(segment,dtype=complex)
        xx,yy = np.zeros(segment),np.zeros(segment)
        for i in range(blocks):
            context.checkpoint(90*i//blocks)
            row = slice(i*hop,i*hop+segment)
            a,b = left[row],right[row]
            if remove_mean:
                a,b = a-np.mean(a),b-np.mean(b)
            a,b = np.fft.fft(taper*a),np.fft.fft(taper*b)
            if remove_mean and window=='boxcar':
                a[0] = b[0] = 0.
            cross += (a*b.conj()-cross)/(i+1)
            xx += (abs(a)**2-xx)/(i+1)
            yy += (abs(b)**2-yy)/(i+1)

        settings = {'schema':1,'method':'welch','sample_rate_hz':rate,'window':window,'segment':segment,
                    'overlap':overlap,'remove_segment_mean':bool(remove_mean),'segments_used':blocks,
                    'unused_tail':count-((blocks-1)*hop+segment),'common_origin':start,'common_last_index':end-1,
                    'sidedness':'two-sided, FFT-shifted','input_hashes':list(digests),
                    'convention':'Sxy = average(X conj(Y)) / (Fs * window energy)'}
        if window=='kaiser':settings['beta']=float(beta)
        fraction, rate_shift = math.frexp(rate)
        unavailable = []

        def output(values, exponent, name, operation, units):
            physical = restore_scale(np.fft.fftshift(values),exponent-rate_shift,1/fraction,1/energy)
            if not np.isfinite(physical).all() or np.all(physical==0) and np.any(values!=0):
                unavailable.append(name)
                return None
            return Signal(physical,origin,spacing,'Hz',name,'frequency',metadata={
                **settings,'operation':operation,'density_units':units})

        ux,uy = (item.metadata.get('amplitude_units') or 'amplitud' for item in (first,second))
        cross_out = output(cross,px+py,'Densidad espectral cruzada','cross_spectral_density',f'{ux}·{uy}/Hz')
        first_out = output(xx,2*px,'Densidad de x','spectral_density',f'{ux}²/Hz')
        second_out = output(yy,2*py,'Densidad de y','spectral_density',f'{uy}²/Hz')

        coherence = {'operation':'magnitude_squared_coherence',**settings,'start_hz':origin,'step_hz':spacing,
                     'unrepresentable_outputs':unavailable,'values':None}
        if blocks>1:
            denominator=np.sqrt(xx)*np.sqrt(yy)
            valid=(denominator>0)
            if remove_mean and window=='boxcar':valid[0]=False
            with np.errstate(divide='ignore',invalid='ignore',under='ignore'):
                magnitude=np.divide(abs(cross),denominator,out=np.zeros_like(xx),where=valid)
            value=np.square(np.clip(magnitude,0,1))
            coherence['values']=[float(v) if defined else None for v,defined in
                                  zip(np.fft.fftshift(value),np.fft.fftshift(valid),strict=True)]
            coherence['scope']='Coherencia de magnitud al cuadrado. Si un canal tiene potencia nula, ese bin queda indefinido.'
        else:
            coherence['scope']='Se necesitan al menos dos bloques para estimar coherencia. El espectro cruzado sigue definido.'
        verify_inputs((first,second),digests,context.checkpoint)
        context.checkpoint(100)
        return CrossSpectra(cross_out,first_out,second_out,coherence)


def store_cross_spectra(project, result, inputs, *, execution=None, tool=None):
    """Publish coherence and its available spectra with both observed records."""
    from .statistics_results import store_statistics
    context = execution or ExecutionContext()
    report = result.coherence
    digest = settings_digest(['calculation',report])
    with project.stage_records(before_commit=context.checkpoint) as staged:
        sources, report_id = store_statistics(staged,report,inputs,'Coherencia y espectro cruzado',execution=context,tool=tool)
        ids = {}
        for label,spectrum in (('cross',result.cross),('first',result.first),('second',result.second)):
            if spectrum is not None:
                ids[label] = staged.add(spectrum,operation=spectrum.name,parents=(report_id,),tool=tool,
                                       verification=(content_digest(spectrum,context.checkpoint),(digest,),context.checkpoint))
    return {'source_ids':sources,'report_id':report_id,'spectrum_ids':ids}


ADVANCED_PSD = {'blackman_tukey':'Blackman–Tukey', 'multitaper':'Multitaper DPSS', 'ar':'PSD autorregresiva'}


def _lag_density(values, lag, bins, context):
    count=len(values)
    context.checkpoint(15)
    raw=correlate(values,values,mode='full',method='fft')[count-1:count+lag]/count
    raw[0]=float(np.mean(abs(values)**2))
    lags=np.arange(lag+1)
    raw *= 1-lags/(lag+1)
    padded=np.zeros(bins,dtype=complex)
    padded[:lag+1]=raw
    if lag:
        padded[-lag:]=np.conj(raw[:0:-1])
    density=np.fft.fft(padded).real
    tolerance=64*np.finfo(float).eps*float(np.sum(abs(padded)))
    if np.min(density)<-tolerance:
        raise FloatingPointError('La ventana lag dio una densidad negativa fuera del error de redondeo.')
    return np.maximum(density,0.)


def advanced_density(source, *, method, rate=None, nfft=None, max_lag=None,
                     bandwidth=None, tapers=None, order=None, remove_mean=False, execution=None):
    """Calibrated bilateral density by lag window, DPSS average or an AR model."""
    _align((source,))
    if method not in ADVANCED_PSD:
        raise ValueError('Estimador estadístico de PSD desconocido.')
    fs=common_rate(source)
    rate=real(fs if rate is None else rate,'Frecuencia de muestreo (Hz)',positive=True)
    if fs is not None and not math.isclose(fs,rate,rel_tol=1e-12,abs_tol=0):
        raise ValueError('La frecuencia de muestreo no coincide con el registro.')
    n=len(source.values)
    if method=='blackman_tukey':
        lag=min(n-1, max(0,n//4)) if max_lag is None else integer(max_lag,'Retardo máximo',minimum=0,maximum=n-1)
        minimum=2*lag+1
        settings={'max_lag':lag,'lag_window':'bartlett','covariance_divisor':'N'}
        scratch=256*n
    elif method=='multitaper':
        nw=min(3.,max(.5,n/4)) if bandwidth is None else real(bandwidth,'Producto tiempo-ancho de banda NW',positive=True)
        if not .5<=nw<n/2:
            raise ValueError('DPSS requiere 0,5 ≤ NW < N/2.')
        k=max(1,int(2*nw)-1) if tapers is None else integer(tapers,'Cantidad de ventanas DPSS',maximum=n)
        minimum=n
        settings={'time_bandwidth':nw,'tapers':k,'weights':'equal','window_normalization':'unit energy'}
        scratch=192*n+48*n*k
    else:
        order=min(8,n//4) if order is None else integer(order,'Orden AR',minimum=0,maximum=max(0,n-2))
        minimum=order+1
        settings={'ar_order':order,'ar_algorithm':'burg','dc_line_excluded':True}
        remove_mean=True
        scratch=224*n+32*order**2
    bins=max(n,minimum) if nfft is None else integer(nfft,'Cantidad de bins',minimum=minimum)
    spacing=real(rate/bins,'Separación entre bins',positive=True)
    ctx=execution or ExecutionContext()
    with ctx.reserve(scratch+192*bins):
        digest=content_digest(source,ctx.checkpoint)
        if method=='ar':
            from .ar_estimation import fit
            fitted=ctx.run(lambda:fit(source,order,method='burg'))
            if not fitted['stationary'] or fitted['near_exact']:
                raise ValueError('El ajuste AR no identifica una PSD estacionaria con varianza positiva.')
            denominator=abs(np.fft.fft(fitted['a'],bins))
            logs=fitted['innovation_variance']['log_value']-math.log(rate)-2*np.log(denominator)
            with np.errstate(over='ignore',under='ignore'):
                power=np.exp(logs)
            settings.update(a=fitted['a'],innovation_variance=fitted['innovation_variance'])
        else:
            values,exponent=(centered_bounded(source.values) if remove_mean else bounded(source.values,normalize=True))
            if method=='blackman_tukey':
                normalized=_lag_density(values,lag,bins,ctx)
            else:
                taperset,concentration=dpss(n,nw,Kmax=k,norm=2,return_ratios=True)
                ctx.checkpoint(15)
                normalized=np.zeros(bins)
                for index,taper in enumerate(taperset):
                    ctx.checkpoint(15+80*index//k)
                    energy=float(np.dot(taper,taper))
                    candidate=abs(np.fft.fft(values*taper,bins))**2/energy
                    normalized += (candidate-normalized)/(index+1)
                settings['spectral_concentration']=np.asarray(concentration).tolist()
            fraction,shift=math.frexp(rate)
            power=restore_scale(normalized,2*exponent-shift,1/fraction).real
        if np.any(~np.isfinite(power)):
            raise FloatingPointError('La PSD no cabe en el rango numérico de amplitud por Hz.')
        verify_inputs((source,),(digest,),ctx.checkpoint)
        ctx.checkpoint(100)
        units=source.metadata.get('amplitude_units') or 'amplitud'
        return Signal(np.fft.fftshift(power),-((bins//2)/bins)*rate,spacing,'Hz',ADVANCED_PSD[method],
                      'frequency',metadata={'operation':'spectral_density','estimator':method,'nfft':bins,
                          'density_units':f'{units}²/Hz','density_convention':'per_coordinate',
                          'sample_rate_hz':rate,'sidedness':'two-sided, FFT-shifted','input_hashes':[digest],
                          'remove_mean':bool(remove_mean),'input_samples':n,**settings})


def lomb_periodogram(source, timestamps, *, low, high, points=1025, execution=None):
    """Generalized Lomb–Scargle normalized against a floating constant."""
    _align((source,))
    if np.any(source.values.imag):
        raise ValueError('Lomb–Scargle requiere observaciones reales.')
    n=len(source.values)
    if n<4:
        raise ValueError('Lomb–Scargle requiere al menos cuatro observaciones.')
    count=integer(points,'Puntos de frecuencia',minimum=2)
    lo,hi=real(low,'Frecuencia mínima',positive=True),real(high,'Frecuencia máxima',positive=True)
    if lo>=hi:
        raise ValueError('La frecuencia mínima debe ser menor que la máxima.')
    block=min(64,max(1,262_144//n))
    ctx=execution or ExecutionContext()
    with ctx.reserve(192*n+128*n*block+128*count):
        digest=content_digest(source,ctx.checkpoint)
        if np.iscomplexobj(timestamps):
            raise ValueError('Los tiempos deben ser reales.')
        times=np.asarray(timestamps,dtype=float)
        if times.shape!=(n,) or not np.all(np.isfinite(times)) or not np.all(times[:-1]<times[1:]):
            raise ValueError('Ingresá un tiempo finito y estrictamente creciente para cada observación.')
        span=float(times[-1])-float(times[0])
        cycles=hi*span
        if not math.isfinite(span) or not math.isfinite(math.tau*cycles) or lo*span<1e-7:
            raise ValueError('El intervalo de frecuencias y tiempos excede la resolución de la regresión sinusoidal.')
        values,_=centered_bounded(source.values)
        if not np.any(values):
            raise ValueError('El registro constante no define una potencia normalizada.')
        grid=np.linspace(lo,hi,count)
        phase=math.tau*(grid*span)
        time=(times-times[0])/span
        powers=np.empty(count)
        for offset in range(0,count,block):
            ctx.checkpoint(95*offset//count)
            end=min(count,offset+block)
            powers[offset:end]=lombscargle(time,values.real,phase[offset:end],normalize=True,floating_mean=True)
        if not np.all(np.isfinite(powers)) or np.any(powers>1+1e-9) or np.any(powers< -1e-9):
            raise ValueError('La regresión de algunos bins es degenerada para esta grilla temporal.')
        verify_inputs((source,),(digest,),ctx.checkpoint)
        return Signal(np.clip(powers,0,1),lo,(hi-lo)/(count-1),'Hz','Lomb–Scargle normalizado','frequency',
                      metadata={'operation':'irregular_periodogram','input_hashes':[digest],'timestamps_s':times.tolist(),
                                'meaning':'Fracción de error cuadrático explicada, con media flotante. Es adimensional.'})
