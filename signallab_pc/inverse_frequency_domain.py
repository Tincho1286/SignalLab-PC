"""Validate the frequency region transferred with a formula."""
import sympy as sp


def exclusions(condition,domain,variable):
    from sympy.core.relational import Equality,Unequality
    if condition is sp.true:return sp.S.EmptySet
    if condition is sp.false:return domain
    if condition.func==sp.And:return sp.Union(*(exclusions(part,domain,variable) for part in condition.args))
    if condition.func==sp.Or:return sp.Intersection(*(exclusions(part,domain,variable) for part in condition.args))
    if isinstance(condition,(Equality,Unequality)):
        roots=sp.solveset(condition.lhs-condition.rhs,variable,domain=domain)
        return roots if isinstance(condition,Unequality) else domain-roots
    return domain-condition.as_set()


def require_inverse_domain(request,value,domain,variable):
    text=request.get('input_frequency_condition','True')
    if text=='True':return
    from .symbolic import parse
    try:
        condition=parse(text)
        if condition.free_symbols-{variable}:raise ValueError('La condición de frecuencia contiene parámetros sin asignar.')
        omitted=exclusions(condition,domain,variable)
    except (SyntaxError,TypeError,NotImplementedError) as exc:
        raise ValueError('No se pudo verificar el dominio de la fórmula importada.') from exc
    if omitted is sp.S.EmptySet:return
    if isinstance(omitted,sp.FiniteSet) and not value.has(sp.DiracDelta):return
    raise ValueError('La fórmula importada no está definida en todo el intervalo de la inversa. Definí explícitamente los tramos faltantes antes de integrarla.')


def require_defined_samples(spectrum):
    text=spectrum.metadata.get('source_frequency_condition','True')
    if text=='True':return
    from .symbolic import parse,W
    from .analytic_frequency import _condition_mask
    condition=parse(text)
    if condition.free_symbols-{W}:raise ValueError('La condición de frecuencia contiene parámetros sin asignar.')
    if not _condition_mask(condition,spectrum.axis).all():
        raise ValueError('La rejilla incluye frecuencias fuera del dominio de la fórmula. Si son puntos aislados, probá la inversa algebraica o una rejilla que los evite.')
