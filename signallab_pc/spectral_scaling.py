"""Binary scaling for sums and FFTs whose final normalization can be finite."""
import math
import numpy as np


def _ldexp(values, exponent):
    scaled=np.empty(values.shape,dtype=complex)
    scaled.real=np.ldexp(values.real,exponent)
    scaled.imag=np.ldexp(values.imag,exponent)
    return scaled


def bounded(values):
    peak=max(np.max(abs(values.real),initial=0.),np.max(abs(values.imag),initial=0.))
    _, exponent=math.frexp(peak)
    # Preserve the original samples at ordinary scales. This also avoids
    # a needless rounding step for mixtures of very small and large values.
    if abs(exponent)<=450:return values,0
    with np.errstate(under='ignore'):
        return _ldexp(values,-exponent),exponent


def restore_scale(values, exponent, *factors):
    mantissa=1.
    for factor in factors:
        part, shift=math.frexp(factor)
        mantissa*=part
        exponent+=shift
    if exponent==0 and mantissa==1.:return values
    with np.errstate(over='ignore',under='ignore',invalid='ignore'):
        if mantissa==1.:return _ldexp(values,exponent)
        result=np.empty(values.shape,dtype=complex)
        # Apply the final exponent once per component, even for subnormals.
        for component,target in ((values.real,result.real),(values.imag,result.imag)):
            fraction,shift=np.frexp(component)
            target[:]=np.ldexp(fraction*mantissa,shift+exponent)
        return result
