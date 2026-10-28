import unittest
import numpy as np
from signallab_pc.filters import Transfer,from_poles_zeros
from signallab_pc.frequency_analysis import analyze_frequency
from signallab_pc.pole_zero_analysis import analyze_roots
from signallab_pc.project import encode,decode
from signallab_pc.course_tools import inverse_z_contour
from signallab_pc.symbolic import execute
from signallab_pc.model import Signal
from signallab_pc.realization import realize_system

class NoncausalDesignTests(unittest.TestCase):
    def test_noncausal_zpk_matches_positive_z_and_origin_roots(self):
        w=np.linspace(-2.8,2.8,251);z=np.exp(1j*w)
        for zeros,poles,gain in [([0,0],[],1),([.2,-.7],[.5],2),([0,-.4],[],1),([],[.2,.5],1)]:
            h=from_poles_zeros(zeros,poles,gain)
            expected=gain*np.prod(z[:,None]-np.array(zeros),axis=1)/np.prod(z[:,None]-np.array(poles),axis=1)
            np.testing.assert_allclose(h.response(w),expected,atol=4e-14)
            actual_z,actual_p=analyze_roots(h)
            np.testing.assert_allclose(np.sort_complex(actual_z),np.sort_complex(zeros),atol=2e-14)
            np.testing.assert_allclose(np.sort_complex(actual_p),np.sort_complex(poles),atol=2e-14)
        h=from_poles_zeros([0,0],[])
        np.testing.assert_allclose(h.group_delay(w),-2,atol=1e-15)
        np.testing.assert_allclose(analyze_frequency(h,w).delay,-2,atol=1e-15)

    def test_formula_reuse_and_persistence_preserve_advance_once(self):
        for expression,function in [('z^2+1',lambda z:z*z+1),('z^2/(z-.5)',lambda z:z*z/(z-.5))]:
            exact=execute(dict(operation='system_formula',domain='digital',expression=expression))
            h=Transfer([complex(*v) for v in exact['numeric_b']],[complex(*v) for v in exact['numeric_a']],advance=exact['advance'])
            kind,payload=encode(h);copy=decode(kind,payload)
            w=np.linspace(.05,1.3,101);np.testing.assert_allclose(copy.response(w),function(np.exp(1j*w)),atol=5e-14)
            self.assertEqual(copy.advance,h.advance);self.assertEqual(copy.to_document()['advance'],h.advance);self.assertEqual(copy.to_document()['version'],2)
        legacy=analyze_frequency(Transfer([1],[1]),np.array([.2,.4]),advance=2)
        np.testing.assert_allclose(legacy.delay,[-2,-2]);self.assertEqual(legacy.advance,2)

    def test_contour_includes_negative_indices(self):
        h=from_poles_zeros([1j,-1j],[])
        result=inverse_z_contour(h,'stable',1.,-4,9,1024)['signals'][0]
        expected=np.zeros(9);expected[2]=1;expected[4]=1
        np.testing.assert_allclose(result.values,expected,atol=2e-14)
        with self.assertRaises(ValueError):h.apply(Signal([1,0,0]))
        with self.assertRaises(ValueError):realize_system(h)

    def test_causal_and_analog_definitions_keep_existing_conventions(self):
        causal=from_poles_zeros([],[.5]);self.assertEqual(causal.advance,0)
        np.testing.assert_allclose(causal.apply(Signal([1,0,0])).values,[0,1,.5])
        analog=from_poles_zeros([-.2,-.3],[-1],domain='analog');w=np.array([0,.3,1.])
        np.testing.assert_allclose(analog.response(w),(1j*w+.2)*(1j*w+.3)/(1j*w+1))
        reduced=Transfer([0,1],[1],advance=1);self.assertEqual(reduced.advance,0);np.testing.assert_array_equal(reduced.b,[1])

if __name__=='__main__':unittest.main()
