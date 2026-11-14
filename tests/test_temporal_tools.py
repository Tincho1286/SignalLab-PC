"""Independent responses, observed step measures and result-local UI controls."""
import os,unittest,json,tempfile
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
from unittest.mock import patch
import numpy as np
from numpy.testing import assert_allclose
from PySide6.QtWidgets import QApplication
from signallab_pc.filters import Transfer
from signallab_pc.model import Signal
from signallab_pc import temporal_analysis as ta,response_steps as steps


class Arithmetic(unittest.TestCase):
    def test_complex_fir_tail_and_clock_use_the_full_linear_convolution(self):
        source=Signal([1,2],-4,expression='n+5',metadata={'sample_rate_hz':50,'time_start_s':17.})
        system=Transfer([1+1j,2,-1j],[1],sample_period_s=.02);snapshot=ta.simulate(system,source,extra=2);output=snapshot['outputs'][0]
        assert_allclose(output.values,np.convolve([1,2],[1+1j,2,-1j]));assert_allclose(source.values,[1,2])
        self.assertEqual(output.origin,-4);self.assertEqual(output.metadata['time_start_s'],17);self.assertEqual(snapshot['input'].metadata['sample_rate_hz'],50);self.assertEqual(snapshot['input'].expression,'');self.assertEqual(snapshot['original_input'].expression,'n+5')
    def test_continuous_tail_respects_linear_and_held_transition_to_zero(self):
        system=Transfer([1],[1,1],domain='analog');source=Signal([1,1],5,1,'s','x','continuous',expression='1')
        for mode,expected in [('linear',[0,1-np.exp(-1),1-np.exp(-1)-np.exp(-2),np.exp(-1)*(1-np.exp(-1)-np.exp(-2))]),('hold',[0,1-np.exp(-1),1-np.exp(-2),np.exp(-1)*(1-np.exp(-2))])]:
            snapshot=ta.simulate(system,source,extra=2,interpolation=mode);assert_allclose(snapshot['outputs'][0].values,expected,atol=3e-15)
            self.assertEqual(snapshot['input'].metadata['input_interpolation'],mode);self.assertEqual(snapshot['input'].expression,'');self.assertEqual(snapshot['original_input'].expression,'1')
    def test_continuous_off_grid_impulse_keeps_its_weight_and_decay(self):
        system=Transfer([1,2],[1,1],domain='analog');source=Signal([0,0],5,1,'s','x','continuous',metadata={'dirac_terms':[[5.5,[2.,0.]]]})
        output=ta.simulate(system,source,extra=2)['outputs'][0];assert_allclose(output.values,[0,2*np.exp(-.5),2*np.exp(-1.5),2*np.exp(-2.5)],atol=1e-14)
        self.assertEqual(output.metadata['dirac_terms'],[[5.5,[2.,0.]]])
    def test_history_decomposition_and_inspector_use_the_saved_recurrence(self):
        snapshot=ta.simulate(Transfer([1,.25],[2,-1]),Signal([1,0,-1],10),extra=3,separate=True,previous_inputs=[2],previous_outputs=[4]);total,forced,natural=snapshot['outputs'];assert_allclose(total.values,[2.75,1.5,.25,0,0,0]);assert_allclose(total.values,forced.values+natural.values)
        trace=steps.capture(snapshot);saved=steps.inspect(trace,10);self.assertEqual(saved['reconstructed'],2.75);self.assertEqual(saved['rows'][1]['source'],'Historial inicial');snapshot['input'].values[:]=0;snapshot['outputs'][0].values[:]=0;self.assertEqual(steps.inspect(trace,10)['computed'],2.75)
    def test_sos_inspector_retains_each_section_and_the_authoritative_output(self):
        system=Transfer.from_sos([[1,0,0,1,-.5,0],[1,1,0,1,0,0]]);source=Signal([1+2j,0,0,0,0]);snapshot=ta.simulate(system,source);expected=(1+2j)*np.array([1,1.5,.75,.375,.1875]);assert_allclose(snapshot['outputs'][0].values,expected)
        trace=steps.capture(snapshot);self.assertEqual(len(trace['frames']),2)
        for index in range(5):
            data=steps.inspect(trace,index,1);self.assertEqual(data['computed'],expected[index]);self.assertEqual(data['residual'],0)
    def test_inspector_does_not_silently_zero_unrepresentable_contributions(self):
        tiny=np.nextafter(0.,1.);trace=dict(origin=0,count=3,frames=[dict(name='FIR',b=np.full(3,1e-162),a=np.array([1]),x=np.full(3,1e-162),y=np.array([0,0,tiny]),previous_inputs=[],previous_outputs=[])])
        data=steps.inspect(trace,2);self.assertEqual(data['unrepresentable'],3);self.assertEqual(data['reconstructed'],tiny);self.assertTrue(all(row['contribution'] is None for row in data['rows']));self.assertIsNone(data['residual'])
    def test_step_measures_use_model_dc_not_the_last_sample_and_handle_negative_gain(self):
        t=np.linspace(0,6,601)
        for gain in (1.,-2.):
            output=Signal(gain*(1-np.exp(-t)),0,.01,'s','y','continuous');metrics=ta.step_metrics(Transfer([gain],[1,1],domain='analog'),output)
            self.assertEqual(metrics['final_value'],gain);self.assertNotEqual(metrics['last_value'],gain);self.assertAlmostEqual(metrics['rise_time'],np.log(9),places=4);self.assertAlmostEqual(metrics['settling_from_start'],np.log(50),places=4);self.assertEqual(metrics['overshoot_percent'],0)
        short=ta.step_metrics(Transfer([1],[1,1],domain='analog'),Signal(1-np.exp(-t[:51]),0,.01,'s','y','continuous'))
        self.assertIsNone(short['rise_time']);self.assertIsNone(short['settling_coordinate']);self.assertEqual(short['final_value'],1)
    def test_oscillatory_step_overshoot_matches_its_closed_expression(self):
        zeta=.2;wd=np.sqrt(1-zeta*zeta);t=np.linspace(0,30,6001);y=1-np.exp(-zeta*t)*(np.cos(wd*t)+zeta/wd*np.sin(wd*t));m=ta.step_metrics(Transfer([1],[1,2*zeta,1],domain='analog'),Signal(y,0,.005,'s','y','continuous'))
        self.assertAlmostEqual(m['overshoot_percent'],100*np.exp(-zeta*np.pi/wd),places=3);self.assertLess(abs(m['peak_coordinate']-np.pi/wd),.005);self.assertIsNotNone(m['settling_coordinate'])
    def test_discrete_crossings_keep_large_integer_coordinates_and_physical_units(self):
        origin=2**60;output=Signal(1-.5**(np.arange(10)+1),origin,metadata={'sample_rate_hz':8});m=ta.step_metrics(Transfer([.5],[1,-.5]),output,12.5)
        self.assertEqual(m['crossing_10'],origin);self.assertEqual(m['crossing_90'],origin+3);self.assertEqual(m['rise_time'],3);self.assertEqual(m['settling_coordinate'],origin+2);self.assertEqual(m['physical_seconds']['rise_time'],3/8)
    def test_undefined_percentages_are_explained_and_subnormal_thresholds_survive(self):
        t=np.linspace(0,2,21)
        unstable=ta.step_metrics(Transfer([1],[1,-1],domain='analog'),Signal(np.exp(t)-1,0,.1,'s','y','continuous'));self.assertFalse(unstable['available'])
        boundary=ta.step_metrics(Transfer([1],[1,-np.nextafter(1.,0.)]),Signal([1,2]));self.assertFalse(boundary['available']);self.assertIn('frontera',boundary['notes'][-1])
        highpass=ta.step_metrics(Transfer([-1,0],[1,1],domain='analog'),Signal(-np.exp(-t),0,.1,'s','y','continuous'));self.assertEqual(highpass['final_value'],0);self.assertEqual(highpass['peak_value'],-1);self.assertNotIn('rise_time',highpass)
        tiny=np.nextafter(0.,1.);m=ta.step_metrics(Transfer([tiny],[1]),Signal([tiny,tiny]),1e-320);self.assertEqual(m['final_value'],tiny);self.assertEqual(m['settling_from_start'],0);self.assertEqual(m['overshoot_percent'],0)
    def test_suggestions_are_modal_cancel_exact_factors_and_limit_growth_window(self):
        stable=ta.suggest_window(Transfer([1],[1,1],domain='analog'));self.assertAlmostEqual(stable['duration'],np.log(1000));self.assertGreaterEqual(stable['count'],501)
        static=ta.suggest_window(Transfer([1,-1],[1,-1],domain='analog'));self.assertTrue(static['stable']);self.assertEqual(static['duration'],1)
        growing=ta.suggest_window(Transfer([1],[1,-99.999,-.1],domain='analog'));self.assertFalse(growing['stable']);self.assertLess(growing['duration'],.1)
        self.assertEqual(ta.suggest_window(Transfer([1],[1,-1e100]))['count'],1)
        canceled=Transfer([1,-.9],[1,-.9]);self.assertGreater(ta.suggest_window(canceled,include_memory=True)['count'],ta.suggest_window(canceled)['count'])


class Interface(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        from test_workflow_contracts import Host
        from signallab_pc.temporal_panel import TemporalPanel
        self.host=Host();self.panel=TemporalPanel(self.host);self.errors=[];self.warning=patch('PySide6.QtWidgets.QMessageBox.warning',side_effect=lambda *a:self.errors.append(str(a[2])));self.warning.start()
    def tearDown(self):self.warning.stop();self.panel.close();self.panel.deleteLater();self.host.bar.close();self.app.processEvents()
    def test_unit_response_comparison_and_measures_are_published_with_real_ids(self):
        panel=self.panel;panel.set_system(Transfer([2],[1]));panel.count.setText('1');panel.calculate();self.assertEqual(self.errors,[]);assert_allclose(panel.output.result.values,[2]);self.assertEqual(len(panel.comparison.result),2);self.assertEqual(len(panel.comparison.result_ids),2)
        for key in panel.comparison.result_ids:self.assertIsInstance(self.host.project.get(key),Signal)
        self.assertIn('y_final = 2.0',panel.measure_report.toPlainText());self.assertTrue(any(row['operation']=='Medidas del escalón' for row in self.host.project.headers()))
        panel.result_tabs.setCurrentIndex(panel.steps_index);self.assertIsNotNone(panel.steps.data);self.assertEqual(panel.steps.data['computed'],2)
    def test_custom_hold_comparison_draws_the_used_input_as_steps(self):
        panel=self.panel;panel.set_system(Transfer([1],[1,1],domain='analog'));panel.stimulus.setCurrentIndex(2);panel.continuous_input.mode.setCurrentIndex(1);panel.continuous_input.samples.setText('1,1');panel.continuous_input.origin.setText('5');panel.continuous_input.step.setText('1');panel.extra_count.setText('2');panel.interpolation.setCurrentIndex(1);panel.calculate();self.assertEqual(self.errors,[])
        assert_allclose(panel.output.result.values,[0,1-np.exp(-1),1-np.exp(-2),np.exp(-1)*(1-np.exp(-2))]);lines=panel.comparison.figure.axes[0].lines;self.assertEqual(lines[0].get_drawstyle(),'default');self.assertTrue(any(line.get_drawstyle()=='steps-post' for line in lines));self.assertEqual(len(panel.input_view.result.values),4)
    def test_invalid_optional_band_does_not_erase_the_computed_response(self):
        panel=self.panel;panel.set_system(Transfer([2],[1]));panel.count.setText('1');panel.settling_percent.setText('no_es_numero');panel.calculate();self.assertEqual(self.errors,[]);assert_allclose(panel.output.result.values,[2]);self.assertIn('Las muestras se conservan',panel.measure_report.toPlainText())
    def test_steps_are_local_and_keep_their_snapshot_after_input_edits(self):
        from signallab_pc.workbench import calculation_buttons
        panel=self.panel;panel.set_system(Transfer([1],[1,-.5]));panel.stimulus.setCurrentIndex(2);panel.discrete_input.mode.setCurrentIndex(1);panel.discrete_input.samples.setText('1,0,0');panel.extra_count.setText('2');panel.calculate();panel.steps.build();self.assertEqual(self.errors,[]);self.assertIsNotNone(panel.steps.data)
        panel.discrete_input.samples.setText('9,9,9');panel.steps.index.setText('2');panel.steps.show_step();self.assertEqual(panel.steps.data['computed'],.25);self.assertNotIn(panel.steps.prepare,calculation_buttons(panel))
        with tempfile.TemporaryDirectory() as folder:
            path=str(Path(folder)/'aportes.csv')
            with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName',return_value=(path,'CSV')):panel.steps.save()
            self.assertIn('"index": 2',Path(path).read_text(encoding='utf-8'))
    def test_suggested_fields_do_not_calculate_and_stale_suggestions_cannot_overwrite(self):
        panel=self.panel;panel.set_system(Transfer([1],[1,1],domain='analog'));panel.suggest_interval();self.assertEqual(self.errors,[]);self.assertIsNone(panel.output.result);self.assertAlmostEqual(float(panel.duration.text()),np.log(1000))
        pending=[]
        with patch.object(self.host,'_run_operation',side_effect=lambda title,job,accept:pending.append((job,accept))):panel.suggest_interval()
        before=panel.count.text();panel.a.setText('1,2');job,accept=pending[0];accept(job());self.assertEqual(panel.count.text(),before);self.assertIn('definición cambió',panel.suggestion_note.text())
    def test_long_inspector_uses_view_jobs_without_recalculating_the_response(self):
        panel=self.panel;panel.set_system(Transfer(np.r_[1,np.zeros(511),.25],[1]));panel.stimulus.setCurrentIndex(1);panel.count.setText('4');panel.calculate();original=panel.output.result.values.copy();jobs=[]
        def run(title,job,accept):jobs.append(title);accept(job())
        with patch.object(self.host,'_run_view_operation',side_effect=run,create=True):panel.steps.build()
        self.assertEqual(len(jobs),2);self.assertEqual(len(panel.steps.data['rows']),513);self.assertEqual(panel.steps.data['computed'],1);assert_allclose(panel.output.result.values,original);self.assertEqual(self.errors,[])


if __name__=='__main__':unittest.main()
