"""Validate and inspect sampled coordinates on their original grid."""
from bisect import bisect_left
import math
import numpy as np


def sample_coordinate(source, index):
    if source.domain == 'discrete':
        return int(source.origin) + index
    return source.origin + source.step * index


def sample_index(source, coordinate, *, base=0):
    """Nearest stored sample inside the axis; ties use the earlier row."""
    count = source.values.size
    if not count:
        return None
    first = sample_coordinate(source, 0) - base
    last = sample_coordinate(source, count - 1) - base
    if not min(first, last) <= coordinate <= max(first, last):
        return None
    if source.domain == 'discrete':
        offset = coordinate - first
        index = int(offset)
        return index + int(offset - index > 0.5)
    direction = 1 if source.step > 0 else -1
    after = bisect_left(range(count), direction * coordinate,
                        key=lambda index: direction * (sample_coordinate(source, index) - base))
    candidates = range(max(0, after - 1), min(count, after + 1))
    return min(candidates, key=lambda index: abs(sample_coordinate(source, index) - base - coordinate))


def uniform_step(coordinates):
    values=np.asarray(coordinates,dtype=float)
    offsets=values-values[0]
    step=float(offsets[-1])/(len(values)-1)
    if not math.isfinite(step) or step<=0 or np.any(np.diff(values)<=0):
        raise ValueError('El eje debe ser uniforme y estrictamente creciente.')
    # Absolute coordinates may carry one ulp of rounding. Tolerance must
    # stay below a meaningful fraction of a sample interval.
    ulp=max(math.ulp(float(values[0])),math.ulp(float(values[-1])))
    tolerance=min(step/4,max(step*1e-7,ulp))
    predicted=values[0]+step*np.arange(len(values),dtype=float)
    if np.any(abs(offsets-step*np.arange(len(values)))>max(tolerance,ulp/2)) or np.any(abs(values-predicted)>tolerance):
        raise ValueError('El eje no es uniforme con la precisión de entrada. No se remuestrean las coordenadas.')
    return step
