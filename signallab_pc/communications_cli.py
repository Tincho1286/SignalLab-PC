"""Execute communication tools through the shared application services."""

import argparse
from dataclasses import asdict
import math
from pathlib import Path

from . import session
from .atomic_file import write_json
from .cli_session import add_output_arguments, add_session_arguments, load_input, load_signal_file, run_command
from .communications_channel import (
    AWGNSpec, MultipathSpec, add_awgn, analyze_multipath, apply_multipath, multipath_frequency, parse_channel_path,
)
from .communications_data import ConstellationSpec, SymbolClock, iq_signal
from .communications_doppler import CarrierShift, apply_carrier_shift
from .communications_experiment import ExperimentSpec, coherent_monte_carlo, run_experiment
from .communications_fading import FadingSpec, apply_fading, parse_fading_path
from .communications_impairments import (
    IQImbalance, PhaseNoiseSpec, TimingOffset, apply_iq_imbalance, apply_phase_noise, apply_timing_offset,
)
from .communications_interference import (
    BandInterference, ExternalInterference, InterferenceSpec, ToneInterference, apply_interference,
    parse_interference_tone, store_interference,
)
from .communications_metrics import QualitySpec, measure_quality
from .communications_modulation import decide_symbols, generate_bits, group_bits, modulate, parse_bits
from .communications_pipeline import read_pipeline_spec, run_channel_pipeline, store_channel_pipeline
from .communications_pulses import PulseSpec, apply_pulse, design_pulse, upsample_symbols
from .communications_propagation import FreeSpaceLoss, LogDistanceLoss, PropagationSpec, apply_propagation
from .communications_receiver import SynchronizationSpec, recover_symbols
from .communications_storage import decode_symbols, encode_bits, encode_symbols, save_experiment
from .communications_sweep import SweepSpec, axis_from_text, export_sweep_csv, load_sweep, run_sweep
from .dsp_application import store_signal
from .project import Project


def _constellation_arguments(parser):
    parser.add_argument('--family', choices=('psk', 'qam'), default='psk')
    parser.add_argument('--order', type=int, default=4, help='Orden de modulación M.')
    parser.add_argument('--labeling', choices=('natural', 'gray'), default='gray')
    parser.add_argument('--rotation', type=float, help='Rotación en radianes.')
    parser.add_argument('--normalization', choices=('unit_energy', 'raw'), default='unit_energy')


def _constellation(args):
    angle = args.rotation
    if angle is None:
        angle = math.pi/4 if args.family == 'psk' and args.order == 4 else 0
    return ConstellationSpec(args.family, args.order, args.labeling, angle, args.normalization)


def _pulse_arguments(parser):
    parser.add_argument('--pulse', choices=('rectangular', 'rc', 'rrc'), default='rrc')
    parser.add_argument('--sps', type=int, default=8, help='Muestras por símbolo.')
    parser.add_argument('--span', type=int, help='Duración del pulso en períodos de símbolo.')
    parser.add_argument('--rolloff', type=float)
    parser.add_argument('--pulse-normalization', choices=('unit_energy', 'unit_peak'), default='unit_energy')


def _pulse(args):
    span = args.span if args.span is not None else (1 if args.pulse == 'rectangular' else 10)
    return PulseSpec(args.pulse, args.sps, span, args.rolloff, args.pulse_normalization)


def _synchronization_arguments(parser):
    parser.add_argument('--sync', choices=('ideal', 'assisted', 'estimated'), default='ideal')
    parser.add_argument('--offset', type=int, help='Desplazamiento del primer símbolo, en muestras.')
    parser.add_argument('--phase', type=float, help='Fase que se compensa, en radianes.')
    parser.add_argument('--search-first', type=int, default=0)
    parser.add_argument('--search-last', type=int)


def _synchronization(args):
    return SynchronizationSpec(args.sync, args.offset, args.phase, args.search_first, args.search_last)


def _bits_arguments(parser, *, manual=True):
    source = parser.add_mutually_exclusive_group() if manual else parser
    source.add_argument('--bits', type=int, default=4096, help='Cantidad de bits pseudoaleatorios.')
    if manual:
        source.add_argument('--manual-bits', help='Bits 0 y 1, con espacios opcionales.')
    parser.add_argument('--seed', type=int, default=2026)
    parser.add_argument('--no-padding', action='store_true', help='Exigí palabras completas.')
    parser.add_argument('--symbol-rate', type=float, default=12000, help='Símbolos por segundo.')


def _save(path, project, workspace, ctx):
    session.save(path, project, workspace, before_commit=ctx.checkpoint, checkpoint=ctx.checkpoint)


def _experiment_configuration(args, bit_count):
    return ExperimentSpec(
        bit_count=bit_count, seed=args.seed,
        symbol_rate_hz=args.symbol_rate, constellation=_constellation(args), pulse=_pulse(args),
        eb_n0_db=None if args.no_noise else args.eb_n0, synchronization=_synchronization(args),
        pilot_symbols=args.pilot_symbols, allow_padding=not args.no_padding,
    )


def _link(args, ctx):
    source = None if args.manual_bits is None else parse_bits(args.manual_bits, ctx)
    spec = _experiment_configuration(args, args.bits if source is None else source.values.size)
    result = run_experiment(spec, bits=source, execution=ctx)
    identifier = save_experiment(args.output, result, ctx)
    return {'record': identifier, **result.report()}


def _modulate(args, ctx):
    bits = generate_bits(args.bits, args.seed, ctx) if args.manual_bits is None else parse_bits(args.manual_bits, ctx)
    spec = _constellation(args)
    labels = group_bits(bits, spec, pad=not args.no_padding, clock=SymbolClock(args.symbol_rate), execution=ctx)
    waveform = modulate(labels, spec, ctx)
    project = Project()
    with project.stage_records(before_commit=ctx.checkpoint) as staged:
        bit_record = staged.add(encode_bits(bits), title='Bits transmitidos')
        label_record = staged.add(encode_symbols(labels), title='Etiquetas transmitidas', parents=(bit_record,))
        signal = staged.add(waveform, parents=(label_record,))
    _save(args.output, project, session.empty_workspace(), ctx)
    return {'record': signal, 'bits_record': bit_record, 'labels_record': label_record,
            'constellation': asdict(spec), 'symbols': labels.labels.size, 'padding_bits': labels.padding_bits}


def _design_pulse(args, ctx):
    pulse = design_pulse(_pulse(args), ctx)
    clock = SymbolClock(args.symbol_rate, pulse.specification.samples_per_symbol)
    response = iq_signal(pulse.taps, clock, name='Respuesta al impulso del pulso')
    project = Project()
    with project.stage_records(before_commit=ctx.checkpoint) as staged:
        model = staged.add(pulse.transfer(clock.sample_rate_hz))
        signal = staged.add(response, parents=(model,))
    _save(args.output, project, session.empty_workspace(), ctx)
    return {'record': signal, 'transfer_record': model, 'tap_count': pulse.taps.size,
            'group_delay_samples': pulse.group_delay_samples, 'energy': pulse.energy}


def _source_id(project, args, source):
    return project.add(source, operation='Importar señal') if args.record is None else args.record


def _shape(args, ctx):
    project, workspace, source = load_input(args, ctx)
    spec = _pulse(args)
    pulse = design_pulse(spec, ctx)
    parent = _source_id(project, args, source)
    if args.interpolate:
        source = upsample_symbols(source, spec.samples_per_symbol, ctx)
        parent = store_signal(project, source, parents=(parent,), execution=ctx)
    initial = apply_pulse(source, pulse, matched=args.matched, execution=ctx)
    transfer = pulse.transfer(initial.metadata.get('sample_rate_hz'), matched=args.matched)
    system = project.add(transfer)
    record = store_signal(project, initial, parents=(parent, system), execution=ctx)
    _save(args.output, project, workspace, ctx)
    return {'record': record, 'transfer_record': system, 'sample_count': initial.values.size}


def _channel(args, ctx):
    project, workspace, source = load_input(args, ctx)
    awgn = add_awgn(source, AWGNSpec(args.reference, args.db, args.seed, args.domain,
                                    args.symbol_energy, args.bits_per_symbol, args.signal_power), ctx)
    parent = _source_id(project, args, source)
    record = store_signal(project, awgn.signal, parents=(parent,), execution=ctx)
    _save(args.output, project, workspace, ctx)
    return {'record': record, 'statistics': asdict(awgn.statistics)}


def _multipath(args, ctx):
    paths = tuple(parse_channel_path(value) for value in args.path)
    project, workspace, source = load_input(args, ctx)
    spec = MultipathSpec(paths, args.normalize_power)
    analysis = response = None
    if args.analyze or args.samples_per_symbol is not None or args.frequency_points is not None:
        sps = args.samples_per_symbol if args.samples_per_symbol is not None else source.metadata.get('samples_per_symbol')
        analysis = analyze_multipath(spec, samples_per_symbol=sps, execution=ctx)
    if args.frequency_points is not None:
        response = multipath_frequency(analysis, args.frequency_points, ctx)
    output = apply_multipath(source, spec, ctx)
    parent = _source_id(project, args, source)
    record = store_signal(project, output, parents=(parent,), execution=ctx)
    receipt = {'record': record, 'sample_count': output.values.size, 'channel': output.metadata['communications_multipath']}
    if analysis is not None:
        data = asdict(analysis)
        receipt['analysis_record'] = project.add(data, title='Análisis multitrayecto', parents=(record,))
        receipt['analysis'] = data
    if response is not None:
        receipt['frequency_record'] = project.add(response, operation='Respuesta del canal',
                                                   parents=(receipt['analysis_record'],))
    _save(args.output, project, workspace, ctx)
    return receipt


def _fading(args, ctx):
    if args.diagnostics and args.doppler_max_hz is None:
        raise ValueError('Indicá --doppler-max-hz para generar diagnósticos Doppler.')
    paths = []
    for value in args.path:
        ctx.checkpoint()
        paths.append(parse_fading_path(value, k_scale=args.k_scale))
    project, workspace, source = load_input(args, ctx)
    result = apply_fading(source, FadingSpec(tuple(paths), args.seed, args.doppler_max_hz), ctx)
    parent = _source_id(project, args, source)
    key = store_signal(project, result.signal, parents=(parent,), execution=ctx)
    coefficients = []
    for item in result.realizations:
        ctx.checkpoint()
        record = project.add(item.coefficients, operation='Realización de fading', parents=(key,))
        entry = {'record': record, 'statistics': asdict(item.statistics)}
        if args.diagnostics and item.path.average_power:
            diagnostics = item.doppler_diagnostics(ctx)
            entry['coherence_seconds'] = diagnostics.coherence_seconds
            entry['doppler_records'] = {
                name: project.add(value, operation='Diagnóstico Doppler', parents=(record,))
                for name, value in diagnostics.signals().items()
            }
        coefficients.append(entry)
    _save(args.output, project, workspace, ctx)
    return {'record': key, 'sample_count': result.signal.values.size, 'paths': coefficients}


def _shift_carrier(args, ctx):
    project, workspace, source = load_input(args, ctx)
    signal = apply_carrier_shift(source, CarrierShift(args.frequency_hz, args.phase_rad), ctx)
    record = store_signal(project, signal, parents=(_source_id(project, args, source),), execution=ctx)
    _save(args.output, project, workspace, ctx)
    return {'record': record, 'sample_count': signal.values.size}


def _impairment(args, ctx):
    project, workspace, source = load_input(args, ctx)
    receipt = {}
    phase = None
    if args.operation == 'timing-offset':
        signal = apply_timing_offset(source, TimingOffset(args.delay_samples, args.sfo_ppm), ctx)
    elif args.operation == 'phase-noise':
        result = apply_phase_noise(source, PhaseNoiseSpec(args.linewidth_hz, args.seed), ctx)
        signal, phase = result.signal, result.phase
        receipt['step_variance_rad2'] = result.step_variance_rad2
    else:
        result = apply_iq_imbalance(source, IQImbalance(args.gain_db, args.phase_rad, args.dc_i, args.dc_q), ctx)
        signal = result.signal
        receipt['statistics'] = asdict(result.statistics)
    record = store_signal(project, signal, parents=(_source_id(project, args, source),), execution=ctx)
    if phase is not None:
        receipt['phase_record'] = project.add(phase, operation='Trayectoria de fase Wiener', parents=(record,))
    _save(args.output, project, workspace, ctx)
    return {**receipt, 'record': record, 'sample_count': signal.values.size}


def _interfere(args, ctx):
    project, workspace, source = load_input(args, ctx)
    external = None
    if args.tone:
        if args.center_hz is not None:
            raise ValueError('Los tonos se trasladan ingresando su frecuencia individual.')
        model = ToneInterference(tuple(parse_interference_tone(value) for value in args.tone))
    elif args.bandwidth_hz is not None:
        model = BandInterference(args.bandwidth_hz, args.center_hz or 0.0, args.seed)
    else:
        model = ExternalInterference(args.center_hz or 0.0)
        if args.interferer_record is not None:
            if args.session is None:
                raise ValueError('--interferer-record requiere una sesión de entrada.')
            external = project.get(args.interferer_record)
        else:
            if args.interferer.resolve() == args.output.resolve():
                raise ValueError('Elegí una ruta de sesión distinta de la señal interferente.')
            external = load_signal_file(args.interferer, ctx)
    spec = InterferenceSpec(model, args.power, args.sir_db, args.noise_snr_db, args.noise_seed)
    result = apply_interference(source, spec, external=external, execution=ctx)
    parents = (_source_id(project, args, source),)
    if external is not None:
        parents += (args.interferer_record or project.add(external, operation='Importar interferencia externa'),)
    records = store_interference(project, result, parents=parents, execution=ctx)
    _save(args.output, project, workspace, ctx)
    return {**records, 'statistics': asdict(result.statistics)}


def _propagation(args, ctx):
    project, workspace, source = load_input(args, ctx)
    model = None
    if args.model == 'free-space':
        model = FreeSpaceLoss(args.distance_m, args.carrier_hz)
    elif args.model == 'log-distance':
        model = LogDistanceLoss(args.distance_m, args.reference_distance_m, args.exponent,
                                args.reference_loss_db, args.carrier_hz)
    result = apply_propagation(source, PropagationSpec(model, args.gain_db, args.shadow_std_db, args.seed), ctx)
    record = store_signal(project, result.signal, parents=(_source_id(project, args, source),), execution=ctx)
    _save(args.output, project, workspace, ctx)
    return {'record': record, 'statistics': asdict(result.statistics)}


def _channel_pipeline(args, ctx):
    config = read_pipeline_spec(args.channel_config, ctx)
    if args.channel_config.resolve() == args.output.resolve():
        raise ValueError('Elegí una salida distinta del archivo de configuración de la cadena.')
    project, workspace, source = load_input(args, ctx)
    external = {}
    records = {}
    for load_record, values in ((True, args.external_record), (False, args.external_file)):
        for binding in values:
            name, separator, target = binding.partition('=')
            if not separator or not name or not target or name in external:
                raise ValueError('Usá nombre=registro o nombre=archivo una sola vez para cada entrada externa.')
            if load_record:
                if args.session is None:
                    raise ValueError('Los vínculos a registros externos requieren una sesión de entrada.')
                records[name] = target
                external[name] = project.get(target)
            else:
                path = Path(target)
                if path.resolve() == args.output.resolve():
                    raise ValueError('Elegí una salida distinta de todas las señales externas.')
                external[name] = load_signal_file(path, ctx)
    result = run_channel_pipeline(source, config, external=external, execution=ctx)
    receipt = store_channel_pipeline(project, result, source_id=args.record, external_records=records, execution=ctx)
    _save(args.output, project, workspace, ctx)
    return {**receipt, 'report_sha256': result.report_sha256, 'sample_count': result.signal.values.size}


def _receive(args, ctx):
    project, workspace, source = load_input(args, ctx)
    pilot = None if args.pilot_record is None else project.get(args.pilot_record)
    recovered = recover_symbols(source, args.symbols, args.sps, _synchronization(args),
                                pilot=pilot, sample_gain=args.gain, execution=ctx)
    parent = _source_id(project, args, source)
    parents = (parent,) if args.pilot_record is None else (parent, args.pilot_record)
    record = None if recovered.symbols is None else store_signal(
        project, recovered.symbols, parents=parents, execution=ctx,
    )
    synchronization = asdict(recovered.synchronization)
    report = project.add(synchronization, title='Sincronización', parents=parents if record is None else (record,))
    _save(args.output, project, workspace, ctx)
    return {'record': record, 'report_record': report, 'synchronization': synchronization}


def _decide(args, ctx):
    project, workspace, source = load_input(args, ctx)
    labels = decide_symbols(source, _constellation(args), valid_bits=args.valid_bits, execution=ctx)
    parent = _source_id(project, args, source)
    record = project.add(encode_symbols(labels), title='Etiquetas recibidas', parents=(parent,))
    _save(args.output, project, workspace, ctx)
    return {'record': record, 'symbols': labels.labels.size, 'bits': labels.valid_bits}


def _measure(args, ctx):
    project, workspace = session.load(args.session, checkpoint=ctx.checkpoint)
    left = decode_symbols(project.get(args.transmitted), ctx)
    right = decode_symbols(project.get(args.received), ctx)
    reference = None if args.reference_record is None else project.get(args.reference_record)
    observation = None if args.observation_record is None else project.get(args.observation_record)
    conditions = QualitySpec(args.tx_start, args.rx_start, args.symbols)
    metrics = measure_quality(left, right, reference=reference, observation=observation,
                              spec=conditions, execution=ctx)
    parents = tuple(key for key in (args.transmitted, args.received, args.reference_record, args.observation_record)
                    if key is not None)
    report = asdict(metrics)
    record = project.add(report, title='BER, SER y EVM', parents=parents)
    _save(args.output, project, workspace, ctx)
    return {'record': record, 'metrics': report}


def _monte_carlo(args, ctx):
    result = coherent_monte_carlo(_constellation(args), args.eb_n0, args.symbols, args.seed, ctx)
    report = asdict(result)
    write_json(args.output, report, before_commit=ctx.checkpoint, checkpoint=ctx.checkpoint)
    return report


def _sweep(args, ctx):
    if args.inspect:
        if args.axis:
            raise ValueError('Abrir un barrido usa la configuración del catálogo.')
        result = load_sweep(args.output, ctx)
    else:
        axes = []
        for raw in args.axis:
            parameter, separator, values = raw.partition('=')
            if not separator:
                raise ValueError('Usá --axis parámetro=valor1,valor2.')
            axes.append(axis_from_text(parameter, values))
        spec = SweepSpec(_experiment_configuration(args, args.bits), tuple(axes), args.seed_policy)
        result = run_sweep(spec, args.output, ctx)
    if args.csv is not None:
        export_sweep_csv(result, args.csv, ctx)
    return {'directory': str(result.directory), 'planned': result.planned,
            'completed': len(result.runs), 'complete': result.complete}


def _link_channel_arguments(parser):
    _synchronization_arguments(parser)
    noise = parser.add_mutually_exclusive_group()
    noise.add_argument('--eb-n0', type=float, default=6.0)
    noise.add_argument('--no-noise', action='store_true')
    parser.add_argument('--pilot-symbols', type=int, default=24)


def main(argv=None):
    parser = argparse.ArgumentParser(prog='signallab-pc communications', description='Laboratorio digital sin Qt.')
    commands = parser.add_subparsers(dest='operation', required=True)
    link = commands.add_parser('link', help='Ejecutá una cadena TX, AWGN y RX.')
    _bits_arguments(link)
    _constellation_arguments(link)
    _pulse_arguments(link)
    _link_channel_arguments(link)
    add_output_arguments(link)
    link.set_defaults(execute=_link)

    modulation = commands.add_parser('modulate', help='Convertí bits en etiquetas y símbolos I/Q.')
    _bits_arguments(modulation)
    _constellation_arguments(modulation)
    add_output_arguments(modulation)
    modulation.set_defaults(execute=_modulate)

    design = commands.add_parser('pulse', help='Diseñá un pulso y guardá su FIR.')
    _pulse_arguments(design)
    design.add_argument('--symbol-rate', type=float, default=12000)
    add_output_arguments(design)
    design.set_defaults(execute=_design_pulse)

    shaping = commands.add_parser('shape', help='Aplicá el FIR de transmisión o el filtro adaptado.')
    _pulse_arguments(shaping)
    shaping.add_argument('--interpolate', action='store_true')
    shaping.add_argument('--matched', action='store_true')
    add_session_arguments(shaping)
    shaping.set_defaults(execute=_shape)

    channel = commands.add_parser('awgn', help='Sumá ruido gaussiano real o complejo.')
    channel.add_argument('--reference', choices=('snr', 'es_n0', 'eb_n0'), default='snr')
    channel.add_argument('--db', type=float, required=True)
    channel.add_argument('--seed', type=int, default=2026)
    channel.add_argument('--domain', choices=('real', 'complex'), default='complex')
    channel.add_argument('--symbol-energy', type=float)
    channel.add_argument('--bits-per-symbol', type=int)
    channel.add_argument('--signal-power', type=float)
    add_session_arguments(channel)
    channel.set_defaults(execute=_channel)

    multipath = commands.add_parser('multipath', help='Sumá trayectorias con retardo entero y ganancia compleja.')
    multipath.add_argument('--path', action='append', required=True, metavar='RETARDO=GANANCIA',
                           help='Repetí la opción por trayectoria. Ejemplo: --path=0=1 --path=4=0.35*i.')
    multipath.add_argument('--normalize-power', action='store_true', help='Fijá la energía de h[n] en uno.')
    multipath.add_argument('--analyze', action='store_true', help='Guardá el perfil de potencia y los retardos.')
    multipath.add_argument('--samples-per-symbol', type=int, help='Calculá también la ISI a intervalos de símbolo.')
    multipath.add_argument('--frequency-points', type=int, help='Guardá H(eʲω) en este número de puntos centrados.')
    add_session_arguments(multipath)
    multipath.set_defaults(execute=_multipath)

    fading = commands.add_parser('fading', help='Aplicá fading Rayleigh/Rician independiente o correlacionado.')
    fading.add_argument('--path', action='append', required=True, metavar='RETARDO=POTENCIA[,K[,FASE]]',
                        help='Retardo en muestras, potencia lineal, K opcional y fase LOS opcional en rad.')
    fading.add_argument('--k-scale', choices=('linear', 'db'), default='linear')
    fading.add_argument('--seed', type=int, default=2026)
    fading.add_argument('--doppler-max-hz', type=float, help='Usá dispersión Clarke de hasta esta frecuencia en Hz.')
    fading.add_argument('--diagnostics', action='store_true', help='Guardá autocorrelación, PSD y coherencia por camino.')
    add_session_arguments(fading)
    fading.set_defaults(execute=_fading)

    shift = commands.add_parser('shift-carrier', help='Aplicá un desplazamiento determinista de frecuencia y fase.')
    shift.add_argument('--frequency-hz', type=float, default=0.0)
    shift.add_argument('--phase-rad', type=float, default=0.0)
    add_session_arguments(shift)
    shift.set_defaults(execute=_shift_carrier)

    timing = commands.add_parser('timing-offset', help='Simulá retardo y desajuste del reloj de muestreo.')
    timing.add_argument('--delay-samples', type=float, default=0.0)
    timing.add_argument('--sfo-ppm', type=float, default=0.0)
    add_session_arguments(timing)
    timing.set_defaults(execute=_impairment)

    phase = commands.add_parser('phase-noise', help='Aplicá una trayectoria de fase Wiener reproducible.')
    phase.add_argument('--linewidth-hz', type=float, required=True, help='Ancho lorentziano completo a media altura.')
    phase.add_argument('--seed', type=int, default=2026)
    add_session_arguments(phase)
    phase.set_defaults(execute=_impairment)

    iq = commands.add_parser('iq-imbalance', help='Modificá la ganancia, fase y nivel DC de la señal I/Q.')
    iq.add_argument('--gain-db', type=float, default=0.0, help='Ganancia de Q relativa a I.')
    iq.add_argument('--phase-rad', type=float, default=0.0, help='Error de ángulo de Q en radianes.')
    iq.add_argument('--dc-i', type=float, default=0.0)
    iq.add_argument('--dc-q', type=float, default=0.0)
    add_session_arguments(iq)
    iq.set_defaults(execute=_impairment)

    interfere = commands.add_parser('interference', help='Agregá tonos, interferencia en banda o una señal externa.')
    model = interfere.add_mutually_exclusive_group(required=True)
    model.add_argument('--tone', action='append', metavar='HZ[,AMPLITUD[,FASE]]', help='Repetible por cada tono.')
    model.add_argument('--bandwidth-hz', type=float)
    model.add_argument('--interferer', type=Path, help='Archivo de señal JSON o SLBIN.')
    model.add_argument('--interferer-record', help='Registro interferente dentro de la sesión.')
    interfere.add_argument('--center-hz', type=float, help='Centro de banda o desplazamiento de la señal externa.')
    calibration = interfere.add_mutually_exclusive_group()
    calibration.add_argument('--power', type=float)
    calibration.add_argument('--sir-db', type=float)
    interfere.add_argument('--seed', type=int, default=2026, help='Semilla de la interferencia de banda limitada.')
    interfere.add_argument('--noise-snr-db', type=float, help='Agregá AWGN con esta SNR nominal de entrada.')
    interfere.add_argument('--noise-seed', type=int, default=2026)
    add_session_arguments(interfere)
    interfere.set_defaults(execute=_interfere)

    loss = commands.add_parser('propagation', help='Aplicá ganancia, pérdidas de propagación y sombra log-normal.')
    loss.add_argument('--model', choices=('gain', 'free-space', 'log-distance'), default='gain')
    loss.add_argument('--gain-db', type=float, default=0)
    loss.add_argument('--distance-m', type=float)
    loss.add_argument('--carrier-hz', type=float)
    loss.add_argument('--reference-distance-m', type=float, default=1)
    loss.add_argument('--reference-loss-db', type=float)
    loss.add_argument('--exponent', type=float, default=2)
    loss.add_argument('--shadow-std-db', type=float, default=0)
    loss.add_argument('--seed', type=int, default=2026)
    add_session_arguments(loss)
    loss.set_defaults(execute=_propagation)

    pipeline = commands.add_parser('channel-pipeline', help='Ejecutá y guardá una cadena ordenada de canales.')
    pipeline.add_argument('--config', dest='channel_config', required=True, type=Path, help='Configuración JSON.')
    pipeline.add_argument('--external-record', action='append', default=[], metavar='NOMBRE=REGISTRO')
    pipeline.add_argument('--external-file', action='append', default=[], metavar='NOMBRE=ARCHIVO')
    add_session_arguments(pipeline)
    pipeline.set_defaults(execute=_channel_pipeline)

    receiver = commands.add_parser('receive', help='Sincronizá y recuperá muestras de símbolo.')
    _synchronization_arguments(receiver)
    receiver.add_argument('--symbols', type=int, required=True)
    receiver.add_argument('--sps', type=int, required=True)
    receiver.add_argument('--gain', type=float, default=1.0)
    receiver.add_argument('--pilot-record', help='Identificador del piloto dentro de la misma sesión.')
    add_session_arguments(receiver)
    receiver.set_defaults(execute=_receive)

    decisions = commands.add_parser('decide', help='Obtené etiquetas por decisión dura.')
    _constellation_arguments(decisions)
    decisions.add_argument('--valid-bits', type=int)
    add_session_arguments(decisions)
    decisions.set_defaults(execute=_decide)

    quality = commands.add_parser('measure', help='Medí BER, SER y EVM de registros alineados.')
    quality.add_argument('--session', type=Path, required=True)
    quality.add_argument('--transmitted', required=True)
    quality.add_argument('--received', required=True)
    quality.add_argument('--reference-record')
    quality.add_argument('--observation-record')
    quality.add_argument('--tx-start', type=int, default=0)
    quality.add_argument('--rx-start', type=int, default=0)
    quality.add_argument('--symbols', type=int)
    add_output_arguments(quality)
    quality.set_defaults(execute=_measure)

    mc = commands.add_parser('monte-carlo', help='Compará tasas observadas con referencias AWGN.')
    _constellation_arguments(mc)
    mc.add_argument('--symbols', type=int, required=True)
    mc.add_argument('--eb-n0', type=float, required=True)
    mc.add_argument('--seed', type=int, default=2026)
    add_output_arguments(mc)
    mc.set_defaults(execute=_monte_carlo)

    sweep = commands.add_parser('sweep', help='Ejecutá, retomá o revisá un barrido guardado.')
    _bits_arguments(sweep, manual=False)
    _constellation_arguments(sweep)
    _pulse_arguments(sweep)
    _link_channel_arguments(sweep)
    sweep.add_argument('--axis', action='append', default=[], help='Parámetro y valores. Ejemplo: eb_n0_db=0,2,4,6.')
    sweep.add_argument('--seed-policy', choices=('per_run', 'common'), default='per_run')
    sweep.add_argument('--inspect', action='store_true', help='Verificá el catálogo existente y sus archivos.')
    sweep.add_argument('--csv', type=Path, help='Exportá las corridas verificadas a una tabla.')
    add_output_arguments(sweep)
    sweep.set_defaults(execute=_sweep)
    return run_command(parser, argv, None, 'No se pudo completar la operación de comunicaciones')
