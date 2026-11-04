"""Validate imported coordinates without moving samples onto another grid."""
import math
import numpy as np


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
