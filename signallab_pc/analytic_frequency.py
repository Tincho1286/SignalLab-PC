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
    def to_document(self):
        return dict(format='signallab-expression-system',version=1,expression=self.expression,domain=self.domain,frequency_expression=self.frequency_expression,condition=self.condition,interpretation=self.interpretation,sample_period_s=self.sample_period_s)


def _sample(value,omega,repair=False,eligible=None,extensions=None,role='H'):
    from .symbolic import W
    try:
        function=sp.lambdify(W,value,modules=[{'sqrt':np.emath.sqrt,'log':np.emath.log},'scipy','numpy'])
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


def _condition_mask(condition,omega):
    """Conservatively hide machine-indistinguishable resonances, never fill them."""
    if condition is sp.true:return np.ones(omega.shape,dtype=bool)
    if condition is sp.false:return np.zeros(omega.shape,dtype=bool)
    if condition.func==sp.And:
        return np.logical_and.reduce([_condition_mask(part,omega) for part in condition.args])
    if condition.func==sp.Or:
        return np.logical_or.reduce([_condition_mask(part,omega) for part in condition.args])
    if condition.func==sp.Ne:
        left,right=(_sample(v,omega) for v in condition.args)
        scale=np.maximum(1,np.maximum(abs(left),abs(right)))
        return np.isfinite(left)&np.isfinite(right)&(abs(left-right)>64*np.finfo(float).eps*scale)
    from .symbolic import W
    function=sp.lambdify(W,condition,modules='numpy')
    with np.errstate(all='ignore'):return np.broadcast_to(np.asarray(function(omega),dtype=bool),omega.shape).copy()


def analyze_expression(exact,request,omega,*,period=None,logarithmic=False,margins=False):
    from .symbolic import execute,parse,S,Z,W
    from .frequency_analysis import FrequencyData
    exact=deepcopy(exact);domain=request['domain'];variable=Z if domain=='digital' else S
    if exact.get('evaluated') is False:
        exact['frequency_notice']='La fórmula contiene operaciones simbólicas pendientes. Se conserva la definición; completá esas operaciones antes de evaluar la frecuencia.'
        return exact,None
    if exact.get('parameters'):
        exact['frequency_notice']='Asigná valores a los parámetros: '+', '.join(exact['parameters'])+'.'
        return exact,None
    expression=parse(exact['transfer']);frequency=sp.simplify(expression.subs(variable,sp.exp(sp.I*W) if domain=='digital' else sp.I*W))
    condition=sp.true;interpretation='Evaluación de H(exp(iω)) o H(iΩ). La fórmula por sí sola no determina la ROC ni demuestra convergencia de Fourier.'
    origin=request.get('source_calculation')
    for _ in range(8):
        nested=origin.get('result',{}).get('source_calculation') if isinstance(origin,dict) else None
        if not isinstance(nested,dict):break
        origin=nested
    source=origin.get('request',{}) if isinstance(origin,dict) else {}
    if source.get('operation')=='z_expression':
        from .result_expressions import expression_result
        original=expression_result(origin)
        if original is None or sp.cancel(parse(original.source)-expression)!=0:
            raise ValueError('La fórmula y la transformada de origen no coinciden. Volvé a cargar la expresión para recuperar sus condiciones, o calculá la fórmula editada sin ese contexto.')
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
    derivative=sp.diff(frequency,W)
    with np.errstate(all='ignore'):
        slope=_sample(derivative,omega,repair=True,eligible=eligible,extensions=extensions,role='dH/dω');delay=-(slope/response).imag;magnitude=abs(response);db=20*np.log10(magnitude)
    valid=eligible&np.isfinite(response)&(magnitude>0)
    delay=np.where(valid&np.isfinite(delay),delay,np.nan);phase=np.full(omega.shape,np.nan)
    for segment in np.split(np.flatnonzero(valid),np.flatnonzero(np.diff(np.flatnonzero(valid))>1)+1):
        if segment.size:phase[segment]=np.unwrap(np.angle(response[segment]))
    system=ExpressionSystem(exact['transfer'],domain,str(frequency),str(condition),interpretation,period)
    margin_data=None
    if margins:margin_data=dict(available=False,reason='Esta vista conserva una expresión no racional. El cálculo de márgenes de esta herramienta requiere una transferencia racional.',convention='No se calcularon márgenes.',scope='No se ha inferido estabilidad a partir de una curva de frecuencia.')
    data=FrequencyData(system,omega,response,magnitude,db,phase,delay,logarithmic,0,margin_data)
    exact['frequency_limit_extensions']=extensions
    exact.update(frequency_expression=str(frequency),frequency_condition=str(condition),frequency_interpretation=interpretation,masked_frequency_samples=int(np.count_nonzero(~eligible)),
        analysis_limits='Se conserva H como expresión. No se calcularon una lista finita de polos/ceros ni una realización b/a. La fase y el retardo se excluyen donde la respuesta es nula, no finita o la condición no puede distinguirse con precisión numérica.')
    if origin is not None:exact['source_calculation']=deepcopy(origin)
    return exact,data
