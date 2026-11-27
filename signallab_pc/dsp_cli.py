"""Console access to the individual DSP application services."""

from argparse import ArgumentParser

from . import session
from .cli_session import add_output_arguments, add_session_arguments, load_input, run_command
from .dsp_application import (
    FIRDesignRequest, FIRRequest, IDFTRequest, PSDRequest, ResampleRequest, apply_fir,
    calculate_idft, design_fir, estimate_psd, resample, store_fir_design, store_signal,
)
from .filters import Transfer
from .project import Project


def _design(args, context):
    project = Project()
    design = design_fir(FIRDesignRequest(args.kind,args.taps,args.f1,args.f2,args.window,args.beta),context)
    model, specification = store_fir_design(project,design,execution=context)
    session.save(args.output,project,session.empty_workspace(),checkpoint=context.checkpoint)
    return {'result_id':model, 'specification_id':specification}


def _execute(args, context):
    project, workspace, source = load_input(args,context)
    filter_model = None
    if args.operation == 'idft':
        result = calculate_idft(IDFTRequest(source,not args.zero_origin),context)
    elif args.operation == 'fir':
        filter_model = project.get(args.filter_record) if args.filter_record else Transfer(args.coefficients,[1])
        if not isinstance(filter_model,Transfer):
            raise ValueError('El registro seleccionado debe ser un filtro.')
        result = apply_fir(FIRRequest(source,filter_model,args.mode),context)
    elif args.operation == 'resample':
        converted = resample(ResampleRequest(source,args.up,args.down,rate=args.rate,start=args.start,
                                             half_width=args.half_width,beta=args.beta,boundary=args.boundary,
                                             override_clock=args.override_clock,return_filter=True),context)
        result,filter_model = converted.signal,converted.antialias
    else:
        result = estimate_psd(PSDRequest(source,args.rate,args.method,args.segment,args.overlap,
                                         args.window,args.beta,args.remove_mean,args.sidedness,
                                         maximum_lag=args.max_lag,nfft=args.nfft,time_bandwidth=args.bandwidth,
                                         tapers=args.tapers,ar_order=args.ar_order),context)
    context.checkpoint()
    parent = args.record or project.add(source,operation='Entrada DSP')
    model_id = getattr(args,'filter_record',None)
    if filter_model is not None and model_id is None:
        model_id = project.add(filter_model,operation='Coeficientes FIR',
                               parents=(parent,) if args.operation=='resample' else ())
    parents = (parent,) if model_id is None else (parent,model_id)
    result_id = store_signal(project,result,parents=parents,execution=context)
    receipt = {'source_id':parent,'result_id':result_id,'filter_id':model_id}
    if getattr(args,'white_confidence',None) is not None:
        from .statistical_spectra import white_noise_confidence
        from .statistics_results import store_statistics
        bounds = white_noise_confidence(result,model=args.white_confidence,coverage=args.coverage,execution=context)
        _, key = store_statistics(project,bounds,((result,result_id,()),),'Intervalos de densidad',execution=context)
        receipt['confidence_id'] = key
    session.save(args.output,project,workspace,checkpoint=context.checkpoint)
    return receipt


def main(argv):
    parser = ArgumentParser(prog='signallab-pc dsp')
    commands = parser.add_subparsers(dest='operation',required=True)
    idft = commands.add_parser('idft')
    idft.add_argument('--zero-origin',action='store_true')
    fir = commands.add_parser('fir')
    coefficients = fir.add_mutually_exclusive_group(required=True)
    coefficients.add_argument('--coefficients',type=float,nargs='+')
    coefficients.add_argument('--filter-record',help='ID de un FIR guardado en --session.')
    fir.add_argument('--mode',choices=('same','full'),default='same')
    rate_change = commands.add_parser('resample')
    rate_change.add_argument('--up',type=int,required=True)
    rate_change.add_argument('--down',type=int,required=True)
    rate_change.add_argument('--rate',type=float)
    rate_change.add_argument('--start',type=float)
    rate_change.add_argument('--half-width',type=int,default=10)
    rate_change.add_argument('--beta',type=float,default=5.0)
    rate_change.add_argument('--boundary',choices=('zero','line'),default='zero')
    rate_change.add_argument('--override-clock',action='store_true')
    psd = commands.add_parser('psd')
    psd.add_argument('--rate',type=float)
    psd.add_argument('--method',choices=('welch','periodogram','legacy','bartlett','blackman_tukey','multitaper','ar'),default='welch')
    psd.add_argument('--segment',type=int,default=256)
    psd.add_argument('--overlap',type=int,default=128)
    psd.add_argument('--window',choices=('boxcar','hann','hamming','blackman','kaiser'),default='hann')
    psd.add_argument('--beta',type=float,default=5.0)
    psd.add_argument('--remove-mean',action='store_true')
    psd.add_argument('--max-lag',type=int,help='Retardo máximo en Blackman–Tukey.')
    psd.add_argument('--nfft',type=int,help='Bins para Blackman–Tukey, multitaper y AR.')
    psd.add_argument('--bandwidth',type=float,help='Producto tiempo-ancho de banda NW en multitaper.')
    psd.add_argument('--tapers',type=int,help='Cantidad de ventanas DPSS en multitaper.')
    psd.add_argument('--ar-order',type=int,help='Orden del estimador autorregresivo.')
    psd.add_argument('--sidedness',choices=('one-sided','two-sided'),default='two-sided')
    psd.add_argument('--white-confidence',choices=('real_gaussian_white','proper_complex_gaussian_white'),
                     help='Modelo gaussiano blanco de media cero para intervalos por bin.')
    psd.add_argument('--coverage',type=float,default=.95)
    for command in (idft,fir,rate_change,psd):
        add_session_arguments(command)
        command.set_defaults(execute=_execute)
    design = commands.add_parser('fir-design')
    add_output_arguments(design)
    design.add_argument('--kind',choices=('lowpass','highpass','bandpass','bandstop'),required=True)
    design.add_argument('--taps',type=int,required=True)
    design.add_argument('--f1',type=float,required=True,help='Corte en ciclos/muestra.')
    design.add_argument('--f2',type=float,help='Segundo corte en ciclos/muestra.')
    design.add_argument('--window',choices=('boxcar','hann','hamming','blackman','kaiser','bartlett'),default='hamming')
    design.add_argument('--beta',type=float,default=8.6)
    design.set_defaults(execute=_design)
    return run_command(parser,argv,None,'No se pudo completar la operación DSP')
