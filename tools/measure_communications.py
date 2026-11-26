"""Measure the communications candidate in fresh numerical and desktop processes."""

import argparse
import json
import os
from pathlib import Path
import platform
from statistics import median
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Event, Timer
from time import perf_counter
from unittest.mock import patch

from check_resource_limits import ROOT, peak_rss


PROFILES = (128, 2048, 65536)


def _save(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def _measure(operation, label, times):
    start = perf_counter()
    result = operation()
    times[label] = perf_counter() - start
    return result


def numerical_trial(count):
    import numpy as np
    from signallab_pc import session
    from signallab_pc.communications_channel import AWGNSpec, add_awgn
    from signallab_pc.communications_data import SymbolClock
    from signallab_pc.communications_experiment import ExperimentSpec, run_experiment
    from signallab_pc.communications_metrics import measure_quality
    from signallab_pc.communications_modulation import decide_symbols, generate_bits, group_bits, modulate
    from signallab_pc.communications_pulses import apply_pulse, design_pulse, upsample_symbols
    from signallab_pc.communications_receiver import SynchronizationSpec, recover_symbols
    from signallab_pc.communications_storage import load_experiment, save_experiment

    spec = ExperimentSpec(bit_count=2*count, seed=20261126)
    constellation, shaping = spec.constellation, spec.pulse
    sps = shaping.samples_per_symbol
    times = {}
    before = peak_rss()
    bits = _measure(lambda: generate_bits(spec.bit_count, spec.seed), 'generate_bits', times)
    labels = _measure(lambda: group_bits(bits, constellation, clock=SymbolClock(spec.symbol_rate_hz)), 'group', times)
    symbols = _measure(lambda: modulate(labels, constellation), 'modulate', times)
    pulse = _measure(lambda: design_pulse(shaping), 'pulse', times)
    train = _measure(lambda: upsample_symbols(symbols, sps), 'upsample', times)
    tx = _measure(lambda: apply_pulse(train, pulse), 'fir_tx', times)
    noise = AWGNSpec('eb_n0', spec.eb_n0_db, spec.seed+1, symbol_energy=pulse.energy, bits_per_symbol=2)
    channel = _measure(lambda: add_awgn(tx, noise), 'awgn', times)
    matched = _measure(lambda: apply_pulse(channel.signal, pulse, matched=True), 'fir_rx', times)
    synchronization = SynchronizationSpec(sample_offset=pulse.taps.size-1)
    rx = _measure(lambda: recover_symbols(matched, count, sps, synchronization, sample_gain=pulse.energy),
                  'recover', times)
    decoded = _measure(lambda: decide_symbols(rx.symbols, constellation), 'decide', times)
    quality = _measure(lambda: measure_quality(labels, decoded, reference=symbols, observation=rx.symbols),
                       'metrics', times)
    if quality.ber.evaluated != 2*count or matched.values.size != (count-1)*sps + 2*pulse.taps.size - 1:
        raise ValueError('El perfil no conservó el soporte o la longitud exacta de los datos.')
    del labels, symbols, train, tx, channel, matched, rx, decoded
    result = _measure(lambda: run_experiment(spec), 'experiment', times)
    with TemporaryDirectory(prefix='slcomms-trial-') as folder:
        path = Path(folder)/'trial.slproj'
        key = _measure(lambda: save_experiment(path, result), 'save_slproj', times)
        project, _ = _measure(lambda: session.load(path), 'load_slproj', times)
        restored = load_experiment(project, key)
        if restored.report['metrics'] != result.report()['metrics']:
            raise ValueError('Las métricas guardadas cambiaron al reabrir.')
        np.testing.assert_array_equal(project.get(restored.records['matched']).values, result.matched.values)
        archive_bytes = path.stat().st_size
    return {
        'symbols': count, 'sps': sps, 'taps': pulse.taps.size, 'seconds': times,
        'peak_before_bytes': before, 'peak_rss_bytes': peak_rss(), 'archive_bytes': archive_bytes,
        'matched_samples': result.matched.values.size, 'estimated_work_bytes': result.estimated_work_bytes,
        'archive_verified': True,
    }


def _cancellation(operation, ctx, event, signalled, minimum):
    from signallab_pc.jobs import OperationCancelled
    try:
        operation(ctx)
    except OperationCancelled:
        if not event.is_set() or not signalled:
            raise ValueError('La cancelación se produjo fuera del punto de medición.')
        return {'method': minimum, 'seconds_after_request': perf_counter()-signalled[0], 'discarded': True}
    raise ValueError('El perfil terminó sin observar la solicitud de cancelación.')


def cancel_and_campaign():
    import numpy as np
    from signallab_pc.communications_channel import AWGNSpec, add_awgn
    from signallab_pc.communications_data import SymbolClock, iq_signal
    from signallab_pc.communications_experiment import ExperimentSpec, run_experiment
    from signallab_pc.communications_pulses import PulseSpec, apply_pulse, design_pulse
    from signallab_pc.communications_storage import save_experiment
    from signallab_pc.communications_sweep import SweepAxis, SweepSpec, load_sweep, run_sweep
    from signallab_pc.execution import ExecutionContext
    from signallab_pc.filters import Transfer

    source = iq_signal(np.ones(480_000), SymbolClock(12_000, 8))
    pulse = design_pulse(PulseSpec('rrc', 8, 34))
    event = Event()
    signalled = []

    def request():
        signalled.append(perf_counter())
        event.set()

    timer = Timer(.002, request)
    original = Transfer.apply

    def observed(model, waveform, *args, **kwargs):
        timer.start()
        return original(model, waveform, *args, **kwargs)

    try:
        with patch.object(Transfer, 'apply', observed):
            fir = _cancellation(lambda ctx: apply_pulse(source, pulse, execution=ctx),
                                ExecutionContext(cancel=event), event, signalled, 'timer_from_fir_entry')
    finally:
        timer.cancel()
        if timer.ident is not None:
            timer.join()

    def reset():
        event.clear()
        signalled.clear()

    reset()

    def noise_progress(value):
        if value >= 35 and not event.is_set():
            request()

    awgn = _cancellation(lambda ctx: add_awgn(source, AWGNSpec('snr', 10, 11), ctx),
                         ExecutionContext(cancel=event, progress=noise_progress), event, signalled, 'noise_block')
    reset()
    with TemporaryDirectory(prefix='slcomms-campaign-') as directory:
        folder = Path(directory)
        path = folder/'cancelled.slproj'
        result = run_experiment(ExperimentSpec(bit_count=4096))
        from signallab_pc import project_archive
        original_save = project_archive.save

        def cancel_archive(destination, project, workspace, *, before_commit=None, checkpoint=None):
            def stop():
                request()
                before_commit()
            return original_save(destination, project, workspace, before_commit=stop, checkpoint=checkpoint)

        with patch.object(project_archive, 'save', cancel_archive):
            storage = _cancellation(lambda ctx: save_experiment(path, result, ctx), ExecutionContext(cancel=event),
                                    event, signalled, 'before_archive_commit')
        if path.exists():
            raise ValueError('La escritura cancelada dejó un archivo visible.')
        spec = SweepSpec(ExperimentSpec(bit_count=4096, seed=660),
                         (SweepAxis('eb_n0_db', (0, 2, 4, 6)), SweepAxis('rolloff', (.2, .35))))
        times = {}
        campaign = folder/'sweep'
        run = _measure(lambda: run_sweep(spec, campaign), 'execute', times)
        verified = _measure(lambda: load_sweep(campaign), 'reopen', times)
        if verified != run or not run.complete:
            raise ValueError('El perfil de campaña no conservó sus corridas.')
        size = sum(path.stat().st_size for path in campaign.glob('*.slproj'))
    return {'cancellation': {'fir': fir, 'awgn': awgn, 'persistence': storage},
            'sweep': {'runs': len(run.runs), 'seconds': times, 'archive_bytes': size, 'verified': True}}


def desktop_trial():
    from PySide6.QtCore import QDeadlineTimer, QSettings, QTimer, Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QMessageBox
    from signallab_pc.workbench import WorkbenchWindow
    from signallab_pc.workspaces import ROUTES

    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory(prefix='slcomms-desktop-') as directory:
        settings = QSettings(str(Path(directory)/'settings.ini'), QSettings.Format.IniFormat)
        with (patch('signallab_pc.workbench.desktop_settings', return_value=settings),
              patch('signallab_pc.update_ui.installed', return_value=None),
              patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Discard),
              patch.object(QMessageBox, 'warning') as warning,
              patch('signallab_pc.runtime_diagnostics.report_error') as error):
            window = WorkbenchWindow(recovery_directory=directory)
            window.resize(940, 700)
            window.show()
            route = ROUTES['communications', 'link']
            window.open_tool(route)
            panel = window.pages[route].panel
            panel.fields['bit_count'].setText(str(2*PROFILES[-1]))
            app.processEvents()
            times = []
            timer = QTimer()
            timer.setTimerType(Qt.TimerType.PreciseTimer)
            timer.setInterval(10)
            timer.timeout.connect(lambda: times.append(perf_counter()))
            start = perf_counter()
            timer.start()
            window.calculate_active()
            deadline = QDeadlineTimer(45_000)
            while window._workers and not deadline.hasExpired():
                QTest.qWait(5)
            elapsed = perf_counter()-start
            timer.stop()
            if window._workers or warning.called or error.called or panel.artifact is None or len(times) < 2:
                raise ValueError('El perfil de escritorio no terminó o no registró pulsos de eventos.')
            ticks = [b-a for a,b in zip([start, *times], [*times, start+elapsed], strict=True)]
            window.close()
    return {'qt_platform': app.platformName(), 'window': [940, 700], 'bit_count': 2*PROFILES[-1],
            'heartbeat_period_ms': 10, 'heartbeat_count': len(times), 'median_gap_seconds': median(ticks),
            'maximum_gap_seconds': max(ticks), 'seconds': elapsed, 'peak_rss_bytes': peak_rss(), 'passed': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--trial', choices=tuple(map(str, PROFILES))+('cancel-sweep','desktop'))
    args = parser.parse_args()
    if args.trial is not None:
        value = (desktop_trial() if args.trial == 'desktop' else cancel_and_campaign()
                 if args.trial == 'cancel-sweep' else numerical_trial(int(args.trial)))
        _save(args.output, value)
        return
    import numpy as np
    import scipy

    def git(*cmd):
        return subprocess.check_output(['git', *cmd], cwd=ROOT, text=True).strip()

    commit = git('rev-parse', 'HEAD')
    if git('status', '--porcelain'):
        raise ValueError('La medición requiere un candidato limpio.')
    env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', QT_QPA_PLATFORM='offscreen')
    reports = {}
    with TemporaryDirectory(prefix='slcomms-measure-') as directory:
        for trial in (*map(str, PROFILES), 'cancel-sweep', 'desktop'):
            target = Path(directory)/f'{trial}.json'
            subprocess.run([sys.executable, '-B', '-X', 'utf8', str(Path(__file__).resolve()),
                            '--trial', trial, '--output', str(target)], cwd=ROOT, env=env, check=True, timeout=110)
            reports[trial] = json.loads(target.read_text(encoding='utf-8'))
            print('Measured communications profile', trial, flush=True)
    if git('status', '--porcelain') or git('rev-parse', 'HEAD') != commit:
        raise ValueError('La revisión cambió durante la medición.')
    _save(args.output, {'commit': commit, 'clean_checkout': True, 'platform': platform.platform(),
                        'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__,
                        'threads': 1, 'profiles': [reports[str(count)] for count in PROFILES],
                        **reports['cancel-sweep'], 'desktop': reports['desktop']})


if __name__ == '__main__':
    main()
