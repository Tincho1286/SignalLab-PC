import unittest
import numpy as np
import sympy as sp
from scipy.integrate import quad
from signallab_pc.model import Signal
from signallab_pc.operations import correlation
from signallab_pc.continuous import periodic_correlation
from signallab_pc.symbolic import execute,parse,TAU

def temporal(values,origin=0,step=.25):return Signal(values,origin,step,'s','x','continuous')

class CorrelationVariantsTests(unittest.TestCase):
    def test_discrete_circular_origins_against_definition(self):
        x=Signal([1+2j,3,-1,2j],-3);h=Signal([2,-1j,1,4],2)
        result=correlation(x,h,circular=True)
        expected=[sum(x.values[j]*np.conj(h.values[(int(x.origin)+j-lag-int(h.origin))%4]) for j in range(4)) for lag in range(4)]
        np.testing.assert_allclose(result.values,expected,atol=1e-12)
        np.testing.assert_allclose(correlation(x,h,circular=True,normalization='mean').values,np.array(expected)/4)
        energy=np.sqrt(np.sum(abs(x.values)**2)*np.sum(abs(h.values)**2))
        np.testing.assert_allclose(correlation(x,h,circular=True,normalization='energy').values,np.array(expected)/energy)
    def test_discrete_auto_normalized(self):
        x=Signal([1,2j,3],-7);result=correlation(x,normalization='energy')
        self.assertAlmostEqual(result.values[2].real,1)
        np.testing.assert_allclose(result.values,np.conj(result.values[::-1]),atol=1e-12)
    def test_periodic_continuous_constant(self):
        x=temporal([2]*4);result=periodic_correlation(x)
        np.testing.assert_allclose(result.values,4)
        np.testing.assert_allclose(periodic_correlation(x,normalization='energy').values,1)
        np.testing.assert_allclose(periodic_correlation(temporal([2]*4,step=.5),normalization='mean').values,4)
    def test_periodic_continuous_independent_quadrature(self):
        x=temporal([1+2j,-1,3j,2],.2);h=temporal([2j,1,-1j,3],-.3)
        result=periodic_correlation(x,h);period=4*x.step
        def at(source,time):
            phase=((time-source.origin)/source.step)%4
            return np.interp(phase,np.arange(5),np.r_[source.values,source.values[0]])
        for lag,value in zip(result.axis,result.values):
            fn=lambda t:at(x,t)*np.conj(at(h,t-lag))
            reference=quad(lambda t:fn(t).real,x.origin,x.origin+period,points=x.axis[1:],epsabs=1e-12)[0]+1j*quad(lambda t:fn(t).imag,x.origin,x.origin+period,points=x.axis[1:],epsabs=1e-12)[0]
            self.assertAlmostEqual(abs(value-reference),0,places=10)
        self.assertAlmostEqual(result.origin,.5)
    def test_periodic_continuous_energy_and_bound(self):
        x=temporal([1+2j,-1,3j,2]);r=periodic_correlation(x,normalization='energy')
        self.assertAlmostEqual(r.values[0].real,1);self.assertLessEqual(np.max(abs(r.values)),1+1e-12)
        np.testing.assert_allclose(r.values[1:],np.conj(r.values[:0:-1]),atol=1e-12)
    def test_invalid_normalization_or_period(self):
        with self.assertRaises(ValueError):periodic_correlation(temporal([0,0]),normalization='energy')
        with self.assertRaises(ValueError):periodic_correlation(temporal([1,2]),temporal([1,2,3]))
        with self.assertRaises(ValueError):correlation(Signal([1]),circular=False,normalization='mean')
    def test_symbolic_bilateral(self):
        result=execute(dict(operation='continuous_correlation',left='exp(-t^2)',right='exp(-t^2)'))
        self.assertTrue(result['evaluated']);self.assertEqual(sp.simplify(parse(result['result'])-sp.sqrt(sp.pi/2)*sp.exp(-TAU**2/2)),0)
    def test_symbolic_period_and_complex_conjugation(self):
        result=execute(dict(operation='continuous_correlation',left='sin(t)',right='i*sin(t)',period='2*pi'))
        self.assertTrue(result['evaluated']);self.assertEqual(sp.simplify(parse(result['result'])+sp.I*sp.pi*sp.cos(TAU)),0)

if __name__=='__main__':unittest.main()
