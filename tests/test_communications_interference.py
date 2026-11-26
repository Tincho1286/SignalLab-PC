import math
from threading import Event
import unittest

import numpy as np

from signallab_pc.communications_interference import (
    BandInterference, ExternalInterference, InterferenceSpec, InterferenceTone, ToneInterference,
    apply_interference, measure_power_ratio, parse_interference_tone, store_interference,
)
from signallab_pc.execution import ExecutionContext
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.resources import ResourceLimitError


class InterferenceContracts(unittest.TestCase):
    def test_tones_match_analytic_sum_and_target_sir(self):
        size, rate = 256, 1024
        k = np.arange(size)
        x = Signal(np.exp(2j*np.pi*k/32), origin=-3,
                   metadata={'sample_rate_hz': rate, 'time_start_s': 0.1})
        model = ToneInterference((parse_interference_tone('100, 0.5, pi/4'), InterferenceTone(-220, 2)))
        expectation = .5*np.exp(1j*(math.tau*100*k/rate+np.pi/4)) + 2*np.exp(-1j*math.tau*220*k/rate)
        result = apply_interference(x, InterferenceSpec(model, sir_db=6))
        calibrated = expectation*np.sqrt(10**(-.6)/(4+.25))
        np.testing.assert_allclose(result.interference.values, calibrated, rtol=0, atol=2e-14)
        np.testing.assert_allclose(result.signal.values, x.values+calibrated, rtol=0, atol=2e-14)
        self.assertEqual(result.signal.origin, -3)
        self.assertEqual(result.signal.metadata['time_start_s'], .1)
        self.assertAlmostEqual(result.statistics.sir.db, 6)
        self.assertAlmostEqual(result.statistics.sinr.db, 6)
        self.assertEqual(result.statistics.snr.state, 'unbounded')
        self.assertIsNone(result.noise)

    def test_band_support_power_and_seed_at_baseband_and_adjacent_frequency(self):
        size, rate = 512, 1024
        source = Signal(np.ones(size), metadata={'sample_rate_hz': rate})
        for center in (0, 256):
            with self.subTest(center=center):
                config = InterferenceSpec(BandInterference(128, center, 58), power=2.5)
                result = apply_interference(source, config)
                f = np.fft.fftfreq(size, 1/rate)
                powers = abs(np.fft.fft(result.interference.values))**2
                inside = (f >= center - 64) & (f < center + 64)
                self.assertLess(sum(powers[~inside])/sum(powers), 1e-26)
                self.assertAlmostEqual(sum(powers)/size**2, 2.5)
                np.testing.assert_array_equal(result.interference.values,
                                              apply_interference(source, config).interference.values)
                self.assertEqual(result.signal.metadata['communications_interference']['synthesis']['occupied_bins'], 64)
        with self.assertRaisesRegex(ValueError, 'bin DFT'):
            apply_interference(source, InterferenceSpec(BandInterference(.1, 1)))
        with self.assertRaisesRegex(ValueError, 'Nyquist'):
            apply_interference(source, InterferenceSpec(BandInterference(128, 490)))

    def test_external_alignment_rotation_and_source_verification(self):
        source = Signal(np.ones(6), origin=-2, metadata={'sample_rate_hz': 8, 'time_start_s': .125,
                                                          'amplitude_units': 'V'})
        external = Signal([1+1j, 2, -1j], origin=0,
                          metadata={'sample_rate_hz': 8, 'time_start_s': .375, 'amplitude_units': 'V'})
        model = InterferenceSpec(ExternalInterference(2))
        result = apply_interference(source, model, external=external)
        wanted = np.pad(external.values, (2, 1))*np.exp(.5j*np.pi*np.arange(6))
        np.testing.assert_allclose(result.interference.values, wanted, rtol=0, atol=1e-14)
        self.assertEqual(result.signal.metadata['communications_interference']['synthesis']['overlap_samples'], 3)
        referenced = apply_interference(
            source.copy_with(metadata={**source.metadata, 'center_frequency_hz': 100}),
            InterferenceSpec(ExternalInterference()),
            external=external.copy_with(metadata={**external.metadata, 'center_frequency_hz': 102}),
        )
        np.testing.assert_allclose(referenced.interference.values, wanted, rtol=0, atol=1e-14)
        project = Project()
        parents = (project.add(source), project.add(external))
        records = store_interference(project, result, parents=parents)
        self.assertIn('verified_provenance',
                      next(row for row in project.headers() if row['id'] == records['interference_record']))
        with self.assertRaisesRegex(ValueError, 'origen'):
            store_interference(project, result, parents=parents[::-1])
        with self.assertRaisesRegex(ValueError, 'unidades'):
            apply_interference(source, model, external=external.copy_with(
                metadata={**external.metadata, 'amplitude_units': 'mV'}))
        with self.assertRaisesRegex(ValueError, 'tiempos'):
            apply_interference(source, model, external=external.copy_with(
                metadata={**external.metadata, 'time_start_s': .125}))
        with self.assertRaisesRegex(ValueError, 'misma Fs'):
            apply_interference(source, model, external=Signal([1, 2]))
        repeated = apply_interference(source, InterferenceSpec(ExternalInterference()), external=source)
        saved = store_interference(project, repeated, parents=(parents[0], parents[0]))
        np.testing.assert_array_equal(project.get(saved['record']).values, 2*source.values)

    def test_noise_and_disturbance_powers_are_measured_separately(self):
        source = Signal(np.full(8192, 2j), metadata={'sample_rate_hz': 4096})
        spec = InterferenceSpec(BandInterference(2048, 0, 73), sir_db=8, noise_snr_db=10, noise_seed=73)
        result = apply_interference(source, spec)
        i, n = result.interference.values, result.noise.values
        p_i, p_n = (float(np.mean(abs(values)**2)) for values in (i, n))
        expected = 10*math.log10(4/(p_i+p_n))
        self.assertAlmostEqual(result.statistics.interference_power, p_i)
        self.assertAlmostEqual(result.statistics.noise_power, p_n)
        self.assertAlmostEqual(result.statistics.observed_disturbance_power, np.mean(abs(i+n)**2))
        self.assertAlmostEqual(result.statistics.sinr.db, expected)
        self.assertLess(abs(p_n/.4 - 1), .04)
        self.assertLess(abs(np.vdot(i, n)/len(i)), .03)
        np.testing.assert_array_equal(result.signal.values, source.values+(i+n))
        self.assertEqual(measure_power_ratio(0, 0).state, 'undefined')
        self.assertEqual(measure_power_ratio(0, 2).state, 'zero')

    def test_limits_cancellation_and_mutated_auxiliary_record(self):
        source = Signal(np.ones(1024), metadata={'sample_rate_hz': 1024})
        spec = InterferenceSpec(ToneInterference((InterferenceTone(1),)), power=0)
        with self.assertRaises(ResourceLimitError):
            apply_interference(source, spec, execution=ExecutionContext(max_work_bytes=1024))
        stop = Event()

        def progress(percentage):
            if percentage > 0:
                stop.set()

        with self.assertRaises(OperationCancelled):
            apply_interference(source, spec, execution=ExecutionContext(cancel=stop, progress=progress))
        with self.assertRaisesRegex(ValueError, 'positiva'):
            apply_interference(Signal([0]), InterferenceSpec(spec.model, sir_db=0))
        with self.assertRaisesRegex(ValueError, 'potencia solicitada'):
            apply_interference(source, InterferenceSpec(ToneInterference((InterferenceTone(0, 0),)), power=1))
        result = apply_interference(source, spec)
        np.testing.assert_array_equal(result.signal.values, source.values)
        self.assertEqual(result.statistics.sir.state, 'unbounded')
        project = Project()
        parent = project.add(source)
        result.interference.values[0] = 1
        with self.assertRaisesRegex(ValueError, 'cambió'):
            store_interference(project, result, parents=(parent,))
        self.assertEqual(len(project.headers()), 1)
