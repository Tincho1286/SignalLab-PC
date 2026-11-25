"""Shared session input and cooperative CLI execution."""

import argparse
import json
import math
from pathlib import Path
import signal
import sys
from threading import Event
from time import monotonic

from . import session
from .execution import ExecutionContext
from .jobs import OperationCancelled
from .model import Signal
from .project import Project
from .storage import load_json


def timeout_seconds(value):
    seconds = float(value)
    if not math.isfinite(seconds) or seconds <= 0:
        raise argparse.ArgumentTypeError('Ingresá un plazo positivo y finito en segundos.')
    return seconds


def load_input(args, execution):
    execution.checkpoint()
    if args.session is not None:
        project, workspace = session.load(args.session)
        source = project.get(args.record)
    else:
        if args.signal.resolve() == args.output.resolve():
            raise ValueError('Elegí un archivo de sesión distinto de la señal de entrada.')
        if args.signal.suffix.lower() == '.slbin':
            from .scientific_storage import load_binary_signal
            source = load_binary_signal(args.signal, execution)
        else:
            source = load_json(args.signal)
        project, workspace = Project(), session.empty_workspace()
    if not isinstance(source, Signal):
        raise ValueError('El registro seleccionado debe ser una señal.')
    execution.checkpoint()
    return project, workspace, source


def add_session_arguments(parser):
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--signal', type=Path, help='Señal SignalLab en JSON o .slbin.')
    source.add_argument('--session', type=Path, help='Proyecto o sesión SignalLab existente.')
    parser.add_argument('--record', help='Identificador de la señal dentro de --session.')
    add_output_arguments(parser)


def add_output_arguments(parser):
    parser.add_argument('--output', type=Path, required=True, help='Ruta de la sesión resultante.')
    parser.add_argument('--max-work-bytes', type=int, help='Presupuesto estimado de memoria en bytes.')
    parser.add_argument('--timeout', type=timeout_seconds, help='Plazo cooperativo en segundos.')


def run_command(parser, argv, execute, failure):
    args = parser.parse_args(argv)
    if hasattr(args, 'record') and ((args.record is None) != (args.session is None) or args.record == ''):
        parser.error('--session requiere --record, y --record sólo se usa con --session.')

    cancel = Event()
    previous = signal.signal(signal.SIGINT, lambda *_: cancel.set())
    try:
        deadline = monotonic() + args.timeout if args.timeout is not None else None
        execution = ExecutionContext(args.max_work_bytes, deadline, cancel)
        receipt = (execute or args.execute)(args, execution)
    except OperationCancelled as error:
        print(str(error), file=sys.stderr)
        return 130
    except (OSError, ValueError, TypeError, MemoryError, FloatingPointError, KeyError) as error:
        print(f'{failure}: {error}', file=sys.stderr)
        return 1
    finally:
        signal.signal(signal.SIGINT, previous)
    print(json.dumps(receipt))
    return 0
