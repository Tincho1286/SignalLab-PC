"""Bilateral Laplace: intersect half-plane ROCs, invert rational modes by support."""
import sympy as sp
from .partial_fractions import apart_list
from .symbolic import parse, T, S, N, Z, W
from .jobs import checkpoint
from .resources import ensure_working_set
from .signal_notation import source


def roc_text(lower, upper):
    if lower == -sp.oo and upper == sp.oo:
        return 'Todo el plano s finito'
    if upper == sp.oo:
        return 'Re(s) > ' + str(lower)
    if lower == -sp.oo:
        return 'Re(s) < ' + str(upper)
    return str(lower) + ' < Re(s) < ' + str(upper)


def direct(request):
    from .expression_definition import prepare,attach
    definition=prepare(request['expression'],T,'continuous',(-sp.oo,sp.oo),request.get('input_conditions',()),'integration_interval')
    value = definition.integral_expression()
    if value.has(S, N, Z, W):
        raise ValueError('Laplace directa: ingresá x(t) usando t.')
    # Distributions at t=0 belong to the full transform once, not to both
    # unilateral halves. Integrate singular additive terms separately.
    regular = []; singular = []
    for term in sp.Add.make_args(sp.expand_mul(value)):
        (singular if term.has(sp.DiracDelta) else regular).append(term)
    from .procedure import step
    records=[];impulse = sp.S.Zero
    for term in singular:
        checkpoint()
        from .impulse_pairs import impulse_integral
        pair=impulse_integral(term,T,sp.exp(-S*T))
        current=pair if pair is not None else sp.integrate(term * sp.exp(-S*T), (T, -sp.oo, sp.oo))
        impulse+=current
        records.append(step('Aporte de impulso','Integración distribucional sobre toda la recta',term,current,conditions='El peso se incorpora una sola vez, también en t=0.',source='impulse_pairs.impulse_integral'))
    regular = sp.piecewise_fold(sp.Add(*regular).rewrite(sp.Piecewise))
    try:
        regions = regular.as_expr_set_pairs(domain=sp.S.Reals) if isinstance(regular, sp.Piecewise) else [(regular, sp.S.Reals)]
    except (NotImplementedError, ValueError) as exc:
        raise ValueError('No se pudo determinar el soporte real de los tramos. Usá bordes temporales reales y condiciones sobre t.') from exc
    lower = -sp.oo; upper = sp.oo; conditions = []; pieces = [impulse]
    u = sp.Dummy('u', positive=True)
    def half(value):
        return (sp.S.Zero, -sp.oo, sp.true) if value == 0 else sp.laplace_transform(value, u, S)
    for amplitude, region in regions:
        if amplitude == 0:
            continue
        intervals = region.args if isinstance(region, sp.Union) else [region]
        for interval in intervals:
            if isinstance(interval, sp.FiniteSet):
                continue  # Isolated ordinary values have zero integral.
            if not isinstance(interval, sp.Interval):
                raise ValueError('No se pudo expresar el soporte como intervalos reales.')
            a, b = interval.start, interval.end
            checkpoint()
            if a != -sp.oo and b != sp.oo:
                # A bounded time interval has no tail convergence restriction.
                # Applying a unilateral table to a clipped exponential can
                # otherwise report its un-clipped exponent as a false bound.
                pieces.append(sp.integrate(amplitude*sp.exp(-S*T), (T, a, b)))
                records.append(step('Tramo temporal acotado','Integración en el intervalo real registrado',sp.Integral(amplitude*sp.exp(-S*T),(T,a,b)),pieces[-1],conditions='No se agregan restricciones de cola infinita a un tramo acotado.',source='laplace_algebra.direct'))
                continue
            if b == sp.oo:
                start = sp.S.Zero if a == -sp.oo else a
                part, plane, condition = half(amplitude.subs(T, u+start))
                pieces.append(sp.exp(-start*S)*part); lower = sp.Max(lower, plane); conditions.append(condition)
                records.append(step('Cola derecha','Traslación t=u+t₀ y Laplace unilateral',sp.Integral(amplitude*sp.exp(-S*T),(T,start,sp.oo)),pieces[-1],conditions='Re(s) > '+str(plane)+'; '+str(condition),source='laplace_algebra.direct'))
            if a == -sp.oo:
                end = sp.S.Zero if b == sp.oo else b
                part, plane, condition = half(amplitude.subs(T, end-u))
                pieces.append(sp.exp(-end*S)*part.subs(S, -S)); upper = sp.Min(upper, -plane); conditions.append(condition)
                records.append(step('Cola izquierda','Inversión t=t₀−u y sustitución s→−s',sp.Integral(amplitude*sp.exp(-S*T),(T,-sp.oo,end)),pieces[-1],conditions='Re(s) < '+str(-plane)+'; '+str(condition),source='laplace_algebra.direct'))
    condition = sp.simplify(sp.And(*conditions, lower < upper))
    evaluated = not sp.Add(*pieces).has(
        sp.LaplaceTransform, sp.Integral, sp.oo, sp.zoo, sp.nan)
    if condition == sp.false:
        result = sp.Integral(value*sp.exp(-S*T), (T, -sp.oo, sp.oo))
        evaluated = False
    else:
        result = sp.factor_terms(sp.Add(*pieces))
    hint = None
    if not condition.free_symbols and condition == sp.true:
        if upper == sp.oo:
            hint = {'interpretation': 'bilateral', 'laplace_roc': 'right'}
        elif lower == -sp.oo:
            hint = {'interpretation': 'bilateral', 'laplace_roc': 'left'}
        elif not (lower.free_symbols or upper.free_symbols):
            hint = {'interpretation': 'bilateral', 'laplace_roc': 'line', 'sigma': str((lower+upper)/2)}
    answer={
        'operation': 'Laplace bilateral', 'result': str(result), 'output_variable': 's',
        'evaluated': bool(evaluated), 'condition': str(condition), 'convergence_empty': condition == sp.false,
        'roc': 'Vacía: las dos mitades no tienen una zona común de convergencia' if condition == sp.false else roc_text(lower, upper),
        'roc_lower': str(lower), 'roc_upper': str(upper), 'inverse_laplace_hint': hint,
        'scope': ('No existe una ROC abierta común. No se presenta la cancelación formal de las dos mitades como una transformada válida.' if condition == sp.false else
                  'Se integra sobre toda la recta temporal. La ROC es la intersección de las convergencias de t≥0 y t≤0; sus bordes están excluidos. Los impulsos se integran una sola vez. Las condiciones adicionales también deben cumplirse.')}

    records.append(step('Franja común','Intersección de las convergencias',after=roc_text(lower,upper) if condition is not sp.false else 'ROC vacía',conditions=condition,source='laplace_algebra.direct'))
    records.append(step('Resultado','Suma de los aportes compatibles' if condition is not sp.false else 'La definición queda sin evaluar por convergencia vacía',value,result,conditions=condition,source='laplace_algebra.direct'))
    answer['procedure']=records
    return attach(answer,definition)


def _right_of(pole, sigma, values):
    """Prove the selected vertical line is strictly to the right of a pole."""
    approximation = values.value(pole)
    sigma_numeric = values.value(sigma).real
    if abs(sigma_numeric-approximation.real) <= values.context.mpf('1e-65')*max(1, abs(approximation), abs(sigma_numeric)):
        raise ValueError('La línea coincide con la parte real de un polo o queda demasiado cerca para distinguirla con precisión. Elegí otro σ dentro de la ROC.')
    if isinstance(pole, sp.CRootOf):
        interval = pole._get_interval()
        for _ in range(256):
            lo, hi = (interval.a, interval.b) if pole.is_real else (interval.ax, interval.bx)
            if (sigma-sp.Rational(hi)).is_positive is True:
                return True
            if (sp.Rational(lo)-sigma).is_positive is True:
                return False
            interval = interval.refine()
    else:
        distance = sp.simplify(sigma-sp.re(pole))
        if distance.is_positive is True:
            return True
        if distance.is_negative is True:
            return False
    raise ValueError('La línea coincide con la parte real de un polo o no puede separarse de ella. Elegí otro valor de σ dentro de la ROC.')


def inverse(request):
    from .numeric_modes import PoleValues, modal_expression, expression_source
    expression = sp.powsimp(parse(request['expression']))
    if expression.has(T, N, Z, W, sp.zoo, sp.nan, sp.oo):
        raise ValueError('Laplace inversa: ingresá X(s) usando s, con constantes finitas.')
    mode = request.get('laplace_roc', 'right')
    if mode not in ('right', 'left', 'line'):
        raise ValueError('Elegí una ROC derecha, izquierda o una línea interior.')
    sigma = sp.simplify(parse(request.get('sigma', '0'))) if mode == 'line' else sp.S.Zero
    if mode == 'line' and (sigma.free_symbols or sigma.is_real is not True or sigma.is_finite is not True):
        raise ValueError('σ debe ser una constante real finita; admite pi, fracciones y notación científica.')
    # A global exponential is a time shift; the rational ROC does not change.
    delay = sp.S.Zero; rational = sp.S.One
    for factor in sp.Mul.make_args(expression):
        if factor.func == sp.exp and factor.has(S):
            argument = sp.expand(factor.args[0]); slope = argument.coeff(S)
            rest = sp.simplify(argument-slope*S)
            if rest.has(S) or slope.is_real is not True or slope.is_finite is not True:
                raise ValueError('El factor exponencial debe representar un desplazamiento real: exp(-d*s).')
            delay -= slope; rational *= sp.exp(rest)
        else:
            rational *= factor
    rational = sp.cancel(rational)
    try:
        num, den = [sp.Poly(v, S) for v in sp.fraction(rational)]
        ensure_working_set(max(1, int(den.degree())**2), bytes_per_sample=1024, live_arrays=8)
        common, polynomial, parts = apart_list(rational, S)
    except (sp.PolynomialError, NotImplementedError) as exc:
        raise ValueError('La inversa bilateral admite X(s) racional y un desplazamiento global exp(-d*s).') from exc
    parameters = sorted(map(str, rational.free_symbols-{S}))
    if mode == 'line' and parameters:
        raise ValueError('Asigná los parámetros antes de elegir una línea dentro de la ROC.')
    numeric = not parameters
    values = PoleValues(); roots_cache = {}; poles = {}; terms = []; alias = False
    for factor, coefficient, denominator, order in parts:
        if coefficient.expr == 0:
            continue
        dummy = denominator.variables[0]
        if sp.expand(denominator.expr-(S-dummy)) != 0:
            raise ValueError('No se pudo normalizar la descomposición de X(s).')
        key = factor.as_expr()
        if key not in roots_cache:
            checkpoint()
            if factor.degree() > 2 and not (key.free_symbols-{factor.gen}):
                roots = factor.all_roots(radicals=False)
            else:
                solved = sp.roots(key, factor.gen)
                if sum(solved.values()) != factor.degree():
                    raise ValueError('No se resolvieron todos los polos; no se devuelve una inversa incompleta.')
                roots = [p for p, multiplicity in solved.items() for _ in range(multiplicity)]
            roots_cache[key] = roots
            if numeric:
                values.values.update(values.match(factor, roots))
        for pole in roots_cache[key]:
            checkpoint()
            if pole not in poles:
                poles[pole] = mode == 'right' or (mode == 'line' and _right_of(pole, sigma, values))
            c = common*coefficient(pole)
            if c == 0:
                continue
            alias |= pole.has(sp.CRootOf) or sp.count_ops(pole) > 20
            if numeric:
                p = values.value(pole)
                point = sp.Float(str(p.real), 85)+sp.I*sp.Float(str(p.imag), 85)
                nc = values.value(common*coefficient(point))
            else:
                p = nc = None
            terms.append((pole, int(order), c, p, nc, poles[pole]))
    def real_part(pole):
        return pole if pole.is_real is True else sp.re(pole, evaluate=not pole.has(sp.CRootOf))
    right = [real_part(p) for p, side in poles.items() if side]
    left = [real_part(p) for p, side in poles.items() if not side]
    lower = sp.Max(*right, evaluate=not alias) if right else -sp.oo
    upper = sp.Min(*left, evaluate=not alias) if left else sp.oo
    tau = T-delay
    impulses = [common*c*sp.DiracDelta(tau, power) for (power,), c in polynomial.terms() if c]
    groups = {}
    for pole, order, c, _, _, side in terms:
        groups.setdefault(side, []).append(c*tau**(order-1)*sp.exp(pole*tau)/sp.factorial(order-1))
    exact = sp.Add(*impulses, *[(1 if side else -1)*sp.Heaviside(tau if side else -tau)*sp.Add(*items) for side, items in groups.items()])
    approximate = bool(numeric and alias)
    display_terms = []
    if approximate:
        numeric_terms = [{'pole': p, 'coefficient': c, 'order': m, 'right': side} for _, m, _, p, c, side in terms]
        real = all(c.is_real is True for c in num.all_coeffs()+den.all_coeffs())
        modes, fragments = modal_expression(numeric_terms, T, values, 'laplace', real, with_terms=True)
        display = sp.Add(*impulses, modes.subs(T, tau))
        text = expression_source(display)
        display_terms = [expression_source(v.subs(T, tau)) for v in fragments]+[source(v) for v in impulses]
        # RootOf bounds remain exact in the record; readable ROC uses evaluated numbers.
        lower_display = max((values.value(p).real for p, side in poles.items() if side), default=None)
        upper_display = min((values.value(p).real for p, side in poles.items() if not side), default=None)
        display_roc = roc_text(values.number(lower_display) if lower_display is not None else -sp.oo,
                               values.number(upper_display) if upper_display is not None else sp.oo)
    else:
        text = source(exact); display_roc = roc_text(lower, upper)
    decomposition=[str(common*polynomial.as_expr())] if not polynomial.is_zero else []
    for pole,order,c,point,nc,side in terms:
        p=str(values.complex_number(point)) if numeric else str(pole)
        coefficient=str(values.complex_number(nc)) if numeric else str(c)
        decomposition.append('('+coefficient+')/(s-('+p+'))^'+str(order))
    decomposition='+'.join(decomposition) or '0'
    if delay:decomposition='exp(-('+str(delay)+')*s)*('+decomposition+')'
    from .cas_engine import encode
    return {'decomposition':decomposition,'time_shift':('Se desplaza la señal completa en d='+str(delay)+'. La ROC se conserva.' if delay else ''),
        'cas_encoded': encode(exact), 'operation': 'Laplace inversa bilateral', 'result': str(exact), 'display_result': text,
        'display_terms': display_terms, 'display_numeric': approximate, 'display_precision': 17 if approximate else None,
        'output_variable': 't', 'evaluated': True, 'parameters': parameters,
        'roc': display_roc, 'roc_lower': str(lower), 'roc_upper': str(upper),
        'scope': 'La ROC determina el soporte de cada término: los polos a su izquierda generan términos derechos y los polos a su derecha generan términos izquierdos. Los polos repetidos añaden potencias del tiempo a las exponenciales. Los términos polinómicos generan impulsos o sus derivadas.'
                 + (' El factor exp(−d·s) desplaza toda la señal en d='+str(delay)+', sin cambiar la ROC.' if delay else '')
                 + (' La fórmula visible evalúa polos y coeficientes con al menos 17 cifras; la descomposición algebraica exacta se conserva en el resultado.' if approximate else '')}
