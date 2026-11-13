"""Independent sums, reconstruction coverage, result reuse and library navigation."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import csv,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from numpy.testing import assert_allclose
from signallab_pc.model import Signal
from signallab_pc import stft_tools as st


class StftMath(unittest.TestCase):
    def test_frame_spectrum_matches_direct_sum_with_shifted_complex_input(self):
        source=Signal(np.arange(15)+1j*np.arange(15)[::-1],-3)
        result=st.analyze(source,7,4,11,'hamming',boundary='centered')
        for index in (0,2,result['metadata']['frames']-1):
            product=st.frame_signals(result,index)[2];f=result['frequency']
            expected=np.array([sum(v*np.exp(-1j*w*n) for n,v in zip(product.axis,product.values)) for w in f])/sum(result['weights'])
            assert_allclose(st.spectrum(result,index,phase='global').values,expected,atol=1e-13)

    def test_bilateral_density_integrates_window_weighted_power_and_changes_units(self):
        source=Signal([1,2,1j,3,-1,2,4,2j],-2,metadata={'sample_rate_hz':20.,'time_start_s':3.})
        result=st.analyze(source,5,3,13,'hann',boundary='centered');index=2;chunk=st.frame_signals(result,index)[0].values
        expected=sum(abs(chunk*result['weights'])**2)/sum(result['weights']**2)
        digital=st.density_spectrum(result,index);physical=st.density_spectrum(result,index,True)
        self.assertAlmostEqual(float(sum(digital.values.real)*digital.step),expected,places=12)
        assert_allclose(physical.values,digital.values/20);self.assertAlmostEqual(physical.step,20*digital.step)
        f,t,fu,tu,_=st.axes(result,True);self.assertEqual((fu,tu),('rad/s','s'));self.assertAlmostEqual(t[0],3+(-2+2)/20)
        self.assertEqual(digital.metadata['operation'],'spectral_density')

    def test_inverse_recovers_real_and_complex_records_for_all_windows(self):
        source=Signal(np.exp(.4j*np.arange(37))+np.arange(37)/10,-11,metadata={'sample_rate_hz':32.,'time_start_s':.5})
        for window in ('hann','hamming','blackman','boxcar','bartlett','kaiser'):
            with self.subTest(window=window):
                result=st.analyze(source,9,5,15,window,boundary='centered');inverse=st.synthesize(result)
                assert_allclose(inverse.values,source.values,atol=4e-14);self.assertEqual(inverse.origin,source.origin);self.assertEqual(inverse.metadata['time_start_s'],.5)

    def test_inverse_uses_coefficients_not_cached_source_and_rejects_lost_samples(self):
        source=Signal(np.arange(17)+1.,0);result=st.analyze(source,8,4,12,'hann',boundary='centered')
        result['values']*=2;assert_allclose(st.synthesize(result).values,2*source.values,atol=1e-13)
        lost=st.analyze(source,8,4,12,'hann')
        with self.assertRaisesRegex(ValueError,'información suficiente'):st.synthesize(lost)
        holes=st.analyze(source,8,0,12,'hann',boundary='centered')
        with self.assertRaisesRegex(ValueError,'información suficiente'):st.synthesize(holes)
        rectangular=st.analyze(source,8,0,12,'boxcar');assert_allclose(st.synthesize(rectangular).values,source.values,atol=1e-13)

    def test_continuous_frame_padding_clock_and_physical_phase(self):
        source=Signal([1,3,2,4,1,2],.25,.1,'s','x','continuous')
        result=st.analyze(source,4,2,8,'hamming',boundary='centered');parts=st.frame_signals(result,0)
        assert_allclose(parts[0].values,[0,0,1,3]);self.assertAlmostEqual(parts[0].origin,.05)
        assert_allclose(st.synthesize(result).values,source.values,atol=1e-13)
        spectrum=st.spectrum(result,0,phase='global');expected=np.array([sum(v*np.exp(-1j*w*t) for t,v in zip(parts[2].axis,parts[2].values)) for w in spectrum.axis])/sum(result['weights'])
        assert_allclose(spectrum.values,expected,atol=1e-13)

    def test_large_and_zero_levels_have_safe_log_scales(self):
        large=st.analyze(Signal(np.full(8,1e200)),4,2,8,'boxcar',boundary='centered')
        with self.assertRaisesRegex(ValueError,'escala lineal'):st.map_values(large,'density')
        values,_,_=st.map_values(large,'density_db');self.assertTrue(np.all(np.isfinite(values)))
        zero=st.analyze(Signal(np.zeros(8)),4,2,8,'hann',boundary='centered');values,_,_=st.map_values(zero)
        assert_allclose(values,-100);assert_allclose(st.density_spectrum(zero,1).values,0)
        with self.assertRaisesRegex(ValueError,'Fs registrada'):st.axes(zero,True)
        with self.assertRaises(ValueError):st.analyze(Signal([1,2,3]),2.5,1,4,'hann')

    def test_digital_global_phase_reduces_large_integer_origin_exactly(self):
        origin=2**53+5;source=Signal(np.arange(16)+1.,origin);result=st.analyze(source,8,4,8,'hamming')
        self.assertEqual(st.frame_signals(result,0)[0].origin,origin)
        local=st.spectrum(result,0);expected=local.values*np.exp(-1j*result['frequency']*(origin%8))
        assert_allclose(st.spectrum(result,0,phase='global').values,expected,atol=2e-13)


class Blocks(unittest.TestCase):
    def test_ola_and_ols_inspection_agree_with_direct_circular_and_linear_sums(self):
        from signallab_pc.dsp_extensions import block_convolution
        from signallab_pc.block_inspection import capture,inspect
        x=Signal(np.arange(17)+1j*np.arange(17)[::-1],-4);h=Signal(np.array([1,2,-1,3,.5,-2,1,1j]),-2)
        expected=np.convolve(x.values,h.values)
        for method in ('ola','ols'):
            result=block_convolution(x,h,6,method);assert_allclose(result.values,expected,atol=1e-12);trace=capture(x,h,result)
            for index in (0,result.metadata['blocks']-1):
                data=inspect(trace,index);chunk,raw,valid,final=data['signals'];size=data['fft_size']
                circular=[sum(v*h.values[(k-j)%size] for j,v in enumerate(chunk.values) if (k-j)%size<len(h.values)) for k in range(size)]
                assert_allclose(raw.values,np.asarray(circular)[:len(raw.values)],atol=1e-12)
                if method=='ols':assert_allclose(valid.values,final.values,atol=1e-12);self.assertEqual(data['discard'],7)
                else:self.assertEqual(data['discard'],0);assert_allclose(valid.values,np.convolve(chunk.values,h.values),atol=1e-12)
                self.assertEqual(valid.origin,result.origin+index*6)


class RealPanels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        self.widgets=[];self.warnings=[];self.warning=patch('PySide6.QtWidgets.QMessageBox.warning',side_effect=lambda *args:self.warnings.append(str(args[2])));self.warning.start()
    def tearDown(self):
        self.warning.stop()
        for widget in self.widgets:widget.close();widget.deleteLater()
        self.app.processEvents()
    def host(self):
        from test_workflow_contracts import Host
        host=Host();self.widgets.append(host.bar);return host

    def test_stft_panel_selects_frames_scales_and_reconstructs_without_retyping(self):
        from signallab_pc.dsp_extensions_panel import DspExtensionsPanel
        host=self.host();panel=DspExtensionsPanel(host,'stft');self.widgets.append(panel)
        panel.sources[0].set_source(Signal(np.arange(15)+1.,-2,metadata={'sample_rate_hz':20.,'time_start_s':1.}),None)
        for name,text in [('length','6'),('overlap','3'),('nfft','11')]:panel.fields[name].setText(text)
        panel.calculate();view=panel.explorer;self.assertFalse(self.warnings);self.assertIsNotNone(view.data)
        snapshot=view.data['values'].copy();view.clock.setCurrentIndex(1);view.scale.setCurrentIndex(2)
        view.pick_frame(SimpleNamespace(inaxes=view.axis,button=1,xdata=view._centers[2]));self.assertEqual(view.frame.value(),3)
        view.part.setCurrentIndex(3);assert_allclose(view.frame_view.result.values,st.frame_signals(view.data,2)[2].values)
        view.part.setCurrentIndex(4);self.assertEqual(view.frame_view.result.metadata['operation'],'spectral_density')
        view.inverse();assert_allclose(view.inverse_view.result.values,np.arange(15)+1,atol=1e-12);assert_allclose(view.data['values'],snapshot)
        self.assertTrue(view.inverse_view.result_ids[0]);self.assertFalse(self.warnings)
        view.range.setText('unused in linear scale');view.redraw();self.assertFalse(self.warnings)
        extreme=st.analyze(Signal(np.full(15,1e200)),6,3,11,'hann',boundary='centered');view.set_data(extreme,[])
        self.assertIsNone(view.axis);self.assertIsNone(view.inverse_view.result);self.assertIsNone(view.frame_view.result);self.assertTrue(self.warnings)
        view.range.setText('100');view.scale.setCurrentIndex(0);view.part.setCurrentIndex(0);self.assertIsNotNone(view.axis);self.assertIsNotNone(view.frame_view.result)

    def test_csv_preserves_selected_physical_axes_and_phase(self):
        from signallab_pc.stft_view import StftExplorer
        host=self.host();view=StftExplorer(host);self.widgets.append(view)
        source=Signal([1,2,3,4,5,6],-1,metadata={'sample_rate_hz':10.,'time_start_s':.2});view.set_data(st.analyze(source,4,2,7,'hamming',boundary='centered'),[]);view.clock.setCurrentIndex(1)
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'stft.csv'
            with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName',return_value=(str(path),'CSV')):view.export_matrix()
            with path.open(encoding='utf-8') as stream:
                metadata=json.loads(stream.readline()[2:]);rows=list(csv.DictReader(stream))
            self.assertEqual(metadata['export_phase'],'global');self.assertEqual(metadata['export_frequency_units'],'rad/s')
            expected=st.spectrum(view.data,0,physical=True,phase='global');self.assertEqual(len(rows),7*view.data['metadata']['frames'])
            assert_allclose([complex(float(row['real']),float(row['imaginaria'])) for row in rows[:7]],expected.values)

    def test_block_panel_inspector_exposes_valid_contribution_and_tail(self):
        from signallab_pc.dsp_extensions_panel import DspExtensionsPanel
        host=self.host();panel=DspExtensionsPanel(host,'blocks');self.widgets.append(panel)
        panel.sources[0].set_source(Signal([1,2,3,4,5],-2),None);panel.kernel.set_source(Signal([1,-1,2],-1),None);panel.fields['length'].setText('2');panel.method.setCurrentIndex(1);panel.calculate()
        panel.view.views.setCurrentIndex(panel.inspector_index);self.assertIsNotNone(panel.inspector.data)
        panel.inspector.index.setValue(panel.result.metadata['blocks']);panel.inspector.part.setCurrentIndex(2)
        assert_allclose(panel.inspector.view.result.values,panel.inspector.data['signals'][3].values,atol=1e-13);self.assertFalse(self.warnings)

    def test_library_uses_short_titles_keeps_routes_and_searches_old_names(self):
        from signallab_pc.theory_panel import TheoryPanel
        from signallab_pc.workspaces import ROUTES
        panel=TheoryPanel(lambda _:None);self.widgets.append(panel)
        self.assertEqual(len(panel.sections),122);self.assertTrue(all(len(s['title'])<=38 for s in panel.sections))
        self.assertLess(panel.items.topLevelItemCount(),14)
        panel.kind.setCurrentIndex(2);self.assertTrue(all(s['content_kind']=='tool' for s in panel.filtered))
        panel.select_tool(ROUTES['dsp_extensions','stft']);self.assertEqual(panel.selected_route,ROUTES['dsp_extensions','stft']);self.assertEqual(panel.items.currentItem().text(0),'STFT y espectrograma')
        panel.search.setText('notación científica');panel.kind.setCurrentIndex(0);self.assertTrue(panel.filtered)
        self.assertIn('Coeficientes y constantes',[s['title'] for s in panel.filtered])
        panel.follow_reference(__import__('PySide6.QtCore',fromlist=['QUrl']).QUrl('library:article/tool:course_tools:fir'));self.assertEqual(panel.selected_route,ROUTES['course_tools','fir'])


if __name__=='__main__':unittest.main()
