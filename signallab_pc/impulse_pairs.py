"""Domain-aware impulse notation and exact distributional transform pairs."""
import sympy as sp
from .jobs import checkpoint


def impulse(argument,order=0):
    argument=sp.sympify(argument);order=sp.sympify(order)
    if any(v.name in ('n','k') for v in argument.free_symbols) and not any(v.name in ('t','x','w','omega','tau') for v in argument.free_symbols):
        if order!=0:raise ValueError('El impulso discreto no tiene derivadas de Dirac. Usá impulse(n-a) o diferencias de impulsos.')
        return sp.KroneckerDelta(argument,0)
    return sp.DiracDelta(argument,order)


def complete_products(expression):
    """Complete ordinary coefficients before applying an impulse, not across it."""
    from .singularities import extend_removable
    if not expression.has(sp.KroneckerDelta,sp.DiracDelta,sp.Heaviside):return extend_removable(expression)
    if isinstance(expression,sp.Add):
        singular=[term for term in expression.args if term.has(sp.KroneckerDelta,sp.DiracDelta,sp.Heaviside)]
        ordinary=extend_removable(sp.Add(*(term for term in expression.args if term not in singular),evaluate=False))
        return sp.Add(ordinary,*(complete_products(term) for term in singular),evaluate=False)
    if isinstance(expression,sp.Mul):
        factors=[]
        def flatten(value):
            if isinstance(value,sp.Mul):
                for factor in value.args:flatten(factor)
            else:factors.append(value)
        flatten(expression)
        gates=[factor for factor in factors if factor.has(sp.KroneckerDelta,sp.DiracDelta,sp.Heaviside)]
        ordinary=[factor for factor in factors if factor not in gates]
        if gates and ordinary:
            coefficient=extend_removable(sp.Mul(*ordinary,evaluate=False))
            return sp.Mul(coefficient,*gates,evaluate=False)
    return expression if expression.has(sp.KroneckerDelta,sp.DiracDelta,sp.Heaviside) else extend_removable(expression)


def affine_impulse(delta,variable):
    try:polynomial=sp.Poly(delta.args[0],variable)
    except sp.PolynomialError:return None
    if polynomial.degree()!=1:return None
    scale=polynomial.nth(1);position=sp.cancel(-polynomial.nth(0)/scale)
    if scale.is_real is not True or scale.is_zero is not False or position.is_real is not True:return None
    return scale,position


def expand_real_impulses(value, variable):
    """Reduce simple real roots before sampling a temporal weight."""
    if not value.has(sp.DiracDelta):
        return value
    return sp.expand_mul(value.expand(diracdelta=True, wrt=variable))


def distribution_parts(value, variable, lower, upper, *, right_open=False):
    """Split a window into its ordinary expression and exact impulse areas."""
    from .periodic_signals import ImpulseTrain, weighted_lines

    regular = []
    lines = {}
    for term in sp.Add.make_args(sp.expand_mul(value)):
        checkpoint()
        if term.has(ImpulseTrain):
            entries = weighted_lines(term, variable, lower, upper, right_open=right_open)
            if entries is None:
                raise ValueError('Para graficar el tren, usá un argumento afín real y un período conocido.')
        elif term.has(sp.DiracDelta):
            atoms = term.atoms(sp.DiracDelta)
            if len(atoms) != 1:
                raise ValueError('Separá los impulsos en una suma de líneas.')
            delta, = atoms
            geometry = affine_impulse(delta, variable)
            if geometry is None or len(delta.args)>1 and delta.args[1]!=0:
                raise ValueError('La figura de líneas admite impulsos de orden cero con argumento afín real.')
            _, position = geometry
            inside = sp.simplify(sp.And(position>=lower, position<upper if right_open else position<=upper))
            if inside is sp.false:
                continue
            if inside is not sp.true:
                raise ValueError('No se pudo ubicar un impulso dentro de la ventana.')
            area = impulse_integral(term, variable, sp.S.One)
            if area is None:
                raise ValueError('No se obtuvo un área finita para un impulso.')
            entries = [(position, area)]
        else:
            regular.append(term)
            continue
        for position, area in entries:
            lines[position] = lines.get(position, sp.S.Zero)+area
    return sp.Add(*regular), [(position, area) for position, total in lines.items()
                              if (area:=sp.simplify(total)) != 0]


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
    affine=affine_impulse(delta,variable)
    if affine is None:return None
    scale,position=affine
    inside=sp.And(position>=lower,position<=upper)
    if inside is sp.false:return sp.S.Zero
    order=delta.args[1] if len(delta.args)>1 else sp.S.Zero
    if not isinstance(order,sp.Integer) or order<0:return None
    from .resources import ensure_working_set
    ensure_working_set(int(order)+1,bytes_per_sample=8192,live_arrays=8)
    # A polynomial gate whose argument is nonzero at the impulse has a
    # constant local sign. This also removes irrelevant jump derivatives.
    local_gates = {}
    for gate in weight.atoms(sp.Heaviside,sp.sign):
        argument = gate.args[0]
        if argument.is_polynomial(variable):
            center = argument.subs(variable,position)
            if center.is_positive is True or center.is_negative is True:
                local_gates[gate] = gate.subs(variable,position)
    weight = weight.xreplace(local_gates)
    if weight == 0:
        return sp.S.Zero
    # Products with a jump at the impulse have no canonical sifting value.
    real=sp.Dummy('coordinate',real=True)
    from .expression_definition import Definition
    regular_weight=Definition('',weight,variable,'continuous').integral_expression()
    if weight.has(variable):
        for level in range(int(order)+1):
            checkpoint();factor=sp.diff(regular_weight,variable,level)
            if factor.has(sp.DiracDelta):raise ValueError('El factor de Dirac no es suficientemente suave en su posición. Indicá el peso del impulso por separado.')
            at=weight.subs(variable,position) if level==0 else factor.subs(variable,position)
            if at.has(sp.nan,sp.zoo,sp.oo,-sp.oo) or weight.has(sp.Heaviside,sp.Piecewise,sp.sign,sp.Abs):
                left=sp.limit(factor.xreplace({variable:real}),real,position,dir='-')
                right=sp.limit(factor.xreplace({variable:real}),real,position,dir='+')
                if sp.simplify(left-right)!=0 or left.is_finite is not True or (level==0 and sp.simplify(left-at)!=0):
                    raise ValueError('El factor de Dirac es discontinuo o no está definido en su posición. Indicá su peso explícitamente.')
    checkpoint()
    derivative=sp.diff(regular_weight*kernel,variable,int(order))
    sampled=derivative.subs(variable,position)
    if sampled.has(sp.nan,sp.zoo,sp.oo,-sp.oo) or (order and weight.has(sp.Piecewise)):sampled=sp.limit(derivative.xreplace({variable:real}),real,position)
    answer=(-1)**order*sampled/(sp.Abs(scale)*scale**order)
    if answer.has(sp.nan,sp.zoo,sp.oo,-sp.oo,sp.Limit,sp.Derivative):return None
    return sp.simplify(answer) if inside is sp.true else sp.Piecewise((sp.simplify(answer),inside),(0,True))


def _integer_delay(weight,frequency):
    coefficient,carrier=sp.powsimp(weight,combine='exp').as_independent(frequency,as_Add=False)
    if carrier==1:return coefficient,sp.S.Zero
    if carrier.func!=sp.exp:return None
    argument=sp.expand(carrier.args[0])
    delay=sp.simplify(sp.I*argument.coeff(frequency))
    phase=sp.expand(argument+sp.I*frequency*delay)
    if delay.is_integer is not True or phase.has(frequency):return None
    return coefficient*sp.exp(phase),delay


def _inverse_delayed_comb(term,frequency,index):
    """Apply the roots-of-unity identity to a comb times an integer delay."""
    from .periodic_signals import ImpulseTrain,affine_train_term

    trains=term.atoms(ImpulseTrain)
    if len(trains)!=1:return None
    train,=trains
    geometry=affine_train_term(train,frequency)
    weight=term.extract_multiplicatively(train)
    if geometry is None or weight is None or weight.has(ImpulseTrain,sp.DiracDelta):return None
    spacing,origin,area=geometry
    period=sp.simplify(2*sp.pi/spacing)
    if not isinstance(period,sp.Integer) or period<=0:return None
    pair=_integer_delay(weight,frequency)
    if pair is None:return None
    coefficient,delay=pair
    return area*period*coefficient*sp.exp(sp.I*origin*(index-delay))*sp.KroneckerDelta(sp.Mod(index-delay,period),0)


def _inverse_delayed_principal_value(term,frequency,index):
    from .periodic_signals import ImpulseTrain,PVCot
    values=term.atoms(PVCot)
    if len(values)!=1:return None
    principal,=values
    weight=term.extract_multiplicatively(principal)
    if weight is None or weight.has(PVCot,ImpulseTrain,sp.DiracDelta):return None
    from .periodic_generalized import cotangent_geometry
    geometry=cotangent_geometry(principal,frequency)
    pair=_integer_delay(weight,frequency)
    if geometry is None or pair is None:return None
    period,origin,orientation=geometry
    if not isinstance(period,sp.Integer):return None
    coefficient,delay=pair
    position=index-delay
    return (2*sp.pi*sp.I*orientation*coefficient*sp.exp(sp.I*origin*position)
            *sp.sign(position)*sp.KroneckerDelta(sp.Mod(position,period),0))


def inverse_periodic_impulses(value,frequency,index,lower,upper):
    """Count the periodic seam once, with full weight for a single endpoint."""
    from .periodic_signals import ImpulseTrain, PVCot, weighted_lines

    if not value.has(sp.DiracDelta,ImpulseTrain,PVCot):return sp.S.Zero,value
    known=[];remaining=[];ends={lower:[],upper:[]}
    kernel=sp.exp(sp.I*frequency*index)
    full_cycle=sp.simplify(upper-lower-2*sp.pi)==0
    for term in sp.Add.make_args(sp.expand_mul(value)):
        checkpoint()
        if term.has(PVCot):
            recovered=_inverse_delayed_principal_value(term,frequency,index) if full_cycle else None
            if recovered is None:remaining.append(term)
            else:known.append(recovered)
            continue
        if term.has(ImpulseTrain):
            integer_comb=_inverse_delayed_comb(term,frequency,index) if full_cycle else None
            if integer_comb is not None:
                known.append(integer_comb)
                continue
            lines=weighted_lines(term,frequency,lower,upper)
            if lines is None:remaining.append(term)
            else:known.extend(area*kernel.subs(frequency,point) for point,area in lines)
            continue
        deltas=term.atoms(sp.DiracDelta)
        answer=impulse_integral(term,frequency,kernel,lower,upper) if deltas else None
        if answer is None:
            remaining.append(term)
            continue
        affine=affine_impulse(next(iter(deltas)),frequency)
        position=affine[1]
        if position in ends:ends[position].append(answer)
        else:known.append(answer)
    left,right=ends.values()
    seam=sp.Add(*left,*right)/(2 if left and right else 1)
    return (sp.Add(*known)+seam)/(2*sp.pi),sp.Add(*remaining)


def fourier_pairs(value,variable,output,*,inverse=False):
    """Extract certified distributions without breaking ordinary cancellations."""
    from .periodic_signals import ImpulseTrain, affine_train_term, wrapped_period

    known=[];remaining=[];kernel=sp.exp((sp.I if inverse else -sp.I)*variable*output)
    divisor=2*sp.pi if inverse else sp.S.One
    def polynomial_pair(term):
        rate=sp.S.Zero;factors=[]
        for factor in sp.Mul.make_args(term):
            if factor.func==sp.exp and factor.has(variable):
                slope=sp.diff(factor.args[0],variable);offset=sp.simplify(factor.args[0]-slope*variable)
                if slope.has(variable) or offset.has(variable):return None
                rate+=slope;factors.append(sp.exp(offset))
            else:factors.append(factor)
        carrier=sp.simplify(rate/sp.I)
        if carrier.is_real is not True:return None
        try:polynomial=sp.Poly(sp.Mul(*factors),variable)
        except sp.PolynomialError:return None
        argument=output+carrier if inverse else output-carrier
        multiplier=-sp.I if inverse else sp.I;scale=sp.S.One if inverse else 2*sp.pi
        return scale*sp.Add(*(c*multiplier**m[0]*sp.DiracDelta(argument,m[0]) for m,c in polynomial.terms()))
    if not inverse and value.has(ImpulseTrain):
        from .gated_impulse_trains import partition_trains,spectrum

        spans,value=partition_trains(value,variable)
        terms = [spectrum(span, output) for span in spans]
        if None in terms:
            raise ValueError('Una cola de impulsos crece exponencialmente y no tiene transformada de Fourier. Usá Laplace para revisar su región de convergencia.')
        known.extend(terms)
    for term in sp.Add.make_args(value):
        checkpoint()
        train=affine_train_term(term,variable)
        if train is not None:
            period,origin,area=train
            phase=sp.exp((sp.I if inverse else -sp.I)*output*origin)
            known.append(2*sp.pi*area*phase*ImpulseTrain(output,2*sp.pi/period)/(period*divisor))
            continue
        if inverse and term.has(ImpulseTrain):
            from .periodic_comb_inverse import inverse_weighted_comb
            answer=inverse_weighted_comb(term,variable,output)
            if answer is not None:
                known.append(answer)
                continue
        cycle=wrapped_period(term,variable)
        if cycle is not None and not term.has(ImpulseTrain,sp.DiracDelta):
            period,first,ordinary=cycle
            weight=sp.integrate(ordinary*kernel,(variable,first,first+period))
            known.append(2*sp.pi*weight*ImpulseTrain(output,2*sp.pi/period)/(period*divisor))
            continue
        if term.has(sp.DiracDelta):
            answer=impulse_integral(term,variable,kernel)
            if answer is not None:known.append(answer/divisor);continue
            remaining.append(term);continue
        direct=polynomial_pair(term)
        if direct is not None:known.append(direct);continue
        # Rewrite trigonometric carriers only. Rewriting all powers can turn
        # t**2 into exp(2*log(t)), losing even the basic polynomial table.
        trigonometric=term.replace(lambda node:node.func in (sp.sin,sp.cos),lambda node:node.rewrite(sp.exp))
        rewritten=sp.Add.make_args(sp.expand(trigonometric,power_base=False,power_exp=False))
        candidates=[polynomial_pair(item) for item in rewritten]
        if all(item is not None for item in candidates):known.extend(candidates)
        else:remaining.append(term)
    return sp.Add(*known),sp.Add(*remaining)


def ordinary_laplace(value, variable, output, *, split_support=True):
    """Apply an exponential translation after the base transform is evaluated."""
    from .jobs import checkpoint

    if split_support and value.has(sp.Heaviside, sp.Piecewise, sp.Abs, sp.sign):
        from .periodic_support import split_periodic_support
        from .periodic_fourier import finite_laplace_piece, periodic_integral

        spans = split_periodic_support(value, variable, preserve_addends=True, require_wrap=False)
        if spans is not None:
            pieces, planes, conditions = [], [], []
            for branch, lower, upper in spans:
                checkpoint()
                lower = sp.Max(sp.S.Zero, lower)
                if branch == 0 or lower >= upper:
                    continue
                if upper.is_finite:
                    piece = (periodic_integral(branch,variable,lower,upper,laplace_variable=output)
                             if branch.has(sp.Mod) else finite_laplace_piece(branch,variable,output,lower,upper))
                    pieces.append(piece if piece is not None else
                                  sp.Integral(branch*sp.exp(-output*variable),(variable,lower,upper)))
                else:
                    local = sp.Dummy('time', positive=True)
                    piece, plane, condition = ordinary_laplace(
                        branch.subs(variable,local+lower),local,output,split_support=False)
                    pieces.append(sp.exp(-output*lower)*piece)
                    planes.append(plane)
                    conditions.append(condition)
            return sp.Add(*pieces), sp.Max(-sp.oo,*planes), sp.And(*conditions)

    results, planes, conditions = [], [], []
    for term in sp.Add.make_args(sp.expand_mul(value)):
        if term == 0:
            continue
        checkpoint()
        shift = sp.S.Zero
        factors = []
        for factor in sp.Mul.make_args(term):
            if factor.func == sp.exp and factor.has(variable):
                exponent = sp.expand(factor.args[0])
                rate = exponent.coeff(variable)
                constant = exponent - rate*variable
                if not (rate.has(variable) or constant.has(variable)):
                    shift += rate
                    factors.append(sp.exp(constant))
                    continue
            factors.append(factor)
        # Keeping the kernel argument symbolic also lets the t**k table
        # differentiate it before the frequency translation.
        result, plane, condition = sp.laplace_transform(sp.Mul(*factors),variable,output)
        at = output-shift
        results.append(result.subs(output,at))
        planes.append(plane+sp.re(shift))
        conditions.append(sp.sympify(condition).subs(output,at))
    return sp.Add(*results), sp.Max(-sp.oo,*planes), sp.And(*conditions)


def unilateral_laplace(value,variable,output):
    """Keep 0-minus impulse weights and derivative scaling out of generic tables."""
    from .periodic_fourier import gated_periodic_laplace,periodic_laplace
    from .periodic_signals import ImpulseTrain

    gated=gated_periodic_laplace(value,variable,output)
    if gated is not None:
        finite,tail=gated
        return sp.factor_terms(finite+tail),sp.S.Zero if tail!=0 else -sp.oo,sp.true

    known=[];remaining=[];periodic=[]
    train_plane = -sp.oo
    if value.has(ImpulseTrain):
        from .gated_impulse_trains import laplace_spans,partition_trains

        spans,value=partition_trains(value,variable,require_roc=True)
        result,lower,_=laplace_spans(spans,output,unilateral=True)
        (periodic if lower==0 else known).append(result)
        if lower != 0:
            train_plane = lower
    for term in sp.Add.make_args(sp.expand_mul(expand_real_impulses(value,variable))):
        extension=periodic_laplace(term,variable,output) if term.has(sp.Mod) else None
        if extension is not None:
            periodic.append(extension)
            continue
        gated=gated_periodic_laplace(term,variable,output)
        if gated is not None:
            known.append(gated[0])
            periodic.append(gated[1])
            continue
        if term.has(sp.DiracDelta):
            answer=impulse_integral(term,variable,sp.exp(-output*variable),sp.S.Zero,sp.oo)
            known.append(answer if answer is not None else sp.LaplaceTransform(term,variable,output))
        else:
            remaining.append(term)
    result, plane, condition = ordinary_laplace(sp.Add(*remaining),variable,output)
    periodic=sp.simplify(sp.Add(*periodic))
    if periodic!=0:plane=sp.Max(plane,0)
    combined = sp.Add(*known)+result+periodic
    combined = sp.factor_terms(combined) if combined.has(sp.Piecewise) else sp.simplify(combined)
    return combined,sp.Max(plane,train_plane),condition
