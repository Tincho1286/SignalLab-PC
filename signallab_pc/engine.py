"""Motor matemático mínimo de la primera entrega; no ejecuta texto Python."""

import ast
import operator

import numpy as np

from .model import Signal
from .resources import ensure_working_set


_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: lambda a, b: np.power(np.asarray(a, dtype=np.complex128), b), ast.Mod: operator.mod}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_FUNCS = {"sin": np.sin, "cos": np.cos, "tan": np.tan, "exp": np.exp,
          "sqrt": lambda v: np.sqrt(np.asarray(v, dtype=np.complex128)),
          "abs": np.abs, "log": lambda v: np.log(np.asarray(v, dtype=np.complex128)),
          "ln": lambda v: np.log(np.asarray(v, dtype=np.complex128)),
          "sinh": np.sinh, "cosh": np.cosh, "tanh": np.tanh, "sign": np.sign,
          "asin": np.arcsin, "acos": np.arccos, "atan": np.arctan,
          "re": np.real, "im": np.imag, "conj": np.conjugate,
          "floor": np.floor, "ceiling": np.ceil, "ceil": np.ceil,
          "heaviside": lambda v, edge=.5: np.heaviside(v, edge),
          "step": lambda v: np.asarray(v) >= 0,
          "impulse": lambda v: np.asarray(v) == 0,
          "sinc": np.sinc}


class ExpressionError(ValueError):
    pass


def evaluate_expression(expression: str, x: np.ndarray) -> np.ndarray:
    """Evalúa una expresión real/complexa con x, pi, e y funciones permitidas."""
    source = expression.strip().replace("^", "**")
    if not source:
        raise ExpressionError("Escribí una expresión, por ejemplo cos(pi*x/4).")
    try:
        tree = ast.parse(source, mode="eval")
        node_count = sum(1 for _ in ast.walk(tree))
        coordinates = np.asarray(x, dtype=float)
        ensure_working_set(coordinates.size, live_arrays=max(4, node_count + 3))
        result = _visit(tree.body, coordinates)
        arr = np.asarray(result, dtype=np.complex128)
        if arr.ndim == 0:
            arr = np.full(np.asarray(x).shape, arr, dtype=np.complex128)
        if arr.shape != np.asarray(x).shape:
            arr = np.broadcast_to(arr, np.asarray(x).shape).astype(np.complex128)
        if np.any(~np.isfinite(arr)):
            raise ExpressionError("La expresión produce valores no finitos en la ventana elegida.")
        return arr
    except ExpressionError:
        raise
    except Exception as exc:
        raise ExpressionError(f"No se pudo evaluar la expresión: {exc}") from exc


def _visit(node, x):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float, complex)):
        return node.value
    if isinstance(node, ast.Name):
        key = node.id.lower()
        if key in {"x", "t", "n", "k", "w"}:
            return x
        if key == "pi":
            return np.pi
        if key == "e":
            return np.e
        if key == "i":
            return 1j
        raise ExpressionError(f"Nombre no permitido: {node.id}")
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
        if isinstance(node.op,ast.Mult):
            factors=[]
            def flatten(value):
                if isinstance(value,ast.BinOp) and isinstance(value.op,ast.Mult):flatten(value.left);flatten(value.right)
                else:factors.append(value)
            flatten(node)
            gates=[value for value in factors if isinstance(value,ast.Call) and isinstance(value.func,ast.Name) and value.func.id.lower() in ('step','impulse','heaviside','kroneckerdelta')]
            if gates:
                # A supported signal is zero outside its support. Do not first
                # overflow an exponential there and then multiply infinity by 0.
                remaining=[value for value in factors if value not in gates]
                if remaining:
                    weight=np.ones(np.asarray(x).shape,dtype=np.complex128)
                    for gate in gates:weight*=_visit(gate,x)
                    active=weight!=0;answer=np.zeros(weight.shape,dtype=np.complex128)
                    if np.any(active):
                        product=np.ones(np.count_nonzero(active),dtype=np.complex128)
                        for value in remaining:product*=_visit(value,np.asarray(x)[active])
                        answer[active]=weight[active]*product
                    return answer
        return _BIN[type(node.op)](_visit(node.left, x), _visit(node.right, x))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_visit(node.operand, x))
    if isinstance(node, ast.Compare):
        comparisons = {ast.Lt: operator.lt, ast.LtE: operator.le, ast.Gt: operator.gt,
                       ast.GtE: operator.ge, ast.Eq: operator.eq, ast.NotEq: operator.ne}
        left = _visit(node.left, x)
        result = np.ones(np.asarray(x).shape, dtype=bool)
        for operation, operand in zip(node.ops, node.comparators):
            if type(operation) not in comparisons: raise ExpressionError("Comparación no permitida.")
            right = _visit(operand, x)
            result &= comparisons[type(operation)](left, right)
            left = right
        return result
    if isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
        result = np.full(np.asarray(x).shape, isinstance(node.op, ast.And), dtype=bool)
        for value in node.values:
            result = np.logical_and(result, _visit(value, x)) if isinstance(node.op, ast.And) else np.logical_or(result, _visit(value, x))
        return result
    if isinstance(node, ast.IfExp):
        return _piecewise(node.test, node.body, node.orelse, x)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
        if node.func.id.lower() == "where" and len(node.args) == 3:
            return _piecewise(*node.args, x)
        if node.func.id.lower()=='heaviside' and len(node.args)==2:
            return _FUNCS['heaviside'](*[_visit(arg,x) for arg in node.args])
        if node.func.id.lower()=='kroneckerdelta' and len(node.args)==2:
            return np.asarray(_visit(node.args[0],x))==np.asarray(_visit(node.args[1],x))
        fn = _FUNCS.get(node.func.id.lower())
        if fn is None or len(node.args) != 1:
            raise ExpressionError("Función no permitida; disponibles: " + ", ".join(_FUNCS))
        return fn(_visit(node.args[0], x))
    raise ExpressionError("La expresión contiene sintaxis no admitida.")


def sequence_from_expression(expression: str, origin: int, count: int, *, name="x") -> Signal:
    if isinstance(origin, bool) or not isinstance(origin, (int, np.integer)):
        raise ValueError("El índice inicial debe ser un entero.")
    if isinstance(count, bool) or not isinstance(count, (int, np.integer)) or int(count) < 1:
        raise ValueError("La cantidad debe ser un entero positivo.")
    origin, count = int(origin), int(count)
    limit = np.iinfo(np.int64)
    if origin < limit.min or origin + count - 1 > limit.max:
        raise ValueError("El eje excede el rango de índices enteros de 64 bits.")
    ensure_working_set(count, live_arrays=6)
    indices = np.arange(origin, origin + count, dtype=np.int64)
    values = evaluate_expression(expression, indices)
    return Signal(values, origin, 1.0, "n", name, "discrete", expression)


def sequence_from_values(text: str, origin: int, *, name="x") -> Signal:
    if isinstance(origin, bool) or not isinstance(origin, (int, np.integer)):
        raise ValueError("El índice inicial debe ser un entero.")
    source = text.strip()
    if source.startswith("[") and source.endswith("]"):source=source[1:-1]
    fields = [part.strip() for part in source.replace(";", ",").replace("\n", ",").split(",") if part.strip()]
    if not fields:
        raise ValueError("Ingresá al menos una muestra separada por comas.")
    limit = np.iinfo(np.int64)
    if int(origin) < limit.min or int(origin) + len(fields) - 1 > limit.max:
        raise ValueError("El eje excede el rango de índices enteros de 64 bits.")
    ensure_working_set(len(fields), live_arrays=5)
    values=[]
    from .numeric_input import constant_value
    for index,part in enumerate(fields,1):
        try:
            try:value=complex(part.replace("i","j").replace("I","j"))
            except ValueError:value=constant_value(part)
            values.append(value)
        except ValueError as exc:raise ValueError(f'Muestra {index} ({part}): {exc}') from exc
    return Signal(np.asarray(values), int(origin), 1.0, "n", name, "discrete", "lista ingresada")


def replace_sample(signal: Signal, index: int, value: complex) -> Signal:
    if index < 0 or index >= signal.values.size:
        raise IndexError("El índice seleccionado no existe en la señal.")
    values = signal.values.copy()
    values[index] = value
    return signal.copy_with(values=values)




def _piecewise(condition, left, right, coordinates):
    """Evalúa únicamente la rama seleccionada; where(x==0,0,1/x) no divide por cero."""
    mask = np.broadcast_to(np.asarray(_visit(condition, coordinates), dtype=bool), np.asarray(coordinates).shape)
    result = np.empty(mask.shape, dtype=np.complex128)
    for selected, expression in ((mask, left), (~mask, right)):
        if np.any(selected):
            result[selected] = _visit(expression, np.asarray(coordinates)[selected])
    return result
