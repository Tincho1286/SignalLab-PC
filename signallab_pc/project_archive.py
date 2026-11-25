"""Optional transactional project or session with binary signal records."""

from hashlib import sha256
from hmac import compare_digest
import json
from pathlib import Path
from shutil import disk_usage
import struct

import numpy as np

from .atomic_file import atomic_binary_file
from .execution import ExecutionContext
from .input_files import decode_finite_json, regular_binary_file
from .jobs import checkpoint as check_job
from .project import Project, _record_without_samples
from .resources import ResourceLimitError, ensure_working_set


MAGIC = b'SLPROJ\x00\x01'
_MAX_HEADER = 16 * 1024**2
_MAX_RECORDS = 10000
_CHUNK = 1024**2
_DTYPE = np.dtype('<c16')


def save(path, project, workspace=None, *, before_commit=None, checkpoint=None):
    check = checkpoint or check_job
    check()
    records = project._stable_records()
    if len(records) > _MAX_RECORDS:
        raise ResourceLimitError('El proyecto científico supera 10 000 registros.')
    counts = [len(row['data']['values']) if row['kind'] == 'signal' else 0 for row in records]
    header = json.dumps({
        'project': {'format': 'signallab-project', 'schema_version': 2,
                    'records': [_record_without_samples(row) for row in records]},
        'workspace': workspace, 'counts': counts,
    }, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')
    if len(header) > _MAX_HEADER:
        raise ResourceLimitError('Los metadatos del proyecto científico superan 16 MiB.')
    prefix = MAGIC + struct.pack('<I', len(header))
    size = len(prefix) + len(header) + _DTYPE.itemsize * sum(counts) + 32
    if size > disk_usage(Path(path).parent).free:
        raise ResourceLimitError('El proyecto científico requiere más espacio disponible en disco.')

    def commit_check():
        check()
        if before_commit is not None:
            before_commit()

    digest = sha256(prefix + header)
    with ExecutionContext().reserve(8*len(header) + _CHUNK), atomic_binary_file(path, before_commit=commit_check) as file:
        file.write(prefix)
        file.write(header)
        for row, count in zip(records, counts, strict=True):
            if count:
                values = memoryview(np.asarray(row['data']['values'], dtype=_DTYPE)).cast('B')
                for offset in range(0, len(values), _CHUNK):
                    check()
                    block = values[offset:offset+_CHUNK]
                    digest.update(block)
                    file.write(block)
        file.write(digest.digest())


def _read_manifest(file, size):
    prefix = file.read(len(MAGIC) + 4)
    if len(prefix) != len(MAGIC) + 4 or not prefix.startswith(MAGIC):
        raise ValueError('Formato de proyecto científico desconocido.')
    length = struct.unpack('<I', prefix[len(MAGIC):])[0]
    if not 0 < length <= _MAX_HEADER or len(prefix) + length + 32 > size:
        raise ValueError('Tamaño de manifiesto de proyecto inválido.')
    ensure_working_set(length, bytes_per_sample=1, live_arrays=8)
    header = file.read(length)
    if len(header) != length:
        raise ValueError('El manifiesto del proyecto científico está incompleto.')
    manifest = decode_finite_json(header.decode('utf-8'))
    if not isinstance(manifest, dict) or set(manifest) != {'project', 'workspace', 'counts'}:
        raise ValueError('Manifiesto de proyecto científico inválido.')
    document, workspace, counts = (manifest[key] for key in ('project', 'workspace', 'counts'))
    records = document.get('records') if isinstance(document, dict) else None
    if (not isinstance(records, list) or not isinstance(counts, list)
            or len(records) != len(counts) or len(records) > _MAX_RECORDS):
        raise ValueError('El catálogo del proyecto científico está incompleto.')
    for row, count in zip(records, counts, strict=True):
        if not isinstance(row, dict) or type(count) is not int or count < 0:
            raise ValueError('Referencia de muestras inválida.')
        if row.get('kind') == 'signal':
            if not count or not isinstance(row.get('data'), dict) or 'values' in row['data']:
                raise ValueError('La señal requiere una referencia binaria no vacía.')
        elif count:
            raise ValueError('Sólo los registros de señal admiten referencias binarias.')
    data_bytes = _DTYPE.itemsize * sum(counts)
    if len(prefix) + length + data_bytes + 32 != size:
        raise ValueError('El tamaño de las muestras no coincide con el manifiesto.')
    return document, workspace, counts, sha256(prefix + header), 3*data_bytes + 8*length


def _read_samples(file, document, counts, digest, check):
    for row, count in zip(document['records'], counts, strict=True):
        if not count:
            continue
        check()
        data = np.empty(count, dtype=_DTYPE)
        payload = memoryview(data).cast('B')
        for offset in range(0, len(payload), _CHUNK):
            check()
            block = payload[offset:offset+_CHUNK]
            if file.readinto(block) != len(block):
                raise ValueError('Muestras incompletas en el proyecto científico.')
            digest.update(block)
        row['data']['values'] = data
    if not compare_digest(file.read(32), digest.digest()) or file.read(1):
        raise ValueError('Falló la integridad del proyecto científico.')


def load(path, *, checkpoint=None):
    check = checkpoint or check_job
    check()
    with regular_binary_file(path, 'El proyecto científico requiere un archivo regular.') as (file, info):
        document, workspace, counts, digest, footprint = _read_manifest(file, info.st_size)
        with ExecutionContext().reserve(footprint):
            _read_samples(file, document, counts, digest, check)
            check()
            project = Project.from_document(document, checkpoint=check)
    check()
    return project, workspace
