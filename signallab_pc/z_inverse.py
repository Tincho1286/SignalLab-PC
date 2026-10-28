"""Exact rational Z inversion without expanding or simplifying radical roots."""
import math
import sympy as sp
import mpmath as mp
from .symbolic import parse,Z,N,T,S,W
from .resources import ensure_working_set
from .jobs import checkpoint


def inverse(request):
    from .z_properties import inverse_pairs
    answer=inverse_pairs(request)
    if answer is not None:return answer
    expression=sp.cancel(parse(request['expression']))
    if expression.has(N,T,S,W):raise ValueError('Z inversa: ingresá X(z) usando z. Para x[n], elegí Directa.')
    if expression.has(sp.zoo,sp.nan,sp.oo):raise ValueError('La entrada debe definir una función racional finita.')
    mode=request.get('roc','right')
    if mode not in ('right','left','radius'):raise ValueError('Elegí soporte derecho, izquierdo o una ROC por radio.')
    radius=sp.cancel(parse(request.get('radius','1'))) if mode=='radius' else sp.S.One
    if mode=='radius' and (radius.free_symbols or radius.is_real is not True or radius.is_positive is not True):raise ValueError('El radio debe ser real, positivo y numérico.')
    try:
        num,den=map(lambda v:sp.Poly(v,Z),sp.fraction(expression))
        degree=max(0,int(den.degree()));ensure_working_set(max(1,degree**2),bytes_per_sample=1024,live_arrays=8)
        common,polynomial,parts=sp.apart_list(expression,Z)
    except sp.PolynomialError as exc:raise ValueError('Esta inversa algebraica admite funciones racionales de z.') from exc
    parameters=sorted(map(str,expression.free_symbols-{Z}));numeric=not parameters
    from .numeric_modes import PoleValues
    values=PoleValues();context=values.context;numeric_values=values.values
    as_mp=values.value;matched_values=values.match
    def radial_side(pole,value):
        distance=abs(value)-radius_mp
        uncertainty=context.mpf('1e-65')*max(1,abs(value),abs(radius_mp))
        if abs(distance)<=uncertainty:raise ValueError('El radio coincide con un polo o no puede separarse de él con suficiente precisión. Elegí otro radio dentro de la ROC.')
        if isinstance(pole,sp.CRootOf):
            interval=pole._get_interval();squared=sp.cancel(radius**2)
            def bounds(a,b):
                a,b=sp.Rational(a),sp.Rational(b)
                return (sp.S.Zero if a<=0<=b else min(a*a,b*b),max(a*a,b*b))
            for _ in range(256):
                if pole.is_real:lower,upper=bounds(interval.a,interval.b)
                else:
                    l1,u1=bounds(interval.ax,interval.bx);l2,u2=bounds(interval.ay,interval.by);lower,upper=l1+l2,u1+u2
                if (squared-upper).is_positive is True:return True
                if (lower-squared).is_positive is True:return False
                interval=interval.refine()
            raise ValueError('No se pudo separar el radio del módulo del polo mediante sus intervalos exactos. Elegí otro radio.')
        exact=sp.simplify(sp.Abs(pole)-radius)
        if exact.is_zero is True:raise ValueError('El radio coincide con un polo; elegí otro radio dentro de la ROC.')
        if exact.is_negative is True:return True
        if exact.is_positive is True:return False
        raise ValueError('No se pudo decidir la posición exacta del radio respecto del polo. Elegí otro radio o constantes exactas.')
    radius_mp=as_mp(radius).real if mode=='radius' else None
    poles=[];pole_index={};factor_cache={};terms=[];inner=[];outer=[];alias_needed=False
    for factor,coefficient_lambda,denominator_lambda,order in parts:
        if coefficient_lambda.expr==0:continue
        # apart_list expresses every denominator as z-p, not X(z)/z. This also
        # avoids adding an artificial origin pole just to apply a transform table.
        dummy=denominator_lambda.variables[0]
        if sp.expand(denominator_lambda.expr-(Z-dummy))!=0:raise ValueError('No se pudo normalizar una fracción parcial de la entrada.')
        key=factor.as_expr()
        if key not in factor_cache:
            checkpoint()
            try:roots=factor.all_roots(radicals=False) if factor.degree()>2 and not (factor.as_expr().free_symbols-{factor.gen}) else None
            except (NotImplementedError,sp.PolynomialError):roots=None
            if roots is None:
                solved=sp.roots(factor.as_expr(),factor.gen)
                if sum(solved.values())!=factor.degree():raise ValueError('No se resolvieron todos los polos. Usá coeficientes exactos; no se devuelve una inversa incompleta.')
                roots=[root for root,multiplicity in solved.items() for _ in range(multiplicity)]
            factor_cache[key]=roots
            if numeric:numeric_values.update(matched_values(factor,roots))
        for pole in factor_cache[key]:
            checkpoint()
            if pole not in pole_index:
                index=len(poles)+1;pole_index[pole]=index
                value=as_mp(pole) if numeric else None
                if pole==0:right=True
                elif mode=='right':right=True
                elif mode=='left':right=False
                else:
                    if pole.free_symbols:raise ValueError('Asigná los parámetros antes de elegir una ROC por radio.')
                    if value is None:value=as_mp(pole)
                    right=radial_side(pole,value)
                info={'pole':pole,'value':value,'right':bool(right),'polynomial':str(factor.as_expr().subs(factor.gen,Z)).replace('**','^'),'index':index}
                poles.append(info)
                if pole!=0:(inner if right else outer).append(info)
            info=poles[pole_index[pole]-1]
            coefficient=common*coefficient_lambda(pole)
            if coefficient==0:continue
            alias_needed=alias_needed or pole.has(sp.CRootOf) or sp.count_ops(pole)>20
            if numeric:
                approximate=info['value'];point=sp.Float(str(approximate.real),85)+sp.I*sp.Float(str(approximate.imag),85)
                numeric_coefficient=as_mp(common*coefficient_lambda(point))
            else:numeric_coefficient=None
            terms.append((info,int(order),coefficient,numeric_coefficient))
    def bound(items,largest):
        if not items:return sp.S.Zero if largest else sp.oo
        if numeric:return (max if largest else min)(items,key=lambda item:abs(item['value']))['pole']
        return (sp.Max if largest else sp.Min)(*[sp.Abs(item['pole']) for item in items])
    low_pole=bound(inner,True);high_pole=bound(outer,False)
    low=sp.Abs(low_pole) if numeric else low_pole;high=sp.Abs(high_pole) if numeric else high_pole
    if not numeric and mode=='radius':raise ValueError('Asigná los parámetros antes de elegir un radio.')
    if numeric and inner and outer and abs(as_mp(low_pole))>=abs(as_mp(high_pole)):raise ValueError('La región elegida es vacía.')
    impulses=[]
    for (power,),coefficient in polynomial.terms():
        if coefficient:impulses.append((int(-power),common*coefficient))
    actual_impulses=[c*sp.KroneckerDelta(N,n) for n,c in impulses];display_impulses=list(actual_impulses)
    actual_groups={};display_groups={};coefficient_rows=[]
    for term_index,(info,order,c,numeric_c) in enumerate(terms,1):
        pole=info['pole'];right=info['right'];p=sp.IndexedBase('p')[info['index']];a=sp.IndexedBase('A')[term_index]
        if pole==0:
            actual_impulses.append(c*sp.KroneckerDelta(N,order));display_impulses.append(a*sp.KroneckerDelta(N,order))
        else:
            condition=N>=order if right else N<=0
            weight=sp.binomial(N-1,order-1) if right else (-1)**order*sp.binomial(order-N-1,order-1)
            actual_groups.setdefault(condition,[]).append(c*weight*pole**(N-order))
            display_groups.setdefault(condition,[]).append(a*weight*p**(N-order))
        # The residue is a polynomial in the pole. Store a short exact definition
        # using the displayed root name rather than repeating RootOf everywhere.
        coefficient_rows.append((f'A[{term_index}]',str(c.xreplace({pole:p}))))
    def assembled(impulse_terms,groups):
        return sp.Add(*impulse_terms,*[sp.Piecewise((sp.Add(*items),condition),(0,True),evaluate=False) for condition,items in groups.items()])
    result=assembled(actual_impulses,actual_groups)
    display_numeric=bool(numeric and alias_needed)
    if display_numeric:
        from .numeric_modes import modal_expression,expression_source
        numeric_terms=[{'pole':info['value'],'coefficient':coefficient,'order':order,'right':info['right']} for info,order,c,coefficient in terms if info['pole']!=0]
        real_coefficients=all(c.is_real is True for c in num.all_coeffs()+den.all_coeffs())
        numerical_modes,fragments=modal_expression(numeric_terms,N,values,'z',real_coefficients,with_terms=True)
        display=sp.Add(*actual_impulses,numerical_modes)
        display_text=expression_source(display)
        display_terms=[expression_source(term) for term in [*actual_impulses,*fragments]]
    else:
        from .signal_notation import source as signal_source
        display_text=signal_source(result)
        display_terms=[]
    start=int(request.get('start',-16));count=int(request.get('count',65))
    if count<1:raise ValueError('Usá una cantidad positiva de muestras.')
    ensure_working_set(count,bytes_per_sample=1024,live_arrays=10)
    samples=[]
    if request.get('include_samples',True) and numeric:
        end=start+count-1;causal_exact=None
        # Initial samples of rational-coefficient causal models are inexpensive
        # to obtain exactly by recurrence. Distant indices use modal evaluation;
        # the switch changes the algorithm, never the permitted output interval.
        if mode=='right' and 0<=end<=512 and all(c.is_Rational for c in num.all_coeffs()+den.all_coeffs()):
            a=den.all_coeffs();q,remainder=sp.div(num,den);m=max(0,int(den.degree()));b=sp.Poly(remainder,Z).all_coeffs();b=[sp.S.Zero]*(m+1-len(b))+b
            causal_exact=[]
            for n in range(end+1):
                value=((b[n] if n<len(b) else 0)-sum(a[k]*causal_exact[n-k] for k in range(1,min(n,len(a)-1)+1)))/a[0]
                causal_exact.append(value)
        modal=[(info,order,numeric_c) for info,order,c,numeric_c in terms]
        real_input=all(c.is_real is True for c in num.all_coeffs()+den.all_coeffs())
        for offset,n in enumerate(range(start,start+count)):
            if offset%64==0:checkpoint(.5+.4*offset/max(1,count))
            if causal_exact is not None:
                value=complex(causal_exact[n] if n>=0 else 0)
                value+=sum(complex(c) for index,c in impulses if index==n)
            else:
                value=context.mpc(0)
                for index,c in impulses:
                    if index==n:value+=as_mp(c)
                for info,order,c in modal:
                    p=info['pole']
                    if p==0:
                        if n==order:value+=c
                    elif info['right'] and n>=order:value+=c*math.comb(n-1,order-1)*info['value']**(n-order)
                    elif not info['right'] and n<=0:value+=c*(-1)**order*math.comb(order-n-1,order-1)*info['value']**(n-order)
                if real_input:
                    if abs(value.imag)>context.mpf('1e-55')*max(1,abs(value)):raise ValueError('La cancelación de términos requiere más precisión para obtener muestras fiables.')
                    value=context.mpc(value.real,0)
                value=complex(value)
            if not math.isfinite(value.real) or not math.isfinite(value.imag):raise ValueError('Las muestras exceden el rango numérico.')
            samples.append([value.real,value.imag])
    zero_included=not inner and den.eval(0).is_zero is False
    infinity_included=not outer and num.degree()<=den.degree()
    roc=f'{low} '+('≤' if zero_included else '<')+f' |z| < {high}'
    pole_rows=[]
    if alias_needed:
        def endpoint(p,is_low):
            if p==0:return '0'
            if p==sp.oo:return '∞'
            if numeric:
                from .numeric_modes import expression_source
                return expression_source(values.number(abs(as_mp(p))))
            return sp.sstr(sp.Abs(p),order='none')
        roc=endpoint(low_pole,True)+(' ≤ ' if zero_included else ' < ')+'|z| < '+endpoint(high_pole,False)
        for info in poles:
            pole_rows.append((f'p[{info["index"]}]','Raíz de '+info['polynomial']+' = 0; aproximación '+(context.nstr(info['value'],16).replace('j','i') if numeric else str(info['pole']))+'; término '+('derecho' if info['right'] else 'izquierdo')))
    from .cas_engine import encode
    return {'cas_encoded':encode(result),'operation':'Z inversa algebraica','result':sp.sstr(result,order='none'),'display_result':display_text,'display_terms':display_terms,'display_numeric':display_numeric,'display_precision':17 if display_numeric else None,'evaluated':True,'roc':roc,'infinity_included':bool(infinity_included),
        'scope':'La descomposición es algebraica exacta. La ROC decide qué términos son derechos o izquierdos; los términos polinómicos se representan por impulsos discretos. Las muestras describen sólo el intervalo elegido.'+(' El texto completo de la fórmula evalúa polos y coeficientes con al menos 17 cifras significativas y es una aproximación numérica; el cálculo conserva la definición algebraica. La vista redondeada facilita su lectura.' if display_numeric else ''),
        'origin':start,'numeric_samples':samples or None,'output_variable':'n','parameters':parameters,'pole_definitions':pole_rows,'coefficient_definitions':coefficient_rows if alias_needed else [],
        'root_note':'p[k] identifica una raíz exacta del polinomio indicado. Su decimal sólo ayuda a reconocerla; no reemplaza la definición algebraica. A[k] es el coeficiente exacto del término mostrado.' if alias_needed else ''}

