from cmath import exp
from math import tau
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np
from numpy.testing import assert_allclose

from signallab_pc import session
from signallab_pc.dft_application import DFTRequest, calculate_dft
from signallab_pc.dsp_application import (
    FIRDesignRequest, FIRRequest, IDFTRequest, PSDRequest, ResampleRequest,
    apply_fir, calculate_idft, design_fir, estimate_psd, resample, store_fir_design, store_signal,
)
from signallab_pc.execution import ExecutionContext
from signallab_pc.filters import Transfer
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.resources import ResourceLimitError


class DSPApplicationTests(unittest.TestCase):
    def test_idft_against_direct_positive_exponents_and_roundtrip(self):
        coeff = Signal([1j, 2, -1, 3j], units='bin k')
        direct = [sum(v*exp(1j*tau*k*n/4) for k,v in enumerate(coeff.values))/4 for n in range(4)]
        assert_allclose(calculate_idft(IDFTRequest(coeff)).values, direct, atol=1e-14)
        signal = Signal([1+2j, -2, .5j], -7, units='índice',
                        metadata={'sample_rate_hz':16, 'time_start_s':-.25, 'amplitude_units':'V'})
        result = calculate_idft(IDFTRequest(calculate_dft(DFTRequest(signal)).spectrum))
        assert_allclose(result.values, signal.values, atol=1e-14)
        self.assertEqual((result.origin, result.units, result.metadata['sample_rate_hz']), (-7, 'índice', 16))
        self.assertEqual(result.metadata['amplitude_units'], 'V')

    def test_fir_design_and_causal_response_against_analytic_vectors(self):
        result = design_fir(FIRDesignRequest('lowpass', 3, .25, window='boxcar', sample_period_s=.125))
        assert_allclose(result.transfer.b, [1/np.pi,.5,1/np.pi], atol=1e-15)
        response = result.transfer.response(np.array([0., np.pi]))
        assert_allclose(response, [.5 + 2/np.pi, 2/np.pi - .5], atol=1e-15)
        impulse = Signal([1,0,0], 3, metadata={'sample_rate_hz':8, 'time_start_s':.75})
        output = apply_fir(FIRRequest(impulse, result.transfer))
        assert_allclose(output.values, result.transfer.b)
        self.assertEqual((output.origin, output.metadata['time_start_s']), (3,.75))
        signal = Signal([1+2j, -3], -2)
        model = Transfer([2,-1j],[1])
        assert_allclose(apply_fir(FIRRequest(signal,model,'full')).values, [2+4j,-4-1j,3j])

    def test_resampling_against_explicit_kaiser_convolution(self):
        source = Signal([1,2j,-1,.5], -3, metadata={'sample_rate_hz':12,'time_start_s':-.25})
        result = resample(ResampleRequest(source, 4, 6, half_width=2, beta=2, return_filter=True))
        L,M,half = 2,3,6
        n = np.arange(-half,half+1)
        window = np.i0(2*np.sqrt(1-(n/half)**2))/np.i0(2)
        h = window*np.sinc(n/M)/M
        h *= L/np.sum(h)
        direct = [sum(x*h[half+m*M-k*L] for k,x in enumerate(source.values) if abs(m*M-k*L)<=half)
                  for m in range(3)]
        assert_allclose(result.signal.values, direct, atol=1e-14)
        assert_allclose(result.antialias.b, h, atol=1e-15)
        self.assertEqual((result.signal.origin,result.signal.metadata['sample_rate_hz'],
                          result.signal.metadata['time_start_s']), (0,8,-.25))
        n=np.arange(512)
        high=Signal(np.exp(1j*1.5*np.pi*n/2),metadata={'sample_rate_hz':12})
        attenuated=resample(ResampleRequest(high,1,2)).signal.values[32:-32]
        self.assertLess(float(np.max(np.abs(attenuated))),.01)

    def test_psd_power_folding_for_tones_constants_and_seeded_noise(self):
        rng = np.random.default_rng(917)
        for size in (9,10):
            for samples in (np.ones(size), np.cos(tau*2*np.arange(size)/size), rng.normal(size=size)):
                source = Signal(samples, 5, metadata={'sample_rate_hz': 16,'amplitude_units':'mV'})
                out=estimate_psd(PSDRequest(source, method='periodogram', window='boxcar', sidedness='one-sided'))
                expected=np.array([abs(sum(x*exp(-1j*tau*k*n/size) for n,x in enumerate(samples)))**2/(16*size)
                                   for k in range(size//2+1)])
                expected[1:(None if size%2 else -1)] *= 2
                assert_allclose(out.values.real, expected, atol=1e-14)
                self.assertAlmostEqual(float(out.values.real.sum()*out.step), float(np.mean(samples**2)))
                self.assertEqual(out.metadata['density_units'],'mV²/Hz')
        x=Signal([1e150,1e150],metadata={'sample_rate_hz':4})
        assert_allclose(estimate_psd(PSDRequest(x,method='periodogram',window='boxcar')).values.real,[0,5e299])

    def test_psd_small_finite_rate_preserves_centered_bins(self):
        rate = 1e-309
        source = Signal([1e-160, -1e-160, 1e-160, -1e-160])
        out = estimate_psd(PSDRequest(source, rate, method='periodogram', window='boxcar'))
        assert_allclose(out.axis, [-rate/2, -rate/4, 0, rate/4], rtol=0, atol=1e-323)
        # Only Nyquist is nonzero. Compute 4*a²/Fs without underflow in a².
        assert_allclose(out.values, [4e-11, 0, 0, 0], rtol=2e-14, atol=0)
        with self.assertRaisesRegex(ValueError, 'separación entre bins'):
            estimate_psd(PSDRequest(source, 5e-324, method='periodogram', window='boxcar'))

    def test_bartlett_matches_disjoint_dfts_and_preserves_density_calibration(self):
        source_data = np.array([1,-2,7,4,2,1,-2,1,3,4,9,8,1000.])
        fs = 24.
        for length in (5,6):
            count = len(source_data)//length
            bins = range(-(length//2),(length+1)//2)
            blocks = np.split(source_data[:count*length],count)
            expected = [sum(abs(sum(v*exp(-1j*tau*k*n/length) for n,v in enumerate(block)))**2
                            for block in blocks)/(fs*length*count) for k in bins]
            source = Signal(source_data,origin=7,metadata={'sample_rate_hz':fs,'amplitude_units':'mV'})
            spec = estimate_psd(PSDRequest(source,method='bartlett',segment=length,window='kaiser',overlap=20))
            assert_allclose(spec.axis,np.asarray(list(bins))*fs/length,atol=1e-14)
            assert_allclose(spec.values,expected,atol=1e-14)
            self.assertEqual(spec.metadata['window'],'boxcar')
            self.assertEqual(spec.metadata['overlap'],0)
            self.assertEqual(spec.metadata['unused_tail'],len(source_data)-count*length)
            self.assertEqual(spec.metadata['density_units'],'mV²/Hz')
            folded = estimate_psd(PSDRequest(source,method='bartlett',segment=length,sidedness='one-sided'))
            self.assertAlmostEqual(float(spec.values.real.sum()*spec.step),float(np.mean(source_data[:count*length]**2)))
            self.assertAlmostEqual(float(folded.values.real.sum()*folded.step),float(spec.values.real.sum()*spec.step))

    def test_invalid_constraints_and_budgets(self):
        x = Signal([1j, 1], metadata={'sample_rate_hz':8})
        with self.assertRaisesRegex(ValueError,'unilateral'):
            estimate_psd(PSDRequest(x, method='periodogram', sidedness='one-sided'))
        with self.assertRaisesRegex(ValueError,'reloj'):
            resample(ResampleRequest(x, 1, 2, rate=4))
        with self.assertRaisesRegex(ValueError,'FIR'):
            apply_fir(FIRRequest(x,Transfer([1],[1,.5])))
        with self.assertRaises(ResourceLimitError):
            apply_fir(FIRRequest(x,Transfer([1],[1])), ExecutionContext(max_work_bytes=1))

    def test_design_specification_and_result_survive_session(self):
        project = Project()
        design = design_fir(FIRDesignRequest('lowpass', 5, .15))
        model_id, spec = store_fir_design(project, design)
        source = Signal([1,0,0])
        source_id = project.add(source)
        filtered = apply_fir(FIRRequest(source, design.transfer))
        result_id = store_signal(project, filtered,parents=(source_id,model_id))
        with TemporaryDirectory() as folder:
            path=Path(folder)/'session.json'
            session.save(path,project,session.empty_workspace())
            restored,_=session.load(path)
            self.assertEqual(restored.get(spec)['f1'],.15)
            assert_allclose(restored.get(model_id).b,design.transfer.b)
            self.assertEqual(restored.headers()[-1]['parents'],[source_id,model_id])
            self.assertEqual(restored.get(result_id).metadata['core_provenance']['operation'],'fir_apply')
