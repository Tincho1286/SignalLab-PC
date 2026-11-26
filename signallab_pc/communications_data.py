"""Scientific data contracts for digital communications, independent of Qt."""

from dataclasses import dataclass
import math
from numbers import Complex
from operator import index
import sys

import numpy as np

from .model import Signal
from .resources import ensure_working_set
from .system_clock import CLOCK_MAPPING, validate_clock_resolution


def integer(value, label, *, minimum=1, maximum=None):
    try:
        if isinstance(value, (bool, np.bool_)):
            raise TypeError
        value = index(value)
    except TypeError as exc:
        raise ValueError(f'{label} debe ser un entero.') from exc
    if value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f'{label} está fuera del rango admitido.')
    return value


def real(value, label, *, minimum=None, maximum=None, positive=False):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, float, np.integer, np.floating)):
        raise ValueError(f'{label} debe ser real y finito.')
    try:
        value = float(value)
    except OverflowError as exc:
        raise ValueError(f'{label} debe ser real y finito.') from exc
    if not math.isfinite(value):
        raise ValueError(f'{label} debe ser real y finito.')
    if (positive and value <= 0) or (minimum is not None and value < minimum) or (
        maximum is not None and value > maximum
    ):
        raise ValueError(f'{label} está fuera del rango admitido.')
    return value


_MAX_ORDER = 1 << 32
MAX_SEED = (1 << 128) - 1


def _binary_order(order):
    order = integer(order, 'El orden de modulación', minimum=2, maximum=_MAX_ORDER)
    if order & (order - 1):
        raise ValueError('El orden de modulación debe ser una potencia de dos.')
    return order


def immutable_array(values, dtype):
    """Snapshot an array on a buffer that callers cannot make writeable."""
    return np.frombuffer(np.asarray(values, dtype=dtype).tobytes(), dtype=dtype)


def _integer_vector(values, *, maximum, dtype, label, allow_bool=False):
    if not isinstance(values, (np.ndarray, list, tuple)):
        raise ValueError(f'{label} requiere un vector unidimensional.')
    if isinstance(values, np.ndarray) and values.ndim != 1:
        raise ValueError(f'{label} requiere un vector unidimensional.')
    if not len(values):
        raise ValueError(f'{label} no puede quedar vacío.')
    ensure_working_set(len(values), bytes_per_sample=np.dtype(dtype).itemsize, live_arrays=2)
    if isinstance(values, np.ndarray):
        kinds = 'uib' if allow_bool else 'ui'
        if values.dtype.kind not in kinds or values.min() < 0 or int(values.max()) > maximum:
            raise ValueError(f'{label} admite enteros entre 0 y {maximum}.')
    else:
        for item in values:
            if allow_bool and isinstance(item, (bool, np.bool_)):
                continue
            integer(item, label, minimum=0, maximum=maximum)
    return immutable_array(values, dtype)


@dataclass(frozen=True, slots=True, eq=False)
class BitSequence:
    """Nonempty bits in transmission order, with an optional PCG64 seed."""

    values: np.ndarray
    seed: int | None = None

    def __post_init__(self):
        object.__setattr__(self, 'values', _integer_vector(
            self.values, maximum=1, dtype=np.uint8, label='La secuencia binaria', allow_bool=True,
        ))
        if self.seed is not None:
            object.__setattr__(self, 'seed', integer(
                self.seed, 'La semilla', minimum=0, maximum=MAX_SEED,
            ))


@dataclass(frozen=True, slots=True)
class SymbolClock:
    """Symbol and sample rates and the physical time at the first sample."""

    symbol_rate_hz: float
    samples_per_symbol: int = 1
    time_start_s: float | None = 0.0
    center_frequency_hz: float | None = None

    def __post_init__(self):
        rate = real(self.symbol_rate_hz, 'La tasa de símbolos', positive=True)
        sps = integer(self.samples_per_symbol, 'Las muestras por símbolo', maximum=sys.maxsize)
        start = None if self.time_start_s is None else real(self.time_start_s, 'El tiempo inicial')
        validate_clock_resolution(start or 0.0, rate * sps, 1)
        object.__setattr__(self, 'symbol_rate_hz', rate)
        object.__setattr__(self, 'samples_per_symbol', sps)
        object.__setattr__(self, 'time_start_s', start)
        if self.center_frequency_hz is not None:
            object.__setattr__(self, 'center_frequency_hz', real(
                self.center_frequency_hz, 'La frecuencia central',
            ))

    @property
    def sample_rate_hz(self):
        return self.symbol_rate_hz * self.samples_per_symbol

    def metadata(self, count):
        count = integer(count, 'La cantidad de muestras', maximum=sys.maxsize)
        validate_clock_resolution(self.time_start_s or 0.0, self.sample_rate_hz, count)
        fields = {
            'symbol_rate_hz': self.symbol_rate_hz,
            'samples_per_symbol': self.samples_per_symbol,
            'sample_rate_hz': self.sample_rate_hz,
        }
        if self.time_start_s is not None:
            fields.update(time_start_s=self.time_start_s, time_mapping=CLOCK_MAPPING)
        if self.center_frequency_hz is not None:
            fields['center_frequency_hz'] = self.center_frequency_hz
        return fields


def clock_from_signal(signal: Signal, expected_sps: int) -> SymbolClock | None:
    fields = signal.metadata
    recorded = integer(fields.get('samples_per_symbol', expected_sps), 'Las muestras por símbolo')
    if recorded != expected_sps:
        raise ValueError('Las muestras por símbolo registradas no coinciden con la operación.')
    sample_rate = fields.get('sample_rate_hz')
    if sample_rate is not None:
        sample_rate = real(sample_rate, 'Fs', positive=True)
    symbol_rate = fields.get('symbol_rate_hz')
    if symbol_rate is None:
        if sample_rate is None:
            return None
        symbol_rate = sample_rate / expected_sps
    clock = SymbolClock(symbol_rate, expected_sps, fields.get('time_start_s'), fields.get('center_frequency_hz'))
    if sample_rate is not None and not math.isclose(sample_rate, clock.sample_rate_hz, rel_tol=1e-12, abs_tol=0):
        raise ValueError('La tasa de muestras y la de símbolos son incompatibles.')
    return clock


@dataclass(frozen=True, slots=True, eq=False)
class SymbolSequence:
    """Integer labels (bit words), separated from their complex coordinates."""

    labels: np.ndarray
    order: int
    valid_bits: int | None = None
    clock: SymbolClock | None = None

    def __post_init__(self):
        order = _binary_order(self.order)
        labels = _integer_vector(
            self.labels, maximum=order - 1, dtype=np.uint32, label='Las etiquetas de símbolo',
        )
        width = order.bit_length() - 1
        capacity = labels.size * width
        valid = capacity if self.valid_bits is None else integer(
            self.valid_bits, 'Los bits útiles', minimum=capacity - width + 1, maximum=capacity,
        )
        if self.clock is not None:
            if not isinstance(self.clock, SymbolClock) or self.clock.samples_per_symbol != 1:
                raise ValueError('El reloj de las etiquetas requiere una muestra por símbolo.')
            self.clock.metadata(labels.size)
        object.__setattr__(self, 'labels', labels)
        object.__setattr__(self, 'order', order)
        object.__setattr__(self, 'valid_bits', valid)

    @property
    def bits_per_symbol(self):
        return self.order.bit_length() - 1

    @property
    def padding_bits(self):
        return self.labels.size * self.bits_per_symbol - self.valid_bits


@dataclass(frozen=True, slots=True)
class ConstellationSpec:
    family: str
    order: int
    labeling: str = 'gray'
    rotation_rad: float = 0.0
    normalization: str = 'unit_energy'

    def __post_init__(self):
        order = _binary_order(self.order)
        if self.family not in ('psk', 'qam'):
            raise ValueError('La familia debe ser PSK o QAM cuadrada.')
        if self.family == 'qam' and (order.bit_length() - 1) % 2:
            raise ValueError('QAM cuadrada requiere un orden M = 4^k.')
        if self.labeling not in ('gray', 'natural'):
            raise ValueError('El mapeo debe ser Gray o natural.')
        if self.normalization not in ('unit_energy', 'raw'):
            raise ValueError('Seleccioná energía media unitaria o escala geométrica.')
        phase = math.remainder(real(self.rotation_rad, 'La rotación'), math.tau)
        object.__setattr__(self, 'order', order)
        object.__setattr__(self, 'rotation_rad', -math.pi if phase == math.pi else phase or 0.0)

    @property
    def bits_per_symbol(self):
        return self.order.bit_length() - 1


def iq_signal(samples, clock: SymbolClock, *, origin=0, name='I/Q', amplitude_units='1', metadata=None):
    """Adapt a complex time record to the existing Signal and project routes."""
    if not isinstance(clock, SymbolClock):
        raise ValueError('La señal I/Q requiere un reloj de símbolos.')
    if not isinstance(amplitude_units, str) or not amplitude_units.strip():
        raise ValueError('Indicá la unidad de amplitud de la señal I/Q.')
    if isinstance(samples, np.ndarray):
        valid = samples.ndim == 1 and samples.dtype.kind in 'buifc'
    else:
        valid = isinstance(samples, (list, tuple)) and all(isinstance(value, Complex) for value in samples)
    if not valid:
        raise ValueError('La señal I/Q requiere un vector numérico de muestras.')
    count = len(samples)
    ensure_working_set(count, live_arrays=3)
    origin = integer(origin, 'El índice inicial', minimum=-(1 << 63), maximum=(1 << 63) - 1)
    fields = {
        **(metadata or {}), **clock.metadata(count),
        'amplitude_units': amplitude_units, 'communications_representation': 'complex_baseband',
    }
    return Signal(samples, origin=origin, name=name, metadata=fields)
