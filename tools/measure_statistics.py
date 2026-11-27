"""Measure Phase 05 time, memory, cancellation and persistence on native runners."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import math
import os
from pathlib import Path
import platform
from statistics import median
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Event
from time import perf_counter, process_time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import scipy
from scipy.signal import lfilter

from check_resource_limits import peak_rss
from check_quality_gate_05 import RESOURCE_PROFILES
from signallab_pc import project_archive, session
from signallab_pc.adaptive_filter import adaptive_fir
from signallab_pc.atomic_file import write_json
from signallab_pc.dsp_application import PSDRequest, estimate_psd
from signallab_pc.execution import ExecutionContext, ResourcePool
from signallab_pc.jobs import OperationCancelled
from signallab_pc.kalman_filter import kalman_filter
from signallab_pc.model import Signal
from signallab_pc.monte_carlo import CampaignSpec, Scenario, load_campaign, run_campaign
from signallab_pc.multivariate_probability import Gaussian, generate_gaussian
from signallab_pc.probability import Distribution, generate_realizations
from signallab_pc.project import Project
from signallab_pc.resources import ResourceLimitError
from signallab_pc.state_space import StateModel
from signallab_pc.stochastic_covariance import covariance_matrix
from signallab_pc.time_series_identification import fit_arma


class MeasuredPool(ResourcePool):
    def __init__(self):
        super().__init__(256*1024**2)
        self.maximum = 0

    def reserve(self, amount):
        self.maximum = max(self.maximum, amount)
        return super().reserve(amount)


def realizations(scale, ctx, _):
    n, replicas = scale*2**17, 4
    records = generate_realizations(Distribution('normal', {'mean': 1., 'std': 2.}), n, 701,
                                    replicas=replicas, origin=-100, rate=48000, execution=ctx)
    assert len(records) == replicas and all(record.origin == -100 and len(record.values) == n
                                           for record in records)
    x = np.stack([record.values.real for record in records])
    np.testing.assert_allclose(x.mean(axis=1), 1, atol=12/math.sqrt(n))
    np.testing.assert_allclose(x.var(axis=1), 4, atol=24*math.sqrt(2/(n-1)))
    assert not np.array_equal(x[0], x[1]) and records[0].metadata['sample_rate_hz'] == 48000
    return {'samples': n, 'replicas': replicas, 'complexity': 'O(samples × replicas)'}


def joint_covariance(scale, ctx, _):
    n, width = scale*2**14, 8
    cov = np.eye(width) + .25*np.ones((width,width))
    records = generate_gaussian(Gaussian(np.arange(width), cov), n, 702, execution=ctx)
    output = covariance_matrix(records, execution=ctx)
    x = np.stack([record.values.real for record in records])
    np.testing.assert_allclose(output['covariance']['real'], np.cov(x), atol=2e-12)
    np.testing.assert_allclose(output['covariance']['real'], cov, atol=.07)
    return {'samples': n, 'dimensions': width, 'complexity': 'O(samples × dimensions²)'}


def identification(scale, ctx, _):
    n = scale*4096
    white = np.random.default_rng(703).normal(size=n+1024)
    x = lfilter([1.,.28], [1.,-.7], white)[1024:]
    result = fit_arma(Signal(x), 1, 1, validation=n//8, execution=ctx)
    np.testing.assert_allclose(result['a'], [1.,-.7], atol=.09)
    np.testing.assert_allclose(result['b'], [1.,.28], atol=.09)
    return {'samples': n, 'order': [1,1], 'reserved_samples': n//8,
            'complexity': 'linear in samples per likelihood evaluation at fixed orders'}


def spectral(scale, ctx, _):
    n, segment = scale*2**18, 2048
    x = 1.25*np.cos(2*np.pi/16*np.arange(n))
    result = estimate_psd(PSDRequest(Signal(x,metadata={'sample_rate_hz':1024}), method='bartlett',
                                     segment=segment), ctx)
    np.testing.assert_allclose(result.values.real.sum()*result.step, 1.25**2/2, atol=1e-12)
    np.testing.assert_allclose(abs(result.axis[np.argmax(result.values.real)]), 64, atol=1e-12)
    return {'samples': n, 'segment': segment, 'complexity': 'O(samples × log(segment))'}


def kalman_trial(n, ctx):
    x = 3 + np.random.default_rng(704).normal(size=n)
    model = StateModel([[1.]], [[0.]], [[1.]], [[0.]], 1/128)
    result = kalman_filter(model, x[:,None], [[0.]], [[1.]], [0.], [[1.]], execution=ctx)
    np.testing.assert_allclose(result.corrected[-1,0], x.sum()/(n+1), atol=1e-11)
    np.testing.assert_allclose(result.posterior_covariance[-1,0,0], 1/(n+1), atol=1e-12)


def kalman(scale, ctx, _):
    n = scale*2048
    kalman_trial(n, ctx)
    return {'samples': n, 'states': 1, 'complexity': 'linear in samples at fixed dimensions'}


def adaptive(scale, ctx, _):
    n, length = scale*2**14, 8
    x = np.random.default_rng(705).normal(size=n)
    taps = np.array([.5,.25,-.125,0.,.125,0.,-.2,.15])
    result = adaptive_fir(Signal(x), Signal(lfilter(taps,[1.],x)), length=length,
                          method='nlms', reserve=n//8, execution=ctx)
    np.testing.assert_allclose(result.system.b, taps, atol=1e-9)
    assert np.max(abs(result.error.values[-(n//8):])) < 1e-8
    return {'samples': n, 'length': length, 'complexity': 'O(samples × length) for NLMS'}


def campaign_spec(scale):
    scenarios = tuple(Scenario(str(p), Distribution('bernoulli', {'p': p})) for p in (.01,.1,.4,.8))
    return CampaignSpec(scenarios, 'probability', 706, samples=2048, replicas=scale*128,
                        batch=32, low=1, high=1, common_random_numbers=True)


def monte_carlo(scale, ctx, folder):
    spec = campaign_spec(scale)
    target = folder/'campaign'
    result = run_campaign(spec,target,ctx)
    assert len(result.replicas) == spec.replicas
    for row, p in zip(result.report['summaries'], (.01,.1,.4,.8), strict=True):
        assert abs(row['value']-p) <= 6*math.sqrt(p*(1-p)/row['trials'])
    assert load_campaign(target,ctx).replicas == result.replicas
    return {'samples_per_replica': spec.samples, 'replicas': spec.replicas, 'scenarios': len(spec.scenarios),
            'disk_bytes': sum(path.stat().st_size for path in target.iterdir() if path.is_file()),
            'complexity': 'O(samples × replicas × scenarios) with batched summaries'}


def archive(scale, ctx, folder):
    n, project = scale*2**17, Project()
    record = Signal(np.resize([1.,-2.,3j,4.],n),name='Perfil de archivo',origin=-16)
    key = project.add(record)
    target = folder/'profile.slproj'
    with patch.object(project_archive, 'ExecutionContext', return_value=ctx):
        begin = perf_counter()
        session.save(target, project, session.empty_workspace(), checkpoint=ctx.checkpoint)
        write_seconds = perf_counter()-begin
        begin = perf_counter()
        restored, workspace = session.load(target, checkpoint=ctx.checkpoint)
        read_seconds = perf_counter()-begin
    assert restored.get(key).origin == -16 and workspace == session.empty_workspace()
    np.testing.assert_array_equal(restored.get(key).values, record.values)
    return {'samples': n, 'disk_bytes': target.stat().st_size, 'write_seconds': write_seconds,
            'read_seconds': read_seconds, 'complexity': 'linear in samples'}


NUMERICAL_TRIALS = {
    'realizations': realizations, 'joint_covariance': joint_covariance, 'identification': identification,
    'spectral': spectral, 'kalman': kalman, 'adaptive': adaptive, 'monte_carlo': monte_carlo, 'archive': archive,
}


def numeric_profile(name, scale):
    pool = MeasuredPool()
    with TemporaryDirectory(prefix='sl-statistics-') as directory:
        start, cpu = perf_counter(), process_time()
        details = NUMERICAL_TRIALS[name](scale, ExecutionContext(pool=pool), Path(directory))
        elapsed, cpu = perf_counter()-start, process_time()-cpu
        return {'verified': True, 'seconds': elapsed, 'cpu_seconds': cpu, 'scale': scale,
                'peak_rss_bytes': peak_rss(), 'work_estimate_bytes': pool.maximum, **details}


def cancellation(operation, *, minimum=None):
    stop, timestamp = Event(), []

    def request():
        if not stop.is_set():
            timestamp.append(perf_counter())
            stop.set()

    def observe(percent):
        if minimum is not None and percent >= minimum:
            request()

    ctx = ExecutionContext(cancel=stop, progress=observe)
    try:
        operation(ctx, request)
    except OperationCancelled:
        assert len(timestamp) == 1
        return {'discarded': True, 'seconds_after_request': perf_counter()-timestamp[0]}
    raise AssertionError('El resultado se entregó después de solicitar cancelación.')


def cancel_and_recover():
    numbers = cancellation(lambda ctx, _: kalman_trial(8192,ctx), minimum=20)
    with TemporaryDirectory(prefix='sl-statistics-atomic-') as directory:
        folder = Path(directory)
        spec = campaign_spec(1)
        target = folder/'campaign'
        campaign = cancellation(lambda ctx, _: run_campaign(spec,target,ctx), minimum=50)
        prefix = load_campaign(target).replicas
        assert len(prefix) == 64
        resumed = run_campaign(spec,target)
        assert resumed.replicas[:len(prefix)] == prefix
        assert resumed.replicas == run_campaign(spec,folder/'reference').replicas
        batch = next(target.glob('batch-*.json'))
        record = json.loads(batch.read_text(encoding='utf-8'))
        write_json(batch, {**record, 'sha256': '0'*64})
        np.testing.assert_raises_regex(ValueError, 'huella|integridad', load_campaign, target)

        previous = Project()
        key = previous.add(Signal([1,2,3]))
        target = folder/'session.slproj'
        workspace = session.empty_workspace()
        session.save(target,previous,workspace)
        old = target.read_bytes()
        changed = Project()
        replacement = changed.add(Signal(np.ones(2**18)))

        def stop_save(ctx, request):
            def before_commit():
                request()
                ctx.checkpoint()

            session.save(target,changed,workspace,before_commit=before_commit,checkpoint=ctx.checkpoint)

        persistence = cancellation(stop_save)
        saved, _ = session.load(target)
        assert old == target.read_bytes() and np.array_equal(saved.get(key).values,[1,2,3])
        assert not list(folder.glob('session.slproj.*.tmp'))
        session.save(target,changed,workspace)
        assert session.load(target)[0].get(replacement).values.size == 2**18
        pool = ResourcePool(420_000)
        ctx = ExecutionContext(pool=pool)
        dist = Distribution('normal', {'mean': 0.,'std': 1.})
        admitted, release = Event(), Event()

        def first_progress(_):
            if not admitted.is_set():
                admitted.set()
                if not release.wait(20):
                    raise TimeoutError('No se recibió la solicitud concurrente de recursos.')

        with ThreadPoolExecutor(max_workers=1) as executor:
            active = executor.submit(run_campaign,spec,folder/'concurrent',
                                     ExecutionContext(pool=pool,progress=first_progress))
            try:
                assert admitted.wait(20)
                np.testing.assert_raises(ResourceLimitError, generate_realizations, dist,1024,707,execution=ctx)
            finally:
                release.set()
            assert len(active.result().replicas) == spec.replicas
        records = generate_realizations(dist,1024,707,execution=ctx)
        assert len(records) == 1 and records[0].values.size == 1024
    return {'cancellation': {'numeric': numbers, 'campaign': campaign, 'persistence': persistence},
            'persistence': {'previous_file_preserved': True, 'campaign_resumed': True,
                            'corruption_rejected': True, 'competing_request_rejected': True, 'retry_verified': True}}


def desktop_trial():
    from PySide6.QtCore import QDeadlineTimer, QSettings, QTimer, Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QMessageBox
    from signallab_pc.workbench import WorkbenchWindow
    from signallab_pc.workspaces import ROUTES

    app = QApplication.instance() or QApplication([])
    route = ROUTES['statistical_experiment','campaign']
    replicas, samples = 512, 8192
    with TemporaryDirectory(prefix='sl-statistics-desktop-') as directory:
        settings = QSettings(str(Path(directory)/'settings.ini'), QSettings.Format.IniFormat)
        with (patch('signallab_pc.workbench.desktop_settings', return_value=settings),
              patch('signallab_pc.update_ui.installed', return_value=None),
              patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Discard),
              patch.object(QMessageBox,'warning') as warning,
              patch('signallab_pc.runtime_diagnostics.report_error') as error):
            window = WorkbenchWindow(recovery_directory=directory)
            window.resize(940,700)
            window.show()
            window.open_tool(route)
            panel = window.pages[route].panel
            panel.directory.setText(str(Path(directory)/'campaign'))
            panel.samples.setText(str(samples))
            panel.replicas.setText(str(replicas))
            panel.seed.setText('708')
            app.processEvents()
            ticks = []
            timer = QTimer()
            timer.setTimerType(Qt.TimerType.PreciseTimer)
            timer.setInterval(10)
            timer.timeout.connect(lambda: ticks.append(perf_counter()))
            start = perf_counter()
            timer.start()
            window.calculate_active()
            deadline = QDeadlineTimer(45_000)
            while window._workers and not deadline.hasExpired():
                QTest.qWait(5)
            end = perf_counter()
            timer.stop()
            assert not (window._workers or warning.called or error.called) and panel.campaign is not None
            assert len(panel.campaign.replicas) == replicas and len(ticks)>1
            gaps = [b-a for a,b in zip([start,*ticks],[*ticks,end],strict=True)]
            window.close()
    return {'qt_platform': app.platformName(), 'window': [940,700], 'replicas': replicas, 'samples': samples,
            'heartbeat_period_ms': 10, 'heartbeat_count': len(ticks), 'median_gap_seconds': median(gaps),
            'maximum_gap_seconds': max(gaps), 'seconds': end-start, 'peak_rss_bytes': peak_rss(), 'passed': True}


def main():
    if not __debug__:
        raise RuntimeError('La medición requiere comprobaciones activas. Quitá la optimización de Python.')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--trial', choices=(*RESOURCE_PROFILES,'cancellation','desktop'))
    parser.add_argument('--scale', type=int, choices=(1,2), default=1)
    args = parser.parse_args()
    if args.trial:
        if args.trial == 'cancellation':
            result = cancel_and_recover()
        elif args.trial == 'desktop':
            result = desktop_trial()
        else:
            result = numeric_profile(args.trial,args.scale)
        write_json(args.output,result)
        return

    def git(*command):
        return subprocess.check_output(['git',*command], cwd=ROOT,text=True).strip()

    commit = git('rev-parse','HEAD')
    if git('status','--porcelain'):
        raise ValueError('La medición requiere un candidato limpio.')
    env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
               BLIS_NUM_THREADS='1', QT_QPA_PLATFORM='offscreen')
    with TemporaryDirectory(prefix='sl-statistics-measure-') as directory:
        def trial(name, scale=1):
            target = Path(directory)/f'{name}-{scale}.json'
            subprocess.run([sys.executable,'-B','-X','utf8',str(Path(__file__).resolve()),
                            '--trial',name,'--scale',str(scale),'--output',str(target)],
                           cwd=ROOT,env=env,check=True,timeout=110)
            print(f'Measured statistical profile {name} at scale {scale}', flush=True)
            return json.loads(target.read_text(encoding='utf-8'))

        profiles = [{'profile': name, **trial(name,2), 'reference_scale': trial(name)} for name in RESOURCE_PROFILES]
        recovery, desktop = trial('cancellation'), trial('desktop')
    if git('status','--porcelain') or git('rev-parse','HEAD') != commit:
        raise ValueError('La revisión cambió durante la medición.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, {'schema': 1,'phase': '05','commit': commit,'clean_checkout': True,
                            'platform': platform.platform(),'python': platform.python_version(),'threads': 1,
                            'numpy': np.__version__, 'scipy': scipy.__version__,
                            'cancellation_scope': 'cooperative checkpoints and before atomic replacement',
                            'profiles': profiles,'desktop': desktop, **recovery})


if __name__ == '__main__':
    main()
