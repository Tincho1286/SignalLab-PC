from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from signallab_pc import session
from signallab_pc.__main__ import main
from signallab_pc.communications_experiment import ExperimentSpec, run_experiment
from signallab_pc.communications_storage import decode_bits, decode_symbols, load_experiment
from signallab_pc.model import Signal
from signallab_pc.scientific_storage import save_binary_signal


class CommunicationsCLITests(unittest.TestCase):
    def invoke(self, command, *args, expected=0):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = main(['communications', command, *map(str, args)])
        self.assertEqual(status, expected, stderr.getvalue())
        if status:
            return stderr.getvalue()
        return json.loads(stdout.getvalue())

    def test_link_uses_same_python_service_without_qt(self):
        with TemporaryDirectory() as folder:
            path = Path(folder)/'link.slproj'
            script = '''import builtins, sys
original = builtins.__import__
def guard(name, *args, **kwargs):
    if name.partition(".")[0] in {"PySide6", "shiboken6", "PyQt6"}:
        raise AssertionError(name)
    return original(name, *args, **kwargs)
builtins.__import__ = guard
from signallab_pc.__main__ import main
raise SystemExit(main())
'''
            args = ['communications', 'link', '--bits', '83', '--seed', '15', '--no-noise', '--output', str(path)]
            run = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-c', script, *args],
                                 capture_output=True, text=True, encoding='utf-8', timeout=20)
            self.assertEqual(run.returncode, 0, run.stderr)
            receipt = json.loads(run.stdout)
            project, _ = session.load(path)
            restored = load_experiment(project, receipt['record'])
            python = run_experiment(ExperimentSpec(bit_count=83, seed=15, eb_n0_db=None))
            self.assertEqual(restored.specification, python.specification)
            self.assertEqual(restored.report['metrics'], python.report()['metrics'])
            for name, value in python.signals().items():
                np.testing.assert_array_equal(project.get(restored.records[name]).values, value.values)
            fail = self.invoke('link', '--order', 3, '--output', Path(folder)/'invalid.slproj', expected=1)
            self.assertIn('potencia de dos', fail)
            self.assertFalse((Path(folder)/'invalid.slproj').exists())

    def test_independent_operations_exchange_records(self):
        with TemporaryDirectory() as folder:
            path = Path(folder)/'flow.slproj'
            source = self.invoke('modulate', '--family', 'qam', '--order', 16, '--manual-bits', '0111 0010 1101',
                                 '--output', path)
            self.assertEqual(source['symbols'], 3)
            self.assertEqual(source['padding_bits'], 0)
            labels_id = source['labels_record']
            project, _ = session.load(path)
            np.testing.assert_array_equal(decode_bits(project.get(source['bits_record'])).values,
                                          [0, 1, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1])
            tx = self.invoke('shape', '--session', path, '--record', source['record'], '--interpolate', '--pulse',
                             'rectangular', '--sps', 4, '--output', path)
            rx = self.invoke('shape', '--session', path, '--record', tx['record'], '--pulse', 'rectangular',
                             '--sps', 4, '--matched', '--output', path)
            observed = self.invoke('receive', '--session', path, '--record', rx['record'], '--symbols', 3,
                                   '--sps', 4, '--offset', 3, '--output', path)
            received = self.invoke('decide', '--session', path, '--record', observed['record'], '--family', 'qam',
                                   '--order', 16, '--output', path)
            report = self.invoke('measure', '--session', path, '--transmitted', labels_id, '--received',
                                 received['record'], '--reference-record', source['record'], '--observation-record',
                                 observed['record'], '--output', path)
            self.assertEqual(report['metrics']['ber']['errors'], 0)
            self.assertEqual(report['metrics']['ser']['errors'], 0)
            self.assertLess(report['metrics']['evm']['rms'] or 0, 1e-14)
            project, _ = session.load(path)
            self.assertEqual(decode_symbols(project.get(received['record'])).valid_bits, 12)
            self.assertEqual(project.get(observed['record']).metadata['sample_rate_hz'], 12_000)

    def test_pulse_awgn_and_coherent_statistics_export(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            response = self.invoke('pulse', '--pulse', 'rrc', '--sps', 4, '--span', 5, '--output', root/'pulse.json')
            self.assertEqual(response['tap_count'], 21)
            self.assertEqual(response['group_delay_samples'], 10)
            self.assertAlmostEqual(response['energy'], 1.0)
            path = root/'input.slbin'
            save_binary_signal(Signal([1, -1, 1, -1], origin=-2), path)
            output = root/'channel.slproj'
            noise = self.invoke('awgn', '--signal', path, '--db', 10, '--domain', 'real', '--output', output)
            self.assertAlmostEqual(noise['statistics']['nominal_variance_i'], 0.1)
            self.assertEqual(noise['statistics']['nominal_variance_q'], 0)
            project, _ = session.load(output)
            self.assertEqual(project.get(noise['record']).origin, -2)
            unavailable = self.invoke('receive', '--session', output, '--record', noise['record'], '--symbols', 16,
                                      '--sps', 2, '--output', output)
            self.assertIsNone(unavailable['record'])
            self.assertEqual(unavailable['synchronization']['state'], 'unavailable')
            monte = root/'monte.json'
            result = self.invoke('monte-carlo', '--symbols', 2048, '--eb-n0', 3, '--output', monte)
            self.assertEqual(result['stopping_rule'], 'fixed_symbol_count')
            self.assertEqual(result, json.loads(monte.read_text(encoding='utf-8')))

    def test_multipath_saves_the_clock_and_leaves_existing_session_on_failure(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            path, output = root/'input.slbin', root/'channel.slproj'
            source = Signal([1+2j, 3-1j], origin=-1, metadata={'sample_rate_hz': 2000, 'time_start_s': 0.2})
            save_binary_signal(source, path)
            result = self.invoke('multipath', '--signal', path, '--path=0=1', '--path=2=-i/2', '--output', output)
            project, _ = session.load(output)
            restored = project.get(result['record'])
            np.testing.assert_array_equal(restored.values, [1+2j, 3-1j, 1-0.5j, -0.5-1.5j])
            self.assertEqual(result['sample_count'], 4)
            self.assertEqual(restored.origin, -1)
            self.assertEqual(restored.metadata['time_start_s'], 0.2)
            self.assertEqual(restored.metadata['communications_multipath'], result['channel'])
            original = output.read_bytes()
            failure = self.invoke('multipath', '--session', output, '--record', result['record'],
                                  '--path=0=z', '--output', output, expected=1)
            self.assertIn('constante', failure)
            self.assertEqual(output.read_bytes(), original)
            result = self.invoke('multipath', '--signal', path, '--path=0=2', '--path=2=-i',
                                 '--normalize-power', '--samples-per-symbol', 2, '--frequency-points', 16,
                                 '--output', output)
            self.assertAlmostEqual(result['analysis']['total_power'], 1)
            self.assertAlmostEqual(result['analysis']['symbol_spaced_isi']['interference_to_reference_power'], 0.25)
            project, _ = session.load(output)
            self.assertEqual(project.get(result['analysis_record']), result['analysis'])
            response = project.get(result['frequency_record'])
            self.assertEqual(response.units, 'rad/muestra')
            np.testing.assert_allclose(response.values, (2-1j*np.exp(-2j*response.axis))/np.sqrt(5))

    def test_fading_stores_its_realizations_in_the_session(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            source, output = root/'input.slbin', root/'fading.slproj'
            save_binary_signal(Signal(np.ones(20), origin=4, metadata={'sample_rate_hz': 8000}), source)
            stats = self.invoke('fading', '--signal', source, '--path=0=2', '--path=3=1,6,pi/4', '--k-scale',
                                'db', '--seed', 73, '--output', output)
            project, _ = session.load(output)
            direct, echo = [project.get(path['record']) for path in stats['paths']]
            received = project.get(stats['record'])
            np.testing.assert_array_equal(received.values, np.pad(direct.values, (0, 3)) + np.pad(echo.values, (3, 0)))
            self.assertEqual(echo.origin, 7)
            self.assertEqual(received.metadata['sample_rate_hz'], 8000)
            self.assertEqual(received.metadata['communications_fading']['specification']['seed'], 73)

    def test_doppler_cli_persists_psd_and_signed_phase_rotation(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            source, output = root/'input.slbin', root/'doppler.slproj'
            save_binary_signal(Signal(np.ones(512), origin=-3, metadata={'sample_rate_hz': 4096}), source)
            fading = self.invoke('fading', '--signal', source, '--path=0=1', '--doppler-max-hz', 64,
                                 '--diagnostics', '--seed', 43, '--output', output)
            project, _ = session.load(output)
            path, = fading['paths']
            self.assertGreater(path['coherence_seconds'], 0)
            psd = project.get(path['doppler_records']['theoretical_psd'])
            self.assertEqual(psd.units, 'Hz')
            self.assertEqual(psd.data_kind, 'density')
            self.assertAlmostEqual(float(sum(psd.values.real)*psd.step), 1)
            shifted = self.invoke('shift-carrier', '--signal', source, '--frequency-hz', -512,
                                  '--phase-rad', 0.25, '--output', output)
            project, _ = session.load(output)
            result = project.get(shifted['record'])
            np.testing.assert_allclose(result.values, np.exp(1j*(0.25-np.pi/4*np.arange(512))), atol=1e-13)
            self.assertEqual(result.origin, -3)

    def test_sweep_cli_runs_and_verifies_a_reproducible_grid(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            output = root/'experiment'
            result = self.invoke('sweep', '--axis', 'eb_n0_db=2,6', '--axis', 'span_symbols=4,8',
                                 '--bits', 96, '--output', output)
            self.assertEqual((result['completed'], result['planned'], result['complete']), (4, 4, True))
            csv_path = root/'results.csv'
            inspected = self.invoke('sweep', '--inspect', '--output', output, '--csv', csv_path)
            self.assertEqual(result, inspected)
            self.assertIn('span_symbols', csv_path.read_text(encoding='utf-8'))
            invalid = self.invoke('sweep', '--axis', 'sps:2,4', '--output', root/'invalid', expected=1)
            self.assertIn('parámetro=valor1,valor2', invalid)


if __name__ == '__main__':
    unittest.main()
