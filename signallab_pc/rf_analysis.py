"""Port connections, termination, and sampled measurements of RF networks."""

from dataclasses import dataclass

import numpy as np

from .execution import ExecutionContext
from .rf_network import (
    CONDITION_TOLERANCE, RFNetwork, _reject_at, _solve, convert, renormalize,
)


def _load_array(value, shape, label):
    array = np.asarray(value)
    if array.dtype.kind not in 'fciu' or array.shape not in ((), shape[1:], shape):
        raise ValueError(f'{label}: ingresá un valor común, por puerto o por frecuencia y puerto.')
    return np.broadcast_to(np.asarray(array, dtype=complex), shape)


def load_reflection(load_ohm, reference_ohm):
    """Reflection of a finite passive load, or an exact matched, open or short load."""
    reference = np.asarray(reference_ohm)
    if reference.dtype.kind not in 'fiu' or not np.isfinite(reference).all() or np.any(reference <= 0):
        raise ValueError('Las referencias deben ser reales, positivas y finitas.')
    reference = np.asarray(reference, dtype=float)
    if isinstance(load_ohm, str):
        if load_ohm not in ('matched', 'open', 'short'):
            raise ValueError('La carga ideal debe ser matched, open o short.')
        return np.full(reference.shape, {'matched': 0, 'open': 1, 'short': -1}[load_ohm], dtype=complex)
    shape = reference.shape
    if reference.ndim == 0:
        shape = np.shape(load_ohm)
    load = _load_array(load_ohm, shape, 'Carga en Ω')
    if not np.isfinite(load).all() or np.any(load.real < 0):
        raise ValueError('Ingresá una carga finita con resistencia no negativa.')
    scale = np.maximum(np.maximum(np.abs(load.real), np.abs(load.imag)), reference)
    normalized = load.real / scale + 1j * (load.imag / scale)
    ref = reference / scale
    return (normalized - ref) / (normalized + ref)


def cascade(left: RFNetwork, right: RFNetwork, *, renormalize_internal=False, context=None) -> RFNetwork:
    """Connect left port 2 to right port 1 on an identical grid."""
    ctx = context if context is not None else ExecutionContext()
    ctx.checkpoint()
    if left.nports != 2 or right.nports != 2:
        raise ValueError('La cascada en serie requiere dos redes de dos puertos.')
    frequency = left.frequencies_hz
    if not np.array_equal(frequency, right.frequencies_hz):
        raise ValueError('Las rejillas en Hz deben coincidir. Podés interpolar en la banda común.')
    a = convert(left, 'S', context=ctx)
    b = convert(right, 'S', context=ctx)
    if not np.array_equal(a.reference_ohm[:, 1], b.reference_ohm[:, 0]):
        if not renormalize_internal:
            raise ValueError('Las referencias en la conexión difieren. Elegí renormalizar el enlace interno.')
        b = renormalize(b, np.column_stack((a.reference_ohm[:, 1], b.reference_ohm[:, 1])), context=ctx)

    labels = (a.port_names[0], b.port_names[1])
    if labels[0] == labels[1]:
        labels = (f'Entrada {labels[0]}', f'Salida {labels[1]}')
    with ctx.reserve(frequency.size * 420):
        values = np.empty_like(a.values)
        for start in range(0, frequency.size, 256):
            ctx.checkpoint()
            section = slice(start, start + 256)
            x, y = a.values[section], b.values[section]
            axx, axy, ayx, ayy = x[:, 0, 0], x[:, 0, 1], x[:, 1, 0], x[:, 1, 1]
            bxx, bxy, byx, byy = y[:, 0, 0], y[:, 0, 1], y[:, 1, 0], y[:, 1, 1]
            with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
                loop = ayy * bxx
                divisor = 1 - loop
                _reject_at(~np.isfinite(loop) | (np.abs(divisor) <= CONDITION_TOLERANCE * np.maximum(1, np.abs(loop))),
                           frequency[section], 'Cascada')
                values[section, 0, 0] = axx + axy * (bxx / divisor) * ayx
                values[section, 0, 1] = (axy / divisor) * bxy
                values[section, 1, 0] = (byx / divisor) * ayx
                values[section, 1, 1] = byy + byx * (ayy / divisor) * bxy
            _reject_at(~np.isfinite(values[section]).all(axis=(1, 2)), frequency[section], 'Cascada')
        reference = np.column_stack((a.reference_ohm[:, 0], b.reference_ohm[:, 1]))
    return RFNetwork(frequency, values, reference_ohm=reference, port_names=labels,
                     name='Cascada de dos puertos', context=ctx,
                     metadata={'left': a.name, 'right': b.name, 'renormalize_internal': renormalize_internal})


def terminate(network: RFNetwork, keep, *, load_ohm='matched', reflection=None, context=None) -> RFNetwork:
    """Retain chosen zero-based ports, with independent loads on the others in input order."""
    ctx = context if context is not None else ExecutionContext()
    ctx.checkpoint()
    ports = network.nports
    retained = tuple(keep)
    if (not retained or any(type(index) not in (int, np.int32, np.int64) or not 0 <= index < ports
                            for index in retained) or len(set(retained)) != len(retained)):
        raise ValueError('Indicá puertos retenidos válidos, únicos y numerados desde cero.')
    if reflection is not None and not (isinstance(load_ohm, str) and load_ohm == 'matched'):
        raise ValueError('Elegí cargas en Ω o coeficientes de reflexión.')
    source = convert(network, 'S', context=ctx)
    eliminated = tuple(index for index in range(ports) if index not in retained)
    frequency = source.frequencies_hz
    work = frequency.size * (72 * len(retained)**2 + 64 * ports)
    block_size = max(1, min(256, 8192 // (ports * ports)))
    work += 350 * min(block_size, frequency.size) * ports**2
    with ctx.reserve(work):
        reference = source.reference_ohm[:, retained]
        load_reference = source.reference_ohm[:, eliminated]
        if reflection is None:
            gamma = load_reflection(load_ohm, load_reference)
        else:
            gamma = _load_array(reflection, load_reference.shape, 'Coeficientes de reflexión')
            if not np.isfinite(gamma).all() or np.any(np.abs(gamma) > 1 + 8 * np.finfo(float).eps):
                raise ValueError('Las terminaciones pasivas requieren |Γ| ≤ 1.')
        values = np.empty((frequency.size, len(retained), len(retained)), dtype=complex)
        for start in range(0, frequency.size, block_size):
            ctx.checkpoint()
            section = slice(start, start + block_size)
            s = source.values[section]
            result = s[:, retained, :][:, :, retained]
            if eliminated:
                identity = np.eye(len(eliminated))
                block = gamma[section, None, :]
                loop = s[:, eliminated, :][:, :, eliminated] * block
                rhs = s[:, eliminated, :][:, :, retained]
                transmission = s[:, retained, :][:, :, eliminated] * block
                with np.errstate(over='ignore', invalid='ignore'):
                    returned = _solve(identity - loop, rhs, frequency[section], 'Terminación',
                                      row_floor=np.maximum(1, np.abs(loop).max(axis=2, keepdims=True)))
                    result += transmission @ returned
                _reject_at(~np.isfinite(result).all(axis=(1, 2)), frequency[section], 'Terminación')
            values[section] = result
    return RFNetwork(frequency, values, reference_ohm=reference, context=ctx, name=source.name,
                     port_names=tuple(source.port_names[index] for index in retained),
                     metadata={**source.metadata, 'terminated_ports': [source.port_names[i] for i in eliminated]})


def _db(values):
    with np.errstate(divide='ignore'):
        return 20 * np.log10(values)


def _phase_delay(frequency, scattering, magnitude, checkpoint):
    phase = np.full(scattering.shape, np.nan)
    delay = np.full_like(phase, np.nan)
    for row in range(scattering.shape[1]):
        for column in range(scattering.shape[2]):
            checkpoint()
            trace = magnitude[:, row, column]
            valid = trace > (64 * np.finfo(float).eps * trace.max())
            edges = np.flatnonzero(np.diff(np.r_[False, valid, False]))
            if np.any(valid):
                phase[valid, row, column] = np.angle(scattering[valid, row, column])
            for start, stop in edges.reshape(-1, 2):
                if stop - start >= 2:
                    section = slice(start, stop)
                    segment = np.unwrap(phase[section, row, column])
                    phase[section, row, column] = segment
                    with np.errstate(over='ignore', divide='ignore', invalid='ignore'):
                        slope = np.gradient(segment, frequency[section]) / (-2 * np.pi)
                    delay[section, row, column] = np.where(np.isfinite(slope), slope, np.nan)
    return phase, delay


def input_parameters(gamma, reference_ohm):
    """Zin and Yin. NaNs denote ideal infinite values or unrepresentable arithmetic."""
    gamma = np.asarray(gamma, dtype=complex)
    with np.errstate(divide='ignore', invalid='ignore', over='ignore'):
        impedance = (1 + gamma) / (1 - gamma) * reference_ohm
        admittance = (1 - gamma) / (1 + gamma) / reference_ohm
    eps = 8 * np.finfo(float).eps
    impedance = np.where(np.isfinite(impedance) & (np.abs(1 - gamma) > eps), impedance, complex(np.nan, np.nan))
    admittance = np.where(np.isfinite(admittance) & (np.abs(1 + gamma) > eps), admittance, complex(np.nan, np.nan))
    return impedance, admittance


def standing_wave_ratio(gamma):
    magnitude = np.abs(gamma)
    upper = 1 + 8 * np.finfo(float).eps
    with np.errstate(divide='ignore', invalid='ignore'):
        bounded = np.minimum(magnitude, 1)
        return np.where(magnitude <= upper, (1 + bounded) / (1 - bounded), np.nan)


@dataclass(frozen=True, slots=True)
class NetworkMeasurements:
    scattering: RFNetwork
    magnitude: np.ndarray
    magnitude_db: np.ndarray
    phase_rad: np.ndarray
    group_delay_s: np.ndarray
    reflection: np.ndarray
    return_loss_db: np.ndarray
    insertion_loss_db: np.ndarray
    isolation_db: np.ndarray
    input_impedance_ohm: np.ndarray
    input_admittance_siemens: np.ndarray
    vswr: np.ndarray
    reciprocity_error: np.ndarray
    symmetry_error: np.ndarray
    max_singular_value: np.ndarray
    reciprocal: np.ndarray
    passive: np.ndarray

    @property
    def transmission(self):
        """Complex transmission, with diagonal entries reserved for reflection."""
        off_diagonal = ~np.eye(self.scattering.nports, dtype=bool)
        return np.where(off_diagonal, self.scattering.values, complex(np.nan, np.nan))


def measure(network: RFNetwork, *, tolerance=1e-9, context=None) -> NetworkMeasurements:
    """Measure S parameters with all other ports matched to their references."""
    ctx = context if context is not None else ExecutionContext()
    ctx.checkpoint()
    if not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError('Usá una tolerancia finita no negativa.')
    s = convert(network, 'S', context=ctx)
    count, ports, _ = s.values.shape
    block_size = max(1, min(256, 8192 // (ports * ports)))
    with ctx.reserve(100 * s.values.size + 120 * count * ports + 80 * block_size * ports**2):
        values = s.values
        magnitude = np.abs(values)
        _reject_at(~np.isfinite(magnitude).all(axis=(1, 2)), s.frequencies_hz, 'Módulo de S')
        magnitude_db = _db(magnitude)
        phase, delay = _phase_delay(s.frequencies_hz, values, magnitude, ctx.checkpoint)
        gamma = np.diagonal(values, axis1=1, axis2=2)
        impedance, admittance = input_parameters(gamma, s.reference_ohm)
        losses = -magnitude_db
        insertion = np.where(~np.eye(ports, dtype=bool), losses, np.nan)
        # For a selected forward path output <- input, the reverse uses S[input, output].
        isolation = insertion.swapaxes(1, 2)
        reciprocity = np.empty(count)
        symmetry = np.empty(count)
        singular = np.empty(count)
        for start in range(0, count, block_size):
            ctx.checkpoint()
            section = slice(start, start + block_size)
            block = values[section]
            reciprocity[section] = np.abs(block - block.swapaxes(1, 2)).max(axis=(1, 2))
            # Port reversal is a specific symmetry, independent of reciprocity.
            symmetry[section] = np.abs(block - block[:, ::-1, ::-1]).max(axis=(1, 2))
            singular[section] = np.linalg.svd(block, compute_uv=False)[:, 0]
        result = NetworkMeasurements(s, magnitude, magnitude_db, phase, delay, gamma, -_db(np.abs(gamma)),
                                     insertion, isolation, impedance, admittance, standing_wave_ratio(gamma),
                                     reciprocity, symmetry, singular, reciprocity <= tolerance,
                                     singular <= 1 + tolerance)
    ctx.checkpoint()
    return result
