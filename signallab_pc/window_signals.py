"""Finite symmetric windows as independent discrete signals."""
import re
from fractions import Fraction
import numpy as np
from scipy.signal import get_window
from .model import Signal
from .filters import positive_integer
from .resources import ensure_working_set

WINDOWS=(('Rectangular','boxcar'),('Hann','hann'),('Hamming','hamming'),('Blackman','blackman'),('Bartlett (triangular)','bartlett'),('Kaiser','kaiser'))


def generate_window(window,length,origin=0,beta=8.6):
    names={key:name for name,key in WINDOWS}
    if window not in names:raise ValueError('Elegí una ventana disponible.')
    length=positive_integer(length,'Longitud L')
    if isinstance(origin,bool) or int(origin)!=origin:raise ValueError('El índice inicial n₀ debe ser entero.')
    origin=int(origin);limit=np.iinfo(np.int64)
    if origin<limit.min or origin+length-1>limit.max:raise ValueError('El intervalo excede el rango de índices enteros.')
    if window=='kaiser' and (not np.isfinite(beta) or beta<0):raise ValueError('β de Kaiser debe ser finito y no negativo.')
    ensure_working_set(length,live_arrays=10)
    with np.errstate(over='ignore',invalid='ignore',under='ignore'):
        values=get_window(('kaiser',beta) if window=='kaiser' else window,length,fftbins=False)
        if window=='kaiser' and not np.isfinite(values).all():
            from scipy.special import i0e
            local=np.linspace(-1,1,length);radial=np.sqrt(np.maximum(0,1-local*local))
            values=np.exp(beta*(radial-1))*i0e(beta*radial)/i0e(beta)
    if length>1 and window in ('hann','blackman','bartlett'):
        # These endpoints are exactly zero by definition, not a magnitude cutoff.
        values[0]=values[-1]=0.
    if not np.isfinite(values).all():raise ValueError('La ventana no es representable con los parámetros elegidos.')
    metadata={'operation':'window_generation','window':window,'window_name':names[window],'window_length':length,'symmetric':True,'support_start':origin,'support_end':origin+length-1,'outside_support':'zero','normalization':'standard window; no additional gain normalization','scope':'Secuencia finita de L muestras sobre índices enteros, cero fuera del intervalo. Se usa la ventana simétrica del diseño FIR; no se supone repetición periódica ni se renormaliza la ganancia.'}
    if window=='kaiser':metadata['beta']=float(beta)
    result=Signal(values,origin,1,'n','Ventana '+names[window]+' · L='+str(length),'discrete',metadata=metadata)
    from .temporal_formula import attach_temporal_formula
    formula=summary(result).sections[0].formulas[0].expression.split(' = ',1)[1]
    return attach_temporal_formula(result,dict(evaluated=True,result=formula,display_numeric=True,scope=metadata['scope']))


def summary(signal):
    from .result_summary import Summary,Section,Formula,number
    from .fir_formula import window_expression
    meta=signal.metadata;length=len(signal.values);origin=signal.origin;last=origin+length-1
    if length==1:core='1'
    else:
        core=window_expression(meta['window'],length,meta.get('beta',0))
        local='n' if origin==0 else '(n+'+str(-origin)+')' if origin<0 else '(n-'+str(origin)+')'
        core=re.sub(r'\bn\b',lambda _:local,core)
    expression='Piecewise(('+core+', '+str(origin)+' <= n <= '+str(last)+'), (0, True))'
    rows=[('Ventana',meta['window_name']),('Longitud L (muestras)',str(length)),('Índices',str(origin)+' a '+str(last)),('Centro geométrico',str(Fraction(2*origin+length-1,2))),('Simetría','Simétrica, como en diseño FIR')]
    if meta['window']=='kaiser':rows.append(('β de Kaiser',number(meta['beta'])))
    if length==1:rows.append(('Única muestra', '1'))
    return Summary(signal.name,[Section('Ventana generada',rows=rows,formulas=[
        Formula('w[n] = '+expression,'w[n] = '+core+' para '+str(origin)+' ≤ n ≤ '+str(last)+'. Vale cero fuera de ese intervalo.',numeric=True)
    ])])
