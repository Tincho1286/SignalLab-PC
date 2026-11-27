"""Headless commands for stochastic processes and their realizations."""

from argparse import ArgumentParser
from pathlib import Path

from . import session
from .cli_session import add_output_arguments, add_session_arguments, load_input, load_signal_file, run_command, timeout_seconds
from .input_files import decode_finite_json
from .project import Project
from .statistics_results import store_statistics
from .stochastic_covariance import METHODS, covariance_matrix, ensemble_moments, estimate_correlation
from .stochastic_noise import NOISES, Noise, generate_noise, noise_spectrum, store_noise
from .stochastic_processes import PROCESSES, Process, generate_process, process_moments, process_transition, store_processes


def _inspect(args, context):
    context.checkpoint()
    parameters = decode_finite_json(args.parameters)
    if args.family in NOISES:
        if args.first is not None or args.second is not None:
            raise ValueError('Las posiciones temporales se indican al consultar una transición de proceso.')
        model = Noise(args.family, parameters)
        spectrum = noise_spectrum(model, 257 if args.bins is None else args.bins, rate=args.rate, execution=context)
        return {'model': model.document(), 'variance': spectrum.metadata['variance'],
                'density_convention': 'bilateral por Hz', 'sidedness': 'two-sided',
                'start_hz': spectrum.origin, 'step_hz': spectrum.step, 'density': spectrum.values.real.tolist()}
    model = Process(args.family, parameters)
    if args.bins is not None:
        raise ValueError('La cantidad de bins se indica al consultar la densidad de ruido.')
    first = 0 if args.first is None else args.first
    second = 1 if args.second is None else args.second
    moments = process_moments(model, first, second, rate=args.rate, execution=context)
    transition = process_transition(model, abs(second-first), rate=args.rate, execution=context)
    return {'moments': moments, 'transition': transition}


def _generate(args, context):
    context.checkpoint()
    parameters = decode_finite_json(args.parameters)
    if args.family in NOISES:
        model, generate, store = Noise(args.family, parameters), generate_noise, store_noise
    else:
        model, generate, store = Process(args.family, parameters), generate_process, store_processes
    records = generate(model, args.count, args.seed, replicas=args.replicas, origin=args.origin,
                       rate=args.rate, execution=context)
    project = Project()
    parent, ids = store(project, model.document(), records, context)
    session.save(args.output, project, session.empty_workspace(), checkpoint=context.checkpoint)
    return {'model_id': parent, 'result_ids': ids}


def _save_analysis(args, project, workspace, result, records, operation, context):
    inputs = tuple((record, key, ()) for record, key in records)
    keys, result_id = store_statistics(project, result, inputs, operation, execution=context)
    session.save(args.output, project, workspace, checkpoint=context.checkpoint)
    return {'source_ids': keys, 'result_id': result_id}


def _correlate(args, context):
    project, workspace, first = load_input(args, context)
    records = [(first, args.record)]
    second = None
    if args.second_record is not None:
        if args.session is None:
            raise ValueError('La segunda referencia requiere una sesión de entrada.')
        second = project.get(args.second_record)
        records.append((second, args.second_record))
    elif args.second_signal is not None:
        if args.second_signal.resolve() == args.output.resolve():
            raise ValueError('Elegí una salida distinta de la segunda señal de entrada.')
        second = load_signal_file(args.second_signal, context)
        records.append((second, None))
    result = estimate_correlation(first, second, max_lag=args.max_lag, remove_mean=args.center,
                                  denominator=args.divisor, normalize=args.normalize, method=args.method, execution=context)
    return _save_analysis(args, project, workspace, result, records, result.name, context)


def _ensemble(args, context):
    project, workspace = session.load(args.session, checkpoint=context.checkpoint)
    if len(set(args.records)) != len(args.records):
        raise ValueError('Seleccioná registros distintos del proyecto.')
    records = [(project.get(key), key) for key in args.records]
    signals = [record for record, _ in records]
    if args.analysis == 'matrix':
        result = covariance_matrix(signals, sample=not args.population, execution=context)
        title = 'Matriz de covarianza'
    else:
        if not args.independent:
            raise ValueError('Confirmá la independencia entre trayectorias con --independent.')
        result = ensemble_moments(signals, args.first, args.second, sample=not args.population, execution=context)
        title = 'Momentos de conjunto'
    return _save_analysis(args, project, workspace, result, records, title, context)


def main(argv):
    parser = ArgumentParser(prog='signallab-pc stochastic')
    commands = parser.add_subparsers(required=True)
    inspect = commands.add_parser('inspect', help='Calcular propiedades de un proceso o la PSD de un ruido.')
    inspect.add_argument('--first', type=int, help='Primera posición desde el inicio (por defecto 0).')
    inspect.add_argument('--second', type=int, help='Segunda posición desde el inicio (por defecto 1).')
    inspect.add_argument('--bins', type=int, help='Bins de la densidad bilateral de ruido (por defecto 257).')
    inspect.add_argument('--max-work-bytes', type=int)
    inspect.add_argument('--timeout', type=timeout_seconds)
    inspect.set_defaults(execute=_inspect)
    generate = commands.add_parser('generate', help='Guardar trayectorias reproducibles.')
    add_output_arguments(generate)
    generate.add_argument('--count', type=int, required=True)
    generate.add_argument('--seed', type=int, required=True)
    generate.add_argument('--replicas', type=int, default=1)
    generate.add_argument('--origin', type=int, default=0)
    generate.set_defaults(execute=_generate)
    correlation = commands.add_parser('correlate', help='Estimar correlación temporal auto o cruzada.')
    correlation.set_defaults(execute=_correlate)
    add_session_arguments(correlation)
    second = correlation.add_mutually_exclusive_group()
    second.add_argument('--second-record')
    second.add_argument('--second-signal', type=Path)
    correlation.add_argument('--max-lag', type=int)
    correlation.add_argument('--center', action='store_true', help='Restar las medias para estimar covarianza.')
    correlation.add_argument('--divisor', default='N', choices=('N', 'overlap'))
    correlation.add_argument('--normalize', action='store_true')
    correlation.add_argument('--method', default='auto', choices=METHODS)
    matrix = commands.add_parser('matrix', help='Estimar matrices de covarianza de canales.')
    ensemble = commands.add_parser('ensemble', help='Comparar realizaciones independientes en dos posiciones.')
    ensemble.add_argument('--first', type=int, default=0)
    ensemble.add_argument('--second', type=int, default=1)
    ensemble.add_argument('--independent', action='store_true')
    for name, command in [('matrix',matrix),('ensemble',ensemble)]:
        command.set_defaults(execute=_ensemble, analysis=name)
        command.add_argument('--session', type=Path, required=True)
        command.add_argument('--records', nargs='+', required=True)
        command.add_argument('--population', action='store_true', help='Dividir por N para describir los datos observados.')
        add_output_arguments(command)
    for command in (inspect, generate):
        command.add_argument('--family', choices=(*PROCESSES, *NOISES), required=True)
        command.add_argument('--parameters', required=True, help='Objeto JSON de parámetros.')
        command.add_argument('--rate', type=float, help='Frecuencia de muestreo en Hz del proceso.')
    return run_command(parser, argv, None, 'No se pudo completar la operación estocástica')
