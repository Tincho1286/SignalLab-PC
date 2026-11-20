"""Separate finite support limits from the inequalities inside a period."""

import sympy as sp
from sympy.core.relational import Relational

from .jobs import checkpoint


def split_periodic_support(value, variable):
    if not value.has(sp.Mod):
        return None
    expression = sp.piecewise_fold(value.rewrite(sp.Piecewise))
    conditions = {}
    points = set()
    for condition in expression.atoms(Relational):
        if condition.free_symbols != {variable} or condition.has(sp.Mod):
            continue
        checkpoint()
        try:
            region = condition.as_set()
        except (NotImplementedError, TypeError, ValueError):
            continue
        parts = region.args if isinstance(region,sp.Union) else (region,)
        boundaries = []
        for part in parts:
            if isinstance(part,sp.Interval):
                boundaries.extend(point for point in (part.start,part.end) if point.is_finite)
            elif isinstance(part,sp.FiniteSet):
                boundaries.extend(part)
            elif part != sp.S.EmptySet:
                break
        else:
            points.update(boundaries)
            conditions[condition] = region

    if not conditions:
        return None
    endpoints = [-sp.oo,*sorted(points),sp.oo]
    discrete = variable.is_integer is True
    result = []
    for lower,upper in zip(endpoints,endpoints[1:]):
        checkpoint()
        if lower == -sp.oo:
            probe = sp.S.Zero if upper == sp.oo else upper-1
        else:
            probe = lower+1 if upper == sp.oo else (lower+upper)/2
        truth = {condition:region.contains(probe) for condition,region in conditions.items()}
        if any(flag not in (sp.true,sp.false) for flag in truth.values()):
            return None
        branch = expression.xreplace(truth)
        if not discrete:
            result.append((branch,lower,upper))
            continue
        first = lower if lower == -sp.oo else sp.floor(lower)+1
        last = upper if upper == sp.oo else sp.ceiling(upper)-1
        if first <= last:
            result.append((branch,first,last))
        if upper.is_integer is True:
            result.append((expression.subs(variable,upper),upper,upper))
    return result
