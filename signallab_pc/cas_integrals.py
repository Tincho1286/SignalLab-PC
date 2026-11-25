"""CAS integration and summation conventions for real signals."""
import sympy as sp


def sum_on_indices(value, *limits):
    if isinstance(value,sp.Expr) and len(limits)==1 and isinstance(limits[0],(tuple,list,sp.Tuple)):
        coordinate,lower,upper = limits[0] if len(limits[0])==3 else (None,None,None)
        if (isinstance(coordinate,sp.Symbol) and coordinate.is_integer
                and (lower == -sp.oo or isinstance(lower,sp.Integer))
                and (upper == sp.oo or isinstance(upper,sp.Integer)) and lower<=upper
                and value.has(sp.Piecewise,sp.Heaviside,sp.KroneckerDelta)):
            from .z_direct_pairs import pieces
            from .jobs import checkpoint

            branches = pieces(value,lower,upper,index=coordinate)
            if branches is not None:
                terms = []
                for branch,start,stop in branches:
                    checkpoint()
                    if branch != 0:
                        terms.append(branch.subs(coordinate,start) if start==stop else
                                     sp.summation(branch,(coordinate,start,stop)))
                return sp.Add(*terms)
    return sp.summation(value,*limits)



def _dirac_integral(value,coordinate,start,stop,options):
    """Finite real endpoints use symmetric half weight; Laplace keeps 0−."""
    if not value.has(sp.DiracDelta):return None
    if not isinstance(coordinate,sp.Symbol) or not all(bound.is_extended_real is True for bound in (start,stop)):return None
    if start==stop:return sp.S.Zero
    direction=1 if (stop-start).is_positive is True else -1 if (stop-start).is_negative is True else None
    if direction is None:return None
    lower,upper=(start,stop) if direction==1 else (stop,start)
    from .impulse_pairs import affine_impulse,expand_real_impulses,impulse_integral
    terms=[]
    # expand_diracdelta handles simple non-affine real roots, when certified.
    expanded=expand_real_impulses(value,coordinate)
    for term in sp.Add.make_args(expanded):
        atoms=term.atoms(sp.DiracDelta)
        if not atoms:
            terms.append(_ordinary_integral(term,coordinate,lower,upper,options));continue
        if len(atoms)!=1:raise ValueError('No se define el producto de impulsos Dirac. Separá sus términos mediante una suma.')
        delta=next(iter(atoms));affine=affine_impulse(delta,coordinate)
        if affine is None:
            # Keep unresolved distributions explicit rather than trust an
            # ordinary integral that might discard their boundary contribution.
            terms.append(sp.Integral(term,(coordinate,lower,upper)));continue
        _,position=affine;order=delta.args[1] if len(delta.args)>1 else 0
        boundary=sp.Or(sp.Eq(position,lower),sp.Eq(position,upper))
        if order and boundary is not sp.false:
            raise ValueError('Una derivada de Dirac puede coincidir con un extremo de integración. Su peso en ese borde no tiene una convención ordinaria única; elegí límites que dejen el impulso estrictamente adentro o afuera.')
        answer=impulse_integral(term,coordinate,sp.S.One,lower,upper)
        if answer is None:terms.append(sp.Integral(term,(coordinate,lower,upper)));continue
        # Infinite endpoints cannot equal a finite affine root. The helper
        # uses complete endpoint weights; only this CAS adapter halves them.
        weight=sp.Piecewise((sp.S.Half,boundary),(1,True)) if not order else sp.S.One
        terms.append(answer*weight)
    return direction*sp.Add(*terms)


def _rational_divergence(value, coordinate, start, stop):
    if not (isinstance(value,sp.Expr) and isinstance(coordinate,sp.Symbol)
            and not value.free_symbols-{coordinate}
            and all(bound.is_real is True and bound.is_number for bound in (start,stop))
            and value.is_rational_function(coordinate)):
        return None
    if value.is_polynomial(coordinate):
        return None
    direction = sp.sign(stop-start)
    if direction not in (sp.S.One,sp.S.NegativeOne):
        return None
    low, high = (start,stop) if direction==1 else (stop,start)
    from .jobs import checkpoint
    checkpoint()
    try:
        num, den = sp.cancel(value).as_numer_denom()
        if not den.has(coordinate):
            return None
        checkpoint()
        numerator = sp.Poly(num,coordinate,extension=True)
        denominator = sp.Poly(den,coordinate,extension=True)
        if not all(c.is_real is True and not c.has(sp.Float)
                   for c in numerator.all_coeffs()+denominator.all_coeffs()):
            return None
        poles = denominator.real_roots(multiple=False)
    except (sp.PolynomialError,NotImplementedError):
        return None
    signs = set()
    for pole, order in poles:
        checkpoint()
        has_left, has_right = low < pole, pole < high
        if sp.Or(low > pole,pole > high) is sp.true:
            continue
        if not all(side in (sp.true,sp.false) for side in (has_left,has_right)):
            return None
        # Locally f(x) is c/(x-pole)^order. Each nonempty side diverges
        # with the sign of its leading term.
        leading = numerator.eval(pole)/denominator.diff((coordinate,order)).eval(pole)
        sign = sp.sign(leading)
        if sign not in (sp.S.One,sp.S.NegativeOne):
            return None
        if has_left:
            signs.add(sign*(-1)**order)
        if has_right:
            signs.add(sign)
    if len(signs)>1:
        return sp.nan
    if signs:
        return direction*signs.pop()*sp.oo
    return None


def _ordinary_integral(value,coordinate,start,stop,options):
    divergence = _rational_divergence(value,coordinate,start,stop)
    if divergence is not None:
        return divergence
    return sp.integrate(value,(coordinate,start,stop),**options)


def integrate(value,*limits,**options):
    bounds=tuple(limits[0]) if len(limits)==1 and isinstance(limits[0],(tuple,list,sp.Tuple)) and len(limits[0])==3 else limits if len(limits)==3 and isinstance(limits[0],sp.Symbol) else None
    if isinstance(value,sp.Expr) and bounds is not None:
        coordinate,start,stop=map(sp.sympify,bounds)
        answer=_dirac_integral(value,coordinate,start,stop,options)
        if answer is not None:return answer
        if value.has(sp.Mod) and isinstance(coordinate,sp.Symbol) and all(v.is_real is True and v.is_finite is True and not v.free_symbols for v in (start,stop)):
            if start==stop:return sp.S.Zero
            from .fourier_bands import _band_intervals
            low,high=sp.Min(start,stop),sp.Max(start,stop)
            bands=_band_intervals(value,coordinate,sp.Interval(low,high))
            if bands is not None:
                from .jobs import checkpoint
                totals=[]
                for amplitude,lower,upper in bands:
                    checkpoint()
                    if amplitude.has(coordinate):
                        totals.append(_ordinary_integral(amplitude,coordinate,lower,upper,options))
                    else:totals.append(amplitude*(upper-lower))
                return sp.Add(*totals) if start==low else -sp.Add(*totals)
        return _ordinary_integral(value,coordinate,start,stop,options)
    return sp.integrate(value,*limits,**options)
