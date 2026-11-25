"""Reproduce storage measurements using only fresh synthetic data."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import struct
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from check_resource_limits import peak_rss


FORMATS = ('json', 'npy', 'npz', 'hdf5', 'sigmf', 'hybrid')
SIZES = (1024, 65536, 262144, 1048576, 10000000)


def sample_array(size, kind):
    import numpy as np
    generator = np.random.default_rng(20261125)
    values = generator.normal(size=size)
    if kind == 'complex':
        values = values + 1j*generator.normal(size=size)
    return values.astype('<c16' if kind == 'complex' else '<f8', copy=False)


def atomic_write(path, writer):
    temporary = path.with_suffix('.tmp')
    with temporary.open('wb') as stream:
        writer(stream)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def codec(format_name, path, values):
    import numpy as np
    from signallab_pc import storage
    from signallab_pc.model import Signal

    count = len(values)
    snippet = slice(count//2, count//2+32)
    dtype = values.dtype
    extra = None
    if format_name == 'json':
        source = Signal(values, metadata={'sample_rate_hz':8000})
        write = lambda: storage.save_json(source,path)
        read = lambda: storage.load_json(path).values
        partial = lambda: read()[snippet]
    elif format_name == 'npy':
        write = lambda: atomic_write(path,lambda stream:np.save(stream,values,allow_pickle=False))
        read = lambda: np.load(path,allow_pickle=False)
        partial = lambda: np.load(path,allow_pickle=False,mmap_mode='r')[snippet].copy()
    elif format_name == 'npz':
        write = lambda: atomic_write(path,lambda stream:np.savez_compressed(stream,values=values,allow_pickle=False))
        def read():
            with np.load(path,allow_pickle=False) as bundle:
                return bundle['values']
        partial = lambda: read()[snippet]
    elif format_name == 'hdf5':
        import h5py
        def writer(stream):
            # HDF5's file-object driver needs read/write access to its stream.
            with h5py.File(stream,'w',driver='fileobj') as file:
                file.create_dataset('values',data=values)
        def write():
            temporary = path.with_suffix('.tmp')
            with temporary.open('w+b') as stream:
                writer(stream)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary,path)
        def get(selection):
            with h5py.File(path,'r') as file:
                return file['values'][selection]
        read = lambda: get(slice(None))
        partial = lambda: get(snippet)
    elif format_name == 'sigmf':
        from signallab_pc.atomic_file import write_json
        extra = path.with_suffix('.sigmf-meta')
        metadata = {'global': {'core:datatype': 'cf64_le' if dtype.kind=='c' else 'rf64_le',
                               'core:sample_rate':8000, 'core:version':'1.2.0'},
                    'captures':[{'core:sample_start':0}], 'annotations':[]}
        def write():
            atomic_write(path,lambda stream:stream.write(memoryview(values).cast('B')))
            write_json(extra,metadata)
        def read():
            json.loads(extra.read_text(encoding='utf-8'))
            return np.fromfile(path,dtype=dtype)
        partial = lambda: np.memmap(path,dtype=dtype,mode='r')[snippet].copy()
    else:
        data = memoryview(values).cast('B')
        def writer(stream):
            header = json.dumps({'count':count,'dtype':dtype.str,'sample_rate_hz':8000,
                                 'sha256':hashlib.sha256(data).hexdigest()}).encode()
            stream.write(struct.pack('<I',len(header)))
            stream.write(header)
            stream.write(data)
        def read():
            with path.open('rb') as stream:
                metadata = json.loads(stream.read(struct.unpack('<I',stream.read(4))[0]))
                payload = stream.read()
            if hashlib.sha256(payload).hexdigest()!=metadata['sha256']:
                raise ValueError('Huella incorrecta')
            return np.frombuffer(payload,dtype=metadata['dtype'])
        def partial():
            # Access by offset alone. Full-file integrity is measured by read().
            with path.open('rb') as stream:
                head_size = struct.unpack('<I',stream.read(4))[0]
                stream.seek(4+head_size+snippet.start*dtype.itemsize)
                return np.fromfile(stream,dtype=dtype,count=32)
        write = lambda: atomic_write(path,writer)
    return write,read,partial,extra


def measure(function, repeats):
    samples = []
    for _ in range(repeats):
        t0 = perf_counter()
        value = function()
        samples.append(perf_counter()-t0)
    return value, dict(median_s=statistics.median(samples), min_s=min(samples), max_s=max(samples))


def probe(format_name, size, kind, repeats):
    import numpy as np
    values = sample_array(size,kind)
    with TemporaryDirectory(prefix='signallab-storage-probe-') as directory:
        path = Path(directory)/('data.sigmf-data' if format_name=='sigmf' else 'data.bin')
        write,read,partial,extra = codec(format_name,path,values)
        write()
        np.testing.assert_array_equal(read(),values)
        _, writes = measure(write,repeats)
        result, reads = measure(read,repeats)
        subset, partials = measure(partial,repeats)
        np.testing.assert_array_equal(result,values)
        np.testing.assert_array_equal(subset,values[size//2:size//2+32])
        return dict(format=format_name, size=size, kind=kind, write=writes, read=reads,
                    partial=partials, peak_rss_bytes=peak_rss(), size_bytes=path.stat().st_size+
                    (extra.stat().st_size if extra else 0), exact=True)


def historical(repeats):
    from signallab_pc import session
    from signallab_pc.dft_application import DFTRequest, calculate_dft, store_dft
    from signallab_pc.model import Signal
    from signallab_pc.project import Project
    from numpy.testing import assert_array_equal

    source = Signal(sample_array(65536,'complex'),-7)
    spectrum = calculate_dft(DFTRequest(source))
    with TemporaryDirectory(prefix='signallab-storage-history-') as directory:
        path = Path(directory)/'historical.json'
        def write():
            project = Project()
            _, key = store_dft(project,spectrum,source=source)
            session.save(path,project,session.empty_workspace())
            return key
        write()
        key, writes = measure(write,repeats)
        restored, reads = measure(lambda:session.load(path)[0].get(key),repeats)
        assert_array_equal(restored.values,spectrum.spectrum.values)
        return dict(size=65536, write=writes, read=reads, size_bytes=path.stat().st_size,
                    peak_rss_bytes=peak_rss(), exact=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--repeats',type=int,default=3)
    parser.add_argument('--quick',action='store_true')
    parser.add_argument('--probe',nargs=3)
    parser.add_argument('--historical',action='store_true')
    args = parser.parse_args()
    if args.repeats < 2:
        parser.error('Use al menos dos repeticiones.')
    if args.probe:
        mode,count,kind = args.probe
        print(json.dumps(probe(mode,int(count),kind,args.repeats)))
        return
    if args.historical:
        print(json.dumps(historical(args.repeats)))
        return
    if args.output is None:
        parser.error('Indicá --output.')
    from signallab_pc.resources import available_physical_memory
    budget = min(512*2**20,available_physical_memory()//4)
    sizes = SIZES[:2] if args.quick else SIZES
    accepted = [n for n in sizes if n*256 <= budget]
    skipped = [n for n in sizes if n not in accepted]
    cmd = [sys.executable,'-B','-X','utf8',str(Path(__file__).resolve()),'--repeats',str(args.repeats)]
    env = os.environ | {'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'}
    prior=json.loads(subprocess.check_output([*cmd,'--historical'],env=env,timeout=180))
    rows=[]
    for n in accepted:
        for kind in ('real','complex'):
            for mode in FORMATS:
                output=subprocess.check_output([*cmd,'--probe',mode,str(n),kind],env=env,timeout=180)
                rows.append(json.loads(output))
            print('Storage',n,kind,'OK',flush=True)
    report=dict(platform=platform.platform(),python=platform.python_version(), repeats=args.repeats,
                candidate=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                case_budget_bytes=budget, skipped_sizes=skipped, cache='process isolated, cache primed, write includes fsync',
                historical_session=prior,cases=rows)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
