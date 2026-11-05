"""Ordinary Fourier pairs and properties before generic symbolic integration."""
import sympy as sp
from .jobs import checkpoint
from .resources import ensure_working_set


def pairs(value, variable, output, *, inverse=False):
    q=sp.Dummy('angular_frequency',real=True)
    cache={}

    def linear(argument):
        try:p=sp.Poly(sp.expand(argument),variable)
        except sp.PolynomialError:return None
        if p.degree()!=1:return None
        a,b=p.nth(1),p.nth(0)
        if a.is_real is not True or a.is_zero is not False or b.is_real is not True:return None
        return a,b

    def sinc(term):
        trig=[f for f in term.atoms(sp.sin,sp.cos) if f.has(variable)]
        if len(trig)!=1:return None
        wave=trig[0];argument=wave.args[0]+(sp.pi/2 if wave.func==sp.cos else 0)
        affine=linear(argument)
        if affine is None:return None
        a,b=affine;width=sp.Abs(a)
        if width.is_finite is not True or width.is_positive is not True:return None
        for factor in sp.Mul.make_args(term):
            base,power=factor.as_base_exp()
            if power!=-1:continue
            denominator=linear(base)
            if denominator is None:continue
            d=sp.cancel(-denominator[1]/denominator[0])
            turns=sp.simplify((a*d+b)/sp.pi)
            if not isinstance(turns,sp.Integer):continue
            coefficient=sp.simplify(term*(variable-d)/wave)*(-1)**turns
            if coefficient.has(variable):continue
            height=coefficient*sp.pi*sp.sign(a)*sp.exp(-sp.I*q*d)
            return sp.Piecewise((height,sp.Abs(q)<width),(height/2,sp.Eq(sp.Abs(q),width)),(0,True))
        return None

    def match(term):
        checkpoint()
        if term in cache:return cache[term]
        cache[term]=None
        canonical=sp.powsimp(term,combine='exp')
        if canonical!=term:
            cache[term]=match(canonical);return cache[term]
        coefficient,dependent=term.as_independent(variable,as_Add=False)
        if dependent==1:return None  # Polynomial/distributional pairs use their own path.
        if coefficient!=1:
            result=match(dependent)
            if result is not None:cache[term]=coefficient*result
            return cache[term]
        if term.is_Add:
            results=[match(v) for v in term.args]
            if all(v is not None for v in results):cache[term]=sp.Add(*results)
            return cache[term]

        # Hyperbolic linearity is valid only when every exponential term has
        # an ordinary convergent pair. Never infer convergence from a rewrite.
        if term.has(sp.sinh,sp.cosh):
            expanded=sp.expand_mul(term.replace(lambda v:v.func in (sp.sinh,sp.cosh),lambda v:v.rewrite(sp.exp)))
            result=match(expanded)
            if result is not None:cache[term]=result;return result

        # Isolate certified real modulation even when stored in the same exp
        # as a decaying envelope. Exponential sums split without branch choices.
        carrier=sp.S.Zero;factors=[]
        for factor in sp.Mul.make_args(term):
            if factor.func==sp.exp:
                exponent=sp.expand(factor.args[0]);rate=sp.im(exponent.coeff(variable))
                if not rate.has(variable) and rate.is_real is True and rate.is_finite is True and rate!=0:
                    carrier+=rate;factor=sp.exp(exponent-sp.I*rate*variable)
            factors.append(factor)
        if carrier!=0:
            result=match(sp.Mul(*factors))
            if result is not None:cache[term]=result.subs(q,q-carrier)
            return cache[term]

        result=sinc(term)
        if result is not None:cache[term]=result;return result

        if term.func==sp.exp:
            exponent=sp.expand(term.args[0]);absolute=[a for a in exponent.atoms(sp.Abs) if a.has(variable)]
            if len(absolute)==1:
                node=absolute[0];affine=linear(node.args[0]);weight=exponent.coeff(node)
                rest=sp.simplify(exponent-weight*node)
                try:polynomial=sp.Poly(rest,variable)
                except sp.PolynomialError:polynomial=None
                if affine is not None and polynomial is not None and polynomial.degree()<=1:
                    a,b=affine;decay=sp.simplify(-weight*sp.Abs(a));d=sp.cancel(-b/a)
                    slope=polynomial.nth(1)
                    if decay.is_finite is True and slope.is_finite is True and sp.re(decay-slope).is_positive is True and sp.re(decay+slope).is_positive is True:
                        result=sp.exp(polynomial.eval(d))*sp.exp(-sp.I*q*d)*(1/(decay-slope+sp.I*q)+1/(decay+slope-sp.I*q))
            if result is None:
                try:p=sp.Poly(exponent,variable)
                except sp.PolynomialError:p=None
                if p is not None and p.degree()==2:
                    decay=-p.nth(2);d=sp.cancel(p.nth(1)/(2*decay))
                    if decay.is_positive is True and decay.is_finite is True and d.is_real is True:
                        rest=sp.simplify(p.nth(0)+decay*d**2)
                        result=sp.exp(rest)*sp.sqrt(sp.pi/decay)*sp.exp(-q**2/(4*decay))*sp.exp(-sp.I*q*d)
            if result is not None:cache[term]=result;return result

        factors=sp.Mul.make_args(term)
        for gate in factors:
            if gate.func!=sp.Heaviside:continue
            affine=linear(gate.args[0])
            if affine is None:continue
            a,b=affine;d=sp.cancel(-b/a);side=sp.sign(a)
            if side not in (-1,1):continue
            envelope=sp.cancel(term/gate)
            if envelope.func!=sp.exp:continue
            try:p=sp.Poly(sp.expand(envelope.args[0]),variable)
            except sp.PolynomialError:continue
            if p.degree()!=1:continue
            decay=sp.simplify(-side*p.nth(1))
            if decay.is_positive is True and decay.is_finite is True:
                result=sp.exp(p.eval(d))*sp.exp(-sp.I*q*d)/(decay+side*sp.I*q)
                cache[term]=result;return result

        for factor in factors:
            if factor.func in (sp.cos,sp.sin):
                affine=linear(factor.args[0])
                if affine is None:continue
                a,b=affine;rest=sp.Mul(*(v for v in factors if v is not factor))
                base=match(rest)
                if base is None:continue
                positive=sp.exp(sp.I*b)*base.subs(q,q-a)
                negative=sp.exp(-sp.I*b)*base.subs(q,q+a)
                result=(positive+negative)/2 if factor.func==sp.cos else (positive-negative)/(2*sp.I)
                cache[term]=result;return result
            try:p=sp.Poly(factor,variable)
            except sp.PolynomialError:continue
            if p.degree()<1:continue
            rest=sp.Mul(*(v for v in factors if v is not factor))
            base=match(rest)
            if base is None:continue
            ensure_working_set(int(p.degree())+1,bytes_per_sample=8192,live_arrays=8)
            result=sp.Add(*(c*sp.I**m[0]*sp.diff(base,q,m[0]) for m,c in p.terms()))
            # Derivatives at rectangle edges are distributions. Keep them in
            # the generic path until their edge contributions are explicit.
            if base.has(sp.Piecewise):continue
            cache[term]=result;return result
        return None

    known=[];remaining=[]
    for term in sp.Add.make_args(sp.expand_mul(value)):
        result=match(term)
        if result is None:remaining.append(term)
        else:known.append(result)
    transformed=sp.Add(*known).subs(q,-output if inverse else output)
    if inverse:transformed/=2*sp.pi
    return transformed,sp.Add(*remaining) if known else value
