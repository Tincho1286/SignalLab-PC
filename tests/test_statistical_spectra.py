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
from signallab_pc.fourier import require_complex_spectrum
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.spectral_measurements import supported
from signallab_pc.statistical_spectra import cross_spectra, white_noise_confidence
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
        with self.assertRaises(ValueError):
            require_complex_spectrum(result.cross)
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
