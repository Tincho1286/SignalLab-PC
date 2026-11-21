"""Weighted Dirac trains with exact geometric weights on real time intervals."""

from dataclasses import dataclass, replace

import sympy as sp

from .harmonic_measures import _exponential_terms
from .jobs import checkpoint
from .periodic_signals import ImpulseTrain, _common_period, affine_train_term
from .resources import ensure_working_set
from .periodic_support import split_periodic_support


@dataclass(frozen=True)
class TrainSpan:
    period: sp.Expr
    origin: sp.Expr
    weight: sp.Expr
    first: sp.Expr
    last: sp.Expr
    rate: sp.Expr = sp.S.Zero


def train_spans(value, time):
    """Resolve a train and its gate into uninterrupted runs of impulse indices."""
    trains = value.atoms(ImpulseTrain)
    if len(trains) != 1:
        return None
    train, = trains
    geometry = affine_train_term(train, time)
    gate = value.extract_multiplicatively(train)
    if geometry is None or gate is None or gate.has(ImpulseTrain, sp.DiracDelta):
        return None
    period, origin, area = geometry
    if not gate.has(time):
        return [TrainSpan(period, origin, area*gate, -sp.oo, sp.oo)] if gate != 0 else []
    intervals = split_periodic_support(gate, time, preserve_addends=True, require_wrap=False)
    if intervals is None:
        intervals = [(gate, -sp.oo, sp.oo)]
    modes = [_exponential_terms(branch, time) for branch, _, _ in intervals]
    if any(terms is None or any(weight.is_finite is not True or rate.is_finite is not True
                                or rate.free_symbols for rate, weight in terms)
           for terms in modes):
        return None
    for (before, _, boundary), (after, _, _) in zip(intervals, intervals[1:]):
        checkpoint()
        hits = sp.simplify((boundary-origin)/period).is_integer
        if hits is None:
            return None
        if hits:
            actual = gate.subs(time, boundary)
            left = before.subs(time, boundary)
            right = after.subs(time, boundary)
            if sp.simplify(right-left) != 0 or sp.simplify(actual-left) != 0:
                raise ValueError('El borde temporal coincide con un impulso del tren. Definí ese impulso y su peso por separado.')

    spans = []
    for (_, lower, upper), terms in zip(intervals, modes):
        if not terms:
            continue
        first = lower if lower == -sp.oo else sp.ceiling((lower-origin)/period)
        last = upper if upper == sp.oo else sp.ceiling((upper-origin)/period)-1
        if (first.is_finite and not first.is_Integer) or (last.is_finite and not last.is_Integer):
            return None
        if first <= last:
            spans.extend(TrainSpan(period, origin, area*weight, first, last, rate)
                         for rate, weight in terms if weight != 0)
    return spans


def partition_trains(value, time, *, require_roc=False):
    """Combine weights sharing an impulse lattice before certifying support and ROC."""
    if not value.has(ImpulseTrain):
        return [], value

    def factors(expression):
        if isinstance(expression, sp.Mul):
            for part in expression.args:
                yield from factors(part)
        else:
            yield expression

    def addends(expression):
        if isinstance(expression, sp.Add):
            for term in expression.args:
                yield from addends(term)
        elif isinstance(expression, sp.Mul):
            parts = tuple(factors(expression))
            trains = [part for part in parts if part.has(ImpulseTrain)]
            if len(trains)==1 and isinstance(trains[0],sp.Add):
                gate = sp.Mul(*(part for part in parts if part is not trains[0]))
                for term in addends(trains[0]):
                    yield gate*term
            else:
                yield expression
        else:
            yield expression

    groups = {}
    remaining = []
    for term in addends(value):
        checkpoint()
        atoms = term.atoms(ImpulseTrain)
        if len(atoms) != 1:
            remaining.append(term)
            continue
        train, = atoms
        geometry = affine_train_term(train, time)
        coefficient = term.extract_multiplicatively(train)
        if geometry is None or coefficient is None or coefficient.has(ImpulseTrain, sp.DiracDelta):
            remaining.append(term)
            continue
        period, origin, area = geometry
        key = period, sp.Mod(origin, period)
        groups.setdefault(key, []).append((term, coefficient*area))

    spans = []
    for (period, origin), terms in groups.items():
        coefficient = sp.Add(*(weight for _, weight in terms))
        if coefficient == 0:
            continue
        available = train_spans(coefficient*ImpulseTrain(time-origin,period), time)
        if available is None:
            remaining.extend(term for term, _ in terms)
        else:
            spans.extend(available)
    trimmed = _trim_canceled_tails(spans)
    if trimmed is None and require_roc:
        return [], value
    return (spans if trimmed is None else trimmed), sp.Add(*remaining)


def _tail_is_zero(tails):
    if not tails:
        return True
    if all(span.rate.is_real is True for span in tails):
        if all(span.weight.is_positive is True for span in tails) or all(span.weight.is_negative is True for span in tails):
            return False

    groups = []
    for span in tails:
        for members in groups:
            basis = members[0]
            rate = sp.simplify(span.period/basis.period).is_rational
            if rate is None:
                return None
            if not rate:
                continue
            phase = sp.simplify((span.origin-basis.origin)/basis.period).is_rational
            if phase is None:
                return None
            if phase:
                members.append(span)
                break
        else:
            groups.append([span])

    unknown=False
    for members in groups:
        # Each group has a common period and rational relative offsets.
        # Other groups can share isolated impulses only if their periods
        # are incommensurate, or have disjoint positions if their offsets differ.
        basis=members[0]
        period=_common_period([span.period for span in members])
        counts=[int(period/span.period) for span in members]
        ensure_working_set(sum(counts),bytes_per_sample=4096,live_arrays=8)
        pulses={}
        for span,count in zip(members,counts):
            spacing=sp.simplify(span.period/basis.period)
            origin=sp.Mod(sp.simplify((span.origin-basis.origin)/basis.period),spacing)
            for k in range(count):
                checkpoint()
                position=origin+k*spacing
                time = basis.origin+position*basis.period
                coefficient = span.weight*sp.exp(span.rate*time)
                modes = pulses.setdefault(position, [])
                for index, (other, current) in enumerate(modes):
                    same_ratio = sp.simplify((span.rate-other)*period/(2*sp.pi*sp.I)).is_integer
                    if same_ratio is None:
                        return None
                    if same_ratio:
                        modes[index] = other, current+coefficient
                        break
                else:
                    modes.append((span.rate, coefficient))
        zeros=[sp.simplify(weight).is_zero for modes in pulses.values() for _, weight in modes]
        if False in zeros:
            return False
        unknown=unknown or None in zeros
    return None if unknown else True


def _trim_canceled_tails(spans):
    """Trim canceled infinite families separately for each exponential growth rate."""
    growth_groups = {}
    for span in spans:
        growth = sp.simplify(sp.re(span.rate))
        growth_groups.setdefault(growth, []).append(span)
    trimmed = []
    for group in growth_groups.values():
        remaining = _trim_growth_group(group)
        if remaining is None:
            return None
        trimmed.extend(remaining)
    return trimmed


def _trim_growth_group(spans):
    right=[span for span in spans if span.last==sp.oo]
    zero_right=_tail_is_zero(right)
    if zero_right is None:
        return None
    if right and zero_right:
        boundary=max((span.origin+span.period*span.first for span in right if span.first.is_finite),default=sp.S.Zero)
        spans=[replace(span,last=sp.ceiling((boundary-span.origin)/span.period)-1)
               if span.last==sp.oo else span for span in spans]
        spans=[span for span in spans if span.first<=span.last]
    left=[span for span in spans if span.first==-sp.oo]
    zero_left=_tail_is_zero(left)
    if zero_left is None:
        return None
    if left and zero_left:
        boundary=min((span.origin+span.period*span.last for span in left if span.last.is_finite),default=sp.S.Zero)
        spans=[replace(span,first=sp.floor((boundary-span.origin)/span.period)+1)
               if span.first==-sp.oo else span for span in spans]
    return [span for span in spans if span.first<=span.last]


def _finite_sum(span, parameter):
    count = span.last-span.first+1
    parameter -= span.rate
    phase = sp.exp(-parameter*(span.origin+span.period*span.first))
    if count == 1:
        return span.weight*phase
    ratio = sp.exp(-parameter*span.period)
    factor = sp.Piecewise((count, sp.Eq(ratio, 1)), ((1-ratio**count)/(1-ratio), True))
    return span.weight*phase*factor


def spectrum(span, frequency):
    from .periodic_generalized import _half_comb

    if span.first.is_finite and span.last.is_finite:
        return _finite_sum(span, sp.I*frequency)
    growth = sp.simplify(sp.re(span.rate))
    if growth.is_zero is True:
        shifted = sp.simplify(frequency-sp.im(span.rate))
        if span.first == -sp.oo and span.last == sp.oo:
            spacing = 2*sp.pi/span.period
            return spacing*span.weight*sp.exp(-sp.I*shifted*span.origin)*ImpulseTrain(shifted, spacing)
        edge, direction = (span.first, 1) if span.first.is_finite else (span.last, -1)
        weight = span.weight*sp.exp(-sp.I*shifted*(span.origin+span.period*edge))
        return _half_comb(weight, span.period, direction, shifted)
    if ((span.last == sp.oo and growth.is_negative is not True)
            or (span.first == -sp.oo and growth.is_positive is not True)):
        return None
    return laplace_spans([span], sp.I*frequency)[0]


def laplace_spans(spans, parameter, *, unilateral=False):
    terms = []
    lower, upper = -sp.oo, sp.oo
    for span in spans:
        if unilateral:
            start = sp.ceiling(-span.origin/span.period)
            span = replace(span, first=sp.Max(span.first, start))
            if span.first > span.last:
                continue
        if span.first.is_finite and span.last.is_finite:
            terms.append(_finite_sum(span, parameter))
            continue
        growth = sp.simplify(sp.re(span.rate))
        if span.last == sp.oo:
            lower = sp.Max(lower, growth)
        if span.first == -sp.oo:
            upper = sp.Min(upper, growth)
        edge, direction = (span.first, 1) if span.first.is_finite else (span.last, -1)
        if edge.is_finite:
            shifted = parameter-span.rate
            terms.append(span.weight*sp.exp(-shifted*(span.origin+span.period*edge))
                         /(1-sp.exp(-direction*span.period*shifted)))
    return sp.Add(*terms), lower, upper
