"""Filtros definidos por respuesta en frecuencia; cuadratura explícita, sin ajuste racional."""
import numpy as np
from .model import Signal
from .fourier import dtft,ctft,_sum
from .resources import ensure_working_set

def analyze(response,domain,start,count,step,source=None):
    from .distributions import regular_only
    regular_only(response,'El filtro definido por valores de H(ω)')
    if response.domain!='frequency' or response.step<=0 or response.values.size<2:
        raise ValueError('H requiere al menos dos frecuencias crecientes con paso uniforme.')
    unit='rad/muestra' if domain=='discrete' else 'rad/s'
    if response.units!=unit:raise ValueError('Las unidades de H deben ser '+unit+'.')
    w=response.axis
    if not np.all(np.isfinite(w)):raise ValueError('El eje de frecuencias debe ser finito.')
    midpoint=domain=='discrete' and np.isclose(w[0]-response.step/2,-np.pi,rtol=0,atol=1e-10) and np.isclose(w[-1]+response.step/2,np.pi,rtol=0,atol=1e-10)
    if domain=='discrete' and not midpoint and (not np.isclose(w[0],-np.pi,rtol=0,atol=1e-10) or not np.isclose(w[-1],np.pi,rtol=0,atol=1e-10)):
        raise ValueError('La respuesta debe cubrir un período de −π a π: extremos incluidos o puntos centrales de celdas uniformes.')
    if count<2 or count!=int(count):raise ValueError('Usá al menos dos puntos de salida.')
    ensure_working_set(int(count+len(w)),live_arrays=12)
    axis=start+step*np.arange(count)
    if not np.isfinite(start) or not np.isfinite(step) or step<=0 or not np.all(np.isfinite(axis)):
        raise ValueError('El intervalo de salida debe ser finito y creciente.')
    if domain=='discrete' and (start!=int(start) or step!=1):raise ValueError('La salida discreta requiere inicio entero y paso 1.')
    weights=np.full(len(w),response.step)
    if not midpoint:weights[[0,-1]]*=.5
    def inverse(values,coordinates):return _sum(values*weights,w,coordinates,sign=1)/(2*np.pi)
    h=Signal(inverse(response.values,axis),int(start) if domain=='discrete' else start,step,'n' if domain=='discrete' else 's','Respuesta al impulso h',domain,'',{'operation':'frequency_filter_impulse','approximation':'trapezoidal inverse Fourier','frequency_start':float(w[0]),'frequency_stop':float(w[-1]),'frequency_points':len(w)})
    outputs=[response,h]
    if source is not None:
        if source.domain!=domain:raise ValueError('La señal y el filtro deben usar el mismo dominio temporal.')
        x=(dtft if domain=='discrete' else ctft)(source,float(w[0]),float(w[-1]),len(w))
        y=x.copy_with(values=x.values*response.values,name='Espectro de salida Y = H·X')
        y.metadata={**x.metadata,'filter_expression':response.expression,'filter_model':'frequency_response'}
        clock = {key:source.metadata[key] for key in ('sample_rate_hz','time_start_s','time_mapping')
                 if key in source.metadata}
        metadata = {**clock, 'operation':'frequency_filter_output', 'filter_expression':response.expression,
                    'approximation':'finite-grid inverse Fourier', 'frequency_start':float(w[0]),
                    'frequency_stop':float(w[-1]), 'frequency_points':len(w)}
        output = source.copy_with(values=inverse(y.values,source.axis), name='Salida filtrada y',
                                  expression='', metadata=metadata)
        outputs.extend([x,y,output])
    report='Filtro definido en frecuencia\n\nH(ω) indica cuánto amplifica y retrasa cada componente sinusoidal. La definición puede tener tramos y valores complejos.\n\nY(ω) = H(ω) X(ω)\n\nLa respuesta al impulso y la salida se calculan por integración numérica (regla del trapecio). Aumentá la cantidad de frecuencias para estudiar la convergencia cerca de discontinuidades. No se ajusta un FIR ni un IIR.\n\nUn filtro ideal con corte abrupto puede tener respuesta infinita en el tiempo y no ser causal. El tramo de h mostrado no es toda la respuesta ni un FIR equivalente. La salida se muestra sobre el mismo intervalo de la entrada; no representa su cola completa.\n\n'+('En discreto se integra un período de −π a π. Una rejilla finita produce repetición numérica en el tiempo; ampliá su resolución para separar las réplicas del intervalo que estudiás.' if domain=='discrete' else 'En continuo se integra sólo la banda de frecuencias indicada. La energía fuera de esa banda se omite: un pasaaltos ideal requiere una banda cada vez más amplia para aproximar su efecto. El impulso de Dirac de una ganancia constante no se representa exactamente mediante esta cuadratura.')+'\n\nExportar H conserva sus muestras y su fórmula. Se puede volver a cargar en esta herramienta. Los menús que requieren coeficientes b/a describen otro tipo de representación.'
    if midpoint:report=report.replace('regla del trapecio','regla del punto medio sobre un período completo; no evalúa ±π')
    return outputs,report
