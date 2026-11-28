"""Uniform transmission lines and Smith coordinates under the RF network convention."""

from dataclasses import dataclass

import numpy as np

from .execution import ExecutionContext
from .rf_analysis import input_parameters, load_reflection, standing_wave_ratio, terminate
from .rf_network import RFNetwork, _real_array, _references


LIGHT_SPEED_M_S = 299792458.0
DB_PER_NEPER = 20 / np.log(10)


def _values(value, shape, name, *, positive=False):
    source = _real_array(value, name)
    if source.shape not in ((), shape) or not np.isfinite(source).all():
        raise ValueError(f'{name}: indicá un valor real finito o un valor por frecuencia.')
    if np.any(source < 0) or (positive and np.any(source == 0)):
        raise ValueError(f'{name}: indicá valores {"positivos" if positive else "no negativos"}.')
    return np.broadcast_to(source, shape)


def _length(value):
    return float(_values(value, (), 'Longitud en m'))


def _grid(frequencies_hz, *, positive=False):
    frequency = _real_array(frequencies_hz, 'El eje en Hz')
    if (frequency.ndim != 1 or not frequency.size or not np.isfinite(frequency).all()
            or frequency[0] < 0 or (positive and frequency[0] == 0)
            or np.any(frequency[1:] <= frequency[:-1])):
        raise ValueError('Ingresá frecuencias en Hz crecientes y finitas en el dominio del modelo.')
    return frequency


def _scaled_chain(gamma_l):
    """ABCD divided by exp(gamma*l), with cancellation controlled near zero."""
    exponent = np.minimum(gamma_l.real, 750) + 1j * gamma_l.imag
    forward = np.exp(-exponent)
    difference = -np.expm1(-2 * exponent) / 2
    return 1 - difference, difference, forward


@dataclass(frozen=True, slots=True)
class TransmissionLineResult:
    network: RFNetwork
    length_m: float
    characteristic_ohm: np.ndarray
    propagation_per_m: np.ndarray
    phase_rad: np.ndarray
    phase_velocity_m_s: np.ndarray
    wavelength_m: np.ndarray
    velocity_factor: np.ndarray
    intrinsic_loss_db: np.ndarray
    load_voltage_reflection: np.ndarray
    input_voltage_reflection: np.ndarray
    input_reference_reflection: np.ndarray
    input_impedance_ohm: np.ndarray
    input_admittance_siemens: np.ndarray
    input_reference_vswr: np.ndarray

    def standing_waves(self, frequency_index, distance_from_load_m, *, context=None):
        """Return |V| and |I| per unit incident voltage at the sending end."""
        ctx = context if context is not None else ExecutionContext()
        ctx.checkpoint()
        if (not isinstance(frequency_index, (int, np.integer)) or isinstance(frequency_index, bool)
                or not 0 <= frequency_index < len(self.network.frequencies_hz)):
            raise ValueError('Elegí un índice de frecuencia de la línea.')
        position = _values(distance_from_load_m, np.shape(distance_from_load_m), 'Distancia a la carga en m')
        if np.any(position > self.length_m):
            raise ValueError('La distancia a la carga debe estar dentro de la línea.')
        gamma = self.propagation_per_m[frequency_index]
        with ctx.reserve(128 * position.size):
            forward = np.exp(-gamma * (self.length_m - position))
            returned = self.load_voltage_reflection[frequency_index] * np.exp(-gamma * (self.length_m + position))
            voltage = np.abs(forward + returned)
            current = np.abs((forward - returned) / self.characteristic_ohm[frequency_index])
        ctx.checkpoint()
        return voltage, current


def _evaluate(frequency, length, characteristic, gamma, phase_velocity, reference_ohm, load_ohm, ctx):
    if not np.isfinite(characteristic).all() or not np.isfinite(gamma).all() or np.any(characteristic.real <= 0):
        raise ValueError('La impedancia característica o la propagación queda fuera del dominio numérico.')
    with np.errstate(over='ignore', invalid='ignore'):
        electrical = gamma * length
        loss_db = electrical.real * DB_PER_NEPER
    if not np.isfinite(electrical).all() or not np.isfinite(loss_db).all() or np.max(electrical.imag) > 1e10:
        raise ValueError('La longitud eléctrica excede el rango de fase resoluble.')
    reference = _references(reference_ohm, (len(frequency), 2))
    root = np.sqrt(reference)
    first, second = root.T
    cosh, sinh, forward = _scaled_chain(electrical)
    # Chain converted to power-wave coordinates. Normalization cancels exp(+gamma*l).
    ratio = second / first
    product = first * second
    a, d = cosh * ratio, cosh / ratio
    b, c = sinh * (characteristic / product), sinh * (product / characteristic)
    denominator = a + b + c + d
    scale = np.maximum.reduce((np.abs(a), np.abs(b), np.abs(c), np.abs(d)))
    if np.any(~np.isfinite(denominator) | (np.abs(denominator) <= 1e-12 * scale)):
        raise ValueError('La línea queda singular en las referencias solicitadas.')
    scattering = np.empty((len(frequency), 2, 2), dtype=complex)
    scattering[:, 0, 0] = (a + b - c - d) / denominator
    scattering[:, 1, 1] = (-a + b - c + d) / denominator
    scattering[:, 1, 0] = scattering[:, 0, 1] = 2 * forward / denominator
    network = RFNetwork(frequency, scattering, reference_ohm=reference, name='Línea de transmisión', context=ctx)
    reduced = terminate(network, [0], load_ohm=load_ohm, context=ctx)
    input_reflection = reduced.values[:, 0, 0]

    # Traveling voltage waves use characteristic impedance. The S port uses a real reference.
    if isinstance(load_ohm, str) and load_ohm in ('open', 'short'):
        load_voltage_reflection = np.full(frequency.shape, 1 if load_ohm == 'open' else -1, dtype=complex)
    else:
        load = reference[:, 1] if isinstance(load_ohm, str) else np.asarray(load_ohm, dtype=complex).reshape(-1)
        scale = np.maximum.reduce(np.broadcast_arrays(np.abs(load.real), np.abs(load.imag),
                                                      np.abs(characteristic.real), np.abs(characteristic.imag)))
        normalized_load = load.real / scale + 1j * (load.imag / scale)
        normalized_line = characteristic.real / scale + 1j * (characteristic.imag / scale)
        load_voltage_reflection = (normalized_load - normalized_line) / (normalized_load + normalized_line)
    impedance, admittance = input_parameters(input_reflection, reference[:, 0])
    wavelength = np.full(frequency.shape, np.inf)
    np.divide(2 * np.pi, gamma.imag, out=wavelength, where=gamma.imag > 0)
    result = TransmissionLineResult(network, length, characteristic.copy(), gamma.copy(), electrical.imag,
                                    phase_velocity, wavelength, phase_velocity / LIGHT_SPEED_M_S,
                                    loss_db, load_voltage_reflection,
                                    load_voltage_reflection * forward**2, input_reflection,
                                    impedance, admittance, standing_wave_ratio(input_reflection))
    ctx.checkpoint()
    return result


def uniform_line(frequencies_hz, length_m, characteristic_ohm=50, *, velocity_factor=1,
                 attenuation_db_per_m=0, reference_ohm=50, load_ohm='matched', context=None):
    """Model a uniform line with real Zc, constant velocity factor and supplied loss per metre."""
    ctx = context if context is not None else ExecutionContext()
    ctx.checkpoint()
    frequency = _grid(frequencies_hz)
    length = _length(length_m)
    factor = float(_values(velocity_factor, (), 'Factor de velocidad', positive=True))
    if factor > 1:
        raise ValueError('Este modelo de línea requiere 0 < factor de velocidad ≤ 1.')
    # Loads for a swept line use scalar or one value per frequency.
    if not isinstance(load_ohm, str):
        load_ohm = _swept_load(load_ohm, frequency.shape)
    with ctx.reserve(260 * len(frequency)):
        velocity = np.full(frequency.shape, LIGHT_SPEED_M_S * factor)
        characteristic = _values(characteristic_ohm, frequency.shape, 'Impedancia característica en Ω', positive=True)
        alpha = _values(attenuation_db_per_m, frequency.shape, 'Atenuación en dB/m') / DB_PER_NEPER
        beta = (frequency / velocity) * (2 * np.pi)
        gamma = alpha + 1j * beta
        return _evaluate(frequency, length, characteristic, gamma, velocity, reference_ohm, load_ohm, ctx)


def _swept_load(load_ohm, shape):
    raw = np.asarray(load_ohm)
    if raw.shape not in ((), shape):
        raise ValueError('La carga debe ser común o contener un valor por frecuencia.')
    return raw if raw.ndim == 0 else raw[:, None]


def rlgc_line(frequencies_hz, length_m, *, resistance_ohm_per_m, inductance_h_per_m,
              conductance_s_per_m, capacitance_f_per_m, reference_ohm=50,
              load_ohm='matched', context=None):
    """Use passive R,L,G,C values per metre. Each may be a scalar or a frequency sweep."""
    ctx = context if context is not None else ExecutionContext()
    ctx.checkpoint()
    frequency = _grid(frequencies_hz, positive=True)
    length = _length(length_m)
    if not isinstance(load_ohm, str):
        load_ohm = _swept_load(load_ohm, frequency.shape)
    with ctx.reserve(360 * len(frequency)):
        shape = frequency.shape
        r = _values(resistance_ohm_per_m, shape, 'R en Ω/m')
        inductance = _values(inductance_h_per_m, shape, 'L en H/m', positive=True)
        g = _values(conductance_s_per_m, shape, 'G en S/m')
        c = _values(capacitance_f_per_m, shape, 'C en F/m', positive=True)
        with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
            series = np.sqrt(r + 1j * (frequency * inductance * (2 * np.pi)))
            shunt = np.sqrt(g + 1j * (frequency * c * (2 * np.pi)))
            characteristic = series / shunt
            gamma_raw = series * shunt
            # Analytically nonnegative in this quadrant. Remove signed roundoff at R=G=0.
            gamma = np.maximum(gamma_raw.real, 0) + 1j * gamma_raw.imag
            velocity = (frequency / gamma.imag) * (2 * np.pi)
        if not np.isfinite(velocity).all() or np.any(velocity <= 0):
            raise ValueError('Los parámetros RLGC exceden el rango numérico resoluble.')
        return _evaluate(frequency, length, characteristic, gamma, velocity, reference_ohm, load_ohm, ctx)


def smith_values(reflection):
    """Return normalized z and y at a physical Γ point in either Smith grid."""
    return input_parameters(reflection, 1.0)


def smith_grid(mode='impedance', *, real=(0, .2, .5, 1, 2, 5), imaginary=(.2, .5, 1, 2, 5), points=257):
    """Return the complex loci within the unit disk for a Z or Y Smith grid."""
    if mode not in ('impedance', 'admittance'):
        raise ValueError('Elegí una carta de impedancia o admitancia.')
    if type(points) is not int or not 2 <= points <= 4096:
        raise ValueError('La cuadrícula Smith admite de 2 a 4096 puntos por trazo.')
    real = tuple(float(_values(value, (), 'Resistencia o conductancia normalizada')) for value in real)
    imaginary = tuple(float(_values(value, (), 'Reactancia o susceptancia normalizada', positive=True))
                      for value in imaginary)
    sign = 1 if mode == 'impedance' else -1
    t = np.linspace(0, 1, points)
    circle = np.exp((2j * np.pi) * t)
    loci = [(value, sign * ((value + circle) / (1 + value))) for value in real]
    reactance = []
    for value in imaginary:
        for signed in (value, -value):
            # Parameterize z=r+jx with r from zero to infinity, using t=r/(1+r).
            denominator = 1 + (1 - t) * (1j * signed)
            curve = 1 - 2 * (1 - t) / denominator
            reactance.append((signed, sign * curve))
    return {'constant_real': tuple(loci), 'constant_imaginary': tuple(reactance),
            'real_axis': sign * (2 * t - 1)}
