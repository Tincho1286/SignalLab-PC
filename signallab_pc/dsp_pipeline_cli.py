"""Command-line adapter for the fixed DSP demonstration."""

from argparse import ArgumentParser
from dataclasses import asdict

from . import session
from .cli_session import add_session_arguments, load_input, run_command
from .dsp_application import ResampleRequest
from .dsp_pipeline import DSPPipelineRequest, run_pipeline, store_pipeline
from .filters import Transfer


def execute(args, execution):
    project, workspace, signal = load_input(args, execution)
    conversion = ResampleRequest(signal, args.up, args.down, rate=args.rate, return_filter=True)
    request = DSPPipelineRequest(conversion, Transfer(args.fir, [1]), fir_mode=args.fir_mode,
                                 dft_length=args.length, psd_method=args.psd_method,
                                 psd_segment=args.segment, psd_overlap=args.overlap, psd_window=args.window)
    result = run_pipeline(request, execution)
    ids = store_pipeline(project, request, result, source_id=args.record, execution=execution)
    session.save(args.output, project, workspace, before_commit=execution.checkpoint)
    return asdict(ids)


def main(argv):
    parser = ArgumentParser(prog='signallab-pc dsp-pipeline',
                            description='Guardá un flujo de cambio de tasa, FIR, DFT y PSD.')
    add_session_arguments(parser)
    parser.add_argument('--up', type=int, required=True)
    parser.add_argument('--down', type=int, required=True)
    parser.add_argument('--rate', type=float)
    parser.add_argument('--fir', type=float, nargs='+', required=True)
    parser.add_argument('--fir-mode', choices=('same', 'full'), default='same')
    parser.add_argument('--length', type=int)
    parser.add_argument('--psd-method', choices=('welch', 'periodogram'), default='welch')
    parser.add_argument('--segment', type=int)
    parser.add_argument('--overlap', type=int)
    parser.add_argument('--window', choices=('boxcar','hann','hamming','blackman','kaiser'), default='hann')
    return run_command(parser, argv, execute, 'No se pudo completar el flujo DSP')
