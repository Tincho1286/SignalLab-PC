"""Finite-record transformations with explicit mathematical relationships."""
import math
import numpy as np
from .model import Signal
from .resources import ensure_working_set
from .operations import shift,reverse,scale_amplitude,even_odd_parts,_finite_output,_half_sum
from .continuous import interpolate_record, transform_time


def continuous_even_odd(source):
    if source.domain!='continuous' or source.step<=0 or len(source.values)<2:raise ValueError('Par e impar continuo requiere un registro creciente con al menos dos puntos.')
    from .distributions import dirac_terms,attach_terms
    radius=max(abs(float(source.origin)),abs(float(source.axis[-1])));ratio=radius/source.step
    if not math.isfinite(ratio):raise ValueError('El intervalo reflejado excede el rango numérico.')
    nearest=round(ratio);half=nearest if abs(ratio-nearest)<=8*math.ulp(ratio) else math.ceil(ratio);half=max(1,half)
    count=2*half+1;ensure_working_set(count,live_arrays=12)
    step=radius/half
    if source.full_definition:
        from .continuous_expression import sample_continuous

        complete = sample_continuous(source.full_definition, -radius, step, count)
        values = complete.values
        impulses = dirac_terms(complete)
        scope = 'Se evalúa la fórmula completa en t y en −t sobre una ventana simétrica. Las áreas de Dirac se combinan por separado.'
    else:
        grid=Signal(np.zeros(count),-radius,step,source.units,'Rejilla simétrica','continuous')
        values=interpolate_record(source,grid.axis)
        impulses=dirac_terms(source)
        scope = 'Descomposición sin conjugación alrededor de t=0. La parte ordinaria se interpola linealmente y vale cero fuera del registro. Se usa una rejilla simétrica que incluye cero, con un paso basado en el de entrada; entre muestras es una aproximación. Los términos Dirac conservan sus posiciones y pesos por separado.'
    reflected=values[::-1]
    even=_finite_output(_half_sum(values,reflected),'La parte par');odd=_finite_output(_half_sum(values,reflected,-1),'La parte impar')
    metadata={'operation':'even_odd_decomposition','input':source.name,'input_expression':source.expression,'source_interval':[source.origin,float(source.axis[-1])],
        'scope':scope}
    if source.units=='s':
        metadata['time_start_s']=-radius;rate=1/step
        if math.isfinite(rate):metadata['sample_rate_hz']=rate
    terms=dict(impulses);positions=sorted(set(terms)|{-t for t in terms});outputs=[]
    for values,label,sign in ((even,'par',1),(odd,'impar',-1)):
        weights=[(t,complex(_half_sum(np.asarray(terms.get(t,0j)),np.asarray(terms.get(-t,0j)),sign))) for t in positions]
        info=attach_terms(dict(metadata),weights);info['component']=label
        outputs.append(Signal(values,-radius,step,source.units,source.name+' · '+label,'continuous','',info))
    return tuple(outputs)


def transform_signal(source,operation,*,amplitude=1,delay=0,time_scale=1,offset=0):
    if source.domain=='discrete':
        if operation=='shift':return shift(source,delay)
        if operation=='reverse':return reverse(source)
        if operation=='scale':return scale_amplitude(source,amplitude,offset=offset)
        if operation=='parity':return even_odd_parts(source)
    elif source.domain=='continuous':
        if operation=='parity':return continuous_even_odd(source)
        if operation=='shift':return transform_time(source,1,1,delay)
        if operation=='reverse':return transform_time(source,1,-1,0)
        if operation=='scale':return transform_time(source,amplitude,1,0,offset=offset)
        if operation=='affine':return transform_time(source,amplitude,time_scale,delay,offset=offset)
    raise ValueError('La transformación no corresponde al dominio de la entrada.')


def transform_definition(source, result, operation, *, amplitude, delay, time_scale, offset, parameter_sources=None):
    """Carry the infinite definition alongside its transformed sample window."""
    definition=source.full_definition
    if not definition:return result
    import sympy as sp
    from .symbolic import N,T,parse

    def exact(name,value):
        text=(parameter_sources or {}).get(name)
        if text:
            try:
                candidate=sp.simplify(parse(text))
                if candidate.is_finite is True and not candidate.free_symbols:return candidate
            except (ValueError,TypeError,SyntaxError):
                pass  # The numeric input has already been validated.
        converted=complex(value)
        return sp.Rational(str(converted.real))+sp.I*sp.Rational(str(converted.imag))

    variable=N if source.domain=='discrete' else T
    expression=parse(definition)
    key = 'periodic_definition' if source.metadata.get('periodic_definition') else 'full_axis_definition'

    def keep(signal, formula):
        text = str(formula)
        return signal.copy_with(expression=text,metadata={**signal.metadata,key:text})

    if operation=='parity':
        reflected=expression.subs(variable,-variable)
        return keep(result[0],(expression+reflected)/2), keep(result[1],(expression-reflected)/2)
    shift=sp.Integer(delay) if source.domain=='discrete' else exact('delay',delay)
    coordinate={'shift':variable-shift,'reverse':-variable,'scale':variable,
                'affine':exact('time_scale',time_scale)*(variable-shift)}[operation]
    expression=expression.subs(variable,coordinate)
    if operation in ('scale','affine'):
        expression=exact('amplitude',amplitude)*expression+exact('offset',offset)
    scope='La tabla y el gráfico muestran una ventana. La fórmula transformada describe la señal en todo el eje.'
    transformed=keep(result,expression)
    transformed.metadata['scope']=scope
    return transformed
