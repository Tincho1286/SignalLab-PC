import unittest,json,csv,tempfile
from pathlib import Path
import numpy as np
from signallab_pc.model import Signal
from signallab_pc.phase_reconstruction import reconstruct,export_reconstruction

def source(values,origin=-np.pi):return Signal(values,origin,2*np.pi/(len(values)-1),'rad/muestra','Dato de prueba','frequency')

class ReconstructionTests(unittest.TestCase):
    def test_magnitude_and_delay_against_analytic_iir(self):
        w=np.linspace(-np.pi,np.pi,257);h=1/(1-.5*np.exp(-1j*w))
        result=reconstruct(source(abs(h)))['reconstruction']
        np.testing.assert_allclose(result['response'].values,h,atol=3e-14)
        expected=(.5*np.cos(w)-.25)/(1.25-np.cos(w))
        np.testing.assert_allclose(result['delay'],expected,atol=2e-12)
        self.assertLess(result['metadata']['grid_input_error'],1e-14)

    def test_phase_fixes_gain_but_does_not_invent_delay(self):
        w=np.linspace(-np.pi,np.pi,257);base=1/(1-.5*np.exp(-1j*w));phase=-np.arctan2(.5*np.sin(w),1-.5*np.cos(w))-3*w+.4
        result=reconstruct(source(phase),'phase',reference_gain=2,delay=3)['reconstruction']
        np.testing.assert_allclose(result['response'].values,base*np.exp(.4j-3j*w),atol=6e-14)
        index=np.flatnonzero(result['impulse'].axis==3)[0];self.assertAlmostEqual(abs(result['impulse'].values[index]),1,places=13)
        with self.assertRaisesRegex(ValueError,'no cierra'):reconstruct(source(phase),'phase',delay=0)
        with self.assertRaises(ValueError):reconstruct(source(phase),'phase',delay=3,reference_gain=0)

    def test_complex_response_shifted_period_and_odd_impulse_grid(self):
        w=np.linspace(0,2*np.pi,257);pole=.3+.2j;values=abs(1/(1-pole*np.exp(-1j*w)))
        result=reconstruct(source(values,0))['reconstruction'];target=1/(1-pole*np.exp(-1j*result['omega']))
        np.testing.assert_allclose(result['response'].values,target,atol=3e-14)
        w=np.linspace(-np.pi,np.pi,130);h=1-.5*np.exp(-1j*w);result=reconstruct(source(abs(h)))['reconstruction'];impulse=result['impulse']
        expected=np.zeros(len(impulse.values));expected[impulse.axis==0]=1;expected[impulse.axis==1]=-.5
        np.testing.assert_allclose(impulse.values,expected,atol=5e-14)

    def test_floor_partial_band_and_exports_are_explicit(self):
        w=np.linspace(-np.pi,np.pi,257);m=1+np.cos(w)
        with self.assertRaises(ValueError):reconstruct(source(m))
        result=reconstruct(source(m),floor=.001)['reconstruction']
        self.assertGreater(result['metadata']['modified_points'],0);self.assertAlmostEqual(result['magnitude'][0],.001,places=13)
        data=source(np.ones(257));data.step=np.pi/256
        with self.assertRaisesRegex(ValueError,'período completo'):reconstruct(data)
        data.origin=0
        half=reconstruct(data,real_half_period=True)['reconstruction'];self.assertTrue(half['metadata']['completed_by_real_symmetry']);np.testing.assert_allclose(half['response'].values,1,atol=1e-14)
        positive=np.linspace(0,np.pi,129);phase=-np.arctan2(.5*np.sin(positive),1-.5*np.cos(positive))-2*positive
        input_phase=Signal(phase,0,np.pi/128,'rad/muestra','Fase real','frequency')
        half=reconstruct(input_phase,'phase',real_half_period=True,reference_gain=2,delay=2)['reconstruction'];full_w=half['omega']
        np.testing.assert_allclose(half['response'].values,np.exp(-2j*full_w)/(1-.5*np.exp(-1j*full_w)),atol=5e-14)
        db=reconstruct(source(20*np.log10(np.maximum(m,.001))),'db')['reconstruction']
        np.testing.assert_allclose(result['response'].values,db['response'].values,atol=1e-13)
        json.dumps(result['response'].metadata,allow_nan=False)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'comparison.csv';export_reconstruction(result,path)
            with path.open() as stream:self.assertEqual(len(list(csv.DictReader(stream))),257)
        self.assertTrue(result['impulse'].metadata['not_a_fir_definition'])

if __name__=='__main__':unittest.main()
