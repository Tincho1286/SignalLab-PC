"""Conditional AR estimation, common-sample order scores and honest predictions."""
import math
import numpy as np
from scipy import signal,stats
from .model import Signal
from .filters import Transfer
from .resources import ensure_working_set
from .jobs import checkpoint
from .spectral_measurements import quantity


def integer(value,name,minimum=0):
    try:valid=not isinstance(value,(bool,np.bool_)) and int(value)==value and value>=minimum
    except (TypeError,ValueError,OverflowError):valid=False
    if not valid:raise ValueError(name+' debe ser un entero ≥'+str(minimum)+'.')
    return int(value)


def prepare(source,validation=0):
    from .signal_semantics import require_temporal
    require_temporal(source)
    if source.domain!='discrete' or np.any(source.values.imag):raise ValueError('El ajuste AR requiere muestras temporales discretas reales.')
    n=len(source.values);validation=integer(validation,'Muestras reservadas')
    if n-validation<2:raise ValueError('La reserva debe dejar al menos dos muestras para ajustar.')
    from .system_clock import common_rate,validate_clock_resolution
    rate=common_rate(source)
    if rate is not None:validate_clock_resolution(source.metadata.get('time_start_s',source.origin/rate),rate,n)
    scale=float(np.max(abs(source.values.real[:n-validation]))) or 1.
    with np.errstate(over='ignore',under='ignore'):normalized=source.values.real/scale
    return dict(source=source,x=normalized,scale=scale,train=n-validation,validation=validation)


def _prediction(data,fit,start,stop):
    x=data['x'];p=fit['order'];mean=fit['center_scaled'];answer=np.full(stop-start,mean+fit['offset_scaled'])
    for k,c in enumerate(fit['phi'],1):
        checkpoint(k/max(1,p));answer+=c*(x[start-k:stop-k]-mean)
    if not np.isfinite(answer).all():raise ValueError('La predicción excede el rango numérico.')
    return answer


def _error_measure(errors,scale):
    # errors are normalized before squaring. Preserve tiny/huge physical variances.
    peak=float(np.max(abs(errors))) if len(errors) else 0.
    if peak==0:return quantity(-np.inf)
    return quantity(2*math.log(scale)+2*math.log(peak)+math.log(float(np.mean((errors/peak)**2))))


def fit(source,order,*,method='ols',validation=0,hold_back=None):
    data=prepare(source,validation);return fit_prepared(data,order,method,hold_back)


def fit_prepared(data,order,method='ols',hold_back=None):
    p=integer(order,'Orden AR');train=data['train'];start=p if hold_back is None else integer(hold_back,'Inicio común')
    if start<p or train-start<1 or method=='ols' and train-start<=p+1:raise ValueError('Se necesitan más filas de ajuste que coeficientes (incluida la constante). Reducí el orden, el inicio común o la reserva.')
    x=data['x'];mean=float(np.mean(x[:train]));centered=x-mean;nfit=train-start;scale=data['scale'];condition=None
    ensure_working_set(int(nfit*(p+2)+p*p+len(x)),live_arrays=6)
    if method=='ols':
        matrix=np.ones((nfit,p+1))
        for k in range(1,p+1):matrix[:,k]=centered[start-k:train-k]
        coefficients,_,rank,singular=np.linalg.lstsq(matrix,centered[start:train],rcond=None)
        if rank!=p+1:raise ValueError('Las columnas de retardos son dependientes. No hay un ajuste AR único para ese orden.')
        condition=float(singular[0]/singular[-1])
        if not np.isfinite(coefficients).all() or condition>1/math.sqrt(np.finfo(float).eps):raise ValueError('El ajuste está mal condicionado; reducí el orden o revisá el registro.')
        phi=coefficients[1:];offset=float(coefficients[0]);method_name='Mínimos cuadrados condicionales'
    elif method=='yw':
        if hold_back is not None and hold_back!=p:raise ValueError('La comparación con inicio común usa mínimos cuadrados; Yule–Walker conserva su propia estimación de covarianzas.')
        if p==0:phi=np.empty(0);offset=0.
        else:
            from scipy.linalg import solve_toeplitz,toeplitz
            cov=signal.correlate(centered[:train],centered[:train],mode='full',method='fft')[train-1:train+p]/train
            cov[0]=np.mean(centered[:train]**2)
            if cov[0]<=0:raise ValueError('Un registro constante no identifica coeficientes AR de orden positivo.')
            phi=solve_toeplitz(cov[:p],cov[1:]);offset=0.
            residual=toeplitz(cov[:p])@phi-cov[1:]
            if not np.isfinite(phi).all() or np.linalg.norm(residual)>1e-9*max(np.linalg.norm(cov),np.finfo(float).tiny):raise ValueError('Las ecuaciones de Yule–Walker no tienen precisión suficiente.')
        method_name='Yule–Walker (covarianza con divisor N)'
    else:raise ValueError('Método AR no reconocido.')
    intercept_scaled=float(offset+mean*(1-float(np.sum(phi))));intercept=intercept_scaled*scale
    if not math.isfinite(intercept):raise ValueError('La constante del modelo excede el rango numérico.')
    denominator=np.r_[1.,-phi];poles=np.roots(denominator);radius=float(np.max(abs(poles))) if p else 0.
    row=dict(order=p,phi=phi.tolist(),a=denominator.tolist(),intercept=intercept,center_scaled=mean,offset_scaled=offset,scale=scale,method=method,method_name=method_name,fit_start=start,train=train,validation=data['validation'],nfit=nfit,parameters=p+2,condition=condition,radius=radius,stationary=bool(radius<1-64*np.finfo(float).eps),error=None)
    prediction=_prediction(data,row,start,train);errors=x[start:train]-prediction;measure=_error_measure(errors,scale);row['residual_mse']=measure
    tol=256*np.finfo(float).eps*max(float(np.max(abs(x[start:train]))),float(np.max(abs(prediction))),np.finfo(float).tiny)
    near_exact=bool(float(np.max(abs(errors)))<=tol);row['near_exact']=near_exact
    if method=='yw':
        innovation=float(np.mean(centered[:train]**2)) if not p else float(cov[0]-np.dot(phi,cov[1:]))
        if innovation<0:raise ValueError('La varianza de innovación de Yule–Walker no es válida.')
        row['innovation_variance']=quantity(-np.inf if innovation==0 else 2*math.log(scale)+math.log(innovation))
    else:row['innovation_variance']=measure
    # Conditional Gaussian ML scores are valid here only for conditional OLS.
    scores={key:None for key in ('aic','aicc','bic')}
    if method=='ols' and not near_exact and measure['log_value'] is not None:
        deviance=nfit*(math.log(math.tau)+1+measure['log_value']);k=p+2
        scores.update(aic=deviance+2*k,bic=deviance+k*math.log(nfit))
        if nfit>k+1:scores['aicc']=scores['aic']+2*k*(k+1)/(nfit-k-1)
    row.update(scores)
    row['validation_mse']=None;row['validation_notice']=None
    if data['validation']:
        try:
            if not np.isfinite(x).all():raise ValueError('El tramo reservado excede la escala numérica del entrenamiento.')
            row['validation_mse']=_error_measure(x[train:]-_prediction(data,row,train,len(x)),scale)
        except (ValueError,ArithmeticError) as exc:row['validation_notice']=str(exc)
    return row


def compare(source,maximum,minimum=0,*,validation=0,criterion='bic'):
    data=prepare(source,validation);minimum=integer(minimum,'Orden mínimo');maximum=integer(maximum,'Orden máximo')
    if minimum>maximum:raise ValueError('El orden mínimo debe ser ≤ al máximo.')
    if data['train']-maximum<=maximum+1:raise ValueError('La comparación necesita más de 2·p_máximo+1 muestras de entrenamiento para usar el mismo intervalo en todos los órdenes.')
    if criterion not in ('aic','aicc','bic','validation'):raise ValueError('Criterio no reconocido.')
    if criterion=='validation' and not data['validation']:raise ValueError('Reservá muestras para elegir por error de validación.')
    rows=[];ensure_working_set(int(data['train']*(maximum+3)+maximum*maximum),live_arrays=6)
    for p in range(minimum,maximum+1):
        checkpoint((p-minimum)/max(1,maximum-minimum+1))
        try:row=fit_prepared(data,p,'ols',maximum)
        except (ValueError,np.linalg.LinAlgError) as exc:row=dict(order=p,error=str(exc))
        rows.append(row)
    def score(row):
        if row.get('error'):return None
        return row['validation_mse']['log_value'] if criterion=='validation' and row['validation_mse']['value']!=0 else -np.inf if criterion=='validation' else row[criterion]
    candidates=[(score(row),i) for i,row in enumerate(rows) if not row.get('error') and (row['validation_mse'] is not None if criterion=='validation' else row[criterion] is not None)]
    selected=min(candidates)[1] if candidates else None
    return dict(rows=rows,selected=selected,criterion=criterion,hold_back=maximum,train=data['train'],validation=data['validation'],scope='Todos los órdenes se ajustan sobre las mismas respuestas, con constante; k=p+2 incluye la varianza. Se reserva el final antes de ajustar. Menor criterio no demuestra el orden verdadero.')


def temporal(source,values,offset,name,operation,**extra):
    metadata=dict(operation=operation,**extra);rate=source.metadata.get('sample_rate_hz')
    if rate is not None:
        from .system_clock import validate_clock_resolution
        metadata['sample_rate_hz']=float(rate)
        if 'time_start_s' in source.metadata:
            start=float(source.metadata['time_start_s'])+offset/float(rate);validate_clock_resolution(start,float(rate),len(values));metadata['time_start_s']=start
    return Signal(values,int(source.origin)+offset,1,'n',name,'discrete',metadata=metadata)


def diagnostics(source,row,max_lag=20):
    data=prepare(source,row['validation']);start=row['fit_start'];train=row['train'];stop=train if row['validation_notice'] else len(data['x']);pred=_prediction(data,row,start,stop);observed=data['x'][start:stop];residual=observed-pred;scale=data['scale']
    outputs=[temporal(source,pred*scale,start,'Predicción a un paso','ar_one_step',model_order=row['order'],scope='Cada punto usa antecedentes observados, también dentro de la reserva; no es predicción recursiva.'),temporal(source,residual*scale,start,'Residuo a un paso','ar_residual',model_order=row['order'],training_last=int(source.origin)+train-1)]
    fit_res=residual[:train-start];n=len(fit_res);lag=min(integer(max_lag,'Retardos del diagnóstico'),n-1);rows=[]
    centered=fit_res-float(np.mean(fit_res));peak=float(np.max(abs(centered)))
    if peak==0 or row['near_exact']:return dict(signals=outputs,rows=[],report='El residuo de entrenamiento es nulo o compatible con redondeo. No se asignan autocorrelaciones normalizadas ni valores p ficticios.',lags=lag)
    normalized=centered/peak;cov=signal.correlate(normalized,normalized,mode='full',method='fft')[n-1:n+lag];rho=cov/cov[0];rho[0]=1.
    # Ljung–Box: residuals centered, estimated AR degrees of freedom p.
    terms=rho[1:]**2/(n-np.arange(1,lag+1));q=n*(n+2)*np.cumsum(terms);p=row['order']
    for k in range(1,lag+1):rows.append(dict(lag=k,correlation=float(rho[k]),Q=float(q[k-1]),dof=k-p,p_value=float(stats.chi2.sf(q[k-1],k-p)) if k>p else None))
    acf=Signal(np.r_[rho[:0:-1],rho],-lag,1,'retardo k','Autocorrelación del residuo de entrenamiento','discrete',metadata=dict(operation='ar_residual_acf',model_order=p,input_samples=n,scope='Divisor N; residuo centrado. Sólo entrenamiento.'))
    outputs.append(acf)
    return dict(signals=outputs,rows=rows,lags=lag,report='El diagnóstico usa sólo '+str(n)+' residuos de entrenamiento, centrados y con divisor N. Q de Ljung–Box es acumulativo; sus grados de libertad son k−p. El valor p es asintótico y presupone un modelo apropiado con innovaciones independientes. Un valor p grande no demuestra blancura ni independencia. Con k≤p no se calcula valor p; en muestras cortas la aproximación puede ser pobre.')


def forecast(source,row,horizon=16,coverage=95):
    horizon=integer(horizon,'Horizonte',1)
    if not math.isfinite(coverage) or not 0<coverage<100:raise ValueError('La cobertura debe estar entre 0 y 100 %, sin incluir extremos.')
    ensure_working_set(int(len(source.values)+horizon+row['order']),live_arrays=12)
    data=prepare(source,row['validation']);x=data['x'];p=row['order'];mean=row['center_scaled'];history=np.r_[x[-p:] if p else [],np.zeros(horizon)];values=np.empty(horizon)
    for h in range(horizon):
        checkpoint(h/horizon);value=mean+row['offset_scaled']
        for k,c in enumerate(row['phi'],1):value+=c*(history[p+h-k]-mean)
        if not math.isfinite(value):raise ValueError('La predicción recursiva excede el rango numérico; el ajuste se conserva.')
        history[p+h]=values[h]=value
    with np.errstate(over='ignore',invalid='ignore'):values*=data['scale']
    if not np.isfinite(values).all():raise ValueError('La amplitud predicha excede float64; el ajuste se conserva.')
    offset=len(x);base=dict(model_order=p,training_samples=row['train'],observed_samples=len(x),coverage=coverage,scope='Coeficientes fijados en entrenamiento. El pronóstico parte de los últimos antecedentes observados; después reutiliza sus predicciones.')
    outputs=[temporal(source,values,offset,'Predicción recursiva AR','ar_forecast',**base)]
    notice='Los intervalos presuponen innovaciones gaussianas independientes, parámetros fijados y varianza estimada. Incluyen incertidumbre de innovaciones futuras, no de parámetros ni selección del orden.'
    if row['near_exact']:return dict(signals=outputs,report='No se calcula intervalo: el residuo es compatible con redondeo y no permite estimar una incertidumbre estadística fiable.')
    impulse=np.zeros(horizon);impulse[0]=1.;psi=signal.lfilter([1.],row['a'],impulse)
    if not np.isfinite(psi).all():return dict(signals=outputs,report='La respuesta de innovaciones excede float64. Se conserva la predicción, sin intervalo.')
    with np.errstate(divide='ignore'):logvar=np.logaddexp.accumulate(2*np.log(abs(psi)))
    innovation=row['innovation_variance']['log_value'];z=float(stats.norm.isf((100-coverage)/200))
    if innovation is None or not math.isfinite(z) or z<=0:return dict(signals=outputs,report='La varianza o la cobertura no permiten representar un intervalo fiable. Se conserva la predicción.')
    with np.errstate(over='ignore',under='ignore'):width=np.exp((logvar+innovation)/2+math.log(z))
    with np.errstate(over='ignore',invalid='ignore'):lower,upper=values-width,values+width
    if not np.isfinite(lower).all() or not np.isfinite(upper).all() or np.any((width==0)|(lower==values)|(upper==values)):return dict(signals=outputs,report='El intervalo excede el rango o la resolución de float64. Se conserva la predicción. '+notice)
    outputs.extend([temporal(source,lower,offset,'Límite predictivo inferior','ar_prediction_limit',**base),temporal(source,upper,offset,'Límite predictivo superior','ar_prediction_limit',**base)])
    return dict(signals=outputs,report=notice)


def system(source,row):
    rate=source.metadata.get('sample_rate_hz');period=None if rate is None else 1/float(rate)
    return Transfer([1],row['a'],name='AR('+str(row['order'])+') · innovaciones a x',sample_period_s=period)


def report(row):
    def value(key):return 'No definido' if row.get(key) is None else format(row[key],'.12g')
    terms=[format(row['intercept'],'.12g')]+['('+format(v,'.12g')+')*x[n-'+str(k)+']' for k,v in enumerate(row['phi'],1) if v]+['e[n]']
    text=row['method_name']+'\n\nx[n] = '+' + '.join(terms)+'\nConstante c: '+format(row['intercept'],'.12g')+'\nφ[1]…φ[p]: '+(', '.join(format(v,'.12g') for v in row['phi']) or 'Sin términos de memoria (p=0)')
    text+='\nOrden p: '+str(row['order'])+'\nFilas de ajuste: '+str(row['nfit'])+'\nMuestras reservadas: '+str(row['validation'])+'\nMayor módulo de polo: '+value('radius')+'\nMSE de entrenamiento: '+row['residual_mse']['text']+'\nVarianza de innovación: '+row['innovation_variance']['text']
    if row['validation_mse'] is not None:text+='\nMSE de validación a un paso: '+row['validation_mse']['text']
    if row['validation_notice']:text+='\nValidación no disponible: '+row['validation_notice']+' El ajuste se conserva.'
    if row['method']=='ols':text+='\nAIC: '+value('aic')+'\nAICc: '+value('aicc')+'\nBIC: '+value('bic')+'\nParámetros contados: p+2 (coeficientes, constante y varianza). AICc exige N_ajuste > p+3.'
    if row['near_exact']:text+='\n\nResiduo compatible con redondeo: no se utilizan criterios gaussianos degenerados ni valores p.'
    text+='\n\nEl ajuste no prueba que el proceso sea AR. La predicción a un paso usa el pasado observado; la recursiva utiliza sus propias salidas futuras.'
    if not row['stationary']:text+='\n\nEste ajuste no es estable como modelo causal estacionario. Se conservan coeficientes y predicciones; no se le asignan estadísticas estacionarias.'
    return text
