"""Check noise spectra and generation against independent sums and path statistics."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import cmath
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
import unittest

import numpy as np

from signallab_pc import session
from signallab_pc.execution import ExecutionContext, ResourceLimitError
from signallab_pc.jobs import OperationCancelled
from signallab_pc.stochastic_cli import main
from signallab_pc.stochastic_noise import Noise, generate_noise, noise_spectrum


def direct_dft(values):
    n = len(values)
    return np.asarray([sum(x*cmath.exp(-2j*math.pi*k*i/n) for i,x in enumerate(values))
                       for k in range(-(n//2), (n+1)//2)])


class StochasticNoiseOracles(unittest.TestCase):
    def test_real_specification_matches_bilateral_dft_and_edge_bands(self):
        model = Noise('specified_noise', dict(frequency_hz=[0,1,3], density=[0,1,2], complex=False))
        expected = [0,2,1.5,1,0,1,1.5,2]
        spectrum = noise_spectrum(model,8,rate=8)
        self.assertEqual(spectrum.data_kind, 'density')
        np.testing.assert_array_equal(spectrum.axis, np.arange(-4,4))
        np.testing.assert_array_equal(spectrum.values, expected)
        self.assertEqual(spectrum.metadata['variance'], 9)
        sample = generate_noise(model,8,4,rate=8)[0]
        white = generate_noise(Noise('white_noise', dict(variance=1,complex=False)),8,4)[0]
        np.testing.assert_allclose(direct_dft(sample.values), direct_dft(white.values)*np.sqrt(8*np.asarray(expected)), atol=2e-12)
        self.assertEqual(sample.metadata['sample_rate_hz'], 8)
        self.assertTrue(sample.metadata['periodic_covariance'])
        self.assertEqual(sample.values.imag.max(), 0)
        flat = Noise('specified_noise', dict(frequency_hz=[0,4], density=[.25,.25], complex=False))
        shaped = generate_noise(flat,8,4,rate=8)[0]
        np.testing.assert_allclose(shaped.values, math.sqrt(2)*white.values, atol=2e-12)

    def test_complex_density_preserves_frequency_sign(self):
        model = Noise('specified_noise', dict(frequency_hz=[-4,0,3,4], density=[0,0,3,0], complex=True))
        count, rate, seed = 9, 9, 7
        spectrum = noise_spectrum(model,count,rate=rate)
        np.testing.assert_array_equal(spectrum.values, [0,0,0,0,0,1,2,3,0])
        white = generate_noise(Noise('white_noise', dict(variance=1,complex=True)),count,seed)[0]
        shaped = generate_noise(model,count,seed,rate=rate)[0]
        np.testing.assert_allclose(direct_dft(shaped.values), direct_dft(white.values)*np.sqrt(rate*spectrum.values), atol=2e-12)
        self.assertEqual(spectrum.metadata['variance'], 6)

    def test_color_slopes_and_power(self):
        for color, exponent in [('pink',-1),('brown',-2),('blue',1),('violet',2)]:
            with self.subTest(color=color):
                model = Noise('colored_noise', dict(color=color, variance=3, low_hz=1, high_hz=3, complex=False))
                spectrum = noise_spectrum(model,8,rate=8)
                levels = spectrum.values.real
                self.assertAlmostEqual(levels[6]/levels[5], 2.**exponent, delta=2e-12)
                self.assertAlmostEqual(sum(levels)*spectrum.step, 3, delta=2e-12)
                self.assertEqual(levels[0], 0)
                self.assertEqual(levels[4], 0)

    def test_fir_white_prehistory_matches_linear_convolution(self):
        taps = [.5,-1.,.25]
        model = Noise('fir_noise', dict(taps=taps, variance=4, complex=False))
        rng_model = Noise('white_noise', dict(variance=4, complex=False))
        white = generate_noise(rng_model, 19, 24)[0].values.real
        expected = [sum(tap*white[i+len(taps)-1-j] for j,tap in enumerate(taps)) for i in range(17)]
        sample = generate_noise(model,17,24)[0]
        np.testing.assert_allclose(sample.values, expected, atol=2e-12)
        powers = noise_spectrum(model, 4, rate=8)
        expected_psd = [4/8*abs(sum(h*cmath.exp(-2j*math.pi*f*k/8) for k,h in enumerate(taps)))**2 for f in powers.axis]
        np.testing.assert_allclose(powers.values, expected_psd, atol=2e-12)
        self.assertEqual(sample.metadata['theoretical_variance'], 4*sum(t*t for t in taps))
        self.assertNotEqual(sample.values[0], 0)
        complex_fir = Noise('fir_noise', dict(taps={'real':[1,0], 'imag':[0,1]}, variance=2, complex=True))
        self.assertEqual(noise_spectrum(complex_fir, 9, rate=9).metadata['variance'], 4.)
        self.assertEqual(generate_noise(complex_fir, 8, 11)[0].metadata['theoretical_variance'], 4.)

    def test_impulse_mixture_uses_declared_conditional_variances(self):
        options = dict(background_std=.2, impulse_std=2, complex=False)
        model = Noise('impulsive_noise', dict(**options, impulse_probability=.05))
        theory = .95*.2**2+.05*2**2
        self.assertAlmostEqual(noise_spectrum(model,16,rate=8).metadata['variance'], theory)
        for probability,width in [(0,.2),(1,2)]:
            boundary = Noise('impulsive_noise', dict(**options,impulse_probability=probability))
            result = generate_noise(boundary,8,24)[0]
            expected = generate_noise(Noise('white_noise', dict(variance=width**2,complex=False)),8,24)[0]
            np.testing.assert_array_equal(result.values, expected.values)

    def test_seeded_lag_variance_and_proper_white_process(self):
        size, replicas, seed = 16, 2048, 2026112904
        noise = Noise('colored_noise', dict(color='pink', variance=2, low_hz=1, high_hz=8, complex=False))
        paths = generate_noise(noise,size,seed,replicas=replicas,rate=16)
        data = np.stack([record.values.real[:2] for record in paths])
        power = [1/abs(k) if k else 0 for k in range(-8,8)]
        expected = 2*sum(w*math.cos(2*math.pi*k/size) for k,w in zip(range(-8,8),power,strict=True))/sum(power)
        self.assertAlmostEqual(np.mean(data[:,0]**2), 2, delta=6*math.sqrt(8/replicas))
        self.assertAlmostEqual(np.prod(data,axis=1).mean(), expected, delta=6*math.sqrt((4+expected**2)/replicas))
        white = Noise('white_noise', dict(variance=4,complex=True))
        c = np.asarray([record.values[0] for record in generate_noise(white,size,seed,replicas=replicas)])
        for values in (c.real,c.imag):
            self.assertAlmostEqual(np.mean(values**2), 2, delta=6*math.sqrt(8/replicas))
        self.assertAlmostEqual(np.mean(c.real*c.imag), 0, delta=12/math.sqrt(replicas))

    def test_validation_and_no_partial_work(self):
        for family, options in [
            ('wrong',{}), ('white_noise',{}), ('white_noise',dict(variance=1,complex=1)),
            ('colored_noise',dict(color='red',variance=1,low_hz=0,high_hz=1,complex=False)),
            ('colored_noise',dict(color='brown',variance=1,low_hz=0,high_hz=1,complex=False)),
            ('colored_noise',dict(color='blue',variance=1,low_hz=1,high_hz=1,complex=False)),
            ('specified_noise',dict(frequency_hz=[0,0], density=[1,1], complex=False)),
            ('specified_noise',dict(frequency_hz=[0,1], density=[-1,1], complex=False)),
            ('specified_noise',dict(frequency_hz=(-1,1), density=[1,1], complex=False)),
            ('fir_noise',dict(taps=[1j],variance=1,complex=False)),
            ('fir_noise',dict(taps={'real':[1], 'imag':[0,0]},variance=1,complex=True)),
            ('fir_noise',dict(taps={'real':[1]},variance=1,complex=True)),
        ]:
            with self.subTest(family=family, options=options), self.assertRaises(ValueError):
                Noise(family, options)
        narrow = Noise('colored_noise', dict(color='blue', variance=1,low_hz=1.1,high_hz=1.2,complex=False))
        spec = Noise('specified_noise',dict(frequency_hz=[1.1,1.2],density=[.1,.2],complex=False))
        for model in (narrow,spec):
            with self.assertRaises(ValueError):
                noise_spectrum(model,4,rate=2)
            with self.assertRaises(ValueError):
                noise_spectrum(model,8,rate=8)
        zero = Noise('colored_noise', dict(color='pink', variance=0,low_hz=1.1,high_hz=1.2,complex=False))
        np.testing.assert_array_equal(generate_noise(zero,8,5,rate=8)[0].values, np.zeros(8))
        event = Event()
        event.set()
        for operation, options in [(noise_spectrum, (8,)), (generate_noise,(8,12))]:
            with self.assertRaises(ResourceLimitError):
                operation(zero,*options,rate=8,execution=ExecutionContext(max_work_bytes=1))
            with self.assertRaises(OperationCancelled):
                operation(zero,*options,rate=8,execution=ExecutionContext(cancel=event))

    def test_cli_reports_spectrum_and_reopens_batch(self):
        p = dict(color='pink',variance=1,low_hz=1,high_hz=4,complex=False)
        model = Noise('colored_noise',p)
        common = ['--family',model.family,'--parameters',json.dumps(p),'--rate','8']

        def invoke(args, code=0):
            stdout, stderr = StringIO(),StringIO()
            with redirect_stdout(stdout),redirect_stderr(stderr):
                self.assertEqual(main(args),code,stderr.getvalue())
            return json.loads(stdout.getvalue()) if code == 0 else stderr.getvalue()

        result = invoke(['inspect',*common,'--bins','8'])
        np.testing.assert_array_equal(result['density'],noise_spectrum(model,8,rate=8).values)
        self.assertIn('posiciones', invoke(['inspect', *common, '--first','2'], 1))
        poisson=['inspect','--family','poisson_process','--parameters','{"initial":3,"event_rate":2}','--rate','8']
        transition=invoke(poisson)['transition']
        self.assertAlmostEqual(transition['event_mean']['value'],.25)
        self.assertIn('bins',invoke([*poisson,'--bins','10'],1))
        with TemporaryDirectory() as folder:
            target = Path(folder)/'noise.slproj'
            result = invoke(['generate',*common,'--count','8','--seed','17','--output',str(target)])
            project, _ = session.load(target)
            self.assertEqual(project.get(result['model_id']),model.document())
            np.testing.assert_array_equal(project.get(result['result_ids'][0]).values,generate_noise(model,8,17,rate=8)[0].values)
