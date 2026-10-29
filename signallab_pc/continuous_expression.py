"""Sample the ordinary part and retain finite, affine Dirac terms by area."""
import ast
import math
from dataclasses import dataclass
import numpy as np
from .engine import evaluate_expression
from .model import Signal
from .distributions import attach_terms
from .resources import ensure_working_set
from .expression_dialects import to_numeric

DIRAC_NAMES={'dirac','diracdelta','impulse'}
AXIS_NAMES={'t','x'}


def has_dirac(expression):
    tree=ast.parse(expression.replace('^','**'),mode='eval')
    return any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id.lower() in DIRAC_NAMES for n in ast.walk(tree))


def _depends(node):
    return any(isinstance(n,ast.Name) and n.id.lower() in AXIS_NAMES for n in ast.walk(node))


def _number(value):return ast.Constant(value=value)
def _zero(node):return isinstance(node,ast.Constant) and node.value==0


def _binary(left,op,right):
    if isinstance(op,ast.Div) and _zero(right):raise ValueError('El peso o la parte ordinaria no puede incluir una división por cero.')
    if isinstance(op,(ast.Mult,ast.Div)) and _zero(left):return _number(0)
    if isinstance(op,ast.Mult) and _zero(right):return _number(0)
    if isinstance(op,ast.Add):
        if _zero(left):return right
        if _zero(right):return left
    return ast.BinOp(left=left,op=op,right=right)


def _value(node,point):
    return complex(evaluate_expression(ast.unparse(node),np.array([point],dtype=float))[0])


def _affine(node):
    """Return a,b in a*t+b, rejecting nonlinear or complex support coordinates."""
    if isinstance(node,ast.Name) and node.id.lower() in AXIS_NAMES:return 1+0j,0j
    if not _depends(node):return 0j,_value(node,0.)
    if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
        a,b=_affine(node.operand);sign=-1 if isinstance(node.op,ast.USub) else 1;return sign*a,sign*b
    if isinstance(node,ast.BinOp):
        a,b=_affine(node.left);c,d=_affine(node.right)
        if isinstance(node.op,ast.Add):return a+c,b+d
        if isinstance(node.op,ast.Sub):return a-c,b-d
        if isinstance(node.op,ast.Mult) and not (a and c):return a*d+b*c,b*d
        if isinstance(node.op,ast.Div) and not c and d:return a/d,b/d
        if isinstance(node.op,ast.Pow) and not c and d==1:return a,b
    raise ValueError('El argumento de Dirac debe ser lineal en t, como t-0.3 o 2*t+1. Los argumentos no lineales se conservan para el cálculo algebraico.')


def _near_zero(node,point):
    value=_value(node,point)
    try:
        a,b=_affine(node);scale=max(abs(a*point),abs(b),abs(value))
    except ValueError:scale=abs(value)
    return abs(value)<=8*math.ulp(float(scale))


def _condition(node,point):
    """Three-valued truth on a neighbourhood: None means a support boundary."""
    if isinstance(node,ast.Constant) and isinstance(node.value,bool):return node.value
    if isinstance(node,ast.BoolOp):
        values=[_condition(v,point) for v in node.values]
        if isinstance(node.op,ast.And):return False if False in values else None if None in values else True
        return True if True in values else None if None in values else False
    if isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.Not):
        value=_condition(node.operand,point);return None if value is None else not value
    if isinstance(node,ast.Compare):
        values=[];operands=[node.left,*node.comparators]
        for index,op in enumerate(node.ops):
            a,b=operands[index:index+2]
            relation=ast.Compare(left=a,ops=[op],comparators=[b])
            if ast.dump(a)==ast.dump(b):values.append(bool(_value(relation,point)));continue
            difference=_binary(a,ast.Sub(),b)
            values.append(None if _depends(difference) and _near_zero(difference,point) else bool(_value(relation,point)))
        return False if False in values else None if None in values else True
    if _depends(node) and _near_zero(node,point):return None
    return bool(_value(node,point))


def _smooth_at(node,point):
    if isinstance(node,ast.IfExp):
        condition=_condition(node.test,point)
        if condition is None:raise ValueError('El impulso coincide con un borde de los tramos. Escribí su peso y posición como un término Dirac separado.')
        _smooth_at(node.body if condition else node.orelse,point);return
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
        name=node.func.id.lower()
        if name=='where' and len(node.args)==3:
            condition=_condition(node.args[0],point)
            if condition is None:raise ValueError('El impulso coincide con un borde de los tramos. Escribí su peso y posición por separado.')
            _smooth_at(node.args[1] if condition else node.args[2],point);return
        if name in ('step','heaviside','sign','floor','ceil','ceiling') and node.args and _depends(node.args[0]):
            arg=node.args[0]
            at_boundary=_near_zero(arg,point) if name in ('step','heaviside','sign') else _value(arg,point).imag==0 and _value(arg,point).real.is_integer()
            if at_boundary:raise ValueError('El factor que multiplica Dirac es discontinuo en su posición. Indicá explícitamente el peso del impulso, sin multiplicarlo por ese borde.')
    if isinstance(node,(ast.Compare,ast.BoolOp)) and _condition(node,point) is None:
        raise ValueError('El factor del impulso cambia en su posición. Escribí explícitamente su peso.')
    for child in ast.iter_child_nodes(node):_smooth_at(child,point)


@dataclass
class Pulse:
    position:float
    weight:ast.AST
    gates:tuple=()


def _split(node):
    if not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id.lower() in DIRAC_NAMES for n in ast.walk(node)):
        return node,[]
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
        name=node.func.id.lower()
        if name in DIRAC_NAMES:
            if name in ('dirac','diracdelta') and len(node.args)==2 and isinstance(node.args[1],ast.Constant) and node.args[1].value==0:node.args=node.args[:1]
            if len(node.args)!=1 or node.keywords:raise ValueError('Esta carga admite Dirac de orden cero. Las derivadas de Dirac deben permanecer como expresiones algebraicas.')
            a,b=_affine(node.args[0])
            if a.imag or b.imag or not np.isfinite(a) or not np.isfinite(b):raise ValueError('La posición y la escala temporal de Dirac deben ser reales y finitas.')
            if not a:
                if b:return _number(0),[]
                raise ValueError('Dirac necesita un argumento que varíe con t; dirac(0) no define un impulso temporal.')
            position=float(-b.real/a.real);weight=1/abs(a.real)
            if not math.isfinite(position) or not math.isfinite(weight):raise ValueError('La posición o el peso de Dirac exceden el rango numérico.')
            return _number(0),[Pulse(position,_number(weight))]
        if name=='where' and len(node.args)==3 and not node.keywords:
            condition,left,right=node.args
            a,pa=_split(left);b,pb=_split(right)
            for pulse in pa:pulse.gates+=((condition,True),)
            for pulse in pb:pulse.gates+=((condition,False),)
            return ast.Call(func=ast.Name(id='where',ctx=ast.Load()),args=[condition,a,b],keywords=[]),pa+pb
    if isinstance(node,ast.IfExp):
        return _split(ast.Call(func=ast.Name(id='where',ctx=ast.Load()),args=[node.test,node.body,node.orelse],keywords=[]))
    if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
        regular,pulses=_split(node.operand)
        if isinstance(node.op,ast.USub):
            regular=_binary(_number(-1),ast.Mult(),regular)
            for pulse in pulses:pulse.weight=_binary(_number(-1),ast.Mult(),pulse.weight)
        return regular,pulses
    if isinstance(node,ast.BinOp):
        left,pa=_split(node.left);right,pb=_split(node.right)
        if isinstance(node.op,(ast.Add,ast.Sub)):
            if isinstance(node.op,ast.Sub):
                for pulse in pb:pulse.weight=_binary(_number(-1),ast.Mult(),pulse.weight)
            return _binary(left,node.op,right),pa+pb
        if isinstance(node.op,ast.Mult):
            if pa and pb:raise ValueError('El producto de impulsos Dirac no se define como un producto de muestras. Usá suma, convolución o una expresión algebraica con sus hipótesis.')
            for pulse in pa:pulse.weight=_binary(pulse.weight,ast.Mult(),right)
            for pulse in pb:pulse.weight=_binary(left,ast.Mult(),pulse.weight)
            return _binary(left,ast.Mult(),right),pa+pb
        if isinstance(node.op,ast.Div) and not pb:
            for pulse in pa:pulse.weight=_binary(pulse.weight,ast.Div(),right)
            return _binary(left,ast.Div(),right),pa
        if isinstance(node.op,ast.Pow) and isinstance(right,ast.Constant) and right.value==1 and not pb:return left,pa
    raise ValueError('Esta operación no está definida para Dirac en un registro numérico. Se admiten sumas y factores ordinarios finitos, no potencias, recíprocos ni funciones de un impulso.')


def _parts(expression,lower,upper,*,right_open=False):
    lower,upper=float(lower),float(upper)
    original=ast.parse(expression.replace('^','**'),mode='eval')
    if any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id.lower()=='kroneckerdelta' for n in ast.walk(original)):
        raise ValueError('KroneckerDelta es un impulso discreto. Usá una entrada discreta para δ[n] o DiracDelta(t-a) para una Dirac continua.')
    source=to_numeric(expression);tree=ast.parse(source,mode='eval')
    if has_dirac(source) and any(isinstance(n,ast.Name) and n.id.lower() in {'n','k','w'} for n in ast.walk(tree)):
        raise ValueError('Una Dirac temporal usa t como variable. Para el impulso discreto usá impulse(n) en una entrada discreta.')
    regular,pulses=_split(tree.body)
    ordinary=ast.unparse(regular)
    if not math.isfinite(lower) or not math.isfinite(upper) or upper<lower:raise ValueError('El intervalo de los impulsos debe ser real, finito y creciente.')
    terms=[];excluded=[]
    for pulse in pulses:
        if _zero(pulse.weight):continue
        tolerance=8*max(math.ulp(lower),math.ulp(upper),math.ulp(pulse.position))
        if pulse.position<lower-tolerance or pulse.position>upper+tolerance or (right_open and abs(pulse.position-upper)<=tolerance):
            excluded.append(pulse.position);continue
        active=True
        for condition,expected in pulse.gates:
            value=_condition(condition,pulse.position)
            if value is None:raise ValueError('Un impulso coincide con el borde de un tramo. Definilo por separado con su posición y peso, sin una selección ambigua en el borde.')
            if value!=expected:active=False;break
        if not active:continue
        _smooth_at(pulse.weight,pulse.position);weight=_value(pulse.weight,pulse.position)
        if not np.isfinite(weight):raise ValueError('El peso del impulso debe ser finito.')
        terms.append((pulse.position,weight))
    return ordinary,terms,excluded,bool(pulses)


def sample_continuous(expression,origin,step,count,*,name='x(t)',support=None,right_open=False):
    count=int(count);origin=float(origin);step=float(step)
    if count<1 or not math.isfinite(origin) or not math.isfinite(step) or step<=0:raise ValueError('La rejilla requiere inicio finito, cantidad positiva y paso positivo.')
    ensure_working_set(count,live_arrays=10)
    axis=origin+step*np.arange(count)
    if not np.all(np.isfinite(axis)) or (count>1 and np.any(np.diff(axis)<=0)):raise ValueError('La rejilla no distingue sus coordenadas con la precisión disponible.')
    lower,upper=(origin,float(axis[-1])) if support is None else tuple(map(float,support))
    ordinary,terms,excluded,singular=_parts(expression,lower,upper,right_open=right_open)
    values=evaluate_expression(ordinary,axis)
    metadata=attach_terms({},terms)
    if singular:metadata.update(operation='continuous_expression',regular_expression=ordinary,dirac_scope='Los valores guardados son la parte ordinaria. Dirac se conserva por posición y peso; sólo se incluyen impulsos dentro del intervalo elegido.',excluded_dirac_positions=excluded)
    return Signal(values,origin,step,'s',name,'continuous',expression,metadata)


def finite_definition(expression,lower,upper):
    """Limit only the ordinary part; endpoint impulses retain their full weight."""
    from .expression_dialects import to_symbolic
    ordinary,terms,_,_=_parts(expression,lower,upper)
    pieces=[]
    if ordinary!='0':pieces.append('Piecewise((('+to_symbolic(ordinary)+'), (t >= '+repr(float(lower))+') and (t <= '+repr(float(upper))+')), (0, True))')
    for position,weight in terms:
        coefficient='('+repr(float(weight.real))+'+i*('+repr(float(weight.imag))+'))'
        pieces.append(coefficient+'*DiracDelta(t-('+repr(position)+'))')
    return '+'.join('('+piece+')' for piece in pieces) if pieces else '0'
