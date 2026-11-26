import math
from threading import Event
import unittest

import numpy as np

from signallab_pc.communications_impairments import (
    IQImbalance, PhaseNoiseSpec, TimingOffset, apply_iq_imbalance, apply_phase_noise, apply_timing_offset,
)
from signallab_pc.communications_receiver import SynchronizationSpec, recover_symbols
from signallab_pc.execution import ExecutionContext
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.resources import ResourceLimitError


class ImpairmentContracts(unittest.TestCase):
    def test_integer_offsets_keep_receiver_window_and_fill_exposed_edges(self):
        source = Signal([1, 2j, -3, 4], -2, metadata={'sample_rate_hz': 1000, 'time_start_s': 0.4})
        for delay, samples in ((2, [0, 0, 1, 2j]), (-2, [-3, 4, 0, 0]), (8, [0, 0, 0, 0])):
            result = apply_timing_offset(source, TimingOffset(delay))
            np.testing.assert_array_equal(result.values, samples)
            np.testing.assert_array_equal(result.axis, source.axis)
            self.assertEqual(result.metadata['time_start_s'], 0.4)
        np.testing.assert_array_equal(apply_timing_offset(source, TimingOffset()).values, source.values)

    def test_sfo_and_fractional_delay_match_analytical_tone_and_preserve_symbol_rate(self):
        k = np.arange(8192)
        omega, rate = math.pi/5, 8000
        source = Signal(np.exp(1j*omega*k), origin=-20,
                        metadata={'sample_rate_hz': rate, 'time_start_s': -0.1, 'samples_per_symbol': 8})
        for ppm in (250, -250, .1):
            with self.subTest(ppm=ppm):
                ratio = 1 + ppm/1e6
                result = apply_timing_offset(source, TimingOffset(.375, ppm))
                ideal = np.exp(1j*omega*(k/ratio-.375))
                self.assertLess(float(np.max(abs(result.values[64:-64] - ideal[64:-64]))), .002)
                np.testing.assert_array_equal(result.axis, source.axis)
                self.assertEqual(result.metadata['time_start_s'], -0.1)
                self.assertAlmostEqual(result.metadata['sample_rate_hz'], rate*ratio)
                self.assertEqual(result.metadata['symbol_rate_hz'], 1000)
                self.assertNotIn('samples_per_symbol', result.metadata)
                with self.assertRaisesRegex(ValueError, 'incompatibles'):
                    recover_symbols(result, 8, 8, SynchronizationSpec())
        shifted = apply_timing_offset(Signal(source.values), TimingOffset(-.25))
        np.testing.assert_allclose(shifted.values[64:-64], np.exp(1j*omega*(k[64:-64]+.25)), rtol=0, atol=.002)

    def test_resampling_rejects_out_of_band_tone_and_invalid_clock_or_budget(self):
        count, rate = 4096, 4096
        k = np.arange(count)
        pass_tone, alias_tone = np.exp(.1j*np.pi*k), np.exp(.8j*np.pi*k)
        # A large rate error exercises the anti-alias kernel as well as fractional timing.
        source = Signal(pass_tone + alias_tone, metadata={'sample_rate_hz': rate})
        result = apply_timing_offset(source, TimingOffset(.125, -5e5))
        interior = slice(64, 1900)
        expected = np.exp(.1j*np.pi*(2*k[interior]-.125))
        self.assertLess(float(np.max(abs(result.values[interior] - expected))), .002)
        with self.assertRaisesRegex(ValueError, 'muestreo'):
            apply_timing_offset(Signal([1, 2]), TimingOffset(0, 1))
        with self.assertRaisesRegex(ValueError, 'tasa de salida'):
            TimingOffset(0, -1e6)
        with self.assertRaises(ResourceLimitError):
            apply_timing_offset(source, TimingOffset(.125), ExecutionContext(max_work_bytes=1024))
        cancel = Event()

        def stop(progress):
            if progress > 10:
                cancel.set()

        with self.assertRaises(OperationCancelled):
            apply_timing_offset(source, TimingOffset(.125), ExecutionContext(cancel=cancel, progress=stop))

    def test_phase_noise_increment_variance_reproduction_and_identity(self):
        rate, linewidth = 8000, 16
        source = Signal(np.full(65536, 1j), origin=-10, metadata={'sample_rate_hz': rate, 'time_start_s': 0.2})
        spec = PhaseNoiseSpec(linewidth, 673)
        result = apply_phase_noise(source, spec)
        expected = math.tau*linewidth/rate
        self.assertAlmostEqual(result.step_variance_rad2, expected)
        increments = np.diff(result.phase.values.real)
        self.assertLess(abs(np.var(increments)/expected - 1), .03)
        np.testing.assert_allclose(abs(result.signal.values), 1, rtol=0, atol=3e-15)
        self.assertEqual(result.phase.metadata['time_start_s'], 0.2)
        self.assertEqual(result.phase.metadata['amplitude_units'], 'rad')
        self.assertEqual(result.phase.values[0], 0)
        np.testing.assert_array_equal(result.phase.values, apply_phase_noise(source, spec).phase.values)
        np.testing.assert_array_equal(apply_phase_noise(Signal([1, 2j]), PhaseNoiseSpec(0, 7)).signal.values, [1, 2j])
        with self.assertRaisesRegex(ValueError, 'muestreo'):
            apply_phase_noise(Signal([1]), spec)

    def test_iq_image_and_dc_match_independent_complex_projections(self):
        tone = np.exp(1j*math.tau*19*np.arange(128)/128)
        source = Signal(tone, origin=4, metadata={'amplitude_units': 'V'})
        spec = IQImbalance(20*math.log10(1.25), .23, .025, -.07)
        result = apply_iq_imbalance(source, spec)
        desired = np.vdot(tone, result.signal.values)/len(tone)
        image = np.vdot(np.conjugate(tone), result.signal.values)/len(tone)
        self.assertAlmostEqual(desired, complex(result.statistics.desired_real, result.statistics.desired_imag))
        self.assertAlmostEqual(image, complex(result.statistics.image_real, result.statistics.image_imag))
        self.assertAlmostEqual(np.mean(result.signal.values), .025-.07j)
        self.assertAlmostEqual(result.statistics.image_rejection_db, 10*math.log10(abs(desired/image)**2))
        self.assertEqual(result.signal.metadata['amplitude_units'], 'V')
        ideal = apply_iq_imbalance(source, IQImbalance())
        self.assertEqual(ideal.statistics.image_rejection_state, 'no_image')
        self.assertIsNone(ideal.statistics.image_rejection_db)
        np.testing.assert_array_equal(ideal.signal.values, tone)
        conjugate = apply_iq_imbalance(source, IQImbalance(0, math.pi))
        self.assertEqual(conjugate.statistics.image_rejection_state, 'no_desired')
        np.testing.assert_array_equal(conjugate.signal.values, np.conjugate(tone))
