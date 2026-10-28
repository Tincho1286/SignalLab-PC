import unittest,json
import numpy as np
from scipy import signal
from signallab_pc.filter_arithmetic import simulate
from signallab_pc.precision import Encoding
from signallab_pc.filters import Transfer
from signallab_pc.model import Signal

class ExecutionTests(unittest.TestCase):
    def test_rounding_products_and_guard_bits(self):
        x=Signal([.25,.25,0],origin=-3)
        result=simulate(Transfer([.5,.5],[1]),x,Encoding('fixed',2,2),tail=0)
        np.testing.assert_array_equal(result['output'].values,[.25,.5,.25])
        np.testing.assert_array_equal(result['storage_reference'],[.125,.25,.125])
        storage=simulate(Transfer([.5,.5],[1]),x,Encoding('fixed',2,2),tail=0,operations=False)
        np.testing.assert_array_equal(storage['output'].values,[.25,.5,.25])
        self.assertNotIn('productos',storage['metadata']['operation_counts'])
        # Two products can cancel. A wider accumulator avoids clipping the
        # intermediate sum before adding the next memory of DF-II transposed.
        h=Transfer([0,1.5,0],[1,-1.5,0]);x=Signal([1])
        narrow=simulate(h,x,Encoding('fixed',2,2),initial=[1.5,-1.5],tail=0,guard_bits=0)
        wide=simulate(h,x,Encoding('fixed',2,2),initial=[1.5,-1.5],tail=0,guard_bits=3)
        self.assertGreater(narrow['metadata']['operation_counts']['sumas']['overflows'],wide['metadata']['operation_counts']['sumas']['overflows'])

    def test_overflow_modes_and_cycles(self):
        h=Transfer([1.5],[1]);x=Signal([1.5]);q=Encoding('fixed',2,1)
        self.assertEqual(simulate(h,x,q,tail=0)['output'].values[0],1.5)
        self.assertEqual(simulate(h,x,q,tail=0,overflow='wrap')['output'].values[0],-1.5)
        h=Transfer([1],[1,-.5]);x=Signal([0]*8);q=Encoding('fixed',2,2)
        cycle=simulate(h,x,q,initial=[.25],tail=0)
        self.assertEqual(cycle['metadata']['cycle']['period'],1);self.assertTrue(cycle['metadata']['cycle']['nonzero_state'])
        np.testing.assert_array_equal(cycle['output'].values,[.25]*8)
        truncated=simulate(h,x,Encoding('fixed',2,2,'truncate'),initial=[.25],tail=0)
        self.assertFalse(truncated['metadata']['cycle']['nonzero_state'])

    def test_ieee_and_sos_with_independent_reference(self):
        h=Transfer([.3,.15],[1,-.9]);x=Signal([1,0,.7,0,-1,0,0])
        result=simulate(h,x,Encoding('float16'),tail=0)
        b=np.array(h.b.real,dtype=np.float16);a=np.array(h.a.real,dtype=np.float16);memory=np.float16(0);expected=[]
        for value in x.values.real.astype(np.float16):
            y=np.float16(np.float16(b[0]*value)+memory)
            memory=np.float16(np.float16(b[1]*value)-np.float16(a[1]*y));expected.append(y)
        np.testing.assert_array_equal(result['output'].values,expected)
        sos=signal.butter(4,.3,output='sos');h=Transfer.from_sos(sos);x=Signal(np.cos(np.arange(30)*.2)+1j*np.sin(np.arange(30)*.1))
        initial=[.01,-.02,.03,-.04]
        result=simulate(h,x,Encoding('float64'),tail=0,initial=initial)
        expected,_=signal.sosfilt(sos,x.values,zi=np.array(initial,dtype=complex).reshape(-1,2))
        np.testing.assert_allclose(result['output'].values,expected,atol=2e-15,rtol=2e-14)
        self.assertTrue(result['sections']);self.assertEqual(result['system'].sos.shape,sos.shape)

    def test_reference_failure_does_not_hide_finite_output(self):
        result=simulate(Transfer([1],[1,-4]),Signal([1]+[0]*699),Encoding('fixed',2,3),tail=0)
        self.assertTrue(np.all(np.isfinite(result['output'].values)))
        self.assertLess(result['metrics']['finite_reference_samples'],700)
        json.dumps(result['metadata'],allow_nan=False)
        with self.assertRaises(ValueError):simulate(Transfer([1],[1]),Signal([100000]),Encoding('float16'),tail=0)
        with self.assertRaises(ValueError):simulate(Transfer([1],[1,-.5]),Signal([0]),Encoding(),initial=[1,2],tail=0)

if __name__=='__main__':unittest.main()
