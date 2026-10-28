import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from numpy.testing import assert_allclose
from signallab_pc.state_space import StateModel
from signallab_pc.filters import Transfer
from signallab_pc.project import Project

class StateSpaceTests(unittest.TestCase):
    def scalar(self,dt=None):return StateModel([[-2]],[[1]],[[3]],[[.5]],dt)
    def test_continuous_initial_state_and_zoh_step(self):
        model=self.scalar();t,y,x=model.simulate(np.ones(51),step=.02,initial=[2])
        expected=.5+1.5*np.exp(-2*t)
        assert_allclose(x[:,0],expected,rtol=1e-13)
        assert_allclose(y[:,0],3*expected+.5,rtol=1e-13)
    def test_discrete_mimo_recurrence_and_feedthrough(self):
        model=StateModel([[.5,0],[0,.25]],np.eye(2),[[1,2],[0,1]],[[1,0],[0,2]],.1)
        values=np.array([[1,2],[3,4],[5,6]])
        t,y,x=model.simulate(values,initial=[2,3])
        assert_allclose(t,[0,.1,.2]);assert_allclose(x,[[2,3],[2,2.75],[4,4.6875]])
        assert_allclose(y,[[9,7],[10.5,10.75],[18.375,16.6875]])
    def test_ranks_and_internal_stability(self):
        m=StateModel([[-1,0],[0,2]],[[1],[0]],[[1,0]],[[0]])
        a=m.analysis();self.assertEqual(a['controllability_rank'],1);self.assertEqual(a['observability_rank'],1)
        self.assertEqual(a['stability'],'Internamente inestable')
        m=StateModel([[-1,0],[0,-2]],np.eye(2),np.eye(2),np.zeros((2,2)))
        self.assertEqual(m.analysis()['observability_rank'],2);self.assertEqual(m.analysis()['controllability_rank'],2)
    def test_frequency_analog_and_digital_units(self):
        w=np.array([0.,.2,2.])
        assert_allclose(self.scalar().response(w)[:,0,0],3/(2+1j*w)+.5)
        m=StateModel([[.5]],[[2]],[[3]],[[1]],.2)
        assert_allclose(m.response(w)[:,0,0],6/(np.exp(1j*w*.2)-.5)+1)
    def test_complex_channel_conversion(self):
        m=StateModel([[-1+2j]],[[1-1j]],[[2+3j]],[[.25j]])
        w=np.array([.1,1,4]);assert_allclose(m.to_transfer().response(w),m.response(w)[:,0,0],rtol=1e-12)
    def test_analog_transfer_roundtrip(self):
        source=Transfer([2,3],[1,4,5],'analog')
        model=StateModel.from_transfer(source);w=np.linspace(0,5,25)
        assert_allclose(model.response(w)[:,0,0],source.response(w),atol=1e-13)
        assert_allclose(model.to_transfer().response(w),source.response(w),atol=1e-13)
    def test_digital_roundtrips_preserve_delays_and_fir(self):
        for b,a in [([0,1],[1]),([1,2,3],[1]),([2,1],[2,-.5,.1]),([1],[1,-.2])]:
            with self.subTest(b=b,a=a):
                source=Transfer(b,a);model=StateModel.from_transfer(source,.125);w=np.linspace(.1,2.8,25)
                assert_allclose(model.response(w/.125)[:,0,0],source.response(w),atol=1e-12)
                assert_allclose(model.to_transfer().response(w),source.response(w),atol=1e-12)
        m=StateModel.from_transfer(Transfer([0,1],[1]),.1)
        assert_allclose(m.simulate([1,2,3])[1][:,0],[0,1,2])
    def test_zoh_and_bilinear_discretization(self):
        m=self.scalar();d=m.discretize(.1);assert_allclose(d.A,[[np.exp(-.2)]]);assert_allclose(d.B,[[(1-np.exp(-.2))/2]])
        d=m.discretize(.1,'bilinear');assert_allclose(d.A,[[(1-.1)/(1+.1)]])
        integrator=StateModel([[0]],[[2]],[[1]],[[0]]).discretize(.1)
        assert_allclose(integrator.A,[[1]]);assert_allclose(integrator.B,[[.2]])
    def test_static_gain_with_zero_state_shapes(self):
        m=StateModel.from_transfer(Transfer([2j],[1],'analog'))
        self.assertEqual(m.states,0);assert_allclose(m.simulate([1,2],step=.1)[1][:,0],[2j,4j])
        assert_allclose(m.response([0,2])[:,0,0],[2j,2j]);self.assertEqual(m.analysis()['states'],0)
        self.assertEqual(m.discretize(.2).B.shape,(0,1))
        p=Project();key=p.add(m);m.D[0,0]=4
        self.assertEqual(p.get(key).D[0,0],2j)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'project.json';p.save(path);q=Project();q.merge(path)
            restored=q.get(q.headers()[0]['id'])
            self.assertEqual(restored.B.shape,(0,1));self.assertEqual(restored.C.shape,(1,0));self.assertEqual(restored.D[0,0],2j)
    def test_schema_one_compatibility_and_atomic_invalid_model(self):
        p=Project();p.add(Transfer([1],[1]))
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'p.json';p.save(path);doc=json.loads(path.read_text());doc['schema_version']=1;path.write_text(json.dumps(doc))
            q=Project();self.assertEqual(q.merge(path),1)
            p.add(self.scalar());p.save(path);doc=json.loads(path.read_text());doc['records'][-1]['data']['D']['shape']=[2,1];path.write_text(json.dumps(doc))
            before=q.records()
            with self.assertRaises(ValueError):q.merge(path)
            self.assertEqual(q.records(),before)
    def test_reject_invalid_models_clocks_and_channels(self):
        with self.assertRaises(ValueError):StateModel([[1,2]],[[1]],[[1]],[[0]])
        with self.assertRaises(ValueError):self.scalar(.1).simulate([1,2],step=.2)
        with self.assertRaises(ValueError):self.scalar().simulate([1,2],step=.1,initial=[1,2])
        with self.assertRaises(ValueError):self.scalar().to_transfer(1,0)
        with self.assertRaises(ValueError):StateModel.from_transfer(Transfer([1],[1]))
        with self.assertRaises(ValueError):self.scalar(.1).discretize(.1)
    def test_small_nonzero_numerator_is_not_trimmed(self):
        for domain in ('analog','digital'):
            source=Transfer([1e-20,2e-22],[1,2],domain)
            model=StateModel.from_transfer(source,.1 if domain=='digital' else None)
            w=np.array([.1,.5,1.])
            assert_allclose(model.response(w/.1 if domain=='digital' else w)[:,0,0],source.response(w),rtol=1e-13,atol=0)
            self.assertNotEqual(model.D[0,0],0)
    def test_singular_frequency_is_unavailable(self):
        m=StateModel([[0]],[[1]],[[1]],[[0]])
        self.assertTrue(np.isnan(m.response([0])[0,0,0]));assert_allclose(m.response([1])[0,0,0],-1j)

if __name__=='__main__':unittest.main()
