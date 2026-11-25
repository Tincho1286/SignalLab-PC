"""Measure Core workloads without including application startup in operation times."""

import argparse
from hashlib import file_digest
import json
import os
from pathlib import Path
import platform
from statistics import median
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Event, Timer
from time import perf_counter, process_time
from unittest.mock import patch

from check_resource_limits import ROOT, cancellation, peak_rss


def workload(operation, size, directory):
    import numpy as np
    from signallab_pc import session
    from signallab_pc.atomic_file import write_json
    from signallab_pc.dft_application import DFTRequest, calculate_dft, store_dft
    from signallab_pc.dsp_application import (
        FIRRequest, IDFTRequest, PSDRequest, ResampleRequest, apply_fir, calculate_idft,
        estimate_psd, resample, resample_size,
    )
    from signallab_pc.dsp_pipeline import DSPPipelineRequest, estimate_pipeline_memory, run_pipeline
    from signallab_pc.filters import Transfer
    from signallab_pc.model import Signal
    from signallab_pc.operations import DFT_WORK_BYTES_PER_BIN, dft
    from signallab_pc.project import Project
    from signallab_pc.resources import available_physical_memory, ensure_working_set
    from signallab_pc.scientific_storage import load_binary_signal, save_binary_signal
    from signallab_pc.symbolic_process import run_request

    # JSON expands numeric payloads into Python objects. Screen conservatively first.
    serialization = {'publish', 'session_save', 'session_load', 'json_write'}
    ensure_working_set(size, bytes_per_sample=1024 if operation in serialization else 512, live_arrays=1)
    seed = 20261125
    source = Signal(np.random.default_rng(seed).standard_normal(size), -3,
                    metadata={'sample_rate_hz': 8192})
    model = Transfer(np.ones(31) / 31, [1])
    conversion = ResampleRequest(source, 2, 3)
    signal_path = directory / 'samples.slbin'
    project_path = directory / 'session.json'
    archive_path = directory / 'project.slproj'
    flat_path = directory / 'data.json'
    mat_path = directory / 'signal.mat'
    matlab = None
    spectrum = dft(source) if operation == 'idft' else None
    project = Project()
    if operation.startswith(('session_', 'archive_')):
        store_dft(project, calculate_dft(DFTRequest(source)), source=source)
    if operation == 'session_load':
        session.save(project_path, project, session.empty_workspace())
    if operation == 'archive_load':
        session.save(archive_path, project, session.empty_workspace())
    if operation == 'slbin_read':
        save_binary_signal(source, signal_path)
    if operation in ('mat_classic', 'mat_hdf5'):
        from signallab_pc.matlab_import import MatlabFile
        if operation == 'mat_classic':
            from scipy.io import savemat
            savemat(mat_path, {'signal': source.values}, do_compression=True)
        else:
            import h5py
            with h5py.File(mat_path, 'w') as handle:
                handle.create_dataset('signal', data=source.values, compression='gzip')
        matlab = lambda: MatlabFile(mat_path).load('signal')
    result = calculate_dft(DFTRequest(source)) if operation == 'publish' else None
    flat = source.values.real.tolist() if operation == 'json_write' else None
    pipeline = DSPPipelineRequest(conversion, model)
    _, _, _, _, resampling_estimate = resample_size(conversion)
    jobs = {
        'dft': (lambda ctx: calculate_dft(DFTRequest(source), ctx), DFT_WORK_BYTES_PER_BIN * size),
        'idft': (lambda ctx: calculate_idft(IDFTRequest(spectrum), ctx), DFT_WORK_BYTES_PER_BIN * size),
        'fir': (lambda ctx: apply_fir(FIRRequest(source, model), ctx), (size + len(model.b)) * 128),
        'resample': (lambda ctx: resample(conversion, ctx), resampling_estimate),
        'psd': (lambda ctx: estimate_psd(PSDRequest(source), ctx), 256 * 256),
        'pipeline': (lambda ctx: run_pipeline(pipeline, ctx), estimate_pipeline_memory(pipeline).total_bytes),
        'publish': (lambda ctx: store_dft(Project(), result, source=source, execution=ctx), None),
        'session_save': (lambda ctx: session.save(project_path, project, session.empty_workspace(),
                                                 checkpoint=ctx.checkpoint), None),
        'session_load': (lambda ctx: session.load(project_path, checkpoint=ctx.checkpoint), None),
        'archive_save': (lambda ctx: session.save(archive_path, project, session.empty_workspace(),
                                                 checkpoint=ctx.checkpoint), 16 * 2 * size),
        'archive_load': (lambda ctx: session.load(archive_path, checkpoint=ctx.checkpoint), 16 * 2 * size * 3),
        'slbin_write': (lambda ctx: save_binary_signal(source, signal_path, ctx), 32 * size),
        'slbin_read': (lambda ctx: load_binary_signal(signal_path, ctx), 64 * size),
        'json_write': (lambda ctx: write_json(flat_path, flat, checkpoint=ctx.checkpoint), None),
        'symbolic': (lambda ctx: run_request({'operation': 'z_expression', 'expression': 'exp(-n)',
                                            'lower': '0', 'upper': 'oo'}), None),
        'mat_classic': (lambda ctx: ctx.run(matlab), None),
        'mat_hdf5': (lambda ctx: ctx.run(matlab), None),
    }
    task, estimate = jobs[operation]
    return task, estimate, available_physical_memory()


def measure(operation, size, repeats):
    from signallab_pc.execution import ExecutionContext
    from signallab_pc.resources import ResourceLimitError

    with TemporaryDirectory(prefix='signallab-bench-') as folder:
        directory = Path(folder)
        prep_start = perf_counter()
        try:
            task, estimate, available = workload(operation, size, directory)
        except ResourceLimitError as error:
            return dict(operation=operation, samples=size, status='inadmitted', detail=str(error))
        prep = perf_counter() - prep_start
        rss_before = peak_rss()
        task(ExecutionContext())
        rows = []
        for _ in range(repeats):
            start, cpu = perf_counter(), process_time()
            task(ExecutionContext())
            rows.append([perf_counter() - start, process_time() - cpu])
        return dict(operation=operation, samples=size, status='measured', seconds_setup=prep,
                    work_estimate_bytes=estimate, available_bytes=available,
                    peak_before_bytes=rss_before, peak_after_bytes=peak_rss(),
                    files_bytes={item.name: item.stat().st_size for item in directory.iterdir()},
                    wall_samples=[row[0] for row in rows], cpu_samples=[row[1] for row in rows],
                    wall_median_seconds=median(row[0] for row in rows),
                    cpu_median_seconds=median(row[1] for row in rows))


def timed_cancellation(operation, size):
    from signallab_pc.execution import ExecutionContext
    from signallab_pc.jobs import OperationCancelled

    numeric = operation in {'dft', 'idft', 'fir', 'resample', 'psd'}
    with TemporaryDirectory(prefix='signallab-cancel-') as folder:
        directory = Path(folder)
        task, _, _ = workload(operation, size, directory)
        def digests():
            files = {}
            for path in directory.iterdir():
                with path.open('rb') as stream:
                    files[path.name] = file_digest(stream, 'sha256').hexdigest()
            return files

        files = digests()
        event, triggered = Event(), []
        def request_stop():
            triggered.append(perf_counter())
            event.set()

        timer = Timer(.001, request_stop)
        run = ExecutionContext.run
        starts = []

        def observed_run(ctx, *args, **kwargs):
            if not starts:
                starts.append(perf_counter())
                timer.start()
            return run(ctx, *args, **kwargs)

        try:
            with patch.object(ExecutionContext, 'run', observed_run):
                if not numeric:
                    starts.append(perf_counter())
                    timer.start()
                task(ExecutionContext(cancel=event))
        except OperationCancelled:
            elapsed = perf_counter() - triggered[0]
            assert digests() == files
            return dict(operation=operation, samples=size, status='cancelled',
                        trigger_after_seconds=triggered[0] - starts[0],
                        latency_seconds=elapsed, files_preserved=True)
        finally:
            timer.cancel()
            if timer.ident is not None:
                timer.join()
        return dict(operation=operation, samples=size, status='completed_before_acknowledgement')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--probe', nargs=2)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('--repeats debe ser positivo')
    if args.probe:
        op, value = args.probe
        data = (timed_cancellation(op, int(value.split(':')[1])) if value.startswith('cancel:')
                else measure(op, int(value), args.repeats))
        print(json.dumps(data))
        return
    if args.output is None:
        parser.error('Specify --output.')
    from importlib.metadata import version

    def git(*arguments):
        return subprocess.check_output(['git', *arguments], cwd=ROOT, text=True).strip()

    revision = git('rev-parse', 'HEAD')
    clean = not git('status', '--porcelain')
    sizes = (1024, 16384, 65536, 262144, 1048576)
    operations = {
        **dict.fromkeys(('dft', 'idft', 'fir', 'resample', 'psd', 'pipeline', 'slbin_read', 'slbin_write',
                         'archive_save', 'archive_load'), sizes),
        **dict.fromkeys(('publish', 'session_save', 'session_load', 'json_write'), sizes[:4]),
        **dict.fromkeys(('mat_classic', 'mat_hdf5'), (65536, 262144)),
        'symbolic': (1,),
    }
    env = os.environ | {'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'}
    def isolate(op, value):
        cmd = [sys.executable, '-B', __file__, '--probe', op, str(value), '--repeats', str(args.repeats)]
        return json.loads(subprocess.check_output(cmd, cwd=ROOT, env=env, timeout=100, text=True))

    rows = [isolate(op, size) for op, lengths in operations.items() for size in lengths]
    numerical = ('dft', 'idft', 'fir', 'resample', 'psd', 'pipeline', 'slbin_write', 'archive_save')
    cancelled = [isolate(op, f'cancel:{size}') for size in (262144, 1048576) for op in numerical]
    cancelled.extend(isolate(op, 'cancel:262144') for op in
                     ('json_write', 'session_load', 'archive_load', 'mat_classic', 'mat_hdf5'))
    cancelled.append(isolate('slbin_read', 'cancel:1048576'))
    symbolic = cancellation()
    report = dict(commit=revision, clean_checkout=clean and git('rev-parse', 'HEAD') == revision
                  and not git('status', '--porcelain'),
                  platform=platform.platform(), machine=platform.machine(), processor=platform.processor(),
                  logical_cpus=os.cpu_count(), python=platform.python_version(),
                  versions={name: version(name) for name in ('numpy', 'scipy', 'sympy')},
                  openblas_threads=1, omp_threads=1, seed=20261125, repeats=args.repeats,
                  cold_process_each_case=True, one_warmup_per_case=True, filesystem_cache='warm',
                  cancellation=cancelled, symbolic_cancellation=symbolic, measurements=rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
