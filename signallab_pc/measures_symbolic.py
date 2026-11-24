"""Energía y potencia de expresiones, con resultados y límites explícitos."""
import math
import sympy as sp
from .resources import ensure_working_set


def measure_expression(request):
    from .symbolic import parse,T,N,W,S,Z
    from .cycle_measures import cycle_mean_square, discrete_cycle_mean_square, periodic_decay_energy
    from .periodic_signals import ImpulseTrain, PVCot, cycle_sum, discrete_cycle, wrapped_period
    from .periodic_support import split_periodic_support
    from .periodic_fourier import periodic_integral
    domain=request.get('domain','continuous');mode=request.get('mode','interval')
    if domain not in ('continuous','discrete') or mode not in ('interval','global','periodic'):raise ValueError('Dominio o alcance no admitido.')
    variable=T if domain=='continuous' else N
    source_value = value = parse(request['expression'])
    cycle_power = discrete_cycle_mean_square if domain == 'discrete' else cycle_mean_square
    if domain == 'discrete':
        from .expression_definition import fold_discrete_gates
        value = fold_discrete_gates(value)
    value = sp.simplify(value)
    if not isinstance(value,sp.Expr) or value.has(sp.DiracDelta,ImpulseTrain,PVCot,sp.oo,-sp.oo,sp.zoo,sp.nan):raise ValueError('La energía requiere una función ordinaria; no se eleva al cuadrado una distribución o un valor no finito.')
    if value.free_symbols.intersection({T,N,W,S,Z}-{variable}):raise ValueError('Usá sólo t para tiempo continuo o n para secuencias; las otras variables de dominio no son parámetros.')
    power_density=sp.simplify(value*sp.conjugate(value))
    def constant(text,integer=False):
        result=sp.simplify(parse(str(text)))
        if result.free_symbols or result.is_real is not True or result.is_finite is not True:raise ValueError('Los límites y el periodo deben ser constantes reales finitas.')
        if integer and result.is_integer is not True:raise ValueError('Los índices y periodos discretos deben ser enteros.')
        return result
    def unresolved(expression):return expression.has(sp.Sum,sp.Integral,sp.Limit)
    def simplify_measure(expression):
        return expression if unresolved(expression) else sp.simplify(expression)
    def accumulated(lower,upper,density=power_density):
        if lower.is_finite and upper.is_finite and density.has(sp.Mod) and not (lower.free_symbols or upper.free_symbols):
            total=bounded_modular_measure(lower,upper,density)
            if total is not None:return simplify_measure(total)
        if domain=='discrete':
            if lower.is_number and upper.is_number and lower.is_finite and upper.is_finite:ensure_working_set(int(upper-lower+1),bytes_per_sample=1024,live_arrays=8)
            if not (lower.free_symbols or upper.free_symbols) and density.has(sp.Piecewise):
                from .z_direct_pairs import pieces
                intervals = pieces(density, lower, upper)
                if intervals is not None:
                    return simplify_measure(sp.Add(*(sp.summation(value, (N, start, stop))
                                                for value, start, stop in intervals if value != 0)))
            # Separar en n<0 y n>=0 ayuda a conservar los soportes de Abs/Piecewise.
            if lower==-sp.oo and upper==sp.oo:
                return simplify_measure(sp.summation(density,(N,-sp.oo,-1))+sp.summation(density,(N,0,sp.oo)))
            return simplify_measure(sp.summation(density,(N,lower,upper)))
        from .continuous_algebra import nonnegative_integral
        return simplify_measure(nonnegative_integral(density,T,lower,upper))
    def bounded_modular_measure(lower,upper,density):
        from .jobs import checkpoint
        parts=split_periodic_support(density,variable) or [(density,lower,upper)]
        terms=[]
        for branch,begin,end in parts:
            checkpoint()
            start,stop=sp.Max(begin,lower),sp.Min(end,upper)
            if start>stop or domain=='continuous' and start==stop:
                continue
            if not branch.has(sp.Mod):
                terms.append(accumulated(start,stop,branch))
            elif domain=='continuous':
                area=periodic_integral(branch,variable,start,stop)
                if area is None:return None
                terms.append(area)
            else:
                wrapping=wrapped_period(branch,variable)
                if wrapping is not None and stop-start+1>=wrapping[0]:
                    terms.append(cycle_sum(discrete_cycle(branch,variable),start,stop))
                else:
                    ensure_working_set(int(stop-start+1),bytes_per_sample=1024,live_arrays=8)
                    samples=[]
                    for position in range(int(start),int(stop+1)):
                        checkpoint()
                        sample=sp.simplify(branch.subs(variable,position))
                        if sample.has(sp.nan,sp.zoo,sp.oo,-sp.oo):
                            raise ValueError(f'La secuencia no tiene una muestra finita en n = {position}.')
                        samples.append(sample)
                    terms.append(sp.Add(*samples))
        return sp.Add(*terms)
    def state(expression):
        if expression.has(sp.nan,sp.zoo) or isinstance(expression,sp.AccumBounds):return 'undefined'
        if expression==sp.oo:return 'divergent'
        if unresolved(expression):return 'unevaluated'
        if expression.has(sp.Piecewise) or expression.free_symbols:return 'conditional'
        if expression.is_real is True and expression.is_nonnegative is True and expression.is_finite is True:return 'finite'
        return 'undetermined'
    def record(expression,*,convergent=False):
        status=state(expression);data={'exact':str(expression),'status':'convergent' if status=='unevaluated' and convergent else status}
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
    def cycle_energy(cycle,first,density):
        if domain=='discrete' and density.has(sp.Mod):
            sequence=discrete_cycle(density,variable)
            if sequence is not None:
                samples=sequence[1]
                return sp.Add(*samples)*(cycle/len(samples))
        return accumulated(first,first+cycle-(1 if domain=='discrete' else 0),density)
    def gated_periodic_measures():
        parts=split_periodic_support(source_value,variable,preserve_addends=True)
        if parts is None:return None
        tail_means=[]
        finite_areas=[]
        zero_tail_energy_certified=True
        for branch,lo,hi in parts:
            density = sp.simplify(branch*sp.conjugate(branch))
            if lo.is_finite and hi.is_finite:
                area=accumulated(lo,hi,density)
                if state(area)!='finite':return None
                finite_areas.append(area)
                continue
            if not density.has(variable):
                mean=density
            else:
                cycle=wrapped_period(density,variable)
                if cycle is not None:
                    period,start,base=cycle
                    mean=simplify_measure(cycle_energy(period,start,base)/period)
                else:
                    direction=1 if lo.is_finite else -1
                    mean=(cycle_power(branch,variable,tail=direction) if branch.has(sp.Mod)
                          else harmonic_power(branch,variable,tail=direction))
                    # An exponentially decaying tail can have finite nonzero energy.
                    zero_tail_energy_certified=False
            if mean is None or state(mean)!='finite':return None
            tail_means.append(mean)
        if len(tail_means)!=2:return None
        power=sp.simplify(sp.Add(*tail_means)/2)
        if power.is_positive is True:return sp.oo,power
        if power==0 and zero_tail_energy_certified:return sp.Add(*finite_areas),power
        return None
    def sinc_band_energy():
        if domain!='discrete' or not source_value.has(sp.sin,sp.cos):
            return None
        if not any(factor.exp.is_negative is True and factor.base.has(N)
                   for factor in source_value.atoms(sp.Pow)):
            return None
        from .dtft_pairs import direct
        from .fourier_bands import discrete_band_energy
        spectrum = direct(source_value)
        return discrete_band_energy(spectrum,W) if spectrum is not None else None
    wrapping=wrapped_period(value if mode=='periodic' else power_density,variable) if mode!='interval' else None
    interval_energy=None;period_verified=False;energy_converges=False
    if mode=='interval':
        lower=constant(request.get('lower','0'),domain=='discrete');upper=constant(request.get('upper','1'),domain=='discrete')
        if upper<lower or domain=='continuous' and upper==lower:raise ValueError('El intervalo debe ser creciente; en discreto puede contener un único índice.')
        measure=upper-lower+(1 if domain=='discrete' else 0)
        energy=accumulated(lower,upper);power=simplify_measure(energy/measure)
        scope='Promedio sobre el intervalo indicado; no es la potencia media de toda la señal. Los índices discretos incluyen ambos extremos.'
        classification='Medidas del intervalo; sin clasificación global'
    elif mode=='periodic':
        from .signal_period import expression_period
        detected=expression_period(source_value,variable)
        raw_period=request.get('period')
        declared=str(raw_period).strip() if raw_period is not None else ''
        if not declared and detected == 0:
            from .signal_period import formula_period
            detected=formula_period(request['expression'],domain)
        if not declared and not detected:
            raise ValueError('No se pudo detectar un período. Ingresá el período de la señal.')
        period=constant(declared,domain=='discrete') if declared else detected
        if period.is_positive is not True:raise ValueError('El periodo debe ser positivo.')
        if wrapping is not None and (period/wrapping[0]).is_integer is True:
            cycle, lower, one_period=wrapping
            density=sp.simplify(one_period*sp.conjugate(one_period))
            upper=lower+period-(1 if domain=='discrete' else 0)
            interval_energy=cycle_energy(cycle,lower,density)*(period/cycle)
        else:
            if detected is None or (detected != 0 and (period/detected).is_integer is not True):
                residual=sp.trigsimp(sp.simplify(value.subs(variable,variable+period)-value))
                if residual!=0:raise ValueError('No se pudo demostrar que el período indicado repita la expresión. Revisá el período o usá el análisis global.')
            lower=sp.Integer(0);upper=period-1 if domain=='discrete' else period
            interval_energy=accumulated(lower,upper)
        period_verified=True;power=simplify_measure(interval_energy/period)
        energy=energy_from_mean(power)
        scope='Periodicidad demostrada para el periodo indicado. Promedio calculado en un periodo; energía total sobre todo el eje.'
        classification=None
    else:
        from .harmonic_measures import exponential_energy, harmonic_power, piecewise_harmonic_power, rational_tail_measures
        from .oscillatory_measures import oscillatory_measures

        lower,upper=-sp.oo,sp.oo
        power=harmonic_power(value,variable) if wrapping is None else None
        discrete_period = None
        if domain == 'discrete' and wrapping is None and power is None and value.has(sp.Mod,sp.Piecewise):
            from .signal_period import expression_period
            period = expression_period(value,variable)
            if period is not None and period.is_Integer and period>0:
                discrete_period = period
        if wrapping is not None:
            cycle,first,density=wrapping
            power=simplify_measure(cycle_energy(cycle,first,density)/cycle)
            energy=energy_from_mean(power)
            scope='La definición se repite en todo el eje. La potencia se calcula sobre un período completo.'
        elif power is not None:
            energy=energy_from_mean(power)
            scope='Se agrupan las componentes con la misma frecuencia antes de calcular su potencia.'
            if domain=='discrete':scope+=' Las frecuencias separadas por un múltiplo de 2π representan la misma secuencia.'
        elif discrete_period is not None:
            from .jobs import checkpoint
            ensure_working_set(int(discrete_period),bytes_per_sample=1024,live_arrays=8)
            total = sp.S.Zero
            for index in range(int(discrete_period)):
                checkpoint()
                total += power_density.subs(variable,index)
            power = sp.simplify(total/discrete_period)
            energy = energy_from_mean(power)
            scope='Se demostraron los períodos de los tramos y se evaluaron todos los índices de un ciclo común.'
        elif (power:=cycle_power(source_value,variable)) is not None:
            energy=energy_from_mean(power)
            scope=('Se promedian los productos de las componentes que comparten frecuencias en su ciclo común. '
                   'Entre dos grupos de períodos inconmensurables, los productos se promedian usando sus valores medios.'
                   if domain=='continuous' else 'Los tonos se comparan con los armónicos del ciclo. '
                   'Sólo las frecuencias que coinciden salvo múltiplos de 2π aportan términos cruzados.')
        elif (gated:=gated_periodic_measures()) is not None:
            energy,power=gated
            scope='Los cambios de soporte separan las colas del tramo finito. La potencia global promedia las potencias de ambas colas. Si las dos son nulas, la energía se suma en el tramo restante.'
        elif (tails:=piecewise_harmonic_power(value,variable,accumulated)) is not None and tails.is_positive is True:
            power=tails;energy=sp.oo
            scope='Se calcula la potencia de cada cola armónica y se promedian las dos mitades del eje.'
        elif (energy:=periodic_decay_energy(source_value,variable,accumulated)) is not None:
            power=sp.S.Zero
            scope='Se integra o suma un ciclo de cada cola y se acumulan las repeticiones con su factor de decaimiento. La energía es finita y la potencia media vale cero.'
        elif (energy:=exponential_energy(power_density,variable,accumulated)) is not None:
            power=sp.S.Zero
            scope='La energía se obtiene sumando los aportes de decaimiento exponencial. Como es finita, la potencia media vale cero.'
        elif (energy:=sinc_band_energy()) is not None:
            power=sp.S.Zero
            scope='La identidad de Parseval integra el módulo al cuadrado de la DTFT exacta en un período.'
        elif (asymptotic:=rational_tail_measures(power_density,variable)) is not None:
            energy,power=asymptotic
            scope='La energía diverge. El promedio simétrico se determina por los límites de la densidad o por sus polos no integrables.'
        elif (oscillatory:=oscillatory_measures(power_density,variable)) is not None:
            power,energy,energy_converges=oscillatory
            if energy is None:
                aggregate=sp.Sum if domain=='discrete' else sp.Integral
                energy=aggregate(power_density,(variable,lower,upper))
                if power_density.is_rational_function(variable):
                    try:energy=accumulated(lower,upper)
                    except (NotImplementedError,RecursionError):pass
            scope='El promedio se obtiene de la componente constante de la densidad en cada semieje. Las componentes oscilatorias con amplitud acotada tienen promedio nulo cuando su frecuencia efectiva es distinta de cero.'
            if energy_converges and unresolved(energy):
                scope+=' El decaimiento de la densidad certifica que la energía total es finita.'
        else:
            aggregate=sp.Sum if domain=='discrete' else sp.Integral
            try:energy=accumulated(lower,upper)
            except (NotImplementedError,RecursionError):energy=aggregate(power_density,(variable,lower,upper))
            if state(energy)=='finite':power=sp.S.Zero
            else:
                limit_variable=sp.Symbol('M',positive=True,integer=True) if domain=='discrete' else sp.Symbol('R',positive=True)
                try:area=accumulated(-limit_variable,limit_variable)
                except (NotImplementedError,RecursionError):area=aggregate(power_density,(variable,-limit_variable,limit_variable))
                average=area/(2*limit_variable+(1 if domain=='discrete' else 0))
                power=sp.Limit(average,limit_variable,sp.oo)
                if not unresolved(area):
                    try:power=simplify_measure(power.doit())
                    except (NotImplementedError,ValueError,TypeError,RecursionError):pass
            scope='La energía abarca todo el eje. La potencia usa el límite del promedio en ventanas simétricas crecientes.'
        classification=None
    if classification is None:
        if energy==0:classification='Energía nula'
        elif state(energy)=='finite' and energy.is_positive is True or energy_converges and unresolved(energy):classification='Señal de energía'
        elif state(power)=='finite' and power.is_positive is True:classification='Señal de potencia'
        elif energy==sp.oo and power in (0,sp.oo):classification='Ni señal de energía ni de potencia finita'
        else:classification='Clasificación no determinada; revisar condiciones o resultados pendientes'
    rms=sp.sqrt(power)
    result={'operation':'signal_measures_expression','domain':domain,'mode':mode,'expression':request['expression'],'resolved_expression':str(value),
        'energy':record(energy,convergent=energy_converges),'mean_square':record(power),'rms':record(rms),'classification':classification,'scope':scope,
        'power_density':str(power_density),'bounds':[str(lower),str(upper)],'period_verified':period_verified,
        'convention':'E=sum |x[n]|^2; P=lim M→∞ sum(n=-M..M) |x[n]|^2/(2M+1)' if domain=='discrete' else 'E=integral |x(t)|^2 dt; P=lim R→∞ integral(-R..R) |x(t)|^2 dt/(2R)',
        'parameters':sorted(str(p) for p in value.free_symbols-{variable})}
    if interval_energy is not None:result['period_energy']=record(interval_energy);result['period']=str(period)
    return result


def sample_measure_expression(request):
    """Ventana numérica explícita, incluso si la definición tiene soporte infinito."""
    import numpy as np
    from .symbolic import parse,T,N
    from .periodic_signals import ImpulseTrain,PVCot
    domain=request.get('domain','continuous')
    if domain not in ('continuous','discrete'):raise ValueError('Dominio no admitido.')
    variable = T if domain == 'continuous' else N
    value = parse(request['expression'])
    if domain == 'discrete':
        from .expression_definition import fold_discrete_gates
        value = fold_discrete_gates(value)
    value = sp.simplify(value)
    if value.has(sp.DiracDelta,ImpulseTrain,PVCot,sp.Integral,sp.Sum,sp.Limit):raise ValueError('La expresión no es una función evaluable en muestras ordinarias.')
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
