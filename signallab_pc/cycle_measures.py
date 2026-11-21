"""Exact time averages of wrapped waveforms mixed with other spectral components."""

import sympy as sp

from .harmonic_measures import _exponential_terms, harmonic_power
from .jobs import checkpoint
from .periodic_fourier import _bounded_cycle
from .periodic_signals import continuous_periodic_components, cycle_weight, discrete_cycle, repeat


def cycle_mean_square(value, time, *, tail=0):
    """Average coherent terms together and omit transients certified to have zero power."""
    if tail:
        # A term of zero mean-square cannot contribute a nonzero cross average
        # with a bounded periodic component (Cauchy-Schwarz on each window).
        terms = sp.Add.make_args(sp.expand_mul(value))
        value = sp.Add(*(term for term in terms
                         if term.has(sp.Mod) or harmonic_power(term, time, tail=tail) != 0))
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



def discrete_cycle_mean_square(value, index, *, tail=0):
    """Include a tone in the cross average only when it coincides with a cycle bin."""
    if not value.has(sp.Mod) or value.free_symbols - {index}:
        return None
    periodic, tones = [], []
    for term in sp.Add.make_args(sp.expand_mul(value)):
        (periodic if term.has(sp.Mod) or not term.has(index) else tones).append(term)
    harmonic = sp.Add(*tones)
    tone_power = harmonic_power(harmonic, index, tail=tail)
    if tone_power is None:
        return None
    cycle = discrete_cycle(sp.Add(*periodic), index)
    if cycle is None:
        return None
    origin, samples = cycle
    period = len(samples)
    cross = sp.S.Zero
    for slope, amplitude in _exponential_terms(harmonic, index):
        checkpoint()
        if tail and (tail*sp.re(slope)).is_negative is True:
            continue
        frequency = sp.simplify(slope/sp.I)
        bin_index = sp.simplify(frequency*period/(2*sp.pi))
        if bin_index.is_integer is None:
            return None
        if bin_index.is_integer:
            cross += sp.conjugate(amplitude)*cycle_weight(
                cycle, origin, lambda n: sp.exp(-sp.I*frequency*n))
    own_power = sp.Add(*(sp.Abs(sample)**2 for sample in samples))/period
    result = sp.simplify(own_power + tone_power + 2*sp.re(cross)/period)
    return result if result.is_nonnegative is True and result.is_finite is True else None
