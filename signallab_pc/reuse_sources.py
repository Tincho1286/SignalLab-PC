"""Describe reusable inputs using headers and expressions, without copying arrays."""
from .result_expressions import ExpressionResult


def temporal_expression(project, key):
    expression = project.expression(key)
    if expression is not None and expression.variable in ('t', 'n', None):
        return expression
    info = project.describe(key)
    if info.get('input_expression'):
        # Reuse the signal definition, never its scalar energy/power value.
        return ExpressionResult(info['input_expression'], info['input_variable'],
                                tuple(dict.fromkeys(('Se reutiliza la definición de entrada de este cálculo.', *info.get('input_conditions', ())))))
    return None


def source_info(project, key, kind):
    record = project.describe(key)
    if kind == 'cas_source':
        from .cas_transfer import can_send
        return {**record,'label':'Resultado para CAS'} if can_send(project.get(key)) else None
    if kind == 'system_source':
        if record['kind'] == 'system':
            return {**record, 'label': 'Sistema', 'definition': 'system'}
        expression = project.expression(key)
        if expression is not None and expression.variable in ('s', 'z'):
            return {'domain': 'analog' if expression.variable == 's' else 'digital', 'advance': None,
                    'variable': expression.variable, 'label': 'Expresión como H('+expression.variable+')', 'definition': 'expression'}
        if expression is not None and expression.variable=='w' and expression.units in ('rad/s','rad/muestra'):
            return {'domain':'analog' if expression.units=='rad/s' else 'digital','advance':None,'variable':'w','label':'Respuesta en frecuencia H(w)','definition':'expression'}
        return None
    if kind == 'temporal_expression':
        expression = temporal_expression(project, key)
        return {'variable': expression.variable, 'units': expression.units, 'label': 'Definición de señal'} if expression else None
    if record['kind'] != kind and not (kind == 'expression' and project.expression(key) is not None):
        return None
    info = record
    if kind == 'expression':
        expression = project.expression(key)
        info.update(variable=expression.variable, units=expression.units, label='Expresión')
    return info


def compatible(info, *, domains=None, variables=None, units=None, allow_advance=True, dft_input=False):
    if info is None:
        return False
    if domains is not None and info.get('domain') not in domains:
        return False
    if dft_input and info.get('domain') != 'discrete' and not info.get('centered_dft'):
        return False
    if variables is not None and info.get('variable') not in variables:
        return False
    if units is not None and info.get('units') and info['units'] not in units:
        return False
    return allow_advance or not info.get('advance')
