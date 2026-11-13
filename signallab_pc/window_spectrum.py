"""Window gain, equivalent noise bandwidth and directly evaluated -3 dB width."""
import math
import numpy as np
from scipy.fft import rfft,next_fast_len
from scipy.optimize import brentq
from .resources import ensure_working_set


def analyze(source):
    from .operations import _discrete
    _discrete(source)
    values=np.asarray(source.values)
    if np.any(values.imag!=0) or np.any(values.real<0):raise ValueError('Estas medidas requieren una ventana real no negativa.')
    values=values.real;length=len(values);scale=float(values.max(initial=0))
    scaled=values/scale if scale else values
    total=float(np.sum(scaled));energy=float(np.dot(scaled,scaled))
    gain=scale*(total/length)
    metrics=dict(length=length,coherent_gain=gain,energy=(scale*scale)*energy,
                 enbw_bins=length*energy/(total*total) if total else None,
                 enbw_radians=2*np.pi*energy/(total*total) if total else None,
                 half_power_frequency=None,full_3db_width=None,normalizable=bool(total))
    size=2*next_fast_len(max(1024,8*length));ensure_working_set(size,live_arrays=6)
    spectrum=np.abs(rfft(scaled,n=size));frequency=np.linspace(0,np.pi,len(spectrum))
    relative=spectrum/total if total else spectrum
    if total and length>1:
        candidates=np.flatnonzero(relative<=1/math.sqrt(2))
        if candidates.size:
            right=int(candidates[0]);local=np.arange(length,dtype=float)-(length-1)/2
            def crossing(w):
                # Magnitude of the exact finite DTFT of the stored samples.
                amplitude=np.dot(scaled,np.exp(-1j*w*local))
                return abs(amplitude)/total-1/math.sqrt(2)
            omega=brentq(crossing,float(frequency[right-1]),float(frequency[right]),xtol=1e-14)
            metrics.update(half_power_frequency=float(omega),full_3db_width=float(2*omega))
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
          ('Ancho completo a −3.0103 dB (rad/muestra)',show('full_3db_width'))]
    notes=['La ganancia coherente mide la atenuación de una componente situada en un bin; no normaliza las muestras. El ancho equivalente de ruido compara el área de |W|² con un rectángulo de altura |W(0)|². Los bins se refieren a L, aunque después se use una FFT más larga.',
           'La figura muestra |W(ω)|/|W(0)|, con ω en rad/muestra. El ancho de media potencia mide entre −ω₃dB y +ω₃dB; no es el ancho entre ceros ni la banda de transición de un filtro. El cruce se refina evaluando la DTFT de las muestras; no depende del índice inicial.']
    if not m['normalizable']:notes.append('Todas las muestras son cero: no hay ganancia coherente ni ancho equivalente definido. La figura muestra cero sin dividir por W(0).')
    elif m['half_power_frequency'] is None:notes.append('No se alcanza media potencia entre 0 y π; no se inventa una frecuencia de cruce.')
    return Section('Propiedades espectrales',rows=rows,paragraphs=notes,formulas=[Formula('B = 2*pi*Sum(abs(w[n])**2, (n, a, a+L-1))/abs(Sum(w[n], (n, a, a+L-1)))**2','B_eq = 2π · Σ|w[n]|² / |Σw[n]|², desde n₀ hasta n₀+L−1')])
