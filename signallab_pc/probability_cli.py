"""Headless console access to the statistical distribution services."""

from argparse import ArgumentParser

import numpy as np

from . import session
from .cli_session import add_output_arguments, run_command, timeout_seconds
from .input_files import decode_finite_json
from .multivariate_probability import (
    Gaussian, Multinomial, gaussian_condition, gaussian_density, gaussian_marginal,
    generate_gaussian, generate_multinomial,
)
from .probability import (
    Distribution, FAMILIES, distribution_value, generate_realizations, interval_probability,
    moment, population, store_realizations,
)
from .project import Project


def _number_parts(document):
    if not isinstance(document, dict):
        return document
    if set(document) != {'real', 'imag'}:
        raise ValueError('Una matriz compleja usa los campos real e imag.')
    real = np.asarray(document['real'], dtype=float)
    imag = np.asarray(document['imag'], dtype=float)
    if real.shape != imag.shape:
        raise ValueError('Las componentes real e imaginaria deben tener la misma forma.')
    return real + 1j * imag


def _model(args):
    data = decode_finite_json(args.parameters)
    if not isinstance(data, dict):
        raise ValueError('Los parámetros deben formar un objeto JSON.')
    if args.family == 'multinomial':
        return Multinomial(**data)
    if args.family == 'multivariate_normal':
        for key in ('mean', 'covariance', 'pseudocovariance'):
            if key in data:
                data[key] = _number_parts(data[key])
        return Gaussian(**data)
    return Distribution(args.family, data)


def _inspect(args, context):
    model = _model(args)
    context.checkpoint()
    operation = args.function
    if isinstance(model, Distribution):
        if operation == 'population':
            result = population(model)
        elif operation == 'interval':
            result = interval_probability(model, args.argument, args.upper)
        elif operation == 'moment':
            result = moment(model, args.order)
        else:
            result = distribution_value(model, operation, args.argument)
    elif isinstance(model, Multinomial):
        if operation == 'population':
            result = model.population()
        elif operation == 'density':
            result = model.mass(decode_finite_json(args.observation))
        elif operation == 'marginal':
            if len(args.components) != 1:
                raise ValueError('El marginal multinomial requiere una categoría.')
            result = population(model.marginal(args.components[0]))
        elif operation == 'conditional':
            result = model.condition(args.components, decode_finite_json(args.observation)).population()
        else:
            raise ValueError('Elegí una operación conjunta multinomial.')
    elif operation == 'population':
        result = model.document()
    elif operation == 'density':
        result = gaussian_density(model, _number_parts(decode_finite_json(args.observation)))
    elif operation == 'marginal':
        result = gaussian_marginal(model, args.components).document()
    elif operation == 'conditional':
        result = gaussian_condition(model, args.components,
                                    _number_parts(decode_finite_json(args.observation)), context).document()
    else:
        raise ValueError('Elegí una operación conjunta gaussiana.')
    context.checkpoint()
    return {'distribution': model.document(), 'operation': operation, 'result': result}


def _generate(args, context):
    model = _model(args)
    generator = {Distribution: generate_realizations, Gaussian: generate_gaussian,
                 Multinomial: generate_multinomial}[type(model)]
    records = generator(model, args.count, args.seed, replicas=args.replicas, origin=args.origin,
                        rate=args.rate, execution=context)
    project = Project()
    parent, ids = store_realizations(project, model.document(), records, context)
    session.save(args.output, project, session.empty_workspace(), checkpoint=context.checkpoint)
    return {'model_id': parent, 'result_ids': ids}


def main(argv):
    parser = ArgumentParser(prog='signallab-pc probability')
    commands = parser.add_subparsers(required=True)
    inspect = commands.add_parser('inspect', help='Evaluar una distribución y sus propiedades.')
    inspect.add_argument('--function', default='population',
                         choices=('population', 'density', 'log_density', 'cdf', 'log_cdf',
                                  'survival', 'log_survival', 'quantile', 'interval', 'moment',
                                  'marginal', 'conditional'))
    inspect.add_argument('--argument', type=float)
    inspect.add_argument('--upper', type=float)
    inspect.add_argument('--order', type=int)
    inspect.add_argument('--observation', default='null', help='Observación conjunta JSON.')
    inspect.add_argument('--components', type=int, nargs='+', default=())
    inspect.add_argument('--max-work-bytes', type=int)
    inspect.add_argument('--timeout', type=timeout_seconds)
    inspect.set_defaults(execute=_inspect)
    generate = commands.add_parser('generate', help='Guardar realizaciones como sesión o SLPROJ.')
    add_output_arguments(generate)
    generate.add_argument('--count', type=int, required=True)
    generate.add_argument('--seed', type=int, required=True)
    generate.add_argument('--replicas', type=int, default=1)
    generate.add_argument('--origin', type=int, default=0)
    generate.add_argument('--rate', type=float, help='Frecuencia de muestreo en Hz, si corresponde.')
    generate.set_defaults(execute=_generate)
    for command in (inspect, generate):
        command.add_argument('--family', choices=(*FAMILIES, 'multivariate_normal', 'multinomial'), required=True)
        command.add_argument('--parameters', required=True, help='Objeto JSON de parámetros.')
    return run_command(parser, argv, None, 'No se pudo completar la operación de probabilidad')
