"""Shared RF request and result boundary for Python, CLI and the Workbench."""

from dataclasses import dataclass, fields, is_dataclass
import json
import math

import numpy as np

from .execution import ExecutionContext
from .input_files import decode_finite_json
from .model import Signal
from .operation_provenance import content_digest, encoded_digest, settings_digest
from .rf_analysis import cascade, measure, terminate
from .rf_line import rlgc_line, uniform_line
from .rf_link import RFStage, characterize_device, link_budget, noise_cascade
from .rf_matching import evaluate_matching, synthesize_matching
from .rf_network import RFNetwork, convert, interpolate, renormalize
from .rf_storage import encode_network, load_network, store_network


_NETWORK_ARITY = {
    'analyze':1, 'convert':1, 'renormalize':1, 'interpolate':1, 'cascade':2, 'terminate':1,
}
_NO_INPUT = ('define','line','rlgc','match','link','noise','device','bessel','window',
             'matching_sweep','noise_sweep','bessel_sensitivity','link_campaign')
OPERATIONS = (*_NETWORK_ARITY, *_NO_INPUT, 'zoom', 'czt')


@dataclass(frozen=True, slots=True, init=False)
class RFRequest:
    operation: str
    _parameters: str

    def __init__(self, operation, parameters=None):
        if operation not in OPERATIONS or (parameters is not None and not isinstance(parameters,dict)):
            raise ValueError('Operación RF o parámetros de solicitud desconocidos.')
        try:
            encoded=json.dumps(parameters or {},sort_keys=True,allow_nan=False,separators=(',',':'))
        except (TypeError,ValueError,OverflowError) as exc:
            raise ValueError('Los parámetros deben ser un objeto JSON finito.') from exc
        object.__setattr__(self,'operation',operation)
        object.__setattr__(self,'_parameters',encoded)

    @property
    def parameters(self):
        return decode_finite_json(self._parameters)

    def document(self):
        return {'schema':1,'operation':self.operation,'parameters':self.parameters}

    @classmethod
    def from_document(cls, document):
        if (not isinstance(document,dict) or set(document)!={'schema','operation','parameters'}
                or type(document['schema']) is not int or document['schema']!=1):
            raise ValueError('La solicitud requiere schema 1, operation y parameters.')
        return cls(document['operation'],document['parameters'])


def _complex_pairs(value):
    pairs=np.asarray(value)
    if pairs.ndim < 1 or pairs.shape[-1]!=2 or pairs.dtype.kind not in 'fiu' or not np.isfinite(pairs).all():
        raise ValueError('Usá pares [parte real, parte imaginaria] finitos.')
    return np.asarray(pairs[...,0],dtype=float)+1j*np.asarray(pairs[...,1],dtype=float)


def _stages(rows):
    if not isinstance(rows,(tuple,list)) or len(rows)>128 or any(not isinstance(row,dict) for row in rows):
        raise ValueError('La cadena admite hasta 128 objetos de etapa con ganancia y ruido o pérdida pasiva.')
    return tuple(RFStage.passive(**row) if 'loss_db' in row else RFStage(**row) for row in rows)


def _propagation(document):
    from .communications_propagation import FreeSpaceLoss, LogDistanceLoss, PropagationSpec
    if not isinstance(document,dict):
        raise ValueError('Indicá un objeto de propagación.')
    parameters=dict(document)
    model=parameters.pop('model',None)
    if model is not None:
        if not isinstance(model,dict):
            raise ValueError('El modelo de propagación requiere un objeto.')
        settings=dict(model)
        name=settings.pop('kind',None)
        if name=='free_space':
            model=FreeSpaceLoss(**settings)
        elif name=='log_distance':
            model=LogDistanceLoss(**settings)
        else:
            raise ValueError('Elegí espacio libre, log-distancia o ganancia fija.')
    return PropagationSpec(model,**parameters)


def _input_digest(value, ctx):
    if isinstance(value,RFNetwork):
        return encoded_digest('calculation',encode_network(value,context=ctx),ctx.checkpoint)
    return content_digest(value,ctx.checkpoint)


def _portable(value, *, vectors):
    if isinstance(value,Signal):
        result={'name':value.name,'units':value.units,'length':len(value.values),'metadata':value.metadata}
        if vectors:
            result.update(axis=_portable(value.axis,vectors=True),values=_portable(value.values,vectors=True))
        return result
    if isinstance(value,RFNetwork):
        result={'name':value.name,'representation':value.representation,'wave_convention':value.wave_convention,
                'ports':list(value.port_names),'frequencies':len(value.frequencies_hz),'frequency_unit':'Hz'}
        if vectors:
            result.update(hz=_portable(value.frequencies_hz,vectors=True),
                          reference_ohm=_portable(value.reference_ohm,vectors=True),
                          values=_portable(value.values,vectors=True))
        return result
    if is_dataclass(value):
        return {field.name:_portable(getattr(value,field.name),vectors=vectors) for field in fields(value)
                if vectors or not isinstance(getattr(value,field.name),np.ndarray)}
    if isinstance(value,np.ndarray):
        return _portable(value.tolist(),vectors=True) if vectors else {'shape':list(value.shape)}
    if isinstance(value,(tuple,list)):
        return [_portable(item,vectors=vectors) for item in value]
    if isinstance(value,dict):
        return {key:_portable(item,vectors=vectors) for key,item in value.items() if key!='systems'}
    if isinstance(value,complex):
        return [value.real,value.imag] if np.isfinite(value) else None
    if isinstance(value,(np.integer,np.floating,np.bool_)):
        return _portable(value.item(),vectors=vectors)
    if isinstance(value,float) and not math.isfinite(value):
        return None
    return value


@dataclass(frozen=True, slots=True)
class RFResult:
    request: RFRequest
    input_hashes: tuple[str,...]
    data: object
    sources: tuple
    product_hash: str | None
    network: RFNetwork | None = None
    signal: Signal | None = None
    system: object = None

    def document(self, *, vectors=False):
        specification=self.request.document()
        data=self.data.report if self.request.operation=='link_campaign' else self.data
        return {'schema':1,'operation':self.request.operation,'request':specification,
                'request_sha256':settings_digest(specification),'input_sha256':list(self.input_hashes),
                'product_sha256':self.product_hash,
                'result':_portable(data,vectors=vectors)}


def _execute(request, inputs, ctx):
    operation=request.operation
    settings=request.parameters
    if operation in _NETWORK_ARITY:
        if len(inputs)!=_NETWORK_ARITY[operation] or any(not isinstance(net,RFNetwork) for net in inputs):
            raise ValueError('La operación requiere las redes RF indicadas como entradas.')
        if operation=='analyze':
            return measure(*inputs,context=ctx,**settings), inputs[0], None, None
        if 'load_ohm_pairs' in settings:
            settings['load_ohm']=_complex_pairs(settings.pop('load_ohm_pairs'))
        if 'reflection_pairs' in settings:
            settings['reflection']=_complex_pairs(settings.pop('reflection_pairs'))
        function={'convert':convert,'renormalize':renormalize,'interpolate':interpolate,
                  'cascade':cascade,'terminate':terminate}[operation]
        network=function(*inputs,context=ctx,**settings)
        return network,network,None,None
    if operation in ('zoom','czt'):
        from .advanced_fourier import chirp_z, zoom_fft
        if len(inputs)!=1 or not isinstance(inputs[0],Signal):
            raise ValueError('La transformada requiere una señal temporal discreta.')
        if operation=='zoom':
            result=zoom_fft(inputs[0],context=ctx,**settings)
            return result,None,result.spectrum,None
        result=chirp_z(inputs[0],context=ctx,**settings)
        return result,None,result.samples,None
    if inputs:
        raise ValueError('La operación calcula desde sus parámetros, sin entradas adicionales.')
    if operation=='define':
        settings['values']=_complex_pairs(settings.pop('value_pairs',None))
        network=RFNetwork(context=ctx,**settings)
        return network,network,None,None
    if operation in ('line','rlgc','match'):
        if 'load_ohm_pairs' in settings:
            settings['load_ohm']=_complex_pairs(settings.pop('load_ohm_pairs')).item() if operation=='match' else (
                _complex_pairs(settings.pop('load_ohm_pairs')))
        if operation=='match':
            grid = settings.pop('frequencies_hz')
            designs=synthesize_matching(**settings)
            evaluated=tuple(evaluate_matching(design,grid,context=ctx) for design in designs)
            return {'designs':designs,'responses':evaluated},evaluated[0].network,None,None
        result=(uniform_line if operation=='line' else rlgc_line)(context=ctx,**settings)
        return result,result.network,None,None
    if operation=='link':
        return _link(settings,ctx),None,None,None
    if operation=='noise':
        settings['stages']=_stages(settings.get('stages',[]))
        return noise_cascade(context=ctx,**settings),None,None,None
    if operation=='device':
        return characterize_device(**settings),None,None,None
    if operation in ('matching_sweep','noise_sweep','bessel_sensitivity','link_campaign'):
        return _experiment(operation,settings,ctx),None,None,None
    if operation=='bessel':
        from .analog_design import bessel_prototype
        result=ctx.run(lambda:bessel_prototype(**settings))
        return result,None,None,result['systems'][0]
    from .window_signals import generate_window
    result=ctx.run(lambda:generate_window(**settings))
    return result,None,result,None


def _link(settings,ctx):
    path=_propagation(settings.pop('propagation',{}))
    for key in ('transmit_stages','receive_stages'):
        if key in settings:
            settings[key]=_stages(settings[key])
    return link_budget(propagation=path,context=ctx,**settings)


def _experiment(operation,settings,ctx):
    from .rf_experiments import (
        LinkUncertainty,bessel_sensitivity,link_campaign,matching_sweep,noise_figure_sweep,
    )
    if operation=='matching_sweep':
        design=dict(settings.pop('design'))
        design['load_ohm']=_complex_pairs(design.pop('load_ohm_pairs')).item()
        solutions=synthesize_matching(**design)
        from .communications_data import integer
        index=integer(settings.pop('solution',0),'Solución a evaluar',minimum=0,maximum=len(solutions)-1)
        return matching_sweep(solutions[index],context=ctx,**settings)
    if operation=='noise_sweep':
        settings['stages']=_stages(settings.get('stages',[]))
        return noise_figure_sweep(context=ctx,**settings)
    if operation=='bessel_sensitivity':
        return bessel_sensitivity(context=ctx,**settings)
    rows=settings.pop('scenarios')
    if not isinstance(rows,list) or not 1<=len(rows)<=16:
        raise ValueError('Una campaña RF admite entre uno y 16 escenarios.')
    scenarios=[]
    for row in rows:
        ctx.checkpoint()
        definition=dict(row)
        baseline=_link(dict(definition.pop('link')),ctx)
        scenarios.append(LinkUncertainty(budget=baseline,**definition))
    return link_campaign(scenarios,context=ctx,**settings)


def run_rf(request: RFRequest, inputs=(), *, context=None) -> RFResult:
    if not isinstance(request,RFRequest):
        raise TypeError('La frontera RF requiere una solicitud RFRequest.')
    ctx = context if context is not None else ExecutionContext()
    ctx.checkpoint()
    sources=tuple(inputs)
    hashes=tuple(_input_digest(value,ctx) for value in sources)
    try:
        data,network,signal,system=_execute(request,sources,ctx)
    except (KeyError,TypeError) as exc:
        raise ValueError('La operación RF tiene parámetros incompletos o desconocidos.') from exc
    if tuple(_input_digest(value,ctx) for value in sources)!=hashes:
        raise ValueError('Una entrada cambió durante el cálculo RF.')
    ctx.checkpoint()
    product=next((value for value in (network,signal,system) if value is not None),None)
    product_hash=_input_digest(product,ctx) if product is not None else None
    return RFResult(request,hashes,data,sources,product_hash,network,signal,system)


def store_rf(project, result: RFResult, *, source_ids=(), tool=None, context=None):
    """Commit result and source relations as a single transaction."""
    ctx=context if context is not None else ExecutionContext()
    sources=result.sources
    ids=tuple(source_ids) if source_ids else (None,)*len(sources)
    if len(ids)!=len(sources) or tuple(_input_digest(value,ctx) for value in sources)!=result.input_hashes:
        raise ValueError('Las entradas ya no coinciden con la solicitud RF.')
    product_value=next((item for item in (result.network,result.signal,result.system) if item is not None),None)
    if product_value is not None and _input_digest(product_value,ctx)!=result.product_hash:
        raise ValueError('El resultado RF cambió después del cálculo.')
    operation='RF · '+result.request.operation
    with project.stage_records(before_commit=ctx.checkpoint) as staged:
        parent_ids=[]
        for value,key,expected in zip(sources,ids,result.input_hashes,strict=True):
            if key is not None:
                row=staged._records.get(key)
                stored=(_input_digest(load_network(staged,key,context=ctx),ctx)
                        if isinstance(value,RFNetwork) and row is not None else
                        staged._record_digest(row,ctx.checkpoint) if row is not None else None)
                if stored!=expected:
                    raise ValueError('La entrada del proyecto no coincide con la usada en el cálculo RF.')
            elif isinstance(value,RFNetwork):
                key=store_network(staged,value,operation='Entrada RF',tool=tool,context=ctx)
            else:
                key=staged.add(value,operation='Entrada RF',tool=tool,verification=(expected,(),ctx.checkpoint))
            parent_ids.append(key)
        product=None
        alternatives=[]
        if result.request.operation=='link_campaign':
            from .monte_carlo import store_campaign
            product=store_campaign(staged,result.data,execution=ctx,tool=tool)
        if result.network is not None:
            product=next((key for source,key in zip(sources,parent_ids,strict=True) if source is result.network),None)
            if product is None:
                product=store_network(staged,result.network,parents=parent_ids,operation=operation,
                                      settings=result.request.document(),tool=tool,context=ctx)
            if result.request.operation=='match':
                for index,response in enumerate(result.data['responses'][1:],2):
                    alternatives.append(store_network(staged,response.network,parents=parent_ids,operation=operation,
                                        settings={**result.request.document(),'solution':index},tool=tool,context=ctx))
        else:
            if product_value is not None:
                parent_ids=list(dict.fromkeys(parent_ids))
                hashes=tuple(staged._record_digest(staged._records[key],ctx.checkpoint) for key in parent_ids)
                product=staged.add(product_value,operation=operation,parents=parent_ids,tool=tool,
                                   verification=(content_digest(product_value,ctx.checkpoint),hashes,ctx.checkpoint))
        reports=list(dict.fromkeys(parent_ids+([product] if product else [])+alternatives))
        document=result.document()
        hashes=tuple(staged._record_digest(staged._records[key],ctx.checkpoint) for key in reports)
        receipt=staged.add(document,title=operation,operation=operation,parents=reports,tool=tool,
                           verification=(encoded_digest('calculation',document,ctx.checkpoint),hashes,ctx.checkpoint))
    return {'result_id':receipt,'product_id':product,'source_ids':parent_ids,'alternative_ids':alternatives}
