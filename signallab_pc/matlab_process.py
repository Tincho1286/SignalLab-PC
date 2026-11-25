"""Bounded transport for MAT inspection via a dedicated native reader process."""

import json
import math
import os
from pathlib import Path
import stat
import subprocess
import sys
from contextlib import contextmanager
from tempfile import TemporaryDirectory
from threading import BoundedSemaphore
from time import monotonic

from .jobs import checkpoint
from .execution import ExecutionContext
from .resources import ResourceLimitError, available_physical_memory, ensure_working_set


_MIB = 1024**2
MAT_FILE_BYTES = 128 * _MIB
MAT_ARRAY_BYTES = 64 * _MIB
MAT_WORKER_BYTES = 1024 * _MIB
MAT_TIMEOUT_SECONDS = 15
MAT_VARIABLES = 4096
_READERS = BoundedSemaphore(1)
_HDF_SIGNATURE = b'\x89HDF\r\n\x1a\n'


def _stamp(info):
    if not stat.S_ISREG(info.st_mode):
        raise ValueError('El origen MAT debe ser un archivo regular.')
    if not 0 < info.st_size <= MAT_FILE_BYTES:
        raise ResourceLimitError('El archivo MAT debe ocupar entre 1 byte y 128 MiB.')
    return [info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns]


def _array_bytes(shape, itemsize):
    if not isinstance(shape, (list, tuple)) or len(shape) > 2 or any(type(n) is not int or n <= 0 for n in shape):
        raise ValueError('La variable MAT debe ser un vector o matriz no vacía.')
    size = math.prod(shape) * itemsize
    if size > MAT_ARRAY_BYTES:
        raise ResourceLimitError('La variable MAT decodificada supera 64 MiB.')
    return size


@contextmanager
def _open_source(path, stamp):
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NONBLOCK', 0)
    with open(path, 'rb', opener=lambda filename, _: os.open(filename, flags)) as stream:
        if _stamp(os.fstat(stream.fileno())) != stamp:
            raise ValueError('El archivo MAT cambió desde la selección. Volvé a abrirlo.')
        yield stream
        if _stamp(os.fstat(stream.fileno())) != stamp:
            raise ValueError('El archivo MAT cambió durante la lectura. Volvé a abrirlo.')


def _hdf_source(stream, size):
    offset = 0
    while offset + len(_HDF_SIGNATURE) <= size:
        stream.seek(offset)
        if stream.read(len(_HDF_SIGNATURE)) == _HDF_SIGNATURE:
            stream.seek(0)
            return True
        offset = 2 * offset if offset else 512
    stream.seek(0)
    return False


def file_identity(path):
    return _stamp(Path(path).stat())


def read_mat(path, stamp, *, name=None, shape=None):
    checkpoint()
    if not _READERS.acquire(blocking=False):
        raise ResourceLimitError('Hay otro archivo MAT en lectura. Volvé a intentar cuando termine.')
    try:
        return _run_reader(path, stamp, name, shape)
    finally:
        _READERS.release()


def _run_reader(path, stamp, name, shape):
    if file_identity(path) != stamp:
        raise ValueError('El archivo MAT cambió desde la selección. Volvé a abrirlo.')
    budget = min(MAT_WORKER_BYTES, int(.35 * available_physical_memory()))
    if budget < 256 * _MIB:
        raise ResourceLimitError('Se requieren 256 MiB de presupuesto disponible para iniciar el lector MAT.')
    with ExecutionContext().reserve(budget), TemporaryDirectory(prefix='signallab-mat-') as directory:
        folder = Path(directory)
        request = folder/'request.json'
        request.write_text(json.dumps({'path': str(path), 'stamp': stamp, 'name': name, 'shape': shape, 'budget': budget}),
                           encoding='utf-8')
        entry = [sys.executable] if getattr(sys, 'frozen', False) else [
            sys.executable, str(Path(__file__).resolve().parent.parent/'main.py')]
        env = {key: value for key, value in os.environ.items() if not key.startswith('HDF5_')}
        env.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', HDF5_PLUGIN_PATH=directory)
        deadline = monotonic() + MAT_TIMEOUT_SECONDS
        with subprocess.Popen(entry + ['--matlab-job', str(folder)], cwd=folder, env=env,
                              stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)) as process:
            try:
                while process.poll() is None:
                    checkpoint()
                    remaining = deadline - monotonic()
                    if remaining <= 0:
                        raise TimeoutError(f'La lectura MAT superó {MAT_TIMEOUT_SECONDS} s.')
                    try:
                        process.wait(timeout=min(.05, remaining))
                    except subprocess.TimeoutExpired:
                        pass
            finally:
                if process.poll() is None:
                    process.kill()
        checkpoint()
        report = folder/'result.json'
        if not report.is_file() or report.stat().st_size > 1024**2:
            raise ValueError('El lector MAT se detuvo o superó su límite de recursos.')
        answer = json.loads(report.read_text(encoding='utf-8'))
        if process.returncode != 0:
            error_type = ResourceLimitError if answer.get('resource') else ValueError
            raise error_type(answer.get('error', 'El lector MAT no pudo completar la operación.'))
        if name is None:
            return answer['hdf'], {key: tuple(value) for key, value in answer['entries'].items()}
        import numpy as np

        dtype = np.dtype(answer['dtype'])
        payload = folder/'values.bin'
        if dtype.kind not in 'biufc' or dtype.itemsize > 16 or answer['shape'] != list(shape):
            raise ValueError('La respuesta del lector MAT contiene una variable incompatible.')
        size = _array_bytes(shape, dtype.itemsize)
        ensure_working_set(size, bytes_per_sample=1, live_arrays=6)
        with payload.open('rb') as stream:
            if os.fstat(stream.fileno()).st_size != size:
                raise ValueError('La variable MAT llegó incompleta.')
            return np.fromfile(stream, dtype=dtype, count=math.prod(shape)).reshape(shape)


def worker(folder):
    from .native_job_limit import limit_worker_memory

    folder = Path(folder)
    try:
        request = json.loads((folder/'request.json').read_text(encoding='utf-8'))
        budget = request['budget']
        if type(budget) is not int or not 256 * _MIB <= budget <= MAT_WORKER_BYTES:
            raise ResourceLimitError('Presupuesto del lector MAT no admitido.')
        limit_worker_memory(budget)
        with _open_source(request['path'], request['stamp']) as stream:
            hdf = _hdf_source(stream, request['stamp'][2])
            if request['name'] is None:
                entries = _entries(stream, hdf)
                result = {'hdf': hdf, 'entries': entries}
            else:
                array = _load(stream, hdf, request['name'], tuple(request['shape']))
                array.tofile(folder/'values.bin')
                result = {'shape': array.shape, 'dtype': array.dtype.str}
        status = 0
    except Exception as error:
        result = {'error': str(error)[:2000] or 'El lector alcanzó un límite de recursos.',
                  'resource': isinstance(error, MemoryError)}
        status = 1
    (folder/'result.json').write_text(json.dumps(result), encoding='utf-8')
    return status


def _entries(stream, hdf):
    found = {}

    def add(name, shape):
        if len(found) >= MAT_VARIABLES:
            raise ResourceLimitError('El catálogo MAT supera 4096 variables.')
        if len(name) <= 128 and len(shape) <= 2 and math.prod(shape):
            found[name] = shape

    if hdf:
        import h5py
        from .matlab_import import _local_numeric_dataset

        with h5py.File(stream, 'r') as file:
            def visit(name, node):
                if not name.startswith('#') and _local_numeric_dataset(node, h5py):
                    add(name, tuple(reversed(node.shape)))
            file.visititems(visit)
    else:
        from scipy.io import whosmat

        kinds = {'double', 'single', 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32',
                 'int64', 'uint64', 'logical'}
        for name, shape, kind in whosmat(stream):
            if kind in kinds:
                add(name, shape)
    if not found:
        raise ValueError('No hay vectores ni matrices numéricas locales compatibles.')
    return found


def _load(stream, hdf, name, shape):
    import numpy as np

    _array_bytes(shape, 1)
    if hdf:
        import h5py
        from .matlab_import import _local_dataset

        with h5py.File(stream, 'r') as file:
            dataset = _local_dataset(file, name, h5py)
            if tuple(reversed(dataset.shape)) != shape:
                raise ValueError('La variable MAT cambió de dimensiones. Volvé a abrir el archivo.')
            _array_bytes(shape, dataset.dtype.itemsize)
            result = dataset[()]
        if result.dtype.names:
            result = result['real'] + 1j*result['imag']
        result = np.asarray(result).T
    else:
        from scipy.io import loadmat

        result = loadmat(stream, variable_names=[name], verify_compressed_data_integrity=True)[name]
    if result.shape != shape or result.dtype.kind not in 'biufc' or result.dtype.itemsize > 16:
        raise ValueError('La variable MAT cambió de dimensiones o tipo.')
    _array_bytes(shape, result.dtype.itemsize)
    if not np.isfinite(result).all():
        raise ValueError('Las variables MAT deben tener muestras finitas.')
    return np.asarray(result, order='C')
