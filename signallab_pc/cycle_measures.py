"""Exact time averages of bounded continuous waveforms with several periods."""

import sympy as sp

from .jobs import checkpoint
from .periodic_fourier import _bounded_cycle
from .periodic_signals import continuous_periodic_components, repeat


def cycle_mean_square(value, time):
    """Average coherent terms together and use zero cross-covariance between period groups."""
    components = continuous_periodic_components(value, time)
    if components is None:
        return None

    groups = []
    mean = sp.S.Zero
    for period, expression in components:
        if period is None:
            mean += expression
            continue
        if not expression.has(sp.Mod):
            expression = repeat(expression, time, period)
        for basis, members in groups:
            rational = sp.simplify(period / basis).is_rational
            if rational is None:
                return None
            if rational:
                members.append(expression)
                break
        else:
            groups.append((period, [expression]))

    variance = sp.S.Zero
    for _, members in groups:
        checkpoint()
        waveform = sp.Add(*members)
        if not waveform.has(time):
            mean += waveform
            continue
        cycle = _bounded_cycle(waveform, time)
        if cycle is None:
            return None
        period, _, pieces, _ = cycle
        areas, squared_areas = [], []
        for lower, upper, branch in pieces:
            checkpoint()
            limits = time, lower, upper
            areas.append(sp.integrate(branch, limits))
            squared_areas.append(sp.integrate(sp.simplify(branch * sp.conjugate(branch)), limits))
        average = sp.simplify(sp.Add(*areas) / period)
        mean_square = sp.simplify(sp.Add(*squared_areas) / period)
        if any(moment.is_finite is not True or moment.has(sp.Integral) for moment in (average, mean_square)):
            return None
        mean += average
        variance += mean_square - sp.Abs(average)**2

    # Nonzero harmonics of groups whose period ratio is irrational never share
    # a frequency. Averaging the squared modulus preserves their DC cross terms.
    result = sp.simplify(variance + sp.Abs(sp.simplify(mean))**2)
    return result if result.is_nonnegative is True and result.is_finite is True else None
