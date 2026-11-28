"""Finite symmetric windows as independent discrete signals."""
import re
from fractions import Fraction
import numpy as np
from scipy.signal import get_window
from .model import Signal
from .filters import positive_integer
from .resources import ensure_working_set

WINDOWS=(('Rectangular','boxcar'),('Hann','hann'),('Hamming','hamming'),('Blackman','blackman'),
         ('Bartlett (triangular)','bartlett'),('Kaiser','kaiser'),('Tukey','tukey'),('Flat Top','flattop'),
         ('Nuttall','nuttall'),('DPSS (primer taper)','dpss'),('Dolph–Chebyshev','chebwin'))
WINDOW_PARAMETERS = {
    'kaiser': ('beta', 'β de Kaiser', 8.6),
    'tukey': ('alpha', 'Fracción de coseno α', .5),
    'dpss': ('nw', 'Semiancho de banda × longitud (NW)', 2.5),
    'chebwin': ('attenuation_db', 'Atenuación de lóbulos (dB)', 90.0),
}


def window_samples(window, length, *, symmetric=True, beta=8.6, alpha=.5, nw=2.5, attenuation_db=90):
    """Build the actual finite window used by generation and Fourier tools."""
    names={key:name for name,key in WINDOWS}
    if window not in names or type(symmetric) is not bool:
        raise ValueError('Elegí una ventana disponible y el modo simétrico o periódico.')
    length=positive_integer(length,'Longitud L')
    parameters = {'beta': beta, 'alpha': alpha, 'nw': nw, 'attenuation_db': attenuation_db}
    scipy_window = window
    if window in WINDOW_PARAMETERS:
        from .communications_data import real
        key, title, _ = WINDOW_PARAMETERS[window]
        parameter = real(parameters[key], title)
        if window == 'kaiser' and parameter < 0:
            raise ValueError('β de Kaiser debe ser finito y no negativo.')
        if window == 'tukey' and not 0 <= parameter <= 1:
            raise ValueError('α de Tukey debe estar entre 0 y 1.')
        if window == 'dpss' and not (parameter > 0 and (length == 1 or parameter < length/2)):
            raise ValueError('DPSS requiere 0 < NW < L/2 con más de una muestra.')
        if window == 'chebwin' and not 45 <= parameter <= 600:
            raise ValueError('La ventana Dolph–Chebyshev admite atenuación especificada de 45 a 600 dB.')
        scipy_window = (window, parameter)
    ensure_working_set(length,live_arrays=14 if window in ('dpss', 'chebwin') else 10)
    if length == 1:
        return np.ones(1)
    with np.errstate(over='ignore',invalid='ignore',under='ignore'):
        values=get_window(scipy_window,length,fftbins=not symmetric)
        if window=='kaiser' and not np.isfinite(values).all():
            from scipy.special import i0e
            local=np.linspace(-1,1,length if symmetric else length+1)[:length]
            radial=np.sqrt(np.maximum(0,1-local*local))
            values=np.exp(beta*(radial-1))*i0e(beta*radial)/i0e(beta)
    if window in ('hann','blackman','bartlett') or (window=='tukey' and alpha>0):
        values[0]=0.
        if symmetric:
            values[-1]=0.
    if not np.isfinite(values).all():
        raise ValueError('La ventana no es representable con los parámetros elegidos.')
    return values


def generate_window(window,length,origin=0,beta=8.6,*,symmetric=True,alpha=.5,nw=2.5,attenuation_db=90):
    length=positive_integer(length,'Longitud L')
    if isinstance(origin,bool) or int(origin)!=origin:raise ValueError('El índice inicial n₀ debe ser entero.')
    origin=int(origin);limit=np.iinfo(np.int64)
    if origin<limit.min or origin+length-1>limit.max:raise ValueError('El intervalo excede el rango de índices enteros.')
    values = window_samples(window,length,symmetric=symmetric,beta=beta,alpha=alpha,nw=nw,attenuation_db=attenuation_db)
    name = dict((key,title) for title,key in WINDOWS)[window]
    scope='Secuencia finita de L muestras sobre índices enteros, cero fuera del intervalo. '+(
        'Modo simétrico para diseño FIR.' if symmetric else
        'Modo periódico para análisis DFT. Se usa la malla de un período de la ventana; el resultado es un registro finito.')
    metadata={'operation':'window_generation','window':window,'window_name':name,'window_length':length,
              'symmetric':symmetric,'support_start':origin,'support_end':origin+length-1,'outside_support':'zero',
              'normalization':'standard window; no additional gain normalization','scope':scope}
    if window in WINDOW_PARAMETERS:
        key=WINDOW_PARAMETERS[window][0]
        metadata[key]=float({'beta':beta,'alpha':alpha,'nw':nw,'attenuation_db':attenuation_db}[key])
    result=Signal(values,origin,1,'n','Ventana '+name+' · L='+str(length),'discrete',metadata=metadata)
    from .temporal_formula import attach_temporal_formula
    formulas=summary(result).sections[0].formulas
    if formulas:
        formula=formulas[0].expression.split(' = ',1)[1]
        attach_temporal_formula(result,dict(evaluated=True,result=formula,display_numeric=True,scope=metadata['scope']))
    return result


def summary(signal):
    from .result_summary import Summary,Section,Formula,number
    from .fir_formula import window_expression
    meta=signal.metadata;length=len(signal.values);origin=signal.origin;last=origin+length-1
    window=meta['window'];symmetric=meta.get('symmetric',True)
    basis=length if symmetric else length+1
    if length==1:core='1'
    elif window in ('dpss','chebwin'):core=None
    elif window in ('flattop','nuttall'):
        coeffs=((.21557895,-.41663158,.277263158,-.083578947,.006947368)
                if window=='flattop' else (.3635819,-.4891775,.1365995,-.0106411))
        core=str(coeffs[0])+''.join(f'{value:+.10g}*cos({2*index}*pi*n/{basis-1})' for index,value in enumerate(coeffs[1:],1))
    elif window=='tukey':
        alpha=meta['alpha'];d=basis-1
        if not alpha:core='1'
        elif alpha==1:core=window_expression('hann',basis,0)
        else:
            edge=alpha*d/2
            core=(f'Piecewise(((1+cos(pi*(n/{edge!r}-1)))/2, n < {edge!r}), '
                  f'((1+cos(pi*(({d}-n)/{edge!r}-1)))/2, n > {d-edge!r}), (1, True))')
    else:
        core=window_expression(window,basis,meta.get('beta',0))
    if core is not None:
        local='n' if origin==0 else '(n+'+str(-origin)+')' if origin<0 else '(n-'+str(origin)+')'
        core=re.sub(r'\bn\b',lambda _:local,core)
    rows=[('Ventana',meta['window_name']),('Longitud L (muestras)',str(length)),('Índices',str(origin)+' a '+str(last)),('Centro geométrico',str(Fraction(2*origin+length-1,2))),('Malla','Simétrica para FIR' if symmetric else 'Periódica para análisis DFT')]
    if window in WINDOW_PARAMETERS:
        key,label,_=WINDOW_PARAMETERS[window]
        rows.append((label,number(meta[key])))
    if length==1:rows.append(('Única muestra', '1'))
    section=Section('Ventana generada',rows=rows)
    if core is not None:
        expression='Piecewise(('+core+', '+str(origin)+' <= n <= '+str(last)+'), (0, True))'
        section.formulas.append(Formula('w[n] = '+expression,
            'w[n] = '+core+' para '+str(origin)+' ≤ n ≤ '+str(last)+'. Vale cero fuera de ese intervalo.',numeric=True))
    else:
        section.paragraphs.append('Primer vector de máxima concentración espectral para el semiancho indicado.'
                                  if window=='dpss' else
                                  'Secuencia simétrica calculada a partir de polinomios de Chebyshev y una DFT inversa.')
    return Summary(signal.name,[section])
