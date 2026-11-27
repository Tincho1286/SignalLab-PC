"""Independent finite-sample spectral confidence oracles."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from signallab_pc import session
from signallab_pc.dsp_application import PSDRequest, estimate_psd
from signallab_pc.dsp_cli import main
from signallab_pc.execution import ExecutionContext, ResourceLimitError
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.statistical_spectra import white_noise_confidence
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
