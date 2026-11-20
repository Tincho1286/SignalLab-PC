"""Exact averages for finite sums of complex exponentials."""

import sympy as sp


def harmonic_power(value, variable):
    """Merge equal tones, including discrete aliases, before averaging |x|²."""
    if not value.has(variable):
        return sp.simplify(sp.Abs(value)**2)
    tones = []
    discrete = variable.is_integer is True
    for term in sp.Add.make_args(sp.expand(value.rewrite(sp.exp))):
        amplitude, varying = term.as_independent(variable, as_Add=False)
        exponent = sp.S.Zero
        for factor in sp.Mul.make_args(varying):
            if factor == 1:
                continue
            if factor.func == sp.exp:
                exponent += factor.args[0]
            elif factor.is_Pow and not factor.base.has(variable) and factor.base.is_zero is False:
                if factor.base.is_positive is not True and factor.exp.is_integer is not True:
                    return None
                exponent += factor.exp * sp.log(factor.base)
            else:
                return None
        exponent = sp.expand(exponent)
        slope = exponent.coeff(variable)
        phase = exponent - slope * variable
        frequency = sp.simplify(slope / sp.I)
        if phase.has(variable) or frequency.is_real is not True or frequency.free_symbols:
            return None
        coefficient = sp.simplify(amplitude * sp.exp(phase))
        for index, (other, weight) in enumerate(tones):
            difference = sp.simplify(frequency - other)
            equal = (difference / (2 * sp.pi)).is_integer if discrete else difference.is_zero
            if equal is None:
                return None
            if equal:
                tones[index] = (other, weight + coefficient)
                break
        else:
            tones.append((frequency, coefficient))
    return sp.simplify(sp.Add(*(sp.Abs(sp.simplify(weight))**2 for _, weight in tones)))
