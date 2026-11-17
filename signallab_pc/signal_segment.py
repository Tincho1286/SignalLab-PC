"""Extract inclusive sample bounds while retaining the physical clock."""
import math
from copy import deepcopy
from .scalar_expression import integer_value,real_value


def extract(source,low,high):
    if source.domain not in ('discrete','continuous'):raise ValueError('Se requiere una señal temporal.')
    parse=integer_value if source.domain=='discrete' else real_value;first,last=parse(str(low)),parse(str(high))
    if first>last:raise ValueError('El inicio debe ser menor o igual al final.')
    if source.domain=='discrete':a,b=first-int(source.origin),last-int(source.origin)
    else:
        positions=[(v-source.origin)/source.step for v in (first,last)];a,b=[round(v) for v in positions]
        for value,index in zip((first,last),(a,b)):
            expected=source.origin+index*source.step;tolerance=min(source.step/16,8*max(math.ulp(float(value)),math.ulp(float(expected))))
            if abs(value-expected)>tolerance:raise ValueError('Los límites deben coincidir con puntos del registro; no se remuestrea el tramo.')
    if not 0<=a<=b<len(source.values):raise ValueError('Los límites deben estar dentro de las muestras cargadas.')
    origin=int(source.origin)+a if source.domain=='discrete' else source.origin+a*source.step;metadata=deepcopy(source.metadata)
    metadata.update(operation='extract_edited_record',selected_offsets=[a,b],source_interval=[source.origin,int(source.origin)+len(source.values)-1 if source.domain=='discrete' else source.origin+(len(source.values)-1)*source.step])
    if source.expression:metadata['source_expression']=source.expression
    if source.domain=='discrete' and 'sample_rate_hz' in metadata:
        rate=float(metadata['sample_rate_hz'])
        if not math.isfinite(rate) or rate<=0:raise ValueError('El reloj de la señal requiere Fs finita y positiva.')
        start=float(metadata.get('time_start_s',0))+a/rate
        if not math.isfinite(start):raise ValueError('El reloj del tramo excede el rango numérico.')
        metadata['time_start_s']=start
    elif source.domain=='continuous' and source.units=='s':
        rate=1/source.step
        if not math.isfinite(rate):raise ValueError('El reloj del tramo excede el rango numérico.')
        metadata.update(time_start_s=origin,sample_rate_hz=rate)
    return source.copy_with(values=source.values[a:b+1],origin=origin,name=source.name+' · tramo',metadata=metadata,expression='')
