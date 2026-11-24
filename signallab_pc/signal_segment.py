"""Extract inclusive sample bounds while retaining the physical clock."""
from bisect import bisect_left
import math
from copy import deepcopy
from .scalar_expression import integer_value,real_value


def extract(source,low,high):
    if source.domain not in ('discrete','continuous'):raise ValueError('Se requiere una señal temporal.')
    parse=integer_value if source.domain=='discrete' else real_value;first,last=parse(str(low)),parse(str(high))
    if first>last:raise ValueError('El inicio debe ser menor o igual al final.')
    if source.domain=='discrete':a,b=first-int(source.origin),last-int(source.origin)
    else:
        count = len(source.values)
        direction = 1 if source.step > 0 else -1
        spacing = abs(source.step)

        def coordinate(index):
            return source.origin + index*source.step

        positions = []
        for value in (first,last):
            position = bisect_left(range(count), direction*value,
                                   key=lambda index: direction*coordinate(index))
            neighbors = range(max(0,position-1), min(count,position+1))
            index = min(neighbors, key=lambda index: abs(coordinate(index)-value))
            expected = coordinate(index)
            coordinate_error = max(math.ulp(expected), math.ulp(source.origin), math.ulp(index*source.step))
            tolerance = min(spacing/16, 8*max(math.ulp(value), coordinate_error))
            if abs(value-expected)>tolerance:raise ValueError('Los límites deben coincidir con puntos del registro; no se remuestrea el tramo.')
            positions.append(index)
        a,b = sorted(positions)
    if not 0<=a<=b<len(source.values):raise ValueError('Los límites deben estar dentro de las muestras cargadas.')
    origin=int(source.origin)+a if source.domain=='discrete' else source.origin+a*source.step;metadata=deepcopy(source.metadata)
    metadata.update(operation='extract_edited_record',selected_offsets=[a,b],source_interval=[source.origin,int(source.origin)+len(source.values)-1 if source.domain=='discrete' else source.origin+(len(source.values)-1)*source.step])
    if source.expression:metadata['source_expression']=source.expression
    if source.domain=='discrete':
        from .system_clock import reindex_clock
        clock = reindex_clock(source.metadata,a,b-a+1)
        for key in ('sample_rate_hz','time_start_s','time_mapping'):
            metadata.pop(key,None)
        metadata.update(clock)
    elif source.domain=='continuous' and source.units=='s':
        rate=1/abs(source.step)
        if not math.isfinite(rate):raise ValueError('El reloj del tramo excede el rango numérico.')
        metadata.update(time_start_s=origin,sample_rate_hz=rate)
    return source.copy_with(values=source.values[a:b+1],origin=origin,name=source.name+' · tramo',metadata=metadata,expression='')
