"""Finite integrals across explicit affine frequency folds."""
import sympy as sp


def integrate(value,*limits,**options):
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
