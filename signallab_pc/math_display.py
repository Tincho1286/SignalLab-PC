"""Offline mathematical typography; only a bounded AST is read, never executed."""
import ast
import html
import re
from io import BytesIO
from functools import lru_cache
from matplotlib.mathtext import math_to_image
from matplotlib import rc_context
from matplotlib.font_manager import FontProperties
from PySide6.QtGui import QImage

def numeric_presentation(source,digits=6):
    """Round only displayed decimal literals; stored/copied formulas stay intact."""
    from decimal import Decimal
    source=source.replace('^','**');tree=ast.parse(source,mode='eval');changes=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Constant) and isinstance(node.value,float):
            token=ast.get_source_segment(source,node);value=Decimal(token);shown=format(value,'.'+str(digits)+'g')
            # Preserve information near zero and unit-circle boundaries.
            if Decimal(shown) in (0,1,-1) and Decimal(shown)!=value:shown=token
            changes.append((node.col_offset,node.end_col_offset,shown))
    for first,last,shown in sorted(changes,reverse=True):source=source[:first]+shown+source[last:]
    return source

def latex(source):
    if len(source)>1000:raise ValueError('Formula extensa')
    source=source.strip().replace('^','**')
    tree=ast.parse(source,mode='eval')
    if sum(1 for _ in ast.walk(tree))>180:raise ValueError('Formula extensa')
    def wrapped(value):return r'\left('+value+r'\right)'
    def visit(n,parent=0):
        priority=100
        if isinstance(n,ast.Constant) and isinstance(n.value,(int,float,complex)):
            result=(ast.get_source_segment(source,n) or str(n.value)).replace('_','') if isinstance(n.value,float) else str(n.value)
            if isinstance(n.value,float) and 'e' in result.lower():
                priority=20;mantissa,exponent=result.lower().split('e');result=mantissa+r'\times 10^{'+str(int(exponent))+'}'
        elif isinstance(n,ast.Name) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*',n.id):
            greek={'pi','omega','tau','alpha','beta','gamma','delta','theta','sigma','lambda','phi','epsilon'}
            result=('\\'+n.id) if n.id in greek else r'\infty' if n.id in ('oo','infinity') else n.id if len(n.id)==1 else r'\mathit{'+n.id.replace('_',r'\_')+'}'
            numbered=re.fullmatch(r'([A-Za-z]+)_?([0-9]+)',n.id)
            if numbered:result=numbered[1]+'_{'+numbered[2]+'}'
        elif isinstance(n,ast.Subscript):
            result=visit(n.value)+r'\left['+visit(n.slice)+r'\right]'
        elif isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.USub,ast.UAdd)):
            priority=30;result=('-' if isinstance(n.op,ast.USub) else '+')+visit(n.operand,priority)
        elif isinstance(n,ast.BinOp):
            if isinstance(n.op,ast.Add) and isinstance(n.right,ast.UnaryOp) and isinstance(n.right.op,ast.USub):
                return visit(ast.BinOp(left=n.left,op=ast.Sub(),right=n.right.operand),parent)
            if isinstance(n.op,ast.Add) and isinstance(n.right,ast.BinOp) and isinstance(n.right.op,ast.Mult) and isinstance(n.right.left,ast.UnaryOp) and isinstance(n.right.left.op,ast.USub):
                positive=ast.BinOp(left=n.right.left.operand,op=ast.Mult(),right=n.right.right)
                return visit(ast.BinOp(left=n.left,op=ast.Sub(),right=positive),parent)
            if isinstance(n.op,ast.Div):result=r'\frac{'+visit(n.left)+'}{'+visit(n.right)+'}'
            elif isinstance(n.op,ast.Pow):
                priority=40;base=visit(n.left,41)
                if isinstance(n.left,ast.BinOp) and isinstance(n.left.op,ast.Div):base=wrapped(base)
                result='{'+base+'}^{'+visit(n.right)+'}'
            else:
                op={ast.Add:'+',ast.Sub:'-',ast.Mult:r'\cdot ',ast.Mod:r'\bmod '}.get(type(n.op))
                if op is None:raise ValueError('Operador no admitido')
                priority=10 if isinstance(n.op,(ast.Add,ast.Sub)) else 20
                result=visit(n.left,priority)+op+visit(n.right,priority+1 if isinstance(n.op,(ast.Sub,ast.Mod)) else priority)
        elif isinstance(n,ast.Compare):
            priority=5;ops={ast.Lt:'<',ast.LtE:r'\leq ',ast.Gt:'>',ast.GtE:r'\geq ',ast.Eq:'=',ast.NotEq:r'\neq '}
            result=visit(n.left,6)+''.join(ops[type(op)]+visit(v,6) for op,v in zip(n.ops,n.comparators))
        elif isinstance(n,ast.BoolOp):
            priority=2 if isinstance(n.op,ast.And) else 1
            result=(r'\ \mathrm{y}\ ' if isinstance(n.op,ast.And) else r'\ \mathrm{o}\ ').join(visit(v,priority) for v in n.values)
        elif isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ('Integral','Sum') and len(n.args)==2 and isinstance(n.args[1],ast.Tuple) and len(n.args[1].elts)==3:
            variable,lower,upper=map(visit,n.args[1].elts)
            result=(r'\int_{'+lower+'}^{'+upper+'}'+visit(n.args[0],20)+r'\,d'+variable if n.func.id=='Integral' else r'\sum_{'+variable+'='+lower+'}^{'+upper+'}'+visit(n.args[0],20))
        elif isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*',n.func.id) and not n.keywords:
            args=','.join(visit(arg) for arg in n.args);name=n.func.id
            if name.lower()=='kroneckerdelta' and len(n.args)==2:
                a,b=n.args
                if isinstance(a,ast.Constant) and a.value==0:a,b=b,a
                argument=a if isinstance(b,ast.Constant) and b.value==0 else ast.BinOp(left=a,op=ast.Sub(),right=b)
                result=r'\delta['+visit(argument)+']'
            elif name.lower() in ('diracdelta','dirac'):
                result=r'\delta'+(r'^{('+visit(n.args[1])+')}' if len(n.args)==2 else '')+wrapped(visit(n.args[0]))
            elif name.lower() in ('heaviside','step','impulse'):
                discrete=any(isinstance(v,ast.Name) and v.id.lower() in ('n','k') for v in ast.walk(n.args[0])) or (name.lower()=='impulse' and not any(isinstance(v,ast.Name) and v.id.lower() in ('t','x','w') for v in ast.walk(n.args[0])))
                edge=visit(n.args[1]) if len(n.args)==2 else '1' if name.lower() in ('step','impulse') else r'\frac{1}{2}'
                default='1' if discrete else r'\frac{1}{2}'
                symbol=r'\delta' if name.lower()=='impulse' else 'u'+('_{'+edge+'}' if edge!=default else '')
                result=symbol+(r'\left['+visit(n.args[0])+r'\right]' if discrete else wrapped(visit(n.args[0])))
            elif name=='binomial' and len(n.args)==2:result=r'\binom{'+visit(n.args[0])+'}{'+visit(n.args[1])+'}'
            elif name=='factorial' and len(n.args)==1:result=visit(n.args[0],100)+'!'
            elif name=='sqrt':result=r'\sqrt{'+args+'}'
            elif name.lower()=='abs':result=r'\left|'+args+r'\right|'
            elif name=='exp':result='e^{'+args+'}'
            elif re.fullmatch(r'g[0-9]+',name):result=visit(n.func)+wrapped(args)
            else:result=r'\mathrm{'+name.replace('_',r'\_')+'}'+wrapped(args)
        else:raise ValueError('Notación no disponible')
        return wrapped(result) if priority<parent else result
    return visit(tree.body)

@lru_cache(maxsize=256)
def formula_png(source,leading_dot=False):
    if len(source)>1000:raise ValueError('Formula extensa')
    stream=BytesIO()
    with rc_context({'mathtext.fontset':'stix','savefig.transparent':True,'savefig.facecolor':'none','figure.facecolor':'none'}):
        math_to_image('$'+(r'\cdot ' if leading_dot else '')+latex(source)+'$',stream,format='png',dpi=140,color='#e1e7ee',prop=FontProperties(family='STIXGeneral',size=15))
    return stream.getvalue()

def formula_image(source,leading_dot=False):return QImage.fromData(formula_png(source,leading_dot))

def formula_vector(source,leading_dot=False):
    from .vector_math import render_latex
    return render_latex((r'\cdot ' if leading_dot else '')+latex(source))
