"""Fourier numérica del registro finito y estimadores espectrales calibrados."""
import math
import numpy as np
from scipy.signal import get_window

from .model import Signal
from .engine import evaluate_expression
from .operations import _discrete, _finite_output
from .resources import ensure_working_set
from .sampling import positive_integer, positive_finite
from .jobs import checkpoint


def grid(start, stop, count):
    count = positive_integer(count, "Puntos de salida")
    start, stop = float(start), float(stop)
    if not math.isfinite(start) or not math.isfinite(stop) or stop <= start or count < 2:
        raise ValueError("La rejilla requiere extremos finitos crecientes y al menos dos puntos.")
    ensure_working_set(count, live_arrays=10)
    values = np.linspace(start, stop, count)
    if np.any(np.diff(values) <= 0):
        raise ValueError("El paso de la rejilla no se distingue con precisión float64.")
    return values


def _sum(values, input_axis, output_axis, sign=-1):
    """Suma compleja por bloques: no construye una matriz N por M completa."""
    ensure_working_set(int(len(values)+len(output_axis)), live_arrays=10)
    rows, cols = min(128, len(output_axis)), min(2048, len(values))
    ensure_working_set(int(rows*cols), live_arrays=4)
    result = np.zeros(len(output_axis), dtype=complex)
    for start in range(0, len(output_axis), rows):
        checkpoint(start/len(output_axis))
        target = output_axis[start:start+rows]
        accumulator = np.zeros(len(target), dtype=complex)
        for offset in range(0, len(values), cols):
            checkpoint()
            phase = np.multiply.outer(target, input_axis[offset:offset+cols])
            if not np.all(np.isfinite(phase)):
                raise ValueError("El producto de coordenadas excede el rango numérico de fase.")
            accumulator += np.exp(sign*1j*phase) @ values[offset:offset+cols]
        result[start:start+rows] = accumulator
    checkpoint(1)
    return _finite_output(result, "La transformada")


def _frequency_signal(values, frequencies, name, units, metadata):
    return Signal(values, float(frequencies[0]), float(frequencies[1]-frequencies[0]),
                  units, name, "frequency", "", metadata)


def dtft(x, start=-math.pi, stop=math.pi, count=1025):
    _discrete(x)
    last = int(x.origin)+x.values.size-1
    if max(abs(int(x.origin)), abs(last)) > 2**53:
        raise ValueError("La fase de DTFT requiere índices representables exactamente en float64 (|n| ≤ 2^53).")
    omega = grid(start, stop, count)
    values = _sum(x.values, x.axis.astype(float), omega)
    return _frequency_signal(values, omega, f"DTFT_{x.name}", "rad/muestra",
        {"operation": "DTFT", "input_origin": int(x.origin), "input_length": int(x.values.size),
         "convention": "sum x[n] exp(-j*w*n); finite record, zero outside"})


def dtft_with_dft(x,start,stop,count):
    """Misma DTFT independiente; DFT sobre sus propias frecuencias, sin interpolar."""
    spectrum=dtft(x,start,stop,count)
    n=x.values.size;spacing=2*np.pi/n
    first=math.ceil(float(start)/spacing);last=math.floor(float(stop)/spacing)
    if max(abs(first),abs(last))>2**53:
        raise ValueError('El intervalo excede la precisión de las frecuencias de la DFT.')
    size=max(0,last-first+1);ensure_working_set(int(n+size),live_arrays=10)
    indices=np.arange(size,dtype=np.int64)+first
    omega=indices*spacing
    values=np.fft.fft(x.values)[indices % n]*np.exp(-1j*omega*int(x.origin))
    return spectrum,(omega,values)


def discrete_series(x):
    _discrete(x)
    n = x.values.size
    ensure_working_set(int(n), live_arrays=8)
    k = np.arange(n, dtype=float)
    # Origen reducido módulo N antes de pasarlo a float.
    coefficients = np.fft.fft(x.values)/n * np.exp(-2j*np.pi*k*((int(x.origin)%n)/n))
    return Signal(_finite_output(coefficients, "La serie discreta"), 0, 1, "k", f"DFS_{x.name}", "discrete", "",
                  {"operation": "discrete_fourier_series", "period_samples": int(n),
                   "input_origin": int(x.origin), "convention": "c[k]=(1/N) sum over one period x[n] exp(-j*2*pi*k*n/N)"})


def synthesize_discrete(coefficients):
    if coefficients.metadata.get("operation") != "discrete_fourier_series":
        raise ValueError("Cargá coeficientes producidos por Serie discreta.")
    n = coefficients.values.size
    origin = int(coefficients.metadata["input_origin"])
    ensure_working_set(int(n), live_arrays=8)
    values = np.fft.ifft(coefficients.values * np.exp(2j*np.pi*np.arange(n)*((origin%n)/n)))*n
    return Signal(_finite_output(values, "La síntesis"), origin, 1, "n", "Síntesis_DFS", "discrete", "",
                  {"operation": "discrete_series_synthesis", "period_samples": int(n)})


def ctft(x, start, stop, count):
    if x.domain != "continuous" or x.step <= 0:
        raise ValueError("La CTFT numérica requiere un registro temporal con paso positivo en segundos.")
    omega = grid(start, stop, count)
    from .distributions import dirac_terms
    impulses=dirac_terms(x)
    values = _sum(x.values, x.axis, omega)*x.step if np.any(x.values) else np.zeros(omega.size,dtype=complex)
    for position,weight in impulses:values+=weight*np.exp(-1j*omega*position)
    return _frequency_signal(_finite_output(values, "La CTFT"), omega, f"CTFT_{x.name}", "rad/s",
        {"operation": "CTFT_rectangle", "input_start": x.origin, "input_step": x.step,
         "input_dirac_terms": [[t,[float(w.real),float(w.imag)]] for t,w in impulses],
         "convention": "dt*sum regular(tk) exp(-j*w*tk) plus exact Fourier terms of Dirac impulses, when present; finite regular window quadrature"})


def ictft(spectrum, start, stop, count):
    from .distributions import regular_only
    regular_only(spectrum,'La Fourier inversa numérica de muestras; usá la inversa algebraica para distribuciones')
    if spectrum.domain != "frequency" or spectrum.units != "rad/s" or spectrum.step <= 0:
        raise ValueError("La inversa requiere un espectro con eje uniforme en rad/s y paso positivo.")
    time = grid(start, stop, count)
    weighted = spectrum.values.copy()
    if len(weighted) == 1: weighted[:] = 0
    else: weighted[0] *= .5; weighted[-1] *= .5
    values = _sum(weighted, spectrum.axis, time, sign=1)*spectrum.step/(2*np.pi)
    return Signal(_finite_output(values, "La inversa de Fourier"), float(time[0]), float(time[1]-time[0]),
                  "s", "ICTFT", "continuous", "",
                  {"operation": "ICTFT", "convention": "Trapezoidal quadrature over finite frequency window; 1/(2*pi)"})


def continuous_series(expression, start, period, samples, harmonics):
    period = positive_finite(period, "Periodo T")
    samples = positive_integer(samples, "Celdas por periodo")
    if isinstance(harmonics, bool) or not isinstance(harmonics, int) or harmonics < 0:
        raise ValueError("K debe ser un entero no negativo.")
    count = 2*harmonics+1
    ensure_working_set(samples+count, live_arrays=10)
    start = float(start)
    time = start+(np.arange(samples)+.5)*(period/samples)
    if not np.all(np.isfinite(time)) or (samples > 1 and np.any(np.diff(time) <= 0)):
        raise ValueError("Los centros de celda no se distinguen con la precisión disponible.")
    from .continuous_expression import sample_continuous
    from .distributions import dirac_terms
    source=sample_continuous(expression,float(time[0]),period/samples,samples,support=(start,start+period),right_open=True)
    time=source.axis;values=source.values;impulses=dirac_terms(source)
    k = np.arange(-harmonics, harmonics+1, dtype=np.int64)
    coeff = _sum(values, time, k*(2*np.pi/period))/samples if np.any(values) else np.zeros(k.size,dtype=complex)
    for position,weight in impulses:coeff+=weight*np.exp(-1j*k*(2*np.pi/period)*position)/period
    return Signal(coeff, -harmonics, 1, "k", "Coeficientes_FS", "discrete", expression,
                  {"operation": "continuous_fourier_series", "period_s": period, "period_start_s": start,
                   "cells": samples, "harmonics_each_side": harmonics,
                   "input_dirac_terms":[[t,[float(w.real),float(w.imag)]] for t,w in impulses],
                   "convention": "Midpoint quadrature of the ordinary part on one period plus exact Dirac weights; impulses use [start,start+T). c[k]=(1/T) integral x(t) exp(-j*k*w0*t) dt"})


def synthesize_continuous(coefficients, start, stop, count):
    if coefficients.metadata.get("operation") != "continuous_fourier_series":
        raise ValueError("Cargá coeficientes de Serie continua.")
    if coefficients.domain!='discrete' or coefficients.units not in ('n','k') or coefficients.metadata.get('distribution'):raise ValueError('La síntesis requiere coeficientes c[k] con índice armónico entero, no pesos de líneas espectrales.')
    period=positive_finite(coefficients.metadata['period_s'],'Período T')
    time = grid(start, stop, count)
    omega = coefficients.axis*(2*np.pi/period)
    values = _sum(coefficients.values, omega, time, sign=1)
    return Signal(values, float(time[0]), float(time[1]-time[0]), "s", "Síntesis_FS", "continuous", "",
                  {"operation": "continuous_series_synthesis", "harmonics": int(coefficients.values.size),
                   "convention": "Finite sum of harmonics; may exhibit Gibbs near jumps"})


def spectral_density(x, rate, *, method="welch", segment=256, overlap=128,
                     window="hann", beta=5.0, remove_mean=False):
    _discrete(x)
    rate = positive_finite(rate, "Fs")
    if method not in {"welch", "periodogram", "legacy"}:
        raise ValueError("Estimador desconocido.")
    if method != "welch": segment, overlap = int(x.values.size), 0
    segment = positive_integer(segment, "Longitud de segmento")
    if segment > x.values.size or isinstance(overlap, bool) or not isinstance(overlap, int) or not 0 <= overlap < segment:
        raise ValueError("Se requiere segmento ≤ N y solape entero entre 0 y segmento−1.")
    if window not in {"boxcar", "hann", "hamming", "blackman", "kaiser"}:
        raise ValueError("Ventana desconocida.")
    if not math.isfinite(beta) or beta < 0:
        raise ValueError("Beta debe ser finito y no negativo.")
    ensure_working_set(segment, live_arrays=14)
    weights = get_window(("kaiser", beta) if window == "kaiser" else window, segment, fftbins=False)
    energy = float(np.sum(weights**2))
    if not math.isfinite(energy) or energy <= 0:
        raise ValueError("La ventana tiene energía nula o no finita; cambiá ventana o segmento.")
    hop = segment-overlap
    blocks = 1+(x.values.size-segment)//hop
    power = np.zeros(segment)
    divisor = segment if method == "legacy" else rate*energy
    if not math.isfinite(divisor) or divisor <= 0:
        raise ValueError("La escala espectral queda fuera del rango numérico.")
    for block in range(blocks):
        checkpoint(block/blocks)
        values = x.values[block*hop:block*hop+segment]
        if remove_mean: values = values-np.mean(values)
        transformed = np.fft.fft(values*weights)
        estimate = np.abs(transformed / math.sqrt(divisor))**2
        if not np.all(np.isfinite(estimate)):
            raise FloatingPointError("La potencia espectral excede float64.")
        power += (estimate-power)/(block+1)
    checkpoint(1)
    frequencies = np.fft.fftshift(np.fft.fftfreq(segment, d=1/rate))
    if segment == 1:
        origin, step = 0, rate
    else: origin, step = float(frequencies[0]), rate/segment
    return Signal(np.fft.fftshift(power), origin, step, "Hz", f"PSD_{method}_{x.name}", "frequency", "",
                  {"operation": "spectral_density", "estimator": method, "density_units": "amplitude²/Hz" if method != "legacy" else "amplitude²",
                   "sample_rate_hz": rate, "window": window, "segment": segment, "overlap": overlap,
                   "segments_used": int(blocks), "unused_tail": int(x.values.size-((blocks-1)*hop+segment)),
                   "remove_segment_mean": bool(remove_mean), "sidedness": "two-sided, FFT-shifted",
                   "convention": "Symmetric window; mean of |FFT(window*x)|²/(Fs*sum(window²)); legacy uses /N"})


def energy_density(spectrum):
    from .distributions import regular_only
    regular_only(spectrum,'La densidad de energía de valores de X(ω)')
    if spectrum.domain != "frequency":raise ValueError("La densidad espectral requiere un espectro, no un registro temporal.")
    if spectrum.units not in {'rad/s','rad/muestra'}:raise ValueError('Definí el eje del espectro en rad/s o rad/muestra.')
    if spectrum.metadata.get('distribution') or spectrum.metadata.get('operation') in {'continuous_fourier_series','discrete_fourier_series'}:
        raise ValueError('Los coeficientes de serie y los pesos de deltas describen una señal periódica. Usá Potencia periódica y líneas espectrales; no se puede elevar una delta al cuadrado como una muestra ordinaria.')
    if spectrum.metadata.get('operation') in {'energy_density','spectral_density','welch','periodogram'}:raise ValueError('La entrada ya es una densidad. Cargá una señal o su espectro complejo X.')
    values = _finite_output(abs(spectrum.values)**2, "La densidad de energía")
    return Signal(values, spectrum.origin, spectrum.step, spectrum.units, "Densidad_energía", "frequency", "",
                  {"operation": "energy_density", "discrete_spectrum": bool(spectrum.metadata.get("discrete_spectrum")) or spectrum.metadata.get("operation") in {"DFT","stft"}, "convention": "|X|²; integral dω/(2π) over shown band is partial energy"})


def energy_report(spectrum, source=None, density=None):
    """Explain finite-band quadrature and the conditions for a Parseval check."""
    if density is None:density=energy_density(spectrum)
    if density.step<=0:raise ValueError('La integración requiere un eje creciente con paso positivo.')
    count=density.values.size;start=density.origin;stop=start+(count-1)*density.step
    power=density.values.real
    area=float(np.trapezoid(power,dx=density.step)/(2*np.pi))
    if not np.isfinite(area):raise ValueError('La integral de energía excede el rango numérico.')
    lines=['Densidad espectral de energía','D(ω) = |X(ω)|²','E = integral D(ω) dω / (2π)',
           '',f'Intervalo representado: [{start:.12g}, {stop:.12g}] {spectrum.units}',
           f'Puntos: {count}; paso angular: {density.step:.12g}',
           f'Energía integrada en ese intervalo: {area:.12g}',
           'La integración usa trapecios y no duplica una banda positiva.']
    if count<2:lines+=['Un solo punto no define una banda de integración: el intervalo tiene ancho cero.']
    operation=spectrum.metadata.get('operation')
    complete_fft=(operation=='DFT' and spectrum.units=='rad/muestra' and np.isclose(count*spectrum.step,2*np.pi,rtol=1e-10,atol=0))
    if complete_fft:
        energy=float(np.sum(power/count))
        if not np.isfinite(energy):raise ValueError('La suma de Parseval excede el rango numérico.')
        lines+=['','Parseval de la DFT',f'Suma |X[k]|²/N = {energy:.12g}',
                'La DFT contiene N frecuencias sin repetir el extremo de su período. Esta suma incluye el período completo; la integral anterior abarca sólo del primer al último punto.',
                'La energía corresponde al registro transformado, incluida su ventana, recorte o escala si los hubiera.']
    if source is not None and source.domain=='discrete':
        from .operations import finite_measures
        energy=finite_measures(source).energy
        lines+=['','Comparación temporal',f'Suma |x[n]|² = {energy:.12g}']
        if np.isclose(stop-start,2*np.pi,rtol=1e-10,atol=0):
            difference=abs(area-energy)
            lines += [f'Diferencia absoluta: {difference:.12g}']
            if energy:lines += [f'Diferencia relativa: {difference/energy:.6g}']
            if count-1<source.values.size:
                lines+=['Rejilla insuficiente para una comprobación general de Parseval: usá al menos N+1 puntos para un registro de N muestras en un período de 2π. Una rejilla gruesa puede ocultar oscilaciones de |X|².']
            else:lines+=['Se integró un período completo con al menos N subintervalos. Para este registro finito, la identidad de Parseval debe coincidir salvo redondeo numérico.']
        else:lines+=['No se compara como energía total: el intervalo no es exactamente un período de 2π. Una banda parcial omite energía; varios períodos la cuentan varias veces.']
    elif source is not None and source.domain=='continuous':
        from .distributions import dirac_terms
        if dirac_terms(source):
            lines+=['','Entrada con impulso ideal','La entrada incluye impulsos Dirac. Su transformada incluye sus pesos y fases exactos, pero esta señal no tiene energía finita ordinaria: no se puede integrar el cuadrado de una delta como una función ordinaria. La energía de la banda mostrada no es la energía total de la señal.']
            return '\n'.join(lines)
        energy=float(np.sum(abs(source.values)**2)*source.step)
        if not np.isfinite(energy):raise ValueError('La energía temporal excede el rango numérico.')
        lines+=['','Referencia temporal',f'Suma rectangular Δt·Σ|x(tk)|² = {energy:.12g}',
                'La transformada numérica usa una suma sobre un registro muestreado. La banda espectral finita, el paso temporal y los extremos afectan la aproximación; no se certifica Parseval de la señal continua completa.',
                'La transformada de estas muestras repite su módulo cada 2π/Δt. Integrar más allá de un período puede contar réplicas numéricas; aumentá la resolución temporal para analizar una banda mayor.']
    else:lines+=['','Interpretación','Sin el registro temporal no se puede comprobar su energía. En discreto, Parseval usa un período de 2π; en continuo, la integral sobre una banda finita es sólo parcial.']
    lines+=['','Gráfico','La vista en dB usa 10 log10(D), equivalente a 20 log10(|X|). Los valores nulos corresponden a −∞ dB y no se dibujan como valores finitos.']
    return '\n'.join(lines)
