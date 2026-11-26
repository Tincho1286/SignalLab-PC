import json
import math
from pathlib import Path
from threading import Event
import unittest

import numpy as np
from scipy.stats import binom

from signallab_pc.communications_data import ConstellationSpec, SymbolSequence
from signallab_pc.communications_metrics import QualitySpec, error_rate, measure_quality, theoretical_error
from signallab_pc.execution import ExecutionContext
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.resources import ResourceLimitError


REFERENCE = json.loads((Path(__file__).resolve().parents[1] / 'docs' / 'engineering' /
                        'phase_03' / 'evidence' / 'analytical-reference-v1.json').read_text(encoding='utf-8'))


class CommunicationsMetricsTests(unittest.TestCase):
    def test_aligned_metrics_use_hamming_counts_and_complex_reference(self):
        tx = SymbolSequence([7, 3, 12], 16, valid_bits=10)
        rx = SymbolSequence([13, 3, 10], 16, valid_bits=10)
        ideal = Signal([98, 1+1j, -1], name='Referencia', metadata={'amplitude_units': 'V'})
        observed = Signal([999, 1+1.25j, -0.5], metadata={'amplitude_units': 'V'})
        result = measure_quality(tx, rx, reference=ideal, observation=observed, spec=QualitySpec(1, 1, 2))
        self.assertEqual((result.ber.errors, result.ber.evaluated, result.ber.value), (1, 6, 1/6))
        self.assertEqual((result.ser.errors, result.ser.evaluated, result.ser.value), (1, 2, 0.5))
        self.assertEqual(result.transmitted_excluded_symbols, 1)
        self.assertEqual(result.received_excluded_symbols, 1)
        self.assertEqual(result.excluded_padding_bits, 2)
        self.assertEqual(result.evm.status, 'measured')
        evm = math.sqrt((0.25**2+0.5**2)/(2+1))
        self.assertAlmostEqual(result.evm.rms, evm)
        self.assertAlmostEqual(result.evm.percent, evm*100)
        self.assertAlmostEqual(result.evm.db, 20*math.log10(evm))
        self.assertEqual(result.evm.reference_name, 'Referencia')
        self.assertEqual(result.evm.amplitude_units, 'V')

    def test_padding_only_errors_affect_ser_but_not_useful_ber(self):
        tx = SymbolSequence([7, 12], 16, 6)
        rx = SymbolSequence([7, 13], 16, 6)
        result = measure_quality(tx, rx)
        self.assertEqual(result.ber.errors, 0)
        self.assertEqual(result.ber.evidence, 'zero_observed')
        self.assertIsNone(result.ber.confidence)
        self.assertEqual(result.ser.errors, 1)
        self.assertEqual(result.evm.status, 'reference_unavailable')

    def test_evm_status_and_overflow_resistant_ratio(self):
        labels = SymbolSequence([1], 2)

        def evm(ref, obs):
            return measure_quality(labels, labels, reference=Signal([ref]), observation=Signal([obs])).evm

        self.assertEqual(evm(0, 0).status, 'zero_reference')
        perfect = evm(1+1j, 1+1j)
        self.assertEqual((perfect.status, perfect.rms, perfect.db), ('perfect', 0.0, None))
        huge = evm(-1.7e308, 1.7e308)
        self.assertEqual(huge.status, 'measured')
        self.assertAlmostEqual(huge.rms, 2, delta=1e-12)
        tiny = evm(1, 1+1e-300j)
        self.assertEqual(tiny.status, 'measured')
        self.assertAlmostEqual(tiny.rms/1e-300, 1)
        self.assertAlmostEqual(tiny.db, -6000.0)
        extreme = evm(math.ulp(0.0), 1.7e308)
        self.assertEqual(extreme.status, 'numerical_range')
        self.assertIsNone(extreme.rms)
        self.assertTrue(math.isfinite(extreme.db))

    def test_exact_confidence_intervals_by_binomial_tail(self):
        sample = 142
        zero = error_rate(0, sample, independent=True, confidence=0.95)
        self.assertEqual(zero.confidence.method, 'exact_upper_bound')
        self.assertEqual(zero.confidence.lower, 0)
        self.assertAlmostEqual(binom.pmf(0, sample, zero.confidence.upper), 0.05)
        estimate = error_rate(7, sample, independent=True)
        bounds = estimate.confidence
        self.assertEqual(bounds.method, 'clopper_pearson')
        self.assertAlmostEqual(binom.cdf(7, sample, bounds.upper), 0.025)
        self.assertAlmostEqual(binom.sf(6, sample, bounds.lower), 0.025)
        self.assertEqual(error_rate(sample, sample, independent=True).confidence.upper, 1)
        self.assertEqual(error_rate(sample, sample).evidence, 'observed')
        self.assertEqual(error_rate(29, sample).evidence, 'few_errors')
        with self.assertRaises(ValueError):
            error_rate(143, sample)
        with self.assertRaises(ValueError):
            error_rate(7, sample, independent=True, confidence=1)
        labels = SymbolSequence([0, 1], 2)
        result = measure_quality(labels, labels, spec=QualitySpec(independent_bits=True, independent_symbols=True))
        self.assertEqual(result.ber.confidence, result.ser.confidence)

    def test_theory_matches_antipodal_quadrature_and_qam_decision_integral(self):
        for db, ber in REFERENCE['antipodal_ber']:
            bpsk = theoretical_error(ConstellationSpec('psk', 2), db)
            qpsk = theoretical_error(ConstellationSpec('psk', 4, rotation_rad=math.pi/4), db)
            natural = theoretical_error(ConstellationSpec('psk', 4, 'natural'), db)
            self.assertAlmostEqual(bpsk.ber, ber, delta=2e-15)
            self.assertEqual(bpsk.ser, bpsk.ber)
            self.assertEqual(qpsk.ber, bpsk.ber)
            self.assertAlmostEqual(qpsk.ser, ber*(2-ber), delta=2e-15)
            independent_axis = ber*(1-ber)
            self.assertAlmostEqual(natural.ber, (3*independent_axis + ber**2)/2, delta=2e-15)
        for row in REFERENCE['square_qam_decision_probabilities']:
            order, db = row['order'], row['eb_n0_db']
            with self.subTest(order=order, db=db):
                result = theoretical_error(ConstellationSpec('qam', order), db)
                self.assertAlmostEqual(result.ser, row['ser'], delta=2e-15)
                self.assertEqual(result.ser_reference, 'exact')
                if order == 4:
                    self.assertEqual(result.ber_reference, 'exact')
                    self.assertAlmostEqual(result.ber, row['gray_ber'], delta=2e-15)
                else:
                    self.assertEqual(result.ber_reference, 'gray_nearest_neighbors')
                    if order == 256 and db == 0:
                        self.assertGreater(abs(result.ber-row['gray_ber']), 0.07)
                    if db == 12 and order <= 64:
                        self.assertAlmostEqual(result.ber, row['gray_ber'], delta=2e-10)
        self.assertIsNone(theoretical_error(ConstellationSpec('qam', 16, 'natural'), 0).ber)
        self.assertIsNone(theoretical_error(ConstellationSpec('psk', 8), 0).ser)
        self.assertEqual(theoretical_error(ConstellationSpec('psk', 2), 1e308).ber, 0)
        self.assertEqual(theoretical_error(ConstellationSpec('psk', 2), -1e308).ber, 0.5)
        with self.assertRaises(TypeError):
            theoretical_error('QPSK', 0)

    def test_invalid_alignment_reference_and_resource_paths_fail_cleanly(self):
        tx = SymbolSequence([0, 3, 3], 4, 6)
        rx = SymbolSequence([0, 3, 3], 4, 5)
        for kwargs in ({'confidence': 1}, {'independent_bits': 1}, {'transmitted_start': -1}, {'symbol_count': 0}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                QualitySpec(**kwargs)
        with self.assertRaises(TypeError):
            measure_quality('bits', rx)
        with self.assertRaises(TypeError):
            measure_quality(tx, tx, spec='automatic')
        with self.assertRaises(ValueError):
            measure_quality(tx, SymbolSequence([0, 1], 2))
        with self.assertRaisesRegex(ValueError, 'distinta'):
            measure_quality(tx, rx)
        with self.assertRaisesRegex(ValueError, 'cuántos'):
            measure_quality(tx, tx, spec=QualitySpec(1, 0))
        with self.assertRaisesRegex(ValueError, 'excede'):
            measure_quality(tx, tx, spec=QualitySpec(symbol_count=4))
        ref = Signal([1, 0, -1], metadata={'amplitude_units': 'V'})
        with self.assertRaisesRegex(ValueError, 'observado'):
            measure_quality(tx, tx, reference=ref)
        with self.assertRaisesRegex(ValueError, 'unidades'):
            measure_quality(tx, tx, reference=ref, observation=ref.copy_with(metadata={'amplitude_units': 'mV'}))
        with self.assertRaisesRegex(ValueError, 'observación'):
            measure_quality(tx, tx, reference=ref, observation=Signal([1, 2]))
        with self.assertRaisesRegex(ValueError, 'discreto'):
            measure_quality(tx, tx, reference=ref, observation=Signal([1, 2, 3], domain='frequency'))
        bad = Signal([1, 2, 3])
        bad.values[0] = np.nan
        with self.assertRaisesRegex(ValueError, 'finitas'):
            measure_quality(tx, tx, reference=ref, observation=bad)
        with self.assertRaises(ResourceLimitError):
            measure_quality(tx, tx, execution=ExecutionContext(max_work_bytes=1))

    def test_cancellation_and_changes_in_reference_are_detected(self):
        labels = SymbolSequence([0, 1, 1], 2)
        x = Signal([1, 2, 3])
        event = Event()

        def cancel(progress):
            if progress == 100:
                event.set()

        with self.assertRaises(OperationCancelled):
            measure_quality(labels, labels, reference=x, observation=x,
                            execution=ExecutionContext(cancel=event, progress=cancel))

        def mutate(progress):
            if progress == 100:
                x.values[0] *= -1

        with self.assertRaisesRegex(ValueError, 'cambió'):
            measure_quality(labels, labels, reference=x, observation=x,
                            execution=ExecutionContext(progress=mutate))


if __name__ == '__main__':
    unittest.main()
