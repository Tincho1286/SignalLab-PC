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


if __name__=='__main__':unittest.main()
