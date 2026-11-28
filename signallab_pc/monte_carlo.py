"""Resumable Monte Carlo designs with independent or paired random substreams."""

import csv
from dataclasses import dataclass
import io
import json
import math
from pathlib import Path
import sys

import numpy as np
from scipy import __version__ as scipy_version
from scipy.stats import t

from .atomic_file import atomic_binary_file, write_json
from .campaign_files import campaign_writer, safe_file
from .communications_data import MAX_SEED, integer, real
from .execution import ExecutionContext
from .input_files import decode_finite_json, read_json
from .operation_provenance import settings_digest
from .probability import Distribution, _MAX_EXACT_INTEGER, _moment_status, interval_probability, population
from .spectral_scaling import restore_scalar
from .statistical_inference import _binomial_interval


_FORMAT = 'signallab-monte-carlo'
_SCHEMA = 1
_MANIFEST = 'monte-carlo.json'
_BLOCK = 16_384
_MAX_REPLICAS = (1 << 32)-1
METRICS = ('probability','mean','variance')


@dataclass(frozen=True, slots=True)
class Scenario:
    name: str
    distribution: Distribution

    def __post_init__(self):
        if not isinstance(self.name,str) or not self.name.strip() or any(ch in self.name for ch in '\r\n\t'):
            raise ValueError('Cada escenario requiere un nombre para identificarlo en el informe.')
        if not isinstance(self.distribution,Distribution):
            raise ValueError('Cada escenario requiere una distribución univariada.')


@dataclass(frozen=True, slots=True)
class CampaignSpec:
    scenarios: tuple[Scenario,...]
    metric: str
    seed: int
    samples: int = 128
    replicas: int = 128
    batch: int = 16
    confidence: float = .95
    low: float | None = None
    high: float | None = None
    common_random_numbers: bool = False
    target_half_width: float | None = None
    minimum_replicas: int = 2
    scientific_context: str | None = None

    def __post_init__(self):
        scenarios = tuple(self.scenarios)
        if not scenarios or not all(isinstance(row,Scenario) for row in scenarios):
            raise ValueError('Definí al menos un escenario.')
        if len({item.name for item in scenarios}) != len(scenarios):
            raise ValueError('Usá nombres distintos para comparar escenarios.')
        if self.metric not in METRICS:
            raise ValueError('Elegí probabilidad, media o varianza.')
        if type(self.common_random_numbers) is not bool:
            raise ValueError('Indicá si los escenarios comparten números aleatorios.')
        minimum = 2 if self.metric=='variance' else 1
        samples = integer(self.samples,'Muestras por réplica',minimum=minimum,maximum=sys.maxsize)
        replicas = integer(self.replicas,'Réplicas máximas',minimum=2,maximum=_MAX_REPLICAS)
        if samples*replicas > 2**53:
            raise ValueError('La cantidad total excede el rango de recuentos exactos.')
        batch = integer(self.batch,'Réplicas por bloque',maximum=_MAX_REPLICAS)
        lower = integer(self.minimum_replicas,'Réplicas mínimas',minimum=2,maximum=replicas)
        confidence = real(self.confidence,'Nivel de confianza',positive=True)
        if confidence >= 1:
            raise ValueError('El nivel de confianza debe estar entre 0 y 1.')
        if self.metric=='probability':
            low, high = real(self.low,'Extremo inferior del evento'), real(self.high,'Extremo superior del evento')
            if low > high:
                raise ValueError('Ordená los extremos del evento.')
            object.__setattr__(self,'low',low)
            object.__setattr__(self,'high',high)
        else:
            if self.low is not None or self.high is not None:
                raise ValueError('El intervalo corresponde a una estimación de probabilidad.')
            order = 4 if self.metric=='variance' else 2
            if any(_moment_status(row.distribution,order) for row in scenarios):
                raise ValueError(f'El intervalo requiere un momento poblacional finito de orden {order}.')
        if self.target_half_width is not None:
            object.__setattr__(self,'target_half_width',real(self.target_half_width,'Semiancho objetivo',positive=True))
        if self.scientific_context is not None:
            if not isinstance(self.scientific_context,str) or len(self.scientific_context)>65536:
                raise ValueError('El contexto científico requiere un objeto JSON acotado.')
            document=decode_finite_json(self.scientific_context)
            if not isinstance(document,dict):
                raise ValueError('El contexto científico de campaña debe ser un objeto.')
            object.__setattr__(self,'scientific_context',json.dumps(document,sort_keys=True,allow_nan=False,
                                                                    separators=(',',':')))
        for key,value in (('scenarios',scenarios),('seed',integer(self.seed,'Semilla maestra',minimum=0,maximum=MAX_SEED)),
                          ('samples',samples),('replicas',replicas),('batch',batch),('minimum_replicas',lower),
                          ('confidence',confidence)):
            object.__setattr__(self,key,value)

    def document(self):
        names = ('metric','seed','samples','replicas','batch','confidence','low','high','common_random_numbers',
                 'target_half_width','minimum_replicas')
        document={**{key:getattr(self,key) for key in names},
                  'scenarios':[{'name':row.name,'family':row.distribution.family,
                                'parameters':dict(row.distribution.parameters)} for row in self.scenarios]}
        if self.scientific_context is not None:
            document['scientific_context']=self.scientific_context
        return document


def campaign_spec(document):
    if not isinstance(document,dict) or not isinstance(document.get('scenarios'),list):
        raise ValueError('La configuración requiere una lista de escenarios.')
    rows = tuple(Scenario(row['name'],Distribution(row['family'],row['parameters'])) for row in document['scenarios'])
    return CampaignSpec(rows,**{key:value for key,value in document.items() if key!='scenarios'})


@dataclass(frozen=True, slots=True)
class CampaignResult:
    folder: Path
    spec: CampaignSpec
    fingerprint: str
    replicas: tuple
    report: dict


def _definition(spec):
    return {'format':_FORMAT,'schema':_SCHEMA,'specification':spec.document(),
            'numpy':np.__version__,'scipy':scipy_version,'generator':'PCG64',
            'kernel_draw_block':_BLOCK,'seed_rule':'spawn=(replica, scenario) or spawn=(replica,) for shared uniform draws'}


def _draw_row(spec,index,context):
    output = []
    for ordinal,row in enumerate(spec.scenarios):
        spawn_key = (index,) if spec.common_random_numbers else (index,ordinal)
        rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(spec.seed,spawn_key=spawn_key)))
        law = row.distribution._backend
        hits = 0
        exponent = 0
        mean = variance = 0.
        for first in range(0,spec.samples,_BLOCK):
            context.checkpoint()
            size = min(_BLOCK,spec.samples-first)
            if spec.common_random_numbers:
                uniform = np.maximum(rng.random(size),np.nextafter(0.,1.))
                values = law.ppf(uniform)
            else:
                values = law.rvs(size=size,random_state=rng)
            if not np.all(np.isfinite(values)):
                raise FloatingPointError('El modelo generó una muestra fuera del rango numérico.')
            if row.distribution.discrete and np.any((values>_MAX_EXACT_INTEGER)|(values<-_MAX_EXACT_INTEGER)):
                raise FloatingPointError('Una muestra discreta excede la representación entera exacta.')
            if spec.metric=='probability':
                hits += int(np.count_nonzero((values>=spec.low)&(values<=spec.high)))
                continue
            peak = float(np.max(abs(values),initial=0.))
            _, block_exponent = math.frexp(peak)
            target_exponent = block_exponent
            if first and (mean or variance):
                target_exponent = max(exponent,block_exponent) if peak else exponent
            with np.errstate(under='ignore'):
                normalized = np.ldexp(np.asarray(values,dtype=float),-target_exponent)
            mean = math.ldexp(mean,exponent-target_exponent)
            variance = math.ldexp(variance,2*(exponent-target_exponent))
            offset = normalized[0]
            centered = normalized-offset
            block_mean = float(centered.mean())
            ratio = size/(first+size)
            delta = (offset-mean)+block_mean
            variance = (1-ratio)*variance+ratio*(float(np.var(centered))+(1-ratio)*delta**2)
            mean += ratio*delta
            exponent = target_exponent
        if spec.metric=='probability':
            output.append(hits)
        else:
            value = restore_scalar(mean,exponent) if spec.metric=='mean' else restore_scalar(
                variance,2*exponent,spec.samples/(spec.samples-1))
            if not math.isfinite(value):
                raise FloatingPointError('La réplica tiene un estimador fuera del rango numérico.')
            output.append(value)
    return tuple(output)


def _reference(scenario,spec):
    if spec.metric=='probability':
        return interval_probability(scenario.distribution,spec.low,spec.high)
    return population(scenario.distribution)[spec.metric]


def _interval(values,tail):
    vector = np.asarray(values,dtype=float)
    _, exponent = math.frexp(float(np.max(abs(vector),initial=0.)))
    scaled = np.ldexp(vector,-exponent)
    mean = float(scaled.mean())
    center = restore_scalar(mean,exponent)
    if len(vector)<2:
        return center,None,None
    standard = float(scaled.std(ddof=1))/math.sqrt(len(vector))
    radius = t.isf(tail,len(vector)-1)*standard
    lower,upper = (restore_scalar(value,exponent) for value in (mean-radius,mean+radius))
    return center,(lower if math.isfinite(lower) else None,upper if math.isfinite(upper) else None),restore_scalar(standard,exponent)


def _tail(spec):
    looks = math.ceil(spec.replicas/spec.batch) if spec.target_half_width is not None else 1
    return (1-spec.confidence)/(2*looks*len(spec.scenarios))


def _estimates(spec, replicas):
    count = len(replicas)
    if count==0:
        return []
    total = count*spec.samples
    tail = _tail(spec)
    results = []
    for scenario,values in zip(spec.scenarios,zip(*replicas,strict=True),strict=True):
        if spec.metric=='probability':
            successes = sum(values)
            interval = _binomial_interval(successes,total,tail)
            evidence = 'sin eventos observados' if successes==0 else 'pocos eventos' if successes<30 else 'eventos observados'
            row = {'value':successes/total,'interval':interval,'successes':successes,'trials':total,
                   'evidence':evidence,'calibration':'Clopper–Pearson bilateral por escenario'}
        else:
            value,interval,standard = _interval(values,tail)
            row = {'value':value,'interval':interval,'standard_error':standard,
                   'calibration':'intervalo t por réplicas, aproximado'}
        results.append({'scenario':scenario.name,'replicas':count,**row})
    return results


def _precision(spec,rows):
    if spec.target_half_width is None or len(rows)<spec.minimum_replicas:
        return False
    return all(row['interval'] is not None and all(bound is not None for bound in row['interval'])
               and .5*row['interval'][1]-.5*row['interval'][0] <= spec.target_half_width
               for row in _estimates(spec,rows))


def _report(spec,rows,fingerprint):
    summaries = _estimates(spec,rows)
    for row,scenario in zip(summaries,spec.scenarios):
        row['theory'] = _reference(scenario,spec)
    count = len(rows)
    status = 'max_replicas' if count==spec.replicas else 'target_precision' if _precision(spec,rows) else 'incomplete'
    comparisons = []
    if summaries:
        scale = spec.samples if spec.metric=='probability' else 1
        pairing = 'números aleatorios comunes, diferencias por réplica' if spec.common_random_numbers else 'escenarios independientes'
        for first,second in zip(range(len(summaries)-1),range(1,len(summaries))):
            differences = [row[second]/scale-row[first]/scale for row in rows]
            if not all(math.isfinite(value) for value in differences):
                comparisons.append({'first':summaries[first]['scenario'],'second':summaries[second]['scenario'],
                                    'value':None,'interval':None,'standard_error':None,'status':'overflow','pairing':pairing})
                continue
            value, interval, error = _interval(differences,(1-spec.confidence)/2)
            comparisons.append({'first':summaries[first]['scenario'],'second':summaries[second]['scenario'],
                                'value':value,'interval':interval if spec.target_half_width is None else None,
                                'standard_error':error,'pairing':pairing,
                                'calibration':'intervalo t marginal aproximado, disponible con cantidad fija de réplicas'})
    return {'schema':_SCHEMA,'operation':'monte_carlo','settings_sha256':fingerprint,'status':status,
            'specification':spec.document(),'replicas':count,'confidence':spec.confidence,
            'summaries':summaries,'differences':comparisons,
            'scope':'Las bandas binomiales usan Bonferroni para los escenarios y las revisiones planificadas. '
                    'Los intervalos t son aproximados para resultados por réplica. Cero eventos mantiene una cota superior positiva.'}


def _read_batches(folder,spec,fingerprint,context):
    rows, previous = [], fingerprint
    batches = sorted(folder.glob('batch-*.json'))
    for index,path in enumerate(batches):
        context.checkpoint()
        expected = f'batch-{index:010d}.json'
        if path.name!=expected or _precision(spec,rows):
            raise ValueError('La secuencia de bloques no coincide con la campaña.')
        document = read_json(safe_file(folder,expected),checkpoint=context.checkpoint)
        if not isinstance(document,dict):
            raise ValueError('El bloque de réplicas debe ser un objeto.')
        data = document.get('rows')
        remaining = spec.replicas-len(rows)
        if remaining<=0 or not isinstance(data,list) or len(data)!=min(spec.batch,remaining):
            raise ValueError('La cantidad de réplicas del bloque es incompatible.')
        for row in data:
            if not isinstance(row,list) or len(row)!=len(spec.scenarios):
                raise ValueError('Cada réplica requiere un resultado por escenario.')
            for value in row:
                if spec.metric=='probability':
                    integer(value,'Eventos de la réplica',minimum=0,maximum=spec.samples)
                else:
                    real(value,'Estimación de la réplica',minimum=0 if spec.metric=='variance' else None)
        stamp = settings_digest([previous,len(rows),data])
        if document.get('sha256')!=stamp:
            raise ValueError('La huella del bloque de réplicas no coincide.')
        rows.extend(tuple(row) for row in data)
        previous = stamp
    return rows,len(batches),previous


def _prepare(folder,spec,context):
    path = safe_file(folder,_MANIFEST)
    definition = _definition(spec)
    stamp = settings_digest(definition)
    if path.exists():
        recorded = read_json(path,checkpoint=context.checkpoint)
        if recorded != {'definition':definition,'sha256':stamp}:
            raise ValueError('La campaña existente usa otra configuración o versiones numéricas.')
    else:
        if any(folder.glob('batch-*.json')):
            raise ValueError('Hay bloques sin su definición de campaña.')
        write_json(path,{'definition':definition,'sha256':stamp},before_commit=context.checkpoint,checkpoint=context.checkpoint)
    return stamp


def load_campaign(directory,execution=None):
    """Verify a complete or interrupted campaign, without changing its files."""
    context = execution or ExecutionContext()
    folder = Path(directory).resolve()
    record = read_json(safe_file(folder,_MANIFEST),checkpoint=context.checkpoint)
    definition = record.get('definition') if isinstance(record,dict) else None
    if not isinstance(definition,dict) or definition.get('format')!=_FORMAT or definition.get('schema')!=_SCHEMA:
        raise ValueError('Formato de campaña Monte Carlo incompatible.')
    spec = campaign_spec(definition['specification'])
    stamp = settings_digest(definition)
    if record.get('sha256') != stamp:
        raise ValueError('La huella de la campaña no coincide.')
    with context.reserve(160*spec.replicas*len(spec.scenarios)):
        rows,_,_ = _read_batches(folder,spec,stamp,context)
        return CampaignResult(folder,spec,stamp,tuple(rows),_report(spec,rows,stamp))


def run_campaign(spec,directory,execution=None):
    """Commit only complete batches of replicate summaries and resume deterministically."""
    if not isinstance(spec,CampaignSpec):
        raise TypeError('Indicá la configuración de Monte Carlo.')
    context = execution or ExecutionContext()
    folder = Path(directory).resolve()
    work = 160*spec.replicas*len(spec.scenarios)+128*min(spec.samples,_BLOCK)
    with context.reserve(work):
        folder.mkdir(parents=True,exist_ok=True)
        with campaign_writer(folder,operation='estudio',filename='monte-carlo.lock'):
            stamp = _prepare(folder,spec,context)
            rows,batch,previous = _read_batches(folder,spec,stamp,context)
            while len(rows)<spec.replicas and not _precision(spec,rows):
                end = min(len(rows)+spec.batch,spec.replicas)
                data = []
                for index in range(len(rows),end):
                    context.checkpoint(100*index//spec.replicas)
                    data.append(_draw_row(spec,index,context))
                digest = settings_digest([previous,len(rows),data])
                path = safe_file(folder,f'batch-{batch:010d}.json')
                write_json(path,{'rows':data,'sha256':digest},before_commit=context.checkpoint,checkpoint=context.checkpoint)
                rows.extend(data)
                batch += 1
                previous = digest
            context.checkpoint(100)
            return CampaignResult(folder,spec,stamp,tuple(rows),_report(spec,rows,stamp))


def validate_campaign_destination(path, directory, extension):
    """Preserve the directory and its catalog when writing a derived file."""
    path = Path(path)
    destination = path.resolve()
    folder = Path(directory).resolve()
    if (destination == folder or destination.is_dir()
            or (destination.parent == folder and destination.suffix.lower() != extension)):
        raise ValueError('Elegí una salida distinta de la carpeta de campaña y sus archivos internos.')
    return path


def export_campaign_csv(result,path,execution=None):
    context = execution or ExecutionContext()
    path = validate_campaign_destination(path, result.folder, '.csv')
    with atomic_binary_file(path,before_commit=context.checkpoint) as handle:
        text = io.TextIOWrapper(handle,encoding='utf-8',newline='')
        try:
            writer = csv.writer(text)
            writer.writerow(['replica',*[f'Escenario: {row.name}' for row in result.spec.scenarios]])
            for index,values in enumerate(result.replicas,1):
                context.checkpoint()
                writer.writerow([index,*values])
            text.flush()
        finally:
            text.detach()


def campaign_trajectory(result,points=256):
    """Return prefix estimates at evenly distributed replicate counts."""
    size = len(result.replicas)
    if not size:
        return np.empty(0,dtype=int), np.empty((0,len(result.spec.scenarios)))
    counts = np.unique(np.linspace(1,size,min(size,points),dtype=int))
    values = np.asarray(result.replicas,dtype=float)
    if result.spec.metric=='probability':
        return counts,np.cumsum(values,axis=0)[counts-1]/(counts[:,None]*float(result.spec.samples))
    _, exponent = np.frexp(np.max(abs(values),axis=0))
    with np.errstate(under='ignore'):
        cumulative = np.cumsum(np.ldexp(values,-exponent),axis=0)/np.arange(1,size+1)[:,None]
        return counts,np.ldexp(cumulative[counts-1],exponent)


def store_campaign(project,result,*,execution=None,tool=None):
    """Archive the report and completed replica summaries in the project."""
    context = execution or ExecutionContext()
    with context.reserve(96*len(result.replicas)*len(result.spec.scenarios)):
        rows = [list(row) for row in result.replicas]
        payload = {**result.report,'replicate_summaries':rows,'replicate_sha256':settings_digest(rows)}
        proof = settings_digest(['calculation',payload])
        with project.stage_records(before_commit=context.checkpoint) as stage:
            return stage.add(payload,title='Campaña de Monte Carlo',operation='Medir incertidumbre por simulación',
                             tool=tool,verification=(proof,(),context.checkpoint))
