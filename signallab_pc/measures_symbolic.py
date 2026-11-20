"""Energía y potencia de expresiones, con resultados y límites explícitos."""
import math
import sympy as sp
from .resources import ensure_working_set


def measure_expression(request):
    from .symbolic import parse,T,N,W,S,Z
    from .periodic_signals import ImpulseTrain, wrapped_period
    domain=request.get('domain','continuous');mode=request.get('mode','interval')
    if domain not in ('continuous','discrete') or mode not in ('interval','global','periodic'):raise ValueError('Dominio o alcance no admitido.')
    variable=T if domain=='continuous' else N
    value = parse(request['expression'])
    if domain == 'discrete':
        from .expression_definition import fold_discrete_gates
        value = fold_discrete_gates(value)
    value = sp.simplify(value)
    if not isinstance(value,sp.Expr) or value.has(sp.DiracDelta,ImpulseTrain,sp.oo,-sp.oo,sp.zoo,sp.nan):raise ValueError('La energía requiere una función ordinaria; no se eleva al cuadrado una distribución o un valor no finito.')
    if value.free_symbols.intersection({T,N,W,S,Z}-{variable}):raise ValueError('Usá sólo t para tiempo continuo o n para secuencias; las otras variables de dominio no son parámetros.')
    power_density=sp.simplify(value*sp.conjugate(value))
    def constant(text,integer=False):
        result=sp.simplify(parse(str(text)))
        if result.free_symbols or result.is_real is not True or result.is_finite is not True:raise ValueError('Los límites y el periodo deben ser constantes reales finitas.')
        if integer and result.is_integer is not True:raise ValueError('Los índices y periodos discretos deben ser enteros.')
        return result
    def accumulated(lower,upper,density=power_density):
        if domain=='discrete':
            if lower.is_number and upper.is_number and lower.is_finite and upper.is_finite:ensure_working_set(int(upper-lower+1),bytes_per_sample=1024,live_arrays=8)
            if not (lower.free_symbols or upper.free_symbols) and density.has(sp.Piecewise):
                from .z_direct_pairs import pieces
                intervals = pieces(density, lower, upper)
                if intervals is not None:
                    return sp.simplify(sp.Add(*(sp.summation(value, (N, start, stop))
                                                for value, start, stop in intervals if value != 0)))
            # Separar en n<0 y n>=0 ayuda a conservar los soportes de Abs/Piecewise.
            if lower==-sp.oo and upper==sp.oo:
                return sp.simplify(sp.summation(density,(N,-sp.oo,-1))+sp.summation(density,(N,0,sp.oo)))
            return sp.simplify(sp.summation(density,(N,lower,upper)))
        integrand=sp.piecewise_fold(density.rewrite(sp.Piecewise)) if density.has(sp.Heaviside) else density
        return sp.simplify(sp.integrate(integrand,(T,lower,upper)))
    def unresolved(expression):return expression.has(sp.Sum,sp.Integral,sp.Limit)
    def state(expression):
        if expression.has(sp.nan,sp.zoo) or isinstance(expression,sp.AccumBounds):return 'undefined'
        if expression==sp.oo:return 'divergent'
        if unresolved(expression):return 'unevaluated'
        if expression.has(sp.Piecewise) or expression.free_symbols:return 'conditional'
        if expression.is_real is True and expression.is_nonnegative is True and expression.is_finite is True:return 'finite'
        return 'undetermined'
    def record(expression):
        status=state(expression);data={'exact':str(expression),'status':status}
        if status=='finite':
            approximation=float(sp.N(expression,17))
            if math.isfinite(approximation):data['approximation']=approximation
        return data
    def energy_from_mean(power):
        if power==0:return sp.S.Zero
        if power.is_positive is True:return sp.oo
        if unresolved(power) or power.has(sp.nan,sp.zoo):
            return sp.Sum(power_density,(N,-sp.oo,sp.oo)) if domain=='discrete' else sp.Integral(power_density,(T,-sp.oo,sp.oo))
        return sp.Piecewise((0,sp.Eq(power,0)),(sp.oo,True))
    wrapping=wrapped_period(value if mode=='periodic' else power_density,variable) if mode!='interval' else None
    interval_energy=None;period_verified=False
    if mode=='interval':
        lower=constant(request.get('lower','0'),domain=='discrete');upper=constant(request.get('upper','1'),domain=='discrete')
        if upper<lower or domain=='continuous' and upper==lower:raise ValueError('El intervalo debe ser creciente; en discreto puede contener un único índice.')
        measure=upper-lower+(1 if domain=='discrete' else 0)
        energy=accumulated(lower,upper);power=sp.simplify(energy/measure)
        scope='Promedio sobre el intervalo indicado; no es la potencia media de toda la señal. Los índices discretos incluyen ambos extremos.'
        classification='Medidas del intervalo; sin clasificación global'
    elif mode=='periodic':
        period=constant(request.get('period','1'),domain=='discrete')
        if period.is_positive is not True:raise ValueError('El periodo debe ser positivo.')
        if wrapping is not None and (period/wrapping[0]).is_integer is True:
            cycle, lower, one_period=wrapping
            density=sp.simplify(one_period*sp.conjugate(one_period))
            upper=lower+period-(1 if domain=='discrete' else 0)
            interval_energy=accumulated(lower,lower+cycle-(1 if domain=='discrete' else 0),density)*(period/cycle)
        else:
            residual=sp.trigsimp(sp.simplify(value.subs(variable,variable+period)-value))
            if residual!=0:raise ValueError('No se pudo demostrar que el período indicado repita la expresión. Revisá el período o usá el análisis global.')
            lower=sp.Integer(0);upper=period-1 if domain=='discrete' else period
            interval_energy=accumulated(lower,upper)
        period_verified=True;power=sp.simplify(interval_energy/period)
        energy=energy_from_mean(power)
        scope='Periodicidad demostrada para el periodo indicado. Promedio calculado en un periodo; energía total sobre todo el eje.'
        classification=None
    else:
        from .harmonic_measures import harmonic_power

        lower,upper=-sp.oo,sp.oo
        power=harmonic_power(value,variable) if wrapping is None else None
        if wrapping is not None:
            cycle,first,density=wrapping
            power=sp.simplify(accumulated(first,first+cycle-(1 if domain=='discrete' else 0),density)/cycle)
            energy=energy_from_mean(power)
            scope='La definición se repite en todo el eje. La potencia se calcula sobre un período completo.'
        elif power is not None:
            energy=energy_from_mean(power)
            scope='Se agrupan las componentes con la misma frecuencia antes de calcular su potencia.'
            if domain=='discrete':scope+=' Las frecuencias separadas por un múltiplo de 2π representan la misma secuencia.'
        else:
            energy=accumulated(lower,upper)
            if state(energy)=='finite':power=sp.S.Zero
            else:
                limit_variable=sp.Symbol('M',positive=True,integer=True) if domain=='discrete' else sp.Symbol('R',positive=True)
                average=accumulated(-limit_variable,limit_variable)/(2*limit_variable+(1 if domain=='discrete' else 0))
                try:power=sp.simplify(sp.limit(average,limit_variable,sp.oo))
                except (NotImplementedError,ValueError,TypeError):power=sp.Limit(average,limit_variable,sp.oo)
            scope='La energía abarca todo el eje. La potencia usa el límite del promedio en ventanas simétricas crecientes.'
        classification=None
    if classification is None:
        if energy==0:classification='Energía nula'
        elif state(energy)=='finite' and energy.is_positive is True:classification='Señal de energía'
        elif state(power)=='finite' and power.is_positive is True:classification='Señal de potencia'
        elif energy==sp.oo and power==sp.oo:classification='Ni señal de energía ni de potencia finita'
        else:classification='Clasificación no determinada; revisar condiciones o resultados pendientes'
    rms=sp.sqrt(power)
    result={'operation':'signal_measures_expression','domain':domain,'mode':mode,'expression':request['expression'],'resolved_expression':str(value),
        'energy':record(energy),'mean_square':record(power),'rms':record(rms),'classification':classification,'scope':scope,
        'power_density':str(power_density),'bounds':[str(lower),str(upper)],'period_verified':period_verified,
        'convention':'E=sum |x[n]|^2; P=lim M→∞ sum(n=-M..M) |x[n]|^2/(2M+1)' if domain=='discrete' else 'E=integral |x(t)|^2 dt; P=lim R→∞ integral(-R..R) |x(t)|^2 dt/(2R)',
        'parameters':sorted(str(p) for p in value.free_symbols-{variable})}
    if interval_energy is not None:result['period_energy']=record(interval_energy);result['period']=str(period)
    return result


def sample_measure_expression(request):
    """Ventana numérica explícita, incluso si la definición tiene soporte infinito."""
    import numpy as np
    from .symbolic import parse,T,N
    from .periodic_signals import ImpulseTrain
    domain=request.get('domain','continuous')
    if domain not in ('continuous','discrete'):raise ValueError('Dominio no admitido.')
    variable = T if domain == 'continuous' else N
    value = parse(request['expression'])
    if domain == 'discrete':
        from .expression_definition import fold_discrete_gates
        value = fold_discrete_gates(value)
    value = sp.simplify(value)
    if value.has(sp.DiracDelta,ImpulseTrain,sp.Integral,sp.Sum,sp.Limit):raise ValueError('La expresión no es una función evaluable en muestras ordinarias.')
    if value.free_symbols-{variable}:raise ValueError('Asigná valores numéricos a los parámetros antes de crear muestras.')
    if domain=='discrete':
        lower=sp.simplify(parse(str(request['start'])));upper=sp.simplify(parse(str(request['stop'])))
        if lower.is_integer is not True or upper.is_integer is not True or lower.is_finite is not True or upper.is_finite is not True:raise ValueError('La ventana discreta requiere índices enteros finitos.')
        start,stop=int(lower),int(upper);count=stop-start+1;step=1
        if count<1:raise ValueError('El índice final debe ser mayor o igual al inicial.')
        if max(abs(start),abs(stop))>2**53:raise ValueError('Estos índices no se representan exactamente en la evaluación numérica.')
        ensure_working_set(count,live_arrays=16);grid=start+np.arange(count,dtype=np.int64)
    else:
        start=float(request['start']);stop=float(request['stop']);raw_count=request['count']
        if isinstance(raw_count,bool) or isinstance(raw_count,float) and not raw_count.is_integer():raise ValueError('La cantidad de puntos debe ser entera.')
        count=int(raw_count)
        if not np.isfinite([start,stop]).all() or stop<=start or count<2:raise ValueError('La ventana debe ser finita y creciente, con al menos dos puntos.')
        ensure_working_set(count,live_arrays=16);grid=np.linspace(start,stop,count);step=(stop-start)/(count-1)
        if np.any(np.diff(grid)<=0):raise ValueError('La rejilla excede la precisión temporal disponible.')
    from .singularities import sample_symbolic
    samples=sample_symbolic(value,variable,grid)
    if samples.ndim==0:samples=np.full(count,samples,dtype=complex)
    if samples.shape!=(count,) or not np.isfinite(samples).all():raise ValueError('La ventana incluye valores no finitos; no se sustituyen por cero.')
    with np.errstate(all='ignore'):
        density=samples.real**2+samples.imag**2
        energy=float(np.sum(density)) if domain=='discrete' else float(np.trapezoid(density,dx=step))
        average=energy/count if domain=='discrete' else energy/(stop-start)
    if not np.isfinite([energy,average]).all():raise ValueError('Las medidas numéricas exceden el rango finito; no representan divergencia matemática.')
    return {'operation':'signal_measures_window','samples':[[float(v.real),float(v.imag)] for v in samples],
        'origin':start,'step':step,'domain':domain,'energy':energy,'mean_square':average,'rms':math.sqrt(average),
        'method':'Suma sobre índices inclusivos' if domain=='discrete' else 'Cuadratura trapezoidal de |x(t)|²',
        'scope':'Sólo la ventana muestreada. No determina energía total ni potencia global de una expresión infinita.'}
