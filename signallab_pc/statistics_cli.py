"""Console entry points for analyses of sampled records."""

from argparse import ArgumentParser
from pathlib import Path

from . import session
from .cli_session import add_session_arguments, load_input, load_signal_file, run_command
from .descriptive_statistics import PROJECTIONS, describe_record
from .input_files import decode_finite_json
from .probability import Distribution, FAMILIES
from .statistical_inference import FIT_FAMILIES, METHODS, fit_distribution, infer_record
from .statistics_results import store_statistics


def _reference(args):
    if (args.reference_family is None) != (args.reference_parameters is None):
        raise ValueError('Indicá juntos --reference-family y --reference-parameters.')
    if args.reference_family is not None:
        return Distribution(args.reference_family, decode_finite_json(args.reference_parameters))
    return None


def _describe(args, context):
    project, workspace, source = load_input(args, context)
    reference = _reference(args)
    result = describe_record(source, args.projection, probabilities=args.quantiles,
                             diagnostics=args.diagnostics or reference is not None, reference=reference,
                             qq_points=args.qq_points, execution=context)
    return _save(args, context, project, workspace, result, (source,), (args.record,), 'Estadística descriptiva')


def _save(args, context, project, workspace, result, sources, records, operation):
    inputs = tuple((source, key, ()) for source, key in zip(sources, records, strict=True))
    parents, record = store_statistics(project, result, inputs, operation, execution=context)
    session.save(args.output, project, workspace, checkpoint=context.checkpoint)
    receipt = {'source_id': parents[0], 'result_id': record}
    if len(parents) > 1:
        receipt['second_source_id'] = parents[1]
    return receipt


def _fit(args, context):
    project, workspace, source = load_input(args, context)
    result = fit_distribution(source, args.family, component=args.projection,
                              estimator=args.estimator, trials=args.trials, level=args.level,
                              iid=args.iid, execution=context)
    return _save(args, context, project, workspace, result, (source,), (args.record,), 'Ajuste de distribución')


def _infer(args, context):
    project, workspace, source = load_input(args, context)
    second = None
    if args.second_record is not None:
        if args.session is None or args.second_record == args.record:
            raise ValueError('Elegí otro registro de la misma sesión para la segunda muestra.')
        second = project.get(args.second_record)
    elif args.second_signal is not None:
        path = args.second_signal.resolve()
        if path == args.output.resolve() or args.signal is not None and path == args.signal.resolve():
            raise ValueError('La segunda señal requiere un archivo distinto de la primera señal y la salida.')
        second = load_signal_file(path, context)
    result = infer_record(source, args.method, iid=args.iid, component=args.projection, second=second,
                          null=args.null, level=args.level, alternative=args.alternative,
                          known_std=args.known_std, reference=_reference(args), lags=args.lags,
                          fitted_parameters=args.fitted_parameters, execution=context)
    sources = (source,) if second is None else (source, second)
    records = (args.record,) if second is None else (args.record, args.second_record)
    return _save(args, context, project, workspace, result, sources, records, 'Inferencia estadística')


def main(argv):
    parser = ArgumentParser(prog='signallab-pc statistics')
    commands = parser.add_subparsers(required=True)
    describe = commands.add_parser('describe', help='Resumir y guardar la estadística de un registro.')
    describe.set_defaults(execute=_describe)
    describe.add_argument('--quantiles', nargs='+', type=float, default=(.05, .25, .5, .75, .95))
    describe.add_argument('--diagnostics', action='store_true', help='Incluir CDF, CCDF y diagrama de caja.')
    describe.add_argument('--qq-points', type=int, default=257)
    fit = commands.add_parser('fit', help='Estimar parámetros de una familia univariada.')
    fit.add_argument('--family', required=True, choices=tuple(FIT_FAMILIES))
    fit.add_argument('--estimator', choices=('ml', 'moments'), default='ml')
    fit.add_argument('--trials', type=int, help='Cantidad de ensayos conocida en el ajuste binomial.')
    fit.add_argument('--level', type=float, help='Nivel de confianza bilateral (requiere --iid).')
    fit.add_argument('--iid', action='store_true', help='Confirmar independencia para los intervalos.')
    fit.set_defaults(execute=_fit)
    infer = commands.add_parser('infer', help='Contrastar hipótesis y guardar el informe.')
    infer.add_argument('--method', required=True, choices=tuple(METHODS))
    infer.add_argument('--iid', action='store_true', help='Declarar independencia bajo el modelo de muestreo.')
    infer.add_argument('--null', type=float, help='Valor de la hipótesis nula si corresponde.')
    infer.add_argument('--known-std', type=float)
    infer.add_argument('--level', type=float, default=.95)
    infer.add_argument('--alternative', default='two-sided', choices=('two-sided', 'less', 'greater'))
    infer.add_argument('--lags', type=int)
    infer.add_argument('--fitted-parameters', type=int)
    second = infer.add_mutually_exclusive_group()
    second.add_argument('--second-signal', type=Path)
    second.add_argument('--second-record')
    infer.set_defaults(execute=_infer)
    for command in (describe, infer):
        command.add_argument('--reference-family', choices=tuple(FAMILIES))
        command.add_argument('--reference-parameters')
    for command in (describe, fit, infer):
        add_session_arguments(command)
        command.add_argument('--projection', default='real', choices=PROJECTIONS)
    return run_command(parser, argv, None, 'No se pudo completar el análisis estadístico')
