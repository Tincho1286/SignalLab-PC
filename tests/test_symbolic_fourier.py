import unittest
import numpy as np
import sympy as sp
from signallab_pc.symbolic import execute,parse,T,W
from signallab_pc.fourier import energy_density
from signallab_pc.model import Signal

class SymbolicFourierTests(unittest.TestCase):
    def transform(self,expression,inverse=False):return execute(dict(operation='inverse_fourier_angular' if inverse else 'fourier_angular',expression=expression))
    def test_gaussian_angular_and_inverse(self):
        direct=self.transform('exp(-t^2)');self.assertTrue(direct['evaluated']);self.assertEqual(direct['condition'],'True')
        self.assertEqual(sp.simplify(parse(direct['result'])-sp.sqrt(sp.pi)*sp.exp(-W**2/4)),0)
        inverse=self.transform(direct['result'],True)
        self.assertEqual(sp.simplify(parse(inverse['result'])-sp.exp(-T**2)),0)
    def test_two_sided_exponential(self):
        result=self.transform('exp(-abs(t))')
        self.assertEqual(sp.simplify(parse(result['result'])-2/(1+W**2)),0)
    def test_time_shift_phase(self):
        result=self.transform('exp(-(t-2)^2)')
        self.assertEqual(sp.simplify(parse(result['result'])-sp.sqrt(sp.pi)*sp.exp(-W**2/4)*sp.exp(-2*sp.I*W)),0)
    def test_complex_grid_and_constant(self):
        result=execute(dict(operation='expression_grid',variable='w',expression='exp(-i*w)',start=0,stop=1,count=5))
        values=np.array([complex(*v) for v in result['samples']]);np.testing.assert_allclose(values,np.exp(-1j*np.linspace(0,1,5)))
        result=execute(dict(operation='expression_grid',variable='t',expression='2',start=0,stop=1,count=3));self.assertEqual(result['samples'],[[2.,0.]]*3)
    def test_no_distribution_or_singular_grid(self):
        for expression in ['dirac(t)','a*t']:
            with self.assertRaises(ValueError):execute(dict(operation='expression_grid',variable='t',expression=expression,start=0,stop=1,count=5))
        with self.assertRaises(FloatingPointError):execute(dict(operation='expression_grid',variable='t',expression='1/t',start=0,stop=1,count=5))
    def test_output_variable_collision(self):
        with self.assertRaises(ValueError):self.transform('cos(w*t)')
        with self.assertRaises(ValueError):self.transform('exp(-t*w^2)',True)
    def test_dtft_finite_matches_definition(self):
        result=execute(dict(operation='dtft_expression',expression='1+i*n',lower='-2',upper='3'))
        self.assertTrue(result['evaluated'])
        expression=parse(result['result'])
        for omega in [0,.3,np.pi]:
            expected=sum((1+1j*n)*np.exp(-1j*omega*n) for n in range(-2,4))
            self.assertAlmostEqual(abs(complex(expression.subs(W,omega).evalf())-expected),0,places=11)
    def test_dtft_geometric_infinite(self):
        result=execute(dict(operation='dtft_expression',expression='(1/2)^n',lower='0',upper='oo'))
        self.assertTrue(result['evaluated'])
        self.assertEqual(sp.simplify(parse(result['result'])-1/(1-sp.exp(-sp.I*W)/2)),0)
        self.assertEqual(result['frequency_units'],'rad/muestra')
    def test_dtft_left_sided_and_divergent(self):
        result=execute(dict(operation='dtft_expression',expression='2^n',lower='-oo',upper='0'))
        self.assertTrue(result['evaluated'])
        self.assertEqual(sp.simplify(parse(result['result'])-1/(1-sp.exp(sp.I*W)/2)),0)
        divergent=execute(dict(operation='dtft_expression',expression='2^n',lower='0',upper='oo'))
        self.assertFalse(divergent['evaluated'])
    def test_dtft_invalid_limits(self):
        with self.assertRaises(ValueError):execute(dict(operation='dtft_expression',expression='n',lower='1/2',upper='5'))
    def test_spectral_density_rejects_temporal_samples(self):
        with self.assertRaises(ValueError):energy_density(Signal([1,2],0,.1,'s','x','continuous',metadata={'operation':'fourier_expression_samples'}))
        result=energy_density(Signal([1,2],0,.1,'rad/s','X','frequency',metadata={'operation':'fourier_expression_samples'}))
        np.testing.assert_array_equal(result.values,[1,4])

if __name__=='__main__':unittest.main()
