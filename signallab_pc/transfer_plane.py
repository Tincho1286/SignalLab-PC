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


def effective_system(system):
    """Cancel exact common polynomial factors; never match nearby roots."""
    if system.domain!='digital':return system
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
    return Transfer(b,a,'analog',system.name)


def convergence(system):
    if system.domain!='digital':return {'known':False,'unit':None,'text':'La ROC anular corresponde a H(z).'}
    system=effective_system(system)
    from .filters import validate_roc
    specification=validate_roc(system.roc,system.domain)
    if specification is None:return {'known':False,'unit':None,'text':'ROC no especificada. La expresión racional por sí sola no determina el soporte de h[n].'}
    zeros,poles=system.poles_zeros();radii=np.abs(poles);radii=radii[radii>0]
    from fractions import Fraction
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
    return {'known':True,'zero_included':zero_included,'inner':inner,'outer':outer,'unit':unit,'text':text,'zeros':zeros,'poles':poles}


def evaluate_plane(system,z):
    system=effective_plane_system(system)
    z=np.asarray(z,dtype=complex)
    with np.errstate(all='ignore'):
        if system.domain=='analog':
            value=np.polyval(system.b,z)/np.polyval(system.a,z)
        elif system.sos is not None and not np.any(z==0):
            q=1/z;value=z**system.advance
            for row in system.sos:value=value*np.polynomial.polynomial.polyval(q,row[:3])/np.polynomial.polynomial.polyval(q,row[3:])
        else:
            # Positive-power polynomials avoid artificial 1/0 singularities at z=0.
            degree=max(len(system.b),len(system.a))
            b=np.pad(system.b,(0,degree-len(system.b)+system.advance));a=np.pad(system.a,(0,degree-len(system.a)))
            while len(a)>1 and a[-1]==0 and b[-1]==0:a=a[:-1];b=b[:-1]
            value=np.polyval(b,z)/np.polyval(a,z)
    return np.where(np.isfinite(value),value,complex(np.nan,np.nan))




def plane_roots(system):
    zeros,poles=effective_plane_system(system).poles_zeros()
    zero_indices=np.flatnonzero(zeros==0);pole_indices=np.flatnonzero(poles==0)
    common=min(len(zero_indices),len(pole_indices))
    return np.delete(zeros,zero_indices[:common]),np.delete(poles,pole_indices[:common])
