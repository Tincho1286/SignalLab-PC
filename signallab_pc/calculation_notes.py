"""Passive records of existing finite-limit extensions; no numerical policy changes."""
from contextlib import contextmanager
from contextvars import ContextVar
import ast,html

_active=ContextVar('signallab_calculation_notes',default=None)
_source=ContextVar('signallab_expression_source',default=None)
TITLE='Levantamiento de indeterminaciones'
CRITERION='Se completó la expresión por continuidad: los límites por izquierda y por derecha coinciden y son finitos.'
SCOPE='En una secuencia discreta es una convención de carga de la fórmula. Un valor definido explícitamente por tramos se conserva. Los polos, las divergencias y los límites laterales distintos no se levantan con este criterio.'

@contextmanager
def capture():
    parent=_active.get();records={};token=_active.set(records)
    try:yield records
    finally:
        _active.reset(token)
        if parent is not None:parent.update(records)

@contextmanager
def expression_source(source):
    token=_source.set(source)
    try:yield
    finally:_source.reset(token)

def merge(records):
    target=_active.get()
    if target is None:return
    for record in records:
        key=(record['expression'],record['variable'],record['point'],record['value'])
        target[key]=dict(record)

def record_extension(expression,variable,point,value):
    if _active.get() is None:return
    import sympy as sp
    source=_source.get();display_expression=expression;display_variable=variable
    if source:
        try:
            names={node.id for node in ast.walk(ast.parse(source,mode='eval')) if isinstance(node,ast.Name)}
            axes=names.intersection({'n','k','t','x','w','omega'})
            if len(axes)==1:
                display_variable=sp.Symbol(next(iter(axes)),real=True)
                display_expression=expression.xreplace({variable:display_variable})
        except SyntaxError:pass
    try:latex=r'\lim_{'+sp.latex(display_variable)+r'\to '+sp.latex(point)+'} '+sp.latex(display_expression)+' = '+sp.latex(value)
    except Exception:latex=None
    record={'expression':str(display_expression),'variable':str(display_variable),'point':str(point),'value':str(value),'method':'finite_equal_two_sided_real_limits',
            'latex':latex}
    merge([record])

def plain_text(records):
    if not records:return ''
    lines=[TITLE,CRITERION]
    for record in records:lines.append(record['expression']+'; '+record['variable']+' = '+record['point']+' → valor usado: '+record['value'])
    return '\n\n'.join([*lines,SCOPE])

def callout_html(records,render=None):
    if not records:return ''
    parts=['<div style="background-color:#172e35;border-left:3px solid #79c4ad;padding:12px;margin-bottom:16px"><h2>'+TITLE+'</h2><p>'+CRITERION+'</p>']
    for record in records:
        formula=None
        if render:
            try:formula=render(record['latex'])
            except (ValueError,TypeError,RuntimeError):pass
        text=record['expression']+'; '+record['variable']+' = '+record['point']+' → '+record['value']
        parts.append('<p>'+(formula or html.escape(text))+'</p>')
    parts.extend(['<p>'+SCOPE+'</p></div>'])
    return ''.join(parts)
