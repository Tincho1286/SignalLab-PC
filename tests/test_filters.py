import tempfile
import unittest
from pathlib import Path

import numpy as np

from signallab_pc.filters import Transfer, fir, biquad, rc, bilinear, from_poles_zeros
from signallab_pc.model import Signal
from signallab_pc.operations import even_odd_parts
from signallab_pc.storage import load_json, save_json


class FiltersTests(unittest.TestCase):
    def test_first_order_impulse_and_step_from_closed_form(self):
        system = Transfer([1], [1, -.5])
        n = np.arange(12)
        np.testing.assert_allclose(system.excitation_response(12).values, .5**n)
        np.testing.assert_allclose(system.excitation_response(12, "step").values, 2-.5**n)

    def test_nonunit_a0_and_complex_negative_origin(self):
        system = Transfer([2, 2], [2, -1])
        x = Signal([1j, 2, 0], origin=-3)
        result = system.apply(x)
        np.testing.assert_allclose(result.values, [1j, 2+1.5j, 3+.75j])
        self.assertEqual(result.origin, -3)

    def test_explicit_initial_history(self):
        result = Transfer([1], [1, -.5]).apply(Signal([0, 0, 0]), previous_outputs=[4])
        np.testing.assert_allclose(result.values, [2, 1, .5])

    def test_pure_delay_has_origin_pole_and_correct_phase(self):
        system = Transfer([0, 1], [1])
        zeros, poles = system.poles_zeros()
        self.assertEqual(zeros.size, 0)
        np.testing.assert_array_equal(poles, [0])
        w = np.array([0, .5, np.pi])
        np.testing.assert_allclose(system.response(w), np.exp(-1j*w), atol=1e-15)

    def test_exact_removable_zero_and_true_pole_are_distinct(self):
        w = np.array([0, 1e-4])
        np.testing.assert_allclose(Transfer([1, -1], [1, -1]).response(w), [1, 1])
        self.assertTrue(np.isnan(Transfer([1], [1, -1]).response(w)[0]))
        near = Transfer([1, -1+1e-12], [1, -1]).response(w)
        self.assertTrue(np.isnan(near[0]))
        self.assertTrue(np.isfinite(near[1]))

    def test_fir_matches_sinc_formula_without_gain_normalization(self):
        result = fir("lowpass", 3, .25, window="boxcar")
        np.testing.assert_allclose(result.b, [1/np.pi, .5, 1/np.pi])
        self.assertNotAlmostEqual(float(result.b.sum().real), 1)
        high = fir("highpass", 3, .25, window="boxcar")
        np.testing.assert_allclose(high.b + result.b, [0, 1, 0])

    def test_fir_has_no_hp_101_tap_cap_and_validates_parity(self):
        self.assertEqual(len(fir("lowpass", 1001, .1).b), 1001)
        with self.assertRaises(ValueError):
            fir("highpass", 100, .1)

    def test_biquad_peak_gain_is_q_for_hp_bandpass_convention(self):
        q, f0 = 2.0, .125
        response = biquad("bandpass", f0, q).response(np.array([2*np.pi*f0]))
        self.assertAlmostEqual(abs(response[0]), q)
        self.assertAlmostEqual(abs(biquad("lowpass", f0, q).response(np.array([0]))[0]), 1)

    def test_rc_corner_and_bilinear_exact_example(self):
        system = rc("lowpass", 1000, .001)
        np.testing.assert_allclose(system.response(np.array([0, 1])), [1, .5-.5j])
        converted = bilinear(system, 1)
        np.testing.assert_allclose(converted.b, [1/3, 1/3])
        np.testing.assert_allclose(converted.a, [1, -1/3])

    def test_pole_zero_design_keeps_relative_degree_and_stability(self):
        system = from_poles_zeros([], [.5], 2)
        np.testing.assert_allclose(system.b, [0, 2])
        np.testing.assert_allclose(system.excitation_response(4).values, [0, 2, 1, .5])
        self.assertTrue(system.stability().startswith("Estable"))
        self.assertTrue(Transfer([1], [1, -1.1]).stability().startswith("Inestable"))

    def test_even_odd_for_asymmetric_support(self):
        even, odd = even_odd_parts(Signal([1, 2, 3], origin=2))
        n = even.axis
        x = np.where(n == 2, 1, np.where(n == 3, 2, np.where(n == 4, 3, 0)))
        np.testing.assert_allclose(even.values + odd.values, x)
        np.testing.assert_allclose(even.values, even.values[::-1])
        np.testing.assert_allclose(odd.values, -odd.values[::-1])

    def test_json_retains_int64_origin_beyond_float_exact_range(self):
        original = Signal([1, 2], origin=2**53+1)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"signal.json"
            save_json(original, path)
            restored = load_json(path)
        self.assertEqual(restored.origin, original.origin)
        np.testing.assert_array_equal(restored.axis, original.axis)


if __name__ == "__main__":
    unittest.main()
