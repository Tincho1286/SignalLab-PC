"""Headless commands for stochastic processes and their realizations."""

from argparse import ArgumentParser

from . import session
from .cli_session import add_output_arguments, run_command, timeout_seconds
from .input_files import decode_finite_json
from .project import Project
from .stochastic_processes import PROCESSES, Process, generate_process, process_moments, process_transition, store_processes


def _inspect(args, context):
    context.checkpoint()
    model = Process(args.family, decode_finite_json(args.parameters))
    moments = process_moments(model, args.first, args.second, rate=args.rate, execution=context)
    transition = process_transition(model, abs(args.second-args.first), rate=args.rate, execution=context)
    return {'moments': moments, 'transition': transition}


def _generate(args, context):
    context.checkpoint()
    model = Process(args.family, decode_finite_json(args.parameters))
    records = generate_process(model, args.count, args.seed, replicas=args.replicas, origin=args.origin,
                               rate=args.rate, execution=context)
    project = Project()
    parent, ids = store_processes(project, model.document(), records, context)
    session.save(args.output, project, session.empty_workspace(), checkpoint=context.checkpoint)
    return {'model_id': parent, 'result_ids': ids}


def main(argv):
    parser = ArgumentParser(prog='signallab-pc stochastic')
    commands = parser.add_subparsers(required=True)
    inspect = commands.add_parser('inspect', help='Calcular momentos y transiciones de un proceso.')
    inspect.add_argument('--first', type=int, default=0, help='Primera posición desde el inicio.')
    inspect.add_argument('--second', type=int, default=1, help='Segunda posición desde el inicio.')
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
        command.add_argument('--family', choices=tuple(PROCESSES), required=True)
        command.add_argument('--parameters', required=True, help='Objeto JSON de parámetros.')
        command.add_argument('--rate', type=float, help='Frecuencia de muestreo en Hz del proceso.')
    return run_command(parser, argv, None, 'No se pudo completar la operación estocástica')
