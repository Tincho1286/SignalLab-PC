"""Worksheet-local scalar assumptions, with no global SymPy context."""
import sympy as sp
from sympy.core.relational import Relational

PROPERTIES={'real','complex','integer','positive','negative','nonnegative','nonpositive','nonzero','zero'}


def symbol(name,assumptions):
    return sp.Symbol(name,**assumptions.get(name,{}).get('flags',{}))


def constrain(name,assumptions,property_name=None,condition=None):
    entry=assumptions.setdefault(name,{'flags':{},'conditions':[]})
    flags=entry['flags'].copy();conditions=list(entry['conditions']);bare=sp.Symbol(name)
    if property_name is not None:
        if property_name not in PROPERTIES:raise ValueError('Propiedades: '+', '.join(sorted(PROPERTIES))+'.')
        flags[property_name]=True
    else:
        if not isinstance(condition,Relational):raise ValueError('Usá assume(x>0), assume(x<2) o assume(x,real).')
        condition=condition.xreplace({v:bare for v in condition.free_symbols if v.name==name})
        left,right=condition.lhs,condition.rhs
        if right==bare:left,right=right,left;condition=condition.reversed
        if left!=bare or right.free_symbols or right.is_real is not True or right.is_finite is not True:
            raise ValueError('El supuesto debe comparar un símbolo con una constante real finita. Las relaciones entre parámetros no están implementadas.')
        if isinstance(condition,sp.Unequality):
            if right!=0:raise ValueError('Para ≠ se admite assume(x!=0).')
            flags['zero']=False
        elif isinstance(condition,sp.Equality):
            if right!=0:raise ValueError('Para fijar un valor usá x:=valor. Como supuesto se admite assume(x=0).')
            flags['zero']=True
        else:
            flags['real']=True
            if str(condition) not in conditions:conditions.append(str(condition))
    if any(key in flags and flags[key]!=value for key,value in entry['flags'].items()):raise ValueError('Los supuestos se contradicen; usá purge('+name+') para reemplazarlos.')
    # Conditions are stored as mathematical constructor strings, never evaluated.
    from .cas_engine import restore,encode
    stored=[restore(text) for text in entry.get('encoded_conditions',[])]
    if condition is not None and not isinstance(condition,(sp.Equality,sp.Unequality)):
        if condition not in stored:stored.append(condition)
    try:
        candidate=sp.Symbol(name,**flags)
        domain=sp.S.Reals if candidate.is_real else sp.S.Complexes
        if stored:
            interval=sp.reduce_inequalities(stored,bare).as_set()
            if interval is sp.S.EmptySet:raise ValueError('Los supuestos se contradicen.')
            if interval.is_subset(sp.Interval.open(0,sp.oo)) is True:flags['positive']=True
            elif interval.is_subset(sp.Interval(0,sp.oo)) is True:flags['nonnegative']=True
            if interval.is_subset(sp.Interval.open(-sp.oo,0)) is True:flags['negative']=True
            elif interval.is_subset(sp.Interval(-sp.oo,0)) is True:flags['nonpositive']=True
            domain=interval
        candidate=sp.Symbol(name,**flags)
        domain=domain.intersect(_flag_domain(candidate))
        if domain is sp.S.EmptySet:raise ValueError('Los supuestos se contradicen.')
    except (ValueError,TypeError) as exc:raise ValueError('Supuestos incompatibles para '+name+'. Usá purge('+name+') para empezar de nuevo.') from exc
    entry.update(flags=flags,conditions=conditions,encoded_conditions=[encode(v) for v in stored])


def _flag_domain(value):
    domain=sp.S.Integers if value.is_integer else sp.S.Reals if value.is_real else sp.S.Complexes
    if value.is_zero is True:return sp.FiniteSet(0)
    if value.is_positive:domain=domain.intersect(sp.Interval.open(0,sp.oo))
    elif value.is_nonnegative:domain=domain.intersect(sp.Interval(0,sp.oo))
    if value.is_negative:domain=domain.intersect(sp.Interval.open(-sp.oo,0))
    elif value.is_nonpositive:domain=domain.intersect(sp.Interval(-sp.oo,0))
    if value.is_zero is False:domain=domain-sp.FiniteSet(0)
    return domain


def solution_domain(value,assumptions):
    from .cas_engine import restore
    domain=_flag_domain(value);conditions=assumptions.get(value.name,{}).get('encoded_conditions',[])
    if conditions:domain=domain.intersect(sp.reduce_inequalities([restore(c) for c in conditions],sp.Symbol(value.name)).as_set())
    return domain


def descriptions(assumptions):
    labels={'real':'real','complex':'complejo','integer':'entero','positive':'positivo','negative':'negativo','nonnegative':'no negativo','nonpositive':'no positivo','nonzero':'real no nulo','zero':'cero'}
    return [(name,', '.join([labels[key] if flag else 'no '+labels[key] for key,flag in entry['flags'].items()]+entry.get('conditions',[]))) for name,entry in sorted(assumptions.items())]
