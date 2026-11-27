"""Real causal AR/MA/ARMA models driven by white Gaussian innovations."""
from dataclasses import dataclass
import warnings
import numpy as np
from scipy import signal as sp, linalg
from .communications_data import integer, real
from .execution import ExecutionContext
from .filters import Transfer, positive_integer
from .model import Signal
from .resources import ensure_working_set


@dataclass
class ModelAnalysis:
    system: Transfer
    noise_mean: float
    noise_variance: float
    mean: float
    variance: float
    radius: float
    A: np.ndarray
    B: np.ndarray
    covariance: np.ndarray
    signals: list
    fit: dict | None = None


def analyze(b, a, noise_mean=0, noise_std=1, max_lag=40, points=2049, *, execution=None):
    """Compute stationary moments and spectra with shared resource admission."""
    max_lag=positive_integer(max_lag+1,'Cantidad de retardos')-1
    points=positive_integer(points,'Puntos espectrales')
    if points<3:
        raise ValueError('Usá al menos tres puntos para el espectro.')
    noise_mean=real(noise_mean,'Media del ruido')
    noise_std=real(noise_std,'Desviación del ruido',minimum=0)
    system=Transfer(b,a,name='Modelo ARMA')
    if np.any(system.b.imag) or np.any(system.a.imag):
        raise ValueError('Este modelo requiere coeficientes reales.')
    b=system.b.real;a=system.a.real
    # Drop trailing zero coefficients, not delays at the beginning of b.
    b=np.trim_zeros(b,'b') if np.any(b) else np.array([0.])
    a=np.trim_zeros(a,'b');system=Transfer(b,a,name='Modelo ARMA');order=max(len(b),len(a))-1
    estimate=ensure_working_set(int(order*order+points+2*max_lag+1),live_arrays=18)
    context=execution or ExecutionContext()
    with context.reserve(estimate):
        return _stationary_analysis(system, noise_mean, noise_std, max_lag, points, context)


def _stationary_analysis(system, noise_mean, noise_std, max_lag, points, context):
    b,a=system.b.real,system.a.real
    order=max(len(b),len(a))-1
    poles=np.roots(a);radius=float(np.max(abs(poles))) if len(poles) else 0.
    if radius>=1-64*np.finfo(float).eps:
        raise ValueError('El modelo causal estacionario requiere todos los polos dentro del círculo unidad. Revisá a; un polo en 1 produce un proceso no estacionario.')
    var=float(noise_std*noise_std)
    if not np.isfinite(var) or (var==0 and noise_std>0):
        raise ValueError('La varianza del ruido queda fuera del rango numérico.')
    with np.errstate(over='ignore',invalid='ignore',divide='ignore'):
        mean=float(noise_mean*np.sum(b)/np.sum(a))
    if not np.isfinite(mean):
        raise ValueError('La media estacionaria no es representable con estos coeficientes.')
    bp=np.pad(b,(0,order+1-len(b)));ap=np.pad(a,(0,order+1-len(a)))
    D=float(bp[0])
    scaled_feedthrough=noise_std*D
    if not np.isfinite(scaled_feedthrough):
        raise ValueError('La ganancia instantánea sobre el ruido queda fuera del rango numérico.')
    if order:
        A=np.diag(np.ones(order-1),1);A[:,0]-=ap[1:]
        B=bp[1:]-ap[1:]*D
        magnitude=np.abs(B[B!=0])
        limits=np.finfo(float)
        scaled_outer=(0<var<limits.tiny or np.any(magnitude>np.sqrt(limits.max))
                      or np.any(magnitude<np.sqrt(limits.tiny)))
        with np.errstate(over='ignore',invalid='ignore'):
            scaled_input=noise_std*B
            Q=np.outer(scaled_input,scaled_input) if scaled_outer else var*np.outer(B,B)
        if not np.isfinite(Q).all():
            raise ValueError('La covarianza de la innovación del estado queda fuera del rango numérico.')
        with warnings.catch_warnings():
            warnings.simplefilter('error',linalg.LinAlgWarning)
            try:P=linalg.solve_discrete_lyapunov(A,Q)
            except (ValueError,linalg.LinAlgError,linalg.LinAlgWarning) as exc:
                raise ValueError('No se pudo obtener una covarianza estacionaria fiable. Revisá el orden y los polos cercanos a 1.') from exc
        P=(P+P.T)/2
        if not np.isfinite(P).all():
            raise ValueError('La covarianza estacionaria excede el rango numérico.')
        eigen,vectors=np.linalg.eigh(P)
        tol=1024*np.finfo(float).eps*max(1,order)*max(np.max(abs(eigen)),np.finfo(float).tiny)
        if np.min(eigen)<-tol:
            raise ValueError('La covarianza calculada no es semidefinida positiva; el modelo está mal condicionado.')
        P=(vectors*np.maximum(eigen,0))@vectors.T
        residual=A@P@A.T-P+Q
        if np.linalg.norm(residual)>1e-8*max(np.linalg.norm(P),np.linalg.norm(Q),np.finfo(float).tiny):
            raise ValueError('La solución de la covarianza no tiene precisión suficiente para este modelo.')
        gamma=np.empty(max_lag+1);gamma[0]=P[0,0]+scaled_feedthrough*scaled_feedthrough
        state=A@P[:,0]+scaled_input*scaled_feedthrough
        for k in range(1,max_lag+1):
            if k%256==0:context.checkpoint()
            gamma[k]=state[0];state=A@state
    else:
        A=np.empty((0,0));B=np.empty(0);P=np.empty((0,0))
        gamma=np.zeros(max_lag+1);gamma[0]=scaled_feedthrough*scaled_feedthrough
    if not np.isfinite(gamma).all() or gamma[0]<0:
        raise ValueError('La covarianza del modelo no es representable.')
    system.name='Modelo '+('AR' if len(a)>1 and len(b)==1 else 'MA' if len(a)==1 else 'ARMA')
    cov=np.r_[gamma[:0:-1],gamma];cor=cov+mean*mean
    w=np.linspace(-np.pi,np.pi,points)
    with np.errstate(over='ignore',invalid='ignore'):
        driven=Transfer(noise_std*b,a)
        psd=abs(driven.response(w))**2
    if not np.isfinite(psd).all() or not np.isfinite(cor).all():
        raise ValueError('El espectro o la correlación exceden el rango numérico.')
    meta={'model':'real causal ARMA','theoretical':True,'noise_mean':float(noise_mean),'noise_variance':var,'process_mean':mean,'process_variance':float(gamma[0])}
    signals=[Signal(cov,-max_lag,1,'retardo k','Autocovarianza teórica','discrete',metadata={**meta,'operation':'model_autocovariance'}),
             Signal(cor,-max_lag,1,'retardo k','Autocorrelación teórica','discrete',metadata={**meta,'operation':'model_autocorrelation'}),
             Signal(psd,-np.pi,2*np.pi/(points-1),'rad/muestra','Densidad de potencia de x−media','frequency',metadata={**meta,'operation':'spectral_density','density_units':'amplitud²','convention':'C[k]=(1/(2*pi))*integral_{-pi}^{pi} S_c(w)*exp(j*w*k) dw; mean line excluded','dc_line_weight':float(2*np.pi*mean*mean)})]
    context.checkpoint()
    return ModelAnalysis(system,float(noise_mean),var,mean,float(gamma[0]),radius,A,B,P,signals)


def realization(model, count, seed, origin=0, *, initialization='stationary', initial_state=None,
                warm_up=0, execution=None):
    """Simulate the centered direct-form II transposed recursion and restore its mean."""
    count = positive_integer(count, 'Cantidad de muestras')
    seed = integer(seed, 'Semilla', minimum=0)
    warm_up = integer(warm_up, 'Muestras de calentamiento', minimum=0)
    if initialization not in ('stationary', 'rest', 'manual'):
        raise ValueError('Elegí estado estacionario, reposo o estado manual.')
    if (initial_state is not None) != (initialization == 'manual'):
        raise ValueError('Cargá el vector de estado únicamente para la inicialización manual.')
    order = len(model.B)
    context = execution or ExecutionContext()
    block_size = 32768
    total = count + warm_up
    estimate = 40*count + 64*min(total, block_size) + 96*order**2
    with context.reserve(estimate):
        rng = np.random.Generator(np.random.PCG64(seed))
        state = np.zeros(order)
        starting_state = None
        if initialization == 'manual':
            entries = np.asarray(initial_state)
            if (entries.shape != (order,) or entries.dtype.kind not in 'iuf'
                    or not np.isfinite(entries).all()):
                raise ValueError(f'El vector de estado debe tener {order} componentes reales finitas.')
            state = entries.astype(float)
            if not np.isfinite(state).all():
                raise ValueError('El vector de estado excede el rango representable.')
            starting_state = state.tolist()
        elif initialization == 'stationary' and order:
            eig, vec = np.linalg.eigh(model.covariance)
            state = (vec*np.sqrt(np.maximum(eig,0))) @ rng.standard_normal(order)
        values = np.empty(count)
        b, a = model.system.b.real, model.system.a.real
        sigma = np.sqrt(model.noise_variance)
        for start in range(0, total, block_size):
            context.checkpoint(95*start//total)
            stop = min(start+block_size, total)
            noise = rng.normal(0, sigma, stop-start)
            with np.errstate(over='ignore', invalid='ignore'):
                if order:
                    block, state = sp.lfilter(b, a, noise, zi=state)
                else:
                    block = b[0]*noise
                block += model.mean
            if not (np.isfinite(block).all() and np.isfinite(state).all()):
                raise FloatingPointError('La realización ARMA excede el rango numérico.')
            first = max(start, warm_up)
            if first < stop:
                values[first-warm_up:stop-warm_up] = block[first-start:]
        metadata = {
            'operation': 'stationary_arma_realization' if initialization == 'stationary' else 'arma_realization',
            'seed': seed, 'generator': 'PCG64', 'numpy_version': np.__version__,
            'theoretical_mean': model.mean, 'theoretical_variance': model.variance,
            'initialization': ('Gaussian stationary state covariance from discrete Lyapunov; not initial rest'
                               if initialization == 'stationary' else 'Centered direct form II transposed state'),
            'initialization_mode': initialization, 'warm_up_samples': warm_up,
            'statistics_scope': 'stationary' if initialization == 'stationary' else 'stationary_limit',
            'noise_mean': model.noise_mean, 'noise_variance': model.noise_variance,
        }
        if starting_state is not None:
            metadata['initial_state'] = starting_state
        result = Signal(values, origin, 1, 'n', 'Realización '+model.system.name, 'discrete', metadata=metadata)
        from .system_clock import input_metadata
        result.metadata = input_metadata(model.system, result)
        context.checkpoint(100)
    return result


def model_pacf(model):
    """PACF of the stationary covariance already calculated by analyze."""
    from .system_clock import lag_clock
    from .time_series_identification import partial_autocorrelation
    covariance = next(value for value in model.signals if value.metadata.get('operation') == 'model_autocovariance')
    center = -covariance.origin
    values = partial_autocorrelation(covariance.values[center:])
    period = model.system.sample_period_s
    clock = lag_clock(None if period is None else 1/period,0,len(values))
    return Signal(values, 0, 1, 'retardo k', 'Autocorrelación parcial teórica', 'discrete',
                  metadata={'operation': 'model_pacf', 'model': model.system.name, 'theoretical': True, **clock})


def sensitivity(model, parameter, values, *, index=None, execution=None):
    """Compare changes to one parameter on the stationary model's spectral grid."""
    from .result_summary import number

    b, a = model.system.b.real, model.system.a.real
    if parameter in ('b','a'):
        coefficients = b if parameter == 'b' else a
        index = integer(index, 'Índice del coeficiente', minimum=int(parameter == 'a'),
                        maximum=len(coefficients)-1)
        label = f'{parameter}[{index}]'
        original = float(coefficients[index])
    elif parameter in ('noise_mean','noise_std') and index is None:
        label = 'Media de e[n]' if parameter == 'noise_mean' else 'Desviación de e[n]'
        original = model.noise_mean if parameter == 'noise_mean' else float(np.sqrt(model.noise_variance))
    else:
        raise ValueError('Elegí un coeficiente o un parámetro de las innovaciones.')
    values = tuple(dict.fromkeys(real(value, 'Valor para comparar') for value in values))
    if not values:
        raise ValueError('Ingresá al menos un valor para comparar.')
    covariance, _, reference = model.signals[:3]
    context = execution or ExecutionContext()
    lag, points = int(-covariance.origin), reference.values.size
    rows, curves = [], []
    with context.reserve(int(128*len(values)*points)):
        for position, value in enumerate(values):
            context.checkpoint(95*position//len(values))
            name = f'{label} = {number(value)}'
            options = {'b':b.copy(), 'a':a.copy(), 'noise_mean':model.noise_mean,
                       'noise_std':np.sqrt(model.noise_variance), 'max_lag':lag, 'points':points}
            if parameter in ('b','a'):
                options[parameter][index] = value
            else:
                options[parameter] = value
            try:
                variant = analyze(**options,execution=context)
            except ValueError as error:
                rows.append({'label':name,'value':value,'error':str(error)})
                continue
            curve = variant.signals[2]
            curve.name = name
            curve.metadata.update(sensitivity_parameter=parameter,sensitivity_index=index,
                                  sensitivity_value=value,sensitivity_reference=original)
            curves.append(curve)
            rows.append({'label':name,'value':value,'mean':variant.mean,'variance':variant.variance,
                         'pole_radius':variant.radius})
        context.checkpoint(100)
    return {'parameter':label,'reference':original,'rows':tuple(rows),'spectra':tuple(curves)}


def store_analysis(project, model, signals, report, *, parents=(), tool=None, execution=None):
    """Deliver the model, report and all requested records in one transaction."""
    from .operation_provenance import content_digest, settings_digest

    context = execution or ExecutionContext()
    check = context.checkpoint
    parents = tuple(dict.fromkeys(parents))
    parent_hashes = tuple(content_digest(project.get(key),check) for key in parents)
    model_hash = content_digest(model.system,check)
    signal_hashes = tuple(content_digest(value,check) for value in signals)
    with project.stage_records(before_commit=check) as staged:
        system_id = staged.add(model.system,operation='Modelo de proceso aleatorio',parents=parents,tool=tool,
                               verification=(model_hash,parent_hashes,check))
        record_ids = tuple(staged.add(value,operation=value.name,parents=(system_id,*parents),tool=tool,
                                      verification=(stamp,(model_hash,*parent_hashes),check))
                           for value,stamp in zip(signals,signal_hashes,strict=True))
        report_id = staged.add(report,title=model.system.name,operation='Análisis de proceso aleatorio',
                               parents=(system_id,*record_ids),tool=tool,
                               verification=(settings_digest(['calculation',report]),(model_hash,*signal_hashes),check))
    return system_id,record_ids,report_id


def fit_ar(source,order,max_lag=40,points=2049):
    """Yule-Walker, biased sample covariance, estimated mean, real data."""
    if source.domain!='discrete' or np.any(source.values.imag):
        raise ValueError('La estimación AR requiere un registro discreto real.')
    order=positive_integer(order,'Orden AR');n=len(source.values)
    if order>=n:
        raise ValueError('El orden AR debe ser menor que la cantidad de muestras.')
    ensure_working_set(int(2*n+order*order+points),live_arrays=16)
    scale=float(np.max(abs(source.values.real)))
    if scale==0:
        raise ValueError('Un registro constante no permite estimar este modelo AR.')
    normalized=source.values.real/scale;mean_scaled=float(np.mean(normalized));centered=normalized-mean_scaled
    cov=sp.correlate(centered,centered,mode='full',method='fft')[n-1:n+order]/n
    cov[0]=np.mean(centered*centered)
    if cov[0]<=0:
        raise ValueError('Un registro constante no permite estimar este modelo AR.')
    try:coeff=linalg.solve_toeplitz(cov[:order],-cov[1:order+1])
    except linalg.LinAlgError as exc:raise ValueError('Las ecuaciones AR son singulares; reducí el orden o revisá el registro.') from exc
    residual=np.dot(linalg.toeplitz(cov[:order]),coeff)+cov[1:order+1]
    if not np.isfinite(coeff).all() or np.linalg.norm(residual)>1e-9*max(np.linalg.norm(cov),np.finfo(float).tiny):
        raise ValueError('El ajuste AR está mal condicionado; reducí el orden.')
    error=float(cov[0]+np.dot(coeff,cov[1:]))
    if error<=0:
        raise ValueError('La varianza de innovación estimada no es positiva; reducí el orden.')
    mean=mean_scaled*scale;variance=error*scale*scale;a=np.r_[1.,coeff]
    if not np.isfinite([mean,variance]).all() or variance==0:
        raise ValueError('Las estadísticas del ajuste quedan fuera del rango numérico.')
    model=analyze([1],a,mean*float(np.sum(a)),float(np.sqrt(variance)),max_lag,points)
    errors=sp.lfilter(a,[1],centered)[order:]*scale
    model.system.name='Modelo AR('+str(order)+') estimado'
    error_signal=Signal(errors,source.origin+order,1,'n','Innovación estimada (tramo válido)','discrete',metadata={'operation':'estimated_ar_innovations','model_order':order,'input_samples':n,'scope':'Primeras p muestras excluidas; resto con p antecedentes observados. No prueba blancura ni independencia.'})
    model.fit={'order':order,'input_samples':n,'estimated_mean':mean,'innovation_variance':variance,'residual_mean_square':float(np.mean(errors*errors)),'covariance_divisor':'N','method':'Yule-Walker with estimated sample mean','mean_interpretation':'El modelo describe x−media; la media se repone al generar.','source_origin':int(source.origin)}
    rate=source.metadata.get('sample_rate_hz')
    if rate is not None:
        if not np.isfinite(rate) or rate<=0:
            raise ValueError('La tasa de muestreo del registro debe ser positiva y finita.')
        from .system_clock import validate_period
        model.system.sample_period_s=validate_period(1/float(rate))
        error_signal.metadata['sample_rate_hz']=float(rate)
        if 'time_start_s' in source.metadata:error_signal.metadata['time_start_s']=float(source.metadata['time_start_s'])+order/float(rate)
    model.signals.append(error_signal)
    return model


def summary(model):
    from .result_summary import Formula,Section,Summary,number
    from .phase_summary import transfer_formula
    system=model.system;terms=[]
    for k,value in enumerate(-system.a[1:].real,1):
        if value:terms.append(('' if value==1 else '-' if value==-1 else '('+number(value)+')*')+'x[n-'+str(k)+']')
    for k,value in enumerate(system.b.real):
        if value:terms.append(('' if value==1 else '-' if value==-1 else '('+number(value)+')*')+'e['+('n-'+str(k) if k else 'n')+']')
    equation='x[n] = '+('+'.join(terms) if terms else '0')
    formulas=[transfer_formula(system)[0]]
    if len(equation)<850:formulas.insert(0,Formula(equation,equation,numeric=True))
    sections=[Section('Modelo calculado',paragraphs=['e[n] representa las innovaciones gaussianas independientes.'],formulas=formulas),
        Section('Estadísticas del proceso estacionario',rows=[('Media del ruido e[n]',number(model.noise_mean)),('Varianza del ruido',number(model.noise_variance)),('Media de x[n]',number(model.mean)),('Varianza de x[n]',number(model.variance)),('Valor cuadrático medio',number(model.variance+model.mean**2)),('Mayor módulo de polo',number(model.radius))],formulas=[Formula('R[k] = C[k]' + (' + ('+number(model.mean)+')^2' if model.mean else ''),'R[k] = C[k] + media²',numeric=True)]),
        Section('Alcance de las estadísticas',paragraphs=['La correlación y la densidad corresponden al modelo estacionario. La densidad describe las fluctuaciones alrededor de la media.'])]
    if model.mean:
        sections.append(Section('Línea de la media',rows=[('Frecuencia', '0 rad/muestra')],paragraphs=['La línea se registra por separado de la densidad de las fluctuaciones.']))
    if model.fit:
        fit=model.fit
        sections.insert(1,Section('Estimación desde el registro',rows=[('Método','Yule–Walker'),('Orden AR',str(fit['order'])),('Muestras observadas',str(fit['input_samples'])),('Media estimada',number(fit['estimated_mean'])),('Varianza de innovación estimada',number(fit['innovation_variance'])),('Media cuadrática del residuo válido',number(fit['residual_mean_square']))]))
    return Summary(system.name,sections)
