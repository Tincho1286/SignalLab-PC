"""Independent numerical references for sampling and Fourier."""

from cmath import exp
import math
import unittest

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from signallab_pc import fourier, sampling
from signallab_pc.model import Signal
from signallab_pc.operations import dft


def sinc(value):
    return math.sin(math.pi * value) / (math.pi * value) if value else 1


class SamplingReferences(unittest.TestCase):
    def test_alias_preserves_complex_samples_and_initial_phase(self):
        rate, start, frequency = 8, 1/32, 13
        signal = sampling.sample_expression('exp(26*pi*i*t)', start, rate, 9)
        alias = sampling.alias_frequency(frequency, rate)
        self.assertEqual(alias['signed_alias_hz'], -3)
        self.assertEqual(alias['real_sinusoid_alias_hz'], 3)
        self.assertFalse(alias['strict_nyquist'])
        expected = [exp(1j*math.tau*(frequency*start - 3*j/rate)) for j in range(9)]
        assert_allclose(signal.values, expected, rtol=0, atol=2e-14)
        self.assertEqual(signal.metadata['time_start_s'], start)
        self.assertEqual(signal.metadata['sample_rate_hz'], rate)

    def test_alias_is_half_open_at_nyquist(self):
        below, above = math.nextafter(4, 0), math.nextafter(4, math.inf)
        cases = ((-12, -4), (-4, -4), (4, -4), (12, -4), (below, below), (above, above-8))
        for frequency, wrapped in cases:
            with self.subTest(frequency=frequency):
                report = sampling.alias_frequency(frequency, 8)
                self.assertEqual(report['signed_alias_hz'], wrapped)
                self.assertEqual(report['at_nyquist'], abs(frequency) == 4)
                self.assertEqual(report['strict_nyquist'], abs(frequency) < 4)
        for multiples in (-3, -1, 1, 3):
            report = sampling.alias_angular_frequency(multiples * math.pi, 1)
            self.assertAlmostEqual(report['digital_alias_rad_sample'], -math.pi)
            self.assertTrue(report['alias_at_nyquist'])

    def test_interpolation_values_and_physical_clock_by_method(self):
        x = Signal([1+2j, -3j, 2], -3, metadata={'sample_rate_hz': 8, 'time_start_s': -.25})
        expected = {
            'expand': [1+2j, 0, -3j, 0, 2],
            'zoh': [1+2j, 1+2j, -3j, -3j, 2],
            'linear': [1+2j, .5-.5j, -3j, 1-1.5j, 2],
            'sinc': [sum(value*sinc(j/2-k) for k,value in enumerate(x.values))
                     for j in range(5)],
        }
        for method, values in expected.items():
            with self.subTest(method=method):
                y = sampling.resample(x, 2, method)
                assert_allclose(y.values, values, rtol=0, atol=2e-15)
                assert_array_equal(y.axis, [-6, -5, -4, -3, -2])
                self.assertEqual(y.metadata['sample_rate_hz'], 16)
                self.assertEqual(y.metadata['time_start_s'], -.25)
                if method != 'expand':
                    z = sampling.reconstruct(x, None, None, 2, method)
                    assert_allclose(z.values, values, rtol=0, atol=2e-15)
                    assert_array_equal(z.axis, [-.25, -.1875, -.125, -.0625, 0])
                    self.assertEqual(z.units, 's')

    def test_decimation_phase_sets_first_time_only_with_rate_known(self):
        values = [1, 2j, 4, -3, 8j, 5]
        for rate in (12, None):
            with self.subTest(rate=rate):
                clock = {'time_start_s': -.5}
                if rate is not None:
                    clock['sample_rate_hz'] = rate
                x = Signal(values, -7, metadata=clock)
                out = sampling.resample(x, 3, 'decimate', phase=2)
                assert_array_equal(out.values, [4, 5])
                assert_array_equal(out.axis, [0, 1])
                self.assertFalse(out.metadata['antialias_filter'])
                if rate is None:
                    self.assertNotIn('time_start_s', out.metadata)
                else:
                    self.assertEqual(out.metadata['sample_rate_hz'], 4)
                    self.assertAlmostEqual(out.metadata['time_start_s'], -1/3)

    def test_rational_conversion_matches_direct_centered_fir_sum(self):
        source = Signal([1+2j, 2, 3-1j, -2+1j], -4,
                        metadata={'sample_rate_hz': 12, 'time_start_s': -.125})
        # Beta zero is a rectangular Kaiser window. Reduced factors are 2/3.
        ideal = {n: sinc(n/3) for n in range(-6, 7)}
        gain = sum(ideal.values())
        taps = {n: 2 * value/gain for n,value in ideal.items()}
        for boundary in ('zero', 'line'):
            with self.subTest(boundary=boundary):
                def value(j):
                    if 0 <= j < len(source.values):
                        return source.values[j]
                    if boundary == 'line':
                        return source.values[0] + j*(source.values[-1]-source.values[0])/3
                    return 0
                expected = [sum(taps[3*m-2*j]*value(j) for j in range(-4, 8)
                                if 3*m-2*j in taps) for m in range(3)]
                signal, fir, reason = sampling.resample_rational(
                    source, 4, 6, half_width=2, beta=0, boundary=boundary, return_filter=True)
                assert_allclose(signal.values, expected, rtol=0, atol=2e-15)
                assert_allclose(fir.b, list(taps.values()), rtol=0, atol=2e-15)
                self.assertIsNone(reason)
                self.assertEqual(fir.sample_period_s, 1/24)
                self.assertEqual(signal.metadata['sample_rate_hz'], 8)
                self.assertEqual(signal.metadata['time_start_s'], -.125)

    def test_quantization_levels_residual_and_selected_snr(self):
        samples = [-3, -1.5, -1.25, 0, .25, 1.75, 2]
        for method, expected in (
                ('round', [-2, -1, -1, 0, 0, 1, 1]),
                ('floor', [-2, -2, -2, 0, 0, 1, 1])):
            with self.subTest(method=method):
                result = sampling.quantize(Signal(samples, -2), 2, -1.5, 1.5, method,
                                           align_zero=True, first=1, last=4)
                errors = [y-x for x,y in zip(samples, expected)]
                assert_array_equal(result.signal.values, expected)
                assert_array_equal(result.error.values, errors)
                self.assertEqual((result.levels, result.clipped_samples, result.selected_samples), (4, 3, 4))
                expected_snr = 10*math.log10(sum(x*x for x in samples[1:5])/sum(e*e for e in errors[1:5]))
                self.assertAlmostEqual(result.snr_db, expected_snr)

    def test_rounding_distinguishes_values_on_both_sides_of_a_midpoint(self):
        for low, high, threshold in ((0, 3, .5), (-2, 1, -.5)):
            with self.subTest(low=low, high=high):
                signal = Signal([math.nextafter(threshold, -math.inf), threshold,
                                 math.nextafter(threshold, math.inf)])
                result = sampling.quantize(signal, 2, low, high)
                assert_array_equal(result.signal.values, [threshold-.5, threshold+.5, threshold+.5])

    def test_large_range_quantization_keeps_intermediate_levels_representable(self):
        result = sampling.quantize(Signal([-1e308, -3e307, 0, 3e307, 1e308]), 2, -1e308, 1e308)
        assert_allclose(result.signal.values.real/1e308, [-1, -1/3, 1/3, 1/3, 1], atol=5e-16)
        self.assertTrue(math.isfinite(result.snr_db))

    def test_signed_fixed_point_rounding_and_saturation_with_exact_errors(self):
        cases = (('0.375', 'round', '1/2', '0010', '-1/8', '0'),
                 ('-0.375', 'round', '-1/2', '1110', '1/8', '0'),
                 ('-0.375', 'truncate', '-1/4', '1111', '-1/8', '0'),
                 ('2.5', 'round', '7/4', '0111', '3/4', '3/4'),
                 ('-3', 'truncate', '-2', '1000', '-1', '-1'))
        for value, method, shown, bits, error, saturation in cases:
            with self.subTest(value=value, method=method):
                result = sampling.fixed_point(value, 2, 2, method)
                self.assertEqual(result['represented_exact'], shown)
                self.assertEqual(result['binary_twos_complement'], bits)
                self.assertEqual(result['total_error_exact'], error)
                self.assertEqual(result['saturation_error_exact'], saturation)

    def test_nonphysical_sampling_and_clock_reinterpretation(self):
        with self.assertRaisesRegex(ValueError, 'Dirac'):
            sampling.sample_expression('Dirac(t)', 0, 8, 9)
        with self.assertRaisesRegex(ValueError, 'float64'):
            sampling.sample_expression('1', 2**54, 2, 3)
        source = Signal([1, 3], metadata={'sample_rate_hz': 8, 'time_start_s': -.125})
        with self.assertRaisesRegex(ValueError, 'Fs difiere'):
            sampling.reconstruct(source, 4, -.125, 2, 'linear')
        changed = sampling.reconstruct(source, 4, 0, 2, 'linear', override_clock=True)
        assert_array_equal(changed.values, [1, 2, 3])
        assert_array_equal(changed.axis, [0, .125, .25])


class FourierReferences(unittest.TestCase):
    def test_continuous_coefficients_and_synthesis_are_independent_of_cycle_start(self):
        expected = [0, -1.5j, 1, 1, 1, 1.5j, 0]
        for start in (-.25, .125):
            with self.subTest(start=start):
                coeff = fourier.continuous_series('1+2*cos(pi*t)-3*sin(2*pi*t)', start, 2, 32, 3)
                assert_array_equal(coeff.axis, range(-3, 4))
                assert_allclose(coeff.values, expected, rtol=0, atol=3e-15)
                synthesized = fourier.synthesize_continuous(coeff, -.75, 2.25, 13)
                formula = [1+2*math.cos(math.pi*t)-3*math.sin(math.tau*t) for t in synthesized.axis]
                assert_allclose(synthesized.values, formula, rtol=0, atol=9e-15)

    def test_continuous_series_counts_period_edge_impulses_once(self):
        coefficients = fourier.continuous_series('Dirac(t-0.5)+Dirac(t-2.5)', .5, 2, 16, 3)
        expected = [.5*exp(-1j*math.pi*k*.5) for k in range(-3, 4)]
        assert_allclose(coefficients.values, expected, rtol=0, atol=2e-15)
        self.assertEqual(coefficients.metadata['input_dirac_terms'], [[.5, [1.0, 0.0]]])

    def test_ctft_preserves_dirac_phase_and_complex_weight(self):
        origin, weight = .375, 2-3j
        impulse = Signal([0, 0, 0], -.25, .25, 's', 'h', 'continuous',
                         metadata={'dirac_terms': [[origin, [weight.real, weight.imag]]]})
        spectrum = fourier.ctft(impulse, -4, 4, 9)
        assert_allclose(spectrum.values, [weight*exp(-1j*w*origin) for w in range(-4, 5)],
                        rtol=0, atol=2e-15)
        self.assertEqual(spectrum.units, 'rad/s')
        self.assertIn('impulsos Dirac', fourier.energy_report(spectrum, source=impulse))

    def test_inverse_ctft_has_positive_exponent_and_half_weight_endpoints(self):
        spectrum = Signal([2+4j, -1j, 4-2j], -1, 1, 'rad/s', 'X', 'frequency')
        result = fourier.ictft(spectrum, 0, math.pi, 3)
        assert_allclose(result.values, np.asarray([3, 3, -3-2j])/math.tau, rtol=0, atol=3e-16)
        self.assertEqual(result.units, 's')

    def test_welch_with_overlap_matches_direct_sums_and_power(self):
        samples = [1j, 2, -1+1j, 3, 2j, 2-3j, -1, 4, 50]
        x = Signal(samples, -5, metadata={'sample_rate_hz': 16})
        for remove_mean in (False, True):
            with self.subTest(remove_mean=remove_mean):
                blocks = [samples[start:start+4] for start in (0, 2, 4)]
                if remove_mean:
                    blocks = [[v-sum(block)/4 for v in block] for block in blocks]
                coefficients = [[sum(v*exp(-1j*math.tau*k*m/4) for m,v in enumerate(block))
                                 for k in (-2, -1, 0, 1)] for block in blocks]
                expected = [sum(abs(row[k])**2 for row in coefficients)/(3*16*4) for k in range(4)]
                result = fourier.spectral_density(x, 16, segment=4, overlap=2, window='boxcar',
                                                  remove_mean=remove_mean)
                assert_array_equal(result.axis, [-8, -4, 0, 4])
                assert_allclose(result.values, expected, rtol=2e-15, atol=1e-16)
                self.assertAlmostEqual(4*sum(result.values.real),
                                       sum(abs(v)**2 for block in blocks for v in block)/12)
                self.assertEqual((result.metadata['segments_used'], result.metadata['unused_tail']), (3, 1))

    def test_energy_report_separates_full_parseval_and_displayed_band(self):
        signal = Signal([2-1j, 0, 0, 0], -2)
        for stop, integrated in ((0, 2.5), (math.pi, 5)):
            with self.subTest(stop=stop):
                report = fourier.energy_report(fourier.dtft(signal, -math.pi, stop, 17), signal)
                self.assertIn(f'Energía integrada en ese intervalo: {integrated:g}', report)
                self.assertIn('Suma |x[n]|² = 5', report)
        spectrum = dft(signal, centered=True, phase_reference='sample_indices')
        report = fourier.energy_report(spectrum, signal)
        self.assertIn('Energía integrada en ese intervalo: 3.75', report)
        self.assertIn('Suma |X[k]|²/N = 5', report)
        self.assertNotIn('Parseval de la DFT', fourier.energy_report(
            Signal([2-1j], 0, 1, 'rad/muestra', 'X', 'frequency')))

    def test_energy_scaling_avoids_intermediate_overflow(self):
        spectrum = Signal([1e154, 1e154], 0, .25, 'rad/s', 'X', 'frequency')
        source = Signal([1e155, 1e155], 0, 1e-10, 's', 'x', 'continuous')
        report = fourier.energy_report(spectrum, source)
        integrated = next(s for s in report.splitlines() if s.startswith('Energía integrada'))
        assert_allclose(float(integrated.split(': ')[1]), 1e308/(4*math.tau), rtol=2e-12)
        self.assertIn('Suma rectangular Δt·Σ|x(tk)|² = 2e+300', report)
