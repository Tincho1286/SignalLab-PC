"""Explain calculated temporal signals using their own definitions and samples."""
from hashlib import sha256
from .result_summary import Formula,Section,number


def _literal(value):
    z=complex(value)
    real=repr(z.real)
    if not z.imag:return real
    return '('+real+'+i*('+repr(z.imag)+'))'


def _symbol(signal):
    meta=signal.metadata;op=meta.get('operation','')
    if meta.get('component'):return 'y'
    if meta.get('excitation')=='impulse' or op in ('frequency_filter_impulse','windowed_impulse'):return 'h'
    if op in ('difference_equation','forced_response','discrete_response_decomposition','analog_response','frequency_filter_output'):return 'y'
    if op in ('Salida de simulación','Estado de simulación'):return signal.name
    if 'correlation' in op or 'covariance' in op or signal.units in ('retardo','retardo k'):return 'r'
    return 'x'


def _recurrence(signal,symbol):
    meta=signal.metadata
    if signal.domain!='discrete' or meta.get('operation') not in ('difference_equation','forced_response','discrete_response_decomposition'):return None
    b,a=meta.get('b'),meta.get('a')
    if not b or not a:return None
    rows=[];formulas=[]
    stages=meta.get('sos')
    if stages:
        expression='v_j[n] = Sum(b[j,k]*v_prev[n-k],(k,0,2))-Sum(a[j,k]*v_j[n-k],(k,1,2))'
        formulas.append(Formula(expression,'vⱼ[n] = Σ bⱼ[k]·vⱼ₋₁[n−k] − Σ aⱼ[k]·vⱼ[n−k]'))
        rows.append(('Entrada y salida de la cascada','v₀ = x, '+symbol+' = v'+str(len(stages))))
        for index,stage in enumerate(stages[:8],1):
            rows.append((f'Sección {index}', 'b = '+', '.join(map(number,stage[:3]))+' · a = '+', '.join(map(number,stage[3:]))))
        if len(stages)>8:rows.append(('Secciones restantes','Coeficientes completos en Detalles.'))
    else:
        values_b=[complex(*v) for v in b];values_a=[complex(*v) for v in a]
        if len(b)+len(a)<=14:
            terms=[]
            for values,name,sign,first in ((values_b,'x',1,0),(values_a,symbol,-1,1)):
                for delay in range(first,len(values)):
                    coefficient=sign*values[delay]
                    if coefficient:
                        terms.append(f'({_literal(coefficient)})*{name}[n'+(f'-{delay}' if delay else '')+']')
            expression=symbol+'[n] = '+(' + '.join(terms) or '0')
            if values_a[0]!=1:expression=symbol+'[n] = ('+(' + '.join(terms) or '0')+')/('+_literal(values_a[0])+')'
        else:
            expression=f'{symbol}[n] = (Sum(b[k]*x[n-k],(k,0,{len(b)-1}))-Sum(a[k]*{symbol}[n-k],(k,1,{len(a)-1})))/a[0]'
        formulas.append(Formula(expression,expression))
        if len(values_a)==1 and len(values_b)>5 and not meta.get('component'):
            if meta.get('excitation')=='impulse':
                fir=f'h[n] = Piecewise((b[n]/a[0], And(n>=0,n<{len(b)})), (0, True))'
                formulas.append(Formula(fir,f'h[n] = b[n]/a[0] para 0 ≤ n < {len(b)}; h[n] = 0 fuera de ese intervalo.'))
            elif meta.get('excitation')=='step':
                fir=f'y[n] = Sum(b[k]*Heaviside(n-k,1),(k,0,{len(b)-1}))/a[0]'
                formulas.append(Formula(fir,f'y[n] = Σ de k=0 a {len(b)-1} de b[k]·u[n−k] / a[0]'))
        rows.extend([('Numerador b',', '.join(map(number,values_b[:12]))),('Denominador a',', '.join(map(number,values_a[:12])))])
        if max(len(b),len(a))>12:rows.append(('Coeficientes restantes','Vectores completos en Detalles.'))
    start=str(signal.origin)
    if meta.get('component')=='zero_input':rows.append(('Entrada durante el registro','x[n] = 0'))
    elif meta.get('excitation')=='impulse':rows.append(('Entrada','x[n] = δ[n]'))
    elif meta.get('excitation')=='step':rows.append(('Entrada','x[n] = u[n], con u[0] = 1'))
    elif meta.get('input_name'):rows.append(('Entrada x[n]',meta['input_name']))
    if meta.get('initial_rest'):
        rows.append(('Condición inicial','Reposo desde n₀ = '+start))
    else:
        for key,label in (('previous_inputs','Entradas anteriores'),('previous_outputs','Salidas anteriores')):
            if key in meta:rows.append((label,', '.join(number(complex(*v)) for v in meta[key]) or 'Cero'))
        rows.append(('Primer índice n₀',start))
    return Section('Ecuación en diferencias de la respuesta',rows=rows,formulas=formulas,
                   paragraphs=['La recurrencia usa los coeficientes y el historial del cálculo. El registro muestra las muestras obtenidas en el intervalo elegido.'])


def sections(signal):
    if signal.data_kind!='temporal':return []
    meta=signal.metadata;symbol=_symbol(signal);output=[]
    discrete=signal.domain=='discrete'
    variable=('k' if discrete else 'tau') if symbol=='r' else 'n' if discrete else 't'
    lhs=f'{symbol}[{variable}]' if discrete else f'{symbol}({variable})'
    exact=meta.get('temporal_formula')
    if isinstance(exact,dict) and exact.get('expression') and exact.get('variable')==variable and exact.get('operation')==meta.get('operation') and (exact.get('origin'),exact.get('step'))==(signal.origin,signal.step) and exact.get('fingerprint')==sha256(memoryview(signal.values).cast('B')).hexdigest():
        formula=lhs+' = '+exact['expression']
        output.append(Section('Expresión del modelo temporal',formulas=[Formula(formula,formula,numeric=bool(exact.get('numeric')))],
                              paragraphs=[exact.get('scope','La expresión describe el modelo asociado al registro.')]))
    recurrence=_recurrence(signal,symbol)
    if recurrence is not None:output.append(recurrence)
    from .inverse_fourier_report import stored_model
    if stored_model(signal):return output
    count=int(signal.values.size)
    if discrete:
        first=int(signal.origin);last=first+count-1
        if count<=8:
            cases=', '.join('('+_literal(value)+f', Eq({variable},{first+i}))' for i,value in enumerate(signal.values))
            expression=lhs+' = Piecewise('+cases+')'
        else:
            index=variable+'-'+str(first) if first>=0 else variable+'+'+str(-first)
            expression=lhs+' = v['+index+']'
        paragraphs=[f'Fórmula del registro entre {variable} = {first} y {variable} = {last}. Fuera de ese intervalo la tabla no determina la señal.']
    else:
        first=number(signal.origin);step=number(signal.step)
        expression=f'{symbol}({variable}_k) = v[k]'
        paragraphs=[f'{variable}_k = {first} + k·({step}), para k = 0…{count-1}. La expresión indica los valores calculados en la rejilla temporal.']
    rows=[(f'v[{i}]',number(v)) for i,v in enumerate(signal.values[:8])]
    if count>len(rows):paragraphs.append('El vector v completo está en Valores y en la exportación. Aquí se muestran sus primeras ocho entradas.')
    output.append(Section('Expresión del registro calculado',paragraphs=paragraphs,rows=rows,formulas=[Formula(expression,expression)]))
    return output


def attach_temporal_formula(signal,result,scope=None):
    if not result.get('evaluated') or not result.get('result'):return signal
    shown=result.get('display_result') or result['result']
    signal.metadata['temporal_formula']={'expression':shown,'source':result['result'],
        'variable':'n' if signal.domain=='discrete' else 't','numeric':bool(result.get('display_numeric')),
        'scope':scope or result.get('scope','Expresión del modelo evaluada sobre el registro.'),
        'operation':signal.metadata.get('operation'),'origin':signal.origin,'step':signal.step,
        'fingerprint':sha256(memoryview(signal.values).cast('B')).hexdigest()}
    return signal


def add_excitation_formula(signal,system,kind):
    """Use existing inverse engines for compact rational step and impulse responses."""
    if system.sos is not None or max(len(system.a),len(system.b))>5:return signal
    from .transfer_plane import effective_plane_system
    model=effective_plane_system(system)
    digital=model.domain=='digital'
    variable='z' if digital else 's'
    def polynomial(coefficients):
        order=len(coefficients)-1
        return '+'.join('('+_literal(value)+')*'+variable+'^('+str(-i if digital else order-i)+')'
                        for i,value in enumerate(coefficients) if value) or '0'
    expression='('+polynomial(model.b)+')/('+polynomial(model.a)+')'
    if kind=='step':expression+='*z/(z-1)' if digital else '/s'
    from .symbolic_process import run_request
    request={'operation':'z_inverse_expression' if digital else 'inverse_laplace','expression':expression,
             'roc':'right','laplace_roc':'right','include_samples':False}
    try:result=run_request(request)
    except (ValueError,ArithmeticError,OSError,RuntimeError):return signal
    scope='Respuesta causal de los coeficientes usados en el cálculo. La simulación muestra sólo la ventana elegida.'
    if not digital:scope+=' El registro causal empieza en el límite por la derecha en t=0.'
    return attach_temporal_formula(signal,result,scope)
