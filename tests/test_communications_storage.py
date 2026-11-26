import base64
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
import unittest

import numpy as np

from signallab_pc import session
from signallab_pc.communications_data import BitSequence, SymbolClock, SymbolSequence
from signallab_pc.communications_experiment import ExperimentSpec, run_experiment
from signallab_pc.communications_pulses import PulseSpec
from signallab_pc.communications_receiver import SynchronizationSpec
from signallab_pc.communications_storage import (
    decode_bits, decode_experiment_spec, decode_symbols, encode_bits, encode_symbols,
    load_experiment, save_experiment, store_experiment,
)
from signallab_pc.execution import ExecutionContext
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.resources import ResourceLimitError


class CommunicationsStorageTests(unittest.TestCase):
    def test_typed_vectors_round_trip_canonical_bytes_and_clock(self):
        bits = BitSequence([1, 0, 1, 1, 1], seed=9289171)
        binary = encode_bits(bits)
        self.assertEqual(base64.b64decode(binary['data_base64']), bytes([0b10111000]))
        np.testing.assert_array_equal(decode_bits(binary).values, bits.values)
        self.assertEqual(decode_bits(binary).seed, 9289171)
        full = BitSequence([1]*8)
        self.assertEqual(decode_bits(encode_bits(full)).values.size, 8)
        clock = SymbolClock(12000, time_start_s=-0.013, center_frequency_hz=-12_000_000)
        for order, width in ((4, 1), (1024, 2), (2**32, 4)):
            with self.subTest(order=order):
                original = SymbolSequence([order-1, 1], order, clock=clock)
                document = encode_symbols(original)
                raw = base64.b64decode(document['data_base64'])
                self.assertEqual(raw, (order-1).to_bytes(width, 'little') + (1).to_bytes(width, 'little'))
                restored = decode_symbols(document)
                np.testing.assert_array_equal(restored.labels, original.labels)
                self.assertEqual(restored.valid_bits, original.valid_bits)
                self.assertEqual(restored.clock, clock)
        self.assertIsNone(decode_symbols(encode_symbols(SymbolSequence([3], 4))).clock)

    def test_malformed_vectors_and_timing_are_rejected_before_publication(self):
        bits = encode_bits(BitSequence([1]))
        words = encode_symbols(SymbolSequence([3], 4))
        for data in (
            [], bits | {'schema': True}, bits | {'format': 'unknown'}, bits | {'length': 0},
            bits | {'data_base64': 'AB'}, bits | {'data_base64': '*A=='},
            bits | {'data_base64': 'gR=='}, bits | {'data_base64': 'gQ=='},  # surplus or noncanonical bits
            bits | {'data_base64': 'gIAA'}, bits | {'seed': -1},
        ):
            with self.subTest(data=data), self.assertRaises(ValueError):
                decode_bits(data)
        for data in (words | {'order': 3}, words | {'order': 2}, words | {'clock': '1200'},
                     words | {'clock': {'unknown': 1}}, words | {'valid_bits': 4}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                decode_symbols(data)
        budget = ExecutionContext(max_work_bytes=1)
        with self.assertRaises(ResourceLimitError):
            decode_bits(bits, budget)
        with self.assertRaises(ResourceLimitError):
            decode_symbols(words, budget)
        for function in (encode_bits, encode_symbols):
            with self.assertRaises(TypeError):
                function([0, 1])
        for spec in (None, {}, {'synchronization': 1}):
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                decode_experiment_spec(spec)

    def test_experiment_reopens_in_existing_json_and_slproj_sessions(self):
        result = run_experiment(ExperimentSpec(bit_count=145, seed=202, eb_n0_db=8,
                                               synchronization=SynchronizationSpec('estimated')))
        with TemporaryDirectory() as directory:
            for extension in ('.slproj', '.json'):
                with self.subTest(extension=extension):
                    path = Path(directory)/f'experiment{extension}'
                    identifier = save_experiment(path, result)
                    project, workspace = session.load(path)
                    restored = load_experiment(project, identifier)
                    self.assertEqual(restored.specification, result.specification)
                    self.assertEqual(restored.report['metrics'], result.report()['metrics'])
                    self.assertEqual(workspace, session.empty_workspace())
                    for role, signal in result.signals().items():
                        actual = project.get(restored.records[role])
                        np.testing.assert_array_equal(actual.values, signal.values)
                        self.assertEqual(actual.metadata['sample_rate_hz'], signal.metadata['sample_rate_hz'])
                    bits = decode_bits(project.get(restored.records['input_bits']))
                    np.testing.assert_array_equal(bits.values, result.input_bits.values)
                    labels = decode_symbols(project.get(restored.records['tx_labels']))
                    np.testing.assert_array_equal(labels.labels, result.transmitted_labels.labels)
                    # Project incorporation relocates IDs without invalidating signal or report hashes.
                    audit = Project()
                    mapping = audit.incorporate(project, root=identifier)
                    copied = Project.from_document(audit.document())
                    view = load_experiment(copied, mapping[identifier])
                    self.assertEqual(view.records['input_bits'], mapping[restored.records['input_bits']])

    def test_existing_project_remains_consistent_during_failed_delivery(self):
        project = Project()
        old = project.add(Signal([3, 4], origin=3))
        before = project.headers()
        result = run_experiment(ExperimentSpec(bit_count=80, eb_n0_db=None))
        with self.assertRaises(TypeError):
            store_experiment(None, result)
        with self.assertRaises(ResourceLimitError):
            store_experiment(project, result, ExecutionContext(max_work_bytes=1))
        with self.assertRaisesRegex(ValueError, 'informe'):
            store_experiment(project, replace(result, metrics=None))
        with self.assertRaisesRegex(ValueError, 'bits'):
            store_experiment(project, replace(result, input_bits=BitSequence(1-result.input_bits.values)))
        with self.assertRaisesRegex(ValueError, 'incompleto'):
            store_experiment(project, replace(result, signal_digests=()))
        result.transmitted.values[0] += 1
        with self.assertRaisesRegex(ValueError, 'cambió'):
            store_experiment(project, result)
        self.assertEqual(project.headers(), before)
        self.assertEqual(project.get(old).origin, 3)
        with self.assertRaisesRegex(ValueError, 'verificable'):
            load_experiment(project, old)

    def test_cancellation_before_commit_and_readable_unavailable_reports(self):
        event = Event()

        class CancelAtCommit(Project):
            @contextmanager
            def stage_records(self, *, before_commit):
                def interrupt():
                    event.set()
                    before_commit()
                with super().stage_records(before_commit=interrupt) as staged:
                    yield staged

        project = CancelAtCommit()
        result = run_experiment(ExperimentSpec(bit_count=16, eb_n0_db=None,
                                              pulse=PulseSpec('rectangular', 2, 1),
                                              synchronization=SynchronizationSpec('assisted', sample_offset=100)))
        with self.assertRaises(OperationCancelled):
            store_experiment(project, result, ExecutionContext(cancel=event))
        self.assertFalse(project.headers())
        project = Project.from_document({'format': 'signallab-project', 'schema_version': 1, 'records': []})
        identifier = store_experiment(project, result)
        stored = load_experiment(project, identifier)
        self.assertNotIn('observed', stored.records)
        self.assertNotIn('output_bits', stored.records)
        self.assertIsNone(stored.report['metrics'])
        self.assertEqual(stored.report['synchronization']['state'], 'unavailable')


if __name__ == '__main__':
    unittest.main()
