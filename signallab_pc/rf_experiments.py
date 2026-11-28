"""Parametric sweeps and resumable link uncertainty using the Phase 05 campaign engine."""

from dataclasses import asdict, dataclass, replace
import json
import math

import numpy as np

from .analog_design import bessel_prototype
from .communications_data import real
from .execution import ExecutionContext
from .monte_carlo import CampaignSpec, Scenario, run_campaign
from .probability import Distribution
from .resources import ResourceLimitError
from .rf_line import _grid
from .rf_link import LinkBudget, RFStage, noise_cascade
from .rf_matching import MatchingDesign, evaluate_matching


MAX_SWEEP_EVALUATIONS = 512
MAX_SWEEP_CELLS = 1_000_000


@dataclass(frozen=True, slots=True)
class MatchingSweep:
    parameter: str
    values: np.ndarray
    frequencies_hz: np.ndarray
    reflection: np.ndarray
    delivered_power_fraction: np.ndarray


def _sweep_vector(values, limit=MAX_SWEEP_EVALUATIONS):
    if not isinstance(values, (list, tuple, np.ndarray)) or np.ndim(values)==0:
        raise ValueError('El barrido requiere una lista de valores reales finitos.')
    if len(values)>limit:
        raise ResourceLimitError(f'El barrido admite hasta {limit} evaluaciones.')
    raw = np.asarray(values)
    if raw.ndim!=1 or not raw.size or raw.dtype.kind not in 'fiu' or not np.isfinite(raw).all():
        raise ValueError('El barrido requiere una lista de valores reales finitos.')
    data = raw.astype(float)
    if np.any(np.diff(data)<=0):
        raise ValueError('Completá el barrido con valores estrictamente crecientes.')
    return data


def _with_parameter(design, parameter, value):
    if parameter == 'resistance_ohm':
        return replace(design,load_ohm=complex(value,design.load_ohm.imag))
    if parameter == 'reactance_ohm':
        return replace(design,load_ohm=complex(design.load_ohm.real,value))
    if parameter == 'velocity_factor':
        return replace(design,velocity_factor=value)
    if parameter not in dict(design.elements):
        raise ValueError('El parámetro no pertenece a este adaptador.')
    return replace(design,elements=tuple((key,value if key==parameter else old) for key,old in design.elements))


def matching_sweep(design: MatchingDesign, parameter, values, frequencies_hz, *, context=None) -> MatchingSweep:
    """Measure frequency and parameter independently for a fixed matching circuit."""
    ctx = context if context is not None else ExecutionContext()
    ctx.checkpoint()
    variable = _sweep_vector(values)
    frequency = _grid(frequencies_hz,positive=True)
    size = variable.size * frequency.size
    if size>MAX_SWEEP_CELLS:
        raise ResourceLimitError('El barrido RF admite hasta 1 000 000 pares de frecuencia y parámetro.')
    with ctx.reserve(48*size):
        reflection=np.empty((variable.size,frequency.size),dtype=complex)
        power=np.empty_like(reflection.real)
        for i,value in enumerate(variable):
            ctx.checkpoint(100*i//variable.size)
            result=evaluate_matching(_with_parameter(design,parameter,value),frequency,context=ctx)
            reflection[i]=result.reflection
            power[i]=result.delivered_power_fraction
        ctx.checkpoint(100)
        return MatchingSweep(parameter,variable,frequency.copy(),reflection,power)


def matching_tolerance(design, parameter, lower, upper, *, context=None):
    """Symmetric or asymmetric bounded changes. The derivative is a secant estimate."""
    low=real(lower,'Valor mínimo del componente')
    high=real(upper,'Valor máximo del componente')
    nominal={'resistance_ohm':design.load_ohm.real,'reactance_ohm':design.load_ohm.imag,
             'velocity_factor':design.velocity_factor,**dict(design.elements)}.get(parameter)
    if nominal is None or not low < nominal < high:
        raise ValueError('La tolerancia debe contener estrictamente el valor nominal.')
    study=matching_sweep(design,parameter,[low,nominal,high],[design.frequency_hz],context=context)
    gamma=study.reflection[:,0]
    # Unequal spacings use the derivative of the quadratic through all three points.
    left,right=nominal-low,high-nominal
    backward,forward=(gamma[1]-gamma[0])/left,(gamma[2]-gamma[1])/right
    derivative=(right/(left+right))*backward+(left/(left+right))*forward
    return {'parameter':parameter,'frequency_hz':design.frequency_hz,'samples':study.values,
            'reflection':gamma,'sensitivity_per_unit':complex(derivative),
            'scope':'Derivada local estimada con tres puntos. Los extremos son las dos variaciones evaluadas.'}


def bessel_sensitivity(order, characteristic_rad_s, perturbation, omega_rad_s, *, edge_index=0,
                       kind='lowpass', normalization='phase', context=None):
    """Central difference of H and group delay against a selected characteristic edge."""
    ctx = context if context is not None else ExecutionContext()
    ctx.checkpoint()
    nominal = np.atleast_1d(np.asarray(characteristic_rad_s))
    if type(edge_index) is not int or not 0<=edge_index<nominal.size or nominal.dtype.kind not in 'fiu':
        raise ValueError('Elegí un borde real del prototipo Bessel.')
    delta = real(perturbation,'Variación angular en rad/s',positive=True)
    omega = _grid(omega_rad_s)
    def sample(offset):
        edge=nominal.astype(float)
        edge[edge_index]+=offset
        filt=bessel_prototype(order,edge,kind=kind,normalization=normalization)['systems'][0]
        ctx.checkpoint()
        return filt.response(omega),filt.group_delay(omega)
    with ctx.reserve(200*omega.size):
        central, delay=sample(0)
        low, delay_low=sample(-delta)
        high, delay_high=sample(delta)
        result={'frequencies_rad_s':omega.copy(),'nominal':central,'nominal_delay_s':delay,
                'derivative':(high-low)/2/delta,'delay_derivative':(delay_high-delay_low)/2/delta,
                'edge_index':edge_index,'perturbation_rad_s':delta}
    ctx.checkpoint()
    return result


def noise_figure_sweep(stages, stage_index, figures_db, bandwidth_hz, *, source_temperature_k=290,
                       required_snr_db=0, context=None):
    """Sweep a noise figure while holding prior gains, bandwidth and source temperature fixed."""
    ctx = context if context is not None else ExecutionContext()
    ctx.checkpoint()
    stages=tuple(stages)
    if type(stage_index) is not int or not 0<=stage_index<len(stages) or not all(isinstance(s,RFStage) for s in stages):
        raise ValueError('Identificá una etapa receptora registrada.')
    figures=_sweep_vector(figures_db)
    results=[]
    for figure in figures:
        ctx.checkpoint()
        parts=list(stages)
        parts[stage_index]=replace(stages[stage_index],noise_figure_db=figure)
        results.append(noise_cascade(parts,bandwidth_hz,source_temperature_k=source_temperature_k,
                                     required_snr_db=required_snr_db,context=ctx))
    return {'stage':stages[stage_index].name,'figures_db':figures,'noise':tuple(results)}


@dataclass(frozen=True, slots=True)
class LinkUncertainty:
    name: str
    budget: LinkBudget
    propagation_std_db: float = 0.0
    gain_std_db: float = 0.0
    noise_level_std_db: float = 0.0

    def document(self):
        if not isinstance(self.name,str) or not self.name.strip() or not isinstance(self.budget,LinkBudget):
            raise ValueError('Identificá un cálculo de enlace completo por escenario.')
        return {'name':self.name,'budget':asdict(self.budget),**{
            key:real(getattr(self,key),key,minimum=0) for key in
            ('propagation_std_db','gain_std_db','noise_level_std_db')}}


def link_campaign(scenarios, directory, *, seed, metric='mean', replicas=64, samples=128, batch=8,
                  confidence=.95, context=None):
    """Simulate independent Gaussian changes in the three additive dB terms of each budget.

    The probability measures link success (margin >= 0) within the finite binary64
    range. Replicate draws and recoverable batches use the common campaign engine.
    """
    if metric not in ('mean','probability'):
        raise ValueError('Elegí la media de margen o probabilidad de enlace operativo.')
    ctx = context if context is not None else ExecutionContext()
    ctx.checkpoint()
    definitions=[]
    rows=[]
    for scenario in scenarios:
        ctx.checkpoint()
        if not isinstance(scenario,LinkUncertainty):
            raise ValueError('La campaña requiere estudios de incertidumbre de enlace.')
        definition=scenario.document()
        sigma=math.hypot(definition['propagation_std_db'],definition['gain_std_db'],
                         definition['noise_level_std_db'])
        if not math.isfinite(sigma) or sigma==0:
            raise ValueError('Indicá al menos una incertidumbre de nivel positiva y representable.')
        distribution=Distribution('normal',{'mean':scenario.budget.margin_db,'std':sigma})
        rows.append(Scenario(scenario.name,distribution))
        definitions.append(definition)
    provenance={'operation':'rf_link_uncertainty','version':1,'scenarios':definitions,
                'assumptions':'Independent Gaussian perturbations of received gain, path loss and total receiver noise in dB.'}
    bounds={'low':0,'high':float(np.finfo(float).max)} if metric=='probability' else {}
    spec=CampaignSpec(tuple(rows),metric,seed,replicas=replicas,samples=samples,batch=batch,
                      confidence=confidence,scientific_context=json.dumps(provenance,allow_nan=False),**bounds)
    return run_campaign(spec,directory,execution=ctx)
