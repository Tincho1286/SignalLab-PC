"""Transform pairs for ordinary waveforms defined by a continuous cycle."""

import sympy as sp
from sympy.calculus.util import continuous_domain

from .jobs import checkpoint
from .periodic_signals import ImpulseTrain, repeat, wrapped_period


def _bounded_cycle(value, time):
    if value.free_symbols - {time} or value.has(ImpulseTrain, sp.DiracDelta):
        return None
    wrapping = wrapped_period(value, time)
    if wrapping is None:
        return None
    period, start, cycle = wrapping
    end = start+period
    cycle = sp.piecewise_fold(cycle.rewrite(sp.Piecewise))
    window = sp.Interval.open(start, end)
    try:
        regions = cycle.as_expr_set_pairs(domain=window) if isinstance(cycle, sp.Piecewise) else [(cycle, window)]
    except (NotImplementedError, TypeError, ValueError):
        return None
    pieces = []
    for branch, region in regions:
        checkpoint()
        for part in (region.args if isinstance(region, sp.Union) else (region,)):
            if isinstance(part, sp.FiniteSet) or part == sp.S.EmptySet:
                continue
            if not isinstance(part, sp.Interval):
                return None
            interior = sp.Interval.open(part.start, part.end)
            try:
                if any(continuous_domain(component, time, interior) != interior for component in branch.as_real_imag()):
                    return None
            except (NotImplementedError, TypeError, ValueError):
                return None
            pieces.append((part.start, part.end, branch))
    if not pieces:
        return None
    pieces.sort(key=lambda piece: piece[0])
    starts, stops, branches = zip(*pieces)
    if starts != (start, *stops[:-1]) or stops[-1] != end:
        return None
    limits = []
    for index, (lower, _, branch) in enumerate(pieces):
        checkpoint()
        left = sp.limit(branches[index-1], time, stops[index-1], dir='-')
        right = sp.limit(branch, time, lower, dir='+')
        if left.is_finite is not True or right.is_finite is not True:
            return None
        limits.append((left, right))
    return period, start, pieces, limits


def periodic_fourier_pair(value, time, frequency):
    """Return the exact line spectrum and its canonical inverse at the jumps."""
    cycle = _bounded_cycle(value, time)
    if cycle is None:
        return None
    period, start, pieces, limits = cycle
    end = start+period
    weight = sp.S.Zero
    entries = []
    kernel = sp.exp(-sp.I*frequency*time)
    for (lower, upper, branch), (left, right) in zip(pieces, limits):
        checkpoint()
        area = sp.integrate(branch*kernel, (time, lower, upper))
        if area.has(sp.Integral, sp.oo, -sp.oo, sp.zoo, sp.nan):
            return None
        weight += area
        midpoint = sp.simplify((left+right)/2)
        if sp.simplify(branch.subs(time, lower)-midpoint) != 0:
            entries.append((midpoint, sp.Eq(time, lower)))
        entries.append((branch, time < upper if upper != end else True))

    spacing = 2*sp.pi/period
    spectrum = spacing*weight*ImpulseTrain(frequency, spacing)
    return spectrum, repeat(sp.Piecewise(*entries), time, period, start)


def periodic_laplace(value, time, output):
    """Use the cycle starting at zero and sum its causal repetitions."""
    cycle = _bounded_cycle(value, time)
    if cycle is None:
        return None
    period, start, pieces, _ = cycle
    offset = period*sp.floor(-start/period)
    kernel = sp.exp(-output*time)
    terms = []
    for lower, upper, branch in pieces:
        for shift in (offset, offset+period):
            left, right = sp.Max(0, lower+shift), sp.Min(period, upper+shift)
            if left >= right:
                continue
            checkpoint()
            region = branch.subs(time, time-shift)
            area = sp.integrate(region*kernel, (time, left, right), conds='none')
            if area.has(sp.Integral, sp.oo, -sp.oo, sp.zoo, sp.nan):
                return None
            terms.append(area)
    return sp.Add(*terms)/(1-sp.exp(-output*period))
