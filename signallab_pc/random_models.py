"""Real causal AR/MA/ARMA models driven by white Gaussian innovations."""
from dataclasses import dataclass
import warnings
import numpy as np
from scipy import signal as sp, linalg
from .filters import Transfer, positive_integer
from .model import Signal
from .resources import ensure_working_set
from .jobs import checkpoint


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


def analyze(b, a, noise_mean=0, noise_std=1, max_lag=40, points=2049):
    max_lag=positive_integer(max_lag+1,'Cantidad de retardos')-1
    points=positive_integer(points,'Puntos espectrales')
    if points<3:raise ValueError('Usá al menos tres puntos para el espectro.')
    if not np.isfinite([noise_mean,noise_std]).all() or noise_std<0:
        raise ValueError('La media debe ser finita y la desviación del ruido no negativa.')
    system=Transfer(b,a,name='Modelo ARMA')
    if np.any(system.b.imag) or np.any(system.a.imag):raise ValueError('Este modelo requiere coeficientes reales.')
    b=system.b.real;a=system.a.real
    # Drop trailing zero coefficients, not delays at the beginning of b.
    b=np.trim_zeros(b,'b') if np.any(b) else np.array([0.])
    a=np.trim_zeros(a,'b');system=Transfer(b,a,name='Modelo ARMA');order=max(len(b),len(a))-1
    ensure_working_set(int(order*order+points+2*max_lag+1),live_arrays=18)
    poles=np.roots(a);radius=float(np.max(abs(poles))) if len(poles) else 0.
    if radius>=1-64*np.finfo(float).eps:
        raise ValueError('El modelo causal estacionario requiere todos los polos dentro del círculo unidad. Revisá a; un polo en 1 produce un proceso no estacionario.')
    var=float(noise_std*noise_std)
    if not np.isfinite(var):raise ValueError('La varianza del ruido excede el rango numérico.')
    with np.errstate(over='ignore',invalid='ignore',divide='ignore'):
        mean=float(noise_mean*np.sum(b)/np.sum(a))
    if not np.isfinite(mean):raise ValueError('La media estacionaria no es representable con estos coeficientes.')
    bp=np.pad(b,(0,order+1-len(b)));ap=np.pad(a,(0,order+1-len(a)))
    D=bp[0]
    if order:
        A=np.diag(np.ones(order-1),1);A[:,0]-=ap[1:]
        B=bp[1:]-ap[1:]*D
        Q=var*np.outer(B,B)
        with warnings.catch_warnings():
            warnings.simplefilter('error',linalg.LinAlgWarning)
            try:P=linalg.solve_discrete_lyapunov(A,Q)
            except (ValueError,linalg.LinAlgError,linalg.LinAlgWarning) as exc:
                raise ValueError('No se pudo obtener una covarianza estacionaria fiable. Revisá el orden y los polos cercanos a 1.') from exc
        P=(P+P.T)/2
        if not np.isfinite(P).all():raise ValueError('La covarianza estacionaria excede el rango numérico.')
        eigen,vectors=np.linalg.eigh(P)
        tol=1024*np.finfo(float).eps*max(1,order)*max(np.max(abs(eigen)),np.finfo(float).tiny)
        if np.min(eigen)<-tol:raise ValueError('La covarianza calculada no es semidefinida positiva; el modelo está mal condicionado.')
        P=(vectors*np.maximum(eigen,0))@vectors.T
        residual=A@P@A.T-P+Q
        if np.linalg.norm(residual)>1e-8*max(np.linalg.norm(P),np.linalg.norm(Q),np.finfo(float).tiny):
            raise ValueError('La solución de la covarianza no tiene precisión suficiente para este modelo.')
        gamma=np.empty(max_lag+1);gamma[0]=P[0,0]+var*D*D
        state=A@P[:,0]+B*(var*D)
        for k in range(1,max_lag+1):
            if k%256==0:checkpoint(k/max(1,max_lag))
            gamma[k]=state[0];state=A@state
    else:
        A=np.empty((0,0));B=np.empty(0);P=np.empty((0,0))
        gamma=np.zeros(max_lag+1);gamma[0]=var*D*D
    if not np.isfinite(gamma).all() or gamma[0]<0:raise ValueError('La covarianza del modelo no es representable.')
    system.name='Modelo '+('AR' if len(a)>1 and len(b)==1 else 'MA' if len(a)==1 else 'ARMA')
    cov=np.r_[gamma[:0:-1],gamma];cor=cov+mean*mean
    w=np.linspace(-np.pi,np.pi,points)
    with np.errstate(over='ignore',invalid='ignore'):
        psd=var*abs(system.response(w))**2
    if not np.isfinite(psd).all() or not np.isfinite(cor).all():raise ValueError('El espectro o la correlación exceden el rango numérico.')
    meta={'model':'real causal ARMA','theoretical':True,'noise_mean':float(noise_mean),'noise_variance':var,'process_mean':mean,'process_variance':float(gamma[0])}
    signals=[Signal(cov,-max_lag,1,'retardo k','Autocovarianza teórica','discrete',metadata={**meta,'operation':'model_autocovariance'}),
             Signal(cor,-max_lag,1,'retardo k','Autocorrelación teórica','discrete',metadata={**meta,'operation':'model_autocorrelation'}),
             Signal(psd,-np.pi,2*np.pi/(points-1),'rad/muestra','Densidad de potencia de x−media','frequency',metadata={**meta,'operation':'spectral_density','density_units':'amplitud²','convention':'C[k]=(1/(2*pi))*integral_{-pi}^{pi} S_c(w)*exp(j*w*k) dw; mean line excluded','dc_line_weight':float(2*np.pi*mean*mean)})]
    return ModelAnalysis(system,float(noise_mean),var,mean,float(gamma[0]),radius,A,B,P,signals)


def realization(model,count,seed,origin=0):
    count=positive_integer(count,'Cantidad de muestras')
    if isinstance(seed,bool) or int(seed)!=seed or seed<0:raise ValueError('La semilla debe ser un entero no negativo.')
    ensure_working_set(count,live_arrays=10)
    rng=np.random.Generator(np.random.PCG64(int(seed)))
    if len(model.B):
        eig,vec=np.linalg.eigh(model.covariance)
        initial=(vec*np.sqrt(np.maximum(eig,0)))@rng.standard_normal(len(eig))
    else:initial=np.empty(0)
    noise=rng.normal(0,np.sqrt(model.noise_variance),count)
    if len(initial):values=sp.lfilter(model.system.b.real,model.system.a.real,noise,zi=initial)[0]
    else:values=model.system.b.real[0]*noise
    values+=model.mean
    metadata={'operation':'stationary_arma_realization','seed':int(seed),'generator':'PCG64','numpy_version':np.__version__,'theoretical_mean':model.mean,'theoretical_variance':model.variance,'initialization':'Gaussian stationary state covariance from discrete Lyapunov; not initial rest','noise_mean':model.noise_mean,'noise_variance':model.noise_variance}
    result=Signal(values,origin,1,'n','Realización '+model.system.name,'discrete',metadata=metadata)
    from .system_clock import input_metadata
    result.metadata=input_metadata(model.system,result)
    return result


def fit_ar(source,order,max_lag=40,points=2049):
    """Yule-Walker, biased sample covariance, estimated mean, real data."""
    if source.domain!='discrete' or np.any(source.values.imag):raise ValueError('La estimación AR requiere un registro discreto real.')
    order=positive_integer(order,'Orden AR');n=len(source.values)
    if order>=n:raise ValueError('El orden AR debe ser menor que la cantidad de muestras.')
    ensure_working_set(int(2*n+order*order+points),live_arrays=16)
    scale=float(np.max(abs(source.values.real)))
    if scale==0:raise ValueError('Un registro constante no permite estimar este modelo AR.')
    normalized=source.values.real/scale;mean_scaled=float(np.mean(normalized));centered=normalized-mean_scaled
    cov=sp.correlate(centered,centered,mode='full',method='fft')[n-1:n+order]/n
    cov[0]=np.mean(centered*centered)
    if cov[0]<=0:raise ValueError('Un registro constante no permite estimar este modelo AR.')
    try:coeff=linalg.solve_toeplitz(cov[:order],-cov[1:order+1])
    except linalg.LinAlgError as exc:raise ValueError('Las ecuaciones AR son singulares; reducí el orden o revisá el registro.') from exc
    residual=np.dot(linalg.toeplitz(cov[:order]),coeff)+cov[1:order+1]
    if not np.isfinite(coeff).all() or np.linalg.norm(residual)>1e-9*max(np.linalg.norm(cov),np.finfo(float).tiny):
        raise ValueError('El ajuste AR está mal condicionado; reducí el orden.')
    error=float(cov[0]+np.dot(coeff,cov[1:]))
    if error<=0:raise ValueError('La varianza de innovación estimada no es positiva; reducí el orden.')
    mean=mean_scaled*scale;variance=error*scale*scale;a=np.r_[1.,coeff]
    if not np.isfinite([mean,variance]).all():raise ValueError('Las estadísticas del ajuste exceden el rango numérico.')
    model=analyze([1],a,mean*float(np.sum(a)),float(np.sqrt(variance)),max_lag,points)
    errors=sp.lfilter(a,[1],centered)[order:]*scale
    model.system.name='Modelo AR('+str(order)+') estimado'
    error_signal=Signal(errors,source.origin+order,1,'n','Innovación estimada (tramo válido)','discrete',metadata={'operation':'estimated_ar_innovations','model_order':order,'input_samples':n,'scope':'Primeras p muestras excluidas; resto con p antecedentes observados. No prueba blancura ni independencia.'})
    model.fit={'order':order,'input_samples':n,'estimated_mean':mean,'innovation_variance':variance,'residual_mean_square':float(np.mean(errors*errors)),'covariance_divisor':'N','method':'Yule-Walker with estimated sample mean','mean_interpretation':'El modelo describe x−media; la media se repone al generar.','source_origin':int(source.origin)}
    rate=source.metadata.get('sample_rate_hz')
    if rate is not None:
        if not np.isfinite(rate) or rate<=0:raise ValueError('La tasa de muestreo del registro debe ser positiva y finita.')
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
    sections=[Section('Modelo y convención',paragraphs=['e[n] es ruido blanco gaussiano, con muestras independientes. Los coeficientes del denominador están ordenados como 1, z⁻¹, z⁻²…; en la recurrencia los términos a[k] cambian de signo al pasar a la derecha. El modelo es real, causal y estable.'],formulas=formulas),
        Section('Estadísticas del proceso estacionario',rows=[('Media del ruido e[n]',number(model.noise_mean)),('Varianza del ruido',number(model.noise_variance)),('Media de x[n]',number(model.mean)),('Varianza de x[n]',number(model.variance)),('Valor cuadrático medio',number(model.variance+model.mean**2)),('Mayor módulo de polo',number(model.radius))],formulas=[Formula('R[k] = C[k]' + (' + ('+number(model.mean)+')^2' if model.mean else ''),'R[k] = C[k] + media²',numeric=True)]),
        Section('Leer las salidas',paragraphs=['La autocovarianza y la autocorrelación son del modelo, no estimaciones de la realización. La densidad muestra las fluctuaciones x−media: su integral en −π…π dividida por 2π es la varianza. Si la media no es cero, el espectro completo incluye además una línea en ω=0 de peso 2π·media²; no se dibuja como una muestra de altura finita.','La realización usa un estado inicial gaussiano con covarianza estacionaria, calculada mediante Lyapunov. No arranca artificialmente desde reposo ni requiere elegir un descarte de muestras. La semilla permite reproducirla; un registro finito puede tener estadísticas diferentes de las teóricas.'])]
    if model.fit:
        fit=model.fit
        sections.insert(1,Section('Estimación desde el registro',rows=[('Método','Yule–Walker'),('Orden AR',str(fit['order'])),('Muestras observadas',str(fit['input_samples'])),('Media estimada',number(fit['estimated_mean'])),('Varianza de innovación estimada',number(fit['innovation_variance'])),('Media cuadrática del residuo válido',number(fit['residual_mean_square']))],paragraphs=['Se resta la media muestral y se estima la autocovarianza con divisor N antes de resolver las ecuaciones. El espectro resultante es paramétrico: depende del orden elegido. El residuo conserva sólo índices con p antecedentes observados. Su media cuadrática puede diferir de la varianza de innovación obtenida por Yule–Walker. El ajuste no demuestra que el proceso original sea AR ni que los residuos sean blancos.']))
    return Summary(system.name,sections)
