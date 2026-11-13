"""Independent definitions and real controls for the 1.8.1 analysis additions."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import unittest
from unittest.mock import patch
import numpy as np
from numpy.testing import assert_allclose
from scipy.signal import freqz
from signallab_pc.model import Signal
from signallab_pc.operations import linear_convolution
from signallab_pc.convolution_steps import capture,inspect
from signallab_pc.window_signals import generate_window
from signallab_pc.window_spectrum import analyze


class AnalysisMath(unittest.TestCase):
    def test_complex_convolution_products_preserve_indices_and_snapshot(self):
        x=Signal([1+2j,3-1j,-2],-4);h=Signal([2-1j,1j],7)
        y=linear_convolution(x,h);trace=capture(x,h,y)
        expected=np.convolve(x.values,h.values)
        for i,value in enumerate(expected):
            data=inspect(trace,3+i)
            self.assertAlmostEqual(data['reconstructed'],value)
            self.assertAlmostEqual(data['computed'],value)
            for row in data['rows']:
                self.assertEqual(row['h_index'],data['index']-row['k'])
                self.assertEqual(row['product'],row['x']*row['h'])
        x.values[:]=0;h.values[:]=0;y.values[:]=0
        self.assertAlmostEqual(inspect(trace,4)['computed'],expected[1])

    def test_product_pages_cover_overlap_and_large_indices_remain_integer(self):
        x=Signal(np.arange(1,202),2**53+1);h=Signal(np.ones(201),-2**53)
        trace=capture(x,h,linear_convolution(x,h));data=inspect(trace,201,offset=100)
        self.assertEqual(data['total'],201);self.assertEqual(len(data['rows']),100)
        self.assertEqual(data['rows'][0]['k'],2**53+101);self.assertEqual(data['reconstructed'],20301)
        self.assertEqual(len(inspect(trace,201,offset=200)['rows']),1)
        with self.assertRaises(ValueError):inspect(trace,201,offset=201)
        with self.assertRaises(ValueError):inspect(trace,0)

    def test_rectangular_and_hann_gain_enbw_and_half_power(self):
        for kind in ('boxcar','hann'):
            source=generate_window(kind,33,origin=-16);data=analyze(source);m=data['metrics']
            expected_gain=1 if kind=='boxcar' else 16/33
            expected_bins=1 if kind=='boxcar' else 1.5*33/32
            self.assertAlmostEqual(m['coherent_gain'],expected_gain)
            self.assertAlmostEqual(m['enbw_bins'],expected_bins)
            self.assertAlmostEqual(m['enbw_radians'],expected_bins*2*np.pi/33)
            response=freqz(source.values,worN=[m['half_power_frequency']])[1][0]
            self.assertAlmostEqual(abs(response)/abs(np.sum(source.values)),1/np.sqrt(2),places=11)
            self.assertEqual(m['full_3db_width'],2*m['half_power_frequency'])
            shifted=analyze(generate_window(kind,33,origin=2**53+1))
            assert_allclose(shifted['magnitude'],data['magnitude'],atol=0,rtol=0)
            self.assertAlmostEqual(np.trapezoid(data['magnitude']**2,data['frequency'])/np.pi,m['enbw_bins']/33)

    def test_degenerate_windows_have_no_fabricated_bandwidth(self):
        one=analyze(generate_window('boxcar',1));self.assertIsNone(one['metrics']['half_power_frequency']);self.assertEqual(one['metrics']['enbw_bins'],1)
        zero=analyze(generate_window('hann',2));self.assertFalse(zero['metrics']['normalizable']);self.assertIsNone(zero['metrics']['enbw_bins']);self.assertTrue(np.all(zero['magnitude']==0))
        extreme=analyze(generate_window('kaiser',31,beta=1000));self.assertTrue(np.isfinite(extreme['magnitude']).all())


class AnalysisUi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        from test_workflow_contracts import Host
        self.host=Host();self.widgets=[];self.errors=[]
        self.warning=patch('PySide6.QtWidgets.QMessageBox.warning',side_effect=lambda *a:self.errors.append(str(a[2])));self.warning.start()

    def tearDown(self):
        self.warning.stop()
        for widget in [*self.widgets,self.host.bar]:widget.close();widget.deleteLater()
        self.app.processEvents()

    def test_convolution_actual_button_and_inspector_retain_original_inputs(self):
        from signallab_pc.toolbox import ToolPage
        page=ToolPage(self.host,('Convolución lineal','basic','convolve','pair'));self.widgets.append(page)
        page.first.mode.setCurrentIndex(1);page.first.samples.setText('1, 2');page.first.origin.setText('-1')
        page.second.samples.setText('3, 4');page.second.origin.setText('2')
        page.result_state.button.click()
        self.assertEqual(self.errors,[]);self.assertIsNotNone(page.convolution_inspector.trace)
        page.first.samples.setText('100, 200');page.convolution_inspector.next.click()
        self.assertEqual(page.convolution_inspector.data['computed'],10)
        self.assertTrue(page.basic_result.views.isTabVisible(page.convolution_step_index))
        self.assertTrue(page.convolution_inspector.canvas._signallab_explicit_plot)

    def test_window_actual_button_and_spectrum_scale_do_not_change_samples(self):
        from signallab_pc.window_signal_panel import WindowSignalPanel
        panel=WindowSignalPanel(self.host);self.widgets.append(panel);panel.kind.setCurrentIndex(panel.kind.findData('hann'));panel.length.setText('33')
        panel.calculate_button.click();self.assertEqual(self.errors,[])
        samples=panel.result.values.copy();self.assertIn('Ancho equivalente',panel.output.text.toPlainText())
        panel.spectrum_view.scale.setCurrentIndex(1);assert_allclose(panel.result.values,samples,atol=0,rtol=0)
        self.assertEqual(panel.spectrum_view.figure.axes[0].get_ylabel(),'Módulo relativo')
        self.assertTrue(panel.output.views.isTabVisible(panel.spectrum_index))
        metrics=[self.host.project.get(row['id']).get('window_metrics') for row in self.host.project.headers('calculation')]
        self.assertTrue(any(value and value['length']==33 for value in metrics))

    def test_spectrum_memory_limit_keeps_the_generated_window(self):
        from signallab_pc.window_signal_panel import WindowSignalPanel
        panel=WindowSignalPanel(self.host);self.widgets.append(panel)
        with patch('signallab_pc.window_spectrum.ensure_working_set',side_effect=MemoryError('Memoria insuficiente para la vista')):
            panel.calculate_button.click()
        self.assertEqual(self.errors,[]);self.assertIsNotNone(panel.result)
        self.assertIn('La ventana generada se conserva',panel.output.text.toPlainText())
        self.assertIn('error',panel.spectrum_view.data)


if __name__=='__main__':unittest.main()
