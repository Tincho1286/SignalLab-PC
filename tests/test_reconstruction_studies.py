"""Kernel identities, independent errors, clock preservation and complete exports."""
import os,json,tempfile,unittest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
from unittest.mock import patch
import numpy as np
from numpy.testing import assert_allclose
from PySide6.QtWidgets import QApplication
from signallab_pc.model import Signal
from signallab_pc import reconstruction_studies as calc


class Numerical(unittest.TestCase):
    def test_common_grid_and_errors_against_linear_reference(self):
        r=calc.analyze(Signal([0,1],-8),1,0,2,reference='t');self.assertEqual(r['interval'],[0,1]);self.assertEqual(r['count'],3)
        assert_allclose(r['signals']['zoh'].values,[0,0,1]);assert_allclose(r['signals']['linear'].values,[0,.5,1]);assert_allclose(r['signals']['sinc'].values,[0,2/np.pi,1]);self.assertEqual(r['errors']['linear']['metrics']['rms']['value'],0);self.assertIn('+∞',r['errors']['linear']['snr_text']);self.assertAlmostEqual(r['errors']['zoh']['metrics']['rms']['value'],.5/np.sqrt(3))
    def test_zero_extension_exposes_the_last_hold_triangle_and_sinc_tails(self):
        r=calc.analyze(Signal([1,2]),1,0,2,1,2);assert_allclose(r['signals']['zoh'].values,[0,0,1,1,2,2,0,0,0]);assert_allclose(r['signals']['linear'].values,[0,.5,1,1.5,2,1,0,0,0]);self.assertAlmostEqual(r['signals']['sinc'].values[1].real,2/(3*np.pi));self.assertEqual(r['interval'],[-1,3])
    def test_cardinal_kernels_and_large_original_indices(self):
        for key in calc.METHODS:
            assert_allclose(calc.weights(key,1,3),[0,1,0])
        r=calc.analyze(Signal([1,2,3],2**53+17),4,2,2);d=calc.inspect(r,2.125,'linear');self.assertEqual(d['rows'][0]['index'],2**53+17);self.assertEqual(d['value'],1.5);self.assertEqual(d['stored'],1.5);self.assertEqual(d['residual'],0)
    def test_recorded_clock_conflicts_require_explicit_reinterpretation(self):
        x=Signal([1,2],-2,metadata={'sample_rate_hz':4,'time_start_s':2})
        r=calc.analyze(x,None,None,2,1,0);self.assertEqual(r['interval'],[1.75,2.25]);self.assertEqual(r['source_rate'],4)
        with self.assertRaises(ValueError):calc.analyze(x,8,2)
        override=calc.analyze(x,8,3,2,override_clock=True);self.assertEqual(override['source_start'],3);self.assertEqual(override['source_rate'],8)
    def test_compensated_products_preserve_cancellation_and_subnormal_values(self):
        self.assertEqual(calc.weighted_sum(np.ones(3),np.array([1e308,1e-200,-1e308],complex)),1e-200)
        self.assertEqual(calc.weighted_sum(np.array([1.,1.,-1.]),np.full(3,1e308,complex)),1e308)
        tiny=np.nextafter(0.,1.);self.assertEqual(calc.weighted_sum(np.array([.5,.5]),np.full(2,tiny,complex)),tiny)
        r=calc.analyze(Signal([tiny,tiny]),1,0,2);assert_allclose(r['signals']['linear'].values,[tiny,tiny,tiny],rtol=0,atol=0)
    def test_bad_reference_keeps_models_and_null_cases_do_not_invent_snr(self):
        r=calc.analyze(Signal([0,1]),1,0,2,reference='1/(t-0.5)');self.assertEqual(len(r['signals']),3);self.assertIsNone(r['reference']);self.assertTrue(r['reference_notice'])
        zero=calc.analyze(Signal([0,0]),1,0,2,reference='0');self.assertIsNone(zero['errors']['zoh']['snr_db']);self.assertIn('No definido',zero['errors']['zoh']['snr_text'])
    def test_fft_path_matches_an_independent_finite_sinc_sum(self):
        values=np.zeros(100);values[50]=1;r=calc.analyze(Signal(values),1,0,256);self.assertIn('FFT',r['signals']['sinc'].metadata['algorithm']);t=49.5;d=calc.inspect(r,t,'sinc');self.assertAlmostEqual(d['value'].real,2/np.pi);self.assertAlmostEqual(d['stored'].real,2/np.pi,places=12)
    def test_instant_outside_window_uses_the_same_model_and_snapshot(self):
        x=Signal([1,2]);r=calc.analyze(x,1,0,2);x.values[:]=100;d=calc.inspect(r,-.5,'sinc');self.assertTrue(d['outside_window']);self.assertAlmostEqual(d['value'].real,2/(3*np.pi));self.assertEqual(d['rows'][0]['sample'],1)
        with self.assertRaises(ValueError):calc.analyze(x,1,0,0)
        with self.assertRaises(ValueError):calc.analyze(x,1,0,2,-1,0)


class Interface(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        from test_workflow_contracts import Host
        from signallab_pc.reconstruction_panel import ReconstructionPanel
        self.host=Host();self.errors=[];self.warning=patch('PySide6.QtWidgets.QMessageBox.warning',side_effect=lambda *a:self.errors.append(str(a[2])));self.warning.start();self.panel=ReconstructionPanel(self.host)
    def tearDown(self):self.warning.stop();self.panel.close();self.panel.deleteLater();self.host.bar.close();self.app.processEvents()
    def calculate(self):
        p=self.panel;p.source.mode.setCurrentIndex(1);p.source.samples.setText('0,1');p.rate.setText('1');p.start.setText('0');p.factor.setText('2');p.use_reference.setChecked(True);p.reference.setText('t');p.calculate();self.assertEqual(self.errors,[]);return p
    def test_all_outputs_and_inspector_keep_provenance_and_old_input_snapshot(self):
        p=self.calculate();self.assertEqual(len(p.ids),7);p.method.setCurrentIndex(1);p.time.setText('.5');p.inspect();self.assertEqual(self.errors,[]);self.assertEqual(p.inspection['value'],.5);self.assertEqual(len(p.parts.rows),2)
        p.source.samples.setText('7,8');p.inspect();self.assertEqual(p.inspection['value'],.5);self.assertIn('modificados',p.state.text());json.dumps(self.host.project.records(),allow_nan=False)
    def test_only_one_global_action_and_method_selection_stays_in_sync(self):
        from signallab_pc.workbench import calculation_buttons
        p=self.calculate();self.assertEqual(calculation_buttons(p),[p.calculate_button]);index=next(i for i in range(p.choice.count()) if p.choice.itemData(i)==('models','linear'));p.choice.setCurrentIndex(index);self.assertEqual(p.method.currentData(),'linear');p.method.setCurrentIndex(2);self.assertEqual(p.choice.currentData(),('models','sinc'))
    def test_export_of_a_four_curve_comparison_preserves_every_signal(self):
        p=self.calculate()
        with tempfile.TemporaryDirectory() as folder:
            path=str(Path(folder)/'curvas.csv')
            with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName',return_value=(path,'Tabla CSV (*.csv)')):p.view.export()
            self.assertEqual(self.errors,[]);self.assertEqual(sorted(f.name for f in Path(folder).glob('*.csv')),['curvas_1.csv','curvas_2.csv','curvas_3.csv','curvas_4.csv'])
    def test_new_primary_calculation_clears_previous_inspector(self):
        p=self.calculate();p.inspect();self.assertIsNotNone(p.inspection);p.source.samples.setText('1,1');p.calculate();self.assertEqual(self.errors,[]);self.assertIsNone(p.inspection);self.assertEqual(p.parts.rows,[])


if __name__=='__main__':unittest.main()
