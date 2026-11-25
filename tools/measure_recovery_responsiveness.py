"""Measure the Qt event loop during original JSON save and current recovery."""

import argparse
import json
from pathlib import Path
import platform
from statistics import median, quantiles
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import perf_counter
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
from PySide6.QtCore import QEventLoop, QSettings, QStandardPaths, QTimer, Qt
from PySide6.QtWidgets import QApplication

from measure_core_hardening import peak_rss
from signallab_pc import session
from signallab_pc.atomic_file import write_json
from signallab_pc.model import Signal
from signallab_pc.session_desktop import capture
from signallab_pc.workbench import WorkbenchWindow


def measure(window, profile, samples, attempt, mode):
    old, workspace = profile/'legacy.json', capture(window)
    loop = QEventLoop()
    heartbeat = QTimer()
    heartbeat.setTimerType(Qt.TimerType.PreciseTimer)
    heartbeat.setInterval(10)
    beats, elapsed = [], []
    started = None
    heartbeat.timeout.connect(lambda: beats.append(perf_counter()))

    def done():
        elapsed.append(perf_counter() - started)
        QTimer.singleShot(120, loop.quit)

    def start():
        nonlocal started
        started = perf_counter()
        if mode == 'sync_json':
            session.save(old, window.project, workspace)
            done()
        else:
            window.sessions.autosave()
            observe.start()

    def complete():
        if window.sessions.writing is None:
            observe.stop()
            done()

    observe = QTimer()
    observe.setInterval(10)
    observe.timeout.connect(complete)
    watchdog = QTimer()
    watchdog.setSingleShot(True)
    watchdog.timeout.connect(loop.quit)
    watchdog.start(60000)
    heartbeat.start()
    QTimer.singleShot(120, start)
    loop.exec()
    heartbeat.stop()
    watchdog.stop()
    if not elapsed:
        raise TimeoutError('El banco de recuperación no terminó.')
    path = old if mode == 'sync_json' else window.sessions.path
    project, _ = session.load(path)
    assert [row['id'] for row in project.headers()] == [row['id'] for row in window.project.headers()]
    gaps = [1000*(last-first) for first,last in zip(beats, beats[1:])]
    return {'mode': mode, 'attempt': attempt, 'samples_per_record': samples, 'seconds': elapsed[0],
            'max_gap_ms': max(gaps), 'p95_gap_ms': quantiles(gaps, n=20)[-1] if len(gaps) >= 20 else None,
            'heartbeat_count': len(beats), 'file_bytes': path.stat().st_size, 'process_peak_bytes': peak_rss()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    sha = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
    clean = not subprocess.check_output(['git','status','--porcelain'], cwd=ROOT, text=True).strip()
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    with TemporaryDirectory(prefix='signallab-recovery-bench-') as directory:
        profile = Path(directory)
        settings = QSettings(str(profile/'settings.ini'), QSettings.Format.IniFormat)
        writable = QStandardPaths.writableLocation
        layout = QStandardPaths.StandardLocation

        def isolated(location):
            return str(profile/location.name) if location in (layout.GenericCacheLocation, layout.GenericDataLocation) else writable(location)

        rows = []
        with patch('signallab_pc.workbench.desktop_settings', return_value=settings), \
                patch('signallab_pc.update_ui.installed', return_value=None), \
                patch.object(QStandardPaths, 'writableLocation', side_effect=isolated):
            window = WorkbenchWindow(recovery_directory=profile/'recovery')
            window.show()
            samples = 262144
            values = np.random.default_rng(20261125).normal(size=samples)
            window.publish(Signal(values, origin=-9), operation='Banco')
            window.publish(Signal(values[::-1] + 1j), operation='Banco')
            for attempt in range(1, 4):
                for mode in ('sync_json', 'archive_worker'):
                    window.sessions.checkpoint = None
                    rows.append(measure(window, profile, samples, attempt, mode))
            window.project.dirty = False
            window.sessions.saved = capture(window)
            window.close()
        app.processEvents()
    report = {'commit': sha, 'clean_checkout': clean, 'os': platform.platform(),
              'qt_platform': app.platformName(), 'heartbeat_interval_ms': 10, 'trials': rows,
              'summary': {mode: {'median_seconds': median(row['seconds'] for row in rows if row['mode'] == mode),
                                 'max_gap_ms': max(row['max_gap_ms'] for row in rows if row['mode'] == mode)}
                          for mode in ('sync_json', 'archive_worker')}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, report)
    print(json.dumps(report['summary']))


if __name__ == '__main__':
    main()
