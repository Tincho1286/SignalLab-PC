"""Transform pairs for ordinary waveforms defined by a continuous cycle."""

import sympy as sp
from sympy.calculus.util import continuous_domain

from .jobs import checkpoint
from .periodic_signals import ImpulseTrain, repeat, wrapped_period


def _slice_cycle(pieces, period, start, time, lower, upper):
    """Yield the pieces of an interval no longer than one period."""
    offset = period*sp.floor((lower-start)/period)
    for lo,hi,branch in pieces:
        for shift in (offset,offset+period):
            left,right = sp.Max(lower,lo+shift),sp.Min(upper,hi+shift)
            if left < right:
                yield left,right,branch.subs(time,time-shift)


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
    kernel = sp.exp(-output*time)
    terms = []
    for left,right,branch in _slice_cycle(pieces,period,start,time,sp.S.Zero,period):
        checkpoint()
        area = sp.integrate(branch*kernel, (time,left,right), conds='none')
        if area.has(sp.Integral, sp.oo, -sp.oo, sp.zoo, sp.nan):
            return None
        terms.append(area)
    return sp.Add(*terms)/(1-sp.exp(-output*period))


def finite_laplace_piece(value,time,output,lower,upper):
    result=sp.integrate(value*sp.exp(-output*time),(time,lower,upper))
    # Parameter branches from integration can include real-line infinity
    # guards. Here s ranges over all finite complex numbers.
    return result.xreplace({output>-sp.oo:sp.true,output<sp.oo:sp.true,-sp.oo<output:sp.true,sp.oo>output:sp.true})


def periodic_integral(value, time, lower, upper, *, laplace_variable=None):
    """Integrate full cycles once, plus the remaining fraction of a cycle."""
    cycle = _bounded_cycle(value,time)
    if cycle is None:
        return None
    period,start,pieces,_ = cycle
    cycles = sp.floor((upper-lower)/period)
    if not isinstance(cycles,sp.Integer):
        return None
    def integrate(start_at, stop_at):
        terms=[]
        for left,right,branch in _slice_cycle(pieces,period,start,time,start_at,stop_at):
            checkpoint()
            area=(sp.integrate(branch,(time,left,right)) if laplace_variable is None
                  else finite_laplace_piece(branch,time,laplace_variable,left,right))
            terms.append(area)
        return sp.Add(*terms)
    whole = integrate(lower,lower+period) if cycles else sp.S.Zero
    remainder = integrate(lower,upper-cycles*period)
    if laplace_variable is None or not cycles:
        return cycles*whole+remainder
    factor = sp.exp(-laplace_variable*period)
    repeat_count = sp.Piecewise((cycles,sp.Eq(factor,1)),((1-factor**cycles)/(1-factor),True))
    return whole*repeat_count+factor**cycles*remainder


def gated_periodic_laplace(value, time, output):
    """Laplace from zero with an exact ROC for a gated periodic waveform."""
    if value.has(ImpulseTrain,sp.DiracDelta):
        return None
    from .periodic_support import split_periodic_support
    split=split_periodic_support(value,time)
    if split is None:
        return None
    finite=[]
    tail=sp.S.Zero
    for branch,left,right in split:
        start=sp.Max(0,left)
        if start>=right or branch==0:
            continue
        if right==sp.oo:
            transformed=periodic_laplace(branch.subs(time,time+start),time,output)
            if transformed is None and not branch.has(time):
                transformed=branch/output
            if transformed is None:
                return None
            tail=sp.exp(-output*start)*transformed
        else:
            transformed=(periodic_integral(branch,time,start,right,laplace_variable=output) if branch.has(sp.Mod)
                         else finite_laplace_piece(branch,time,output,start,right))
            if transformed is None or transformed.has(sp.Integral,sp.nan,sp.oo,sp.zoo):
                return None
            finite.append(transformed)
    return sp.Add(*finite),tail
