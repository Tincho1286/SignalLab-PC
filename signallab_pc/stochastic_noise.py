"""Stationary noise generation from amplitude laws, FIRs or bilateral PSDs."""

from collections.abc import Mapping
from dataclasses import dataclass
import math
from types import MappingProxyType

import numpy as np
from scipy.signal import oaconvolve

from .communications_data import MAX_SEED, integer, real
from .execution import ExecutionContext
from .model import Signal
from .operation_provenance import content_digest, settings_digest
from .realization_batch import store_batch
from .spectral_scaling import bounded, restore_scalar, restore_scale
from .system_clock import CLOCK_MAPPING, validate_clock_resolution


COLORS = {'pink': -1, 'brown': -2, 'blue': 1, 'violet': 2}
NOISES = {
    'white_noise': ('Ruido blanco gaussiano', ('variance', 'complex')),
    'colored_noise': ('Ruido por color espectral', ('color', 'variance', 'low_hz', 'high_hz', 'complex')),
    'impulsive_noise': ('Ruido impulsivo', ('background_std', 'impulse_std', 'impulse_probability', 'complex')),
    'specified_noise': ('Ruido con PSD especificada', ('frequency_hz', 'density', 'complex')),
    'fir_noise': ('Ruido blanco filtrado por FIR', ('taps', 'variance', 'complex')),
}
FREQUENCY_NOISES = frozenset(('colored_noise', 'specified_noise'))
_MAX_INDEX = (1 << 63) - 1
_BLOCK = 8192


def _vector(values, label, *, complex_allowed=False):
    if complex_allowed and isinstance(values, Mapping):
        if set(values) != {'real', 'imag'}:
            raise ValueError(f'{label} requiere campos real e imag.')
        re = _vector(values['real'], label)
        im = _vector(values['imag'], label)
        if len(re) != len(im):
            raise ValueError(f'Las dos componentes de {label} deben tener igual longitud.')
        return tuple(complex(a,b) for a,b in zip(re,im,strict=True))
    if not isinstance(values, (tuple, list, np.ndarray)) or np.ndim(values) != 1 or not len(values):
        raise ValueError(f'{label} requiere un vector no vacío.')
    if complex_allowed:
        return tuple(complex(real(np.real(v), label), real(np.imag(v), label)) for v in values)
    return tuple(real(v, label) for v in values)


@dataclass(frozen=True, slots=True)
class Noise:
    family: str
    parameters: Mapping

    def __post_init__(self):
        if self.family not in NOISES:
            raise ValueError('Modelo de ruido desconocido.')
        _, keys = NOISES[self.family]
        if not isinstance(self.parameters, Mapping) or set(self.parameters) != set(keys):
            raise ValueError('Parámetros requeridos: ' + ', '.join(keys))
        p = dict(self.parameters)
        if type(p['complex']) is not bool:
            raise ValueError('Elegí explícitamente ruido real o complejo.')
        if 'variance' in p:
            p['variance'] = real(p['variance'], 'Varianza', minimum=0)
        if self.family == 'colored_noise':
            if p['color'] not in COLORS:
                raise ValueError('Color espectral desconocido.')
            order = COLORS[p['color']]
            p['low_hz'] = real(p['low_hz'], 'Corte inferior (Hz)', minimum=0, positive=order < 0)
            p['high_hz'] = real(p['high_hz'], 'Corte superior (Hz)', positive=True)
            if p['low_hz'] >= p['high_hz']:
                raise ValueError('El corte inferior debe ser menor que el superior.')
        elif self.family == 'specified_noise':
            f = p['frequency_hz'] = _vector(p['frequency_hz'], 'Frecuencias')
            density = p['density'] = _vector(p['density'], 'Densidad')
            if len(f) < 2 or len(f) != len(density) or any(a >= b for a,b in zip(f,f[1:])):
                raise ValueError('La PSD requiere al menos dos pares de frecuencias estrictamente crecientes.')
            if min(density) < 0 or (not p['complex'] and f[0] < 0):
                raise ValueError('La PSD debe ser no negativa. Para una señal real, ingresá su mitad f ≥ 0.')
        elif self.family == 'impulsive_noise':
            p['background_std'] = real(p['background_std'], 'Desviación de fondo', minimum=0)
            p['impulse_std'] = real(p['impulse_std'], 'Desviación durante un impulso', minimum=p['background_std'])
            p['impulse_probability'] = real(p['impulse_probability'], 'Probabilidad de impulso', minimum=0, maximum=1)
        elif self.family == 'fir_noise':
            taps = p['taps'] = _vector(p['taps'], 'Coeficientes FIR', complex_allowed=True)
            if not p['complex'] and any(x.imag for x in taps):
                raise ValueError('Los coeficientes complejos requieren una salida compleja.')
        object.__setattr__(self, 'parameters', MappingProxyType(p))

    def document(self):
        p = dict(self.parameters)
        if self.family == 'fir_noise':
            p['taps'] = {'real': [x.real for x in p['taps']], 'imag': [x.imag for x in p['taps']]}
        elif self.family == 'specified_noise':
            p.update(frequency_hz=list(p['frequency_hz']), density=list(p['density']))
        return {'schema': 1, 'noise': self.family, 'parameters': p}


def _rate(model, value, required):
    if not isinstance(model, Noise):
        raise ValueError('Seleccioná el modelo de ruido.')
    if value is None and not (required or model.family in FREQUENCY_NOISES):
        return None
    rate = real(value, 'Frecuencia de muestreo (Hz)', positive=True)
    if model.family == 'colored_noise' and model.parameters['high_hz'] > rate / 2:
        raise ValueError('El corte superior excede Nyquist.')
    if model.family == 'specified_noise' and max(map(abs, model.parameters['frequency_hz'])) > rate / 2:
        raise ValueError('Las frecuencias de la PSD deben estar entre −Fs/2 y Fs/2.')
    return rate


def _grid(count, rate):
    spacing = real(rate / count, 'Espaciado en frecuencia', positive=True)
    frequency = (np.arange(count, dtype=float)-count//2)*spacing
    return frequency, spacing


def _colored_weights(p, frequency):
    f = abs(frequency)
    active = (p['low_hz'] <= f) & (f <= p['high_hz']) & (f > 0)
    w = np.zeros(len(f))
    if np.any(active):
        order = COLORS[p['color']]
        log_f = np.log(f[active])
        extreme = min(log_f) if order < 0 else max(log_f)
        w[active] = np.exp(order * (log_f - extreme))
    return w


def _power_response(model, count, frequency, rate):
    """Return PSD on a centered grid and the variance of one interior sample."""
    family, p = model.family, model.parameters
    spacing = rate / count
    if family == 'colored_noise':
        weights = _colored_weights(p, frequency)
        total = float(np.sum(weights))
        var = p['variance']
        if total == 0 and var:
            raise ValueError('La banda no contiene bins con densidad positiva. Ampliá la banda o usá más muestras.')
        fraction, exponent = math.frexp(spacing)
        density = restore_scale(weights/total, -exponent, var, 1/fraction).real if total else weights
    elif family == 'specified_noise':
        points = frequency if p['complex'] else abs(frequency)
        density = np.interp(points, p['frequency_hz'], p['density'], left=0, right=0)
        peak = float(np.max(density))
        if not peak and max(p['density']):
            raise ValueError('La grilla no contiene bins de PSD positiva. Usá más muestras o revisá la banda.')
        var = restore_scalar(float(np.mean(density/peak)), 0, peak, rate) if peak else 0.
    elif family == 'fir_noise':
        taps, power = bounded(np.asarray(p['taps']), normalize=True)
        grid = np.zeros(count, dtype=complex)
        np.add.at(grid, np.arange(len(taps)) % count, taps)
        gain = abs(np.fft.fftshift(np.fft.fft(grid)))**2
        fraction, exponent = math.frexp(rate)
        density = restore_scale(gain, 2*power-exponent, p['variance'], 1/fraction).real
        var = restore_scalar(float(np.sum(abs(taps)**2)), 2*power, p['variance'])
    else:
        var = _white_variance(model)
        density = np.full(count, var / rate)
    if not math.isfinite(var) or not np.all(np.isfinite(density)):
        raise ValueError('La potencia o la PSD resultante excede el rango de float64.')
    return density, var


def _white_variance(model):
    p = model.parameters
    if model.family == 'white_noise':
        return p['variance']
    probability = p['impulse_probability']
    rms = math.hypot(p['background_std'] * math.sqrt(1-probability), p['impulse_std'] * math.sqrt(probability))
    return real(rms*rms, 'Varianza de la mezcla', minimum=0)


def noise_spectrum(model, count, *, rate, execution=None):
    """Return a reusable theoretical density in amplitude squared per Hz."""
    rate = _rate(model, rate, True)
    count = integer(count, 'Cantidad de bins', maximum=_MAX_INDEX)
    context = execution or ExecutionContext()
    taps = len(model.parameters['taps']) if model.family == 'fir_noise' else 0
    with context.reserve(192*count + 96*taps):
        f, spacing = _grid(count, rate)
        density, variance = _power_response(model, count, f, rate)
        context.checkpoint()
        return Signal(density, f[0], spacing, 'Hz', 'PSD teórica · ' + NOISES[model.family][0], 'frequency',
                      metadata={'operation': 'spectral_density', 'schema': 1, 'model': model.document(),
                                'density_convention': 'per_coordinate', 'sidedness': 'two-sided',
                                'sample_rate_hz': rate, 'variance': variance,
                                'periodic_grid': True, 'nfft': count})


def _normal(rng, count, complex_output):
    if complex_output:
        parts = rng.standard_normal((count, 2))
        return (parts[:,0] + 1j*parts[:,1]) / math.sqrt(2)
    return rng.standard_normal(count)


def _noise_values(model, count, rng, context, scale, taps):
    family, p = model.family, model.parameters
    dtype = complex if p['complex'] else float
    if family == 'fir_noise':
        length = count + len(taps) - 1
    else:
        length = count
    values = np.empty(length, dtype=dtype)
    for offset in range(0, length, _BLOCK):
        context.checkpoint()
        end = min(length, offset+_BLOCK)
        draws = _normal(rng, end - offset, p['complex'])
        if family == 'impulsive_noise':
            spreads = np.where(rng.random(len(draws)) < p['impulse_probability'], p['impulse_std'], p['background_std'])
            draws *= spreads
        values[offset:end] = draws
    if family == 'fir_noise':
        return oaconvolve(values, taps, mode='valid')
    if family in FREQUENCY_NOISES:
        spectrum = np.fft.fft(values) * scale
        context.checkpoint()
        colored = np.fft.ifft(spectrum)
        return colored if p['complex'] else colored.real
    if family == 'white_noise':
        values *= scale
    return values


def generate_noise(model, count, seed, *, replicas=1, origin=0, rate=None, execution=None):
    """Produce independent finite records and preserve the target law or spectrum."""
    rate = _rate(model, rate, False)
    count = integer(count, 'Muestras', maximum=_MAX_INDEX)
    replicas = integer(replicas, 'Réplicas', maximum=_MAX_INDEX)
    seed = integer(seed, 'Semilla', minimum=0, maximum=MAX_SEED)
    origin = integer(origin, 'Índice inicial', minimum=-_MAX_INDEX-1, maximum=_MAX_INDEX-count+1)
    if rate is not None:
        validate_clock_resolution(0., rate, count)
    context = execution or ExecutionContext()
    p, family = model.parameters, model.family
    taps_count = len(p['taps']) if family == 'fir_noise' else 0
    estimate = 16*count*replicas + 240*(count + taps_count) + 2048*replicas
    output = []
    with context.reserve(estimate):
        document = model.document()
        metadata = {'operation': 'stochastic_noise', 'schema': 1, 'model': document,
                    'settings_sha256': settings_digest(document), 'seed': seed, 'generator': 'PCG64',
                    'numpy_version': np.__version__, 'draw_block_size': _BLOCK}
        if rate is not None:
            metadata.update(sample_rate_hz=rate, time_start_s=0., time_mapping=CLOCK_MAPPING)
        taps, scale = None, None
        if family in FREQUENCY_NOISES:
            f, _ = _grid(count, rate)
            density, variance = _power_response(model, count, f, rate)
            scale = math.sqrt(rate)*np.sqrt(np.fft.ifftshift(density))
            metadata['periodic_covariance'] = True
        elif family == 'fir_noise':
            raw = np.asarray(p['taps'], dtype=complex)
            raw = raw if p['complex'] else raw.real
            normalized, power = bounded(raw, normalize=True)
            variance = real(restore_scalar(float(np.sum(abs(normalized)**2)), 2*power, p['variance']),
                            'Varianza después del FIR', minimum=0)
            taps = restore_scale(normalized, power, math.sqrt(p['variance']))
            if not p['complex']:
                taps = taps.real
            metadata['initialization'] = 'independent white-noise prehistory'
        else:
            variance = _white_variance(model)
            scale = math.sqrt(variance)
        metadata['theoretical_variance'] = variance
        for index in range(replicas):
            context.checkpoint()
            rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(seed, spawn_key=(index,))))
            values = _noise_values(model, count, rng, context, scale, taps)
            record = Signal(values, origin=origin, name=f'{NOISES[family][0]} · realización {index+1}',
                            metadata={**metadata, 'substream': [index]})
            record._realization_digest = content_digest(record, context.checkpoint)
            output.append(record)
        context.checkpoint()
    return tuple(output)


def store_noise(project, document, records, execution=None, *, tool=None):
    return store_batch(project, document, records, execution, title='Modelo de ruido',
                       operation='Modelo de ruido estocástico', tool=tool)
