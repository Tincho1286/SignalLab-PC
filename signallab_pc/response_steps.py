"""Read the stored recurrence, including factored SOS and binary-exact sums."""
import math
import numpy as np
from scipy.signal import lfilter
from .jobs import checkpoint
from .resources import ensure_working_set


def capture(snapshot):
    source=snapshot['input'];output=snapshot['outputs'][0]
    if source.domain!='discrete':raise ValueError('El inspector de muestras corresponde a la ecuación en diferencias discreta.')
    meta=output.metadata;stages=meta.get('sos');count=len(source.values)
    ensure_working_set(count*(len(stages)+3 if stages else 4),live_arrays=4)
    frames=[];values=source.values.copy()
    if stages:
        for index,row in enumerate(stages):
            checkpoint(index/max(1,len(stages)))
            result=lfilter(row[:3],row[3:],values)
            if not np.isfinite(result).all():raise ValueError('La reconstrucción por sección excede el rango; se conserva la respuesta original.')
            frames.append(dict(name='Sección '+str(index+1),b=np.asarray(row[:3],complex),a=np.asarray(row[3:],complex),x=values,y=result,previous_inputs=np.array([],complex),previous_outputs=np.array([],complex)))
            values=result
        # The original final output is authoritative; do not replace it with a
        # second floating realization merely to make the residual zero.
        frames[-1]['y']=output.values.copy()
    else:
        pair=lambda values:np.asarray([complex(*v) for v in values],complex)
        frames.append(dict(name='Ecuación del sistema',b=pair(meta['b']),a=pair(meta['a']),x=values,y=output.values.copy(),previous_inputs=pair(meta.get('previous_inputs',[])),previous_outputs=pair(meta.get('previous_outputs',[]))))
    return dict(origin=int(source.origin),count=count,frames=frames)


def _shown(pair):
    components=[]
    for value in pair:
        try:converted=float(value)
        except OverflowError:return None
        if not math.isfinite(converted) or converted==0 and value:return None
        components.append(converted)
    return complex(*components)


def inspect(trace,index,section=0):
    from .scalar_expression import integer_value
    from .rational_frequency import exact,add,mul,div,ZERO
    index=integer_value(index);section=integer_value(section);offset=index-trace['origin']
    if not 0<=offset<trace['count']:raise ValueError('El índice debe pertenecer al intervalo calculado.')
    if not 0<=section<len(trace['frames']):raise ValueError('Elegí una sección del cálculo.')
    frame=trace['frames'][section];rows=[];total=ZERO;a0=complex(frame['a'][0]);ensure_working_set(len(frame['a'])+len(frame['b']),bytes_per_sample=1024,live_arrays=6)
    for family,coefficients,values,history,sign,start in (('Entrada',frame['b'],frame['x'],frame['previous_inputs'],1,0),('Salida anterior',frame['a'],frame['y'],frame['previous_outputs'],-1,1)):
        for delay in range(start,len(coefficients)):
            if delay%128==0:checkpoint()
            coefficient=complex(coefficients[delay]);position=offset-delay
            value=complex(values[position]) if position>=0 else complex(history[-position-1]) if -position<=len(history) else 0j
            normalized=div(exact(sign*coefficient),exact(a0));term=mul(normalized,exact(value));total=add(total,term)
            rows.append(dict(family=family,lag=delay,index=index-delay,raw_coefficient=sign*coefficient,normalization=a0,coefficient=_shown(normalized),value=value,contribution=_shown(term),source='Registro calculado' if position>=0 else 'Historial inicial' if -position<=len(history) else 'Reposo inicial'))
    computed=complex(frame['y'][offset]);residual=add(exact(computed),tuple(-v for v in total))
    return dict(index=index,section=section,name=frame['name'],rows=rows,computed=computed,reconstructed=_shown(total),residual=_shown(residual),unrepresentable=sum(row['contribution'] is None for row in rows),a0=a0)


def summary(trace,data):
    from .result_summary import Summary,Section,number
    show=lambda value:number(value) if value is not None else 'No representable como complejo float64; no se reemplaza por cero.'
    return Summary('Respuesta · paso n='+str(data['index']),[
        Section(data['name'],rows=[('Primer índice n₀',str(trace['origin'])),('a₀',number(data['a0']))],paragraphs=['Se evalúa y[n] = Σ(b[k]/a₀)·x[n−k] − Σ(a[k]/a₀)·y[n−k]. La tabla usa las muestras y los historiales del último cálculo; editar el formulario no altera esta explicación.']),
        Section('Reconstrucción de la muestra',rows=[('Suma de aportes',show(data['reconstructed'])),('Salida almacenada',show(data['computed'])),('Almacenada menos suma',show(data['residual'])),('Aportes fuera de rango float64',str(data['unrepresentable']))],paragraphs=['Los productos y la suma se reconstruyen como racionales exactos de los valores binarios almacenados y se redondean al mostrarlos. La diferencia puede reflejar redondeo de la realización; no demuestra una identidad simbólica ni reemplaza la salida original. En SOS, cada sección conserva su entrada; la última compara con la salida calculada por la cascada.'])])
