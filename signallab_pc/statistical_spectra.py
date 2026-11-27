"""Statistical interpretation of calibrated spectral estimates."""

from dataclasses import dataclass
import math

import numpy as np
from scipy.stats import chi2

from .communications_data import integer, real
from .execution import ExecutionContext
from .model import Signal
from .operation_provenance import content_digest, settings_digest, verify_inputs
from .spectral_scaling import bounded, restore_scale
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
