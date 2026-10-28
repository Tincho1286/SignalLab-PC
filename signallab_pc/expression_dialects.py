"""Translate mathematical notation between numeric and CAS editors using AST only."""
import ast


def translate(source, *, symbolic):
    tree=ast.parse(source.replace('^','**'),mode='eval')
    if sum(1 for _ in ast.walk(tree))>1000:
        raise ValueError('La expresión es demasiado extensa para copiar su definición.')
    class Converter(ast.NodeTransformer):
        def visit_Name(self,node):
            if not symbolic:node.id={'I':'i','E':'e'}.get(node.id,node.id)
            return node
        def visit_BinOp(self,node):
            node=self.generic_visit(node)
            if isinstance(node.op,(ast.BitAnd,ast.BitOr)):
                return ast.BoolOp(op=ast.And() if isinstance(node.op,ast.BitAnd) else ast.Or(),values=[node.left,node.right])
            return node
        def visit_IfExp(self,node):
            node=self.generic_visit(node)
            if symbolic:return piecewise(node.test,node.body,node.orelse)
            return ast.Call(func=ast.Name(id='where',ctx=ast.Load()),args=[node.test,node.body,node.orelse],keywords=[])
        def visit_Call(self,node):
            node=self.generic_visit(node)
            if not isinstance(node.func,ast.Name):return node
            name=node.func.id.lower()
            if symbolic and name=='where' and len(node.args)==3:
                return piecewise(*node.args)
            if not symbolic and name=='piecewise':
                result=ast.Name(id='nan',ctx=ast.Load())
                for pair in reversed(node.args):
                    if not isinstance(pair,ast.Tuple) or len(pair.elts)!=2:raise ValueError('Cada tramo necesita valor y condición.')
                    value,condition=pair.elts
                    if isinstance(condition,ast.Constant) and condition.value is True:result=value
                    else:result=ast.Call(func=ast.Name(id='where',ctx=ast.Load()),args=[condition,value,result],keywords=[])
                return result
            if not symbolic and name=='kroneckerdelta' and len(node.args)==2:
                return ast.Call(func=ast.Name(id='impulse',ctx=ast.Load()),args=[ast.BinOp(left=node.args[0],op=ast.Sub(),right=node.args[1])],keywords=[])
            if name in ('and','or'):
                return ast.BoolOp(op=ast.And() if name=='and' else ast.Or(),values=node.args)
            if name in ('eq','ne') and len(node.args)==2:
                return ast.Compare(left=node.args[0],ops=[ast.Eq() if name=='eq' else ast.NotEq()],comparators=[node.args[1]])
            if not symbolic:node.func.id={'Abs':'abs','Heaviside':'heaviside','conjugate':'conj','DiracDelta':'dirac'}.get(node.func.id,node.func.id)
            return node
    def piecewise(condition,value,otherwise):
        return ast.Call(func=ast.Name(id='Piecewise',ctx=ast.Load()),args=[ast.Tuple(elts=[value,condition],ctx=ast.Load()),ast.Tuple(elts=[otherwise,ast.Constant(value=True)],ctx=ast.Load())],keywords=[])
    return ast.unparse(Converter().visit(tree))


def to_numeric(source):return translate(source,symbolic=False)
def to_symbolic(source):return translate(source,symbolic=True)
