"""Store typed communication records in the existing Project and session formats."""

import base64
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
import sys

import numpy as np

from . import session
from .communications_data import BitSequence, ConstellationSpec, SymbolClock, SymbolSequence, integer
from .communications_experiment import ExperimentResult, ExperimentSpec
from .communications_pipeline import decode_pipeline_spec, load_channel_pipeline, stage_channel_pipeline
from .communications_pulses import PulseSpec
from .communications_receiver import SynchronizationSpec
from .execution import ExecutionContext
from .input_files import decode_base64_exact
from .operation_provenance import content_digest, encoded_digest, settings_digest
from .project import Project


_FORMAT = 'signallab-communications'
_SCHEMA = 1


def _label_dtype(order):
    width = order.bit_length()-1
    return np.dtype('<u1' if width <= 8 else '<u2' if width <= 16 else '<u4')


def _typed_payload(kind, length, data, **fields):
    return {'format': _FORMAT, 'schema': _SCHEMA, 'kind': kind, 'length': length,
            'data_base64': base64.b64encode(data).decode('ascii'), **fields}


def encode_bits(bits: BitSequence):
    if not isinstance(bits, BitSequence):
        raise TypeError('El registro requiere datos binarios.')
    fields = np.packbits(bits.values, bitorder='big')
    return _typed_payload('bits', bits.values.size, fields, seed=bits.seed)


def encode_symbols(symbols: SymbolSequence):
    if not isinstance(symbols, SymbolSequence):
        raise TypeError('El registro requiere etiquetas de símbolos.')
    packed = symbols.labels.astype(_label_dtype(symbols.order), copy=False)
    return _typed_payload('symbols', symbols.labels.size, packed, order=symbols.order,
                          valid_bits=symbols.valid_bits,
                          clock=None if symbols.clock is None else asdict(symbols.clock))


def _payload(document, kind):
    if (not isinstance(document, dict) or document.get('format') != _FORMAT
            or type(document.get('schema')) is not int or document['schema'] != _SCHEMA
            or document.get('kind') != kind):
        raise ValueError('Tipo o versión del registro de comunicaciones incompatible.')
    return integer(document.get('length'), 'El largo del registro', maximum=sys.maxsize)


def _encoded_bytes(document, size):
    return decode_base64_exact(document.get('data_base64'), size)


def decode_bits(document, execution: ExecutionContext | None = None) -> BitSequence:
    length = _payload(document, 'bits')
    size = (length+7)//8
    ctx = execution or ExecutionContext()
    with ctx.reserve(2*length+6*size):
        raw = _encoded_bytes(document, size)
        unused = 8*size-length
        if unused and raw[-1] & ((1 << unused)-1):
            raise ValueError('El relleno del registro binario debe ser cero.')
        values = np.unpackbits(np.frombuffer(raw, dtype=np.uint8), count=length, bitorder='big')
        result = BitSequence(values, document.get('seed'))
        ctx.checkpoint()
    return result


def decode_symbols(document, execution: ExecutionContext | None = None) -> SymbolSequence:
    length = _payload(document, 'symbols')
    order = integer(document.get('order'), 'El orden de modulación', minimum=2, maximum=1 << 32)
    if order & (order-1):
        raise ValueError('El orden almacenado debe ser una potencia de dos.')
    dtype = _label_dtype(order)
    size = length*dtype.itemsize
    ctx = execution or ExecutionContext()
    with ctx.reserve(8*length+6*size):
        raw = _encoded_bytes(document, size)
        timing = document.get('clock')
        if timing is not None and not isinstance(timing, dict):
            raise ValueError('El reloj almacenado debe ser un objeto.')
        try:
            clock = None if timing is None else SymbolClock(**timing)
        except TypeError as exc:
            raise ValueError('El reloj almacenado está incompleto o tiene campos desconocidos.') from exc
        result = SymbolSequence(np.frombuffer(raw, dtype=dtype), order, document.get('valid_bits'), clock)
        ctx.checkpoint()
    return result


def decode_experiment_spec(document) -> ExperimentSpec:
    if not isinstance(document, dict):
        raise ValueError('Se esperaba un objeto con la configuración del experimento.')
    fields = dict(document)
    try:
        fields['constellation'] = ConstellationSpec(**fields['constellation'])
        fields['pulse'] = PulseSpec(**fields['pulse'])
        fields['synchronization'] = SynchronizationSpec(**fields['synchronization'])
        if 'channel_pipeline' in fields:
            fields['channel_pipeline'] = decode_pipeline_spec(fields['channel_pipeline'])
        return ExperimentSpec(**fields)
    except (KeyError, TypeError) as exc:
        raise ValueError('La configuración almacenada está incompleta o tiene campos desconocidos.') from exc


@dataclass(frozen=True, slots=True)
class StoredExperiment:
    identifier: str
    specification: ExperimentSpec
    report: dict
    records: dict[str, str]
    chain: dict | None = None


def load_experiment(project: Project, identifier: str) -> StoredExperiment:
    project = project.snapshot()
    data = project.get(identifier)
    header = next((row for row in project.headers('calculation') if row['id'] == identifier), None)
    if (not isinstance(data, dict) or data.get('format') != _FORMAT or data.get('kind') != 'experiment'
            or type(data.get('schema')) is not int or data['schema'] != _SCHEMA
            or header is None or 'verified_provenance' not in header):
        raise ValueError('El registro no es un experimento verificable de comunicaciones.')
    roles, parents = data.get('roles'), header['parents']
    if (not isinstance(roles, list) or any(not isinstance(role, str) or not role for role in roles)
            or len(roles) != len(parents) or len(set(roles)) != len(roles)):
        raise ValueError('Las relaciones del experimento no coinciden con sus registros.')
    report = data.get('report')
    if not isinstance(report, dict) or data.get('report_sha256') != settings_digest(report):
        raise ValueError('El informe del experimento cambió después del cálculo.')
    spec = decode_experiment_spec(report.get('specification'))
    records = dict(zip(roles, parents, strict=True))
    chain = None
    if spec.channel_pipeline is not None:
        if not {'channel_pipeline', 'channel_output', 'tx'} <= records.keys():
            raise ValueError('El experimento no conserva la cadena de canal indicada.')
        configuration, chain = load_channel_pipeline(project, records['channel_pipeline'])
        if (configuration != spec.channel_pipeline or chain['report_sha256'] != settings_digest(report.get('channel_pipeline'))
                or chain['source_record'] != records['tx'] or chain['stage_records'][-1]['record'] != records['channel_output']):
            raise ValueError('La cadena guardada no corresponde al enlace.')
    return StoredExperiment(identifier, spec, report, records, chain)


def store_experiment(project: Project, result: ExperimentResult,
                     execution: ExecutionContext | None = None) -> str:
    """Commit the scientific report and its entire lineage in one transaction."""
    if not isinstance(project, Project) or not isinstance(result, ExperimentResult):
        raise TypeError('La publicación requiere un proyecto y el resultado del experimento.')
    ctx = execution or ExecutionContext()
    ctx.checkpoint()
    report = result.report()
    if settings_digest(report) != result.report_sha256:
        raise ValueError('El informe del experimento cambió después del cálculo.')
    if sha256(result.input_bits.values).hexdigest() != result.provenance.input_bits_sha256:
        raise ValueError('Los bits de entrada cambiaron después del cálculo.')
    signals = result.signals()
    expected = dict(result.signal_digests)
    if expected.keys() != signals.keys():
        raise ValueError('El resultado vectorial del experimento está incompleto.')
    rate = result.specification.symbol_rate_hz * result.specification.pulse.samples_per_symbol
    cost = 24*sum(value.values.size for value in signals.values()) + 36*result.transmitted_labels.labels.size
    estimates = cost + 24*result.input_bits.values.size + 384*result.pulse.taps.size
    if result.pipeline is not None:
        estimates += result.pipeline.storage_estimate
    with ctx.reserve(estimates), project.stage_records(before_commit=ctx.checkpoint) as staged:
        ids, hashes = {}, {}

        def add(role, value, parents=(), *, title=None, digest=None):
            ctx.checkpoint()
            if digest is None:
                digest = (encoded_digest('calculation', value, ctx.checkpoint)
                          if isinstance(value, dict) else content_digest(value, ctx.checkpoint))
            ids[role] = staged.add(value, operation=f'Comunicaciones · {title or role}', title=title,
                                   parents=tuple(ids[parent] for parent in parents),
                                   verification=(digest, tuple(hashes[parent] for parent in parents), ctx.checkpoint))
            hashes[role] = digest

        add('input_bits', encode_bits(result.input_bits), title='Bits transmitidos')
        if result.pilot is not None:
            add('pilot', result.pilot, digest=expected['pilot'])
        pilot_parents = ('pilot',) if result.pilot is not None else ()
        add('tx_labels', encode_symbols(result.transmitted_labels), ('input_bits', *pilot_parents),
            title='Etiquetas transmitidas')
        add('pulse_tx', result.pulse.transfer(rate))
        receiver_rate = result.matched.metadata.get('sample_rate_hz', rate)
        add('pulse_rx', result.pulse.transfer(receiver_rate, matched=True))
        stages = [('symbols', ('tx_labels',)), ('upsampled', ('symbols',)),
                  ('tx', ('upsampled', 'pulse_tx'))]
        for role, parents in stages:
            add(role, signals[role], parents, digest=expected[role])
        receiver_parent = 'tx'
        if result.pipeline is not None:
            receipt = stage_channel_pipeline(staged, result.pipeline, source_id=ids['tx'], execution=ctx)
            ids['channel_pipeline'] = receipt['report_record']
            hashes['channel_pipeline'] = encoded_digest('calculation', staged.get(receipt['report_record']), ctx.checkpoint)
            ids['channel_output'] = receipt['record']
            hashes['channel_output'] = expected['channel_output']
            receiver_parent = 'channel_output'
        if result.channel is not None:
            add('awgn', signals['awgn'], (receiver_parent,), digest=expected['awgn'])
            receiver_parent = 'awgn'
        add('matched', signals['matched'], (receiver_parent, 'pulse_rx'), digest=expected['matched'])
        if result.reception.symbols is not None:
            add('observed', signals['observed'], ('matched', *pilot_parents), digest=expected['observed'])
        if result.received_labels is not None:
            add('rx_labels', encode_symbols(result.received_labels), ('observed',), title='Etiquetas recibidas')
            add('output_bits', encode_bits(result.received_bits), ('rx_labels',), title='Bits recuperados')
        # Keep identities in Project parents. The verified payload survives remapping on import.
        document = {'format': _FORMAT, 'schema': _SCHEMA, 'kind': 'experiment', 'roles': list(ids),
                    'report_sha256': result.report_sha256, 'report': report}
        add('experiment', document, tuple(ids), title='Experimento de comunicaciones')
    return ids['experiment']


def save_experiment(path, result: ExperimentResult, execution: ExecutionContext | None = None):
    ctx = execution or ExecutionContext()
    project = Project()
    key = store_experiment(project, result, ctx)
    session.save(Path(path), project, session.empty_workspace(),
                 before_commit=ctx.checkpoint, checkpoint=ctx.checkpoint)
    return key
