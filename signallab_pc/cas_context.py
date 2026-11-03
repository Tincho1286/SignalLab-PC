"""Frequency-coordinate context across CAS results; never unit conversion."""
from copy import deepcopy
import ast
import sympy as sp

REWRITES={'simplify','expand','factor','cancel','together','apart','trigsimp','expand_trig','powsimp','exp2trig','trig2exp','ans'}

def remember(state,cell,context):
    state.setdefault('result_contexts',{})[str(cell)]=deepcopy(context)

def imported(data,value,notices):
    unit=data.get('frequency_units','')
    if data.get('variable',data.get('coordinate_variable'))!='w':return {}
    if unit not in ('rad/s','rad/muestra','incompatible') or not isinstance(value,sp.Expr):return {}
    return dict(frequency_units=unit,coordinate_variable='w',frequency_condition=data.get('frequency_condition','True'),origin_conditions=list(notices))

def combine(calculator,value,source,notices):
    contexts=[c for c in calculator.contexts if c.get('frequency_units')]
    if not contexts or not isinstance(value,sp.Expr):return {}
    original=list(dict.fromkeys(str(v) for c in contexts for v in c.get('origin_conditions',())))
    notices.extend(v for v in original if v not in notices)
    units={c['frequency_units'] for c in contexts}
    if len(units)!=1 or not units<= {'rad/s','rad/muestra'}:
        notices.append('Los resultados de origen usan rad/s y rad/muestra. No se asigna una unidad común ni se convierte la frecuencia automáticamente.');return dict(frequency_units='incompatible',coordinate_variable='w',origin_conditions=original)
    from .cas_engine import normalize
    try:
        tree=ast.parse(normalize(source,calculator.functions,calculator.variables),mode='eval')
        calls={node.func.id.lower() for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name)}
        rewrite=calls<=REWRITES
    except (SyntaxError,ValueError):rewrite=False
    has_w=any(str(v)=='w' for v in value.free_symbols)
    if not rewrite and not has_w:return {}
    condition='True'
    if rewrite:
        from .symbolic import parse
        condition=str(sp.And(*[parse(c.get('frequency_condition','True')) for c in contexts],*calculator.domain_restrictions))
        if condition!='True':notices.append('Condición de frecuencia conservada: '+condition+'. No se completan automáticamente las posiciones excluidas.')
    else:notices.append('Se conservan las condiciones de origen como referencia. Esta operación CAS modifica la definición; no se certifica automáticamente el dominio de la respuesta resultante.')
    return dict(frequency_units=next(iter(units)),coordinate_variable='w',frequency_condition=condition,origin_conditions=original,context_rewrite=rewrite)
