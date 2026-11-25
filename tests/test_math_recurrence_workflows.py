"""Algebraic and numerical contracts for recurrences with explicit prehistory."""
import math
import unittest

import numpy as np
import sympy as sp

from signallab_pc.cas_engine import restore
from signallab_pc.difference_equations import solve, summary
from signallab_pc.symbolic import N, Z, parse


class RecurrenceContracts(unittest.TestCase):
    def test_overlapping_piecewise_conditions_use_first_matching_interval(self):
        request = dict(coefficients=['1', '-1/2'], start=-3, count=9, rest=False,
                       initial=['3'], expression='Piecewise((2,n<=-1),(4,n<2),(0,True))')
        result = solve(request)
        self.assertTrue(result['closed_form'])
        symbolic = restore(result['cas_encoded'])
        zero_state = parse(result['zero_state'])
        zero_input = parse(result['zero_input'])
        samples = np.array([complex(*pair) for pair in result['numeric_samples']])
        previous = sp.Integer(3)
        for k in range(9):
            n = k-3
            previous = previous/2+(2 if n<=-1 else 4 if n<2 else 0)
            self.assertEqual(sp.simplify(symbolic.subs(N,n)-previous), 0)
            self.assertEqual(sp.simplify(zero_input.subs(N,n)-3*sp.Rational(1,2)**(k+1)), 0)
            self.assertEqual(sp.simplify(zero_state.subs(N,n)+zero_input.subs(N,n)-previous), 0)
            self.assertAlmostEqual(samples[k].real, float(previous))
        self.assertEqual(result['residual_check']['interval'], [-3, 5])
        self.assertLess(result['residual_check']['normalized_max'], 1e-14)
        self.assertIn('Aportes de la memoria y la entrada', summary(request, result).plain_text())

    def test_polynomial_times_geometric_and_repeated_roots_match_a_closed_sum(self):
        request = dict(coefficients=['1', '-1', '1/4'], start=2, count=8,
                       expression='(n-2)*(1/2)^(n-2)')
        result = solve(request)
        self.assertTrue(result['closed_form'])
        exact = restore(result['cas_encoded'])
        state = parse(result['system_expression'])
        self.assertEqual(sp.cancel(state-1/(1-1/(2*Z))**2), 0)
        for k in range(13):
            expected = sp.binomial(k+2, 3)*sp.Rational(1,2)**k
            self.assertEqual(sp.simplify(exact.subs(N,k+2)-expected), 0)
        self.assertEqual(len(result['numeric_samples']), 8)

    def test_nonrational_forcing_keeps_a_finite_convolution_and_accurate_samples(self):
        request = dict(coefficients=['2', '-1'], start=1, count=8,
                       rest=False, initial=['-1'], expression='sin(n^2)')
        result = solve(request)
        exact = restore(result['cas_encoded'])
        self.assertFalse(result['closed_form'])
        self.assertTrue(exact.has(sp.Sum))
        self.assertIsNone(result['unilateral_output'])
        self.assertIn('suma finita', summary(request,result).plain_text())
        previous = -1.
        for index, pair in enumerate(result['numeric_samples'], 1):
            previous = (math.sin(index**2)+previous)/2
            self.assertAlmostEqual(complex(*pair).real, previous, places=13)
            self.assertAlmostEqual(float(exact.subs(N,index).doit().evalf()), previous, places=13)

    def test_symbolic_gain_and_zero_forcing_have_clear_residual_status(self):
        result = solve(dict(coefficients=['1','-a'], expression='0', count=4,
                            rest=False, initial=['3']))
        self.assertEqual(result['parameters'], ['a'])
        self.assertIsNone(result['numeric_samples'])
        exact = restore(result['cas_encoded'])
        a, = exact.free_symbols-{N}
        self.assertEqual(sp.simplify(exact.subs(N,2)-3*a**3), 0)
        result = solve(dict(coefficients=['1','-1/2'], expression='0', count=4))
        np.testing.assert_array_equal(result['numeric_samples'], np.zeros((4,2)))
        self.assertEqual(result['residual_check']['normalized_max'], 0)

    def test_bad_prehistory_coefficients_and_support_are_rejected_explicitly(self):
        base = dict(coefficients=['2','-1'], expression='n', start=-2, count=4,
                    rest=False, initial=['0'])
        for change, reason in [
            ({'coefficients':['0','0']}, 'todos sus coeficientes'),
            ({'coefficients':['0','1']}, 'a₀ no puede'),
            ({'coefficients':['1','n']}, 'requiere una constante'),
            ({'coefficients':['1','oo']}, 'debe ser finito'),
            ({'count':0}, 'cantidad de muestras'),
            ({'initial':[]}, 'Cargá 1 valores'),
            ({'initial':['n']}, 'requiere una constante'),
            ({'expression':'cos(t)'}, 'Usá n'),
            ({'expression':'Piecewise((1,n<0))'}, 'sin definir'),
        ]:
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, reason):
                solve({**base, **change})
