"""Coordinates and phase factors for discrete Fourier grids."""
from fractions import Fraction
import math

import numpy as np

from .jobs import checkpoint


def bin_frequency(index, length):
    return (index/length)*math.tau


def bin_range(start, stop, length):
    """Inclusive bounds in the same coordinate convention used to plot bins."""
    low, high = (start/math.tau)*length, (stop/math.tau)*length
    if max(abs(low), abs(high)) >= 2**52:
        raise ValueError('El intervalo excede la precisión de las frecuencias de la DFT.')
    first, last = math.ceil(low), math.floor(high)
    while bin_frequency(first-1, length) >= start:
        first -= 1
    while bin_frequency(first, length) < start:
        first += 1
    while bin_frequency(last+1, length) <= stop:
        last += 1
    while bin_frequency(last, length) > stop:
        last -= 1
    return first, last


def _simple_cycles(angle):
    if abs(angle) > 1e4:
        return None
    value = Fraction(angle/math.tau).limit_denominator(4096)
    return value if float(value)*math.tau == angle else None


def _cycles_grid(start, stop, count):
    first, last = _simple_cycles(start), _simple_cycles(stop)
    if first is None or last is None:
        return None
    step = (last-first)/(count-1)
    denominator = math.lcm(first.denominator, step.denominator)
    return int(first*denominator), int(step*denominator), denominator


def _angles(count, first, step, denominator, multiplier):
    offset = first*multiplier % denominator
    increment = step*multiplier % denominator
    half = denominator//2
    return np.fromiter(((((offset+j*increment+half)%denominator)-half)/denominator*math.tau
                        for j in range(count)), dtype=float, count=count)


def dtft_angles(omega, start, stop, origin):
    """Small local angles and a separate phase shift for the integer origin."""
    cycles = _cycles_grid(start, stop, len(omega))
    if cycles is not None:
        local = _angles(len(omega), *cycles, 1)
        shift = _angles(len(omega), *cycles, origin) if origin else np.zeros_like(omega)
        return local, np.exp(-1j*shift)

    if max(abs(start), abs(stop)) <= math.tau and max(abs(start*origin), abs(stop*origin)) < 1e4:
        return omega, np.exp(-1j*omega*origin)

    # The generic axis represents radian floats, not guessed rational multiples
    # of pi. Reduce its exact binary values before multiplying large indices.
    import mpmath
    precision = max(50, math.frexp(max(abs(start), abs(stop), 1))[1]//3+45)
    context = mpmath.mp.clone()
    context.dps = precision
    period = 2*context.pi
    local = np.empty_like(omega)
    shift = np.empty_like(omega)
    for index, angle in enumerate(omega):
        if index % 64 == 0:
            checkpoint()
        simple = _simple_cycles(float(angle))
        if simple is not None:
            local[index] = float(simple % 1)*math.tau
            shift[index] = float((simple*origin) % 1)*math.tau
        else:
            value = context.mpf(float(angle))
            local[index] = float(context.fmod(value, period))
            shift[index] = float(context.fmod(value*origin, period))
    return local, np.exp(-1j*shift)


def dft_origin_phase(indices, length, origin):
    offset = origin % length
    if length <= math.isqrt(np.iinfo(np.int64).max):
        cycles = ((indices % length)*offset % length)/length
    else:
        cycles = np.fromiter(((int(index)*offset % length)/length for index in indices),
                             dtype=float, count=len(indices))
    return np.exp(-1j*math.tau*cycles)
