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


if __name__=='__main__':unittest.main()
