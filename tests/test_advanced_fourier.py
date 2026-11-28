from threading import Event
import unittest

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from signallab_pc.advanced_fourier import chirp_z, zoom_fft
from signallab_pc.execution import ExecutionContext
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.resources import ResourceLimitError
from signallab_pc.window_signals import generate_window, summary, window_samples
from signallab_pc.window_spectrum import analyze


class AdvancedFourierTests(unittest.TestCase):
    def test_zoom_matches_direct_sum_on_same_grid_in_radians_and_hz(self):
        x = Signal([3+2j, -2, 1j, 4, .8j], -7, metadata={'sample_rate_hz':100, 'time_start_s':.013})
        zoom = zoom_fft(x, -11, 33, 225, units='Hz')
        radians = zoom_fft(x, -.11*2*np.pi, .33*2*np.pi, 225)
        transform = np.exp(-2j*np.pi*np.outer(zoom.spectrum.axis/100, x.axis)) @ x.values
        assert_allclose(zoom.spectrum.values, transform, atol=3e-14)
        assert_allclose(radians.spectrum.values, transform, atol=3e-14)
        self.assertEqual(zoom.spectrum.metadata['input_clock'], {'sample_rate_hz':100, 'time_start_s':.013})
        self.assertEqual(zoom.spectrum.metadata['input_origin'], -7)
        self.assertAlmostEqual(zoom.duration_s, .05)
        self.assertAlmostEqual(zoom.grid_step, 44/224)
        self.assertAlmostEqual(zoom.nominal_dft_spacing, 20)
        self.assertTrue(zoom.spectrum.data_kind == 'spectrum')
        with self.assertRaisesRegex(ValueError, 'reloj'):
            zoom_fft(x, -1, 1, units='Hz', rate_hz=101)
        with self.assertRaisesRegex(ValueError, 'reloj'):
            zoom_fft(Signal([1]), -1, 1, units='Hz')
        explicit = zoom_fft(Signal([1]), -1, 1, units='Hz', rate_hz=20)
        self.assertEqual(explicit.spectrum.metadata['input_clock']['sample_rate_hz'], 20)
        assert_allclose(explicit.spectrum.values, 1, atol=1e-14)

    def test_windowed_peak_amplitude_phase_and_frequency_of_off_bin_tone(self):
        f = .123456
        n = np.arange(-48, 112)
        amplitude, phase = 2.3, .73
        x = Signal(amplitude*np.exp(1j*(n*f+phase)), -48)
        narrow = zoom_fft(x, .11, .14, 46, complex_tone_peaks=1, window='hann',
                          window_options={'symmetric':False})
        peak, = narrow.peaks
        self.assertAlmostEqual(peak.refined_frequency, f, places=10)
        self.assertAlmostEqual(peak.amplitude, amplitude, places=11)
        self.assertAlmostEqual(peak.phase_rad, phase, places=9)
        self.assertGreater(abs(peak.sampled_frequency - f), 1e-5)
        self.assertEqual(zoom_fft(Signal([0,0]), -1, 1, 10, complex_tone_peaks=4).peaks, ())

    def test_optional_dft_is_on_its_original_bins_with_same_window_and_phase(self):
        values=np.array([.5+.7j,1,2-1j,-1,.1,2,3j,-4])
        source=Signal(values,-3,metadata={'sample_rate_hz':64})
        result=zoom_fft(source,-20.,30.,107,units='Hz',window='hann',compare_dft=True,
                        window_options={'symmetric':False})
        assert_array_equal(result.dft_bins,[-16,-8,0,8,16,24])
        weights=.5-.5*np.cos(2*np.pi*np.arange(8)/8)
        expected=np.exp(-2j*np.pi*np.outer(result.dft_bins/64,source.axis)) @ (values*weights)
        assert_allclose(result.dft_values,expected,atol=3e-15)
        plain=zoom_fft(source,1,2,41)
        self.assertIsNone(plain.dft_bins)
        with self.assertRaises(ValueError):
            zoom_fft(source,-1,1,21,compare_dft=1)

    def test_chirp_z_matches_laurent_polynomial_including_negative_origin(self):
        x = Signal([.5+1j, 1, -2j, 3, -1], -2)
        result = chirp_z(x, 137, initial_radius=.8, initial_angle_rad=-.4, radius_ratio=1.003,
                         angle_step_rad=.008)
        z = .8*1.003**np.arange(137)*np.exp(1j*(-.4 + .008*np.arange(137)))
        expected = (.5+1j)*z**2+z-2j+3/z-1/z**2
        assert_allclose(result.z, z, atol=5e-15)
        assert_allclose(result.samples.values, expected, atol=1e-14)
        self.assertEqual(result.samples.data_kind, 'z_samples')
        real = chirp_z(x, 4, radius_ratio=2, angle_step_rad=0)
        assert_allclose(real.z, [1,2,4,8])
        assert_allclose(real.samples.values, sum(x.values[i]*real.z**(-n) for i,n in enumerate(x.axis)))

    def test_unit_circle_matches_dft_and_reversed_polar_path(self):
        work = np.array([1+1j, .2-1j, 3, .5])
        source = Signal(work, -3)
        default = chirp_z(source, 8)
        expected = np.fft.fft(work, n=8) * np.exp(2j*np.pi*np.arange(8)*3/8)
        assert_allclose(default.samples.values, expected, atol=1e-14)
        band = chirp_z(source, 10, initial_angle_rad=.2, angle_step_rad=-.1)
        assert_allclose(band.samples.values, band.z[:, None] ** (-source.axis) @ work, atol=1e-14)
        impulses = Signal([1], (1 << 61) + 3)
        very_late = zoom_fft(impulses, -np.pi, np.pi, count=9).spectrum
        k = np.arange(-4,5)
        assert_allclose(very_late.values, np.exp(-2j*np.pi*(3*k % 8)/8), atol=3e-15)

    def test_domains_admission_and_cancellation(self):
        x = Signal([1,2,3])
        for options in ({'count':0}, {'units':'k'}, {'window_options':{'bad':1}}, {'complex_tone_peaks':51}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                zoom_fft(x, -1, 1, **options)
        with self.assertRaisesRegex(ValueError, 'período'):
            zoom_fft(x, -5, 5)
        with self.assertRaises(ValueError):
            zoom_fft(x, 1, -1)
        with self.assertRaises(ValueError):
            chirp_z(x, 16, initial_radius=0)
        with self.assertRaises(ValueError):
            chirp_z(x, 16, angle_step_rad=0)
        with self.assertRaises(ValueError):
            chirp_z(x, 16, angle_step_rad=8)
        with self.assertRaisesRegex(ValueError, 'rango exponencial'):
            chirp_z(Signal([1], 1000), 6, initial_radius=4)
        with self.assertRaisesRegex(ValueError, 'productos'):
            chirp_z(Signal(np.ones(4096)), 9000, initial_radius=.99)
        with self.assertRaises(ResourceLimitError):
            zoom_fft(x, -.5, .5, 50, context=ExecutionContext(max_work_bytes=10))
        event = Event()
        event.set()
        for operation in (lambda: zoom_fft(x,-1,1,16,context=ExecutionContext(cancel=event)),
                          lambda: chirp_z(x,16,radius_ratio=.97,context=ExecutionContext(cancel=event))):
            with self.assertRaises(OperationCancelled):
                operation()


class AdvancedWindowTests(unittest.TestCase):
    def test_periodic_truncation_and_endpoints(self):
        for kind, options in (('tukey',{'alpha':.4}), ('flattop',{}), ('nuttall',{}),
                              ('dpss',{'nw':2}), ('chebwin',{'attenuation_db':100}), ('hann',{})):
            with self.subTest(kind=kind):
                symmetric = window_samples(kind, 21, **options)
                periodic = window_samples(kind, 20, symmetric=False, **options)
                assert_allclose(symmetric, symmetric[::-1], atol=2e-14)
                assert_allclose(periodic, symmetric[:-1], atol=2e-14)
                generated = generate_window(kind, 20, -9, symmetric=False, **options)
                assert_array_equal(generated.axis, np.arange(-9,11))
                assert_array_equal(generated.values.real, periodic)
                self.assertFalse(generated.metadata['symmetric'])
                self.assertIn('Periódica', summary(generated).plain_text())
        assert_array_equal(window_samples('tukey', 11, alpha=0), 1)
        assert_allclose(window_samples('tukey', 11, alpha=1), window_samples('hann',11))
        assert_array_equal(window_samples('dpss', 1), [1])

    def test_dpss_matches_eigenvector_of_energy_concentration_kernel(self):
        length, nw = 20, 2.0
        halfband = nw/length
        indices = np.arange(length)
        kernel = 2*halfband*np.sinc(2*halfband*(indices[:,None]-indices[None,:]))
        _, basis = np.linalg.eigh(kernel)
        ranking = np.sign(basis[:, -1].sum())*basis[:, -1]
        actual = window_samples('dpss', length, nw=nw)
        assert_allclose(actual/np.linalg.norm(actual), ranking, atol=1e-12)

    def test_metrics_and_flat_top_loss_against_rectangular_formula(self):
        count = 48
        calculated = analyze(generate_window('boxcar', count))['metrics']
        exact_half_bin = -20*np.log10(1/(count*np.sin(np.pi/(2*count))))
        self.assertAlmostEqual(calculated['coherent_gain'], 1)
        self.assertAlmostEqual(calculated['enbw_bins'], 1)
        self.assertAlmostEqual(calculated['enbw_radians'], 2*np.pi/count)
        self.assertAlmostEqual(calculated['scalloping_db'], exact_half_bin, places=11)
        self.assertAlmostEqual(calculated['main_lobe_width_rad'], 4*np.pi/count, places=8)
        self.assertLess(calculated['peak_sidelobe_db'], -13)
        flat = analyze(generate_window('flattop', count, symmetric=False))['metrics']
        self.assertLess(abs(flat['scalloping_db']), .02)
        self.assertGreater(flat['enbw_bins'], 3.7)
        self.assertGreater(flat['main_lobe_width_rad'], calculated['main_lobe_width_rad'])
        zero_dc = analyze(Signal([1,-1]))['metrics']
        self.assertFalse(zero_dc['normalizable'])
        self.assertIsNone(zero_dc['enbw_bins'])

    def test_reject_invalid_parameters(self):
        for kind, options in (('boxcar',{'symmetric':0}), ('unknown',{}), ('tukey',{'alpha':1.01}),
                              ('dpss',{'nw':10}), ('chebwin',{'attenuation_db':25}),('kaiser',{'beta':-1})):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                window_samples(kind, 20, **options)

    def test_sidelobe_at_nyquist_and_spectrum_without_a_half_power_crossing(self):
        from signallab_pc.window_spectrum import measure_section
        short=analyze(generate_window('boxcar',3))['metrics']
        self.assertAlmostEqual(short['peak_sidelobe_db'],20*np.log10(1/3))
        flat=analyze(Signal([1,0]))
        self.assertIsNone(flat['metrics']['half_power_frequency'])
        self.assertTrue(any('No se alcanza media potencia' in paragraph for paragraph in measure_section(flat).paragraphs))
        cancellation=analyze(Signal([1,-1]))
        self.assertTrue(any('componente en ω=0' in paragraph for paragraph in measure_section(cancellation).paragraphs))
        with self.assertRaisesRegex(ValueError,'real'):
            analyze(Signal([1j,1j]))


if __name__ == '__main__':
    unittest.main()
