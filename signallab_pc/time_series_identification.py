"""Stable recursions shared by real-valued time-series estimators."""

import math

import numpy as np
from scipy import signal as dsp, stats
from scipy.optimize import least_squares

from .communications_data import integer, real
from .execution import ExecutionContext
from .filters import Transfer
from .model import Signal
from .operation_provenance import content_digest, settings_digest, verify_inputs
from .signal_semantics import require_temporal
from .spectral_measurements import quantity
from .system_clock import common_rate, lag_clock, reindex_clock


def burg_coefficients(centered, order, *, checkpoint):
    """One-step denominator and log innovation variance from the Burg recursion."""
    count = len(centered)
    if order >= count-1:
        raise ValueError('Burg requiere al menos dos pares al completar el orden elegido.')
    variance = float(np.mean(centered**2))
    if variance == 0 and order:
        raise ValueError('Un registro constante no identifica coeficientes Burg.')
    innovation = math.log(variance) if variance else -math.inf
    coefficients = np.asarray([1.0])
    reflection = []
    forward, backward = centered[1:], centered[:-1]
    for level in range(1, order+1):
        checkpoint(level/(order+1))
        norm = float(np.dot(forward,forward) + np.dot(backward,backward))
        if norm <= 0:
            raise ValueError('Burg agotó la varianza antes del orden pedido.')
        k = -2*float(np.dot(forward,backward))/norm
        if not math.isfinite(k) or abs(k) >= 1-8*np.finfo(float).eps:
            raise ValueError('Burg encontró una reflexión unitaria o un orden sin información suficiente.')
        coefficients = np.r_[coefficients,0.] + k*np.r_[0.,coefficients[::-1]]
        reflection.append(k)
        innovation += math.log1p(-k*k)
        if level < order:
            forward, backward = (forward+k*backward)[1:], (backward+k*forward)[:-1]
    return coefficients, innovation, tuple(reflection)


def partial_autocorrelation(covariance, max_lag=None, *, execution=None):
    """Real PACF from nonnegative lags of a positive-definite covariance."""
    values = np.asarray(covariance)
    if values.ndim != 1 or not len(values) or np.any(values.imag) or not np.all(np.isfinite(values)):
        raise ValueError('La PACF requiere covarianzas reales, finitas y ordenadas desde el retardo cero.')
    lag = len(values)-1 if max_lag is None else integer(max_lag, 'Retardos de la PACF', minimum=0, maximum=len(values)-1)
    if values[0].real <= 0:
        raise ValueError('La PACF es indefinida con varianza nula.')
    context = execution or ExecutionContext()
    with context.reserve(80*(lag+1)):
        if np.max(abs(values[:lag+1].real)) > values[0].real:
            raise ValueError('La covarianza excede su valor de retardo cero.')
        scale = float(values[0].real)
        covariance = values[:lag+1].real / scale
        partial = np.empty(lag+1)
        partial[0] = 1.
        prediction = np.empty(0)
        innovation = 1.
        for order in range(1, lag+1):
            context.checkpoint()
            k = (covariance[order] - np.dot(prediction,covariance[order-1:0:-1])) / innovation
            if abs(k) >= 1-8*np.finfo(float).eps or not math.isfinite(k):
                raise ValueError('La secuencia de covarianzas no identifica una PACF de ese orden.')
            prediction = np.r_[prediction-k*prediction[::-1], k]
            innovation *= (1-k)*(1+k)
            if innovation == 0:
                raise ValueError('La varianza de predicción no es representable para ese orden.')
            partial[order] = k
        context.checkpoint()
        return partial


_REFLECTION_LIMIT = math.atanh(1 - 2**-20)


def _polynomial(reflections):
    coefficients = np.asarray([1.])
    for reflection in reflections:
        coefficients = np.r_[coefficients, 0.] + reflection*np.r_[0., coefficients[::-1]]
    return coefficients


def _finite_series(source):
    if not isinstance(source, Signal) or source.domain != 'discrete' or np.any(source.values.imag):
        raise ValueError('La identificación requiere un registro temporal discreto real.')
    require_temporal(source)
    return source.values.real


def _difference(values, order, exponent, checkpoint):
    with np.errstate(over='ignore', invalid='ignore', under='ignore'):
        values = np.ldexp(values, -exponent)
        terminal = []
        for _ in range(order):
            checkpoint()
            terminal.append(float(values[-1]))
            values = np.diff(values)
    if not np.all(np.isfinite(values)) or not all(map(math.isfinite, terminal)):
        raise ValueError('La diferenciación o la escala exceden el rango numérico.')
    return values, terminal


def _profile(a, b, values, start, *, observe=None):
    # The mean minimizes the same innovation sum as the fitted coefficients.
    with np.errstate(over='ignore', invalid='ignore'):
        data = dsp.lfilter(a,b,values)
        weights = dsp.lfilter(a,b,np.ones(len(values)))
        scale = np.dot(weights[start:], weights[start:])
        if scale <= 0 or not np.isfinite(scale):
            raise ValueError('La media del modelo no está identificada en este soporte.')
        mean = float(np.dot(data[start:], weights[start:]) / scale)
        residual = data - mean*weights
    if not np.isfinite(residual).all() or not math.isfinite(mean):
        raise ValueError('Los residuos del ajuste exceden el rango numérico.')
    if observe is not None:
        observe()
    return mean, residual


def _conditional_fit(values, p, q, start, evaluations, context):
    size = p+q
    if not size:
        return np.ones(1), np.ones(1), True, 1

    def polynomial(parameters):
        reflection = np.tanh(parameters)
        return _polynomial(reflection[:p]), _polynomial(reflection[p:])

    def residual(parameters):
        context.checkpoint()
        a,b = polynomial(parameters)
        return _profile(a,b,values,start)[1][start:]

    initials = [np.zeros(size)]
    if p and q:
        # Mixed models have linearly dependent directions at the all-zero start.
        for ar, ma in ((-.45,.2), (-.2,-.4), (.35,.2)):
            initial = np.zeros(size)
            initial[0], initial[p] = ar, ma
            initials.append(initial)
    best = None
    total = 0
    for initial in initials:
        context.checkpoint()
        optimum = least_squares(residual, initial, bounds=(-_REFLECTION_LIMIT,_REFLECTION_LIMIT),
                                max_nfev=evaluations, ftol=1e-10, gtol=1e-10, xtol=1e-10)
        total += optimum.nfev
        if optimum.success and (best is None or optimum.cost < best.cost):
            best = optimum
    if best is None:
        raise ValueError('El ajuste condicional no convergió. Revisá el orden o ampliá el presupuesto de evaluaciones.')
    singular = np.linalg.svd(best.jac, compute_uv=False)
    scale = max(float(singular[0]), np.finfo(float).tiny)
    independent = singular[-1] > math.sqrt(np.finfo(float).eps)*scale
    a,b = polynomial(best.x)
    return a,b,bool(independent),total


def fit_arma(source, p, q, *, differences=0, validation=0, hold_back=None,
             max_evaluations=200, execution=None):
    """Conditional Gaussian ML of ARMA on d differences, with explicit initial rest."""
    x = _finite_series(source)
    p, d, q = [integer(value, name, minimum=0) for value,name in
               ((p,'Orden AR'),(differences,'Diferencias'),(q,'Orden MA'))]
    validation = integer(validation, 'Muestras reservadas', minimum=0, maximum=len(x)-1)
    start = max(p,q) if hold_back is None else integer(hold_back, 'Inicio común', minimum=max(p,q))
    trials = integer(max_evaluations, 'Evaluaciones por intento')
    train = len(x)-validation
    usable = train-d-start
    if usable <= p+q+1:
        raise ValueError('El soporte de entrenamiento es demasiado corto para los órdenes indicados.')
    context = execution or ExecutionContext()
    estimate = (p+q+6)*96*(train-d) + 256*len(x) + 128*(p+q+1)**2
    with context.reserve(estimate):
        checksum = content_digest(source, context.checkpoint)
        _, exponent = math.frexp(float(np.max(abs(x[:train]))))
        y, _ = _difference(x[:train],d,exponent,context.checkpoint)
        if (p or q) and np.all(y == y[0]):
            raise ValueError('Un registro constante después de diferenciar no identifica términos AR o MA.')
        a,b,identified,evaluations = _conditional_fit(y,p,q,start,trials,context)
        mean, residual = _profile(a,b,y,start,observe=context.checkpoint)
        errors = residual[start:]
        mse = float(np.mean(errors**2))
        limit = 256*np.finfo(float).eps*max(float(np.max(abs(y[start:]))), np.finfo(float).tiny)
        near_exact = bool(float(np.max(abs(errors))) <= limit)
        if not math.isfinite(mse):
            raise ValueError('La varianza de innovación excede el rango numérico del ajuste.')
        log_variance = 2*exponent*math.log(2) + math.log(mse) if mse else -math.inf
        poles, zeros = np.roots(a), np.roots(b)
        pole_radius, zero_radius = float(np.max(abs(poles),initial=0.)), float(np.max(abs(zeros),initial=0.))
        shared_root = bool(len(poles) and len(zeros) and np.any(np.abs(poles[:,None]-zeros) <= 1e-7))
        stationary_core = bool(pole_radius < 1-64*np.finfo(float).eps)
        invertible = bool(zero_radius < 1-64*np.finfo(float).eps)
        identified = identified and not shared_root and stationary_core and invertible and not near_exact
        parameters = p+q+2
        aic,aicc,bic = None,None,None
        if identified and mse:
            deviance = usable*(math.log(math.tau)+1+log_variance)
            aic,bic = deviance+2*parameters,deviance+parameters*math.log(usable)
            if usable > parameters+1:
                aicc = aic+2*parameters*(parameters+1)/(usable-parameters-1)
        row = {'schema':1, 'operation':'arma_conditional_fit', 'p':p, 'd':d, 'q':q,
               'a':a.tolist(), 'b':b.tolist(), 'mean_differenced':math.ldexp(mean, exponent),
               'mean_scaled':mean, 'scale_exponent':exponent, 'variance_scaled':mse,
               'innovation_variance':quantity(log_variance), 'parameters':parameters,
               'training':train, 'hold_back':start, 'fitted_samples':usable, 'validation':validation,
               'stationary_core':stationary_core, 'stationary_levels':stationary_core and d==0,
               'invertible':invertible, 'pole_radius':pole_radius, 'zero_radius':zero_radius,
               'shared_root':shared_root, 'identifiable':identified, 'near_exact':near_exact,
               'optimizer_evaluations':evaluations, 'aic':aic, 'aicc':aicc, 'bic':bic,
               'input_hashes':[checksum], 'validation_mse':None,
               'scope':'Verosimilitud gaussiana condicional. Se inicia el filtro de innovaciones en reposo y se omite el tramo inicial indicado.'}
        if validation:
            try:
                whole,_ = _difference(x,d,exponent,context.checkpoint)
                future_errors = dsp.lfilter(a,b,whole-mean)[train-d:]
                peak = float(np.max(abs(future_errors)))
                if not math.isfinite(peak):
                    raise ValueError('El tramo reservado excede la escala de entrenamiento.')
                log_error = (2*(math.log(peak)+exponent*math.log(2))+
                             math.log(float(np.mean((future_errors/peak)**2))) if peak else -math.inf)
                row['validation_mse'] = quantity(log_error)
            except (ValueError, ArithmeticError) as error:
                row['validation_notice'] = str(error)
        verify_inputs((source,), (checksum,), context.checkpoint)
    return row


def _record(source, data, origin_offset, name, operation):
    clock = reindex_clock(source.metadata, origin_offset, len(data))
    units = source.metadata.get('amplitude_units','')
    return Signal(data,source.origin+origin_offset,name=name,
                  metadata={'operation':operation,'amplitude_units':units,**clock})


def arma_forecast(source, fit, horizon, *, coverage=.95, execution=None):
    """Forecast levels after the last observation and propagate future innovations."""
    x = _finite_series(source)
    horizon = integer(horizon, 'Horizonte')
    coverage = real(coverage, 'Cobertura', positive=True)
    if coverage >= 1:
        raise ValueError('La cobertura debe estar entre 0 y 1, sin incluir los extremos.')
    context = execution or ExecutionContext()
    with context.reserve(256*(len(x)+horizon+fit['p']+fit['q']+fit['d'])):
        verify_inputs((source,), tuple(fit['input_hashes']), context.checkpoint)
        d, exponent = fit['d'], fit['scale_exponent']
        values, terminal = _difference(x,d,exponent,context.checkpoint)
        a,b,mean = np.asarray(fit['a']),np.asarray(fit['b']),fit['mean_scaled']
        centered = values-mean
        residual = dsp.lfilter(a,b,centered)
        zeros = np.zeros(horizon)
        if len(a) > 1 or len(b) > 1:
            state = dsp.lfiltic(b,a,centered[::-1],residual[::-1])
            predicted,_ = dsp.lfilter(b,a,zeros,zi=state)
        else:
            predicted = zeros
        predicted = predicted+mean
        for level in reversed(terminal):
            context.checkpoint()
            predicted = level+np.cumsum(predicted)
        with np.errstate(over='ignore', invalid='ignore'):
            physical = np.ldexp(predicted,exponent)
        forecast = _record(source,physical,len(x),'Pronóstico de niveles','arma_forecast')
        results = [forecast]
        note = 'El intervalo incluye incertidumbre de futuras innovaciones gaussianas. Los coeficientes estimados se mantienen fijos.'
        if fit['near_exact'] or not fit['stationary_core'] or not fit['invertible'] or not fit['identifiable']:
            return {'signals':results,'scope':'El ajuste no permite asignar un intervalo predictivo fiable.'}
        integrated = a.copy()
        for _ in range(d):
            context.checkpoint()
            integrated = np.convolve(integrated,[1.,-1.])
        impulse = np.zeros(horizon)
        impulse[0] = 1.
        psi = dsp.lfilter(b,integrated,impulse)
        factor = math.sqrt(fit['variance_scaled'])*float(stats.norm.isf((1-coverage)/2))
        with np.errstate(over='ignore', invalid='ignore'):
            width = factor*np.hypot.accumulate(psi)
            lower,upper = np.ldexp(predicted-width,exponent),np.ldexp(predicted+width,exponent)
        if np.all(np.isfinite(lower)) and np.all(np.isfinite(upper)) and np.all(lower<physical) and np.all(upper>physical):
            results.extend(_record(source,y,len(x),label,'arma_prediction_limit')
                           for y,label in ((lower,'Límite inferior'),(upper,'Límite superior')))
        else:
            note = 'El intervalo excede el rango o la resolución numérica. Se conserva el pronóstico.'
        context.checkpoint()
        return {'signals':results,'scope':note}


def arma_diagnostics(source, fit, max_lag=20, *, execution=None):
    """Recover conditional residuals, one-step estimates and whiteness diagnostics."""
    x = _finite_series(source)
    lag = integer(max_lag, 'Retardos', minimum=0)
    context = execution or ExecutionContext()
    with context.reserve(224*len(x)):
        verify_inputs((source,), tuple(fit['input_hashes']), context.checkpoint)
        d, exponent, start, train = fit['d'], fit['scale_exponent'], fit['hold_back'], fit['training']
        use = train if fit.get('validation_notice') else len(x)
        y,_ = _difference(x[:use],d,exponent,context.checkpoint)
        error = dsp.lfilter(fit['a'],fit['b'],y-fit['mean_scaled'])[start:]
        offset = d+start
        with np.errstate(over='ignore',under='ignore',invalid='ignore'):
            physical_error = np.ldexp(error,exponent)
            prediction = x[offset:use] - physical_error
        outputs = [_record(source,prediction,offset,'Predicción a un paso','arma_one_step'),
                   _record(source,physical_error,offset,'Innovación condicional','arma_residual')]
        rows = []
        report = 'Predicción a un paso con antecedentes observados. La ACF, la PACF y Ljung–Box usan solo innovaciones de entrenamiento.'
        n = train-offset
        lag = min(lag,n-1)
        if not fit['near_exact']:
            from .stochastic_covariance import estimate_correlation
            train_error = _record(source,error[:n],offset,'Innovación para diagnóstico','arma_scaled_error')
            acf = estimate_correlation(train_error,max_lag=lag,remove_mean=True,normalize=True,execution=context)
            acf.name = 'Autocorrelación de las innovaciones'
            acf.metadata['operation'] = 'arma_residual_acf'
            outputs.append(acf)
            rho = acf.values[lag:].real
            try:
                partial = partial_autocorrelation(rho,execution=context)
                outputs.append(Signal(partial,0,1,'retardo k','PACF de las innovaciones','discrete',
                                      metadata={'operation':'arma_residual_pacf',**lag_clock(common_rate(source),0,len(partial))}))
            except ValueError as error:
                report += ' PACF no disponible. '+str(error)
            statistic = n*(n+2)*np.cumsum(rho[1:]**2/(n-np.arange(1,lag+1)))
            fitted = fit['p']+fit['q']
            for k,value in enumerate(statistic,1):
                degrees = k-fitted
                rows.append({'lag':k,'correlation':float(rho[k]),'Q':float(value),'dof':degrees,
                             'p_value':float(stats.chi2.sf(value,degrees)) if degrees>0 and fit['identifiable'] else None})
            report += ' Ljung–Box usa una aproximación χ² con k−p−q grados válidos cuando son positivos y el ajuste está identificado.'
        else:
            report += ' Las innovaciones son compatibles con redondeo. No se asigna una prueba de blancura.'
        context.checkpoint()
        return {'signals':outputs,'rows':rows,'scope':report}


def arma_system(source, fit, *, levels=False):
    """Return the innovations-to-series transfer, without the fitted location."""
    a = np.asarray(fit['a'])
    if levels:
        for _ in range(fit['d']):
            a = np.convolve(a,[1.,-1.])
    rate = source.metadata.get('sample_rate_hz')
    return Transfer(fit['b'],a,name='Modelo estimado de innovaciones',
                    sample_period_s=None if rate is None else 1/float(rate))


def store_arma_result(project, source, source_key, fit, system, signals, *, origins=(), execution=None, tool=None):
    """Publish the fit, transfer and available views with their input in one transaction."""
    from .statistics_results import store_statistics
    context = execution or ExecutionContext()
    label = f"ARIMA({fit['p']},{fit['d']},{fit['q']})"
    fit_digest = settings_digest(['calculation',fit])
    with project.stage_records(before_commit=context.checkpoint) as staged:
        inputs, fit_key = store_statistics(staged,fit,((source,source_key,origins),),label,execution=context,tool=tool)
        model_key = staged.add(system,operation='Modelo estimado',parents=(fit_key,),tool=tool,
                               verification=(content_digest(system,context.checkpoint),(fit_digest,),context.checkpoint))
        keys = [staged.add(record,operation=record.name,parents=(fit_key,),tool=tool,
                           verification=(content_digest(record,context.checkpoint),(fit_digest,),context.checkpoint))
                for record in signals]
    return {'source_id':inputs[0],'result_id':fit_key,'model_id':model_key,'signal_ids':keys}


def compare_arma(source, orders, *, differences=0, validation=0, criterion='bic',
                 max_evaluations=200, execution=None):
    """Compare (p,q) pairs on one differencing and observation support."""
    if criterion not in ('aic','aicc','bic','validation'):
        raise ValueError('Criterio de comparación desconocido.')
    if criterion == 'validation' and not validation:
        raise ValueError('Reservá observaciones para comparar el error de validación.')
    pairs = list(dict.fromkeys((integer(p,'Orden AR',minimum=0),integer(q,'Orden MA',minimum=0)) for p,q in orders))
    if not pairs:
        raise ValueError('Indicá al menos un par de órdenes.')
    common = max(max(pair) for pair in pairs)
    context = execution or ExecutionContext()
    rows, candidates = [], []
    with context.reserve(4096*len(pairs)):
        for index,(p,q) in enumerate(pairs):
            context.checkpoint()
            try:
                row = fit_arma(source,p,q,differences=differences,validation=validation,hold_back=common,
                               max_evaluations=max_evaluations,execution=context)
            except ValueError as error:
                row = {'p':p,'d':differences,'q':q,'error':str(error)}
            rows.append(row)
            if 'error' in row or not row['identifiable']:
                continue
            if criterion == 'validation':
                measure = row['validation_mse']
                score = None if measure is None else measure['log_value'] if measure['value'] != 0 else -math.inf
            else:
                score = row[criterion]
            if score is not None:
                candidates.append((score,p+q,index))
        selected = min(candidates)[2] if candidates else None
        return {'rows':rows,'selected':selected,'criterion':criterion,'hold_back':common,
                'scope':'Se compara el mismo intervalo y orden de diferencias con la misma inicialización de innovaciones. Los criterios no acreditan por sí solos el orden poblacional.'}
