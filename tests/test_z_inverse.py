import unittest
import numpy as np
import sympy as sp
from signallab_pc.z_algebra import inverse
from signallab_pc.symbolic import N

EXPRESSION='(z^(-2)+z^(-3)-2*z^(-1))/(z^(-2)+1-z^(-3))'

def samples(expression,mode='right',radius='1',start=-8,count=25):
    result=inverse(dict(expression=expression,roc=mode,radius=radius,start=start,count=count,include_samples=True))
    return result,np.array([complex(*value) for value in result['numeric_samples']])

def contour(function,radius,start=-8,count=25):
    theta=2*np.pi*np.arange(8192)/8192;z=radius*np.exp(1j*theta);coefficients=np.fft.ifft(function(z));n=np.arange(start,start+count)
    return coefficients[n%len(theta)]*radius**n

class RationalInverseZTests(unittest.TestCase):
    def test_reported_cubic_and_three_rocs(self):
        function=lambda z:(-2*z*z+z+1)/(z**3+z-1)
        for mode,radius in [('right',1.5),('left',.5),('radius',1.)]:
            result,actual=samples(EXPRESSION,mode,str(radius))
            np.testing.assert_allclose(actual,contour(function,radius),atol=2e-10,rtol=2e-11)
            self.assertEqual(len(result['pole_definitions']),3)
            self.assertEqual(result['parameters'],[])
        _,right=samples(EXPRESSION);np.testing.assert_array_equal(right[8:15],[0,-2,1,3,-3,-2,6])
    def test_repeated_poles_and_finite_terms(self):
        for mode,radius in [('right',1.),('left',.25)]:
            _,actual=samples('1/(z-1/2)^3',mode)
            np.testing.assert_allclose(actual,contour(lambda z:1/(z-.5)**3,radius),atol=2e-10,rtol=2e-11)
        _,actual=samples('z+2+3/z');expected=np.zeros(25);expected[7:10]=[1,2,3];np.testing.assert_array_equal(actual,expected)
        _,actual=samples('(z+2)/(z^3+z-1)^2','radius','1')
        np.testing.assert_allclose(actual,contour(lambda z:(z+2)/(z**3+z-1)**2,1.),atol=2e-10,rtol=2e-11)
    def test_symbolic_parameters_and_origin_poles(self):
        answer=inverse(dict(expression='z/(z-a)^2',roc='right',include_samples=False));self.assertEqual(answer['parameters'],['a'])
        a=sp.Symbol('a');formula=sp.sympify(answer['result'],locals={'n':N,'a':a})
        self.assertEqual(formula.subs({a:sp.Rational(1,3),N:4}),sp.Rational(4,27))
        for mode in ('right','left'):
            _,actual=samples('1/z^3',mode);expected=np.zeros(25);expected[11]=1;np.testing.assert_array_equal(actual,expected)
        with self.assertRaises(ValueError):samples('z/(z-1/2)','radius','1/2')
        with self.assertRaises(ValueError):samples('z/(z-a)','radius','1')
    def test_high_degree_and_complex_coefficients(self):
        _,actual=samples('1/(z^5-z-1)')
        np.testing.assert_allclose(actual,contour(lambda z:1/(z**5-z-1),1.5),atol=2e-10,rtol=2e-11)
        _,actual=samples('1/(z^2+i)')
        np.testing.assert_allclose(actual,contour(lambda z:1/(z*z+1j),1.5),atol=2e-10,rtol=2e-11)

if __name__=='__main__':unittest.main()
