"""Binary scaling for sums and FFTs whose final normalization can be finite."""
import math
import numpy as np


def _ldexp(values, exponent):
    scaled=np.empty(values.shape,dtype=complex)
    scaled.real=np.ldexp(values.real,exponent)
    scaled.imag=np.ldexp(values.imag,exponent)
    return scaled


def bounded(values, *, normalize=False):
    peak=max(np.max(abs(values.real),initial=0.),np.max(abs(values.imag),initial=0.))
    _, exponent=math.frexp(peak)
    # Preserve the original samples at ordinary scales. This also avoids
    # a needless rounding step for mixtures of very small and large values.
    if not normalize and abs(exponent)<=450:return values,0
    with np.errstate(under='ignore'):
        return _ldexp(values,-exponent),exponent


def restore_scalar(value, exponent, *factors):
    """Restore a real scalar with a single rounding into the subnormal range."""
    fraction, shift = math.frexp(float(value))
    exponent += shift
    for factor in factors:
        part, shift = math.frexp(factor)
        fraction *= part
        exponent += shift
    try:
        return math.ldexp(fraction, exponent)
    except OverflowError:
        return math.copysign(math.inf, fraction)


def range_status(value, normalized):
    if normalized and value == 0:
        return 'underflow'
    if not math.isfinite(value):
        return 'overflow'
    return 'ok'


def centered_bounded(values):
    """Keep small fluctuations even when another component has a large DC offset."""
    parts = []
    with np.errstate(under='ignore'):
        for component in (values.real, values.imag):
            _, exponent = math.frexp(float(np.max(abs(component), initial=0)))
            scaled = np.ldexp(component, -exponent)
            shifted = scaled - scaled[0]
            shifted -= np.mean(shifted)
            peak = float(np.max(abs(shifted), initial=0))
            if peak:
                _, correction = math.frexp(peak)
                parts.append((np.ldexp(shifted, -correction), exponent + correction))
            else:
                parts.append((shifted, None))
        exponent = max((offset for _, offset in parts if offset is not None), default=0)
        result = np.empty(values.shape, dtype=complex)
        for (part, offset), target in zip(parts, (result.real, result.imag)):
            target[:] = part if offset is None else np.ldexp(part, offset-exponent)
    return result, exponent


def fft_values(values, *, size=None, inverse=False):
    """Keep butterfly sums in range until the FFT normalization is applied."""
    if size is not None:
        values=values[:size]
    scaled,exponent=bounded(values)
    transform=np.fft.ifft if inverse else np.fft.fft
    return restore_scale(transform(scaled,n=size),exponent)


def periodic_inverse_coefficients(values, *, closed):
    """Average the repeated endpoint before rounding back to the input scale."""
    if not closed:
        return fft_values(values, inverse=True)
    scaled, exponent = bounded(values)
    period = scaled[:-1].copy()
    period[0] = (scaled[0] + scaled[-1]) * .5
    return restore_scale(np.fft.ifft(period), exponent)


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
