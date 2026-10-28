import unittest
import numpy as np
import sympy as sp
from scipy.integrate import quad
from signallab_pc.model import Signal
from signallab_pc.continuous import convolution,correlation
from signallab_pc.symbolic import execute,parse,T

def signal(values,origin=0,step=1):return Signal(values,origin,step,'s','x','continuous')

class ContinuousTests(unittest.TestCase):
    def test_rectangles_make_triangle(self):
        result=convolution(signal([1,1],2,.5),signal([1,1],-1,.5))
        np.testing.assert_allclose(result.values,[0,.5,0]);self.assertEqual(result.origin,1)
    def test_ramp_against_exact_integral(self):
        result=convolution(signal([0,1]),signal([0,1]))
        self.assertAlmostEqual(result.values[1].real,1/6)
    def test_independent_quadrature_complex(self):
        x=signal([1+2j,2-1j,-1,3],-.4,.2);h=signal([2j,-2,1],.7,.2)
        y=convolution(x,h)
        def interpolate(s,t):return np.interp(t,s.axis,s.values,left=0,right=0)
        for time,value in zip(y.axis,y.values):
            lo=max(x.axis[0],time-h.axis[-1]);hi=min(x.axis[-1],time-h.axis[0])
            if hi<=lo:reference=0
            else:
                points=sorted(set(v for v in [*x.axis,*(time-h.axis)] if lo<v<hi))
                f=lambda t:interpolate(x,t)*interpolate(h,time-t)
                reference=quad(lambda t:f(t).real,lo,hi,points=points,epsabs=1e-12)[0]+1j*quad(lambda t:f(t).imag,lo,hi,points=points,epsabs=1e-12)[0]
            self.assertAlmostEqual(abs(value-reference),0,places=11)
    def test_autocorrelation_energy_and_hermitian(self):
        x=signal([1+2j,-2j,3],2,.25);r=correlation(x)
        np.testing.assert_allclose(r.values,np.conj(r.values[::-1]),atol=1e-12)
        self.assertEqual(r.origin,-.5)
        energy=quad(lambda t:abs(np.interp(t,x.axis,x.values))**2,x.axis[0],x.axis[-1],points=x.axis[1:-1])[0]
        self.assertAlmostEqual(r.values[2].real,energy)
        normalized=correlation(x,normalized=True)
        self.assertAlmostEqual(normalized.values[2].real,1)
        self.assertLessEqual(np.max(abs(normalized.values)),1+1e-12)
    def test_invalid_input(self):
        with self.assertRaises(ValueError):convolution(signal([1,1]),signal([1,1],step=.1))
        with self.assertRaises(ValueError):correlation(signal([0,0]),normalized=True)
        with self.assertRaises(ValueError):convolution(Signal([1,2]),signal([1,2]))
    def test_symbolic_causal(self):
        result=execute(dict(operation='continuous_convolution',left='exp(-t)',right='exp(-2*t)',causal=True))
        value=parse(result['result'])
        self.assertTrue(result['evaluated']);self.assertEqual(value.subs(T,-1),0)
        self.assertEqual(sp.simplify(value.subs(T,1)-(sp.exp(-1)-sp.exp(-2))),0)
    def test_symbolic_bilateral_gaussians(self):
        result=execute(dict(operation='continuous_convolution',left='exp(-t^2)',right='exp(-t^2)',causal=False))
        self.assertTrue(result['evaluated'])
        self.assertEqual(sp.simplify(parse(result['result'])-sp.sqrt(sp.pi/2)*sp.exp(-T**2/2)),0)

if __name__=='__main__':unittest.main()
