"""Small release gate: independent pairs, domain semantics and result transport."""
import json,tempfile,unittest
from pathlib import Path
import sympy as sp
from signallab_pc.symbolic import execute,parse,N,T,S,Z,W
from signallab_pc.cas_engine import restore
from signallab_pc.expression_definition import prepare
from signallab_pc.transform_status import finalize


def expression(result):
    if not result['evaluated']:raise AssertionError(result)
    return parse(result['branches'][0]['expression'] if result.get('branches') else result['result'])


class MathematicalReliabilityTests(unittest.TestCase):
    def direct(self,source,kind='z_expression',lower='0',upper='oo',**options):
        return execute(dict(operation=kind,expression=source,lower=lower,upper=upper,**options))

    def equivalent(self,actual,expected):self.assertEqual(sp.simplify(actual-expected),0)

    def test_sinc_sample_survives_both_discrete_transforms(self):
        for kind in ('z_expression','dtft_expression'):
            for lo,hi in (('0','oo'),('-oo','oo'),('-3','4')):
                with self.subTest(kind=kind,support=(lo,hi)):
                    r=self.direct('sin(pi*n)/(pi*n)',kind,lo,hi)
                    self.equivalent(expression(r),1)
                    definition=r['input_definition'];self.assertEqual(definition['domain'],'discrete')
                    self.assertEqual(definition['support']['lower'],lo)
                    self.assertEqual(restore(definition['encoded_expression']).subs(N,0),1)
                    self.assertTrue(any(v['point']=='0' and v['value']=='1' for v in definition['extensions']))

    def test_shift_and_support_are_not_lost(self):
        for d in (-2,2):
            source=f'sin(pi*(n-({d})))/(pi*(n-({d})))'
            with self.subTest(delay=d):
                self.equivalent(expression(self.direct(source,lower='-oo')),Z**(-d))
                self.equivalent(expression(self.direct(source,'dtft_expression','-oo')),sp.exp(-sp.I*W*d))
                self.equivalent(expression(self.direct(source)),Z**(-d) if d>=0 else 0)

    def test_explicit_integer_point_overrides_extension(self):
        for kind in ('z_expression','dtft_expression'):
            r=self.direct('Piecewise((7,n==0),(sin(pi*n)/(pi*n),True))',kind)
            self.equivalent(expression(r),7);self.assertEqual(r['input_definition']['extensions'],[])

    def test_true_integer_pole_is_rejected(self):
        for kind in ('z_expression','dtft_expression'):
            with self.subTest(kind=kind):
                with self.assertRaisesRegex(ValueError,'n=0'):self.direct('1/n',kind)
        with self.assertRaisesRegex(ValueError,'polo'):
            execute({'operation':'expression_grid','variable':'t','expression':'1/t','start':0,'stop':1,'count':5})

    def test_real_pole_between_integer_samples_is_not_rejected(self):
        r=self.direct('1/(n-1/2)',lower='-1',upper='2')
        self.equivalent(expression(r),-2*Z/3-2+2/Z+2/(3*Z**2))

    def test_incomplete_piecewise_is_not_zero_filled(self):
        try:r=self.direct('Piecewise((1,n==0))')
        except (ValueError,TypeError):return
        self.assertFalse(r['evaluated'],r)

    def test_polynomial_geometric_removable_pair(self):
        r=self.direct('(n^2-1)/(n-1)*(1/2)^n')
        self.equivalent(expression(r),1/(1-1/(2*Z))**2)
        self.assertEqual(r['calculation_status']['code'],'conditional')

    def test_geometric_and_frequency_pair(self):
        z=self.direct('(1/2)^n');self.equivalent(expression(z),Z/(Z-sp.Rational(1,2)))
        condition=parse(z['branches'][0]['condition']);self.assertEqual(condition.subs(Z,2),sp.true);self.assertEqual(condition.subs(Z,sp.Rational(1,4)),sp.false)
        f=self.direct('(1/2)^n','dtft_expression');self.equivalent(expression(f),1/(1-sp.exp(-sp.I*W)/2))

    def test_causal_sinc_logarithmic_pair(self):
        r=self.direct('sin(pi*n/2)/(pi*n)')
        expected=sp.Rational(1,2)+(sp.log(1+sp.I/Z)-sp.log(1-sp.I/Z))/(2*sp.I*sp.pi)
        self.equivalent(expression(r),expected)

    def test_bilateral_sinc_dtft_does_not_claim_z_roc(self):
        source='sin(pi*n/2)/(pi*n)';z=self.direct(source,lower='-oo')
        self.assertFalse(z['evaluated']);self.assertEqual(z['calculation_status']['code'],'no_convergence')
        f=self.direct(source,'dtft_expression','-oo');value=expression(f)
        for w,y in ((0,1),(sp.pi/2,sp.Rational(1,2)),(3*sp.pi/4,0),(2*sp.pi,1)):
            with self.subTest(frequency=w):self.equivalent(value.subs(W,w),y)

    def test_continuous_isolated_value_is_not_a_discrete_impulse(self):
        r=self.direct('Piecewise((9,t==0),(exp(-t^2),True))','fourier_angular')
        self.equivalent(expression(r),sp.sqrt(sp.pi)*sp.exp(-W**2/4))
        self.assertEqual(restore(r['input_definition']['encoded_expression']).subs(T,0),9)

    def test_laplace_removable_and_causal_convention(self):
        r=self.direct('(t^2-1)/(t-1)*exp(-t)','laplace')
        self.equivalent(expression(r),(S+2)/(S+1)**2)
        self.assertEqual(r['input_definition']['support']['kind'],'unilateral_0minus')

    def test_continuous_dirac_keeps_its_weight(self):
        for kind,expected in (('laplace',3),('fourier_angular',3)):
            with self.subTest(kind=kind):self.equivalent(expression(self.direct('3*dirac(t)',kind)),expected)

    def test_bilateral_laplace_pair_and_empty_strip(self):
        r=self.direct('exp(-abs(t))','laplace',interpretation='bilateral')
        self.equivalent(expression(r),2/(1-S**2));self.assertEqual(r['calculation_status']['code'],'conditional')
        r=self.direct('1','laplace',interpretation='bilateral')
        self.assertFalse(r['evaluated']);self.assertEqual(r['calculation_status']['code'],'no_convergence')

    def test_inverse_pairs_keep_their_interpretation(self):
        for mode,n,value in (('right',3,sp.Rational(1,8)),('left',-1,-2)):
            r=self.direct('z/(z-1/2)','z_inverse_expression',roc=mode,include_samples=False)
            self.equivalent(expression(r).subs(N,n),value);self.assertEqual(r['input_definition']['domain'],'complex')
        r=self.direct('1/(s+1)','inverse_laplace');self.equivalent(expression(r).subs(T,2),sp.exp(-2))
        r=self.direct('1','inverse_dtft_expression');self.equivalent(expression(r).subs(N,0),1);self.equivalent(expression(r).subs(N,1),0)
        self.assertEqual(r['input_definition']['support']['kind'],'integration_period')

    def test_constant_inverse_pairs_include_zero_and_parameters(self):
        for value in (0,1,3):
            for op in ('z_inverse_expression','inverse_dtft_expression'):
                with self.subTest(value=value,operation=op):
                    r=self.direct(str(value),op,roc='right',include_samples=False)
                    self.equivalent(expression(r).subs(N,0),value);self.equivalent(expression(r).subs(N,1),0)
            r=self.direct(str(value),'inverse_laplace',interpretation='bilateral')
            self.equivalent(expression(r),value*sp.DiracDelta(T))

        r=self.direct('a','z_inverse_expression',roc='right',include_samples=False)
        self.equivalent(expression(r).subs(N,0),sp.Symbol('a'));self.assertEqual(r['parameters'],['a'])

    def test_finite_sequence_keeps_negative_origin(self):
        r=execute({'operation':'z_finite','origin':-1,'samples':[[1,0],[2,0]]})
        self.equivalent(expression(r),Z+2);self.assertEqual(r['input_definition']['support']['lower'],'-1')
        with self.assertRaises(ValueError):execute({'operation':'z_finite','origin':.5,'samples':[[1,0]]})

    def test_fourier_inverse_known_gaussian(self):
        r=self.direct('sqrt(pi)*exp(-w^2/4)','inverse_fourier_angular')
        self.equivalent(expression(r),sp.exp(-T**2))

    def test_pending_computation_cannot_be_promoted_by_flag(self):
        r=finalize({'result':'Integral(exp(-s*t),(t,0,oo))','evaluated':True})
        self.assertFalse(r['evaluated']);self.assertEqual(r['calculation_status']['code'],'unresolved')

    def test_result_library_export_and_cas_keep_definition(self):
        from signallab_pc.project import Project
        from signallab_pc.cas_transfer import payload
        from signallab_pc.cas_import import import_result
        request={'operation':'z_expression','expression':'sin(pi*n)/(pi*n)','lower':'0','upper':'oo','input_conditions':['Convención de entrada preservada']}
        result=execute(request);project=Project();key=project.add({'request':request,'result':result})
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/'result.json';project.export_record(key,file)
            document=json.loads(file.read_text(encoding='utf-8'));saved=document['records'][0]['data']['result']
            self.assertEqual(saved['input_definition'],result['input_definition'])
        data=payload(project.get(key));self.assertEqual(data['provenance']['input_definition'],result['input_definition'])
        imported=import_result({'payload':data,'cell':1});self.assertEqual(imported['provenance'],data['provenance'])
        self.assertIn('Convención de entrada preservada',imported['notices'])

    def test_worker_keeps_notes_without_an_active_ui_capture(self):
        from signallab_pc.symbolic_process import run_request
        r=run_request({'operation':'z_expression','expression':'sin(pi*n)/(pi*n)','lower':'0','upper':'oo'})
        self.equivalent(expression(r),1);self.assertTrue(r['calculation_notes']);self.assertTrue(r['input_definition']['extensions'])
        self.assertTrue(r['derivation'])


if __name__=='__main__':unittest.main()
