"""Independent Laplace integrals and worksheet domain contracts."""
import cmath
import math
import sys
import unittest

from scipy.integrate import quad
import sympy as sp

from signallab_pc.cas_engine import calculate, empty_state, restore
from signallab_pc.symbolic import S, execute, parse


def integrate_oracle(function, frequency, lower=0, upper=math.inf):
    def weighted(t):
        return function(t)*cmath.exp(-frequency*t)

    real = quad(lambda t: weighted(t).real, lower, upper, epsabs=1e-11)[0]
    imag = quad(lambda t: weighted(t).imag, lower, upper, epsabs=1e-11)[0]
    return complex(real, imag)


class RationalTimeLaplaceContracts(unittest.TestCase):
    def assert_matches_integral(self, expression, function, *, options=None, lower=0,
                                upper=math.inf, frequencies=(1, .7+.9j)):
        result = execute(dict(operation='laplace', expression=expression, **(options or {})))
        self.assertTrue(result['evaluated'], result['result'])
        transform = parse(result['result'])
        for frequency in frequencies:
            with self.subTest(frequency=frequency):
                actual = complex(transform.subs(S, frequency).evalf())
                self.assertAlmostEqual(actual, integrate_oracle(function,frequency,lower,upper), places=9)
        return result

    def test_repeated_and_distinct_linear_denominators_with_polynomial_quotient(self):
        for expression, function in (
            ('1/(t+1)', lambda t: 1/(t+1)),
            ('(t+3)/(2*t+3)', lambda t: (t+3)/(2*t+3)),
            ('1/(t+2)^3', lambda t: 1/(t+2)**3),
            ('(t+2)/((t+1)^2*(t+3))', lambda t: (t+2)/((t+1)**2*(t+3))),
            ('1/(t^2+1)', lambda t: 1/(t*t+1)),
            ('1/(t+2+i)', lambda t: 1/(t+2+1j)),
        ):
            with self.subTest(expression=expression):
                result = self.assert_matches_integral(expression,function)
                self.assertEqual(result['convergence_abscissa'],'0')

    def test_exponential_shift_and_cutoff_keep_the_correct_roc(self):
        result = self.assert_matches_integral('exp(-2*t)/(t+1)',lambda t:math.exp(-2*t)/(t+1))
        self.assertEqual(result['convergence_abscissa'],'-2')
        result = self.assert_matches_integral('Step(t-2)/(t+1)',lambda t:1/(t+1),lower=2)
        self.assertEqual(result['convergence_abscissa'],'0')
        result = self.assert_matches_integral('Step(-t)/(1-t)',lambda t:1/(1-t),
                    options={'interpretation':'bilateral'},lower=-math.inf,upper=0,
                    frequencies=(-1,-.7+.9j))
        self.assertEqual((result['roc_lower'],result['roc_upper']),('-oo','0'))

    def test_real_poles_on_the_interval_do_not_produce_a_laplace_transform(self):
        for expression in ('1/t', '1/(t-1)^2', '(t+3)/((t+2)*(t-1))'):
            with self.subTest(expression=expression):
                result = execute(dict(operation='laplace',expression=expression))
                self.assertFalse(result['evaluated'])
                self.assertEqual(result['condition'],'False')

    def test_canceled_poles_are_checked_after_grouping_the_same_exponential_shift(self):
        response = self.assert_matches_integral(
            'exp(-2*t)*(t+1)/(t-1)-2*exp(-2*t)/(t-1)',
            lambda t: math.exp(-2*t),
        )
        self.assertEqual(response['convergence_abscissa'],'-2')

    def test_symbolic_offsets_export_the_valid_branch_condition(self):
        symbolic = execute(dict(operation='laplace',expression='1/(t+a)'))
        a = sp.Symbol('a')
        condition = parse(symbolic['condition'])
        self.assertTrue(symbolic['evaluated'])
        self.assertIs(sp.simplify(condition.subs(a,2)),sp.true)
        self.assertIs(sp.simplify(condition.subs(a,-2)),sp.false)
        unresolved = execute(dict(operation='laplace',expression='1/(t-2+i)'))
        self.assertFalse(unresolved['evaluated'])


class WorksheetScopeContracts(unittest.TestCase):
    def setUp(self):
        self.addCleanup(sys.set_int_max_str_digits,sys.get_int_max_str_digits())
        self.state = empty_state()
        self.cell = 0

    def evaluate(self, source):
        self.cell += 1
        self.result = calculate(dict(source=source,state=self.state,cell=self.cell))
        self.state = self.result['state']
        return restore(self.state['results'][str(self.cell)])

    def test_laplace_tuple_retains_roc_and_boolean_when_approximated(self):
        transform, abscissa, condition = self.evaluate('laplace_transform(1/(t+1),t,s)')
        self.assertEqual((abscissa,condition),(0,sp.true))
        self.assertAlmostEqual(float(transform.subs(S,1).evalf()),
                               integrate_oracle(lambda t:1/(t+1),1).real,places=13)
        result = self.evaluate('approx(laplace_transform(exp(-2*t),t,s),20)')
        self.assertEqual(float(result[1]),-2.)
        self.assertIs(result[2],sp.true)
        self.assertAlmostEqual(float(result[0].subs(S,1)),1/3)

    def test_resolving_a_conditional_system_replaces_external_parameters_only(self):
        solutions = sp.FiniteSet(sp.Tuple(2,3))
        unresolved = self.evaluate('linsolve([(x-2)/(a-1),y-3],[x,y])')
        self.assertIsInstance(unresolved,sp.ConditionSet)
        self.assertEqual(unresolved.free_symbols,{sp.Symbol('a')})
        self.assertEqual(self.evaluate('subst(r1,a,2)'),solutions)
        self.assertEqual(self.evaluate('subst(r1,a,1)'),sp.S.EmptySet)
        self.assertEqual(self.evaluate('subst(r1,x,4)'),unresolved)
        symbolic = self.evaluate('subst(r1,a,x)')
        x = sp.Symbol('x')
        self.assertIn(x,symbolic.free_symbols)
        self.assertNotIn(x,symbolic.bound_symbols)

    def test_substitution_does_not_capture_an_integral_or_collapse_mapping_keys(self):
        capture = self.evaluate('subst(integral(x+t,(t,0,1)),x,t)')
        t = sp.Symbol('t')
        self.assertEqual(capture.doit(),t+sp.S.Half)
        result = self.evaluate('subst([[x,y],(x,y),{1:x,2:y},matrix([[x,y]])],{x:2,y:3})')
        self.assertEqual(result,[[2,3],(2,3),{1:2,2:3},sp.Matrix([[2,3]])])
        previous = self.state
        with self.assertRaisesRegex(ValueError,'claves distintas'):
            self.evaluate('subst({x:2,y:5},{x:1,y:1})')
        self.assertEqual(self.state,previous)

    def test_piecewise_roots_and_reversed_assumptions_preserve_one_sided_limits(self):
        self.assertEqual(self.evaluate('solve(piecewise((x^2,x<0),(x,True))=4,x)'),
                         sp.FiniteSet(-2,4))
        self.evaluate('assume(0 < x, x < 2)')
        self.assertEqual(self.evaluate('limit(sqrt(x^2),x,0,right)'),0)
        with self.assertRaisesRegex(ValueError,'por ese lado'):
            self.evaluate('limit(sqrt(x^2),x,0,left)')
        self.assertEqual(self.evaluate('integrate(sqrt(x^2),(x,-1,1))'),1)
        self.evaluate('purge(x)')
        self.evaluate('assume(x<0)')
        self.assertEqual(self.evaluate('solve(x^2=4,x)'),sp.FiniteSet(-2))
        for expression in ('assume(x,positive)','assume(x!=2)','assume(x=2)'):
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                self.evaluate(expression)

    def test_composite_powers_exact_log_bases_and_poles_have_consistent_domains(self):
        self.assertEqual(self.evaluate('matrix([[1,1],[0,1]])^3'),sp.Matrix([[1,3],[0,1]]))
        self.assertEqual(self.evaluate('log(8,2)'),3)
        self.evaluate('x^a')
        self.assertIn('domain_condition',self.result)
        self.assertEqual(self.evaluate('subst(r3,{x:0,a:1/2})'),0)
        for expression in ('subst(r3,{x:0,a:-1/2})','tan(pi/2)','log(3,1)','atan(i)'):
            with self.subTest(expression=expression), self.assertRaisesRegex(ValueError,'fuera del dominio'):
                self.evaluate(expression)
