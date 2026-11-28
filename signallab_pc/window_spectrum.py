"""Window gain, equivalent noise bandwidth and directly evaluated -3 dB width."""
import math
import numpy as np
from scipy.fft import rfft,next_fast_len
from scipy.optimize import brentq, minimize_scalar
from .resources import ensure_working_set


def analyze(source):
    from .operations import _discrete
    _discrete(source)
    values=np.asarray(source.values)
    if np.any(values.imag!=0) or not np.isfinite(values).all():raise ValueError('Estas medidas requieren una ventana real y finita.')
    values=values.real;length=len(values);scale=float(np.abs(values).max(initial=0))
    scaled=values/scale if scale else values
    total=float(np.sum(scaled));energy=float(np.dot(scaled,scaled))
    gain=scale*(total/length)
    dc=abs(total)
    normalizable=bool(dc and dc>16*np.finfo(float).eps*np.sum(np.abs(scaled)))
    metrics=dict(length=length,coherent_gain=gain,energy=(scale*scale)*energy,
                 enbw_bins=length*energy/(dc*dc) if normalizable else None,
                 enbw_radians=2*np.pi*energy/(dc*dc) if normalizable else None,
                 half_power_frequency=None,full_3db_width=None,normalizable=normalizable,
                 scalloping_db=None,main_lobe_width_rad=None,first_minimum_rad=None,
                 first_minimum_db=None,peak_sidelobe_db=None)
    size=2*next_fast_len(max(1024,8*length));ensure_working_set(size,live_arrays=6)
    spectrum=np.abs(rfft(scaled,n=size));frequency=np.linspace(0,np.pi,len(spectrum))
    relative=spectrum/dc if normalizable else spectrum
    if normalizable and length>1:
        local=np.arange(length,dtype=float)-(length-1)/2

        def response(w):
            return abs(np.dot(scaled,np.exp(-1j*w*local)))/dc

        def db(magnitude):
            return float(20*np.log10(magnitude)) if magnitude else -np.inf

        metrics['scalloping_db']=-db(response(np.pi/length))
        candidates=np.flatnonzero(relative<=1/math.sqrt(2))
        if candidates.size:
            right=int(candidates[0])
            def crossing(w):return response(w)-1/math.sqrt(2)
            omega=brentq(crossing,float(frequency[right-1]),float(frequency[right]),xtol=1e-14)
            metrics.update(half_power_frequency=float(omega),full_3db_width=float(2*omega))
            minima=np.flatnonzero((relative[1:-1]<=relative[:-2]) & (relative[1:-1]<relative[2:]))+1
            available=minima[minima>=right]
            if available.size:
                index=int(available[0])
                minimum=minimize_scalar(response, bounds=(frequency[index-1],frequency[index+1]),
                                        method='bounded', options={'xatol':1e-14})
                after=index+1+int(np.argmax(relative[index+1:]))
                if after == len(frequency)-1:
                    maximum=relative[after]
                else:
                    refine=minimize_scalar(lambda w:-response(w),
                                           bounds=(frequency[after-1],frequency[after+1]),
                                           method='bounded', options={'xatol':1e-14})
                    maximum=max(relative[after],-refine.fun,relative[-1])
                metrics.update(first_minimum_rad=float(minimum.x),main_lobe_width_rad=float(2*minimum.x),
                               first_minimum_db=db(minimum.fun),peak_sidelobe_db=db(maximum))
    # Measured zeros are represented by absent logarithmic values in JSON.
    for key in ('scalloping_db','first_minimum_db','peak_sidelobe_db'):
        if metrics[key] is not None and not np.isfinite(metrics[key]):metrics[key]=None
    return dict(metrics=metrics,frequency=frequency,magnitude=relative)


def measure_section(analysis):
    from .result_summary import Section,Formula,number
    if analysis.get('error'):
        return Section('Propiedades espectrales',paragraphs=['La ventana generada se conserva. No se pudo construir esta vista adicional: '+analysis['error']])
    m=analysis['metrics'];show=lambda key:number(m[key]) if m[key] is not None else 'No definido'
    rows=[('Ganancia coherente · Σw/L',show('coherent_gain')),('Energía · Σ|w|²',show('energy')),
          ('Ancho equivalente de ruido · bins de una DFT de L puntos',show('enbw_bins')),
          ('Ancho equivalente de ruido (rad/muestra)',show('enbw_radians')),
          ('Primera frecuencia de media potencia (rad/muestra)',show('half_power_frequency')),
          ('Ancho completo a −3.0103 dB (rad/muestra)',show('full_3db_width')),
          ('Pérdida a medio bin (dB)',show('scalloping_db')),
          ('Ancho del lóbulo entre primeros mínimos (rad/muestra)',show('main_lobe_width_rad')),
          ('Nivel del mayor lóbulo secundario (dB)',show('peak_sidelobe_db'))]
    notes=['La ganancia coherente mide la atenuación de una componente situada en un bin; no normaliza las muestras. El ancho equivalente de ruido compara el área de |W|² con un rectángulo de altura |W(0)|². Los bins se refieren a L, aunque después se use una FFT más larga.',
           'La figura muestra |W(ω)|/|W(0)|, con ω en rad/muestra. El ancho de media potencia mide entre −ω₃dB y +ω₃dB; no es el ancho entre ceros ni la banda de transición de un filtro. El cruce se refina evaluando la DTFT de las muestras; no depende del índice inicial.']
    notes.append('La pérdida a medio bin compara |W(π/L)| con |W(0)|. El primer mínimo después de media potencia delimita el lóbulo principal. El nivel posterior se estima con la rejilla mostrada y refinamiento local.')
    if not m['normalizable']:notes.append('La componente en ω=0 es nula o indistinguible de la cancelación numérica. La figura se muestra sin dividir por W(0).')
    elif m['half_power_frequency'] is None:notes.append('No se alcanza media potencia entre 0 y π; no se inventa una frecuencia de cruce.')
    return Section('Propiedades espectrales',rows=rows,paragraphs=notes,formulas=[Formula('B = 2*pi*Sum(abs(w[n])**2, (n, a, a+L-1))/abs(Sum(w[n], (n, a, a+L-1)))**2','B_eq = 2π · Σ|w[n]|² / |Σw[n]|², desde n₀ hasta n₀+L−1')])
