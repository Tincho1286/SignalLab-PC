"""Frequency analysis of an expression without inventing finite b/a coefficients."""
from dataclasses import dataclass
from copy import deepcopy
import numpy as np
import sympy as sp


@dataclass
class ExpressionSystem:
    expression:str
    domain:str
    frequency_expression:str
    condition:str='True'
    interpretation:str='Evaluación de la fórmula sobre la frontera de Fourier; convergencia no demostrada.'
    sample_period_s:float|None=None
    name:str='Sistema definido por expresión'
    advance:int=0
    definition_kind:str='expression'
    def to_document(self):
        return dict(format='signallab-expression-system',version=1,expression=self.expression,domain=self.domain,frequency_expression=self.frequency_expression,definition_kind=self.definition_kind,condition=self.condition,interpretation=self.interpretation,sample_period_s=self.sample_period_s)


def _sample(value,omega,repair=False,eligible=None,extensions=None,role='H'):
    from .symbolic import W
    value=value.xreplace({sp.zoo:sp.nan,sp.oo:sp.nan,-sp.oo:sp.nan})
    try:
        from .hyperbolic import NUMERIC
        function=sp.lambdify(W,value,modules=[NUMERIC,{'sqrt':np.emath.sqrt,'log':np.emath.log},'scipy','numpy'])
        with np.errstate(all='ignore'):result=function(omega)
        result=np.broadcast_to(np.asarray(result,dtype=complex),omega.shape).copy()
    except (NameError,TypeError):
        # Special functions such as Lerch and polylog have no NumPy ufunc.
        # Evaluate their mathematical definition numerically, not a fitted FIR.
        import mpmath as mp
        from .jobs import checkpoint
        function=sp.lambdify(W,value,modules='mpmath');result=np.full(omega.shape,complex(np.nan,np.nan))
        active=np.ones(omega.shape,dtype=bool) if eligible is None else eligible
        with mp.workdps(20):
            for index in np.flatnonzero(active):
                checkpoint()
                try:result.flat[index]=complex(function(mp.mpf(repr(float(omega.flat[index])))))
                except (ValueError,ZeroDivisionError,OverflowError):pass
    if repair:
        from .singularities import finite_extension
        invalid=~np.isfinite(result)
        if eligible is not None:invalid&=eligible
        for point in np.unique(omega[invalid]):
            try:
                extension=finite_extension(value,W,point);number=complex(extension.evalf(18))
                if np.isfinite(number):
                    result[invalid&(omega==point)]=number
                    if extensions is not None:extensions.append(dict(role=role,point=str(point),value=str(extension)))
            except (ValueError,TypeError,NotImplementedError):pass
    return result


def _refine_periodic_zeros(difference,omega,ambiguous):
    from .symbolic import W
    from .fourier_phase import _simple_cycles
    from .jobs import checkpoint
    import math
    from fractions import Fraction
    import mpmath
    context=mpmath.mp.clone()
    evaluator=sp.lambdify(W,difference,modules=[context,'mpmath'])
    for index in np.flatnonzero(ambiguous):
        checkpoint()
        point=float(omega.flat[index])
        cycle=_simple_cycles(point)
        if cycle is None and 0<abs(point)<1e4:
            # Grids can accumulate one ULP when constructing an intended
            # rational multiple of pi. Never conflate a nonzero point with 0.
            nearby=Fraction(point/math.tau).limit_denominator(4096)
            if nearby and abs(float(nearby)*math.tau-point)<=2*math.ulp(point):
                cycle=nearby
        if cycle is not None:
            exact=difference.subs(W,2*sp.pi*sp.Rational(cycle.numerator,cycle.denominator))
            zero=exact.is_zero
            if zero is None and not exact.free_symbols and sp.count_ops(exact)<128:
                zero=sp.simplify(sp.expand_complex(exact)).is_zero
            if zero is not None:
                ambiguous.flat[index]=zero
                continue
        # A double near zero can be much smaller than machine epsilon; the
        # identity cos(x)-1 loses two powers of x when evaluated by subtraction.
        digits=max(55,45-2*int(math.log10(abs(point)))) if point else 55
        try:
            with context.workdps(digits):
                ambiguous.flat[index]=evaluator(context.mpf(point))==0
        except (TypeError,ValueError,OverflowError,ZeroDivisionError,NameError):
            pass
    return ambiguous


def _condition_mask(condition,omega):
    """Conservatively hide machine-indistinguishable resonances, never fill them."""
    if condition is sp.true:return np.ones(omega.shape,dtype=bool)
    if condition is sp.false:return np.zeros(omega.shape,dtype=bool)
    if condition.func==sp.And:
        return np.logical_and.reduce([_condition_mask(part,omega) for part in condition.args])
    if condition.func==sp.Or:
        return np.logical_or.reduce([_condition_mask(part,omega) for part in condition.args])
    if condition.func in (sp.Eq,sp.Ne):
        # Remove constant factors first so the tolerance does not turn a
        # mere change of units into extra excluded frequencies.
        difference=sp.factor_terms(sp.expand_mul(condition.lhs-condition.rhs))
        if difference.is_zero is True:return np.full(omega.shape,condition.func==sp.Eq,dtype=bool)
        _,difference=difference.as_independent(*difference.free_symbols,as_Add=False)
        if not difference.free_symbols:
            equal=difference.is_zero
            if equal is not None:return np.full(omega.shape,equal==(condition.func==sp.Eq),dtype=bool)
        from .symbolic import W
        polynomial=difference.free_symbols<={W} and difference.is_polynomial(W)
        if polynomial and sp.degree(difference,W)<=32:
            # Zero multiplicity should not increase the radius of exclusion.
            difference=sp.Poly(difference,W).sqf_part().as_expr()
        if not polynomial and difference.is_Pow and difference.exp.is_Integer and difference.exp>0:
            difference=difference.base
        observed=_sample(difference,omega)
        terms=sp.Add.make_args(difference)
        scale=sum(abs(_sample(term,omega)) for term in terms) if len(terms)>1 else abs(observed)
        # Single trigonometric terms still need a small tolerance for
        # machine approximations to their exact zeros.
        tolerance=64*np.finfo(float).eps*(scale if polynomial else np.maximum(1,scale))
        equal=abs(observed)<=tolerance
        if not polynomial and equal.any() and difference.has(sp.sin,sp.cos,sp.tan,sp.exp):
            equal=_refine_periodic_zeros(difference,omega,equal)
        return np.isfinite(observed)&np.isfinite(scale)&(equal if condition.func==sp.Eq else ~equal)
    from .symbolic import W
    from .hyperbolic import NUMERIC
    function=sp.lambdify(W,condition,modules=[NUMERIC,'numpy'])
    with np.errstate(all='ignore'):return np.broadcast_to(np.asarray(function(omega),dtype=bool),omega.shape).copy()


def smooth_frequency_derivative(frequency,omega):
    """Ordinary branch derivatives; a jump has no ordinary group delay."""
    from .symbolic import W
    steps=frequency.atoms(sp.Heaviside)
    modules=sorted(frequency.atoms(sp.Mod),key=sp.count_ops,reverse=True)
    replacements={term:sp.Dummy('fold',real=True) for term in modules}
    replacements.update({term:sp.Dummy('step',real=True) for term in steps})
    smooth=frequency.xreplace(replacements)
    derivative=sp.diff(smooth,W)
    for term,symbol in replacements.items():
        if term.func==sp.Heaviside:continue
        # A variable modulus needs a different derivative and is left explicit.
        if term.args[1].has(W):return sp.diff(frequency,W),np.zeros(omega.shape,dtype=bool)
        derivative+=sp.diff(smooth,symbol)*sp.diff(term.args[0],W)
    derivative=derivative.xreplace({v:k for k,v in replacements.items()})
    epsilon=128*np.finfo(float).eps*np.maximum(1,abs(omega))
    left,right=omega-epsilon,omega+epsilon
    candidates=np.zeros(omega.shape,dtype=bool)
    for term in frequency.atoms(sp.Piecewise):
        branches=sp.Piecewise(*[(sp.Integer(index),condition) for index,(_,condition) in enumerate(term.args)])
        candidates|=(_sample(branches,left)!=_sample(branches,right))
    for term in steps:candidates|=(_sample(term,left)!=_sample(term,right))
    for term in modules:
        a,b=_sample(term,left),_sample(term,right)
        period=_sample(term.args[1],omega)
        candidates|=(abs(a-b)>abs(period)/2)
    jumps=np.zeros(omega.shape,dtype=bool)
    if np.any(candidates):
        a,b=_sample(frequency,left[candidates]),_sample(frequency,right[candidates])
        jumps[candidates]=~np.isfinite(a)|~np.isfinite(b)|(abs(a-b)>1e-8*np.maximum(abs(a),abs(b)))
    return derivative,jumps


def analyze_expression(exact,request,omega,*,period=None,logarithmic=False,margins=False):
    from .symbolic import execute,parse,S,Z,W
    from .frequency_analysis import FrequencyData, response_magnitudes
    exact=deepcopy(exact);domain=request['domain'];variable=Z if domain=='digital' else S
    if exact.get('evaluated') is False:
        exact['frequency_notice']='La fórmula contiene operaciones simbólicas pendientes. Se conserva la definición; completá esas operaciones antes de evaluar la frecuencia.'
        return exact,None
    if exact.get('parameters'):
        exact['frequency_notice']='Asigná valores a los parámetros: '+', '.join(exact['parameters'])+'.'
        return exact,None
    frequency_only=exact.get('model_kind')=='frequency'
    expression=parse(exact['transfer']);frequency=expression if frequency_only else sp.simplify(expression.subs(variable,sp.exp(sp.I*W) if domain=='digital' else sp.I*W))
    condition=sp.true;interpretation='Evaluación de H(exp(iω)) o H(iΩ). La fórmula por sí sola no determina la ROC ni demuestra convergencia de Fourier.'
    if frequency_only:interpretation='Respuesta en frecuencia ingresada directamente. Su existencia y soporte se conservan cuando proviene de una DTFT; no se infiere una ROC abierta de Z.'
    origin=request.get('source_calculation')
    for _ in range(8):
        context=origin.get('cas_answer',{}).get('system_context',{}) if isinstance(origin,dict) else {}
        nested=context.get('source_calculation') if context.get('preserved') else None
        if nested is None:nested=origin.get('result',{}).get('source_calculation') if isinstance(origin,dict) else None
        if not isinstance(nested,dict):break
        origin=nested
    source=origin.get('request',{}) if isinstance(origin,dict) else {}
    if source.get('operation')=='z_expression':
        from .result_expressions import expression_result
        original=expression_result(origin)
        if original is None or original.variable!=('w' if frequency_only else 'z') or sp.simplify(parse(original.source)-expression)!=0:
            raise ValueError('La fórmula y la transformada de origen no coinciden. Volvé a cargar la expresión para recuperar sus condiciones, o calculá la fórmula editada sin ese contexto.')
    if frequency_only and isinstance(origin,dict) and origin.get('cas_answer'):
        answer=origin['cas_answer']
        if answer.get('frequency_units') in ('rad/s','rad/muestra','incompatible') and answer.get('frequency_units')!=('rad/muestra' if domain=='digital' else 'rad/s'):raise ValueError('La unidad de frecuencia del resultado CAS no coincide con el dominio elegido.')
        condition=parse(answer.get('frequency_condition','True'))
        interpretation='Expresión procedente del CAS. Se conservan la unidad de w y las restricciones de las reescrituras algebraicas; las condiciones de origen no se convierten en una ROC nueva.'
    if frequency_only and source.get('operation') in ('dtft_expression','fourier_angular'):
        original=origin.get('result',{})
        if not original.get('evaluated') or sp.simplify(parse(original['result'])-expression)!=0:
            raise ValueError('La respuesta y la transformada de origen no coinciden.')
        condition=parse(original.get('condition','True'))
        interpretation='Respuesta de Fourier calculada desde la señal original. Se conservan sus condiciones de convergencia y sus unidades.'
    if domain=='digital' and source.get('operation')=='z_expression':
        result=execute(dict(operation='dtft_expression',expression=source['expression'],lower=source.get('lower','0'),upper=source.get('upper','oo')))
        if result.get('evaluated'):
            frequency=parse(result['result']);condition=parse(result.get('condition','True'))
            interpretation='DTFT calculada desde la secuencia de origen y su soporte. La convergencia se comprueba separadamente de la ROC abierta de Z; se excluyen las resonancias indicadas.'
        else:
            exact['frequency_notice']='La definición se conservó, pero no se obtuvo una DTFT ordinaria convergente para el soporte original. No se presenta una continuación algebraica como respuesta física.'
            return exact,None
    omega=np.asarray(omega,dtype=float);eligible=_condition_mask(condition,omega)
    extensions=[]
    response=_sample(frequency,omega,repair=True,eligible=eligible,extensions=extensions);response[~eligible|~np.isfinite(response)]=complex(np.nan,np.nan)
    derivative,jumps=smooth_frequency_derivative(frequency,omega)
    with np.errstate(all='ignore'):
        slope = _sample(derivative, omega, repair=True, eligible=eligible, extensions=extensions, role='dH/dω')
        scale = np.maximum(abs(response.real), abs(response.imag))
        normalized_response = response.real/scale + 1j*(response.imag/scale)
        normalized_slope = slope.real/scale + 1j*(slope.imag/scale)
        delay = -(normalized_slope/normalized_response).imag
    magnitude, db = response_magnitudes(response)
    valid = eligible & np.isfinite(response) & (response != 0)
    from .frequency_phase import principal_phase
    delay = np.where(valid & ~jumps & np.isfinite(delay), delay, np.nan)
    # Arbitrary expressions can wind between any pair of sampled frequencies.
    # Without a factorization, the principal angle is the defined quantity.
    phase = principal_phase(response)
    system=ExpressionSystem(exact['transfer'],domain,str(frequency),str(condition),interpretation,period)
    system.definition_kind='frequency' if frequency_only else 'expression'
    margin_data=None
    if margins:margin_data=dict(available=False,reason='Esta vista conserva una expresión no racional. El cálculo de márgenes de esta herramienta requiere una transferencia racional.',convention='No se calcularon márgenes.',scope='No se ha inferido estabilidad a partir de una curva de frecuencia.')
    data=FrequencyData(system,omega,response,magnitude,db,phase,delay,logarithmic,0,margin_data,phase_kind="principal")
    exact['frequency_limit_extensions']=extensions
    exact['group_delay_jump_samples']=int(np.count_nonzero(jumps))
    exact.update(frequency_expression=str(frequency),frequency_condition=str(condition),frequency_interpretation=interpretation,masked_frequency_samples=int(np.count_nonzero(~eligible)),
        analysis_limits='Se conserva H como expresión. No se calcularon una lista finita de polos/ceros ni una realización b/a. La fase y el retardo no se muestran donde la respuesta es nula, no finita o su condición no puede distinguirse con precisión numérica. El retardo tampoco se define en saltos de la respuesta.')
    if origin is not None:exact['source_calculation']=deepcopy(origin)
    return exact,data
