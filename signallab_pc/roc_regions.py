"""Open ROC regions of numeric rational transforms, with exact pole cancellation."""
import math
import sympy as sp
from .symbolic import parse,Z,S
from .jobs import checkpoint


def regions(request):
    kind=request['kind']
    if kind not in ('z','laplace'):raise ValueError('Elegí Transformada Z o Laplace.')
    variable=Z if kind=='z' else S;raw=parse(request['expression']);expression=sp.factor_terms(raw) if kind=='laplace' else sp.cancel(raw)
    if expression.free_symbols-{variable}:raise ValueError('Asigná valores a los parámetros antes de explorar los polos y la ROC.')
    if expression.has(sp.nan,sp.zoo,sp.oo,-sp.oo):raise ValueError('La expresión debe definir una transformada finita.')
    if kind=='laplace':
        factors=[]
        for factor in sp.Mul.make_args(expression):
            if factor.func==sp.exp:
                try:exponent=sp.Poly(factor.args[0],S)
                except sp.PolynomialError:
                    factors.append(factor);continue
                if exponent.degree()<=1 and sp.im(exponent.coeff_monomial(S))==0:continue
            factors.append(factor)
        expression=sp.cancel(sp.Mul(*factors))
    if not expression.is_rational_function(variable):
        raise ValueError('El selector visual necesita una expresión racional, o Laplace racional con un retardo global. Podés conservar la definición y elegir la ROC con los campos habituales.')
    denominator=sp.Poly(sp.fraction(expression)[1],variable).sqf_part()
    from .resources import ensure_working_set
    ensure_working_set(max(0,int(denominator.degree()))**2,bytes_per_sample=2048,live_arrays=8)
    checkpoint()
    try:poles=denominator.all_roots(radicals=False) if denominator.degree()>0 else []
    except (NotImplementedError,sp.PolynomialError):
        found=sp.roots(denominator.as_expr(),variable)
        if sum(found.values())!=denominator.degree():raise ValueError('No se identificaron todos los polos. Elegí la ROC con los campos habituales.')
        poles=[p for p,m in found.items() for _ in range(m)]
    from .numeric_modes import PoleValues
    values=PoleValues();ctx=values.context;levels=[];coordinates=[]
    for pole in poles:
        checkpoint();value=values.value(pole)
        if not ctx.isfinite(value):raise ValueError('No se pudo representar un polo finito.')
        x,y=float(value.real),float(value.imag)
        coordinates.append([x,y] if math.isfinite(x) and math.isfinite(y) else None)
        exact=sp.simplify(sp.Abs(pole)) if kind=='z' else sp.simplify(sp.re(pole))
        if kind=='z' and exact==0:continue
        if not any(sp.simplify(exact-old)==0 for old in levels):levels.append(exact)
    def evaluate(v):
        if v==sp.oo:return ctx.inf
        if v==-sp.oo:return -ctx.inf
        return ctx.mpf(str(sp.N(v,85)))
    levels.sort(key=evaluate)
    if any(evaluate(a)>=evaluate(b) for a,b in zip(levels,levels[1:])):
        raise ValueError('Dos bordes de ROC no se distinguen con la precisión disponible. Elegí la región de forma algebraica; no se fusionan los polos por tolerancia.')
    bounds=([sp.S.Zero]+levels+[sp.oo]) if kind=='z' else ([-sp.oo]+levels+[sp.oo])
    choices=[]
    for i,(low,high) in enumerate(zip(bounds,bounds[1:])):
        if kind=='z':
            interior=sp.S.One if not levels else high/2 if low==0 else low*2+1 if high==sp.oo else sp.sqrt(low*high)
            mode='right' if high==sp.oo else 'left' if low==0 else 'radius'
        else:
            interior=sp.S.Zero if not levels else high-sp.Max(1,sp.Abs(high)) if low==-sp.oo else low+sp.Max(1,sp.Abs(low)) if high==sp.oo else (low+high)/2
            mode='left' if low==-sp.oo and levels else 'right' if high==sp.oo else 'line'
        representative=str(sp.N(interior,80))
        # The decimal sent to the inverse must remain strictly in this region.
        numeric=ctx.mpf(representative)
        if not evaluate(low)<numeric<evaluate(high):raise ValueError('No se obtuvo un punto interior fiable para la ROC.')
        coordinate='|z|' if kind=='z' else 'Re(s)'
        digits=10
        if low not in (-sp.oo,sp.oo) and high not in (-sp.oo,sp.oo):
            while ctx.nstr(evaluate(low),digits)==ctx.nstr(evaluate(high),digits) and digits<80:digits+=10
        fmt=lambda v:('-∞' if v==-sp.oo else '∞' if v==sp.oo else ctx.nstr(evaluate(v),digits))
        choices.append(dict(mode=mode,value=representative,display_value=ctx.nstr(numeric,digits+2),lower=str(low),upper=str(high),
                            lower_numeric=None if low==-sp.oo else str(evaluate(low)),upper_numeric=None if high==sp.oo else str(evaluate(high)),
                            label=fmt(low)+' < '+coordinate+' < '+fmt(high)))
    if kind=='z' and not poles:
        choices[0]['label']='Todo el plano finito · sin polos';choices[0]['lower_numeric']=None
    report='Regiones abiertas determinadas por las posiciones de los polos después de cancelaciones exactas. Cada región elige el soporte de los términos de la inversa; no cambia la expresión de entrada.'
    if not poles:report='No hay polos finitos después de las cancelaciones. La inversión determina los posibles impulsos, avances o retardos; no se crean regiones adicionales.'
    boundary_values=[str(evaluate(v)) for v in levels]
    plot_available=all(p is not None for p in coordinates) and all(math.isfinite(float(v)) for v in boundary_values)
    if len(set(map(float,boundary_values)))!=len(boundary_values):plot_available=False
    return dict(operation='roc_regions',kind=kind,expression=request['expression'],poles=coordinates,
                boundaries=boundary_values,regions=choices,report=report,plot_available=plot_available,
                scope='Los bordes no pertenecen a una ROC abierta. La inclusión de cero o infinito en Z se determina en el informe de la inversa; el diagrama representa regiones abiertas del plano finito.')
