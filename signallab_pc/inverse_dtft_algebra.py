"""Inverse DTFT by rational Z properties or one-period symbolic integration."""
import sympy as sp
import numpy as np
from .symbolic import parse,W,N,T,S,Z
from .signal_notation import source
from .resources import ensure_working_set

def rational_z(value):
    expanded=value.rewrite(sp.exp);replacements={}
    for atom in expanded.atoms(sp.exp):
        if not atom.has(W):continue
        power=sp.simplify(sp.diff(atom.args[0],W)/sp.I)
        offset=sp.simplify(atom.args[0]-sp.I*W*power)
        if power.is_Integer and not offset.has(W):replacements[atom]=sp.exp(offset)*Z**power
    candidate=sp.cancel(expanded.xreplace(replacements))
    return candidate if not candidate.has(W) and candidate.is_rational_function(Z) else None

def inverse_expression(request):
    from .expression_definition import prepare,attach
    lower=sp.simplify(parse(request.get('period_origin','-pi')))
    if lower.is_real is not True or lower.is_finite is not True or lower.free_symbols:
        raise ValueError('El inicio de un período de DTFT debe ser real, finito y numérico.')
    upper=lower+2*sp.pi
    definition=prepare(request['expression'],W,'periodic_frequency',(lower,upper),request.get('input_conditions',()),'integration_period')
    value=definition.integral_expression()
    if value.has(N,T,S,Z):raise ValueError('Ingresá X(w) usando w como frecuencia. n es el índice de salida; no se ingresa x[n] ni H(z).')
    from .inverse_frequency_domain import require_inverse_domain
    require_inverse_domain(request,value,sp.Interval(lower,upper),W)
    from .impulse_pairs import inverse_periodic_impulses
    lines,value=inverse_periodic_impulses(value,W,N,lower,upper)
    from .fourier_bands import inverse_bands
    exact=inverse_bands(value,W,N,discrete=True,period_origin=lower) if value==0 or value.has(sp.Piecewise,sp.Heaviside) else None
    if exact is not None:exact=sp.simplify(exact+lines)
    if exact is not None:
        return attach({'operation':'DTFT inversa algebraica','result':source(exact),'display_result':source(exact),
            'evaluated':True,'condition':'True','output_variable':'n','frequency_units':'rad/muestra',
            'input_expression':request['expression'],
            'scope':'La fórmula integra un período e incluye el valor en el origen. En la unión del período un impulso aislado tiene peso completo; si se especifican ambos extremos, sus aportes se promedian.'},definition,exact=exact)
    equivalent=rational_z(value)
    if equivalent is not None and not equivalent.free_symbols-{Z}:
        from .z_inverse import inverse
        try:result=inverse({'expression':str(equivalent),'roc':'radius','radius':'1','include_samples':False,'start':0,'count':1})
        except ValueError as exc:raise ValueError('La inversa ordinaria requiere que el círculo unidad no contenga polos. Revisá las singularidades de X(w). '+str(exc)) from exc
        result.update(operation='DTFT inversa algebraica',output_variable='n',frequency_units='rad/muestra',condition='True',input_expression=request['expression'],z_equivalent=str(equivalent),
            scope='Se usaron propiedades de Z con la ROC que contiene |z|=1. La secuencia puede ser derecha, izquierda o bilateral; no se presupone causalidad. '+result.get('scope',''))
        if lines!=0:
            from .cas_engine import restore
            exact=sp.simplify(restore(result['cas_encoded'])+lines)
            return attach({'operation':'DTFT inversa algebraica','result':source(exact),'display_result':source(exact),
                'evaluated':True,'condition':'True','output_variable':'n','frequency_units':'rad/muestra',
                'input_expression':request['expression'],
                'scope':'La parte ordinaria se invirtió por propiedades de Z. Se sumó la contribución de las líneas espectrales.'},definition,exact=exact)
        return attach(result,definition)
    integral=sp.Integral(value*sp.exp(sp.I*W*N),(W,lower,upper))
    from .cas_integrals import integrate
    try:result=integrate(value*sp.exp(sp.I*W*N),(W,lower,upper),conds='piecewise')/(2*sp.pi)
    except (NotImplementedError,ValueError):result=integral/(2*sp.pi)
    result=sp.simplify(result)
    if result.has(W):
        # A bound frequency left free by conditional integration is not x[n].
        result=integral/(2*sp.pi)
    result=sp.simplify(result+lines) if lines!=0 else result
    evaluated=not result.has(sp.Integral,sp.Sum) and not result.has(sp.oo,-sp.oo,sp.zoo,sp.nan)
    answer={'operation':'DTFT inversa algebraica','result':source(result),'display_result':source(result),'evaluated':evaluated,
        'condition':'True','output_variable':'n','frequency_units':'rad/muestra','input_expression':request['expression'],
        'scope':'x[n] = (1/2π) ∫ de ω₀ a ω₀+2π X(ω)e^(iωn)dω, para n entero. La entrada representa un período y se extiende periódicamente. Si queda una integral sin resolver, no se declara una expresión evaluada.'}
    return attach(answer,definition,exact=result)


def sample_expression(request):
    start=request['start'];count=request['count']
    if isinstance(start,bool) or int(start)!=start or isinstance(count,bool) or int(count)!=count or count<1:raise ValueError('Ingresá un índice entero y una cantidad positiva de muestras.')
    start,count=int(start),int(count)
    if max(abs(start),abs(start+count-1))>2**53:raise ValueError('Los índices exceden la precisión de float64.')
    ensure_working_set(count,live_arrays=12)
    result=request.get('solved') or inverse_expression(request)
    if result.get('z_equivalent'):
        from .z_inverse import inverse
        numerical=inverse({'expression':result['z_equivalent'],'roc':'radius','radius':'1','include_samples':True,'start':start,'count':count})
        return {'samples':numerical['numeric_samples'],'origin':start}
    if not result['evaluated']:raise ValueError('La integral todavía no está resuelta. Usá la DTFT inversa numérica para integrar una rejilla de frecuencia.')
    from .signal_notation import read
    from .cas_engine import restore
    expression=restore(result['cas_encoded']) if result.get('cas_encoded') else read(result['result'],('n',))
    if expression.free_symbols-{N}:raise ValueError('Asigná valores a los parámetros antes de generar muestras.')
    if expression.has(sp.DiracDelta,sp.Integral):raise ValueError('Esta expresión no admite muestras finitas ordinarias.')
    from .singularities import sample_symbolic
    indices=np.arange(count,dtype=np.int64)+start
    values=sample_symbolic(expression,N,indices)
    if values.ndim==0:values=np.full(count,values,dtype=complex)
    if values.shape!=(count,) or not np.isfinite(values).all():raise ValueError('La expresión no tiene un valor finito en todos los índices pedidos.')
    return {'samples':[[float(v.real),float(v.imag)] for v in values],'origin':start}
