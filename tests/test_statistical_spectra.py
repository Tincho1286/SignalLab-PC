"""Independent finite-sample spectral confidence oracles."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import cmath
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from signallab_pc import session
from signallab_pc.dsp_application import PSDRequest, estimate_psd
from signallab_pc.dsp_cli import main
from signallab_pc.execution import ExecutionContext, ResourceLimitError
from signallab_pc.fourier import ictft
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.spectral_measurements import supported
from signallab_pc.statistical_spectra import advanced_density, cross_spectra, lomb_periodogram, white_noise_confidence
from signallab_pc.stochastic_cli import main as stochastic
from signallab_pc.workspaces import ROUTES
from test_desktop_session import DesktopSessionFixture


class SpectralConfidenceTests(unittest.TestCase):
    def test_rectangular_real_bins_have_the_correct_chi_square_law(self):
        source = Signal([1,2,3,-1,4,0,1,2],metadata={'sample_rate_hz':16,'amplitude_units':'V'})
        for sides, expected in [('two-sided',[2,4,2,4]),('one-sided',[2,4,2])]:
            spectrum = estimate_psd(PSDRequest(source,method='bartlett',segment=4,sidedness=sides))
            interval = white_noise_confidence(spectrum,model='real_gaussian_white')
            self.assertEqual(interval['density_units'],'V²/Hz')
            self.assertEqual([row['degrees_of_freedom'] for row in interval['bounds']],expected)
            for estimate,bound in zip(spectrum.values.real,interval['bounds'],strict=True):
                df=bound['degrees_of_freedom']
                for key,target in [('lower',.025),('upper',.975)]:
                    pivot=df*estimate/bound[key]
                    survival=math.exp(-pivot/2)*(1+pivot/2 if df==4 else 1)
                    self.assertAlmostEqual(survival,target,delta=2e-12)

    def test_removed_dc_is_undefined_and_complex_bins_share_degrees(self):
        source = Signal([1,2,3,4,0,1],metadata={'sample_rate_hz':6})
        spec = estimate_psd(PSDRequest(source,method='bartlett',segment=3,remove_mean=True,sidedness='one-sided'))
        report = white_noise_confidence(spec,model='real_gaussian_white')
        self.assertIsNone(report['bounds'][0])
        self.assertEqual(report['bounds'][1]['degrees_of_freedom'],4)
        z = source.copy_with(values=[1+2j,2,1j,4,2,1j])
        spec = estimate_psd(PSDRequest(z,method='periodogram',window='boxcar'))
        report = white_noise_confidence(spec,model='proper_complex_gaussian_white')
        self.assertTrue(all(row['degrees_of_freedom']==2 for row in report['bounds']))
        with self.assertRaises(ValueError):
            white_noise_confidence(spec,model='real_gaussian_white')

    def test_rejects_uncalibrated_models_and_impossible_budgets(self):
        source = Signal([1,2,4,3,9,2,3,4],metadata={'sample_rate_hz':8})
        tapered = estimate_psd(PSDRequest(source,method='welch',segment=4,overlap=2))
        with self.assertRaises(ValueError):
            white_noise_confidence(tapered,model='real_gaussian_white')
        with self.assertRaises(ValueError):
            white_noise_confidence(source,model='real_gaussian_white')
        rectangle = estimate_psd(PSDRequest(source,method='periodogram',window='boxcar'))
        with self.assertRaises(ValueError):
            white_noise_confidence(rectangle,model='')
        with self.assertRaises(ValueError):
            white_noise_confidence(rectangle,model='real_gaussian_white',coverage=1)
        with self.assertRaises(ResourceLimitError):
            white_noise_confidence(rectangle,model='real_gaussian_white',execution=ExecutionContext(max_work_bytes=1))

    def test_cli_stores_the_same_confidence_interval_with_its_psd_parent(self):
        source = Signal([1,3,5,2,1,3,4,0],metadata={'sample_rate_hz':8})
        project=Project()
        original=project.add(source)
        with TemporaryDirectory() as directory:
            base,out=Path(directory)/'input.slproj',Path(directory)/'spectra.slproj'
            session.save(base,project,session.empty_workspace())
            stdout,stderr=StringIO(),StringIO()
            with redirect_stdout(stdout),redirect_stderr(stderr):
                code=main(['psd','--session',str(base),'--record',original,'--output',str(out),
                           '--method','bartlett','--segment','4','--white-confidence','real_gaussian_white'])
            self.assertEqual(code,0,stderr.getvalue())
            receipt=json.loads(stdout.getvalue())
            loaded,_=session.load(out)
            psd=loaded.get(receipt['result_id'])
            self.assertEqual(loaded.get(receipt['confidence_id']),white_noise_confidence(psd,model='real_gaussian_white'))
            self.assertEqual(loaded.headers()[-1]['parents'],[receipt['result_id']])


class SpectralConfidenceWorkbenchTests(DesktopSessionFixture):
    def test_bartlett_band_is_drawn_and_registered_with_the_psd(self):
        window=self.window()
        route=ROUTES['fourier',7]
        window.open_tool(route)
        page=window.pages[route]
        panel=page.panel
        signal=Signal([1,2,3,-1,4,0,1,2],metadata={'sample_rate_hz':16})
        parent=window.publish(signal,operation='Registro de prueba')
        page.context.source.set_source(signal,parent)
        panel.estimator.setCurrentIndex(3)
        panel.segment.setText('4')
        panel.confidence.setCurrentIndex(panel.confidence.findData('real_gaussian_white'))
        window.calculate_active()
        self.wait_for_calculation(window)
        expected=white_noise_confidence(panel.result,model='real_gaussian_white')
        row=window.project.headers('calculation')[-1]
        self.assertEqual(window.project.get(row['id']),expected)
        self.assertIn('Cobertura marginal',panel.report.toPlainText())
        self.assertGreater(len(panel.figure.axes[0].collections),0)
        panel.confidence.setCurrentIndex(0)
        window.calculate_active()
        self.wait_for_calculation(window)
        self.assertIsNone(panel.spectral_interval)

    def test_cross_view_plots_aligned_phase_and_coherence_and_reuses_the_pair(self):
        window=self.window()
        route=ROUTES['fourier',7]
        window.open_tool(route)
        page=window.pages[route]
        panel=page.panel
        y=Signal([1,1j,-1,-1j]*2,metadata={'sample_rate_hz':4})
        x=y.copy_with(values=[-1j,1,1j,-1]*2)
        parents=[window.publish(value,operation='Entrada') for value in (x,y)]
        page.context.source.set_source(x,parents[0])
        self.assertTrue(panel.second_spectrum.isHidden())
        panel.estimator.setCurrentIndex(4)
        self.assertFalse(panel.second_spectrum.isHidden())
        panel.second_spectrum.set_source(y,parents[1])
        panel.window.setCurrentIndex(0)
        panel.segment.setText('4')
        panel.overlap.setText('0')
        window.calculate_active()
        self.wait_for_calculation(window)
        self.assertEqual(panel.result.data_kind,'cross_density')
        np.testing.assert_array_equal(panel.result.values,[0,0,0,-1j])
        self.assertEqual(len(panel.figure.axes),3)
        self.assertEqual(panel.figure.axes[-1].get_ylabel(),'Coherencia')
        self.assertTrue(all(axis.get_xlim()==panel.figure.axes[0].get_xlim() for axis in panel.figure.axes))
        row=window.project.headers('calculation')[-1]
        self.assertEqual(row['parents'],parents)
        self.assertEqual(window.project.get(row['id'])['values'],[None,None,None,1.])

    def test_additional_estimators_and_welch_reference_stay_in_the_psd_tool(self):
        window=self.window()
        route=ROUTES['fourier',7]
        window.open_tool(route)
        page=window.pages[route]
        panel=page.panel
        source=Signal([1,2,0,-3,1,4,2,-2],metadata={'sample_rate_hz':8})
        key=window.publish(source,operation='Entrada')
        page.context.source.set_source(source,key)
        panel.estimator.setCurrentIndex(panel.estimator.findData('multitaper'))
        panel.fft_bins.setText('16')
        panel.bandwidth.setText('1.5')
        panel.tapers.setText('2')
        panel.compare_welch.setChecked(True)
        window.calculate_active()
        self.wait_for_calculation(window)
        expected=advanced_density(source,method='multitaper',nfft=16,bandwidth=1.5,tapers=2)
        np.testing.assert_array_equal(panel.result.values,expected.values)
        self.assertIn('Trazo discontinuo',panel.report.toPlainText())
        self.assertTrue(any(line.get_linestyle()=='--' for line in panel.figure.axes[0].lines))
        panel.estimator.setCurrentIndex(panel.estimator.findData('lomb'))
        times=[0,.3,.4,.85,1.0,1.5,1.7,2.3]
        panel.observation_times.setText(', '.join(map(str,times)))
        panel.minimum_hz.setText('.2')
        panel.maximum_hz.setText('2')
        panel.frequency_points.setText('41')
        window.calculate_active()
        self.wait_for_calculation(window)
        self.assertEqual(panel.result.data_kind,'irregular_periodogram')
        self.assertIsNone(panel.psd_reference)
        np.testing.assert_array_equal(panel.result.values,lomb_periodogram(source,times,low=.2,high=2,points=41).values)


class CrossSpectrumTests(unittest.TestCase):
    def test_welch_cross_spectrum_matches_complex_products_on_the_common_axis(self):
        a=[100,1+2j,2-1j,-1j,4,5+1j,0,8]
        b=[1,3j,.5,3+2j,1-1j,4,3]
        fs=6
        x=Signal(a,origin=-1,metadata={'sample_rate_hz':fs,'time_start_s':0})
        y=Signal(b,origin=0,metadata={'sample_rate_hz':fs,'time_start_s':1/fs})
        result=cross_spectra(x,y,segment=3,overlap=1,window='boxcar')
        pxx,pyy,pxy=[],[],[]
        for k in (-1,0,1):
            lhs,rhs=[],[]
            for offset in (0,2,4):
                phase=[cmath.exp(-2j*math.pi*k*n/3) for n in range(3)]
                lhs.append(sum(a[1+offset+n]*phase[n] for n in range(3)))
                rhs.append(sum(b[offset+n]*phase[n] for n in range(3)))
            total=3*3*fs
            pxx.append(sum(abs(v)**2 for v in lhs)/total)
            pyy.append(sum(abs(v)**2 for v in rhs)/total)
            pxy.append(sum(v*w.conjugate() for v,w in zip(lhs,rhs,strict=True))/total)
        np.testing.assert_allclose(result.cross.values,pxy,atol=2e-12)
        np.testing.assert_allclose(result.first.values,pxx,atol=2e-12)
        np.testing.assert_allclose(result.second.values,pyy,atol=2e-12)
        expected=abs(np.asarray(pxy))**2/(np.asarray(pxx)*pyy)
        np.testing.assert_allclose(result.coherence['values'],expected,atol=2e-12)
        self.assertEqual(result.cross.data_kind,'cross_density')
        self.assertFalse(supported(result.cross))
        with self.assertRaisesRegex(ValueError,'densidad espectral cruzada'):
            ictft(result.cross,0,1,16)
        self.assertEqual(result.coherence['common_origin'],0)
        self.assertEqual(result.coherence['common_last_index'],6)

    def test_cross_phase_and_undefined_coherence(self):
        x=Signal([1,1j,-1,-1j]*2,metadata={'sample_rate_hz':4})
        delay=x.copy_with(values=[-1j,1,1j,-1]*2)
        result=cross_spectra(delay,x,segment=4,overlap=0,window='boxcar')
        np.testing.assert_array_equal(result.cross.values,[0,0,0,-1j])
        self.assertEqual(result.coherence['values'],[None,None,None,1.])
        one=cross_spectra(delay,x,segment=8,window='boxcar')
        self.assertIsNone(one.coherence['values'])
        self.assertIn('dos bloques',one.coherence['scope'])
        real=Signal([1,2,-1,-2,3,2,-3,-2],metadata={'sample_rate_hz':4})
        centered=cross_spectra(real,real,segment=4,overlap=0,window='boxcar',remove_mean=True)
        self.assertIsNone(centered.coherence['values'][2])
        self.assertEqual(centered.cross.values[2],0)

    def test_cross_products_survive_reciprocal_scales(self):
        x=Signal(np.tile([1e200,-1e200],4),metadata={'sample_rate_hz':4})
        y=Signal(np.tile([1e-200,-1e-200],4),metadata={'sample_rate_hz':4})
        result=cross_spectra(x,y,segment=4,overlap=0,window='boxcar')
        self.assertIsNone(result.first)
        self.assertIsNone(result.second)
        self.assertAlmostEqual(result.cross.values[0].real,1.)
        self.assertAlmostEqual(result.coherence['values'][0],1.)
        self.assertEqual(len(result.coherence['unrepresentable_outputs']),2)
        with self.assertRaises(ValueError):
            cross_spectra(x,y,rate=3)
        with self.assertRaises(ResourceLimitError):
            cross_spectra(x,y,execution=ExecutionContext(max_work_bytes=1))

    def test_cli_stores_cross_and_marginal_estimates_together(self):
        x=Signal([0,2,3,4,0,2,4,8],metadata={'sample_rate_hz':8})
        y=x.copy_with(values=[0,1,4,2,3,0,8,4])
        project=Project()
        left,right=project.add(x),project.add(y)
        with TemporaryDirectory() as folder:
            base,out=Path(folder)/'pair.slproj',Path(folder)/'spectrum.slproj'
            session.save(base,project,session.empty_workspace())
            stdout,stderr=StringIO(),StringIO()
            with redirect_stdout(stdout),redirect_stderr(stderr):
                code=stochastic(['spectral-cross','--session',str(base),'--record',left,'--second-record',right,
                                 '--output',str(out),'--segment','4','--overlap','0','--window','boxcar'])
            self.assertEqual(code,0,stderr.getvalue())
            receipt=json.loads(stdout.getvalue())
            reopened,_=session.load(out)
            expected=cross_spectra(x,y,segment=4,overlap=0,window='boxcar')
            self.assertEqual(reopened.get(receipt['report_id']),expected.coherence)
            cross=reopened.get(receipt['spectrum_ids']['cross'])
            np.testing.assert_array_equal(cross.values,expected.cross.values)


class AdvancedSpectralTests(unittest.TestCase):
    def test_truncated_lag_psd_matches_direct_bartlett_weighted_covariance(self):
        x=np.array([2+1j,1j,3,2-3j,-1,0,4j],complex)
        source=Signal(x,metadata={'sample_rate_hz':14})
        result=estimate_psd(PSDRequest(source,method='blackman_tukey',maximum_lag=2,nfft=9,remove_mean=True))
        centered=x-x.mean()
        gammas=[sum(centered[i+k]*centered[i].conjugate() for i in range(len(x)-k))/len(x) for k in range(3)]
        direct=[(gammas[0].real+2*sum((1-k/3)*(gammas[k]*cmath.exp(-2j*math.pi*f*k/14)).real
                                      for k in (1,2)))/14 for f in result.axis]
        np.testing.assert_allclose(result.values,direct,atol=2e-12)
        self.assertAlmostEqual(result.values.real.sum()*result.step,gammas[0].real)
        self.assertEqual(result.metadata['covariance_divisor'],'N')
        white=advanced_density(source,method='blackman_tukey',max_lag=0)
        np.testing.assert_allclose(white.values,np.mean(abs(x)**2)/14)
        self.assertTrue(np.all(result.values.real>=0))

    def test_multitaper_matches_eigenvectors_of_independent_concentration_matrix(self):
        n,nw,k,fs=7,1.5,3,12
        x=np.array([2,1,-4,3,0,1,-2],float)
        w=nw/n
        diffs=np.subtract.outer(np.arange(n),np.arange(n))
        kernel=2*w*np.sinc(2*w*diffs)
        eigen,tapers=np.linalg.eigh(kernel)
        estimate=advanced_density(Signal(x,metadata={'sample_rate_hz':fs}),method='multitaper',
                                  nfft=8,bandwidth=nw,tapers=k)
        expected=[sum(abs(sum(x[i]*window[i]*cmath.exp(-2j*math.pi*f*i/fs) for i in range(n)))**2
                      for window in tapers.T[-k:])/(fs*k) for f in estimate.axis]
        np.testing.assert_allclose(estimate.values,expected,atol=2e-12)
        np.testing.assert_allclose(estimate.metadata['spectral_concentration'],eigen[-1:-k-1:-1],atol=2e-12)

    def test_ar_psd_and_folding_retain_white_power_and_actual_order(self):
        source=Signal([3,0,2,-4,1,-2,2],metadata={'sample_rate_hz':16})
        variance=float(np.var(source.values.real))
        result=estimate_psd(PSDRequest(source,method='ar',ar_order=0,nfft=8,sidedness='one-sided'))
        np.testing.assert_allclose(result.values,(variance/16)*np.asarray([1,2,2,2,1]),rtol=2e-12)
        self.assertAlmostEqual(result.values.real.sum()*result.step,variance)
        self.assertEqual(result.metadata['a'],[1.])
        self.assertTrue(result.metadata['dc_line_excluded'])

    def test_lomb_improvement_matches_explicit_sine_regression_with_floating_mean(self):
        times=np.array([0,.32,.65,1.07,1.48,1.87,2.55,3.03,3.78])
        y=7+2.4*np.sin(math.tau*.8*times+.27)
        source=Signal(y)
        curve=lomb_periodogram(source,times,low=.2,high=1.4,points=13)
        residual_null=float(np.sum((y-y.mean())**2))
        expected=[]
        for f in curve.axis:
            angles=math.tau*f*times
            design=np.column_stack((np.ones(len(y)),np.cos(angles),np.sin(angles)))
            coefficient=np.linalg.lstsq(design,y,rcond=None)[0]
            expected.append(1-np.sum((y-design@coefficient)**2)/residual_null)
        np.testing.assert_allclose(curve.values,expected,atol=2e-12)
        self.assertAlmostEqual(curve.axis[np.argmax(curve.values.real)],.8)
        self.assertFalse(supported(curve))
        with self.assertRaisesRegex(ValueError,'Lomb–Scargle normalizado'):
            ictft(curve,0,1,16)

    def test_invalid_advanced_settings_and_timestamps_fail_with_observable_diagnostics(self):
        source=Signal([1,2,0,-1,4,3],metadata={'sample_rate_hz':6})
        for method,options in [('unknown',{}),('blackman_tukey',{'max_lag':6}),
                               ('blackman_tukey',{'max_lag':2,'nfft':4}),('multitaper',{'bandwidth':3}),
                               ('multitaper',{'tapers':7}),('ar',{'order':5}),('ar',{'rate':-1})]:
            with self.subTest(method=method,options=options),self.assertRaises(ValueError):
                advanced_density(source,method=method,**options)
        for sequence in ([0,1], [0,1,1,2,3,4], [0,1,2,3,4,5j]):
            with self.assertRaises(ValueError):
                lomb_periodogram(source,sequence,low=.1,high=.3)
        with self.assertRaises(ValueError):
            lomb_periodogram(Signal([1,1,1,1]),[0,1,2,3],low=.1,high=.3)
        with self.assertRaises(ResourceLimitError):
            advanced_density(source,method='multitaper',execution=ExecutionContext(max_work_bytes=1))
        with self.assertRaises(ValueError):
            estimate_psd(PSDRequest(source,method='blackman_tukey',tapers=2))

    def test_advanced_and_irregular_cli_preserve_scales_and_timestamps(self):
        source=Signal([1,2,0,-1,4,3],metadata={'sample_rate_hz':6})
        project=Project();key=project.add(source)
        times=[0,.1,.4,.7,1.,1.8]
        with TemporaryDirectory() as directory:
            base,out,coordinates=(Path(directory)/name for name in ('input.slproj','output.slproj','times.json'))
            session.save(base,project,session.empty_workspace())
            coordinates.write_text(json.dumps(times),encoding='utf-8')
            common=['--session',str(base),'--record',key,'--output',str(out)]
            scale=['--low','.25','--high','1','--points','13']
            original=coordinates.read_bytes()
            stderr=StringIO()
            with redirect_stderr(stderr):
                self.assertEqual(stochastic(['lomb','--times-file',str(coordinates),*scale,
                                             *common[:-1],str(coordinates)]),1)
                self.assertIn('archivo de tiempos',stderr.getvalue())
            self.assertEqual(coordinates.read_bytes(),original)
            for runner,args in [(main,['psd','--method','multitaper','--bandwidth','1.5','--tapers','2','--nfft','8']),
                                (stochastic,['lomb','--times-file',str(coordinates),*scale]),
                                (stochastic,['lomb','--times',json.dumps(times),*scale])]:
                stdout,stderr=StringIO(),StringIO()
                with redirect_stdout(stdout),redirect_stderr(stderr):
                    code=runner([*args,*common])
                self.assertEqual(code,0,stderr.getvalue())
                receipt=json.loads(stdout.getvalue())
                saved,_=session.load(out)
                result=saved.get(receipt['result_id'])
                self.assertEqual(saved.headers()[-1]['parents'],[key])
                if runner is stochastic:
                    self.assertEqual(result.metadata['timestamps_s'],times)
                    self.assertEqual(result.data_kind,'irregular_periodogram')
                else:
                    self.assertEqual(result.metadata['nfft'],8)
                    self.assertEqual(result.metadata['tapers'],2)
