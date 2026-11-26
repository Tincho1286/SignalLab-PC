import math
from threading import Event
import unittest

import numpy as np
from scipy.stats import kstest, rayleigh, rice, uniform

from signallab_pc.communications_fading import FadingPath, FadingSpec, apply_fading, parse_fading_path
from signallab_pc.execution import ExecutionContext
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.resources import ResourceLimitError


class FadingContracts(unittest.TestCase):
    def test_iid_envelope_phase_and_power_against_distributions(self):
        signal = Signal(np.ones(32_768))
        power, phase = 2.7, -0.82
        for ratio in (0, 4):
            with self.subTest(K=ratio):
                path = FadingPath(average_power=power, k_linear=ratio, los_phase_rad=phase)
                part, = apply_fading(signal, FadingSpec((path,), 70123)).realizations
                values = part.coefficients.values
                sigma = math.sqrt(power/(2*(1+ratio)))
                law = rayleigh(scale=sigma) if ratio == 0 else rice(math.sqrt(2*ratio), scale=sigma)
                self.assertLess(kstest(abs(values), law.cdf).statistic, 0.015)
                if ratio == 0:
                    self.assertLess(kstest(np.angle(values), uniform(-math.pi, math.tau).cdf).statistic, 0.015)
                expected_mean = math.sqrt(power*ratio/(1+ratio))*np.exp(1j*phase)
                self.assertLess(abs(values.mean() - expected_mean), 0.03*math.sqrt(power))
                self.assertLess(abs(float(np.mean(abs(values)**2)) - power), 0.04*power)
                self.assertAlmostEqual(part.statistics.expected_power, power)
                self.assertAlmostEqual(part.statistics.observed_power, float(np.mean(abs(values)**2)))

    def test_rician_limits_and_linear_db_conversion(self):
        source = Signal(np.ones(128))
        rayleigh_spec = FadingSpec((FadingPath(),), 42)
        k_zero = FadingSpec((FadingPath(los_phase_rad=2.1, k_linear=0),), 42)
        np.testing.assert_array_equal(apply_fading(source, rayleigh_spec).signal.values,
                                      apply_fading(source, k_zero).signal.values)
        dominant = FadingPath.from_k_db(200, average_power=4, los_phase_rad=math.pi/2)
        self.assertAlmostEqual(dominant.k_linear/1e20, 1)
        los = apply_fading(source, FadingSpec((dominant,), 42))
        np.testing.assert_allclose(los.signal.values, np.full(128, 2j), rtol=0, atol=1e-9)
        self.assertEqual(parse_fading_path('4 = 1/2, 10, pi/4', k_scale='db'),
                         FadingPath(4, 0.5, 10, math.pi/4))
        self.assertEqual(parse_fading_path('0=1', k_scale='db'), FadingPath())

    def test_multipath_realizations_reconstruct_the_output_and_preserve_arrival_clock(self):
        source = Signal([1+2j, -2j, -3], origin=-3, metadata={'sample_rate_hz': 8, 'time_start_s': 0.25})
        configuration = FadingSpec((FadingPath(0), FadingPath(1, .2, 1), FadingPath(1, .1)), 88)
        result = apply_fading(source, configuration)
        np.testing.assert_array_equal(result.signal.axis, [-3, -2, -1, 0])
        expected = np.zeros(4, dtype=complex)
        for index, part in enumerate(result.realizations):
            d = part.path.delay_samples
            self.assertEqual(part.coefficients.origin, -3 + d)
            self.assertEqual(part.coefficients.metadata['time_start_s'], .25 + d/8)
            self.assertEqual(part.coefficients.metadata['spawn_key'], [index])
            expected[d:d+3] += source.values * part.coefficients.values
        np.testing.assert_array_equal(result.signal.values, expected)
        repeat = apply_fading(source, configuration)
        np.testing.assert_array_equal(result.signal.values, repeat.signal.values)
        different = apply_fading(source, FadingSpec(configuration.paths, 87))
        self.assertFalse(np.array_equal(result.signal.values, different.signal.values))
        longest = Signal(np.ones(4096))
        first, second = apply_fading(longest, FadingSpec((FadingPath(), FadingPath()), 88)).realizations
        covariance = np.mean(np.conjugate(first.coefficients.values)*second.coefficients.values)
        self.assertLess(abs(covariance), .05)

    def test_fading_rejects_invalid_parameters_and_cancels_before_delivery(self):
        with self.assertRaisesRegex(ValueError, 'potencia'):
            FadingPath(average_power=-1)
        with self.assertRaisesRegex(ValueError, 'factor K'):
            FadingPath.from_k_db(1e4)
        with self.assertRaisesRegex(ValueError, 'factor K'):
            FadingPath.from_k_db(-1e4)
        with self.assertRaisesRegex(ValueError, 'trayectoria'):
            FadingSpec((), 1)
        spec = FadingSpec((FadingPath(1),), 3)
        source = Signal(np.ones(140_000))
        with self.assertRaises(ResourceLimitError):
            apply_fading(source, spec, ExecutionContext(max_work_bytes=1024))
        event = Event()

        def stop(percentage):
            if percentage > 20:
                event.set()

        with self.assertRaises(OperationCancelled):
            apply_fading(source, spec, ExecutionContext(cancel=event, progress=stop))
        self.assertTrue(event.is_set())
        zero = apply_fading(Signal([1, -2j]), FadingSpec((FadingPath(1, 0),), 3))
        np.testing.assert_array_equal(zero.signal.values, np.zeros(3))
        self.assertEqual(zero.realizations[0].statistics.observed_power, 0)
