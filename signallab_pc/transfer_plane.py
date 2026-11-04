"""Shared H(s)/H(z) evaluation and explicitly selected digital annular ROC."""
from functools import lru_cache
import numpy as np
from .resources import ensure_working_set


@lru_cache(maxsize=32)
def _cancel_common(b,a,advance,domain="digital"):
    if not any(b):return (0j,),(1+0j,),0
    if len(a)==1:return None
    import sympy as sp
    z=sp.Symbol('s' if domain=='analog' else 'z');degree=max(len(b),len(a))
    ensure_working_set(degree*degree,bytes_per_sample=256,live_arrays=8)
    def number(v):return sp.Rational(float(v.real))+sp.I*sp.Rational(float(v.imag))
    bp=sp.Poly.from_list([number(v) for v in b]+([0]*(degree-len(b)) if domain=='digital' else []),z)
    ap=sp.Poly.from_list([number(v) for v in a]+([0]*(degree-len(a)) if domain=='digital' else []),z)
    if bp.is_zero:return (0j,),(1+0j,),0
    divisor=sp.gcd(bp,ap)
    if divisor.degree()==0:return None
    bc=[complex(v.evalf(17)) for v in bp.exquo(divisor).all_coeffs()]
    ac=[complex(v.evalf(17)) for v in ap.exquo(divisor).all_coeffs()]
    shift=max(0,len(bc)-len(ac)) if domain=='digital' else 0
    if domain=='digital':bc=[0j]*max(0,len(ac)-len(bc))+bc
    return tuple(bc),tuple(ac),advance+shift


@lru_cache(maxsize=32)
def _sos_factors(sections, advance):
    """Cancel factors of the stored sections over the exact binary rationals."""
    from collections import Counter
    import sympy as sp
    from .jobs import checkpoint

    if any(not any(row[:3]) for row in sections):
        return (), ()
    coordinate = sp.Symbol('z')
    numerator = Counter()
    denominator = Counter()
    for row in sections:
        checkpoint()
        for coefficients, factors in ((row[:3], numerator), (row[3:], denominator)):
            polynomial = sp.Poly.from_list([sp.Rational(value) for value in coefficients], coordinate, domain=sp.QQ)
            for factor, multiplicity in polynomial.factor_list()[1]:
                factors[factor.monic()] += multiplicity
    if advance:
        numerator[sp.Poly(coordinate, coordinate, domain=sp.QQ)] += advance
    return tuple((numerator-denominator).items()), tuple((denominator-numerator).items())


def _section_factors(system):
    return _sos_factors(tuple(tuple(float(v) for v in row) for row in system.sos), system.advance)


def _factor_roots(factors):
    roots = [np.tile(np.roots([float(value) for value in factor.all_coeffs()]), multiplicity)
             for factor, multiplicity in factors]
    return np.concatenate(roots).astype(complex) if roots else np.empty(0, dtype=complex)


def effective_system(system):
    """Cancel exact common polynomial factors; never match nearby roots."""
    if system.domain != 'digital' or system.sos is not None:
        return system
    reduced=_cancel_common(tuple(system.b),tuple(system.a),system.advance)
    if reduced is None:return system
    from .filters import Transfer
    b,a,advance=reduced
    return Transfer(b,a,system.domain,system.name,advance=advance,sample_period_s=system.sample_period_s,roc=system.roc)


def effective_plane_system(system):
    if system.domain=='digital':return effective_system(system)
    reduced=_cancel_common(tuple(system.b),tuple(system.a),0,'analog')
    if reduced is None:return system
    from .filters import Transfer
    b,a,_=reduced
    return Transfer(b,a,'analog',system.name,roc=system.roc)


def convergence(system):
    if system.domain!='digital':return analog_convergence(system)
    system=effective_system(system)
    from .filters import validate_roc
    specification=validate_roc(system.roc,system.domain)
    if specification is None:return {'known':False,'unit':None,'text':'ROC no especificada. La expresión racional por sí sola no determina el soporte de h[n].'}
    poles=plane_poles(system);radii=np.abs(poles);radii=radii[radii>0]
    from fractions import Fraction
    if system.sos is not None:
        _, denominator = _section_factors(system)
        endpoint_pole = any(factor.eval(z) == 0 for factor, _ in denominator for z in (1, -1))
    else:
        endpoint_pole=any(sum((Fraction(float(c.real))*(q**i) for i,c in enumerate(system.a)),Fraction(0))==0 and sum((Fraction(float(c.imag))*(q**i) for i,c in enumerate(system.a)),Fraction(0))==0 for q in (1,-1))
    mode=specification['mode'];radius=specification.get('radius')
    if mode=='radius' and radius==1 and endpoint_pole:raise ValueError('El radio 1 atraviesa un polo exacto en z=1 o z=−1; no es interior a una ROC.')
    if mode=='right':inner=float(radii.max(initial=0));outer=np.inf
    elif mode=='left':inner=0.;outer=float(radii.min()) if radii.size else np.inf
    else:
        if np.any(np.isclose(radii,radius,rtol=64*np.finfo(float).eps,atol=0)):
            raise ValueError('El radio elegido coincide numéricamente con un polo. Elegí un punto interior a la ROC.')
        inner=float(radii[radii<radius].max(initial=0));above=radii[radii>radius];outer=float(above.min()) if above.size else np.inf
    # A numerical root very close to the unit circle cannot certify inclusion.
    boundary=bool(endpoint_pole or np.any(np.isclose(radii,1,rtol=64*np.finfo(float).eps,atol=0)))
    unit=bool(inner<1<outer and not boundary)
    zero_included=inner==0 and bool(np.isfinite(evaluate_plane(system,np.array([0j]))[0]))
    text=f'{inner:.12g} '+('≤' if zero_included else '<')+' |z| < '+('∞' if np.isinf(outer) else f'{outer:.12g}')
    text+='; los bordes con polos no se incluyen.'
    return {'known':True,'zero_included':zero_included,'inner':inner,'outer':outer,'unit':unit,'boundary':boundary,'text':text,'poles':poles}


def evaluate_plane(system,z):
    system=effective_plane_system(system)
    z=np.asarray(z,dtype=complex)
    with np.errstate(all='ignore'):
        if system.domain=='analog':
            value=np.polyval(system.b,z)/np.polyval(system.a,z)
        elif system.sos is not None:
            q = np.divide(1, z, out=np.zeros_like(z), where=z != 0)
            value = z**system.advance
            for row in system.sos:
                value = value * np.polynomial.polynomial.polyval(q, row[:3]) / np.polynomial.polynomial.polyval(q, row[3:])
            # The z=0 limit must use the exact section products, including delays.
            value = np.where(z != 0, value, complex(np.nan, np.nan))
        else:
            # Positive-power polynomials avoid artificial 1/0 singularities at z=0.
            degree=max(len(system.b),len(system.a))
            b=np.pad(system.b,(0,degree-len(system.b)+system.advance));a=np.pad(system.a,(0,degree-len(system.a)))
            while len(a)>1 and a[-1]==0 and b[-1]==0:a=a[:-1];b=b[:-1]
            value=np.polyval(b,z)/np.polyval(a,z)
    if system.domain=='analog':bb,aa=system.b,system.a
    else:
        degree=max(len(system.b),len(system.a));bb=np.pad(system.b,(0,degree-len(system.b)+system.advance));aa=np.pad(system.a,(0,degree-len(system.a)))
    with np.errstate(all='ignore'):
        denominator=np.polyval(aa,z);bound=np.polyval(abs(aa),abs(z))
        uncertain=abs(denominator)<=(32+8*len(aa))*np.finfo(float).eps*bound
    from .rational_frequency import repair_plane
    value=repair_plane(system,z,value,~np.isfinite(value)|(value==0)|uncertain|~np.isfinite(bound))
    return np.where(np.isfinite(value),value,complex(np.nan,np.nan))




def plane_roots(system):
    if system.sos is not None:
        zeros, poles = _section_factors(system)
        return _factor_roots(zeros), _factor_roots(poles)
    zeros,poles=effective_plane_system(system).poles_zeros()
    zero_indices=np.flatnonzero(zeros==0);pole_indices=np.flatnonzero(poles==0)
    common=min(len(zero_indices),len(pole_indices))
    return np.delete(zeros,zero_indices[:common]),np.delete(poles,pole_indices[:common])


def analog_convergence(system):
    system=effective_plane_system(system)
    from .filters import validate_roc
    specification=validate_roc(system.roc,'analog')
    if specification is None:return {'known':False,'unit':None,'text':'ROC no especificada. H(s) por sí sola no determina el soporte de h(t).'}
    poles=plane_poles(system);real=poles.real;mode=specification['mode']
    if mode=='right':lower=float(real.max()) if real.size else -np.inf;upper=np.inf
    elif mode=='left':lower=-np.inf;upper=float(real.min()) if real.size else np.inf
    else:
        sigma=specification['sigma']
        tolerance=64*np.finfo(float).eps*np.maximum(abs(poles),np.finfo(float).tiny)
        if np.any(abs(real-sigma)<=tolerance):raise ValueError('La línea σ elegida atraviesa numéricamente un polo. Elegí una línea interior a la ROC.')
        below=real[real<sigma];above=real[real>sigma]
        lower=float(below.max()) if below.size else -np.inf;upper=float(above.min()) if above.size else np.inf
    boundary=bool(np.any(abs(real)<=64*np.finfo(float).eps*np.maximum(abs(poles),np.finfo(float).tiny)))
    unit=bool(lower<0<upper and not boundary)
    text=('−∞' if np.isneginf(lower) else f'{lower:.12g}')+' < Re(s) < '+('∞' if np.isposinf(upper) else f'{upper:.12g}')+'; los polos no se incluyen.'
    return {'known':True,'inner':lower,'outer':upper,'unit':unit,'boundary':boundary,'text':text,'poles':poles}


def plane_poles(system):
    """Only denominator roots: ROC classification never needs FIR zeros."""
    if system.sos is not None:
        return _factor_roots(_section_factors(system)[1])
    else:
        order=max(0,len(system.a)-1);ensure_working_set(order*order,live_arrays=4)
        poles=np.roots(system.a)
    if system.domain=='digital' and system.advance:
        ids=np.flatnonzero(poles==0);poles=np.delete(poles,ids[:system.advance])
    return poles
