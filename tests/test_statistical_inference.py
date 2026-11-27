"""Independent mathematical oracles for the statistical report contracts."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import itertools
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
from time import monotonic
import unittest

import mpmath
import numpy as np

from signallab_pc import session
from signallab_pc.execution import ExecutionContext, ResourceLimitError
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.probability import Distribution
from signallab_pc.project import Project
from signallab_pc.scientific_storage import save_binary_signal
from signallab_pc.statistical_inference import fit_distribution, infer_record
from signallab_pc.statistics_cli import main
from signallab_pc.statistics_results import store_statistics


def normal_cdf(x):
    return .5 * math.erfc(-x / math.sqrt(2))


class InferenceOracles(unittest.TestCase):
    def test_mean_contrasts_and_two_sided_intervals(self):
        signal = Signal([1, 3], origin=8, metadata={'amplitude_units': 'V', 'sample_rate_hz': 100})
        student = infer_record(signal, 't', iid=True, null=1)
        self.assertEqual(student['inputs'][0], {'amplitude_units': 'V', 'axis_units': 'n', 'domain': 'discrete',
                                                'origin': 8, 'step': 1, 'sample_rate_hz': 100})
        self.assertEqual(student['estimate']['value'], 2)
        self.assertEqual(student['statistic']['value'], 1)
        self.assertAlmostEqual(student['p_value'], .5, delta=2e-12)
        critical = math.tan(math.pi * (.975 - .5))
        np.testing.assert_allclose([row['value'] for row in student['interval']], [2-critical, 2+critical], rtol=2e-11)
        two = infer_record(signal, 'z', iid=True, null=0, known_std=math.sqrt(2))
        self.assertAlmostEqual(two['p_value'], math.erfc(math.sqrt(2)), delta=2e-12)
        for alternative, probability in [('less', normal_cdf(2)), ('greater', normal_cdf(-2))]:
            result = infer_record(signal, 'z', iid=True, null=0, known_std=math.sqrt(2), alternative=alternative)
            self.assertAlmostEqual(result['p_value'], probability, delta=2e-12)
            self.assertEqual(result['interval'], two['interval'])

    def test_variance_ratio_and_welch_against_closed_laws(self):
        signal = Signal([-1, 0, 1])
        chi = infer_record(signal, 'variance', iid=True, null=1)
        self.assertEqual(chi['statistic']['value'], 2)
        self.assertAlmostEqual(chi['p_value'], 2 / math.e, delta=2e-12)
        np.testing.assert_allclose([x['value'] for x in chi['interval']], [-1/math.log(.025), -1/math.log(.975)], rtol=2e-12)
        f_test = infer_record(Signal([-2, 0, 2]), 'f', second=signal, iid=True, null=1)
        self.assertEqual(f_test['degrees_of_freedom'], [2, 2])
        self.assertEqual(f_test['estimate']['value'], 4)
        self.assertAlmostEqual(f_test['p_value'], .4, delta=2e-12)
        np.testing.assert_allclose([x['value'] for x in f_test['interval']], [4/39, 156], rtol=2e-12)
        welch = infer_record(Signal([2, 4]), 'welch', second=Signal([0, 2]), null=0, iid=True)
        expected_t = math.sqrt(2)
        self.assertAlmostEqual(welch['degrees_of_freedom'], 2)
        self.assertAlmostEqual(welch['statistic']['value'], expected_t)
        self.assertAlmostEqual(welch['p_value'], 1 - expected_t / math.sqrt(2 + expected_t**2), delta=2e-12)

    def test_exact_binomial_including_boundary_and_noncentral_counts(self):
        empty = infer_record(Signal([0]*4), 'proportion', iid=True, null=.5, alternative='less')
        self.assertAlmostEqual(empty['p_value'], 1/16, delta=2e-12)
        self.assertEqual(empty['interval'][0]['value'], 0)
        self.assertAlmostEqual(empty['interval'][1]['value'], -math.expm1(math.log(.025)/4), delta=2e-12)
        full = infer_record(Signal([1]*4), 'proportion', iid=True, null=1)
        self.assertEqual(full['p_value'], 1)
        self.assertEqual(full['interval'][1]['value'], 1)
        partial = infer_record(Signal([1, 1, 0, 0, 0, 0]), 'proportion', iid=True, null=.1)
        lower, upper = (bound['value'] for bound in partial['interval'])
        self.assertAlmostEqual(sum(math.comb(6,k)*lower**k*(1-lower)**(6-k) for k in range(2,7)), .025)
        self.assertAlmostEqual(sum(math.comb(6,k)*upper**k*(1-upper)**(6-k) for k in range(3)), .025)

    def test_distribution_diagnostics_and_tail_censoring(self):
        uniform = Distribution('uniform', {'low': 0, 'high': 1})
        ks = infer_record(Signal([.25]), 'ks', iid=True, reference=uniform)
        self.assertEqual(ks['statistic']['value'], .75)
        self.assertEqual(ks['p_value'], .5)
        observed = [-2, -1, 0, 1, 3]
        size = len(observed)
        average = sum(observed)/size
        std = math.sqrt(sum((x-average)**2 for x in observed)/(size-1))
        cdf = [normal_cdf((x-average)/std) for x in observed]
        expected_ad = -size - sum((2*k+1)*(math.log(cdf[k])+math.log1p(-cdf[-1-k])) for k in range(size))/size
        ad = infer_record(Signal(observed), 'ad', iid=True, level=.8)
        self.assertAlmostEqual(ad['statistic']['value'], expected_ad, delta=2e-12)
        self.assertEqual(ad['p_value_relation'], 'at_least')
        self.assertIsNone(ad['reject_null'])
        alternative = [0]*31 + [1]
        ad = infer_record(Signal(alternative), 'ad', iid=True, level=.999)
        self.assertEqual(ad['p_value_relation'], 'at_most')
        self.assertIsNone(ad['reject_null'])
        self.assertTrue(infer_record(Signal(alternative), 'ad', iid=True)['reject_null'])
        sample = [0, 2, 3]
        sse = sum((x-sum(sample)/len(sample))**2 for x in sample)
        shapiro = infer_record(Signal(sample), 'shapiro', iid=True)
        self.assertAlmostEqual(shapiro['statistic']['value'], (max(sample)-min(sample))**2/(2*sse), delta=2e-12)

    def test_ljung_box_and_ranks_with_and_without_ties(self):
        sample = [1, -1, 2, -2, 4]
        count = len(sample)
        deviations = [x-sum(sample)/count for x in sample]
        sse = sum(x*x for x in deviations)
        q = count*(count+2)*sum((sum(a*b for a,b in zip(deviations[k:], deviations[:-k]))/sse)**2/(count-k)
                                  for k in (1,2))
        test = infer_record(Signal(sample), 'ljung_box', iid=True, lags=2)
        self.assertAlmostEqual(test['statistic']['value'], q, delta=2e-12)
        self.assertAlmostEqual(test['p_value'], math.exp(-q/2), delta=2e-12)
        ranked = infer_record(Signal([1,2]), 'mann_whitney', second=Signal([3,4]), iid=True)
        extreme = sum(pair in ((1,2),(3,4)) for pair in itertools.combinations(range(1,5), 2))
        self.assertAlmostEqual(ranked['p_value'], extreme / math.comb(4,2))
        tied = infer_record(Signal([1,2]), 'mann_whitney', second=Signal([2,3]), iid=True)
        self.assertEqual(tied['statistic']['value'], .5)
        self.assertIn('empates', tied['calibration'])

    def test_scaled_estimates_and_log_tail(self):
        near_limit = 1.5e308
        result = infer_record(Signal([near_limit,near_limit]), 'z', iid=True, null=near_limit, known_std=1.)
        self.assertEqual(result['statistic']['value'], 0)
        self.assertEqual(result['estimate']['value'], near_limit)
        values = [near_limit, near_limit, -near_limit, -near_limit, 1e-100]
        result = infer_record(Signal(values), 'z', iid=True, null=0, known_std=math.sqrt(5)*1e-100)
        self.assertEqual(result['estimate']['value'], 2e-101)
        self.assertAlmostEqual(result['statistic']['value'], .2)
        gap = math.ulp(1.)
        result = infer_record(Signal([1., 1.+gap]), 'z', iid=True, null=1, known_std=gap/math.sqrt(2))
        self.assertAlmostEqual(result['statistic']['value'], 1.)
        extreme = infer_record(Signal([-near_limit,near_limit]), 'variance', iid=True, null=1)
        self.assertEqual(extreme['estimate']['status'], 'out_of_range')
        self.assertEqual(extreme['p_value'], 0)
        self.assertEqual(extreme['log_p_value']['status'], 'zero_or_underflow')
        tiny = math.ldexp(1., -1000)
        result = infer_record(Signal([-tiny,tiny]), 'welch', iid=True, null=0, second=Signal([tiny,tiny]))
        self.assertAlmostEqual(result['statistic']['value'], -1.)
        result = infer_record(Signal([1j, 0]), 'z', iid=True, null=0, known_std=1, component='phase')
        self.assertEqual(result['excluded'], [1])
        self.assertEqual(result['inputs'][0]['amplitude_units'], 'rad')
        json.dumps(result, allow_nan=False)

    def test_invalid_inference_leaves_model_assumptions_explicit(self):
        signal = Signal([1,2,3])
        invalid = [
            ('unknown', {}), ('t', {'alternative': 'larger'}), ('z', {'iid': False}),
            ('ks', {'alternative': 'less'}), ('welch', {}), ('t', {'second': signal}),
            ('f', {'second': signal, 'null': 1}), ('f', {'second': [1,2], 'null': 1}),
            ('f', {'second': Signal([2,3,4], metadata={'amplitude_units': 'V'}), 'null': 1}),
            ('t', {'null': 0, 'level': 1}), ('proportion', {'null': .5}),
            ('t', {'null': 0, 'known_std': 1}), ('shapiro', {'null': 0}),
            ('ks', {'lags': 2}), ('ad', {'reference': Distribution('normal', {'mean':0,'std':1})}),
            ('f', {'second': Signal([2,2]), 'null': 1}), ('ad', {}), ('ks', {}),
            ('ljung_box', {'lags': 2, 'fitted_parameters': 2}),
        ]
        for method, options in invalid:
            with self.subTest(method=method, options=options), self.assertRaises(ValueError):
                infer_record(signal, method, **{'iid': True, **options})
        for sample, method, options in [
            (Signal([1]), 't', {'null': 0}), (Signal([1,1]), 't', {'null': 0}),
            (Signal([1,1]), 'welch', {'null':0, 'second': Signal([2,2])}),
            (Signal([1,1,1]), 'shapiro', {}),
            (Signal([.1,.1]), 'ks', {'reference': Distribution('uniform', {'low':0,'high':1})}),
            (Signal([1,2], domain='continuous'), 'ljung_box', {'lags':1}),
        ]:
            with self.subTest(method=method), self.assertRaises(ValueError):
                infer_record(sample, method, iid=True, **options)

    def test_seeded_size_power_coverage_and_mle_bias(self):
        size, replicas, alpha, shift = 32, 256, .05, .5
        generator = np.random.Generator(np.random.PCG64(2026112902))
        under_null, under_shift = generator.standard_normal((2, replicas, size))
        z_size, t_size, z_cover, t_cover, power, ad_size, sw_size, scale_cover = [0]*8
        fitted_means, fitted_variances = [], []
        for sample, moved in zip(under_null, under_shift, strict=True):
            signal = Signal(sample)
            z = infer_record(signal, 'z', iid=True, null=0, known_std=1)
            t = infer_record(signal, 't', iid=True, null=0)
            z_size += z['reject_null']
            t_size += t['reject_null']
            z_cover += z['interval'][0]['value'] <= 0 <= z['interval'][1]['value']
            t_cover += t['interval'][0]['value'] <= 0 <= t['interval'][1]['value']
            power += infer_record(Signal(shift+moved), 'z', iid=True, null=0, known_std=1)['reject_null']
            ad_size += infer_record(signal, 'ad', iid=True)['reject_null']
            sw_size += infer_record(signal, 'shapiro', iid=True)['reject_null']
            model = fit_distribution(signal, 'normal', level=1-alpha, iid=True)
            fit = model['estimated_distribution']['parameters']
            bounds = model['confidence_intervals']['parameters']['std']
            scale_cover += bounds[0]['value'] <= 1 <= bounds[1]['value']
            fitted_means.append(fit['mean'])
            fitted_variances.append(fit['std']**2)
        critical = 1.959963984540054
        expected_power = normal_cdf(-critical-shift*math.sqrt(size)) + normal_cdf(-critical+shift*math.sqrt(size))
        for observed, expected in [(z_size,alpha), (t_size,alpha), (z_cover,1-alpha), (t_cover,1-alpha),
                                   (power,expected_power), (ad_size,alpha), (sw_size,alpha), (scale_cover,1-alpha)]:
            self.assertLessEqual(abs(observed - replicas*expected), 6*math.sqrt(replicas*expected*(1-expected))+1)
        self.assertAlmostEqual(np.mean(fitted_means), 0, delta=6/math.sqrt(size*replicas))
        self.assertAlmostEqual(np.mean(fitted_variances), (size-1)/size, delta=6*math.sqrt(2*(size-1)/replicas)/size)


class FittingAndPersistence(unittest.TestCase):
    def test_confidence_intervals_for_fitted_parameters_invert_independent_pivots(self):
        def interval(sample, family, key, **kwargs):
            fit = fit_distribution(Signal(sample), family, level=.95, iid=True, **kwargs)
            return [end['value'] for end in fit['confidence_intervals']['parameters'][key]]

        expected = [math.sqrt(-1/math.log(.025)), math.sqrt(-1/math.log(.975))]
        np.testing.assert_allclose(interval([-1,0,1], 'normal', 'std'), expected, rtol=2e-12)
        np.testing.assert_allclose(interval([1/math.e,1,math.e], 'lognormal', 'log_std'), expected, rtol=2e-12)
        for family, scale, pivot in [('exponential', [1,3], lambda width: 8/width),
                                     ('rayleigh', [1,3], lambda width: 20/width**2)]:
            lower, upper = interval(scale, family, 'scale')
            for bound, expected_tail in ((lower,.025),(upper,.975)):
                value = pivot(bound)/2
                self.assertAlmostEqual((1+value)*math.exp(-value), expected_tail, delta=2e-12)
        zero, maximum = interval([0]*4, 'poisson', 'rate')
        self.assertEqual(zero, 0)
        self.assertAlmostEqual(maximum, -math.log(.025)/4)
        lower, upper = interval([1,0], 'binomial', 'p', trials=2)
        self.assertAlmostEqual(1-(1-lower)**4, .025, delta=2e-12)
        self.assertAlmostEqual((1-upper)**4 + 4*upper*(1-upper)**3, .025, delta=2e-12)
        self.assertEqual(interval([1,0,0,0], 'bernoulli', 'p'), [lower, upper])
        with self.assertRaises(ValueError):
            fit_distribution(Signal([1,2]), 'normal', level=.95)
        with self.assertRaises(ValueError):
            fit_distribution(Signal([1,2]), 'gamma', level=.95, iid=True)
        with self.assertRaises(ValueError):
            interval([0,1], 'binomial', 'p', trials=1 << 52)

    def test_closed_form_estimators_and_likelihood(self):
        samples = [
            ('normal','ml',[1,3], {'mean': 2., 'std': 1.}, {}),
            ('normal','moments',[1,3], {'mean': 2., 'std': 1.}, {}),
            ('lognormal','ml',[math.exp(-1),math.e], {'log_mean':0.,'log_std':1.}, {}),
            ('rayleigh','ml',[1,3], {'scale':math.sqrt(2.5)}, {}),
            ('rayleigh','moments',[1,3], {'scale':2*math.sqrt(2/math.pi)}, {}),
            ('exponential','ml',[1,3], {'scale':2.}, {}),
            ('uniform','ml',[1,1,3], {'low':1.,'high':3.}, {}),
            ('uniform','moments',[1,3], {'low':2-math.sqrt(3),'high':2+math.sqrt(3)}, {}),
            ('laplace','ml',[0,1,4], {'location':1.,'scale':4/3}, {}),
            ('laplace','moments',[1,3], {'location':2.,'scale':1/math.sqrt(2)}, {}),
            ('gamma','moments',[.5,1.5], {'shape':4.,'scale':.25}, {}),
            ('beta','moments',[.25,.75], {'alpha':1.5,'beta':1.5}, {}),
            ('bernoulli','ml',[0,0,1], {'p':1/3}, {}),
            ('binomial','ml',[1,2,3], {'trials':4,'p':.5}, {'trials':4}),
            ('poisson','ml',[0,1,2], {'rate':1.}, {}),
        ]
        for family, method, values, parameters, options in samples:
            with self.subTest(family=family, method=method):
                result = fit_distribution(Signal(values), family, estimator=method, **options)
                fit = result['estimated_distribution']['parameters']
                self.assertEqual(fit.keys(), parameters.keys())
                for parameter, value in parameters.items():
                    self.assertAlmostEqual(fit[parameter], value, delta=2e-12)
                self.assertTrue(result['parameters_from_same_sample'])
                self.assertEqual(result['log_likelihood']['status'], 'finite')
        normal = fit_distribution(Signal([1,3]), 'normal')
        self.assertAlmostEqual(normal['log_likelihood']['value'], -1-math.log(2*math.pi))
        outside = fit_distribution(Signal([0,0,0,0,10]), 'uniform', estimator='moments')
        self.assertEqual(outside['log_likelihood']['status'], 'zero_joint_likelihood')
        boundary = fit_distribution(Signal([0,2]), 'rayleigh', estimator='moments')
        self.assertEqual(boundary['log_likelihood']['status'], 'zero_joint_likelihood')

    def test_shape_fits_satisfy_independent_likelihood_equations(self):
        samples = [.1,.3,.4,.6,.8,.85]
        count = len(samples)
        fitted = fit_distribution(Signal(samples), 'gamma')['estimated_distribution']['parameters']
        shape, scale = fitted['shape'], fitted['scale']
        self.assertAlmostEqual(shape*scale, sum(samples)/count, delta=2e-12)
        self.assertAlmostEqual(float(mpmath.digamma(shape))+math.log(scale), sum(map(math.log,samples))/count, delta=2e-12)
        fitted = fit_distribution(Signal(samples), 'beta')['estimated_distribution']['parameters']
        alpha, beta = fitted['alpha'], fitted['beta']
        total = mpmath.digamma(alpha+beta)
        for parameter, observed in [(alpha,samples),(beta,[1-x for x in samples])]:
            self.assertAlmostEqual(float(mpmath.digamma(parameter)-total), sum(map(math.log,observed))/count, delta=2e-8)

    def test_fit_rejects_incompatible_sample_and_model(self):
        for values, family, options in [
            ([1,2], 'cauchy', {}), ([1,2], 'lognormal', {'estimator':'moments'}),
            ([1], 'normal', {}), ([1,1], 'normal', {}), ([1,1], 'gamma', {}),
            ([0,1], 'lognormal', {}), ([-1,1], 'exponential', {}), ([.25,1], 'beta', {}),
            ([.25,1], 'poisson', {}), ([0,2], 'bernoulli', {}), ([0,2], 'binomial', {}), ([0,2], 'rayleigh', {}),
        ]:
            with self.subTest(family=family, values=values), self.assertRaises(ValueError):
                fit_distribution(Signal(values), family, **options)
        with self.assertRaises(ValueError):
            fit_distribution([1,2], 'normal')
        with self.assertRaises(ValueError):
            fit_distribution(Signal([1,2]), 'normal', trials=4)

    def test_execution_and_atomic_parents(self):
        signal, other = Signal([1,2,3]), Signal([-1,0,1])
        event = Event()
        event.set()
        for method, arguments in [(infer_record, ('t',)), (fit_distribution, ('normal',))]:
            options = {'iid':True,'null':0} if method is infer_record else {}
            for exception, context in ((ResourceLimitError, ExecutionContext(max_work_bytes=1)),
                                       (OperationCancelled, ExecutionContext(cancel=event)),
                                       (TimeoutError, ExecutionContext(deadline=monotonic()-1))):
                with self.assertRaises(exception):
                    method(signal, *arguments, execution=context, **options)
        project = Project()
        parent = project.add(signal)
        result = infer_record(signal, 'welch', second=other, null=0, iid=True)
        wrong = other.copy_with(values=[1,2,3])
        with self.assertRaises(ValueError):
            store_statistics(project, result, ((signal,parent,()),(wrong,None,(parent,))), 'Comparación')
        self.assertEqual(len(project.headers()), 1)
        with self.assertRaises(OperationCancelled):
            store_statistics(project, result, ((signal,parent,()),(other,None,())), 'Comparación',
                             execution=ExecutionContext(cancel=event))
        self.assertEqual(len(project.headers()), 1)
        keys, answer = store_statistics(project, result, ((signal,parent,()),(other,None,(parent,))), 'Comparación')
        self.assertEqual(project.headers()[-1]['parents'], keys)
        self.assertEqual(project.get(answer), result)

    def test_console_parity_and_output_preservation(self):
        signal, other = Signal([1,2,3]), Signal([-1,0,1])
        project = Project()
        first, second = project.add(signal), project.add(other)
        with TemporaryDirectory() as folder:
            base, out, binary = (Path(folder)/name for name in ['input.slproj', 'output.slproj', 'other.slbin'])
            session.save(base, project, session.empty_workspace())
            save_binary_signal(other, binary)
            base_args = ['--session',str(base),'--record',first,'--output',str(out)]

            def invoke(args, code):
                stdout, stderr = StringIO(), StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    actual = main(args)
                self.assertEqual(actual, code, stderr.getvalue())
                return json.loads(stdout.getvalue()) if code == 0 else stderr.getvalue()

            paths = [['--second-record', second], ['--second-signal', str(binary)]]
            for path in paths:
                args = ['infer', *base_args, '--method','welch','--null','0','--iid',*path]
                receipt = invoke(args, 0)
                reopened, _ = session.load(out)
                self.assertEqual(reopened.get(receipt['result_id']), infer_record(signal, 'welch', second=other, null=0, iid=True))
                self.assertEqual(reopened.headers()[-1]['parents'], [first, receipt['second_source_id']])
            fit = invoke(['fit',*base_args,'--family','normal'], 0)
            reopened, _ = session.load(out)
            self.assertEqual(reopened.get(fit['result_id']), fit_distribution(signal, 'normal'))
            saved = out.read_bytes()
            args = ['infer', *base_args, '--method','welch','--null','0','--iid']
            self.assertIn('otro registro', invoke([*args, '--second-record',first], 1))
            self.assertIn('archivo distinto', invoke([*args, '--second-signal',str(out)], 1))
            self.assertEqual(out.read_bytes(), saved)
