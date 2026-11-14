"""Deterministic measurements of finite temporal records and their linear model."""
import math
from copy import deepcopy
import numpy as np
from .model import Signal
from .jobs import checkpoint
from .resources import ensure_working_set
from .scalar_expression import integer_value, real_value
from .signal_semantics import require_temporal
from .spectral_measurements import quantity


def select(source, low=None, high=None):
    require_temporal(source)
    from .distributions import dirac_terms
    if dirac_terms(source):raise ValueError('Un impulso Dirac ideal no tiene energía cuadrática finita. Usá una señal ordinaria para estas medidas.')
    count=len(source.values)
    ensure_working_set(count,live_arrays=30)
    if source.domain=='discrete':
        first=int(source.origin);last=first+count-1
        a=first if low is None else integer_value(low);b=last if high is None else integer_value(high)
        if not first<=a<=b<=last:raise ValueError('Los índices deben estar ordenados y dentro del registro. Ambos extremos se incluyen.')
        begin=a-first;end=b-first+1;origin=a;step=1;values=source.values[begin:end]
    else:
        axis=source.axis;reverse=source.step<0
        if reverse and source.metadata.get('input_interpolation')=='hold':raise ValueError('La retención ZOH requiere un eje temporal creciente para conservar el lado retenido.')
        if reverse:axis=axis[::-1]
        a=float(axis[0]) if low is None else real_value(low);b=float(axis[-1]) if high is None else real_value(high)
        if not axis[0]<=a<b<=axis[-1]:raise ValueError('Los tiempos deben estar ordenados y dentro del intervalo. Se seleccionan los puntos guardados incluidos en esos límites.')
        begin=int(np.searchsorted(axis,a,side='left'));end=int(np.searchsorted(axis,b,side='right'))
        if end-begin<2:raise ValueError('La selección continua requiere al menos dos puntos guardados. Ampliá el intervalo.')
        values=(source.values[::-1] if reverse else source.values)[begin:end];origin=float(axis[begin]);step=abs(source.step)
    metadata=deepcopy(source.metadata);metadata.update(operation='selected_record',input_expression=source.expression,requested_interval=[a,b],measurement_scope='Muestras guardadas incluidas; extremos incluidos, sin extrapolación.')
    if source.domain=='discrete' and metadata.get('sample_rate_hz') is not None:
        rate=float(metadata['sample_rate_hz'])
        if not math.isfinite(rate) or rate<=0:raise ValueError('La frecuencia de muestreo registrada debe ser positiva y finita.')
        if metadata.get('time_start_s') is not None:
            time=float(metadata['time_start_s'])+begin/rate
            if not math.isfinite(time):raise ValueError('El reloj de la selección excede el rango numérico.')
            metadata['time_start_s']=time
    elif source.domain=='continuous':
        metadata['time_start_s']=origin
        if math.isfinite(1/step):metadata['sample_rate_hz']=1/step
    return Signal(values,origin,step,source.units,source.name+' · intervalo','discrete' if source.domain=='discrete' else 'continuous','',metadata)


def _average(values, discrete, held=False):
    # The shifted sum makes the mean of every constant record exactly that value.
    anchor=values[0];delta=values-anchor
    if discrete or held:weights=delta[:len(values) if discrete else -1]/(len(values) if discrete else len(values)-1)
    else:weights=(delta[:-1]/2+delta[1:]/2)/(len(values)-1)
    return complex(anchor.real+math.fsum(weights.real),anchor.imag+math.fsum(weights.imag))


def _scaled(values,scale):
    # Complex division can form an overflowing reciprocal for subnormal scales.
    result=np.empty(len(values),complex)
    result.real=values.real/scale if scale else values.real
    result.imag=values.imag/scale if scale else values.imag
    return result


def _energy(values, discrete, held=False):
    if discrete or held:return np.abs(values[:len(values) if discrete else -1])**2
    a,b=values[:-1],values[1:]
    return np.abs(a/2+b/2)**2+np.abs(a-b)**2/12


def _physical(normalized, scale, factor=1., power=2):
    if normalized<=0 or scale==0:return quantity(-np.inf)
    return quantity(math.log(normalized)+power*math.log(scale)+math.log(factor))


def _cumulative_inside(a,b,u):
    # Integral |a+(b-a)v|² dv, evaluated by positive Gauss weights on [0,u].
    d=b-a;r=1/math.sqrt(3)
    return u*(abs(a+d*(u*(1-r)/2))**2+abs(a+d*(u*(1+r)/2))**2)/2


def _quantile(masses, cumulative, values, target, discrete, held=False):
    if target<=0:return 0.
    if target>=1:return float(len(values)-1)
    if discrete:return int(np.searchsorted(cumulative,target,side='left'))
    cell=min(int(np.searchsorted(cumulative,target,side='right'))-1,len(masses)-1);cell=max(0,cell)
    mass=masses[cell]
    if mass<=0:return float(cell)
    local=(target-cumulative[cell])/(cumulative[cell+1]-cumulative[cell]);left=0.;right=1.
    if held:return cell+local
    for _ in range(52):
        middle=(left+right)/2
        if _cumulative_inside(values[cell],values[cell+1],middle)<local*mass:left=middle
        else:right=middle
    return cell+(left+right)/2


def analyze(source, low=None, high=None, fraction=.9, level=.5, component='magnitude'):
    fraction=real_value(fraction)
    if not 0<fraction<=1:raise ValueError('La fracción central de energía debe ser mayor que 0 y como máximo 1.')
    selected=select(source,low,high);discrete=selected.domain=='discrete';held=not discrete and selected.metadata.get('input_interpolation')=='hold';values=selected.values
    scale=max(float(np.max(abs(values.real))),float(np.max(abs(values.imag))))
    q=_scaled(values,scale);count=len(values);span=count-1
    factor=1. if discrete else float(selected.step)
    duration=float(count) if discrete else factor*span
    if not math.isfinite(duration) or duration<=0:raise ValueError('El tamaño de la ventana excede el rango numérico.')
    mean_q=_average(q,discrete,held);mean=complex(mean_q.real*scale,mean_q.imag*scale)
    weights=_energy(q,discrete,held);total=math.fsum(weights);power=total/(count if discrete else span)
    with np.errstate(over='ignore',under='ignore',invalid='ignore'):
        ac_values=np.empty(count,complex);ac_values.real=values.real-mean.real;ac_values.imag=values.imag-mean.imag
    ac_representable=bool(np.isfinite(ac_values).all())
    ac_q=_scaled(ac_values,scale) if ac_representable else q-mean_q
    ac_weights=_energy(ac_q,discrete,held);ac_power=math.fsum(ac_weights)/(count if discrete else span)
    measures=dict(energy=_physical(total,scale,factor),power=_physical(power,scale),rms=_physical(math.sqrt(power),scale,power=1),dc_power=_physical(abs(mean_q)**2,scale),ac_power=_physical(ac_power,scale),ac_rms=_physical(math.sqrt(ac_power),scale,power=1))
    cumulative=None;distribution=dict(centroid=None,rms_width=None,central_interval=None,central_span=None,fraction=fraction)
    if total>0:
        normalized=weights/total;cdf=np.cumsum(normalized)
        cdf=np.maximum.accumulate(np.clip(cdf,0,1));cdf[-1]=1.
        if not discrete:cdf=np.r_[0.,cdf]
        metadata=deepcopy(selected.metadata);metadata.update(operation='record_energy_fraction',quantity='Fracción de energía acumulada en los nodos',scope='Valores en las muestras; en continuo la acumulada real del modelo lineal es cúbica entre nodos. La unión de puntos sólo guía la lectura.')
        metadata.pop('input_interpolation',None)
        if held:metadata['scope']='Fracción acumulada de energía del modelo retenido ZOH; lineal entre nodos.'
        cumulative=selected.copy_with(values=cdf,name='Fracción de energía acumulada',metadata=metadata,expression='')
        # Work with local offsets to preserve discrete origins larger than 2**53.
        if discrete:
            nodes=np.arange(count,dtype=float);mass=normalized
        else:
            u=np.array([(1-math.sqrt(3/5))/2,.5,(1+math.sqrt(3/5))/2]);gauss=np.array([5/18,4/9,5/18])
            nodes=(np.arange(span)[:,None]+u).reshape(-1)
            density=np.abs(q[:-1,None]+np.zeros_like(u) if held else q[:-1,None]*(1-u)+q[1:,None]*u)**2
            mass=(density*gauss/total).reshape(-1)
        center=float(np.dot(nodes,mass));width=math.sqrt(max(0.,float(np.dot((nodes-center)**2,mass))))
        left=_quantile(weights,cdf,q,(1-fraction)/2,discrete,held);right=_quantile(weights,cdf,q,1-(1-fraction)/2,discrete,held)
        coordinate=lambda offset:int(selected.origin)+int(offset) if discrete and float(offset).is_integer() else float(selected.origin)+float(offset)*selected.step
        distribution.update(centroid_offset=center*selected.step,centroid=coordinate(center),centroid_text=(str(selected.origin)+' + '+format(center,'.12g')+' muestras') if discrete and abs(selected.origin)>2**52 and not center.is_integer() else str(coordinate(center)),rms_width=width*selected.step,central_interval=[coordinate(left),coordinate(right)],central_span=(right-left)*selected.step)
        if discrete and abs(selected.origin)>2**52 and not center.is_integer():distribution['centroid']=None
    notice='';ac=None
    if ac_representable:
        ac=selected.copy_with(values=ac_values,name='Componente alterna · '+source.name,metadata={**deepcopy(selected.metadata),'operation':'record_ac','mean_removed':[mean.real,mean.imag]},expression='')
    else:notice='La componente alterna contiene valores fuera de float64; se conservan sus medidas y no se publica una señal numérica alterada.'
    dc=selected.copy_with(values=np.full(count,mean,complex),name='Componente continua · '+source.name,metadata={**deepcopy(selected.metadata),'operation':'record_dc'},expression='')
    events=crossings(selected,level,component)
    return dict(selected=selected,cumulative=cumulative,dc=dc,ac=ac,mean=[mean.real,mean.imag],measures=measures,distribution=distribution,events=events,level=real_value(level),component=component,notice=notice,discrete=discrete,held=held,interval=[int(selected.origin) if discrete else float(selected.origin),int(selected.origin)+count-1 if discrete else float(selected.origin)+(count-1)*selected.step],samples=count,units=selected.units,scope='Suma sobre índices enteros.' if discrete else 'Integral exacta de la retención ZOH entre puntos; el último valor no agrega duración.' if held else 'Integral exacta del modelo lineal entre los puntos seleccionados. No reevalúa la fórmula ni extrapola.',duration=duration)


def crossings(source,level,component='magnitude'):
    level=real_value(level)
    if component not in ('real','imag','magnitude'):raise ValueError('Elegí parte real, imaginaria o módulo.')
    if component=='magnitude' and level<0:raise ValueError('El nivel del módulo no puede ser negativo.')
    values=source.values;scale=max(float(np.max(abs(values.real))),float(np.max(abs(values.imag))),abs(level))
    q=_scaled(values,scale);threshold=level/scale if scale else 0.
    scalar=lambda v:float(v.real) if component=='real' else float(v.imag) if component=='imag' else abs(v)
    sign=np.sign((q.real if component=='real' else q.imag if component=='imag' else abs(q))-threshold)
    count=len(q);raw=[]
    held=source.domain=='continuous' and source.metadata.get('input_interpolation')=='hold'
    if source.domain=='discrete' or held:
        i=0
        while i<count:
            if i%512==0:checkpoint()
            if sign[i]==0:
                j=i
                while j+1<count and sign[j+1]==0:j+=1
                left=sign[i-1] if i else None;right=sign[j+1] if j+1<count else None
                end=j+1 if held and j<count-1 else j
                raw.append((i,end,'Tramo igual al nivel [desde,hasta)' if held and end>i and j<count-1 else 'Tramo igual al nivel' if end>i else _kind(left,right)));i=j+1
            else:
                if i and sign[i-1]!=0 and sign[i-1]!=sign[i]:raw.append((i,i,('Salto ascendente sobre el nivel' if sign[i]>0 else 'Salto descendente sobre el nivel') if held else 'Cruce ascendente' if sign[i]>0 else 'Cruce descendente'))
                i+=1
    else:
        for i,(a,b) in enumerate(zip(q[:-1],q[1:])):
            if i%512==0:checkpoint()
            d=b-a
            if component!='magnitude':
                v0=scalar(a)-threshold;v1=scalar(b)-threshold
                if v0==v1==0:raw.append((float(i),float(i+1)))
                elif v0==0:raw.append((float(i),float(i)))
                elif v1==0:raw.append((float(i+1),float(i+1)))
                elif (v0<0)!=(v1<0):
                    point=i+v0/(v0-v1);raw.append((point,point))
            else:
                den=abs(d)**2
                if den==0:
                    if abs(a)==threshold:raw.append((float(i),float(i+1)))
                    continue
                middle=-(a.real*d.real+a.imag*d.imag)/den;perpendicular=abs(a+d*middle)
                if threshold<perpendicular:continue
                distance=math.sqrt(max(0.,(threshold-perpendicular)*(threshold+perpendicular)/den))
                for root in sorted(set((middle-distance,middle+distance))):
                    if 0<=root<=1:raw.append((i+root,i+root))
        merged=[]
        for low,high in sorted(raw):
            if merged and low<=merged[-1][1]:merged[-1]=(merged[-1][0],max(high,merged[-1][1]))
            else:merged.append((low,high))
        def side(position):
            cell=min(int(position),count-2);u=position-cell
            return np.sign(scalar(q[cell]*(1-u)+q[cell+1]*u)-threshold)
        raw=[]
        for i,(low,high) in enumerate(merged):
            left=side(((merged[i-1][1] if i else 0.)+low)/2) if low>0 else None
            right=side((high+(merged[i+1][0] if i+1<len(merged) else count-1))/2) if high<count-1 else None
            raw.append((low,high,'Tramo igual al nivel' if high>low else _kind(left,right)))
    coordinate=lambda p:int(source.origin)+int(p) if source.domain=='discrete' else float(source.origin)+source.step*p
    return [dict(kind=kind,start=coordinate(a),end=coordinate(b),span=(b-a)*source.step) for a,b,kind in raw]


def _kind(left,right):
    if left is None or right is None:return 'Nivel en extremo del registro'
    if left<0<right:return 'Cruce ascendente'
    if left>0>right:return 'Cruce descendente'
    return 'Contacto con el nivel'


def summary(data):
    from .result_summary import Summary,Section,number
    m=data['measures'];d=data['distribution'];mean=complex(*data['mean'])
    sections=[Section('Intervalo medido',rows=[('Desde',str(data['interval'][0])),('Hasta',str(data['interval'][1])),('Muestras incluidas',str(data['samples'])),('Unidad del eje',data['units'])],paragraphs=[data['scope'],'Los límites seleccionan puntos guardados. En discreto se incluyen ambos índices; en continuo el informe muestra el primer y último punto realmente incluidos. Estas medidas no clasifican la señal infinita.']),Section('Energía y amplitud',rows=[('Energía',m['energy']['text']),('Potencia media en la ventana',m['power']['text']),('RMS',m['rms']['text'])]),Section('Continua y alterna',rows=[('Media compleja',number(mean)),('Potencia de la componente continua',m['dc_power']['text']),('Potencia de la componente alterna',m['ac_power']['text']),('RMS alterno',m['ac_rms']['text'])],paragraphs=['La continua es la media en esta ventana; alterna = registro − media. No son una clasificación global de DC/AC. Potencia total = potencia continua + potencia alterna para la misma ventana, salvo redondeo.',data['notice']])]
    if data['cumulative'] is None:sections.append(Section('Distribución de energía',paragraphs=['El registro es nulo: el centro, la dispersión y una fracción de energía no están definidos. No se inventa una acumulada normalizada.']))
    else:sections.append(Section('Distribución de energía',rows=[('Centro energético',d['centroid_text']),('Centro respecto del primer punto',number(d['centroid_offset'])),('Dispersión RMS del eje',number(d['rms_width'])),('Fracción central solicitada',number(d['fraction'])),('Intervalo central',str(d['central_interval'])),('Separación entre sus extremos',number(d['central_span']))],paragraphs=['Se reparte la energía restante por igual entre las dos colas. Es un intervalo central, no el intervalo más corto posible. En discreto se eligen muestras y se puede incluir más energía de la solicitada; no se interpola entre índices. La separación entre extremos no es la cantidad de muestras.']))
    sections.append(Section('Cruces y contactos',rows=[('Componente',{'real':'Parte real','imag':'Parte imaginaria','magnitude':'Módulo'}[data['component']]),('Nivel',number(data['level'])),('Eventos encontrados',str(len(data['events'])))],paragraphs=['La tabla distingue cruces, contactos y tramos iguales al nivel. En discreto un cruce se ubica en la primera muestra del nuevo lado, sin inventar un instante entre muestras. En continuo se usa el modelo lineal complejo, incluido el módulo dentro de cada segmento. No se extrapola fuera del registro.','Esta entrada conserva retención ZOH: se distinguen saltos sobre el nivel, sin inventar cruces lineales. Los tramos retenidos excluyen el extremo donde cambia su valor.' if data['held'] else '']))
    return Summary('Medidas del registro',sections)
