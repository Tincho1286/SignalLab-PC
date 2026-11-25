"""Independent oracles for filter studies and numeric MATLAB exchange."""
from pathlib import Path
import math
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from signallab_pc import course_tools as course
from signallab_pc.amplitude_design import design
from signallab_pc.filters import Transfer
from signallab_pc.jobs import OperationCancelled, observe
from signallab_pc.matlab_import import MatlabFile, expression, make_signal, vector


class FilterStudyContracts(unittest.TestCase):
    def test_windowed_spectrum_has_physical_phase_and_observed_clock(self):
        from signallab_pc.model import Signal
        samples = np.array([3+2j, -1, 4j, 7])
        source = Signal(samples, -5, metadata={'sample_rate_hz': 200, 'time_start_s': -.1})
        for window, weights in [('boxcar', np.ones(3)), ('kaiser', np.kaiser(3, 3.))]:
            with self.subTest(window=window):
                fft, dense, used, taper, response, coefficients = course.window_fft(
                    source, 3, 7, window, 3., 17)['signals']
                wanted = samples[:3]*weights
                np.testing.assert_allclose(taper.values, weights)
                np.testing.assert_allclose(used.values, wanted)
                self.assertEqual(used.metadata['time_start_s'], -.1)
                self.assertEqual(coefficients.metadata['input_clock']['sample_rate_hz'], 200)
                for result, values, indices in ((fft, wanted, range(-5,-2)), (dense, wanted, range(-5,-2)),
                                                  (response, weights, range(-5,-2))):
                    direct = [sum(x*np.exp(-1j*w*n) for n,x in zip(indices,values)) for w in result.axis]
                    np.testing.assert_allclose(result.values, direct, atol=4e-14)

    def test_window_validation_rejects_options_that_could_discard_samples(self):
        from signallab_pc.model import Signal
        source = Signal([1,2,3])
        for args, message in [((Signal([1], domain='continuous'),2,4,'hann',0,5), 'discreta'),
                              ((source,4,4,'hann',0,5), 'longitud'),
                              ((source,3,2,'hann',0,5), 'NFFT'),
                              ((source,3,4,'hann',0,1), 'dos frecuencias'),
                              ((source,3,4,'kaiser',-1,5), 'β'),
                              ((source,3,4,'kaiser',np.nan,5), 'β'),
                              ((Signal([1,2,3], units='bin k'),3,4,'hann',0,5), 'temporal')]:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError,message):
                course.window_fft(*args)

    def test_fft_and_dtft_retain_index_phase_beyond_exact_float_integers(self):
        from signallab_pc.model import Signal

        n0=2**53+11
        source=Signal([2+1j,-2,1j],n0)
        spectrum,dtft,*_=course.window_fft(source,3,8,'boxcar',0,17)['signals']
        for data,width in [(spectrum,8),(dtft,16)]:
            for position,value in enumerate(data.values):
                k=position-width//2
                exact=sum(x*np.exp(-2j*np.pi*((n0+step)*k%width)/width)
                          for step,x in enumerate(source.values))
                self.assertAlmostEqual(value,exact,places=13)

    def test_legacy_explicit_fir_length_preserves_the_selected_ideal_and_taper(self):
        for p,s,band in [([.7],[1.4],'lowpass'), ([1.4],[.7],'highpass'),
                         ([1.,1.8],[.5,2.5],'bandpass'), ([.5,2.5],[1.,1.8],'bandstop')]:
            with self.subTest(band=band):
                n = np.arange(21)-10
                cut = (np.array(p)+s)/2
                kernels = [w/np.pi*np.sinc(w*n/np.pi) for w in cut]
                center = (n==0).astype(float)
                ideal = {'lowpass': kernels[0], 'highpass': center-kernels[0],
                         'bandpass': kernels[-1]-kernels[0],
                         'bandstop': center-kernels[-1]+kernels[0]}[band]
                result = course.design_filter(p,s,.12,.12,'kaiser',taps=21,window='hann')
                h, taper, taps = (signal.values for signal in result['signals'])
                np.testing.assert_allclose(h,ideal,atol=2e-15)
                np.testing.assert_allclose(taper,np.hanning(21),atol=2e-15)
                raw = ideal*np.hanning(21)
                reference = {'lowpass': 0, 'highpass': np.pi, 'bandpass': np.mean(cut), 'bandstop': 0}[band]
                np.testing.assert_allclose(taps,raw/np.dot(raw,np.cos(n*reference)),atol=2e-14)
                self.assertEqual(result['specifications']['kind'],band)

    def test_fir_search_compares_shorter_odd_lengths_and_preserves_failure(self):
        p,s = [2.3],[.6]
        result = course.design_filter(p,s,.2,.2,'kaiser',window='hamming',search=31)
        h = result['systems'][0].b
        self.assertEqual(len(h)%2,1)
        omega = np.linspace(0,np.pi,4097)
        mag = abs(np.exp(-1j*np.outer(omega,np.arange(len(h))))@h)
        self.assertLessEqual(max(mag[omega<=s[0]]),.2001)
        self.assertGreaterEqual(min(mag[omega>=p[0]]),.7999)
        for bound in (1,2):
            with self.subTest(bound=bound), self.assertRaisesRegex(ValueError, 'búsqueda|longitud'):
                course.design_filter(p,s,.08,.08,'kaiser',window='hamming',search=bound)
        def cancel(fraction):
            if fraction is not None:
                raise OperationCancelled()
        with observe(cancel),self.assertRaises(OperationCancelled):
            course.design_filter(p,s,.2,.2,'kaiser',window='hamming',search=31)

    def test_legacy_auto_standard_window_delegates_to_minimum_length_design(self):
        p,s=[.7],[1.45]
        model=course.design_filter(p,s,.13,.15,'kaiser',window='hamming')
        direct=design(p,s,.13,.15,'kaiser',window='hamming')
        np.testing.assert_array_equal(model['systems'][0].b,direct['systems'][0].b)
        self.assertTrue(model['specification_met'])

    def test_filter_specification_validation_identifies_the_wrong_parameter(self):
        for p,s,dp,ds,method,opts,error in [
            ([float('nan')],[1],.1,.1,'butter',{},'finitos'),
            ([1],[float('inf')],.1,.1,'butter',{},'finitos'),
            ([1,2],[1],.1,.1,'butter',{},'bordes'),
            ([1,2,3],[1,2,3],.1,.1,'butter',{},'bordes'),
            ([0],[1],.1,.1,'butter',{},'bordes'),
            ([1],[0],.1,.1,'butter',{},'bordes'),
            ([np.pi],[1],.1,.1,'butter',{},'bordes'),
            ([1],[np.pi],.1,.1,'butter',{},'bordes'),
            ([1],[1],.1,.1,'butter',{},'transición'),
            ([1,2],[.5,1.5],.1,.1,'butter',{},'inválidos'),
            ([1],[2],0,.1,'butter',{},'tolerancias'),
            ([1],[2],.1,1,'butter',{},'tolerancias'),
            ([1],[2],.1,.1,'butter',{'period':0},'positivo'),
            ([1],[2],.1,.1,'butter',{'period':float('nan')},'finito'),
            ([1],[2],.1,.1,'unknown',{},'Método'),
            ([1],[2],.7,.7,'butter',{},'atenuación'),
            ([1],[2],.1,.1,'kaiser',{'window':'unknown'},'Ventana'),
            ([1],[2],.1,.1,'kaiser',{'search':-1},'cota'),
            ([1],[2],.1,.1,'kaiser',{'taps':-1},'longitud'),
            ([2],[1],.1,.1,'kaiser',{'taps':12},'impar'),
        ]:
            with self.subTest(p=p,s=s,method=method,opts=opts,error=error),self.assertRaisesRegex(ValueError,error):
                course.design_filter(p,s,dp,ds,method,**opts)

    def test_iir_comparison_meets_dense_passband_and_stopband_oracle(self):
        features = course.compare_iir([.6],[1.4],.12,.08)
        self.assertTrue(features['comparison'])
        self.assertEqual(len(features['systems']),4)
        self.assertEqual(features['specifications']['kind'],'lowpass')
        grid=np.linspace(0,np.pi,3001)
        zinv=np.exp(-1j*grid)
        for system in features['systems']:
            with self.subTest(system=system.name):
                response=np.ones(len(grid),complex)
                for b0,b1,b2,a0,a1,a2 in system.sos:
                    response*=(b0+b1*zinv+b2*zinv**2)/(a0+a1*zinv+a2*zinv**2)
                np.testing.assert_allclose(system.response(grid),response,atol=2e-14)
                self.assertGreaterEqual(min(abs(response[grid<=.6])),.88-1e-10)
                self.assertLessEqual(max(abs(response[grid>=1.4])),.08+1e-10)

    def test_analog_prototypes_obey_the_bilinear_map_or_the_sampled_impulse(self):
        dt=.25
        for method in ('bilinear','impulse'):
            with self.subTest(method=method):
                result,analog=course.design_filter([.5],[1.65],.23,.15,method,period=dt)['systems']
                self.assertEqual(result.sample_period_s,dt)
                if method=='bilinear':
                    freqs=np.linspace(0,2,33)
                    np.testing.assert_allclose(result.response(freqs),analog.response(2/dt*np.tan(freqs/2)),atol=2e-12)
                else:
                    from scipy.signal import residue
                    residues,poles,direct=residue(analog.b,analog.a)
                    self.assertEqual(len(direct),0)
                    values=dt*np.exp(np.arange(8)[:,None]*dt*poles)@residues
                    n=np.arange(8)
                    observed=course.inverse_z_contour(result,'causal',1,0,len(n),256)['signals'][0]
                    np.testing.assert_allclose(observed.values,values,atol=1e-12)

    def test_impulse_inverse_branches_sample_the_same_digital_pole(self):
        dt=.5
        for pole, amplitude in ((.4,1),(-.4,1),(.3+.2j,1+.5j),(.3-.2j,1-.5j)):
            with self.subTest(pole=pole):
                digital=Transfer([amplitude],[1,-pole],roc={'mode':'radius','radius':.9})
                candidates=course.convert_system(digital,dt,'impulse_inverse')['systems']
                self.assertEqual(len(candidates),2)
                for candidate in candidates:
                    self.assertAlmostEqual(candidate.roc['sigma'],math.log(.9)/dt)
                    _,poles=candidate.poles_zeros()
                    np.testing.assert_allclose(np.exp(dt*poles),pole,atol=1e-13)
                    # The initial value of these strictly proper candidates is b0/a0.
                    self.assertAlmostEqual(dt*candidate.b[0]/candidate.a[0],amplitude)

    def test_impulse_conversion_checks_direction_distribution_and_repeated_poles(self):
        analog=Transfer([1],[1,2],'analog')
        for model,dt,method,reason in [
            (analog,0,'impulse','positivo'), (analog,float('inf'),'bilinear','finito'),
            (Transfer([1],[1]),1,'impulse','continua'),
            (Transfer([1j],[1,2],'analog'),1,'impulse','reales'),
            (Transfer([1],[1,2j],'analog'),1,'bilinear','reales'),
            (Transfer([3],[1],'analog'),1,'impulse','Dirac'),
            (analog,1,'impulse_inverse',r'H\(z\)'), (analog,1,'inverse','discreta'),
            (Transfer([1],[1,.3],advance=1),1,'impulse_inverse','avances'),
            (Transfer([1,.9],[1,.3]),1,'impulse_inverse','polinómica'),
            (Transfer([1],[1,-.5,.0625]),1,'impulse_inverse','simples'),
        ]:
            with self.subTest(method=method,reason=reason),self.assertRaisesRegex(ValueError,reason):
                course.convert_system(model,dt,method)
        zero=course.convert_system(Transfer([0],[1],'analog'),1.,'impulse')['systems'][0]
        np.testing.assert_array_equal(zero.response([0,1]),[0,0])

    def test_impulse_inverse_rejects_true_multiplicity_and_keeps_exact_cancellation(self):
        for denominator in ([1,-.5,.0625], [1,-.75,.1875,-.015625]):
            with self.subTest(denominator=denominator), self.assertRaisesRegex(ValueError,'polos múltiples'):
                course.convert_system(Transfer([1],denominator),.5,'impulse_inverse')
        model=Transfer([1,-.25],[1,-.5,.0625])
        simple=course.convert_system(model,.5,'impulse_inverse')['systems'][0]
        np.testing.assert_allclose(simple.response([0,1]),2/(2*math.log(4)+1j*np.array([0,1])),atol=1e-13)

    def test_zero_system_and_unknown_mapping_methods_do_not_select_other_models(self):
        original=Transfer([0],[1,-.5,.0625],roc={'mode':'radius','radius':1})
        output=course.convert_system(original,.5,'impulse_inverse')
        zero,=output['systems']
        self.assertEqual(zero.domain,'analog')
        self.assertEqual(zero.roc,{'mode':'line','sigma':0.})
        np.testing.assert_array_equal(zero.response([0,1,10]),[0,0,0])
        with self.assertRaisesRegex(ValueError,'Método de conversión'):
            course.convert_system(original,.5,'kaiser')
        for method in ('inverse','bilinear_inverse'):
            same=course.convert_system(original,.5,method)['systems'][0]
            np.testing.assert_array_equal(same.response([0,1]),[0,0])

    def test_impulse_roc_exchanges_line_and_radius_only_when_representable(self):
        original=Transfer([1],[1,2],'analog',roc={'mode':'line','sigma':-1})
        result=course.convert_system(original,.25,'impulse')['systems'][0]
        self.assertAlmostEqual(result.roc['radius'],math.exp(-.25))
        for sigma in (-1000.,1000.):
            with self.subTest(sigma=sigma),self.assertRaisesRegex(ValueError,'rango'):
                course.impulse_roc(Transfer([1],[1,2],'analog',roc={'mode':'line','sigma':sigma}),1.)
        self.assertEqual(course.impulse_roc(Transfer([1],[1,2],'analog',roc={'mode':'left'}),1.),
                         {'mode':'left'})

    def test_inverse_z_geometric_coefficients_depend_on_the_selected_contour(self):
        for mode,radius,decay in [('causal',1,.5),('anticausal',1,.5),('stable',1,2.),('manual',.7,.5)]:
            with self.subTest(mode=mode):
                model=Transfer([1],[1,-decay])
                result=course.inverse_z_contour(model,mode,radius,-5,11,512)['signals'][0]
                n=np.arange(-5,6,dtype=float)
                positive=result.metadata['radius']>decay
                expected=np.where(n>=0,decay**n,0) if positive else np.where(n<0,-decay**n,0)
                np.testing.assert_allclose(result.values,expected,atol=1e-13)
                self.assertEqual(result.metadata['roc_outer'],None if positive else decay)
                self.assertEqual(result.origin,-5)
        for model,mode,r,lo,count,points,reason in [
            (Transfer([1],[1],'analog'),'manual',1,0,1,16,'discreta'),
            (Transfer([1],[1]),'anticausal',1,0,1,16,'interior'),
            (Transfer([0,1],[1]),'anticausal',1,0,1,16,'interior'),
            (Transfer([1],[1,-1]),'stable',1,0,1,16,'polo'),
            (Transfer([1],[1]),'manual',0,0,1,16,'radio'),
            (Transfer([1],[1]),'manual',float('inf'),0,1,16,'radio'),
            (Transfer([1],[1]),'manual',1,0,0,16,'puntos'),
            (Transfer([1],[1]),'manual',1,0,9,16,'puntos'),
            (Transfer([1],[1]),'manual',1,8,1,16,'mitad'),
            (Transfer([1],[1]),'unknown',1,0,1,16,'contorno no admitida'),
        ]:
            with self.subTest(mode=mode,reason=reason),self.assertRaisesRegex(ValueError,reason):
                course.inverse_z_contour(model,mode,r,lo,count,points)

    def test_frequency_mappings_check_units_branches_and_invalid_periods(self):
        for method,direction,w,analog,T,k,value,unit in [
            ('bilinear','to_analog',np.pi/2,0,.25,0,8.,'rad/s'),
            ('bilinear','to_digital',0,8,.25,0,np.pi/2,'rad/muestra'),
            ('bilinear','period',np.pi/2,8,1,0,.25,'s'),
            ('impulse','to_analog',np.pi/2,0,.25,-1,-6*np.pi,'rad/s'),
            ('impulse','to_digital',0,4*np.pi,.25,0,-np.pi,'rad/muestra'),
            ('impulse','period',np.pi/2,2*np.pi,1,1,1.25,'s'),
        ]:
            with self.subTest(method=method,direction=direction):
                report=course.frequency_mapping(w,analog,T,method,direction,k)['report']
                self.assertIn(f'Resultado: {value:.12g} {unit}',report)
        for args,error in [
            ((0,2,0,'bilinear','to_digital',0),'positivo'),
            ((0,2,np.nan,'impulse','to_digital',0),'finito'),
            ((0,2,1,'bad','to_digital',0),'Método'),
            ((1,2,1,'kaiser','to_analog',0),'Método'),
            ((1,2,1,'impulse','unknown',0),'Sentido'),
            ((1,2,1,'impulse','to_analog',.5),'entero'),
            ((np.pi,1,1,'bilinear','to_analog',0),'requiere'),
            ((1,0,1,'bilinear','period',0),'distinta'),
            ((1,0,1,'impulse','period',0),'distinta'),
            ((-1,1,1,'impulse','period',0),'combinación'),
            ((0,1e308,10,'bilinear','to_digital',0),'rango'),
            ((np.nan,1,1,'impulse','to_analog',0),'finito'),
        ]:
            with self.subTest(args=args),self.assertRaisesRegex(ValueError,error):
                course.frequency_mapping(*args)

    def test_gain_normalization_accepts_extreme_linear_magnitudes_when_coefficients_fit(self):
        tiny=float(np.nextafter(0.,1.))
        for coefficient,target,answer in [
            (1.6e308+1.6e308j,1.,(1+1j)/np.sqrt(2)),
            (tiny,1.,1.),
            (1e300,tiny,tiny),
        ]:
            with self.subTest(coefficient=coefficient, target=target):
                output=course.normalize_gain(Transfer([coefficient],[1]),0.,target)
                system,=output['systems']
                if target==tiny:
                    self.assertEqual(system.b[0],tiny)
                else:
                    np.testing.assert_allclose(system.b,[answer],atol=1e-14)
                self.assertIn(' × 2^',output['report'])
        original=Transfer.from_sos([[.25,0,0,1,-.5,0]],sample_period_s=.125)
        result=course.normalize_gain(original,0.,2.)['systems'][0]
        self.assertEqual(result.sample_period_s,.125)
        np.testing.assert_array_equal(result.sos[0],[1,0,0,1,-.5,0])
        for model,target,reason in [
            (original,0,'objetivo'),
            (Transfer([1,-1],[1]),1.,'cero'),
            (Transfer([1],[1,-1]),1.,'singular'),
        ]:
            with self.subTest(reason=reason),self.assertRaisesRegex(ValueError,reason):
                course.normalize_gain(model,0.,target)


class MatlabNumericContracts(unittest.TestCase):
    def test_matrix_subset_retains_matlab_complex_and_shape_semantics(self):
        A=np.array([[1+2j,4],[3,2j]])
        for source,expected in [
            ("A'",A.conj().T),("A.'",A.T),("2*A",2*A),("A*[1]",A),
            ("A.*[1 2]", A*np.array([1,2])), ("[3 6]./[2 3]",[[1.5,2]]),
            ("A/2",A/2),("A-1",A-1), ("+2.5+.5j",2.5+.5j),
            ("[-4 -1 4].^0.5",[[2j,1j,2]]),("[-4 -1].^2",[[16,1]]),
            ("complex([1,2],[3,4])",[[1+3j,2+4j]]),("0:.1:.25",[[0,.1,.2]]),
            ("3:-2:-2",[[3,1,-1]]),("4:1",np.empty((1,0))),
            ("linspace(-1,1,3)",[[-1,0,1]]),("linspace(0,1)",np.linspace(0,1,100)[None,:]),
            ("ones(2)",[[1,1],[1,1]]),("zeros(2,1)",[[0],[0]]),
            ("[[1;2] [3;4]]",[[1,3],[2,4]]),("[]",np.empty((1,0))),
            ("[1 2] == [1 3]",[[True,False]]),("[1 2] ~= [1 3]",[[False,True]]),
            ("1<2",True),("3<=3",True),("3>2",True),("2>=3",False),
            ("sqrt(-1)",1j),("i+j",2j),("pi/2",np.pi/2),
        ]:
            with self.subTest(source=source):
                np.testing.assert_allclose(expression(source,{'A':A}),expected,atol=2e-15)

    def test_numeric_matlab_dialect_returns_feedback_for_unsupported_inputs(self):
        for source,reason in [
            ('A*A','multiplicación'),('A/A','división'),('A^2','potencia'),
            ('unknown(2)','Expresión no admitida'),('x','no definida'),('1 2','inesperado'),
            ('(1','incompleta'),('[[1;2] 3]','horizontal'),('[1 2;3]','vertical'),
            ('ones(1.5)','Tamaño'),('linspace(0,1,2.5)','Cantidad'),
            ('1:0:3','paso cero'),('-1e308:1e308','rango numérico'),
        ]:
            with self.subTest(source=source),self.assertRaisesRegex(ValueError,reason):
                expression(source,{'A':np.arange(4).reshape(2,2)})

    def test_numeric_script_overwrites_assignments_and_delivers_exact_axis(self):
        with TemporaryDirectory() as d:
            path=Path(d)/'samples.m'
            path.write_text('clear all; clc; close all; A=[1 2;3 4]; A=A*2; n=[-2; -1]; x=[1 ...\n 2]; empty=[];',
                            encoding='utf-8')
            data=MatlabFile(path)
            self.assertEqual(sorted(data.entries),['A','n','x'])
            signal=make_signal(data,'A',1,'discrete',axis_name='n')
            np.testing.assert_array_equal(signal.axis,[-2,-1])
            np.testing.assert_array_equal(signal.values,[4,8])
            self.assertEqual(signal.metadata['column'],2)
            self.assertEqual(signal.metadata['axis_variable'],'n')
            self.assertEqual(signal.metadata['source_file'],'samples.m')
            for source,reason in [('clc;','no define variables'),('A=1/0;','Variable A'),
                                   ('A=1e999;','finito'),('for i=1:2','no admitida')]:
                path.write_text(source,encoding='utf-8')
                with self.subTest(source=source), self.assertRaisesRegex(ValueError,reason):
                    MatlabFile(path)

    def test_mat_axis_validation_preserves_integer_precision_and_channel_selection(self):
        class Source:
            path = Path('clock.mat')
            def __init__(self, axis):
                self.axis=axis
            def load(self,name):
                if name=='axis':
                    return self.axis
                return np.array([[2,3],[4,5],[6,7]])
        exact=np.arange(3,dtype=np.int64)+2**53+3
        imported=make_signal(Source(exact),'x',0,'discrete','axis')
        np.testing.assert_array_equal(imported.axis,exact)
        np.testing.assert_array_equal(imported.values,[2,4,6])
        timed=make_signal(Source(np.array([-.3,.2,.7])),'x',1,'continuous','axis')
        self.assertAlmostEqual(timed.step,.5)
        self.assertAlmostEqual(timed.origin,-.3)
        for axis,domain,reason in [
            (np.ones((2,2,2)),'discrete','vector'),(np.ones((2,2)),'continuous','vector'),
            (np.array([1,2]),'discrete','tantas'),
            (np.array([1+1j,2,3]),'discrete','real'),
            (np.array([1,np.inf,3]),'discrete','finito'),
            (np.array([1.5,2.5,3.5]),'discrete','consecutivos'),
            (np.array([2**63-1]*3,dtype=np.int64),'discrete','64 bits'),
            (np.array([1,2,4]),'continuous','uniforme'),
        ]:
            with self.subTest(axis=axis,domain=domain),self.assertRaisesRegex(ValueError,reason):
                make_signal(Source(axis),'x',0,domain,'axis')
        for arr,column,reason in [(np.ones((1,2,3)),0,'dimensiones'),(np.array([]),0,'muestras'),
                                  (np.ones((2,2)),2,'columna')]:
            with self.subTest(reason=reason),self.assertRaisesRegex(ValueError,reason):
                vector(arr,column)
        for domain,step,reason in [('unknown',1,'Dominio'),('discrete',.1,'exactamente'),
                                   ('continuous',0,'positivo'),('frequency',np.nan,'finito')]:
            with self.subTest(domain=domain,step=step),self.assertRaisesRegex(ValueError,reason):
                make_signal(Source([]),'x',0,domain,step=step)
