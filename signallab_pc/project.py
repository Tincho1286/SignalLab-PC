"""Proyecto compartido: instantáneas tipadas, procedencia y persistencia atómica."""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import json
from .model import Signal
from .atomic_file import write_json
from .filters import Transfer
from .state_space import StateModel


def encode(value):
    if isinstance(value, Signal):
        return 'signal', dict(values=[[float(v.real),float(v.imag)] for v in value.values],
            origin=value.origin,step=value.step,units=value.units,name=value.name,
            domain=value.domain,expression=value.expression,metadata=deepcopy(value.metadata))
    if isinstance(value, Transfer):
        return 'system', dict(b=[[float(v.real),float(v.imag)] for v in value.b],
            a=[[float(v.real),float(v.imag)] for v in value.a],domain=value.domain,name=value.name,sos=value.sos.tolist() if value.sos is not None else None,advance=value.advance,sample_period_s=value.sample_period_s,roc=deepcopy(value.roc))
    if isinstance(value,StateModel):
        data={'dt':value.dt,'name':value.name}
        for key in ('A','B','C','D'):
            matrix=getattr(value,key)
            data[key]={'shape':list(matrix.shape),'values':[[float(z.real),float(z.imag)] for z in matrix.reshape(-1)]}
        return 'state_space',data
    if isinstance(value,dict):return 'calculation',deepcopy(value)
    raise TypeError('Tipo de objeto no admitido en el proyecto.')


def decode(kind,data):
    data=deepcopy(data)
    if kind=='signal':
        data['values']=[complex(*v) for v in data['values']];return Signal(**data)
    if kind=='system':
        data['b']=[complex(*v) for v in data['b']];data['a']=[complex(*v) for v in data['a']];return Transfer(**data)
    if kind=='state_space':
        import numpy as np
        for key in ('A','B','C','D'):
            matrix=data[key];data[key]=np.array([complex(*z) for z in matrix['values']]).reshape(matrix['shape'])
        return StateModel(**data)
    if kind=='calculation' and isinstance(data,dict):return data
    raise ValueError('Tipo de registro desconocido.')


class Project:
    def __init__(self):
        self._records={};self.dirty=False
    def add(self,value,*,title=None,operation='',parents=(),tool=None):
        kind,data=encode(value)
        parents=list(dict.fromkeys(parents))
        if any(parent not in self._records for parent in parents):raise ValueError('Origen no registrado en el proyecto.')
        record=dict(id=uuid4().hex,kind=kind,title=title or getattr(value,'name','Cálculo'),
                    operation=operation,parents=parents,created=datetime.now(timezone.utc).isoformat(),data=data)
        record['tool']=deepcopy(tool) if tool else None
        json.dumps(record,allow_nan=False)
        self._records[record['id']]=record;self.dirty=True
        return record['id']
    def records(self,kind=None):
        return [deepcopy(r) for r in self._records.values() if kind is None or r['kind']==kind or kind=='expression' and self.expression(r['id']) is not None]
    def headers(self,kind=None):
        return [deepcopy({k:v for k,v in r.items() if k!="data"}) for r in self._records.values() if kind is None or r["kind"]==kind or kind=='expression' and self.expression(r['id']) is not None]
    def describe(self,key):
        record=self._records[key];data=record['data']
        if record['kind']=='signal':return dict({k:deepcopy(data[k]) for k in ('domain','origin','step','units','name')},kind='signal',count=len(data['values']))
        if record['kind']=='system':return {'kind':'system','domain':data['domain'],'name':data['name'],'advance':data.get('advance',0)}
        if record['kind']=='state_space':return {'kind':'state_space','domain':'continuous' if data.get('dt') is None else 'discrete'}
        expression=self.expression(key)
        info={'kind':record['kind'],'expression':expression is not None,'variable':expression.variable if expression else None,'units':expression.units if expression else ''}
        result=data.get('result',{});request=data.get('request',{})
        if isinstance(result,dict) and result.get('operation')=='signal_measures_expression' and request.get('expression'):
            info.update(input_expression=request['expression'],input_variable='n' if result['domain']=='discrete' else 't',input_conditions=tuple(request.get('input_conditions',())))
        return info
    def expression(self,key):
        from .result_expressions import expression_result
        record=self._records[key]
        return expression_result(record['data']) if record['kind']=='calculation' else None
    def export_record(self,key,path):
        selected=set()
        def visit(current):
            if current in selected:return
            for parent in self._records[current]['parents']:visit(parent)
            selected.add(current)
        visit(key)
        document=dict(format='signallab-project',schema_version=2,records=[deepcopy(r) for k,r in self._records.items() if k in selected])
        write_json(path,document)
    def get(self,key):
        record=self._records[key];value=decode(record['kind'],record['data'])
        if isinstance(value,Transfer) and value.domain=='digital' and 'sample_period_s' not in record['data']:value.sample_period_s=self.sample_period(key)
        return value
    def sample_period(self,key):
        """Recover a legacy clock only when explicit ancestor clocks agree."""
        import math
        cache={}
        def visit(current):
            if current in cache:return cache[current]
            record=self._records[current];kind=record['kind'];data=record['data'];periods=None
            if kind=='system':
                if data['domain']!='digital':periods=set()
                elif 'sample_period_s' in data:periods=set() if data['sample_period_s'] is None else {data['sample_period_s']}
            elif kind=='state_space':periods=set() if data.get('dt') is None else {data['dt']}
            elif kind=='signal':
                periods=set()
                if data['domain']=='discrete':
                    try:period=1/float(data.get('metadata',{}).get('sample_rate_hz'))
                    except (ValueError,TypeError,ZeroDivisionError,OverflowError):period=None
                    if period is not None and math.isfinite(period) and period>0:periods.add(period)
            if periods is None:
                periods=set()
                for parent in record['parents']:periods.update(visit(parent))
            cache[current]=periods;return periods
        periods=sorted(visit(key))
        return periods[0] if periods and all(math.isclose(period,periods[0],rel_tol=1e-12,abs_tol=0) for period in periods) else None
    def save(self,path):
        path=Path(path)
        document=dict(format='signallab-project',schema_version=2,records=self.records())
        write_json(path,document)
        self.dirty=False
    def merge(self,path):
        from .resources import ensure_working_set
        ensure_working_set(Path(path).stat().st_size,bytes_per_sample=1,live_arrays=8)
        document=json.loads(Path(path).read_text(encoding='utf-8-sig'))
        if not isinstance(document,dict):raise ValueError('El archivo de proyecto debe contener un objeto JSON.')
        if document.get('format')!='signallab-project' or document.get('schema_version') not in (1,2):raise ValueError('Proyecto SignalLab incompatible.')
        records=document.get('records')
        if not isinstance(records,list):raise ValueError('El proyecto no contiene una lista de objetos.')
        staging={};mapping={}
        for record in records:
            if not isinstance(record,dict) or not isinstance(record.get('id'),str) or record['id'] in mapping:raise ValueError('Identificadores de proyecto inválidos o repetidos.')
            mapping[record['id']]=uuid4().hex
        for number,record in enumerate(records,1):
            if record.get('kind') not in ('signal','system','state_space','calculation') or not isinstance(record.get('data'),dict):raise ValueError('Registro '+str(number)+': tipo o datos de resultado inválidos.')
            try:decode(record['kind'],record['data'])
            except (KeyError,TypeError,ValueError,IndexError,OverflowError) as exc:raise ValueError('Registro '+str(number)+' ('+record['id']+'): definición incompleta o inválida. '+str(exc)) from exc
            if not isinstance(record.get('title'),str) or not isinstance(record.get('parents'),list) or any(not isinstance(parent,str) for parent in record['parents']):raise ValueError('Registro '+str(number)+': título o procedencia incompletos.')
            # Los padres deben preceder al resultado: también impide ciclos.
            if any(parent not in staging for parent in record['parents']):raise ValueError('Procedencia faltante o circular.')
            staging[record['id']]=deepcopy(record)
        json.dumps(records,allow_nan=False)
        imported={}
        for old,record in staging.items():
            record['id']=mapping[old];record['parents']=[mapping[p] for p in record['parents']];imported[record['id']]=record
        self._records.update(imported);self.dirty=self.dirty or bool(imported)
        return len(imported)
