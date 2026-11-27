"""Statistical interpretation of calibrated spectral estimates."""

import numpy as np
from scipy.stats import chi2

from .communications_data import integer, real
from .execution import ExecutionContext
from .model import Signal
from .operation_provenance import content_digest, verify_inputs


def white_noise_confidence(spectrum, *, model, coverage=.95, execution=None):
    """Pointwise chi-square bounds for disjoint rectangular white-noise estimates."""
    if not isinstance(spectrum, Signal) or spectrum.data_kind != 'density' or spectrum.units != 'Hz':
        raise ValueError('Cargá una PSD calibrada en Hz.')
    metadata = spectrum.metadata
    estimator = metadata.get('estimator')
    if estimator not in ('bartlett','periodogram','welch') or metadata.get('window') != 'boxcar' or metadata.get('overlap') != 0:
        raise ValueError('Las bandas exactas para ruido blanco requieren bloques rectangulares disjuntos.')
    if model not in ('real_gaussian_white','proper_complex_gaussian_white'):
        raise ValueError('Declarar ruido blanco gaussiano real o complejo propio, con media cero.')
    real_input = model == 'real_gaussian_white'
    if metadata.get('real_input') is not real_input:
        raise ValueError('El modelo de ruido no corresponde al tipo de señal registrado.')
    coverage = real(coverage,'Cobertura',minimum=0,maximum=1,positive=True)
    if coverage == 1:
        raise ValueError('La cobertura debe ser menor que uno.')
    length = integer(metadata.get('segment'),'Longitud de segmento')
    blocks = integer(metadata.get('segments_used'),'Segmentos usados')
    unilateral = metadata.get('sidedness','').startswith('one-sided')
    size = length//2+1 if unilateral else length
    if len(spectrum.values) != size or np.any(spectrum.values.imag) or np.any(spectrum.values.real<0):
        raise ValueError('La grilla o los valores de la PSD no corresponden al estimador declarado.')
    tail = (1-coverage)/2
    context = execution or ExecutionContext()
    with context.reserve(160*size):
        digest = content_digest(spectrum, context.checkpoint)
        ordinary_df = 2*blocks
        degree = np.full(size,ordinary_df,dtype=int)
        dc = 0 if unilateral else length//2
        used = np.ones(size,dtype=bool)
        if real_input:
            degree[dc] = blocks
            if length%2==0:
                degree[-1 if unilateral else 0] = blocks
        if metadata.get('remove_segment_mean'):
            used[dc] = False
        lower = np.empty(size)
        upper = np.empty(size)
        for degrees in (blocks,ordinary_df):
            context.checkpoint()
            mask = degree==degrees
            power = spectrum.values.real[mask]
            with np.errstate(over='ignore',under='ignore'):
                lower[mask] = power*(degrees/chi2.isf(tail,degrees))
                upper[mask] = power*(degrees/chi2.ppf(tail,degrees))
        used &= np.isfinite(lower) & np.isfinite(upper)
        verify_inputs((spectrum,),(digest,),context.checkpoint)
        return {'schema':1,'operation':'white_noise_spectral_confidence','input_hashes':[digest],
                'model':model,'coverage':coverage,'estimator':estimator,'segments':blocks,'start_hz':spectrum.origin,
                'step_hz':spectrum.step,'density_units':metadata.get('density_units','amplitud²/Hz'),
                'bounds':[{'lower':float(lo),'upper':float(hi),'degrees_of_freedom':int(df)} if ok else None
                          for lo,hi,df,ok in zip(lower,upper,degree,used,strict=True)],
                'scope':'Intervalo marginal por bin para ruido blanco gaussiano de media cero. La media retirada excluye DC.'}
