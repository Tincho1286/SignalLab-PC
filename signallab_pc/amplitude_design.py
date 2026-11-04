"""Band-specific desired amplitudes and absolute/relative/dB tolerance contracts."""
import numpy as np
from scipy import signal as sp
from .filters import Transfer
from .model import Signal
from .resources import ensure_working_set
from .jobs import checkpoint


def limits(kind,amplitudes,dp,ds,units):
    amplitudes=np.asarray(amplitudes,float)
    if amplitudes.size!=(2 if kind=='bandstop' else 1) or not np.isfinite(amplitudes).all() or np.any(amplitudes<=0):
        raise ValueError('Indicá una amplitud positiva y finita por banda de paso; el rechazabanda tiene dos amplitudes independientes.')
    if not np.isfinite([dp,ds]).all() or dp<=0 or ds<=0:raise ValueError('Las tolerancias deben ser positivas y finitas.')
    if units=='absolute':lower=amplitudes-dp;upper=amplitudes+dp;stop=ds
    elif units=='relative':lower=amplitudes*(1-dp);upper=amplitudes*(1+dp);stop=amplitudes.max()*ds
    elif units=='db':lower=amplitudes*10**(-dp/20);upper=amplitudes*10**(dp/20);stop=amplitudes.max()*10**(-ds/20)
    else:raise ValueError('Unidad de tolerancias no admitida.')
    if not np.isfinite(np.r_[lower,upper,stop]).all() or np.any(lower<=0) or stop<=0 or stop>=lower.min():
        raise ValueError('Los límites de paso deben ser positivos y el rechazo debe quedar por debajo de todas las bandas de paso. Revisá amplitudes y tolerancias.')
    return amplitudes,lower,upper,float(stop)


def masks(w,wp,ws,kind):
    if kind=='lowpass':return [w<=wp[0]],w>=ws[0]
    if kind=='highpass':return [w>=wp[0]],w<=ws[0]
    if kind=='bandpass':return [(w>=wp[0])&(w<=wp[1])],(w<=ws[0])|(w>=ws[1])
    return [w<=wp[0],w>=wp[1]],(w>=ws[0])&(w<=ws[1])


def evaluate_spec(system,spec):
    from .band_extrema import evaluate
    return evaluate(system,spec)


def scale_system(system,gain):
    if system.sos is not None:
        sections=system.sos.copy();sections[0,:3]*=gain
        result=Transfer.from_sos(sections,name=system.name,sample_period_s=system.sample_period_s);result.advance=system.advance;result.roc=system.roc;return result
    return Transfer(system.b*gain,system.a,system.domain,system.name,advance=system.advance,sample_period_s=system.sample_period_s,roc=system.roc)


# A ceiling on evaluated FFT grid points bounds the work for impractical masks.
# A search that hits it reports its tested range instead of claiming impossibility.
_AUTOMATIC_FIR_WORK = 128 * 1024**2


def _violates_samples(system, spec, wp, ws, nfft):
    """Reject only a measured violation, leaving acceptance to refined extrema."""
    from .band_extrema import fir_magnitude

    error = 64*np.finfo(float).eps*len(system.b)*np.sum(abs(system.b))

    def violates(grid, magnitude):
        passes, stop = masks(grid, wp, ws, spec['kind'])
        for mask, low, high in zip(passes, spec['pass_lower'], spec['pass_upper_bands']):
            if np.any(magnitude[mask] < low-error) or np.any(magnitude[mask] > high+error):
                return True
        return bool(np.any(magnitude[stop] > spec['stop_upper']+error))

    edges = np.r_[wp, ws]
    magnitude_at = fir_magnitude(system)
    if violates(edges, np.array([magnitude_at(w) for w in edges])):
        return True
    grid = np.linspace(0., np.pi, nfft//2+1)
    return violates(grid, abs(np.fft.rfft(system.b.real, n=nfft)))


def _search_fir(candidate, spec, wp, ws, limit=None):
    from scipy.fft import next_fast_len

    odd = spec['kind'] in ('highpass','bandstop')
    # A one-tap filter is constant and the stop limit is below every pass limit.
    length = 3 if odd else 2
    work = 0
    last = 1
    while limit is None or length <= limit:
        nfft = 2*next_fast_len(max(256,4*length), real=True)
        if limit is None and work+nfft > _AUTOMATIC_FIR_WORK:
            break
        checkpoint(work/_AUTOMATIC_FIR_WORK if limit is None else length/limit)
        work += nfft
        ensure_working_set(nfft, live_arrays=10)
        design = candidate(length)
        if not _violates_samples(design[0], spec, wp, ws, nfft):
            accepted, report = evaluate_spec(design[0], spec)
            if accepted:
                return length, design, report
        last = length
        length += 2 if odd else 1
    boundary = ('límite automático de cálculo' if limit is None else 'límite indicado')
    raise ValueError(f'No se encontró un FIR que cumpla hasta L={last} ({boundary}). '
                     'Probá otra ventana o ajustá las tolerancias o la transición.')


def design(wp,ws,dp,ds,method,period=1,taps=0,window='kaiser',search=0,*,amplitudes=(1,),units='absolute',analog=False):
    from .course_tools import bands,design_filter,compare_iir
    wp=np.asarray(wp,float);ws=np.asarray(ws,float)
    if analog:
        # Analog designer validates positive, ordered frequencies without Nyquist.
        if wp.size==1:kind='lowpass' if wp[0]<ws[0] else 'highpass'
        elif wp[0]<ws[0]<ws[1]<wp[1]:kind='bandstop'
        else:kind='bandpass'
    else:wp,ws,kind=bands(wp,ws)
    amplitudes,lower,upper,stop=limits(kind,amplitudes,dp,ds,units)
    spec={'kind':kind,'wp':wp.tolist(),'ws':ws.tolist(),'amplitudes':amplitudes.tolist(),'pass_lower':lower.tolist(),'pass_upper_bands':upper.tolist(),'stop_upper':stop,'tolerance_units':units,'dp':float(dp),'ds':float(ds)}
    if analog:spec.update(domain='analog',plot_range=[float(np.r_[wp,ws].min()/10),float(np.r_[wp,ws].max()*10)])
    if method=='kaiser' and not analog:
        if window not in ('boxcar','hann','hamming','blackman','bartlett','kaiser'):raise ValueError('Ventana no admitida.')
        is_kaiser = window == 'kaiser'
        automatic = not is_kaiser or not taps
        if is_kaiser and (taps<0 or search<0):
            raise ValueError('Longitud y cota de búsqueda deben ser no negativas.')
        if is_kaiser:
            width = float(np.min(abs(wp-ws)))
            error = min(float((amplitudes-lower).min()),float((upper-amplitudes).min()),stop)
            attenuation = 20*(np.log10(float(amplitudes.max()))-np.log10(error))
            estimated,beta = sp.kaiserord(max(8.,attenuation),width/np.pi)
        else:
            beta = 0.
        cutoff=(wp+ws)/2;chosen=('kaiser',beta) if window=='kaiser' else window
        def kernel(m):
            low=lambda cut:cut/np.pi*np.sinc(cut*m/np.pi)
            if kind=='lowpass':return amplitudes[0]*low(cutoff[0])
            if kind=='highpass':return amplitudes[0]*(np.sinc(m)-low(cutoff[0]))
            if kind=='bandpass':return amplitudes[0]*(low(cutoff[1])-low(cutoff[0]))
            return amplitudes[0]*low(cutoff[0])+amplitudes[1]*(np.sinc(m)-low(cutoff[1]))
        def candidate(length):
            ensure_working_set(length,live_arrays=18)
            m=np.arange(length)-(length-1)/2;ideal=kernel(m);window_values=sp.get_window(chosen,length,fftbins=False)
            b=ideal*window_values;b=(b+b[::-1])/2
            return Transfer(b,[1],name='FIR '+window+' · amplitudes por banda'),ideal,window_values
        searching = automatic or bool(search)
        if searching:
            count, (result, ideal, window_values), evaluation = _search_fir(
                candidate, spec, wp, ws, limit=int(search) if is_kaiser and search else None)
            accepted = True
        else:
            count = max(2,int(taps))
            if kind in ('highpass','bandstop') and count%2==0:
                raise ValueError('Paso no nulo en π: el FIR simétrico requiere longitud impar.')
            result, ideal, window_values = candidate(count)
            accepted, evaluation = evaluate_spec(result, spec)
        result.roc={'mode':'right'}
        signals=[Signal(ideal,name='Respuesta ideal truncada'),Signal(window_values,name='Ventana '+window),Signal(result.b,name='Respuesta FIR h[n]')]
        from .fir_formula import kernel as formula_kernel,window_expression
        from .result_summary import Summary,Section,Formula,number
        def formula(variable):
            if kind!='bandstop':return '('+number(amplitudes[0])+')*('+formula_kernel(kind,cutoff,variable)+')'
            return '('+number(amplitudes[0])+')*('+formula_kernel('lowpass',[cutoff[0]],variable)+')+('+number(amplitudes[1])+')*('+formula_kernel('highpass',[cutoff[1]],variable)+')'
        d=number((count-1)/2);condition='0 <= n <= '+str(count-1)
        formulas=[Formula('h_ideal[n] = '+formula('n'),'h_ideal[n] = '+formula('n')),Formula('w[n] = '+window_expression(window,count,beta),'w[n] = '+window_expression(window,count,beta)),Formula('h[n] = Piecewise((('+formula('n-('+d+')')+')*w[n], '+condition+'), (0, True))','h[n] = ('+formula('n-('+d+')')+')*w[n] para '+condition+'; 0 fuera')]
        for value in formulas:value.numeric=True
        length_note = ('Búsqueda automática en orden creciente. L es la primera longitud de esta ventana que supera la comprobación numérica de bandas.'
                       if searching else 'Longitud fijada manualmente.')
        if is_kaiser:
            length_note += f'\nLongitud de referencia por fórmula de Kaiser: {estimated}\nβ Kaiser: {beta:.12g}'
        detail=f'Ventana: {window}\n{length_note}\nLongitud usada L: {count}\nOrden nominal M: {count-1}\nRetardo D: {d} muestras\nTransiciones especificadas: '+', '.join(f'{v:.12g} rad/muestra' for v in abs(wp-ws))+'\nCortes del ideal: '+', '.join(f'{v:.12g}' for v in cutoff)
        summary=Summary('Diseño FIR con amplitudes por banda',[Section('Ideal y filtro enventanado',formulas=formulas,paragraphs=['sinc(x)=sin(πx)/(πx), sinc(0)=1. El ideal está definido para todo n. El filtro usa el ideal desplazado por D=(L−1)/2 y una ventana simétrica, sin normalización global que altere la relación entre bandas.']),Section('Parámetros',paragraphs=detail.splitlines()),Section('Tolerancias',paragraphs=evaluation.splitlines())])
        return {'report':summary.plain_text(),'fir_summary':summary,'systems':[result],'signals':signals,'specifications':spec,'specification_met':accepted}
    if kind=='bandstop' and amplitudes[0]!=amplitudes[1]:
        raise ValueError('Las familias IIR clásicas usan una sola ganancia de paso. Para dos amplitudes independientes en un rechazabanda, elegí FIR por bandas y tolerancias; no se sustituye tu pedido por una ganancia global.')
    gain=float(upper.min());normalized_dp=float(1-lower.max()/gain);normalized_ds=stop/gain
    if analog:
        from .analog_design import design as analog_design
        output=analog_design(wp,ws,normalized_dp,normalized_ds,method)
    elif method=='compare':output=compare_iir(wp,ws,normalized_dp,normalized_ds)
    else:output=design_filter(wp,ws,normalized_dp,normalized_ds,method,period,taps,window,search)
    output['systems']=[scale_system(value,gain) for value in output['systems']];output['specifications']=spec
    for system in output['systems']:
        system.roc={'mode':'right'}
    reports=[];accepted=[]
    for system in output['systems']:
        if system.domain!=('analog' if analog else 'digital'):continue
        status,report=evaluate_spec(system,spec);reports.append(system.name+'\nOrden del denominador: '+str(len(system.a)-1)+'\n'+report);accepted.append(status)
    output['report']='Diseño por bandas y tolerancias\n\nMétodo: '+method+'\nAmplitudes deseadas: '+', '.join(f'{v:.12g}' for v in amplitudes)+'\nLos límites de cada banda se aplican al módulo. La ganancia del prototipo se ajusta al límite superior permitido.\n\n'+'\n\n'.join(reports)
    if method=='impulse':output['report']+='\nLa conversión por invarianza al impulso puede introducir aliasing; se evalúa el resultado digital y no se presume que conserve las tolerancias del prototipo.'
    output['specification_met']=all(accepted);return output
