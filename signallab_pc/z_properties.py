"""Linearity, time shifts and geometric Z pairs before general partial fractions."""
import math
import sympy as sp
from .symbolic import parse,Z,N,T,S,W
from .numeric_modes import PoleValues
from .signal_notation import SignalPrinter
from .resources import ensure_working_set
from .jobs import checkpoint


def _pair(term):
    coefficient=sp.S.One;delay=0;pole=None;order=0;q=sp.Dummy('q')
    for factor in sp.Mul.make_args(sp.powsimp(term)):
        if not factor.has(Z):coefficient*=factor;continue
        if factor==Z:delay-=1;continue
        if factor.is_Pow and factor.base==Z and factor.exp.is_Integer:delay-=int(factor.exp);continue
        if not (factor.is_Pow and factor.exp.is_Integer and factor.exp<0):return None
        m=int(-factor.exp);base=factor.base
        try:
            polynomial=sp.Poly(sp.cancel(base.subs(Z,1/q)),q)
            if polynomial.degree()!=1 or polynomial.nth(0)==0:raise sp.PolynomialError()
            normalizer=polynomial.nth(0);a=sp.simplify(-polynomial.nth(1)/normalizer)
        except sp.PolynomialError:
            try:
                polynomial=sp.Poly(base,Z)
                if polynomial.degree()!=1:return None
                normalizer=polynomial.nth(1);a=sp.simplify(-polynomial.nth(0)/normalizer);delay+=m
            except sp.PolynomialError:return None
        if pole is not None and sp.simplify(pole-a)!=0:return None
        pole=a;order+=m;coefficient*=normalizer**(-m)
    return sp.simplify(coefficient),delay,pole,order


def inverse_pairs(request):
    raw=parse(request['expression'])
    if raw.has(N,T,S,W,sp.zoo,sp.nan,sp.oo):return None
    terms=[]
    for term in sp.Add.make_args(sp.expand_mul(raw)):
        pair=_pair(term)
        if pair is None:return None
        if pair[0]!=0:terms.append(pair)
    if not any(pole is not None for c,d,pole,m in terms):return None
    reduced=sp.cancel(raw);denominator=sp.Poly(sp.fraction(reduced)[1],Z)
    # Canceled modes belong to the finite rational fallback, whose endpoint
    # ROC is already exact; do not retain a fictitious pole from a pair.
    if any(pole==0 for c,d,pole,m in terms if pole is not None):return None
    for c,d,pole,m in terms:
        if pole is not None and sp.simplify(denominator.eval(pole))!=0:return None
    mode=request.get('roc','right')
    if mode not in ('right','left','radius'):raise ValueError('Elegí una ROC derecha, izquierda o por radio.')
    radius=sp.simplify(parse(request.get('radius','1'))) if mode=='radius' else sp.S.One
    if mode=='radius' and (radius.free_symbols or radius.is_real is not True or radius.is_positive is not True or radius.is_finite is not True):raise ValueError('El radio debe ser una constante real, positiva y finita.')
    parameters=sorted(map(str,raw.free_symbols-{Z}));numeric=not parameters
    if mode=='radius' and not numeric:raise ValueError('Asigná los parámetros antes de elegir una ROC por radio.')
    values=PoleValues();context=values.context;sides={};groups={};impulses=[];numeric_terms=[]
    for coefficient,delay,pole,order in terms:
        checkpoint()
        if pole is None:
            impulses.append(coefficient*sp.KroneckerDelta(N,delay));numeric_terms.append((coefficient,delay,None,0,True));continue
        if pole not in sides:
            if mode=='radius':
                difference=sp.simplify(radius-sp.Abs(pole))
                if difference.is_positive is True:sides[pole]=True
                elif difference.is_negative is True:sides[pole]=False
                else:raise ValueError('El radio coincide con un polo o no puede separarse de él exactamente. Elegí otro radio dentro de la ROC.')
            else:sides[pole]=mode=='right'
        right=sides[pole];index=N-delay
        weight=sp.binomial(index+order-1,order-1) if right else (-1)**order*sp.binomial(-index-1,order-1)
        gate=sp.Heaviside(index if right else -index-order,1)
        groups.setdefault(gate,[]).append(coefficient*weight*pole**index)
        numeric_terms.append((coefficient,delay,pole,order,right))
    result=sp.Add(*impulses,*[sp.Add(*items)*gate for gate,items in groups.items()])
    right_poles=[p for p,side in sides.items() if side];left_poles=[p for p,side in sides.items() if not side]
    if numeric:
        lower=sp.Abs(max(right_poles,key=lambda p:abs(values.value(p)))) if right_poles else sp.S.Zero
        upper=sp.Abs(min(left_poles,key=lambda p:abs(values.value(p)))) if left_poles else sp.oo
    else:
        lower=sp.Max(*[sp.Abs(p) for p in right_poles]) if right_poles else sp.S.Zero
        upper=sp.Min(*[sp.Abs(p) for p in left_poles]) if left_poles else sp.oo
    zero_included=not right_poles and sp.limit(reduced,Z,0).is_finite is True
    infinity_included=not left_poles and sp.limit(reduced,Z,sp.oo).is_finite is True
    start=int(request.get('start',-16));count=int(request.get('count',65))
    if count<1:raise ValueError('Usá una cantidad positiva de muestras.')
    ensure_working_set(count,bytes_per_sample=1024,live_arrays=10);samples=[]
    if request.get('include_samples',True) and numeric:
        modes=[(values.value(c),d,values.value(p) if p is not None else None,m,right) for c,d,p,m,right in numeric_terms]
        for offset,n in enumerate(range(start,start+count)):
            if offset%64==0:checkpoint()
            value=context.mpc(0)
            for c,d,p,m,right in modes:
                k=n-d
                if p is None:
                    if k==0:value+=c
                elif right and k>=0:value+=c*math.comb(k+m-1,m-1)*p**k
                elif not right and k<=-m:value+=c*(-1)**m*math.comb(-k-1,m-1)*p**k
            value=complex(value)
            if not math.isfinite(value.real) or not math.isfinite(value.imag):raise ValueError('Las muestras exceden el rango numérico.')
            samples.append([value.real,value.imag])
    from .cas_engine import encode
    text=SignalPrinter({'order':'none'}).doprint(result)
    conditions=[sp.Ne(pole,0) for pole in sides if pole.free_symbols and pole.is_zero is not False]
    return {'operation':'Z inversa por propiedades','result':str(result),'display_result':text,'display_numeric':False,'display_terms':[],
            'evaluated':True,'output_variable':'n','origin':start,'numeric_samples':samples or None,'parameters':parameters,
            'roc':str(lower)+(' ≤ ' if zero_included else ' < ')+'|z| < '+str(upper),'infinity_included':bool(infinity_included),
            'cas_encoded':encode(result),'method':'geometric_pairs','condition':str(sp.And(*conditions)),
            'scope':'Se aplicaron linealidad, desplazamiento y pares de secuencias geométricas. La ROC decide el soporte derecho o izquierdo. La fórmula conserva exponenciales y coeficientes exactos; las muestras sólo cubren el intervalo elegido.'}
