"""Independent reference contracts for the main mathematical tool families."""
import unittest
from fractions import Fraction
import numpy as np
import sympy as sp
from numpy.testing import assert_allclose
from signallab_pc.scalar_expression import exact_constant,constant_value,real_value,integer_value
from signallab_pc.symbolic import execute,parse,N,T,S,Z
from signallab_pc.cas_engine import restore
from signallab_pc.model import Signal
from signallab_pc.filters import Transfer,from_poles_zeros,bilinear


class ScalarContracts(unittest.TestCase):
    def test_exact_arithmetic_before_projection(self):
        for text,want in [('10^20+1-10^20',1),('0.1+0.2-0.3',0),('sin(pi)',0),('cos(pi/2)',0),('floor(2^3/3)',2),('ceil(5/2)',3)]:
            with self.subTest(source=text):self.assertEqual(constant_value(text),want)
        self.assertEqual(exact_constant('1e-3'),sp.Rational(1,1000))
        self.assertEqual(integer_value('10^20+1'),10**20+1)

    def test_complex_numbers_and_branches(self):
        for text,want in [('sqrt(-1)',1j),('log(-1)',1j*np.pi),('3+2j',3+2j),('(1+i)^2',2j),('asin(2)',np.pi/2-1j*np.arccosh(2))]:
            with self.subTest(source=text):assert_allclose(constant_value(text),want,atol=1e-15)
        self.assertEqual(real_value('sqrt(-1)^2'),-1)
        with self.assertRaises(ValueError):real_value('sqrt(-1)')

    def test_numeric_array_functions_match_scalar_principal_values(self):
        from signallab_pc.engine import evaluate_expression,sequence_from_expression
        axis=np.array([-2.,-.5,0.,.5,2.])
        for function in ('asin','acos','floor','ceil','heaviside'):
            if function=='heaviside':source='heaviside(n^2-1)'
            elif function in ('floor','ceil'):source=function+'(n^2/3)'
            else:source=function+'(n)'
            actual=evaluate_expression(source,axis)
            want=[complex(sp.N(parse(source).subs(N,sp.Rational(str(v))),18)) for v in axis]
            assert_allclose(actual,want,atol=1e-14)
        assert_allclose(evaluate_expression('n^2%3',np.arange(5)),[0,1,1,0,1])
        assert_allclose(evaluate_expression('1 if 2 > 1 else 0',axis),np.ones(5))
        assert_allclose(evaluate_expression('where(n<0, 1, 0)',axis),[1,1,0,0,0])
        assert_allclose(evaluate_expression('impulse(0)',axis),np.ones(5))
        assert_allclose(evaluate_expression('10^20+1-10^20',axis),np.ones(5))
        with self.assertRaises(ValueError):evaluate_expression('floor(i*n)',axis)
        with self.assertRaises(ValueError):evaluate_expression('1 if i*n<0 else 0',axis)
        with self.assertRaises(ValueError):sequence_from_expression('n',2**53+1,2)

    def test_constants_cannot_hide_variables_or_nonfinite_values(self):
        for text in ('n','t','k','s','z','w','tau','a','1/0','log(0)','oo','1e400','1e-400','True'):
            with self.subTest(source=text):
                with self.assertRaises(ValueError):constant_value(text)
        for text in ('2.5','9007199254740993.1','True'):
            with self.assertRaises(ValueError):integer_value(text)

    def test_symbolic_coefficients_reserve_all_axis_names(self):
        self.assertEqual(exact_constant('K/3',parameters=True),sp.Symbol('K')/3)
        for axis in ('n','t','s','z','w','tau','k'):
            with self.subTest(axis=axis):
                with self.assertRaises(ValueError):execute(dict(operation='system_analysis',domain='digital',b=[axis],a=['1']))


class SystemContracts(unittest.TestCase):
    def formula(self,text,domain='digital'):
        result=execute(dict(operation='system_formula',domain=domain,expression=text))
        return Transfer([complex(*v) for v in result['numeric_b']],[complex(*v) for v in result['numeric_a']],domain,advance=result.get('advance',0))

    def test_formula_coefficients_and_roots_share_same_response(self):
        w=np.array([-.7,0.,.3,1.9]);z=np.exp(1j*w)
        models=[self.formula('(z+0.25)/(z-0.5)'),Transfer([1,.25],[1,-.5]),from_poles_zeros([-.25],[.5])]
        for model in models:assert_allclose(model.response(w),(z+.25)/(z-.5),atol=2e-14)
        analog=self.formula('(s+2)/(s+3)','analog')
        assert_allclose(analog.response(w),(1j*w+2)/(1j*w+3),atol=1e-14)

    def test_temporal_response_with_history_and_nonunit_a0(self):
        y=Transfer([2],[2,-1]).apply(Signal([0]*6,-4),previous_outputs=[4])
        assert_allclose(y.values,2*.5**np.arange(6));self.assertEqual(y.origin,-4)

    def test_delay_and_advance_have_opposite_phase_and_group_delay(self):
        w=np.array([0.,.2,1.,np.pi])
        for power in (-3,3):
            h=self.formula(f'z^({power})')
            assert_allclose(h.response(w),np.exp(1j*w*power),atol=2e-15)
            assert_allclose(h.group_delay(w),-power,atol=1e-14)

    def test_first_order_analog_group_delay(self):
        w=np.array([0.,.5,2.,20.]);h=Transfer([1],[1,2],'analog')
        assert_allclose(h.response(w),1/(2+1j*w),atol=1e-15)
        assert_allclose(h.group_delay(w),2/(4+w*w),atol=1e-15)

    def test_linear_fir_group_delay_and_nyquist_zero(self):
        h=Transfer([1,2,1],[1]);w=np.array([0.,.7,1.4,np.pi])
        assert_allclose(h.group_delay(w[:-1]),1,atol=1e-15)
        self.assertTrue(np.isnan(h.group_delay(w)[-1]))

    def test_origins_in_poles_and_zeros(self):
        zeros,poles=Transfer([0,0,1],[1]).poles_zeros()
        self.assertEqual(len(zeros),0);assert_allclose(poles,[0,0])
        zeros,poles=from_poles_zeros([0,0],[]).poles_zeros()
        assert_allclose(zeros,[0,0]);self.assertEqual(len(poles),0)

    def test_true_pole_is_not_a_removable_value(self):
        w=np.array([0.,.1])
        assert_allclose(Transfer([1,-1],[1,-1]).response(w),[1,1])
        self.assertTrue(np.isnan(Transfer([1,-1+1e-10],[1,-1]).response(w)[0]))

    def test_bilinear_first_order_and_frequency_warp(self):
        period=.2;h=bilinear(Transfer([1],[1,2],'analog'),period);w=np.array([0.,.2,1.,2.])
        assert_allclose(h.b,[1/12,1/12],atol=1e-15);assert_allclose(h.a,[1,-2/3],atol=1e-15)
        assert_allclose(h.response(w),1/(2+1j*2/period*np.tan(w/2)),atol=1e-14)

    def test_numeric_normalization_cannot_erase_coefficient(self):
        with self.assertRaisesRegex(ValueError,'coeficientes no nulos'):Transfer([1e-300],[1e300])
        assert_allclose(Transfer([1e-200],[1e100]).b,[1e-300],rtol=1e-14,atol=0)


class EquationContracts(unittest.TestCase):
    def difference(self,source='0',**extra):
        from signallab_pc.difference_equations import solve
        return solve(dict(expression=source,coefficients=['1','-1/2'],rest=False,initial=['4'],start=0,count=8,**extra))

    def test_difference_closed_formula_matches_original_equation_and_history(self):
        from signallab_pc.difference_equations import solve
        for start in (-3,2):
            r=solve(dict(expression='1',coefficients=['2','-1'],rest=False,initial=['3'],start=start,count=8))
            y=restore(r['cas_encoded']);previous=sp.Integer(3)
            for n in range(start,start+8):
                current=sp.simplify(y.subs(N,n));self.assertEqual(sp.simplify(2*current-previous-1),0);previous=current
            assert_allclose(np.array(r['numeric_samples'])[:,0],[float(y.subs(N,n)) for n in range(start,start+8)])
            self.assertLess(r['residual_check']['normalized_max'],1e-14)

    def test_difference_preserves_removable_sample_and_explicit_value(self):
        from signallab_pc.difference_equations import solve
        for source,initial_value in [('sin(pi*n)/(pi*n)',1),('Piecewise((7,n==0),(sin(pi*n)/(pi*n),True))',7)]:
            r=solve(dict(expression=source,coefficients=['1','-1/2'],rest=True,start=0,count=6))
            assert_allclose(np.array(r['numeric_samples'])[:,0],initial_value*.5**np.arange(6),atol=1e-15)
            self.assertEqual(restore(r['input_definition']['encoded_expression']).subs(N,0),initial_value)
            self.assertTrue(r['closed_form']);self.assertTrue(r['evaluated'])
            y=restore(r['cas_encoded'])
            for n in range(6):self.assertEqual(sp.simplify(y.subs(N,n)-initial_value*sp.Rational(1,2)**n),0)

    def test_difference_rejects_fractional_indices_and_true_poles(self):
        from signallab_pc.difference_equations import solve
        base=dict(expression='0',coefficients=['1','-1/2'],rest=True,start=0,count=4)
        for changes in (dict(start=.5),dict(count=2.5),dict(expression='1/n'),dict(expression='Piecewise((1,n<2))')):
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):solve(base|changes)

    def test_ode_rejects_time_dependent_coefficients_and_nonfinite_initials(self):
        base=dict(operation='ode',expression='1',coefficients=['2','1'],initial=['3'])
        for changes in (dict(coefficients=['n','1']),dict(coefficients=['2','w']),dict(initial=['1/0']),dict(expression='n')):
            with self.assertRaises(ValueError):execute(base|changes)

    def test_ode_solution_satisfies_equation_and_initial_condition(self):
        r=execute(dict(operation='ode',expression='1',coefficients=['2','1'],initial=['3']))
        y=parse(r['result']).subs(sp.Heaviside(T),1)
        self.assertEqual(sp.simplify(sp.diff(y,T)+2*y-1),0)
        self.assertEqual(sp.limit(y,T,0,dir='+'),3)


class FourierContracts(unittest.TestCase):
    def test_dft_definition_and_parseval_with_complex_data(self):
        from signallab_pc.operations import dft,idft
        x=Signal([1+2j,-3,.5j,2],-3);n=4;k=np.arange(n)
        spectrum=dft(x);expected=np.array([sum(x.values[m]*np.exp(-2j*np.pi*j*m/n) for m in range(n)) for j in k])
        assert_allclose(spectrum.values,expected,atol=4e-15)
        self.assertAlmostEqual(np.sum(abs(x.values)**2),np.sum(abs(spectrum.values)**2)/n)
        assert_allclose(idft(spectrum).values,x.values,atol=1e-15)

    def test_dtft_and_overlay_use_global_origin_and_periodicity(self):
        from signallab_pc.fourier import dtft,dtft_with_dft
        x=Signal([1+1j,2,-1],-2);spectrum,(omega,bins)=dtft_with_dft(x,-2*np.pi,2*np.pi,49)
        expected=lambda w:sum(value*np.exp(-1j*w*int(n)) for value,n in zip(x.values,x.axis))
        assert_allclose(spectrum.values,expected(spectrum.axis),atol=1e-14)
        assert_allclose(bins,expected(omega),atol=1e-14)
        assert_allclose(dtft(x,0,2*np.pi,25).values,dtft(x,2*np.pi,4*np.pi,25).values,atol=2e-14)

    def test_continuous_fourier_quadrature_scaling_and_inverse(self):
        from signallab_pc.fourier import ctft,ictft
        x=Signal([1,2,3],-.25,.25,'s','x','continuous');s=ctft(x,-2,2,5)
        want=np.array([.25*sum(v*np.exp(-1j*w*t) for v,t in zip(x.values,x.axis)) for w in s.axis])
        assert_allclose(s.values,want,atol=1e-15)
        flat=Signal([1]*1001,-np.pi,2*np.pi/1000,'rad/s','X','frequency')
        assert_allclose(ictft(flat,0,2,3).values,[1,0,0],atol=2e-14)

    def test_periodogram_integral_equals_mean_square(self):
        from signallab_pc.fourier import spectral_density
        x=Signal([1+2j,3,-1,2j]);s=spectral_density(x,20,method='periodogram',window='boxcar')
        self.assertAlmostEqual(float(np.sum(s.values.real)*s.step),float(np.mean(abs(x.values)**2)))

    def test_symbolic_energy_and_power_keep_different_definitions(self):
        r=execute(dict(operation='signal_measures_expression',expression='(1/2)^abs(n)',domain='discrete',mode='global'))
        self.assertEqual(sp.simplify(parse(r['energy']['exact'])-sp.Rational(5,3)),0);self.assertEqual(r['mean_square']['exact'],'0')
        r=execute(dict(operation='signal_measures_expression',expression='sin(t)',mode='periodic',period='2*pi'))
        self.assertEqual(r['mean_square']['exact'],'1/2')


class SignalContracts(unittest.TestCase):
    def test_alignment_and_complex_convolution_against_definition(self):
        from signallab_pc.operations import add_sequences,linear_convolution
        x=Signal([1+1j,2],-1);h=Signal([3,2j],2)
        total=add_sequences(x,h);self.assertEqual(total.origin,-1);assert_allclose(total.values,[1+1j,2,0,3,2j])
        y=linear_convolution(x,h);self.assertEqual(y.origin,1)
        assert_allclose(y.values,[3+3j,4+2j,4j])

    def test_correlation_lag_sign_and_complex_conjugation(self):
        from signallab_pc.operations import linear_correlation
        x=Signal([1+2j,3],-2);h=Signal([2j,-1],1);r=linear_correlation(x,h)
        for lag,want in zip(r.axis,r.values):
            expected=sum(a*np.conj(b) for nx,a in zip(x.axis,x.values) for nh,b in zip(h.axis,h.values) if nx-nh==lag)
            self.assertAlmostEqual(abs(want-expected),0)

    def test_continuous_convolution_has_integration_step_and_correct_support(self):
        from signallab_pc.continuous import convolution
        x=Signal([1]*5,-.5,.25,'s','x','continuous')
        y=convolution(x,x);self.assertEqual(y.origin,-1)
        assert_allclose(y.values,[0,.25,.5,.75,1,.75,.5,.25,0],atol=1e-15)

    def test_windows_and_fir_use_identical_samples_and_independent_length(self):
        from signallab_pc.window_signals import generate_window
        from signallab_pc.windowing import window_impulse
        from signallab_pc.fourier import spectral_density
        h=Signal([1]*9,-4)
        for kind,beta in [('boxcar',0),('hann',0),('hamming',0),('blackman',0),('kaiser',2000)]:
            with self.subTest(window=kind):
                w=generate_window(kind,5,-2,beta)
                f=window_impulse(h,kind,beta,length=5,start=-2)
                self.assertEqual(len(f.windowed.values),5);self.assertEqual(f.windowed.origin,-2);self.assertEqual(f.delay,2)
                assert_allclose(f.windowed.values,w.values,atol=0,rtol=0)
                assert_allclose(f.system.response(np.array([0.])),[sum(w.values)],atol=1e-14)
                density=spectral_density(Signal([1]*5),10,method='periodogram',window=kind,beta=beta)
                self.assertAlmostEqual(float(np.sum(density.values.real)*density.step),1)
        self.assertEqual(generate_window('blackman',5).values[0],0)

    def test_time_reversal_and_even_odd_reconstruction(self):
        from signallab_pc.operations import reverse,even_odd_parts,add_sequences
        x=Signal([1j,2,3],-2);r=reverse(x);self.assertEqual(r.origin,0);assert_allclose(r.values,[3,2,1j])
        even,odd=even_odd_parts(x);s=add_sequences(even,odd)
        assert_allclose(s.values,[1j,2,3,0,0],atol=1e-15)


class StateContracts(unittest.TestCase):
    def test_state_trajectory_and_output_have_correct_timing(self):
        from signallab_pc.state_space import StateModel
        m=StateModel([[.5]],[[2]],[[3]],[[1]],.2);time,y,x=m.simulate([1,2,3],initial=[4])
        assert_allclose(time,[0,.2,.4]);assert_allclose(x[:,0],[4,4,6]);assert_allclose(y[:,0],[13,14,21])

    def test_continuous_initial_state_matches_exponential(self):
        from signallab_pc.state_space import StateModel
        m=StateModel([[-2]],[[1]],[[3]],[[.5]]);time,y,x=m.simulate(np.ones(8),step=.1,initial=[2])
        expected=.5+1.5*np.exp(-2*time);assert_allclose(x[:,0],expected,rtol=2e-14);assert_allclose(y[:,0],3*expected+.5,rtol=2e-14)


class SamplingContracts(unittest.TestCase):
    def test_angular_alias_matches_actual_sampled_waveform(self):
        from signallab_pc.sampling import sample_expression,alias_angular_frequency
        r=alias_angular_frequency(13*np.pi,4);self.assertAlmostEqual(r['digital_alias_rad_sample'],-3*np.pi/4)
        x=sample_expression('cos(13*pi*t)',0,4,9)
        assert_allclose(x.values,np.cos(r['digital_alias_rad_sample']*np.arange(9)),atol=2e-14)

    def test_sinc_reconstruction_interpolates_original_samples(self):
        from signallab_pc.sampling import reconstruct
        x=Signal([1,2j,-3,4]);r=reconstruct(x,8,.25,4,'sinc')
        assert_allclose(r.values[::4],x.values,atol=1e-15);self.assertEqual(r.step,1/32);self.assertEqual(r.origin,.25)

    def test_fixed_point_rounding_saturation_and_exact_fraction(self):
        from signallab_pc.precision import Encoding
        q=Encoding('fixed',2,2,'round')
        self.assertEqual(q.encode(Fraction(3,8))['value'],Fraction(1,2))
        high=q.encode(Fraction(8));self.assertTrue(high['saturated']);self.assertEqual(high['value'],Fraction(7,4))


class RandomContracts(unittest.TestCase):
    def test_complex_moments_and_covariance_normalization(self):
        from signallab_pc.random_signals import statistics,autocorrelation
        x=Signal([1+1j,3-1j,-2j]);r=statistics(x,'real',3)
        mean=sum(x.values)/3;power=sum(abs(v)**2 for v in x.values)/3;variance=sum(abs(v-mean)**2 for v in x.values)/3
        assert_allclose(complex(r['mean_real'],r['mean_imag']),mean,atol=1e-15)
        self.assertAlmostEqual(r['mean_square'],power);self.assertAlmostEqual(r['variance_N'],variance);self.assertAlmostEqual(r['variance_N_minus_1'],variance*1.5)
        for divisor in ('N','overlap'):
            a=autocorrelation(x,2,remove_mean=True,denominator=divisor)
            for lag,value in zip(a.axis,a.values):
                k=int(lag);total=sum((x.values[j]-mean)*np.conj(x.values[j-k]-mean) for j in range(3) if 0<=j-k<3)
                self.assertAlmostEqual(abs(value-total/(3 if divisor=='N' else 3-abs(k))),0,places=12)


if __name__=='__main__':unittest.main()
