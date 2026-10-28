import unittest,time
import numpy as np
import sympy as sp
from signallab_pc.signal_notation import normalize,read,source,latex
from signallab_pc.z_algebra import inverse
from signallab_pc.symbolic import N
from signallab_pc.engine import evaluate_expression,ExpressionError

class SignalNotationTests(unittest.TestCase):
    def test_z_right_left_and_endpoints(self):
        for mode,wanted in [('right','(1/2)**n*step(n)'),('left','-(1/2)**n*step(-n-1)')]:
            answer=inverse(dict(expression='z/(z-1/2)',roc=mode,start=-5,count=11))
            actual=read(answer['display_result'],('n',));expected=read(wanted,('n',))
            for n in range(-5,6):self.assertEqual(sp.simplify(actual.subs(N,n)-expected.subs(N,n)),0)
            self.assertNotIn('Piecewise',answer['display_result']);self.assertNotIn('KroneckerDelta',answer['display_result'])
        for expression in ('z/(z-1/2)^2','1/(z-1/2)^3','z+2+3/z'):
            answer=inverse(dict(expression=expression,roc='right',include_samples=False))
            old=sp.sympify(answer['result'],locals={'n':N});new=read(answer['display_result'],('n',))
            for n in range(-6,10):self.assertEqual(sp.simplify(old.subs(N,n)-new.subs(N,n)),0)

    def test_identities_preserve_support_and_hypotheses(self):
        examples=['n*KroneckerDelta(n,3)','n*Piecewise((1,n>=1),(0,True))',
            'KroneckerDelta(0,n)+Piecewise((2**(1-n)/2,n>=1),(0,True))',
            'Piecewise((1/n,n>=1),(0,True))','Heaviside(n,1/2)',
            '3*KroneckerDelta(n,0)+Piecewise((2**(-n),n>=1),(0,True))']
        for text in examples:
            old=read(text,('n',));new=normalize(old)
            for n in range(-6,10):self.assertEqual(sp.simplify(old.subs(N,n)-new.subs(N,n)),0,text)
        self.assertIn('Piecewise',source(read('Piecewise((1/n,n>=1),(0,True))',('n',))))
        self.assertIn('_{',latex(read('Heaviside(n,1/2)',('n',))))
        t=sp.Symbol('t',real=True);self.assertEqual(normalize(sp.Heaviside(t)).subs(t,0),sp.Rational(1,2))

    def test_gate_evaluation_and_invalid_active_values(self):
        coordinates=np.array([-10000.,-1.,0.,1.,10.])
        with np.errstate(all='raise'):
            actual=evaluate_expression('(1/2)^n*step(n)',coordinates)
        np.testing.assert_allclose(actual,[0,0,1,.5,1/1024])
        np.testing.assert_array_equal(evaluate_expression('Heaviside(n,1/2)*2',[-1,0,1]),[0,1,2])
        np.testing.assert_array_equal(evaluate_expression('KroneckerDelta(n,2)*3',[1,2,3]),[0,3,0])
        with np.errstate(all='ignore'):
            with self.assertRaises(ExpressionError):evaluate_expression('1/(n-1)*step(n)',[0,1,2])

    def test_algebraic_roots_remain_fast_and_exact(self):
        start=time.perf_counter()
        answer=inverse(dict(expression='(z^(-2)+z^(-3)-2*z^(-1))/(z^(-2)+1-z^(-3))',roc='right',start=0,count=7))
        self.assertLess(time.perf_counter()-start,8)
        np.testing.assert_array_equal([complex(*v) for v in answer['numeric_samples']],[0,-2,1,3,-3,-2,6])
        self.assertEqual(len(answer['pole_definitions']),3)
        self.assertNotIn('Piecewise',answer['display_result'])

if __name__=='__main__':unittest.main()
