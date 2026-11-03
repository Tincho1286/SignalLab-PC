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

def real_field(widget,*,minimum=None,maximum=None,strict=False):
    from .validation import invalid
    source=widget.text().strip().replace('π','pi').replace('−','-')
    if re.fullmatch(r'[+-]?\d+,\d+',source):source=source.replace(',','.')
    try:
        tree=ast.parse(source.replace('^','**'),mode='eval')
        if any(isinstance(node,ast.Name) and node.id.lower() in {'n','k','t','x','w'} for node in ast.walk(tree)):raise ValueError('Se requiere una constante, sin variables.')
        value=complex(evaluate_expression(source,np.array([0.]))[0])
        if value.imag or not np.isfinite(value.real):raise ValueError('Se requiere un valor real finito.')
    except Exception as exc:
        invalid(widget,'no se pudo interpretar el valor.','Ingresá una constante real finita: pi/4, 10^(-3), 1e-3 o 1/100. Detalle: '+str(exc))
    if minimum is not None and (value.real<=minimum if strict else value.real<minimum):invalid(widget,'valor fuera de rango.',f'Debe ser {"mayor que" if strict else "mayor o igual que"} {minimum}.')
    if maximum is not None and value.real>maximum:invalid(widget,'valor fuera de rango.',f'Debe ser menor o igual que {maximum}.')
    return value.real

def integer_field(widget,*,minimum=None,maximum=None):
    from .validation import invalid
    source=widget.text().strip().replace('π','pi').replace('−','-')
    if re.fullmatch(r'[+-]?\d+',source):value=int(source)
    else:
        number=real_field(widget)
        if not number.is_integer():invalid(widget,'debe ser entero, sin parte decimal.','Por ejemplo: 64 o 2^8.')
        if abs(number)>2**53:invalid(widget,'la expresión excede la precisión entera.','Para enteros grandes, escribí el número completo sin operaciones.')
        value=int(number)
    if minimum is not None and value<minimum:invalid(widget,'valor fuera de rango.',f'Ingresá un entero mayor o igual que {minimum}.')
    if maximum is not None and value>maximum:invalid(widget,'valor fuera de rango.',f'Ingresá un entero menor o igual que {maximum}.')
    return value


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
