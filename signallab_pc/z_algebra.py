"""Algebraic bilateral Z transforms with explicit support/ROC choices."""
import math
import sympy as sp
from .symbolic import parse,Z,N,T,S,W
from .resources import ensure_working_set


def direct(request):
    lower=sp.simplify(parse(request.get('lower','0')));upper=sp.simplify(parse(request.get('upper','oo')))
    if lower!=-sp.oo and not isinstance(lower,sp.Integer):raise ValueError('Inicio entero o -oo.')
    if upper!=sp.oo and not isinstance(upper,sp.Integer):raise ValueError('Final entero u oo.')
    if lower>upper:raise ValueError('El índice final debe ser mayor o igual al inicial.')
    if lower.is_finite and upper.is_finite:ensure_working_set(int(upper-lower+1),bytes_per_sample=1024,live_arrays=8)
    from .expression_definition import prepare,attach
    definition=prepare(request['expression'],N,'discrete',(lower,upper),request.get('input_conditions',()))
    expression=definition.expression
    if expression.has(Z,T,S,W):raise ValueError('Z directa: la secuencia x[n] usa n. Para X(z), elegí Inversa.')
    from .z_direct_pairs import direct_pairs
    try:pair=direct_pairs(expression,lower,upper)
    except (sp.PolynomialError,NotImplementedError):pair=None
    if pair is None:result=sp.summation(sp.simplify(expression*Z**(-N)),(N,lower,upper))
    elif pair['empty']:result=pair['result']
    elif pair['condition'] is sp.true:result=pair['result']
    else:result=sp.Piecewise((pair['result'],pair['condition']),(sp.Sum(expression*Z**(-N),(N,lower,upper)),True),evaluate=False)
    # Never simplify the whole Piecewise: SymPy can turn a complex-plane
    # modulus condition into inequalities on a real z.
    if isinstance(result,sp.Piecewise):
        radius=sp.Symbol('R',positive=True);parts=[]
        for value,condition in result.args:
            radial=condition.subs(sp.Abs(Z),radius)
            if not radial.has(Z) and radial.has(radius):
                try:condition=sp.reduce_inequalities(radial,radius).xreplace({radius:sp.Abs(Z)})
                except (NotImplementedError,ValueError,TypeError):pass
            parts.append((sp.simplify(value) if not value.has(sp.Sum) else value,condition))
        result=sp.Piecewise(*parts,evaluate=False)
    else:result=sp.simplify(result)
    branches=[]
    if isinstance(result,sp.Piecewise):
        for value,condition in result.args:
            if not value.has(sp.Sum,sp.oo,sp.zoo,sp.nan):branches.append({'expression':str(value),'condition':str(condition)})
    evaluated=not result.has(sp.Sum,sp.oo,sp.zoo,sp.nan) or bool(branches)
    answer={'operation':'Transformada Z algebraica','result':str(result),'branches':branches,'evaluated':evaluated,'output_variable':'z','inverse_roc_hint':'right' if lower.is_finite else 'left' if upper.is_finite else None,'scope':f'X(z)=Σ x[n] z^(−n), desde n={lower} hasta {upper}. Fuera del soporte indicado x[n]=0. Las condiciones de convergencia acompañan la expresión; no se descartan al simplificar.'}
    if pair is not None:
        answer['method']='table_pairs'
        if pair.get('finite_support'):answer['inverse_roc_hint']='right'
        if pair['empty']:
            answer['convergence_empty']=True;answer['evaluated']=False;answer['roc']='No existe un anillo abierto de convergencia absoluta. La convergencia de Fourier sobre |z|=1 se comprueba por separado.'
            if lower==-sp.oo and upper==sp.oo:
                from .dtft_pairs import direct as dtft_pairs
                boundary=dtft_pairs(expression)
                if boundary is not None:answer['boundary_dtft']=str(boundary)
            answer['scope']='Las colas izquierda y derecha exigen condiciones incompatibles sobre |z|. Puede existir una DTFT sobre el círculo unitario, pero eso no constituye una ROC abierta para la transformada Z.'
        else:answer['scope']+=' Se separaron los valores definidos por continuidad y se aplicaron linealidad y pares de potencias, exponenciales o series logarítmicas sobre cada tramo.'
    if ((lower.is_finite and upper.is_finite) or (pair is not None and pair.get('finite_support'))) and evaluated and not branches:
        if result.free_symbols-{Z}:
            answer['roc_finite_plane']='Converge para 0<|z|<∞. La inclusión de z=0 y z=∞ depende del soporte efectivo y de los parámetros.'
        else:
            zero=sp.limit(result,Z,0).is_finite;infinity=sp.limit(result,Z,sp.oo).is_finite
            answer['roc_finite_plane']='Todo z finito' if zero is True else 'Todo z finito salvo z=0' if zero is False else 'Converge para 0<|z|<∞; z=0 no determinado'
            if infinity is not None:answer['infinity_included']=bool(infinity)
    return attach(answer,definition)


def inverse(request):
    from .z_inverse import inverse as rational_inverse
    if request.get('complete_finite'):
        value=sp.cancel(parse(request['expression']))
        if not value.is_rational_function(Z):raise ValueError('El soporte finito completo requiere un polinomio de Laurent en z.')
        num,den=map(lambda v:sp.Poly(v,Z),sp.fraction(value))
        if len(den.terms())!=1:raise ValueError('X(z) no es un polinomio de Laurent finito. Elegí un intervalo de muestras para esta secuencia infinita.')
        power=den.monoms()[0][0]
        support=[power-m[0] for m,c in num.terms() if c!=0]
        request=dict(request,start=min(support) if support else 0,count=max(support)-min(support)+1 if support else 1,include_samples=True)
    return rational_inverse(request)
