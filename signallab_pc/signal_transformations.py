"""Finite-record transformations with explicit mathematical relationships."""
import math
import numpy as np
from .model import Signal
from .resources import ensure_working_set
from .operations import shift,reverse,scale_amplitude,even_odd_parts,_finite_output,_half_sum
from .continuous import transform_time


def continuous_even_odd(source):
    if source.domain!='continuous' or source.step<=0 or len(source.values)<2:raise ValueError('Par e impar continuo requiere un registro creciente con al menos dos puntos.')
    from .distributions import dirac_terms,attach_terms
    from .signal_combinations import _interpolate
    radius=max(abs(float(source.origin)),abs(float(source.axis[-1])));ratio=radius/source.step
    if not math.isfinite(ratio):raise ValueError('El intervalo reflejado excede el rango numérico.')
    nearest=round(ratio);half=nearest if abs(ratio-nearest)<=8*math.ulp(ratio) else math.ceil(ratio);half=max(1,half)
    count=2*half+1;ensure_working_set(count,live_arrays=12)
    step=radius/half
    grid=Signal(np.zeros(count),-radius,step,source.units,'Rejilla simétrica','continuous')
    values=_interpolate(source,grid.axis);reflected=values[::-1]
    even=_finite_output(_half_sum(values,reflected),'La parte par');odd=_finite_output(_half_sum(values,reflected,-1),'La parte impar')
    metadata={'operation':'even_odd_decomposition','input':source.name,'input_expression':source.expression,'source_interval':[source.origin,float(source.axis[-1])],
        'scope':'Descomposición sin conjugación alrededor de t=0. La parte ordinaria se interpola linealmente y vale cero fuera del registro. Se usa una rejilla simétrica que incluye cero, con un paso basado en el de entrada; entre muestras es una aproximación. Los términos Dirac conservan sus posiciones y pesos por separado.'}
    if source.units=='s':
        metadata['time_start_s']=-radius;rate=1/step
        if math.isfinite(rate):metadata['sample_rate_hz']=rate
    terms=dict(dirac_terms(source));positions=sorted(set(terms)|{-t for t in terms});outputs=[]
    for values,label,sign in ((even,'par',1),(odd,'impar',-1)):
        weights=[(t,complex(_half_sum(np.asarray(terms.get(t,0j)),np.asarray(terms.get(-t,0j)),sign))) for t in positions]
        info=attach_terms(dict(metadata),weights);info['component']=label
        outputs.append(Signal(values,-radius,step,source.units,source.name+' · '+label,'continuous','',info))
    return tuple(outputs)


def transform_signal(source,operation,*,amplitude=1,delay=0,time_scale=1):
    if source.domain=='discrete':
        if operation=='shift':return shift(source,delay)
        if operation=='reverse':return reverse(source)
        if operation=='scale':return scale_amplitude(source,amplitude)
        if operation=='parity':return even_odd_parts(source)
    elif source.domain=='continuous':
        if operation=='parity':return continuous_even_odd(source)
        if operation=='shift':return transform_time(source,1,1,delay)
        if operation=='reverse':return transform_time(source,1,-1,0)
        if operation=='scale':return transform_time(source,amplitude,1,0)
        if operation=='affine':return transform_time(source,amplitude,time_scale,delay)
    raise ValueError('La transformación no corresponde al dominio de la entrada.')
