"""CAS con entrada AST restringida; se ejecuta en proceso separado cancelable."""
import ast
import re
import math
import sympy as sp
from .resources import ensure_working_set

T = sp.Symbol("t", real=True)
S = sp.Symbol("s")
Z = sp.Symbol("z")
N = sp.Symbol("n", integer=True)
W = sp.Symbol("w", real=True)
TAU = sp.Symbol("tau", real=True)
SYMBOLS = {"t": T, "x": T, "s": S, "z": Z, "n": N, "w": W, "omega": W, "tau": TAU, "pi": sp.pi, "e": sp.E,
           "i": sp.I, "j": sp.I, "oo": sp.oo, "infinity": sp.oo, "true": sp.true, "false": sp.false}
FUNCTIONS = {"sinc": lambda x:sp.Piecewise((sp.S.One,sp.Eq(x,0)),(sp.sin(sp.pi*x)/(sp.pi*x),True)), "ceil":sp.ceiling, "ceiling":sp.ceiling, "floor":sp.floor, "sign":sp.sign,"sin": sp.sin, "cos": sp.cos, "tan": sp.tan, "exp": sp.exp, "log": sp.log,
             "asin":sp.asin, "acos":sp.acos, "atan":sp.atan, "tanh":sp.tanh, "ln": sp.log, "polylog":sp.polylog, "lerchphi":sp.lerchphi, "mod":sp.Mod, "eq":sp.Eq, "ne":sp.Ne, "erf": sp.erf, "erfc": sp.erfc, "sqrt": sp.sqrt, "abs": sp.Abs, "sinh": sp.sinh, "cosh": sp.cosh,
             "heaviside": sp.Heaviside, "diracdelta": sp.DiracDelta, "dirac": sp.DiracDelta,
             "step": lambda x:sp.Heaviside(x,1), "impulse": lambda x:sp.KroneckerDelta(x,0) if x.has(N) else sp.DiracDelta(x), "kroneckerdelta":sp.KroneckerDelta, "piecewise": sp.Piecewise, "conj": sp.conjugate, "re": sp.re, "im": sp.im}


def parse(expression):
    source = expression.strip().replace("π", "pi").replace("−", "-").replace("^", "**")
    source = re.sub(r"(?<=[0-9.)])\s*[iIjJ]\b", "*i", source)
    from .math_source import normalize
    source=normalize(source)
    tree = ast.parse(source, mode="eval")
    nodes = sum(1 for _ in ast.walk(tree))
    ensure_working_set(nodes, bytes_per_sample=1024, live_arrays=8)
    def visit(node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool): return sp.true if node.value else sp.false
            if isinstance(node.value, int): return sp.Integer(node.value)
            if isinstance(node.value, float) and math.isfinite(node.value):
                return sp.Rational(ast.get_source_segment(source, node))
        if isinstance(node, ast.Name):
            key = node.id.lower()
            if key in SYMBOLS: return SYMBOLS[key]
            if node.id.isascii() and node.id.isalpha() and not node.id.startswith("_"):
                return sp.Symbol(node.id)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand); return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp):
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Add): return sp.Add(left,right,evaluate=False)
            if isinstance(node.op, ast.Sub): return sp.Add(left,-right,evaluate=False)
            if isinstance(node.op, ast.Mult): return sp.Mul(left,right,evaluate=False)
            if isinstance(node.op, ast.Div): return sp.Mul(left,sp.Pow(right,-1,evaluate=False),evaluate=False)
            if isinstance(node.op, ast.Pow): return sp.Pow(left,right,evaluate=False)
            if isinstance(node.op, ast.BitAnd):return sp.And(left,right)
            if isinstance(node.op, ast.BitOr):return sp.Or(left,right)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.Invert,ast.Not)):return sp.Not(visit(node.operand))
        if isinstance(node, ast.Tuple): return tuple(visit(item) for item in node.elts)
        if isinstance(node, ast.BoolOp) and isinstance(node.op,(ast.And,ast.Or)):
            return (sp.And if isinstance(node.op,ast.And) else sp.Or)(*(visit(v) for v in node.values))
        if isinstance(node, ast.Compare) and len(node.ops)>1:
            operands=[node.left,*node.comparators]
            return sp.And(*(visit(ast.Compare(left=operands[i],ops=[op],comparators=[operands[i+1]])) for i,op in enumerate(node.ops)))
        if isinstance(node, ast.Compare) and len(node.ops) == 1:
            left, right = visit(node.left), visit(node.comparators[0])
            functions = {ast.Lt: sp.Lt, ast.LtE: sp.Le, ast.Gt: sp.Gt, ast.GtE: sp.Ge, ast.Eq: sp.Eq, ast.NotEq: sp.Ne}
            if type(node.ops[0]) in functions: return functions[type(node.ops[0])](left,right)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
            fn = FUNCTIONS.get(node.func.id.lower())
            if fn is not None:
                args=tuple(visit(arg) for arg in node.args)
                if fn in (sp.sin,sp.cos,sp.tan):return fn(*args,evaluate=False)
                return fn(*args)
        raise ValueError("Sintaxis no admitida. Use fórmulas matemáticas; no se admiten atributos, índices ni código Python.")
    result=visit(tree.body)
    from .singularities import extend_removable
    return extend_removable(result)


def execute(request):
    from .transform_status import OPERATIONS,finalize,merge_notes
    if request.get('operation') not in OPERATIONS:return _execute(request)
    from .calculation_notes import capture
    with capture() as records:result=_execute(request)
    if 'input_definition' not in result and request.get('expression'):
        from .expression_definition import prepare
        variable=Z if request['operation']=='z_inverse_expression' else S
        definition=prepare(request['expression'],variable,'complex',conditions=request.get('input_conditions',()))
        result['input_definition']=definition.metadata()
    result['calculation_notes']=merge_notes(result.get('calculation_notes',[]),records.values())
    return finalize(result)


def _execute(request):
    operation = request["operation"]
    if operation=="difference_equation":
        from .difference_equations import solve
        return solve(request)
    if operation=='cas_import':
        from .cas_import import import_result
        return import_result(request)
    if operation=="cas_worksheet":
        from .cas_engine import calculate
        return calculate(request)
    if operation in ("signal_measures_expression","signal_measures_window"):
        from .measures_symbolic import measure_expression,sample_measure_expression
        return (measure_expression if operation=="signal_measures_expression" else sample_measure_expression)(request)
    if operation in ('inverse_dtft_expression','inverse_dtft_samples'):
        from .inverse_dtft_algebra import inverse_expression,sample_expression
        return (inverse_expression if operation=='inverse_dtft_expression' else sample_expression)(request)
    if operation in ('z_expression','z_inverse_expression'):
        from .z_algebra import direct,inverse
        return (direct if operation=='z_expression' else inverse)(request)
    if operation in ("laplace", "inverse_laplace") and request.get("interpretation") == "bilateral":
        from .laplace_algebra import direct, inverse
        return (direct if operation == "laplace" else inverse)(request)
    expression = request.get("expression", "")
    if operation == 'dtft_expression':
        from .expression_definition import prepare,attach
        lower=sp.simplify(parse(request.get('lower','0')));upper=sp.simplify(parse(request.get('upper','oo')))
        if lower!= -sp.oo and not isinstance(lower,sp.Integer):raise ValueError('El límite inferior debe ser entero o -oo.')
        if upper!=sp.oo and not isinstance(upper,sp.Integer):raise ValueError('El límite superior debe ser entero u oo.')
        if lower>upper:raise ValueError('El límite inferior supera al superior.')
        if lower.is_finite and upper.is_finite:ensure_working_set(int(upper-lower+1),bytes_per_sample=1024,live_arrays=8)
        definition=prepare(expression,N,'discrete',(lower,upper),request.get('input_conditions',()));value=definition.expression
        if value.has(W,T,S,Z):raise ValueError('La secuencia usa n y no puede contener variables temporales continuas o de frecuencia.')
        if lower==-sp.oo and upper==sp.oo:
            from .dtft_pairs import direct as dtft_pairs
            spectrum=dtft_pairs(value)
            if spectrum is not None:
                return attach({'operation':'dtft_expression','result':str(spectrum),'condition':'True','output_variable':'w','evaluated':True,'method':'sinc_rectangle_pair','frequency_units':'rad/muestra','convention':'X(w) = sum x[n] exp(-i*w*n); w is 2*pi-periodic','scope':'Se aplicaron el par sinc/rectángulo, la linealidad, el desplazamiento y la traslación en frecuencia, conservando las muestras definidas por continuidad. Las imágenes espectrales se suman cuando se superponen. El espectro es 2π-periódico; en cada salto toma el promedio de los límites laterales.'},definition)
        from .z_direct_pairs import direct_pairs
        try:pair=direct_pairs(value,lower,upper)
        except (sp.PolynomialError,NotImplementedError):pair=None
        if pair is not None and not pair['empty'] and sp.simplify(pair['condition'].subs(Z,sp.exp(sp.I*W))) is sp.true:
            result=sp.simplify(pair['result'].subs(Z,sp.exp(sp.I*W)))
            return attach({'operation':'dtft_expression','result':str(result),'condition':'True','output_variable':'w','evaluated':not result.has(sp.Sum,sp.oo,sp.zoo,sp.nan),'method':'shared_discrete_pairs','frequency_units':'rad/muestra','convention':'X(w) = sum x[n] exp(-i*w*n); w is 2*pi-periodic','scope':'Se usa la misma secuencia de índices enteros que en Z, incluyendo sus valores por continuidad. La evaluación z=exp(i*w) se aplica sólo cuando las condiciones calculadas permiten todo el círculo unitario.'},definition)
        term=sp.simplify(value*sp.exp(-sp.I*W*N))
        result=sp.simplify(sp.summation(term,(N,lower,upper)))
        if result.has(sp.Sum) and term!=0:
            ratio=sp.simplify(term.subs(N,N+1)/term)
            if not ratio.has(N,sp.nan,sp.zoo,sp.oo):
                if lower.is_finite and upper==sp.oo:
                    condition=sp.simplify(sp.Abs(ratio)<1)
                    closed=sp.simplify(term.subs(N,lower)/(1-ratio))
                    if condition==sp.true:result=closed
                    elif condition!=sp.false:result=sp.Piecewise((closed,condition),(result,True))
                elif lower==-sp.oo and upper.is_finite:
                    condition=sp.simplify(sp.Abs(ratio)>1)
                    closed=sp.simplify(term.subs(N,upper)/(1-1/ratio))
                    if condition==sp.true:result=closed
                    elif condition!=sp.false:result=sp.Piecewise((closed,condition),(result,True))
        return attach({'operation':'dtft_expression','result':str(result),'condition':'True','output_variable':'w',
                'evaluated':not result.has(sp.Sum),'frequency_units':'rad/muestra',
                'convention':'X(w) = sum x[n] exp(-i*w*n); w is 2*pi-periodic',
                'scope':'Secuencia indicada entre límites inclusivos; cero fuera si los límites son finitos. Las condiciones y ramas de convergencia permanecen dentro de la expresión.'},definition)
    if operation in ('fourier_angular','inverse_fourier_angular'):
        frequency=sp.Dummy('frequency',real=True)
        from .expression_definition import prepare,attach
        inverse=operation=='inverse_fourier_angular'
        definition=prepare(expression,W if inverse else T,'frequency' if inverse else 'continuous',(-sp.oo,sp.oo),request.get('input_conditions',()),'integration_interval');value=definition.integral_expression()
        if value.has(T if inverse else W):raise ValueError('La entrada contiene la variable de salida; usá otro nombre para ese parámetro.')
        if inverse:
            answer=sp.inverse_fourier_transform(value.subs(W,2*sp.pi*frequency),frequency,T,noconds=False)
        else:
            answer=sp.fourier_transform(value,T,frequency,noconds=False)
        if isinstance(answer,tuple):result,condition=answer
        else:result,condition=answer,sp.true
        condition=sp.sympify(condition)
        if not inverse:
            result=result.subs(frequency,W/(2*sp.pi));condition=condition.subs(frequency,W/(2*sp.pi))
        result=sp.simplify(result)
        evaluated=not result.has(sp.FourierTransform,sp.InverseFourierTransform,sp.Integral)
        return attach({'operation':operation,'result':str(result),'condition':str(condition),
                'evaluated':evaluated,'output_variable':'t' if inverse else 'w',
                'convention':'x(t) = integral X(w) exp(i*w*t) dw / (2*pi)' if inverse else 'X(w) = integral x(t) exp(-i*w*t) dt',
                'frequency_units':'rad/s','scope':'Transformada bilateral. Las condiciones simbólicas acompañan la expresión; no se asume soporte causal.'},definition)
    if operation == 'expression_grid':
        import numpy as np
        from .operations import _finite_output
        variable={'t':T,'w':W}.get(request['variable'])
        if variable is None:raise ValueError('Elegí t o w como variable de muestreo.')
        value=parse(expression)
        if value.has(sp.DiracDelta,sp.FourierTransform,sp.InverseFourierTransform,sp.Integral,sp.Sum):
            raise ValueError('Una distribución o integral sin evaluar no se puede convertir en muestras finitas.')
        parameters=value.free_symbols-{variable}
        if parameters:raise ValueError('Asigná valores a los parámetros: '+', '.join(sorted(str(p) for p in parameters)))
        count=int(request['count']);start=float(request['start']);stop=float(request['stop'])
        if count<2 or not math.isfinite(start) or not math.isfinite(stop) or stop<=start:raise ValueError('Indicá una rejilla finita creciente con al menos dos puntos.')
        ensure_working_set(count,live_arrays=16)
        grid=np.linspace(start,stop,count)
        if np.any(np.diff(grid)<=0):raise ValueError('La rejilla no se distingue con la precisión disponible.')
        from .singularities import sample_symbolic
        values=sample_symbolic(value,variable,grid)
        if values.ndim==0:values=np.full(count,values,dtype=np.complex128)
        if values.shape!=(count,):raise ValueError('La expresión no produjo un valor por punto.')
        values=_finite_output(values,'La evaluación de la expresión')
        return {'operation':'expression_grid','samples':[[float(v.real),float(v.imag)] for v in values],
                'origin':start,'step':(stop-start)/(count-1),'variable':request['variable'],'expression':expression,
                'scope':'Muestras de la expresión indicada en una ventana finita; no reemplazan la definición algebraica.'}
    if operation == 'continuous_correlation':
        left=parse(request['left']);right=parse(request['right'])
        if left.has(TAU) or right.has(TAU):raise ValueError('Las entradas no deben contener la variable de retardo tau.')
        integrand=left*sp.conjugate(right.subs(T,T-TAU))
        period=request.get('period')
        if period:
            duration=sp.simplify(parse(period))
            if duration.free_symbols or duration.is_positive!=True or duration.is_finite!=True:raise ValueError('El periodo debe ser una constante positiva finita.')
            limits=(T,0,duration)
        else:limits=(T,-sp.oo,sp.oo)
        result=sp.simplify(sp.integrate(integrand,limits))
        return {'operation':'continuous_correlation','result':str(result),'evaluated':not result.has(sp.Integral),
                'output_variable':'tau','period':str(duration) if period else None,
                'scope':'Integral de un periodo, sin normalizar. Las expresiones deben ser periódicas con el periodo indicado.' if period else 'Correlación bilateral sin normalizar. Las expresiones incluyen su soporte y condiciones de convergencia.',
                'convention':'R(tau) = integral x(t) conjugate(h(t-tau)) dt'}
    if operation == "continuous_convolution":
        left=parse(request['left']);right=parse(request['right']);tau=sp.Dummy('tau',real=True)
        causal=bool(request.get('causal',True))
        integrand=left.subs(T,tau)*right.subs(T,T-tau)
        limits=(tau,0,T) if causal else (tau,-sp.oo,sp.oo)
        integral=sp.simplify(sp.integrate(integrand,limits))
        result=sp.Piecewise((integral,T>=0),(0,True)) if causal else integral
        return {'operation':'continuous_convolution','result':str(result),'evaluated':not result.has(sp.Integral),
                'scope':'Ambas entradas son cero para t<0; las fórmulas indicadas valen para t>=0.' if causal else 'Convolución bilateral; las expresiones deben incluir su soporte y cumplir las condiciones de convergencia.',
                'convention':'integral x(tau) h(t-tau) d tau'}
    if operation == "system_formula":
        domain=request['domain'];variable=S if domain=='analog' else Z
        expr=sp.cancel(parse(expression))
        if expr.has(T,N,W,sp.zoo,sp.nan,sp.oo):raise ValueError('Usá una función racional de s o de z, sin variables temporales.')
        numerator,denominator=sp.fraction(expr)
        b=sp.Poly(numerator,variable).all_coeffs();a=sp.Poly(denominator,variable).all_coeffs()
        advance=max(0,len(b)-len(a)) if domain=='digital' else 0
        if domain=='digital':b=[sp.S.Zero]*max(0,len(a)-len(b))+b
        result=execute(dict(operation='system_analysis',domain=domain,b=list(map(str,b)),a=list(map(str,a)),impulse=request.get('impulse',False)))
        result.update(transfer=str(expr),factored=str(sp.factor(expr)),advance=advance,scope=('Expresión racional ingresada. Las potencias de z positivas y negativas se convierten algebraicamente; una fórmula sola no fija la ROC ni prueba estabilidad interna tras cancelaciones.' if domain=='digital' else 'Expresión racional en s. La fórmula no fija por sí sola causalidad ni prueba estabilidad interna tras cancelaciones.'))
        return result
    if operation == "system_analysis":
        domain=request['domain']
        if domain not in ('analog','digital'):raise ValueError('Dominio de sistema inválido.')
        from .scalar_expression import exact_constant,numerical_value
        b=[exact_constant(v,parameters=True) for v in request['b']]
        a=[exact_constant(v,parameters=True) for v in request['a']]
        if not b or not a or all(v==0 for v in a):raise ValueError('El denominador no puede ser nulo.')
        if any(v.has(S,Z,T,N,sp.oo,sp.zoo,sp.nan) for v in b+a):raise ValueError('Los coeficientes deben ser constantes finitas o parámetros.')
        if domain=='digital' and a[0]==0:raise ValueError('La representación digital requiere a0 distinto de cero.')
        variable=S if domain=='analog' else Z
        def polynomial(coefficients):
            return sum(v*variable**(len(coefficients)-i-1 if domain=='analog' else -i) for i,v in enumerate(coefficients))
        numerator=polynomial(b);denominator=polynomial(a)
        expression=sp.cancel(numerator/denominator)
        result={'operation':'system_analysis','domain':domain,'original_numerator':str(numerator),'original_denominator':str(denominator),
                'transfer':str(expression),'factored':str(sp.factor(expression)),
                'coefficient_convention':'descending powers of s' if domain=='analog' else 'ascending powers of z^-1',
                'exact_b':[str(v) for v in b],'exact_a':[str(v) for v in a],
                'scope':'Representación algebraica de los coeficientes ingresados. Simplificar H no prueba estabilidad interna ni identifica una ROC.',
                'parameters':sorted(str(v) for coefficient in b+a for v in coefficient.free_symbols)}
        if not any(v.free_symbols for v in b+a):
            numeric=[numerical_value(v) for v in b+a]
            if any(not math.isfinite(v.real) or not math.isfinite(v.imag) for v in numeric):raise ValueError('Los coeficientes exceden la precisión numérica disponible.')
            result['numeric_b']=[[v.real,v.imag] for v in numeric[:len(b)]]
            result['numeric_a']=[[v.real,v.imag] for v in numeric[len(b):]]
        if request.get('impulse') and domain=='analog':
            impulse=sp.inverse_laplace_transform(expression,S,T)
            result['causal_impulse']=str(impulse)
            result['impulse_evaluated']=not impulse.has(sp.InverseLaplaceTransform)
        return result
    if operation == "laplace":
        from .expression_definition import prepare,attach
        definition=prepare(expression,T,'continuous',(sp.S.Zero,sp.oo),request.get('input_conditions',()),'unilateral_0minus');value=definition.integral_expression()
        if value.has(S,N,Z,W):raise ValueError('Laplace directa: ingresá x(t) usando t. Para una expresión en s elegí Inversa.')
        result, plane, condition = sp.laplace_transform(value, T, S)
        return attach({"operation": "Laplace unilateral", "result": str(result), "convergence": f"Re(s) > {plane}", "convergence_abscissa":str(plane),
                "condition": str(condition), "output_variable":"s", "scope": "Laplace unilateral: se integra desde 0− hasta infinito. Los valores para t<0 no forman parte de esta transformada.", "evaluated": not result.has(sp.LaplaceTransform,sp.Integral,sp.oo,sp.zoo,sp.nan)},definition)
    if operation == "inverse_laplace":
        value=parse(expression)
        if value.has(T,N,Z,W):raise ValueError('Laplace inversa: ingresá X(s) usando s. Para una expresión en t elegí Directa.')
        from .numeric_modes import laplace_numeric
        numeric_result=laplace_numeric(value,S,T)
        if numeric_result is not None:return numeric_result
        result = sp.inverse_laplace_transform(value, S, T)
        return {"operation": "Laplace inversa", "result": str(result), "output_variable":"t", "scope": "Interpretación causal: la salida es cero para t<0. No determina otras regiones de convergencia bilaterales.", "evaluated": not result.has(sp.InverseLaplaceTransform,sp.Integral,sp.zoo,sp.nan)}
    if operation == "z_finite":
        origin_value=sp.simplify(parse(str(request["origin"])))
        if not isinstance(origin_value,sp.Integer):raise ValueError("El primer índice debe ser un entero exacto.")
        origin=int(origin_value)
        samples = [sp.Rational(str(real))+sp.I*sp.Rational(str(imag)) for real,imag in request["samples"]]
        ensure_working_set(len(samples), bytes_per_sample=1024, live_arrays=8)
        terms = [value*Z**(-(origin+index)) for index,value in enumerate(samples) if value != 0]
        result = sp.Add(*terms)
        support = [origin+index for index,value in enumerate(samples) if value != 0]
        from .expression_definition import Definition,attach
        sequence=sp.Add(*[value*sp.KroneckerDelta(N,origin+index) for index,value in enumerate(samples) if value!=0])
        definition=Definition("Secuencia finita",sequence,N,"discrete",(sp.Integer(origin),sp.Integer(origin+len(samples)-1)),conditions=tuple(request.get("input_conditions",())))
        return attach({"operation": "Z de registro finito", "result": str(result), "evaluated":True,"output_variable":"z",
                "roc_finite_plane": "Todo z finito salvo z=0" if support and max(support)>0 else "Todo z finito",
                "infinity_included": not support or min(support)>=0,
                "scope": "Cero fuera del soporte; los decimales representan las muestras almacenadas"},definition)
    if operation == "inverse_z":
        count = int(request["count"])
        if count < 1: raise ValueError("N debe ser positivo.")
        ensure_working_set(count, bytes_per_sample=1024, live_arrays=12)
        q = sp.Symbol("q")
        rational = sp.cancel(parse(expression).subs(Z, 1/q))
        numerator, denominator = sp.fraction(rational)
        b, a = sp.Poly(numerator,q), sp.Poly(denominator,q)
        if not a.as_expr(): raise ValueError("Denominador nulo.")
        if b.is_zero:
            origin=0; coefficients=[sp.Integer(0)]*count
        else:
            bfirst=min(m[0] for m in b.monoms()); afirst=min(m[0] for m in a.monoms())
            origin=bfirst-afirst
            b=sp.Poly(sp.cancel(b.as_expr()/q**bfirst),q); a=sp.Poly(sp.cancel(a.as_expr()/q**afirst),q)
            coefficients=[]
            for index in range(count):
                value=b.nth(index)-sum(a.nth(j)*coefficients[index-j] for j in range(1,min(index,a.degree())+1))
                coefficients.append(sp.cancel(value/a.nth(0)))
        numeric=[]
        for value in coefficients:
            if value.free_symbols: numeric=None; break
            number=complex(value.evalf())
            if not math.isfinite(number.real) or not math.isfinite(number.imag): numeric=None; break
            numeric.append([number.real,number.imag])
        return {"operation": "Z inversa racional: expansión alrededor de z=infinito", "origin": int(origin),
                "coefficients": [str(value) for value in coefficients], "numeric_samples": numeric,
                "scope": "Rama de soporte acotado inferiormente; primeros N términos, no toda la señal infinita",
                "roc": "Exterior de todos los polos finitos no cancelados. La misma expresión con otra ROC puede dar otra secuencia."}
    if operation == "ode":
        from .scalar_expression import exact_constant
        from .expression_definition import prepare
        coefficients=[exact_constant(value,parameters=True) for value in request["coefficients"]]
        while coefficients and coefficients[-1] == 0: coefficients.pop()
        if len(coefficients)<2: raise ValueError("Se requiere una EDO de orden >=1.")
        initial=[exact_constant(value,parameters=True) for value in request["initial"]]
        order=len(coefficients)-1
        if len(initial)!=order: raise ValueError("Ingrese una condición inicial por derivada de orden 0 hasta orden-1.")
        definition=prepare(expression,T,'continuous',(sp.S.Zero,sp.oo),support_kind='unilateral_0minus')
        forcing_expression=definition.integral_expression()
        if forcing_expression.has(N,S,Z,W):raise ValueError('La entrada de la EDO debe estar expresada en t.')
        forcing, plane, condition=sp.laplace_transform(forcing_expression,T,S)
        polynomial=sum(value*S**j for j,value in enumerate(coefficients))
        correction=sum(coefficients[j]*sum(S**(j-1-k)*initial[k] for k in range(j)) for j in range(1,order+1))
        transformed=sp.cancel((forcing+correction)/polynomial)
        result=sp.inverse_laplace_transform(transformed,S,T)
        return {"input_definition":definition.metadata(),"calculation_notes":list(definition.extensions),"operation":"EDO lineal de coeficientes constantes", "result":str(result), "Y(s)":str(transformed),
                "forcing_convergence":f"Re(s) > {plane}; {condition}",
                "scope":"t >= 0 con las condiciones iniciales indicadas; a0*y+a1*y'+...=f(t)",
                "evaluated":not result.has(sp.InverseLaplaceTransform,sp.LaplaceTransform)}
    raise ValueError("Operación simbólica desconocida.")
