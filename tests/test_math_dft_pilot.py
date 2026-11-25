"""Analytic, headless and transactional references for the DFT pilot."""

from cmath import exp
import json
from math import tau
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Event
from time import monotonic
import unittest
from unittest.mock import patch

from numpy.testing import assert_allclose

from signallab_pc import session
from signallab_pc.dft_application import DFTExecution, DFTRequest, calculate_dft, store_dft
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.operations import idft
from signallab_pc.project import Project
from signallab_pc.resources import ResourceLimitError
from signallab_pc.storage import save_json


FIXTURES = Path(__file__).with_name('fixtures')
HEADLESS_ENTRY = """
import importlib.abc, runpy, sys
class RejectQt(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.split('.')[0] in {'PySide6', 'shiboken6', 'PyQt5', 'PyQt6', 'qtpy'}:
            raise AssertionError('Headless path attempted to import ' + name)
sys.meta_path.insert(0, RejectQt())
runpy.run_module('signallab_pc', run_name='__main__', alter_sys=True)
"""


def direct_sum(source, length, centered, phase_reference):
    first = -(length // 2) if centered else 0
    origin = source.origin if phase_reference == 'sample_indices' else 0
    return [sum(sample * exp(-1j * tau * ((k * (origin + offset)) % length) / length)
                for offset, sample in enumerate(source.values[:length]))
            for k in range(first, first + length)]


def cli(*args):
    return subprocess.run([sys.executable, '-B', '-X', 'utf8', '-c', HEADLESS_ENTRY, *map(str,args)],
                          text=True, encoding='utf-8', capture_output=True, timeout=30)


class DFTPilotTests(unittest.TestCase):
    def test_oracle_and_inverse_for_odd_even_padded_truncated_and_signed_origins(self):
        for origin in (-5, 2**62 + 9):
            signal = Signal([2+3j, -1j, .25, -3], origin, units='índice',
                            metadata={'sample_rate_hz': 8., 'time_start_s': -.125})
            for length, centered in ((3, True), (5, False), (6, True), (4, False)):
                for reference in ('sample_indices', 'record_offset'):
                    with self.subTest(origin=origin, length=length, centered=centered, reference=reference):
                        result = calculate_dft(DFTRequest(signal, length, centered, reference))
                        assert_allclose(result.spectrum.values, direct_sum(signal, length, centered, reference), atol=1e-13)
                        self.assertEqual(result.spectrum.units, 'rad/muestra' if centered else 'bin k')
                        self.assertEqual(result.provenance.input_units, 'índice')
                        self.assertEqual(result.estimated_work_bytes, 128 * length)
                        restored = idft(result.spectrum, restore_origin=True)
                        expected = [*signal.values[:length], *([0] * max(0, length-len(signal.values)))]
                        assert_allclose(restored.values, expected, atol=1e-13)
                        self.assertEqual(restored.origin, origin)
                        self.assertEqual(restored.metadata['time_start_s'], -.125)
                        self.assertEqual(restored.metadata['sample_rate_hz'], 8.)

    def test_headless_cli_signal_matches_api_and_preserves_lineage(self):
        with TemporaryDirectory() as folder:
            source_path, output = (Path(folder)/name for name in ('signal.json', 'session.json'))
            source = Signal([1+2j, -3, .5j], -2, metadata={'sample_rate_hz': 4, 'time_start_s': -.375})
            save_json(source, source_path)
            completed = cli('dft', '--signal', source_path, '--output', output, '--length', 6, '--order', 'bins')
            self.assertEqual(completed.returncode, 0, completed.stderr)
            receipt = json.loads(completed.stdout)
            project, workspace = session.load(output)
            signal_id, spectrum_id = receipt['source_id'], receipt['result_id']
            self.assertEqual([record['id'] for record in project.headers()], [signal_id, spectrum_id])
            self.assertEqual(project.headers()[-1]['parents'], [signal_id])
            self.assertEqual(workspace, session.empty_workspace())
            spectrum = project.get(spectrum_id)
            expected = calculate_dft(DFTRequest(source, 6, False)).spectrum
            assert_allclose(spectrum.values, expected.values, atol=1e-14)
            assert_allclose(spectrum.values, direct_sum(source, 6, False, 'sample_indices'), atol=1e-13)
            self.assertEqual(spectrum.metadata, expected.metadata)

    def test_cli_appends_to_historical_sessions_and_keeps_existing_spectra(self):
        names = ('session-v1-draft-1.9.3.json', 'session-v2-draft-1.9.4.json', 'session-v3-dft-2.0.0.json')
        with TemporaryDirectory() as folder:
            for name in names:
                with self.subTest(name=name):
                    fixture = FIXTURES/name
                    project, workspace = session.load(fixture)
                    source, old_spectrum = project.headers('signal')
                    output = Path(folder)/name
                    completed = cli('dft', '--session', fixture, '--record', source['id'],
                                    '--output', output, '--phase-reference', 'record_offset')
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    recovered, controls = session.load(output)
                    self.assertEqual(controls, workspace)
                    self.assertEqual(recovered.records()[:-1], project.records())
                    self.assertEqual(recovered.headers()[-1]['parents'], [source['id']])
                    for key in (old_spectrum['id'], recovered.headers()[-1]['id']):
                        restored = idft(recovered.get(key), restore_origin=True)
                        signal = project.get(source['id'])
                        assert_allclose(restored.values, signal.values, atol=1e-13)
                        self.assertEqual(restored.origin, signal.origin)
                        self.assertEqual(restored.metadata['sample_rate_hz'], signal.metadata['sample_rate_hz'])

    def test_budget_timeout_and_cancellation_are_checked_before_and_after_native_work(self):
        request = DFTRequest(Signal([1, 2]), 4)
        with patch('signallab_pc.operations.dft') as engine:
            with self.assertRaises(ResourceLimitError):
                calculate_dft(request, DFTExecution(max_work_bytes=511))
            with self.assertRaises(TimeoutError):
                calculate_dft(request, DFTExecution(deadline=monotonic()-1))
            engine.assert_not_called()
        self.assertEqual(calculate_dft(request, DFTExecution(max_work_bytes=512)).estimated_work_bytes, 512)
        cancel = Event()
        observed = []
        def progress(percent):
            observed.append(percent)
            if percent == 100:
                cancel.set()
        with self.assertRaises(OperationCancelled):
            calculate_dft(request, DFTExecution(cancel=cancel, progress=progress))
        self.assertEqual(observed, [0, 100])

    def test_cancel_before_project_commit_and_file_replace_keeps_existing_data(self):
        source = Signal([1, 2], -1)
        outcome = calculate_dft(DFTRequest(source))
        project = Project()
        project.add(Signal([7]))
        before = project.document()
        cancel = Event()
        add = Project.add
        def staged_add(pending, value, **kwargs):
            key = add(pending, value, **kwargs)
            if value is outcome.spectrum:
                cancel.set()
            return key
        with patch.object(Project, 'add', staged_add), self.assertRaises(OperationCancelled):
            store_dft(project, outcome, source=source, execution=DFTExecution(cancel=cancel))
        self.assertEqual(project.document(), before)
        with TemporaryDirectory() as folder:
            path = Path(folder)/'session.json'
            session.save(path, project, session.empty_workspace())
            saved = path.read_bytes()
            store_dft(project, outcome, source=source)
            with self.assertRaises(OperationCancelled):
                session.save(path, project, session.empty_workspace(),
                             before_commit=DFTExecution(cancel=cancel).checkpoint)
            self.assertEqual(path.read_bytes(), saved)
            self.assertEqual(list(Path(folder).iterdir()), [path])

    def test_cli_rejected_budget_keeps_destination_bytes(self):
        with TemporaryDirectory() as folder:
            source, output = (Path(folder)/name for name in ('input.json', 'output.json'))
            save_json(Signal([1, 2], -1), source)
            output.write_bytes(b'previous destination')
            failed = cli('dft', '--signal', source, '--output', output, '--max-work-bytes', 255)
            self.assertEqual(failed.returncode, 1, failed.stderr)
            self.assertIn('presupuesto', failed.stderr)
            self.assertEqual(failed.stdout, '')
            self.assertEqual(output.read_bytes(), b'previous destination')
