"""Point-frequency matching synthesis and the corresponding broadband models."""

from dataclasses import dataclass

import numpy as np

from .execution import ExecutionContext
from .rf_analysis import cascade, input_parameters, load_reflection, standing_wave_ratio, terminate
from .rf_line import LIGHT_SPEED_M_S, _grid, _values, uniform_line
from .rf_network import RFNetwork, convert


@dataclass(frozen=True, slots=True)
class MatchingDesign:
    method: str
    frequency_hz: float
    source_ohm: float
    load_ohm: complex
    elements: tuple[tuple[str, float], ...]
    topology: str
    velocity_factor: float = 1.0


@dataclass(frozen=True, slots=True)
class MatchingResponse:
    network: RFNetwork
    input_impedance_ohm: np.ndarray
    reflection: np.ndarray
    return_loss_db: np.ndarray
    vswr: np.ndarray
    delivered_power_fraction: np.ndarray
    effective_insertion_loss_db: np.ndarray


_UNITS = {
    'series_L_H': 'Inductor serie (H)', 'series_C_F': 'Capacitor serie (F)',
    'shunt_L_H': 'Inductor paralelo (H)', 'shunt_C_F': 'Capacitor paralelo (F)',
    'line_m': 'Longitud de línea (m)', 'line_ohm': 'Impedancia de línea (Ω)',
    'stub_m': 'Longitud de stub (m)',
}


def element_label(key):
    return _UNITS[key]


def _design_inputs(frequency_hz, source_ohm, load_ohm, velocity_factor):
    frequency = float(_values(frequency_hz, (), 'Frecuencia central en Hz', positive=True))
    source = float(_values(source_ohm, (), 'Resistencia de fuente en Ω', positive=True))
    factor = float(_values(velocity_factor, (), 'Factor de velocidad', positive=True))
    raw = np.asarray(load_ohm)
    if raw.ndim or raw.dtype.kind not in 'fciu' or not np.isfinite(raw) or raw.real <= 0:
        raise ValueError('La carga de diseño debe tener parte real positiva y ser finita, en Ω.')
    load = complex(raw)
    if factor > 1:
        raise ValueError('Indicá 0 < factor de velocidad ≤ 1.')
    return frequency, source, load, factor


def _components(x, b, frequency):
    omega = 2 * np.pi * frequency
    components = []
    if x > 0:
        components.append(('series_L_H', x / omega))
    elif x < 0:
        components.append(('series_C_F', -1 / x / omega))
    if b > 0:
        components.append(('shunt_C_F', b / omega))
    elif b < 0:
        components.append(('shunt_L_H', -1 / b / omega))
    return tuple(components)


def _l_solutions(frequency, source, load):
    # Solve in normalized impedance so the two quadratic discriminants are dimensionless.
    z = load / source
    solutions = []
    g, b_load = (1 / z).real, (1 / z).imag
    eps = 16 * np.finfo(float).eps
    if 0 < g <= 1 + eps:
        b = np.sqrt(g * max(1 - g, 0))
        for branch in (b, -b) if b else (0,):
            x_series = source * branch / g
            b_shunt = (branch - b_load) / source
            solutions.append(('series_shunt', _components(x_series, b_shunt, frequency)))
    r, x_load = z.real, z.imag
    if 0 < r <= 1 + eps:
        x = np.sqrt(r * max(1 - r, 0))
        for branch in (x, -x) if x else (0,):
            x_series = source * (branch - x_load)
            b_shunt = (branch / r) / source
            solutions.append(('shunt_series', _components(x_series, b_shunt, frequency)))
    # For an already matched load, both topologies can contain no parts.
    unique = []
    for entry in solutions:
        if not any(parts == entry[1] and (len(parts) < 2 or topology == entry[0]) for topology, parts in unique):
            unique.append(entry)
    return unique


def _stub_solutions(source, load, wavelength, kind):
    gamma = complex(load_reflection(load, source))
    radius = abs(gamma)
    if radius == 0:
        return [(kind, ())]
    if radius >= 1:
        raise ValueError('La carga queda demasiado cerca del círculo unidad para sintetizar un stub fiable.')
    imaginary = radius * np.sqrt(1 - radius**2)
    beta = 2 * np.pi / wavelength
    result = []
    for point in (complex(-radius**2, imaginary), complex(-radius**2, -imaginary)):
        distance = ((np.angle(gamma) - np.angle(point)) % (2 * np.pi)) / (2 * beta)
        b = -((1 - point) / (1 + point)).imag
        theta = (np.arctan(b) if kind == 'open' else np.arctan2(1, -b)) % np.pi
        parts = (('line_m', distance), ('stub_m', theta / beta))
        result.append((kind, parts))
    return result


def synthesize_matching(method, frequency_hz, source_ohm, load_ohm, *, velocity_factor=1, stub='open'):
    """Enumerate the exact lossless point matches available under the selected topology."""
    frequency, source, load, factor = _design_inputs(frequency_hz, source_ohm, load_ohm, velocity_factor)
    wavelength = LIGHT_SPEED_M_S * factor / frequency
    if not np.isfinite(wavelength) or wavelength <= 0 or not np.isfinite(2 * np.pi * frequency):
        raise ValueError('La frecuencia de diseño excede el rango numérico.')
    if method == 'l':
        solutions = _l_solutions(frequency, source, load)
    elif method == 'quarter_wave':
        if load.imag != 0:
            raise ValueError('Un transformador de cuarto de onda para este modelo requiere una carga resistiva.')
        solutions = [('quarter_wave', (('line_m', wavelength / 4),
                                       ('line_ohm', np.sqrt(source) * np.sqrt(load.real))))]
    elif method == 'stub' and stub in ('open', 'short'):
        solutions = _stub_solutions(source, load, wavelength, stub)
    else:
        raise ValueError('Elegí una red L, cuarto de onda o un stub abierto/cerrado.')
    if not solutions or any(not np.isfinite(value) or value < 0 or (value == 0 and key not in ('line_m', 'stub_m'))
                            for _, parts in solutions for key, value in parts):
        raise ValueError('No hay solución representable con los parámetros solicitados.')
    return tuple(MatchingDesign(method, frequency, source, load, parts, topology, factor)
                 for topology, parts in solutions)


def _l_network(frequency, source, topology, parts, context):
    if topology not in ('series_shunt', 'shunt_series'):
        raise ValueError('El orden de los elementos de la red L es inválido.')
    valid = {'series_L_H', 'series_C_F', 'shunt_L_H', 'shunt_C_F'}
    if (set(parts) - valid or {'series_L_H', 'series_C_F'} <= set(parts)
            or {'shunt_L_H', 'shunt_C_F'} <= set(parts)):
        raise ValueError('Usá hasta un elemento serie y uno en paralelo.')
    omega = 2 * np.pi * frequency
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        x = omega * parts.get('series_L_H', 0) - (1 / omega / parts['series_C_F'] if 'series_C_F' in parts else 0)
        b = omega * parts.get('shunt_C_F', 0) - (1 / omega / parts['shunt_L_H'] if 'shunt_L_H' in parts else 0)
        values = np.empty((frequency.size, 2, 2), dtype=complex)
        values[:, 0, 1] = 1j * x
        values[:, 1, 0] = 1j * b
        first_series = topology == 'series_shunt'
        values[:, 0, 0] = 1 - x * b if first_series else 1
        values[:, 1, 1] = 1 if first_series else 1 - x * b
    chain = RFNetwork(frequency, values, reference_ohm=source, representation='ABCD', name='Adaptación L',
                      context=context)
    return convert(chain, 'S', context=context)


def _stub_network(frequency, source, factor, topology, parts, context):
    if topology not in ('open', 'short') or set(parts) not in (set(), {'line_m', 'stub_m'}):
        raise ValueError('Indicá el tramo y la longitud del stub abierto o cortocircuitado.')
    line = uniform_line(frequency, parts.get('line_m', 0), source, velocity_factor=factor,
                        reference_ohm=source, context=context).network
    if not parts:
        return line
    phase = (frequency / (LIGHT_SPEED_M_S * factor)) * (2 * np.pi * parts['stub_m'])
    if not np.isfinite(phase).all() or np.any(phase > 1e10):
        raise ValueError('La longitud eléctrica del stub excede el rango resoluble.')
    sin, cos = np.sin(phase), np.cos(phase)
    numerator, denominator = (sin, cos) if topology == 'open' else (-cos, sin)
    # Shunt susceptance is j*numerator/denominator. Multiply through before division
    # to retain the exact limiting short when the stub reaches resonance.
    divisor = 2 * denominator + 1j * numerator
    values = np.empty((frequency.size, 2, 2), dtype=complex)
    values[:, 0, 0] = values[:, 1, 1] = -1j * numerator / divisor
    values[:, 0, 1] = values[:, 1, 0] = 2 * denominator / divisor
    shunt = RFNetwork(frequency, values, reference_ohm=source, name='Stub en derivación', context=context)
    return cascade(shunt, line, context=context)


def evaluate_matching(design: MatchingDesign, frequencies_hz, *, load_ohm=None, context=None):
    """Sweep actual L/C elements or line lengths, terminated in the specified load."""
    ctx = context if context is not None else ExecutionContext()
    ctx.checkpoint()
    frequency = _grid(frequencies_hz, positive=True)
    _, source, load, factor = _design_inputs(design.frequency_hz, design.source_ohm, design.load_ohm,
                                            design.velocity_factor)
    parts = dict(design.elements)
    if len(parts) != len(design.elements):
        raise ValueError('Cada elemento del diseño debe aparecer una sola vez.')
    for key, value in parts.items():
        if key not in _UNITS:
            raise ValueError('Elemento de adaptación desconocido.')
        _values(value, (), _UNITS[key], positive=key not in ('line_m', 'stub_m'))
    with ctx.reserve(450 * frequency.size):
        if design.method == 'l':
            network = _l_network(frequency, source, design.topology, parts, ctx)
        elif design.method == 'quarter_wave' and set(parts) == {'line_m', 'line_ohm'}:
            network = uniform_line(frequency, parts['line_m'], parts['line_ohm'], velocity_factor=factor,
                                   reference_ohm=source, context=ctx).network
        elif design.method == 'stub':
            network = _stub_network(frequency, source, factor, design.topology, parts, ctx)
        else:
            raise ValueError('El diseño de adaptación no coincide con el esquema requerido.')
        if load_ohm is not None:
            load = np.asarray(load_ohm)
            if load.shape not in ((), frequency.shape):
                raise ValueError('Ingresá una carga común o por frecuencia.')
            if load.ndim:
                load = load[:, None]
        gamma_l = load_reflection(load, network.reference_ohm[:, 1:])
        reduced = terminate(network, [0], reflection=gamma_l, context=ctx)
        reflection = reduced.values[:, 0, 0]
        impedance, _ = input_parameters(reflection, source)
        scattering = network.values
        amount = np.maximum(0, 1 - np.abs(gamma_l[:, 0])**2)
        transmitted = scattering[:, 1, 0] / (1 - scattering[:, 1, 1]*gamma_l[:, 0])
        fraction = amount * np.abs(transmitted)**2
        with np.errstate(divide='ignore'):
            rl = -20 * np.log10(np.abs(reflection))
            il = -10 * np.log10(fraction)
        result = MatchingResponse(network, impedance, reflection, rl, standing_wave_ratio(reflection), fraction, il)
    ctx.checkpoint()
    return result
