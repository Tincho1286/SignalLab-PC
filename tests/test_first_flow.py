"""Independent math and model regressions for the first implemented flow."""

import tempfile
import unittest
from pathlib import Path

import numpy as np

from signallab_pc.engine import ExpressionError, replace_sample, sequence_from_expression, sequence_from_values
from signallab_pc.storage import load_json, save_json


class FirstFlowTests(unittest.TestCase):
    def test_cosine_expression_against_known_values(self):
        signal = sequence_from_expression("cos(pi*x/4)", -2, 5)
        np.testing.assert_allclose(signal.values.real, [0, np.sqrt(0.5), 1, np.sqrt(0.5), 0], atol=1e-14)
        np.testing.assert_allclose(signal.values.imag, 0, atol=1e-14)
        np.testing.assert_array_equal(signal.axis, [-2, -1, 0, 1, 2])

    def test_complex_list_and_origin_are_retained(self):
        signal = sequence_from_values("1, 0, 1+2i, -3", -1)
        np.testing.assert_array_equal(signal.values, [1, 0, 1 + 2j, -3])
        np.testing.assert_array_equal(signal.axis, [-1, 0, 1, 2])

    def test_json_round_trip_preserves_complex_values_and_axis_metadata(self):
        original = sequence_from_values("1+2i, -3i", -2)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "signal.json"
            save_json(original, path)
            restored = load_json(path)
        np.testing.assert_array_equal(restored.values, original.values)
        np.testing.assert_array_equal(restored.axis, original.axis)
        self.assertEqual(restored.units, "n")

    def test_editing_sample_does_not_change_axis(self):
        signal = sequence_from_values("1, 0, -1", -2)
        edited = replace_sample(signal, 1, 2 + 3j)
        np.testing.assert_array_equal(edited.values, [1, 2 + 3j, -1])
        np.testing.assert_array_equal(edited.axis, [-2, -1, 0])

    def test_arbitrary_python_call_is_rejected(self):
        with self.assertRaises(ExpressionError):
            sequence_from_expression("__import__('os').system('whoami')", 0, 1)

    def test_discrete_signal_rejects_fractional_origin(self):
        from signallab_pc.model import Signal
        with self.assertRaises(ValueError):
            Signal(np.array([1]), 0.5, 1, "n")


if __name__ == "__main__":
    unittest.main()
