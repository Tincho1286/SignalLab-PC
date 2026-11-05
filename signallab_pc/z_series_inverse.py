"""Inverse Z pairs for convergent reciprocal-power tails."""
from .transform_samples import sample_pair, sample_budget
from dataclasses import dataclass

import sympy as sp

from .jobs import checkpoint
from .resources import ensure_working_set
from .symbolic import N, Z, parse


@dataclass(frozen=True)
class Tail:
    gain: sp.Expr
    delay: int
    base: sp.Expr
    side: int
    order: int
    first: int
    offset: sp.Expr

    @property
    def edge(self):
        return self.delay + self.side * self.first

    def expression(self):
        index = self.side * (N-self.delay)
        value = self.gain * self.base**index / (index+self.offset)**self.order
        return sp.Piecewise((value, index >= self.first), (0, True), evaluate=False)


def _monomial(value):
    coefficient, variable = sp.cancel(value).as_independent(Z, as_Add=False)
    if variable == 1:
        return coefficient, 0
    base, exponent = variable.as_base_exp()
    if base == Z and exponent.is_Integer:
        return coefficient, int(exponent)
    return None


def _term(expression):
    factors = sp.Mul.make_args(expression)
    kernels = [factor for factor in factors if factor.func in (sp.log, sp.polylog, sp.lerchphi) and factor.has(Z)]
    if not kernels:
        finite = _monomial(expression)
        return (finite[0], -finite[1]) if finite is not None else None
    if len(kernels) != 1:
        return None
    kernel = kernels[0]
    prefactor = _monomial(sp.Mul(*(factor for factor in factors if factor is not kernel)))
    if prefactor is None:
        return None
    gain, power = prefactor
    if kernel.func == sp.log and len(kernel.args) == 1:
        argument, order, first, offset = 1-kernel.args[0], 1, 1, sp.S.Zero
        gain = -gain
    elif kernel.func == sp.polylog:
        order, argument = kernel.args
        first, offset = 1, sp.S.Zero
    elif kernel.func == sp.lerchphi:
        argument, order, offset = kernel.args
        first = 0
        if offset.free_symbols or offset.is_positive is not True or offset.is_finite is not True:
            return None
    else:
        return None
    if sp.sympify(order).is_Integer is not True or order < 1:
        return None
    ratio = _monomial(argument)
    if ratio is None or ratio[1] not in (-1, 1) or ratio[0].is_zero is True:
        return None
    return Tail(gain, -power, ratio[0], -ratio[1], int(order), first, offset)


def inverse_tails(request, raw):
    """Invert finite Laurent terms plus shifted logarithmic, Li and Lerch tails."""
    if not raw.has(sp.log, sp.polylog, sp.lerchphi):
        return None
    # Collect by kernel first. Combining rational coefficients can recover a
    # Laurent monomial even if the input was written over a common denominator.
    kernels = [node for node in raw.atoms(sp.log, sp.polylog, sp.lerchphi) if node.has(Z)]
    placeholders = {kernel: sp.Dummy('kernel') for kernel in kernels}
    if not placeholders:
        return None
    try:
        parts = sp.Poly(sp.cancel(raw.xreplace(placeholders)), *placeholders.values())
    except sp.PolynomialError:
        return None
    tails = []
    rational = sp.S.Zero
    for powers, coefficient in parts.terms():
        degree = sum(powers)
        if degree == 0:
            rational = coefficient
        elif degree == 1:
            kernel = kernels[powers.index(1)]
            # A Laurent polynomial times a kernel is a sum of shifted tails.
            for factor in sp.Add.make_args(sp.expand_mul(coefficient)):
                term = _term(factor*kernel)
                if not isinstance(term, Tail):
                    return None
                tails.append(term)
        else:
            return None
    if not tails:
        return None
    if not rational.is_rational_function(Z):
        return None
    right = [sp.Abs(term.base) for term in tails if term.side == 1]
    left = [1/sp.Abs(term.base) for term in tails if term.side == -1]
    lower = sp.Max(*right) if right else sp.S.Zero
    upper = sp.Min(*left) if left else sp.oo
    mode = request.get('roc', 'right')
    if mode not in ('right', 'left', 'radius'):
        raise ValueError('Elegí soporte derecho, izquierdo o una ROC por radio.')
    if (mode == 'right' and left) or (mode == 'left' and right):
        raise ValueError('La ROC elegida no es compatible con la serie de esta expresión. '
                         'Usá soporte derecho para potencias de 1/z, izquierdo para potencias de z, '
                         'o un radio interior si hay colas de ambos lados.')
    from .cas_engine import encode, restore
    rational_result = None
    rational_samples = []
    if rational != 0:
        from .z_inverse import inverse
        include_samples = request.get('include_samples', True) and not (raw.free_symbols - {Z})
        rational_result = inverse(dict(request, expression=str(rational), include_samples=include_samples),
                                  sample_sink=rational_samples)
        rational_lower, rational_upper = restore(rational_result['roc_bounds_encoded'])
        lower = sp.Max(lower, rational_lower)
        upper = sp.Min(upper, rational_upper)
    region = lower < upper
    if region is sp.false:
        raise ValueError('Los términos no comparten una región abierta de convergencia.')
    if mode == 'radius':
        radius = parse(request.get('radius', '1'))
        if radius.free_symbols or radius.is_positive is not True or radius.is_finite is not True:
            raise ValueError('El radio debe ser real, positivo y finito.')
        if sp.And(lower < radius, radius < upper) is not sp.true:
            raise ValueError('El radio debe estar estrictamente dentro de la ROC de la serie.')

    rational_sequence = restore(rational_result['cas_encoded']) if rational_result else sp.S.Zero
    expression = sp.Add(rational_sequence, *(term.expression() for term in tails))
    parameters = sorted(map(str, expression.free_symbols - {N}))
    start = int(request.get('start', -16))
    samples = None
    if request.get('include_samples', True) and not parameters:
        count = int(request.get('count', 65))
        if count < 1:
            raise ValueError('Usá una cantidad positiva de muestras.')
        sample_budget(count, bytes_per_sample=1024, live_arrays=10)
        from .numeric_modes import PoleValues
        numbers = PoleValues()
        numeric_tails = [(term, numbers.value(term.gain), numbers.value(term.base), numbers.value(term.offset)) for term in tails]
        samples = []
        for index in range(start, start+count):
            if (index-start) % 64 == 0:
                checkpoint()
            value = numbers.context.mpc(rational_samples[index-start]) if rational_samples else numbers.context.mpc(0)
            for term, gain, base, offset in numeric_tails:
                j = term.side * (index-term.delay)
                if j >= term.first:
                    value += gain * base**j / (j+offset)**term.order
            samples.append(sample_pair(value))

    zero_included = not right and all(term.edge <= 0 for term in tails) and (not rational_result or rational_result['zero_included'])
    infinity_included = not left and all(term.edge >= 0 for term in tails) and (not rational_result or rational_result['infinity_included'])
    rational_condition = parse(rational_result.get('condition', 'True')) if rational_result else sp.true
    condition = sp.And(region, rational_condition, *(sp.Ne(term.base, 0) for term in tails))
    from .signal_notation import SignalPrinter
    return {
        'operation': 'Z inversa por propiedades', 'method': 'reciprocal_series_pairs',
        'result': str(expression), 'display_result': SignalPrinter({'order': 'none'}).doprint(expression),
        'display_numeric': False, 'display_terms': [], 'evaluated': True, 'output_variable': 'n',
        'origin': start, 'numeric_samples': samples, 'parameters': parameters,
        'roc': f"{lower}{' ≤ ' if zero_included else ' < '}|z| < {upper}",
        'infinity_included': infinity_included, 'zero_included': zero_included, 'roc_bounds_encoded': encode(sp.Tuple(lower, upper)),
        'cas_encoded': encode(expression), 'condition': str(condition),
        'scope': 'Se aplicaron linealidad, desplazamiento y los coeficientes de las series logarítmicas o de potencias recíprocas. La ROC indicada es abierta en sus radios no nulos.',
    }
