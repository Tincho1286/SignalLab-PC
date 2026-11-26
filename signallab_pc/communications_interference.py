"""Finite-record interference, calibrated component powers and verified results."""

from copy import deepcopy
from dataclasses import asdict, dataclass, replace
import math

import numpy as np
from scipy.fft import fftfreq, ifft

from .communications_channel import AWGNSpec, add_awgn, channel_clock, channel_record_power, discrete_channel_size
from .communications_data import MAX_SEED, integer, real
from .communications_doppler import carrier_rotation, normalized_carrier
from .dsp_application import stage_signal, verify_dsp_signal
from .execution import ExecutionContext
from .model import Signal
from .operation_provenance import content_digest, verify_inputs
from .project import Project
from .system_clock import validate_discrete_clocks


_BLOCK = 65_536


@dataclass(frozen=True, slots=True)
class InterferenceTone:
    frequency_hz: float
    amplitude: float = 1.0
    phase_rad: float = 0.0

    def __post_init__(self):
        object.__setattr__(self, 'frequency_hz', real(self.frequency_hz, 'La frecuencia del tono en Hz'))
        object.__setattr__(self, 'amplitude', real(self.amplitude, 'La amplitud del tono', minimum=0))
        object.__setattr__(self, 'phase_rad', real(self.phase_rad, 'La fase del tono en radianes'))


def parse_interference_tone(text: str) -> InterferenceTone:
    from .scalar_expression import real_value

    parts = text.split(',')
    if not 1 <= len(parts) <= 3 or any(not item.strip() for item in parts):
        raise ValueError('Escribí frecuencia[, amplitud[, fase en radianes]] por tono.')
    return InterferenceTone(*(real_value(item) for item in parts))


@dataclass(frozen=True, slots=True)
class ToneInterference:
    tones: tuple[InterferenceTone, ...]

    def __post_init__(self):
        tones = tuple(self.tones)
        if not tones or any(not isinstance(tone, InterferenceTone) for tone in tones):
            raise ValueError('Indicá al menos un tono interferente.')
        object.__setattr__(self, 'tones', tones)


@dataclass(frozen=True, slots=True)
class BandInterference:
    bandwidth_hz: float
    center_hz: float = 0.0
    seed: int = 2026

    def __post_init__(self):
        object.__setattr__(self, 'bandwidth_hz', real(self.bandwidth_hz, 'El ancho de banda en Hz', positive=True))
        object.__setattr__(self, 'center_hz', real(self.center_hz, 'El centro de banda en Hz'))
        object.__setattr__(self, 'seed', integer(self.seed, 'La semilla de interferencia', minimum=0, maximum=MAX_SEED))


@dataclass(frozen=True, slots=True)
class ExternalInterference:
    frequency_shift_hz: float = 0.0

    def __post_init__(self):
        object.__setattr__(self, 'frequency_shift_hz', real(self.frequency_shift_hz, 'El traslado de la interferencia en Hz'))


@dataclass(frozen=True, slots=True)
class InterferenceSpec:
    model: ToneInterference | BandInterference | ExternalInterference
    power: float | None = None
    sir_db: float | None = None
    noise_snr_db: float | None = None
    noise_seed: int = 2026
    sinr_db: float | None = None

    def __post_init__(self):
        if not isinstance(self.model, (ToneInterference, BandInterference, ExternalInterference)):
            raise ValueError('Elegí interferencia tonal, de banda limitada o con una señal externa.')
        if sum(value is not None for value in (self.power, self.sir_db, self.sinr_db)) > 1:
            raise ValueError('Especificá potencia interferente, SIR o SINR, con una referencia por cálculo.')
        if self.power is not None:
            object.__setattr__(self, 'power', real(self.power, 'La potencia interferente', minimum=0))
        if self.sir_db is not None:
            object.__setattr__(self, 'sir_db', real(self.sir_db, 'La SIR en dB'))
        if self.sinr_db is not None:
            object.__setattr__(self, 'sinr_db', real(self.sinr_db, 'La SINR en dB'))
        if self.noise_snr_db is not None:
            object.__setattr__(self, 'noise_snr_db', real(self.noise_snr_db, 'La SNR nominal del ruido en dB'))
        object.__setattr__(self, 'noise_seed', integer(
            self.noise_seed, 'La semilla del ruido', minimum=0, maximum=MAX_SEED,
        ))


@dataclass(frozen=True, slots=True)
class PowerRatio:
    db: float | None
    state: str


def measure_power_ratio(signal, disturbance):
    signal = real(signal, 'La potencia de señal', minimum=0)
    disturbance = real(disturbance, 'La potencia de perturbación', minimum=0)
    if not signal:
        return PowerRatio(None, 'zero' if disturbance else 'undefined')
    if not disturbance:
        return PowerRatio(None, 'unbounded')
    return PowerRatio(10 * (math.log10(signal) - math.log10(disturbance)), 'finite')


@dataclass(frozen=True, slots=True)
class InterferenceStatistics:
    sample_count: int
    signal_power: float
    interference_power: float
    noise_power: float
    summed_component_powers: float
    observed_disturbance_power: float
    sir: PowerRatio
    snr: PowerRatio
    sinr: PowerRatio


@dataclass(frozen=True, slots=True, eq=False)
class InterferenceResult:
    signal: Signal
    interference: Signal
    noise: Signal | None
    statistics: InterferenceStatistics


def _tones(size, tones, rate, ctx):
    frequencies = tuple(normalized_carrier(tone.frequency_hz, rate) for tone in tones)
    out = np.zeros(size, dtype=np.complex128)
    for start in range(0, size, _BLOCK):
        stop = min(size, start + _BLOCK)
        offsets = np.arange(start, stop)
        for tone, ratio in zip(tones, frequencies, strict=True):
            ctx.checkpoint(5 + 40 * start // size)
            out[start:stop] += tone.amplitude * carrier_rotation(offsets, ratio, tone.phase_rad)
    return out, {}


def _band(size, model, rate, ctx):
    rate = real(rate, 'La frecuencia de muestreo Fs en Hz', positive=True)
    width, center = model.bandwidth_hz/rate, model.center_hz/rate
    lo, hi = center - width/2, center + width/2
    if not -.5 <= lo < hi <= .5:
        raise ValueError('La banda de interferencia debe quedar dentro de la Nyquist de entrada.')
    frequency = fftfreq(size)
    bins = np.flatnonzero((frequency >= lo) & (frequency < hi))
    if not bins.size:
        raise ValueError('La banda no contiene un bin DFT del registro. Alargá la señal o ampliá la banda.')
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(model.seed, spawn_key=(0,))))
    spectrum = np.zeros(size, dtype=np.complex128)
    sigma = size / math.sqrt(2*bins.size)
    for start in range(0, bins.size, _BLOCK):
        ctx.checkpoint(5 + 35 * start // bins.size)
        subset = bins[start:start + _BLOCK]
        z = rng.standard_normal((len(subset), 2))
        spectrum[subset] = sigma*(z[:, 0] + 1j*z[:, 1])
    ctx.checkpoint()
    out = ifft(spectrum, workers=1, overwrite_x=True)
    ctx.checkpoint(45)
    return out, {'occupied_bins': int(bins.size), 'bin_width_hz': rate/size, 'band_seed_key': [0]}


def _external(source, interferer, model, rate, ctx):
    discrete_channel_size(interferer, 0)
    fields = source.metadata
    other = interferer.metadata
    if (rate is None) != (other.get('sample_rate_hz') is None):
        raise ValueError('Registrá la misma Fs en ambas señales o alineá ambos registros solo por índice.')
    validate_discrete_clocks(source, interferer)
    if (fields.get('time_start_s') is None) != (other.get('time_start_s') is None):
        raise ValueError('Ambas señales requieren el mismo criterio de tiempo inicial.')
    if rate is None and fields.get('time_start_s') is not None:
        if source.origin != interferer.origin or float(fields['time_start_s']) != float(other['time_start_s']):
            raise ValueError('Se necesita Fs para comprobar la alineación de esos tiempos iniciales.')
    units = fields.get('amplitude_units')
    other_units = other.get('amplitude_units')
    if units is not None and other_units is not None and units != other_units:
        raise ValueError('Las señales deben usar las mismas unidades de amplitud.')
    wanted_center, interferer_center = fields.get('center_frequency_hz'), other.get('center_frequency_hz')
    center_difference = 0.0
    if wanted_center is not None and interferer_center is not None:
        center_difference = real(interferer_center, 'La portadora interferente en Hz') - real(
            wanted_center, 'La portadora deseada en Hz',
        )
    shift = real(center_difference + model.frequency_shift_hz, 'El traslado efectivo en Hz')
    ratio = normalized_carrier(shift, rate)
    out = np.zeros_like(source.values)
    delta = interferer.origin - source.origin
    first = max(0, delta)
    stop = min(out.size, delta+interferer.values.size)
    for start in range(first, stop, _BLOCK):
        ctx.checkpoint(5 + 40 * (start-first) // (stop-first))
        end = min(stop, start + _BLOCK)
        out[start:end] = interferer.values[start-delta:end-delta]*carrier_rotation(np.arange(start, end), ratio)
    return out, {'overlap_samples': max(0, stop - first), 'center_difference_hz': center_difference,
                 'effective_shift_hz': shift}


def _power_for_ratio(signal_power, ratio_db):
    if not signal_power:
        raise ValueError('La calibración de SIR o SINR requiere una señal deseada de potencia positiva.')
    try:
        power = math.exp(math.log(signal_power) - math.log(10)/10 * ratio_db)
    except OverflowError as exc:
        raise ValueError('La potencia interferente excede el rango numérico.') from exc
    return real(power, 'La potencia de perturbación calculada', positive=True)


def _scale_power(values, target, ctx):
    if target == 0:
        values.fill(0)
        return
    measured = channel_record_power(values, 'complex', ctx)
    if measured == 0:
        raise ValueError('La interferencia medida es nula y no puede alcanzar la potencia solicitada.')
    before, after = math.sqrt(measured), math.sqrt(target)
    for start in range(0, values.size, _BLOCK):
        ctx.checkpoint()
        values[start:start + _BLOCK] = (values[start:start + _BLOCK] / before)*after


def apply_interference(signal: Signal, spec: InterferenceSpec, *, external: Signal | None = None,
                       execution: ExecutionContext | None = None) -> InterferenceResult:
    """Add calibrated interference and optional independent AWGN over the input window."""
    if not isinstance(spec, InterferenceSpec):
        raise ValueError('Indicá una configuración de interferencia.')
    external_model = isinstance(spec.model, ExternalInterference)
    if (external is not None) != external_model:
        raise ValueError('La señal externa se carga únicamente con el modelo de interferencia externa.')
    ctx = execution or ExecutionContext()
    size = discrete_channel_size(signal, 0)
    estimate = 192*size + 176*min(size, _BLOCK)
    with ctx.reserve(estimate):
        inputs = (signal, external) if external_model else (signal,)
        if external_model:
            discrete_channel_size(external, 0)
        digests = tuple(content_digest(source, ctx.checkpoint) for source in inputs)
        clock = channel_clock(signal, 0, size)
        rate = clock.get('sample_rate_hz')
        desired_power = channel_record_power(signal.values, 'complex', ctx)
        levels = spec.power if spec.sir_db is None else _power_for_ratio(desired_power, spec.sir_db)
        total_target = None if spec.sinr_db is None else _power_for_ratio(desired_power, spec.sinr_db)
        if spec.noise_snr_db is not None and not desired_power:
            raise ValueError('La SNR del ruido requiere una señal deseada de potencia positiva.')
        try:
            with np.errstate(over='raise', invalid='raise', under='ignore'):
                if isinstance(spec.model, ToneInterference):
                    kind = 'tones'
                    interferer, evidence = _tones(size, spec.model.tones, rate, ctx)
                elif isinstance(spec.model, BandInterference):
                    kind = 'band'
                    interferer, evidence = _band(size, spec.model, rate, ctx)
                else:
                    kind = 'external'
                    interferer, evidence = _external(signal, external, spec.model, rate, ctx)
                fields = {**clock, 'amplitude_units': signal.metadata.get('amplitude_units', '1')}
                noise = None
                noise_power = 0.0
                disturbance = interferer
                if spec.noise_snr_db is not None:
                    seed_words = np.random.SeedSequence(spec.noise_seed, spawn_key=(1,)).generate_state(4)
                    noise_seed = sum(int(word) << (32*i) for i, word in enumerate(seed_words))
                    zero = Signal(np.zeros(size), signal.origin, units=signal.units, metadata=fields)
                    with ctx.aggregate_progress() as progress:
                        child = replace(ctx, pool=None, progress=lambda value: progress.checkpoint(50 + value//4))
                        noise = add_awgn(zero, AWGNSpec('snr', spec.noise_snr_db, noise_seed,
                                                       signal_power=desired_power), child).signal
                    noise.name = 'Ruido aditivo de la interferencia'
                    # The standalone AWGN proof referenced a generated zero input, not a project record.
                    del noise._core_verification
                    noise_power = channel_record_power(noise.values, 'complex', ctx)
                    evidence.update(noise_seed_key=[1], noise_effective_seed=noise_seed)
                if total_target is not None:
                    levels = total_target - noise_power
                    if levels < 0:
                        raise ValueError('La potencia del ruido por sí sola supera la perturbación que permite la SINR objetivo.')
                if levels is not None:
                    _scale_power(interferer, levels, ctx)
                interference_power = channel_record_power(interferer, 'complex', ctx)
                if noise is not None:
                    disturbance = interferer + noise.values
                summed = real(interference_power + noise_power, 'La potencia total por componentes', minimum=0)
                observed = channel_record_power(disturbance, 'complex', ctx)
                values = signal.values + disturbance
        except FloatingPointError as exc:
            raise FloatingPointError('La interferencia excede el rango numérico finito.') from exc

        stats = InterferenceStatistics(size, desired_power, interference_power, noise_power, summed, observed,
                                       measure_power_ratio(desired_power, interference_power),
                                       measure_power_ratio(desired_power, noise_power),
                                       measure_power_ratio(desired_power, summed))
        operation = 'communications_interference'
        wave = Signal(interferer, signal.origin, units=signal.units, name='Componente interferente',
                      metadata={**fields, 'operation': 'communications_interference_component'})
        components = {'interference': content_digest(wave, ctx.checkpoint)}
        if noise is not None:
            components['noise'] = content_digest(noise, ctx.checkpoint)
        specification = asdict(spec)
        if spec.sinr_db is None:
            specification.pop('sinr_db')
        config = {'schema': 1, 'model': kind, 'specification': specification, 'sources_sha256': list(digests),
                  'statistics': asdict(stats), 'synthesis': evidence, 'numpy_version': np.__version__,
                  'window': {'origin': signal.origin, 'sample_count': size}, 'components_sha256': components}
        metadata = {**deepcopy(signal.metadata), **clock}
        metadata.pop('core_provenance', None)
        metadata.update(operation=operation, communications_interference=config)
        result = signal.copy_with(values=values, name='Salida con interferencia', metadata=metadata, expression='')
        result._core_verification = (content_digest(result, ctx.checkpoint), digests, None)
        ctx.checkpoint(100)
        verify_inputs(inputs, digests, ctx.checkpoint)
    return InterferenceResult(result, wave, noise, stats)


def store_interference(project: Project, result: InterferenceResult, *, parents=(),
                       execution: ExecutionContext | None = None):
    """Commit the mixed signal, realized components and statistics in one transaction."""
    ctx = execution or ExecutionContext()
    with project.stage_records(before_commit=ctx.checkpoint) as staged:
        output = stage_signal(staged, result.signal, parents=parents, execution=ctx)
        digest, _, _ = verify_dsp_signal(result.signal)
        config = result.signal.metadata['communications_interference']
        proofs = config['components_sha256']
        report = asdict(result.statistics)
        if report != config['statistics'] or (result.noise is not None) != ('noise' in proofs):
            raise ValueError('Los resultados de interferencia cambiaron después del cálculo.')
        records = {'record': output}
        records['interference_record'] = staged.add(
            result.interference, operation='Componente interferente', parents=(output,),
            verification=(proofs['interference'], (digest,), ctx.checkpoint),
        )
        if result.noise is not None:
            records['noise_record'] = staged.add(
                result.noise, operation='Ruido aditivo', parents=(output,),
                verification=(proofs['noise'], (digest,), ctx.checkpoint),
            )
        records['statistics_record'] = staged.add(report, title='Potencias de interferencia', parents=(output,))
    return records
