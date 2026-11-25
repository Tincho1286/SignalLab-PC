"""Characterize representative CPU, memory and cancellation in isolated processes."""

import argparse
import ctypes
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from threading import Event, Timer
from time import perf_counter
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def peak_rss():
    if sys.platform == 'linux':
        from resource import getrusage, RUSAGE_SELF
        return getrusage(RUSAGE_SELF).ru_maxrss * 1024
    if sys.platform == 'win32':
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [('cb', wintypes.DWORD), ('faults', wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in
                ('peak', 'current', 'paged_peak', 'paged', 'nonpaged_peak', 'nonpaged',
                 'pagefile', 'pagefile_peak')]

        handle = ctypes.windll.kernel32.GetCurrentProcess
        handle.restype = wintypes.HANDLE
        function = ctypes.windll.psapi.GetProcessMemoryInfo
        function.argtypes = (wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD)
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        if not function(handle(), ctypes.byref(counters), counters.cb):
            raise OSError('GetProcessMemoryInfo falló.')
        return counters.peak
    raise ValueError('La medición tiene perfiles Windows y Linux.')


def numeric(operation, size):
    import numpy as np
    from signallab_pc.fourier import dtft
    from signallab_pc.model import Signal
    from signallab_pc.operations import dft
    from signallab_pc.sampling import resample_rational
    from signallab_pc.resources import available_physical_memory

    x = Signal(np.ones(size), 0, metadata={'sample_rate_hz': 8000})
    tasks = {
        'dft': lambda: dft(x),
        'dtft': lambda: dtft(x, -np.pi, np.pi, 1025),
        'resample': lambda: resample_rational(x, 2, 3),
    }
    available = available_physical_memory()
    peak_before = peak_rss()
    start = perf_counter()
    result = tasks[operation]()
    elapsed = perf_counter()-start
    expected = {'dft': size, 'dtft': 1025, 'resample': (2*size+2)//3}
    assert len(result.values)==expected[operation] and np.isfinite(result.values).all()
    if operation in ('dft','dtft'):
        dc = result.values[0 if operation=='dft' else 512]
        np.testing.assert_allclose(dc, size, atol=1e-10, rtol=1e-13)
    return dict(operation=operation, samples=size, output_values=len(result.values),
                seconds=elapsed, peak_before_bytes=peak_before, peak_after_bytes=peak_rss(),
                available_before_bytes=available)


def boundaries():
    from signallab_pc.resources import ResourceLimitError, ensure_working_set
    accepted = ensure_working_set(560, live_arrays=4, available_bytes=102400)
    try:
        ensure_working_set(561, live_arrays=4, available_bytes=102400)
    except ResourceLimitError:
        return dict(available_bytes=102400, fraction=.35, bytes_per_sample=16, live_arrays=4,
                    accepted_samples=560, accepted_bytes=accepted, rejected_samples=561)
    raise ValueError('El presupuesto aceptó una muestra fuera del límite.')


def cancellation():
    import numpy as np
    from signallab_pc import jobs, symbolic_process
    from signallab_pc.fourier import dtft
    from signallab_pc.model import Signal

    event = Event()
    stopped = []

    def signal_cancel():
        stopped.append(perf_counter())
        event.set()

    def progress(percent):
        if percent > 0 and not event.is_set():
            signal_cancel()

    jobs.bind(event, progress)
    try:
        dtft(Signal(np.ones(4096)), count=4097)
    except jobs.OperationCancelled:
        numeric_seconds = perf_counter()-stopped.pop()
    else:
        raise ValueError('DTFT entregó un resultado tras solicitar cancelación.')
    finally:
        jobs.clear()
    event.clear()
    real_popen = subprocess.Popen
    child = []
    timer = Timer(.15, signal_cancel)

    def started(*args, **kwargs):
        process = real_popen(*args, **kwargs)
        child.append((process, Path(kwargs['cwd'])))
        timer.start()
        return process

    jobs.bind(event, None)
    try:
        with patch.object(symbolic_process.subprocess,'Popen', side_effect=started):
            symbolic_process.run_request({'operation':'z_expression',
                                          'expression':'(n+1)^10*exp(-n)', 'lower':'0','upper':'oo'})
    except jobs.OperationCancelled:
        worker_seconds = perf_counter()-stopped.pop()
    else:
        raise ValueError('El proceso simbólico no llegó a la cancelación de prueba.')
    finally:
        jobs.clear()
        timer.cancel()
    process, directory = child[0]
    assert process.poll() is not None and not directory.exists()
    return dict(dtft_seconds_after_signal=numeric_seconds,
                symbolic_seconds_after_signal=worker_seconds, worker_exit=process.returncode,
                symbolic_temporary_removed=True, symbolic_cancel_from_launch_seconds=.15)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--probe', nargs=2)
    args = parser.parse_args()
    if args.probe:
        print(json.dumps(numeric(args.probe[0], int(args.probe[1]))))
        return
    if args.output is None:
        parser.error('Specify --output.')
    env = os.environ | {'OPENBLAS_NUM_THREADS':'1', 'OMP_NUM_THREADS':'1'}
    rows = []
    for name, sizes in (('dft',(16384,262144)), ('dtft',(1024,8192)),
                        ('resample',(16384,262144))):
        for size in sizes:
            run = subprocess.check_output([sys.executable,'-B',__file__,'--probe',name,str(size)],
                                          cwd=ROOT, env=env, timeout=90, text=True)
            rows.append(json.loads(run))
    report = dict(platform=platform.platform(), python=platform.python_version(),
                  commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                  budget=boundaries(), cancellation=cancellation(), numeric=rows)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    main()
