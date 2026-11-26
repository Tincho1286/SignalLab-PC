"""Ordered, reproducible channel composition using the individual channel engines."""

from contextlib import ExitStack
from dataclasses import asdict, dataclass, replace

import numpy as np

from .communications_channel import AWGNSpec, ChannelPath, MultipathSpec, add_awgn, apply_multipath, channel_record_power, discrete_channel_size
from .communications_data import MAX_SEED, integer
from .communications_doppler import CarrierShift, apply_carrier_shift
from .communications_fading import FadingPath, FadingSpec, apply_fading
from .communications_impairments import IQImbalance, PhaseNoiseSpec, TimingOffset, apply_iq_imbalance, apply_phase_noise, apply_timing_offset
from .communications_interference import (
    BandInterference, ExternalInterference, InterferenceSpec, InterferenceTone, ToneInterference, apply_interference,
)
from .communications_propagation import FreeSpaceLoss, LogDistanceLoss, PropagationSpec, apply_propagation
from .dsp_application import stage_signal, verify_dsp_signal
from .dsp_pipeline import PipelineStageError
from .execution import ExecutionContext
from .input_files import decode_finite_json, read_text
from .model import Signal
from .operation_provenance import content_digest, encoded_digest, settings_digest, verify_inputs
from .project import Project


_OPERATIONS = {
    'multipath': (MultipathSpec, apply_multipath),
    'fading': (FadingSpec, apply_fading),
    'carrier': (CarrierShift, apply_carrier_shift),
    'timing': (TimingOffset, apply_timing_offset),
    'phase_noise': (PhaseNoiseSpec, apply_phase_noise),
    'iq_imbalance': (IQImbalance, apply_iq_imbalance),
    'interference': (InterferenceSpec, apply_interference),
    'awgn': (AWGNSpec, add_awgn),
    'propagation': (PropagationSpec, apply_propagation),
}
_NAMES = {specification: name for name, (specification, _) in _OPERATIONS.items()}
_SUBMODELS = {
    ToneInterference: 'tones', BandInterference: 'band', ExternalInterference: 'external',
    FreeSpaceLoss: 'free_space', LogDistanceLoss: 'log_distance',
}
_SUBMODEL_TYPES = {name: model for model, name in _SUBMODELS.items()}
_MAX_STAGES = 128

ChannelOperation = (AWGNSpec | MultipathSpec | FadingSpec | CarrierShift | TimingOffset | PhaseNoiseSpec
                    | IQImbalance | InterferenceSpec | PropagationSpec)


@dataclass(frozen=True, slots=True)
class ChannelStage:
    operation: ChannelOperation
    external_input: str | None = None

    def __post_init__(self):
        if type(self.operation) not in _NAMES:
            raise ValueError('La etapa requiere un modelo de canal compatible.')
        needs_input = isinstance(self.operation, InterferenceSpec) and isinstance(self.operation.model, ExternalInterference)
        if needs_input:
            if not isinstance(self.external_input, str) or not self.external_input.strip():
                raise ValueError('Indicá un nombre para la señal externa de la etapa.')
        elif self.external_input is not None:
            raise ValueError('La entrada externa corresponde a un modelo de interferencia externa.')

    @property
    def kind(self):
        return _NAMES[type(self.operation)]


@dataclass(frozen=True, slots=True)
class ChannelPipelineSpec:
    stages: tuple[ChannelStage, ...] = ()
    seed: int | None = None

    def __post_init__(self):
        stages = tuple(self.stages)
        if len(stages) > _MAX_STAGES or any(not isinstance(stage, ChannelStage) for stage in stages):
            raise ValueError(f'La cadena admite hasta {_MAX_STAGES} etapas compatibles.')
        object.__setattr__(self, 'stages', stages)
        if self.seed is not None:
            object.__setattr__(self, 'seed', integer(self.seed, 'La semilla de la cadena', minimum=0, maximum=MAX_SEED))

    @property
    def external_names(self):
        return tuple(dict.fromkeys(stage.external_input for stage in self.stages if stage.external_input is not None))


def _encode_stage(stage):
    operation = stage.operation
    parameters = asdict(operation)
    if isinstance(operation, InterferenceSpec) and operation.sinr_db is None:
        parameters.pop('sinr_db')
    if isinstance(operation, (InterferenceSpec, PropagationSpec)) and operation.model is not None:
        parameters['model']['kind'] = _SUBMODELS[type(operation.model)]
    return {'kind': stage.kind, 'parameters': parameters, 'external_input': stage.external_input}


def encode_pipeline_spec(spec: ChannelPipelineSpec):
    return {'schema': 1, 'seed': spec.seed, 'stages': [_encode_stage(stage) for stage in spec.stages]}


def _decode_operation(kind, data):
    cls = _OPERATIONS[kind][0]
    values = dict(data)
    if cls in (MultipathSpec, FadingSpec):
        path_type = ChannelPath if cls is MultipathSpec else FadingPath
        values['paths'] = tuple(path_type(**path) for path in values['paths'])
    if cls in (InterferenceSpec, PropagationSpec) and values.get('model') is not None:
        if not isinstance(values['model'], dict):
            raise ValueError('Los parámetros del modelo deben ser un objeto JSON.')
        nested = dict(values['model'])
        nested_cls = _SUBMODEL_TYPES[nested.pop('kind')]
        if nested_cls is ToneInterference:
            nested['tones'] = tuple(InterferenceTone(**tone) for tone in nested['tones'])
        values['model'] = nested_cls(**nested)
    return cls(**values)


def decode_pipeline_spec(document) -> ChannelPipelineSpec:
    if (not isinstance(document, dict) or set(document) - {'schema', 'seed', 'stages'}
            or type(document.get('schema')) is not int or document['schema'] != 1
            or not isinstance(document.get('stages'), (list, tuple)) or len(document['stages']) > _MAX_STAGES):
        raise ValueError('La configuración de cadena debe usar el esquema 1 y una lista de etapas.')
    stages = []
    for index, row in enumerate(document['stages'], 1):
        if (not isinstance(row, dict) or set(row) - {'kind', 'parameters', 'external_input'}
                or not isinstance(row.get('parameters', {}), dict)):
            raise ValueError(f'Etapa {index}: configuración inválida.')
        try:
            operation = _decode_operation(row['kind'], row.get('parameters', {}))
            stages.append(ChannelStage(operation, row.get('external_input')))
        except (KeyError, TypeError, ValueError) as exc:
            raise PipelineStageError(f'Etapa {index}', exc) from exc
    return ChannelPipelineSpec(tuple(stages), document.get('seed'))


def read_pipeline_spec(path, execution: ExecutionContext | None = None):
    ctx = execution or ExecutionContext()
    return decode_pipeline_spec(decode_finite_json(read_text(path, checkpoint=ctx.checkpoint)))


def _effective_stage(stage, root, index):
    if root is None:
        return stage

    def derive(seed, role):
        sequence = np.random.SeedSequence([root, seed], spawn_key=(index, role))
        return sum(int(word) << (32*i) for i, word in enumerate(sequence.generate_state(4)))

    op = stage.operation
    if isinstance(op, (FadingSpec, PhaseNoiseSpec, AWGNSpec, PropagationSpec)):
        return replace(stage, operation=replace(op, seed=derive(op.seed, 0)))
    if isinstance(op, InterferenceSpec):
        model = op.model
        if isinstance(model, BandInterference):
            model = replace(model, seed=derive(model.seed, 0))
        return replace(stage, operation=replace(op, model=model, noise_seed=derive(op.noise_seed, 1)))
    return stage


def _conditions(stage, signal):
    if stage.kind == 'timing':
        timing = signal.metadata['communications_timing_offset']
        if timing['method'] == 'lanczos_sinc':
            return ('Interpolación de banda limitada aproximada, con error en bordes y cerca de Nyquist.',)
    if stage.kind == 'fading' and stage.operation.max_doppler_hz is not None:
        return ('La cuadratura espectral aproxima la dispersión Doppler de Clarke.',)
    if stage.kind == 'interference':
        model = stage.operation.model
        if isinstance(model, BandInterference):
            return ('Banda limitada a la rejilla DFT del registro finito.',)
        synthesis = signal.metadata['communications_interference']['synthesis']
        if isinstance(model, ExternalInterference) and synthesis['overlap_samples'] == 0:
            return ('El interferente no se solapa con la ventana del registro.',)
    if stage.kind == 'propagation' and stage.operation.model is not None:
        return ('La pérdida aplica al escenario declarado y modifica solamente la amplitud.',)
    return ()


@dataclass(frozen=True, slots=True, eq=False)
class ChannelStageResult:
    stage: ChannelStage
    signal: Signal
    input_power: float
    output_power: float
    statistics: dict
    components: tuple[tuple[str, Signal], ...]
    component_digests: tuple[str, ...]

    def report(self):
        digest, parents, _ = verify_dsp_signal(self.signal)
        metadata = self.signal.metadata
        return {
            'effective': _encode_stage(self.stage), 'statistics': self.statistics,
            'input_power': self.input_power, 'output_power': self.output_power,
            'sample_count': self.signal.values.size, 'origin': self.signal.origin,
            'clock': {key: metadata[key] for key in ('sample_rate_hz', 'time_start_s',
                      'symbol_rate_hz', 'samples_per_symbol', 'center_frequency_hz') if key in metadata},
            'amplitude_units': metadata.get('amplitude_units', '1'),
            'conditions': list(_conditions(self.stage, self.signal)),
            'source_sha256': list(parents), 'output_sha256': digest,
            'components_sha256': dict(zip((name for name, _ in self.components), self.component_digests, strict=True)),
        }


@dataclass(frozen=True, slots=True, eq=False)
class ChannelPipelineResult:
    specification: ChannelPipelineSpec
    source: Signal
    external_sources: tuple[tuple[str, Signal], ...]
    input_digests: tuple[str, ...]
    stages: tuple[ChannelStageResult, ...]
    report_sha256: str

    @property
    def signal(self):
        return self.stages[-1].signal if self.stages else self.source

    @property
    def retained_bytes(self):
        return sum(stage.signal.values.nbytes + sum(value.values.nbytes for _, value in stage.components)
                   for stage in self.stages)

    @property
    def storage_estimate(self):
        return 24 * (self.source.values.size + sum(value.values.size for _, value in self.external_sources)
                     + self.retained_bytes // 16)

    def report(self):
        return {
            'schema': 1, 'specification': encode_pipeline_spec(self.specification),
            'source_sha256': self.input_digests[0],
            'external_sha256': dict(zip((name for name, _ in self.external_sources), self.input_digests[1:], strict=True)),
            'stages': [stage.report() for stage in self.stages],
        }


def _run_operation(signal, stage, external, ctx):
    op = stage.operation
    if stage.external_input is not None:
        outcome = apply_interference(signal, op, external=external[stage.external_input], execution=ctx)
    elif isinstance(op, InterferenceSpec):
        outcome = apply_interference(signal, op, execution=ctx)
    else:
        outcome = _OPERATIONS[stage.kind][1](signal, op, ctx)
    if isinstance(outcome, Signal):
        return outcome, {}, ()
    if isinstance(op, FadingSpec):
        stats = {'paths': [asdict(item.statistics) for item in outcome.realizations]}
        components = tuple((f'fading_{i}', item.coefficients) for i, item in enumerate(outcome.realizations, 1))
    elif isinstance(op, PhaseNoiseSpec):
        stats, components = {'step_variance_rad2': outcome.step_variance_rad2}, (('phase', outcome.phase),)
    else:
        stats, components = asdict(outcome.statistics), ()
    if isinstance(op, InterferenceSpec):
        components = (('interference', outcome.interference),)
        if outcome.noise is not None:
            components += (('noise', outcome.noise),)
    return outcome.signal, stats, components


def _progress(ctx, index, count, budget):
    def forward(value):
        ctx.checkpoint(min(99, (index*100 + value)//count))

    return replace(ctx, max_work_bytes=budget, progress=forward)


def run_channel_pipeline(signal: Signal, spec: ChannelPipelineSpec, *, external=None,
                         execution: ExecutionContext | None = None) -> ChannelPipelineResult:
    if not isinstance(spec, ChannelPipelineSpec):
        raise ValueError('Indicá una configuración de cadena de canal.')
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    discrete_channel_size(signal, 0)
    inputs = {} if external is None else dict(external)
    if set(inputs) != set(spec.external_names):
        raise ValueError('Las señales externas deben coincidir con los nombres vinculados en las etapas.')
    sources = tuple((name, inputs[name]) for name in spec.external_names)
    for _, value in sources:
        discrete_channel_size(value, 0)
    originals = (signal, *(value for _, value in sources))
    fingerprints = tuple(content_digest(value, ctx.checkpoint) for value in originals)
    count = len(spec.stages)
    power = channel_record_power(signal.values, 'complex', ctx) if count else 0.0
    stages = []
    retained = 0
    current = signal
    with ExitStack() as held, ctx.aggregate_progress() as notices:
        for index, requested in enumerate(spec.stages):
            ctx.checkpoint()
            budget = None if ctx.max_work_bytes is None else max(1, ctx.max_work_bytes - retained)
            stage = _effective_stage(requested, spec.seed, index)
            child = _progress(notices, index, count, budget)
            try:
                result, statistics, components = _run_operation(current, stage, inputs, child)
                size = result.values.nbytes + sum(value.values.nbytes for _, value in components)
                retained += size
                ctx.require(retained)
                held.enter_context(ctx.reserve(size))
                new_power = channel_record_power(result.values, 'complex', ctx)
                digests = tuple(content_digest(value, ctx.checkpoint) for _, value in components)
            except (ValueError, FloatingPointError) as exc:
                raise PipelineStageError(f'Etapa {index + 1} ({stage.kind})', exc) from exc
            stages.append(ChannelStageResult(stage, result, power, new_power, statistics, components, digests))
            current, power = result, new_power
        pipeline = ChannelPipelineResult(spec, signal, sources, fingerprints, tuple(stages), '')
        fingerprint = settings_digest(pipeline.report())
        ctx.checkpoint(100)
        verify_inputs(originals, fingerprints, ctx.checkpoint)
    return replace(pipeline, report_sha256=fingerprint)


def stage_channel_pipeline(project: Project, result: ChannelPipelineResult, *, source_id=None,
                           external_records=None, execution: ExecutionContext):
    """Store an ordered channel calculation in an existing project transaction."""
    ctx = execution
    report = result.report()
    if settings_digest(report) != result.report_sha256:
        raise ValueError('El informe de la cadena cambió después del cálculo.')
    provided = {} if external_records is None else dict(external_records)
    external_sources = dict(result.external_sources)
    if set(provided) - set(external_sources):
        raise ValueError('Los orígenes externos deben indicar nombres presentes en la cadena.')
    source = project.get(source_id) if source_id is not None else result.source
    sources = {name: project.get(provided[name]) if name in provided else value
               for name, value in external_sources.items()}
    verify_inputs((source, *sources.values()), result.input_digests, ctx.checkpoint)
    if source_id is None:
        source_id = project.add(source, operation='Entrada de la cadena de canal')
    for name, value in sources.items():
        if name not in provided:
            provided[name] = project.add(value, operation='Entrada externa del canal')
    parents = {}

    def slot(identifier, digest):
        if identifier not in parents:
            parents[identifier] = len(parents), digest
        return parents[identifier][0]

    layout = {'source': slot(source_id, result.input_digests[0]), 'external': {}, 'stages': []}
    for (name, _), digest in zip(result.external_sources, result.input_digests[1:], strict=True):
        layout['external'][name] = slot(provided[name], digest)
    rows = []
    parent = source_id
    for stage in result.stages:
        stage_parents = (parent,)
        if stage.stage.external_input is not None:
            stage_parents += (provided[stage.stage.external_input],)
        parent = stage_signal(project, stage.signal, parents=stage_parents, execution=ctx)
        digest, _, _ = verify_dsp_signal(stage.signal)
        stage_slot = slot(parent, digest)
        components = {}
        component_slots = {}
        for (name, signal), expected in zip(stage.components, stage.component_digests, strict=True):
            components[name] = project.add(signal, operation='Componente de canal', parents=(parent,),
                                           verification=(expected, (digest,), ctx.checkpoint))
            component_slots[name] = slot(components[name], expected)
        rows.append({'record': parent, 'components': components})
        layout['stages'].append({'output': stage_slot, 'components': component_slots})
    # Identities are kept in Project parents, so importing can safely remap them.
    summary = {**report, 'format': 'signallab-channel-pipeline', 'report_sha256': result.report_sha256,
               'layout': layout}
    receipt = project.add(summary, title='Cadena de canal', parents=parents,
                          verification=(encoded_digest('calculation', summary, ctx.checkpoint),
                                        tuple(digest for _, digest in parents.values()), ctx.checkpoint))
    return {'record': parent, 'report_record': receipt, 'stages': rows}


def store_channel_pipeline(project: Project, result: ChannelPipelineResult, *, source_id=None, external_records=None,
                           execution: ExecutionContext | None = None):
    ctx = execution or ExecutionContext()
    with ctx.reserve(result.storage_estimate), project.stage_records(before_commit=ctx.checkpoint) as staged:
        return stage_channel_pipeline(staged, result, source_id=source_id, external_records=external_records,
                                      execution=ctx)


def load_channel_pipeline(project: Project, identifier: str, execution: ExecutionContext | None = None):
    """Return the verified report and its original typed configuration."""
    ctx = execution or ExecutionContext()
    project = project.snapshot()
    document = project.get(identifier)
    header = next((row for row in project.headers('calculation') if row['id'] == identifier), None)
    if (not isinstance(document, dict) or document.get('format') != 'signallab-channel-pipeline'
            or header is None or 'verified_provenance' not in header):
        raise ValueError('El registro no contiene un informe verificable de cadena de canal.')
    parents = header['parents']

    def record(slot):
        return parents[integer(slot, 'El registro de la cadena', minimum=0, maximum=len(parents)-1)]

    try:
        report = {key: document[key] for key in ('schema', 'specification', 'source_sha256',
                                                  'external_sha256', 'stages')}
        spec = decode_pipeline_spec(report['specification'])
        if (type(report['schema']) is not int or report['schema'] != 1
                or document['report_sha256'] != settings_digest(report)):
            raise ValueError('La huella del informe de cadena no coincide.')
        layout = document['layout']
        source_record = record(layout['source'])
        external = {name: record(slot) for name, slot in layout['external'].items()}
        if set(external) != set(spec.external_names) or set(report['external_sha256']) != set(external):
            raise ValueError('Los vínculos externos no coinciden con la configuración.')
        for name, external_id in external.items():
            verify_inputs((project.get(external_id),), (report['external_sha256'][name],), ctx.checkpoint)
        prior = report['source_sha256']
        verify_inputs((project.get(source_record),), (prior,), ctx.checkpoint)
        records = []
        for index, (requested, stage, stored) in enumerate(zip(
            spec.stages, report['stages'], layout['stages'], strict=True,
        )):
            effective = _effective_stage(requested, spec.seed, index)
            if settings_digest(stage['effective']) != settings_digest(_encode_stage(effective)):
                raise ValueError('La configuración efectiva de la etapa no coincide.')
            inputs = [prior]
            if requested.external_input is not None:
                inputs.append(report['external_sha256'][requested.external_input])
            if stage['source_sha256'] != inputs:
                raise ValueError('La secuencia de huellas de etapa no coincide.')
            prior = stage['output_sha256']
            output_record = record(stored['output'])
            verify_inputs((project.get(output_record),), (prior,), ctx.checkpoint)
            if set(stored['components']) != set(stage['components_sha256']):
                raise ValueError('Faltan componentes del cálculo de canal.')
            components = {name: record(slot) for name, slot in stored['components'].items()}
            for name, component in components.items():
                verify_inputs((project.get(component),), (stage['components_sha256'][name],), ctx.checkpoint)
            records.append({'record': output_record, 'components': components})
    except (AttributeError, TypeError, KeyError) as exc:
        raise ValueError('Informe de cadena de canal incompleto o dañado.') from exc
    return spec, {**document, 'source_record': source_record, 'external_records': external, 'stage_records': records}
