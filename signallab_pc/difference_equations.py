"""Forward constant-coefficient recurrences with explicit prehistory."""
import math
import sympy as sp
from .symbolic import parse,N,Z,T,S,W
from .resources import ensure_working_set
from .jobs import checkpoint


class NoRationalTransform(ValueError):pass


def intervals(region):
    if region is sp.S.EmptySet:return []
    if region is sp.S.Reals:return [(-sp.oo,sp.oo)]
    if isinstance(region,sp.Union):return [pair for item in region.args for pair in intervals(item)]
    if isinstance(region,sp.FiniteSet):return [(int(v),int(v)) for v in region if v.is_integer is True]
    if isinstance(region,sp.Interval):
        a,b=region.start,region.end
        lower=-sp.oo if a==-sp.oo else sp.floor(a)+1 if region.left_open else sp.ceiling(a)
        upper=sp.oo if b==sp.oo else sp.ceiling(b)-1 if region.right_open else sp.floor(b)
        if lower.free_symbols or upper.free_symbols:raise NoRationalTransform('Bordes de tramos con parámetros pendientes.')
        return [] if lower>upper else [(lower,upper)]
    raise NoRationalTransform('Los tramos requieren condiciones de intervalo sobre n.')


def segments(value,lower,upper):
    """Disjoint intervals for Piecewise; products intersect their supports."""
    if value==0:return []
    if not value.has(sp.Piecewise,sp.Heaviside,sp.KroneckerDelta):return [(value,lower,upper)]
    if value.is_Add:return [part for term in value.args for part in segments(term,lower,upper)]
    if value.is_Mul:
        result=[(sp.S.One,lower,upper)]
        for factor in value.args:
            result=[(a*b,max(l,ll),min(u,uu)) for a,l,u in result for b,ll,uu in segments(factor,lower,upper) if max(l,ll)<=min(u,uu)]
            ensure_working_set(len(result),bytes_per_sample=4096,live_arrays=8)
        return result
    if isinstance(value,sp.Piecewise):
        result=[];covered=sp.S.EmptySet
        for amplitude,condition in value.args:
            try:valid=condition.as_set()
            except (NotImplementedError,ValueError,TypeError) as exc:raise NoRationalTransform('Condición de tramo no reducible a intervalos.') from exc
            region=(valid-covered).intersect(sp.Interval(lower,upper));covered=covered.union(valid)
            for l,u in intervals(region):result.extend(segments(amplitude,l,u))
        if intervals(sp.Interval(lower,upper)-covered):
            raise ValueError('La entrada por tramos deja índices sin definir desde n₀. Agregá un tramo final que complete f[n].')
        return result
    if value.func in (sp.Heaviside,sp.KroneckerDelta):
        argument=value.args[0] if value.func==sp.Heaviside else value.args[0]-value.args[1]
        try:poly=sp.Poly(sp.expand(argument),N)
        except sp.PolynomialError as exc:raise NoRationalTransform('El escalón o impulso debe tener argumento lineal.') from exc
        if poly.degree()!=1:raise NoRationalTransform('El escalón o impulso debe tener argumento lineal.')
        slope=poly.coeff_monomial(N);root=sp.cancel(-poly.coeff_monomial(1)/slope)
        if root.free_symbols or root.is_real is not True:raise NoRationalTransform('El desplazamiento debe ser real y numérico.')
        if value.func==sp.KroneckerDelta:
            return [(sp.S.One,root,root)] if root.is_integer is True and lower<=root<=upper else []
        result=[]
        if slope.is_positive is True:l,u=max(lower,sp.floor(root)+1),upper
        elif slope.is_negative is True:l,u=lower,min(upper,sp.ceiling(root)-1)
        else:raise NoRationalTransform('La pendiente del escalón debe tener signo conocido.')
        if l<=u:result.append((sp.S.One,l,u))
        if root.is_integer is True and lower<=root<=upper:result.append((value.args[1],root,root))
        return result
    raise NoRationalTransform('Entrada no reducible a tramos polinómico-exponenciales.')


def tail_transform(amplitude,start):
    """Transform of amplitude[start+k], k>=0, by geometric derivatives."""
    k=sp.Dummy('k',integer=True,nonnegative=True);u=sp.Dummy('u')
    value=sp.expand_mul(sp.expand_power_exp(amplitude.subs(N,k+start).rewrite(sp.exp)))
    result=sp.S.Zero
    for term in sp.Add.make_args(value):
        polynomial=sp.S.One;constant=sp.S.One;ratio=sp.S.One
        for factor in sp.Mul.make_args(term):
            if not factor.has(k):constant*=factor;continue
            if factor.func==sp.exp:base=sp.E;exponent=factor.args[0]
            elif factor.is_Pow and not factor.base.has(k):base=factor.base;exponent=factor.exp
            else:polynomial*=factor;continue
            slope=sp.diff(exponent,k);offset=sp.expand(exponent-slope*k)
            if slope.has(k) or offset.has(k):raise NoRationalTransform('Exponente no lineal.')
            constant*=base**offset;ratio*=base**slope
        try:poly=sp.Poly(polynomial,k)
        except sp.PolynomialError as exc:raise NoRationalTransform('Entrada no polinómico-exponencial.') from exc
        degree=max(0,int(poly.degree()))
        ensure_working_set((degree+1)**2,bytes_per_sample=2048,live_arrays=8)
        geometric=1/(1-u);sums=[geometric]
        for _ in range(degree):geometric=sp.cancel(u*sp.diff(geometric,u));sums.append(geometric)
        result+=constant*sum(coefficient*sums[power[0]].subs(u,ratio/Z) for power,coefficient in poly.terms())
    return sp.cancel(result)


def unilateral(value,start,parts=False):
    from .z_direct_pairs import pieces
    prepared=pieces(value,sp.Integer(start),sp.oo)
    if prepared is None:prepared=segments(sp.expand_mul(value),sp.Integer(start),sp.oo)
    terms=[]
    for amplitude,lower,upper in prepared:
        checkpoint()
        if amplitude==0:continue
        if lower==upper:
            terms.append(amplitude.subs(N,lower)*Z**(-(lower-start)));continue
        terms.append(Z**(-(lower-start))*tail_transform(amplitude,lower))
        if upper!=sp.oo:terms.append(-Z**(-(upper+1-start))*tail_transform(amplitude,upper+1))
    return terms if parts else sp.cancel(sum(terms,sp.S.Zero))


def forward_inverse(expression):
    from .z_inverse import inverse
    from .cas_engine import restore
    expression=sp.cancel(expression)
    if expression==0:return sp.S.Zero,False
    numerator,denominator=map(lambda v:sp.Poly(v,Z),sp.fraction(expression))
    delay=max(0,int(denominator.degree()-numerator.degree()))
    # Decompose X(z)/z, then advance the inverse one index. This avoids
    # artificial delta[n] + delayed geometric terms for a plain exponential.
    rational=sp.cancel(expression*Z**delay/Z)
    result=inverse({'expression':str(rational),'roc':'right','include_samples':False,'start':0,'count':1})
    k=sp.Dummy('m',integer=True,nonnegative=True)
    value=restore(result['cas_encoded']).subs(N,k+1)
    terms=[]
    for term in sp.Add.make_args(sp.expand_mul(value)):
        for gate in list(term.atoms(sp.Heaviside)):
            if gate.args[1]!=1:continue
            argument=sp.expand(gate.args[0])
            if argument.coeff(k)!=1:continue
            bound=sp.simplify(k-argument)
            if not bound.is_Integer:continue
            amplitude=term.xreplace({gate:sp.S.One})
            # For repeated poles the binomial factor already vanishes on
            # the excluded initial indices, so the step is redundant.
            if bound<=0 or all(sp.simplify(amplitude.subs(k,j))==0 for j in range(int(bound))):term=amplitude
        terms.append(term)
    value=sp.Add(*terms)
    if not value.has(sp.CRootOf) and sp.count_ops(value)<250:value=sp.factor_terms(sp.simplify(value))
    value=value.subs(k,N-delay)
    if delay:value*=sp.Heaviside(N-delay,1)
    return value,bool(result.get('display_numeric'))


def solve(request):
    from .signal_notation import source
    from .cas_engine import encode
    from .scalar_expression import exact_constant,integer_value
    from .expression_definition import prepare
    coefficients=[exact_constant(v,parameters=True) for v in request['coefficients']]
    if any(v.has(N,T,Z,S,W) or v.has(sp.nan,sp.zoo,sp.oo,-sp.oo) for v in coefficients):raise ValueError('Los coeficientes deben ser constantes finitas, independientes de n.')
    while coefficients and coefficients[-1]==0:coefficients.pop()
    if not coefficients:raise ValueError('La ecuación no determina y[n]: todos sus coeficientes son cero.')
    if coefficients[0]==0:raise ValueError('a₀ no puede ser cero: debe permitir despejar y[n].')
    order=len(coefficients)-1;start=integer_value(request.get('start',0));count=integer_value(request.get('count',64))
    if count<1:raise ValueError('La cantidad de muestras debe ser positiva.')
    ensure_working_set(order*order,bytes_per_sample=2048,live_arrays=12)
    history=[] if order==0 else [sp.S.Zero]*order if request.get('rest',True) else [exact_constant(v,parameters=True) for v in request['initial']]
    if len(history)!=order:raise ValueError('Cargá '+str(order)+' valores: y['+str(start-1)+'], y['+str(start-2)+'], …, y['+str(start-order)+'].')
    if any(v.has(N,T,Z,S,W,sp.nan,sp.zoo,sp.oo,-sp.oo) for v in history):raise ValueError('Las condiciones iniciales deben ser constantes finitas.')
    definition=prepare(request['expression'],N,'discrete',(sp.Integer(start),sp.oo),support_kind='recurrence_input')
    forcing=definition.expression
    if forcing.has(T,Z,S,W,sp.DiracDelta):raise ValueError('Usá n en f[n] e impulse(n−k) para impulsos discretos. No uses t, z ni DiracDelta.')
    denominator=sum(a*Z**(-j) for j,a in enumerate(coefficients))
    correction=-sum(coefficients[j]*sum(history[r-1]*Z**(-(j-r)) for r in range(1,j+1)) for j in range(1,order+1))
    transformed=None;closed=True
    if order==0:
        zero_input=sp.S.Zero;zero_state=sp.cancel(forcing/coefficients[0]);numeric_display=False
    else:
        zero_input,numeric_display=forward_inverse(sp.cancel(correction/denominator))
        try:
            transformed_parts=unilateral(forcing,start,parts=True)
            transformed=sp.cancel(sum(transformed_parts,sp.S.Zero));zero_state=sp.S.Zero
            for part in transformed_parts:
                component,display=forward_inverse(sp.cancel(part/denominator));zero_state+=component;numeric_display|=display
        except NoRationalTransform:
            kernel,display=forward_inverse(sp.cancel(1/denominator));numeric_display|=display
            k=sp.Symbol('k',integer=True)
            zero_state=sp.Sum(kernel.subs(N,N-k)*forcing.subs(N,start+k),(k,0,N));closed=False
    def shift(value):return value.subs(N,N-start) if start and order else value
    exact=shift(zero_input+zero_state)
    if not exact.has(sp.CRootOf,sp.Sum) and sp.count_ops(exact)<250:exact=sp.factor_terms(sp.simplify(exact))
    condition='n >= '+str(start)
    if coefficients[0].is_zero is not False:condition+='; '+str(coefficients[0])+' != 0'
    parameters=sorted(str(v) for v in forcing.free_symbols.union(*(a.free_symbols for a in [*coefficients,*history]))-{N})
    numeric=None;numeric_notice='';residual_check={'status':'Sin muestras numéricas: residuo de registro no disponible.'}
    if not parameters:
        import numpy as np
        from scipy.signal import lfilter,lfiltic
        from .transform_samples import sample_pair,sample_budget,NumericSamplingError
        try:
            sample_budget(count,bytes_per_sample=2048,live_arrays=12)
            a=np.array([complex(*sample_pair(sp.cancel(v/coefficients[0]))) for v in coefficients])
            initial=np.array([complex(*sample_pair(v)) for v in history])
            inputs=[]
            for i in range(count):
                if i%64==0:checkpoint(i/max(count,1))
                exact_input=forcing.subs(N,start+i)
                if exact_input.is_finite is False:
                    raise ValueError('f[n] no tiene valor finito en n='+str(start+i)+'.')
                inputs.append(complex(*sample_pair(sp.cancel(exact_input/coefficients[0]))))
            b=np.array([1.+0j]);zi=lfiltic(b,a,initial)
            with np.errstate(all='ignore'):values=lfilter(b,a,np.asarray(inputs),zi=zi)[0]
            if not np.isfinite(values).all():
                raise NumericSamplingError('La recurrencia excede el rango numérico en el intervalo elegido.')
            numeric=[sample_pair(v) for v in values]
            from .equation_checks import difference
            from .auxiliary import optional
            checked,check_notice=optional('Comprobación del residuo',lambda:difference(request,{'origin':start,'numeric_samples':numeric},arrays=(a,initial,values,np.asarray(inputs))))
            if checked is not None:
                residual_check=checked;residual_check['normalized_equation']=True
                residual_check['scope']+=' El residuo corresponde a la ecuación dividida por a₀; el máximo absoluto usa esa escala.'
            elif check_notice:residual_check['status']=check_notice
        except NumericSamplingError as exc:
            numeric=None
            numeric_notice='La solución algebraica se conserva. No se generaron muestras: '+str(exc)
    def text(value):
        if numeric_display:
            from .numeric_modes import expression_source
            return expression_source(sp.N(value,17))
        return source(value)
    from .procedure import step
    from .equation_checks import difference_symbolic
    procedure=[]
    if order==0:
        procedure.append(step('Despeje sin memoria','División por a₀',str(coefficients[0])+'*y[n] = '+str(forcing),'y[n] = '+str(exact),conditions=condition,source='difference_equations.solve'))
    elif transformed is not None:
        procedure.extend([step('Transformar la entrada desde n₀','Transformada Z unilateral de f[n₀+k]',forcing,transformed,conditions='k >= 0; n₀ = '+str(start),source='difference_equations.unilateral'),
            step('Incorporar la prehistoria','Identidad unilateral de los retardos',str(denominator)+'*Y0(z) = F0(z) + C(z)','C(z) = '+str(correction),conditions=condition,interpretation='Y₀ transforma y[n₀+k]; los valores y[n₀−j] son datos independientes.',source='difference_equations.solve'),
            step('Despejar la salida transformada','División por el operador de la recurrencia',str(transformed+correction),sp.cancel((transformed+correction)/denominator),conditions=str(sp.Ne(denominator,0)),source='difference_equations.solve')])
    else:
        procedure.append(step('Entrada no racional','Convolución finita con el núcleo calculado',forcing,zero_state,conditions='n >= n₀',interpretation='La suma se conserva exacta; no se presenta como una forma cerrada.',source='difference_equations.solve'))
    procedure.append(step('Solución y dominio','Suma de entrada cero y estado cero',str(shift(zero_input))+' + '+str(shift(zero_state)),'y[n] = '+str(exact),conditions=condition,source='difference_equations.solve'))
    result = {'procedure':procedure,'input_definition':definition.metadata(),'calculation_notes':list(definition.extensions),'residual_check':residual_check,'operation':'Ecuación en diferencias','result':source(exact),'display_result':text(exact),'display_numeric':numeric_display,'cas_encoded':encode(exact),'evaluated':closed,'closed_form':closed,'output_variable':'n','condition':condition,
            'equation_lhs':str(sum(a*sp.IndexedBase('y')[N-j] for j,a in enumerate(coefficients))),'order':order,'origin':start,'numeric_samples':numeric,'numeric_notice':numeric_notice,'parameters':parameters,'coefficients':[str(v) for v in coefficients],'initial':[str(v) for v in history],
            'zero_input':text(shift(zero_input)),'zero_state':text(shift(zero_state)),'system_expression':str(sp.cancel(1/denominator)),
            'unilateral_output':str(sp.cancel((transformed+correction)/denominator)) if transformed is not None else None,
            'scope':'La ecuación se impone desde n='+str(start)+'. Los valores anteriores indicados son condiciones iniciales; no se supone ni se reconstruye una historia infinita. La fórmula se aplica sólo en ese dominio. La cantidad de muestras controla el gráfico y la tabla, no trunca la solución algebraica.',
            'method':'Despeje algebraico de una ecuación sin memoria' if order==0 else 'Transformada Z unilateral y propiedades racionales' if closed else 'Respuesta de entrada cero más convolución discreta finita; no se obtuvo forma cerrada para la entrada'}

    from .auxiliary import optional
    check,notice=optional('Comprobación exacta de la recurrencia',lambda:difference_symbolic(request,result))
    result['symbolic_check']=check or {'verified':None,'status':notice}
    return result


def summary(request,result):
    from .result_summary import Summary,Section,Formula
    start=result['origin']
    equation=result['equation_lhs']+' = '+request['expression']
    sections=[Section('Ecuación y condiciones iniciales',paragraphs=['a₀ multiplica y[n], a₁ multiplica y[n−1], y así sucesivamente. La ecuación se resuelve hacia índices crecientes desde n₀.'],rows=[('Índice inicial n₀',str(start)),('Orden',str(result['order'])),*[(f'y[{start-k}]',value) for k,value in enumerate(result['initial'],1)]],formulas=[Formula(equation.replace(' = ',' == '),equation,numeric=True)]),
        Section('Solución',paragraphs=['Solución en forma cerrada.' if result['closed_form'] else 'Solución exacta representada por una suma finita de convolución. No se obtuvo una forma cerrada para esta entrada.'],formulas=[Formula('y[n] = '+result['display_result'],'y[n] = '+result['display_result'],numeric=result['display_numeric'])]),
        Section('Entrada cero y estado cero',paragraphs=['Entrada cero conserva las condiciones iniciales y toma f[n]=0. Estado cero conserva f[n] y pone las condiciones iniciales en cero. La suma de ambas da la solución total.'],formulas=[Formula('y_ic[n] = '+result['zero_input'],'y_ic[n] = '+result['zero_input'],numeric=result['display_numeric']),Formula('y_f[n] = '+result['zero_state'],'y_f[n] = '+result['zero_state'],numeric=result['display_numeric'])]),
        Section('Transferencia desde f[n]',paragraphs=['H(z) relaciona la entrada f[n] con y[n] bajo condiciones iniciales nulas. Las condiciones iniciales no forman parte de esta transferencia.'],formulas=[Formula('H(z) = '+result['system_expression'],'H(z) = '+result['system_expression'])]),
        Section('Dominio y método',rows=[('Validez',result['condition']),('Método',result['method'])],paragraphs=[result['scope']])]
    if result.get('symbolic_check'):
        check=result['symbolic_check'];sections.append(Section('Comprobación exacta de la fórmula',paragraphs=[check['status'],check.get('method','')],rows=[('Dominio',check.get('domain',result['condition']))],formulas=[Formula('r[n] = '+check['tail_residual'],'r[n] = '+check['tail_residual'])] if 'tail_residual' in check else []))
    if result.get('numeric_notice'):sections.append(Section('Muestras numéricas',paragraphs=[result['numeric_notice']]))
    if result.get('parameters'):sections.append(Section('Parámetros por asignar',paragraphs=[', '.join(result['parameters'])+'. La expresión se conserva; asigná valores para obtener muestras.']))
    if result.get('residual_check'):
        from .equation_checks import section
        sections.append(section(result['residual_check'],discrete=True))
    return Summary('Ecuación en diferencias',sections)
