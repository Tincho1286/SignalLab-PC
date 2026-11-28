"""Bounded RF snapshots using the verified scientific project record contract."""

import base64
from hashlib import sha256

import numpy as np

from .communications_data import integer
from .execution import ExecutionContext
from .input_files import decode_base64_exact
from .operation_provenance import encoded_digest
from .resources import ResourceLimitError
from .rf_network import RFNetwork


FORMAT = 'signallab-rf-network'
MAX_RF_CELLS = 1_000_000
MAX_RF_PORTS = 64
MAX_RF_FREQUENCIES = 250_000


def is_rf_data(document):
    return isinstance(document, dict) and document.get('format') == FORMAT


def _dimensions(count, ports):
    count = integer(count,'Cantidad de frecuencias', maximum=MAX_RF_FREQUENCIES)
    ports = integer(ports,'Cantidad de puertos', maximum=MAX_RF_PORTS)
    if count*ports**2 > MAX_RF_CELLS:
        raise ResourceLimitError('El registro RF supera 1 000 000 entradas de matriz.')
    return count, ports


def payload_size(document):
    count,ports = _dimensions(document.get('frequencies'),document.get('ports'))
    return count * (16 * ports**2 + 8 * (1+ports))


def encode_network(network: RFNetwork, *, context=None):
    ctx = context if context is not None else ExecutionContext()
    count, ports = _dimensions(len(network.frequencies_hz), network.nports)
    document = {'format':FORMAT,'schema':1,'frequencies':count,'ports':ports,
                'port_names':list(network.port_names),'name':network.name,'metadata':network.metadata,
                'representation':network.representation,'wave_convention':network.wave_convention,
                'frequency_unit':'Hz','reference_unit':'Ω'}
    with ctx.reserve(6*payload_size(document)):
        raw = b''.join(np.asarray(value,dtype=dtype).tobytes() for value,dtype in (
            (network.frequencies_hz,'<f8'), (network.reference_ohm,'<f8'),(network.values,'<c16')))
        document['data_sha256']=sha256(raw).hexdigest()
        document['data_base64']=base64.b64encode(raw).decode('ascii')
    ctx.checkpoint()
    return document


def decode_network(document, *, context=None):
    ctx = context if context is not None else ExecutionContext()
    if (not is_rf_data(document) or type(document.get('schema')) is not int or document['schema']!=1
            or document.get('wave_convention')!='power' or document.get('frequency_unit')!='Hz'
            or document.get('reference_unit')!='Ω'):
        raise ValueError('Contrato, unidades o versión del registro RF incompatibles.')
    count,ports = _dimensions(document.get('frequencies'),document.get('ports'))
    size = payload_size(document)
    with ctx.reserve(6*size):
        raw = decode_base64_exact(document.get('data_base64'),size)
        if sha256(raw).hexdigest()!=document.get('data_sha256'):
            raise ValueError('La huella de las muestras de red RF no coincide.')
        reference=np.frombuffer(raw,dtype='<f8',count=count*ports,offset=8*count).reshape(count,ports)
        samples=np.frombuffer(raw,dtype='<c16',count=count*ports**2,offset=8*count*(1+ports))
        return RFNetwork(np.frombuffer(raw,dtype='<f8',count=count),samples.reshape(count,ports,ports),
                         representation=document.get('representation'),reference_ohm=reference,
                         port_names=document.get('port_names'),name=document.get('name'),
                         metadata=document.get('metadata'),context=ctx)


def store_network(project, network, *, parents=(), operation='Red RF', settings=None, tool=None, context=None):
    """Publish network and provenance atomically, with existing record relationships."""
    ctx = context if context is not None else ExecutionContext()
    document=encode_network(network,context=ctx)
    if settings is not None:
        document['settings']=settings
    parents=tuple(dict.fromkeys(parents))
    with project.stage_records(before_commit=ctx.checkpoint) as staged:
        if any(key not in staged._records for key in parents):
            raise ValueError('Origen RF no registrado en el proyecto.')
        hashes=tuple(staged._record_digest(staged._records[key],ctx.checkpoint) for key in parents)
        digest=encoded_digest('calculation',document,ctx.checkpoint)
        key=staged.add(document,title=network.name or 'Red RF',operation=operation,parents=parents,tool=tool,
                       verification=(digest,hashes,ctx.checkpoint))
    return key


def load_network(project, identifier, *, context=None):
    """Revalidate operation lineage and binary payload when reusing a network."""
    ctx = context if context is not None else ExecutionContext()
    snapshot=project.snapshot()
    row=snapshot._records.get(identifier)
    if (row is None or row['kind']!='calculation' or not is_rf_data(row['data'])
            or 'verified_provenance' not in row):
        raise ValueError('Elegí una red RF verificable de la biblioteca de resultados.')
    snapshot._verify_record(row,ctx.checkpoint,{})
    return decode_network(row['data'],context=ctx)
