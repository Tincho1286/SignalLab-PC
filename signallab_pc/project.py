"""Proyecto compartido: instantáneas tipadas, procedencia y persistencia atómica."""
from copy import deepcopy
from contextlib import contextmanager
from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4
import json
from math import copysign
import numpy as np
from .model import Signal
from .atomic_file import write_json
from .filters import Transfer
from .operation_provenance import content_digest, encoded_digest
from .state_space import StateModel


def encode(value, *, compact=False):
    if isinstance(value, Signal):
        samples = np.array(value.values, dtype=np.complex128, copy=True).reshape(-1) if compact else _sample_pairs(value.values)
        if compact:
            if not samples.size or not np.isfinite(samples).all():
                raise ValueError('El registro requiere muestras finitas.')
            samples.setflags(write=False)
        return 'signal', dict(values=samples,
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


def _sample_pairs(samples):
    return np.asarray(samples, dtype=np.complex128, order='C').view(np.float64).reshape(-1, 2).tolist()


def _record_without_samples(record):
    if record['kind'] != 'signal':
        return record
    return {**record, 'data': {k: v for k, v in record['data'].items() if k != 'values'}}


def _export_record(record):
    if record['kind'] != 'signal':
        return deepcopy(record)
    data = deepcopy(_record_without_samples(record))
    data['data']['values'] = _sample_pairs(record['data']['values'])
    return data


def decode(kind,data):
    if kind=='signal':
        samples = data['values']
        fields = deepcopy({k: v for k, v in data.items() if k != 'values'})
        if not isinstance(samples, np.ndarray):
            samples = [complex(*v) for v in samples]
        return Signal(samples, **fields)
    data=deepcopy(data)
    if kind=='system':
        data['b']=[complex(*v) for v in data['b']];data['a']=[complex(*v) for v in data['a']];return Transfer(**data)
    if kind=='state_space':
        for key in ('A','B','C','D'):
            matrix=data[key];data[key]=np.array([complex(*z) for z in matrix['values']]).reshape(matrix['shape'])
        return StateModel(**data)
    if kind=='calculation' and isinstance(data,dict):return data
    raise ValueError('Tipo de registro desconocido.')


def _calculated_references(value):
    pending = [value]
    while pending:
        node = pending.pop()
        if isinstance(node,dict):
            if len(node) == 1:
                field, identifier = next(iter(node.items()))
                if field in ('result_id','record') and isinstance(identifier,str):
                    yield node, field, identifier
                    continue
            if ('dtype' in node and 'shape' in node) or set(node)=={'type','data'}:
                continue
            pending.extend(item for item in node.values() if isinstance(item,(dict,list)))
        elif isinstance(node,list):
            pending.extend(item for item in node if isinstance(item,(dict,list)))


class Project:
    def __init__(self):
        self._records={};self.dirty=False
        self._records_lock=RLock()
        self._verification_cache = None

    @contextmanager
    def stage_records(self, *, before_commit):
        """Stage additions together and serialize writers during the commit."""
        with self._records_lock:
            staged = Project()
            staged._records = self._records.copy()
            staged._verification_cache = {}
            yield staged
            before_commit()
            self._records = staged._records
            self.dirty = self.dirty or staged.dirty

    def add(self,value,*,title=None,operation='',parents=(),tool=None,verification=None):
        kind,data=encode(value, compact=True)
        parents=list(dict.fromkeys(parents))
        record=dict(id=uuid4().hex,kind=kind,title=title or getattr(value,'name','Cálculo'),
                    operation=operation,parents=parents,created=datetime.now(timezone.utc).isoformat(),data=data)
        record['tool']=deepcopy(tool) if tool else None
        json.dumps(_record_without_samples(record),allow_nan=False)
        with self._records_lock:
            if any(parent not in self._records for parent in parents):raise ValueError('Origen no registrado en el proyecto.')
            if verification is not None:
                expected, parent_digests, checkpoint = verification
                record['verified_provenance'] = {'schema': 1, 'content': expected, 'parents': list(parent_digests)}
                cache = self._verification_cache if self._verification_cache is not None else {}
                self._verify_record(record, checkpoint, cache)
            self._records[record['id']]=record;self.dirty=True
        return record['id']

    def _record_digest(self, record, checkpoint):
        data = record['data']
        if record['kind'] == 'system' and record['id'] in self._records:
            pivot = data['a'][0]
            if (pivot != [1, 0] or copysign(1, pivot[1]) < 0
                    or not {'advance', 'sample_period_s', 'roc'} <= data.keys()):
                return content_digest(self.get(record['id']), checkpoint)
        return encoded_digest(record['kind'], data, checkpoint)

    def _verify_record(self, record, checkpoint, cache):
        proof = record['verified_provenance']
        if (not isinstance(proof, dict) or type(proof.get('schema')) is not int
                or proof['schema'] != 1 or not isinstance(proof.get('parents'), list)
                or len(proof['parents']) != len(record['parents'])):
            raise ValueError('La procedencia verificada del registro tiene un formato inválido.')
        key = record['id']
        if key not in cache:
            cache[key] = self._record_digest(record, checkpoint)
        if cache[key] != proof.get('content'):
            raise ValueError('El resultado o la entrada cambió después del cálculo.')
        for parent, expected in zip(record['parents'], proof['parents'], strict=True):
            if parent not in cache:
                cache[parent] = self._record_digest(self._records[parent], checkpoint)
            if cache[parent] != expected:
                raise ValueError('El origen registrado no coincide con los datos utilizados en el cálculo.')
    def records(self,kind=None):
        return [_export_record(r) for r in self._records.values() if kind is None or r['kind']==kind or kind=='expression' and self.expression(r['id']) is not None]

    def _stable_records(self):
        """Take a shallow snapshot of the internally owned, immutable records."""
        with self._records_lock:
            return tuple(self._records.values())

    def snapshot(self):
        """Capture the catalog under its lock and share immutable record samples."""
        snapshot = Project()
        with self._records_lock:
            snapshot._records = self._records.copy()
        return snapshot
    def headers(self,kind=None):
        return [deepcopy({k:v for k,v in r.items() if k!="data"}) for r in self._records.values() if kind is None or r["kind"]==kind or kind=='expression' and self.expression(r['id']) is not None]
    def describe(self,key):
        record=self._records[key];data=record['data']
        if record['kind']=='signal':
            from .signal_semantics import signal_kind
            metadata=data.get('metadata',{})
            details={k:deepcopy(data[k]) for k in ('domain','origin','step','units','name')}
            return dict(details,kind='signal',count=len(data['values']),
                        data_kind=signal_kind(data['domain'],data['units'],metadata),
                        centered_dft=(data['domain']=='frequency' and data['units']=='rad/muestra'
                                      and metadata.get('dft_order')=='centered'))
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
        selected = set()
        pending = [key]
        while pending:
            current = pending.pop()
            if current not in selected:
                selected.add(current)
                record = self._records[current]
                pending.extend(record['parents'])
                if record['kind'] == 'calculation':
                    pending.extend(ref for _, _, ref in _calculated_references(record['data'].get('calculated_data'))
                                   if ref in self._records)
        document=dict(format='signallab-project',schema_version=2,records=[_export_record(r) for k,r in self._records.items() if k in selected])
        write_json(path,document)
    def get(self,key):
        record=self._records[key];value=decode(record['kind'],record['data'])
        if isinstance(value,Transfer) and value.domain=='digital' and 'sample_period_s' not in record['data']:value.sample_period_s=self.sample_period(key)
        return value
    def sample_period(self,key):
        """Recover a legacy clock only when explicit ancestor clocks agree."""
        import math
        seen = set()
        periods = set()
        pending = [key]
        while pending:
            current = pending.pop()
            if current in seen:
                continue
            seen.add(current)
            record = self._records[current]
            declared, period = _record_period(record)
            if not declared:
                pending.extend(record['parents'])
            elif period is not None:
                periods.add(period)
        periods = sorted(periods)
        return periods[0] if periods and all(math.isclose(period,periods[0],rel_tol=1e-12,abs_tol=0) for period in periods) else None
    def save(self,path):
        with self._records_lock:
            if str(path).lower().endswith('.slproj'):
                from .project_archive import save
                save(path, self)
            else:
                write_json(path,self.document())
            self.dirty=False

    def document(self):
        return dict(format='signallab-project',schema_version=2,records=self.records())

    @classmethod
    def from_document(cls, document, *, checkpoint=None):
        if not isinstance(document,dict):raise ValueError('El archivo de proyecto debe contener un objeto JSON.')
        version = document.get('schema_version')
        if document.get('format')!='signallab-project' or type(version) is not int or version not in (1,2):raise ValueError('Proyecto SignalLab incompatible.')
        records=document.get('records')
        if not isinstance(records,list):raise ValueError('El proyecto no contiene una lista de objetos.')
        staging={};ids=set()
        for record in records:
            if checkpoint is not None:
                checkpoint()
            if not isinstance(record,dict) or not isinstance(record.get('id'),str) or not record['id'] or record['id'] in ids:raise ValueError('Identificadores de proyecto inválidos o repetidos.')
            ids.add(record['id'])
        for number,record in enumerate(records,1):
            if checkpoint is not None:
                checkpoint()
            if record.get('kind') not in ('signal','system','state_space','calculation') or not isinstance(record.get('data'),dict):raise ValueError('Registro '+str(number)+': tipo o datos de resultado inválidos.')
            try:value=decode(record['kind'],record['data'])
            except (KeyError,TypeError,ValueError,IndexError,OverflowError) as exc:raise ValueError('Registro '+str(number)+' ('+record['id']+'): definición incompleta o inválida. '+str(exc)) from exc
            if (not isinstance(record.get('title'),str) or not isinstance(record.get('operation',''),str)
                    or not isinstance(record.get('parents'),list)
                    or any(not isinstance(parent,str) for parent in record['parents'])):
                raise ValueError('Registro '+str(number)+': título, operación o procedencia inválidos.')
            # Los padres deben preceder al resultado: también impide ciclos.
            if any(parent not in staging for parent in record['parents']):raise ValueError('Procedencia faltante o circular.')
            stored = deepcopy(_record_without_samples(record))
            stored.setdefault('operation','')
            if isinstance(value, Signal):
                value.values.setflags(write=False)
                stored['data']['values'] = value.values
                for name in ('origin','step','units','name','domain','expression'):
                    stored['data'][name] = getattr(value,name)
            elif isinstance(value, Transfer):
                for name in ('domain','name'):
                    stored['data'][name] = getattr(value,name)
            staging[record['id']] = stored
            json.dumps(_record_without_samples(stored),allow_nan=False)
        project=cls()
        project._records=staging
        digests = {}
        for record in staging.values():
            if 'verified_provenance' in record:
                project._verify_record(record, checkpoint or (lambda: None), digests)
        return project

    def merge(self,path):
        if str(path).lower().endswith('.slproj'):
            from .project_archive import load
            staging = load(path)[0]._records
        else:
            staging = self.from_document(read_document(path))._records
        mapping={old:uuid4().hex for old in staging}
        imported={}
        for old,record in staging.items():
            record['id']=mapping[old];record['parents']=[mapping[p] for p in record['parents']]
            if record['kind']=='calculation' and 'calculated_data' in record['data']:
                for node, field, identifier in _calculated_references(record['data']['calculated_data']):
                    if identifier in mapping:
                        node[field] = mapping[identifier]
            imported[record['id']]=record
        with self._records_lock:
            self._records.update(imported);self.dirty=self.dirty or bool(imported)
        return len(imported)


def _record_period(record):
    """Return whether this record decides the clock, even when its value is absent."""
    import math
    kind, data = record['kind'], record['data']
    if kind == 'system':
        if data['domain'] != 'digital':
            return True, None
        return 'sample_period_s' in data, data.get('sample_period_s')
    if kind == 'state_space':
        return True, data.get('dt')
    if kind == 'signal':
        rate = data.get('metadata',{}).get('sample_rate_hz') if data['domain']=='discrete' else None
        try:
            period = 1/float(rate)
        except (ValueError,TypeError,ZeroDivisionError,OverflowError):
            period = None
        return True, period if period is not None and math.isfinite(period) and period>0 else None
    for field, clock_key in (('cas_answer','system_context'),('result','sample_period_s')):
        payload = data.get(field)
        if isinstance(payload,dict) and clock_key in payload:
            from .transform_context import result_period
            return True, result_period(data)
    return False, None


def read_document(path):
    from .input_files import read_json
    return read_json(path)
