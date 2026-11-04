"""Filtros definidos por respuesta en frecuencia; cuadratura explícita, sin ajuste racional."""
import math

import numpy as np

from .model import Signal
from .fourier import ctft,_sum
from .resources import ensure_working_set


def _periodic_phase(origin, size, start, count):
    """Phase e^(i*origin*n) without converting an absolute index to float."""
    from fractions import Fraction
    from .fourier_phase import _angles, _simple_cycles, bin_frequency

    offset = origin/math.tau
    cycles = _simple_cycles(origin)
    if abs(offset*size) < 2**52:
        nearest_bin = round(offset*size)
        if bin_frequency(nearest_bin,size)==origin:
            cycles = Fraction(nearest_bin,size)
        elif abs(origin-(-math.pi+math.pi/size))<=4*math.ulp(origin):
            cycles = Fraction(1-size,2*size)
    if cycles is not None:
        angle = _angles(count,cycles.numerator*start,cycles.numerator,cycles.denominator,1)
    else:
        import mpmath

        context = mpmath.mp.clone()
        context.dps = 50 + max(0,math.frexp(abs(origin))[1]//3)
        period = 2*context.pi
        initial = float(context.fmod(context.mpf(origin)*start,period))
        increment = float(context.fmod(context.mpf(origin),period))
        angle = initial+increment*np.arange(count)
    return np.exp(1j*angle)


def _periodic_indices(start, count, size):
    return (np.arange(count,dtype=np.int64)+start%size)%size


def analyze(response,domain,start,count,step,source=None):
    from .distributions import regular_only

    regular_only(response,'El filtro definido por valores de H(ω)')
    if response.domain!='frequency' or response.step<=0 or response.values.size<2:
        raise ValueError('H requiere al menos dos frecuencias crecientes con paso uniforme.')
    digital = domain=='discrete'
    unit = 'rad/muestra' if digital else 'rad/s'
    if response.units!=unit:raise ValueError('Las unidades de H deben ser '+unit+'.')
    w = response.axis
    size = len(w)
    if not np.all(np.isfinite(w)):raise ValueError('El eje de frecuencias debe ser finito.')
    if count<2 or count!=int(count):raise ValueError('Usá al menos dos puntos de salida.')
    count = int(count)
    ensure_working_set(count+size,live_arrays=12)
    if not np.isfinite(start) or not np.isfinite(step) or step<=0:
        raise ValueError('El intervalo de salida debe ser finito y creciente.')
    if source is not None and source.domain!=domain:
        raise ValueError('La señal y el filtro deben usar el mismo dominio temporal.')

    if digital:
        if start!=int(start) or step!=1:raise ValueError('La salida discreta requiere inicio entero y paso 1.')
        start=int(start)
        limit=np.iinfo(np.int64)
        if start<limit.min or start+count-1>limit.max:
            raise ValueError('La salida excede los índices enteros de 64 bits.')
        closed = math.isclose((size-1)*response.step,math.tau,rel_tol=1e-12)
        if not closed and not math.isclose(size*response.step,math.tau,rel_tol=1e-12):
            raise ValueError('H debe cubrir un período completo de 2π rad/muestra, con o sin el extremo repetido.')
        independent=size-int(closed)

        def inverse(values,first,length):
            if closed:
                last=values[-1]
                values=values[:-1].copy()
                values[0]=.5*values[0]+.5*last
            coefficients=np.fft.ifft(values)
            phase=_periodic_phase(response.origin,independent,first,length)
            return coefficients[_periodic_indices(first,length,independent)]*phase

        impulse=inverse(response.values,start,count)
        approximation='periodic inverse Fourier'
        if source is not None:
            samples=source.values.size
            ensure_working_set(samples+size,live_arrays=12)
            phase=_periodic_phase(response.origin,independent,int(source.origin),samples)
            folded=np.zeros(independent,dtype=complex)
            np.add.at(folded,_periodic_indices(int(source.origin),samples,independent),source.values*phase.conj())
            spectrum=np.fft.fft(folded)
            if closed:spectrum=np.r_[spectrum,spectrum[0]]
            x=Signal(spectrum,response.origin,response.step,unit,'DTFT_'+source.name,'frequency',
                     metadata={'operation':'DTFT','input_origin':int(source.origin),'input_length':samples})
            y_values=spectrum*response.values
            output_values=inverse(y_values,int(source.origin),samples)
    else:
        weights=np.full(size,response.step)
        weights[[0,-1]]*=.5
        axis=start+step*np.arange(count)
        if not np.isfinite(axis).all():raise ValueError('El intervalo de salida debe ser finito y creciente.')
        impulse=_sum(response.values*weights,w,axis,sign=1)/math.tau
        approximation='trapezoidal inverse Fourier'
        if source is not None:
            x=ctft(source,float(w[0]),float(w[-1]),size)
            y_values=x.values*response.values
            output_values=_sum(y_values*weights,w,source.axis,sign=1)/math.tau

    grid_metadata={'frequency_start':float(w[0]),'frequency_stop':float(w[-1]),'frequency_points':size}
    h=Signal(impulse,start,step,'n' if digital else 's','Respuesta al impulso h',domain,
             metadata={**grid_metadata,'operation':'frequency_filter_impulse','approximation':approximation})
    outputs=[response,h]
    if source is not None:
        y=x.copy_with(values=y_values,name='Espectro de salida Y = H·X',
                      metadata={**x.metadata,'filter_expression':response.expression,'filter_model':'frequency_response'})
        clock={key:source.metadata[key] for key in ('sample_rate_hz','time_start_s','time_mapping') if key in source.metadata}
        metadata={**clock,**grid_metadata,'operation':'frequency_filter_output',
                  'filter_expression':response.expression,'approximation':approximation}
        output=source.copy_with(values=output_values,name='Salida filtrada y',expression='',metadata=metadata)
        outputs.extend([x,y,output])
    report='Filtro definido en frecuencia\n\nH(ω) indica cuánto amplifica y retrasa cada componente sinusoidal. La definición puede tener tramos y valores complejos.\n\nY(ω) = H(ω) X(ω)\n\nLa respuesta al impulso y la salida se calculan por integración numérica (regla del trapecio). Aumentá la cantidad de frecuencias para estudiar la convergencia cerca de discontinuidades. No se ajusta un FIR ni un IIR.\n\nUn filtro ideal con corte abrupto puede tener respuesta infinita en el tiempo y no ser causal. El tramo de h mostrado no es toda la respuesta ni un FIR equivalente. La salida se muestra sobre el mismo intervalo de la entrada; no representa su cola completa.\n\n'+('En discreto se integra un período de −π a π. Una rejilla finita produce repetición numérica en el tiempo; ampliá su resolución para separar las réplicas del intervalo que estudiás.' if domain=='discrete' else 'En continuo se integra sólo la banda de frecuencias indicada. La energía fuera de esa banda se omite: un pasaaltos ideal requiere una banda cada vez más amplia para aproximar su efecto. El impulso de Dirac de una ganancia constante no se representa exactamente mediante esta cuadratura.')+'\n\nExportar H conserva sus muestras y su fórmula. Se puede volver a cargar en esta herramienta. Los menús que requieren coeficientes b/a describen otro tipo de representación.'
    if digital:
        rule = 'suma periódica con peso medio en los extremos repetidos' if closed else 'suma periódica sin extremo repetido'
        report=report.replace('regla del trapecio',rule)
    return outputs,report
