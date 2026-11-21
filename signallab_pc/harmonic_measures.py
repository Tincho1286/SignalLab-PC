"""Exact averages for finite sums of complex exponentials."""

import sympy as sp


def _exponential_terms(value, variable):
    terms = []
    for term in sp.Add.make_args(sp.expand(value.rewrite(sp.exp))):
        if term == 0:
            continue
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
        phase = sp.expand(exponent - slope * variable)
        if phase.has(variable):
            return None
        coefficient = sp.simplify(amplitude * sp.exp(phase))
        terms.append((slope,coefficient))
    return terms


def harmonic_power(value, variable, *, tail=0):
    """Merge coherent tones, allowing vanishing terms on a specified tail."""
    terms=_exponential_terms(value,variable)
    if terms is None:return None
    tones=[];discrete=variable.is_integer is True
    for slope,coefficient in terms:
        if tail and (tail*sp.re(slope)).is_negative is True:continue
        frequency=sp.simplify(slope/sp.I)
        if frequency.is_real is not True or frequency.free_symbols:return None
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
    powers = []
    for _, weight in tones:
        weight = sp.simplify(weight)
        if weight.is_number and weight.is_real is not True:
            # At DC and Nyquist, conjugate tones collapse onto one discrete
            # frequency. Resolve exact roots of unity before taking the norm.
            real, imaginary = weight.as_real_imag()
            powers.append(sp.simplify(real)**2 + sp.simplify(imaginary)**2)
        else:
            powers.append(sp.Abs(weight)**2)
    return sp.simplify(sp.Add(*powers))


def _intervals(value,variable):
    if variable.is_integer:
        from .z_direct_pairs import pieces

        intervals = pieces(value, -sp.oo, sp.oo)
        if intervals is None:
            return None
    else:
        piecewise = sp.piecewise_fold(value.rewrite(sp.Piecewise))
        if not isinstance(piecewise, sp.Piecewise):
            return [(piecewise,-sp.oo,sp.oo)]
        try:
            regions = piecewise.as_expr_set_pairs(domain=sp.S.Reals)
        except (NotImplementedError, TypeError, ValueError):
            return None
        if sp.Union(*(region for _, region in regions)) != sp.S.Reals:
            return None
        intervals = []
        for amplitude, region in regions:
            for part in (region.args if isinstance(region, sp.Union) else (region,)):
                if part == sp.S.EmptySet or isinstance(part, sp.FiniteSet):
                    continue
                if not isinstance(part, sp.Interval):
                    return None
                intervals.append((amplitude, part.start, part.end))

    return intervals


def exponential_energy(density,variable,accumulate):
    """Integrate or sum density terms whose exponential decay is certified."""
    intervals=_intervals(density,variable)
    if intervals is None:return None
    terms=[];discrete=variable.is_integer is True
    for value,low,high in intervals:
        if value==0:continue
        if low.is_finite and high.is_finite:
            term=accumulate(low,high,value)
            if term.is_finite is not True:return None
            terms.append(term)
            continue
        if low==-sp.oo and high==sp.oo:return None
        expanding=_exponential_terms(value,variable)
        if expanding is None:return None
        direction=1 if high==sp.oo else -1
        start=low if direction==1 else high
        for rate,weight in expanding:
            if (direction*sp.re(rate)).is_negative is not True:return None
            divisor=1-sp.exp(direction*rate) if discrete else -direction*rate
            terms.append(weight*sp.exp(rate*start)/divisor)
    result=sp.simplify(sp.re(sp.Add(*terms)))
    return result if result.is_finite is True and result.is_nonnegative is True else None


def piecewise_harmonic_power(value, variable, accumulate):
    """Separate half-axis averages once all bounded contributions are finite."""
    if not value.has(sp.Piecewise, sp.Heaviside, sp.Abs):return None
    intervals=_intervals(value,variable)
    if intervals is None:return None
    left = right = None
    for amplitude, low, high in intervals:
        if low == -sp.oo or high == sp.oo:
            if low == -sp.oo:
                left = harmonic_power(amplitude, variable, tail=-1)
                if left is None:return None
            if high == sp.oo:
                right = harmonic_power(amplitude, variable, tail=1)
                if right is None:return None
        else:
            total = accumulate(low, high, sp.simplify(sp.Abs(amplitude)**2))
            if total.is_finite is not True:
                return None
    return sp.simplify((left+right)/2) if left is not None and right is not None else None


def rational_tail_measures(density, variable):
    """Use degrees to decide divergent energy and its symmetric mean."""
    intervals=_intervals(density,variable)
    if intervals is None:return None
    discrete=variable.is_integer is True
    averages={};diverges=False
    for value,low,high in intervals:
        if value.free_symbols-{variable} or not value.is_rational_function(variable):return None
        numerator,denominator=map(lambda part:sp.Poly(part,variable),sp.fraction(sp.cancel(value)))
        if denominator.degree():
            axis=sp.Dummy('axis',real=True)
            poles=sp.solveset(denominator.as_expr().xreplace({variable:axis}),axis,domain=sp.S.Reals)
            if poles is not sp.S.EmptySet and not isinstance(poles,sp.FiniteSet):return None
            for pole in poles:
                inside=sp.simplify(sp.And(pole>=low,pole<=high))
                if inside is sp.false:continue
                if inside is not sp.true:return None
                if discrete:
                    if pole.is_integer is not False:return None
                else:return sp.oo,sp.oo
        degree=numerator.degree()-denominator.degree()
        for direction,unbounded in ((-1,low==-sp.oo),(1,high==sp.oo)):
            if unbounded:
                diverges=diverges or degree>=-1
                averages[direction]=sp.oo if degree>0 else numerator.LC()/denominator.LC() if degree==0 else sp.S.Zero
    if diverges and len(averages)==2:
        return sp.oo,sp.simplify((averages[-1]+averages[1])/2)
    return None
