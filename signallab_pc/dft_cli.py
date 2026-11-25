"""Headless entry point for the DFT application boundary."""

import argparse
import json
import math
from pathlib import Path
import signal
import sys
from threading import Event
from time import monotonic

from . import session
from .dft_application import DFTExecution, DFTRequest, calculate_dft, store_dft
from .jobs import OperationCancelled
from .project import Project
from .storage import load_json


def timeout_seconds(value):
    seconds = float(value)
    if not math.isfinite(seconds) or seconds <= 0:
        raise argparse.ArgumentTypeError('Ingresá un plazo positivo y finito en segundos.')
    return seconds


def execute(args, execution):
    execution.checkpoint()
    if args.session is not None:
        project, workspace = session.load(args.session)
        source = project.get(args.record)
    else:
        if args.signal.resolve() == args.output.resolve():
            raise ValueError('Elegí un archivo de sesión distinto de la señal de entrada.')
        source = load_json(args.signal)
        project, workspace = Project(), session.empty_workspace()
    execution.checkpoint()
    request = DFTRequest(source, args.length, args.order == 'centered', args.phase_reference)
    result = calculate_dft(request, execution)
    source_id, result_id = store_dft(
        project, result, source_id=args.record, source=source if args.record is None else None,
        execution=execution)
    session.save(args.output, project, workspace, before_commit=execution.checkpoint)
    return {'source_id': source_id, 'result_id': result_id,
            'length': result.provenance.length, 'estimated_work_bytes': result.estimated_work_bytes}


def main(argv):
    parser = argparse.ArgumentParser(prog='signallab-pc dft',
                                     description='Calculá una DFT y guardala en una sesión SignalLab.')
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--signal', type=Path, help='Archivo JSON de una señal de SignalLab.')
    source.add_argument('--session', type=Path, help='Proyecto o sesión SignalLab existente.')
    parser.add_argument('--record', help='Identificador de la señal dentro de --session.')
    parser.add_argument('--output', type=Path, required=True, help='Ruta de la sesión resultante.')
    parser.add_argument('--length', type=int, help='N de la DFT. Por defecto, longitud natural.')
    parser.add_argument('--order', choices=('centered', 'bins'), default='centered')
    parser.add_argument('--phase-reference', choices=('sample_indices', 'record_offset'),
                        default='sample_indices')
    parser.add_argument('--max-work-bytes', type=int, help='Presupuesto estimado de memoria de la DFT.')
    parser.add_argument('--timeout', type=timeout_seconds, help='Plazo cooperativo en segundos.')
    args = parser.parse_args(argv)
    if (args.record is None) != (args.session is None) or args.record == '':
        parser.error('--session requiere --record, y --record sólo se usa con --session.')

    cancel = Event()
    previous = signal.signal(signal.SIGINT, lambda *_: cancel.set())
    try:
        deadline = monotonic() + args.timeout if args.timeout is not None else None
        execution = DFTExecution(args.max_work_bytes, deadline, cancel)
        receipt = execute(args, execution)
    except OperationCancelled as error:
        print(str(error), file=sys.stderr)
        return 130
    except (OSError, ValueError, TypeError, MemoryError, FloatingPointError, KeyError) as error:
        print(f'No se pudo calcular la DFT: {error}', file=sys.stderr)
        return 1
    finally:
        signal.signal(signal.SIGINT, previous)
    print(json.dumps(receipt))
    return 0
