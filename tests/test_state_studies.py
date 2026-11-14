"""Reference state transformations, exact equilibria and stored trajectory views."""
import os,unittest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from unittest.mock import patch
import numpy as np
from numpy.testing import assert_allclose
from PySide6.QtWidgets import QApplication
from signallab_pc.state_space import StateModel
from signallab_pc.model import Signal
from signallab_pc.state_simulation_inputs import prepare_inputs
from signallab_pc import state_studies as studies,state_response_studies as response


class Numerical(unittest.TestCase):
    def test_diagnostics_show_the_actual_krylov_matrices_and_scaled_threshold(self):
        m=StateModel([[-1,0],[0,-2]],[[1],[0]],[[1,0]],[[0]]);data=m.analysis(details=True);d=data['diagnostics']
        assert_allclose(d['controllability'],[[1,-1],[0,0]]);assert_allclose(d['observability'],[[1,0],[-1,0]]);assert_allclose(d['controllability_singular'],[np.sqrt(2),0]);self.assertEqual(data['controllability_rank'],1);self.assertEqual(data['observability_rank'],1);self.assertGreater(d['controllability_threshold'],0)
    def test_rank_scaling_avoids_overflow_and_handles_subnormal_coefficients(self):
        for amplitude in (1e308,np.nextafter(0.,1.)):
            m=StateModel([[0,0],[0,0]],[[amplitude,0],[0,amplitude]],[[1,0],[0,1]],np.zeros((2,2)));d=m.analysis(details=True);self.assertEqual(d['controllability_rank'],2);self.assertTrue(np.isfinite(d['diagnostics']['controllability_singular']).all())
        m=StateModel([[0]],np.full((1,4),1e308),[[1]],np.zeros((1,4)));self.assertEqual(m.analysis()['controllability_rank'],1)
        huge=StateModel(np.full((2,2),1e308),np.zeros((2,1)),np.zeros((1,2)),[[0]]).analysis();self.assertIsNone(huge['stability_tolerance']);self.assertEqual(huge['poles'],[]);self.assertIn('No determinada',huge['stability'])
    def test_real_coordinate_change_preserves_initial_response_and_clock(self):
        m=StateModel([[.5,.25],[0,.2]],[[1,0],[0,1]],[[1,2]],[[.1,.3]],.25);P=np.array([[1,1],[0,1]]);x0=[2,-1];r=studies.change_coordinates(m,P,x0);q=r['model']
        assert_allclose(q.A,[[.5,.55],[0,.2]]);assert_allclose(r['numeric_initial'],[3,-1]);self.assertEqual(q.dt,.25)
        u=np.array([[1,2],[0,0],[-1,1],[0,0]]);_,y,x=m.simulate(u,initial=x0);_,v,z=q.simulate(u,initial=r['numeric_initial']);assert_allclose(y,v,atol=2e-15);assert_allclose(x,z@P.T,atol=2e-15)
    def test_complex_coordinate_change_uses_inverse_not_conjugate_transpose(self):
        m=StateModel([[-1,2],[0,-2]],[[1],[2]],[[1,1j]],[[0]]);P=np.array([[1+1j,2],[0,1-1j]]);r=studies.change_coordinates(m,P,[1,2j]);q=r['model']
        assert_allclose(q.A,np.linalg.solve(P,m.A@P));assert_allclose(q.B,np.linalg.solve(P,m.B));assert_allclose(q.C,m.C@P);assert_allclose(r['numeric_initial'],np.linalg.solve(P,[1,2j]))
        with self.assertRaises(ValueError):studies.change_coordinates(m,[[1+1j,2+2j],[3-3j,6-6j]])
    def test_coordinate_ranges_keep_exact_matrices_instead_of_zeroing(self):
        m=StateModel([[-1]],[[1]],[[1]],[[0]]);r=studies.change_coordinates(m,[[np.nextafter(0.,1.)]],[1]);self.assertIsNone(r['model']);self.assertIsNone(r['numeric_initial']);self.assertTrue(r['notice']);self.assertIn('B',r['exact_matrices'])
    def test_unique_continuous_and_discrete_equilibria_include_feedthrough(self):
        a=studies.equilibrium(StateModel([[-2]],[[3]],[[4]],[[5]]),[2]);assert_allclose(a['numeric_state'],[3]);assert_allclose(a['numeric_output'],[22]);self.assertEqual(a['kind'],'unique')
        d=studies.equilibrium(StateModel([[.5]],[[1]],[[1]],[[0]],.1),[2]);assert_allclose(d['numeric_state'],[4]);assert_allclose(d['numeric_output'],[4])
    def test_equilibrium_distinguishes_families_inconsistency_and_tiny_modes(self):
        m=StateModel([[0,0],[0,-1]],[[1],[0]],[[1,1]],[[0]]);family=studies.equilibrium(m,[0]);self.assertEqual(family['kind'],'family');self.assertEqual(family['parameters'],1);self.assertEqual(studies.equilibrium(m,[1])['kind'],'inconsistent')
        tiny=StateModel([[-1,0],[0,-1e-20]],[[0],[1]],[[0,1]],[[0]]);r=studies.equilibrium(tiny,[1]);self.assertEqual(r['kind'],'unique');assert_allclose(r['numeric_state'],[0,1e20])
    def test_equilibrium_underflow_retains_the_nonzero_exact_state(self):
        m=StateModel([[-1e160]],[[1e-162]],[[1]],[[0]]);r=studies.equilibrium(m,[1e-162]);self.assertEqual(r['kind'],'unique');self.assertIsNone(r['numeric_state']);self.assertNotEqual(r['particular']['values'][0][0],'0')
    def test_static_model_equilibrium_and_coordinates_have_empty_state(self):
        m=StateModel(np.empty((0,0)),np.empty((0,1)),np.empty((1,0)),[[2]]);r=studies.equilibrium(m,[3]);self.assertEqual(r['kind'],'unique');self.assertEqual(r['numeric_state'].shape,(0,));assert_allclose(r['numeric_output'],[6]);self.assertEqual(studies.change_coordinates(m,np.empty((0,0)))['model'].states,0)
    def test_discrete_decomposition_and_inspector_match_vector_equations(self):
        m=StateModel([[.5,1],[0,.25]],[[1],[2]],[[1,-1]],[[3]],.1);source=Signal([1,0,2],-8);grid=prepare_inputs(m,[source]);run=response.simulate(m,grid,[2,-1],True);a,b,c=run['components'];assert_allclose(a['output'],b['output']+c['output']);assert_allclose(a['states'],b['states']+c['states'])
        trace=response.capture(run);row=response.inspect(trace,0);self.assertEqual(row['computed'],6);self.assertEqual(row['reconstructed'],6);next_state=response.inspect(trace,0,family='state');self.assertEqual(next_state['computed'],1);self.assertEqual(next_state['target_coordinate'],-7)
        natural=response.capture(run,2);self.assertEqual(response.inspect(natural,0)['computed'],3);self.assertTrue(np.all(natural['inputs']==0));forced=response.capture(run,1);self.assertTrue(np.all(forced['states'][0]==0))
        run['components'][0]['states'][:]=0;self.assertEqual(response.inspect(trace,0)['computed'],6)
        with self.assertRaises(ValueError):response.inspect(trace,2,family='state')
    def test_continuous_zoh_components_use_exponential_not_euler(self):
        m=StateModel([[-1]],[[1]],[[2]],[[3]]);grid=prepare_inputs(m,[Signal([1,1,0],4,.5,'s','u','continuous')]);run=response.simulate(m,grid,[3],True);a,b,c=run['components'];expected=1+2*np.exp(-np.arange(3)*.5)
        assert_allclose(a['states'][:,0],expected);assert_allclose(a['output'][:,0],2*expected+3*np.array([1,1,0]));assert_allclose(c['states'][:,0],3*np.exp(-np.arange(3)*.5));assert_allclose(a['states'],b['states']+c['states'])
        trace=response.capture(run);step=response.inspect(trace,0,family='state');self.assertAlmostEqual(step['computed'].real,1+2*np.exp(-.5));self.assertEqual(step['target_coordinate'],4.5)


class Interface(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        from test_workflow_contracts import Host
        self.host=Host();self.errors=[];self.warning=patch('PySide6.QtWidgets.QMessageBox.warning',side_effect=lambda *a:self.errors.append(str(a[2])));self.warning.start();self.widgets=[]
    def tearDown(self):
        self.warning.stop()
        for widget in self.widgets:widget.close();widget.deleteLater()
        self.host.bar.close();self.app.processEvents()
    def panel(self,action):
        from signallab_pc.state_space_panel import StateSpacePanel
        panel=StateSpacePanel(self.host,action);self.widgets.append(panel);return panel
    def test_analysis_studies_are_local_and_publish_a_reusable_transformed_model(self):
        from signallab_pc.workbench import calculation_buttons
        p=self.panel('analysis');p.set_model(StateModel([[-1]],[[1]],[[2]],[[0]]));p.calculate();self.assertEqual(self.errors,[]);self.assertEqual(p.diagnostics.model.values.shape,(1,1));q=p.coordinate_study;q.field.setText('2');q.initial.setText('4');q.calculate();self.assertEqual(self.errors,[]);assert_allclose(q.result['numeric_initial'],[2]);self.assertTrue(q.actions.isEnabled());self.assertEqual(calculation_buttons(p),[p.calculate_button]);q.initial.setText('8');self.assertIn('modificados',q.state.text());assert_allclose(q.result['numeric_initial'],[2])
    def test_equilibrium_family_and_incompatibility_update_the_simulation_action(self):
        p=self.panel('analysis');p.set_model(StateModel([[0]],[[1]],[[1]],[[0]]));p.calculate();e=p.equilibrium_study;e.field.setText('0');e.calculate();self.assertEqual(self.errors,[]);self.assertEqual(e.result['kind'],'family');self.assertTrue(e.simulation.isEnabled());e.field.setText('1');e.calculate();self.assertEqual(e.result['kind'],'inconsistent');self.assertFalse(e.simulation.isEnabled());self.assertIn('Sin equilibrio',e.report.toPlainText())
    def test_simulation_views_select_typed_outputs_states_and_inputs(self):
        p=self.panel('simulation');p.set_model(StateModel([[.5]],[[1]],[[1]],[[0]],.1));p.initial.setText('2');source=p.inputs.field(0);source.mode.setCurrentIndex(1);source.samples.setText('1,0,0');source.origin.setText('-3');p.decompose.setChecked(True);p.calculate();self.assertEqual(self.errors,[]);v=p.simulation_results;self.assertEqual(v.component.count(),3)
        self.assertEqual(len(self.host.project.headers('signal')),10)
        v.family.setCurrentIndex(1);v.component.setCurrentIndex(2);signal=self.host.project.get(p.simulation_channel_id());assert_allclose(signal.values,[2,1,.5]);self.assertEqual(signal.origin,-3);self.assertEqual(signal.metadata['sample_rate_hz'],10)
        v.family.setCurrentIndex(2);signal=self.host.project.get(p.simulation_channel_id());assert_allclose(signal.values,[0,0,0]);p.result_tabs.setCurrentIndex(v.steps_index);self.assertEqual(v.steps.data['computed'],2);self.assertEqual(v.steps.data['component'],'Entrada cero');source.samples.setText('9,9');self.assertEqual(v.steps.data['computed'],2)
        v.steps.channel.setCurrentIndex(1);v.steps.position.setText('1');v.steps.show_step();v.steps.component.setCurrentIndex(0);v.steps.build();self.assertEqual(v.steps.data['index'],1);self.assertEqual(v.steps.data['family'],'state');self.assertEqual(v.steps.data['computed'],1)
    def test_large_step_uses_a_view_job_and_accepts_integer_expressions(self):
        from signallab_pc.state_steps_panel import StateStepsPanel
        p=StateStepsPanel(self.host);self.widgets.append(p);m=StateModel([[.5]],np.ones((1,513)),[[1]],np.zeros((1,513)),.1);sources=[Signal([0,0,0]) for _ in range(513)];run=response.simulate(m,prepare_inputs(m,sources),[2]);jobs=[]
        self.host._run_view_operation=lambda title,f,accept:(jobs.append(title),accept(f()));p.set_run(run);p.build();p.position.setText('1+1');p.show_step();self.assertEqual(p.data['index'],2);self.assertGreaterEqual(len(jobs),2)


if __name__=='__main__':unittest.main()
