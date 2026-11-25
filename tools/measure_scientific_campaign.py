"""Exercise a repeatable synthetic 48-run campaign using independent SLPROJ files."""

import argparse
import json
from pathlib import Path
import platform
from shutil import disk_usage
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np

from measure_core_hardening import peak_rss
from signallab_pc.atomic_file import write_json
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.project_archive import load, save
from signallab_pc.resources import ensure_working_set


SAMPLES = 65536 * 4
RECORDS = 6
MILESTONES = (1, 4, 8, 16, 32, 48)
SEEDS = (20261125, 9937, 25001)


def samples(run, ordinal):
    configuration, seed = divmod(run, len(SEEDS))
    index = np.arange(SAMPLES, dtype=np.int64)
    real = ((index * (2 * configuration + 1) + SEEDS[seed]) % 1021 - 510) / 64
    imaginary = ((index * (2 * ordinal + 3) - SEEDS[seed]) % 511 - 255) / 32
    return real + 1j * imaginary


def run_project(run):
    project = Project()
    parent = []
    configuration, seed = divmod(run, len(SEEDS))
    for ordinal in range(RECORDS):
        signal = Signal(samples(run, ordinal), origin=-64,
                        metadata={'sample_rate_hz': 8192, 'time_start_s': -1/128,
                                  'configuration': configuration, 'seed': SEEDS[seed], 'channel': ordinal})
        parent = [project.add(signal, title=f'Registro {ordinal+1}', operation='Banco sintético', parents=parent)]
    return project


def cancelled_write(path, project):
    calls = 0
    requested = None

    def stop():
        nonlocal calls, requested
        calls += 1
        if calls == 5:
            requested = perf_counter()
            raise OperationCancelled()

    try:
        save(path, project, checkpoint=stop)
    except OperationCancelled:
        elapsed = perf_counter() - requested
    else:
        raise RuntimeError('La escritura cancelada llegó a publicarse.')
    if path.exists() or any(path.parent.glob(path.name + '.*.tmp')):
        raise RuntimeError('La escritura cancelada dejó un archivo parcial.')
    return elapsed


def digest(path):
    with path.open('rb') as stream:
        # Reopening above verifies this trailer against the entire project.
        stream.seek(-32, 2)
        return stream.read(32).hex()


def verify_run(restored, run, expected=None):
    headers = restored.headers()
    if expected is not None:
        assert headers == expected
    assert len(headers) == RECORDS
    for ordinal, row in enumerate(headers):
        signal = restored.get(row['id'])
        assert signal.origin == -64 and signal.metadata['sample_rate_hz'] == 8192
        assert signal.metadata['time_start_s'] == -1/128
        assert signal.metadata['configuration'] == run//3 and signal.metadata['seed'] == SEEDS[run%3]
        assert signal.metadata['channel'] == ordinal
        assert row['parents'] == ([] if ordinal == 0 else [headers[ordinal-1]['id']])
        np.testing.assert_array_equal(signal.values, samples(run, ordinal))


def measure(folder, runs):
    required = runs * RECORDS * SAMPLES * 16 + 16 * 1024**2
    if disk_usage(folder).free < required:
        raise RuntimeError(f'El banco necesita {required} B disponibles en el volumen temporal.')
    ensure_working_set(RECORDS * SAMPLES, bytes_per_sample=16, live_arrays=5)
    index_path = folder/'campaign.json'
    reports = []
    interrupted = None
    begin = perf_counter()
    for run in range(runs):
        path = folder/f'run-{run+1:02}.slproj'
        start = perf_counter()
        project = run_project(run)
        generation = perf_counter() - start
        if run == min(7, runs-1):
            previous = index_path.read_bytes() if index_path.is_file() else b''
            latency = cancelled_write(path, project)
            retained = json.loads(previous)['runs'] if previous else []
            assert retained == reports
            for row in retained:
                previous_path = folder/row['file']
                assert digest(previous_path) == row['digest_sha256']
                previous_project, workspace = load(previous_path)
                assert workspace is None
                verify_run(previous_project, row['run']-1)
                del previous_project
            assert previous == (index_path.read_bytes() if index_path.is_file() else b'')
            reports = retained
            interrupted = dict(run=run+1, previous_runs=len(retained), aborted_seconds=latency,
                               partial_file=False, catalog_preserved=True, revalidated=True, retried=True)
        start = perf_counter()
        save(path, project)
        write_seconds = perf_counter() - start
        headers = project.headers()
        del project
        start = perf_counter()
        restored, workspace = load(path)
        read_seconds = perf_counter() - start
        assert workspace is None
        verify_run(restored, run, headers)
        del restored
        reports.append(dict(run=run+1, file=path.name, configuration=run//3, seed=SEEDS[run%3],
                            records=RECORDS, samples=RECORDS*SAMPLES, bytes=path.stat().st_size,
                            digest_sha256=digest(path), generation_seconds=generation,
                            save_seconds=write_seconds, load_seconds=read_seconds, peak_rss_bytes=peak_rss(),
                            elapsed_seconds=perf_counter()-begin))
        write_json(index_path, {'version': 1, 'runs': reports})
    assert json.loads(index_path.read_bytes())['runs'] == reports
    summary = []
    for count in sorted(set(MILESTONES).intersection(range(1, runs+1)) | {runs}):
        batch = reports[:count]
        summary.append(dict(runs=count, records=count*RECORDS, samples=count*RECORDS*SAMPLES,
                            bytes=sum(row['bytes'] for row in batch),
                            elapsed_seconds=batch[-1]['elapsed_seconds'],
                            save_seconds=sum(row['save_seconds'] for row in batch),
                            load_seconds=sum(row['load_seconds'] for row in batch),
                            peak_rss_bytes=max(row['peak_rss_bytes'] for row in batch)))
    return dict(milestones=summary, runs=reports, interruption=interrupted, integrity_verified=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--runs', type=int, choices=range(1, 49), default=48)
    args = parser.parse_args()
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    clean = not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='signallab-campaign-', dir=args.output.parent) as folder:
        data = measure(Path(folder), args.runs)
    report = dict(commit=sha, clean_checkout=clean, os=platform.platform(), python=platform.python_version(),
                  numpy=np.__version__, project_policy='independent_complete_projects', **data)
    write_json(args.output, report)
    print(report['milestones'][-1])


if __name__ == '__main__':
    main()
