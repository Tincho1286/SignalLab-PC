import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from signallab_pc.filters import Transfer
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.sampling import resample
from signallab_pc.spectral_measurements import stft_band_series
from signallab_pc.stft_tools import analyze, axes, frame_signals, spectrum, synthesize


class FollowupClockAndScaleTests(unittest.TestCase):
    def test_filter_period_supplies_rate_but_not_an_epoch(self):
        model = Transfer([2], [1], sample_period_s=.125)
        for metadata in ({}, {'sample_rate_hz': 8}):
            source = Signal([1, 2], -17, metadata=metadata)
            output = model.apply(source)
            np.testing.assert_array_equal(output.values, [2, 4])
            self.assertEqual(output.origin, -17)
            self.assertEqual(output.metadata['sample_rate_hz'], 8)
            self.assertNotIn('time_start_s', output.metadata)
        output = model.apply(Signal([1, 2], -17, metadata={'time_start_s': 30}))
        self.assertEqual(output.metadata['time_start_s'], 30)
        with self.assertRaisesRegex(ValueError, 'resolución'):
            model.apply(Signal([1, 2], -17, metadata={'time_start_s': 2.**53}))

    def test_stft_rate_only_does_not_turn_a_relative_frame_into_a_timestamp(self):
        x = Signal([0, 1, 2, 3, 4, 5], -17, metadata={'sample_rate_hz': 8})
        result = analyze(x, 4, 2, 8, 'boxcar')
        _, centers, _, label, _ = axes(result, physical=True)
        self.assertIn('relativ', label)
        np.testing.assert_array_equal(centers, [1.5/8, 3.5/8])
        tramo = frame_signals(result, 1)[0]
        self.assertEqual(tramo.origin, -15)
        self.assertEqual(tramo.metadata['sample_rate_hz'], 8)
        self.assertNotIn('time_start_s', tramo.metadata)
        local = spectrum(result, 0, physical=True, phase='local')
        relative = spectrum(result, 0, physical=True, phase='global')
        np.testing.assert_array_equal(local.values, relative.values)
        self.assertNotIn('time_start_s', synthesize(result).metadata)
        power = stft_band_series(result, [('Todo', None, None)])[0]
        self.assertEqual(power.metadata['sample_rate_hz'], 4)
        self.assertNotIn('time_start_s', power.metadata)

    def test_sinc_interpolation_keeps_finite_output_at_large_scale(self):
        source = Signal([1e308, 0])
        result = resample(source, 2, 'sinc')
        self.assertEqual(result.values[0], source.values[0])
        self.assertEqual(result.values[-1], 0)
        self.assertAlmostEqual(result.values[1].real / 1e308, 2 / math.pi, places=14)
        self.assertEqual(result.values[1].imag, 0)


class ProjectLineageTests(unittest.TestCase):
    def test_long_lineage_exports_and_recovers_the_legacy_period(self):
        project = Project()
        source = project.add(Signal([1], metadata={'sample_rate_hz': 8}))
        key = source
        for _ in range(1100):
            key = project.add({'value': 1}, parents=[key])
        system = project.add(Transfer([2], [1]), parents=[key])
        document = project.document()
        del document['records'][-1]['data']['sample_period_s']
        project = Project.from_document(document)
        self.assertEqual(project.get(system).sample_period_s, .125)
        with TemporaryDirectory() as folder:
            path = Path(folder)/'result.json'
            project.export_record(system, path)
            reopened = Project()
            self.assertEqual(reopened.merge(path), 1102)
        self.assertEqual(reopened.get(reopened.headers()[-1]['id']).sample_period_s, .125)

    def test_result_export_includes_references_registered_in_the_report(self):
        project = Project()
        signal_id = project.add(Signal([3,5]))
        report = project.add({'report':'Salida', 'calculated_data':{'output':{'result_id':signal_id}}})
        with TemporaryDirectory() as folder:
            path = Path(folder)/'result.json'
            project.export_record(report,path)
            output = Project()
            self.assertEqual(output.merge(path),2)
        new_signal,new_report = output.headers()
        reference = output.get(new_report['id'])['calculated_data']['output']['result_id']
        self.assertEqual(reference,new_signal['id'])
        self.assertNotEqual(reference,signal_id)
        np.testing.assert_array_equal(output.get(reference).values,[3,5])
