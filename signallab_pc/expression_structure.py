"""Lectura estructural de tramos: no evalúa expresiones ni ejecuta llamadas."""
import ast


def parse_cases(source):
    if len(source)>12000:raise ValueError('La expresión es demasiado extensa para el editor visual.')
    tree=ast.parse(source.replace('^','**'),mode='eval').body
    if sum(1 for _ in ast.walk(tree))>1000:raise ValueError('Demasiados elementos para el editor visual.')
    rows=[]
    if isinstance(tree,ast.Call) and isinstance(tree.func,ast.Name) and tree.func.id.lower()=='piecewise' and not tree.keywords:
        for pair in tree.args:
            if not isinstance(pair,ast.Tuple) or len(pair.elts)!=2:raise ValueError('Cada tramo necesita un valor y una condición.')
            value,condition=pair.elts
            if isinstance(condition,ast.Constant) and condition.value is True:
                return rows,ast.unparse(value)
            rows.append((ast.unparse(value),ast.unparse(condition)))
        if not rows:raise ValueError('La función no contiene tramos.')
        return rows,None
    while True:
        if isinstance(tree,ast.Call) and isinstance(tree.func,ast.Name) and tree.func.id=='where' and len(tree.args)==3 and not tree.keywords:
            condition,value,tree=tree.args
        elif isinstance(tree,ast.IfExp):condition,value,tree=tree.test,tree.body,tree.orelse
        else:break
        rows.append((ast.unparse(value),ast.unparse(condition)))
    if not rows:return None
    otherwise=None if isinstance(tree,ast.Name) and tree.id.lower()=='nan' else ast.unparse(tree)
    return rows,otherwise


def serialize_cases(rows,otherwise,symbolic=False):
    if not rows:return otherwise if otherwise is not None else 'nan'
    if symbolic:
        branches=['('+value+', '+condition+')' for value,condition in rows]
        if otherwise is not None:branches.append('('+otherwise+', True)')
        return 'Piecewise('+','.join(branches)+')'
    value=otherwise if otherwise is not None else 'nan'
    for expression,condition in reversed(rows):value=f'where({condition}, {expression}, {value})'
    return value
