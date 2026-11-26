"""Deterministic frequency shift and finite-record Clarke fading diagnostics."""

from copy import deepcopy
from dataclasses import asdict, dataclass
import math

import numpy as np
from scipy.fft import next_fast_len
from scipy.optimize import brentq
from scipy.signal import ZoomFFT, correlate, welch
from scipy.special import j0

from .communications_channel import channel_clock, discrete_channel_size
from .communications_data import integer, real
from .execution import ExecutionContext
from .model import Signal
from .operation_provenance import content_digest, verify_inputs


_BLOCK = 65_536
_MIN_CLARKE_BINS = 64


def _sample_rate(signal):
    return real(signal.metadata.get('sample_rate_hz'), 'La frecuencia de muestreo Fs en Hz', positive=True)


def _nyquist_ratio(frequency, rate):
    ratio = frequency / rate
    if abs(ratio) >= 0.5 or (frequency != 0 and ratio == 0):
        raise ValueError('La frecuencia debe ser representable y estar entre −Fs/2 y Fs/2 (excluidos).')
    return ratio


def normalized_carrier(frequency, sample_rate):
    if not frequency:
        return 0.0
    rate = real(sample_rate, 'La frecuencia de muestreo Fs en Hz', positive=True)
    return _nyquist_ratio(frequency, rate)


def carrier_rotation(offsets, ratio, phase_rad=0.0):
    """Complex unit rotation for a sample-frequency ratio and a phase reference."""
    turns = np.remainder(ratio * offsets, 1)
    return np.exp(1j * (math.tau * turns + math.remainder(phase_rad, math.tau)))


@dataclass(frozen=True, slots=True)
class CarrierShift:
    """Frequency in Hz and initial phase in radians at the first input sample."""

    frequency_hz: float = 0.0
    phase_rad: float = 0.0

    def __post_init__(self):
        object.__setattr__(self, 'frequency_hz', real(self.frequency_hz, 'El desplazamiento de frecuencia en Hz'))
        object.__setattr__(self, 'phase_rad', real(self.phase_rad, 'La fase inicial en radianes'))


def apply_carrier_shift(signal: Signal, spec: CarrierShift,
                        execution: ExecutionContext | None = None) -> Signal:
    """Apply a unit-magnitude rotation without changing support, clock or units."""
    if not isinstance(spec, CarrierShift):
        raise ValueError('Indicá una configuración de frecuencia y fase.')
    ctx = execution or ExecutionContext()
    size = discrete_channel_size(signal, 0)
    ratio = normalized_carrier(spec.frequency_hz, signal.metadata.get('sample_rate_hz'))
    with ctx.reserve(40 * size + 72 * min(_BLOCK, size)):
        clock = channel_clock(signal, 0, size)
        digest = content_digest(signal, ctx.checkpoint)
        values = np.empty(size, dtype=np.complex128)
        for start in range(0, size, _BLOCK):
            ctx.checkpoint(90 * start // size)
            stop = min(start + _BLOCK, size)
            values[start:stop] = signal.values[start:stop] * carrier_rotation(np.arange(start, stop), ratio, spec.phase_rad)
        metadata = deepcopy(signal.metadata)
        metadata.pop('core_provenance', None)
        metadata.update(clock)
        metadata.update(operation='communications_carrier_shift', communications_carrier_shift={
            'schema': 1, 'specification': asdict(spec), 'source_sha256': digest,
        })
        result = signal.copy_with(values=values, metadata=metadata, expression='', name='Salida con cambio de frecuencia y fase')
        result._core_verification = (content_digest(result, ctx.checkpoint), (digest,), None)
        verify_inputs((signal,), (digest,), ctx.checkpoint)
        ctx.checkpoint(100)
    return result


def _cdf(fraction):
    return 0.5 + np.arcsin(np.clip(fraction, -1, 1)) / math.pi


@dataclass(frozen=True, slots=True)
class ClarkeGrid:
    """Uniform spectral quadrature for one finite record and common clock."""

    ratio: float
    size: int
    bins: int
    work_bytes: int
    coherence_seconds: float | None

    @classmethod
    def for_signal(cls, signal, max_doppler_hz):
        size = signal.values.size
        if max_doppler_hz == 0:
            return cls(0.0, size, _MIN_CLARKE_BINS, 16 * size + 64 * _MIN_CLARKE_BINS, None)
        ratio = _nyquist_ratio(max_doppler_hz, _sample_rate(signal))
        bins = max(_MIN_CLARKE_BINS, math.ceil(8 * ratio * size))
        scratch = 192 * next_fast_len(bins + size - 1) + 64 * (bins + size)
        return cls(ratio, size, bins, scratch, clarke_coherence_seconds(max_doppler_hz))

    def prepare(self, ctx):
        """Precompute one transform for all independent paths."""
        ctx.checkpoint()
        weights = np.sqrt(np.diff(_cdf(np.linspace(-1, 1, self.bins + 1))))
        if self.ratio == 0:
            return weights, None, None
        spacing = 2 * self.ratio / self.bins
        transform = ZoomFFT(self.bins, [0, spacing * self.size], self.size, fs=1)
        rotator = np.exp(1j * math.tau * (-self.ratio + spacing/2) * np.arange(self.size))
        ctx.checkpoint()
        return weights, transform, rotator

    def draw(self, rng, prepared, ctx):
        normal = rng.standard_normal((self.bins, 2))
        coefficients = normal[:, 0] + 1j * normal[:, 1]
        weights, transform, rotator = prepared
        if transform is None:
            return np.full(self.size, np.dot(coefficients, weights), dtype=np.complex128)
        ctx.checkpoint()
        process = np.conj(transform(np.conj(coefficients * weights))) * rotator
        ctx.checkpoint()
        return process


def clarke_coherence_seconds(max_doppler_hz: float) -> float | None:
    """First crossing of J0 at 0.5. None denotes an infinite coherence time."""
    max_doppler = real(max_doppler_hz, 'El Doppler máximo en Hz', minimum=0)
    if max_doppler == 0:
        return None
    seconds = (brentq(lambda x: j0(x) - 0.5, 0, 2) / math.tau) / max_doppler
    if not math.isfinite(seconds):
        raise ValueError('El tiempo de coherencia supera el rango numérico.')
    return seconds


@dataclass(frozen=True, slots=True, eq=False)
class DopplerDiagnostics:
    lags_samples: np.ndarray
    sample_rate_hz: float
    observed_correlation: np.ndarray
    theoretical_correlation: np.ndarray
    frequencies_hz: np.ndarray
    observed_psd: np.ndarray
    theoretical_psd: np.ndarray
    coherence_seconds: float | None

    def signals(self):
        """Expose sampled results in the native signal format."""
        lag_clock = {'sample_rate_hz': self.sample_rate_hz, 'time_start_s': 0.0, 'amplitude_units': '1'}
        records = {
            'observed_covariance': Signal(self.observed_correlation, name='Autocorrelación observada',
                                           metadata=lag_clock.copy()),
            'theoretical_covariance': Signal(self.theoretical_correlation, name='Autocorrelación Clarke',
                                              metadata=lag_clock.copy()),
        }
        step = self.sample_rate_hz / len(self.frequencies_hz)
        for key, values, name in (
            ('observed_psd', self.observed_psd, 'PSD Doppler observada'),
            ('theoretical_psd', self.theoretical_psd, 'PSD Doppler Clarke'),
        ):
            records[key] = Signal(values, float(self.frequencies_hz[0]), step, 'Hz', name, 'frequency',
                                  metadata={'operation': 'spectral_density', 'density_units': '1/Hz'})
        return records


def _clarke_psd(frequencies, doppler_ratio):
    width = 1 / len(frequencies)
    if doppler_ratio == 0:
        mass = (frequencies == 0).astype(float)
    else:
        edges = np.append(frequencies - width/2, frequencies[-1] + width/2)
        with np.errstate(over='ignore'):
            cumulative = _cdf(edges / doppler_ratio)
        mass = np.diff(cumulative)
        # The negative Nyquist cell also covers the last half bin above the positive edge.
        mass[0] += 1 - cumulative[-1]
    return mass / width


def analyze_clarke(coefficients: Signal, max_doppler_hz: float, *, mean=0j, max_lag=512, segment=2048,
                   execution: ExecutionContext | None = None) -> DopplerDiagnostics:
    """Compare normalized diffuse covariance and density against continuous Clarke."""
    size = discrete_channel_size(coefficients, 0)
    if size < 2:
        raise ValueError('El análisis Doppler requiere dos o más coeficientes.')
    rate = _sample_rate(coefficients)
    fd = real(max_doppler_hz, 'El Doppler máximo en Hz', minimum=0)
    ratio = _nyquist_ratio(fd, rate)
    max_lag = min(integer(max_lag, 'El mayor retardo de correlación', minimum=0), size - 1)
    segment = min(integer(segment, 'El segmento Welch', minimum=2), size)
    mean = complex(mean)
    if not math.isfinite(mean.real) or not math.isfinite(mean.imag):
        raise ValueError('La media de los coeficientes debe ser finita.')
    ctx = execution or ExecutionContext()
    with ctx.reserve(120 * next_fast_len(2 * size - 1) + 72 * segment):
        ctx.checkpoint()
        values = coefficients.values - mean
        scale = max(float(np.max(abs(values.real))), float(np.max(abs(values.imag))))
        if not math.isfinite(scale) or scale == 0:
            raise ValueError('Los coeficientes no tienen una componente difusa finita y medible.')
        values /= scale
        lags = np.arange(max_lag + 1)
        raw = correlate(values, values, mode='full', method='fft')[size - 1:size + max_lag] / (size - lags)
        observed = raw / raw[0].real
        observed[0] = 1.0
        theoretical = j0(math.tau * ratio * lags)
        ctx.checkpoint()
        # Compute in cycles/sample and convert the normalized density to 1/Hz.
        # This keeps the window-energy normalization independent of the clock.
        freq, psd = welch(values, fs=1, nperseg=segment, detrend=False, return_onesided=False)
        freq, psd = np.fft.fftshift(freq), np.fft.fftshift(psd)
        with np.errstate(over='ignore', under='ignore'):
            observed_psd = (psd / raw[0].real) / rate
            theoretical_psd = _clarke_psd(freq, ratio) / rate
        freq *= rate
        if not np.all(np.isfinite(observed_psd)) or not np.all(np.isfinite(theoretical_psd)):
            raise ValueError('La densidad Doppler excede el rango numérico.')
        coherence = clarke_coherence_seconds(fd)
        ctx.checkpoint()
    return DopplerDiagnostics(lags, rate, observed, theoretical, freq, observed_psd, theoretical_psd, coherence)
