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


def fft_values(values, *, size=None, inverse=False):
    """Keep butterfly sums in range until the FFT normalization is applied."""
    if size is not None:
        values=values[:size]
    scaled,exponent=bounded(values)
    transform=np.fft.ifft if inverse else np.fft.fft
    return restore_scale(transform(scaled,n=size),exponent)


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


def energy_description(values,divisor=1):
    """Describe a finite sum of squares without squaring extreme amplitudes."""
    scaled,exponent=bounded(np.asarray(values,dtype=complex))
    total=float(np.sum(scaled.real**2+scaled.imag**2))
    if not np.isfinite(total):raise ValueError('No se obtuvo una suma de energía finita normalizada.')
    if total==0:return '0'
    fraction,shift=math.frexp(total);factor,offset=math.frexp(float(divisor))
    fraction/=factor;shift+=2*exponent-offset
    try:number=math.ldexp(fraction,shift)
    except OverflowError:number=float('inf')
    if math.isfinite(number) and number!=0:return format(number,'.12g')
    logarithm=math.log10(fraction)+shift*math.log10(2);decimal_exp=math.floor(logarithm)
    mantissa=10**(logarithm-decimal_exp)
    return format(mantissa,'.12g')+'e'+str(decimal_exp)+' (finita; fuera del rango float64)'
