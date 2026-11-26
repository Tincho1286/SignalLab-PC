"""Resumable communication campaigns built on transactional project archives."""

from contextlib import contextmanager
import csv
from dataclasses import asdict, dataclass, replace
import io
from itertools import product
import math
import os
from pathlib import Path
import re
import sys

import numpy as np
from scipy import __version__ as scipy_version
from scipy.stats import t as student_t

from . import session
from .atomic_file import atomic_binary_file, write_json
from .communications_channel import discrete_channel_size
from .communications_data import integer, real
from .communications_experiment import ExperimentSpec, run_experiment
from .communications_pipeline import decode_pipeline_spec, encode_pipeline_spec
from .communications_storage import decode_experiment_spec, load_experiment, save_experiment
from .execution import ExecutionContext
from .input_files import read_json
from .operation_provenance import content_digest, settings_digest
from .project import Project
from .resources import ResourceLimitError


AXES = {
    'eb_n0_db': 'Eb/N₀ (dB)', 'order': 'Orden de modulación M',
    'rolloff': 'Roll-off β', 'samples_per_symbol': 'Muestras por símbolo',
    'span_symbols': 'Duración del pulso (símbolos)', 'symbol_count': 'Cantidad de símbolos',
}
_FORMAT = 'signallab-communications-sweep'
_SCHEMA = 1
_MAX_RUNS = 1024
_EXTERNAL_ARCHIVE = 'external-sources.slproj'
_CHANNEL_AXIS = re.compile(r'channel\.[1-9][0-9]*(?:\.[a-z][a-z0-9_]*|\.[1-9][0-9]*)+')
_CHANNEL_LABELS = {
    'delay_samples': 'Retardo (muestras)', 'gain_real': 'Ganancia real', 'gain_imag': 'Ganancia imaginaria',
    'average_power': 'Potencia media', 'k_linear': 'Factor K lineal', 'los_phase_rad': 'Fase LOS (rad)',
    'max_doppler_hz': 'Doppler máximo (Hz)', 'frequency_hz': 'Frecuencia (Hz)', 'phase_rad': 'Fase (rad)',
    'sfo_ppm': 'SFO (ppm)', 'linewidth_hz': 'Ancho de línea (Hz)', 'q_gain_db': 'Ganancia de Q (dB)',
    'q_phase_rad': 'Error angular de Q (rad)', 'dc_i': 'DC en I', 'dc_q': 'DC en Q',
    'power': 'Potencia interferente', 'sir_db': 'SIR objetivo (dB)', 'sinr_db': 'SINR objetivo (dB)',
    'noise_snr_db': 'SNR nominal del ruido (dB)', 'bandwidth_hz': 'Ancho de banda (Hz)',
    'center_hz': 'Centro de banda (Hz)', 'frequency_shift_hz': 'Traslado de frecuencia (Hz)', 'amplitude': 'Amplitud',
    'level_db': 'Nivel AWGN (dB)', 'signal_power': 'Potencia de referencia AWGN',
    'gain_db': 'Ganancia adicional (dB)', 'shadow_std_db': 'Sombra (dB)', 'distance_m': 'Distancia (m)',
    'reference_distance_m': 'Distancia de referencia (m)', 'reference_loss_db': 'Pérdida de referencia (dB)',
    'exponent': 'Exponente de pérdida', 'carrier_hz': 'Portadora (Hz)',
}


def axis_label(parameter):
    if parameter in AXES:
        return AXES[parameter]
    _, stage, *path = parameter.split('.')
    hierarchy = ''
    for name, label in (('paths', 'trayectoria'), ('tones', 'tono')):
        if name in path[:-1]:
            hierarchy = f' · {label} {path[path.index(name)+1]}'
            break
    return f"Etapa {stage}{hierarchy} · {_CHANNEL_LABELS.get(path[-1], path[-1])}"


def _channel_axes(document, prefix):
    if isinstance(document, dict):
        for key, value in document.items():
            name = f'{prefix}.{key}'
            if key in _CHANNEL_LABELS:
                yield name
            elif key in ('paths', 'model', 'tones'):
                yield from _channel_axes(value, name)
    elif isinstance(document, (list, tuple)):
        for index, value in enumerate(document, 1):
            yield from _channel_axes(value, f'{prefix}.{index}')


def sweep_axes(pipeline=None):
    options = dict(AXES)
    if pipeline is not None:
        for index, stage in enumerate(encode_pipeline_spec(pipeline)['stages'], 1):
            fields = dict(stage['parameters'])
            if stage['kind'] == 'interference':
                fields.setdefault('sinr_db', None)
            for name in _channel_axes(fields, f'channel.{index}'):
                options[name] = axis_label(name)
    return options


def _integer_axis(parameter):
    return (parameter in ('order', 'samples_per_symbol', 'span_symbols', 'symbol_count')
            or '.paths.' in parameter and parameter.endswith('.delay_samples'))


@dataclass(frozen=True, slots=True)
class SweepAxis:
    parameter: str
    values: tuple[int | float, ...]

    def __post_init__(self):
        if (not isinstance(self.parameter, str) or self.parameter not in AXES
                and _CHANNEL_AXIS.fullmatch(self.parameter) is None):
            raise ValueError('El parámetro del barrido no es compatible.')
        if not isinstance(self.values, (tuple, list)) or not 1 <= len(self.values) <= _MAX_RUNS:
            raise ValueError('Indicá entre 1 y 1024 valores por eje de barrido.')
        label = axis_label(self.parameter)
        if self.parameter == 'rolloff':
            values = tuple(real(value, label, minimum=0, maximum=1) for value in self.values)
        elif _integer_axis(self.parameter):
            minimum = 2 if self.parameter == 'order' else 0 if self.parameter.startswith('channel.') else 1
            values = tuple(integer(value, label, minimum=minimum, maximum=sys.maxsize) for value in self.values)
        else:
            values = tuple(real(value, label) for value in self.values)
        if len(set(values)) != len(values):
            raise ValueError('Quitá los valores repetidos del eje.')
        object.__setattr__(self, 'values', values)


def axis_from_text(parameter, text):
    convert = int if _integer_axis(parameter) else float
    try:
        values = tuple(convert(value.strip()) for value in text.split(','))
    except (AttributeError, ValueError) as exc:
        raise ValueError('Separá los valores del eje con comas y usá punto decimal.') from exc
    return SweepAxis(parameter, values)


@dataclass(frozen=True, slots=True)
class SweepSpec:
    base: ExperimentSpec
    axes: tuple[SweepAxis, ...]
    seed_policy: str = 'per_run'
    repetitions: int = 1

    def __post_init__(self):
        if not isinstance(self.base, ExperimentSpec):
            raise ValueError('El barrido requiere una configuración de enlace.')
        if self.seed_policy not in ('per_run', 'common'):
            raise ValueError('Seleccioná semillas independientes por corrida o una semilla común.')
        axes = self.axes
        if not isinstance(axes, (tuple, list)) or not axes or any(not isinstance(axis, SweepAxis) for axis in axes):
            raise ValueError('El barrido requiere al menos un eje con valores.')
        if len({axis.parameter for axis in axes}) != len(axes):
            raise ValueError('Cada parámetro puede aparecer una sola vez.')
        repetitions = integer(self.repetitions, 'Las repeticiones por punto', maximum=_MAX_RUNS)
        if repetitions * math.prod(len(axis.values) for axis in axes) > _MAX_RUNS:
            raise ResourceLimitError('El catálogo admite hasta 1024 corridas por barrido.')
        available = sweep_axes(self.base.channel_pipeline)
        if any(axis.parameter not in available for axis in axes):
            raise ValueError('Uno de los ejes no está disponible en la cadena del enlace.')
        levels = [axis.parameter.rsplit('.', 1)[0] for axis in axes
                  if axis.parameter.rsplit('.', 1)[-1] in ('power', 'sir_db', 'sinr_db')]
        if len(set(levels)) != len(levels):
            raise ValueError('Variá una sola referencia de potencia de interferencia por etapa.')
        object.__setattr__(self, 'axes', tuple(axes))
        object.__setattr__(self, 'repetitions', repetitions)


@dataclass(frozen=True, slots=True)
class SweepResult:
    directory: Path
    specification: SweepSpec
    planned: int
    runs: tuple[dict, ...]
    external_digests: tuple[tuple[str, str], ...] = ()

    @property
    def complete(self):
        return len(self.runs) == self.planned


def _channel_variant(pipeline, parameters, seed):
    if pipeline is None:
        return None
    document = encode_pipeline_spec(pipeline)
    for name, value in parameters.items():
        if not name.startswith('channel.'):
            continue
        _, stage, *path = name.split('.')
        target = document['stages'][int(stage)-1]['parameters']
        for key in path[:-1]:
            target = target[int(key)-1] if key.isdigit() else target[key]
        leaf = path[-1]
        if leaf in ('power', 'sir_db', 'sinr_db'):
            for alternative in ('power', 'sir_db', 'sinr_db'):
                target.pop(alternative, None)
        target[leaf] = value
    document['seed'] = int(settings_digest(['channel-sweep', pipeline.seed, seed])[:32], 16)
    return decode_pipeline_spec(document)


def _plan(spec):
    names = tuple(axis.parameter for axis in spec.axes)
    for index, values in enumerate(product(*(axis.values for axis in spec.axes))):
        parameters = dict(zip(names, values, strict=True))
        pulse = replace(spec.base.pulse, **{name: parameters[name] for name in (
            'rolloff', 'samples_per_symbol', 'span_symbols',
        ) if name in parameters})
        constellation = replace(spec.base.constellation, order=parameters.get('order', spec.base.constellation.order))
        bit_count = spec.base.bit_count
        if 'symbol_count' in parameters:
            bit_count = parameters['symbol_count'] * constellation.bits_per_symbol
        for replica in range(spec.repetitions):
            if spec.seed_policy == 'common' and spec.repetitions == 1:
                seed = spec.base.seed
            else:
                ordinal = replica if spec.seed_policy == 'common' else index * spec.repetitions + replica
                seed = int(settings_digest(['communications-sweep', spec.base.seed, ordinal])[:32], 16)
            channel = _channel_variant(spec.base.channel_pipeline, parameters, seed)
            configuration = replace(spec.base, constellation=constellation, pulse=pulse, seed=seed, bit_count=bit_count,
                                    eb_n0_db=parameters.get('eb_n0_db', spec.base.eb_n0_db), channel_pipeline=channel)
            reported = parameters if spec.repetitions == 1 else {**parameters, 'repetition': replica+1}
            yield reported, configuration


def _definition(spec, external=None):
    data = {
        'base': spec.base.document(), 'axes': [asdict(axis) for axis in spec.axes], 'seed_policy': spec.seed_policy,
    }
    if spec.repetitions != 1:
        data['repetitions'] = spec.repetitions
    definition = {'engine_contract': _SCHEMA, 'numpy': np.__version__, 'specification': data}
    if spec.base.channel_pipeline is not None:
        definition['scipy'] = scipy_version
    if external:
        definition['external_sha256'] = external
    return definition


def _decode_definition(document):
    if (not isinstance(document, dict) or type(document.get('engine_contract')) is not int
            or document['engine_contract'] != _SCHEMA):
        raise ValueError('El barrido utiliza un contrato de cálculo incompatible.')
    data = document.get('specification')
    if not isinstance(data, dict):
        raise ValueError('El catálogo requiere una configuración de barrido.')
    try:
        return SweepSpec(decode_experiment_spec(data['base']),
                         tuple(SweepAxis(**row) for row in data['axes']), data['seed_policy'], data.get('repetitions', 1))
    except (KeyError, TypeError) as exc:
        raise ValueError('La configuración del barrido está incompleta.') from exc


def _safe_file(folder, name):
    path = folder/name
    if path.is_symlink() or path.exists() and not path.is_file():
        raise ValueError('El catálogo requiere archivos regulares dentro de la carpeta del barrido.')
    return path


@contextmanager
def _locked(folder):
    path = _safe_file(folder, 'campaign.lock')
    with path.open('a+b') as handle:
        if os.name == 'nt':
            from msvcrt import LK_NBLCK, LK_UNLCK, locking
            if handle.tell() == 0:
                handle.write(b'\x00')
                handle.flush()
            handle.seek(0)
            lock = lambda: locking(handle.fileno(), LK_NBLCK, 1)
            unlock = lambda: locking(handle.fileno(), LK_UNLCK, 1)
        else:
            from fcntl import LOCK_EX, LOCK_NB, LOCK_UN, flock
            lock = lambda: flock(handle, LOCK_EX | LOCK_NB)
            unlock = lambda: flock(handle, LOCK_UN)
        try:
            lock()
        except OSError as exc:
            raise ValueError('Otro proceso está escribiendo este barrido o la carpeta impide obtener el bloqueo.') from exc
        try:
            yield
        finally:
            unlock()


def _filename(index):
    return f'run-{index+1:04d}.slproj'


def _binding_digests(spec, values, ctx):
    pipeline = spec.base.channel_pipeline
    names = () if pipeline is None else pipeline.external_names
    if set(values) != set(names):
        raise ValueError('Las señales externas deben coincidir con la configuración del barrido.')
    fingerprints = {}
    for name in names:
        signal = values[name]
        discrete_channel_size(signal, 0)
        fingerprints[name] = content_digest(signal, ctx.checkpoint)
    return fingerprints


def _archived_bindings(folder, spec, expected, ctx):
    if not expected:
        _binding_digests(spec, {}, ctx)
        return {}
    archive = _safe_file(folder, _EXTERNAL_ARCHIVE)
    ctx.require(4*archive.stat().st_size + 1024**2)
    stored, _ = session.load(archive, checkpoint=ctx.checkpoint)
    bindings = {}
    for row in stored.headers():
        if row['kind'] != 'signal' or row['title'] in bindings:
            raise ValueError('El archivo de señales externas tiene registros incompatibles o repetidos.')
        bindings[row['title']] = stored.get(row['id'])
    if _binding_digests(spec, bindings, ctx) != expected:
        raise ValueError('Las señales externas cambiaron desde la creación del catálogo.')
    return bindings


def _store_bindings(folder, spec, supplied, ctx):
    fingerprints = _binding_digests(spec, supplied, ctx)
    if fingerprints:
        archive = _safe_file(folder, _EXTERNAL_ARCHIVE)
        if not archive.exists():
            project = Project()
            for name, signal in supplied.items():
                project.add(signal, title=name, operation='Entrada externa del barrido',
                            verification=(fingerprints[name], (), ctx.checkpoint))
            session.save(archive, project, session.empty_workspace(),
                         before_commit=ctx.checkpoint, checkpoint=ctx.checkpoint)
        # This also reconciles a completed input archive if a prior attempt was interrupted.
        supplied = _archived_bindings(folder, spec, fingerprints, ctx)
    return supplied, fingerprints


def _external_digests(catalog):
    values = catalog['definition'].get('external_sha256', {})
    if not isinstance(values, dict) or any(not isinstance(name, str) or not isinstance(digest, str)
                                          for name, digest in values.items()):
        raise ValueError('El catálogo no contiene huellas válidas para las señales externas.')
    return values


def _artifact_entry(folder, index, assignment, ctx, external):
    parameters, spec = assignment
    file = _filename(index)
    path = _safe_file(folder, file)
    ctx.require(4*path.stat().st_size + 1024**2)
    project, _ = session.load(path, checkpoint=ctx.checkpoint)
    identifiers = [row['id'] for row in project.headers('calculation')
                   if row['title'] == 'Experimento de comunicaciones']
    if len(identifiers) != 1:
        raise ValueError('Cada archivo de corrida debe contener un experimento verificable.')
    identifier = identifiers[0]
    restored = load_experiment(project, identifier)
    expected = restored.report.get('provenance', {}).get('settings_sha256')
    if restored.specification != spec or expected != settings_digest(spec.document()):
        raise ValueError(f'La configuración registrada en {file} es distinta de la corrida planificada.')
    bindings = {} if restored.chain is None else restored.chain['external_sha256']
    if bindings != external:
        raise ValueError(f'Las señales externas de {file} difieren del catálogo.')
    with path.open('rb') as stream:
        stream.seek(-32, os.SEEK_END)
        digest = stream.read(32).hex()
    entry = {
        'ordinal': index+1, 'parameters': parameters, 'seed': spec.seed, 'file': file,
        'archive_sha256': digest, 'record': identifier, 'metrics': restored.report['metrics'],
        'theoretical': restored.report['theoretical'], 'synchronization': restored.report['synchronization']['state'],
    }
    if restored.chain is not None:
        entry['channel_ratios'] = {
            f'channel.{index}.measured_{ratio}_db': stage['statistics'][ratio]['db']
            for index, stage in enumerate(restored.chain['stages'], 1)
            if stage['effective']['kind'] == 'interference'
            for ratio in ('sir', 'snr', 'sinr')
        }
    return entry, project


def _read_manifest(path, ctx):
    catalog = read_json(path, checkpoint=ctx.checkpoint)
    if (not isinstance(catalog, dict) or catalog.get('format') != _FORMAT
            or type(catalog.get('schema')) is not int or catalog['schema'] != _SCHEMA
            or not isinstance(catalog.get('runs'), list)):
        raise ValueError('El archivo no contiene un catálogo de barrido compatible.')
    definition = catalog.get('definition')
    if not isinstance(definition, dict) or catalog.get('settings_sha256') != settings_digest(definition):
        raise ValueError('La huella de configuración del barrido es incorrecta.')
    return catalog


def _verify_runs(folder, catalog, plan, ctx, external):
    rows = catalog['runs']
    if len(rows) > len(plan):
        raise ValueError('El catálogo contiene más corridas que su planificación.')
    for index, row in enumerate(rows):
        ctx.checkpoint()
        if not isinstance(row, dict) or row.get('file') != _filename(index):
            raise ValueError('El catálogo contiene una ruta de corrida inválida.')
        entry, _ = _artifact_entry(folder, index, plan[index], ctx, external)
        if row != entry:
            raise ValueError(f'La evidencia de {_filename(index)} no coincide con el catálogo.')
    return list(rows)


def load_sweep(directory, execution: ExecutionContext | None = None) -> SweepResult:
    ctx = execution or ExecutionContext()
    folder = Path(directory).resolve()
    catalog = _read_manifest(_safe_file(folder, 'campaign.json'), ctx)
    spec = _decode_definition(catalog.get('definition'))
    external = _external_digests(catalog)
    _archived_bindings(folder, spec, external, ctx)
    plan = tuple(_plan(spec))
    rows = _verify_runs(folder, catalog, plan, ctx, external)
    ctx.checkpoint(100)
    return SweepResult(folder, spec, len(plan), tuple(rows), tuple(external.items()))


def run_sweep(spec: SweepSpec, directory, execution: ExecutionContext | None = None, *, external=None) -> SweepResult:
    """Resume only verified complete runs. Reconcile an archive committed before its catalog row."""
    if not isinstance(spec, SweepSpec):
        raise TypeError('Indicá una configuración de barrido.')
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    plan = tuple(_plan(spec))
    folder = Path(directory).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    with _locked(folder), ctx.aggregate_progress() as ctx:
        path = _safe_file(folder, 'campaign.json')
        if path.exists():
            catalog = _read_manifest(path, ctx)
            fingerprints = _external_digests(catalog)
            proof = settings_digest(_definition(spec, fingerprints))
            if catalog['settings_sha256'] != proof:
                raise ValueError('El barrido existente tiene otros parámetros o una versión numérica distinta.')
            if external is not None and _binding_digests(spec, external, ctx) != fingerprints:
                raise ValueError('Las señales externas indicadas no coinciden con el catálogo.')
            bindings = _archived_bindings(folder, spec, fingerprints, ctx)
            rows = _verify_runs(folder, catalog, plan, ctx, fingerprints)
        else:
            bindings, fingerprints = _store_bindings(folder, spec, {} if external is None else dict(external), ctx)
            definition = _definition(spec, fingerprints)
            proof = settings_digest(definition)
            rows = []
            catalog = {'format': _FORMAT, 'schema': _SCHEMA, 'definition': definition,
                       'settings_sha256': proof, 'runs': rows}
            write_json(path, catalog, before_commit=ctx.checkpoint, checkpoint=ctx.checkpoint)
        for index in range(len(rows), len(plan)):
            ctx.checkpoint(index*100//len(plan))
            archive = _safe_file(folder, _filename(index))
            if not archive.exists():
                def progress(percentage):
                    ctx.checkpoint((index*100 + percentage*85//100)//len(plan))

                result = run_experiment(plan[index][1], external=bindings, execution=replace(ctx, progress=progress))
                save_experiment(archive, result, ctx)
                del result
            row, _ = _artifact_entry(folder, index, plan[index], ctx, fingerprints)
            replacement = [*rows, row]
            write_json(path, catalog | {'runs': replacement}, before_commit=ctx.checkpoint, checkpoint=ctx.checkpoint)
            rows = replacement
        ctx.checkpoint(100)
    return SweepResult(folder, spec, len(plan), tuple(rows), tuple(fingerprints.items()))


def load_sweep_run(result: SweepResult, ordinal: int, execution: ExecutionContext | None = None):
    if not isinstance(result, SweepResult):
        raise TypeError('Seleccioná un barrido verificado.')
    index = integer(ordinal, 'La corrida', maximum=len(result.runs)) - 1
    ctx = execution or ExecutionContext()
    assignment = tuple(_plan(result.specification))[index]
    expected = dict(result.external_digests)
    _archived_bindings(result.directory, result.specification, expected, ctx)
    row, project = _artifact_entry(result.directory, index, assignment, ctx, expected)
    if row != result.runs[index]:
        raise ValueError('El archivo de la corrida cambió desde la verificación del catálogo.')
    return project, row['record']


def summarize_sweep_repetitions(result: SweepResult):
    """Estimate means across independent runs at each point, conditional on alignment."""
    axes = [axis.parameter for axis in result.specification.axes]
    groups = {}
    for row in result.runs:
        key = tuple(row['parameters'][name] for name in axes)
        groups.setdefault(key, []).append(row)
    summary = []
    for point, rows in groups.items():
        measurements = {}
        for name in ('ber', 'ser', 'evm'):
            field = 'percent' if name == 'evm' else 'value'
            values = [row['metrics'][name][field] for row in rows
                      if row['metrics'] is not None and row['metrics'][name][field] is not None]
            count = len(values)
            mean = math.fsum(value/count for value in values) if count else None
            confidence = None
            if count >= 3:
                scale = max(values)
                relative = float(np.std(np.asarray(values)/scale, ddof=1)) if scale > 0 else 0.0
                if relative > 0:
                    margin = (float(student_t.ppf(.975, count-1))*relative/math.sqrt(count))*scale
                    upper = mean + margin if name == 'evm' else min(1.0, mean + margin)
                    if math.isfinite(upper):
                        confidence = {'lower': max(0.0, mean - margin), 'upper': upper}
            measurements[name] = {'mean': mean, 'confidence': confidence, 'valid': count}
        summary.append({'parameters': dict(zip(axes, point, strict=True)), 'runs': len(rows),
                        'measurements': measurements, 'theoretical': rows[0]['theoretical']})
    return summary


def export_sweep_csv(result: SweepResult, path, execution: ExecutionContext | None = None):
    if not isinstance(result, SweepResult):
        raise TypeError('La exportación requiere un barrido verificado.')
    target = Path(path).resolve()
    if target.parent == result.directory and (target.name in ('campaign.json', 'campaign.lock', _EXTERNAL_ARCHIVE)
                                               or target.name.startswith('run-') and target.suffix == '.slproj'):
        raise ValueError('Elegí un archivo CSV distinto de los archivos del barrido.')
    ctx = execution or ExecutionContext()
    names = [axis.parameter for axis in result.specification.axes]
    if result.specification.repetitions > 1:
        names.append('repetition')
    ratios = sorted({key for row in result.runs for key in row.get('channel_ratios', {})})
    columns = ['ordinal', *names, 'seed', 'synchronization', 'bits', 'bit_errors', 'ber',
               'symbols', 'symbol_errors', 'ser', 'evm_percent', 'ber_reference', 'ser_reference',
               'theoretical_ber', 'theoretical_ser', *ratios]
    with atomic_binary_file(target, before_commit=ctx.checkpoint) as file:
        text = io.TextIOWrapper(file, encoding='utf-8', newline='')
        try:
            writer = csv.DictWriter(text, fieldnames=columns)
            writer.writeheader()
            for row in result.runs:
                ctx.checkpoint()
                data = {key: row[key] for key in ('ordinal', 'seed', 'synchronization')} | row['parameters']
                data.update(row.get('channel_ratios', {}))
                metrics = row['metrics']
                if metrics is not None:
                    data.update(bits=metrics['ber']['evaluated'], bit_errors=metrics['ber']['errors'],
                                ber=metrics['ber']['value'], symbols=metrics['ser']['evaluated'],
                                symbol_errors=metrics['ser']['errors'], ser=metrics['ser']['value'],
                                evm_percent=metrics['evm']['percent'])
                reference = row['theoretical']
                if reference is not None:
                    data.update(ber_reference=reference['ber_reference'], ser_reference=reference['ser_reference'],
                                theoretical_ber=reference['ber'], theoretical_ser=reference['ser'])
                writer.writerow(data)
            text.flush()
        finally:
            text.detach()
