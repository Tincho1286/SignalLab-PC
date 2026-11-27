"""Headless commands for stochastic processes and their realizations."""

from argparse import ArgumentParser

from . import session
from .cli_session import add_output_arguments, run_command, timeout_seconds
from .input_files import decode_finite_json
from .project import Project
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
    for command in (inspect, generate):
        command.add_argument('--family', choices=(*PROCESSES, *NOISES), required=True)
        command.add_argument('--parameters', required=True, help='Objeto JSON de parámetros.')
        command.add_argument('--rate', type=float, help='Frecuencia de muestreo en Hz del proceso.')
    return run_command(parser, argv, None, 'No se pudo completar la operación estocástica')
