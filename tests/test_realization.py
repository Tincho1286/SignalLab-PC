import unittest
import numpy as np
from scipy import signal
from signallab_pc.filters import Transfer
from signallab_pc.realization import realize_system
from signallab_pc.state_space import StateModel


class RealizationTests(unittest.TestCase):
    def test_analog_complex_and_cancellation_response(self):
        omega=np.array([.1,.5,1.3,3.])
        for source in (Transfer([1,2],[1,3,2],'analog'),Transfer([2,1+1j],[1,2,1],'analog'),Transfer([1,-1],[1,-1],'analog'),Transfer([0],[1,-1],'analog')):
            value=realize_system(source);model=value.to_model()
            np.testing.assert_allclose(model.response(omega)[:,0,0],source.response(omega),atol=2e-14,rtol=2e-13)
            self.assertEqual(model.states,len(source.a)-1)
        self.assertEqual(realize_system(Transfer([1,-1],[1,-1],'analog')).states,1)
    def test_digital_fir_delays_and_iir_impulses(self):
        impulse=np.r_[1.,np.zeros(29)]
        for source in (Transfer([0,0,2],[1]),Transfer([.2,.5,.2],[1,-.3,.1]),Transfer([1,0,1],[1]),Transfer([1e-30,1],[1,-.2])):
            realization=realize_system(source);model=realization.to_model(.1)
            _,actual,_=model.simulate(impulse)
            np.testing.assert_allclose(actual[:,0],signal.lfilter(source.b,source.a,impulse),atol=1e-15,rtol=2e-14)
            w=np.array([.1,.4,1.,2.]);np.testing.assert_allclose(model.response(w/.1)[:,0,0],source.response(w),atol=2e-14)
        value=realize_system(Transfer([1,0],[1,0]));self.assertEqual(value.states,0)
        value=realize_system(Transfer([1,-.2],[1,-.2]));self.assertEqual(value.states,1)
    def test_sos_preserved_and_state_import_matches_same_realization(self):
        sos=signal.butter(8,[.3,.9],btype='bandpass',fs=2*np.pi,output='sos');source=Transfer.from_sos(sos)
        value=realize_system(source);self.assertTrue(value.cascade);self.assertEqual(len(value.stages),len(sos))
        before=source.sos.copy();model=StateModel.from_transfer(source,.2)
        impulse=np.r_[1.,np.zeros(199)];_,actual,_=model.simulate(impulse)
        np.testing.assert_allclose(actual[:,0],signal.sosfilt(sos,impulse),atol=2e-15,rtol=2e-11)
        np.testing.assert_array_equal(source.sos,before)
        for k,stage in enumerate(value.stages):np.testing.assert_array_equal(stage.a,sos[k,3:]/sos[k,3])
    def test_static_zero_orders_and_explicit_unavailable_cases(self):
        for domain,dt in [('analog',None),('digital',.25)]:
            value=realize_system(Transfer([2j],[1],domain));model=value.to_model(dt)
            self.assertEqual(model.states,0);self.assertEqual(model.D[0,0],2j)
        with self.assertRaises(ValueError):realize_system(Transfer([1,1],[1],'analog'))
        with self.assertRaises(ValueError):realize_system(Transfer([1],[1]),1)
        for dt in (None,0,-1,np.inf):
            with self.assertRaises(ValueError):realize_system(Transfer([1],[1])).to_model(dt)
        with self.assertRaises(ValueError):realize_system(Transfer([1],[1],'analog')).to_model(.1)

if __name__=='__main__':unittest.main()
