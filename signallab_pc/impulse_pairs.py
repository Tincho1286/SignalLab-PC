"""Domain-aware impulse notation and exact distributional transform pairs."""
import sympy as sp
from .jobs import checkpoint


def impulse(argument,order=0):
    argument=sp.sympify(argument);order=sp.sympify(order)
    if any(v.name=='n' for v in argument.free_symbols) and not any(v.name in ('t','x','w','omega','tau') for v in argument.free_symbols):
        if order!=0:raise ValueError('El impulso discreto no tiene derivadas de Dirac. Usá impulse(n-a) o diferencias de impulsos.')
        return sp.KroneckerDelta(argument,0)
    return sp.DiracDelta(argument,order)


def impulse_integral(term,variable,kernel,lower=-sp.oo,upper=sp.oo):
    """Sifting of one affine Dirac derivative; None means no certified pair.

    delta^(k)(a*x+b) scales by 1/(abs(a)*a**k), including negative a.
    Unilateral bounds follow the app's 0-minus, full endpoint-weight rule.
    """
    atoms=term.atoms(sp.DiracDelta)
    if not atoms:return None
    if len(atoms)!=1:raise ValueError('No se define el producto de impulsos Dirac. Separá sus pesos mediante una suma.')
    delta=next(iter(atoms));weight=term.extract_multiplicatively(delta)
    if weight is None or weight.has(sp.DiracDelta):raise ValueError('No se definen potencias, recíprocos ni productos de Dirac como funciones ordinarias.')
    try:polynomial=sp.Poly(delta.args[0],variable)
    except sp.PolynomialError:return None
    if polynomial.degree()!=1:return None
    scale=polynomial.nth(1);position=sp.cancel(-polynomial.nth(0)/scale)
    if scale.is_real is not True or scale.is_zero is not False or position.is_real is not True:return None
    inside=sp.And(position>=lower,position<=upper)
    if inside is sp.false:return sp.S.Zero
    order=delta.args[1] if len(delta.args)>1 else sp.S.Zero
    if not isinstance(order,sp.Integer) or order<0:return None
    from .resources import ensure_working_set
    ensure_working_set(int(order)+1,bytes_per_sample=8192,live_arrays=8)
    # Products with a jump at the impulse have no canonical sifting value.
    real=sp.Dummy('coordinate',real=True)
    if weight.has(variable):
        for level in range(int(order)+1):
            checkpoint();factor=sp.diff(weight,variable,level)
            if factor.has(sp.DiracDelta):raise ValueError('El factor de Dirac no es suficientemente suave en su posición. Indicá el peso del impulso por separado.')
            at=factor.subs(variable,position)
            if at.has(sp.nan,sp.zoo,sp.oo,-sp.oo) or factor.has(sp.Heaviside,sp.Piecewise,sp.sign,sp.Abs):
                left=sp.limit(factor.xreplace({variable:real}),real,position,dir='-')
                right=sp.limit(factor.xreplace({variable:real}),real,position,dir='+')
                if sp.simplify(left-right)!=0 or sp.simplify(left-at)!=0 or at.is_finite is not True:
                    raise ValueError('El factor de Dirac es discontinuo o no está definido en su posición. Indicá su peso explícitamente.')
    checkpoint()
    answer=(-1)**order*sp.diff(weight*kernel,variable,int(order)).subs(variable,position)/(sp.Abs(scale)*scale**order)
    if answer.has(sp.nan,sp.zoo,sp.oo,-sp.oo,sp.Limit,sp.Derivative):return None
    return sp.simplify(answer) if inside is sp.true else sp.Piecewise((sp.simplify(answer),inside),(0,True))


def fourier_pairs(value,variable,output,*,inverse=False):
    """Separate certified impulse/modulated-polynomial pairs from regular terms."""
    known=[];remaining=[];kernel=sp.exp((sp.I if inverse else -sp.I)*variable*output)
    divisor=2*sp.pi if inverse else sp.S.One
    for term in sp.Add.make_args(sp.expand_mul(value.rewrite(sp.exp))):
        checkpoint()
        if term.has(sp.DiracDelta):
            answer=impulse_integral(term,variable,kernel)
            if answer is not None:known.append(answer/divisor);continue
            remaining.append(term);continue
        rate=sp.S.Zero;factors=[]
        for factor in sp.Mul.make_args(term):
            if factor.func==sp.exp and factor.has(variable):
                slope=sp.diff(factor.args[0],variable)
                offset=sp.simplify(factor.args[0]-slope*variable)
                if slope.has(variable) or offset.has(variable):factors.append(factor);continue
                rate+=slope;factors.append(sp.exp(offset))
            else:factors.append(factor)
        carrier=sp.simplify(rate/sp.I)
        if carrier.is_real is not True:remaining.append(term);continue
        try:polynomial=sp.Poly(sp.Mul(*factors),variable)
        except sp.PolynomialError:remaining.append(term);continue
        argument=output+carrier if inverse else output-carrier
        multiplier=-sp.I if inverse else sp.I
        scale=sp.S.One if inverse else 2*sp.pi
        known.append(scale*sp.Add(*[coefficient*multiplier**power[0]*sp.DiracDelta(argument,power[0]) for power,coefficient in polynomial.terms()]))
    return sp.Add(*known),sp.Add(*remaining)


def unilateral_laplace(value,variable,output):
    """Keep 0-minus impulse weights and derivative scaling out of generic tables."""
    known=[];remaining=[]
    for term in sp.Add.make_args(sp.expand_mul(value)):
        answer=impulse_integral(term,variable,sp.exp(-output*variable),sp.S.Zero,sp.oo) if term.has(sp.DiracDelta) else None
        (remaining if answer is None else known).append(term if answer is None else answer)
    regular=sp.Add(*remaining)
    result,plane,condition=sp.laplace_transform(regular,variable,output) if regular!=0 else (sp.S.Zero,-sp.oo,sp.true)
    return sp.simplify(sp.Add(*known)+result),plane,condition
