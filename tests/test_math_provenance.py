from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from numpy.testing import assert_array_equal

from signallab_pc import session
from signallab_pc.dft_application import DFTRequest, calculate_dft, store_dft
from signallab_pc.dsp_application import FIRRequest, apply_fir, store_signal
from signallab_pc.dsp_pipeline import run_pipeline, store_pipeline
from signallab_pc.execution import ExecutionContext
from signallab_pc.filters import Transfer
from signallab_pc.model import Signal
from signallab_pc.project import Project
from test_math_dsp_pipeline import case


class VerifiedProvenanceTests(unittest.TestCase):
    def test_dft_checks_samples_and_clock_before_linking_an_existing_record(self):
        source = Signal([1, 2], -1, metadata={'sample_rate_hz': 8})
        result = calculate_dft(DFTRequest(source))
        project = Project()
        good = project.add(source)
        wrong_signal = project.add(source.copy_with(values=[2, 1]))
        wrong_clock = project.add(source.copy_with(metadata={'sample_rate_hz': 16}))
        before = project.document()
        for parent in (wrong_signal, wrong_clock, 'missing'):
            with self.subTest(parent=parent), self.assertRaisesRegex(ValueError, '[Oo]rigen'):
                store_dft(project, result, source_id=parent)
            self.assertEqual(project.document(), before)
        _, target = store_dft(project, result, source_id=good)
        self.assertEqual(project.headers()[-1]['parents'], [good])
        assert_array_equal(project.get(target).values, result.spectrum.values)

    def test_dft_rejects_changed_data_during_calculation_and_at_commit(self):
        source = Signal([1, 2])

        def change_source(progress):
            if progress == 100:
                source.values[0] = 3

        with self.assertRaisesRegex(ValueError, 'cambió durante'):
            calculate_dft(DFTRequest(source), ExecutionContext(progress=change_source))
        result = calculate_dft(DFTRequest(source))
        project = Project()
        source.values[0] = 4
        with self.assertRaisesRegex(ValueError, 'origen registrado'):
            store_dft(project, result, source=source)
        result.spectrum.values[0] = 7
        with self.assertRaisesRegex(ValueError, 'cambió después'):
            store_dft(project, result)
        self.assertEqual(project.headers(), [])

    def test_pipeline_rejects_wrong_identifiers_settings_and_mutable_intermediates(self):
        request = case(2, 3)
        result = run_pipeline(request)
        project = Project()
        source_id = project.add(request.conversion.signal)
        wrong = project.add(Transfer([.4, .6], [1]))
        before = project.document()
        with self.assertRaisesRegex(ValueError, 'origen registrado'):
            store_pipeline(project, request, result, source_id=source_id, filter_id=wrong)
        with self.assertRaisesRegex(ValueError, 'parámetros originales'):
            store_pipeline(project, replace(request, dft_length=8), result)
        result.resampled.antialias.b[0] = 2
        with self.assertRaisesRegex(ValueError, 'cambió después'):
            store_pipeline(project, request, result)
        self.assertEqual(project.document(), before)

    def test_verified_records_survive_session_and_merge_with_new_ids(self):
        request = case()
        result = run_pipeline(request)
        project = Project()
        source_id = project.add(request.conversion.signal)
        model_id = project.add(request.fir)
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'session.json'
            session.save(path, project, session.empty_workspace())
            restored, workspace = session.load(path)
            records = store_pipeline(restored, request, result, source_id=source_id, filter_id=model_id)
            session.save(path, restored, workspace)
            reopened, _ = session.load(path)
            self.assertEqual(restored.headers(), reopened.headers())
            reopened.export_record(records.dft, path)
            imported = Project()
            self.assertEqual(imported.merge(path), 6)
            assert_array_equal(imported.get(imported.headers()[-1]['id']).values, result.dft.spectrum.values)
            changed = reopened.document()
            changed['records'][0]['data']['values'][0][0] = 8.0
            with self.assertRaisesRegex(ValueError, 'origen registrado'):
                Project.from_document(changed)

    def test_individual_fir_requires_the_filter_actually_used(self):
        project = Project()
        x = Signal([1, 2, 3])
        model = Transfer([.5, .5], [1])
        source_id, model_id = project.add(x), project.add(model)
        other_id = project.add(Transfer([.5, .5], [1], sample_period_s=.1))
        out = apply_fir(FIRRequest(x, model))
        with self.assertRaisesRegex(ValueError, 'origen registrado'):
            store_signal(project, out, parents=(source_id, other_id))
        with self.assertRaisesRegex(ValueError, 'todos los orígenes'):
            store_signal(project, out, parents=(source_id,))
        store_signal(project, out, parents=(source_id, model_id))
        self.assertEqual(len(project.headers()), 4)

    def test_complex_normalization_and_legacy_pivot_are_reusable(self):
        project = Project()
        source = Signal([1, -2, 3])
        source_id = project.add(source)
        model = Transfer([1], [-90.1 + 33.2j])
        self.assertEqual(complex(model.a[0]), 1 + 0j)
        model_id = project.add(model)
        stored = project.document()
        for previous_pivot in ([1.0, -0.0], [1.0000000000000002, 0.0]):
            with self.subTest(pivot=previous_pivot):
                stored['records'][1]['data']['a'][0] = previous_pivot
                restored = Project.from_document(stored)
                loaded = restored.get(model_id)
                result = apply_fir(FIRRequest(source, loaded))
                result_id = store_signal(restored, result, parents=(source_id, model_id))
                reopened = Project.from_document(restored.document())
                assert_array_equal(reopened.get(result_id).values, result.values)
