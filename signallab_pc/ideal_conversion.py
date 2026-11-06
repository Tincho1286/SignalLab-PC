"""Conversion of explicitly defined analog frequency responses (not rational fits)."""
import math
import numpy as np
from .engine import evaluate_expression
from .model import Signal
from .resources import ensure_working_set
from .jobs import checkpoint
from .operations import _finite_output


def convert_response(expression,period,method,count=2049,support=None):
    from .continuous_expression import has_dirac
    if has_dirac(expression):raise ValueError('La conversión de H(jΩ) por una rejilla requiere una respuesta ordinaria. Los impulsos ideales en frecuencia deben trabajarse como distribuciones en Fourier algebraica; no son valores de un filtro.')
    if not np.isfinite(period) or period<=0:raise ValueError('T debe ser positivo y finito, en segundos.')
    if isinstance(count,bool) or int(count)!=count or count<3:raise ValueError('Usá al menos tres puntos de frecuencia.')
    count=int(count);ensure_working_set(count,live_arrays=12)
    # Cell centers avoid the infinite bilinear mapping at +/- pi.
    step=2*np.pi/count;omega=-np.pi+(np.arange(count)+.5)*step
    if method=='bilinear':
        analog=(2/period)*np.tan(omega/2)
        if not np.all(np.isfinite(analog)):raise ValueError('El mapeo excede el rango numérico; revisá T.')
        values=evaluate_expression(expression,analog)
        convention='Hd(exp(jω)) = Ha(j (2/T) tan(ω/2))'
        note='Mapeo bilineal de la respuesta sobre el eje de frecuencia. No suma réplicas, pero deforma las frecuencias. No determina por sí solo una realización causal o racional. Los extremos ±π se excluyen porque corresponden a frecuencia analógica infinita.'
    elif method=='impulse':
        if support is None or not np.isfinite(support) or support<=0:raise ValueError('Indicá Ωmáx positiva: Ha es cero fuera de [−Ωmáx, Ωmáx].')
        radius=period*support
        if not np.isfinite(radius):raise ValueError('T·Ωmáx excede el rango numérico.')
        bound=math.ceil((radius+np.pi)/(2*np.pi))
        values=np.zeros(count,dtype=complex)
        sampled_support=False
        for k in range(-bound,bound+1):
            checkpoint((k+bound)/(2*bound+1));analog=(omega+2*np.pi*k)/period
            mask=np.abs(analog)<=support
            if np.any(mask):
                sampled_support=True
                values[mask]+=evaluate_expression(expression,analog[mask])
        if not sampled_support:
            raise ValueError('La rejilla no muestrea el soporte analógico declarado. Aumentá los puntos de frecuencia antes de convertir.')
        convention='h[n] = T ha(nT); Hd(exp(jω)) = Σk Ha(j(ω+2πk)/T)'
        note='Se suman todas las réplicas del soporte finito declarado. Fuera de |Ω| ≤ Ωmáx se define Ha=0. Puede aparecer aliasing si T·Ωmáx supera π. Para una respuesta de soporte infinito, recortarla cambia el filtro; no se afirma una conversión exacta del original.'
    else:raise ValueError('Elegí bilineal o invarianza al impulso.')
    checkpoint(1)
    metadata={'operation':'frequency_filter','time_domain':'discrete','conversion':method,'period_s':period,'analog_expression':expression,'support_rad_s':support if method=='impulse' else None,'convention':convention,'scope':'sampled frequency response; not finite rational coefficients'}
    response=Signal(_finite_output(values,'La conversión ideal'),float(omega[0]),float(step),'rad/muestra','Filtro digital por respuesta en frecuencia','frequency',metadata=metadata)
    report='Conversión de filtro analógico ideal o por tramos\n\n'+convention+'\n\nT = '+str(period)+' s\n'+note+'\n\nEl resultado es una respuesta en frecuencia muestreada. Usá «Usar filtro en…» → «Filtros ideales y por tramos» para obtener h[n] o aplicarlo a una señal. La inversión de esta rejilla es una aproximación; un salto ideal exige refinarla. No se fabrican coeficientes b/a de un filtro ideal.'
    return {'report':report,'signals':[response],'systems':[]}


def windowed_conversion(expression,period,method,count,support,length,window,beta=5):
    from scipy.signal import get_window
    from .filters import Transfer
    from .fourier import _sum
    if length<3 or int(length)!=length or length%2!=1:raise ValueError('La longitud FIR debe ser impar y al menos 3 para centrar y desplazar la respuesta.')
    if count<length:raise ValueError('La rejilla de frecuencia debe tener al menos tantos puntos como coeficientes FIR; refinála para comprobar convergencia.')
    if not np.isfinite(beta) or beta<0:raise ValueError('β debe ser finito y no negativo.')
    bundle=convert_response(expression,period,method,count,support);response=bundle['signals'][0]
    delay=(length-1)//2;n=np.arange(-delay,delay+1)
    impulse=_sum(response.values*response.step,response.axis,n,sign=1)/(2*np.pi)
    # Exact Hermitian samples imply a real inverse; discard only quadrature roundoff.
    if np.array_equal(response.values,response.values[::-1].conj()):impulse=impulse.real
    weights=get_window(('kaiser',beta) if window=='kaiser' else window,length,fftbins=False)
    b=_finite_output(impulse*weights,'El FIR enventanado');system=Transfer(b,[1],'digital','FIR de conversión con ventana '+window,sample_period_s=period,roc={'mode':'right'})
    samples=Signal(b,0,1,'n','Coeficientes FIR causales','discrete',metadata={'operation':'windowed_conversion','delay_samples':delay,'window':window,'period_s':period,'sample_rate_hz':1/period,'time_start_s':0.,'quadrature_points':count})
    bundle['signals'].append(samples);bundle['systems']=[system]
    bundle['report']+='\n\nFIR por ventana: se invierte H sobre la rejilla, se conserva h[n] desde −M hasta M y se multiplica por la ventana. Se desplaza M muestras para obtener coeficientes causales. M = '+str(delay)+'; longitud = '+str(length)+'. El desplazamiento agrega M muestras de retardo. La truncación y la ventana aproximan la respuesta: el resultado ya no es un filtro ideal exacto. Ventana: '+window+'.'
    return bundle
