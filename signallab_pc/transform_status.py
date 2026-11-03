"""Common transform completion states; obtaining a formula is not a proof."""
import ast
from copy import deepcopy

OPERATIONS=frozenset(('z_expression','z_finite','z_inverse_expression','laplace','inverse_laplace','dtft_expression','inverse_dtft_expression','fourier_angular','inverse_fourier_angular'))
PENDING=frozenset(('Sum','Integral','LaplaceTransform','InverseLaplaceTransform','FourierTransform','InverseFourierTransform','Limit','Derivative'))


def merge_notes(*groups):
    records={}
    for group in groups:
        for item in group:
            key=tuple(str(item.get(name,'')) for name in ('expression','variable','point','value','method'))
            records[key]=deepcopy(item)
    return list(records.values())


def closed(text):
    try:tree=ast.parse(str(text).replace('^','**'),mode='eval')
    except SyntaxError:return False
    return not any(isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in PENDING or isinstance(node,ast.Name) and node.id in ('nan','zoo','oo') for node in ast.walk(tree))


def finalize(result):
    if 'result' not in result:return result
    branches=result.get('branches',[])
    valid=[b for b in branches if b.get('condition')!='False' and closed(b.get('expression',''))]
    empty=bool(result.get('convergence_empty')) or result.get('condition')=='False'
    complete=bool(result.get('evaluated',False)) and (bool(valid) if branches else closed(result['result'])) and not empty and len(valid)==len(branches)
    result['evaluated']=complete
    restricted=bool(valid) or any(result.get(name) not in (None,'','True','Todo el plano s finito','Todo z finito') for name in ('condition','roc','convergence','roc_finite_plane'))
    if empty:code,label='no_convergence',('DTFT disponible; sin anillo abierto de ROC' if result.get('boundary_dtft') else 'Sin región de convergencia')
    elif complete and restricted:code,label='conditional','Expresión obtenida con condiciones'
    elif complete:code,label='computed','Expresión obtenida'
    elif valid:code,label='partial','Resultado parcialmente resuelto'
    else:code,label='unresolved','Cálculo sin resolver'
    result['calculation_status']={'code':code,'label':label,'identity_verified':False,
        'scope':'Indica qué resolvió el motor y bajo qué condiciones; no constituye una comprobación independiente de la identidad.'}
    return result
