"""Distribution scaling, transform conventions and energy over exact supports."""
import unittest

import sympy as sp

from signallab_pc.cas_engine import restore
from signallab_pc.measures_symbolic import measure_expression
from signallab_pc.symbolic import N, S, T, W, execute, parse


class DistributionTransformContracts(unittest.TestCase):
    def transform(self, operation, expression, **options):
        result = execute(dict(operation=operation, expression=expression, **options))
        self.assertTrue(result['evaluated'], result.get('scope'))
        return restore(result['cas_encoded']) if 'cas_encoded' in result else parse(result['result'])

    def test_fourier_applies_product_rule_and_negative_affine_scale_to_delta_derivative(self):
        transformed = self.transform('fourier_angular', '(t+1)*DiracDelta(4-2*t,1)')
        expected = (1-3*sp.I*W)*sp.exp(-2*sp.I*W)/4
        self.assertEqual(sp.simplify(transformed-expected), 0)
        inverse = self.transform('inverse_fourier_angular', 'exp(-2*i*w)*(1-3*i*w)/4')
        expected_inverse = (sp.DiracDelta(T-2)-3*sp.DiracDelta(T-2,1))/4
        self.assertEqual(sp.simplify(inverse-expected_inverse), 0)

    def test_laplace_preserves_zero_endpoint_and_discards_impulses_before_it(self):
        result = self.transform('laplace',
                                '2*DiracDelta(t)+DiracDelta(t+1)+(t+1)*DiracDelta(4-2*t,1)'
                                '+Step(t-3)*exp(-2*(t-3))')
        expected = 2+(1-3*S)*sp.exp(-2*S)/4+sp.exp(-3*S)/(S+2)
        self.assertEqual(sp.simplify(result-expected), 0)

    def test_fourier_harmonic_derivative_pairs_keep_the_locations_and_areas(self):
        result = self.transform('fourier_angular', 't*cos(3*t)+2*sin(4*t)')
        expected = (
            sp.I*sp.pi*(sp.DiracDelta(W-3,1)+sp.DiracDelta(W+3,1))
            +2*sp.I*sp.pi*(sp.DiracDelta(W+4)-sp.DiracDelta(W-4))
        )
        self.assertEqual(sp.simplify(result-expected), 0)
        result = self.transform('inverse_fourier_angular', '3*DiracDelta(w-2)+DiracDelta(w+1)')
        expected = (3*sp.exp(2*sp.I*T)+sp.exp(-sp.I*T))/(2*sp.pi)
        self.assertEqual(sp.simplify(result-expected), 0)

    def test_dtft_inverse_counts_the_periodic_seam_only_once_even_with_regular_part(self):
        result = self.transform('inverse_dtft_expression',
                                '2*pi*(DiracDelta(w-pi)+DiracDelta(w+pi))+3*exp(-2*i*w)')
        for n in range(-4,6):
            self.assertEqual(sp.simplify(result.subs(N,n)), sp.Integer((-1)**abs(n)+3*(n==2)))

    def test_distribution_weight_at_a_jump_is_rejected_with_cause(self):
        for expression in ['Step(t)*DiracDelta(t)', 'sign(t)*DiracDelta(t,1)',
                           'DiracDelta(t)*DiracDelta(t-1)', 'DiracDelta(t)**2']:
            with self.subTest(expression=expression), self.assertRaisesRegex(ValueError, 'Dirac|impulsos'):
                self.transform('fourier_angular', expression)


class EnergyAndPowerContracts(unittest.TestCase):
    def test_partial_and_multi_cycle_intervals_match_sample_by_sample(self):
        expression = 'Repeat(n+i,n,3,0)'
        for a,b in [(-2,-2), (-1,0), (-4,8)]:
            with self.subTest(a=a,b=b):
                result = measure_expression(dict(expression=expression, domain='discrete', lower=str(a), upper=str(b)))
                expected = sum((n%3)**2+1 for n in range(a,b+1))
                self.assertEqual(parse(result['energy']['exact']), expected)
                self.assertEqual(sp.simplify(parse(result['mean_square']['exact'])-sp.Rational(expected,b-a+1)), 0)
                self.assertEqual(result['energy']['status'], 'finite')
                self.assertEqual(result['bounds'], [str(a),str(b)])

    def test_discrete_explicit_period_requires_integers_and_preserves_harmonic_aliasing(self):
        request = dict(expression='cos(pi*n/3)+cos(7*pi*n/3)', domain='discrete', mode='periodic')
        result = measure_expression({**request, 'period':'12'})
        self.assertEqual(parse(result['mean_square']['exact']), 2)
        self.assertEqual(parse(result['period_energy']['exact']), 24)
        self.assertEqual(result['energy']['status'], 'divergent')
        self.assertTrue(result['period_verified'])
        for period, reason in [('0','positivo'), ('3','repita'), ('3/2','enteros')]:
            with self.subTest(period=period), self.assertRaisesRegex(ValueError,reason):
                measure_expression({**request, 'period':period})

    def test_prevents_ordinary_energy_for_distributions_and_reversed_or_nonreal_bounds(self):
        for options, reason in [
            ({'expression':'DiracDelta(t)'}, 'función ordinaria'),
            ({'expression':'cos(w)'}, 'Usá sólo t'),
            ({'lower':'i'}, 'constantes reales'),
            ({'upper':'-1'}, 'creciente'),
            ({'domain':'frequency'}, 'Dominio o alcance'),
        ]:
            with self.subTest(options=options), self.assertRaisesRegex(ValueError, reason):
                measure_expression({'expression':'cos(t)', **options})
