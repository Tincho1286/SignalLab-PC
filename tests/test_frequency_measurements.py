"""Independent reference values and captured-result measurement workflows."""
import os,unittest,tempfile,json
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
from unittest.mock import patch
import numpy as np
from numpy.testing import assert_allclose
from PySide6.QtWidgets import QApplication,QWidget,QVBoxLayout,QPushButton
from signallab_pc.filters import Transfer
from signallab_pc.frequency_analysis import analyze_frequency
from signallab_pc.analytic_frequency import analyze_expression
from signallab_pc import frequency_measurements as measure


def analog(model=None,start=0,stop=10,points=31):return analyze_frequency(model or Transfer([1],[1,1],domain='analog'),np.linspace(start,stop,points))

def expression(formula,condition='True'):
    exact=dict(transfer=formula,factored=formula,scope='Definición',model_kind='frequency',evaluated=True,parameters=[])
    request=dict(domain='digital',source_calculation={'cas_answer':dict(frequency_condition=condition,frequency_units='rad/muestra')})
    return analyze_expression(exact,request,np.linspace(-np.pi,np.pi,65))[1]


class Numerical(unittest.TestCase):
    def test_points_evaluate_the_definition_between_plotted_frequencies(self):
        d=analog(points=3);rows,_=measure.readings(d,[.7]);r=rows[0]
        self.assertAlmostEqual(r['real'],1/1.49);self.assertAlmostEqual(r['imag'],-.7/1.49);self.assertAlmostEqual(r['phase'],-np.arctan(.7));self.assertAlmostEqual(r['delay'],1/1.49)
    def test_digital_advance_and_sos_are_preserved_without_double_application(self):
        system=Transfer.from_sos([[1,0,0,1,-.5,0],[1,1,0,1,0,0]]);system.advance=2;w=np.linspace(0,np.pi,25);d=analyze_frequency(system,w,advance=1)
        values=measure.evaluate(d,[.3]);expected=(1+np.exp(-.3j))/(1-.5*np.exp(-.3j))*np.exp(.9j)
        assert_allclose(values['response'],[expected]);assert_allclose(values['delay'],system.group_delay(np.array([.3]))-1)
        self.assertEqual(measure.analyze(d,'points',frequencies=[.3])['extra_advance'],1)
    def test_expression_conditions_zeros_and_removable_values_are_not_replaced(self):
        d=expression('Piecewise((sin(w)/w, Ne(w,0)), (1, True))','w < pi/2');rows,_=measure.readings(d,[0,np.pi,1])
        self.assertEqual(rows[0]['magnitude'],1);self.assertIsNone(rows[1]['real']);self.assertAlmostEqual(rows[2]['magnitude'],np.sin(1))
        zero=measure.readings(expression('0'),[0])[0][0];self.assertEqual(zero['magnitude'],0);self.assertEqual(zero['db'],-np.inf);self.assertIsNone(zero['phase']);self.assertIsNone(zero['delay'])
    def test_half_power_finds_both_negative_and_positive_cutoffs(self):
        d=analog(start=-5,stop=5);r=measure.level_crossings(d,reference=0,count=51)
        assert_allclose([v['frequency'] for v in r['rows']],[-1,1],atol=2e-13);self.assertEqual(len(r['above']),1);self.assertAlmostEqual(r['above'][0]['width'],2);self.assertFalse(r['above'][0]['window_limited'])
    def test_bandpass_level_width_agrees_with_its_quadratic_equations(self):
        d=analog(Transfer([1,0],[1,1,1],domain='analog'),stop=4);r=measure.level_crossings(d,reference=1,count=65)
        expected=[(np.sqrt(5)-1)/2,(np.sqrt(5)+1)/2];assert_allclose([v['frequency'] for v in r['rows']],expected,atol=3e-13);self.assertAlmostEqual(r['above'][0]['width'],1)
    def test_tangent_flat_and_ideal_jump_do_not_invent_bandwidths(self):
        d=analog(Transfer([1,0],[1,1,1],domain='analog'),stop=3);touch=measure.level_crossings(d,relative=False,level=1,count=61)
        self.assertEqual(len(touch['rows']),1);self.assertAlmostEqual(touch['rows'][0]['frequency'],1);self.assertEqual(touch['above'],[])
        flat=measure.level_crossings(analog(Transfer([1],[1],domain='analog')),relative=False,level=1,count=31);self.assertTrue(flat['nonisolated']);self.assertEqual(flat['rows'],[]);self.assertFalse(flat['partition_complete'])
        jump=measure.level_crossings(expression('Piecewise((1, Abs(w)<1), (0, True))'),relative=False,level=.5,count=33);self.assertEqual(jump['rows'],[]);self.assertGreater(jump['rejected'],0);self.assertFalse(jump['partition_complete'])
    def test_band_extrema_limits_and_failed_ranges_keep_their_meaning(self):
        r=measure.analyze(analog(),'bands',bands=[('Paso',0,.2,.95,1.01),('Rechazo',5,10,0,.1)],count=31);a,b=r['rows']
        self.assertAlmostEqual(a['minimum'],1/np.sqrt(1.04));self.assertAlmostEqual(a['maximum'],1);self.assertGreater(a['margin'],0);self.assertLess(b['margin'],0);self.assertEqual(b['status'],'Fuera de los límites')
        with self.assertRaises(ValueError):measure.band_measures(analog(),[('Fuera',0,11,0,1)])
        with self.assertRaises(ValueError):measure.band_measures(analog(),[('Invertida',0,1,2,1)])
    def test_pole_neighbourhoods_detect_a_resonance_between_coarse_points(self):
        d=analog(Transfer([1],[1,2e-8,1],domain='analog'),stop=3,points=12);r=measure.analyze(d,'bands',bands=[('Resonancia',.8,1.2,None,1000)],count=10)
        self.assertGreater(r['rows'][0]['maximum'],4.9e7);self.assertLess(r['rows'][0]['margin'],0)
    def test_delay_constant_fir_and_notch_exclusions_are_separate(self):
        d=analyze_frequency(Transfer([0,0,1],[1]),np.linspace(0,np.pi,33));r=measure.analyze(d,'delay',bands=[('Banda',None,None,None,None)],count=31);row=r['rows'][0]
        self.assertAlmostEqual(row['delay_min'],2);self.assertAlmostEqual(row['delay_max'],2);self.assertLess(row['delay_spread'],1e-12)
        d=analyze_frequency(Transfer([1,1],[1]),np.linspace(0,np.pi,33));r=measure.analyze(d,'delay',bands=[('Banda',None,None,None,None)],count=31);self.assertGreater(r['rows'][0]['delay_undefined'],0);self.assertEqual(r['rows'][0]['delay_median'],.5)


class Interface(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        from test_workflow_contracts import Host
        from signallab_pc.frequency_measurements_panel import FrequencyMeasurementsPanel
        self.host=Host();self.panel=FrequencyMeasurementsPanel(self.host);self.errors=[];self.warning=patch('PySide6.QtWidgets.QMessageBox.warning',side_effect=lambda *a:self.errors.append(str(a[2])));self.warning.start();self.panel.set_source(analog())
    def tearDown(self):self.warning.stop();self.panel.close();self.panel.deleteLater();self.host.bar.close();self.app.processEvents()
    def test_point_readings_publish_with_pi_and_preserve_the_analyzed_model(self):
        p=self.panel;p.points.setText('0, pi/4, 10^(-2)');p.calculate();self.assertEqual(self.errors,[]);self.assertEqual(len(p.result['rows']),3);self.assertGreater(len(self.host.project.headers()),0)
        old=p.result;p.points.setText('1');self.assertIs(p.result,old);self.assertIn('modificados',p.state.text());p.source.system.b[0]=2;self.assertAlmostEqual(old['rows'][0]['magnitude'],1)
        p.points.setText('i');p.calculate();self.assertTrue(self.errors);self.assertIs(p.result,old)
    def test_local_action_and_csv_keep_metadata_and_nonfinite_values(self):
        from signallab_pc.workbench import calculation_buttons
        from signallab_pc.frequency_measurements_panel import COLUMNS
        page=QWidget();layout=QVBoxLayout(page);main=QPushButton('Analizar');main.setObjectName('primary');layout.addWidget(main);layout.addWidget(self.panel);self.assertEqual(calculation_buttons(page),[main])
        p=self.panel;p.set_source(expression('0'));p.calculate();self.assertEqual(self.errors,[]);self.assertIsNone(p.result['rows'][0]['phase'])
        with tempfile.TemporaryDirectory() as folder:
            path=str(Path(folder)/'medidas.csv')
            with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName',return_value=(path,'')):p.save()
            text=Path(path).read_text(encoding='utf-8');metadata=json.loads(text.splitlines()[0][2:]);self.assertEqual(metadata['mode'],'points');self.assertIn('-inf',text);self.assertIn('frequency,real,imag',text)
        self.panel.setParent(None);page.close()
    def test_masks_refined_points_and_selection_are_visible_without_replacing_curve(self):
        p=self.panel;p.mode.setCurrentIndex(2)
        for col,text in enumerate(('Paso','0','.2','.95','1.01')):p.bands.table.item(0,col).setText(text)
        p.count.setText('31');p.calculate();self.assertEqual(self.errors,[]);self.assertEqual(p.model.rows[0]['name'],'Paso');self.assertTrue(p.figure.axes[0].patches)
        p.table.setCurrentIndex(p.model.index(0,0));self.assertTrue(any(getattr(line,'_signallab_reference',False) for line in p.figure.axes[0].lines));self.assertTrue(any(getattr(line,'_signallab_curve_definition',None) for line in p.figure.axes[0].lines));p.set_source(None);self.assertFalse(p.calculate_button.isEnabled());self.assertIsNone(p.result)


if __name__=='__main__':unittest.main()
