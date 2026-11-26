import json
import math
from pathlib import Path
from threading import Event
import unittest

import numpy as np
from scipy.stats import binom

from signallab_pc import jobs
from signallab_pc.communications_data import ConstellationSpec
from signallab_pc.communications_experiment import ExperimentSpec, coherent_monte_carlo, run_experiment
from signallab_pc.communications_modulation import parse_bits
from signallab_pc.communications_pulses import PulseSpec
from signallab_pc.communications_receiver import SynchronizationSpec
from signallab_pc.execution import ExecutionContext, ResourcePool
from signallab_pc.resources import ResourceLimitError


REFERENCE = json.loads((Path(__file__).resolve().parents[1] / 'docs' / 'engineering' /
                        'phase_03' / 'evidence' / 'analytical-reference-v1.json').read_text(encoding='utf-8'))


class CommunicationsExperimentTests(unittest.TestCase):
    def test_default_qpsk_experiment_preserves_samples_and_provenance(self):
        spec = ExperimentSpec(bit_count=333, seed=4917, symbol_rate_hz=4800, eb_n0_db=6)
        result = run_experiment(spec)
        repeated = run_experiment(spec)
        self.assertEqual(result.provenance, repeated.provenance)
        self.assertEqual(result.signal_digests, repeated.signal_digests)
        self.assertEqual(result.specification.constellation.order, 4)
        self.assertEqual(result.reception.synchronization.state, 'ideal')
        self.assertEqual(result.channel.specification.seed, result.provenance.stream_seeds[2])
        self.assertEqual(result.input_bits.seed, result.provenance.stream_seeds[0])
        self.assertEqual(len(set(result.provenance.stream_seeds)), 3)
        self.assertEqual(result.transmitted.metadata['sample_rate_hz'], 8*4800)
        self.assertEqual(result.metrics.ber.evaluated, 333)
        self.assertEqual(result.metrics.ser.evaluated, 167)
        self.assertEqual(result.metrics.excluded_padding_bits, 1)
        self.assertIsNone(result.metrics.ber.confidence)
        self.assertIsNone(result.metrics.ser.confidence)
        self.assertEqual(result.theoretical.ber_reference, 'exact')
        self.assertEqual(set(result.signals()), {'symbols', 'upsampled', 'tx', 'matched', 'awgn', 'observed'})
        for name in result.signals():
            np.testing.assert_array_equal(result.signals()[name].values, repeated.signals()[name].values)

    def test_manual_bits_and_pilot_chain_measure_only_payload(self):
        data = parse_bits('0010 1110 0011 0011 1110 0101 1011 1')
        config = ExperimentSpec(bit_count=data.values.size, seed=11, eb_n0_db=None,
                                pulse=PulseSpec('rrc', 5, 9, 0.35),
                                synchronization=SynchronizationSpec('estimated'),
                                pilot_symbols=31)
        result = run_experiment(config, bits=data)
        self.assertEqual(result.reception.synchronization.state, 'estimated')
        self.assertEqual(result.reception.synchronization.sample_offset, result.pulse.taps.size-1)
        self.assertAlmostEqual(result.reception.synchronization.phase_rad, 0, delta=0.01)
        self.assertIsNone(result.channel)
        self.assertIsNone(result.theoretical)
        self.assertEqual(result.provenance.source, 'supplied')
        self.assertIsNotNone(result.signals()['pilot'])
        self.assertEqual(result.metrics.transmitted_excluded_symbols, 31)
        self.assertEqual(result.metrics.received_excluded_symbols, 31)
        self.assertEqual(result.metrics.ber.evaluated, len(data.values))
        np.testing.assert_array_equal(result.received_bits.values, data.values)
        mutated = parse_bits('10' * (data.values.size//2) + '0')
        other = run_experiment(config, bits=mutated)
        self.assertEqual(result.provenance.settings_sha256, other.provenance.settings_sha256)
        self.assertNotEqual(result.provenance.input_bits_sha256, other.provenance.input_bits_sha256)

    def test_unavailable_synchronization_keeps_complete_diagnostics(self):
        config = ExperimentSpec(bit_count=300, seed=99, eb_n0_db=None, synchronization=SynchronizationSpec(
            'assisted', sample_offset=100_000,
        ))
        result = run_experiment(config)
        self.assertEqual(result.reception.synchronization.state, 'unavailable')
        self.assertIsNone(result.received_bits)
        self.assertIsNone(result.received_labels)
        self.assertIsNone(result.metrics)
        self.assertEqual(set(result.signals()), {'symbols', 'upsampled', 'tx', 'matched'})

    def test_monte_carlo_counts_are_compatible_with_probability_oracles(self):
        samples = 90_000
        antipodal = dict(REFERENCE['antipodal_ber'])
        for order, level, seed in ((2, 0, 191), (2, 4, 577), (4, 0, 901), (4, 4, 817)):
            with self.subTest(order=order, level=level):
                config = ConstellationSpec('psk', order, rotation_rad=math.pi/4)
                result = coherent_monte_carlo(config, level, samples, seed)
                ber = antipodal[level]
                ser = ber if order == 2 else ber*(2-ber)
                self.assertEqual(result.stopping_rule, 'fixed_symbol_count')
                self.assertIsNotNone(result.measured.ber.confidence)
                self.assertIsNotNone(result.measured.ser.confidence)
                for rate, probability in ((result.measured.ber, ber), (result.measured.ser, ser)):
                    lo, hi = binom.interval(0.999, rate.evaluated, probability)
                    self.assertLessEqual(lo, rate.errors)
                    self.assertLessEqual(rate.errors, hi)
        qam = coherent_monte_carlo(ConstellationSpec('qam', 16), 0, samples, seed=522)
        oracle = next(row for row in REFERENCE['square_qam_decision_probabilities']
                      if row['order'] == 16 and row['eb_n0_db'] == 0)
        self.assertIsNone(qam.measured.ber.confidence)
        self.assertIsNotNone(qam.measured.ser.confidence)
        lo, hi = binom.interval(0.999, samples, oracle['ser'])
        self.assertLessEqual(lo, qam.measured.ser.errors)
        self.assertLessEqual(qam.measured.ser.errors, hi)
        # Treat each symbol's erroneous bit fraction as one independent bounded observation.
        margin = math.sqrt(math.log(2/0.001)/(2*samples))
        self.assertAlmostEqual(qam.measured.ber.value, oracle['gray_ber'], delta=margin)

    def test_validation_limits_and_progress_during_worker_execution(self):
        for options in (
            {'bit_count': 0}, {'seed': -1}, {'allow_padding': 'yes'},
            {'allow_padding': False, 'bit_count': 101}, {'synchronization': SynchronizationSpec(sample_offset=1)},
            {'synchronization': 'ideal'}, {'pulse': 'rrc'}, {'pilot_symbols': 1},
        ):
            with self.subTest(options=options), self.assertRaises(ValueError):
                ExperimentSpec(**options)
        with self.assertRaises(TypeError):
            run_experiment(None)
        with self.assertRaises(TypeError):
            coherent_monte_carlo('QPSK', 0, 4, 42)
        request = ExperimentSpec(bit_count=1000)
        with self.assertRaises(ValueError):
            run_experiment(request, bits=parse_bits('01'))
        with self.assertRaises(ResourceLimitError):
            run_experiment(request, execution=ExecutionContext(max_work_bytes=1))
        with self.assertRaises(ValueError):
            run_experiment(ExperimentSpec(bit_count=2**60, pulse=PulseSpec('rrc', 32, 8)))
        event = Event()
        pool = ResourcePool(30_000_000)
        observed, local = [], []

        def progress(value):
            observed.append(value)
            if value >= 65:
                event.set()

        jobs.bind(event, progress)
        try:
            with self.assertRaises(jobs.OperationCancelled):
                run_experiment(request, execution=ExecutionContext(progress=local.append, pool=pool))
        finally:
            jobs.clear()
        self.assertTrue(observed)
        self.assertEqual(observed, sorted(observed))
        self.assertEqual(local, sorted(local))
        self.assertLess(observed[-1], 100)
        with pool.reserve(30_000_000):
            pass


if __name__ == '__main__':
    unittest.main()
