"""Complex adaptive FIR with a priori LMS, NLMS and square-root RLS predictions."""

import math
from dataclasses import dataclass

import numpy as np
from scipy.linalg import solve_triangular
from scipy.linalg.lapack import zlartg

from .communications_data import integer, real
from .execution import ExecutionContext
from .filters import Transfer
from .model import Signal
from .multivariate_probability import _parts
from .operation_provenance import content_digest, settings_digest, verify_inputs
from .resources import ResourceLimitError
from .spectral_scaling import bounded, restore_scalar
from .statistics_results import store_statistics
from .stochastic_covariance import _align
from .wiener_filter import _output, _record, mean_square_metric


METHODS = ('lms', 'nlms', 'rls')
PURPOSES = ('identification', 'cancellation', 'prediction')


@dataclass(frozen=True, slots=True)
class AdaptiveResult:
    report: dict
    system: Transfer
    estimate: Signal
    error: Signal
    reference: Signal


def _rotate(triangle, target, row, value, forgetting):
    """Insert one weighted observation in the augmented least-squares factor."""
    triangle *= forgetting
    target *= forgetting
    update = row.copy()
    for index, below in enumerate(update):
        c, s, diagonal = zlartg(triangle[index,index], below)
        tail = slice(index+1,None)
        upper = triangle[index,tail].copy()
        triangle[index,index] = diagonal
        triangle[index,tail] = c*upper + s*update[tail]
        update[tail] = c*update[tail] - s.conjugate()*upper
        rhs = target[index]
        target[index] = c*rhs+s*value
        value = c*value-s.conjugate()*rhs
    if not np.isfinite(triangle).all() or not np.isfinite(target).all():
        raise FloatingPointError('La actualización RLS excede el rango numérico.')
    if np.any(triangle.diagonal()==0):
        raise ValueError('RLS perdió rango. Revisá la regularización, el olvido y la excitación de la entrada.')
    return solve_triangular(triangle,target,check_finite=False)


def adaptive_fir(drive, desired=None, *, length, method='nlms', purpose='identification', delay=None,
                 step=None, floor=None, forgetting=None, ridge=None, reserve=0, execution=None):
    """Estimate using past weights, then update on the current error during training."""
    if method not in METHODS or purpose not in PURPOSES:
        raise ValueError('Algoritmo o propósito adaptativo desconocido.')
    if purpose == 'prediction':
        if desired is not None:
            raise ValueError('Para predecir, cargá un solo registro y un retardo positivo.')
        inputs, desired = (drive,), drive
    else:
        inputs = (drive,desired)
    minimum_delay = 1 if purpose == 'prediction' else 0
    start,end,rate = _align(inputs)
    delay = minimum_delay if delay is None else integer(delay,'Retardo de entrada',minimum=minimum_delay,
                                                         maximum=end-drive.origin-1)
    length = integer(length,'Cantidad de coeficientes',maximum=end-drive.origin-delay)
    start = max(start, drive.origin+delay+length-1)
    count = end-start
    reserve = integer(reserve,'Muestras de validación',minimum=0,maximum=count-1)
    training = count-reserve
    if method == 'rls':
        if step is not None or floor is not None:
            raise ValueError('RLS usa factor de olvido y regularización inicial.')
        forgetting = real(.99 if forgetting is None else forgetting,'Factor de olvido',positive=True,maximum=1.)
        ridge = real(1. if ridge is None else ridge,'Regularización inicial',positive=True)
        settings = {'forgetting':forgetting,'ridge':ridge}
    else:
        if forgetting is not None or ridge is not None or (method == 'lms' and floor is not None):
            raise ValueError('Los parámetros deben corresponder al algoritmo elegido.')
        step = real((.01 if method == 'lms' else .5) if step is None else step,'Paso de adaptación',positive=True)
        if method == 'nlms' and step>=2:
            raise ValueError('Elegí un paso NLMS entre 0 y 2.')
        settings = {'step':step}
        if method == 'nlms':
            floor = real(1e-8 if floor is None else floor,'Piso de energía',positive=True)
            settings['floor'] = floor
    context = execution or ExecutionContext()
    estimate = 224*count + 64*(length+delay)
    if method == 'rls':
        estimate += 128*length**2
    with context.reserve(estimate):
        digests = tuple(content_digest(source,context.checkpoint) for source in inputs)
        source, ex = bounded(drive.values[start-delay-length+1-drive.origin:end-delay-drive.origin],normalize=True)
        target, ed = bounded(desired.values[start-desired.origin:end-desired.origin],normalize=True)
        design = np.lib.stride_tricks.sliding_window_view(source,length)[:,::-1]
        coefficients = np.zeros(length,dtype=complex)
        prediction = np.empty(count,dtype=complex)
        residual = np.empty_like(prediction)
        if method == 'rls':
            initial = restore_scalar(math.sqrt(ridge),-ex)
            if initial == 0 or not math.isfinite(initial):
                raise ValueError('La regularización inicial no puede representarse a la escala de la entrada.')
            triangle = initial*np.eye(length,dtype=complex)
            rhs = np.zeros(length,dtype=complex)
            decay = math.sqrt(forgetting)
        elif method == 'lms':
            gain = restore_scalar(step,2*ex)
            if gain == 0 or not math.isfinite(gain):
                raise ValueError('El paso LMS es incompatible con las unidades de la entrada.')
        else:
            epsilon = restore_scalar(floor,-2*ex)
        with np.errstate(over='ignore',invalid='ignore'):
            for index,row in enumerate(design):
                context.checkpoint(95*index//count)
                prediction[index] = row @ coefficients
                error = target[index]-prediction[index]
                residual[index] = error
                if index >= training:
                    continue
                if method == 'rls':
                    coefficients = _rotate(triangle,rhs,row,target[index],decay)
                else:
                    power = float(np.vdot(row,row).real)
                    if method == 'nlms':
                        gain = step/(power+epsilon) if power else 0.
                    coefficients += gain*row.conj()*error
                if not np.isfinite(coefficients).all():
                    raise FloatingPointError('La adaptación diverge. Revisá el paso y la escala de entrada.')
        taps = _output(coefficients,ed-ex)
        output = _record(_output(prediction,ed),start,desired,
                         'Ruido estimado' if purpose=='cancellation' else 'Predicción adaptativa')
        error = _record(_output(residual,ed),start,desired,
                        'Estimación limpia' if purpose=='cancellation' else 'Error adaptativo')
        reference = _record(desired.values[start-desired.origin:end-desired.origin],start,desired,'Señal deseada')
        mse = mean_square_metric(residual[:training], ed)
        validation = mean_square_metric(residual[training:], ed) if reserve else None
        result = {'schema':1,'method':method,'purpose':purpose,'input_hashes':list(digests),
                  'length':length,'delay':delay,'first_index':start,'last_index':end-1,
                  'training_samples':training,'validation_samples':reserve,'settings':settings,
                  'initial_coefficients':'zeros','coefficients':_parts(taps),
                  'training_mse':mse,'validation_mse':validation,
                  'scope':'El error usa los coeficientes previos a cada actualización. En el tramo final reservado los coeficientes se mantienen fijos.'}
        transfer = Transfer(np.r_[np.zeros(delay),taps],[1.],name='Filtro fijo final '+method.upper(),
                            sample_period_s=None if rate is None else 1/rate)
        verify_inputs(inputs,digests,context.checkpoint)
        context.checkpoint(100)
        return AdaptiveResult(result,transfer,output,error,reference)


def store_adaptive(project, result, inputs, *, execution=None, tool=None):
    context = execution or ExecutionContext()
    report = result.report
    operation = 'Filtrado adaptativo '+report['method'].upper()
    proof = settings_digest(['calculation',report])
    with project.stage_records(before_commit=context.checkpoint) as staged:
        sources,parent = store_statistics(staged,report,inputs,operation,execution=context,tool=tool)
        receipt = {'sources':sources,'report':parent}
        for label in ('system','estimate','error','reference'):
            value = getattr(result,label)
            receipt[label] = staged.add(value,operation=value.name,parents=(parent,),tool=tool,
                                        verification=(content_digest(value,context.checkpoint),(proof,),context.checkpoint))
    return receipt


def compare_adaptive(drive, desired, configurations, *, length, purpose='identification', delay=None,
                     reserve=0, execution=None):
    """Compare algorithms or sweep parameters on identical causal windows."""
    if not isinstance(configurations, (tuple,list)) or not configurations:
        raise ValueError('La comparación requiere una lista de configuraciones.')
    fields = {'method','step','floor','forgetting','ridge'}
    if any(not isinstance(config,dict) or 'method' not in config or config.keys()-fields for config in configurations):
        raise ValueError('Indicá el algoritmo y sus parámetros en cada configuración.')
    context = execution or ExecutionContext()
    work_bytes = 240 * min(len(drive.values),len(desired.values) if desired is not None else len(drive.values))
    retained = work_bytes*len(configurations)
    with context.aggregate_progress() as parent, parent.reserve(retained):
        remaining = None if parent.max_work_bytes is None else parent.max_work_bytes-retained
        if remaining == 0:
            raise ResourceLimitError('La comparación agotó el presupuesto antes de iniciar un ajuste.')
        results = []
        for index,config in enumerate(configurations):
            parent.checkpoint(100*index//len(configurations))
            # The enclosing budget counts retained curves. Each inner step
            # additionally admits its own temporary arrays and factors.
            child = ExecutionContext(remaining,parent.deadline,parent.cancel,pool=parent.pool)
            results.append(adaptive_fir(drive,desired,length=length,purpose=purpose,delay=delay,
                                        reserve=reserve,execution=child,**config))
        parent.checkpoint(100)
    return tuple(results)


def store_adaptive_comparison(project, results, inputs, *, execution=None, tool=None):
    context = execution or ExecutionContext()
    with project.stage_records(before_commit=context.checkpoint) as staged:
        receipts = []
        for result in results:
            receipt = store_adaptive(staged,result,inputs,execution=context,tool=tool)
            inputs = tuple((value,key,origins) for (value,_,origins),key in zip(inputs,receipt['sources'],strict=True))
            receipts.append(receipt)
        parents = tuple(receipt['report'] for receipt in receipts)
        digests = tuple(settings_digest(['calculation',result.report]) for result in results)
        payload = {'schema':1,'operation':'compare_adaptive','scope':'Mismos índices y tramo de validación para todas las configuraciones.',
                   'rows':[{key:result.report[key] for key in ('method','settings','training_mse','validation_mse')}
                           for result in results]}
        parent = staged.add(payload,title='Comparación de filtrado adaptativo',operation='Comparar sensibilidad',
                            parents=parents,tool=tool,verification=(
                                settings_digest(['calculation',payload]),digests,context.checkpoint))
    return {'comparison':parent,'runs':receipts}
