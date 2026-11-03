"""One exact scalar grammar for coefficients, numerical fields and algebra."""
import math
import sympy as sp


def exact_constant(source, *, parameters=False):
    from .symbolic import parse, T, N, S, Z, W, TAU
    value=parse(str(source))
    if not isinstance(value,sp.Expr):raise ValueError('Ingresá un número o una expresión escalar, no una condición ni una lista.')
    reserved={T,N,S,Z,W,TAU,sp.Symbol('k')}
    if value.free_symbols & reserved:raise ValueError('Se requiere una constante, sin variables de tiempo, índice o frecuencia.')
    if value.free_symbols and not parameters:raise ValueError('Asigná un número a cada parámetro: '+', '.join(sorted(map(str,value.free_symbols)))+'.')
    value=sp.simplify(value)
    if value.has(sp.nan,sp.zoo,sp.oo,-sp.oo) or value.is_finite is False:raise ValueError('El valor debe ser finito; revisá divisiones por cero y el dominio de las funciones.')
    return value


def numerical_value(value):
    """Convert once, after exact arithmetic; do not silently erase underflow."""
    if value.free_symbols:raise ValueError('Asigná los parámetros antes de obtener valores numéricos.')
    try:number=complex(value.evalf(18))
    except (TypeError,ValueError,OverflowError) as exc:raise ValueError('No se pudo obtener un número finito de la expresión.') from exc
    if not math.isfinite(number.real) or not math.isfinite(number.imag):raise ValueError('El valor excede el rango numérico disponible.')
    for exact,part in ((sp.re(value),number.real),(sp.im(value),number.imag)):
        if part==0 and exact.is_zero is False:raise ValueError('Un componente no nulo es menor que el rango numérico disponible; aumentá su escala.')
    return number


def constant_value(source):return numerical_value(exact_constant(source))


def real_value(source):
    value=exact_constant(source)
    if value.is_real is not True:raise ValueError('Se requiere una constante real finita.')
    return numerical_value(value).real


def integer_value(source):
    value=exact_constant(source)
    if value.is_Integer is not True:raise ValueError('Se requiere un entero exacto, sin parte decimal.')
    return int(value)
