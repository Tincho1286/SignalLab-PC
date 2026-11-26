"""Measure scaling on the archived Phase 04 candidate."""
import argparse
from hashlib import sha256
import importlib.abc
import json
from pathlib import Path
import platform
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import perf_counter

CANDIDATE = "2a0a3fd97e63bd766d09739d51dc9aab4e9e6efb"
COUNTS = (1, 4, 16)


class BlockQt(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.split('.')[0] in {'PySide6', 'PyQt6', 'shiboken6', 'qtpy'}:
            raise AssertionError(name)


def measure_paths(count):
    import numpy as np
    from signallab_pc.communications_fading import FadingPath, FadingSpec, apply_fading
    from signallab_pc.model import Signal

    samples, rate, fd = 32768, 96000, 64
    paths = tuple(FadingPath(i, 1/count) for i in range(count))
    source = Signal(np.ones(samples), metadata={'sample_rate_hz': rate})
    start = perf_counter()
    result = apply_fading(source, FadingSpec(paths, 54001, fd))
    elapsed = perf_counter() - start
    expected = np.zeros(samples+count-1, dtype=np.complex128)
    for offset, realization in enumerate(result.realizations):
        expected[offset:offset+samples] += realization.coefficients.values
    np.testing.assert_array_equal(result.signal.values, expected)
    assert len(result.realizations) == count and result.signal.metadata['sample_rate_hz'] == rate
    return {'count': count, 'input_samples': samples, 'sample_rate_hz': rate, 'f_d_hz': fd,
            'compute_seconds': elapsed, 'coefficient_bytes': sum(r.coefficients.values.nbytes for r in result.realizations),
            'verified_output_samples': len(result.signal.values)}


def measure_replicas(count):
    from signallab_pc.communications_experiment import ExperimentSpec
    from signallab_pc.communications_fading import FadingPath, FadingSpec
    from signallab_pc.communications_pipeline import ChannelPipelineSpec, ChannelStage
    from signallab_pc.communications_sweep import SweepAxis, SweepSpec, load_sweep, run_sweep

    pipeline = ChannelPipelineSpec((ChannelStage(FadingSpec((FadingPath(0, 1, 4),), 2026)),), seed=2026)
    base = ExperimentSpec(bit_count=256, seed=2026, channel_pipeline=pipeline)
    spec = SweepSpec(base, (SweepAxis('eb_n0_db', (6,)),), repetitions=count)
    with TemporaryDirectory(prefix='sl04-replica-profile-') as folder:
        directory = Path(folder)
        start = perf_counter()
        created = run_sweep(spec, directory)
        stored = perf_counter() - start
        start = perf_counter()
        restored = load_sweep(directory)
        loaded = perf_counter() - start
        assert restored.runs == created.runs and len(restored.runs) == restored.planned == count
        archive_bytes = sum(entry.stat().st_size for entry in directory.rglob('*') if entry.is_file())
    return {'count': count, 'bits_per_replica': base.bit_count, 'store_seconds': stored, 'reopen_seconds': loaded,
            'archive_bytes': archive_bytes, 'replicas_verified': len(restored.runs)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profiles', type=Path)
    parser.add_argument('--child', choices=('paths', 'replicas'))
    parser.add_argument('--count', type=int, choices=COUNTS)
    args = parser.parse_args()
    sys.path.insert(0, str(Path.cwd()))
    if args.child:
        sys.meta_path.insert(0, BlockQt())
        sys.path.insert(0, str(Path.cwd()/'tools'))
        from check_resource_limits import peak_rss
        measurement = (measure_paths if args.child == 'paths' else measure_replicas)(args.count)
        print(json.dumps({**measurement, 'peak_rss_bytes': peak_rss()}, allow_nan=False))
        return
    if args.profiles is None:
        parser.error('Indique un archivo con --profiles.')
    subprocess.run(['git', 'diff', '--exit-code', CANDIDATE, '--', 'signallab_pc', 'tools',
                    '.python-version', 'requirements-lock.txt'], check=True)
    report = {'candidate': CANDIDATE, 'platform': platform.platform(), 'python': platform.python_version(),
              'qt_blocked': True, 'script_sha256': sha256(Path(__file__).read_bytes()).hexdigest()}
    for case in ('paths', 'replicas'):
        report[case] = []
        for count in COUNTS:
            command = [sys.executable, '-B', '-X', 'utf8', str(Path(__file__).absolute()),
                       '--child', case, '--count', str(count)]
            result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=35)
            if result.returncode:
                raise RuntimeError(result.stderr)
            report[case].append(json.loads(result.stdout))
    args.profiles.write_bytes((json.dumps(report, allow_nan=False, indent=2)+'\n').encode('utf-8'))
    print(json.dumps(report, allow_nan=False))


if __name__ == '__main__':
    main()
