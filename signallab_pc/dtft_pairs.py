"""Sinc/rectangle DTFT pairs with real shifts, frequency images and assigned samples."""
import sympy as sp
from .symbolic import N,W
from .z_direct_pairs import pieces


def direct(expression):
    parts=pieces(expression,-sp.oo,sp.oo,preserve_structure=True)
    if parts is None:return None
    infinite=[value for value,lo,hi in parts if lo==-sp.oo or hi==sp.oo]
    if not infinite:return None
    generic=infinite[0]
    if any(sp.simplify(value-generic)!=0 for value in infinite):return None
    # Integer-index identities may erase the ordinary branch, but never the
    # isolated samples already separated above. Keep other phases intact.
    if sp.simplify(generic)==0:generic=sp.S.Zero
    spectrum=sp.S.Zero
    if generic!=0:
        for term in sp.Add.make_args(sp.expand_mul(generic)):
            trigonometric=[node for node in term.atoms(sp.sin,sp.cos) if node.has(N)]
            if len(trigonometric)!=1:return None
            sine=trigonometric[0]
            argument=sine.args[0]+(sp.pi/2 if sine.func==sp.cos else 0)
            try:phase=sp.Poly(argument,N)
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
                    if root.is_real is True and root.is_finite is True:delay=root;break
            if delay is None or a.is_real is not True or width.is_positive is not True or width.is_finite is not True:return None
            turns=sp.simplify(phase.eval(delay)/sp.pi)
            if not isinstance(turns,sp.Integer):return None
            coefficient=sp.simplify(term*(N-delay)/sine)*(-1)**turns
            carrier=sp.S.Zero
            if coefficient.has(N):
                rate=sp.simplify(sp.diff(coefficient,N)/coefficient)
                if rate.has(N) or (rate/sp.I).is_real is not True:return None
                carrier=sp.simplify(rate/sp.I)
                coefficient=sp.simplify(coefficient*sp.exp(-rate*N))
                if coefficient.has(N):return None
            frequency=W-carrier
            theta=sp.Mod(frequency+sp.pi,2*sp.pi)-sp.pi
            if (sp.pi-width).is_positive is True:aliases=(0,)
            else:
                count=sp.ceiling((width+sp.pi)/(2*sp.pi))
                if not isinstance(count,sp.Integer):return None
                from .resources import ensure_working_set
                ensure_working_set(2*int(count)+1,bytes_per_sample=4096,live_arrays=8)
                aliases=range(-int(count),int(count)+1)
            for alias in aliases:
                from .jobs import checkpoint
                checkpoint()
                folded=theta+2*sp.pi*alias
                # Integer shifts are periodic already. Fractional centres
                # require the phase of each continuous-frequency image.
                phase_frequency=frequency if isinstance(delay,sp.Integer) else folded
                height=coefficient*sp.pi*sp.sign(a)*sp.exp(-sp.I*phase_frequency*delay)
                spectrum+=sp.Piecewise((height,sp.Abs(folded)<width),(height/2,sp.Eq(sp.Abs(folded),width)),(0,True))
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
