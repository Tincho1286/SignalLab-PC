"""Execute the same RF operations used by the Workbench without importing Qt."""

from argparse import ArgumentParser
from pathlib import Path

from . import session
from .cli_session import add_output_arguments, load_signal_file, run_command
from .input_files import read_json
from .model import Signal
from .project import Project
from .rf_application import RFRequest, run_rf, store_rf
from .rf_storage import load_network
from .touchstone import read_touchstone


def _execute(args, context):
    locations=[args.request,*args.network]
    optional=(args.source_session,args.signal)
    if any(args.output.resolve()==path.resolve() for path in (*locations,*filter(None,optional))):
        raise ValueError('Usá un archivo de salida distinto de las entradas.')
    if bool(args.source_session)!=bool(args.record_id):
        raise ValueError('Indicá juntos --source-session y uno o más --record-id.')
    request=RFRequest.from_document(read_json(args.request,checkpoint=context.checkpoint))
    sources=[]
    ids=[]
    project,workspace=Project(),session.empty_workspace()
    if args.source_session:
        project,workspace=session.load(args.source_session,checkpoint=context.checkpoint)
        for key in args.record_id:
            value=project.get(key)
            sources.append(value if isinstance(value,Signal) else load_network(project,key,context=context))
            ids.append(key)
    for path in args.network:
        sources.append(read_touchstone(path,context=context))
        ids.append(None)
    if args.signal:
        sources.append(load_signal_file(args.signal,context))
        ids.append(None)
    result=run_rf(request,sources,context=context)
    receipt=store_rf(project,result,source_ids=ids,context=context)
    session.save(args.output,project,workspace,before_commit=context.checkpoint,checkpoint=context.checkpoint)
    receipt['request_sha256']=result.document()['request_sha256']
    return receipt


def main(argv):
    parser=ArgumentParser(prog='signallab-pc rf',description='Ejecutar una solicitud RF o Fourier avanzada y guardar el proyecto.')
    parser.add_argument('--request',type=Path,required=True,help='Solicitud JSON con schema, operation y parameters.')
    parser.add_argument('--network',type=Path,action='append',default=[],help='Archivo Touchstone de entrada.')
    parser.add_argument('--signal',type=Path,help='Señal de entrada JSON o SLBIN.')
    parser.add_argument('--source-session',type=Path,help='Proyecto o sesión de entrada.')
    parser.add_argument('--record-id',action='append',default=[],help='Registro de entrada en el proyecto.')
    add_output_arguments(parser)
    return run_command(parser,argv,_execute,'No se pudo completar la operación RF')
