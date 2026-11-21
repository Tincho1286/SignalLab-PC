"""Exact inverse of finite impulse sums and geometric impulse trains."""

import sympy as sp

from .gated_impulse_trains import TrainSpan, _trim_canceled_tails
from .harmonic_measures import _exponential_terms
from .jobs import checkpoint
from .periodic_signals import ImpulseTrain


class ImpulsePoleLine(ValueError):
    """The selected Laplace line crosses a pole of the impulse train."""


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
    """Normalize the denominator to 1 or 1-ratio*exp(-period*s)."""
    numerator, denominator = sp.fraction(sp.powsimp(value))
    weights = _modes(numerator, parameter)
    divisor = _modes(denominator, parameter)
    if weights is None or divisor is None or len(divisor) not in (1, 2):
        return None
    rate = next(iter(divisor))
    period = None
    ratio = sp.S.One
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
        ratio = sp.simplify(-divisor[other]/divisor[rate])
        if ratio.is_zero is not False or ratio.is_finite is not True:
            return None
        period = sp.simplify(rate - other)
    scale = divisor[rate]
    return period, ratio, {sp.simplify(rate - slope): sp.simplify(weight / scale) for slope, weight in weights.items()}


def _finite_cycle_branch(piece, parameter):
    # The direct calculation assigns the geometric polynomial its exact value
    # where the cycle ratio equals one. Strip it only when verified.
    if len(piece.args) != 2 or piece.args[1].cond is not sp.true:
        return None
    count, condition = piece.args[0]
    if count.is_Integer is not True or count.is_positive is not True or not isinstance(condition, sp.Eq):
        return None
    lhs, rhs = condition.args
    base = rhs if lhs == 1 else lhs if rhs == 1 else None
    if base is None or not base.has(sp.exp):
        return None
    ordinary = piece.args[1].expr
    pair = _geometric_terms(ordinary, parameter)
    if pair is None or pair[0] is None:
        return None
    period, ratio, terms = pair
    step = ratio*sp.exp(-parameter*period)
    if all(sp.simplify(base-step**direction) != 0 for direction in (-1, 1)):
        return None
    if set(terms) != {sp.S.Zero, period*count}:
        return None
    return ordinary if terms[0] == 1 and sp.simplify(terms[period*count]+ratio**count) == 0 else None


def _span_expression(span, time):
    period = span.period
    first = span.origin + period * span.first
    last = span.origin + period * span.last
    waveform = span.weight * sp.exp(span.rate*time) * ImpulseTrain(time - span.origin, period)
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

    spans = []
    impulses = {}
    for term in sp.Add.make_args(sp.expand_mul(value.xreplace(removable))):
        checkpoint()
        pair = _geometric_terms(term, parameter)
        if pair is None:
            return None
        period, ratio, weights = pair
        if period is not None:
            rate = sp.simplify(sp.log(ratio)/period)
            growth = sp.simplify(sp.log(sp.Abs(ratio))/period)
            if mode == 'line':
                distance = sp.simplify(sigma-growth)
                if distance.is_zero is not True and distance.is_positive is None:
                    return None
                # On a proposed pole line, continue to check if the tails cancel.
                right = distance.is_negative is not True
            else:
                right = mode == 'right'
        for start, area in weights.items():
            if period is None:
                impulses[start] = impulses.get(start, sp.S.Zero) + area
                continue
            origin = sp.Mod(start, period)
            offset = sp.simplify((start - origin) / period)
            if not offset.is_Integer:
                return None
            first, last = (offset, sp.oo) if right else (-sp.oo, offset - 1)
            weight = sp.simplify(area*sp.exp(-rate*start))
            spans.append(TrainSpan(period, origin, weight if right else -weight, first, last, rate))
    spans = _trim_canceled_tails(spans)
    if spans is None:
        return None
    impulses = {position: sp.simplify(weight) for position, weight in impulses.items()}
    for span in tuple(spans):
        if span.first == span.last:
            position = span.origin + span.period * span.first
            area = span.weight*sp.exp(span.rate*position)
            impulses[position] = sp.simplify(impulses.get(position, sp.S.Zero) + area)
            spans.remove(span)
    if unilateral and (any(position.is_negative and weight != 0 for position, weight in impulses.items()) or
                        any((span.origin + span.period * span.first).is_negative for span in spans)):
        raise ValueError('Esta expresión tiene impulsos en tiempos negativos. Elegí la interpretación bilateral para recuperarlos.')
    lower = sp.Max(-sp.oo, *(sp.re(span.rate) for span in spans if span.last == sp.oo))
    upper = sp.Min(sp.oo, *(sp.re(span.rate) for span in spans if span.first == -sp.oo))
    if mode == 'line' and ((sigma-lower).is_extended_positive is not True or (upper-sigma).is_extended_positive is not True):
        raise ImpulsePoleLine(f'La línea Re(s) = {sigma} pasa por los polos del tren. Elegí otro σ dentro de la ROC.')
    waveform = sp.Add(*(weight * sp.DiracDelta(time-position) for position, weight in impulses.items() if weight != 0),
                      *(_span_expression(span, time) for span in spans))
    return waveform, lower, upper
