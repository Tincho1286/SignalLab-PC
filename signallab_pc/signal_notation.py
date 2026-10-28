"""Bounded signal identities for readable results, with no global simplify()."""
import ast,re
from functools import lru_cache
import sympy as sp
from sympy.printing.str import StrPrinter
from sympy.printing.latex import LatexPrinter
from sympy.printing.precedence import PRECEDENCE


def _small_algebra(value):
    if value.has(sp.CRootOf,sp.Integral,sp.Sum,sp.Derivative) or sp.count_ops(value)>80:return value
    value=sp.powsimp(sp.expand_power_exp(value),force=False)
    return sp.factor_terms(value)


def _gate_bound(condition,variable):
    if not getattr(condition,'is_Relational',False):return None
    left,right=condition.lhs,condition.rhs
    if right==variable:condition=condition.reversed;left,right=condition.lhs,condition.rhs
    if left!=variable or right.is_integer is not True:return None
    if isinstance(condition,sp.GreaterThan):return 1,right
    if isinstance(condition,sp.StrictGreaterThan):return 1,right+1
    if isinstance(condition,sp.LessThan):return -1,right
    if isinstance(condition,sp.StrictLessThan):return -1,right-1
    return None


def _step_info(gate,variable):
    if gate.func!=sp.Heaviside or gate.args[1]!=1:return None
    argument=sp.expand(gate.args[0]);slope=argument.coeff(variable);offset=argument-slope*variable
    if offset.has(variable) or offset.is_integer is not True:return None
    if slope==1:return 1,-offset
    if slope==-1:return -1,offset
    return None


def normalize(expression):
    """Keep hypotheses, integer support and step endpoint values intact."""
    if not isinstance(expression,sp.Expr) or expression.has(sp.CRootOf) or sum(1 for _ in sp.preorder_traversal(expression))>500:return expression
    integers=[symbol for symbol in expression.free_symbols if symbol.is_integer is True]
    def visit(value):
        if not isinstance(value,sp.Basic) or not value.args:return value
        if value.func==sp.Piecewise:
            pairs=[(visit(v),c) for v,c in value.args]
            if len(pairs)==2 and pairs[1]==(0,sp.true):
                amplitude,condition=pairs[0]
                for variable in integers:
                    bound=_gate_bound(condition,variable)
                    if bound:
                        # A gate must not turn a well-defined case into 0/0 at
                        # an excluded index (for example 1/n for n >= 1).
                        if any(power.base.has(variable) and power.exp.is_negative for power in amplitude.atoms(sp.Pow)):continue
                        direction,edge=bound;argument=variable-edge if direction==1 else edge-variable
                        return amplitude*sp.Heaviside(argument,1)
            return sp.Piecewise(*pairs,evaluate=False)
        if value.func==sp.Mul:
            value=sp.Mul(*(visit(arg) for arg in value.args))
            # f(n) delta[n-k] = f(k) delta[n-k], only when f(k) is finite.
            for impulse in value.atoms(sp.KroneckerDelta):
                a,b=impulse.args[:2]
                for variable in integers:
                    point=b if a==variable else a if b==variable else None
                    if point is None or point.has(variable) or point.is_integer is not True:continue
                    coefficient=value/impulse;sample=coefficient.subs(variable,point)
                    if sample.is_finite is True:value=sample*impulse
            return _small_algebra(value)
        if value.func==sp.Add:
            value=sp.Add(*(visit(arg) for arg in value.args))
            for variable in integers:
                terms=list(sp.Add.make_args(value));gated=[];rest=[]
                for term in terms:
                    gates=[gate for gate in term.atoms(sp.Heaviside) if _step_info(gate,variable)]
                    if len(gates)==1 and not (term/gates[0]).has(sp.Heaviside):gated.append((term/gates[0],gates[0]))
                    else:rest.append(term)
                for coefficient,gate in gated:
                    coefficient=_small_algebra(coefficient);direction,edge=_step_info(gate,variable)
                    # A cancelling impulse can remove the boundary sample:
                    # delta[n] - a**n u[-n] = -a**n u[-n-1].
                    for _ in range(32):
                        sample=_small_algebra(coefficient.subs(variable,edge))
                        if sample.is_finite is not True or sample==0:break
                        impulse=sp.KroneckerDelta(variable,edge);found=None
                        for index,term in enumerate(rest):
                            if term.has(impulse) and not (term/impulse).has(variable) and _small_algebra(term/impulse+sample)==0:found=index;break
                        if found is None:break
                        rest.pop(found);edge+=direction
                        gate=sp.Heaviside(variable-edge if direction==1 else edge-variable,1)
                    for _ in range(32):
                        boundary=edge-direction;sample=_small_algebra(coefficient.subs(variable,boundary))
                        if sample.is_finite is not True:break
                        impulse=sp.KroneckerDelta(variable,boundary);found=None
                        for index,term in enumerate(rest):
                            if term.has(impulse) and not (term/impulse).has(variable):
                                if _small_algebra(term/impulse-sample)==0:found=index;break
                        if found is None:
                            if sample!=0:break
                        else:rest.pop(found)
                        edge=boundary;gate=sp.Heaviside(variable-edge if direction==1 else edge-variable,1)
                    rest.append(coefficient*gate)
                value=sp.Add(*rest)
            # Collect terms with the same support without expanding the gates.
            gates=list(value.atoms(sp.Heaviside))
            if gates and len(gates)<=16:
                value=sp.collect(value,gates,exact=True)
                value=sp.Add(*[_small_algebra(term) for term in sp.Add.make_args(value)])
            return value
        if value.func==sp.Pow:return _small_algebra(sp.Pow(visit(value.base),visit(value.exp)))
        if value.func==sp.Heaviside:return sp.Heaviside(visit(value.args[0]),value.args[1])
        return value.xreplace({arg:visit(arg) for arg in value.args if isinstance(arg,sp.Expr)})
    value=visit(expression)
    # A second local pass can join gates exposed by collecting adjacent terms.
    return visit(value) if value!=expression else value


class SignalPrinter(StrPrinter):
    def _print_Or(self,value):return '('+' or '.join('('+self._print(term)+')' for term in value.args)+')'
    def _print_And(self,value):return '('+' and '.join('('+self._print(term)+')' for term in value.args)+')'
    def _print_Mul(self,value):
        if any(arg.is_Pow and arg.base.is_Rational and arg.base>1 and arg.exp.free_symbols and arg.exp.could_extract_minus_sign() for arg in value.args):
            return '*'.join(self.parenthesize(arg,PRECEDENCE['Mul']) for arg in value.args)
        return super()._print_Mul(value)
    def _print_Heaviside(self,value):
        argument,edge=value.args
        if argument.is_integer is True and edge==1:return 'step('+self._print(argument)+')'
        return 'Heaviside('+self._print(argument)+((', '+self._print(edge)) if edge!=sp.Rational(1,2) else '')+')'
    def _print_Pow(self,value):
        if value.base.is_Rational and value.base>1 and value.exp.could_extract_minus_sign():
            return '('+self._print(1/value.base)+')**('+self._print(-value.exp)+')'
        return super()._print_Pow(value)


def source(expression):return SignalPrinter({'order':'none'}).doprint(normalize(expression))


class SignalLatexPrinter(LatexPrinter):
    def _print_Heaviside(self,value,exp=None):
        argument,edge=value.args;discrete=argument.is_integer is True
        default=sp.S.One if discrete else sp.S.Half
        name='u'+('_{'+self._print(edge)+'}' if edge!=default else '')
        text=name+(r'\left[' if discrete else r'\left(')+self._print(argument)+(r'\right]' if discrete else r'\right)')
        return text if exp is None else r'\left('+text+r'\right)^{'+exp+'}'
    def _print_KroneckerDelta(self,value,exp=None):
        a,b=value.args[:2]
        if a.is_number and not b.is_number:a,b=b,a
        text=r'\delta\left['+self._print(a-b)+r'\right]'
        return text if exp is None else text+'^{'+exp+'}'


def latex(expression):return SignalLatexPrinter().doprint(normalize(expression))


def read(source_text,integer_names=()):
    """Mathematical AST only; unknown functions stay unevaluated."""
    text=source_text.replace('^','**');tree=ast.parse(text,mode='eval')
    if len(text)>5000 or sum(1 for _ in ast.walk(tree))>500:raise ValueError('Expresión extensa')
    names={name:sp.Symbol(name,integer=True) for name in integer_names}
    constants={'pi':sp.pi,'e':sp.E,'E':sp.E,'i':sp.I,'I':sp.I,'j':sp.I,'oo':sp.oo,'True':sp.true,'False':sp.false}
    constructors={'Piecewise':lambda *pairs:sp.Piecewise(*pairs,evaluate=False),'KroneckerDelta':sp.KroneckerDelta,'DiracDelta':sp.DiracDelta,'Heaviside':sp.Heaviside,'step':lambda arg:sp.Heaviside(arg,1),'impulse':lambda arg:sp.KroneckerDelta(arg,0),'binomial':lambda *args:sp.binomial(*args,evaluate=False),'factorial':lambda arg:sp.factorial(arg,evaluate=False),'sqrt':sp.sqrt,'exp':sp.exp,'sin':sp.sin,'cos':sp.cos,'tan':sp.tan,'Abs':sp.Abs,'abs':sp.Abs,'conjugate':sp.conjugate,'conj':sp.conjugate,'re':sp.re,'im':sp.im,'log':sp.log,'And':sp.And,'Or':sp.Or,'Eq':lambda a,b:sp.Eq(a,b,evaluate=False),'Ne':lambda a,b:sp.Ne(a,b,evaluate=False),'Integral':sp.Integral,'Sum':sp.Sum,'Derivative':sp.Derivative}
    def visit(node):
        if isinstance(node,ast.Name):return constants.get(node.id,names.setdefault(node.id,sp.Symbol(node.id)))
        if isinstance(node,ast.Constant):
            if isinstance(node.value,bool):return sp.true if node.value else sp.false
            if isinstance(node.value,(int,float)):return sp.Rational(ast.get_source_segment(text,node))
        if isinstance(node,(ast.Tuple,ast.List)):return tuple(visit(item) for item in node.elts)
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.USub,ast.UAdd)):return -visit(node.operand) if isinstance(node.op,ast.USub) else visit(node.operand)
        if isinstance(node,ast.BinOp):
            a,b=visit(node.left),visit(node.right)
            if isinstance(node.op,ast.Add):return a+b
            if isinstance(node.op,ast.Sub):return a-b
            if isinstance(node.op,ast.Mult):return a*b
            if isinstance(node.op,ast.Div):return a/b
            if isinstance(node.op,ast.Pow):
                if a.is_Integer and b.is_Integer and abs(b)>4096:raise ValueError('Potencia numérica extensa para presentación')
                return a**b
        if isinstance(node,ast.Subscript) and isinstance(node.value,ast.Name):return sp.IndexedBase(node.value.id)[visit(node.slice)]
        if isinstance(node,ast.Compare):
            operands=[node.left,*node.comparators];functions={ast.Gt:sp.Gt,ast.GtE:sp.Ge,ast.Lt:sp.Lt,ast.LtE:sp.Le,ast.Eq:sp.Eq,ast.NotEq:sp.Ne}
            return sp.And(*[functions[type(op)](visit(operands[k]),visit(operands[k+1]),evaluate=False) for k,op in enumerate(node.ops)])
        if isinstance(node,ast.BoolOp):return (sp.And if isinstance(node.op,ast.And) else sp.Or)(*[visit(arg) for arg in node.values])
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and not node.keywords:
            if not re.fullmatch('[A-Za-z][A-Za-z0-9_]*',node.func.id):raise ValueError('Nombre no matemático')
            arguments=[visit(arg) for arg in node.args];fn=constructors.get(node.func.id)
            if node.func.id in ('CRootOf','RootOf','RootSum'):raise ValueError('Conservar la raíz algebraica sin reconstruirla')
            return fn(*arguments) if fn else sp.Function(node.func.id)(*arguments)
        raise ValueError('Sintaxis no matemática')
    return visit(tree.body)


@lru_cache(maxsize=256)
def normalize_source(text,discrete=False):
    if not any(token in text for token in ('Piecewise','KroneckerDelta','Heaviside','step(','impulse(')):return text
    try:
        integers=('n','k') if discrete or 'KroneckerDelta' in text else ()
        return source(read(text,integers))
    except (ValueError,TypeError,SyntaxError,NotImplementedError,RecursionError,ZeroDivisionError):return text
