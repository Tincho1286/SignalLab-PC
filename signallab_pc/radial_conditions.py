"""Simplify radial constraints without flattening disjunctions into intersections."""
import sympy as sp
from sympy.core.relational import Relational


def simplify_radial(condition, coordinate):
    radius = sp.Dummy('radius', positive=True)
    radial = condition.subs(sp.Abs(coordinate), radius)

    def reduce(node):
        if node.func == sp.Or:
            return sp.Or(*(reduce(part) for part in node.args))
        if not node.has(radius):
            return node
        parts = node.args if node.func == sp.And else (node,)
        radial_parts = [part for part in parts if isinstance(part, Relational) and part.free_symbols == {radius}]
        if not radial_parts:
            return sp.And(*(reduce(part) if part.func == sp.Or else part for part in parts))
        try:
            # Convert each predicate separately. reduce_inequalities may leave
            # equivalent bounds in different forms (r < 1 and 1/r < 1).
            # Intersecting the real sets detects the contradiction exactly.
            region = sp.Intersection(sp.Interval.open(0, sp.oo),
                                     *(part.as_set() for part in radial_parts))
            reduced = region.as_relational(radius)
        except (NotImplementedError, ValueError, TypeError):
            return node
        return sp.And(reduced, *(reduce(part) if part.func == sp.Or else part
                                 for part in parts if part not in radial_parts))

    return reduce(radial).xreplace({radius: sp.Abs(coordinate)})
