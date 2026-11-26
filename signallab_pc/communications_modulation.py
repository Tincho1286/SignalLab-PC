"""Bit sources, geometry, mapping and hard decisions for digital communications."""

from dataclasses import asdict, dataclass
import math
import sys

import numpy as np

from .communications_data import (
    MAX_SEED, BitSequence, ConstellationSpec, SymbolClock, SymbolSequence,
    immutable_array, integer, iq_signal,
)
from .execution import ExecutionContext
from .model import Signal
from .operation_provenance import content_digest, verify_inputs


_BLOCK = 65_536
_BIT_WHITESPACE = str.maketrans('', '', ' \t\r\n')


def parse_bits(text: str, execution: ExecutionContext | None = None) -> BitSequence:
    if not isinstance(text, str):
        raise ValueError('Ingresá una secuencia de 0 y 1.')
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    with ctx.reserve(10 * len(text)):
        try:
            words = text.translate(_BIT_WHITESPACE).encode('ascii')
        except UnicodeEncodeError as exc:
            raise ValueError('La secuencia binaria admite 0, 1 y espacios.') from exc
        result = BitSequence(np.frombuffer(words, dtype=np.uint8) - ord('0'))
        ctx.checkpoint(100)
    return result


def generate_bits(count: int, seed: int, execution: ExecutionContext | None = None) -> BitSequence:
    count = integer(count, 'La cantidad de bits', maximum=sys.maxsize)
    seed = integer(seed, 'La semilla', minimum=0, maximum=MAX_SEED)
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    with ctx.reserve(2 * count + min(count, _BLOCK)):
        rng = np.random.Generator(np.random.PCG64(seed))
        values = np.empty(count, dtype=np.uint8)
        for start in range(0, count, _BLOCK):
            ctx.checkpoint(100 * start // count)
            stop = min(count, start + _BLOCK)
            values[start:stop] = rng.integers(0, 2, stop - start, dtype=np.uint8)
        result = BitSequence(values, seed)
        ctx.checkpoint(100)
    return result


def group_bits(bits: BitSequence, spec: ConstellationSpec, *, pad=False,
               clock: SymbolClock | None = None, execution: ExecutionContext | None = None) -> SymbolSequence:
    if not isinstance(bits, BitSequence) or not isinstance(spec, ConstellationSpec):
        raise TypeError('El agrupamiento requiere bits y una configuración de constelación.')
    if type(pad) is not bool:
        raise ValueError('Indicá explícitamente si se permite completar el último símbolo.')
    width, count = spec.bits_per_symbol, bits.values.size
    complete, remainder = divmod(count, width)
    if remainder and not pad:
        raise ValueError(f'La cantidad de bits debe ser múltiplo de {width}. Podés completar con ceros.')
    length = complete + bool(remainder)
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    with ctx.reserve(8 * length + 8 * width * min(length, _BLOCK)):
        labels = np.empty(length, dtype=np.uint32)
        shifts = np.arange(width, dtype=np.uint32)[::-1]
        weights = np.left_shift(np.uint32(1), shifts)
        for start in range(0, length, _BLOCK):
            ctx.checkpoint(100 * start // length)
            stop = min(length, start + _BLOCK)
            words = bits.values[width * start:width * stop]
            if words.size < (stop - start) * width:
                words = np.pad(words, (0, width - remainder))
            labels[start:stop] = words.reshape(-1, width) @ weights
        result = SymbolSequence(labels, spec.order, count, clock)
        ctx.checkpoint(100)
    return result


def ungroup_symbols(symbols: SymbolSequence, execution: ExecutionContext | None = None) -> BitSequence:
    if not isinstance(symbols, SymbolSequence):
        raise TypeError('La conversión a bits requiere etiquetas de símbolos.')
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    count, width = symbols.valid_bits, symbols.bits_per_symbol
    length = symbols.labels.size
    with ctx.reserve(2 * count + 12 * width * min(length, _BLOCK)):
        values = np.empty(count, dtype=np.uint8)
        shifts = np.arange(width, dtype=np.uint32)[::-1]
        for start in range(0, length, _BLOCK):
            ctx.checkpoint(100 * start // length)
            stop = min(length, start + _BLOCK)
            upper = min(stop * width, count)
            words = ((symbols.labels[start:stop, None] >> shifts) & 1).reshape(-1)
            values[start * width:upper] = words[:upper - start * width]
        result = BitSequence(values)
        ctx.checkpoint(100)
    return result


def _gray_decode(labels, width):
    decoded = labels.copy()
    shift = 1
    while shift < width:
        decoded ^= decoded >> shift
        shift *= 2
    return decoded


def _label_transform(indices, spec, *, inverse):
    if spec.labeling == 'natural':
        return indices
    width = spec.bits_per_symbol
    if spec.family == 'qam':
        width //= 2
        first, second = indices >> width, indices & ((1 << width) - 1)
        if inverse:
            return (_gray_decode(first, width) << width) | _gray_decode(second, width)
        return ((first ^ (first >> 1)) << width) | (second ^ (second >> 1))
    if inverse:
        return _gray_decode(indices, width)
    return indices ^ (indices >> 1)


def _geometry(spec):
    if spec.family == 'psk':
        return 1.0, 2 * math.sin(math.pi / spec.order), 1.0
    energy = 2 * (spec.order - 1) / 3
    gain = 1 / math.sqrt(energy) if spec.normalization == 'unit_energy' else 1.0
    return (1.0 if spec.normalization == 'unit_energy' else energy), 2 * gain, gain


def _coordinates(positions, spec, gain):
    if spec.family == 'psk':
        return np.exp(1j * (spec.rotation_rad + math.tau / spec.order * positions.astype(np.float64)))
    side = math.isqrt(spec.order)
    i = 2 * (positions // side).astype(np.float64) - (side - 1)
    q = 2 * (positions % side).astype(np.float64) - (side - 1)
    return (i + 1j * q) * (gain * np.exp(1j * spec.rotation_rad))


@dataclass(frozen=True, slots=True, eq=False)
class Constellation:
    specification: ConstellationSpec
    points: np.ndarray
    labels: np.ndarray
    mean_symbol_energy: float
    minimum_distance: float


def build_constellation(spec: ConstellationSpec, execution: ExecutionContext | None = None) -> Constellation:
    if not isinstance(spec, ConstellationSpec):
        raise TypeError('Indicá una configuración de constelación.')
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    order = spec.order
    energy, distance, gain = _geometry(spec)
    with ctx.reserve(40 * order + 120 * min(order, _BLOCK)):
        points, labels = np.empty(order, dtype=np.complex128), np.empty(order, dtype=np.uint32)
        for start in range(0, order, _BLOCK):
            ctx.checkpoint(100 * start // order)
            stop = min(order, start + _BLOCK)
            positions = np.arange(start, stop, dtype=np.uint64).astype(np.uint32)
            points[start:stop] = _coordinates(positions, spec, gain)
            labels[start:stop] = _label_transform(positions, spec, inverse=False)
        result = Constellation(spec, immutable_array(points, np.complex128),
                               immutable_array(labels, np.uint32), energy, distance)
        ctx.checkpoint(100)
    return result


def modulate(symbols: SymbolSequence, spec: ConstellationSpec,
             execution: ExecutionContext | None = None) -> Signal:
    if not isinstance(symbols, SymbolSequence) or not isinstance(spec, ConstellationSpec):
        raise TypeError('La modulación requiere etiquetas y una configuración de constelación.')
    if symbols.order != spec.order:
        raise ValueError('Las etiquetas y la constelación deben usar el mismo orden.')
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    count = symbols.labels.size
    energy, _, gain = _geometry(spec)
    with ctx.reserve(48 * count + 96 * min(count, _BLOCK)):
        points = np.empty(count, dtype=np.complex128)
        for start in range(0, count, _BLOCK):
            ctx.checkpoint(100 * start // count)
            stop = min(count, start + _BLOCK)
            positions = _label_transform(symbols.labels[start:stop], spec, inverse=True)
            points[start:stop] = _coordinates(positions, spec, gain)
        metadata = {
            'amplitude_units': '1', 'communications_representation': 'complex_baseband',
            'communications': {
                'schema': 1, 'operation': 'modulate', 'constellation': asdict(spec),
                'mean_symbol_energy': energy, 'bits_per_symbol': spec.bits_per_symbol,
                'valid_bits': symbols.valid_bits, 'padding_bits': symbols.padding_bits,
            },
        }
        if symbols.clock is None:
            result = Signal(points, name='Símbolos I/Q', metadata=metadata)
        else:
            result = iq_signal(points, symbols.clock, name='Símbolos I/Q', metadata=metadata)
        ctx.checkpoint(100)
    return result


def _nearest_positions(values, spec, gain):
    if spec.family == 'psk':
        sector = np.remainder(np.angle(values) - spec.rotation_rad, math.tau) * (spec.order / math.tau)
        position = np.floor(sector + 0.5).astype(np.uint64) % spec.order
        position[values == 0] = 0
        return position.astype(np.uint32)
    side = math.isqrt(spec.order)
    largest_component = np.maximum(np.abs(values.real), np.abs(values.imag))
    # Exact scaling by two avoids overflow in the rotation of extreme inputs.
    scale = np.where(largest_component > np.finfo(np.float64).max / 2, 2.0, 1.0)
    aligned = (values / scale) * np.exp(-1j * spec.rotation_rad)
    bound = (side - 1) * gain / scale
    i = np.floor((np.clip(aligned.real, -bound, bound) * scale / gain + side) / 2).astype(np.uint32)
    q = np.floor((np.clip(aligned.imag, -bound, bound) * scale / gain + side) / 2).astype(np.uint32)
    return i * side + q


def decide_symbols(signal: Signal, spec: ConstellationSpec, *, valid_bits=None,
                   execution: ExecutionContext | None = None) -> SymbolSequence:
    """Decide aligned samples, breaking PSK ties forward and QAM ties upward."""
    if not isinstance(signal, Signal) or not isinstance(spec, ConstellationSpec):
        raise TypeError('La decisión requiere una señal I/Q y una configuración de constelación.')
    if signal.domain != 'discrete' or signal.data_kind != 'temporal':
        raise ValueError('La decisión requiere muestras temporales discretas.')
    sps = integer(signal.metadata.get('samples_per_symbol', 1), 'Las muestras por símbolo')
    if sps != 1:
        raise ValueError('Seleccioná una muestra por símbolo antes de decidir.')
    values = signal.values
    if not isinstance(values, np.ndarray) or values.ndim != 1 or not values.size or values.dtype != np.complex128:
        raise ValueError('La decisión requiere un vector de observaciones complejas.')
    count = values.size
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    _, _, gain = _geometry(spec)
    with ctx.reserve(8 * count + 128 * min(count, _BLOCK)):
        digest = content_digest(signal, ctx.checkpoint)
        labels = np.empty(count, dtype=np.uint32)
        for start in range(0, count, _BLOCK):
            ctx.checkpoint(100 * start // count)
            stop = min(count, start + _BLOCK)
            block = values[start:stop]
            if not np.isfinite(block).all():
                raise ValueError('La decisión requiere observaciones finitas.')
            positions = _nearest_positions(block, spec, gain)
            labels[start:stop] = _label_transform(positions, spec, inverse=False)
        rate = signal.metadata.get('symbol_rate_hz', signal.metadata.get('sample_rate_hz'))
        clock = None if rate is None else SymbolClock(
            rate, time_start_s=signal.metadata.get('time_start_s'),
            center_frequency_hz=signal.metadata.get('center_frequency_hz'),
        )
        if clock is not None and signal.metadata.get('sample_rate_hz', rate) != clock.sample_rate_hz:
            raise ValueError('La tasa de muestras no coincide con la tasa de símbolos.')
        source = signal.metadata.get('communications')
        if valid_bits is None and isinstance(source, dict):
            useful = source.get('valid_bits')
            width = spec.bits_per_symbol
            if source.get('bits_per_symbol') == width and type(useful) is int and (count-1)*width < useful <= count*width:
                valid_bits = useful
        result = SymbolSequence(labels, spec.order, valid_bits, clock)
        ctx.checkpoint(100)
        verify_inputs((signal,), (digest,), ctx.checkpoint)
    return result
