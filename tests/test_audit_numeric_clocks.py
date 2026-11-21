from decimal import Decimal
import math
import tempfile
from pathlib import Path
import unittest

import numpy as np

from signallab_pc.model import Signal
from signallab_pc.operations import (
    add_sequences, correlation, finite_measures, linear_convolution, shift,
)
from signallab_pc.random_cross_correlation import cross_correlation
from signallab_pc.random_signals import autocorrelation, statistics
from signallab_pc.sampling import resample, resample_rational
from signallab_pc.signal_combinations import sum_signals
from signallab_pc.storage import load_csv
from signallab_pc.windowing import multiply_signals


class CalculationScaleTests(unittest.TestCase):
    def test_rms_is_representable_even_when_its_square_is_not(self):
        measured = statistics(Signal([1e-200]*4), 'real', 4)
        self.assertEqual(measured['rms'], 1e-200)
        self.assertEqual(measured['range_status']['mean_square'], 'underflow')
        self.assertEqual(measured['range_status']['variance_N'], 'ok')
        self.assertEqual(measured['variance_N'], 0)
        zero = statistics(Signal([0]), 'real', 3)
        self.assertEqual(zero['range_status']['mean_square'], 'ok')
        self.assertEqual(zero['range_status']['variance_N_minus_1'], 'undefined')
        self.assertEqual(zero['rms'], 0)

    def test_centering_keeps_small_imaginary_variation_and_mean_residual(self):
        signal = Signal([complex(1e200,1), complex(1e200,-1)])
        measured = statistics(signal, 'real', 4, histogram_notice='Sin histograma')
        self.assertEqual(measured['variance_N'], 1)
        self.assertEqual(measured['variance_N_minus_1'], 2)
        self.assertEqual(measured['range_status']['mean_square'], 'overflow')
        self.assertEqual(measured['rms'], 1e200)
        self.assertEqual(statistics(Signal([1e200, 1, -1e200]), 'real', 4)['mean_real'], 1/3)
        np.testing.assert_array_equal(autocorrelation(signal, 1, True).values, [-.5, 1, -.5])

    def test_square_sum_rounds_into_subnormal_range_last(self):
        value = 1e-162
        expected = float(Decimal.from_float(value)**2 * 10000)
        for item in (Signal([value]*10000),
                     Signal([value]*10001, 0, -1, 's', domain='continuous')):
            with self.subTest(domain=item.domain):
                measured = finite_measures(item)
                self.assertGreater(measured.energy, 0)
                self.assertLessEqual(abs(measured.energy-expected), math.ulp(expected))
                self.assertLessEqual(abs(measured.rms-value), math.ulp(value))
                self.assertEqual(measured.power_status, 'underflow')
        narrow = finite_measures(Signal([3+4j, -3-4j], 0, 2, 's', domain='continuous'))
        self.assertAlmostEqual(narrow.energy, 50/3)

    def test_normalized_correlation_accepts_subnormal_input(self):
        minimum = math.ulp(0.)
        first = Signal([minimum, -minimum])
        for measured in (correlation(first, normalization='energy'),
                         cross_correlation(first,first,1,normalize=True)):
            np.testing.assert_allclose(measured.values, [-.5, 1, -.5], atol=0, rtol=1e-14)


class AxisAndClockTests(unittest.TestCase):
    def test_grid_rejects_interior_collisions_both_directions(self):
        for domain in ('continuous', 'frequency'):
            for direction in (1, -1):
                with self.subTest(domain=domain, direction=direction):
                    with self.assertRaisesRegex(ValueError, 'distinguir'):
                        Signal(np.ones(5), direction*2**53, direction*1.5, domain=domain)
                    record = Signal(np.ones(5), direction*2**53, direction*2., domain=domain)
                    np.testing.assert_array_equal(np.diff(record.axis), 2*direction)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'data.csv'
            path.write_text('x\n1\n2\n3\n4\n5\n', encoding='utf-8')
            with self.assertRaises(ValueError):
                load_csv(path, domain='continuous', origin=2**53, step=1.5, axis_column=None, real_column=0)

    def test_sum_and_product_have_one_alignment_rule(self):
        x = Signal([1,2,3,4], -2, expression='n', metadata={'sample_rate_hz':4, 'time_start_s':2.5})
        valid = Signal([10,20], 1, metadata={'sample_rate_hz':4, 'time_start_s':3.25})
        for operation in (add_sequences, sum_signals, multiply_signals):
            with self.subTest(operation=operation.__name__):
                result = operation(x, valid)
                self.assertEqual(result.origin, -2)
                self.assertEqual(result.metadata['sample_rate_hz'], 4)
                self.assertEqual(result.metadata['time_start_s'], 2.5)
                self.assertEqual(result.expression, '')
                for clock in ({'sample_rate_hz':8}, {'sample_rate_hz':4,'time_start_s':3.5}):
                    with self.assertRaises(ValueError):
                        operation(x, valid.copy_with(metadata=clock))
        first = Signal([1], metadata={'sample_rate_hz':.5, 'time_start_s':2**53})
        second = Signal([2], metadata={'sample_rate_hz':.5, 'time_start_s':2**53+2})
        with self.assertRaisesRegex(ValueError, 'mismos índices'):
            add_sequences(first, second)
        np.testing.assert_array_equal(add_sequences(x,valid).values, [1,2,3,14,20])
        np.testing.assert_array_equal(multiply_signals(x,valid).values, [0,0,0,40])

    def test_partial_clocks_and_lag_origins_keep_their_meaning(self):
        x = Signal([1,2], -2, metadata={'sample_rate_hz':4,'time_start_s':2.5})
        h = Signal([2,1], 1, metadata={'sample_rate_hz':4,'time_start_s':3.25})
        bare = Signal([1])
        passive = h.copy_with(metadata={'sample_rate_hz':4})
        for operation in (add_sequences, linear_convolution, correlation):
            self.assertNotIn('sample_rate_hz', operation(x,bare).metadata)
            self.assertNotIn('time_start_s', operation(x,passive).metadata)
        self.assertEqual(multiply_signals(x, bare).metadata['time_start_s'], 2.5)
        self.assertNotIn('sample_rate_hz', multiply_signals(bare,x).metadata)
        self.assertEqual(linear_convolution(x,h).metadata['time_start_s'], 5.75)
        self.assertEqual(correlation(x,h).origin, -4)
        self.assertEqual(correlation(x,h).metadata['time_start_s'], -1.)
        for signal in (shift(passive,2), resample_rational(passive,2,1)):
            self.assertNotIn('time_start_s', signal.metadata)
        sampled = resample(x,2,'decimate',1)
        self.assertEqual((sampled.origin,sampled.metadata['time_start_s']), (0,2.75))
        self.assertEqual(resample_rational(sampled,2,1).metadata['time_start_s'], 2.75)
        estimated = cross_correlation(x, h.copy_with(values=[3,4],origin=-2, metadata=x.metadata), 1)
        self.assertEqual(estimated.metadata['time_start_s'], -.25)
        self.assertEqual(autocorrelation(passive,1).metadata['time_start_s'], -.25)
