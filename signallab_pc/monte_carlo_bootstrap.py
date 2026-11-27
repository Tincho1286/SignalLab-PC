"""Bootstrap uncertainty for observed real-valued records."""

import math

import numpy as np

from .communications_data import MAX_SEED, integer, real
from .execution import ExecutionContext
from .operation_provenance import content_digest, verify_inputs
from .spectral_scaling import restore_scalar
from .stochastic_covariance import _align


def _measure(values, metric, low, high):
    if metric=='probability':
        return float(np.mean((values>=low)&(values<=high)))
    offset = values[0]
    shifted = values-offset
    if metric=='variance':
        return float(np.var(shifted,ddof=1))
    return offset+float(np.mean(shifted))


def bootstrap_record(source, *, metric='mean', replicas=1000, seed, block_length=1,
                     confidence=.95, low=None, high=None, execution=None):
    """Percentile intervals with IID or moving-block resampling."""
    _align((source,))
    if np.any(source.values.imag):
        raise ValueError('El bootstrap requiere una serie real. Elegí antes la componente a estudiar.')
    if metric not in ('mean','variance','probability'):
        raise ValueError('El estadístico del bootstrap debe ser media, varianza o probabilidad.')
    if metric=='probability':
        low,high = real(low,'Extremo inicial'),real(high,'Extremo final')
        if low>high:
            raise ValueError('Ordená los extremos del evento.')
    elif low is not None or high is not None:
        raise ValueError('Los extremos se usan para estimar la probabilidad de un evento.')
    count = len(source.values)
    if count<2:
        raise ValueError('El bootstrap requiere al menos dos observaciones.')
    block_length = integer(block_length,'Longitud del bloque',maximum=count-1)
    replicas = integer(replicas,'Réplicas bootstrap',minimum=2,maximum=(1<<32)-1)
    seed = integer(seed,'Semilla',minimum=0,maximum=MAX_SEED)
    confidence = real(confidence,'Nivel de confianza',positive=True)
    if confidence>=1:
        raise ValueError('El nivel de confianza debe estar entre 0 y 1.')
    context = execution or ExecutionContext()
    with context.reserve(192*count+96*replicas):
        digest = content_digest(source,context.checkpoint)
        values = source.values.real
        _,exponent = math.frexp(float(np.max(abs(values))))
        if metric != 'probability':
            with np.errstate(under='ignore'):
                values = np.ldexp(values,-exponent)
        else:
            exponent = 0
        blocks = (count+block_length-1)//block_length
        offsets = np.arange(block_length,dtype=np.intp)
        statistic = np.empty(replicas)
        for index in range(replicas):
            context.checkpoint(95*index//replicas)
            rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(seed,spawn_key=(index,))))
            starts = rng.integers(0,count-block_length+1,blocks)
            indices = (starts[:,None]+offsets).ravel()[:count]
            statistic[index] = _measure(values[indices],metric,low,high)
        alpha = (1-confidence)/2
        interval = np.quantile(statistic,[alpha,1-alpha])
        observed = _measure(values,metric,low,high)
        exponent *= 2 if metric=='variance' else 1
        estimate = restore_scalar(observed,exponent)
        spread = restore_scalar(float(statistic.std(ddof=1)),exponent)
        bias = restore_scalar(float((statistic-observed).mean()),exponent)
        lower,upper = (restore_scalar(bound,exponent) for bound in interval)
        replicated = [restore_scalar(value,exponent) for value in statistic]
        if not all(math.isfinite(value) for value in (estimate,spread,bias,lower,upper,*replicated)):
            raise FloatingPointError('El resultado bootstrap excede el rango numérico.')
        scope = ('Bootstrap percentil IID.' if block_length==1 else
                 'Bootstrap percentil de bloques contiguos solapados. Requiere dependencia débil y estacionaria.')
        if metric=='probability' and observed in (0,1):
            scope += ' El registro contiene solo un tipo de resultado del evento. El remuestreo no determina su incertidumbre.'
            interval_result = None
        else:
            interval_result = [lower,upper]
        verify_inputs((source,),(digest,),context.checkpoint)
        context.checkpoint(100)
        return {'schema':1,'operation':'bootstrap','metric':metric,'input_hashes':[digest],'samples':count,
                'replicas':replicas,'seed':seed,'generator':'PCG64','block_length':block_length,
                'estimate':estimate,'interval':interval_result,'confidence':confidence,'standard_error':spread,
                'replicate_bias':bias,'replicate_estimates':replicated,'bounds':[low,high] if metric=='probability' else None,
                'scope':scope}
