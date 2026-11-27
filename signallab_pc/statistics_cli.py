"""Console entry points for analyses of sampled records."""

from argparse import ArgumentParser

from . import session
from .cli_session import add_session_arguments, load_input, run_command
from .descriptive_statistics import PROJECTIONS, describe_record
from .input_files import decode_finite_json
from .operation_provenance import settings_digest
from .probability import Distribution, FAMILIES


def _describe(args, context):
    if (args.reference_family is None) != (args.reference_parameters is None):
        raise ValueError('Indicá juntos --reference-family y --reference-parameters.')
    project, workspace, source = load_input(args, context)
    reference = None
    if args.reference_family is not None:
        reference = Distribution(args.reference_family, decode_finite_json(args.reference_parameters))
    result = describe_record(source, args.projection, probabilities=args.quantiles,
                             diagnostics=args.diagnostics or reference is not None, reference=reference,
                             qq_points=args.qq_points, execution=context)
    source_digest = result['input_sha256']
    report_digest = settings_digest(['calculation', result])
    with project.stage_records(before_commit=context.checkpoint) as staged:
        parent = args.record or staged.add(source, operation='Entrada estadística',
                                           verification=(source_digest, (), context.checkpoint))
        record = staged.add(result, title='Estadísticas de ' + source.name,
                            operation='Estadística descriptiva', parents=(parent,),
                            verification=(report_digest, (source_digest,), context.checkpoint))
    session.save(args.output, project, workspace, checkpoint=context.checkpoint)
    return {'source_id': parent, 'result_id': record}


def main(argv):
    parser = ArgumentParser(prog='signallab-pc statistics')
    commands = parser.add_subparsers(required=True)
    describe = commands.add_parser('describe', help='Resumir y guardar la estadística de un registro.')
    add_session_arguments(describe)
    describe.add_argument('--projection', default='real', choices=PROJECTIONS)
    describe.add_argument('--quantiles', nargs='+', type=float, default=(.05, .25, .5, .75, .95))
    describe.add_argument('--diagnostics', action='store_true', help='Incluir CDF, CCDF y diagrama de caja.')
    describe.add_argument('--qq-points', type=int, default=257)
    describe.add_argument('--reference-family', choices=tuple(FAMILIES))
    describe.add_argument('--reference-parameters')
    return run_command(parser, argv, _describe, 'No se pudo completar el análisis estadístico')
