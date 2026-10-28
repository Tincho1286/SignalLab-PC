import unittest,time
import numpy as np
import sympy as sp
from scipy import signal
from signallab_pc.z_algebra import inverse
from signallab_pc.symbolic import execute,N,T
from signallab_pc.signal_notation import read
from signallab_pc.result_summary import transform_summary

CUBIC='(z^(-2)+z^(-3)-2*z^(-1))/(z^(-2)+1-z^(-3))'

class NumericInverseDisplayTests(unittest.TestCase):
    def test_z_numeric_expression_matches_samples_for_three_rocs(self):
        from signallab_pc.math_display import numeric_presentation
        self.assertEqual(numeric_presentation('0.123456789*0.9999999999**n'),'0.123457*0.9999999999**n')
        for mode,radius in [('right','1.5'),('left','.5'),('radius','1')]:
            result=inverse(dict(expression=CUBIC,roc=mode,radius=radius,start=-8,count=25));text=result['display_result']
            self.assertTrue(result['display_numeric']);self.assertNotIn('p[',text);self.assertNotIn('A[',text);self.assertNotIn('RootOf',text)
            expression=read(text,('n',));function=sp.lambdify(N,expression,modules='numpy')
            actual=np.array([complex(*v) for v in result['numeric_samples']]);np.testing.assert_allclose(function(np.arange(-8,17)),actual,atol=2e-11,rtol=3e-13)
            self.assertNotIn('p[',result['roc'])
            fragments=sum((read(term,('n',)) for term in result['display_terms']),sp.S.Zero)
            fragments=sp.lambdify(N,fragments,modules='numpy')
            np.testing.assert_allclose(fragments(np.arange(-8,17)),actual,atol=2e-11,rtol=3e-13)
            summary=transform_summary(dict(operation='z_inverse_expression',expression=CUBIC),result).plain_text()
            self.assertNotIn('Polos de la expresión',summary);self.assertNotIn('A[',summary)

    def test_laplace_numbers_match_independent_state_response(self):
        expression='1/(s^3+2*s^2+3*s+4)';start=time.perf_counter()
        result=execute(dict(operation='inverse_laplace',expression=expression));self.assertLess(time.perf_counter()-start,5)
        self.assertTrue(result['display_numeric']);self.assertNotIn('Root',result['result']);self.assertNotIn('A[',result['result'])
        formula=read(result['result']);t=next(s for s in formula.free_symbols if str(s)=='t');function=sp.lambdify(t,formula,modules='numpy')
        times=np.linspace(0,10,201);_,expected=signal.impulse(([1],[1,2,3,4]),T=times)
        np.testing.assert_allclose(function(times),expected,atol=3e-13,rtol=2e-12)

    def test_repeated_laplace_poles_and_elementary_exact_cases(self):
        result=execute(dict(operation='inverse_laplace',expression='(s+1)/(s^3+2*s^2+3*s+4)^2'))
        formula=read(result['result']);t=next(s for s in formula.free_symbols if str(s)=='t');times=np.linspace(0,8,161)
        denominator=np.convolve([1,2,3,4],[1,2,3,4]);_,expected=signal.impulse(([1,1],denominator),T=times)
        np.testing.assert_allclose(sp.lambdify(t,formula,modules='numpy')(times),expected,atol=2e-12,rtol=3e-11)
        exact=execute(dict(operation='inverse_laplace',expression='1/(s+1)'));self.assertNotIn('display_numeric',exact)
        self.assertIn('exp(-t)',exact['result'])
        z=inverse(dict(expression='z/(z-1/2)',roc='right',include_samples=False));self.assertFalse(z['display_numeric']);self.assertNotIn('p[',z['display_result'])

    def test_rational_impulses_and_time_shift_keep_their_meaning(self):
        result=execute(dict(operation='inverse_laplace',expression='s+1/(s^3+2*s^2+3*s+4)'))
        self.assertIn('DiracDelta(t, 1)',result['result'])
        shifted=execute(dict(operation='inverse_laplace',expression='exp(-2*s)/(s+1)'));self.assertNotIn('display_numeric',shifted)
        self.assertIn('Heaviside(t - 2)',shifted['result'])

if __name__=='__main__':unittest.main()
