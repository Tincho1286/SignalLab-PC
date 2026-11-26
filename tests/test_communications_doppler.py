import math
from threading import Event
import unittest

import numpy as np
from scipy.signal import welch
from scipy.special import jv

from signallab_pc.communications_doppler import CarrierShift, analyze_clarke, apply_carrier_shift, clarke_coherence_seconds
from signallab_pc.communications_fading import FadingPath, FadingSpec, apply_fading
from signallab_pc.execution import ExecutionContext
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.resources import ResourceLimitError


class DopplerContracts(unittest.TestCase):
    def test_signed_carrier_shift_keeps_origin_clock_and_power(self):
        offsets = np.arange(37)
        original = np.exp(1j * math.tau * offsets / 16)
        source = Signal(original, origin=-7, metadata={'sample_rate_hz': 2048, 'time_start_s': -0.25})
        for sign in (-1, 1):
            spec = CarrierShift(sign * 256, math.pi / 4)
            result = apply_carrier_shift(source, spec)
            expected = np.exp(1j * math.pi * (offsets * (1/8 + sign/4) + 1/4))
            np.testing.assert_allclose(result.values, expected, atol=1e-13)
            np.testing.assert_array_equal(result.axis, source.axis)
            self.assertEqual(result.metadata['time_start_s'], -0.25)
            self.assertEqual(result.metadata['sample_rate_hz'], 2048)
            self.assertAlmostEqual(float(np.sum(abs(result.values)**2)), len(offsets), places=12)
        np.testing.assert_allclose(apply_carrier_shift(Signal([1, -2j]), CarrierShift(0, math.pi/2)).values,
                                   [1j, 2], atol=1e-15)
        with self.assertRaisesRegex(ValueError, 'Fs/2'):
            apply_carrier_shift(source, CarrierShift(1024))

    def test_clarke_ensemble_covariance_and_band_power(self):
        size, rate, fd = 32768, 4096, 64
        source = Signal(np.ones(size), metadata={'sample_rate_hz': rate})
        lags = [16, 32, 64]
        covariance, spectra = [], []
        for seed in (2014, 3121, 4919, 7547):
            a, = apply_fading(source, FadingSpec((FadingPath(),), seed, fd)).realizations
            samples = a.coefficients.values
            covariance.append([np.vdot(samples[:-lag], samples[lag:])/(size-lag) for lag in lags])
            f, psd = welch(samples, fs=rate, nperseg=2048, detrend=False, return_onesided=False)
            spectra.append(psd)
        np.testing.assert_allclose(np.mean(covariance, axis=0), jv(0, math.tau*fd/rate*np.array(lags)),
                                   rtol=0, atol=.08)
        mean_psd = np.mean(spectra, axis=0)
        total = np.sum(mean_psd)
        self.assertGreater(sum(mean_psd[abs(f) <= fd+4])/total, .99)
        self.assertLess(abs(sum(mean_psd[abs(f) <= fd/2])/total - 1/3), .04)

    def test_clarke_diagnostics_use_known_los_and_normalized_density(self):
        rate, fd = 2048, 80
        source = Signal(np.ones(8192), metadata={'sample_rate_hz': rate})
        path = FadingPath(0, 3.0, 5, 0.3)
        part, = apply_fading(source, FadingSpec((path,), 86, fd)).realizations
        mean = np.sqrt(2.5)*np.exp(0.3j)
        diagnostics = analyze_clarke(part.coefficients, fd, mean=mean, max_lag=32, segment=255)
        diffuse = part.coefficients.values - mean
        expected = np.vdot(diffuse[:-10], diffuse[10:])/(len(diffuse)-10) / np.mean(abs(diffuse)**2)
        self.assertAlmostEqual(diagnostics.observed_correlation[10], expected)
        self.assertAlmostEqual(jv(0, math.tau*fd*diagnostics.coherence_seconds), .5)
        self.assertAlmostEqual(np.sum(diagnostics.theoretical_psd)*rate/255, 1)
        self.assertAlmostEqual(diagnostics.theoretical_correlation[10], jv(0, math.tau*fd*10/rate))
        self.assertIsNone(clarke_coherence_seconds(0))
        edge = analyze_clarke(part.coefficients, rate/2-1e-3, segment=256)
        self.assertAlmostEqual(np.sum(edge.theoretical_psd)*rate/256, 1)

    def test_near_zero_doppler_fixed_limit_and_invalid_clocks(self):
        path = FadingPath()
        source = Signal(np.ones(128), metadata={'sample_rate_hz': 1000})
        fixed = apply_fading(source, FadingSpec((path,), 81, 0))
        np.testing.assert_array_equal(fixed.signal.values, np.full(128, fixed.signal.values[0]))
        slow = apply_fading(source, FadingSpec((path,), 81, 1e-6)).signal.values
        self.assertGreater(abs(slow[-1]-slow[0]), 1e-10)
        self.assertLess(abs(slow[-1]-slow[0]), 1e-5)
        np.testing.assert_allclose(slow, fixed.signal.values, rtol=0, atol=1e-5)
        compared = apply_fading(source, FadingSpec((path,), 81, 1e-6)).signal.values
        np.testing.assert_array_equal(slow, compared)
        with self.assertRaisesRegex(ValueError, 'muestreo'):
            apply_fading(Signal([1]), FadingSpec((path,), 81, 1))
        with self.assertRaisesRegex(ValueError, 'Fs/2'):
            apply_fading(source, FadingSpec((path,), 81, 500))
        with self.assertRaisesRegex(ValueError, 'difusa'):
            analyze_clarke(Signal(np.zeros(8), metadata={'sample_rate_hz': 1000}), 1)

    def test_correlated_fading_accounts_for_transform_work_and_cancellation(self):
        signal = Signal(np.ones(8192), metadata={'sample_rate_hz': 1000})
        spec = FadingSpec((FadingPath(),), 16, 250)
        with self.assertRaises(ResourceLimitError):
            apply_fading(signal, spec, ExecutionContext(max_work_bytes=1_600_000))
        event = Event()

        def stop(percentage):
            if percentage >= 10:
                event.set()

        with self.assertRaises(OperationCancelled):
            apply_fading(signal, spec, ExecutionContext(cancel=event, progress=stop))
