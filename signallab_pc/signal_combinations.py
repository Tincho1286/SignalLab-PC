"""Sum finite records on their union; preserve clock and distribution data."""
import math
import numpy as np
from .model import Signal
from .operations import add_sequences,_finite_output
from .windowing import validate_discrete_clocks
from .continuous import interpolate_record
from .resources import ensure_working_set


def sum_signals(x,h):
    if x.domain!=h.domain or x.domain not in ('discrete','continuous'):raise ValueError('Las dos entradas deben ser discretas o las dos continuas.')
    if x.units!=h.units:raise ValueError('Los ejes de las dos señales deben usar las mismas unidades.')
    metadata={'operation':'sum','inputs':[x.name,h.name],'input_x_expression':x.expression,'input_h_expression':h.expression}
    if x.domain=='discrete':
        validate_discrete_clocks(x,h);result=add_sequences(x,h)
        sources=sorted((x,h),key=lambda source:'time_start_s' not in source.metadata)
        clock=next((source for source in sources if 'sample_rate_hz' in source.metadata),None)
        if clock is not None:
            rate=float(clock.metadata['sample_rate_hz']);metadata['sample_rate_hz']=rate
            if 'time_start_s' in clock.metadata:
                start=float(clock.metadata['time_start_s'])+(result.origin-clock.origin)/rate
                if not math.isfinite(start):raise ValueError('El reloj de la suma excede el rango numérico. Revisá los tiempos y la tasa de muestreo registrados.')
                metadata['time_start_s']=start
        metadata['scope']='Suma alineada por índices enteros. La salida cubre ambos registros y sus huecos; cada entrada vale cero fuera de su intervalo. No se cambian las tasas de muestreo.'
        return result.copy_with(metadata=metadata)
    if x.step<=0 or h.step<=0:raise ValueError('Los registros continuos necesitan un paso positivo.')
    start=min(x.origin,h.origin);stop=max(float(x.axis[-1]),float(h.axis[-1]));span=stop-start;spacing=min(x.step,h.step)
    ratio=span/spacing
    if not math.isfinite(ratio) or ratio<0:raise ValueError('El intervalo conjunto no es representable con esos orígenes y pasos.')
    nearest=round(ratio);intervals=nearest if abs(ratio-nearest)<=8*math.ulp(ratio) else math.ceil(ratio)
    if span and intervals<1:intervals=1
    singletons=[source for source in (x,h) if source.values.size==1 and source.values[0]!=0]
    if span and singletons:
        from fractions import Fraction
        denominator=1
        for source in singletons:
            offset=(source.origin-start)/span
            fraction=Fraction(offset).limit_denominator(4096)
            if abs(float(fraction)-offset)>4*math.ulp(offset):
                raise ValueError('La rejilla uniforme no puede representar una de las muestras aisladas. Ajustá el paso o los instantes de entrada.')
            denominator=math.lcm(denominator,fraction.denominator)
        intervals=((intervals+denominator-1)//denominator)*denominator
    count=intervals+1;ensure_working_set(count+len(x.values)+len(h.values),live_arrays=12)
    step=span/intervals if intervals else spacing
    # Construct the same uniform axis the returned Signal will expose.
    result=Signal(np.zeros(count),start,step,x.units,'Suma de señales','continuous')
    axis=result.axis
    for source in singletons:
        tolerance=min(source.step/4,4*math.ulp(float(source.origin)))
        index=min(int(np.searchsorted(axis,source.origin)),count-1)
        if min(abs(axis[index]-source.origin),abs(axis[max(0,index-1)]-source.origin))>tolerance:
            raise ValueError('La rejilla de salida no distingue el instante de una muestra aislada.')
    values=interpolate_record(x,axis)+interpolate_record(h,axis)
    metadata['scope']='Suma sobre el intervalo completo de ambos registros. Cada parte ordinaria se interpola linealmente y vale cero fuera de sus datos. La rejilla uniforme usa una resolución basada en el menor paso de entrada y ajusta el paso para abarcar ambos extremos. Entre muestras es una aproximación; no equivale a recuperar información que no estaba en las entradas.'
    if x.units=='s':
        metadata['time_start_s']=start;rate=1/step
        if math.isfinite(rate):metadata['sample_rate_hz']=rate
    from .distributions import dirac_terms,attach_terms
    attach_terms(metadata,dirac_terms(x)+dirac_terms(h))
    if dirac_terms(x) or dirac_terms(h):metadata['scope']+=' Los impulsos Dirac se suman por separado mediante sus posiciones y pesos, sin convertirlos en alturas de muestras.'
    return Signal(_finite_output(values,'La suma'),start,step,x.units,'Suma de señales','continuous','',metadata)
