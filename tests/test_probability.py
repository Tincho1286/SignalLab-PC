"""Reference cases for the Phase 05 distribution services and headless entry point."""

from pathlib import Path
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import math
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Event
import unittest

import mpmath as mp
import numpy as np

from signallab_pc.execution import ExecutionContext, ResourcePool
from signallab_pc.jobs import OperationCancelled
from signallab_pc.multivariate_probability import (
    Gaussian, Multinomial, array_from_parts, gaussian_condition, gaussian_density, gaussian_marginal, gaussian_transform,
    generate_gaussian, generate_multinomial,
)
from signallab_pc.probability import (
    Distribution, FAMILIES, distribution_value, generate_realizations, interval_probability, moment, population,
)
from signallab_pc.resources import ResourceLimitError
from signallab_pc.session import load


def value(distribution, function, argument):
    result = distribution_value(distribution, function, argument)
    if result['status'] != 'finite':
        raise AssertionError(result)
    return result['value']


class UnivariateProbabilityTests(unittest.TestCase):
    def test_discrete_mass_against_elementary_laws(self):
        pairs = [
            ('bernoulli', {'p': .3}, 1, .3),
            ('binomial', {'trials': 8, 'p': .25}, 3, math.comb(8, 3) * .25**3 * .75**5),
            ('negative_binomial', {'successes': 3, 'p': .4}, 5, math.comb(7, 2) * .4**3 * .6**5),
            ('poisson', {'rate': 2}, 3, math.exp(-2) * 8 / 6),
            ('geometric', {'p': .25}, 4, .25 * .75**3),
            ('hypergeometric', {'population': 10, 'successes': 4, 'draws': 3}, 2,
             math.comb(4, 2) * math.comb(6, 1) / math.comb(10, 3)),
            ('discrete_uniform', {'low': -2, 'high': 3}, 3, 1 / 6),
            ('categorical', {'probabilities': [0, .125, .5, .375, 0]}, 2, .5),
        ]
        for name, parameters, x, expected in pairs:
            with self.subTest(family=name):
                law = Distribution(name, parameters)
                self.assertTrue(law.discrete)
                self.assertTrue(math.isclose(value(law, 'density', x), expected, rel_tol=1e-12))
                self.assertEqual(value(law, 'density', x + .5), 0)
                for probability in (.13, .77, .999):
                    q = value(law, 'quantile', probability)
                    self.assertLess(value(law, 'cdf', q - 1), probability)
                    self.assertGreaterEqual(value(law, 'cdf', q), probability)
                self.assertAlmostEqual(value(law, 'cdf', x) + value(law, 'survival', x), 1)
                self.assertEqual(len(generate_realizations(law, 10, 11)[0].values), 10)

    def test_continuous_densities_against_formulas(self):
        beta = math.gamma(2.5) * math.gamma(3.5) / math.gamma(6)
        pairs = [
            ('uniform', {'low': -1, 'high': 4}, 2, .2),
            ('normal', {'mean': 1, 'std': 2}, 3, math.exp(-.5) / (2 * math.sqrt(math.tau))),
            ('exponential', {'scale': 3}, 2, math.exp(-2 / 3) / 3),
            ('gamma', {'shape': 3, 'scale': 2}, 4, 4 * math.exp(-2) / 4),
            ('beta', {'alpha': 2, 'beta': 3}, .4, 12 * .4 * .6**2),
            ('rayleigh', {'scale': 2}, 3, 3 / 4 * math.exp(-9 / 8)),
            ('rician', {'ratio': .75, 'scale': 2}, 2, float(
                mp.exp(-(1 + mp.mpf('.75')**2) / 2) * mp.besseli(0, .75) / 2)),
            ('nakagami', {'shape': 1, 'scale': 2}, 3, 6 / 4 * math.exp(-9 / 4)),
            ('weibull', {'shape': 2, 'scale': 3}, 2, 4 / 9 * math.exp(-4 / 9)),
            ('lognormal', {'log_mean': math.log(2), 'log_std': .5}, 2,
             1 / math.sqrt(math.tau)),
            ('chi_square', {'df': 4}, 3, 3 / 4 * math.exp(-1.5)),
            ('student_t', {'df': 6}, 1, math.gamma(3.5) / (math.sqrt(6 * math.pi) * 2) * (7 / 6)**-3.5),
            ('f', {'df_num': 5, 'df_den': 7}, 2, (5 / 7)**2.5 * 2**1.5 / (beta * (17 / 7)**6)),
            ('laplace', {'location': 1, 'scale': 2}, 2, math.exp(-.5) / 4),
            ('cauchy', {'location': 1, 'scale': 2}, 3, 1 / (4 * math.pi)),
        ]
        for name, parameters, x, expected in pairs:
            with self.subTest(family=name):
                law = Distribution(name, parameters)
                self.assertFalse(law.discrete)
                self.assertTrue(math.isclose(value(law, 'density', x), expected, rel_tol=1e-12))
                self.assertAlmostEqual(value(law, 'log_density', x), math.log(expected))
                for probability in (.1, .5, .975):
                    q = value(law, 'quantile', probability)
                    self.assertAlmostEqual(value(law, 'cdf', q), probability, delta=2e-12)
                self.assertAlmostEqual(value(law, 'cdf', x) + value(law, 'survival', x), 1)
                self.assertEqual(len(generate_realizations(law, 10, 11)[0].values), 10)
        self.assertEqual(len(pairs) + 8, len(FAMILIES))

    def test_intervals_and_small_normal_tails(self):
        normal = Distribution('normal', {'mean': 0, 'std': 1})
        quadratic_tail = math.erfc(10 / math.sqrt(2)) / 2
        self.assertTrue(math.isclose(value(normal, 'survival', 10), quadratic_tail, rel_tol=1e-12))
        reference = quadratic_tail - math.erfc(11 / math.sqrt(2)) / 2
        self.assertTrue(math.isclose(interval_probability(normal, 10, 11)['value'], reference, rel_tol=1e-12))
        self.assertAlmostEqual(interval_probability(normal, -11, -10)['log_value'], math.log(reference))
        tiny = interval_probability(normal, 40, 41)
        self.assertEqual((tiny['value'], tiny['status']), (0, 'underflow'))
        self.assertLess(tiny['log_value'], -800)
        binomial = Distribution('binomial', {'trials': 5, 'p': .5})
        self.assertAlmostEqual(interval_probability(binomial, 2, 2)['value'], 10 / 32)
        self.assertEqual(interval_probability(binomial, 2.01, 2.99)['value'], 0)
        self.assertAlmostEqual(interval_probability(binomial, -1.1, 9.5)['value'], 1)
        self.assertEqual(interval_probability(normal, 1, 1)['value'], 0)
        with self.assertRaises(ValueError):
            interval_probability(normal, 1, 0)

    def test_rician_survival_and_rayleigh_limit(self):
        with mp.workdps(120):
            reference = mp.quad(lambda r: r * mp.exp(-(r*r + 400)/2) * mp.besseli(0, 20*r),
                                [40, mp.mpf('40.2'), 41, 44, mp.inf])
        law = Distribution('rician', {'ratio': 20, 'scale': 1})
        self.assertTrue(math.isclose(value(law, 'survival', 40), float(reference), rel_tol=1e-12))
        limit = Distribution('rician', {'ratio': 0, 'scale': 2})
        self.assertAlmostEqual(value(limit, 'survival', 3), math.exp(-9 / 8))

    def test_moments_and_explicit_special_values(self):
        normal = Distribution('normal', {'mean': 2, 'std': 3})
        self.assertEqual(moment(normal, 2)['value'], 13)
        self.assertAlmostEqual(moment(normal, 4)['value'], 16 + 6 * 4 * 9 + 3 * 81)
        self.assertEqual(moment(normal, 0)['value'], 1)
        self.assertEqual(population(normal)['variance']['value'], 9)
        self.assertEqual(distribution_value(normal, 'quantile', 1)['status'], 'unbounded')
        cauchy = Distribution('cauchy', {'location': 0, 'scale': 1})
        self.assertEqual(moment(cauchy, 1)['status'], 'undefined')
        self.assertEqual(moment(cauchy, 2)['status'], 'divergent')
        self.assertEqual(population(cauchy)['variance']['status'], 'undefined')
        student = Distribution('student_t', {'df': 1.5})
        self.assertEqual(population(student)['variance']['status'], 'divergent')
        fisher = Distribution('f', {'df_num': 4, 'df_den': 2})
        self.assertEqual(moment(fisher, 1)['status'], 'divergent')
        gamma = Distribution('gamma', {'shape': .5, 'scale': 1})
        self.assertEqual(distribution_value(gamma, 'density', 0)['status'], 'singular_density')
        self.assertEqual(distribution_value(gamma, 'log_cdf', 0)['status'], 'zero_probability')
        self.assertEqual(distribution_value(gamma, 'log_density', -1)['status'], 'zero_density')
        json.dumps(population(cauchy), allow_nan=False)

    def test_point_laws(self):
        rows = [
            ('bernoulli', {'p': 0}, 0), ('binomial', {'trials': 3, 'p': 1}, 3),
            ('poisson', {'rate': 0}, 0), ('negative_binomial', {'successes': 2, 'p': 1}, 0),
            ('geometric', {'p': 1}, 1), ('hypergeometric', {'population': 1, 'successes': 1, 'draws': 1}, 1),
            ('discrete_uniform', {'low': -2, 'high': -2}, -2),
        ]
        for family, parameters, point in rows:
            with self.subTest(family=family):
                law = Distribution(family, parameters)
                self.assertEqual(moment(law, 4)['value'], point**4)
                self.assertEqual(population(law)['variance']['value'], 0)
                self.assertEqual(value(law, 'cdf', point - 1), 0)
                self.assertEqual(value(law, 'cdf', point), 1)
                for q in (0, .5, 1):
                    self.assertEqual(value(law, 'quantile', q), point)
                self.assertEqual(interval_probability(law, point, point)['value'], 1)
        law = Distribution('categorical', {'probabilities': [0, .5, .5, 0]})
        self.assertEqual(value(law, 'quantile', 0), 1)
        self.assertEqual(value(law, 'quantile', 1), 2)

    def test_invalid_parameters_and_immutable_specification(self):
        rows = [
            ('unknown', {}), ('normal', {'std': 2}), ('normal', {'mean': 0, 'std': -1}),
            ('bernoulli', {'p': True}), ('binomial', {'trials': 2.5, 'p': .1}),
            ('bernoulli', {'p': 1.01}), ('poisson', {'rate': math.nan}),
            ('hypergeometric', {'population': 3, 'successes': 2, 'draws': 4}),
            ('uniform', {'low': 1, 'high': 1}), ('discrete_uniform', {'low': -1, 'high': -2}),
            ('uniform', {'low': -1e308, 'high': 1e308}),
            ('lognormal', {'log_mean': 1e5, 'log_std': 1}), ('lognormal', {'log_mean': -1e5, 'log_std': 1}),
            ('categorical', {'probabilities': []}), ('categorical', {'probabilities': [.75, .75]}),
        ]
        for name, params in rows:
            with self.subTest(family=name), self.assertRaises(ValueError):
                Distribution(name, params)
        parameters = {'probabilities': [.2, .8]}
        law = Distribution('categorical', parameters)
        parameters['probabilities'][0] = 1
        self.assertEqual(law.parameters['probabilities'], (.2, .8))
        for operation, argument in (('unknown', 0), ('quantile', -1), ('cdf', np.inf)):
            with self.assertRaises(ValueError):
                distribution_value(law, operation, argument)

    def test_realizations_reproducible_with_scale_and_substream_identity(self):
        law = Distribution('normal', {'mean': 2, 'std': 3})
        count, seed = 20_000, 20261127
        streams = generate_realizations(law, count, seed, replicas=2, rate=800, origin=-4)
        solo, = generate_realizations(law, count, seed, rate=800, origin=-4)
        np.testing.assert_array_equal(streams[0].values, solo.values)
        self.assertFalse(np.array_equal(streams[0].values, streams[1].values))
        for index, record in enumerate(streams):
            self.assertLess(abs(record.values.mean().real - 2), 6 * 3 / math.sqrt(count))
            self.assertEqual(record.metadata['substream'], [index])
            self.assertEqual(record.metadata['sample_rate_hz'], 800)
            self.assertEqual(record.origin, -4)

    def test_budget_cancellation_and_axis_overflow(self):
        law = Distribution('poisson', {'rate': 2})
        with self.assertRaises(ResourceLimitError):
            generate_realizations(law, 1000, 12, execution=ExecutionContext(max_work_bytes=10))
        event = Event()
        event.set()
        with self.assertRaises(OperationCancelled):
            generate_realizations(law, 10, 12, execution=ExecutionContext(cancel=event))
        with self.assertRaises(ValueError):
            generate_realizations(law, 10, 12, origin=(1 << 63) - 1)


class JointProbabilityTests(unittest.TestCase):
    def test_gaussian_marginal_conditional_density_and_transform(self):
        means = [2, 3]
        model = Gaussian(means, [[4, 2], [2, 3]])
        means[0] = -42
        density = gaussian_density(model, [2, 3])
        self.assertAlmostEqual(density['density']['value'], 1 / (math.tau * math.sqrt(8)))
        marginal = gaussian_marginal(model, [1])
        np.testing.assert_array_equal(marginal.covariance, [[3]])
        condition = gaussian_condition(model, [0], [6])
        np.testing.assert_allclose(condition.mean, [5])
        np.testing.assert_allclose(condition.covariance, [[2]])
        transformed = gaussian_transform(model, [[1, -1]], offset=[4])
        np.testing.assert_array_equal(transformed.mean, [3])
        np.testing.assert_array_equal(transformed.covariance, [[3]])
        with self.assertRaises(ValueError):
            model.mean.setflags(write=True)

    def test_gaussian_complex_pseudocovariance_and_proper_conditional(self):
        model = Gaussian([1 + 1j, -1j], [[4, 1 + 1j], [1 - 1j, 6]], True,
                         [[1 + 1j, .5 - 1j], [.5 - 1j, 2]])
        records = generate_gaussian(model, 20_000, 20261128)
        coordinates = np.stack([records[0].values.real, records[1].values.real,
                                records[0].values.imag, records[1].values.imag])
        reference = np.asarray([[2.5, .75, .5, -1], [.75, 4, 0, 0],
                                [.5, 0, 1.5, .25], [-1, 0, .25, 2]])
        error = np.sqrt((np.outer(reference.diagonal(), reference.diagonal()) + reference**2) / 19_999)
        self.assertTrue(np.all(abs(np.cov(coordinates) - reference) < 6 * error))
        proper = Gaussian([0, 0], [[2, 1 + .5j], [1 - .5j, 3]], True)
        observed = 1 + 2j
        estimated = gaussian_condition(proper, [0], [observed])
        np.testing.assert_allclose(estimated.mean, [(1 - .5j) * observed / 2])
        np.testing.assert_allclose(estimated.covariance, [[2.375]])
        np.testing.assert_allclose(estimated.pseudocovariance, 0, atol=1e-14)
        json.dumps(model.document(), allow_nan=False)

    def test_singular_support_and_invalid_covariances(self):
        singular = Gaussian([0, 0, 0], [[1, 1, 0], [1, 1, 0], [0, 0, 2]])
        self.assertEqual(gaussian_density(singular, [0, 0, 0])['density']['status'], 'singular_measure')
        np.testing.assert_allclose(gaussian_condition(singular, [0, 1], [2, 2]).covariance, [[2]])
        with self.assertRaisesRegex(ValueError, 'fuera del soporte'):
            gaussian_condition(singular, [0, 1], [2, 3])
        point = Gaussian([2, 3], [[0, 0], [0, 0]])
        a, b = generate_gaussian(point, 7, 0)
        np.testing.assert_array_equal(a.values, np.full(7, 2))
        np.testing.assert_array_equal(b.values, np.full(7, 3))
        for mean, cov, complex_model, pseudo in (
            ([0, 0], [[1, 2], [2, 1]], False, None),
            ([0, 0], [[1, 2], [0, 1]], False, None),
            ([0], [[1]], True, [[2]]),
            ([0], [[1]], False, [[0]]),
            ([0], [[1, 0], [0, 1]], False, None),
            ([0], [[np.inf]], False, None),
            ([1j], [[1]], False, None),
        ):
            with self.subTest(cov=cov), self.assertRaises(ValueError):
                Gaussian(mean, cov, complex_model, pseudo)
        with self.assertRaises(ValueError):
            gaussian_marginal(point, [0, 0])
        with self.assertRaises(ValueError):
            gaussian_condition(point, [0, 1], [2, 3])
        with self.assertRaises(ResourceLimitError):
            generate_gaussian(singular, 100, 0, execution=ExecutionContext(pool=ResourcePool(80)))

    def test_multivariate_dimensions_are_checked_before_likelihood_or_transformation(self):
        proper=Gaussian([1j,2.],[[2.,0.],[0.,1.]],True)
        with self.assertRaisesRegex(ValueError,'mismas dimensiones'):
            array_from_parts({'real':[[1,0],[0,1]],'imag':[[0]]})
        with self.assertRaisesRegex(ValueError,'partes real e imag'):
            array_from_parts({'real':[1,2]})
        with self.assertRaisesRegex(ValueError,'misma forma'):
            Gaussian([1j,2.],[[2.,0.],[0.,1.]],True,[[0.]])
        with self.assertRaisesRegex(ValueError,'observación debe coincidir'):
            gaussian_density(proper,[1j])
        with self.assertRaisesRegex(ValueError,'columna por componente'):
            gaussian_transform(proper,[[1.,0.,0.]])
        with self.assertRaisesRegex(ValueError,'dimensión de salida'):
            gaussian_transform(proper,[[1.,1.]],[0.,1.])
        result=gaussian_transform(proper,[[1.,1.]],[0.])
        np.testing.assert_allclose(result.mean,[2.+1j])
        np.testing.assert_allclose(result.covariance,[[3.]])

    def test_multinomial_population_marginal_condition_and_observations(self):
        model = Multinomial(4, (.25, .25, .5))
        self.assertAlmostEqual(model.mass([1, 1, 2])['mass']['value'], 12 * .25**2 * .5**2)
        self.assertEqual(model.mass([0, 0, 3])['mass']['value'], 0)
        np.testing.assert_allclose(model.population()['covariance'],
                                   [[.75, -.25, -.5], [-.25, .75, -.5], [-.5, -.5, 1]])
        self.assertAlmostEqual(value(model.marginal(2), 'density', 4), .5**4)
        conditional = model.condition([2], [1])
        self.assertEqual((conditional.trials, conditional.probabilities), (3, (.5, .5)))
        a, b, c = generate_multinomial(model, 100, 32)
        np.testing.assert_array_equal(a.values + b.values + c.values, np.full(100, 4))
        with self.assertRaises(ValueError):
            model.condition([1, 2], [3, 3])
        with self.assertRaises(ValueError):
            Multinomial(1, (0, 1)).condition([0], [1])
        with self.assertRaisesRegex(ValueError,'categoría por estimar'):
            model.condition([0,1,2],[1,1,2])
        with self.assertRaisesRegex(ValueError,'recuento por categoría'):
            model.mass([1,3])


class ProbabilityConsoleTests(unittest.TestCase):
    def inspect(self, family, parameters, *arguments, success=True):
        from signallab_pc.probability_cli import main
        output, errors = StringIO(), StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            code = main(['inspect', '--family', family, '--parameters', parameters, *arguments])
        if not success:
            self.assertEqual(code, 1, errors.getvalue())
            return errors.getvalue()
        self.assertEqual(code, 0, errors.getvalue())
        return json.loads(output.getvalue())['result']

    @staticmethod
    def run_console(*arguments):
        command = (
            'import sys; '
            'sys.modules.update({"PySide6": None, "PyQt6": None}); '
            'from signallab_pc.__main__ import main; raise SystemExit(main(sys.argv[1:]))'
        )
        return subprocess.run([sys.executable, '-B', '-X', 'utf8', '-c', command, 'probability', *arguments],
                              capture_output=True, encoding='utf-8', timeout=25)

    def test_headless_inspection_and_archive_parity(self):
        arguments = ('--family', 'normal', '--parameters', '{"mean":2,"std":3}')
        inspected = self.run_console('inspect', *arguments, '--function', 'density', '--argument', '2')
        self.assertEqual(inspected.returncode, 0, inspected.stderr)
        self.assertAlmostEqual(json.loads(inspected.stdout)['result']['value'], 1 / (3 * math.sqrt(math.tau)))
        with TemporaryDirectory() as tmp:
            target = Path(tmp) / 'realizaciones.slproj'
            command = ('generate', *arguments, '--seed', '9', '--count', '10', '--origin', '-2',
                       '--replicas', '2', '--output', str(target))
            executed = self.run_console(*command)
            self.assertEqual(executed.returncode, 0, executed.stderr)
            ids = json.loads(executed.stdout)
            project, _ = load(target)
            expected = generate_realizations(Distribution('normal', {'mean': 2, 'std': 3}),
                                             10, 9, replicas=2, origin=-2)
            for key, record in zip(ids['result_ids'], expected, strict=True):
                reloaded = project.get(key)
                np.testing.assert_array_equal(reloaded.values, record.values)
                self.assertEqual(reloaded.metadata, record.metadata)
            previous = target.read_bytes()
            rejected = self.run_console(*command, '--max-work-bytes', '1')
            self.assertEqual(rejected.returncode, 1, rejected.stderr)
            self.assertEqual(target.read_bytes(), previous)

    def test_inspection_transports_intervals_moments_and_population(self):
        self.assertAlmostEqual(self.inspect('binomial', '{"trials":4,"p":0.5}',
                                           '--function', 'interval', '--argument', '1', '--upper', '2')['value'],
                               10 / 16)
        self.assertEqual(self.inspect('normal', '{"mean":2,"std":3}',
                                     '--function', 'moment', '--order', '2')['value'], 13)
        self.assertEqual(self.inspect('normal', '{"mean":2,"std":3}')['variance']['value'], 9)
        for parameters in ('[]', '{"p":NaN}', '{"p":2}'):
            self.assertIn('No se pudo completar', self.inspect('bernoulli', parameters, success=False))

    def test_multinomial_console_joint_and_conditional(self):
        parameters = '{"trials":4,"probabilities":[0.25,0.25,0.5]}'
        family = 'multinomial'
        self.assertEqual(self.inspect(family, parameters)['mean'], [1, 1, 2])
        self.assertAlmostEqual(self.inspect(family, parameters, '--function', 'density',
                                           '--observation', '[1,1,2]')['mass']['value'], 3 / 16)
        self.assertEqual(self.inspect(family, parameters, '--function', 'marginal',
                                     '--components', '2')['mean']['value'], 2)
        self.assertEqual(self.inspect(family, parameters, '--function', 'conditional',
                                     '--components', '2', '--observation', '[1]')['mean'], [1.5, 1.5])
        self.assertIn('categoría', self.inspect(family, parameters, '--function', 'marginal',
                                              '--components', '1', '2', success=False))
        self.assertIn('multinomial', self.inspect(family, parameters, '--function', 'cdf',
                                                '--argument', '2', success=False))

    def test_console_complex_gaussian_binds_coordinates_and_reports_singular_support(self):
        family = 'multivariate_normal'
        model = '{"mean":{"real":[0,1],"imag":[0,2]},"covariance":[[2,0],[0,4]],"complex_model":true}'
        self.assertEqual(self.inspect(family, model)['real_rank'], 4)
        self.assertEqual(self.inspect(family, model, '--function', 'marginal',
                                     '--components', '1')['mean'], {'real': [1], 'imag': [2]})
        conditional = self.inspect(family, model, '--function', 'conditional', '--components', '0',
                                   '--observation', '{"real":[3],"imag":[2]}')
        np.testing.assert_allclose(conditional['covariance']['real'], [[4]])
        self.assertAlmostEqual(self.inspect(family, model, '--function', 'density',
                                           '--observation', '{"real":[0,1],"imag":[0,2]}')['density']['value'],
                               1 / (8 * math.pi**2))
        for invalid in ('{"real":[0]}', '{"real":[0],"imag":[0,2]}'):
            error = self.inspect(family, model, '--function', 'density', '--observation', invalid, success=False)
            self.assertIn('No se pudo completar', error)
        self.assertIn('gaussiana', self.inspect(family, model, '--function', 'survival',
                                               '--argument', '1', success=False))
