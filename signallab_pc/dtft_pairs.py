"""Sinc/rectangle DTFT pair with exact integer shifts and assigned samples."""
import sympy as sp
from .symbolic import N,W
from .z_direct_pairs import pieces


def direct(expression):
    parts=pieces(expression,-sp.oo,sp.oo)
    if parts is None:return None
    infinite=[value for value,lo,hi in parts if lo==-sp.oo or hi==sp.oo]
    if not infinite:return None
    generic=infinite[0]
    if any(sp.simplify(value-generic)!=0 for value in infinite):return None
    spectrum=sp.S.Zero
    if generic!=0:
        theta=sp.Mod(W+sp.pi,2*sp.pi)-sp.pi
        for term in sp.Add.make_args(sp.expand_mul(generic)):
            sines=list(term.atoms(sp.sin))
            if len(sines)!=1:return None
            sine=sines[0]
            try:phase=sp.Poly(sine.args[0],N)
            except sp.PolynomialError:return None
            if phase.degree()!=1:return None
            a=phase.nth(1);width=sp.Abs(a);delay=None
            for factor in sp.Mul.make_args(term):
                base,exponent=factor.as_base_exp()
                if exponent!=-1:continue
                try:denominator=sp.Poly(base,N)
                except sp.PolynomialError:continue
                if denominator.degree()==1:
                    root=sp.cancel(-denominator.nth(0)/denominator.nth(1))
                    if isinstance(root,sp.Integer):delay=root;break
            if delay is None or a.is_real is not True or width.is_positive is not True or (sp.pi-width).is_positive is not True:return None
            turns=sp.simplify(phase.eval(delay)/sp.pi)
            if not isinstance(turns,sp.Integer):return None
            coefficient=sp.simplify(term*(N-delay)/sine)*(-1)**turns
            if coefficient.has(N):return None
            height=coefficient*sp.pi*sp.sign(a)*sp.exp(-sp.I*W*delay)
            spectrum+=sp.Piecewise((height,sp.Abs(theta)<width),(height/2,sp.Eq(sp.Abs(theta),width)),(0,True))
    real=sp.Dummy('coordinate',real=True)
    for value,lo,hi in parts:
        if lo==-sp.oo or hi==sp.oo or sp.simplify(value-generic)==0:continue
        if lo!=hi:return None
        expected=generic.subs(N,lo)
        if expected.has(sp.nan,sp.zoo,sp.oo):expected=sp.limit(generic.xreplace({N:real}),real,lo)
        if expected.is_finite is False or expected.has(sp.Limit,sp.nan,sp.zoo,sp.oo):return None
        actual=value.subs(N,lo)
        spectrum+=(actual-expected)*sp.exp(-sp.I*W*lo)
    return spectrum
