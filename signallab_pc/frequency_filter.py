"""Filtros definidos por respuesta en frecuencia; cuadratura explícita, sin ajuste racional."""
import math

import numpy as np

from .model import Signal
from .fourier import ctft_on_grid,_sum
from .fourier_phase import periodic_indices,periodic_phase
from .resources import ensure_working_set
from .operations import _finite_output
from .spectral_scaling import bounded,restore_scale,fft_values


def analyze(response,domain,start,count,step,source=None,*,allow_periodic=False):
    from .distributions import regular_only

    from .signal_semantics import require_frequency_response,require_temporal
    require_frequency_response(response)
    regular_only(response,'El filtro definido por valores de H(ω)')
    if source is not None:require_temporal(source)
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

    from .inverse_fourier_report import numeric_model
    source_clock=source.metadata if source is not None else {}
    impulse_clock={}
    if digital:
        from .system_clock import input_period_metadata,inverse_spectrum_clock,spectrum_clock,validate_period
        if start!=int(start) or step!=1:raise ValueError('La salida discreta requiere inicio entero y paso 1.')
        start=int(start)
        limit=np.iinfo(np.int64)
        if start<limit.min or start+count-1>limit.max:
            raise ValueError('La salida excede los índices enteros de 64 bits.')
        closed = math.isclose((size-1)*response.step,math.tau,rel_tol=1e-12)
        if not closed and not math.isclose(size*response.step,math.tau,rel_tol=1e-12):
            raise ValueError('H debe cubrir un período completo de 2π rad/muestra, con o sin el extremo repetido.')
        independent=size-int(closed)
        period=validate_period(response.metadata.get('period_s'))
        impulse_clock=inverse_spectrum_clock(response,start,count)
        if source is not None:
            source_clock=input_period_metadata(period,source)
        folded_input=source is not None and source.values.size>independent
        if folded_input and not allow_periodic:
            raise ValueError(f'La rejilla tiene {independent} frecuencias independientes para {source.values.size} muestras. Aumentá la rejilla o activá el plegado periódico de la entrada.')

        def inverse(values,first,length):
            if closed:
                last=values[-1]
                values=values[:-1].copy()
                values[0]=.5*values[0]+.5*last
            coefficients=_finite_output(fft_values(values,inverse=True),'La inversa de H o de Y')
            phase=periodic_phase(response.origin,independent,first,length)
            return coefficients[periodic_indices(first,length,independent)]*phase,coefficients

        impulse,coefficients=inverse(response.values,start,count)
        inverse_model=numeric_model('periodic',response.origin,response.step,coefficients)
        approximation='periodic inverse Fourier'
        if source is not None:
            samples=source.values.size
            ensure_working_set(samples+size,live_arrays=12)
            phase=periodic_phase(response.origin,independent,int(source.origin),samples)
            folded=np.zeros(independent,dtype=complex)
            scaled,exponent=bounded(source.values)
            np.add.at(folded,periodic_indices(int(source.origin),samples,independent),scaled*phase.conj())
            spectrum=_finite_output(restore_scale(np.fft.fft(folded),exponent),'La DTFT de la entrada')
            if closed:spectrum=np.r_[spectrum,spectrum[0]]
            x=Signal(spectrum,response.origin,response.step,unit,'DTFT_'+source.name,'frequency',
                     metadata={'operation':'DTFT',**spectrum_clock(source,source_clock),'input_length':samples})
            y_values=spectrum*response.values
            output_values,_=inverse(y_values,int(source.origin),samples)
    else:
        weights=np.ones(size)
        weights[[0,-1]]*=.5
        axis=start+step*np.arange(count)
        if not np.isfinite(axis).all():raise ValueError('El intervalo de salida debe ser finito y creciente.')
        factors=(response.step,1/math.tau)
        impulse=_sum(response.values*weights,w,axis,sign=1,factors=factors)
        approximation='trapezoidal inverse Fourier'
        inverse_model=numeric_model('quadrature',response.origin,response.step,response.values)
        if source is not None:
            x=ctft_on_grid(source,w,response.step)
            y_values=x.values*response.values
            output_values=_sum(y_values*weights,w,source.axis,sign=1,factors=factors)

    grid_metadata={'frequency_start':float(w[0]),'frequency_stop':float(w[-1]),'frequency_points':size}
    h=Signal(impulse,start,step,'n' if digital else 's','Respuesta al impulso h',domain,
             metadata={**grid_metadata,**impulse_clock,'operation':'frequency_filter_impulse','approximation':approximation,'inverse_model':inverse_model})
    outputs=[response,h]
    if source is not None:
        y=x.copy_with(values=y_values,name='Espectro de salida Y = H·X',
                      metadata={**x.metadata,'filter_expression':response.expression,'filter_model':'frequency_response'})
        clock={key:source_clock[key] for key in ('sample_rate_hz','time_start_s','time_mapping') if key in source_clock}
        metadata={**clock,**grid_metadata,'operation':'frequency_filter_output',
                  'filter_expression':response.expression,'approximation':approximation}
        output=source.copy_with(values=output_values,name='Salida filtrada y',expression='',metadata=metadata)
        outputs.extend([x,y,output])
    report='Filtro definido en frecuencia\n\nH(ω) indica cuánto amplifica y retrasa cada componente sinusoidal. La definición puede tener tramos y valores complejos.\n\nY(ω) = H(ω) X(ω)\n\nLa respuesta al impulso y la salida se calculan por integración numérica (regla del trapecio). Aumentá la cantidad de frecuencias para estudiar la convergencia cerca de discontinuidades. No se ajusta un FIR ni un IIR.\n\nUn filtro ideal con corte abrupto puede tener respuesta infinita en el tiempo y no ser causal. El tramo de h mostrado no es toda la respuesta ni un FIR equivalente. La salida se muestra sobre el mismo intervalo de la entrada; no representa su cola completa.\n\n'+('En discreto se integra un período completo de 2π sobre la rejilla ingresada. Una rejilla finita produce repetición numérica en el tiempo; ampliá su resolución para separar las réplicas del intervalo que estudiás.' if domain=='discrete' else 'En continuo se integra sólo la banda de frecuencias indicada. La energía fuera de esa banda se omite: un pasaaltos ideal requiere una banda cada vez más amplia para aproximar su efecto. El impulso de Dirac de una ganancia constante no se representa exactamente mediante esta cuadratura.')+'\n\nExportar H conserva sus muestras y su fórmula. Se puede volver a cargar en esta herramienta. Los menús que requieren coeficientes b/a describen otro tipo de representación.'
    if digital:
        rule = 'suma periódica con peso medio en los extremos repetidos' if closed else 'suma periódica sin extremo repetido'
        report=report.replace('regla del trapecio',rule)
        if folded_input:
            report+=f'\n\nPlegado periódico habilitado. Se sumaron las muestras separadas por {independent} índices antes de aplicar H. La salida representa esa secuencia periódica.'
            output.metadata.update(periodic_input_folded=True,periodic_samples=independent)
    return outputs,report
