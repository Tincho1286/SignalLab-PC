"""Keep a system's interpretation only through verified equivalent CAS expressions."""
from copy import deepcopy
import sympy as sp


def equivalent(one,two):
    # Compare over generic complex symbols, without importing the worksheet's
    # assumptions or using approximate numerical equality to assert identity.
    def canonical(value):
        value=value.xreplace({v:sp.Symbol(v.name) for v in value.free_symbols})
        return value.xreplace({v:sp.Rational(v) for v in value.atoms(sp.Float)})
    one,two=canonical(one),canonical(two)
    if one==two:return True
    count=sum(1 for _ in sp.preorder_traversal(one))+sum(1 for _ in sp.preorder_traversal(two))
    if count>400:return False
    symbols=one.free_symbols|two.free_symbols
    if one.is_rational_function(*symbols) and two.is_rational_function(*symbols):return sp.cancel(one-two)==0
    if count<=160:return sp.simplify(one-two)==0
    return False


def origin(record):
    """Retain the defining transform without recursively copying result journals."""
    current=record
    for _ in range(8):
        if not isinstance(current,dict):return None
        context=current.get('cas_answer',{}).get('system_context',{})
        nested=context.get('source_calculation') if context.get('preserved') else None
        if nested is None:nested=current.get('result',{}).get('source_calculation')
        if not isinstance(nested,dict):break
        current=nested
    if not isinstance(current,dict) or not isinstance(current.get('request'),dict):return None
    req_names=('operation','expression','lower','upper','domain','roc_spec','input_conditions','interpretation','roc','radius','laplace_roc','sigma')
    res_names=('result','transfer','output_variable','branches','evaluated','convergence_empty','boundary_dtft','condition','roc','roc_finite_plane','inverse_roc_hint','inverse_laplace_hint','frequency_units','model_kind')
    return {'request':{k:deepcopy(v) for k,v in current['request'].items() if k in req_names},
            'result':{k:deepcopy(v) for k,v in current.get('result',{}).items() if k in res_names}}


def invalidated():return {'system_context':dict(schema_version=1,preserved=False,domain=None,roc=None,period=None)}


def imported(data,value,notices):
    from .cas_engine import encode,restore
    from .filters import validate_roc
    from .system_clock import validate_period
    if not isinstance(value,sp.Expr):return {}
    context=data.get('system_context')
    if context is not None:
        if not isinstance(context,dict) or context.get('schema_version')!=1:raise ValueError('Contexto de sistema CAS no compatible.')
        if not context.get('preserved'):return invalidated()
        if not equivalent(value,restore(context['expression'])):
            notices.append('La expresión cambió respecto del sistema de origen. Su ROC y su reloj no se asignan al resultado nuevo.')
            return invalidated()
        domain=context['domain'];roc=context.get('roc');period=context.get('period');source=context.get('source_calculation')
    else:
        variable=data.get('variable')
        domain=data.get('domain') if data.get('kind')=='system' else {'s':'analog','z':'digital'}.get(variable)
        if domain not in ('analog','digital'):return {}
        roc=data.get('roc',data.get('system_roc'));period=data.get('period');source=data.get('system_origin')
    if domain not in ('analog','digital'):raise ValueError('Dominio de sistema CAS inválido.')
    result=dict(schema_version=1,preserved=True,domain=domain,roc=validate_roc(roc,domain),period=validate_period(period,domain),expression=encode(value))
    if source is not None:result['source_calculation']=deepcopy(source)
    return {'system_context':result}


def combine(calculator,value,notices):
    from .cas_engine import restore
    contexts=[c['system_context'] for c in calculator.contexts if 'system_context' in c]
    if not contexts:return {}
    def refuse():
        notices.append('No se verificó que el resultado sea el mismo sistema de origen. La ROC y el período no se heredan: deben definirse para el sistema resultante.')
        return invalidated()
    if not isinstance(value,sp.Expr) or any(not c.get('preserved') for c in contexts):return refuse()
    reference=contexts[0]
    if any(any(c.get(k)!=reference.get(k) for k in ('domain','roc','period')) for c in contexts[1:]):
        notices.append('Los sistemas de origen tienen dominios, regiones de convergencia o períodos distintos. No se elige uno automáticamente.')
        return invalidated()
    if not all(equivalent(value,restore(c['expression'])) for c in contexts):return refuse()
    return {'system_context':deepcopy(reference)}


def record_context(record):
    if not isinstance(record,dict):return None
    answer=record.get('cas_answer')
    if not isinstance(answer,dict):return None
    context=answer.get('system_context')
    return context if isinstance(context,dict) else None
