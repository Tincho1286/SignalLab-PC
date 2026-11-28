"""RF power, a matched receiver noise chain, and small-signal device characterization."""

from dataclasses import dataclass
import math

import numpy as np

from .communications_data import real
from .communications_propagation import PropagationSpec, evaluate_propagation
from .execution import ExecutionContext


BOLTZMANN_J_PER_K = 1.380649e-23
NOISE_REFERENCE_K = 290.0
_POWER_LOG_PER_DB = math.log(10) / 10
_ONE_DB_VOLTAGE_DROP = -math.expm1(-math.log(10) / 20)


def power_dbm(watts):
    """Convert nonnegative watts, including zero, to dBm."""
    value = real(watts, 'Potencia en W', minimum=0)
    return 10 * math.log10(value) + 30 if value else -math.inf


def power_watts(dbm):
    """Convert dBm to watts. Negative infinity denotes exactly zero."""
    if dbm == -math.inf:
        return 0.0
    level = real(dbm, 'Nivel en dBm')
    try:
        value = 10 ** ((level - 30) / 10)
    except OverflowError as exc:
        raise ValueError('La potencia en W excede el rango numérico.') from exc
    if value == 0:
        raise ValueError('La potencia es demasiado pequeña para representarse en W.')
    return value


def _excess_log(factor_log):
    return factor_log + math.log(-math.expm1(-factor_log)) if factor_log else -math.inf


def _finite_exp(value, label):
    try:
        return real(math.exp(value), label, minimum=0)
    except OverflowError as exc:
        raise ValueError(f'{label} excede el rango numérico.') from exc


def _power_sum(values, label):
    try:
        return real(math.fsum(values), label)
    except OverflowError as exc:
        raise ValueError(f'{label} excede el rango numérico.') from exc


@dataclass(frozen=True, slots=True)
class RFStage:
    name: str
    gain_db: float
    noise_figure_db: float = 0.0

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError('Identificá la etapa de RF.')
        object.__setattr__(self, 'gain_db', real(self.gain_db, 'Ganancia en dB'))
        object.__setattr__(self, 'noise_figure_db', real(self.noise_figure_db, 'Figura de ruido en dB', minimum=0))

    @classmethod
    def passive(cls, name, loss_db, temperature_k=NOISE_REFERENCE_K):
        """A matched passive loss at a known physical temperature."""
        loss = real(loss_db, 'Pérdida en dB', minimum=0)
        temperature = real(temperature_k, 'Temperatura física en K', minimum=0)
        if not temperature or not loss:
            return cls(name, -loss, 0)
        relative = math.log(temperature) - math.log(NOISE_REFERENCE_K)
        figure = float(np.logaddexp(0, relative + _excess_log(loss * _POWER_LOG_PER_DB))) / _POWER_LOG_PER_DB
        return cls(name, -loss, figure)


@dataclass(frozen=True, slots=True)
class NoiseCascade:
    noise_factor: float
    noise_figure_db: float
    equivalent_temperature_k: float
    gain_db: float
    source_temperature_k: float
    reference_temperature_k: float
    noise_bandwidth_hz: float
    input_density_dbm_per_hz: float
    input_noise_dbm: float
    output_noise_dbm: float
    sensitivity_dbm: float


def noise_cascade(stages, bandwidth_hz, *, source_temperature_k=290, required_snr_db=0, context=None):
    """Friis cascaded noise, referred to the receiver input. Bandwidth is noise-equivalent."""
    ctx = context if context is not None else ExecutionContext()
    bandwidth = real(bandwidth_hz, 'Ancho equivalente de ruido en Hz', positive=True)
    source = real(source_temperature_k, 'Temperatura de fuente en K', positive=True)
    required = real(required_snr_db, 'SNR requerida en dB')
    total_gain_db = 0.0
    input_excess_log = -math.inf
    for stage in stages:
        ctx.checkpoint()
        if not isinstance(stage, RFStage):
            raise ValueError('El receptor requiere etapas RF con ganancia y figura de ruido.')
        stage_excess = _excess_log(stage.noise_figure_db * _POWER_LOG_PER_DB)
        input_excess_log = float(np.logaddexp(input_excess_log, stage_excess - total_gain_db * _POWER_LOG_PER_DB))
        total_gain_db = _power_sum((total_gain_db, stage.gain_db), 'Ganancia de recepción')
    factor_log = float(np.logaddexp(0, input_excess_log))
    noise_temperature_log = math.log(NOISE_REFERENCE_K) + input_excess_log
    total_temperature_log = float(np.logaddexp(math.log(source), noise_temperature_log))
    density = (math.log(BOLTZMANN_J_PER_K) + total_temperature_log) / _POWER_LOG_PER_DB + 30
    noise = density + 10 * math.log10(bandwidth)
    result = NoiseCascade(_finite_exp(factor_log, 'Factor de ruido'), factor_log / _POWER_LOG_PER_DB,
                          _finite_exp(noise_temperature_log, 'Temperatura equivalente de ruido'), total_gain_db,
                          source, NOISE_REFERENCE_K, bandwidth, density, noise,
                          _power_sum((noise, total_gain_db), 'Potencia de ruido de salida'),
                          _power_sum((noise, required), 'Sensibilidad'))
    ctx.checkpoint()
    return result


@dataclass(frozen=True, slots=True)
class LinkBudget:
    transmitted_dbm: float
    eirp_dbm: float
    received_at_antenna_dbm: float
    receiver_output_dbm: float
    snr_db: float
    margin_db: float
    path_loss_db: float
    shadow_loss_db: float
    propagation_model: str
    carrier_hz: float | None
    ledger: tuple[tuple[str, float, float], ...]
    noise: NoiseCascade


def link_budget(transmitted_dbm, propagation: PropagationSpec, bandwidth_hz, *,
                tx_antenna_dbi=0, rx_antenna_dbi=0, transmit_stages=(), receive_stages=(),
                source_temperature_k=290, required_snr_db=0, carrier_hz=None, context=None):
    """Link power ledger; losses are negative gains except for the propagation inputs."""
    ctx = context if context is not None else ExecutionContext()
    ctx.checkpoint()
    tx = real(transmitted_dbm, 'Potencia transmitida en dBm')
    tx_gain = real(tx_antenna_dbi, 'Ganancia de antena TX en dBi')
    rx_gain = real(rx_antenna_dbi, 'Ganancia de antena RX en dBi')
    path = evaluate_propagation(propagation, carrier_hz=carrier_hz)
    initial = tx
    ledger = []

    def add(label, delta):
        nonlocal tx
        tx = _power_sum((tx, delta), 'Potencia acumulada')
        ledger.append((label, delta, tx))

    for stage in transmit_stages:
        ctx.checkpoint()
        if not isinstance(stage, RFStage):
            raise ValueError('El transmisor requiere etapas RF con ganancia o pérdida.')
        add(stage.name, stage.gain_db)
    add('Antena TX', tx_gain)
    eirp = tx
    add('Ganancia adicional de propagación', propagation.gain_db)
    add('Pérdida de trayecto', -path.path_loss_db)
    add('Sombra del trayecto', -path.shadow_loss_db)
    add('Antena RX', rx_gain)
    received = tx
    stages = tuple(receive_stages)
    noise = noise_cascade(stages, bandwidth_hz, source_temperature_k=source_temperature_k,
                          required_snr_db=required_snr_db, context=ctx)
    for stage in stages:
        ctx.checkpoint()
        add(stage.name, stage.gain_db)
    snr = _power_sum((received, -noise.input_noise_dbm), 'SNR')
    margin = _power_sum((received, -noise.sensitivity_dbm), 'Margen de enlace')
    ctx.checkpoint()
    return LinkBudget(initial, eirp, received, tx, snr, margin, path.path_loss_db, path.shadow_loss_db,
                      path.model, path.carrier_hz, tuple(ledger), noise)


@dataclass(frozen=True, slots=True)
class DeviceCubics:
    gain_db: float
    iip3_dbm: float
    oip3_dbm: float
    input_p1db_dbm: float
    output_p1db_dbm: float
    input_limit_per_tone_dbm: float
    tones: int
    input_per_tone_dbm: float
    fundamental_per_tone_dbm: float
    compression_db: float
    third_harmonic_dbm: float
    im3_per_product_dbm: float | None
    sfdr_db: float | None
    sfdr_input_limit_dbm: float | None


def characterize_device(gain_db, input_per_tone_dbm, *, iip3_dbm=None, input_p1db_dbm=None,
                         tones=2, output_noise_dbm=None):
    """One or two nondegenerate tones, with an odd cubic valid through 1 dB compression."""
    gain = real(gain_db, 'Ganancia de pequeña señal en dB')
    input_power = real(input_per_tone_dbm, 'Potencia de entrada por tono en dBm')
    if type(tones) is not int or tones not in (1, 2):
        raise ValueError('Elegí uno o dos tonos independientes de igual nivel.')
    if (iip3_dbm is None) == (input_p1db_dbm is None):
        raise ValueError('Indicá IIP3 o P1dB de entrada como calibración del modelo cúbico.')
    difference = 10 * math.log10(_ONE_DB_VOLTAGE_DROP)
    if iip3_dbm is None:
        p1 = real(input_p1db_dbm, 'P1dB de entrada en dBm')
        ip3 = _power_sum((p1, -difference), 'IIP3')
    else:
        ip3 = real(iip3_dbm, 'IIP3 en dBm')
        p1 = _power_sum((ip3, difference), 'P1dB')
    # The neighbouring tone adds two more contributions to the cubic fundamental.
    multiplier = 2 * tones - 1
    limit = _power_sum((p1, -10 * math.log10(multiplier)), 'Límite del modelo')
    if input_power > limit + 1e-12:
        raise ValueError(f'La entrada supera {limit:.6g} dBm por tono, límite del modelo (1 dB de compresión).')
    relative_db = _power_sum((input_power, -ip3), 'Distancia a IIP3')
    fraction = math.exp(relative_db * _POWER_LOG_PER_DB)
    compression = 20 * math.log1p(-multiplier * fraction) / math.log(10)
    linear = _power_sum((input_power, gain), 'Fundamental extrapolada')
    harmonic = _power_sum((linear, 2 * relative_db, -20 * math.log10(3)), 'Tercer armónico')
    im3 = _power_sum((linear, 2 * relative_db), 'Producto IM3') if tones == 2 else None
    sfdr = threshold = None
    if output_noise_dbm is not None:
        noise = real(output_noise_dbm, 'Ruido de salida integrado en dBm')
        intercept_output = _power_sum((ip3, gain), 'OIP3')
        candidate = math.fsum((noise / 3, -gain / 3, 2 * (ip3 / 3)))
        # Use the specified two-tone asymptote only where its intersection is inside the model.
        upper = _power_sum((p1, -10 * math.log10(3)), 'Límite por tono')
        if candidate <= upper:
            sfdr = _power_sum((2*(intercept_output/3), -2*(noise/3)), 'SFDR')
            threshold = candidate
    return DeviceCubics(gain, ip3, _power_sum((ip3, gain), 'OIP3'), p1,
                        _power_sum((p1, gain, -1), 'P1dB de salida'), limit, tones, input_power,
                        _power_sum((linear, compression), 'Fundamental'), -compression,
                        harmonic, im3, sfdr, threshold)
