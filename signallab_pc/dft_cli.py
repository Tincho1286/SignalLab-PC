"""Headless entry point for the DFT application boundary."""

import argparse

from . import session
from .cli_session import add_session_arguments, load_input, run_command
from .dft_application import DFTRequest, calculate_dft, store_dft


def execute(args, execution):
    project, workspace, source = load_input(args, execution)
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
    add_session_arguments(parser)
    parser.add_argument('--length', type=int, help='N de la DFT. Por defecto, longitud natural.')
    parser.add_argument('--order', choices=('centered', 'bins'), default='centered')
    parser.add_argument('--phase-reference', choices=('sample_indices', 'record_offset'),
                        default='sample_indices')
    return run_command(parser, argv, execute, 'No se pudo calcular la DFT')
