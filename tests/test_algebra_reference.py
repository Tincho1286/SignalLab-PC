"""Compare the symbolic entry points with independent closed-form results."""
import unittest

import sympy as sp
from signallab_pc.symbolic import execute, parse, S, W, Z


class AlgebraReferenceTests(unittest.TestCase):
    def assert_measure(self, expression, domain, mode, energy, power, **interval):
        result = execute(dict(operation='signal_measures_expression',expression=expression,
                              domain=domain,mode=mode,**interval))
        for field, expected in (('energy',energy),('mean_square',power)):
            measure = result[field]
            actual = sp.sympify(measure['exact'])
            if expected == sp.oo:
                self.assertEqual(measure['status'],'divergent')
                self.assertEqual(actual,sp.oo)
            else:
                self.assertEqual(measure['status'],'finite')
                self.assertEqual(sp.simplify(actual-expected),0)

    def test_global_cosines_use_orthogonality_and_exact_discrete_aliases(self):
        # Continuous orthogonal quadratures give 4 + (9+16)/2.
        self.assert_measure('2+3*Cos(t)+4*sin(t)','continuous','global',sp.oo,sp.Rational(33,2))
        # Nyquist samples evaluate to (-1)**n / 2, including the phase.
        self.assert_measure('Cos(pi*n+pi/3)','discrete','global',sp.oo,sp.Rational(1,4))
        self.assert_measure('sin(pi*n/2)*Cos(pi*n/2)','discrete','global',0,0)

    def test_finite_cosine_energy_and_removable_sample(self):
        # The interval contains four even indices and five odd indices.
        self.assert_measure('Cos(pi*n/2)','discrete','interval',4,sp.Rational(4,9),lower='-3',upper='5')
        self.assert_measure('Cos(2*t+pi/3)','continuous','interval',sp.pi/4,sp.S.Half,lower='0',upper='pi/2')
        energy = 2+sp.pi**2/4  # samples at -1, 0 and 1
        self.assert_measure('sin(pi*n/2)/n','discrete','interval',energy,energy/3,lower='-1',upper='1')

    def test_damped_cosines_have_finite_energy_and_zero_global_power(self):
        # Integrate 9 exp(-4t) (1+cos(6t))/2 over t >= 0.
        self.assert_measure('3*Step(t)*exp(-2*t)*Cos(3*t)','continuous','global',sp.Rational(153,104),0)
        # Squared samples at n = 2k form the series sum (1/16)**k.
        self.assert_measure('Step(n)*(1/2)^n*Cos(pi*n/2)','discrete','global',sp.Rational(16,15),0)

    def test_laplace_and_fourier_match_known_repeated_pole_and_translation(self):
        for interpretation, roc in (('unilateral','convergence_abscissa'),('bilateral','roc_lower')):
            with self.subTest(interpretation=interpretation):
                laplace = execute(dict(operation='laplace',interpretation=interpretation,
                                       expression='t*exp(-2*t)*Step(t)'))
                self.assertTrue(laplace['evaluated'])
                self.assertEqual(sp.simplify(parse(laplace['result'])-1/(S+2)**2),0)
                self.assertEqual(laplace[roc],'-2')
        fourier = execute(dict(operation='fourier_angular',expression='3*exp(-2*abs(t-1))'))
        self.assertTrue(fourier['evaluated'])
        self.assertEqual(sp.simplify(parse(fourier['result'])-12*sp.exp(-sp.I*W)/(4+W**2)),0)

    def test_discrete_transform_matches_shifted_geometric_series(self):
        text = '3*(1/2)^(n-2)*Step(n-2)'
        for operation, expected in (('z_expression',3/Z**2/(1-1/(2*Z))),
                                    ('dtft_expression',3*sp.exp(-2*sp.I*W)/(1-sp.exp(-sp.I*W)/2))):
            with self.subTest(operation=operation):
                result = execute(dict(operation=operation,expression=text,lower='-oo',upper='oo'))
                self.assertTrue(result['evaluated'])
                formula = result['branches'][0]['expression'] if operation == 'z_expression' else result['result']
                self.assertEqual(sp.simplify(parse(formula)-expected),0)
