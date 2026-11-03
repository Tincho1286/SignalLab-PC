"""General worksheet CAS, using mathematical ASTs and an isolated SymPy worker."""
import ast,io,math,re,tokenize
import sympy as sp
from sympy.core.function import FunctionClass,AppliedUndef
from sympy.core.relational import Relational
from .resources import ensure_working_set


CONSTANTS={'pi':sp.pi,'e':sp.E,'i':sp.I,'j':sp.I,'oo':sp.oo,'infinity':sp.oo,
    'zoo':sp.zoo,'nan':sp.nan,'true':sp.true,'false':sp.false,
    'reals':sp.S.Reals,'complexes':sp.S.Complexes,'integers':sp.S.Integers,
    'naturals':sp.S.Naturals,'naturals0':sp.S.Naturals0,'emptyset':sp.S.EmptySet}
FUNCTIONS={name:getattr(sp,name) for name in ('sin','cos','tan','asin','acos','atan','atan2',
    'sinh','cosh','tanh','asinh','acosh','atanh','exp','log','polylog','lerchphi','sqrt','factorial','binomial','gamma','erf','erfc',
    'simplify','expand','factor','cancel','together','apart','trigsimp','expand_trig','powsimp',
    'diff','integrate','limit','series','summation','product','dsolve','nsolve','laplace_transform','inverse_laplace_transform',
    'gcd','lcm','div','rem','factorint')}
FUNCTIONS.update({'sinc':lambda x:sp.Piecewise((sp.S.One,sp.Eq(x,0)),(sp.sin(sp.pi*x)/(sp.pi*x),True)),'abs':sp.Abs,'ln':sp.log,'re':sp.re,'im':sp.im,'conj':sp.conjugate,
    'arg':sp.arg,'mod':sp.Mod,'piecewise':sp.Piecewise,'heaviside':sp.Heaviside,'diracdelta':sp.DiracDelta,
    'step':lambda value:sp.Heaviside(value,1),'kroneckerdelta':sp.KroneckerDelta,
    'integral':sp.Integral,'derivative':sp.Derivative,'sum':sp.summation,'prod':sp.product,
    'matrix':sp.Matrix,'vector':lambda value:sp.Matrix(value),'det':lambda a:a.det(),
    'inv':lambda a:a.inv(),'transpose':lambda a:a.T,'rank':lambda a:sp.Integer(a.rank()),
    'trace':lambda a:a.trace(),'eigenvalues':lambda a:a.eigenvals(),'nullspace':lambda a:a.nullspace(),
    'rref':lambda a:a.rref(),'diag':sp.diag,'eye':sp.eye,'zeros':sp.zeros,'ones':sp.ones,
    'eq':lambda a,b:sp.Eq(a,b,evaluate=False),'ne':lambda a,b:sp.Ne(a,b,evaluate=False)})
FUNCTIONS.update({'int':sp.integrate,'derive':sp.diff,
    'trig2exp':lambda value:value.rewrite(sp.exp),
    'exp2trig':lambda value:value.replace(lambda v:v.func==sp.exp,lambda v:sp.cos(v.args[0]/sp.I)+sp.I*sp.sin(v.args[0]/sp.I))})
SPECIAL={'assume','solve','solve_real','linsolve','approx','evalf','exact','subst','purge','ans'}
NAME=re.compile(r'[A-Za-z][A-Za-z0-9_]*\Z')


def empty_state():return {'version':1,'variables':{},'functions':{},'results':{},'ans':None,'assumptions':{}}


# Only mathematical SymPy constructors are accepted when restoring worker state.
# No eval, pickle, parse_expr or sympify is applied to user/state strings.
HEADS={name:value for name,value in vars(sp).items() if isinstance(value,type) and issubclass(value,sp.Basic)}
HEADS.update(MutableDenseMatrix=sp.MutableDenseMatrix,ImmutableDenseMatrix=sp.ImmutableDenseMatrix)
HEADS[sp.CRootOf.__name__]=sp.CRootOf
from sympy.functions.elementary.piecewise import ExprCondPair
HEADS['ExprCondPair']=ExprCondPair


def restore(source):
    tree=ast.parse(source,mode='eval');ensure_working_set(sum(1 for _ in ast.walk(tree)),bytes_per_sample=512,live_arrays=4)
    def visit(node):
        if isinstance(node,ast.Constant) and isinstance(node.value,(int,float,bool)):
            if isinstance(node.value,float) and not math.isfinite(node.value):raise ValueError('Estado numérico no finito.')
            return node.value
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.USub):return -visit(node.operand)
        if isinstance(node,(ast.List,ast.Tuple)):
            values=[visit(item) for item in node.elts];return values if isinstance(node,ast.List) else tuple(values)
        if isinstance(node,ast.Dict):return {visit(k):visit(v) for k,v in zip(node.keys,node.values)}
        if isinstance(node,ast.Name) and node.id.lower() in CONSTANTS:return CONSTANTS[node.id.lower()]
        if isinstance(node,ast.Call):
            if isinstance(node.func,ast.Name) and node.func.id in ('Symbol','Dummy','Function','Float'):
                if not node.args or not isinstance(node.args[0],ast.Constant) or not isinstance(node.args[0].value,str):raise ValueError('Estado simbólico inválido.')
                text=node.args[0].value
                if node.func.id=='Float':
                    if not re.fullmatch(r'[+\-0-9.eE]+',text):raise ValueError('Decimal inválido.')
                elif not re.fullmatch(r'_?[A-Za-z][A-Za-z0-9_]*',text):raise ValueError('Nombre simbólico inválido.')
                kwargs={item.arg:visit(item.value) for item in node.keywords}
                if any(key is None or key.startswith('_') for key in kwargs):raise ValueError('Estado simbólico inválido.')
                if node.func.id!='Float' and any(not isinstance(value,bool) and not (node.func.id=='Dummy' and key=='dummy_index' and isinstance(value,int)) for key,value in kwargs.items()):raise ValueError('Supuesto inválido.')
                return getattr(sp,node.func.id)(text,*[visit(arg) for arg in node.args[1:]],**kwargs)
            fn=HEADS.get(node.func.id) if isinstance(node.func,ast.Name) else visit(node.func)
            if fn is None or not (isinstance(node.func,ast.Name) or isinstance(fn,FunctionClass)):raise ValueError('Constructor simbólico no disponible.')
            if node.keywords:raise ValueError('Estado simbólico inválido.')
            return fn(*[visit(arg) for arg in node.args])
        raise ValueError('El estado contiene una construcción no matemática.')
    return visit(tree.body)


def encode(value):
    if isinstance(value,dict):return '{'+','.join(encode(k)+':'+encode(v) for k,v in value.items())+'}'
    if isinstance(value,list):return '['+','.join(encode(v) for v in value)+']'
    if isinstance(value,tuple):return '('+','.join(encode(v) for v in value)+(',' if len(value)==1 else '')+')'
    return sp.srepr(value)


def normalize(source,functions,variables):
    source=source.strip().rstrip(';').replace('π',' pi ').replace('∞',' oo ').replace('−','-').replace('×','*').replace('÷','/').replace('²','^2').replace('³','^3').replace('^','**')
    source=re.sub(r'(?<![<>=!:])=(?!=)','==',source)
    raw=list(tokenize.generate_tokens(io.StringIO(source).readline))
    if sum(token.type==tokenize.NEWLINE for token in raw)>1:raise ValueError('Usá una expresión por entrada. Para partir una fórmula en líneas, mantenela dentro de paréntesis o corchetes.')
    tokens=[token for token in raw if token.type not in (tokenize.NL,tokenize.NEWLINE,tokenize.INDENT,tokenize.DEDENT,tokenize.ENDMARKER)]
    result=[];previous=None
    for token in tokens:
        if previous is not None:
            left=previous.type in (tokenize.NUMBER,tokenize.NAME) or previous.string in (')',']')
            right=token.type in (tokenize.NUMBER,tokenize.NAME) or token.string=='('
            call=previous.type==tokenize.NAME and previous.string.lower() not in CONSTANTS and token.string=='(' and (previous.string.lower() in FUNCTIONS or previous.string.lower() in SPECIAL or previous.string in functions or previous.string not in variables and previous.string not in {'x','t','s','z','n','w','k'})
            boolean=previous.string in ('and','or','not') or token.string in ('and','or','not')
            if left and right and not call and not boolean:result.append((tokenize.OP,'*'))
        result.append((token.type,token.string));previous=token
    return tokenize.untokenize(result)


class Calculator:
    def __init__(self,state):
        self.state=state;self.variables={name:restore(value) for name,value in state['variables'].items()}
        self.functions={name:(value['parameters'],restore(value['body'])) for name,value in state['functions'].items()}
        self.assumptions=state.setdefault('assumptions',{});self.assumption_changes=set()
        self.locals={};self.undefined=set();self._resolving=set();self.numeric_root=False

    def resolve(self,value):
        if isinstance(value,list):return [self.resolve(v) for v in value]
        if isinstance(value,tuple):return tuple(self.resolve(v) for v in value)
        if isinstance(value,dict):return {self.resolve(k):self.resolve(v) for k,v in value.items()}
        if isinstance(value,(sp.Basic,sp.MatrixBase)):
            replacements={symbol:self.name(symbol.name) for symbol in value.free_symbols if symbol.name not in self.locals}
            if replacements:value=value.xreplace(replacements)
        return value

    def name(self,name):
        if name in self.locals:return self.locals[name]
        if name.lower() in CONSTANTS:return CONSTANTS[name.lower()]
        if name.lower()=='ans':
            if self.state['ans'] is None:raise ValueError('Todavía no hay un resultado para ans.')
            return self.resolve(restore(self.state['results'][str(self.state['ans'])]))
        if re.fullmatch(r'r[0-9]+',name):
            if name[1:] not in self.state['results']:raise ValueError(name+' no tiene un resultado válido.')
            return self.resolve(restore(self.state['results'][name[1:]]))
        if not NAME.fullmatch(name):raise ValueError('Usá nombres de letras, números y guion bajo, comenzando con una letra.')
        if name in self.variables:
            if name in self._resolving:raise ValueError('Hay una definición circular en '+name+'. Purgá ese nombre antes de usarlo.')
            self._resolving.add(name)
            try:return self.resolve(self.variables[name])
            finally:self._resolving.remove(name)
        from .cas_assumptions import symbol
        return symbol(name,self.assumptions)

    def parse(self,source):
        source=normalize(source,self.functions,self.variables)
        try:tree=ast.parse(source,mode='eval')
        except SyntaxError as exc:raise ValueError('Revisá paréntesis y operadores. Usá una expresión por cálculo y := para asignar.') from exc
        ensure_working_set(sum(1 for _ in ast.walk(tree)),bytes_per_sample=1024,live_arrays=8)
        def decimal(text):
            text=text.replace('_','');exponent=re.search(r'[eE]([+-]?\d+)',text)
            if exponent:ensure_working_set(abs(int(exponent[1]))+len(text),bytes_per_sample=32,live_arrays=6)
            return sp.Rational(text)
        def visit(node):
            if isinstance(node,ast.Constant):
                if isinstance(node.value,bool):return sp.true if node.value else sp.false
                if isinstance(node.value,int):return sp.Integer(node.value)
                if isinstance(node.value,float):return decimal(ast.get_source_segment(source,node))
                if isinstance(node.value,complex):
                    text=ast.get_source_segment(source,node)
                    return decimal(text[:-1])*sp.I
            if isinstance(node,ast.Name):return self.name(node.id)
            if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.USub,ast.UAdd)):
                value=visit(node.operand);return -value if isinstance(node.op,ast.USub) else value
            if isinstance(node,ast.BinOp):
                a,b=visit(node.left),visit(node.right)
                if isinstance(node.op,ast.Add):return a+b
                if isinstance(node.op,ast.Sub):return a-b
                if isinstance(node.op,ast.Mult):return a*b
                if isinstance(node.op,ast.Div):return a/b
                if isinstance(node.op,ast.Pow):
                    if isinstance(a,sp.Integer) and isinstance(b,sp.Integer) and b>0:
                        estimated=max(1,abs(int(a)).bit_length())*b//8+1
                        ensure_working_set(int(estimated),bytes_per_sample=1,live_arrays=4)
                    return a**b
                if isinstance(node.op,ast.Mod):return a%b
            if isinstance(node,(ast.List,ast.Tuple,ast.Set)):
                values=[visit(v) for v in node.elts]
                if isinstance(node,ast.Set):return sp.FiniteSet(*values)
                return tuple(values) if isinstance(node,ast.Tuple) else values
            if isinstance(node,ast.Dict):return {visit(k):visit(v) for k,v in zip(node.keys,node.values)}
            if isinstance(node,ast.BoolOp):return (sp.And if isinstance(node.op,ast.And) else sp.Or)(*[visit(v) for v in node.values])
            if isinstance(node,ast.Compare):
                operands=[node.left,*node.comparators];comparators={ast.Eq:sp.Eq,ast.NotEq:sp.Ne,ast.Lt:sp.Lt,ast.LtE:sp.Le,ast.Gt:sp.Gt,ast.GtE:sp.Ge}
                values=[comparators[type(op)](visit(operands[i]),visit(operands[i+1]),evaluate=False) for i,op in enumerate(node.ops) if type(op) in comparators]
                if len(values)!=len(node.ops):raise ValueError('Comparación no admitida.')
                return values[0] if len(values)==1 else sp.And(*values)
            if isinstance(node,ast.Subscript):
                value=visit(node.value);index=visit(node.slice)
                if not isinstance(value,(list,tuple,sp.Tuple,sp.MatrixBase)):raise ValueError('Sólo se indexan listas y matrices, desde cero.')
                indices=index if isinstance(index,tuple) else (index,)
                if not all(isinstance(v,sp.Integer) for v in indices):raise ValueError('Los índices deben ser enteros.')
                return value[tuple(map(int,indices)) if len(indices)>1 else int(indices[0])]
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and not node.keywords:
                name=node.func.id;key=name.lower()
                if key=='purge':
                    if not node.args or not all(isinstance(arg,ast.Name) for arg in node.args):raise ValueError('Purge recibe nombres: purge(a) o purge(a,f).')
                    for arg in node.args:
                        self.variables.pop(arg.id,None);self.functions.pop(arg.id,None);self.assumptions.pop(arg.id,None)
                    return sp.true
                if key=='assume':
                    from .cas_assumptions import constrain,PROPERTIES
                    if not node.args:raise ValueError('Usá assume(x>0) o assume(x,real).')
                    if len(node.args)==2 and isinstance(node.args[0],ast.Name) and isinstance(node.args[1],ast.Name) and node.args[1].id.lower() in PROPERTIES:
                        name=node.args[0].id
                        if name in self.variables or name in self.functions or name in self.locals or not isinstance(self.name(name),sp.Symbol):raise ValueError('Purgá el nombre antes de aplicarle supuestos: purge('+name+').')
                        constrain(name,self.assumptions,property_name=node.args[1].id.lower());self.assumption_changes.add(name)
                    else:
                        for arg in node.args:
                            condition=visit(arg)
                            conditions=list(condition.args) if isinstance(condition,sp.And) else [condition]
                            for item in conditions:
                                if not isinstance(item,Relational) or len(item.free_symbols)!=1:raise ValueError('Cada supuesto debe comparar un símbolo libre con una constante real finita.')
                                name=next(iter(item.free_symbols)).name
                                if name in self.variables or name in self.functions or name in self.locals:raise ValueError('Purgá el nombre antes de aplicarle supuestos: purge('+name+').')
                                constrain(name,self.assumptions,condition=item);self.assumption_changes.add(name)
                    return sp.true
                if key=='ans':
                    if node.args:raise ValueError('Usá ans o r1, r2, … para recuperar resultados.')
                    return self.name('ans')
                args=[visit(arg) for arg in node.args]
                if name in self.functions:
                    parameters,body=self.functions[name]
                    if len(args)!=len(parameters):raise ValueError(name+' requiere '+str(len(parameters))+' argumentos.')
                    return self.resolve(body.xreplace({sp.Symbol(param):arg for param,arg in zip(parameters,args)}))
                if key in SPECIAL or name=='N':return self.special('approx' if name=='N' else key,args)
                fn=FUNCTIONS.get(key)
                if fn is not None:
                    if key=='nsolve':self.numeric_root=True
                    if key=='factorial' and args and isinstance(args[0],sp.Integer) and args[0]>100:
                        try:digits=int(math.lgamma(float(args[0])+1)/math.log(10))+1
                        except (OverflowError,ValueError):raise ValueError('El tamaño de ese factorial excede los recursos numéricos disponibles.')
                        ensure_working_set(digits,bytes_per_sample=32,live_arrays=6)
                    if key in {'matrix','vector'}:
                        value=args[0] if args else [];rows=len(value) if isinstance(value,(list,tuple)) else 1;columns=len(value[0]) if rows and isinstance(value,(list,tuple)) and isinstance(value[0],(list,tuple)) else 1
                        ensure_working_set(rows*columns,bytes_per_sample=1024,live_arrays=6)
                    if key in {'zeros','ones','eye'}:
                        if not args or not all(isinstance(v,sp.Integer) and v>=0 for v in args):raise ValueError('Las dimensiones deben ser enteros no negativos.')
                        ensure_working_set(int(args[0]*(args[1] if len(args)>1 else args[0])),bytes_per_sample=1024,live_arrays=6)
                    if key in {'limit'} and len(args)==4 and args[3] in (sp.Symbol('left'),sp.Symbol('right')):args[3]='-' if str(args[3])=='left' else '+'
                    if key in {'integrate','int','sum','summation','prod','product'} and len(args)==4:args=[args[0],tuple(args[1:])]
                    if key in {'det','inv','transpose','rank','trace','eigenvalues','nullspace','rref'} and (not args or not isinstance(args[0],sp.MatrixBase)):raise ValueError('Esta operación requiere matrix([[…],[…]]).')
                    result=fn(*args)
                    if key=='nsolve' and len(args)>1:
                        from .cas_assumptions import solution_domain
                        variables=args[1] if isinstance(args[1],(list,tuple,sp.Tuple)) else [args[1]]
                        values=list(result) if isinstance(result,sp.MatrixBase) else [result]
                        for variable,value in zip(variables,values):
                            if isinstance(variable,sp.Symbol) and variable.name in self.assumptions and solution_domain(variable,self.assumptions).contains(value) is not sp.true:raise ValueError('La raíz numérica no cumple los supuestos de '+variable.name+' o no se pudo verificar. Elegí otra aproximación inicial.')
                    return result
                if not NAME.fullmatch(name):raise ValueError('Nombre de función no admitido.')
                self.undefined.add(name);return sp.Function(name)(*args)
            raise ValueError('Escribí una expresión matemática. No se admiten atributos, archivos ni instrucciones de Python.')
        return visit(tree.body)

    def special(self,name,args):
        if name in {'approx','evalf'}:
            if not 1<=len(args)<=2:raise ValueError('Usá approx(expr) o approx(expr,dígitos).')
            digits=args[1] if len(args)==2 else sp.Integer(15)
            if not isinstance(digits,sp.Integer) or digits<1:raise ValueError('Los dígitos deben ser un entero positivo.')
            ensure_working_set(int(digits),bytes_per_sample=64,live_arrays=4)
            def approximate(value):
                if isinstance(value,dict):
                    result={approximate(key):approximate(item) for key,item in value.items()}
                    if len(result)!=len(value):raise ValueError('Esa precisión hace coincidir claves distintas. Usá más dígitos.')
                    return result
                if isinstance(value,list):return [approximate(item) for item in value]
                if isinstance(value,tuple):return tuple(approximate(item) for item in value)
                if isinstance(value,sp.Tuple):return sp.Tuple(*[approximate(item) for item in value])
                if isinstance(value,sp.FiniteSet):
                    result=sp.FiniteSet(*[approximate(item) for item in value])
                    if len(result)!=len(value):raise ValueError('Esa precisión hace coincidir soluciones distintas. Usá más dígitos.')
                    return result
                if isinstance(value,Relational):return value.func(approximate(value.lhs),approximate(value.rhs),evaluate=False)
                if hasattr(value,'evalf'):return value.evalf(int(digits))
                raise ValueError('Esta estructura no admite aproximación directa. Elegí una expresión numérica o una lista, conjunto o matriz de valores.')
            return approximate(args[0])
        if name=='exact':return sp.nsimplify(*args)
        if name=='subst':
            if len(args)==2 and isinstance(args[1],dict):return args[0].subs(args[1],simultaneous=True)
            if len(args)==2 and isinstance(args[1],sp.Equality):return args[0].subs(args[1].lhs,args[1].rhs,simultaneous=True)
            if len(args)==3:return args[0].subs(args[1],args[2],simultaneous=True)
            raise ValueError('Usá subst(expr,x,valor) o subst(expr,{x:valor,y:valor}).')
        if name in {'solve','solve_real','linsolve'}:
            if len(args)!=2:raise ValueError('Indicá ecuación y variable: solve(expr,x), o una lista de ecuaciones y variables.')
            expression,variables=args
            if isinstance(variables,(tuple,list,sp.Tuple)):
                if name=='solve_real':raise ValueError('Solve_real resuelve una variable real. Para sistemas usá solve o linsolve y revisá sus soluciones.')
                if not all(isinstance(v,sp.Symbol) for v in variables):raise ValueError('Las incógnitas deben ser símbolos libres; purgá sus valores asignados.')
                result=(sp.linsolve if name=='linsolve' else sp.nonlinsolve)(expression,variables)
                if any(v.name in self.assumptions for v in variables):
                    from .cas_assumptions import solution_domain
                    if not isinstance(result,sp.FiniteSet):raise ValueError('La solución con supuestos conserva parámetros; resolvé sin supuestos y revisá sus condiciones.')
                    accepted=[]
                    for row in result:
                        checks=[solution_domain(v,self.assumptions).contains(item) for v,item in zip(variables,row)]
                        if any(check is sp.false for check in checks):continue
                        if any(check is not sp.true for check in checks):raise ValueError('No se pudieron verificar todos los supuestos de la solución paramétrica. No se devuelve como incondicional.')
                        accepted.append(row)
                    result=sp.FiniteSet(*accepted)
                return result
            if not isinstance(variables,sp.Symbol):raise ValueError('La incógnita debe ser un símbolo libre; usá purge(nombre) si tiene un valor asignado.')
            if isinstance(expression,Relational) and not isinstance(expression,sp.Equality):
                if name!='solve_real':raise ValueError('Para desigualdades usá solve_real(expr,x).')
                from .cas_assumptions import solution_domain
                return sp.solve_univariate_inequality(expression,variables,relational=False).intersect(solution_domain(variables,self.assumptions))
            from .cas_assumptions import solution_domain
            domain=solution_domain(variables,self.assumptions)
            if name=='solve_real':domain=domain.intersect(sp.S.Reals)
            return sp.solveset(expression,variables,domain=domain)
        raise ValueError('Comando no disponible.')


def presentation(value):
    if isinstance(value,sp.MatrixBase):
        return {'kind':'matrix','rows':value.rows,'columns':value.cols,'cells':[[presentation(value[i,j]) for j in range(min(value.cols,8))] for i in range(min(value.rows,12))]}
    if isinstance(value,dict):return {'kind':'mapping','total':len(value),'items':[[presentation(k),presentation(v)] for k,v in list(value.items())[:20]]}
    if isinstance(value,(list,tuple,sp.Tuple)):return {'kind':'list','total':len(value),'items':[presentation(v) for v in value[:20]]}
    from .signal_notation import normalize,latex,source
    shown=normalize(value)
    return {'kind':'scalar','latex':latex(shown),'text':source(shown) if isinstance(shown,sp.Expr) else str(shown),'pretty':sp.pretty(shown,use_unicode=True)}


def calculate(request):
    import copy,sys
    # Exact integer output is bounded by available memory, not Python's text-digit guard.
    # This module runs inside the independently cancellable CAS process.
    if hasattr(sys,'set_int_max_str_digits'):sys.set_int_max_str_digits(0)
    state=copy.deepcopy(request.get('state') or empty_state())
    if state.get('version')!=1:raise ValueError('Versión de hoja CAS no compatible.')
    source=str(request['source']).strip();cell=int(request['cell'])
    if not source:raise ValueError('Escribí una expresión antes de calcular.')
    calculator=Calculator(state);assignment=re.fullmatch(r'\s*([A-Za-z][A-Za-z0-9_]*)(?:\(([^()]*)\))?\s*:=\s*(.+)',source,re.S)
    notice=[];defined=None
    if assignment:
        name,parameters,body=assignment.groups()
        if name=='N' or name.lower() in CONSTANTS or name.lower() in FUNCTIONS or name.lower() in SPECIAL or re.fullmatch(r'r\d+',name):raise ValueError('Ese nombre está reservado. Elegí otro nombre para la variable o función.')
        if parameters is not None:
            if name in calculator.assumptions:raise ValueError('El nombre tiene supuestos de variable; usá purge('+name+') antes de definir una función.')
            parameters=[v.strip() for v in parameters.split(',')]
            if not parameters or not all(NAME.fullmatch(v) and v.lower() not in CONSTANTS and v.lower() not in FUNCTIONS and v.lower() not in SPECIAL for v in parameters) or len(set(parameters))!=len(parameters):raise ValueError('Los parámetros deben ser nombres distintos, sin nombres reservados.')
            calculator.locals={v:sp.Symbol(v) for v in parameters};value=calculator.parse(body)
            if not isinstance(value,(sp.Basic,sp.MatrixBase)):raise ValueError('La función debe devolver una expresión o matriz.')
            if any(str(fn.func)==name for fn in value.atoms(AppliedUndef)):raise ValueError('No se admiten funciones recursivas en la hoja CAS.')
            calculator.functions[name]=(parameters,value);calculator.variables.pop(name,None);defined=name+'('+', '.join(parameters)+')'
        else:
            value=calculator.parse(body)
            if isinstance(value,(sp.Basic,sp.MatrixBase)) and any(symbol.name==name for symbol in value.free_symbols):raise ValueError('La asignación se refiere a sí misma. Purgá o usá otro símbolo.')
            if name in calculator.assumptions:
                from .cas_assumptions import solution_domain,symbol
                if not isinstance(value,sp.Expr) or solution_domain(symbol(name,calculator.assumptions),calculator.assumptions).contains(value) is not sp.true:raise ValueError('El valor no cumple los supuestos de '+name+' o no se pudo verificar. Usá purge('+name+') para liberarlos.')
            calculator.variables[name]=value;calculator.functions.pop(name,None);defined=name
    else:value=calculator.parse(source)
    if isinstance(value,sp.Integer):ensure_working_set(max(1,int(value).bit_length()*30103//100000),bytes_per_sample=32,live_arrays=6)
    encoded=encode(value);restore(encoded)
    state.update(variables={name:encode(v) for name,v in calculator.variables.items()},functions={name:{'parameters':params,'body':encode(body)} for name,(params,body) in calculator.functions.items()})
    state['results'][str(cell)]=encoded;state['ans']=cell
    if calculator.undefined:notice.append('Funciones simbólicas sin definición: '+', '.join(sorted(calculator.undefined))+'.')
    if calculator.numeric_root:notice.append('Raíz numérica local: depende de la aproximación inicial y no representa todas las soluciones.')
    if isinstance(value,sp.Basic) and value.has(sp.Integral,sp.Sum,sp.Product,sp.Derivative,sp.Limit,sp.ConditionSet):notice.append('El resultado conserva operaciones o condiciones sin resolver; no se reemplazan por una aproximación supuesta.')
    if isinstance(value,sp.Basic) and value.has(sp.zoo,sp.nan):notice.append('El resultado no representa un valor finito definido.')
    if defined:notice.append('Definición guardada: '+defined+'.')
    from .cas_assumptions import descriptions
    assumption_rows=descriptions(calculator.assumptions)
    for name,description in assumption_rows:
        if name in calculator.assumption_changes:notice.append('Supuestos de '+name+': '+description+'.')
    from .signal_notation import source as signal_source
    plain=signal_source(value) if isinstance(value,sp.Expr) else str(value)
    expression=None;symbols=[]
    if isinstance(value,sp.Expr) and not isinstance(value,sp.MatrixExpr):
        symbols=sorted(str(v) for v in value.free_symbols);expression=sp.sstr(value)
    return {'state':state,'text':plain,'presentation':presentation(value),'notices':notice,'expression':expression,'symbols':symbols,
        'assumptions':assumption_rows,
        'variables':[(name,str(calculator.resolve(value))) for name,value in calculator.variables.items()],
        'functions':[(name+'('+', '.join(params)+')',str(body)) for name,(params,body) in calculator.functions.items()]}
