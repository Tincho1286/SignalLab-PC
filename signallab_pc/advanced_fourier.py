"""Zoom FFT and sampled Z contours with the discrete Fourier phase convention."""

from dataclasses import dataclass
import math

import numpy as np
from scipy.fft import next_fast_len
from scipy.optimize import brentq
from scipy.signal import ZoomFFT, find_peaks

from .communications_data import integer, real
from .execution import ExecutionContext
from .fourier import grid
from .fourier_phase import dtft_angles
from .model import Signal
from .operations import _discrete, _finite_output
from .signal_semantics import require_temporal
from .spectral_scaling import bounded, restore_scale
from .system_clock import common_rate, spectrum_clock
from .window_signals import window_samples


MAX_CONTOUR_SAMPLES = 262_145
MAX_RADIAL_PRODUCTS = 32_000_000


@dataclass(frozen=True, slots=True)
class SpectralPeak:
    bin_index: int
    sampled_frequency: float
    refined_frequency: float
    amplitude: float | None
    phase_rad: float | None
    level_relative_db: float


@dataclass(frozen=True, slots=True)
class ZoomSpectrum:
    spectrum: Signal
    input_length: int
    grid_step: float
    nominal_dft_spacing: float
    duration_s: float | None
    peaks: tuple[SpectralPeak, ...]
    dft_bins: np.ndarray | None
    dft_values: np.ndarray | None


@dataclass(frozen=True, slots=True)
class ChirpZResult:
    samples: Signal
    z: np.ndarray


def _checked_signal(source):
    _discrete(source)
    require_temporal(source)
    if not np.isfinite(source.values).all():
        raise ValueError('La señal debe tener muestras complejas finitas.')
    return int(source.origin)


def _sample_rate(source, entered):
    known = common_rate(source)
    if entered is None:
        return known
    entered = real(entered, 'Frecuencia de muestreo en Hz', positive=True)
    if known is not None and not math.isclose(entered, known, rel_tol=1e-12):
        raise ValueError('La frecuencia de muestreo no coincide con el reloj registrado.')
    return entered


def _zoom_values(source, normalized, ctx, origin):
    scaled, exponent = bounded(source)
    first, last = float(normalized[0]), float(normalized[-1])
    transformer = ZoomFFT(len(source), [first, last], m=len(normalized), fs=math.tau, endpoint=True)
    ctx.checkpoint()
    transform = transformer(scaled)
    ctx.checkpoint()
    _, shift = dtft_angles(normalized, first, last, origin)
    return _finite_output(restore_scale(transform * shift, exponent), 'La transformada')


def _peaks(values, axis, angular, origin, weights, interpolants, limit, ctx):
    scaled, exponent = bounded(values, normalize=True)
    magnitudes = np.abs(interpolants)
    maximum = float(magnitudes.max())
    if not maximum:
        return ()
    significant = maximum * 1e-7  # Operational threshold, presented as −140 dB relative.
    indices, _ = find_peaks(magnitudes, height=significant, plateau_size=(1, 1))
    indices = sorted(indices, key=lambda index: (-magnitudes[index], index))
    local = np.arange(len(values), dtype=float)
    weight_sum = float(np.sum(weights))
    if abs(weight_sum) <= 16*np.finfo(float).eps*np.sum(np.abs(weights)):
        raise ValueError('La ventana tiene ganancia coherente nula. Elegí otra para estimar amplitud y fase.')
    rows = []
    for index in indices[:limit]:
        ctx.checkpoint()
        left, center, right = angular[index-1:index+2]

        def phase_vector(w):
            ctx.checkpoint()
            return np.exp(-1j*w*local)

        derivatives = -1j*local*scaled

        def slope(w):
            phases = phase_vector(w)
            return float(np.real(np.dot(derivatives,phases)*np.conj(np.dot(scaled,phases))))

        frequency = float(center)
        if slope(left)>0 and slope(right)<0:
            frequency = brentq(slope,left,right,xtol=max(1e-15,4*math.ulp(frequency)))
        # Off-grid components near a neighbouring tone are estimates of a local maximum.
        correction = dtft_angles(np.array([frequency, frequency]), float(frequency), float(frequency), origin)[1][0]
        sample = np.dot(scaled, phase_vector(frequency)) * correction / weight_sum
        calibrated = restore_scale(np.array([sample]), exponent)[0]
        coordinate = axis[index] + (frequency-center) * (axis[1]-axis[0]) / (angular[1]-angular[0])
        amplitude = float(abs(calibrated))
        amplitude = amplitude if np.isfinite(amplitude) else None
        phase = float(np.angle(sample)) if sample else None
        rows.append(SpectralPeak(int(index), float(axis[index]), float(coordinate), amplitude, phase,
                                 float(20*(np.log10(magnitudes[index])-np.log10(maximum)))))
    return tuple(rows)


def zoom_fft(source: Signal, start, stop, count=1025, *, units='rad/muestra', rate_hz=None,
             window='boxcar', window_options=None, complex_tone_peaks=0, compare_dft=False, context=None):
    """Evaluate the DTFT on a closed grid. Peak amplitudes assume isolated complex tones."""
    ctx = context if context is not None else ExecutionContext()
    ctx.checkpoint()
    origin = _checked_signal(source)
    count = integer(count, 'Puntos de Zoom FFT', minimum=2, maximum=MAX_CONTOUR_SAMPLES)
    peak_count = integer(complex_tone_peaks, 'Cantidad de picos', minimum=0, maximum=50)
    if type(compare_dft) is not bool:
        raise ValueError('Indicá si querés superponer los bins de la DFT.')
    low, high = real(start, 'Inicio de banda'), real(stop, 'Fin de banda')
    rate = _sample_rate(source, rate_hz)
    if units not in ('rad/muestra', 'Hz') or (units == 'Hz' and rate is None):
        raise ValueError('Elegí rad/muestra o definí el reloj de la señal para usar Hz.')
    length = source.values.size
    if (not isinstance(window_options, (dict, type(None)))
            or set(window_options or {}) - {'symmetric', 'beta', 'alpha', 'nw', 'attenuation_db'}):
        raise ValueError('Parámetros de ventana espectral no reconocidos.')
    work = 160 * next_fast_len(length + count - 1) + 72 * (length + count) + (144*length if compare_dft else 0)
    with ctx.reserve(work):
        axis = grid(low, high, count)
        angular = axis if units == 'rad/muestra' else (axis / rate)*math.tau
        if (not np.isfinite(angular).all() or np.any(np.diff(angular) <= 0)
                or np.max(abs(angular)) > math.tau or angular[-1] - angular[0] > math.tau*(1+1e-14)):
            raise ValueError('Elegí un intervalo de hasta un período, con frecuencias normalizadas dentro de ±2π.')
        weights = window_samples(window, length, **(window_options or {}))
        values = _finite_output(source.values * weights, 'La señal enventanada')
        transformed = _zoom_values(values, angular, ctx, origin)
        peaks = _peaks(values, axis, angular, origin, weights, transformed, peak_count, ctx) if peak_count else ()
        bins=coefficients=None
        if compare_dft:
            from .fourier_phase import bin_frequency, bin_range, dft_values
            first,last=bin_range(float(angular[0]),float(angular[-1]),length)
            indices=np.arange(first,last+1,dtype=np.int64)
            bins=bin_frequency(indices,length)
            coefficients=dft_values(values,length,origin)[indices%length]
            if units=='Hz':
                bins=(bins/math.tau)*rate
            ctx.checkpoint()
        step = (high-low)/(count-1)
        spacing = (math.tau if units == 'rad/muestra' else rate)/length
        elapsed = real(length/rate, 'Duración del registro en s', positive=True) if rate else None
        clock = spectrum_clock(source)
        if rate is not None:
            clock['input_clock']['sample_rate_hz'] = rate
        metadata = {**clock, 'operation':'zoom_fft', 'input_length':int(length), 'window':window,
                    'window_options':dict(window_options or {}), 'frequency_bounds':[low,high],
                    'grid_step':step, 'nominal_dft_spacing':spacing, 'duration_s':elapsed,
                    'phase_reference':'sample_indices',
                    'convention':'Sum x[n] w[n] exp(-j*w*n). Closed grid; finer spacing does not improve physical resolution.'}
        spectrum = Signal(transformed, low, step, units, 'Zoom FFT · '+source.name, 'frequency', metadata=metadata)
    ctx.checkpoint()
    return ZoomSpectrum(spectrum, int(length), step, spacing, elapsed, peaks, bins, coefficients)


def chirp_z(source: Signal, count, *, initial_radius=1, initial_angle_rad=0, radius_ratio=1,
            angle_step_rad=None, context=None):
    """Evaluate X(z)=sum x[n] z^-n on z[k]=r0 * ratio^k * exp(j*(θ0+k*Δθ))."""
    ctx = context if context is not None else ExecutionContext()
    ctx.checkpoint()
    origin = _checked_signal(source)
    count = integer(count, 'Puntos de Chirp-Z', minimum=2, maximum=MAX_CONTOUR_SAMPLES)
    radius = real(initial_radius, 'Radio inicial', positive=True)
    ratio = real(radius_ratio, 'Razón entre radios', positive=True)
    first = real(initial_angle_rad, 'Ángulo inicial en rad')
    step = math.tau/count if angle_step_rad is None else real(angle_step_rad, 'Paso angular en rad')
    last = first + (count-1)*step
    if max(abs(first),abs(last)) > math.tau or abs(last-first) > math.tau*(1+1e-14):
        raise ValueError('El recorrido angular admite un período, dentro de ±2π.')
    if first == last and (step or ratio == 1):
        raise ValueError('Definí puntos de contorno distinguibles.')
    size = source.values.size
    unit_circle = radius == ratio == 1
    if not unit_circle and size*count > MAX_RADIAL_PRODUCTS:
        raise ValueError(f'El contorno fuera del círculo unidad admite hasta {MAX_RADIAL_PRODUCTS} productos.')
    scratch = 160 * next_fast_len(size+count-1) if unit_circle else 100 * min(size,2048)*min(count,64)
    with ctx.reserve(scratch+80*(size+count)):
        angular = first + step*np.arange(count)
        if step and np.any(np.diff(angular)==0):
            raise ValueError('El paso angular no se distingue en doble precisión.')
        if unit_circle:
            values = _zoom_values(source.values, angular, ctx, origin) if step>0 else (
                _zoom_values(source.values, angular[::-1], ctx, origin)[::-1])
            z = np.exp(1j*angular)
        else:
            log_radii = math.log(radius) + math.log(ratio)*np.arange(count)
            if ratio != 1 and np.any(np.diff(log_radii)==0) and not step:
                raise ValueError('El paso radial no se distingue en doble precisión.')
            bound = float(max(abs(log_radii[0]), abs(log_radii[-1])))
            if bound * max(1, abs(origin), abs(origin+size-1)) > 680:
                raise ValueError('El contorno y los índices combinados exceden el rango exponencial admitido.')
            values = _radial_sum(source.values, angular, log_radii, origin, ctx)
            z = np.exp(log_radii+1j*angular)
        metadata = {**spectrum_clock(source), 'operation':'chirp_z', 'length':size, 'radius':radius,
                    'radius_ratio':ratio, 'initial_angle_rad':first, 'angle_step_rad':step,
                    'convention':'z[k] = r0 * ratio^k * exp(j*(angle0+k*step)); sum x[n] z[k]^(-n).'}
        samples = Signal(values, 0, 1, 'paso de CZT', 'Chirp-Z · '+source.name, 'frequency', metadata=metadata)
    ctx.checkpoint()
    return ChirpZResult(samples, z)


def _radial_sum(values, angular, log_radii, origin, ctx):
    scaled, exponent = bounded(values, normalize=True)
    local = np.arange(len(values), dtype=float)
    _, shift = dtft_angles(angular, float(angular[0]), float(angular[-1]), origin)
    result = np.zeros(len(angular), dtype=complex)
    for first in range(0, len(angular), 64):
        section = slice(first, first+64)
        radius = log_radii[section]
        w = angular[section]
        scaling = np.maximum(0,-radius*(len(values)-1))
        accumulator = np.zeros(w.shape, dtype=complex)
        for start in range(0, len(values), 2048):
            ctx.checkpoint()
            segment = slice(start, start+2048)
            azimuth = np.multiply.outer(-w, local[segment])
            real_part = np.multiply.outer(-radius, local[segment])-scaling[:,None]
            accumulator += np.exp(real_part+1j*azimuth) @ scaled[segment]
        for i, scaled_value in enumerate(accumulator, first):
            factor = math.exp(float(scaling[i-first]) - origin*log_radii[i])
            result[i] = restore_scale(np.array([scaled_value*shift[i]]), exponent, factor)[0]
    return _finite_output(result, 'La transformada Z en el contorno')
