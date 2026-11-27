import json
import math
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event

import numpy as np

from signallab_pc import session
from signallab_pc.execution import ExecutionContext
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.optimal_estimation import linear_gaussian
from signallab_pc.project import Project
from signallab_pc.resources import ResourceLimitError
from signallab_pc.stochastic_cli import main
from signallab_pc.wiener_filter import store_wiener, wiener_fir, wiener_hopf


def matched_records():
    observed = np.asarray([2-1j, -3j, 1, 3+2j, -1, 4j, 2.5, -2j, .5])
    h = np.asarray([.5+.25j, -.75j])
    bias = 1.25-.25j
    reference = [bias + h[0]*right + h[1]*left for left, right in zip(observed, observed[1:])]
    source = Signal(observed, -3, metadata={'sample_rate_hz':4, 'time_start_s':2, 'amplitude_units':'V'})
    desired = Signal(reference, -2, metadata={'sample_rate_hz':4, 'time_start_s':2.25, 'amplitude_units':'V'})
    return source, desired, h, bias


class GaussianEstimationTests(unittest.TestCase):
    def test_correlated_observations_match_hand_calculated_gls_and_posterior(self):
        result = linear_gaussian([3, 1], [[1], [2]], [[2, 1], [1, 3]],
                                 prior_mean=[2], prior_covariance=[[4]], parameter=[1])
        ml, posterior, reference = (result[key] for key in ('ml', 'posterior', 'reference'))
        self.assertAlmostEqual(ml['estimate'][0], 6/7)
        self.assertAlmostEqual(ml['cramer_rao'][0][0], 5/7)
        self.assertAlmostEqual(result['fisher_information'][0][0], 7/5)
        self.assertAlmostEqual(reference['log_likelihood']['value'], -math.log(math.tau)-math.log(5)/2-9/5)
        for decision in ('map', 'mmse', 'lmmse'):
            self.assertAlmostEqual(posterior[decision][0], 34/33)
        self.assertAlmostEqual(posterior['bayes_mse']['value'], 20/33)
        self.assertAlmostEqual(reference['posterior_estimator_bias'][0], 5/33)
        self.assertAlmostEqual(reference['posterior_estimator_variance'][0], (20/33)**2*7/5)

    def test_unobserved_coordinate_keeps_prior_variance_and_has_no_unique_ml(self):
        result = linear_gaussian([4], [[1, 0, 0]], [[3]],
                                 prior_mean=[0, 3, 5], prior_covariance=np.diag([1, 2, 4]))
        self.assertEqual(result['rank'], 1)
        self.assertIsNone(result['ml'])
        np.testing.assert_allclose(result['posterior']['map'], [1, 3, 5])
        np.testing.assert_allclose(result['posterior']['covariance'], np.diag([.75, 2, 4]))

    def test_high_information_preserves_positive_posterior_covariance(self):
        result = linear_gaussian([2], [[1]], [[1e-24]], prior_mean=[0], prior_covariance=[[2]])
        self.assertAlmostEqual(result['posterior']['mmse'][0], 2)
        self.assertAlmostEqual(result['posterior']['covariance'][0][0] / 1e-24, 1)

    def test_partial_prior_and_invalid_covariance_are_rejected(self):
        for observations, design, covariance, options in (
            ([1], [[1], [2]], [[1]], {}),
            ([1, 2], [[1], [2]], [[2, 0], [1, 2]], {}),
            ([1, 2], [[1], [2]], [[1, 2], [2, 1]], {}),
            ([1], [[1]], [[0]], {}),
            ([1], [[1]], [[1, 0], [0, 1]], {}),
            ([1], [[1]], [[1]], {'prior_mean':[0]}),
            ([1j], [[1]], [[1]], {}),
        ):
            with self.subTest(options=options, observations=observations, covariance=covariance):
                with self.assertRaises(ValueError):
                    linear_gaussian(observations, design, covariance, **options)
        with self.assertRaises(ResourceLimitError):
            linear_gaussian([1], [[1]], [[1]], execution=ExecutionContext(max_work_bytes=1))

    def test_fisher_information_overflow_yields_actionable_numerical_error(self):
        with self.assertRaisesRegex(FloatingPointError, 'precisión disponible'):
            linear_gaussian([1], [[1e155]], [[1]])


class WienerFilterTests(unittest.TestCase):
    def test_complex_wiener_hopf_conjugation_and_theoretical_mse(self):
        # Independent model: x[n] = w[n] + j w[n-1]/2, d = h*x + e.
        # w is proper white with unit power and e independently has power 0.3.
        rx = [1.25, .5j]
        h = np.asarray([.25j, -.5])
        p = np.asarray([1.25*h[0]-.5j*h[1], .5j*h[0]+1.25*h[1]])
        # Direct synthesis equivalent: d = .25j*w - .625*w[n-1] - .25j*w[n-2] + e.
        p_d = .25**2+.625**2+.25**2+.3
        outcome = wiener_hopf(rx, p, p_d)
        actual = np.asarray(outcome['coefficients']['real']) + 1j*np.asarray(outcome['coefficients']['imag'])
        np.testing.assert_allclose(actual, h, atol=2e-15)
        self.assertAlmostEqual(outcome['theoretical_mse']['value'], .3)

    def test_singular_wiener_uses_minimum_norm_and_rejects_impossible_moments(self):
        result = wiener_hopf([2, 2], [1, 1], 1)
        self.assertEqual(result['rank'], 1)
        np.testing.assert_allclose(result['coefficients']['real'], [.25,.25])
        self.assertAlmostEqual(result['theoretical_mse']['value'], .5)
        self.assertEqual(wiener_hopf([0,0], [0,0], 3)['theoretical_mse']['value'], 3)
        for x, p, d in (([1,2],[0,0],1), ([1,1],[1,-1],2), ([1],[2],1), ([2],[1],0),
                        ([1j],[0],2), ([0,1],[0,0],1), ([1],[0],-1), ([1],[0,0],1)):
            with self.subTest(x=x, p=p, d=d), self.assertRaises(ValueError):
                wiener_hopf(x,p,d)

    def test_empirical_affine_fit_recovers_complex_taps_and_preserves_clock(self):
        source, desired, taps, bias = matched_records()
        result = wiener_fir(source, desired, 2, fit_offset=True, reserve=3)
        report, model, estimate, error, reference, observed = result
        np.testing.assert_allclose(model.b, taps, atol=2e-14)
        self.assertAlmostEqual(complex(report['offset']['real'], report['offset']['imag']), bias)
        self.assertEqual(report['validation_samples'], 3)
        self.assertLess(report['validation_mse']['value'], 1e-27)
        np.testing.assert_allclose(estimate.values, desired.values, atol=2e-14)
        np.testing.assert_allclose(error.values, 0., atol=2e-14)
        np.testing.assert_array_equal(reference.values, desired.values)
        np.testing.assert_array_equal(observed.values, source.values[1:])
        self.assertEqual((estimate.origin, estimate.metadata['time_start_s'], model.sample_period_s), (-2, 2.25, .25))

    def test_holdout_is_excluded_from_fit_and_denominator_uses_held_out_samples(self):
        x = Signal([1, -2, 3, -1, 2, 1])
        y = Signal([2, -4, 6, -2, 5, 4])
        result = wiener_fir(x,y,1,reserve=2)
        self.assertAlmostEqual(result[1].b[0].real, 2)
        self.assertAlmostEqual(result[0]['validation_mse']['value'], (1+4)/2)
        with self.assertRaises(ValueError):
            wiener_fir(x,y,4,reserve=2)
        with self.assertRaises(ValueError):
            wiener_fir(x,Signal([2, 3], origin=10),1)

    def test_subnormal_covariance_preserves_unitless_wiener_taps(self):
        result = wiener_hopf([2e-320, 0], [1e-320, 0], 1e-320)
        np.testing.assert_allclose(result['coefficients']['real'], [.5,0], atol=1e-14)
        self.assertEqual(result['theoretical_mse']['value'], 5e-321)

    def test_cancelled_registration_keeps_project_empty_and_can_retry(self):
        x,d,*_ = matched_records()
        result = wiener_fir(x,d,2,fit_offset=True)
        inputs = [(x,None,()),(d,None,())]
        project = Project()
        cancel = Event()
        cancel.set()
        with self.assertRaises(OperationCancelled):
            store_wiener(project, result, inputs, execution=ExecutionContext(cancel=cancel))
        self.assertEqual(project.headers(), [])
        saved = store_wiener(project, result, inputs)
        headers = {row['id']:row for row in project.headers()}
        self.assertEqual(headers[saved['report']]['parents'], saved['sources'])
        self.assertEqual(headers[saved['estimate']]['parents'], [saved['report']])

    def test_cli_produces_reopenable_estimators_with_lineage(self):
        with TemporaryDirectory() as folder:
            model, output, base = (Path(folder)/name for name in ('spec.json','result.slproj','record.slproj'))
            available = Project()
            x,d,h,_ = matched_records()
            observed, desired = available.add(x), available.add(d)
            session.save(base, available, session.empty_workspace())
            cases = (
                ('estimate-gaussian', {'observations':[3], 'design':[[1]], 'measurement_covariance':[[2]]}),
                ('wiener-model', {'autocorrelation':{'real':[2], 'imag':[0]}, 'cross_correlation':[1], 'target_power':1}),
                ('wiener', None),
            )
            for command, spec in cases:
                if spec is not None:
                    model.write_text(json.dumps(spec), encoding='utf-8')
                    args = ['--model', str(model)]
                else:
                    args = ['--session', str(base), '--record', observed, '--second-record', desired, '--length', '2', '--offset']
                stdout, stderr = StringIO(), StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    code = main([command,*args,'--output',str(output)])
                self.assertEqual(code, 0, stderr.getvalue())
                receipt = json.loads(stdout.getvalue())
                saved,_ = session.load(output)
                report = saved.get(receipt['report'])
                if command == 'estimate-gaussian':
                    self.assertAlmostEqual(report['ml']['estimate'][0], 3)
                elif command == 'wiener-model':
                    np.testing.assert_allclose(saved.get(receipt['system']).b, [.5])
                else:
                    self.assertEqual(receipt['sources'], [observed,desired])
                    np.testing.assert_allclose(saved.get(receipt['system']).b, h, atol=2e-14)
