"""Inverse DTFT over one complete angular period, without an IDFT input model."""
import math
import numpy as np
from .model import Signal
from .sampling import positive_integer
from .resources import ensure_working_set
from .operations import _finite_output
from .jobs import checkpoint
from .fourier_phase import periodic_indices,periodic_phase
from .fourier import require_complex_spectrum

def inverse_dtft(spectrum,start,count):
    from .distributions import regular_only
    regular_only(spectrum,'La DTFT inversa numérica de muestras; usá la inversa algebraica para distribuciones')
    require_complex_spectrum(spectrum)
    if spectrum.domain!='frequency' or spectrum.units!='rad/muestra':raise ValueError('La DTFT inversa necesita X(ω) en rad/muestra. No usa frecuencias en rad/s ni Hz.')
    if isinstance(start,bool) or int(start)!=start:raise ValueError('El primer índice n debe ser entero.')
    start=int(start);count=positive_integer(count,'Cantidad de muestras');last=start+count-1
    limit=np.iinfo(np.int64)
    if start<limit.min or last>limit.max:raise ValueError('La salida excede los índices enteros de 64 bits.')
    size=len(spectrum.values);step=float(spectrum.step)
    if size<2 or step<=0:raise ValueError('Ingresá al menos dos frecuencias en orden creciente.')
    period=2*math.pi
    closed=math.isclose((size-1)*step,period,rel_tol=1e-10,abs_tol=1e-12)
    opened=math.isclose(size*step,period,rel_tol=1e-10,abs_tol=1e-12)
    if not closed and not opened:raise ValueError('La rejilla debe cubrir un período de 2π: (cantidad−1)·paso=2π con extremo repetido, o cantidad·paso=2π sin repetirlo. Una banda parcial no define la inversa completa.')
    ensure_working_set(size+count,live_arrays=12);checkpoint()
    values=spectrum.values.copy()
    if closed:
        values=values[:-1];values[0]=spectrum.values[0]/2+spectrum.values[-1]/2
    length=len(values);coefficients=np.fft.ifft(values)
    origin=float(spectrum.origin)
    indices=periodic_indices(start,count,length)
    multiplier=periodic_phase(origin,length,start,count)
    result=_finite_output(coefficients[indices]*multiplier,'La DTFT inversa');checkpoint(1)
    return Signal(result,start,1,'n','DTFT inversa · '+spectrum.name,'discrete','',{
        'operation':'inverse_dtft','convention':'x[n] = integral_over_one_period X(w)*exp(i*w*n) dw / (2*pi)',
        'frequency_units':'rad/muestra','frequency_origin':origin,'frequency_step':step,'frequency_samples':size,
        'independent_frequencies':length,'quadrature':'Trapezoidal: extremos con peso 1/2' if closed else 'Periódica: sin duplicar el extremo',
        'endpoint_policy':'El primer y último valor comparten peso si ambos extremos están incluidos.' if closed else 'Todos los puntos tienen el mismo peso.',
        'scope':'Coeficientes de Fourier aproximados de X(ω), no una secuencia causal impuesta. La rejilla finita confunde índices separados por '+str(length)+'; puede introducir un factor de fase según el inicio del período. Pedir más índices no agrega información espectral.'})
