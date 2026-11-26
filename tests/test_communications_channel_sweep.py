import csv
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
import unittest

import numpy as np

from signallab_pc.communications_experiment import ExperimentSpec
from signallab_pc.communications_interference import (
    BandInterference, ExternalInterference, InterferenceSpec, apply_interference,
)
from signallab_pc.communications_pipeline import ChannelPipelineSpec, ChannelStage
from signallab_pc.communications_propagation import PropagationSpec
from signallab_pc.communications_storage import load_experiment
from signallab_pc.communications_sweep import (
    SweepAxis, SweepSpec, axis_from_text, export_sweep_csv, load_sweep, load_sweep_run, run_sweep,
    summarize_sweep_repetitions, sweep_axes,
)
from signallab_pc.execution import ExecutionContext
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal


class ChannelSweepContracts(unittest.TestCase):
    def test_sinr_calibration_accounts_for_realized_noise(self):
        signal = Signal(np.ones(1024), metadata={'sample_rate_hz': 1024})
        model = BandInterference(128, 200)
        result = apply_interference(signal, InterferenceSpec(model, noise_snr_db=20, sinr_db=8))
        self.assertAlmostEqual(result.statistics.sinr.db, 8)
        measured = float(np.mean(abs(result.interference.values)**2) + np.mean(abs(result.noise.values)**2))
        self.assertAlmostEqual(measured, 10**(-.8))
        without_noise = apply_interference(signal, InterferenceSpec(model, sinr_db=8))
        self.assertAlmostEqual(without_noise.statistics.sir.db, 8)
        with self.assertRaisesRegex(ValueError, 'ruido por sí sola'):
            apply_interference(signal, InterferenceSpec(model, noise_snr_db=10, sinr_db=50))

    def test_multidimensional_channel_campaign_and_common_replica_seeds(self):
        pipeline = ChannelPipelineSpec((
            ChannelStage(PropagationSpec(gain_db=0)),
            ChannelStage(InterferenceSpec(BandInterference(6000, 10000), noise_snr_db=20, sir_db=3)),
        ), seed=85)
        spec = SweepSpec(ExperimentSpec(bit_count=160, eb_n0_db=None, channel_pipeline=pipeline),
                         (axis_from_text('channel.2.sinr_db', '4,8'), SweepAxis('channel.1.gain_db', (0, 6))),
                         'common', 3)
        with TemporaryDirectory() as folder:
            result = run_sweep(spec, folder)
            self.assertEqual(result.planned, 12)
            self.assertEqual(result, load_sweep(folder))
            self.assertEqual(result.runs[0]['seed'], result.runs[3]['seed'])
            self.assertNotEqual(result.runs[0]['seed'], result.runs[1]['seed'])
            for row in result.runs:
                self.assertAlmostEqual(row['channel_ratios']['channel.2.measured_sinr_db'],
                                       row['parameters']['channel.2.sinr_db'])
            summary = summarize_sweep_repetitions(result)
            self.assertEqual(len(summary), 4)
            self.assertTrue(all(point['runs'] == point['measurements']['evm']['valid'] == 3 for point in summary))
            self.assertTrue(all(point['measurements']['evm']['confidence'] is not None for point in summary))
            archive, key = load_sweep_run(result, 5)
            run = load_experiment(archive, key)
            self.assertEqual(run.specification.channel_pipeline.stages[1].operation.sinr_db, 4)
            self.assertIsNone(run.specification.channel_pipeline.stages[1].operation.sir_db)
            output = Path(folder)/'curve.csv'
            export_sweep_csv(result, output)
            with output.open(encoding='utf-8', newline='') as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(rows[4]['repetition'], '2')
            self.assertAlmostEqual(float(rows[4]['channel.2.measured_sinr_db']), 4)

    def test_external_archive_survives_cancel_and_supplies_resume(self):
        source = Signal(np.full(12, .01j), metadata={'sample_rate_hz': 96000, 'time_start_s': 0})
        pipeline = ChannelPipelineSpec((ChannelStage(InterferenceSpec(ExternalInterference()), 'peer'),))
        base = ExperimentSpec(bit_count=80, eb_n0_db=None, channel_pipeline=pipeline)
        spec = SweepSpec(base, (SweepAxis('channel.1.power', (0.001, .002)),))
        cancel = Event()

        def stop_after_first(percent):
            if percent >= 50:
                cancel.set()

        with TemporaryDirectory() as folder:
            context = ExecutionContext(cancel=cancel, progress=stop_after_first)
            with self.assertRaises(OperationCancelled):
                run_sweep(spec, folder, context, external={'peer': source})
            partial = load_sweep(folder)
            self.assertEqual(len(partial.runs), 1)
            with self.assertRaisesRegex(ValueError, 'externas'):
                run_sweep(spec, folder, external={'peer': source.copy_with(values=2*source.values)})
            finished = run_sweep(partial.specification, folder)
            self.assertTrue(finished.complete)
            self.assertEqual(finished.runs[0], partial.runs[0])
            inputs = Path(folder)/'external-sources.slproj'
            inputs.write_bytes(b'invalid')
            with self.assertRaises((ValueError, OSError)):
                load_sweep(folder)

    def test_unavailable_axes_and_invalid_channel_values_stop_before_catalog(self):
        pipeline = ChannelPipelineSpec((ChannelStage(InterferenceSpec(BandInterference(1000))),))
        base = ExperimentSpec(bit_count=80, channel_pipeline=pipeline)
        self.assertIn('channel.1.sinr_db', sweep_axes(pipeline))
        with self.assertRaisesRegex(ValueError, 'disponible'):
            SweepSpec(base, (SweepAxis('channel.2.model.bandwidth_hz', (1000,)),))
        with self.assertRaisesRegex(ValueError, 'una sola referencia'):
            SweepSpec(base, (SweepAxis('channel.1.power', (1,)), SweepAxis('channel.1.sir_db', (3,))))
        spec = SweepSpec(base, (SweepAxis('channel.1.model.bandwidth_hz', (-100,)),))
        with TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, 'ancho de banda'):
                run_sweep(spec, folder)
            self.assertFalse((Path(folder)/'campaign.json').exists())

    def test_intervals_leave_zero_or_unavailable_observations_unbounded_by_the_sample(self):
        pipeline = ChannelPipelineSpec((ChannelStage(PropagationSpec()),))
        spec = SweepSpec(ExperimentSpec(bit_count=160, eb_n0_db=None, channel_pipeline=pipeline),
                         (SweepAxis('channel.1.gain_db', (0,)),), repetitions=3)
        with TemporaryDirectory() as folder:
            result = run_sweep(spec, folder)
            ber = summarize_sweep_repetitions(result)[0]['measurements']['ber']
            self.assertEqual(ber, {'mean': 0.0, 'confidence': None, 'valid': 3})
