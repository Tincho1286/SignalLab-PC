"""Common headless entry points for a digital link and coherent Monte Carlo."""

from dataclasses import asdict, dataclass, field, replace
from hashlib import sha256
import math
import sys

import numpy as np

from .communications_channel import AWGNResult, AWGNSpec, add_awgn
from .communications_data import MAX_SEED, BitSequence, ConstellationSpec, SymbolClock, SymbolSequence, integer, real
from .communications_metrics import QualityMetrics, QualitySpec, TheoreticalError, measure_quality, theoretical_error
from .communications_modulation import decide_symbols, generate_bits, group_bits, modulate, ungroup_symbols
from .communications_pulses import Pulse, PulseSpec, apply_pulse, design_pulse, upsample_symbols
from .communications_receiver import ReceiveResult, SynchronizationSpec, recover_symbols
from .execution import ExecutionContext
from .model import Signal
from .operation_provenance import content_digest, settings_digest


def _default_constellation():
    return ConstellationSpec('psk', 4, rotation_rad=math.pi/4)


@dataclass(frozen=True, slots=True)
class ExperimentSpec:
    bit_count: int = 4096
    seed: int = 2026
    symbol_rate_hz: float = 12000
    constellation: ConstellationSpec = field(default_factory=_default_constellation)
    pulse: PulseSpec = field(default_factory=PulseSpec)
    eb_n0_db: float | None = 6.0
    synchronization: SynchronizationSpec = field(default_factory=SynchronizationSpec)
    pilot_symbols: int = 24
    allow_padding: bool = True

    def __post_init__(self):
        if not isinstance(self.constellation, ConstellationSpec) or not isinstance(self.pulse, PulseSpec):
            raise ValueError('El experimento requiere una constelación y una configuración de pulso.')
        sync = self.synchronization
        if not isinstance(sync, SynchronizationSpec):
            raise ValueError('El experimento requiere una configuración de sincronización.')
        if sync.mode == 'ideal' and (sync.sample_offset != 0 or sync.phase_rad != 0):
            raise ValueError('La cadena ideal deriva el instante del retardo TX/RX y usa fase cero.')
        if type(self.allow_padding) is not bool:
            raise ValueError('Indicá explícitamente si se permite relleno.')
        size = integer(self.bit_count, 'La cantidad de bits', maximum=sys.maxsize)
        width = self.constellation.bits_per_symbol
        if not self.allow_padding and size % width:
            raise ValueError('La cantidad de bits debe completar cada palabra de la constelación.')
        pilot = integer(self.pilot_symbols, 'Los símbolos de piloto', minimum=2, maximum=sys.maxsize)
        seed = integer(self.seed, 'La semilla', minimum=0, maximum=MAX_SEED)
        clock = SymbolClock(self.symbol_rate_hz, self.pulse.samples_per_symbol)
        level = None if self.eb_n0_db is None else real(self.eb_n0_db, 'Eb/N0')
        object.__setattr__(self, 'bit_count', size)
        object.__setattr__(self, 'pilot_symbols', pilot)
        object.__setattr__(self, 'seed', seed)
        object.__setattr__(self, 'symbol_rate_hz', clock.symbol_rate_hz)
        object.__setattr__(self, 'eb_n0_db', level)


@dataclass(frozen=True, slots=True)
class ExperimentProvenance:
    schema: int
    settings_sha256: str
    generator: str
    numpy_version: str
    stream_seeds: tuple[int, int, int]
    source: str
    input_bits_sha256: str


@dataclass(frozen=True, slots=True, eq=False)
class ExperimentResult:
    specification: ExperimentSpec
    provenance: ExperimentProvenance
    input_bits: BitSequence
    transmitted_labels: SymbolSequence
    transmitted_symbols: Signal
    pilot: Signal | None
    pulse: Pulse
    upsampled: Signal
    transmitted: Signal
    channel: AWGNResult | None
    matched: Signal
    reception: ReceiveResult
    received_labels: SymbolSequence | None
    received_bits: BitSequence | None
    metrics: QualityMetrics | None
    theoretical: TheoreticalError | None
    estimated_work_bytes: int
    signal_digests: tuple[tuple[str, str], ...]
    report_sha256: str

    def signals(self):
        records = {'symbols': self.transmitted_symbols, 'upsampled': self.upsampled, 'tx': self.transmitted,
                   'matched': self.matched}
        if self.pilot is not None:
            records['pilot'] = self.pilot
        if self.channel is not None:
            records['awgn'] = self.channel.signal
        if self.reception.symbols is not None:
            records['observed'] = self.reception.symbols
        return records

    def report(self):
        return {
            'specification': asdict(self.specification),
            'provenance': asdict(self.provenance),
            'pulse': {'tap_count': self.pulse.taps.size, 'energy': self.pulse.energy,
                      'group_delay_samples': self.pulse.group_delay_samples},
            'channel': None if self.channel is None else asdict(self.channel.statistics),
            'synchronization': asdict(self.reception.synchronization),
            'sample_gain': self.reception.applied_sample_gain,
            'metrics': None if self.metrics is None else asdict(self.metrics),
            'theoretical': None if self.theoretical is None else asdict(self.theoretical),
            'estimated_work_bytes': self.estimated_work_bytes,
        }


def _stream_seeds(seed):
    children = np.random.SeedSequence(seed).spawn(3)
    return tuple(sum(int(word) << (32*i) for i, word in enumerate(child.generate_state(4)))
                 for child in children)


def _working_set(spec, pilot_count):
    width = spec.constellation.bits_per_symbol
    symbols = (spec.bit_count+width-1)//width + pilot_count
    stride = spec.pulse.samples_per_symbol
    taps = spec.pulse.tap_count
    train = (symbols-1)*stride + 1
    tx = train + taps - 1
    matched = tx + taps - 1
    if matched > sys.maxsize//16:
        raise ValueError('El experimento excede el espacio de direcciones.')
    retained = (2*spec.bit_count + 40*symbols + 16*(train+2*tx+matched) + 32*pilot_count + 256*taps)
    receiver_scratch = 64 * min(pilot_count*(2*taps-1), max(65_536, pilot_count))
    workspace = max(144*matched+384*taps, 48*tx+96*min(tx, 65_536), receiver_scratch+128*symbols)
    return retained + workspace


def _child(ctx, index):
    highest = index*10-1

    def forward(value):
        nonlocal highest
        percentage = min(99, index*10 + value//10)
        if percentage > highest:
            highest = percentage
            ctx.checkpoint(percentage)

    return replace(ctx, pool=None, progress=forward)


def _frame(payload, spec, pilot_seed, pilot_count, clock, ctx):
    config = spec.constellation
    payload_labels = group_bits(payload, config, pad=spec.allow_padding, clock=clock, execution=ctx)
    if not pilot_count:
        return payload_labels, None
    width = config.bits_per_symbol
    pilot_bits = generate_bits(pilot_count*width, pilot_seed, ctx)
    pilot_labels = group_bits(pilot_bits, config, clock=clock, execution=ctx)
    frame = SymbolSequence(np.concatenate((pilot_labels.labels, payload_labels.labels)), config.order,
                           pilot_count*width+payload_labels.valid_bits, clock)
    return frame, modulate(pilot_labels, config, ctx)


def _quality(spec, frame, observed, reference, pilot_count, random_source, ctx):
    decoded = decide_symbols(observed, spec.constellation, valid_bits=frame.valid_bits, execution=ctx)
    unpacked = ungroup_symbols(decoded, ctx)
    bits = BitSequence(unpacked.values[pilot_count*frame.bits_per_symbol:])
    independent_symbols = (random_source and not frame.padding_bits and spec.synchronization.mode == 'ideal'
                           and spec.pulse.family == 'rectangular' and spec.pulse.span_symbols == 1)
    config = spec.constellation
    independent_bits = independent_symbols and (
        config.order == 2 or config.order == 4 and (config.labeling == 'gray' or config.family == 'qam')
    )
    settings = QualitySpec(pilot_count, pilot_count, independent_bits=independent_bits,
                           independent_symbols=independent_symbols)
    metrics = measure_quality(frame, decoded, reference=reference, observation=observed, spec=settings, execution=ctx)
    return decoded, bits, metrics


def run_experiment(spec: ExperimentSpec, *, bits: BitSequence | None = None,
                   execution: ExecutionContext | None = None) -> ExperimentResult:
    """Run one finite TX/AWGN/RX experiment using the same public operation services."""
    if not isinstance(spec, ExperimentSpec):
        raise TypeError('Indicá una configuración de experimento.')
    if bits is not None and (not isinstance(bits, BitSequence) or bits.values.size != spec.bit_count):
        raise ValueError('Los bits de entrada deben coincidir con la cantidad configurada.')
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    pilot_count = spec.pilot_symbols if spec.synchronization.mode == 'estimated' else 0
    estimate = _working_set(spec, pilot_count)
    seeds = _stream_seeds(spec.seed)
    clock = SymbolClock(spec.symbol_rate_hz)
    random_source = bits is None
    with ctx.reserve(estimate), ctx.aggregate_progress() as ctx:
        source = generate_bits(spec.bit_count, seeds[0], _child(ctx, 0)) if random_source else bits
        frame, pilot = _frame(source, spec, seeds[1], pilot_count, clock, _child(ctx, 1))
        symbols = modulate(frame, spec.constellation, _child(ctx, 2))
        pulse = design_pulse(spec.pulse, _child(ctx, 3))
        train = upsample_symbols(symbols, spec.pulse.samples_per_symbol, _child(ctx, 4))
        tx = apply_pulse(train, pulse, execution=_child(ctx, 5))
        channel = reference = None
        if spec.eb_n0_db is not None:
            energy = symbols.metadata['communications']['mean_symbol_energy'] * pulse.energy
            noise = AWGNSpec('eb_n0', spec.eb_n0_db, seeds[2], symbol_energy=energy,
                             bits_per_symbol=frame.bits_per_symbol)
            channel = add_awgn(tx, noise, _child(ctx, 6))
            reference = theoretical_error(spec.constellation, spec.eb_n0_db)
        matched = apply_pulse(tx if channel is None else channel.signal, pulse, matched=True, execution=_child(ctx, 7))
        sync_spec = spec.synchronization
        if sync_spec.mode == 'ideal':
            sync_spec = replace(sync_spec, sample_offset=pulse.taps.size-1)
        reception = recover_symbols(matched, frame.labels.size, spec.pulse.samples_per_symbol, sync_spec,
                                    pilot=pilot, sample_gain=pulse.energy, execution=_child(ctx, 8))
        labels = recovered = metrics = None
        if reception.symbols is not None:
            labels, recovered, metrics = _quality(spec, frame, reception.symbols, symbols, pilot_count,
                                                   random_source, _child(ctx, 9))
        bit_digest = sha256()
        bit_bytes = memoryview(source.values)
        for start in range(0, len(bit_bytes), 1 << 20):
            ctx.checkpoint()
            bit_digest.update(bit_bytes[start:start + (1 << 20)])
        provenance = ExperimentProvenance(1, settings_digest(asdict(spec)), 'PCG64', np.__version__, seeds,
                                          'pcg64' if random_source else 'supplied', bit_digest.hexdigest())
        result = ExperimentResult(spec, provenance, source, frame, symbols, pilot, pulse, train, tx, channel, matched,
                                  reception, labels, recovered, metrics, reference, estimate, (), '')
        fingerprints = tuple((role, content_digest(value, ctx.checkpoint)) for role, value in result.signals().items())
        report_sha256 = settings_digest(result.report())
        ctx.checkpoint(100)
    return replace(result, signal_digests=fingerprints, report_sha256=report_sha256)


@dataclass(frozen=True, slots=True)
class MonteCarloResult:
    symbols: int
    bits: int
    stopping_rule: str
    measured: QualityMetrics
    theoretical: TheoreticalError
    provenance: ExperimentProvenance


def coherent_monte_carlo(constellation: ConstellationSpec, eb_n0_db, symbols, seed,
                         execution: ExecutionContext | None = None) -> MonteCarloResult:
    """Fixed-count, memoryless coherent experiment with independent symbol trials."""
    if not isinstance(constellation, ConstellationSpec):
        raise TypeError('La simulación requiere una constelación.')
    count = integer(symbols, 'La cantidad de símbolos')
    level = real(eb_n0_db, 'Eb/N0')
    request = ExperimentSpec(
        bit_count=count*constellation.bits_per_symbol, seed=seed, symbol_rate_hz=1,
        constellation=constellation, pulse=PulseSpec('rectangular', 1, 1),
        eb_n0_db=level, allow_padding=False,
    )
    result = run_experiment(request, execution=execution)
    return MonteCarloResult(count, request.bit_count, 'fixed_symbol_count', result.metrics,
                            result.theoretical, result.provenance)
