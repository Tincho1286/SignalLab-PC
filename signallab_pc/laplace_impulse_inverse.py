"""Exact inverse of finite impulse sums and constant-weight geometric trains."""

import sympy as sp

from .gated_impulse_trains import TrainSpan, _trim_canceled_tails
from .harmonic_measures import _exponential_terms
from .jobs import checkpoint
from .periodic_signals import ImpulseTrain


def _modes(value, parameter):
    terms = _exponential_terms(value, parameter)
    if terms is None:
        return None
    combined = {}
    for slope, weight in terms:
        if slope.is_real is not True or slope.is_finite is not True or weight.is_finite is not True:
            return None
        combined[slope] = combined.get(slope, sp.S.Zero) + weight
    return {slope: weight for slope, weight in combined.items() if weight != 0}


def _geometric_terms(value, parameter):
    """Normalize the denominator to 1 or 1-exp(-period*s)."""
    numerator, denominator = sp.fraction(sp.powsimp(value))
    weights = _modes(numerator, parameter)
    divisor = _modes(denominator, parameter)
    if weights is None or divisor is None or len(divisor) not in (1, 2):
        return None
    rate = next(iter(divisor))
    period = None
    if len(divisor) == 2:
        first, second = divisor
        difference = sp.simplify(first - second)
        if difference.is_zero is not False or difference.is_real is not True:
            return None
        if difference.is_positive:
            rate, other = first, second
        elif difference.is_negative:
            rate, other = second, first
        else:
            return None
        if sp.simplify(divisor[rate] + divisor[other]) != 0:
            return None
        period = sp.simplify(rate - other)
    scale = divisor[rate]
    return period, {sp.simplify(rate - slope): sp.simplify(weight / scale) for slope, weight in weights.items()}


def _finite_cycle_branch(piece, parameter):
    # The direct calculation assigns the geometric polynomial its exact value
    # where exp(-s*P)=1. Strip that branch only when the assignment is certified.
    if len(piece.args) != 2 or piece.args[1].cond is not sp.true:
        return None
    count, condition = piece.args[0]
    if count.is_Integer is not True or count.is_positive is not True or not isinstance(condition, sp.Eq):
        return None
    lhs, rhs = condition.args
    base = rhs if lhs == 1 else lhs if rhs == 1 else None
    if base is None or base.func != sp.exp:
        return None
    ordinary = piece.args[1].expr
    pair = _geometric_terms(ordinary, parameter)
    if pair is None or pair[0] is None:
        return None
    period, terms = pair
    if all(sp.simplify(base.args[0] + direction*parameter*period) != 0 for direction in (-1,1)):
        return None
    return ordinary if terms == {sp.S.Zero: sp.S.One, period * count: sp.S.NegativeOne} else None


def _span_expression(span, time):
    period = span.period
    first = span.origin + period * span.first
    last = span.origin + period * span.last
    waveform = span.weight * ImpulseTrain(time - span.origin, period)
    if first.is_finite:
        waveform *= sp.Heaviside(time - first + period / 2, 1)
    if last.is_finite:
        waveform *= sp.Heaviside(last + period / 2 - time, 1)
    return waveform


def inverse_impulse_laplace(value, parameter, time, *, mode='right', sigma=sp.S.Zero, unilateral=False):
    if not value.has(sp.exp) or value.free_symbols - {parameter}:
        return None
    removable = {}
    for piece in value.atoms(sp.Piecewise):
        branch = _finite_cycle_branch(piece, parameter)
        if branch is None:
            return None
        removable[piece] = branch

    right = mode == 'right' or (mode == 'line' and sigma.is_negative is not True)
    spans = []
    impulses = {}
    for term in sp.Add.make_args(sp.expand_mul(value.xreplace(removable))):
        checkpoint()
        pair = _geometric_terms(term, parameter)
        if pair is None:
            return None
        period, weights = pair
        for start, area in weights.items():
            if period is None:
                impulses[start] = impulses.get(start, sp.S.Zero) + area
                continue
            origin = sp.Mod(start, period)
            offset = sp.simplify((start - origin) / period)
            if not offset.is_Integer:
                return None
            first, last = (offset, sp.oo) if right else (-sp.oo, offset - 1)
            spans.append(TrainSpan(period, origin, area if right else -area, first, last))
    spans = _trim_canceled_tails(spans)
    if spans is None:
        return None
    impulses = {position: sp.simplify(weight) for position, weight in impulses.items()}
    for span in tuple(spans):
        if span.first == span.last:
            position = span.origin + span.period * span.first
            impulses[position] = sp.simplify(impulses.get(position, sp.S.Zero) + span.weight)
            spans.remove(span)
    if unilateral and (any(position.is_negative and weight != 0 for position, weight in impulses.items()) or
                        any((span.origin + span.period * span.first).is_negative for span in spans)):
        raise ValueError('Esta expresión tiene impulsos en tiempos negativos. Elegí la interpretación bilateral para recuperarlos.')
    has_right = any(span.last == sp.oo for span in spans)
    has_left = any(span.first == -sp.oo for span in spans)
    if mode == 'line' and ((has_right and sigma.is_positive is not True) or (has_left and sigma.is_negative is not True)):
        raise ValueError('La línea Re(s) = 0 pasa por los polos del tren. Elegí σ positivo o negativo según la ROC.')
    waveform = sp.Add(*(weight * sp.DiracDelta(time-position) for position, weight in impulses.items() if weight != 0),
                      *(_span_expression(span, time) for span in spans))
    return waveform, sp.S.Zero if has_right else -sp.oo, sp.S.Zero if has_left else sp.oo
