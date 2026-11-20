"""Recover compact polynomial pieces from the weights of a Fourier comb."""

import sympy as sp

from .jobs import checkpoint
from .periodic_signals import ImpulseTrain, affine_train_term
from .resources import ensure_working_set


def _compact_pieces(weight, frequency, time, zero_is_line):
    folded = sp.piecewise_fold(weight)
    ordinary = folded
    if isinstance(folded, sp.Piecewise):
        nonzero_axis = sp.S.Reals - sp.FiniteSet(0)
        try:
            regions = [(branch, region) for branch, region in folded.as_expr_set_pairs(domain=nonzero_axis)
                       if region != sp.S.EmptySet]
        except (NotImplementedError, TypeError, ValueError):
            return None
        if len(regions) != 1 or regions[0][1] != nonzero_axis:
            return None
        ordinary = regions[0][0]
    if ordinary.free_symbols - {frequency}:
        return None

    ordinary = ordinary.replace(lambda node:node.func in (sp.sin,sp.cos), lambda node:node.rewrite(sp.exp))
    delayed = {}
    for term in sp.Add.make_args(sp.expand(sp.cancel(ordinary))):
        checkpoint()
        constant = sp.S.One
        exponent = sp.S.Zero
        power = sp.S.Zero
        for factor in sp.Mul.make_args(sp.factor_terms(term)):
            if not factor.has(frequency):
                constant *= factor
            elif factor.func == sp.exp:
                exponent += factor.args[0]
            else:
                base, degree = factor.as_base_exp()
                if base != frequency or not isinstance(degree, sp.Integer):
                    return None
                power += degree
        if power >= 0 or constant.is_finite is not True:
            return None
        # (i*w)^(-k) times a shift gives a truncated power away from w=0.
        # Requiring all right-hand polynomials to cancel removes the singular
        # terms at w=0 and leaves an ordinary compact-support transform.
        delay = sp.simplify(sp.I*sp.diff(exponent, frequency))
        phase = sp.expand(exponent+sp.I*frequency*delay)
        if delay.has(frequency) or phase.has(frequency) or delay.is_real is not True or delay.is_finite is not True:
            return None
        order = int(-power)
        ensure_working_set(order**2, bytes_per_sample=1024, live_arrays=8)
        coefficient = constant*sp.exp(phase)*sp.I**order/sp.factorial(order-1)
        delayed[delay] = delayed.get(delay, sp.S.Zero) + coefficient*(time-delay)**(order-1)

    if sp.expand(sp.Add(*delayed.values())) != 0:
        return None
    stops = sorted(delayed)
    pieces = []
    branch = sp.S.Zero
    for left, right in zip(stops, stops[1:]):
        checkpoint()
        branch = sp.expand(branch+delayed[left])
        if branch != 0:
            pieces.append((left, right, branch))
    if zero_is_line:
        area = sp.Add(*(sp.integrate(branch,(time,left,right)) for left,right,branch in pieces))
        actual_dc = folded.subs(frequency,0)
        if actual_dc.has(sp.zoo,sp.nan):
            # The compact-support expression has a unique continuous extension.
            # Only use it when no explicit conflicting value was supplied.
            if isinstance(folded, sp.Piecewise):
                return None
            actual_dc = area
        if actual_dc.is_finite is not True or sp.simplify(actual_dc-area) != 0:
            return None
    return pieces


def _periodize(pieces, time, spacing, origin, area):
    if not pieces:
        return sp.S.Zero
    period = 2*sp.pi/spacing
    start = pieces[0][0]
    end = start+period
    changes = {start:sp.S.Zero,end:sp.S.Zero}
    copies = 0
    for left, right, branch in pieces:
        begin = sp.floor((left-start)/period)
        beyond = sp.ceiling((right-start)/period)
        if not isinstance(begin,sp.Integer) or not isinstance(beyond,sp.Integer):
            return None
        copies += int(beyond-begin)
        ensure_working_set(copies, bytes_per_sample=4096, live_arrays=8)
        for index in range(int(begin),int(beyond)):
            checkpoint()
            offset = period*index
            low = sp.Max(start,left-offset)
            high = sp.Min(end,right-offset)
            if high <= low:
                continue
            adjusted = branch.subs(time,time+offset)*sp.exp(-sp.I*origin*offset)
            changes[low] = changes.get(low,sp.S.Zero)+adjusted
            changes[high] = changes.get(high,sp.S.Zero)-adjusted

    points = sorted(changes)
    intervals = []
    branch = sp.S.Zero
    for left, right in zip(points,points[1:]):
        branch = sp.expand(branch+changes[left])
        intervals.append((left,right,branch))
    before = intervals[-1][2].subs(time,end)*sp.exp(-sp.I*origin*period)
    formula = []
    scale = area/spacing
    for left,right,branch in intervals:
        checkpoint()
        after = branch.subs(time,left)
        difference = sp.simplify(before-after)
        if difference != 0:
            formula.append((sp.simplify(scale*(after+difference/2)),sp.Eq(time,left)))
        formula.append((sp.expand(scale*branch),time<right if right!=end else True))
        before = branch.subs(time,right)
    phase = start+sp.Mod(time-start,period)
    return sp.exp(sp.I*origin*(time-phase))*sp.Piecewise(*formula).subs(time,phase)


def inverse_weighted_comb(term, frequency, time):
    trains = term.atoms(ImpulseTrain)
    if len(trains) != 1:
        return None
    train, = trains
    weight = term.extract_multiplicatively(train)
    geometry = affine_train_term(train,frequency)
    if (weight is None or geometry is None or not weight.has(frequency)
            or weight.has(ImpulseTrain,sp.DiracDelta)):
        return None
    spacing, origin, area = geometry
    if (spacing.free_symbols or origin.free_symbols or spacing.is_positive is not True
            or spacing.is_finite is not True or origin.is_finite is not True):
        return None
    zero_is_line = (origin/spacing).is_integer
    if zero_is_line is None:
        return None
    pieces = _compact_pieces(weight,frequency,time,zero_is_line)
    # A translated comb can have its removable point at its reference line.
    if pieces is None and origin != 0:
        shifted = _compact_pieces(weight.subs(frequency,frequency+origin),frequency,time,True)
        if shifted is not None:
            result = _periodize(shifted,time,spacing,sp.S.Zero,area)
            return None if result is None else sp.exp(sp.I*origin*time)*result
    return None if pieces is None else _periodize(pieces,time,spacing,origin,area)
