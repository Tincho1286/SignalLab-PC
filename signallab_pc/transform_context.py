"""Convergence hints shared by expression/system reuse actions."""
from copy import deepcopy


def result_roc(value):
    if not isinstance(value,dict):return None
    from .cas_system_context import record_context
    context=record_context(value)
    if context is not None:return deepcopy(context.get('roc')) if context.get('preserved') else None
    request=value.get('request',{});result=value.get('result',{})
    if 'roc_spec' in request:return deepcopy(request['roc_spec'])
    if request.get('operation')=='inverse_laplace':
        mode=request.get('laplace_roc','right')
        if mode in ('right','left'):return {'mode':mode}
        try:
            from .numeric_input import constant_value
            sigma=constant_value(request.get('sigma','0'))
            if not sigma.imag:return {'mode':'line','sigma':float(sigma.real)}
        except ValueError:pass
        return None
    hint=result.get('inverse_laplace_hint')
    if hint:
        if hint['laplace_roc'] in ('right','left'):return {'mode':hint['laplace_roc']}
        try:
            from .numeric_input import constant_value
            sigma=constant_value(hint['sigma'])
            if not sigma.imag:return {'mode':'line','sigma':float(sigma.real)}
        except ValueError:pass
        return None
    if request.get('operation')=='laplace' and request.get('interpretation')!='bilateral':return {'mode':'right'}
    if request.get('operation')=='z_inverse_expression':
        mode=request.get('roc','right')
        if mode in ('right','left'):return {'mode':mode}
        try:
            from .numeric_input import constant_value
            radius=constant_value(request.get('radius','1'))
            if not radius.imag and radius.real>0:return {'mode':'radius','radius':float(radius.real)}
        except ValueError:pass
        return None
    hint=result.get('inverse_roc_hint')
    if hint in ('right','left'):return {'mode':hint}
    if request.get('operation')=='z_finite' or 'roc_finite_plane' in result:return {'mode':'right'}
    return None


def result_period(value):
    from .cas_system_context import record_context
    from .system_clock import validate_period
    context=record_context(value)
    if context is not None:return validate_period(context.get('period'),context.get('domain')) if context.get('preserved') else None
    if not isinstance(value,dict):return None
    result=value.get('result',{})
    return validate_period(result.get('sample_period_s'))
