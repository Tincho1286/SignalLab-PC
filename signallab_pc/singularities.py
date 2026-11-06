"""Finite values by continuous extension, never by numerical neighbourhood guesses."""
import ast
import numpy as np
import sympy as sp
from .jobs import checkpoint


def finite_extension(expression, variable, point):
    """Require an exact finite two-sided real limit at the requested coordinate."""
    coordinate=point if isinstance(point,sp.Basic) else sp.Rational(str(point))
    real=sp.Dummy('coordinate',real=True)
    value=expression.xreplace({variable:real})
    left=sp.limit(value,real,coordinate,dir='-')
    right=sp.limit(value,real,coordinate,dir='+')
    if left.is_finite is not True or right.is_finite is not True or sp.simplify(left-right)!=0:
        raise ValueError('La expresión tiene un polo, una divergencia o límites laterales distintos en '+str(point)+'.')
    from .calculation_notes import record_extension
    record_extension(expression,variable,coordinate,left)
    return left


def repair_values(expression,variable,coordinates,values):
    coordinates=np.asarray(coordinates)
    result=np.broadcast_to(np.asarray(values,dtype=complex),coordinates.shape).copy()
    invalid=~np.isfinite(result)
    for point in np.unique(coordinates[invalid]):
        checkpoint()
        # Match an exact singular coordinate only when its conversion equals
        # this machine coordinate, never by an arbitrary neighbourhood tolerance.
        real=sp.Dummy('coordinate',real=True);candidates=[]
        try:
            poles=sp.singularities(expression.xreplace({variable:real}),real,domain=sp.S.Reals)
            if isinstance(poles,sp.FiniteSet):candidates.extend(poles)
        except (ValueError,TypeError,NotImplementedError):pass
        for equation in expression.atoms(sp.Equality):
            if equation.lhs==variable and not equation.rhs.free_symbols:candidates.append(equation.rhs)
            elif equation.rhs==variable and not equation.lhs.free_symbols:candidates.append(equation.lhs)
        matched=[]
        for candidate in candidates:
            try:
                if candidate.is_real is True and float(candidate.evalf(17))==float(point):matched.append(candidate)
            except (ValueError,TypeError,OverflowError):pass
        matched=list(set(matched))
        if len(matched)>1:raise ValueError('La precisión del eje no distingue varias singularidades exactas en '+str(point)+'.')
        exact_point=matched[0] if matched else point
        exact=expression.subs(variable,exact_point)
        if exact.is_finite is not True:
            if expression.has(sp.KroneckerDelta,sp.Heaviside):raise ValueError('La muestra no está definida. Completá el factor que multiplica al impulso o escalón; no se levanta un polo tomando límites del producto a través de su salto.')
            exact=finite_extension(expression,variable,exact_point)
        if exact.free_symbols:raise ValueError('El límite conserva parámetros sin valor: '+str(exact))
        value=complex(exact.evalf(17))
        if not np.isfinite(value):raise ValueError('El límite es finito, pero excede el rango numérico disponible.')
        result[invalid&(coordinates==point)]=value
    return result


def numeric_expression(source):
    """Translate only the already restricted numeric grammar to the shared parser."""
    from .symbolic import parse,T
    class Translate(ast.NodeTransformer):
        def visit_Name(self,node):
            return ast.copy_location(ast.Name(id='t',ctx=ast.Load()),node) if node.id.lower() in ('x','t','n','k','w') else node
        def visit_IfExp(self,node):
            return self.piece(self.visit(node.test),self.visit(node.body),self.visit(node.orelse))
        def piece(self,condition,left,right):
            return ast.Call(func=ast.Name(id='Piecewise',ctx=ast.Load()),args=[ast.Tuple(elts=[left,condition],ctx=ast.Load()),ast.Tuple(elts=[right,ast.Constant(True)],ctx=ast.Load())],keywords=[])
        def visit_Call(self,node):
            node=self.generic_visit(node)
            if isinstance(node.func,ast.Name) and node.func.id.lower() in ('dirac','diracdelta','impulse'):
                if len(node.args)==1 or len(node.args)==2 and isinstance(node.args[1],ast.Constant) and node.args[1].value==0:
                    return ast.Call(func=ast.Name(id='KroneckerDelta',ctx=ast.Load()),args=[node.args[0],ast.Constant(value=0)],keywords=[])
            if isinstance(node.func,ast.Name) and node.func.id.lower()=='where' and len(node.args)==3:
                return self.piece(node.args[0],node.args[1],node.args[2])
            return node
    from .math_source import normalize
    tree=Translate().visit(ast.parse(normalize(source),mode='eval'))
    return parse(ast.unparse(ast.fix_missing_locations(tree))),T


def _numeric_kronecker(left,right,delta_range=None):
    """Exact equality on arrays; SymPy's scalar ternary cannot sample a grid."""
    values=np.equal(left,right)
    if delta_range is not None:
        lower,upper=delta_range
        values=values & np.greater_equal(left,lower) & np.less_equal(left,upper)
    return np.asarray(values,dtype=float)


def sample_symbolic(expression,variable,coordinates):
    # The built-in printer emits a scalar ternary even with a module override.
    numeric=expression.xreplace({delta:sp.Function('_sample_delta')(*delta.args) for delta in expression.atoms(sp.KroneckerDelta)})
    from .hyperbolic import NUMERIC
    function=sp.lambdify(variable,numeric,modules=[NUMERIC,{'sqrt':np.emath.sqrt,'log':np.emath.log,'_sample_delta':_numeric_kronecker},'scipy','numpy'])
    with np.errstate(all='ignore'):
        try:values=function(np.asarray(coordinates,dtype=float))
        except ZeroDivisionError:values=np.full(np.asarray(coordinates).shape,complex(np.nan,np.nan))
    values=reject_finite_poles(expression,variable,coordinates,values)
    return repair_values(expression,variable,coordinates,values)


def resolve_finite_support(expression,variable,lower,upper):
    """Extend only undefined values at actual finite summation indices."""
    if not (lower.is_finite and upper.is_finite):return expression
    replacements=[]
    for index in range(int(lower),int(upper)+1):
        if index%64==0:checkpoint()
        evaluated=expression.subs(variable,index)
        if evaluated.has(sp.nan,sp.zoo,sp.oo,-sp.oo):
            replacements.append((finite_extension(expression,variable,index),sp.Eq(variable,index)))
    return sp.Piecewise(*replacements,(expression,True)) if replacements else expression


def extend_removable(expression):
    """Exact isolated continuous extensions before integer simplification."""
    if not isinstance(expression,sp.Expr):return expression
    axes=[v for v in expression.free_symbols if str(v) in ('n','t','w')]
    if len(axes)!=1:return expression
    variable=axes[0];real=sp.Dummy('coordinate',real=True)
    try:points=sp.singularities(expression.xreplace({variable:real}),real,domain=sp.S.Reals)
    except (ValueError,TypeError,NotImplementedError):return expression
    if not isinstance(points,sp.FiniteSet):return expression
    replacements=[]
    for point in points:
        checkpoint()
        if point.is_finite is not True:continue
        assigned=expression.subs(variable,point)
        if assigned.is_finite is True:continue
        try:
            value=finite_extension(expression,variable,point)
        except (ValueError,TypeError,NotImplementedError):continue
        replacements.append((value,sp.Eq(variable,point)))
    return sp.Piecewise(*replacements,(expression,True),evaluate=False) if replacements else expression


def reject_finite_poles(expression,variable,coordinates,values):
    """Verify suspected floating-point zeros exactly before invalidating a value.

    The tolerance selects work only; proximity alone never declares a pole.
    The complete expression is checked so inactive branches and cancellations
    remain valid. This catches sin(pi*n) rounding to a tiny nonzero number.
    """
    denominators=[node.base for node in expression.atoms(sp.Pow) if node.exp.is_negative is True and node.base.has(variable)]
    for node in expression.atoms(sp.tan,sp.tanh,sp.sech,sp.csch,sp.coth):
        if node.has(variable):denominators.append((sp.cos if node.func==sp.tan else sp.cosh if node.func in (sp.tanh,sp.sech) else sp.sinh)(node.args[0]))
    if not denominators:return values
    from .hyperbolic import NUMERIC
    coordinates=np.asarray(coordinates,dtype=float);result=np.broadcast_to(np.asarray(values,dtype=complex),coordinates.shape).copy()
    candidates=np.zeros(coordinates.shape,dtype=bool)
    for denominator in set(denominators):
        try:
            evaluator=sp.lambdify(variable,denominator,modules=[NUMERIC,{'sqrt':np.emath.sqrt,'log':np.emath.log},'scipy','numpy'])
            with np.errstate(all='ignore'):probe=np.broadcast_to(np.asarray(evaluator(coordinates),dtype=complex),coordinates.shape)
            candidates|=np.abs(probe)<1e-7
        except (NameError,TypeError,ValueError,ZeroDivisionError):continue
    candidates&=np.isfinite(result)
    if not candidates.any():return result
    checked=sp.piecewise_fold(expression.rewrite(sp.Piecewise)) if expression.has(sp.Heaviside,sp.KroneckerDelta,sp.Piecewise) else expression
    for point in np.unique(coordinates[candidates]):
        checkpoint();exact_point=sp.Rational(str(point))
        # Use only a proven symbolic pole; a large finite value is left intact.
        exact=checked.subs(variable,exact_point)
        if exact.is_finite is False or exact.has(sp.zoo,sp.oo,-sp.oo,sp.nan):result[candidates&(coordinates==point)]=complex(np.nan,np.nan)
    return result
