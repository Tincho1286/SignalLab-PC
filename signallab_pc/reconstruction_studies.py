"""Finite reconstruction kernels, common-clock comparisons and nodal error measures."""
import math
from copy import deepcopy
from fractions import Fraction
import numpy as np
from .model import Signal
from . import sampling
from .operations import _discrete
from .record_measurements import _physical,_scaled
from .resources import ensure_working_set
from .jobs import checkpoint,OperationCancelled
from .scalar_expression import real_value,integer_value

METHODS={'zoh':'ZOH','linear':'Lineal','sinc':'SINC'}


def weights(method,position,count):
    if method not in METHODS:raise ValueError('Elegí ZOH, lineal o SINC.')
    position=real_value(position);out=np.zeros(count,float)
    if method=='zoh':
        index=math.floor(position)
        if 0<=index<count:out[index]=1.
    elif method=='linear':
        index=math.floor(position);fraction=position-index
        if 0<=index<count:out[index]=1-fraction
        if 0<=index+1<count:out[index+1]=fraction
    elif position.is_integer():
        index=int(position)
        if 0<=index<count:out[index]=1.
    else:
        nearest=round(position);fraction=position-nearest
        numerator=math.sin(math.pi*fraction)*(-1 if nearest%2 else 1)
        indices=np.arange(count,dtype=np.int64)
        out=numerator*np.where(indices%2,-1.,1.)/math.pi/(position-indices)
    return out


def weighted_sum(coefficients,values):
    """Compensated sum; preserve terms lost by intermediate range limitations."""
    with np.errstate(over='ignore',under='ignore',invalid='ignore'):
        real=coefficients*values.real;imag=coefficients*values.imag
    unsafe=(~np.isfinite(real))|(~np.isfinite(imag))|((real==0)&(coefficients!=0)&(values.real!=0))|((imag==0)&(coefficients!=0)&(values.imag!=0))
    try:
        if unsafe.any():raise OverflowError
        result=complex(math.fsum(real),math.fsum(imag))
    except OverflowError:
        def component(part):
            total=Fraction(0)
            for i,(a,b) in enumerate(zip(coefficients,part)):
                if i%256==0:checkpoint()
                total+=Fraction(float(a))*Fraction(float(b))
            value=float(total)
            if value==0 and total:raise FloatingPointError('La suma no nula queda por debajo de float64; no se sustituye por cero.')
            return value
        result=complex(component(values.real),component(values.imag))
    if not np.isfinite(result):raise FloatingPointError('La reconstrucción supera el rango numérico representable.')
    return result


def _linear(padded,factor):
    count=(len(padded)-1)*factor+1;indices=np.arange(count,dtype=np.int64);left=indices//factor;alpha=(indices%factor)/factor
    a=padded[left];b=padded[np.minimum(left+1,len(padded)-1)]
    with np.errstate(over='ignore',under='ignore',invalid='ignore'):
        real_a=a.real*(1-alpha);real_b=b.real*alpha;imag_a=a.imag*(1-alpha);imag_b=b.imag*alpha
        out=np.empty(count,complex);out.real=real_a+real_b;out.imag=imag_a+imag_b
    same=a==b;out[same]=a[same]
    unsafe=(~np.isfinite(out))|(((real_a==0)&(a.real!=0)&(alpha!=1))|((real_b==0)&(b.real!=0)&(alpha!=0))|((imag_a==0)&(a.imag!=0)&(alpha!=1))|((imag_b==0)&(b.imag!=0)&(alpha!=0)))&~same
    for j in np.flatnonzero(unsafe):
        checkpoint();out[j]=weighted_sum(np.array([1-alpha[j],alpha[j]]),np.array([a[j],b[j]]))
    return out


def _sinc(values,factor,before,after):
    count=(len(values)-1+before+after)*factor+1
    scale=max(float(np.max(abs(values.real))),float(np.max(abs(values.imag))))
    normalized=_scaled(values,scale)
    erased=np.any((normalized.real==0)&(values.real!=0)) or np.any((normalized.imag==0)&(values.imag!=0))
    if count*len(values)>2_000_000 and not erased:
        padded=np.zeros(len(values)+before+after,complex);padded[before:before+len(values)]=normalized
        result=sampling.resample(Signal(padded),factor,'sinc').values
        with np.errstate(over='ignore',under='ignore',invalid='ignore'):
            projected=np.empty(len(result),complex);projected.real=result.real*scale;projected.imag=result.imag*scale
        if np.isfinite(projected).all():
            projected[before*factor:(before+len(values)-1)*factor+1:factor]=values
            return projected,'Convolución FFT del núcleo SINC, con nudos conservados por construcción.'
    result=np.empty(count,complex)
    for j in range(count):
        if j%64==0:checkpoint()
        result[j]=weighted_sum(weights('sinc',(j-before*factor)/factor,len(values)),values)
    return result,'Suma directa compensada del núcleo SINC; nudos cardinales exactos.'


def statistics(values):
    scale=max(float(np.max(abs(values.real))),float(np.max(abs(values.imag))))
    q=_scaled(values,scale);squares=np.abs(q)**2;total=math.fsum(squares)
    return dict(energy=_physical(total,scale),rms=_physical(math.sqrt(total/len(values)),scale,power=1),maximum=_physical(float(np.max(abs(q))),scale,power=1))


def error_measurement(reference,calculated):
    with np.errstate(over='ignore',under='ignore',invalid='ignore'):difference=calculated.values-reference.values
    error=None
    if np.isfinite(difference).all():
        metrics=statistics(difference)
        error=calculated.copy_with(values=difference,name='Error '+calculated.metadata['method_label']+' − referencia',metadata={**calculated.metadata,'operation':'reconstruction_error','input_interpolation':'linear','scope':'Diferencia en los puntos de la rejilla común; no es una integral continua del error.'},expression='')
    else:
        scale=max(float(np.max(abs(reference.values.real))),float(np.max(abs(reference.values.imag))),float(np.max(abs(calculated.values.real))),float(np.max(abs(calculated.values.imag))))
        q=_scaled(calculated.values,scale)-_scaled(reference.values,scale);squares=abs(q)**2;total=math.fsum(squares)
        metrics=dict(energy=_physical(total,scale),rms=_physical(math.sqrt(total/len(q)),scale,power=1),maximum=_physical(float(np.max(abs(q))),scale,power=1))
    ref=statistics(reference.values)['energy'];err=metrics['energy']
    if ref['log_value'] is None and err['log_value'] is None:snr=None;text='No definido: referencia y error nulos.'
    elif err['log_value'] is None:snr=None;text='+∞: error nulo y referencia no nula.'
    elif ref['log_value'] is None:snr=None;text='−∞: referencia nula y error no nulo.'
    else:snr=10/math.log(10)*(ref['log_value']-err['log_value']);text=format(snr,'.12g')+' dB'
    return dict(signal=error,metrics=metrics,snr_db=snr,snr_text=text,notice='' if error is not None else 'La diferencia contiene valores fuera de float64: se conservan las medidas, sin publicar una señal de error alterada.')


def analyze(source,rate,start,factor=16,before=0,after=0,*,override_clock=False,reference=None):
    _discrete(source);factor=integer_value(factor);before=integer_value(before);after=integer_value(after)
    if factor<1 or before<0 or after<0:raise ValueError('Las subdivisiones deben ser positivas y los períodos antes/después enteros no negativos.')
    source=source.copy_with(metadata=deepcopy(source.metadata));clock=sampling.reconstruct(source,rate,start,1,'zoh',override_clock=override_clock)
    rate=clock.metadata['source_rate_hz'];start=clock.origin;count=(len(source.values)-1+before+after)*factor+1
    ensure_working_set(max(count,len(source.values)+before+after),live_arrays=40)
    origin=start-before/rate;step=1/rate/factor
    from .system_clock import validate_time_step
    validate_time_step(origin,step,count)
    padded=np.zeros(len(source.values)+before+after,complex);padded[before:before+len(source.values)]=source.values
    signals={};methods=[];positions=np.arange(count,dtype=np.int64)//factor
    metadata=dict(operation='reconstruction_study',source_rate_hz=rate,source_time_start_s=start,input_origin=int(source.origin),input_length=len(source.values),subdivisions=factor,before_periods=before,after_periods=after,clock_override=bool(override_clock),time_start_s=origin)
    if math.isfinite(1/step):metadata['sample_rate_hz']=1/step
    for method,label in METHODS.items():
        checkpoint();error='';signal=None;algorithm='Retención por la derecha.' if method=='zoh' else 'Interpolación convexa entre muestras, con extensión nula.'
        try:
            if method=='zoh':values=padded[positions]
            elif method=='linear':values=_linear(padded,factor)
            else:values,algorithm=_sinc(source.values,factor,before,after)
            signal=Signal(values,origin,step,'s',label+' · '+source.name,'continuous','',{**metadata,'method':method,'method_label':label,'input_interpolation':'hold' if method=='zoh' else 'linear','algorithm':algorithm,'scope':'Extensión nula de la secuencia original. ZOH retiene cada muestra un período; lineal utiliza núcleos triangulares y SINC conserva todas las colas del registro finito dentro de la ventana mostrada.'})
            signals[method]=signal
            at_nodes=values[before*factor:(before+len(source.values)-1)*factor+1:factor]
            node_stats=statistics(at_nodes-source.values)
        except (ValueError,FloatingPointError,OverflowError) as exc:error=str(exc);node_stats=None
        methods.append(dict(method=method,label=label,error=error,nodes=node_stats,algorithm=algorithm))
    if not signals:raise ValueError('Ningún método pudo representarse numéricamente: '+'; '.join(row['error'] for row in methods))
    expected=None;reference_notice='';errors={}
    if reference is not None:
        try:
            if not str(reference).strip():raise ValueError('Completá la expresión de referencia r(t).')
            from .continuous_expression import sample_continuous
            from .distributions import dirac_terms
            expected=sample_continuous(str(reference),origin,step,count,name='Referencia r(t)')
            if dirac_terms(expected):raise ValueError('Una referencia con Dirac ideal no admite error cuadrático puntual.')
            for method,value in signals.items():errors[method]=error_measurement(expected,value)
        except OperationCancelled:raise
        except Exception as exc:reference_notice='Referencia no evaluada: '+str(exc);expected=None;errors={}
    return dict(source=source,source_rate=rate,source_start=start,factor=factor,before=before,after=after,signals=signals,methods=methods,reference=expected,reference_expression=str(reference) if reference is not None else None,reference_notice=reference_notice,errors=errors,interval=[origin,origin+(count-1)*step],count=count)


def inspect(run,time,method):
    time=real_value(time);source=run['source'];rate=run['source_rate'];start=run['source_start']
    try:position=float((Fraction(time)-Fraction(start))*Fraction(rate))
    except OverflowError:raise ValueError('Ese instante no se puede expresar respecto del reloj guardado.') from None
    if not math.isfinite(position):raise ValueError('Ese instante no se puede expresar respecto del reloj guardado.')
    coeff=weights(method,position,len(source.values));value=weighted_sum(coeff,source.values)
    with np.errstate(over='ignore',under='ignore',invalid='ignore'):
        products=np.empty(len(coeff),complex);products.real=coeff*source.values.real;products.imag=coeff*source.values.imag
    unsafe=(~np.isfinite(products))|((products.real==0)&(coeff!=0)&(source.values.real!=0))|((products.imag==0)&(coeff!=0)&(source.values.imag!=0))
    metadata=deepcopy(source.metadata);metadata.update(operation='reconstruction_kernel',method=method,query_time_s=time,query_position=position,source_time_start_s=start,source_rate_hz=rate)
    kernel=source.copy_with(values=coeff,name='Pesos '+METHODS[method]+' en t='+format(time,'.12g'),metadata=metadata,expression='')
    contributions=None if unsafe.any() else source.copy_with(values=products,name='Aportes '+METHODS[method]+' en t='+format(time,'.12g'),metadata={**metadata,'operation':'reconstruction_contributions'},expression='')
    rows=[dict(index=int(source.origin)+i,time=start+i/rate,weight=float(w),sample=complex(x),contribution=None if bad else complex(p)) for i,(w,x,p,bad) in enumerate(zip(coeff,source.values,products,unsafe))]
    signal=run['signals'].get(method);stored=None;residual=None
    if signal is not None and run['interval'][0]<=time<=run['interval'][1]:
        j=round((time-signal.origin)/signal.step)
        if 0<=j<len(signal.values) and signal.origin+j*signal.step==time:
            stored=complex(signal.values[j]);residual=stored-value
    return dict(method=method,time=time,position=position,value=value,stored=stored,residual=residual,weights=kernel,contributions=contributions,rows=rows,outside_window=not run['interval'][0]<=time<=run['interval'][1])


def summary(run):
    from .result_summary import Summary,Section,number,Formula
    sections=[Section('Reloj y ventana',rows=[('Fs de entrada',number(run['source_rate'])+' muestras/s'),('Primer instante original',number(run['source_start'])+' s'),('Subdivisiones por período',str(run['factor'])),('Ventana mostrada',str(run['interval'])+' s'),('Puntos comunes',str(run['count']))],paragraphs=['Los tres métodos usan las mismas muestras y el mismo reloj. Un origen n distinto de cero no cambia el instante asignado a la primera muestra. Ampliar la ventana agrega períodos antes y después, sin inventar muestras originales.']),Section('Núcleos de reconstrucción',formulas=[Formula('x_r(t) = Sum(x[k]*p(Fs*(t-t0)-k), (k, 0, N-1))','xᵣ(t) = Σ x[k] · p(Fs·(t−t₀)−k)')],paragraphs=['k es la posición local del registro, desde cero. ZOH usa p(u)=1 para 0≤u<1; lineal usa max(1−|u|,0); SINC usa sin(πu)/(πu), con valor 1 en u=0. La secuencia vale cero fuera de sus muestras guardadas. ZOH conserva la última muestra un período; lineal tiene una rampa hacia cero en cada borde. Las colas SINC siguen fuera de la ventana dibujada.'])]
    for row in run['methods']:
        if row['error']:sections.append(Section(row['label'],paragraphs=['No se obtuvo una señal representable: '+row['error']]));continue
        rows=[('Máximo desvío en los nudos originales',row['nodes']['maximum']['text']),('RMS del desvío en los nudos',row['nodes']['rms']['text'])]
        sections.append(Section(row['label']+' · nudos originales',rows=rows,paragraphs=[row['algorithm'],'Los nudos se conservan por la definición cardinal y, en FFT, se restauran por construcción. Un desvío nulo no demuestra ausencia de aliasing ni recuperación de una señal infinita.']))
        if row['method'] in run['errors']:
            e=run['errors'][row['method']];sections.append(Section(row['label']+' · error frente a referencia',rows=[('RMS de los puntos de error',e['metrics']['rms']['text']),('Máximo módulo del error',e['metrics']['maximum']['text']),('SNR referencia/error',e['snr_text'])],paragraphs=['Las medidas usan todos los puntos de la rejilla común, con ambos extremos incluidos e igual peso. No se presentan como una integral continua del error.',e['notice']]))
    if run['reference_notice']:sections.append(Section('Referencia',paragraphs=[run['reference_notice'],'Las reconstrucciones se conservan y se pueden utilizar sin referencia.']))
    sections.append(Section('Interpretación',paragraphs=['SINC reconstruye el modelo de una secuencia finita extendida por cero. La exactitud en los nudos no permite deducir lo ocurrido entre muestras ni descartar aliasing. Comparar con una referencia y ampliar el registro son estudios distintos. Las curvas y el inspector conservan el último cálculo aunque edites las entradas.']))
    return Summary('Comparación de reconstrucciones',sections)


def inspection_summary(data):
    from .result_summary import Summary,Section,number
    rows=[('Método',METHODS[data['method']]),('Instante',number(data['time'])+' s'),('Posición local Fs·(t−t₀)',number(data['position'])),('Suma de aportes',number(data['value']))]
    if data['stored'] is not None:rows.extend([('Punto guardado en la figura',number(data['stored'])),('Guardado menos suma',number(data['residual']))])
    return Summary('Aportes de las muestras a la reconstrucción',[Section('Instante consultado',rows=rows,paragraphs=['Cada peso multiplica la muestra del índice indicado; los tiempos provienen del reloj del último cálculo. SINC incluye todas las muestras, sin renormalizar sus pesos. Una diferencia con FFT refleja las dos evaluaciones numéricas; no modifica la curva guardada.','El instante está fuera de la ventana dibujada, pero pertenece al mismo modelo de reconstrucción.' if data['outside_window'] else 'El inspector evalúa el núcleo directamente, incluso entre puntos de la figura.'])])
