"""Preemptive regressions and negative controls for release safeguards."""
import contextlib,io,tempfile,unittest
from pathlib import Path
import numpy as np
import sympy as sp
from numpy.testing import assert_allclose
from signallab_pc.symbolic import execute,parse,N,Z,W
from signallab_pc.filters import Transfer


class PreventiveContracts(unittest.TestCase):
    def test_causal_reciprocal_tail_has_conditional_dtft(self):
        r=execute(dict(operation='dtft_expression',expression='1/n',lower='1',upper='oo'))
        self.assertTrue(r['evaluated']);self.assertEqual(r['method'],'certified_boundary_pairs')
        value=parse(r['result']);self.assertEqual(sp.simplify(value+sp.log(1-sp.exp(-sp.I*W))),0)
        self.assertEqual(sp.simplify(parse(r['condition']).subs(W,0)),sp.false)
        self.assertEqual(sp.simplify(parse(r['condition']).subs(W,sp.pi/2)),sp.true)

    def test_absolutely_summable_tail_includes_resonant_frequency(self):
        r=execute(dict(operation='dtft_expression',expression='1/n^2',lower='1',upper='oo'))
        self.assertTrue(r['evaluated']);self.assertEqual(r['condition'],'True')
        self.assertEqual(sp.simplify(parse(r['result']).subs(W,0)-sp.pi**2/6),0)

    def test_z_continuation_does_not_invent_ordinary_step_dtft(self):
        from signallab_pc.z_direct_pairs import direct_pairs
        for source in ('1','n','n^2','(-1)^n'):
            pair=direct_pairs(parse(source),sp.S.Zero,sp.oo)
            self.assertIsNotNone(pair)
            self.assertEqual(sp.simplify(pair['boundary_condition'].subs(Z,sp.exp(sp.I*W))),sp.false)

    def test_repeated_common_factors_have_analytic_group_delay(self):
        for domain,common,denominator in [('digital',[1,-2,1],[1,-.5]),('analog',[1,0,0],[1,2])]:
            h=Transfer(common,np.polymul(common,denominator),domain)
            base=Transfer([1],denominator,domain);w=np.array([0.,.2,.8])
            assert_allclose(h.response(w),base.response(w),atol=1e-13)
            assert_allclose(h.group_delay(w),base.group_delay(w),atol=1e-13)
            assert_allclose(h.group_delay(0.),base.group_delay(0.),atol=1e-13)
        self.assertTrue(np.isnan(Transfer([1,-1+1e-12],[1,-1]).group_delay(np.array([0.]))[0]))
        self.assertTrue(np.isnan(Transfer([1,-2,1],[1,-1]).group_delay(np.array([0.]))[0]))

    def test_shifted_causal_sinc_dtft_uses_certified_convergence(self):
        a=sp.Rational(3,10)*sp.pi;delay=4
        r=execute(dict(operation='dtft_expression',expression='sin(0.3*pi*(n-4))/(pi*(n-4))',lower='0',upper='oo'))
        self.assertTrue(r['evaluated']);self.assertEqual(r['method'],'certified_boundary_pairs');x=parse(r['input_definition']['effective_expression'])
        value=parse(r['result']);prefix=sum(x.subs(N,n)*sp.exp(-sp.I*W*n) for n in range(delay))
        q=sp.exp(-sp.I*W);tail=(sp.log(1-q*sp.exp(-sp.I*a))-sp.log(1-q*sp.exp(sp.I*a)))/(2*sp.I*sp.pi)
        want=prefix+sp.exp(-sp.I*W*delay)*(sp.Rational(3,10)+tail)
        for w in (sp.S.Zero,sp.pi/2,-sp.pi/4):assert_allclose(complex(value.subs(W,w).evalf(18)),complex(want.subs(W,w).evalf(18)),atol=3e-13)
        for w in (a,-a):self.assertEqual(sp.simplify(parse(r['condition']).subs(W,w)),sp.false)

    def test_audit_deadline_blocks_incomplete_results(self):
        from tools.audit_mathematics import run_audit
        with tempfile.TemporaryDirectory() as folder,contextlib.redirect_stdout(io.StringIO()):
            report=run_audit(Path(folder)/'audit.json',seed=1,case_seconds=.00001)
        self.assertFalse(report['passed']);self.assertIsNotNone(report['timeout']);self.assertLess(report['completed_cases'],report['expected_cases'])


    def test_periodic_poles_are_undefined_without_approximate_cancellation(self):
        from signallab_pc.transfer_plane import evaluate_plane
        omega=np.array([0.,2*np.pi,4*np.pi,-2*np.pi])
        for order in (1,2,3):
            a=np.array([1.])
            for _ in range(order):a=np.polymul(a,[1.,-1.])
            h=Transfer([1],a);self.assertTrue(np.isnan(h.response(omega)).all());self.assertTrue(np.isnan(h.group_delay(omega)).all())
            self.assertTrue(np.isnan(evaluate_plane(h,np.array([1.+0j]))).all())
        h=Transfer([1],[1,-1,1]);w=np.array([np.pi/3,2*np.pi+np.pi/3,-np.pi/3]);self.assertTrue(np.isnan(h.response(w)).all())
        cancelled=Transfer([1,-1],[1,-1.5,.5]);assert_allclose(cancelled.response(omega),2,atol=5e-14);assert_allclose(cancelled.group_delay(omega),1,atol=5e-14)
        almost=Transfer([1,-1],[1,-(1-1e-15)]);self.assertEqual(almost.response(np.array([0.]))[0],0);self.assertTrue(np.isnan(almost.response(np.array([2*np.pi]))[0]))
        r=1-1e-15;near=Transfer([1],[1,-r]);assert_allclose(near.response(np.array([0.])),[1/(1-r)],rtol=2e-14);assert_allclose(near.group_delay(np.array([0.])),[r/(1-r)],rtol=2e-14)
        self.assertTrue(np.isfinite(evaluate_plane(Transfer([1],[1,-1]),np.array([1+1e-20j]))[0]))

    def test_large_frequency_ratios_keep_finite_response(self):
        from signallab_pc.transfer_plane import evaluate_plane
        h=Transfer([1,2,1],[1,3,2],domain='analog');w=np.array([1e160,1e200,-1e200])
        result=h.response(w);self.assertTrue(np.isfinite(result).all());assert_allclose(result.real,1,atol=1e-14)
        assert_allclose(result.imag,1/w,rtol=2e-14,atol=0)
        self.assertTrue(np.isfinite(evaluate_plane(h,1j*w)).all())
        # The subnormal response of 1/s is representable and must survive.
        first=Transfer([1],[1,0],domain='analog');assert_allclose(first.response(np.array([1e200])),[-1e-200j],atol=0,rtol=2e-14)

    def test_underflow_is_not_reported_as_an_exact_zero(self):
        from signallab_pc.frequency_analysis import analyze_frequency
        small=Transfer([1,0,0],[1],domain='analog');self.assertEqual(small.response(np.array([0.]))[0],0)
        self.assertTrue(np.isnan(small.response(np.array([1e-200]))[0]))
        large=Transfer([1],[1,0,0],domain='analog');self.assertTrue(np.isnan(large.response(np.array([1e200]))[0]))
        physical=Transfer([1],[1,1],domain='analog');self.assertTrue(np.isnan(physical.group_delay(np.array([1e200]))[0]))
        data=analyze_frequency(small,np.array([0.,1e-200]));self.assertTrue(np.isnan(data.phase).all());self.assertTrue(np.isnan(data.delay).all())
        zero=Transfer([0],[1,-1]);np.testing.assert_array_equal(zero.response([0,2*np.pi]),[0,0]);self.assertTrue(np.isnan(zero.group_delay([0,2*np.pi])).all())

    def test_exact_cascade_cancellation_survives_intermediate_overflow(self):
        r=1-1e-15
        sections=np.vstack([np.tile([1,0,0,1,-r,0],(25,1)),np.tile([1,-r,0,1,0,0],(25,1))])
        h=Transfer.from_sos(sections);w=np.array([0.,.3,np.pi]);assert_allclose(h.response(w),1,atol=2e-13);np.testing.assert_array_equal(h.group_delay(w),[0,0,0])
        advanced=Transfer([1],[1],sos=sections,advance=2);assert_allclose(advanced.response(w),np.exp(2j*w),atol=2e-13);assert_allclose(advanced.group_delay(w),-2,atol=2e-13)
        self.assertEqual(Transfer([1],[1,-.5]).response(0.),2)

    def test_small_real_group_delay_is_not_flattened(self):
        from fractions import Fraction
        shift=2.**-48;h=Transfer([1,1],[1,1+shift],domain='analog')
        want=float(Fraction(1,1)/Fraction(1+shift)-1)
        actual=h.group_delay(np.array([0.]))[0];self.assertNotEqual(actual,0);self.assertAlmostEqual(actual/want,1,places=14)

    def test_inactive_support_excludes_factor_poles(self):
        for source,want in [('Step(n-1)/n',-sp.log(1-1/Z)),('Step(n-2)/(n-1)',-sp.log(1-1/Z)/Z),('Impulse(n-3)/n',1/(3*Z**3))]:
            with self.subTest(source=source):
                r=execute(dict(operation='z_expression',expression=source,lower='-oo',upper='oo'));self.assertTrue(r['evaluated'])
                actual=parse(r['branches'][0]['expression'] if r.get('branches') else r['result'])
                for z in (2,3):self.assertAlmostEqual(abs(complex((actual-want).subs(Z,z).evalf())),0,places=13)
                effective=parse(r['input_definition']['effective_expression']);self.assertEqual(effective.subs(N,0),0)
        for source in ('Step(n)/n','Heaviside(n)/n','Impulse(n)/n'):
            with self.subTest(source=source),self.assertRaises(ValueError):execute(dict(operation='z_expression',expression=source,lower='-oo',upper='oo'))
        r=execute(dict(operation='dtft_expression',expression='Step(n-1)/n',lower='-oo',upper='oo'));self.assertTrue(r['evaluated']);self.assertEqual(sp.simplify(parse(r['condition']).subs(W,0)),sp.false)

    def test_finite_impulse_dtft_uses_shared_discrete_description(self):
        r=execute(dict(operation='dtft_expression',expression='2*Dirac(n+1)+3*Impulse(n-2)',lower='-oo',upper='oo'))
        self.assertTrue(r['evaluated']);self.assertEqual(r['method'],'shared_discrete_pairs')
        self.assertEqual(sp.simplify(parse(r['result'])-2*sp.exp(sp.I*W)-3*sp.exp(-2*sp.I*W)),0)


    def test_energy_and_samples_respect_discrete_support(self):
        expression = 'Step(n-1)/n'
        interval = execute(dict(operation='signal_measures_expression', expression=expression, domain='discrete', mode='interval', lower='-1', upper='1'))
        self.assertEqual(interval['energy']['exact'], '1')
        total = execute(dict(operation='signal_measures_expression', expression=expression, domain='discrete', mode='global'))
        self.assertEqual(sp.simplify(parse(total['energy']['exact'])-sp.pi**2/6), 0)
        sampled = execute(dict(operation='signal_measures_window', expression=expression, domain='discrete', start='-1', stop='1'))
        self.assertEqual(sampled['samples'], [[0, 0], [0, 0], [1, 0]])
        with self.assertRaises(ValueError):
            execute(dict(operation='signal_measures_window', expression='Step(n)/n', domain='discrete', start='-1', stop='1'))

    def test_sos_roc_cancels_only_exact_section_factors(self):
        from signallab_pc.frequency_analysis import analyze_frequency
        from signallab_pc.transfer_plane import convergence, evaluate_plane, plane_roots
        system = Transfer.from_sos([[1, -1, 0, 1, -.7, 0], [1, .2, 0, 1, -1, 0]])
        system.roc = {'mode': 'right'}
        grid = np.array([0., .5])
        q = np.exp(-1j*grid)
        assert_allclose(analyze_frequency(system, grid).response, (1+.2*q)/(1-.7*q), atol=2e-14)
        assert_allclose(plane_roots(system)[1], [.7], atol=2e-14)
        assert_allclose(evaluate_plane(system, np.array([0, 1, 2])), [-2/7, 4, 22/13], atol=2e-14)
        nearby = Transfer.from_sos([[1, np.nextafter(-1., 0.), 0, 1, -.7, 0], [1, .2, 0, 1, -1, 0]])
        nearby.roc = {'mode': 'right'}
        self.assertFalse(convergence(nearby)['unit'])

    def test_frequency_db_phase_and_delay_survive_linear_magnitude_overflow(self):
        from signallab_pc.frequency_analysis import analyze_frequency
        from signallab_pc.analytic_frequency import analyze_expression
        grid = np.array([0., .5])
        value = 1.5e308
        expected_db = 20*np.log10(value) + 10*np.log10(2)
        expression = '1.5e308*(1+i)'
        request = dict(operation='system_frequency_expression', expression=expression, domain='digital')
        _, analytical = analyze_expression(execute(request), request, grid)
        for data in (analyze_frequency(Transfer([complex(value,value)], [1]), grid), analytical):
            self.assertTrue(np.isinf(data.magnitude).all())
            assert_allclose(data.db, expected_db)
            assert_allclose(data.phase, np.pi/4)
            assert_allclose(data.delay, 0)

    def test_reciprocal_z_tails_round_trip_with_support(self):
        cases = [
            ('Step(n-2)/(n-1)', '2', 'oo', 'right', -1, [0,0,0,1,.5,1/3]),
            ('Step(-n-1)/n^2', '-oo', '-1', 'left', -4, [1/16,1/9,1/4,1,0,0]),
            ('Step(n-26)/n', '26', 'oo', 'right', 24, [0,0,1/26,1/27,1/28,1/29]),
        ]
        for expression, lower, upper, side, start, expected in cases:
            with self.subTest(expression=expression):
                direct = execute(dict(operation='z_expression', expression=expression, lower=lower, upper=upper))
                branch = direct['branches'][0]['expression']
                request = dict(operation='z_inverse_expression', expression=branch, roc=side, start=start, count=len(expected))
                inverse = execute(request)
                self.assertEqual(inverse['method'], 'reciprocal_series_pairs')
                assert_allclose(np.asarray(inverse['numeric_samples'])[:,0], expected, atol=1e-15)
                for index,value in enumerate(expected, start):
                    self.assertAlmostEqual(float(parse(inverse['result']).subs(N,index)), value, places=14)
                with self.assertRaisesRegex(ValueError, 'ROC'):
                    execute(dict(request, roc='left' if side == 'right' else 'right'))


    def test_z_radial_intersection_for_one_sided_and_bilateral_sums(self):
        fixtures = [
            ('(1/2)^n+(1/4)^n','0','oo',[sp.Rational(1,3),1], [False,True]),
            ('2^n+3^n','-oo','-1',[1,2,3],[True,False,False]),
            ('Step(n)*(1/2)^n+Step(-n-1)*2^n','-oo','oo',[sp.Rational(1,3),1,3],[False,True,False]),
        ]
        for expression,lo,hi,points,expected in fixtures:
            direct=execute(dict(operation='z_expression',expression=expression,lower=lo,upper=hi))
            self.assertTrue(direct['evaluated'],direct)
            condition=parse(direct['branches'][0]['condition'])
            self.assertEqual([bool(sp.simplify(condition.subs(Z,point))) for point in points],expected)
        from signallab_pc.radial_conditions import simplify_radial
        union=sp.Or(sp.Abs(Z)<sp.Rational(1,2),sp.Abs(Z)>2)
        condition=simplify_radial(union,Z)
        self.assertEqual([bool(condition.subs(Z,point)) for point in (sp.Rational(1,4),1,3)], [True,False,True])

    def test_mixed_z_inverse_intersects_regions_and_sums_samples(self):
        expression='1/(1-1/(2*z))-log(1-1/z)'
        request=dict(operation='z_inverse_expression',expression=expression,roc='right',start=-1,count=5)
        result=execute(request)
        assert_allclose(np.array(result['numeric_samples'])[:,0],[0,1,1.5,.75,1/3+.125],atol=1e-14)
        self.assertTrue(result['roc'].startswith('1 <'))
        bilateral=execute(dict(request,expression='1/(1-z/2)-log(1-1/z)',roc='radius',radius='3/2'))
        assert_allclose(np.array(bilateral['numeric_samples'])[:,0],[.5,1,1,.5,1/3],atol=1e-14)
        self.assertTrue(bilateral['roc'].endswith('< 2'))
        # Round once after combining the two families. Their 1-unit residual
        # would vanish if the rational part were rounded to float first.
        cancelling=execute(dict(request,expression='2*(10^16+1)/(1-1/(2*z))+10^16*log(1-1/z)',start=1,count=1))
        self.assertEqual(cancelling['numeric_samples'],[[1.,0.]])
        with self.assertRaisesRegex(ValueError,'ROC|convergencia|radio'):
            execute(dict(request,expression='1/(1-1/(2*z))-log(1-z)-log(1-1/z)',roc='radius',radius='3/2'))

    def test_impulse_invariance_maps_left_and_bilateral_roc(self):
        from signallab_pc.course_tools import convert_system, inverse_z_contour
        t=.25
        source=Transfer([1],[1,-1],domain='analog',roc={'mode':'left'})
        digital=convert_system(source,t,'impulse')['systems'][0]
        self.assertEqual(digital.roc,{'mode':'left'})
        h=inverse_z_contour(digital,'radius',1,-3,7,512)['signals'][0]
        assert_allclose(h.values,[-t*np.exp(t*n) if n<0 else 0 for n in range(-3,4)],atol=2e-13)
        source=Transfer([1,0],[1,0,-1],domain='analog',roc={'mode':'line','sigma':0})
        digital=convert_system(source,t,'impulse')['systems'][0]
        self.assertEqual(digital.roc,{'mode':'radius','radius':1.})
        h=inverse_z_contour(digital,'radius',1,-3,7,512)['signals'][0]
        assert_allclose(h.values,[t/2*np.exp(-t*n) if n>=0 else -t/2*np.exp(t*n) for n in range(-3,4)],atol=2e-13)

    def test_initial_rest_eliminates_exact_hidden_modes_but_keeps_histories(self):
        from signallab_pc.model import Signal
        model=Transfer.from_sos([[1,.2,0,1,-2,0],[1,-2,0,1,-.99,0]])
        reduced=Transfer([1,.2],[1,-.99])
        x=Signal(np.r_[1,np.zeros(120)])
        assert_allclose(model.apply(x).values,reduced.apply(x).values,atol=2e-14)
        # Past outputs can excite a canceled mode in the original recurrence.
        polynomial=Transfer([1,-2],[1,-2])
        assert_allclose(polynomial.apply(Signal([0,0,0]),previous_outputs=[1]).values,[2,4,8])
        assert_allclose(polynomial.apply(Signal([1,0,0])).values,[1,0,0])

    def test_rational_phase_keeps_winding_on_sparse_grids(self):
        from signallab_pc.frequency_analysis import analyze_frequency
        from signallab_pc.filters import from_poles_zeros
        omega=np.linspace(0,np.pi,51)
        for delay in (80, 400):
            pure=Transfer(np.r_[np.zeros(delay),1],[1])
            result=analyze_frequency(pure,omega)
            self.assertEqual(result.phase_kind,'continuous')
            assert_allclose(result.phase,-delay*omega,atol=3e-12)
        cascade=from_poles_zeros([.9,.85],[.1,.2],domain='digital')
        shifted=Transfer(np.r_[np.zeros(80),cascade.b],cascade.a)
        result=analyze_frequency(shifted,omega)
        ref=np.unwrap(np.angle(shifted.response(np.linspace(0,np.pi,5001))))[::100]
        assert_allclose(result.phase,ref,atol=2e-8)

    def test_dft_overlay_keeps_exact_nyquist_and_respects_open_cutoff(self):
        from signallab_pc.fourier import dtft_with_dft
        from signallab_pc.model import Signal
        for length in (6, 50, 70):
            signal=Signal(np.r_[1,np.zeros(length-1)])
            _, (bins,_) = dtft_with_dft(signal,-np.pi,np.pi,65)
            self.assertEqual(len(bins),length+1)
            assert_allclose(bins[[0,-1]],[-np.pi,np.pi],atol=0,rtol=0)
            _, (bins,_) = dtft_with_dft(signal,np.nextafter(-np.pi,0),np.nextafter(np.pi,0),65)
            self.assertEqual(len(bins),length-1)

    def test_discrete_fourier_uses_integer_origin_modulo_the_grid(self):
        from signallab_pc.course_tools import window_fft
        from signallab_pc.fourier import dtft, dtft_with_dft
        from signallab_pc.model import Signal
        import mpmath
        for origin in (2**53-3, -(2**57)+5, 2**63-5):
            signal=Signal([0,0,0,1],origin)
            spectrum,(frequencies,bins)=dtft_with_dft(signal,0,np.pi,3)
            expected=np.exp(-2j*np.pi*((np.arange(3)*((origin+3)%4))%4)/4)
            assert_allclose(spectrum.values,expected,atol=2e-15)
            assert_allclose(bins,expected,atol=2e-15)
            assert_allclose(frequencies,[0,np.pi/2,np.pi])
            windowed=window_fft(signal,4,4,'boxcar',0,9)['signals'][0]
            assert_allclose(windowed.values,np.exp(-2j*np.pi*((np.arange(-2,2)*((origin+3)%4))%4)/4),atol=2e-15)
        angle=.123456789
        signal=Signal([1],2**60+17)
        data=dtft(signal,angle,angle+.01,2)
        with mpmath.workdps(70):
            expected=complex(mpmath.exp(-1j*mpmath.mpf(angle)*signal.origin))
        assert_allclose(data.values[0],expected,atol=2e-15)


    def test_causal_state_realization_respects_an_explicit_roc(self):
        from signallab_pc.state_space import StateModel
        from signallab_pc.realization import realize_system
        for system in (Transfer([1],[1,-2],roc={'mode':'left'},sample_period_s=.125),
                       Transfer([1],[1,-1],'analog',roc={'mode':'line','sigma':0.})):
            with self.assertRaisesRegex(ValueError,'ROC.*anticausal'):
                StateModel.from_transfer(system)
            with self.assertRaisesRegex(ValueError,'ROC.*anticausal'):
                realize_system(system)
        causal=Transfer([1],[1,-2],roc={'mode':'radius','radius':3.},sample_period_s=.125)
        model=StateModel.from_transfer(causal)
        self.assertEqual(model.to_transfer().roc,{'mode':'right'})
        assert_allclose(model.simulate([1,0,0,0])[1][:,0],[1,2,4,8])

    def test_state_frequency_resolves_singularities_per_channel(self):
        from signallab_pc.state_space import StateModel
        # This triangular basis hides the diagonal input-output transfer.
        A=[[0,-1],[0,-1]];B=[[1,1],[0,1]];C=[[1,-1],[0,1]];D=[[0,0],[0,0]]
        model=StateModel(A,B,C,D)
        response=model.response([0.,.5])
        self.assertTrue(np.isnan(response[0,0,0]))
        assert_allclose([response[0,0,1],response[0,1,0],response[0,1,1]],[0,0,1])
        assert_allclose(response[1],np.diag([-2j,1/(1+.5j)]),atol=2e-15)
        digital=StateModel([[-1,0],[0,.5]],np.eye(2),np.eye(2),D,.125)
        response=digital.response([np.pi],normalized=True)[0]
        self.assertTrue(np.isnan(response[0,0]))
        assert_allclose([response[0,1],response[1,0],response[1,1]],[0,0,-2/3])

    def test_frequency_filter_output_preserves_clock_for_resampling(self):
        from signallab_pc.frequency_filter import analyze
        from signallab_pc.model import Signal
        from signallab_pc.sampling import resample_rational
        source=Signal([1,2,3],5,metadata={'sample_rate_hz':8000.,'time_start_s':.25})
        response=Signal(np.ones(129),-np.pi,np.pi/64,'rad/muestra','H','frequency')
        output=analyze(response,'discrete',-4,9,1,source)[0][-1]
        assert_allclose(output.values,source.values,atol=2e-14)
        self.assertEqual(output.origin,5)
        reused=resample_rational(output,2,1)
        self.assertEqual(reused.metadata['sample_rate_hz'],16000.)
        self.assertEqual(reused.metadata['time_start_s'],.25)

    def test_nonkaiser_fir_search_starts_at_the_smallest_valid_length(self):
        from scipy.signal import firwin, freqz
        from signallab_pc.amplitude_design import design
        wp=.3*np.pi;ws=.5*np.pi
        result=design([wp],[ws],.05,.01,'kaiser',taps=200,search=2,window='hamming')
        b=result['systems'][0].b
        self.assertTrue(result['specification_met'])
        self.assertEqual(len(b),31)
        w=np.unique(np.r_[np.linspace(0,np.pi,4097),wp,ws])
        for length in range(2,len(b)):
            trial=firwin(length,(wp+ws)/2,window='hamming',fs=2*np.pi,scale=False)
            h=abs(freqz(trial,worN=w)[1]);passing=h[w<=wp]
            self.assertTrue(np.min(passing)<.95 or np.max(passing)>1.05 or np.max(h[w>=ws])>.01)
        high=design([.7*np.pi],[.4*np.pi],.05,.04,'kaiser',window='hann')
        self.assertTrue(high['specification_met'])
        self.assertEqual(len(high['systems'][0].b)%2,1)


if __name__=='__main__':unittest.main()
