"""Measure an integrated QPSK/RRC channel with verified storage."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib.abc
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Event
from time import perf_counter
from unittest.mock import patch

from check_resource_limits import ROOT, peak_rss
from measure_communications import PROFILES, _measure, _save, desktop_trial


class BlockQt(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in ('PySide6', 'shiboken6', 'PyQt6', 'qtpy'):
            raise AssertionError(f'Importación Qt en el perfil científico: {fullname}')


def profile_spec(count):
    from signallab_pc.communications_channel import ChannelPath, MultipathSpec
    from signallab_pc.communications_doppler import CarrierShift
    from signallab_pc.communications_experiment import ExperimentSpec
    from signallab_pc.communications_fading import FadingPath, FadingSpec
    from signallab_pc.communications_impairments import IQImbalance, PhaseNoiseSpec
    from signallab_pc.communications_interference import BandInterference, InterferenceSpec
    from signallab_pc.communications_pipeline import ChannelPipelineSpec, ChannelStage

    operations = (
        MultipathSpec((ChannelPath(0, 1), ChannelPath(5, .08, .06), ChannelPath(9, 0, -.04))),
        FadingSpec((FadingPath(0, 1, 8, .2), FadingPath(4, .12)), 2026, 64),
        CarrierShift(19, .06),
        PhaseNoiseSpec(2, 2026),
        IQImbalance(.3, .043, .006, -.002),
        InterferenceSpec(BandInterference(4800, 12000, 2026), sir_db=18),
    )
    chain = ChannelPipelineSpec(tuple(ChannelStage(model) for model in operations), seed=421555)
    return ExperimentSpec(bit_count=2*count, seed=20261126, eb_n0_db=10, channel_pipeline=chain)


def numerical_trial(count):
    import numpy as np
    from signallab_pc import session
    from signallab_pc.communications_experiment import run_experiment
    from signallab_pc.communications_storage import load_experiment, save_experiment
    from signallab_pc.operation_provenance import settings_digest

    spec = profile_spec(count)
    times = {}
    initial_rss = peak_rss()
    result = _measure(lambda: run_experiment(spec), 'compute', times)
    compute_rss = peak_rss()
    if result.metrics is None or result.metrics.ber.evaluated != 2*count or result.pipeline is None:
        raise ValueError('El perfil requiere un enlace completo con la cantidad de bits configurada.')
    with TemporaryDirectory(prefix='sl04-profile-') as directory:
        path = Path(directory)/'channel.slproj'
        identifier = _measure(lambda: save_experiment(path, result), 'save', times)
        save_rss = peak_rss()
        archive_bytes = path.stat().st_size
        project, _ = _measure(lambda: session.load(path), 'load', times)
        restored = _measure(lambda: load_experiment(project, identifier), 'verify', times)
        if restored.specification != spec or settings_digest(restored.report) != result.report_sha256:
            raise ValueError('La configuración o informe cambiaron al reabrir el enlace.')
        actual = project.get(restored.records['channel_output'])
        np.testing.assert_array_equal(actual.values, result.pipeline.signal.values)
        np.testing.assert_array_equal(project.get(restored.records['matched']).values, result.matched.values)
        records = len(project.headers())
    return {
        'symbols': count, 'samples_per_symbol': spec.pulse.samples_per_symbol,
        'sample_rate_hz': result.transmitted.metadata['sample_rate_hz'], 'pulse_taps': result.pulse.taps.size,
        'source_samples': result.transmitted.values.size, 'received_samples': result.matched.values.size,
        'model_stages': len(result.pipeline.stages), 'parameters': spec.document(),
        'baseline_peak_rss_bytes': initial_rss, 'compute_peak_rss_bytes': compute_rss,
        'save_peak_rss_bytes': save_rss, 'peak_rss_bytes': peak_rss(), 'archive_bytes': archive_bytes,
        'verified_records': records, 'archive_verified': True,
        'estimated_link_retention_bytes': result.estimated_work_bytes,
        'retained_channel_bytes': result.pipeline.retained_bytes, 'seconds': times,
    }


def resources_trial(spec):
    from scipy.signal import ZoomFFT
    import numpy as np
    from signallab_pc import session
    from signallab_pc.communications_experiment import run_experiment
    from signallab_pc.communications_storage import save_experiment
    from signallab_pc.execution import ExecutionContext, ResourcePool
    from signallab_pc.jobs import OperationCancelled
    from signallab_pc.model import Signal
    from signallab_pc.project import Project
    from signallab_pc.resources import ResourceLimitError

    def cancel_during(operation, instrument):
        flag, requested = Event(), []
        ctx = ExecutionContext(cancel=flag)

        def request():
            if not flag.is_set():
                requested.append(perf_counter())
                flag.set()

        try:
            with instrument(request):
                operation(ctx)
        except OperationCancelled:
            if requested:
                return {'discarded': True, 'seconds_after_request': perf_counter()-requested[0]}
            raise
        raise ValueError('La operación produjo un resultado después de solicitar la cancelación.')

    transform = ZoomFFT.__call__

    def clarke_instrument(request):
        def measured(self, *args, **kwargs):
            request()
            return transform(self, *args, **kwargs)
        return patch.object(ZoomFFT, '__call__', measured)

    clarke = cancel_during(lambda ctx: run_experiment(spec, execution=ctx), clarke_instrument)
    result = run_experiment(spec)
    archive = session.save
    with TemporaryDirectory(prefix='sl04-checks-') as directory:
        destination = Path(directory)/'channel.slproj'
        previous = Project()
        reference = previous.add(Signal([1, 2, 3]))
        session.save(destination, previous, session.empty_workspace())
        fingerprint = destination.read_bytes()

        def archive_instrument(request):
            def measured(path, project, workspace, *, before_commit, checkpoint):
                def interrupt_delivery():
                    request()
                    before_commit()
                return archive(path, project, workspace, before_commit=interrupt_delivery, checkpoint=checkpoint)
            return patch.object(session, 'save', measured)

        persisted = cancel_during(lambda ctx: save_experiment(destination, result, ctx), archive_instrument)
        try:
            save_experiment(destination, result, ExecutionContext(max_work_bytes=1))
        except ResourceLimitError:
            rejected = destination.read_bytes() == fingerprint and list(Path(directory).iterdir()) == [destination]
        else:
            rejected = False
        restored, _ = session.load(destination)
        np.testing.assert_array_equal(restored.get(reference).values, [1, 2, 3])
        if not rejected:
            raise ValueError('La cancelación o el rechazo dañó el archivo previo o dejó un temporal.')

    # Hold the first calculation at the native transform, while its estimated
    # reservation is active, then try a second calculation against the same pool.
    admitted, advance = Event(), Event()
    estimate = result.estimated_work_bytes - result.pipeline.retained_bytes
    capacity = 350 * 1024**2
    pool = ResourcePool(capacity)

    def pause(self, *args, **kwargs):
        if not admitted.is_set():
            admitted.set()
            if not advance.wait(8):
                raise TimeoutError('El controlador de concurrencia superó el plazo.')
        return transform(self, *args, **kwargs)

    with patch.object(ZoomFFT, '__call__', pause), ThreadPoolExecutor(max_workers=2) as workers:
        ctx = ExecutionContext(pool=pool)
        first = workers.submit(run_experiment, spec, execution=ctx)
        try:
            if not admitted.wait(8):
                raise TimeoutError('El primer cálculo no llegó a la transformada Clarke.')
            try:
                run_experiment(spec, execution=ctx)
            except ResourceLimitError:
                pass
            else:
                raise ValueError('Dos reservas simultáneas superaron la capacidad configurada.')
        finally:
            advance.set()
        completed = first.result(timeout=20)
    retry = run_experiment(spec, execution=ExecutionContext(pool=pool))
    if retry.signal_digests != completed.signal_digests:
        raise ValueError('El rechazo concurrente cambió la reproducibilidad del perfil.')
    return {'cancellation': {'clarke_transform': clarke, 'atomic_archive': persisted},
            'archive_rejected_without_changes': rejected,
            'concurrency': {'budget_bytes': capacity, 'estimate_bytes': estimate,
                            'competing_request_rejected': True, 'retry_verified': True}}



def configure_workbench(panel):
    spec = profile_spec(PROFILES[-1])
    panel.fields['seed'].setText(str(spec.seed))
    panel.fields['eb_n0'].setText(str(spec.eb_n0_db))
    panel.fields['channel_enabled'].setChecked(True)
    panel.fields['pipeline'].set_specification(spec.channel_pipeline)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--trial', choices=tuple(map(str, PROFILES))+('boundaries', 'desktop'))
    args = parser.parse_args()
    if args.trial == 'desktop':
        _save(args.output, desktop_trial(configure=configure_workbench))
        return
    if args.trial is not None:
        sys.meta_path.insert(0, BlockQt())
        value = resources_trial(profile_spec(PROFILES[-1])) if args.trial == 'boundaries' else numerical_trial(int(args.trial))
        _save(args.output, value)
        return
    import numpy as np
    import scipy

    def git(*arguments):
        return subprocess.check_output(['git', *arguments], cwd=ROOT, text=True).strip()

    commit = git('rev-parse', 'HEAD')
    if git('status', '--porcelain'):
        raise ValueError('El perfil requiere un checkout limpio.')
    environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
    reports = {}
    with TemporaryDirectory(prefix='sl04-measure-') as directory:
        for trial in (*map(str, PROFILES), 'boundaries', 'desktop'):
            output = Path(directory)/f'{trial}.json'
            command = [sys.executable, '-B', '-X', 'utf8', str(Path(__file__).resolve()),
                       '--trial', trial, '--output', str(output)]
            subprocess.run(command, cwd=ROOT, env=environment, check=True, timeout=110)
            reports[trial] = json.loads(output.read_text(encoding='utf-8'))
            print(f'Perfil de canal {trial} verificado', flush=True)
    if git('status', '--porcelain') or git('rev-parse', 'HEAD') != commit:
        raise ValueError('La revisión cambió durante la medición.')
    _save(args.output, {'commit': commit, 'clean_checkout': True, 'platform': platform.platform(),
                        'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__,
                        'threads': 1, 'profiles': [reports[str(count)] for count in PROFILES],
                        **reports['boundaries'], 'desktop': reports['desktop']})


if __name__ == '__main__':
    main()
