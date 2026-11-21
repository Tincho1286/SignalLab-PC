"""Weighted Dirac trains cut by piecewise constant time gates."""

from dataclasses import dataclass, replace

import sympy as sp

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
    if intervals is None or any(branch.has(time) or branch.is_finite is not True for branch, _, _ in intervals):
        return None

    for (before, _, boundary), (after, _, _) in zip(intervals, intervals[1:]):
        checkpoint()
        hits = sp.simplify((boundary-origin)/period).is_integer
        if hits is None:
            return None
        if hits:
            actual = gate.subs(time, boundary)
            if sp.simplify(after-before) != 0 or sp.simplify(actual-before) != 0:
                raise ValueError('El borde temporal coincide con un impulso del tren. Definí ese impulso y su peso por separado.')

    spans = []
    for branch, lower, upper in intervals:
        if branch == 0:
            continue
        first = lower if lower == -sp.oo else sp.ceiling((lower-origin)/period)
        last = upper if upper == sp.oo else sp.ceiling((upper-origin)/period)-1
        if (first.is_finite and not first.is_Integer) or (last.is_finite and not last.is_Integer):
            return None
        if first <= last:
            spans.append(TrainSpan(period, origin, area*branch, first, last))
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
                pulses[position]=pulses.get(position,sp.S.Zero)+span.weight
        zeros=[sp.simplify(weight).is_zero for weight in pulses.values()]
        if False in zeros:
            return False
        unknown=unknown or None in zeros
    return None if unknown else True


def _trim_canceled_tails(spans):
    """Replace canceling infinite families by their remaining finite edge contributions."""
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
    if span.first == -sp.oo and span.last == sp.oo:
        spacing = 2*sp.pi/span.period
        return spacing*span.weight*sp.exp(-sp.I*frequency*span.origin)*ImpulseTrain(frequency, spacing)
    edge, direction = (span.first, 1) if span.first.is_finite else (span.last, -1)
    weight = span.weight*sp.exp(-sp.I*frequency*(span.origin+span.period*edge))
    return _half_comb(weight, span.period, direction, frequency)


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
        if span.last == sp.oo:
            lower = sp.S.Zero
        if span.first == -sp.oo:
            upper = sp.S.Zero
        edge, direction = (span.first, 1) if span.first.is_finite else (span.last, -1)
        if edge.is_finite:
            terms.append(span.weight*sp.exp(-parameter*(span.origin+span.period*edge))
                         /(1-sp.exp(-direction*span.period*parameter)))
    return sp.Add(*terms), lower, upper
