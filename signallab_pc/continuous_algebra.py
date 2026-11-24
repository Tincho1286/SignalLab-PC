"""Integrate ordinary and distributional signals on their actual real support."""
import sympy as sp
from sympy.integrals.transforms import IntegralTransformError

from .jobs import checkpoint
from .periodic_support import split_periodic_support
from .resources import ensure_working_set


def spans(value, variable, lower=-sp.oo, upper=sp.oo):
    parts = split_periodic_support(value,variable,preserve_addends=True,require_wrap=False)
    if parts is None:
        parts = [(value,-sp.oo,sp.oo)]
    for branch, first, last in parts:
        start, stop = sp.Max(first,lower), sp.Min(last,upper)
        if branch != 0 and (start < stop) is not sp.false:
            yield branch,start,stop


def nonnegative_integral(density, variable, lower, upper):
    """Check interior poles by real one-sided limits before integrating."""
    terms = []
    for branch, start, stop in spans(density,variable,lower,upper):
        checkpoint()
        definition = sp.Integral(branch,(variable,start,stop))
        try:
            points = sp.singularities(branch,variable,domain=sp.S.Reals)
        except (NotImplementedError, ValueError, TypeError):
            points = None
        if isinstance(points,sp.FiniteSet):
            internal = [p for p in points if (start < p) is sp.true and (p < stop) is sp.true]
            edges = [start,*sorted(internal,key=lambda p:float(p.evalf(25))),stop]
            u = sp.Dummy('distance',positive=True)
            for a,b in zip(edges,edges[1:]):
                for point,direction in ((a,1),(b,-1)):
                    if points.contains(point) is not sp.true:
                        continue
                    try:
                        lead = branch.subs(variable,point+direction*u).as_leading_term(u)
                        coefficient, power = lead.as_coeff_exponent(u)
                    except (NotImplementedError, ValueError, TypeError):
                        continue
                    if not coefficient.has(u) and coefficient.is_positive is True and (power+1).is_nonpositive is True:
                        return sp.oo
        else:
            edges = [start,stop]
        for a,b in zip(edges,edges[1:]):
            try:
                if isinstance(points,sp.FiniteSet) and (points.contains(a) is sp.true or points.contains(b) is sp.true):
                    # Give the backend a positive distance from the pole so
                    # fractional powers stay on the correct real branch.
                    from_left = points.contains(a) is sp.true
                    local = sp.simplify(branch.subs(variable,a+u if from_left else b-u))
                    result = sp.integrate(local,(u,0,b-a))
                else:
                    result = sp.integrate(branch,(variable,a,b))
            except (IntegralTransformError,NotImplementedError,ValueError,TypeError):
                result = definition if (a,b)==(start,stop) else sp.Integral(branch,(variable,a,b))
            if result is sp.oo:
                return sp.oo
            if (result.has(sp.nan,sp.zoo) or result.is_extended_real is False
                    or result.is_extended_nonnegative is False):
                result = sp.Integral(branch,(variable,a,b))
            terms.append(result)
    return sp.Add(*terms)


def impulse_components(value, variable, *, causal=False):
    """Return ordinary part and normalized (position, derivative order, weight)."""
    from .impulse_pairs import affine_impulse, expand_real_impulses, impulse_integral

    regular, impulses = [], []
    for term in sp.Add.make_args(expand_real_impulses(value,variable)):
        atoms = term.atoms(sp.DiracDelta)
        if not atoms:
            regular.append(term)
            continue
        delta = next(iter(atoms))
        geometry = affine_impulse(delta,variable)
        order = delta.args[1] if len(delta.args)>1 else sp.S.Zero
        if len(atoms)!=1 or geometry is None or not isinstance(order,sp.Integer) or order<0:
            raise ValueError('Usá impulsos con raíces reales simples y pesos definidos en sus posiciones.')
        _,position = geometry
        for power in range(int(order)+1):
            kernel = (variable-position)**power/sp.factorial(power)
            coefficient = impulse_integral(term,variable,kernel,0 if causal else -sp.oo,sp.oo)
            if coefficient is None:
                raise ValueError('No se pudo determinar el peso o la derivada de un impulso.')
            if coefficient != 0:
                impulses.append((position,power,(-1)**power*coefficient))
    return sp.Add(*regular),impulses


def _supported_derivative(value, variable, order, causal):
    if order == 0:
        return value*sp.Heaviside(variable,1) if causal else value
    terms = []
    lower = sp.S.Zero if causal else -sp.oo
    for branch,start,stop in spans(value,variable,lower):
        checkpoint()
        gate = sp.Heaviside(variable-start,1)-sp.Heaviside(variable-stop,1)
        terms.append(sp.diff(branch,variable,order)*gate)
        for n in range(order):
            derivative = sp.diff(branch,variable,n)
            for point,direction,sign in ((start,'+',1),(stop,'-',-1)):
                if not point.is_finite:
                    continue
                weight = sp.limit(derivative,variable,point,dir=direction)
                if weight.is_finite is not True:
                    raise ValueError('La derivada distribucional requiere límites laterales finitos en los bordes del soporte.')
                if weight != 0:
                    terms.append(sign*weight*sp.DiracDelta(variable-point,order-1-n))
    return sp.Add(*terms)


def convolution(left, right, variable, *, causal=False, correlation=False, lag=None):
    left,left_impulses = impulse_components(left,variable,causal=causal)
    right,right_impulses = impulse_components(right,variable,causal=causal)
    output = lag if correlation else variable
    if correlation:
        right = sp.conjugate(right.subs(variable,-variable))
        right_impulses = [(-point,order,(-1)**order*sp.conjugate(gain))
                          for point,order,gain in right_impulses]
    lower = sp.S.Zero if causal else -sp.oo
    result = []
    x = sp.Dummy('coordinate',real=True)
    left_spans = list(spans(left,variable,lower))
    right_spans = list(spans(right,variable,lower))
    ensure_working_set(len(left_spans)*len(right_spans)+len(left_impulses)*len(right_impulses),
                       bytes_per_sample=2048,live_arrays=8)
    for a, alo, ahi in left_spans:
        for b, blo, bhi in right_spans:
            checkpoint()
            start = sp.Max(alo,output-bhi)
            stop = sp.Min(ahi,output-blo)
            inside = start < stop
            if inside is sp.false:
                continue
            integrand = sp.simplify(a.subs(variable,x)*b.subs(variable,output-x))
            area = sp.integrate(integrand,(x,start,stop))
            result.append(area if inside is sp.true else sp.Piecewise((area,inside),(0,True)))
    for ordinary, impulses in ((right,left_impulses),(left,right_impulses)):
        if ordinary == 0:
            continue
        derivatives = {}
        for point, order, gain in impulses:
            checkpoint()
            if order not in derivatives:
                derivatives[order] = _supported_derivative(ordinary,variable,order,causal)
            result.append(gain*derivatives[order].subs(variable,output-point))
    for left_point,left_order,left_gain in left_impulses:
        for right_point,right_order,right_gain in right_impulses:
            result.append(left_gain*right_gain*sp.DiracDelta(output-left_point-right_point,left_order+right_order))
    return sp.simplify(sp.Add(*result))
