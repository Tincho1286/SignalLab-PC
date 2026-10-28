import unittest
import numpy as np
from scipy.signal import firwin
from signallab_pc.model import Signal
from signallab_pc.sampling import resample_rational

class RationalResamplingTests(unittest.TestCase):
    def test_clock_length_and_reduced_ratio(self):
        x=Signal(np.arange(100),-7,metadata={'sample_rate_hz':48000,'time_start_s':3.25})
        y=resample_rational(x,294,320)
        self.assertEqual(y.values.size,92);self.assertEqual(y.origin,0)
        self.assertEqual(y.metadata['sample_rate_hz'],44100)
        self.assertEqual(y.metadata['time_start_s'],3.25)
        self.assertEqual((y.metadata['up'],y.metadata['down']),(147,160))
        self.assertEqual(x.origin,-7)
    def test_definition_against_explicit_fir_sum(self):
        x=Signal([1+1j,2,-1j,3,0,2]);up,down,width=3,2,4
        y=resample_rational(x,up,down,rate=100,half_width=width)
        kernel=firwin(2*width*max(up,down)+1,1/max(up,down),window=('kaiser',5))
        center=(len(kernel)-1)//2
        expected=[]
        for m in range(y.values.size):
            expected.append(sum(up*v*kernel[center+m*down-n*up] for n,v in enumerate(x.values) if 0<=center+m*down-n*up<len(kernel)))
        np.testing.assert_allclose(y.values,expected,rtol=1e-13,atol=1e-13)
    def test_antialias_rejects_out_of_band_tone(self):
        t=np.arange(8000)/1000
        low=resample_rational(Signal(np.exp(2j*np.pi*50*t)),1,4,rate=1000)
        high=resample_rational(Signal(np.exp(2j*np.pi*400*t)),1,4,rate=1000)
        self.assertLess(abs(np.mean(abs(low.values[100:-100]))-1),.003)
        self.assertLess(np.max(abs(high.values[100:-100])),.003)
        self.assertAlmostEqual(np.mean(abs(np.exp(2j*np.pi*400*t)[::4])),1)
    def test_identity_and_zero(self):
        x=Signal([1,2j,-3]);y=resample_rational(x,2,2,rate=10)
        np.testing.assert_array_equal(x.values,y.values);self.assertFalse(y.metadata['antialias_filter'])
        np.testing.assert_array_equal(resample_rational(Signal([0,0]),3,2,rate=10).values,0)
    def test_invalid_parameters(self):
        x=Signal([1,2])
        for kwargs in [{'up':0,'down':1,'rate':10},{'up':1,'down':2,'rate':0},{'up':1,'down':2,'rate':10,'beta':-1}]:
            with self.assertRaises(ValueError):resample_rational(x,**kwargs)
        with self.assertRaises(ValueError):resample_rational(Signal([1]),1,2,rate=10,boundary='line')

if __name__=='__main__':unittest.main()
