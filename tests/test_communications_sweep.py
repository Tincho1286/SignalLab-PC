import csv
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Event
import unittest
from unittest.mock import patch

from signallab_pc.communications_experiment import ExperimentSpec, run_experiment
from signallab_pc.communications_pulses import PulseSpec
from signallab_pc.communications_receiver import SynchronizationSpec
from signallab_pc.communications_storage import load_experiment, save_experiment
from signallab_pc.communications_sweep import (
    SweepAxis, SweepSpec, _locked, axis_from_text, export_sweep_csv, load_sweep, load_sweep_run, run_sweep,
)
from signallab_pc.execution import ExecutionContext
from signallab_pc.jobs import OperationCancelled
from signallab_pc.operation_provenance import settings_digest
from signallab_pc.resources import ResourceLimitError


class CommunicationsSweepTests(unittest.TestCase):
    def request(self):
        return SweepSpec(ExperimentSpec(bit_count=72, seed=11, pulse=PulseSpec('rrc', 3, 4)),
                         (SweepAxis('eb_n0_db', (0, 5)), SweepAxis('span_symbols', (4, 7))))

    def test_parameter_grid_seed_order_and_verified_csv(self):
        spec = self.request()
        with TemporaryDirectory() as directory:
            folder = Path(directory)/'study'
            output = run_sweep(spec, folder)
            self.assertTrue(output.complete)
            self.assertEqual(output.planned, 4)
            expected = [{'eb_n0_db': level, 'span_symbols': span} for level in (0, 5) for span in (4, 7)]
            self.assertEqual([row['parameters'] for row in output.runs], expected)
            self.assertEqual(len({row['seed'] for row in output.runs}), 4)
            restored = load_sweep(folder)
            self.assertEqual(restored.runs, output.runs)
            self.assertEqual(restored.specification, spec)
            export = folder/'comparison.csv'
            export_sweep_csv(restored, export)
            with export.open(newline='', encoding='utf-8') as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(float(rows[-1]['eb_n0_db']), 5)
            self.assertEqual(int(rows[0]['span_symbols']), 4)
            self.assertEqual(int(rows[0]['bits']), 72)
            self.assertEqual(rows[0]['ber_reference'], 'exact')
            self.assertAlmostEqual(float(rows[1]['evm_percent']), output.runs[1]['metrics']['evm']['percent'])
            with self.assertRaisesRegex(ValueError, 'distinto'):
                export_sweep_csv(restored, folder/'campaign.json')
            with self.assertRaises(TypeError):
                export_sweep_csv([], folder/'invalid.csv')
            with patch('signallab_pc.communications_sweep.run_experiment') as engine:
                self.assertEqual(run_sweep(spec, folder), restored)
                engine.assert_not_called()

    def test_parallel_axes_hold_common_seed_and_control_modulation_and_clock(self):
        spec = SweepSpec(ExperimentSpec(bit_count=16, seed=21, pulse=PulseSpec('rrc', 2, 3), eb_n0_db=None),
                         (SweepAxis('order', (2, 4)), SweepAxis('symbol_count', (8,)),
                          SweepAxis('samples_per_symbol', (3,)), SweepAxis('rolloff', (.2, .5))), 'common')
        with TemporaryDirectory() as directory:
            run = run_sweep(spec, directory)
            self.assertEqual([row['seed'] for row in run.runs], [21]*4)
            self.assertEqual([row['metrics']['ber']['evaluated'] for row in run.runs], [8, 8, 16, 16])
            export = Path(directory)/'results.csv'
            export_sweep_csv(run, export)
            with export.open(newline='', encoding='utf-8') as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(rows[0]['theoretical_ber'], '')

    def test_cancelled_write_boundary_adopts_complete_archive_on_resume(self):
        spec = self.request()
        cancel = Event()
        with TemporaryDirectory() as directory:
            folder = Path(directory)/'campaign'

            def interrupt_after_archive(path, result, execution):
                identifier = save_experiment(path, result, execution)
                if path.name == 'run-0002.slproj':
                    cancel.set()
                return identifier

            with patch('signallab_pc.communications_sweep.save_experiment', side_effect=interrupt_after_archive):
                with self.assertRaises(OperationCancelled):
                    run_sweep(spec, folder, ExecutionContext(cancel=cancel))
            interrupted = load_sweep(folder)
            self.assertFalse(interrupted.complete)
            self.assertEqual(len(interrupted.runs), 1)
            files = [folder/row for row in ('run-0001.slproj', 'run-0002.slproj')]
            contents = [path.read_bytes() for path in files]
            with patch('signallab_pc.communications_sweep.run_experiment', wraps=run_experiment) as calculate:
                resumed = run_sweep(spec, folder)
                self.assertEqual(calculate.call_count, 2)
            self.assertEqual([path.read_bytes() for path in files], contents)
            self.assertEqual(resumed.runs[0], interrupted.runs[0])
            reference = run_sweep(spec, Path(directory)/'reference')
            for expected, actual in zip(reference.runs, resumed.runs, strict=True):
                for name in ('ordinal', 'parameters', 'seed', 'metrics', 'theoretical', 'synchronization'):
                    self.assertEqual(actual[name], expected[name])

    def test_exclusive_writer_lock_and_canonical_paths(self):
        spec = self.request()
        with TemporaryDirectory() as directory:
            folder = Path(directory)
            program = '''import sys
from signallab_pc.communications_experiment import ExperimentSpec
from signallab_pc.communications_sweep import SweepAxis,SweepSpec,run_sweep
try:
    run_sweep(SweepSpec(ExperimentSpec(bit_count=8),(SweepAxis('eb_n0_db',(3,)),)),sys.argv[1])
except ValueError as error:
    print(error)
    raise SystemExit(6)
'''
            with _locked(folder):
                denied = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-c', program, directory],
                                        capture_output=True, encoding='utf-8', timeout=20)
            self.assertEqual(denied.returncode, 6, denied.stderr)
            self.assertIn('bloqueo', denied.stdout)
            self.assertFalse((folder/'campaign.json').exists())
            nested = folder/'archive'
            nested.mkdir()
            (nested/'run-0001.slproj').mkdir()
            with self.assertRaisesRegex(ValueError, 'regulares'):
                run_sweep(spec, nested)

    def test_corruption_and_incompatible_definition_do_not_replace_completed_runs(self):
        spec = self.request()
        with TemporaryDirectory() as directory:
            folder = Path(directory)
            result = run_sweep(spec, folder)
            catalog = folder/'campaign.json'
            original = catalog.read_bytes()
            wrong = SweepSpec(spec.base, (SweepAxis('eb_n0_db', (1,)),))
            with self.assertRaisesRegex(ValueError, 'otros parámetros'):
                run_sweep(wrong, folder)
            self.assertEqual(catalog.read_bytes(), original)
            doc = json.loads(original)
            doc['runs'][0]['file'] = '../missing.slproj'
            catalog.write_text(json.dumps(doc), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'ruta'):
                load_sweep(folder)
            doc['runs'][0] = result.runs[0] | {'archive_sha256': 'bad'}
            catalog.write_text(json.dumps(doc), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'evidencia'):
                load_sweep(folder)
            catalog.write_bytes(original)
            archive = folder/result.runs[0]['file']
            contents = bytearray(archive.read_bytes())
            contents[-1] ^= 1
            archive.write_bytes(contents)
            with self.assertRaises(ValueError):
                run_sweep(spec, folder)
            self.assertEqual(catalog.read_bytes(), original)

    def test_validation_and_unavailable_metrics_export(self):
        for name, values in (('unknown',(1,)), ('rolloff',(2,)), ('span_symbols',(0,)),
                             ('order',(1,)), ('eb_n0_db',()), ('eb_n0_db',(0,0))):
            with self.subTest(name=name, values=values), self.assertRaises(ValueError):
                SweepAxis(name, values)
        base = ExperimentSpec(bit_count=16, pulse=PulseSpec('rectangular', 2, 1),
                              synchronization=SynchronizationSpec('assisted', sample_offset=10_000))
        axis = SweepAxis('eb_n0_db', (3,))
        with self.assertRaises(ValueError):
            SweepSpec(base, ())
        with self.assertRaises(ValueError):
            SweepSpec(base, (axis, axis))
        with self.assertRaises(ValueError):
            SweepSpec(base, (axis,), 'random')
        with self.assertRaises(ResourceLimitError):
            SweepSpec(base, (SweepAxis('eb_n0_db', tuple(range(33))), SweepAxis('order', tuple(range(33,66)))))
        with TemporaryDirectory() as directory:
            folder = Path(directory)/'study'
            with self.assertRaises(TypeError):
                run_sweep(None, folder)
            with self.assertRaises(ValueError):
                run_sweep(SweepSpec(base, (SweepAxis('rolloff', (.2,)),)), folder)
            self.assertFalse(folder.exists())
            result = run_sweep(SweepSpec(base, (axis,)), folder)
            self.assertIsNone(result.runs[0]['metrics'])
            export = folder/'summary.csv'
            export_sweep_csv(result, export)
            with export.open(newline='', encoding='utf-8') as stream:
                row = next(csv.DictReader(stream))
            self.assertEqual(row['synchronization'], 'unavailable')
            self.assertEqual(row['ber'], '')
            self.assertTrue(row['theoretical_ber'])

    def test_catalog_schema_and_digest_checked_before_reading_runs(self):
        with TemporaryDirectory() as directory:
            folder = Path(directory)
            campaign = run_sweep(self.request(), folder)
            catalog = folder/'campaign.json'
            original = json.loads(catalog.read_bytes())
            cases = (
                (original | {'runs': {}}, 'catálogo de barrido'),
                (original | {'settings_sha256': '00'*32}, 'huella de configuración'),
                (original | {'runs': [*original['runs'], original['runs'][0]]}, 'más corridas'),
            )
            for malformed, message in cases:
                with self.subTest(message=message):
                    catalog.write_text(json.dumps(malformed), encoding='utf-8')
                    with self.assertRaisesRegex(ValueError, message):
                        load_sweep(folder)
            for key, value, message in (('engine_contract', 999, 'contrato de cálculo'),
                                         ('specification', [], 'requiere una configuración'),
                                         ('specification', {}, 'está incompleta')):
                definition = original['definition'] | {key: value}
                document = original | {'definition': definition, 'settings_sha256': settings_digest(definition)}
                catalog.write_text(json.dumps(document), encoding='utf-8')
                with self.subTest(key=key, value=value), self.assertRaisesRegex(ValueError, message):
                    load_sweep(folder)
            self.assertTrue(campaign.complete)

    def test_import_rechecks_verified_archive_and_rejects_replacement(self):
        with TemporaryDirectory() as directory:
            folder = Path(directory)
            campaign = run_sweep(self.request(), folder)
            project, key = load_sweep_run(campaign, 1)
            self.assertEqual(load_experiment(project, key).report['metrics'], campaign.runs[0]['metrics'])
            archive = folder/campaign.runs[0]['file']
            with self.assertRaises(TypeError):
                load_sweep_run(None, 1)
            with self.assertRaises(ValueError):
                load_sweep_run(campaign, 0)
            session_output = run_experiment(campaign.specification.base)
            save_experiment(archive, session_output)
            with self.assertRaisesRegex(ValueError, 'distinta de la corrida'):
                load_sweep_run(campaign, 1)
            catalog = folder/'campaign.json'
            document = json.loads(catalog.read_bytes())
            document['runs'][1]['record'] = 'changed'
            catalog.write_text(json.dumps(document), encoding='utf-8')
            modified = type(campaign)(campaign.directory, campaign.specification, campaign.planned,
                                      tuple(document['runs']))
            with self.assertRaisesRegex(ValueError, 'cambió desde la verificación'):
                load_sweep_run(modified, 2)

    def test_decimal_sweep_values_match_cli_and_form_conventions(self):
        self.assertEqual(axis_from_text('eb_n0_db', '1.5, 2.75'), SweepAxis('eb_n0_db', (1.5, 2.75)))
        with self.assertRaises(ValueError):
            axis_from_text('span_symbols', '2.5')


if __name__ == '__main__':
    unittest.main()
