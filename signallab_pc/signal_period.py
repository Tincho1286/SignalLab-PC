"""Prove a period from a signal definition without fitting a finite record."""

import ast
from itertools import islice
from tokenize import TokenError

import sympy as sp

from .periodic_signals import ImpulseTrain, _common_period, _wrap_geometry, affine_train_term


def _periods(value, variable):
    if not value.has(variable):
        return []
    if value == variable:
        return None
    if value.func == sp.Mod:
        entries = _wrap_geometry(value, variable)
        if entries is not None:
            return [entry[-1] for entry in entries]
    if value.func == ImpulseTrain:
        geometry = affine_train_term(value, variable)
        return [geometry[0]] if geometry is not None and geometry[0].is_positive is True else None
    operator = value.func
    argument = value.args[0] if operator in (sp.sin, sp.cos, sp.tan, sp.exp) else None
    if value.is_Pow and not value.base.has(variable) and sp.Abs(value.base) == 1:
        operator, argument = sp.exp, sp.log(value.base) * value.exp
    if argument is not None:
        slope = sp.simplify(sp.diff(argument, variable))
        offset = sp.simplify(argument - slope*variable) if not slope.has(variable) else argument
        if not offset.has(variable) and slope.is_finite is True and offset.is_finite is True:
            frequency = slope / sp.I if operator == sp.exp else slope
            if frequency.is_real is True:
                if frequency.is_zero is True:
                    return []
                if frequency.is_zero is False:
                    turn = sp.pi if operator == sp.tan else 2 * sp.pi
                    ratio = sp.simplify(frequency / turn)
                    if variable.is_integer:
                        return [sp.Integer(ratio.q)] if ratio.is_Rational else None
                    return [sp.simplify(1 / sp.Abs(ratio))]
    periods = []
    for argument in value.args:
        result = _periods(argument, variable)
        if result is None:
            return None
        periods.extend(result)
    return periods


def expression_period(value, variable):
    """Return a proven period, zero for a constant or None when unknown."""
    if not isinstance(value, sp.Expr) or value.free_symbols - {variable}:
        return None
    if len(list(islice(sp.preorder_traversal(value), 401))) > 400 or value.has(sp.nan, sp.zoo, sp.oo, -sp.oo):
        return None
    try:
        periods = _periods(value, variable)
        if periods is None:
            return None
        return _common_period(periods) if periods else sp.S.Zero
    except (ValueError, ArithmeticError, TypeError, NotImplementedError, RecursionError):
        return None


def _declared_cycle(source, variable, parse):
    """Preserve an explicit Repeat period when the parsed waveform is constant."""
    from .math_source import normalize

    node = ast.parse(normalize(source), mode='eval').body
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        name, args = node.func.id.lower(), node.args
        position = 1 if name == 'repeat' else 0
        if len(args) <= position or not isinstance(args[position], ast.Name) or args[position].id.lower() != variable.name:
            return sp.S.Zero
        if name == 'repeat' and len(args) in (3, 4):
            return sp.simplify(parse(ast.unparse(args[2])))
        if name == 'repeatsamples' and len(args) in (3, 4) and isinstance(args[2], ast.Tuple):
            step = parse(ast.unparse(args[3])) if len(args) == 4 else sp.S.One
            return sp.simplify(len(args[2].elts)*step)
    return sp.S.Zero


def formula_period(source, domain, *other_formulas):
    from .symbolic import N, T, parse

    variable = N if domain == 'discrete' else T
    try:
        periods = []
        for text in (source, *other_formulas):
            if not isinstance(text, str) or not text.strip():
                return None
            period = expression_period(parse(text), variable)
            if period == 0:
                period = _declared_cycle(text, variable, parse)
            periods.append(period)
        if None in periods:
            return None
        nonconstant = [period for period in periods if period != 0]
        return _common_period(nonconstant) if nonconstant else None
    except (ValueError, SyntaxError, TokenError, ArithmeticError, TypeError, NotImplementedError, RecursionError):
        return None
