"""Frequency-coordinate context across CAS results; never unit conversion."""
from copy import deepcopy
import ast
import sympy as sp

REWRITES={'simplify','expand','factor','cancel','together','apart','trigsimp','expand_trig','powsimp','exp2trig','trig2exp','ans','sin','cos','exp','sinh','cosh','abs','re','im','conj'}

def remember(state,cell,context):
    state.setdefault('result_contexts',{})[str(cell)]=deepcopy(context)

def imported(data,value,notices):
    if data.get('variable',data.get('coordinate_variable'))!='w' or not isinstance(value,sp.Expr):return {}
    unit=data.get('frequency_units','')
    if unit not in ('','rad/s','rad/muestra','incompatible'):return {}
    return dict(frequency_units=unit,coordinate_variable='w',frequency_condition=data.get('frequency_condition','True'),origin_conditions=list(notices))

def frequency_assumptions(calculator):
    from .cas_assumptions import symbol
    from .cas_engine import restore
    from .symbolic import W
    entry=calculator.assumptions.get('w',{});value=symbol('w',calculator.assumptions);conditions=[]
    if value.is_integer is True:conditions.append(sp.Eq(W,sp.floor(W)))
    for flag,condition in [('positive',W>0),('negative',W<0),('nonnegative',W>=0),('nonpositive',W<=0)]:
        if getattr(value,'is_'+flag) is True:conditions.append(condition)
    if value.is_zero is True:conditions.append(sp.Eq(W,0))
    elif value.is_zero is False:conditions.append(sp.Ne(W,0))
    for text in entry.get('encoded_conditions',[]):
        condition=restore(text);conditions.append(condition.xreplace({v:W for v in condition.free_symbols if str(v)=='w'}))
    return conditions

def combine(calculator,value,source,notices):
    if not isinstance(value,sp.Expr):return {}
    contexts=[c for c in calculator.contexts if c.get('coordinate_variable')=='w']
    from .cas_engine import normalize
    try:
        tree=ast.parse(normalize(source,calculator.functions,calculator.variables),mode='eval')
        calls={node.func.id.lower() for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name)}
        rewrite=calls<=REWRITES
    except (SyntaxError,ValueError):rewrite=False
    has_w=any(str(v)=='w' for v in value.free_symbols)
    if not contexts and not has_w and not (rewrite and 'w' in calculator.referenced_axes):return {}
    original=list(dict.fromkeys(str(v) for c in contexts for v in c.get('origin_conditions',())))
    notices.extend(v for v in original if v not in notices)
    units={c['frequency_units'] for c in contexts if c.get('frequency_units')}
    if len(units)>1 or not units<= {'rad/s','rad/muestra'}:
        notices.append('Los resultados de origen usan unidades de frecuencia incompatibles. No se asigna una unidad común ni se convierte la frecuencia automáticamente.')
        return dict(frequency_units='incompatible',coordinate_variable='w',origin_conditions=original)
    if not rewrite and not has_w:return {}
    restrictions=frequency_assumptions(calculator)
    if rewrite:
        from .symbolic import parse
        restrictions.extend(parse(c.get('frequency_condition','True')) for c in contexts)
        restrictions.extend(calculator.domain_restrictions)
    else:notices.append('Se conservan las condiciones de origen como referencia. Esta operación CAS modifica la definición; no se certifica automáticamente el dominio de la respuesta resultante.')
    condition=str(sp.And(*restrictions))
    if condition!='True':notices.append('Condición de frecuencia conservada: '+condition+'. No se completan automáticamente las posiciones excluidas.')
    return dict(frequency_units=next(iter(units)) if units else '',coordinate_variable='w',frequency_condition=condition,origin_conditions=original,context_rewrite=rewrite)
