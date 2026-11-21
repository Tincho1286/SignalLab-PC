"""Exact time averages of wrapped waveforms mixed with other spectral components."""

import sympy as sp

from .harmonic_measures import _exponential_terms, harmonic_power
from .jobs import checkpoint
from .periodic_fourier import _bounded_cycle, periodic_laplace
from .periodic_signals import continuous_periodic_components, cycle_weight, discrete_cycle, repeat, wrapped_period
from .periodic_support import split_periodic_support


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
        return _mixed_wrapped_mean_square(value, time)

    groups = []
    mean = sp.S.Zero
    for period, expression in components:
        if period is None:
            mean += expression
            continue
        if not expression.has(sp.Mod):
            expression = repeat(expression, time, period)
        if not _add_to_cycle_group(groups, period, expression):
            return None

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


def _add_to_cycle_group(groups, period, expression):
    for basis, members in groups:
        rational = sp.simplify(period / basis).is_rational
        if rational is None:
            return False
        if rational:
            members.append(expression)
            return True
    groups.append((period, [expression]))
    return True


def _mixed_wrapped_mean_square(value, time):
    if not value.has(sp.Mod) or value.free_symbols - {time}:
        return None
    density = sp.expand_mul(value * sp.conjugate(value))
    moments = {}
    total = sp.S.Zero
    for term in sp.Add.make_args(density):
        checkpoint()
        constant, varying = term.as_independent(time, as_Add=False)
        groups = []
        for factor in sp.Mul.make_args(varying):
            if factor == 1:
                continue
            cycle = wrapped_period(factor, time)
            if cycle is None or not _add_to_cycle_group(groups, cycle[0], factor):
                return None
        # Irrationality of a period ratio guarantees the product average only
        # for two groups. Pairwise irrational ratios do not prove independence of three.
        if len(groups)>2:
            return None
        for _, members in groups:
            waveform = sp.Mul(*members)
            if waveform not in moments:
                cycle = _bounded_cycle(waveform, time)
                if cycle is None:
                    return None
                period, _, pieces, _ = cycle
                mean = sp.Add(*(sp.integrate(branch,(time,lo,hi)) for lo,hi,branch in pieces))/period
                if mean.is_finite is not True or mean.has(sp.Integral):
                    return None
                moments[waveform] = mean
            constant *= moments[waveform]
        total += constant
    result = sp.simplify(total)
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


def periodic_decay_energy(value, variable, accumulate):
    """Sum exponentially weighted cycles on each half-axis with a certified decay rate."""
    if not value.has(sp.Mod) or value.free_symbols - {variable}:
        return None
    parts = split_periodic_support(value, variable, preserve_addends=True)
    if parts is None:
        first = -1 if variable.is_integer else 0
        parts = [(value, -sp.oo, sp.Integer(first)), (value, sp.S.Zero, sp.oo)]
    areas = []
    for branch, lower, upper in parts:
        checkpoint()
        if branch == 0:
            continue
        density = sp.expand_mul(branch * sp.conjugate(branch))
        if lower.is_finite and upper.is_finite:
            area = accumulate(lower, upper, density)
        else:
            start, direction = (lower, 1) if upper == sp.oo else (upper, -1)
            area = _decaying_cycle_tail(density, variable, start, direction)
        if area is None or area.is_finite is not True:
            return None
        areas.append(area)
    energy = sp.simplify(sp.Add(*areas))
    return energy if energy.is_finite is True and energy.is_nonnegative is True else None


def _decaying_cycle_tail(density, variable, start, direction):
    areas = []
    discrete = variable.is_integer is True
    for term in sp.Add.make_args(density):
        checkpoint()
        periodic, exponential = [], []
        for factor in sp.Mul.make_args(term):
            (periodic if factor.has(sp.Mod) else exponential).append(factor)
        modes = _exponential_terms(sp.Mul(*exponential), variable)
        if modes is None:
            return None
        waveform = sp.Mul(*periodic).subs(variable, start + direction * variable)
        cycle = discrete_cycle(waveform, variable) if discrete and periodic else None
        if discrete and periodic and cycle is None:
            return None
        for slope, coefficient in modes:
            rate = direction * slope
            if sp.re(rate).is_negative is not True:
                return None
            if cycle is not None:
                first_cycle = cycle_weight(cycle, 0, lambda n: sp.exp(rate * n))
                weight = first_cycle / (1 - sp.exp(rate * len(cycle[1])))
            elif periodic:
                weight = periodic_laplace(waveform, variable, -rate)
            else:
                weight = 1 / (1 - sp.exp(rate)) if discrete else -1 / rate
            if weight is None:
                return None
            areas.append(coefficient * sp.exp(slope * start) * weight)
    return sp.Add(*areas)
