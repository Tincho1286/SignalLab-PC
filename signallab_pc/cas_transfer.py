"""Prepare typed result data for the CAS without evaluating mathematics in the UI."""
from dataclasses import is_dataclass,asdict
import math
import numpy as np
from .model import Signal
from .filters import Transfer
from .state_space import StateModel
from .result_expressions import expression_result
from .resources import ensure_working_set


def can_send(value):
    if isinstance(value,(Signal,Transfer,StateModel)):return True
    if isinstance(value,dict) and (expression_result(value) is not None or 'cas_answer' in value):return True
    if is_dataclass(value):return can_send(asdict(value))
    if isinstance(value,(int,float,complex,np.number,np.ndarray)):return True
    if isinstance(value,dict) and value.get('format')=='signallab-expression-grid':return False
    if isinstance(value,dict):return 'record' in value or any(can_send(v) for k,v in value.items() if k not in ('request','report','specifications'))
    if isinstance(value,(tuple,list)):return any(can_send(v) for v in value)
    return False


def payload(value,window=None,seen=None):
    seen=set() if seen is None else seen
    if isinstance(value,dict):
        if value.get('format')=='signallab-expression-grid':raise ValueError('Este registro contiene posiciones no definidas. Enviá la expresión algebraica al CAS; no se descartan las filas N/D.')
        if 'cas_answer' in value and value['cas_answer'].get('encoded_value'):
            answer=value['cas_answer'];return {'kind':'encoded','encoded':answer['encoded_value'],'conditions':answer.get('notices',[]),'provenance':answer.get('provenance'),'frequency_units':answer.get('frequency_units',''),'frequency_condition':answer.get('frequency_condition','True'),'coordinate_variable':answer.get('coordinate_variable'),'system_context':answer.get('system_context'),'domain_condition':answer.get('domain_condition'),'context_rewrite':answer.get('context_rewrite')}
        expression=expression_result(value)
        if expression is not None:
            from .transform_context import result_roc,result_period
            from .cas_system_context import origin
            return {'kind':'expression','source':expression.source,'variable':expression.variable,'conditions':list(expression.conditions),'system_roc':result_roc(value),'period':result_period(value),'system_origin':origin(value),
                    'domain_condition':value.get('result',{}).get('cas_domain_condition'),
                    'encoded':value.get('result',{}).get('cas_encoded'),'numeric_source':expression.numerical_source,'frequency_units':expression.units,'frequency_condition':value.get('cas_answer',{}).get('frequency_condition',value.get('result',{}).get('frequency_condition',value.get('result',{}).get('condition','True'))),'provenance':{name:value.get('result',{}).get(name) for name in ('input_definition','calculation_notes','calculation_status') if name in value.get('result',{})}}
        if isinstance(value.get('result'),dict) and value['result'].get('operation')=='signal_measures_expression':
            data={name:{'expression':value['result'][name]['exact']} for name in ('energy','mean_square','rms')}
            return {'kind':'measures','items':data,'conditions':[value['result']['scope'],value['result']['classification']]}
        if 'calculated_data' in value:return payload(value['calculated_data'],window,seen)
    def pairs(values):return [[float(complex(v).real),float(complex(v).imag)] for v in values]
    if isinstance(value,Transfer):
        return {'kind':'system','b':pairs(value.b),'a':pairs(value.a),'domain':value.domain,'advance':value.advance,'period':value.sample_period_s,'roc':value.roc}
    if isinstance(value,Signal):
        ensure_working_set(int(value.values.size),bytes_per_sample=2048,live_arrays=4)
        from .distributions import dirac_terms
        return {'kind':'samples','axis':[int(v) if value.domain=='discrete' else float(v) for v in value.axis],
                'values':pairs(value.values),'units':value.units,'domain':value.domain,
                'dirac':[[float(t),[float(w.real),float(w.imag)]] for t,w in dirac_terms(value)]}
    if isinstance(value,StateModel):
        return {'kind':'states','matrices':[{'rows':v.shape[0],'cols':v.shape[1],'values':pairs(v.reshape(-1))} for v in (value.A,value.B,value.C,value.D)],'period':value.dt}
    if is_dataclass(value):value=asdict(value)
    if isinstance(value,np.ndarray):
        ensure_working_set(value.size,bytes_per_sample=2048,live_arrays=4)
        if value.ndim<=2:
            return {'kind':'matrix','rows':value.shape[0] if value.ndim else 1,'cols':value.shape[1] if value.ndim==2 else 1,'values':pairs(value.reshape(-1))}
        value=value.tolist()
    if isinstance(value,np.generic):value=value.item()
    if isinstance(value,complex):return {'kind':'complex','value':[value.real,value.imag]}
    if isinstance(value,(bool,int,float)):
        if isinstance(value,float) and not math.isfinite(value):return {'kind':'expression','source':'oo' if value>0 else '-oo' if value<0 else 'nan','conditions':[]}
        return {'kind':'number','value':value}
    if isinstance(value,dict):
        if 'record' in value and window is not None:
            key=value['record']
            if key in seen:raise ValueError('Referencia circular en los resultados.')
            return payload(window.project.get(key),window,seen|{key})
        if set(value)=={'real','imag'}:return {'kind':'complex','value':[value['real'],value['imag']]}
        if set(value)>={'shape','values'} and 'dtype' in value:
            shape=value['shape']
            if len(shape)<=2:return {'kind':'matrix','rows':shape[0] if shape else 1,'cols':shape[1] if len(shape)==2 else 1,'values':[v if isinstance(v,list) else [v,0] for v in value['values']]}
        items={}
        for key,item in value.items():
            if key in ('request','report','type','operation','scope','classification','specifications'):continue
            converted=payload(item,window,seen)
            if converted is not None:items[str(key)]=converted
        return {'kind':'mapping','items':items} if items else None
    if isinstance(value,(tuple,list)):
        items=[payload(v,window,seen) for v in value];items=[v for v in items if v is not None]
        return {'kind':'list','items':items} if items else None
    return None


def send_to_cas(window,key=None,*,value=None,label=None):
    from PySide6.QtWidgets import QMessageBox
    try:
        if value is None:
            if key is None:raise ValueError('Calculá o seleccioná un resultado primero.')
            value=window.project.get(key)
        data=payload(value,window)
        if data is None:raise ValueError('Este informe no contiene una expresión ni valores matemáticos para el CAS.')
        if key is not None and data.get('kind')=='expression' and data.get('variable')=='z' and data.get('period') is None:data['period']=window.project.sample_period(key)
        if label is None:
            label=next((r['title'] for r in window.project.headers() if r['id']==key),getattr(value,'name','Resultado calculado'))
        window.open_cas();page=window.pages[window.current_operation];page.import_result(data,label,key)
    except (ValueError,TypeError,KeyError,MemoryError,OverflowError) as exc:QMessageBox.warning(window,'No se pudo enviar al CAS',str(exc))
