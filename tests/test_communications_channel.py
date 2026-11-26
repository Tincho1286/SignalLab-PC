import math
from threading import Event
import unittest

import numpy as np
from scipy.signal import freqz
from scipy.stats import chi2

from signallab_pc.communications_channel import (
    AWGNSpec, ChannelPath, MultipathSpec, add_awgn, analyze_multipath, apply_multipath, multipath_frequency,
)
from signallab_pc.communications_data import SymbolClock, iq_signal
from signallab_pc.communications_pulses import PulseSpec, apply_pulse, design_pulse, upsample_symbols
from signallab_pc.dsp_application import store_signal
from signallab_pc.execution import ExecutionContext, ResourcePool
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.resources import ResourceLimitError


class CommunicationsChannelTests(unittest.TestCase):
    def test_complex_channel_uses_per_sample_power_without_sps_factor(self):
        source = iq_signal([1+2j, -3j, -4+0j], SymbolClock(2000, 4, -0.75, 500e3),
                           origin=-4, amplitude_units='V')
        result = add_awgn(source, AWGNSpec('snr', 10, 123))
        stats = result.statistics
        measured = (5+9+16)/3
        self.assertAlmostEqual(stats.reference_power, measured)
        self.assertAlmostEqual(stats.measured_signal_power, measured)
        self.assertAlmostEqual(stats.n0, measured/10)
        self.assertAlmostEqual(stats.nominal_variance_i, measured/20)
        self.assertAlmostEqual(stats.nominal_variance_q, measured/20)
        self.assertEqual(stats.snr_db, 10)
        self.assertIsNone(stats.symbol_energy)
        self.assertIsNone(stats.eb_n0_db)
        self.assertIsNone(stats.es_n0_db)
        self.assertEqual(result.signal.origin, -4)
        for tag in ('sample_rate_hz', 'symbol_rate_hz', 'samples_per_symbol',
                    'time_start_s', 'center_frequency_hz', 'amplitude_units'):
            self.assertEqual(result.signal.metadata[tag], source.metadata[tag])
        np.testing.assert_array_equal(source.values, [1+2j, -3j, -4+0j])

    def test_eb_n0_conventions_real_and_complex_against_theory(self):
        samples = 150_000
        source = Signal(np.resize([1, -1], samples))
        for domain, total_noise, snr in (('real', 0.05, 10*math.log10(20)), ('complex', 0.1, 10)):
            with self.subTest(domain=domain):
                spec = AWGNSpec('eb_n0', 10, 76621, domain, symbol_energy=2, bits_per_symbol=2)
                result = add_awgn(source, spec)
                stats = result.statistics
                self.assertAlmostEqual(stats.bit_energy, 1)
                self.assertAlmostEqual(stats.n0, 0.1)
                self.assertAlmostEqual(stats.snr_db, snr)
                self.assertAlmostEqual(stats.es_n0_db, 10*math.log10(20))
                self.assertEqual(stats.eb_n0_db, 10)
                self.assertAlmostEqual(stats.nominal_variance_i, 0.05)
                self.assertAlmostEqual(stats.nominal_variance_i + stats.nominal_variance_q, total_noise)
                delta = result.signal.values - source.values
                lo, hi = chi2.ppf((0.0005, 0.9995), samples - 1)*0.05/samples
                self.assertAlmostEqual(stats.measured_variance_i, float(np.var(delta.real)), places=14)
                self.assertAlmostEqual(stats.measured_mean_i, float(np.mean(delta.real)), places=14)
                self.assertLess(lo, stats.measured_variance_i)
                self.assertLess(stats.measured_variance_i, hi)
                self.assertLess(abs(stats.measured_mean_i), 5*math.sqrt(0.05/samples))
                if domain == 'real':
                    np.testing.assert_array_equal(delta.imag, 0)
                    self.assertEqual(stats.nominal_variance_q, 0)
                    self.assertEqual(stats.measured_variance_q, 0)
                    self.assertEqual(stats.measured_covariance_iq, 0)
                else:
                    self.assertAlmostEqual(stats.measured_variance_q, float(np.var(delta.imag)), places=14)
                    self.assertAlmostEqual(stats.measured_mean_q, float(np.mean(delta.imag)), places=14)
                    covariance = np.cov(delta.real, delta.imag, ddof=0)[0, 1]
                    self.assertAlmostEqual(stats.measured_covariance_iq, covariance, places=14)
                    self.assertLess(lo, stats.measured_variance_q)
                    self.assertLess(stats.measured_variance_q, hi)
                    self.assertLess(abs(stats.measured_covariance_iq), 5*0.05/math.sqrt(samples))

    def test_seed_and_unit_conversion_are_reproducible(self):
        source = Signal(np.ones(80_003))
        spec = AWGNSpec('es_n0', 6, 0, symbol_energy=4, bits_per_symbol=4)
        first = add_awgn(source, spec)
        second = add_awgn(source, spec)
        other = add_awgn(source, AWGNSpec('es_n0', 6, 1, symbol_energy=4))
        expected_var = (4 / 10**0.6) / 2
        rng = np.random.Generator(np.random.PCG64(0))
        expected = rng.standard_normal((source.values.size, 2))
        mixed = (1 + math.sqrt(expected_var)*expected[:, 0]) + 1j*math.sqrt(expected_var)*expected[:, 1]
        np.testing.assert_allclose(first.signal.values, mixed, atol=2e-15)
        np.testing.assert_array_equal(first.signal.values, second.signal.values)
        self.assertEqual(first.statistics, second.statistics)
        self.assertFalse(np.array_equal(first.signal.values, other.signal.values))
        self.assertAlmostEqual(first.statistics.nominal_variance_i, expected_var)
        self.assertAlmostEqual(first.statistics.eb_n0_db, 6-10*math.log10(4))
        self.assertEqual(first.statistics.es_n0_db, 6)
        self.assertEqual(first.signal.metadata['communications_noise']['generator'], 'PCG64')

    def test_reference_power_and_zero_records_have_explicit_policies(self):
        source = Signal([0, 0])
        with self.assertRaisesRegex(ValueError, 'positiva'):
            add_awgn(source, AWGNSpec('snr', 3, 1))
        # Calibration power can be supplied for a measured zero record.
        specified = AWGNSpec('snr', 0, 1, domain='real', signal_power=2,
                             symbol_energy=4, bits_per_symbol=2)
        stats = add_awgn(source, specified).statistics
        self.assertEqual(stats.measured_signal_power, 0)
        self.assertEqual(stats.reference_power, 2)
        self.assertAlmostEqual(stats.n0, 4)
        self.assertAlmostEqual(stats.nominal_variance_i, 2)
        self.assertAlmostEqual(stats.es_n0_db, 0)
        self.assertAlmostEqual(stats.eb_n0_db, -10*math.log10(2))
        by_energy = add_awgn(source, AWGNSpec('es_n0', 0, 0, symbol_energy=1))
        self.assertIsNone(by_energy.statistics.snr_db)
        self.assertAlmostEqual(by_energy.statistics.nominal_variance_i, 0.5)

    def test_invalid_configuration_signal_and_nonrepresentable_noise(self):
        for reference, value, seed, kwargs in (
            ('other', 1, 0, {}), ('snr', 1, 0, {'domain': 'imaginary'}),
            ('snr', math.inf, 0, {}), ('snr', 0, True, {}),
            ('snr', 0, 0, {'signal_power': 0}), ('snr', 0, 0, {'bits_per_symbol': 50}),
            ('es_n0', 0, 0, {}), ('es_n0', 0, 0, {'symbol_energy': False}),
            ('eb_n0', 0, 0, {'symbol_energy': 1}),
        ):
            with self.subTest(reference=reference, kwargs=kwargs), self.assertRaises(ValueError):
                AWGNSpec(reference, value, seed, **kwargs)
        spec = AWGNSpec('snr', 0, 1, 'real')
        with self.assertRaises(TypeError):
            add_awgn('not a signal', spec)
        with self.assertRaises(ValueError):
            add_awgn(Signal([1], domain='frequency'), spec)
        with self.assertRaisesRegex(ValueError, 'imaginaria'):
            add_awgn(Signal([1j]), spec)
        for extreme in (1e-200, 1e200):
            with self.subTest(extreme=extreme), self.assertRaisesRegex(ValueError, 'potencia'):
                add_awgn(Signal([extreme]), spec)
        for db in (-4000, 4000):
            with self.subTest(db=db), self.assertRaisesRegex(ValueError, 'ruido'):
                add_awgn(Signal([1]), AWGNSpec('snr', db, 0))
        tiny = AWGNSpec('eb_n0', 0, 0, symbol_energy=math.ulp(0.0), bits_per_symbol=4)
        with self.assertRaisesRegex(ValueError, 'energía por bit'):
            add_awgn(Signal([1]), tiny)
        source = Signal([1, 2])
        source.values[0] = np.nan
        with self.assertRaisesRegex(ValueError, 'finitas'):
            add_awgn(source, spec)
        source.values = np.ones((2, 1), dtype=complex)
        with self.assertRaisesRegex(ValueError, 'vector'):
            add_awgn(source, spec)

    def test_cancel_and_mutation_never_produce_a_result(self):
        source = Signal(np.ones(140_000))
        spec = AWGNSpec('snr', 12, 3)
        with self.assertRaises(ResourceLimitError):
            add_awgn(source, spec, ExecutionContext(max_work_bytes=1024))
        event = Event()
        budget = 20_000_000
        pool = ResourcePool(budget)

        def stop(percentage):
            if percentage > 40:
                event.set()

        with self.assertRaises(OperationCancelled):
            add_awgn(source, spec, ExecutionContext(cancel=event, progress=stop, pool=pool))
        self.assertTrue(event.is_set())
        with pool.reserve(budget):
            pass

        def mutate(percentage):
            if percentage == 100:
                source.values[0] = 3

        with self.assertRaisesRegex(ValueError, 'cambió'):
            add_awgn(source, spec, ExecutionContext(progress=mutate))

    def test_awgn_and_upsampling_publish_complete_results_from_existing_signals(self):
        x = iq_signal([1, 2], SymbolClock(1200, 1, -0.25))
        p = design_pulse(PulseSpec('rectangular', 1, 1))
        y = apply_pulse(x, p)  # Contains FIR provenance at the input boundary.
        up = upsample_symbols(y, 4)
        noisy = add_awgn(up, AWGNSpec('snr', 3, 11)).signal
        project = Project()
        fir = project.add(y)
        inserted = store_signal(project, up, parents=(fir,))
        noise = store_signal(project, noisy, parents=(inserted,))
        np.testing.assert_array_equal(project.get(noise).values, noisy.values)
        self.assertEqual(project.get(noise).metadata['time_start_s'], -0.25)


class MultipathContracts(unittest.TestCase):
    def test_coherent_power_profile_and_symbol_spaced_isi(self):
        paths = (ChannelPath(1, 1, 1), ChannelPath(1, 1, -1), ChannelPath(5, 0, 1))
        spec = MultipathSpec(paths)
        analysis = analyze_multipath(spec, samples_per_symbol=4)
        self.assertEqual([(p.delay_samples, p.power) for p in analysis.power_delay_profile], [(1, 4), (5, 1)])
        self.assertEqual(analysis.total_power, 5)
        self.assertAlmostEqual(analysis.mean_delay_samples, 1.8)
        self.assertAlmostEqual(analysis.rms_delay_spread_samples, 1.6)
        self.assertEqual(analysis.symbol_spaced_isi.interfering_lags_symbols, (1,))
        self.assertEqual(analysis.symbol_spaced_isi.interference_to_reference_power, 0.25)
        self.assertEqual(analyze_multipath(spec, samples_per_symbol=3).symbol_spaced_isi.interfering_lags_symbols, ())
        normalized = MultipathSpec(paths, normalize_power=True)
        self.assertAlmostEqual(analyze_multipath(normalized).total_power, 1)
        impulse = apply_multipath(Signal([1]), normalized)
        np.testing.assert_allclose(impulse.values, [0, 2/math.sqrt(5), 0, 0, 0, 1j/math.sqrt(5)])

    def test_frequency_matches_freqz_on_centered_even_and_odd_grids(self):
        analysis = analyze_multipath(MultipathSpec((ChannelPath(0, 2, 1), ChannelPath(3, -0.5, 1))))
        impulse = [2+1j, 0, 0, -0.5+1j]
        for points in (40, 41):
            with self.subTest(points=points):
                response = multipath_frequency(analysis, points)
                omega = np.fft.fftshift(np.fft.fftfreq(points))*math.tau
                np.testing.assert_allclose(response.axis, omega, rtol=0, atol=1e-15)
                _, expected = freqz(impulse, worN=omega)
                np.testing.assert_allclose(response.values, expected, rtol=0, atol=7e-15)
        delay = (1 << 63) - 1
        sparse = analyze_multipath(MultipathSpec((ChannelPath(delay), ChannelPath(delay-2))))
        self.assertEqual(sparse.rms_delay_spread_samples, 1)
        response = multipath_frequency(sparse, 8)
        _, expected = freqz([0, 0, 0, 0, 0, 1, 0, 1], worN=response.axis)
        np.testing.assert_allclose(response.values, expected, rtol=0, atol=7e-15)

    def test_zero_profile_and_extreme_normalization(self):
        cancelling = (ChannelPath(2), ChannelPath(2, -1))
        empty = analyze_multipath(MultipathSpec(cancelling), samples_per_symbol=1)
        self.assertIsNone(empty.mean_delay_samples)
        self.assertIsNone(empty.rms_delay_spread_samples)
        self.assertIsNone(empty.symbol_spaced_isi)
        np.testing.assert_array_equal(multipath_frequency(empty, 4).values, np.zeros(4))
        with self.assertRaisesRegex(ValueError, 'nula'):
            analyze_multipath(MultipathSpec(cancelling, normalize_power=True))
        for gain in (1e-300, 1e300):
            with self.subTest(gain=gain):
                spec = MultipathSpec((ChannelPath(0, gain, gain),), normalize_power=True)
                self.assertAlmostEqual(analyze_multipath(spec).total_power, 1)
                got = apply_multipath(Signal([1]), spec)
                np.testing.assert_allclose(got.values, [(1+1j)/math.sqrt(2)])

    def test_multipath_matches_dense_convolution_and_preserves_clock(self):
        source = iq_signal([1+2j, 3-1j, 2, -1j], SymbolClock(4000, 2, -0.25, 1e6),
                           origin=-3, amplitude_units='V')
        paths = (ChannelPath(4, 0, 0.25), ChannelPath(1, -0.5), ChannelPath(1, 0, 1),
                 ChannelPath(0), ChannelPath(7, 0))
        expected = np.convolve(source.values, [1, -0.5+1j, 0, 0, 0.25j, 0, 0, 0])
        result = apply_multipath(source, paths)
        np.testing.assert_array_equal(result.values, expected)
        np.testing.assert_array_equal(result.axis, np.arange(-3, 8))
        identity = apply_multipath(source, (ChannelPath(0),))
        np.testing.assert_array_equal(identity.values, source.values)
        for name in ('sample_rate_hz', 'time_start_s', 'samples_per_symbol', 'center_frequency_hz', 'amplitude_units'):
            self.assertEqual(result.metadata[name], source.metadata[name])
        project = Project()
        parent = project.add(source)
        key = store_signal(project, result, parents=(parent,))
        self.assertIn(parent, next(row for row in project.headers() if row['id'] == key)['parents'])
        different = project.add(source.copy_with(values=source.values + 1))
        with self.assertRaises(ValueError):
            store_signal(project, result, parents=(different,))
        self.assertEqual(len(project.headers()), 3)

    def test_multipath_validates_limits_and_cancels_between_blocks(self):
        source = Signal(np.ones(140_000))
        paths = (ChannelPath(0), ChannelPath(3, -1))
        with self.assertRaisesRegex(ValueError, 'trayectoria'):
            apply_multipath(source, ())
        with self.assertRaisesRegex(ValueError, 'temporal discreta'):
            apply_multipath(Signal([1], domain='frequency'), paths)
        with self.assertRaisesRegex(ValueError, 'soporte'):
            apply_multipath(Signal([1], origin=(1 << 63) - 1), (ChannelPath(1),))
        with self.assertRaisesRegex(ValueError, 'reloj'):
            apply_multipath(Signal([1], metadata={'sample_rate_hz': 1e-308}), (ChannelPath(2),))
        with self.assertRaisesRegex(FloatingPointError, 'rango'):
            apply_multipath(Signal([1e308]), (ChannelPath(0, 2),))
        with self.assertRaises(ResourceLimitError):
            apply_multipath(source, paths, ExecutionContext(max_work_bytes=1024))
        event = Event()
        budget = 20_000_000
        pool = ResourcePool(budget)

        def stop(percentage):
            if percentage > 20:
                event.set()

        with self.assertRaises(OperationCancelled):
            apply_multipath(source, paths, ExecutionContext(cancel=event, progress=stop, pool=pool))
        self.assertTrue(event.is_set())
        with pool.reserve(budget):
            pass
        result = apply_multipath(source, paths)
        np.testing.assert_array_equal(result.values[:3], [1, 1, 1])
        np.testing.assert_array_equal(result.values[3:-3], np.zeros(139_997))
        np.testing.assert_array_equal(result.values[-3:], [-1, -1, -1])


if __name__ == '__main__':
    unittest.main()
