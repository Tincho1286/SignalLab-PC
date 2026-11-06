"""Bilinear polynomial substitution over exact stored binary rationals."""
import math
import sympy as sp
from .jobs import checkpoint
from .resources import ensure_working_set


def convert(system,period,*,inverse=False):
    from .filters import Transfer
    from .rational_frequency import RationalModel
    from .scalar_expression import numerical_value
    from .procedure import step
    period=float(period)
    if not math.isfinite(period) or period<=0:raise ValueError('T debe ser positivo y finito.')
    if system.domain!=('digital' if inverse else 'analog'):raise ValueError('Elegí H(z) para la bilineal inversa o H(s) para la directa.')
    degree=max(len(system.a),len(system.b))-1
    ensure_working_set((degree+system.advance+1)**2,bytes_per_sample=1024,live_arrays=16)
    model=RationalModel.system(system)
    def exact(pair):return sp.Rational(pair[0].numerator,pair[0].denominator)+sp.I*sp.Rational(pair[1].numerator,pair[1].denominator)
    b=list(map(exact,model.b));a=list(map(exact,model.a));degree=max(len(a),len(b))-1
    q=sp.Symbol('s' if inverse else 'q');T=sp.Rational(period)
    numerator=sp.Poly(1-T*q/2,q) if inverse else sp.Poly(2*(1-q)/T,q)
    denominator=sp.Poly(1+T*q/2,q) if inverse else sp.Poly(1+q,q)
    # Homogeneous evaluation prevents intermediate floating cancellation of
    # the leading coefficient, which may be exactly zero at s=2/T.
    powers_d=[sp.Poly(1,q)]
    for index in range(degree):
        checkpoint();powers_d.append(powers_d[-1]*denominator)
    def substitute(coefficients):
        result=sp.Poly(coefficients[0],q);local_degree=len(coefficients)-1
        for index,value in enumerate(coefficients[1:],1):
            checkpoint();result=result*numerator+value*powers_d[index]
        return result*powers_d[degree-local_degree]
    nb,na=substitute(b),substitute(a)
    if inverse and system.advance:
        nb*=denominator**system.advance;na*=numerator**system.advance
    common=sp.gcd(nb,na);nb=nb.exquo(common);na=na.exquo(common)
    mapped=sp.cancel(nb.as_expr()/na.as_expr())
    advance=0
    if inverse:out_b,out_a=nb.all_coeffs(),na.all_coeffs()
    else:
        out_b=list(reversed(nb.all_coeffs()));out_a=list(reversed(na.all_coeffs()))
        while len(out_a)>1 and out_a[0]==0:advance+=1;out_a.pop(0)
    scale=out_a[0]
    values_b=[numerical_value(sp.cancel(v/scale)) for v in out_b]
    values_a=[numerical_value(sp.cancel(v/scale)) for v in out_a]
    result=Transfer(values_b,values_a,'analog' if inverse else 'digital','Bilineal inversa' if inverse else 'Bilineal de '+system.name,
                    advance=advance,sample_period_s=None if inverse else period)
    s,z=sp.Symbol('s'),sp.Symbol('z')
    original_q=1/z if inverse else s
    original=(sum(v*original_q**(len(b)-1-i) for i,v in enumerate(b))/sum(v*original_q**(len(a)-1-i) for i,v in enumerate(a)))*(z**system.advance if inverse else 1)
    exact_result=mapped if inverse else sp.cancel(mapped.subs(q,1/z))
    relation='z = (1+s*T/2)/(1-s*T/2)' if inverse else 's = (2/T)*(z-1)/(z+1)'
    records=[step('Sustitución bilineal','Sustitución racional con T = '+repr(period)+' s y cancelación exacta',original,exact_result,
        conditions='T > 0; fuera de los polos. La ROC no se infiere de esta sustitución.',interpretation=relation+'. Los coeficientes de entrada se interpretan como los números binarios almacenados; se redondea sólo al construir la transferencia de salida.',source='bilinear_mapping.convert')]
    return result,records,str(exact_result)
