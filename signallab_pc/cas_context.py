"""Frequency-coordinate context across CAS results; never unit conversion."""
from copy import deepcopy
import sympy as sp

def coordinate_domain(variable):
    if variable in ('n','k'):return sp.S.Integers
    if variable in ('t','w','tau'):return sp.S.Reals
    return None

def remember(state,cell,context):
    state.setdefault('result_contexts',{})[str(cell)]=deepcopy(context)

def imported(data,value,notices):
    from .cas_system_context import imported as imported_system
    context=imported_system(data,value,notices)
    condition=sp.true
    if data.get('domain_condition'):
        from .cas_engine import restore
        condition=restore(data['domain_condition'])
        if not isinstance(condition,sp.logic.boolalg.Boolean):raise ValueError('Condición de dominio CAS inválida.')
        from .cas_domains import intrinsic_system_domain
        context.update(domain_condition=data['domain_condition'],domain_symbols=sorted({s.name for s in condition.free_symbols}),
                       domain_condition_implicit=intrinsic_system_domain(value,condition),
                       domain_condition_analysis=intrinsic_system_domain(value,condition,analysis=True))
    variable=data.get('variable') or data.get('coordinate_variable')
    if not isinstance(value,sp.Expr) or coordinate_domain(variable) is None:return context
    if variable!='w':return {**context,'coordinate_variable':variable}
    if condition is sp.true and data.get('frequency_condition') not in (None,'True'):
        from .symbolic import parse
        condition=sp.And(condition,parse(data['frequency_condition']))
    condition=frequency_condition(condition)
    unit=data.get('frequency_units','')
    if unit not in ('','rad/s','rad/muestra','incompatible'):return context
    return {**context,**dict(frequency_units=unit,coordinate_variable='w',frequency_condition=str(condition),
                              origin_conditions=list(notices),context_rewrite=not (condition.has(sp.Contains) or any(s.name!='w' for s in condition.free_symbols)))}

def combine(calculator,value,source,notices):
    from .cas_system_context import combine as combine_system
    context=frequency_context(calculator,value,source,notices)
    if not context and isinstance(value,sp.Expr):
        axes={c.get('coordinate_variable') for c in calculator.contexts}&{'n','k','t','tau'}
        axes-=calculator.removed_coordinates
        if len(axes)==1 and {s.name for s in value.free_symbols}<=axes:
            context['coordinate_variable']=axes.pop()
    return {**context,**combine_system(calculator,value,notices)}


def frequency_context(calculator,value,source,notices):
    if not isinstance(value,sp.Expr):return {}
    contexts=[c for c in calculator.contexts if c.get('coordinate_variable')=='w']
    condition=sp.And(*calculator.domain_restrictions)
    symbols={s.name for s in value.free_symbols | condition.free_symbols}
    constant_on_axis=not symbols and not calculator.frequency_axis_removed and (contexts or 'w' in calculator.referenced_axes)
    if 'w' not in symbols and not constant_on_axis:return {}
    original=list(dict.fromkeys(str(v) for c in contexts for v in c.get('origin_conditions',())))
    notices.extend(v for v in original if v not in notices)
    units={c['frequency_units'] for c in contexts if c.get('frequency_units')}
    if len(units)>1 or not units<= {'rad/s','rad/muestra'}:
        notices.append('Los resultados de origen usan unidades de frecuencia incompatibles. No se asigna una unidad común ni se convierte la frecuencia automáticamente.')
        return dict(frequency_units='incompatible',coordinate_variable='w',origin_conditions=original)
    condition=frequency_condition(condition)
    return dict(frequency_units=next(iter(units)) if units else '',coordinate_variable='w',
                frequency_condition=str(condition),origin_conditions=original,
                context_rewrite=not bool(symbols-{'w'} or condition.has(sp.Contains)))

def frequency_condition(condition):
    from .symbolic import W
    condition=condition.xreplace({sp.Symbol('w'):W})
    def membership(term):
        value,domain=term.args
        if domain is sp.S.Complexes or domain is sp.S.Reals and value.is_real:return sp.true
        if isinstance(domain,sp.Range) or domain is sp.S.Integers:
            grid=sp.Eq(value,sp.floor(value))
            if domain is sp.S.Integers:return grid
            lower=domain.inf;upper=domain.sup
            return sp.And(grid,value>=lower,value<=upper) if domain.step==1 else term
        if hasattr(domain,'as_relational'):return domain.as_relational(value)
        return term
    return condition.replace(lambda item:isinstance(item,sp.Contains),membership)
