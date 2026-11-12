"""Scientific examples and real controls for the interactive analysis additions."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import csv,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from numpy.testing import assert_allclose
from signallab_pc.roc_regions import regions
from signallab_pc.recurrence_inspector import inspect_step
from signallab_pc.difference_equations import solve
from signallab_pc.fir_comparison import compare,export_csv


class InteractiveMath(unittest.TestCase):
    def test_recurrence_nonzero_start_and_original_initial_condition(self):
        result=solve(dict(coefficients=['2','-1'],expression='1',start=10,count=3,rest=False,initial=['3']))
        assert_allclose(np.asarray(result['numeric_samples'])[:,0],[2,1.5,1.25])
        first=inspect_step(result,10);self.assertEqual(first['forcing'],.5)
        self.assertEqual(first['contributions'][0]['index'],9);self.assertEqual(first['contributions'][0]['value'],3)
        self.assertEqual(first['contributions'][0]['source'],'Condición inicial');self.assertEqual(first['reconstructed'],2)
        self.assertEqual(inspect_step(result,11)['contributions'][0]['source'],'Calculada')
        with self.assertRaises(ValueError):inspect_step(result,9)

    def test_recurrence_complex_and_memoryless(self):
        result=solve(dict(coefficients=['1','-i/2'],expression='0',start=-1,count=3,rest=False,initial=['1+i']))
        expected=[-.5+.5j,-.25-.25j,.125-.125j]
        for n,y in zip(range(-1,2),expected):self.assertAlmostEqual(inspect_step(result,n)['computed'],y)
        simple=solve(dict(coefficients=['2','0'],expression='n',start=-2,count=2,rest=True,initial=[]))
        self.assertEqual(inspect_step(simple,-2)['computed'],-1);self.assertEqual(inspect_step(simple,-2)['contributions'],[])

    def test_roc_selection_recovers_a_known_bilateral_sequence(self):
        expression='z/((z-1/2)*(z-2))';data=regions(dict(kind='z',expression=expression))
        self.assertEqual([v['mode'] for v in data['regions']],['left','radius','right'])
        from signallab_pc.symbolic import execute
        choice=data['regions'][1]
        result=execute(dict(operation='z_inverse_expression',expression=expression,roc=choice['mode'],radius=choice['value'],include_samples=True,start=-2,count=5))
        assert_allclose(np.asarray(result['numeric_samples'])[:,0],[-1/6,-1/3,-2/3,-1/3,-1/6],rtol=1e-12)
        json.dumps(data,allow_nan=False)

    def test_laplace_global_delay_and_equivalent_factoring(self):
        a=regions(dict(kind='laplace',expression='exp(-2*s)/((s+1)*(s-2))'))
        b=regions(dict(kind='laplace',expression='1/((s+1)*(s-2)*exp(2*s))'))
        self.assertEqual(a['boundaries'],b['boundaries']);self.assertEqual(len(a['regions']),3)
        self.assertEqual(a['regions'][1]['mode'],'line');self.assertEqual(float(a['regions'][1]['value']),.5)
        json.dumps(a,allow_nan=False)

    def test_cancelled_poles_origin_and_close_boundaries(self):
        result=regions(dict(kind='z',expression='(z-1/2)/((z-1/2)*(z-2))'))
        self.assertEqual(len(result['poles']),1);self.assertEqual(len(result['regions']),2)
        repeated=regions(dict(kind='z',expression='1/(z-1/2)^5'));self.assertEqual(len(repeated['poles']),1);self.assertEqual(len(repeated['regions']),2)
        origin=regions(dict(kind='z',expression='1/z'));self.assertEqual(origin['poles'],[[0.,0.]])
        constant=regions(dict(kind='z',expression='z/z'))
        from signallab_pc.roc_picker import region_at
        self.assertEqual(region_at(constant,0),0)
        near=regions(dict(kind='z',expression='1/((z-1)*(z-1-10^(-20)))'))
        self.assertEqual(len(near['regions']),3);self.assertFalse(near['plot_available'])

    def test_roc_does_not_invent_regions_for_general_functions(self):
        with self.assertRaisesRegex(ValueError,'racional'):regions(dict(kind='z',expression='log(z)'))
        with self.assertRaisesRegex(ValueError,'parámetros'):regions(dict(kind='z',expression='1/(z-a)'))

    def test_equal_length_matches_the_window_definition_and_type_ii(self):
        result=compare([.2*np.pi],[.6*np.pi],.2,.15,['hann','hamming'],mode='length',length=12)
        n=np.arange(12)-5.5;ideal=.4*np.sinc(.4*n)
        for system,window,row in zip(result['systems'],[np.hanning(12),np.hamming(12)],result['fir_comparison']['rows']):
            assert_allclose(system.b,ideal*window,atol=1e-15)
            self.assertEqual(row['length'],12);self.assertEqual(row['fir_type'],'II');self.assertEqual(row['delay'],5.5)
        self.assertEqual(len(result['systems']),2)

    def test_explicit_one_tap_is_preserved_in_both_design_paths(self):
        from signallab_pc.amplitude_design import design
        single=design([.2],[.8],.1,.1,'kaiser',taps=1)
        batch=compare([.2],[.8],.1,.1,['kaiser'],mode='length',length=1)
        self.assertEqual(len(single['systems'][0].b),1)
        assert_allclose(single['systems'][0].b,batch['systems'][0].b)

    def test_equal_tolerances_returns_compliant_windows(self):
        result=compare([.2*np.pi],[.65*np.pi],.2,.15,['kaiser','hann'],mode='tolerances')
        for system,row in zip(result['systems'],result['fir_comparison']['rows']):
            self.assertTrue(row['met']);self.assertIsNotNone(row['metrics'])
            w=np.linspace(0,np.pi,16001);h=abs(system.response(w))
            self.assertGreaterEqual(h[w<=.2*np.pi].min(),.8-1e-10)
            self.assertLessEqual(h[w<=.2*np.pi].max(),1.2+1e-10)
            self.assertLessEqual(h[w>=.65*np.pi].max(),.15+1e-10)

    def test_partial_failure_csv_and_forbidden_nyquist_parity(self):
        from signallab_pc.amplitude_design import design
        def candidate(*args,**kwargs):
            if kwargs['window']=='blackman':raise ValueError('Presupuesto agotado para esta ventana')
            return design(*args,**kwargs)
        with patch('signallab_pc.amplitude_design.design',side_effect=candidate):
            result=compare([.2*np.pi],[.6*np.pi],.2,.15,['hann','blackman'],mode='length',length=12)
        self.assertEqual(len(result['systems']),1);self.assertIsNone(result['fir_comparison']['rows'][1]['system_index'])
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'table.csv';export_csv(result['fir_comparison'],path)
            with path.open(encoding='utf-8-sig',newline='') as source:rows=list(csv.reader(source,delimiter=';'))
            self.assertEqual(len(rows),3);self.assertIn('Presupuesto agotado',rows[2][-1])
        with self.assertRaisesRegex(ValueError,'impar'):compare([.7*np.pi],[.4*np.pi],.2,.15,['hann'],mode='length',length=12)


class InteractiveUi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        from test_workflow_contracts import Host
        self.host=Host();self.widgets=[];self.warnings=[]
        self.warning=patch('PySide6.QtWidgets.QMessageBox.warning',side_effect=lambda *args:self.warnings.append(str(args[2])));self.warning.start()

    def tearDown(self):
        self.warning.stop()
        for widget in self.widgets:widget.close();widget.deleteLater()
        self.host.bar.close();self.host.bar.deleteLater();self.app.processEvents()

    def test_filter_table_selects_the_reused_system_and_clears_on_single_design(self):
        from signallab_pc.course_tools_panel import CourseToolsPanel
        panel=CourseToolsPanel(self.host,'fir');self.widgets.append(panel)
        panel.fields['comparison_mode'].setCurrentIndex(2);panel.fields['common_length'].setText('12')
        panel.band_edges.edits[0].setText('.2*pi');panel.band_edges.edits[1].setText('.6*pi')
        panel.fields['dp'].setText('.2');panel.fields['ds'].setText('.15');panel.fields['compare_kaiser'].setChecked(False)
        panel.calculate();self.assertEqual(self.warnings,[]);self.assertEqual(len(panel.items),2)
        panel.fir_comparison_view.table.setCurrentCell(1,0)
        self.assertEqual(panel.selector.currentIndex(),1)
        self.assertEqual(self.host.project.get(panel.records[1]).name,panel.items[1].name)
        panel.fields['comparison_mode'].setCurrentIndex(0);panel.fields['taps'].setText('12');panel.calculate()
        self.assertEqual(self.warnings,[]);self.assertIsNone(panel.fir_comparison_view.data)

    def test_roc_application_and_stale_definition_guard(self):
        from signallab_pc.transform_lab import TransformLab
        from signallab_pc.roc_picker import RocPicker
        panel=TransformLab(self.host,'laplace');self.widgets.append(panel);panel.mode.setCurrentIndex(1)
        panel.expression.setText('1/((s+1)*(s-2))');data=regions(dict(kind='laplace',expression=panel.expression.text()))
        picker=RocPicker(panel,data)
        from signallab_pc.plot_view import install_enlarge
        install_enlarge(picker.toolbar);self.assertIs(picker.canvas.parentWidget(),picker)
        picker.choice.setCurrentIndex(1);picker.apply(False)
        self.assertEqual(panel.interpretation.currentIndex(),1);self.assertEqual(panel.laplace_roc.currentIndex(),2)
        self.assertEqual(float(panel.sigma.text()),.5)
        picker=RocPicker(panel,data);picker.choice.setCurrentIndex(1);panel.expression.setText('1/(s+4)');picker.apply(False)
        self.assertIn('cambió',picker.status.text());picker.close()

    def test_real_inverse_button_process_and_selected_bilateral_result(self):
        from signallab_pc.transform_lab import TransformLab
        panel=TransformLab(self.host,'z');self.widgets.append(panel);panel.mode.setCurrentIndex(1)
        panel.expression.setText('z/((z-1/2)*(z-2))');panel.start.setText('-2');panel.count.setText('5')
        panel.roc_button.click();self.assertEqual(self.warnings,[])
        self.assertIsNotNone(panel.roc_picker);panel.roc_picker.choice.setCurrentIndex(1);panel.roc_picker.apply(True)
        self.assertEqual(self.warnings,[]);self.assertIsNotNone(panel.last)
        assert_allclose(np.asarray(panel.last['numeric_samples'])[:,0],[-1/6,-1/3,-2/3,-1/3,-1/6],rtol=1e-12)

    def test_inspector_navigation_uses_last_computed_snapshot(self):
        from signallab_pc.difference_panel import DifferencePanel
        result=solve(dict(coefficients=['2','-1'],expression='1',start=10,count=3,rest=False,initial=['3']))
        panel=DifferencePanel(self.host);self.widgets.append(panel);panel.inspector.set_result(result)
        panel.expression.setText('100');panel.inspector.next.click()
        self.assertEqual(panel.inspector.index.text(),'11');self.assertIn('1.5',panel.inspector.report.toPlainText())
        self.assertIn('y[10]',panel.inspector.report.toPlainText())


if __name__=='__main__':unittest.main()
