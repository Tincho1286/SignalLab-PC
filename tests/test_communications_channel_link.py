from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from signallab_pc import session
from signallab_pc.communications_channel import ChannelPath, MultipathSpec
from signallab_pc.communications_doppler import CarrierShift
from signallab_pc.communications_experiment import ExperimentSpec, run_experiment
from signallab_pc.communications_fading import FadingPath, FadingSpec
from signallab_pc.communications_impairments import TimingOffset
from signallab_pc.communications_interference import ExternalInterference, InterferenceSpec
from signallab_pc.communications_pipeline import ChannelPipelineSpec, ChannelStage
from signallab_pc.communications_receiver import SynchronizationSpec
from signallab_pc.communications_storage import load_experiment, save_experiment
from signallab_pc.model import Signal


class ChannelLinkContracts(unittest.TestCase):
    def test_disabled_channel_preserves_historical_settings_and_awgn_waveform(self):
        legacy = ExperimentSpec(bit_count=96, seed=6, eb_n0_db=10)
        explicit_empty = replace(legacy, channel_pipeline=ChannelPipelineSpec(seed=7))
        original, control = (run_experiment(spec) for spec in (legacy, explicit_empty))
        self.assertEqual(original.report(), control.report())
        self.assertNotIn('channel_pipeline', original.report()['specification'])
        for role, signal in original.signals().items():
            np.testing.assert_array_equal(signal.values, control.signals()[role].values)

    def test_known_integer_channel_delay_keeps_the_symbol_grid(self):
        config = ExperimentSpec(bit_count=160, seed=8, eb_n0_db=None)
        baseline = run_experiment(config)
        chain = ChannelPipelineSpec((ChannelStage(MultipathSpec((ChannelPath(5),))),))
        delayed = run_experiment(replace(config, channel_pipeline=chain))
        np.testing.assert_allclose(delayed.reception.symbols.values, baseline.reception.symbols.values, atol=2e-13)
        self.assertEqual(delayed.reception.synchronization.sample_offset, baseline.reception.synchronization.sample_offset+5)
        self.assertEqual(delayed.reception.synchronization.method, 'known_channel_reference')
        self.assertEqual(delayed.metrics.ber.errors, 0)
        np.testing.assert_array_equal(delayed.pipeline.signal.values, np.pad(baseline.transmitted.values, (5, 0)))

    def test_fractional_and_clock_mismatch_are_not_assessed_as_aligned(self):
        baseline = ExperimentSpec(bit_count=160, eb_n0_db=None)
        for impairment, method in ((TimingOffset(.375), 'known_channel_reference'),
                                  (TimingOffset(sfo_ppm=250), 'clock_mismatch')):
            with self.subTest(impairment=impairment):
                spec = replace(baseline, channel_pipeline=ChannelPipelineSpec((ChannelStage(impairment),)))
                result = run_experiment(spec)
                self.assertEqual(result.reception.synchronization.state, 'unavailable')
                self.assertEqual(result.reception.synchronization.method, method)
                self.assertIsNone(result.metrics)
                self.assertIsNone(result.received_bits)
                with TemporaryDirectory() as folder:
                    file = Path(folder)/'experiment.slproj'
                    key = save_experiment(file, result)
                    archive, _ = session.load(file)
                    stored = load_experiment(archive, key)
                    self.assertEqual(stored.specification, spec)
                    self.assertIsNone(stored.report['metrics'])
                    self.assertNotIn('observed', stored.records)
                    self.assertEqual(stored.chain['stage_records'][-1]['record'], stored.records['channel_output'])
                    if method == 'clock_mismatch':
                        self.assertAlmostEqual(archive.get(stored.records['matched']).metadata['sample_rate_hz'], 96024)

    def test_fading_and_doppler_preserve_their_states_and_require_measured_metrics(self):
        base = ExperimentSpec(bit_count=200, seed=71, eb_n0_db=14,
                              synchronization=SynchronizationSpec('estimated', search_first=77, search_last=86))
        for path in (FadingPath(2), FadingPath(2, 1, 20, .3)):
            with self.subTest(path=path):
                stages = (ChannelStage(FadingSpec((path,), 76, 0)), ChannelStage(CarrierShift(.01)))
                result = run_experiment(replace(base, channel_pipeline=ChannelPipelineSpec(stages, seed=11)))
                self.assertEqual(result.reception.synchronization.method, 'pilot_normalized_correlation')
                self.assertEqual(result.reception.synchronization.sample_offset, 82)
                self.assertIsNotNone(result.metrics)
                self.assertIsNone(result.theoretical)
                self.assertIsNotNone(result.channel)
                self.assertEqual(result.report()['channel_pipeline']['stages'][0]['sample_count'],
                                 result.transmitted.values.size + 2)
                self.assertIn('fading_1', dict(result.pipeline.stages[0].components))

    def test_external_interference_is_archived_inside_the_link(self):
        base = ExperimentSpec(bit_count=40, eb_n0_db=None)
        tx = run_experiment(base).transmitted
        peer = tx.copy_with(values=np.full(tx.values.size, .005j), name='Interferente externo')
        config = ChannelPipelineSpec((ChannelStage(InterferenceSpec(ExternalInterference()), 'peer'),))
        spec = replace(base, channel_pipeline=config)
        result = run_experiment(spec, external={'peer': peer})
        np.testing.assert_allclose(result.pipeline.signal.values, tx.values + .005j)
        with TemporaryDirectory() as folder:
            file = Path(folder)/'interference.slproj'
            key = save_experiment(file, result)
            archive, _ = session.load(file)
            stored = load_experiment(archive, key)
            self.assertIn('peer', stored.chain['external_records'])
            np.testing.assert_array_equal(archive.get(stored.chain['external_records']['peer']).values, peer.values)
