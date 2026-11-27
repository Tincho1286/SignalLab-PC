"""Aligned BER, SER and EVM, and coherent AWGN probability references."""

from dataclasses import dataclass
import math
import sys

import numpy as np
from scipy.special import betaincinv

from .communications_data import ConstellationSpec, SymbolSequence, integer, real
from .execution import ExecutionContext
from .model import Signal
from .operation_provenance import content_digest, verify_inputs


_BLOCK = 65_536
_LOG_DB = math.log(10) / 10
_LOG_TWO = math.log(2)


@dataclass(frozen=True, slots=True)
class QualitySpec:
    transmitted_start: int = 0
    received_start: int = 0
    symbol_count: int | None = None
    independent_bits: bool = False
    independent_symbols: bool = False
    confidence: float = 0.95

    def __post_init__(self):
        for field in ('transmitted_start', 'received_start'):
            object.__setattr__(self, field, integer(
                getattr(self, field), 'El inicio de la alineación', minimum=0, maximum=sys.maxsize,
            ))
        if self.symbol_count is not None:
            object.__setattr__(self, 'symbol_count', integer(
                self.symbol_count, 'La cantidad de símbolos', maximum=sys.maxsize,
            ))
        if type(self.independent_bits) is not bool or type(self.independent_symbols) is not bool:
            raise ValueError('Indicá explícitamente cuáles observaciones son independientes.')
        confidence = real(self.confidence, 'El nivel de confianza', positive=True)
        if confidence >= 1:
            raise ValueError('El nivel de confianza debe estar entre cero y uno.')
        object.__setattr__(self, 'confidence', confidence)


@dataclass(frozen=True, slots=True)
class ConfidenceBounds:
    level: float
    method: str
    lower: float
    upper: float


@dataclass(frozen=True, slots=True)
class ErrorRate:
    errors: int
    evaluated: int
    value: float
    evidence: str
    confidence: ConfidenceBounds | None


def error_rate(errors, evaluated, *, independent=False, confidence=0.95) -> ErrorRate:
    evaluated = integer(evaluated, 'Los datos evaluados')
    errors = integer(errors, 'La cantidad de errores', minimum=0, maximum=evaluated)
    bounds = None
    if independent:
        coverage = real(confidence, 'El nivel de confianza', positive=True)
        if coverage >= 1:
            raise ValueError('El nivel de confianza debe estar entre cero y uno.')
        if errors == 0:
            bounds = ConfidenceBounds(coverage, 'exact_upper_bound', 0.,
                                      -math.expm1(math.log1p(-coverage)/evaluated))
        else:
            tail = (1-coverage)/2
            lower = float(betaincinv(errors, evaluated-errors+1, tail))
            upper = 1. if errors == evaluated else float(betaincinv(errors+1, evaluated-errors, 1-tail))
            bounds = ConfidenceBounds(coverage, 'clopper_pearson', lower, upper)
    evidence = 'zero_observed' if errors == 0 else 'few_errors' if errors < 30 else 'observed'
    return ErrorRate(errors, evaluated, errors/evaluated, evidence, bounds)


@dataclass(frozen=True, slots=True)
class EVM:
    status: str
    rms: float | None = None
    percent: float | None = None
    db: float | None = None
    reference_name: str | None = None
    amplitude_units: str | None = None


@dataclass(frozen=True, slots=True)
class QualityMetrics:
    ber: ErrorRate
    ser: ErrorRate
    evm: EVM
    specification: QualitySpec
    transmitted_excluded_symbols: int
    received_excluded_symbols: int
    excluded_padding_bits: int


def _aligned_range(transmitted, received, spec):
    n_tx, n_rx = transmitted.labels.size, received.labels.size
    start_tx, start_rx = spec.transmitted_start, spec.received_start
    available_tx, available_rx = n_tx - start_tx, n_rx - start_rx
    count = spec.symbol_count
    if count is None:
        if available_tx != available_rx:
            raise ValueError('Indicá cuántos símbolos querés comparar en los registros.')
        count = available_tx
    if min(available_tx, available_rx) < count or count < 1:
        raise ValueError('El intervalo de comparación excede las secuencias.')
    width = transmitted.bits_per_symbol
    useful_tx = min(count*width, transmitted.valid_bits - start_tx*width)
    useful_rx = min(count*width, received.valid_bits - start_rx*width)
    if useful_tx != useful_rx:
        raise ValueError('Las secuencias alineadas contienen distinta cantidad de bits útiles.')
    return count, useful_tx, count*width-useful_tx


def _validate_iq(signal, size):
    if not isinstance(signal, Signal) or signal.domain != 'discrete' or signal.data_kind != 'temporal':
        raise ValueError('La EVM requiere un registro I/Q discreto por cada secuencia.')
    if signal.metadata.get('samples_per_symbol', 1) != 1 or signal.values.ndim != 1 or signal.values.size != size:
        raise ValueError('La EVM requiere una observación I/Q por cada etiqueta de símbolo.')
    return signal.metadata.get('amplitude_units')


def _label_errors(transmitted, received, padding):
    differences = transmitted ^ received
    symbol_errors = differences != 0
    if padding:
        differences[-1] >>= padding
    return np.bitwise_count(differences), symbol_errors


def quality_error_trace(transmitted, received, metrics):
    """Sample the cumulative rates of an already validated measurement."""
    count = metrics.ser.evaluated
    width = transmitted.bits_per_symbol
    points = min(count, 4096)
    spec = metrics.specification
    ctx = ExecutionContext()
    ctx.checkpoint(0)
    with ctx.reserve(64 * min(count, _BLOCK) + 64 * points):
        counts = np.linspace(1, count, points, dtype=np.int64)
        ber, ser = np.empty(points), np.empty(points)
        bit_total = symbol_total = index = 0
        for start in range(0, count, _BLOCK):
            ctx.checkpoint(100 * start // count)
            stop = min(count, start + _BLOCK)
            tx = transmitted.labels[spec.transmitted_start + start:spec.transmitted_start + stop]
            rx = received.labels[spec.received_start + start:spec.received_start + stop]
            bits, symbols = _label_errors(tx, rx, metrics.excluded_padding_bits if stop == count else 0)
            bit_counts, symbol_counts = np.cumsum(bits), np.cumsum(symbols)
            end = int(counts.searchsorted(stop, side='right'))
            selected = counts[index:end]
            offsets = selected - start - 1
            ber[index:end] = (bit_total + bit_counts[offsets]) / np.minimum(selected * width, metrics.ber.evaluated)
            ser[index:end] = (symbol_total + symbol_counts[offsets]) / selected
            bit_total += int(bit_counts[-1])
            symbol_total += int(symbol_counts[-1])
            index = end
        ctx.checkpoint(100)
    return counts, ber, ser


def _log_squared_norm(values):
    scale = max(float(np.max(np.abs(values.real))), float(np.max(np.abs(values.imag))))
    if scale == 0:
        return -math.inf
    energy = float(np.sum((values.real/scale)**2 + (values.imag/scale)**2))
    return 2*math.log(scale) + math.log(energy)


def _evm_norms(reference, observed):
    if not np.isfinite(reference).all() or not np.isfinite(observed).all():
        raise ValueError('Las observaciones de EVM deben ser finitas.')
    with np.errstate(over='ignore', invalid='ignore'):
        errors = observed - reference
    scale = 0.0
    if not np.isfinite(errors).all():
        errors = observed*0.5 - reference*0.5
        scale = 2*_LOG_TWO
    return _log_squared_norm(reference), _log_squared_norm(errors) + scale


def _representable_positive(log_value):
    try:
        return math.exp(log_value) or None
    except OverflowError:
        return None


def _evm(reference, units, ref_energy, error_energy):
    if reference is None:
        return EVM('reference_unavailable')
    if ref_energy == -math.inf:
        return EVM('zero_reference', reference_name=reference.name, amplitude_units=units)
    if error_energy == -math.inf:
        return EVM('perfect', 0., 0., reference_name=reference.name, amplitude_units=units)
    log_evm = (error_energy-ref_energy)/2
    rms = _representable_positive(log_evm)
    percent = _representable_positive(log_evm + math.log(100))
    state = 'measured' if rms is not None and percent is not None else 'numerical_range'
    return EVM(state, rms, percent, 2*log_evm/_LOG_DB, reference.name, units)


def measure_quality(transmitted: SymbolSequence, received: SymbolSequence, *,
                    reference: Signal | None = None, observation: Signal | None = None,
                    spec: QualitySpec | None = None, execution: ExecutionContext | None = None) -> QualityMetrics:
    """Compare aligned labels and optionally measure calibrated complex errors."""
    if not isinstance(transmitted, SymbolSequence) or not isinstance(received, SymbolSequence):
        raise TypeError('BER y SER requieren etiquetas transmitidas y recibidas.')
    if transmitted.order != received.order:
        raise ValueError('Las secuencias deben usar el mismo orden de modulación.')
    spec = QualitySpec() if spec is None else spec
    if not isinstance(spec, QualitySpec):
        raise TypeError('Indicá una configuración de medición de calidad.')
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    count, useful, padding = _aligned_range(transmitted, received, spec)
    units = None
    if (reference is None) != (observation is None):
        raise ValueError('Para medir EVM indicá la referencia I/Q y el registro observado.')
    if reference is not None:
        reference_units = _validate_iq(reference, transmitted.labels.size)
        observation_units = _validate_iq(observation, received.labels.size)
        if reference_units is not None and observation_units is not None and reference_units != observation_units:
            raise ValueError('Igualá las unidades de las amplitudes I/Q antes de medir EVM.')
        units = reference_units or observation_units
    inputs = () if reference is None else (reference, observation)
    tx_start, rx_start = spec.transmitted_start, spec.received_start
    symbol_errors = bit_errors = 0
    ref_energy = error_energy = -math.inf
    with ctx.reserve(144*min(count, _BLOCK)):
        digests = tuple(content_digest(value, ctx.checkpoint) for value in inputs)
        for start in range(0, count, _BLOCK):
            ctx.checkpoint(100*start//count)
            stop = min(count, start + _BLOCK)
            tx_slice = slice(tx_start+start, tx_start+stop)
            rx_slice = slice(rx_start+start, rx_start+stop)
            bits, symbols = _label_errors(transmitted.labels[tx_slice], received.labels[rx_slice],
                                          padding if stop == count else 0)
            symbol_errors += int(np.count_nonzero(symbols))
            bit_errors += int(bits.sum())
            if reference is not None:
                re, ee = _evm_norms(reference.values[tx_slice], observation.values[rx_slice])
                ref_energy = float(np.logaddexp(ref_energy, re))
                error_energy = float(np.logaddexp(error_energy, ee))
        ber = error_rate(bit_errors, useful, independent=spec.independent_bits, confidence=spec.confidence)
        ser = error_rate(symbol_errors, count, independent=spec.independent_symbols, confidence=spec.confidence)
        evm = _evm(reference, units, ref_energy, error_energy)
        result = QualityMetrics(ber, ser, evm, spec, transmitted.labels.size-count, received.labels.size-count, padding)
        ctx.checkpoint(100)
        verify_inputs(inputs, digests, ctx.checkpoint)
    return result


@dataclass(frozen=True, slots=True)
class TheoreticalError:
    eb_n0_db: float
    ber: float | None
    ser: float | None
    ber_reference: str
    ser_reference: str


def _gaussian_tail(log_argument):
    # At arguments beyond 30, erfc is smaller than the least binary64 subnormal.
    return 0.0 if log_argument > math.log(30) else math.erfc(math.exp(log_argument))/2


def theoretical_error(spec: ConstellationSpec, eb_n0_db) -> TheoreticalError:
    """Probabilities for equiprobable symbols and coherent hard decisions in AWGN."""
    if not isinstance(spec, ConstellationSpec):
        raise TypeError('Indicá una configuración de constelación.')
    db = real(eb_n0_db, 'Eb/N0')
    log_ratio = db*_LOG_DB
    order, width = spec.order, spec.bits_per_symbol
    if spec.family == 'psk' and order <= 4:
        single = _gaussian_tail(log_ratio/2)
        ber = single if order == 2 or spec.labeling == 'gray' else single*(1.5-single)
        ser = single if order == 2 else single*(2-single)
        return TheoreticalError(db, ber, ser, 'exact', 'exact')
    if spec.family == 'qam':
        q = _gaussian_tail((log_ratio + math.log(1.5*width/(order-1)))/2)
        axis = 2*(1-1/math.isqrt(order))*q
        ser = axis*(2-axis)
        if order == 4:
            return TheoreticalError(db, q, ser, 'exact', 'exact')
        if spec.labeling == 'gray':
            return TheoreticalError(db, 2*axis/width, ser, 'gray_nearest_neighbors', 'exact')
        return TheoreticalError(db, None, ser, 'unavailable', 'exact')
    return TheoreticalError(db, None, None, 'unavailable', 'unavailable')
