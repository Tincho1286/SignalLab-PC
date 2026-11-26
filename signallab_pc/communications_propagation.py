"""Large-scale gain, free-space loss, log-distance loss and log-normal shadowing."""

from copy import deepcopy
from dataclasses import asdict, dataclass
import math

import numpy as np

from .communications_channel import channel_clock, discrete_channel_size
from .communications_data import MAX_SEED, integer, real
from .execution import ExecutionContext
from .model import Signal
from .operation_provenance import content_digest, verify_inputs


_BLOCK = 65_536
_LIGHT_SPEED = 299_792_458.0


@dataclass(frozen=True, slots=True)
class FreeSpaceLoss:
    distance_m: float
    carrier_hz: float | None = None

    def __post_init__(self):
        object.__setattr__(self, 'distance_m', real(self.distance_m, 'La distancia en metros', positive=True))
        if self.carrier_hz is not None:
            object.__setattr__(self, 'carrier_hz', real(self.carrier_hz, 'La portadora en Hz', positive=True))


@dataclass(frozen=True, slots=True)
class LogDistanceLoss:
    distance_m: float
    reference_distance_m: float = 1.0
    exponent: float = 2.0
    reference_loss_db: float | None = None
    carrier_hz: float | None = None

    def __post_init__(self):
        reference = real(self.reference_distance_m, 'La distancia de referencia en metros', positive=True)
        distance = real(self.distance_m, 'La distancia en metros', minimum=reference)
        object.__setattr__(self, 'reference_distance_m', reference)
        object.__setattr__(self, 'distance_m', distance)
        object.__setattr__(self, 'exponent', real(self.exponent, 'El exponente de pérdida', positive=True))
        if self.reference_loss_db is not None:
            object.__setattr__(self, 'reference_loss_db', real(self.reference_loss_db, 'La pérdida de referencia en dB'))
        if self.carrier_hz is not None:
            object.__setattr__(self, 'carrier_hz', real(self.carrier_hz, 'La portadora en Hz', positive=True))


@dataclass(frozen=True, slots=True)
class PropagationSpec:
    model: FreeSpaceLoss | LogDistanceLoss | None = None
    gain_db: float = 0.0
    shadow_std_db: float = 0.0
    seed: int = 2026

    def __post_init__(self):
        if self.model is not None and not isinstance(self.model, (FreeSpaceLoss, LogDistanceLoss)):
            raise ValueError('Elegí una ganancia fija, espacio libre o pérdida log-distancia.')
        object.__setattr__(self, 'gain_db', real(self.gain_db, 'La ganancia adicional en dB'))
        object.__setattr__(self, 'shadow_std_db', real(self.shadow_std_db, 'La desviación de sombra en dB', minimum=0))
        object.__setattr__(self, 'seed', integer(self.seed, 'La semilla de sombra', minimum=0, maximum=MAX_SEED))


@dataclass(frozen=True, slots=True)
class PropagationStatistics:
    model: str
    carrier_hz: float | None
    reference_loss_db: float | None
    path_loss_db: float
    shadow_loss_db: float
    net_gain_db: float
    amplitude_factor: float


@dataclass(frozen=True, slots=True, eq=False)
class PropagationResult:
    signal: Signal
    statistics: PropagationStatistics


def free_space_loss_db(distance_m, carrier_hz):
    distance = real(distance_m, 'La distancia en metros', positive=True)
    frequency = real(carrier_hz, 'La portadora en Hz', positive=True)
    loss = 20 * math.fsum((math.log10(4*math.pi), math.log10(distance),
                           math.log10(frequency), -math.log10(_LIGHT_SPEED)))
    if loss < 0:
        raise ValueError('La distancia queda fuera del régimen de propagación de espacio libre.')
    return loss


def _carrier(model, recorded):
    selected = model.carrier_hz
    if selected is not None and recorded is not None:
        recorded = real(recorded, 'La portadora registrada en Hz', positive=True)
        if not math.isclose(recorded, selected, rel_tol=1e-12):
            raise ValueError('La portadora del modelo debe coincidir con la portadora registrada.')
    if selected is None:
        selected = recorded
    return None if selected is None else real(selected, 'La portadora en Hz', positive=True)


def evaluate_propagation(spec: PropagationSpec, *, carrier_hz=None) -> PropagationStatistics:
    """Compute the gain without generating or changing the waveform."""
    if not isinstance(spec, PropagationSpec):
        raise ValueError('Indicá una configuración de propagación.')
    model = spec.model
    carrier = carrier_hz if model is None else _carrier(model, carrier_hz)
    reference = None
    if model is None:
        name, loss = 'gain', 0.0
    elif isinstance(model, FreeSpaceLoss):
        name, loss = 'free_space', free_space_loss_db(model.distance_m, carrier)
    else:
        name = 'log_distance'
        reference = model.reference_loss_db
        if reference is None:
            reference = free_space_loss_db(model.reference_distance_m, carrier)
        relative = math.log10(model.distance_m) - math.log10(model.reference_distance_m)
        loss = real(reference + (10 * relative)*model.exponent, 'La pérdida log-distancia')
    if carrier is not None:
        carrier = real(carrier, 'La portadora en Hz')
    shadow = 0.0
    if spec.shadow_std_db:
        rng = np.random.Generator(np.random.PCG64(spec.seed))
        shadow = real(spec.shadow_std_db*float(rng.standard_normal()), 'La pérdida por sombra')
    try:
        gain = math.fsum((spec.gain_db, -loss, -shadow))
        amplitude = 10.0 ** (gain/20)
    except OverflowError as exc:
        raise ValueError('La ganancia de propagación excede el rango numérico.') from exc
    amplitude = real(amplitude, 'El factor de amplitud de propagación', positive=True)
    return PropagationStatistics(name, carrier, reference, loss, shadow, gain, amplitude)


def apply_propagation(signal: Signal, spec: PropagationSpec,
                      execution: ExecutionContext | None = None) -> PropagationResult:
    ctx = execution or ExecutionContext()
    size = discrete_channel_size(signal, 0)
    stats = evaluate_propagation(spec, carrier_hz=signal.metadata.get('center_frequency_hz'))
    with ctx.reserve(40 * size + 24 * min(size, _BLOCK)):
        digest = content_digest(signal, ctx.checkpoint)
        metadata = {**deepcopy(signal.metadata), **channel_clock(signal, 0, size)}
        if stats.carrier_hz is not None:
            metadata['center_frequency_hz'] = stats.carrier_hz
        values = np.empty_like(signal.values)
        try:
            with np.errstate(over='raise', invalid='raise', under='ignore'):
                for start in range(0, size, _BLOCK):
                    ctx.checkpoint(90 * start // size)
                    stop = min(start + _BLOCK, size)
                    values[start:stop] = stats.amplitude_factor * signal.values[start:stop]
        except FloatingPointError as exc:
            raise FloatingPointError('La salida de propagación excede el rango numérico finito.') from exc
        metadata.pop('core_provenance', None)
        metadata.update(operation='communications_propagation', communications_propagation={
            'schema': 1, 'specification': asdict(spec), 'statistics': asdict(stats),
            'source_sha256': digest, 'shadow_generator': 'PCG64', 'numpy_version': np.__version__,
        })
        result = signal.copy_with(values=values, metadata=metadata, name='Salida de propagación', expression='')
        result._core_verification = (content_digest(result, ctx.checkpoint), (digest,), None)
        ctx.checkpoint(100)
        verify_inputs((signal,), (digest,), ctx.checkpoint)
    return PropagationResult(result, stats)
