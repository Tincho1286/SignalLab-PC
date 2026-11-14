"""Finite response snapshots, modal suggestions and observed step measurements."""
from copy import deepcopy
import math
from fractions import Fraction
import numpy as np
from .model import Signal
from .filters import Transfer
from .resources import ensure_working_set
from .jobs import checkpoint


def extend_input(source,extra=0):
    if isinstance(extra,bool) or not isinstance(extra,(int,np.integer)) or extra<0:raise ValueError('Los puntos de extensión deben ser un entero no negativo.')
    if source.data_kind!='temporal':raise ValueError('La respuesta requiere una entrada temporal.')
    ensure_working_set(int(source.values.size+extra),live_arrays=18)
    result=deepcopy(source)
    if extra:
        original=int(source.values.size)
        result=source.copy_with(values=np.r_[source.values,np.zeros(extra)],metadata=deepcopy(source.metadata),expression='')
        # A zero-extended record is a new input, not the original inverse or
        # recurrence model continued to indices where its values were replaced.
        result.metadata['source_operation']=result.metadata.get('operation');result.metadata['operation']='response_input'
        for field in ('temporal_formula','derivation','derivation_operation','excitation'):result.metadata.pop(field,None)
        result.metadata['response_extension']=dict(original_count=original,extra_count=int(extra),last_loaded_coordinate=int(source.axis[-1]) if source.domain=='discrete' else float(source.axis[-1]),
            input_definition=source.expression,scope='Se agregan muestras cero. En continuo se conserva la interpolación elegida hacia el primer cero; no se impone una desconexión instantánea entre puntos.')
        if result.domain=='discrete' and 'sample_rate_hz' in result.metadata:
            from .system_clock import validate_clock_resolution
            rate=float(result.metadata['sample_rate_hz']);validate_clock_resolution(float(result.metadata.get('time_start_s',source.origin/rate)),rate,len(result.values))
    return result


def unit_input(system,count,kind,duration=None):
    if isinstance(count,bool) or not isinstance(count,(int,np.integer)) or count<(1 if system.domain=='digital' else 2):raise ValueError('La entrada requiere una muestra discreta o dos puntos continuos como mínimo.')
    if kind not in ('step','impulse'):raise ValueError('Elegí escalón, impulso o una entrada propia.')
    ensure_working_set(int(count),live_arrays=10)
    digital=system.domain=='digital';values=np.ones(count) if kind=='step' else np.zeros(count)
    if digital:
        values[0]=1;source=Signal(values,name='Entrada escalón' if kind=='step' else 'Entrada impulso',expression='Heaviside(n,1)' if kind=='step' else 'KroneckerDelta(n,0)',metadata={'input_kind':kind})
        from .system_clock import input_metadata
        source.metadata=input_metadata(system,source)
        return source
    if duration is None or not math.isfinite(float(duration)) or duration<=0:raise ValueError('La duración debe ser positiva y finita.')
    metadata={'input_kind':kind}
    if kind=='impulse':metadata['dirac_at_zero']=[1.,0.]
    return Signal(values,0,float(duration)/(count-1),'s','Entrada escalón' if kind=='step' else 'Entrada impulso','continuous','Heaviside(t,1)' if kind=='step' else 'DiracDelta(t)',metadata)


def suggest_window(system,*,include_memory=False):
    from .transfer_plane import effective_plane_system,plane_poles
    from .system_conditions import require_causal_roc
    require_causal_roc(system)
    if system.advance:raise ValueError('La sugerencia temporal requiere un modelo causal sin avances.')
    model=Transfer(system.b,system.a,system.domain,system.name,sample_period_s=system.sample_period_s,roc=system.roc) if include_memory else effective_plane_system(system);poles=plane_poles(model)
    if not np.isfinite(poles).all():raise ValueError('Los polos no permiten estimar una escala temporal finita.')
    digital=model.domain=='digital';memory=max(len(model.b),len(model.a))-1;level=math.log(1000)
    stable=bool(np.all(abs(poles)<1) if digital else np.all(poles.real<0))
    notes=['Sugerencia modal orientativa: no certifica establecimiento ni tolerancias. Los polos repetidos y los pesos de cada modo pueden alargar el transitorio.']
    if include_memory:notes.append('Se incluyen los modos de la ecuación original asociados al historial; una cancelación de H no elimina una condición inicial no nula.')
    if digital:
        radii=abs(poles);rates=np.abs(np.log(radii[radii>0]));rates=rates[rates>0]
        growing=np.log(radii[radii>1])
        horizon=level/float(max(growing)) if len(growing) else level/float(min(rates)) if len(rates) else 0.
        angles=abs(np.angle(poles));oscillations=angles[angles>0]
        if not len(rates) and len(oscillations):horizon=3*2*np.pi/float(min(oscillations))
        if not math.isfinite(horizon):raise ValueError('La escala temporal excede el rango disponible. Elegí el intervalo manualmente.')
        count=max(1,int(math.floor(horizon))+1) if len(growing) else max(16,memory+2,int(math.ceil(horizon))+memory+1)
        ensure_working_set(count,live_arrays=18)
        return dict(count=count,duration=None,stable=stable,notes=notes+['Se orienta la caída modal a 10⁻³ si los polos son estables; para modos crecientes se observa su crecimiento, sin asignarles un establecimiento.'],poles=[[float(p.real),float(p.imag)] for p in poles])
    rates=abs(poles.real);nonzero=rates[rates>0];frequencies=abs(poles.imag);oscillations=frequencies[frequencies>0]
    growing=poles.real[poles.real>0]
    duration=level/float(max(growing)) if len(growing) else level/float(min(nonzero)) if len(nonzero) else 3*2*np.pi/float(min(oscillations)) if len(oscillations) else 1.
    if not math.isfinite(duration) or duration<=0:raise ValueError('La escala temporal excede el rango disponible. Elegí el intervalo manualmente.')
    step=duration/500
    if len(rates) and max(rates)>0:step=min(step,1/(32*float(max(rates))))
    if len(oscillations):step=min(step,2*np.pi/(64*float(max(oscillations))))
    ratio=duration/step if step>0 else float('inf')
    if not math.isfinite(ratio):raise ValueError('No se pueden resolver juntas estas escalas temporales. Elegí duración y paso manualmente.')
    count=max(2,int(math.ceil(ratio))+1);ensure_working_set(count*max(1,len(model.a)),live_arrays=18)
    if not len(poles):notes.append('El modelo no tiene polos dinámicos; 1 s es sólo una ventana de visualización.')
    if not stable:notes.append('Hay modos crecientes o sobre la frontera: esta ventana no representa un tiempo de establecimiento.')
    return dict(count=count,duration=float(duration),stable=stable,notes=notes,poles=[[float(p.real),float(p.imag)] for p in poles])


def _finite_ratio(numerator,denominator,multiplier=1):
    try:
        exact=Fraction(numerator)/Fraction(denominator)*multiplier;value=float(exact)
        return value if math.isfinite(value) and (value!=0 or exact==0) else None
    except (OverflowError,ZeroDivisionError):return None


def _bound(value,up):
    """A float threshold that compares stored floats to an exact rational bound."""
    try:rounded=float(value)
    except OverflowError:return math.inf if value>0 else -math.inf
    if not math.isfinite(rounded):return rounded
    if (Fraction(rounded)<value if up else Fraction(rounded)>value):rounded=math.nextafter(rounded,math.inf if up else -math.inf)
    return rounded


def step_metrics(system,output,percent=2.):
    """Unit step from rest; crossings interpolate only continuous sampled curves."""
    percent=float(percent)
    if not math.isfinite(percent) or percent<=0:raise ValueError('La banda de establecimiento debe ser un porcentaje positivo y finito.')
    expected='discrete' if system.domain=='digital' else 'continuous'
    if output.domain!=expected or output.data_kind!='temporal':raise ValueError('Las medidas requieren la respuesta temporal en el dominio del sistema.')
    from .transfer_plane import effective_plane_system,plane_poles,convergence
    model=effective_plane_system(system);poles=plane_poles(model);digital=model.domain=='digital'
    result=dict(available=False,percent=percent,units='muestras' if digital else 's',notes=['Medidas sobre la ventana calculada. La permanencia dentro de una banda hasta el final del registro no certifica todos los instantes futuros.','La estabilidad entrada–salida se evalúa con los polos numéricos del modelo y sus cancelaciones exactas; no certifica estabilidad interna.'])
    unstable=np.any(abs(poles)>=1) if digital else np.any(poles.real>=0)
    if unstable:
        result['notes'].append('No se asigna un valor final por DC: el modelo causal no tiene todos sus polos estrictamente estables.');return result
    causal=Transfer.from_document(model.to_document());causal.roc={'mode':'right'}
    if convergence(causal).get('boundary'):
        result['notes'].append('No se asigna un valor final: hay un polo sobre la frontera de Fourier o numéricamente indistinguible de ella.');return result
    target=complex(model.response(np.array([0.]))[0])
    if not np.isfinite(target) or target.imag or np.any(output.values.imag):
        result['notes'].append('Las medidas de escalón real requieren una respuesta y una ganancia DC reales y finitas. Las componentes complejas se conservan en la figura.');return result
    target=float(target.real);y=output.values.real;coordinate=output.axis
    value=lambda index:int(coordinate[index]) if digital else float(coordinate[index])
    sign=-1. if target<0 else 1.;peak=int(np.argmax(abs(y) if target==0 else sign*y));last=float(y[-1])
    result.update(available=True,final_value=target,last_value=last,peak_value=float(y[peak]),peak_coordinate=value(peak),peak_from_start=peak if digital else float(peak*output.step))
    if target==0:
        result['notes'].append('La ganancia DC es cero: los porcentajes respecto del valor final, la subida 10–90 % y la banda relativa no están definidos.');return result
    ensure_working_set(len(y),live_arrays=8)
    reference=Fraction(abs(target));oriented=sign*y;band=Fraction(percent)*reference/100
    def crossing(level):
        threshold=level*reference;found=np.flatnonzero(oriented>=_bound(threshold,True))
        if not len(found):return None,None
        index=int(found[0])
        if digital:return value(index),index
        fraction=0. if index==0 else float((threshold-Fraction(float(oriented[index-1])))/(Fraction(float(oriented[index]))-Fraction(float(oriented[index-1]))))
        elapsed=0. if index==0 else (index-1+float(fraction))*output.step
        return float(output.origin+elapsed),float(elapsed)
    c10,t10=crossing(Fraction(1,10));c90,t90=crossing(Fraction(9,10))
    low,high=reference-band,reference+band
    outside=np.flatnonzero((oriented<_bound(low,True))|(oriented>_bound(high,False)))
    last_bad=int(outside[-1]) if len(outside) else -1
    settling=None;settling_from_start=None
    if last_bad<len(y)-1:
        index=last_bad+1
        if digital:settling=value(index);settling_from_start=index
        else:
            if index==0:elapsed=0.
            else:
                previous=Fraction(float(oriented[last_bad]));current=Fraction(float(oriented[index]));boundary=high if previous>high else low
                fraction=(boundary-previous)/(current-previous);elapsed=(last_bad+float(fraction))*output.step
            settling_from_start=float(elapsed);settling=float(output.origin+elapsed)
    overshoot=_finite_ratio(max(Fraction(0),Fraction(float(sign*y[peak]))-reference),reference,100)
    result.update(crossing_10=c10,crossing_90=c90,rise_time=None if t10 is None or t90 is None else t90-t10,overshoot_percent=overshoot,settling_coordinate=settling,settling_from_start=settling_from_start)
    if digital:
        rate=output.metadata.get('sample_rate_hz')
        if rate is not None:
            result['physical_seconds']={key:_finite_ratio(result[key],float(rate)) if result[key] is not None else None for key in ('rise_time','settling_from_start','peak_from_start')}
            if any(result[key] is not None and result['physical_seconds'][key] is None for key in result['physical_seconds']):result['notes'].append('Alguna medida en segundos excede el rango representable; se conserva su valor en muestras.')
    else:result['notes'].append('Cruces y entrada en banda interpolados linealmente entre puntos calculados; no son soluciones algebraicas exactas.')
    return result


def simulate(system,source,*,kind=None,duration=None,extra=0,interpolation='linear',separate=False,previous_inputs=(),previous_outputs=(),percent=2.):
    from . import control
    from .system_clock import input_metadata
    from .temporal_formula import add_excitation_formula
    system=Transfer.from_document(system.to_document());source=deepcopy(source)
    if system.domain=='digital':source.metadata=input_metadata(system,source)
    has_model=bool(source.expression or any(source.metadata.get(key) for key in ('temporal_formula','inverse_model','derivation')))
    original=deepcopy(source) if extra or kind is None and source.domain=='continuous' and has_model else None;source=extend_input(source,extra)
    checkpoint(0)
    if separate:outputs=control.discrete_response_parts(system,source,previous_inputs,previous_outputs)
    elif kind:
        output=system.excitation_response(len(source.values),kind) if system.domain=='digital' else control.analog_response(system,duration,len(source.values),kind)
        outputs=(add_excitation_formula(output,system,kind),)
    else:outputs=(control.forced_response(system,source,interpolation),)
    metrics=None
    if kind=='step' and (not separate or not np.any(previous_inputs) and not np.any(previous_outputs)):
        try:
            from .scalar_expression import real_value
            metrics=step_metrics(system,outputs[0],real_value(percent) if isinstance(percent,str) else percent)
        except (ValueError,ArithmeticError,RuntimeError) as exc:metrics=dict(available=False,notes=['Las muestras se conservan. No se pudieron obtener medidas auxiliares: '+str(exc)])
    for output in outputs:
        if 'response_extension' in source.metadata:output.metadata['response_extension']=deepcopy(source.metadata['response_extension'])
    if kind is None and source.domain=='continuous':
        source.metadata={**source.metadata,'input_definition':source.expression if not extra else source.metadata['response_extension']['input_definition'],'operation':'response_input','input_interpolation':interpolation}
        for field in ('temporal_formula','derivation','derivation_operation','excitation'):source.metadata.pop(field,None)
        source.expression=''
    checkpoint(1)
    return dict(system=system,input=source,original_input=original,outputs=outputs,kind=kind,metrics=metrics,
        previous_inputs=np.asarray(previous_inputs,dtype=complex).copy(),previous_outputs=np.asarray(previous_outputs,dtype=complex).copy(),interpolation=interpolation)


def measurement_summary(metrics):
    from .result_summary import Summary,Section,number,Formula
    if metrics is None:return Summary('Medidas del escalón',[Section('Entrada y condiciones',paragraphs=['Estas medidas corresponden al escalón unitario desde reposo. Elegí esa entrada para medir valor final, subida, sobreimpulso y permanencia en banda. La respuesta a una entrada propia o a memoria no nula conserva sus datos y gráficos sin asignarle estas medidas de escalón.'])])
    notes=list(metrics.get('notes',[]));sections=[]
    if metrics.get('available'):
        unit=metrics['units'];target=metrics['final_value']
        sections.append(Section('Referencia del modelo causal estable',formulas=[Formula('y_final = '+repr(target),'y_final = '+repr(target))],rows=[('Último valor observado',number(metrics['last_value'])),('Mayor módulo observado' if target==0 else 'Extremo en dirección del valor final',number(metrics['peak_value'])),('Coordenada del extremo',str(metrics['peak_coordinate']))],paragraphs=['La referencia se obtiene de la ganancia DC del modelo estable, no de la última muestra del registro.']))
        names=[('crossing_10','Primer cruce del 10 %'),('crossing_90','Primer cruce del 90 %'),('rise_time','Subida 10–90 % ('+unit+')'),('overshoot_percent','Sobreimpulso (%)'),('settling_coordinate','Entrada en la banda observada'),('settling_from_start','Desde el inicio hasta la banda ('+unit+')')]
        rows=[(label,'No observado o no representable en esta ventana' if metrics[key] is None else number(metrics[key])) for key,label in names if key in metrics]
        if rows:sections.append(Section('Transitorio observado',rows=[('Banda relativa',number(metrics['percent'])+' % del valor final'),*rows]))
        physical=metrics.get('physical_seconds')
        if physical:
            labels={'rise_time':'Subida 10–90 %','settling_from_start':'Desde el inicio hasta la banda','peak_from_start':'Desde el inicio hasta el extremo'}
            sections.append(Section('Lectura con el reloj registrado',rows=[(labels[key],'No disponible en segundos' if value is None else number(value)+' s') for key,value in physical.items()]))
    sections.append(Section('Interpretación y alcance',paragraphs=notes))
    return Summary('Medidas de la respuesta al escalón',sections)


def context_sections(snapshot):
    from .result_summary import Section
    source=snapshot['input'];outputs=snapshot['outputs'];digital=source.domain=='discrete';extension=source.metadata.get('response_extension')
    rows=[('Puntos de la entrada usada',str(len(source.values))),('Primera coordenada',str(source.origin)),('Última coordenada',str(int(source.axis[-1]) if digital else float(source.axis[-1])))]
    paragraphs=['La entrada y la salida comparten el eje calculado. Comparación permite superponerlas y consultar las componentes con los cursores, sin recalcular. Cada señal conserva sus acciones de exportación y reutilización.']
    if not digital:
        paragraphs.append('Entre puntos se usa interpolación lineal.' if snapshot['interpolation']=='linear' else 'Entre puntos se usa retención constante de la entrada; la comparación la dibuja como escalones.')
        if snapshot['kind'] is None:paragraphs.append('Se reutiliza la entrada reconstruida desde sus muestras. Cuando había una fórmula original, se conserva además como un resultado padre; la reconstrucción no se presenta como si fuese esa función exacta entre puntos.')
    if extension:
        rows.extend([('Puntos cargados',str(extension['original_count'])),('Ceros agregados',str(extension['extra_count'])),('Última coordenada cargada',str(extension['last_loaded_coordinate']))]);paragraphs.append(extension['scope'])
    else:paragraphs.append('No se calcula la evolución posterior a la ventana. En una entrada propia podés agregar puntos cero para observar la cola sin reescribir sus datos.')
    if len(outputs)>1:paragraphs.append('Total = estado cero + entrada cero. El historial se ordena desde n₀−1 hacia atrás. La respuesta de entrada cero conserva la memoria previa; el inspector describe la realización usada, incluidas las secciones cuando corresponde.')
    if snapshot['system'].sos is not None and outputs[0].metadata.get('realization')=='polynomial':paragraphs.append('El historial global de entradas y salidas se ejecuta con la ecuación polinómica, no como estados internos SOS. En órdenes altos puede perder precisión; las tres componentes usan esa misma realización.')
    return [Section('Entrada, comparación y ventana observada',rows=rows,paragraphs=paragraphs)]
