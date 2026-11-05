"""Lectura estructural de tramos: no evalúa expresiones ni ejecuta llamadas."""
import ast


def parse_cases(source):
    if len(source)>12000:raise ValueError('La expresión es demasiado extensa para el editor visual.')
    tree=ast.parse(source.replace('^','**'),mode='eval').body
    if sum(1 for _ in ast.walk(tree))>1000:raise ValueError('Demasiados elementos para el editor visual.')
    rows=[]
    while True:
        if isinstance(tree,ast.Call) and isinstance(tree.func,ast.Name) and tree.func.id.lower()=='piecewise' and not tree.keywords:
            otherwise=None
            for pair in tree.args:
                if not isinstance(pair,ast.Tuple) or len(pair.elts)!=2:raise ValueError('Cada tramo necesita un valor y una condición.')
                value,condition=pair.elts
                if isinstance(condition,ast.Constant) and condition.value is True:
                    otherwise=value
                    break
                rows.append((ast.unparse(value),ast.unparse(condition)))
            if otherwise is None:
                if not rows:raise ValueError('La función no contiene tramos.')
                return rows,None
            tree=otherwise
        elif isinstance(tree,ast.Call) and isinstance(tree.func,ast.Name) and tree.func.id.lower()=='where' and len(tree.args)==3 and not tree.keywords:
            condition,value,tree=tree.args
            rows.append((ast.unparse(value),ast.unparse(condition)))
        elif isinstance(tree,ast.IfExp):
            condition,value,tree=tree.test,tree.body,tree.orelse
            rows.append((ast.unparse(value),ast.unparse(condition)))
        else:
            break
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

def periodic_display(source):
    """Abbreviate repeated folded frequency coordinates only in presentation."""
    tree=ast.parse(source.replace('^','**'),mode='eval')
    nodes=list(ast.walk(tree))
    if len(nodes)>1000:return source,[]
    occupied={node.id for node in nodes if isinstance(node,ast.Name)}
    repeated={}
    for node in nodes:
        if not isinstance(node,ast.BinOp) or not isinstance(node.op,(ast.Add,ast.Sub)):continue
        for term,offset in ((node.left,node.right),(node.right,node.left)):
            if not (isinstance(term,ast.Call) and isinstance(term.func,ast.Name) and term.func.id.lower()=='mod' and len(term.args)==2):continue
            offset_names={name.id for name in ast.walk(offset) if isinstance(name,ast.Name)}
            if offset_names-{'pi','e','E'}:continue
            if not any(isinstance(name,ast.Name) and name.id=='w' for name in ast.walk(term)):continue
            key=ast.dump(node)
            found,count=repeated.get(key,(node,0))
            repeated[key]=(found,count+1)
    choices=[(key,node) for key,(node,count) in repeated.items() if count>1]
    if not choices or len(choices)>4:return source,[]
    replacements={};definitions=[]
    for index,(key,node) in enumerate(choices,1):
        name='w_p' if index==1 else 'w_p'+str(index)
        while name in occupied:name+='p'
        occupied.add(name)
        replacements[key]=name
        definitions.append((name,ast.unparse(node)))
    class Abbreviate(ast.NodeTransformer):
        def visit_BinOp(self,node):
            name=replacements.get(ast.dump(node))
            if name is not None:return ast.copy_location(ast.Name(id=name,ctx=ast.Load()),node)
            return self.generic_visit(node)
    shown=Abbreviate().visit(tree)
    return ast.unparse(shown),definitions

def covers_display_period(source,definitions):
    """Certify only the coverage of the displayed cases over a folded period."""
    if len(definitions)!=1:return False
    from .signal_notation import read
    import sympy as sp
    name,formula=definitions[0]
    try:
        coordinate=sp.Symbol(name,real=True)
        folded=read(formula)
        modules=folded.atoms(sp.Mod)
        if len(modules)!=1:return False
        modulo=next(iter(modules))
        divisor=modulo.args[1]
        slope=folded.coeff(modulo)
        offset=sp.simplify(folded-slope*modulo)
        if slope not in (1,-1) or offset.free_symbols or offset.is_real is not True or divisor.is_positive is not True or divisor.free_symbols:return False
        domain=sp.Interval(offset,offset+divisor,right_open=True) if slope==1 else sp.Interval(offset-divisor,offset,left_open=True)
        value=read(source)
        value=value.xreplace({symbol:coordinate for symbol in value.free_symbols if symbol.name==name})
        if sp.count_ops(value)>150:return False
        value=sp.piecewise_fold(value)
        if not isinstance(value,sp.Piecewise):return not value.has(sp.nan)
        parts=value.as_expr_set_pairs(domain=domain)
        covered=sp.Union(*(region for expression,region in parts if not expression.has(sp.nan)))
        return covered==domain
    except (ValueError,TypeError,SyntaxError,NotImplementedError):
        return False
