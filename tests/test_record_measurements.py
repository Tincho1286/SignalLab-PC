"""Independent finite sums, polynomial integrals and real result-routing controls."""
import os,unittest,json
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from unittest.mock import patch
import numpy as np
from numpy.testing import assert_allclose
from PySide6.QtWidgets import QApplication
from signallab_pc.model import Signal
from signallab_pc import record_measurements as calc


class Numerical(unittest.TestCase):
    def test_discrete_energy_mean_ac_and_physical_clock_selection(self):
        x=Signal([9,1,2,3,9],-2,metadata={'sample_rate_hz':2,'time_start_s':7})
        d=calc.analyze(x,-1,1);assert_allclose(d['selected'].values,[1,2,3]);self.assertEqual(d['selected'].metadata['time_start_s'],7.5)
        self.assertAlmostEqual(d['measures']['energy']['value'],14);self.assertAlmostEqual(d['measures']['power']['value'],14/3);self.assertEqual(d['mean'],[2,0]);assert_allclose(d['ac'].values,[-1,0,1]);assert_allclose(d['cumulative'].values,[1/14,5/14,1]);self.assertAlmostEqual(d['distribution']['centroid'],4/7)
    def test_linear_ramp_uses_polynomial_energy_quantiles_and_moments(self):
        d=calc.analyze(Signal([0,1],0,1,'s','ramp','continuous'))
        self.assertAlmostEqual(d['measures']['energy']['value'],1/3);self.assertAlmostEqual(d['measures']['ac_power']['value'],1/12);self.assertEqual(d['mean'],[.5,0]);self.assertAlmostEqual(d['distribution']['centroid'],.75);self.assertAlmostEqual(d['distribution']['rms_width'],np.sqrt(3/80));assert_allclose(d['distribution']['central_interval'],[.05**(1/3),.95**(1/3)],atol=1e-14)
    def test_complex_continuous_mean_and_decomposition_with_reversed_axis(self):
        d=calc.analyze(Signal([1+2j,3-2j,1+2j],2,-1,'s','x','continuous'))
        self.assertEqual(d['interval'],[0,2]);self.assertEqual(d['mean'],[2,0]);m=d['measures'];self.assertAlmostEqual(m['power']['value'],m['dc_power']['value']+m['ac_power']['value']);assert_allclose(d['dc'].values+d['ac'].values,d['selected'].values)
    def test_extreme_scales_keep_rms_and_scientific_energy_without_nan(self):
        for value in (1e200,np.nextafter(0.,1.)):
            d=calc.analyze(Signal([value,value]));self.assertEqual(d['mean'],[value,0]);assert_allclose(d['ac'].values,[0,0]);self.assertIsNone(d['measures']['energy']['value']);self.assertGreater(d['measures']['rms']['value'],0);self.assertTrue(np.isfinite(d['cumulative'].values).all())
    def test_zero_energy_and_distribution_rejections_are_explicit(self):
        d=calc.analyze(Signal([0,0,0]));self.assertIsNone(d['cumulative']);self.assertIsNone(d['distribution']['centroid']);self.assertEqual(d['measures']['energy']['value'],0)
        with self.assertRaises(ValueError):calc.analyze(Signal([1,2]),fraction=0)
        with self.assertRaises(ValueError):calc.analyze(Signal([1,2]),low=-1)
        with self.assertRaises(ValueError):calc.analyze(Signal([0,1],0,1,'s','x','continuous'),.1,.9)
        with self.assertRaises(ValueError):calc.analyze(Signal([1,2],0,1,'k'))
    def test_discrete_crossings_are_sampled_and_contacts_merge_into_runs(self):
        rows=calc.crossings(Signal([-1,1,-1,0,0,1],-7),0,'real');self.assertEqual([r['start'] for r in rows],[-6,-5,-4]);self.assertEqual(rows[-1]['end'],-3);self.assertEqual(rows[-1]['kind'],'Tramo igual al nivel')
    def test_magnitude_finds_two_interior_crossings_and_zero_contact(self):
        x=Signal([-1,1],0,1,'s','x','continuous');rows=calc.crossings(x,.5);assert_allclose([r['start'] for r in rows],[.25,.75]);self.assertEqual([r['kind'] for r in rows],['Cruce descendente','Cruce ascendente']);touch=calc.crossings(x,0);self.assertEqual(touch[0]['start'],.5);self.assertEqual(touch[0]['kind'],'Contacto con el nivel')
        plateau=calc.crossings(Signal([.5,.5,.5],0,1,'s','x','continuous'),.5);self.assertEqual(len(plateau),1);self.assertEqual(plateau[0]['end'],2)
        mixed=Signal([-1e-200,1e-200,1e200],0,1,'s','mixed','continuous');rows=calc.crossings(mixed,0,'real');self.assertEqual(len(rows),1);self.assertEqual(rows[0]['start'],.5);self.assertEqual(rows[0]['kind'],'Cruce ascendente')
    def test_large_discrete_origin_keeps_selected_indices_and_quantile_samples(self):
        origin=2**53+7;d=calc.analyze(Signal([1,1,1],origin),origin,origin+2);self.assertEqual(d['interval'],[origin,origin+2]);self.assertEqual(d['distribution']['central_interval'],[origin,origin+2]);self.assertEqual(d['distribution']['centroid'],origin+1)
    def test_zoh_mean_energy_quantiles_and_jumps_preserve_the_retained_model(self):
        x=Signal([1,0,100],0,1,'s','held','continuous',metadata={'operation':'response_input','input_interpolation':'hold'})
        d=calc.analyze(x,level=.5,component='real');self.assertEqual(d['mean'],[.5,0]);self.assertAlmostEqual(d['measures']['energy']['value'],1);self.assertAlmostEqual(d['distribution']['centroid'],.5);assert_allclose(d['distribution']['central_interval'],[.05,.95]);self.assertTrue(d['events'][0]['kind'].startswith('Salto descendente'));self.assertEqual(d['events'][0]['start'],1);self.assertEqual(d['cumulative'].metadata.get('input_interpolation'),None)


class Interface(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        from test_workflow_contracts import Host
        from signallab_pc.record_measurements_panel import RecordMeasurePanel
        self.host=Host();self.errors=[];self.warning=patch('PySide6.QtWidgets.QMessageBox.warning',side_effect=lambda *a:self.errors.append(str(a[2])));self.warning.start();self.panel=RecordMeasurePanel(self.host)
    def tearDown(self):self.warning.stop();self.panel.close();self.panel.deleteLater();self.host.bar.close();self.app.processEvents()
    def test_results_register_all_signals_and_snapshot_survives_input_edit(self):
        p=self.panel;p.source.mode.setCurrentIndex(1);p.source.samples.setText('1,2,3');p.calculate();self.assertEqual(self.errors,[]);self.assertEqual(len(p.signals),4);self.assertEqual(len(p.ids),4)
        for key,signal in p.signals.items():assert_allclose(self.host.project.get(p.ids[key]).values,signal.values)
        p.choice.setCurrentIndex(p.choice.findData('ac'));assert_allclose(p.view.result.values,[-1,0,1]);p.source.samples.setText('9');self.assertIn('modificados',p.state.text());self.assertEqual(p.result['mean'],[2,0]);json.dumps(self.host.project.records(),allow_nan=False)
    def test_loaded_continuous_source_selects_domain_and_preserves_domain_limits(self):
        p=self.panel;p.low.setText('2');p.high.setText('5');p.continuous_source.set_source(Signal([0,1,0],0,1,'s','x','continuous'));self.assertEqual(p.domain.currentIndex(),1);self.assertEqual(p.low.text(),'');p.calculate();self.assertEqual(self.errors,[]);p.domain.setCurrentIndex(0);self.assertEqual(p.low.text(),'2');self.assertEqual(p.high.text(),'5')
    def test_single_global_calculation_action_and_null_result_refresh(self):
        from signallab_pc.workbench import calculation_buttons
        p=self.panel;self.assertEqual(calculation_buttons(p),[p.calculate_button]);p.source.mode.setCurrentIndex(1);p.source.samples.setText('1,2');p.calculate();p.choice.setCurrentIndex(p.choice.findData('cumulative'));p.source.samples.setText('0,0');p.calculate();self.assertEqual(self.errors,[]);self.assertEqual(len(p.signals),3);self.assertNotIn('cumulative',p.signals);self.assertIsNone(p.result['cumulative'])


if __name__=='__main__':unittest.main()
