"""Entradas escalares con expresiones y mensajes vinculados al campo."""
import ast,re
import numpy as np
from .engine import evaluate_expression

def field_name(widget):
    if hasattr(widget,'accessibleName') and widget.accessibleName():return widget.accessibleName()
    parent=widget.parentWidget() if hasattr(widget,'parentWidget') else None
    while parent is not None:
        layout=parent.layout()
        if hasattr(layout,'labelForField'):
            try:label=layout.labelForField(widget)
            except TypeError:label=None
            if label is not None and hasattr(label,'text'):return label.text()
        parent=parent.parentWidget()
    return 'Este campo'

def real_field(widget):
    name=field_name(widget);source=widget.text().strip().replace('π','pi').replace('−','-')
    if re.fullmatch(r'[+-]?\d+,\d+',source):source=source.replace(',','.')
    try:
        tree=ast.parse(source.replace('^','**'),mode='eval')
        if any(isinstance(node,ast.Name) and node.id.lower() in {'n','k','t','x','w'} for node in ast.walk(tree)):raise ValueError('Se requiere una constante, sin variables.')
        value=complex(evaluate_expression(source,np.array([0.]))[0])
        if value.imag or not np.isfinite(value.real):raise ValueError('Se requiere un valor real finito.')
        return value.real
    except Exception as exc:raise ValueError(f'{name}: ingresá un número real o una expresión constante, por ejemplo 0.5, pi/4 o 1/100. {exc}') from exc

def integer_field(widget):
    source=widget.text().strip().replace('π','pi').replace('−','-')
    if re.fullmatch(r'[+-]?\d+',source):return int(source)
    value=real_field(widget)
    if not value.is_integer():raise ValueError(f'{field_name(widget)}: debe ser entero, sin parte decimal.')
    if abs(value)>2**53:raise ValueError(f'{field_name(widget)}: para enteros grandes, escribí el número completo sin operaciones.')
    return int(value)


def constant_value(text):
    """Constante real o compleja: evalúa aritmética, nunca nombres del eje."""
    source=str(text).strip().replace('π','pi').replace('−','-')
    if not source:raise ValueError('Completá el valor.')
    # Sólo la unidad imaginaria, sin alterar pi, sin ni otros identificadores.
    source=re.sub(r'(?<=[0-9.)])\s*[iI]\b','*i',source)
    source=re.sub(r'\b[jJ]\b','i',source)
    try:
        tree=ast.parse(source.replace('^','**'),mode='eval')
        if any(isinstance(node,ast.Name) and node.id.lower() in {'n','k','t','x','w'} for node in ast.walk(tree)):
            raise ValueError('El coeficiente debe ser constante, sin variables; reemplazá el exponente por un número.')
        return complex(evaluate_expression(source,np.array([0.]))[0])
    except (ValueError,SyntaxError,TypeError) as exc:
        raise ValueError('Ingresá una constante finita: se admiten pi, 10^(-3), 1e-3 y operaciones entre números. '+str(exc)) from exc
