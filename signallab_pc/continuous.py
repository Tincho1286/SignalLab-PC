"""Operaciones sobre registros continuos interpolados linealmente y nulos fuera."""
import math

import numpy as np
from scipy.signal import convolve
from .model import Signal
from .resources import ensure_working_set
from .operations import _finite_output
from .jobs import checkpoint


def _validate(x):
    if x.domain!='continuous' or x.step<=0 or x.values.size<2:
        raise ValueError('Se requiere un registro continuo con al menos dos puntos y paso positivo.')
    if x.units!='s':raise ValueError('El eje temporal debe estar expresado en segundos.')


def interpolate_record(source,axis):
    points=source.axis
    # Snap only sub-sample roundoff at the endpoints, not exterior intervals.
    tolerance=min(source.step/4,max(4*math.ulp(float(points[0])),4*math.ulp(float(points[-1]))))
    adjusted=np.where(np.abs(axis-points[0])<=tolerance,points[0],np.where(np.abs(axis-points[-1])<=tolerance,points[-1],axis))
    return np.interp(adjusted,points,source.values.real,left=0,right=0)+1j*np.interp(adjusted,points,source.values.imag,left=0,right=0)


def convolution(x,h):
    """Integral exacta del producto de interpolantes en la rejilla de salida.

    Cada par de segmentos lineales tiene producto cuadrático: Simpson es
    exacto en cada intervalo. Las cuatro convoluciones evitan una matriz Nx*Nh.
    Esto no afirma exactitud para las funciones originales entre las muestras.
    """
    _validate(x);_validate(h)
    if not np.isclose(x.step,h.step,rtol=1e-12,atol=0):
        raise ValueError('Los registros deben usar el mismo paso temporal. Remuestreá uno antes de combinarlos.')
    size=int(x.values.size+h.values.size-1);ensure_working_set(size,live_arrays=18)
    # Acumular una convolución a la vez para limitar la memoria temporal.
    interior=np.zeros(size-2,dtype=np.complex128)
    for left,right,weight in [(x.values[:-1],h.values[:-1],1),
                              (x.values[:-1],h.values[1:],2),
                              (x.values[1:],h.values[:-1],2),
                              (x.values[1:],h.values[1:],1)]:
        checkpoint();interior+=weight*convolve(left,right,mode='full',method='auto')
    values=np.zeros(size,dtype=np.complex128);values[1:-1]=interior*(x.step/6)
    from .distributions import dirac_terms,attach_terms
    tx,th=dirac_terms(x),dirac_terms(h)
    ensure_working_set(len(tx)*len(th),live_arrays=8)
    origin=x.origin+h.origin;products=[(a+b,u*v) for a,u in tx for b,v in th]
    if tx or th:
        starts=[origin];ends=[origin+(size-1)*x.step]
        for t,_ in tx:starts.append(t+h.origin);ends.append(t+h.origin+(h.values.size-1)*h.step)
        for t,_ in th:starts.append(t+x.origin);ends.append(t+x.origin+(x.values.size-1)*x.step)
        for t,_ in products:starts.append(t);ends.append(t)
        first=int(np.floor((min(starts)-origin)/x.step));last=int(np.ceil((max(ends)-origin)/x.step))
        count=last-first+1;ensure_working_set(count,live_arrays=12)
        regular=np.zeros(count,dtype=complex);regular[-first:-first+size]=values
        origin=origin+first*x.step;axis=origin+x.step*np.arange(count)
        if not np.all(np.isfinite(axis)) or np.any(np.diff(axis)<=0):raise ValueError('La rejilla de la convolución no distingue sus coordenadas.')
        def interpolate(source,delay):
            positions=(axis-delay-source.origin)/source.step;nearest=np.rint(positions)
            positions=np.where(abs(positions-nearest)<=32*np.finfo(float).eps*np.maximum(1,abs(positions)),nearest,positions)
            return np.interp(positions,np.arange(source.values.size),source.values,left=0,right=0)
        for t,weight in tx:checkpoint();regular+=weight*interpolate(h,t)
        for t,weight in th:checkpoint();regular+=weight*interpolate(x,t)
        values=regular
    checkpoint()
    singular=attach_terms({},products)
    result = Signal(_finite_output(values,'La convolución continua'),origin,x.step,'s',
        f'{x.name} * {h.name}','continuous','',
        {**singular,'operation':'continuous_convolution','dirac_rule':'regular convolution + weighted shifted regular terms + pairwise Dirac products','input_model':'linear interpolation between endpoints; zero outside closed finite interval',
         'quadrature':'exact segment-product integral at output grid, up to floating point error',
         'convention':'y(t)=integral x(tau) h(t-tau) d tau',
         'input_intervals':[[x.origin,x.origin+(x.values.size-1)*x.step],[h.origin,h.origin+(h.values.size-1)*h.step]],
         'sample_step_s':x.step})
    from .quality_steps import convolution as steps
    result.metadata['derivation']=steps(x,h,result,continuous=True)
    result.metadata['derivation_operation']=result.metadata['operation']
    return result


def _unit_energy(x):
    from .distributions import regular_only
    regular_only(x,'La normalización por energía')
    scale=max(float(np.max(np.abs(x.values.real))),float(np.max(np.abs(x.values.imag))))
    if scale==0:raise ValueError('La correlación normalizada no está definida para energía cero.')
    values=x.values/scale
    left,right=values[:-1],values[1:]
    energy=x.step*np.sum(np.abs(left)**2+np.abs(right)**2+np.real(left*np.conj(right)))/3
    if not np.isfinite(energy) or energy<=0:raise ValueError('La energía no es representable con esta escala temporal.')
    return x.copy_with(values=values/np.sqrt(energy))


def correlation(x,h=None,*,normalized=False):
    h=x if h is None else h;_validate(x);_validate(h)
    if not np.isclose(x.step,h.step,rtol=1e-12,atol=0):raise ValueError('Los registros deben usar el mismo paso temporal.')
    from .distributions import dirac_terms,attach_terms,regular_only
    if normalized or not (dirac_terms(x) or dirac_terms(h)):
        def grid(source):
            values=source.values
            if normalized:
                regular_only(source,'La correlación normalizada')
                scale=max(float(np.max(abs(values.real))),float(np.max(abs(values.imag))))
                if not scale:raise ValueError('La correlación normalizada no está definida para energía cero.')
                values=values/scale;a,b=values[:-1],values[1:]
                energy=float(np.sum(abs(a)**2+abs(b)**2+(a*b.conj()).real)/3)
                values=values/np.sqrt(energy)
            return Signal(values,0,1,'s',source.name,'continuous')
        left,right=grid(x),grid(h)
        reflected=Signal(right.values[::-1].conj(),-(len(right.values)-1),1,'s',h.name,'continuous')
        unit=convolution(left,reflected)
        values=unit.values if normalized else unit.values*x.step
        origin=(x.origin-h.origin)-(len(h.values)-1)*x.step
        result=Signal(_finite_output(values,'La correlación continua'),origin,x.step,'s',f'r({x.name},{h.name})','continuous',metadata={'input_model':'linear interpolation; zero outside finite support','sample_step_s':x.step})
    else:
        reflected=Signal(np.conj(h.values[::-1]),-(h.origin+(h.values.size-1)*h.step),h.step,'s',h.name,'continuous',metadata=attach_terms({},[(-t,w.conjugate()) for t,w in dirac_terms(h)]))
        result=convolution(x,reflected);result.name=f'r({x.name},{h.name})'
    result.metadata.update(operation='continuous_correlation',normalized=normalized,
        convention='r(tau)=integral x(t) conjugate(h(t-tau)) dt; no mean subtraction',
        normalization='sqrt(Ex*Eh) of linear interpolants' if normalized else 'none')
    return result


def periodic_correlation(x,h=None,*,normalization='sum'):
    """Un periodo sin repetir el extremo, con interpolación lineal periódica."""
    h=x if h is None else h;_validate(x);_validate(h)
    from .distributions import regular_only
    regular_only(x,'La correlación periódica');regular_only(h,'La correlación periódica')
    if x.values.size!=h.values.size or not np.isclose(x.step,h.step,rtol=1e-12,atol=0):
        raise ValueError('Los periodos deben tener igual cantidad de puntos y paso temporal.')
    if normalization not in ('sum','energy','mean'):raise ValueError('Escala de correlación desconocida.')
    size=int(x.values.size);period=size*x.step
    if not np.isfinite(period) or period<=0:raise ValueError('El periodo excede el rango numérico.')
    ensure_working_set(size,live_arrays=18)
    def unit_values(source):
        scale=max(float(np.max(np.abs(source.values.real))),float(np.max(np.abs(source.values.imag))))
        if scale==0:raise ValueError('La correlación normalizada no está definida para energía cero.')
        values=source.values/scale;next_values=np.roll(values,-1)
        energy=np.sum(abs(values)**2+abs(next_values)**2+np.real(values*np.conj(next_values)))/3
        if not np.isfinite(energy) or energy<=0:raise ValueError('La energía del periodo no es representable.')
        return values/np.sqrt(energy)
    left,right=(unit_values(x),unit_values(h)) if normalization=='energy' else (x.values,h.values)
    checkpoint();discrete=np.fft.ifft(np.fft.fft(left)*np.conj(np.fft.fft(right)))
    values=(2/3)*discrete+(1/6)*np.roll(discrete,1)+(1/6)*np.roll(discrete,-1)
    if normalization=='mean':values/=size
    elif normalization!='energy':values*=x.step
    checkpoint()
    return Signal(_finite_output(values,'La correlación periódica continua'),x.origin-h.origin,x.step,'s',f'R({x.name},{h.name})','continuous','',
        {'operation':'periodic_continuous_correlation','period_s':period,'normalization':normalization,
         'input_model':'N samples per period T=N*dt, endpoint excluded; periodic linear interpolation',
         'convention':'integral over one period x(t) conjugate(h(t-tau)) dt; no mean subtraction',
         'output_lags':'x.origin-h.origin + k*dt, one period',
         'quadrature':'exact segment-product integrals at aligned lag grid, up to floating point error'})


def transform_time(source, amplitude=1, time_scale=1, delay=0):
    """y(t)=A*x(a*(t-t0)): transforma el eje del registro sin interpolar."""
    _validate(source)
    amplitude=complex(amplitude);time_scale=float(time_scale);delay=float(delay)
    if not np.isfinite(amplitude) or not np.isfinite(time_scale) or not np.isfinite(delay):
        raise ValueError("Amplitud, escala y desplazamiento deben ser finitos.")
    if time_scale==0:
        raise ValueError("La escala temporal a debe ser distinta de cero. a=0 requiere conocer x(0) y definir otra ventana de salida.")
    reverse=time_scale<0
    first=source.origin+(source.values.size-1)*source.step if reverse else source.origin
    origin=first/time_scale+delay
    step=source.step/abs(time_scale)
    last=origin+(source.values.size-1)*step
    if not np.isfinite(origin) or not np.isfinite(last) or not np.isfinite(step) or step<=0:
        raise ValueError("El eje transformado excede el rango numérico disponible.")
    if source.values.size>1 and (origin+step<=origin or last-step>=last):
        raise ValueError("El paso temporal no se distingue con ese desplazamiento y escala.")
    values=_finite_output(amplitude*(source.values[::-1] if reverse else source.values),"La amplitud transformada")
    from .distributions import dirac_terms,attach_terms
    singular=attach_terms({},[(t/time_scale+delay,amplitude*w/abs(time_scale)) for t,w in dirac_terms(source)])
    if source.units=='s':
        singular['time_start_s']=origin;rate=1/step
        if np.isfinite(rate):singular['sample_rate_hz']=rate
    singular['input_expression']=source.expression
    return Signal(values,origin,step,source.units,"Señal transformada y(t)","continuous","",{**singular,
        "operation":"continuous_time_transform",
        "convention":"y(t)=A*x(a*(t-t0))",
        "amplitude":[amplitude.real,amplitude.imag],"time_scale":time_scale,"delay":delay,
        "source_interval":[source.origin,source.origin+(source.values.size-1)*source.step],
        "scope":"Transformación del registro finito; no extrapola la señal fuera de su intervalo. Se conserva la cantidad de puntos y se transforma su eje, sin interpolar.",
    })


def finite_measures(x):
    """Exact L2 integral of the piecewise-linear model on the stored interval."""
    from .distributions import dirac_terms
    from .operations import FiniteMeasures
    if x.domain!='continuous' or x.values.size<2:raise ValueError('Usá un registro continuo con al menos dos puntos y un intervalo no nulo.')
    if dirac_terms(x):raise ValueError('No se asignan energía y RMS finitos a impulsos Dirac ideales.')
    ensure_working_set(int(x.values.size),live_arrays=7)
    duration=abs(float(x.step))*(int(x.values.size)-1)
    if not np.isfinite(duration) or duration<=0:raise ValueError('La duración del registro debe ser positiva y finita.')
    magnitudes=np.abs(x.values)
    if not np.all(np.isfinite(magnitudes)):raise FloatingPointError('La magnitud excede el rango numérico finito.')
    scale=float(np.max(magnitudes));energy=power=rms=0.
    if scale:
        q=x.values/scale;a=q[:-1];b=q[1:]
        mean=float(np.sum(abs(a)**2+(a*b.conj()).real+abs(b)**2)/(3*len(a)))
        rms=scale*np.sqrt(mean);power=float(rms)*float(rms)
        amplitude=float(rms)*np.sqrt(duration);energy=float(amplitude)*float(amplitude)
        if not np.isfinite(power) or not np.isfinite(energy):raise FloatingPointError('La energía o la potencia excede el rango de float64; revisá las unidades y la escala.')
        if not power or not energy:raise FloatingPointError('La energía o la potencia queda por debajo del rango representable de float64.')
    first=float(x.origin);last=first+float(x.step)*(len(x.values)-1)
    return FiniteMeasures(energy=float(energy),average_power=float(power),rms=float(rms),sample_count=len(x.values),interpretation='Integral exacta del modelo interpolado linealmente entre puntos; no determina la señal fuera del intervalo.',domain='continuous',interval=(min(first,last),max(first,last)),integration='piecewise_linear',duration=duration,axis_units=x.units)
