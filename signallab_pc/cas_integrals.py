"""Finite integrals across explicit affine frequency folds."""
import sympy as sp



def _dirac_integral(value,coordinate,start,stop,options):
    """Finite real endpoints use symmetric half weight; Laplace keeps 0−."""
    if not value.has(sp.DiracDelta):return None
    if not isinstance(coordinate,sp.Symbol) or not all(bound.is_extended_real is True for bound in (start,stop)):return None
    if start==stop:return sp.S.Zero
    direction=1 if (stop-start).is_positive is True else -1 if (stop-start).is_negative is True else None
    if direction is None:return None
    lower,upper=(start,stop) if direction==1 else (stop,start)
    from .impulse_pairs import affine_impulse,impulse_integral
    terms=[]
    # expand_diracdelta handles simple non-affine real roots, when certified.
    expanded=sp.expand_mul(value.expand(diracdelta=True,wrt=coordinate))
    for term in sp.Add.make_args(expanded):
        atoms=term.atoms(sp.DiracDelta)
        if not atoms:
            terms.append(sp.integrate(term,(coordinate,lower,upper),**options));continue
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


def integrate(value,*limits,**options):
    if isinstance(value,sp.Expr) and value.has(sp.DiracDelta):
        bounds=tuple(limits[0]) if len(limits)==1 and isinstance(limits[0],(tuple,list,sp.Tuple)) and len(limits[0])==3 else limits if len(limits)==3 else None
        if bounds is not None:
            coordinate,start,stop=map(sp.sympify,bounds)
            answer=_dirac_integral(value,coordinate,start,stop,options)
            if answer is not None:return answer
    if (isinstance(value,sp.Expr) and value.has(sp.Mod)
            and len(limits)==1 and isinstance(limits[0],(tuple,list,sp.Tuple)) and len(limits[0])==3):
        coordinate,start,stop=limits[0]
        if isinstance(coordinate,sp.Symbol) and all(v.is_real is True and v.is_finite is True and not v.free_symbols for v in (start,stop)):
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
                        totals.append(sp.integrate(amplitude,(coordinate,lower,upper),**options))
                    else:totals.append(amplitude*(upper-lower))
                return sp.Add(*totals) if start==low else -sp.Add(*totals)
    return sp.integrate(value,*limits,**options)
