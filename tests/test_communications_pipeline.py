import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
import unittest

import numpy as np

from signallab_pc import session
from signallab_pc.communications_channel import AWGNSpec, ChannelPath, MultipathSpec
from signallab_pc.communications_doppler import CarrierShift
from signallab_pc.communications_fading import FadingPath, FadingSpec
from signallab_pc.communications_impairments import IQImbalance, PhaseNoiseSpec, TimingOffset
from signallab_pc.communications_interference import (
    BandInterference, ExternalInterference, InterferenceSpec, InterferenceTone, ToneInterference,
)
from signallab_pc.communications_pipeline import (
    ChannelPipelineSpec, ChannelStage, decode_pipeline_spec, encode_pipeline_spec,
    load_channel_pipeline, run_channel_pipeline, store_channel_pipeline,
)
from signallab_pc.communications_propagation import FreeSpaceLoss, LogDistanceLoss, PropagationSpec
from signallab_pc.dsp_pipeline import PipelineStageError
from signallab_pc.execution import ExecutionContext, ResourcePool
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.resources import ResourceLimitError


class ChannelPipelineContracts(unittest.TestCase):
    def test_order_is_observable_and_empty_chain_is_identity(self):
        signal = Signal([1+2j, 2-3j, 4], origin=-2, metadata={'sample_rate_hz': 1024, 'time_start_s': .25})
        gain = ChannelStage(PropagationSpec(gain_db=20*math.log10(2)))
        additive = ChannelStage(InterferenceSpec(ToneInterference((InterferenceTone(0, 2),))))
        forward = run_channel_pipeline(signal, ChannelPipelineSpec((gain, additive)))
        reverse = run_channel_pipeline(signal, ChannelPipelineSpec((additive, gain)))
        np.testing.assert_allclose(forward.signal.values, 2*signal.values+2)
        np.testing.assert_allclose(reverse.signal.values, 2*(signal.values+2))
        self.assertEqual(forward.report()['stages'][0]['clock']['time_start_s'], .25)
        self.assertAlmostEqual(forward.stages[1].input_power, np.mean(abs(2*signal.values)**2))
        empty = run_channel_pipeline(signal, ChannelPipelineSpec())
        self.assertIs(empty.signal, signal)
        self.assertFalse(empty.stages)
        project = Project()
        result = store_channel_pipeline(project, empty)
        self.assertEqual(load_channel_pipeline(project, result['report_record'])[0], empty.specification)

    def test_codec_round_trip_and_invalid_schema(self):
        operations = (
            MultipathSpec((ChannelPath(0), ChannelPath(8, .1))), FadingSpec((FadingPath(),), 20, 60),
            CarrierShift(128, .1), TimingOffset(.3, 100), PhaseNoiseSpec(2, 77), IQImbalance(3, .05),
            InterferenceSpec(BandInterference(120, 200, 3), sir_db=8),
            InterferenceSpec(ToneInterference((InterferenceTone(8, .1),))),
            AWGNSpec('snr', 10, 6), PropagationSpec(),
            PropagationSpec(FreeSpaceLoss(100, 9e8)), PropagationSpec(LogDistanceLoss(100, 1, 2, 32)),
        )
        spec = ChannelPipelineSpec((*map(ChannelStage, operations),
                                    ChannelStage(InterferenceSpec(ExternalInterference()), 'interferer')), seed=7)
        self.assertEqual(decode_pipeline_spec(json.loads(json.dumps(encode_pipeline_spec(spec)))), spec)
        for document in ({'schema': True, 'stages': []}, {'schema': 1, 'stages': [{}]},
                         {'schema': 1, 'stages': [{'kind': 'carrier', 'parameters': {'unknown': 1}}]},
                         {'schema': 1, 'stages': [{'kind': 'fading', 'parameters': {'seed': 2}}]},
                         {'schema': 1, 'stages': [{'kind': 'awgn', 'parameters': {'reference': 'snr',
                                                                              'level_db': 3, 'seed': 5},
                                                   'external_input': 'unused'}]}):
            with self.subTest(document=document), self.assertRaises(ValueError):
                decode_pipeline_spec(document)

    def test_reproducible_substreams_and_auxiliary_results(self):
        signal = Signal(np.ones(512), metadata={'sample_rate_hz': 1024})
        phase = ChannelStage(PhaseNoiseSpec(6, 73))
        fading = ChannelStage(FadingSpec((FadingPath(),), 120, 2))
        spec = ChannelPipelineSpec((phase, phase, fading), seed=19)
        result = run_channel_pipeline(signal, spec)
        repeat = run_channel_pipeline(signal, spec)
        np.testing.assert_array_equal(result.signal.values, repeat.signal.values)
        self.assertEqual(result.report_sha256, repeat.report_sha256)
        first, second, third = result.stages
        self.assertNotEqual(first.stage.operation.seed, second.stage.operation.seed)
        ph1, ph2 = first.components[0][1], second.components[0][1]
        self.assertFalse(np.array_equal(ph1.values, ph2.values))
        np.testing.assert_allclose(second.signal.values, np.exp(1j*(ph1.values+ph2.values)), atol=2e-15)
        self.assertTrue(third.report()['conditions'])
        control = run_channel_pipeline(signal, ChannelPipelineSpec((phase, phase)))
        self.assertEqual(control.stages[0].stage, control.stages[1].stage)
        band = ChannelStage(InterferenceSpec(BandInterference(120, 200, 73), noise_snr_db=10, noise_seed=73))
        mixture = run_channel_pipeline(signal, ChannelPipelineSpec((band,), seed=19)).stages[0]
        self.assertNotEqual(mixture.stage.operation.model.seed, mixture.stage.operation.noise_seed)
        self.assertEqual(tuple(name for name, _ in mixture.components), ('interference', 'noise'))

    def test_archive_round_trip_and_project_remapping(self):
        x, external = Signal([1, 2, 3, 4], origin=-1), Signal([2j, -1], origin=0)
        spec = ChannelPipelineSpec((
            ChannelStage(InterferenceSpec(ExternalInterference()), 'peer'),
            ChannelStage(IQImbalance(dc_i=.5)),
        ))
        result = run_channel_pipeline(x, spec, external={'peer': external})
        np.testing.assert_array_equal(result.signal.values, [1.5, 2.5+2j, 2.5, 4.5])
        project = Project()
        source_id, external_id = project.add(x), project.add(external)
        original = store_channel_pipeline(project, result, source_id=source_id, external_records={'peer': external_id})
        with TemporaryDirectory() as folder:
            archive = Path(folder)/'chain.slproj'
            session.save(archive, project, session.empty_workspace())
            loaded, _ = session.load(archive)
            recovered, report = load_channel_pipeline(loaded, original['report_record'])
            self.assertEqual(recovered, spec)
            self.assertEqual(report['external_records'], {'peer': external_id})
        copied = Project()
        ids = copied.incorporate(loaded, root=original['report_record'])
        _, report = load_channel_pipeline(copied, ids[original['report_record']])
        self.assertEqual(report['external_records']['peer'], ids[external_id])
        np.testing.assert_array_equal(copied.get(report['stage_records'][-1]['record']).values, result.signal.values)

    def test_failed_stages_budget_and_cancellation_leave_no_partial_archive(self):
        signal = Signal(np.ones(1024), metadata={'sample_rate_hz': 1024})
        gain = ChannelStage(PropagationSpec())
        spec = ChannelPipelineSpec((gain, gain))
        with self.assertRaisesRegex(PipelineStageError, 'Etapa 2.*carrier'):
            run_channel_pipeline(signal, ChannelPipelineSpec((gain, ChannelStage(CarrierShift(800)))))
        with self.assertRaisesRegex(ValueError, 'externas'):
            run_channel_pipeline(signal, spec, external={'unused': signal})
        with self.assertRaises(ResourceLimitError):
            run_channel_pipeline(signal, spec, execution=ExecutionContext(max_work_bytes=70*signal.values.size))
        cancellation = Event()
        pool = ResourcePool(100_000)

        def progress(value):
            if value > 51:
                cancellation.set()

        with self.assertRaises(OperationCancelled):
            run_channel_pipeline(signal, spec, execution=ExecutionContext(cancel=cancellation, pool=pool, progress=progress))
        with pool.reserve(100_000):
            self.assertTrue(cancellation.is_set())
        result = run_channel_pipeline(signal, ChannelPipelineSpec((gain, ChannelStage(PhaseNoiseSpec(6, 8)))))
        project = Project()
        source_id = project.add(signal)
        result.stages[1].components[0][1].values[0] = 9
        with self.assertRaisesRegex(ValueError, 'cambió'):
            store_channel_pipeline(project, result, source_id=source_id)
        self.assertEqual(len(project.headers()), 1)
