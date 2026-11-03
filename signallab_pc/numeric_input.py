"""Entradas escalares con expresiones y mensajes vinculados al campo."""
import re
from .scalar_expression import constant_value,real_value,integer_value

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
        value=real_value(source)
    except Exception as exc:
        invalid(widget,'no se pudo interpretar el valor.','Ingresá una constante real finita: pi/4, 10^(-3), 1e-3 o 1/100. Detalle: '+str(exc))
    if minimum is not None and (value<=minimum if strict else value<minimum):invalid(widget,'valor fuera de rango.',f'Debe ser {"mayor que" if strict else "mayor o igual que"} {minimum}.')
    if maximum is not None and value>maximum:invalid(widget,'valor fuera de rango.',f'Debe ser menor o igual que {maximum}.')
    return value

def integer_field(widget,*,minimum=None,maximum=None):
    from .validation import invalid
    source=widget.text().strip().replace('π','pi').replace('−','-')
    if re.fullmatch(r'[+-]?\d+,\d+',source):source=source.replace(',','.')
    try:value=integer_value(source)
    except (ValueError,SyntaxError,TypeError) as exc:invalid(widget,'debe ser entero, sin parte decimal.','Ingresá un entero o una expresión exacta como 2^8. Detalle: '+str(exc))
    if minimum is not None and value<minimum:invalid(widget,'valor fuera de rango.',f'Ingresá un entero mayor o igual que {minimum}.')
    if maximum is not None and value>maximum:invalid(widget,'valor fuera de rango.',f'Ingresá un entero menor o igual que {maximum}.')
    return value
