"""Frequency-domain multiports with real power-wave reference impedances."""

from dataclasses import dataclass
import json

import numpy as np

from .execution import ExecutionContext


REPRESENTATIONS = ('S', 'Z', 'Y', 'ABCD')
CONDITION_TOLERANCE = 1e-12


class NetworkConditionError(ValueError):
    """The requested representation or connection has no reliable unique solution."""


def _real_array(value, label):
    array = np.asarray(value)
    if array.dtype.kind not in 'fiu':
        raise ValueError(f'{label} requiere valores reales.')
    return np.asarray(array, dtype=np.float64)


def _references(value, shape):
    array = _real_array(value, 'La referencia de cada puerto')
    if array.shape not in ((), shape[1:], shape):
        raise ValueError('Indicá una referencia común, por puerto o por frecuencia y puerto.')
    if not np.isfinite(array).all() or np.any(array <= 0):
        raise ValueError('Las referencias deben ser positivas y finitas, en Ω.')
    return np.broadcast_to(array, shape)


def _immutable(array):
    return np.frombuffer(array.tobytes(), dtype=array.dtype).reshape(array.shape)


def _representation(value):
    if not isinstance(value, str) or value.upper() not in REPRESENTATIONS:
        raise ValueError('Representación de red desconocida. Usá S, Z, Y o ABCD.')
    return value.upper()


@dataclass(frozen=True, slots=True, init=False, eq=False)
class RFNetwork:
    """A sampled network. S/Z/Y entries are indexed as [frequency, output, input]."""

    frequencies_hz: np.ndarray
    values: np.ndarray
    reference_ohm: np.ndarray
    representation: str
    port_names: tuple[str, ...]
    name: str
    _metadata_json: str
    wave_convention = 'power'

    def __init__(self, frequencies_hz, values, *, representation='S', reference_ohm=50,
                 port_names=None, name='', metadata=None, context=None):
        ctx = context if context is not None else ExecutionContext()
        ctx.checkpoint()
        kind = _representation(representation)
        raw = np.asarray(values)
        if (raw.ndim != 3 or not raw.shape[0] or not raw.shape[1]
                or raw.shape[1] != raw.shape[2] or raw.dtype.kind not in 'fciu'):
            raise ValueError('Las matrices requieren forma (frecuencias, puertos, puertos).')
        count, ports, _ = raw.shape
        if kind == 'ABCD' and ports != 2:
            raise ValueError('ABCD representa una red de dos puertos.')
        if isinstance(port_names, str):
            raise ValueError('Indicá las etiquetas de puertos como una secuencia.')
        labels = tuple(str(index + 1) for index in range(ports)) if port_names is None else tuple(port_names)
        if (len(labels) != ports or any(not isinstance(label, str) or not label.strip() for label in labels)
                or len(set(labels)) != ports):
            raise ValueError('Las etiquetas de puertos deben ser únicas y corresponder a la matriz.')
        if not isinstance(name, str) or (metadata is not None and not isinstance(metadata, dict)):
            raise ValueError('La red requiere un nombre de texto y metadatos de tipo objeto.')
        try:
            metadata_json = json.dumps(metadata or {}, allow_nan=False, ensure_ascii=False, sort_keys=True)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError('Los metadatos de red deben ser JSON finito.') from exc
        with ctx.reserve(40 * raw.size + 24 * count * ports + 32 * count):
            frequencies = _real_array(frequencies_hz, 'El eje en Hz')
            if (frequencies.shape != (count,) or not np.isfinite(frequencies).all()
                    or frequencies[0] < 0 or np.any(frequencies[1:] <= frequencies[:-1])):
                raise ValueError('Ingresá una frecuencia en Hz por matriz, en orden creciente y desde 0 Hz.')
            matrices = np.asarray(raw, dtype=np.complex128)
            if not np.isfinite(matrices).all():
                raise ValueError('Los parámetros de red deben ser finitos.')
            references = _references(reference_ohm, (count, ports))
            object.__setattr__(self, 'frequencies_hz', _immutable(frequencies))
            object.__setattr__(self, 'values', _immutable(matrices))
            object.__setattr__(self, 'reference_ohm', _immutable(references))
        object.__setattr__(self, 'representation', kind)
        object.__setattr__(self, 'port_names', labels)
        object.__setattr__(self, 'name', name)
        object.__setattr__(self, '_metadata_json', metadata_json)
        ctx.checkpoint()

    @property
    def nports(self):
        return self.values.shape[1]

    @property
    def metadata(self):
        return json.loads(self._metadata_json)


def _norm_columns(values, root, *, impedance):
    if impedance:
        return values / root[..., :, None] / root[..., None, :]
    return values * root[..., :, None] * root[..., None, :]


def _abcd_scale(values, root, *, normalize):
    first, second = root.T
    # Work in a dimensionless voltage/current basis before solving.
    ratio = second / first
    product = first * second
    result = values.copy()
    if normalize:
        result[:, 0, 0] *= ratio
        result[:, 0, 1] /= product
        result[:, 1, 0] *= product
        result[:, 1, 1] /= ratio
    else:
        result[:, 0, 0] /= ratio
        result[:, 0, 1] *= product
        result[:, 1, 0] /= product
        result[:, 1, 1] *= ratio
    return result


def _relation(values, reference, representation):
    identity = np.broadcast_to(np.eye(values.shape[1], dtype=complex), values.shape)
    if representation == 'S':
        return identity - values, -identity - values
    root = np.sqrt(reference)
    if representation == 'Z':
        return identity, -_norm_columns(values, root, impedance=True)
    if representation == 'Y':
        return -_norm_columns(values, root, impedance=False), identity
    abcd = _abcd_scale(values, root, normalize=True)
    cv, ci = np.empty_like(values), np.empty_like(values)
    cv[:, :, 0] = (1, 0)
    ci[:, :, 0] = (0, 1)
    cv[:, :, 1] = -abcd[:, :, 0]
    ci[:, :, 1] = abcd[:, :, 1]
    return cv, ci


def _reject_at(invalid, frequencies, action):
    if np.any(invalid):
        first = frequencies[int(np.argmax(invalid))]
        raise NetworkConditionError(f'{action} a {first:.12g} Hz: sistema singular o mal condicionado.')


def _component_scale(array):
    return np.maximum(np.abs(array.real), np.abs(array.imag)).max(axis=2, keepdims=True)


def _solve(lhs, rhs, frequencies, action, *, row_floor=None):
    scale = np.maximum(_component_scale(lhs), _component_scale(rhs))
    if row_floor is not None:
        scale = np.maximum(scale, row_floor)
    _reject_at(np.any((scale == 0) | ~np.isfinite(scale), axis=(1, 2)), frequencies, action)
    # Separate real and imaginary division also handles scales in the subnormal range.
    lhs = lhs.real / scale + 1j * (lhs.imag / scale)
    rhs = rhs.real / scale + 1j * (rhs.imag / scale)
    singular = np.linalg.svd(lhs, compute_uv=False)
    _reject_at(singular[:, -1] <= CONDITION_TOLERANCE * np.maximum(1, singular[:, 0]),
               frequencies, action)
    return np.linalg.solve(lhs, rhs)


def _parameters(cv, ci, reference, frequencies, target):
    action = f'Conversión a {target}'
    if target == 'S':
        return _solve(cv - ci, -(cv + ci), frequencies, action)
    root = np.sqrt(reference)
    if target == 'Z':
        z = _solve(cv, -ci, frequencies, action)
        return _norm_columns(z, root, impedance=False)
    if target == 'Y':
        y = _solve(ci, -cv, frequencies, action)
        return _norm_columns(y, root, impedance=True)
    # Unknowns [v1, i1], independent inputs [v2, -i2].
    lhs = np.stack((cv[:, :, 0], ci[:, :, 0]), axis=2)
    rhs = np.stack((-cv[:, :, 1], ci[:, :, 1]), axis=2)
    return _abcd_scale(_solve(lhs, rhs, frequencies, action), root, normalize=False)


def _converted(network, representation, reference, context):
    sample_count, ports, _ = network.values.shape
    block_size = max(1, min(256, 8192 // (ports * ports)))
    estimate = 72 * network.values.size + 32 * sample_count * ports
    estimate += 340 * min(sample_count, block_size) * ports * ports
    with context.reserve(estimate):
        result = np.empty_like(network.values)
        for start in range(0, sample_count, block_size):
            section = slice(start, min(start + block_size, sample_count))
            context.checkpoint()
            old = network.reference_ohm[section]
            new = reference[section]
            frequencies = network.frequencies_hz[section]
            with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
                cv, ci = _relation(network.values[section], old, network.representation)
                if not np.array_equal(old, new):
                    ratio = np.sqrt(new) / np.sqrt(old)
                    cv = cv * ratio[:, None, :]
                    ci = ci / ratio[:, None, :]
                _reject_at(~np.isfinite(cv).all(axis=(1, 2)) | ~np.isfinite(ci).all(axis=(1, 2)),
                           frequencies, f'Conversión a {representation}')
                result[section] = _parameters(cv, ci, new, frequencies, representation)
                _reject_at(~np.isfinite(result[section]).all(axis=(1, 2)), frequencies,
                           f'Conversión a {representation}')
    return RFNetwork(network.frequencies_hz, result, representation=representation, reference_ohm=reference,
                     port_names=network.port_names, name=network.name, metadata=network.metadata, context=context)


def convert(network: RFNetwork, representation: str, *, context=None) -> RFNetwork:
    """Convert directly from the source constitutive relation to S, Z, Y or ABCD."""
    ctx = context if context is not None else ExecutionContext()
    ctx.checkpoint()
    target = _representation(representation)
    if target == 'ABCD' and network.nports != 2:
        raise ValueError('ABCD representa una red de dos puertos.')
    if target == network.representation:
        return network
    return _converted(network, target, network.reference_ohm, ctx)


def renormalize(network: RFNetwork, reference_ohm, *, context=None) -> RFNetwork:
    """Change the real reference impedances while preserving the physical network."""
    ctx = context if context is not None else ExecutionContext()
    ctx.checkpoint()
    new = _references(reference_ohm, network.reference_ohm.shape)
    if np.array_equal(new, network.reference_ohm):
        return network
    if network.representation == 'S':
        return _converted(network, 'S', new, ctx)
    return RFNetwork(network.frequencies_hz, network.values, reference_ohm=new,
                     representation=network.representation, port_names=network.port_names,
                     name=network.name, metadata=network.metadata, context=ctx)


def interpolate(network: RFNetwork, frequencies_hz, *, context=None) -> RFNetwork:
    """Interpolate stored parameters by component on an explicitly chosen in-band grid."""
    ctx = context if context is not None else ExecutionContext()
    ctx.checkpoint()
    frequencies = _real_array(frequencies_hz, 'El eje en Hz')
    source = network.frequencies_hz
    if (frequencies.ndim != 1 or not frequencies.size or not np.isfinite(frequencies).all()
            or frequencies[0] < source[0] or frequencies[-1] > source[-1]
            or np.any(frequencies[1:] <= frequencies[:-1])):
        raise ValueError('La nueva rejilla en Hz debe ser creciente y estar dentro de la banda original.')
    if np.array_equal(source, frequencies):
        return network
    ports = network.nports
    with ctx.reserve(frequencies.size * ports * (72 * ports + 32)):
        values = np.empty((frequencies.size, ports, ports), dtype=complex)
        reference = np.empty((frequencies.size, ports))
        for row in range(ports):
            ctx.checkpoint()
            reference[:, row] = np.interp(frequencies, source, network.reference_ohm[:, row])
            for column in range(ports):
                ctx.checkpoint()
                values[:, row, column] = np.interp(frequencies, source, network.values[:, row, column])
    return RFNetwork(frequencies, values, reference_ohm=reference, representation=network.representation,
                     port_names=network.port_names, name=network.name, context=ctx,
                     metadata={**network.metadata, 'interpolation': 'linear_cartesian_in_band'})
