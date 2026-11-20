"""Global measures for harmonics with rational energy envelopes."""

import sympy as sp

from .harmonic_measures import _intervals
from .jobs import checkpoint


def rational_components(density, variable):
    """Group the rational coefficients of exp(i*frequency*variable)."""
    expanded = sp.expand(density.rewrite(sp.exp))
    coefficients = {}
    for term in sp.Add.make_args(expanded):
        checkpoint()
        frequency = sp.S.Zero
        factors = []
        for factor in sp.Mul.make_args(sp.factor_terms(term)):
            if factor.func != sp.exp or not factor.has(variable):
                factors.append(factor)
                continue
            rate = sp.diff(factor.args[0], variable)
            phase = sp.expand(factor.args[0] - rate*variable)
            if phase.has(variable) or rate.has(variable) or rate.is_imaginary is not True:
                return None
            frequency += rate/sp.I
            factors.append(sp.exp(phase))
        if frequency.free_symbols or frequency.is_real is not True:
            return None
        if variable.is_integer:
            frequency = sp.simplify(sp.Mod(frequency+sp.pi, 2*sp.pi)-sp.pi)
        coefficient = sp.Mul(*factors)
        coefficients[frequency] = coefficients.get(frequency, sp.S.Zero) + coefficient

    components = []
    for frequency, coefficient in coefficients.items():
        rational = sp.cancel(coefficient)
        if rational == 0:
            continue
        if rational.free_symbols - {variable} or not rational.is_rational_function(variable):
            return None
        numerator, denominator = (sp.Poly(part, variable) for part in sp.fraction(rational))
        components.append((frequency, numerator, denominator))
    return components


def _no_axis_poles(denominator, variable, lower, upper):
    if denominator.degree() < 1:
        return True
    coordinate = sp.Dummy('axis', real=True)
    poles = sp.solveset(denominator.as_expr().xreplace({variable: coordinate}), coordinate,
                        domain=sp.Interval(lower, upper))
    if variable.is_integer:
        poles = sp.Intersection(poles, sp.S.Integers)
    return poles == sp.S.EmptySet


def _lorentzian(frequency, numerator, denominator, *, discrete):
    if numerator.degree() != 0 or denominator.degree() % 2:
        return None
    scale, factors = denominator.factor_list()
    if len(factors) != 1 or factors[0][0].degree() != 2:
        return None
    quadratic, order = factors[0]
    leading = quadratic.nth(2)
    center = -quadratic.nth(1)/(2*leading)
    radius_squared = sp.simplify(quadratic.nth(0)/leading - center**2)
    if radius_squared.is_positive is not True or center.is_real is not True:
        return None
    if discrete and center.is_integer is not True:
        return None
    radius = sp.Dummy('radius', positive=True)
    # Continuous exponential transform. Sampling its inverse gives the
    # discrete result by summing the 2π-shifted exponential copies.
    envelope = (sp.cosh(radius*(sp.pi-sp.Abs(frequency)))/sp.sinh(sp.pi*radius)
                if discrete else sp.exp(-radius*sp.Abs(frequency)))
    integral = envelope/radius
    for degree in range(1, order):
        checkpoint()
        integral = -sp.diff(integral, radius)/(2*degree*radius)
    return sp.pi*numerator.nth(0)*sp.exp(sp.I*frequency*center)*integral.subs(radius, sp.sqrt(radius_squared))/(scale*leading**order)


def oscillatory_measures(density, variable):
    """Certify means and convergence without inferring a sum from sampled values."""
    intervals = _intervals(density, variable)
    if intervals is None:
        return None
    averages = {}
    convergent = True
    logarithmic_growth = False
    whole_axis_components = None
    for expression, lower, upper in intervals:
        components = rational_components(expression, variable)
        if components is None:
            return None
        sample_mean = sp.S.Zero
        infinite = lower == -sp.oo or upper == sp.oo
        for frequency, numerator, denominator in components:
            if not _no_axis_poles(denominator, variable, lower, upper):
                return None
            if not infinite:
                continue
            degree = numerator.degree()-denominator.degree()
            if degree > 0:
                return None
            if degree == 0:
                convergent = False
            if degree == 0 and frequency == 0:
                sample_mean += numerator.LC()/denominator.LC()
            if degree == -1 and frequency == 0:
                # At a nonzero frequency a rational O(1/|x|) term satisfies
                # the Dirichlet test. The constant component has a log tail.
                leading = numerator.LC()/denominator.LC()
                side = 1 if upper == sp.oo else -1
                logarithmic_growth |= (side*leading).is_positive is True
                convergent = False
        if lower == -sp.oo:
            averages[-1] = sample_mean
        if upper == sp.oo:
            averages[1] = sample_mean
        if lower == -sp.oo and upper == sp.oo:
            whole_axis_components = components

    if len(averages) != 2:
        return None
    mean = sp.simplify(sp.re((averages[-1]+averages[1])/2))
    if mean.is_nonnegative is not True:
        return None
    if mean.is_positive is True or logarithmic_growth:
        return mean, sp.oo, False
    if convergent and whole_axis_components:
        terms = [_lorentzian(*component, discrete=variable.is_integer) for component in whole_axis_components]
        if all(term is not None for term in terms):
            energy = sp.simplify(sp.re(sp.Add(*terms)))
            if energy.is_finite is True and energy.is_nonnegative is True:
                return mean, energy, True
    return mean, None, convergent
