import unittest
import numpy as np
from scipy import signal
from signallab_pc.filters import Transfer
from signallab_pc.phase_compensation import design_compensator

class CompensationTests(unittest.TestCase):
    def test_known_gain_and_delayed_inverse(self):
        result=design_compensator(Transfer([2],[1]),0,np.pi,1,0,regularization=0)
        np.testing.assert_allclose(result['systems'][0].b,[.5],atol=1e-14)
        result=design_compensator(Transfer([1],[1,-.5]),0,np.pi,8,3,regularization=0)
        expected=np.zeros(8);expected[3:5]=[1,-.5]
        np.testing.assert_allclose(result['systems'][0].b,expected,atol=2e-14)
        self.assertLess(result['compensation']['metrics']['relative_max'],1e-12)
        impulse=np.r_[1.,np.zeros(39)];joint=result['systems'][1]
        actual=signal.lfilter(joint.b,joint.a,impulse);target=np.zeros(40);target[3]=1
        np.testing.assert_allclose(actual,target,atol=2e-14)
    def test_nonminimum_phase_is_approximated_with_delay(self):
        data=design_compensator(Transfer([1,-2],[1]),0,np.pi,33,16,regularization=0)['compensation']
        self.assertLess(data['metrics']['relative_rms'],1e-4)
        self.assertGreater(data['metrics']['relative_rms'],0)
        self.assertTrue(np.isfinite(data['compensator'].b).all())
    def test_zero_in_band_and_regularization_are_not_hidden(self):
        system=Transfer([1,-1],[1]);one=design_compensator(system,0,np.pi,15,7,regularization=0)['compensation'];two=design_compensator(system,0,np.pi,15,7,regularization=.1)['compensation']
        self.assertGreaterEqual(one['metrics']['relative_max'],1)
        self.assertLess(np.linalg.norm(two['compensator'].b),np.linalg.norm(one['compensator'].b))
        self.assertGreater(two['metrics']['relative_rms'],one['metrics']['relative_rms'])
    def test_sos_snapshot_and_explicit_scope(self):
        source=Transfer.from_sos(signal.butter(6,.7,fs=2*np.pi,output='sos'));before=source.sos.copy()
        result=design_compensator(source,.1,.6,15,10);data=result['compensation']
        np.testing.assert_allclose(data['joint'],source.response(data['omega'])*data['compensator'].response(data['omega']))
        np.testing.assert_array_equal(source.sos,before)
        for system in (Transfer([1],[1,-1.1]),Transfer([0],[1]),Transfer([1j],[1]),Transfer([1],[1],'analog')):
            with self.assertRaises(ValueError):design_compensator(system,0,np.pi,5,2)
        for args in ((-.1,1,5,2),(0,4,5,2),(1,.1,5,2),(0,1,0,2),(0,1,5,-1),(0,1,5,1.5)):
            with self.assertRaises(ValueError):design_compensator(Transfer([1],[1]),*args)

if __name__=='__main__':unittest.main()
