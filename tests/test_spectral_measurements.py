"""Closed integrals, Parseval, bin boundaries, peaks and real result transport."""
import os,math,csv,json,tempfile,unittest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
from unittest.mock import patch
import numpy as np
from numpy.testing import assert_allclose
from scipy.signal import find_peaks,peak_prominences
from signallab_pc.model import Signal
from signallab_pc import spectral_measurements as m


class Measures(unittest.TestCase):
    def test_linear_density_bands_centroid_and_rms_against_closed_integrals(self):
        source=Signal([0,1],0,1,'Hz','P','frequency');result=m.analyze(source,[('todo',None,None),('medio',.25,.75)],interpretation='power_density')
        self.assertAlmostEqual(result['total']['value'],.5);self.assertAlmostEqual(result['bands'][1]['measure']['value'],.25)
        self.assertAlmostEqual(result['moments']['centroid'],2/3);self.assertAlmostEqual(result['moments']['rms_width'],math.sqrt(1/18))
        self.assertTrue(result['overlap']);assert_allclose(result['cumulative'].values,[0,1])

    def test_complex_spectrum_has_parseval_factor_and_partial_interval(self):
        source=Signal(np.full(129,1+1j),-math.pi,math.tau/128,'rad/muestra','X','frequency')
        data=m.analyze(source,[('izquierda',None,0),('derecha',0,None)])
        self.assertAlmostEqual(data['total']['value'],2);self.assertAlmostEqual(sum(r['measure']['value'] for r in data['bands']),2)
        self.assertFalse(data['overlap']);self.assertAlmostEqual(data['moments']['centroid'],0,places=13);self.assertAlmostEqual(data['moments']['rms_width'],math.pi/math.sqrt(3))

    def test_even_odd_dft_and_index_views_sum_bins_once(self):
        from signallab_pc.operations import dft
        for count in (1,5,8):
            x=Signal(np.arange(count)+1j*np.arange(count)[::-1]);expected=float(sum(abs(x.values)**2))
            for centered in (False,True):
                source=dft(x,centered=centered);p=m.prepare(source);mid=(p['low']+p['high'])/2
                data=m.analyze(source,[('a',None,mid),('b',mid,None)])
                self.assertAlmostEqual(data['total']['value'],expected,places=10);self.assertAlmostEqual(sum(r['measure']['value'] for r in data['bands']),expected,places=10)
                if centered:
                    indexed=Signal(source.values,-count//2 if count%2==0 else -(count//2),1,'k','K','discrete',metadata=source.metadata.copy())
                    self.assertAlmostEqual(m.analyze(indexed,[('total',None,None)])['total']['value'],expected,places=10)

    def test_calibrated_psd_uses_density_not_density_squared(self):
        from signallab_pc.fourier import spectral_density
        x=Signal([1,2,3,4,5,6,7,8]);psd=spectral_density(x,100,method='periodogram',window='boxcar')
        result=m.analyze(psd,[('total',None,None)]);self.assertEqual(result['quantity'],'Potencia');self.assertAlmostEqual(result['total']['value'],float(np.mean(x.values.real**2)))
        self.assertAlmostEqual(result['limits'][0],-50);self.assertAlmostEqual(result['limits'][1],50)
        legacy=spectral_density(x,100,method='legacy',window='boxcar')
        with self.assertRaisesRegex(ValueError,'sin calibración'):m.analyze(legacy,[('total',None,None)])
        angular=Signal(np.full(129,2.),-math.pi,math.tau/128,'rad/muestra','Sx','frequency',metadata={'operation':'spectral_density','density_units':'amplitud²'})
        self.assertAlmostEqual(m.analyze(angular,[('',None,None)])['total']['value'],2)
        self.assertAlmostEqual(m.analyze(angular,[('',None,None)],interpretation='density_per_unit')['total']['value'],2*math.tau)

    def test_line_weights_integrate_by_summation_and_transport_is_offered(self):
        from signallab_pc.course_tools import periodic_lines
        from signallab_pc.toolbox import signal_destinations
        from signallab_pc.workspaces import ROUTES
        coefficients=Signal([1,2,3],-1);lines=periodic_lines(coefficients,2)['signals'][0]
        result=m.analyze(lines,[('negativa',None,0),('resto',0,None)])
        self.assertAlmostEqual(result['total']['value'],14);self.assertAlmostEqual(result['bands'][0]['measure']['value'],1)
        self.assertEqual(len(result['peaks']),3);self.assertIn(ROUTES['course_tools','band'],signal_destinations(lines,list(ROUTES.values())))
        normalized=coefficients.copy_with(metadata={'operation':'continuous_fourier_series'})
        self.assertAlmostEqual(m.analyze(normalized,[('todo',None,None)])['total']['value'],14)
        self.assertIn(ROUTES['course_tools','band'],signal_destinations(normalized,list(ROUTES.values())))

    def test_system_response_is_area_and_zero_measure_is_not_a_fake_cdf(self):
        h=Signal(np.ones(33),0,math.pi/32,'rad/muestra','H','frequency',metadata={'operation':'frequency_response'})
        result=m.analyze(h,[('total',None,None)]);self.assertEqual(result['quantity'],'Área de |H|²');self.assertAlmostEqual(result['total']['value'],math.pi)
        zero=m.analyze(h.copy_with(values=np.zeros(33)),[('total',None,None)])
        self.assertIsNone(zero['cumulative']);self.assertIsNone(zero['moments']['centroid']);self.assertIsNone(zero['bands'][0]['fraction']);self.assertEqual(zero['peaks'],[])

    def test_extreme_mass_and_moments_retain_small_nonzero_results(self):
        source=Signal([1,1e-300],0,1e200,'Hz','P','frequency',metadata={'operation':'spectral_density','segment':2})
        data=m.analyze(source,[('todo',None,None),('débil',1e200,2e200)])
        self.assertAlmostEqual(data['moments']['centroid']/1e-100,1,places=11);self.assertAlmostEqual(data['moments']['rms_width']/1e50,1,places=11)
        self.assertAlmostEqual(data['bands'][1]['measure']['value']/1e-100,1,places=11)
        huge=Signal([1e250,1e250],0,1,'rad/s','X','frequency');result=m.analyze(huge,[('a',0,.5),('b',.5,1)])
        self.assertIsNone(result['total']['value']);self.assertIn('fuera de float64',result['total']['text']);self.assertAlmostEqual(result['bands'][0]['fraction'],.5,places=11)

    def test_invalid_density_band_and_undefined_frequency_region_are_rejected(self):
        source=Signal([1,2,1],-1,1,'rad/s','X','frequency')
        for values in ([-1,2,1],[1,2j,1]):
            with self.assertRaises(ValueError):m.analyze(source.copy_with(values=values),[('',None,None)],interpretation='power_density')
        for low,high in ((-2,0),(0,0),(1,-1)):
            with self.assertRaises(ValueError):m.analyze(source,[('',low,high)])
        conditional=source.copy_with(metadata={'source_frequency_condition':'w != 0'})
        with self.assertRaises(ValueError):m.analyze(conditional,[('',None,None)])


class PeaksAndFrames(unittest.TestCase):
    def test_prominence_matches_scipy_without_repeated_global_scans(self):
        rng=np.random.default_rng(5)
        for values in (rng.random(1000)+.001,np.array([0.,1,1,0,2,0,1,0])):
            found,_=find_peaks(values)
            with np.errstate(divide='ignore'):logs=np.log(values)
            assert_allclose(np.exp(m.log_prominences(logs,found)),peak_prominences(values,found)[0],atol=1e-14)
        many=np.tile([0.,1.],10000);found=np.arange(1,len(many)-1,2)
        with np.errstate(divide='ignore'):result=m.log_prominences(np.log(many),found)
        assert_allclose(np.exp(result),1)

    def test_periodic_edges_plateaus_and_optional_sub_bin_estimates(self):
        x=np.arange(9)-4;source=Signal(np.exp(-.5*(x-.25)**2),-4,1,'Hz','P','frequency')
        data=m.analyze(source,[('',None,None)],interpretation='power_density',interpolate=True,prominence_percent=0)
        peak=data['peaks'][0];self.assertEqual(peak['frequency'],0);self.assertAlmostEqual(peak['estimated_frequency'],.25)
        from signallab_pc.operations import dft
        dc=dft(Signal(np.ones(8)),centered=False);peaks=m.analyze(dc,[('',None,None)])['peaks'];self.assertEqual(peaks[0]['frequency'],0)
        flat=Signal([0,1,1,0],0,1,'Hz','P','frequency');peaks=m.analyze(flat,[('',None,None)],interpretation='power_density',interpolate=True)['peaks'];self.assertEqual(peaks[0]['plateau'],2);self.assertIsNone(peaks[0]['estimated_frequency'])

    def test_tiny_peaks_can_be_found_without_linear_ratio_underflow(self):
        source=Signal([0,1e200,0,1e-200,0],0,1,'rad/s','X','frequency')
        peaks=m.analyze(source,[('',None,None)],level_db=-9000,prominence_percent=0)['peaks'];self.assertEqual([r['frequency'] for r in peaks],[1,3]);self.assertLess(peaks[1]['relative_db'],-7000)

    def test_stft_band_power_matches_direct_window_weighted_samples_and_clock(self):
        from signallab_pc.stft_tools import analyze,frame_signals
        source=Signal(np.arange(37)%5,-7,metadata={'sample_rate_hz':100.,'time_start_s':2.})
        data=analyze(source,8,4,17,'hann',boundary='centered');curves=m.stft_band_series(data,[('total',None,None)])
        expected=[float(sum(abs(frame_signals(data,i)[2].values)**2)/sum(data['weights']**2)) for i in range(data['metadata']['frames'])]
        assert_allclose(curves[0].values,expected,atol=1e-12);self.assertEqual(curves[0].domain,'discrete');self.assertEqual(curves[0].metadata['sample_rate_hz'],25)
        physical=m.stft_band_series(data,[('total',None,None)],True)[0];assert_allclose(physical.values,expected,atol=1e-12);self.assertEqual(physical.domain,'continuous');self.assertAlmostEqual(physical.origin,1.995)
        left,right=m.stft_band_series(data,[('a',-math.pi,0),('b',0,math.pi)]);assert_allclose(left.values+right.values,expected,atol=1e-12)
        left,right=m.stft_band_series(data,[('a',-math.pi*100,0),('b',0,math.pi*100)],True);assert_allclose(left.values+right.values,expected,atol=1e-12)


class Panels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        from test_workflow_contracts import Host
        self.host=Host();self.widgets=[self.host.bar];self.errors=[];self.warnings=patch('PySide6.QtWidgets.QMessageBox.warning',side_effect=lambda *args:self.errors.append(str(args[2])));self.warnings.start()
    def tearDown(self):
        self.warnings.stop()
        for widget in self.widgets:widget.close();widget.deleteLater()
        self.app.processEvents()
    def panel(self):
        from signallab_pc.spectral_measurements_panel import SpectralMeasurePanel
        panel=SpectralMeasurePanel(self.host);self.widgets.append(panel);return panel

    def test_independent_formula_multibands_and_mouse_selection_keep_result_snapshot(self):
        panel=self.panel();panel.source.expression.setText('1');panel.source.frequency_units.setCurrentText('rad/muestra');panel.source.origin.setText('-pi');panel.source.step.setText('2*pi/128');panel.source.count.setText('129');panel.bands.add()
        panel.bands.table.item(0,2).setText('0');panel.bands.table.item(1,1).setText('0');panel.calculate()
        self.assertFalse(self.errors);self.assertAlmostEqual(panel.result['total']['value'],1);self.assertFalse(panel.result['overlap']);self.assertTrue(panel.cumulative.result_ids[0])
        previous=panel.result;panel.bands.table.setCurrentCell(0,1);panel.select_range(-1,1);self.assertIs(panel.result,previous);self.assertIn('anterior',panel.state.text())
        panel.bands.add();panel.bands.remove();panel.calculate();self.assertFalse(self.errors)

    def test_dft_index_transport_and_cumulative_guards_are_semantic(self):
        from signallab_pc.operations import dft
        from signallab_pc.toolbox import signal_destinations
        from signallab_pc.workspaces import ROUTES
        from signallab_pc.fourier import ictft,energy_density
        source=dft(Signal([1,2,3,4]));panel=self.panel();key=self.host.publish(source);panel.source.set_source(source,key);panel.calculate();self.assertFalse(self.errors)
        self.assertAlmostEqual(panel.result['total']['value'],30);self.assertIn(ROUTES['course_tools','band'],signal_destinations(source,list(ROUTES.values())))
        cdf=panel.cumulative.result;self.assertEqual(cdf.data_kind,'spectral_measurement')
        with self.assertRaises(ValueError):energy_density(cdf)
        with self.assertRaises(ValueError):ictft(cdf,0,1,10)
        self.assertEqual(signal_destinations(cdf,list(ROUTES.values())),[])

    def test_csv_has_units_and_numeric_band_bounds(self):
        panel=self.panel();panel.source.set_source(Signal([0,2,0,1,0],0,.5,'Hz','P','frequency',metadata={'operation':'spectral_density'}));panel.calculate();self.assertFalse(self.errors)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'bands.csv'
            with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName',return_value=(str(path),'CSV')):panel.export_table('bands')
            with path.open(encoding='utf-8') as stream:metadata=json.loads(stream.readline()[2:]);rows=list(csv.DictReader(stream))
            self.assertEqual(metadata['units'],'Hz');self.assertEqual(float(rows[0]['low']),0);self.assertEqual(float(rows[0]['high']),2)

    def test_stft_band_view_publishes_reusable_curves_and_marks_edited_bounds(self):
        from signallab_pc.stft_view import StftExplorer
        from signallab_pc.stft_tools import analyze
        view=StftExplorer(self.host);self.widgets.append(view);view.set_data(analyze(Signal(np.ones(32)),8,4,16,'hann',boundary='centered'),[])
        power=view.band_power;power.calculate();self.assertFalse(self.errors);self.assertIsNotNone(power.view.result);self.assertEqual(power.view.result.domain,'discrete')
        power.bands.table.item(0,2).setText('0');self.assertIn('anterior',power.state.text());self.assertIsNotNone(power.view.result_ids[0])


if __name__=='__main__':unittest.main()
