"""Stable polynomial/partial-fraction shape, including constant functions."""
import sympy as sp


def apart_list(expression,variable):
    if not expression.has(variable):return sp.S.One,sp.Poly(expression,variable),[]
    return sp.apart_list(expression,variable)
