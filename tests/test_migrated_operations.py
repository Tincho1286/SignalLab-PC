import unittest
from unittest.mock import patch

import numpy as np

from signallab_pc.engine import sequence_from_values, sequence_from_expression
from signallab_pc.operations import (
    add_sequences, dft, even_odd_parts, finite_measures, idft,
    linear_convolution, linear_correlation, reverse, scale_amplitude, shift,
)
from signallab_pc.resources import ResourceLimitError, ensure_working_set


class MigratedOperationsTests(unittest.TestCase):
    def sig(self, values, origin=0):
        return sequence_from_values(values, origin)

    def test_convolution_preserves_negative_start_index(self):
        result = linear_convolution(self.sig("1,2", -2), self.sig("1,1", 1))
        np.testing.assert_array_equal(result.values, [1, 3, 2])
        np.testing.assert_array_equal(result.axis, [-1, 0, 1])

    def test_complex_correlation_matches_definition(self):
        x = self.sig("1+1i, 2-i", -1)
        h = self.sig("2i, 1", 2)
        result = linear_correlation(x, h)
        lag_start = int(x.origin) - int(h.origin) - len(h.values) + 1
        lag_stop = int(x.origin) + len(x.values) - int(h.origin)
        expected = []
        for lag in range(lag_start, lag_stop):
            total = 0j
            for j, xv in enumerate(x.values):
                n = int(x.origin) + j
                hi = n - lag - int(h.origin)
                if 0 <= hi < len(h.values):
                    total += xv * np.conjugate(h.values[hi])
            expected.append(total)
        np.testing.assert_allclose(result.values, expected, atol=1e-13)
        self.assertEqual(result.origin, lag_start)

    def test_finite_energy_power_rms_use_complex_magnitude(self):
        measure = finite_measures(self.sig("3+4i, 0"))
        self.assertEqual(measure.energy, 25)
        self.assertEqual(measure.average_power, 12.5)
        self.assertAlmostEqual(measure.rms, np.sqrt(12.5))

    def test_even_and_odd_parts_reconstruct_original_support(self):
        even, odd = even_odd_parts(self.sig("1,2,3", -1))
        np.testing.assert_array_equal(even.values, [2, 2, 2])
        np.testing.assert_array_equal(odd.values, [-1, 0, 1])
        np.testing.assert_array_equal(even.values + odd.values, [1, 2, 3])
        self.assertEqual(even.origin, -1)

    def test_shift_and_time_reversal_update_integer_axis(self):
        original = self.sig("1,2,3", -1)
        self.assertEqual(shift(original, 4).origin, 3)
        reversed_signal = reverse(original)
        self.assertEqual(reversed_signal.origin, -1)
        np.testing.assert_array_equal(reversed_signal.values, [3, 2, 1])

    def test_complex_scaling_preserves_domain_and_metadata(self):
        original = self.sig("1,2", -2)
        scaled = scale_amplitude(original, 1j)
        np.testing.assert_array_equal(scaled.values, [1j, 2j])
        self.assertEqual(scaled.axis.tolist(), [-2, -1])

    def test_energy_overflow_is_reported(self):
        huge = self.sig("1e308")
        with self.assertRaises(FloatingPointError):
            finite_measures(huge)

    def test_dft_and_idft_use_signal_lab_normalization(self):
        x = self.sig("1,2,3,4")
        spectrum = dft(x)
        np.testing.assert_allclose(spectrum.values, [10, -2+2j, -2, -2-2j], atol=1e-13)
        self.assertIn("no forward normalization", spectrum.metadata["convention"])
        np.testing.assert_allclose(idft(spectrum).values, x.values, atol=1e-13)

    def test_dft_length_change_is_explicit_and_does_not_mutate_input(self):
        x = self.sig("1,2,3")
        padded = dft(x, 4)
        self.assertEqual(padded.metadata["input_action"], "zero padded")
        self.assertEqual(len(x.values), 3)
        self.assertEqual(len(padded.values), 4)
        self.assertEqual(dft(x, 2).metadata["input_action"], "truncated at N")

    def test_sum_aligns_samples_by_integer_index(self):
        result = add_sequences(self.sig("1,2", -1), self.sig("10,20", 0))
        np.testing.assert_array_equal(result.values, [1, 12, 20])
        np.testing.assert_array_equal(result.axis, [-1, 0, 1])

    def test_memory_policy_scales_with_available_memory(self):
        self.assertEqual(ensure_working_set(5, live_arrays=4, available_bytes=1000), 320)
        with self.assertRaises(ResourceLimitError):
            ensure_working_set(6, live_arrays=4, available_bytes=1000)

    def test_expression_count_exceeds_old_calculator_cap(self):
        with patch("signallab_pc.engine.ensure_working_set", return_value=0):
            signal = sequence_from_expression("0", 0, 1_000_001)
        self.assertEqual(signal.values.size, 1_000_001)


if __name__ == "__main__":
    unittest.main()
