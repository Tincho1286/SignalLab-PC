"""Resumable communication campaigns built on transactional project archives."""

from contextlib import contextmanager
import csv
from dataclasses import asdict, dataclass, replace
import io
from itertools import product
import math
import os
from pathlib import Path
import sys

import numpy as np

from . import session
from .atomic_file import atomic_binary_file, write_json
from .communications_data import integer, real
from .communications_experiment import ExperimentSpec, run_experiment
from .communications_storage import decode_experiment_spec, load_experiment, save_experiment
from .execution import ExecutionContext
from .input_files import read_json
from .operation_provenance import settings_digest
from .resources import ResourceLimitError


AXES = {
    'eb_n0_db': 'Eb/N₀ (dB)', 'order': 'Orden de modulación M',
    'rolloff': 'Roll-off β', 'samples_per_symbol': 'Muestras por símbolo',
    'span_symbols': 'Duración del pulso (símbolos)', 'symbol_count': 'Cantidad de símbolos',
}
_FORMAT = 'signallab-communications-sweep'
_SCHEMA = 1
_MAX_RUNS = 1024


@dataclass(frozen=True, slots=True)
class SweepAxis:
    parameter: str
    values: tuple[int | float, ...]

    def __post_init__(self):
        if not isinstance(self.parameter, str) or self.parameter not in AXES:
            raise ValueError('El parámetro del barrido no es compatible.')
        if not isinstance(self.values, (tuple, list)) or not 1 <= len(self.values) <= _MAX_RUNS:
            raise ValueError('Indicá entre 1 y 1024 valores por eje de barrido.')
        label = AXES[self.parameter]
        if self.parameter == 'eb_n0_db':
            values = tuple(real(value, label) for value in self.values)
        elif self.parameter == 'rolloff':
            values = tuple(real(value, label, minimum=0, maximum=1) for value in self.values)
        else:
            minimum = 2 if self.parameter == 'order' else 1
            values = tuple(integer(value, label, minimum=minimum, maximum=sys.maxsize) for value in self.values)
        if len(set(values)) != len(values):
            raise ValueError('Quitá los valores repetidos del eje.')
        object.__setattr__(self, 'values', values)


def axis_from_text(parameter, text):
    convert = float if parameter in ('eb_n0_db', 'rolloff') else int
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
        if math.prod(len(axis.values) for axis in axes) > _MAX_RUNS:
            raise ResourceLimitError('El catálogo admite hasta 1024 corridas por barrido.')
        object.__setattr__(self, 'axes', tuple(axes))


@dataclass(frozen=True, slots=True)
class SweepResult:
    directory: Path
    specification: SweepSpec
    planned: int
    runs: tuple[dict, ...]

    @property
    def complete(self):
        return len(self.runs) == self.planned


def _plan(spec):
    names = tuple(axis.parameter for axis in spec.axes)
    for i, values in enumerate(product(*(axis.values for axis in spec.axes))):
        parameters = dict(zip(names, values, strict=True))
        pulse = replace(spec.base.pulse, **{name: parameters[name] for name in (
            'rolloff', 'samples_per_symbol', 'span_symbols',
        ) if name in parameters})
        constellation = replace(spec.base.constellation, order=parameters.get('order', spec.base.constellation.order))
        bit_count = spec.base.bit_count
        if 'symbol_count' in parameters:
            bit_count = parameters['symbol_count'] * constellation.bits_per_symbol
        seed = spec.base.seed if spec.seed_policy == 'common' else int(
            settings_digest(['communications-sweep', spec.base.seed, i])[:32], 16
        )
        configuration = replace(spec.base, constellation=constellation, pulse=pulse, seed=seed, bit_count=bit_count,
                                eb_n0_db=parameters.get('eb_n0_db', spec.base.eb_n0_db))
        yield parameters, configuration


def _definition(spec):
    return {'engine_contract': _SCHEMA, 'numpy': np.__version__, 'specification': asdict(spec)}


def _decode_definition(document):
    if (not isinstance(document, dict) or type(document.get('engine_contract')) is not int
            or document['engine_contract'] != _SCHEMA):
        raise ValueError('El barrido utiliza un contrato de cálculo incompatible.')
    data = document.get('specification')
    if not isinstance(data, dict):
        raise ValueError('El catálogo requiere una configuración de barrido.')
    try:
        return SweepSpec(decode_experiment_spec(data['base']),
                         tuple(SweepAxis(**row) for row in data['axes']), data['seed_policy'])
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


def _artifact_entry(folder, index, assignment, ctx):
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
    if restored.specification != spec or expected != settings_digest(asdict(spec)):
        raise ValueError(f'La configuración registrada en {file} es distinta de la corrida planificada.')
    with path.open('rb') as stream:
        stream.seek(-32, os.SEEK_END)
        digest = stream.read(32).hex()
    entry = {
        'ordinal': index+1, 'parameters': parameters, 'seed': spec.seed, 'file': file,
        'archive_sha256': digest, 'record': identifier, 'metrics': restored.report['metrics'],
        'theoretical': restored.report['theoretical'], 'synchronization': restored.report['synchronization']['state'],
    }
    return entry, project


def _read_manifest(path, ctx):
    catalog = read_json(path, checkpoint=ctx.checkpoint)
    if (not isinstance(catalog, dict) or catalog.get('format') != _FORMAT
            or type(catalog.get('schema')) is not int or catalog['schema'] != _SCHEMA
            or not isinstance(catalog.get('runs'), list)):
        raise ValueError('El archivo no contiene un catálogo de barrido compatible.')
    definition = catalog.get('definition')
    if catalog.get('settings_sha256') != settings_digest(definition):
        raise ValueError('La huella de configuración del barrido es incorrecta.')
    return catalog


def _verify_runs(folder, catalog, plan, ctx):
    rows = catalog['runs']
    if len(rows) > len(plan):
        raise ValueError('El catálogo contiene más corridas que su planificación.')
    for index, row in enumerate(rows):
        ctx.checkpoint()
        if not isinstance(row, dict) or row.get('file') != _filename(index):
            raise ValueError('El catálogo contiene una ruta de corrida inválida.')
        entry, _ = _artifact_entry(folder, index, plan[index], ctx)
        if row != entry:
            raise ValueError(f'La evidencia de {_filename(index)} no coincide con el catálogo.')
    return list(rows)


def load_sweep(directory, execution: ExecutionContext | None = None) -> SweepResult:
    ctx = execution or ExecutionContext()
    folder = Path(directory).resolve()
    catalog = _read_manifest(_safe_file(folder, 'campaign.json'), ctx)
    spec = _decode_definition(catalog.get('definition'))
    plan = tuple(_plan(spec))
    rows = _verify_runs(folder, catalog, plan, ctx)
    ctx.checkpoint(100)
    return SweepResult(folder, spec, len(plan), tuple(rows))


def run_sweep(spec: SweepSpec, directory, execution: ExecutionContext | None = None) -> SweepResult:
    """Resume only verified complete runs. Reconcile an archive committed before its catalog row."""
    if not isinstance(spec, SweepSpec):
        raise TypeError('Indicá una configuración de barrido.')
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    plan = tuple(_plan(spec))
    folder = Path(directory).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    definition = _definition(spec)
    proof = settings_digest(definition)
    with _locked(folder), ctx.aggregate_progress() as ctx:
        path = _safe_file(folder, 'campaign.json')
        if path.exists():
            catalog = _read_manifest(path, ctx)
            if catalog['settings_sha256'] != proof:
                raise ValueError('El barrido existente tiene otros parámetros o una versión numérica distinta.')
            rows = _verify_runs(folder, catalog, plan, ctx)
        else:
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

                result = run_experiment(plan[index][1], execution=replace(ctx, progress=progress))
                save_experiment(archive, result, ctx)
                del result
            row, _ = _artifact_entry(folder, index, plan[index], ctx)
            replacement = [*rows, row]
            write_json(path, catalog | {'runs': replacement}, before_commit=ctx.checkpoint, checkpoint=ctx.checkpoint)
            rows = replacement
        ctx.checkpoint(100)
    return SweepResult(folder, spec, len(plan), tuple(rows))


def load_sweep_run(result: SweepResult, ordinal: int, execution: ExecutionContext | None = None):
    if not isinstance(result, SweepResult):
        raise TypeError('Seleccioná un barrido verificado.')
    index = integer(ordinal, 'La corrida', maximum=len(result.runs)) - 1
    ctx = execution or ExecutionContext()
    assignment = tuple(_plan(result.specification))[index]
    row, project = _artifact_entry(result.directory, index, assignment, ctx)
    if row != result.runs[index]:
        raise ValueError('El archivo de la corrida cambió desde la verificación del catálogo.')
    return project, row['record']


def export_sweep_csv(result: SweepResult, path, execution: ExecutionContext | None = None):
    if not isinstance(result, SweepResult):
        raise TypeError('La exportación requiere un barrido verificado.')
    target = Path(path).resolve()
    if target.parent == result.directory and (target.name in ('campaign.json', 'campaign.lock')
                                               or target.name.startswith('run-') and target.suffix == '.slproj'):
        raise ValueError('Elegí un archivo CSV distinto de los archivos del barrido.')
    ctx = execution or ExecutionContext()
    names = [axis.parameter for axis in result.specification.axes]
    columns = ['ordinal', *names, 'seed', 'synchronization', 'bits', 'bit_errors', 'ber',
               'symbols', 'symbol_errors', 'ser', 'evm_percent', 'ber_reference', 'ser_reference',
               'theoretical_ber', 'theoretical_ser']
    with atomic_binary_file(target, before_commit=ctx.checkpoint) as file:
        text = io.TextIOWrapper(file, encoding='utf-8', newline='')
        try:
            writer = csv.DictWriter(text, fieldnames=columns)
            writer.writeheader()
            for row in result.runs:
                ctx.checkpoint()
                data = {key: row[key] for key in ('ordinal', 'seed', 'synchronization')} | row['parameters']
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
