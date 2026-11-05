"""Small release gate: independent pairs, domain semantics and result transport."""
import json,tempfile,unittest
from pathlib import Path
import sympy as sp
from signallab_pc.symbolic import execute,parse,N,T,S,Z,W
from signallab_pc.cas_engine import restore
from signallab_pc.expression_definition import prepare
from signallab_pc.result_summary import transform_summary
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


    def request(self, expression, **options):
        return dict(operation='z_inverse_expression', expression=expression,
                    roc='right', start=-2, count=7, **options)

    def test_automatic_scope_keeps_infinite_inverse_and_requested_viewport(self):
        for expression in ['-18/(z+1)', '(1-2/z)/(1-1/(2*z))', 'log(1-1/(2*z))']:
            request=self.request(expression, complete_finite=True)
            actual=execute(request)
            expected=execute(dict(request,complete_finite=False))
            self.assertTrue(actual['evaluated'])
            self.assertEqual(actual['sample_scope'],'interval')
            self.assertEqual(actual['origin'],-2)
            self.assertEqual(actual['numeric_samples'],expected['numeric_samples'])
            self.assertEqual(restore(actual['cas_encoded']),restore(expected['cas_encoded']))
            self.assertEqual(actual['roc'],expected['roc'])
            self.assertIn('El soporte no es finito',transform_summary(request,actual).plain_text())
        result=execute(self.request('-18/(z+1)',complete_finite=True))
        self.assertEqual([x[0] for x in result['numeric_samples']],[0,0,0,-18,18,-18,18])

    def test_automatic_scope_covers_finite_advances_delays_and_zero(self):
        for expression,origin,values in [('1-18/z',0,[1,-18]),('z^2+3/z',-2,[1,0,0,3]),('0',0,[0])]:
            result=execute(self.request(expression,complete_finite=True))
            self.assertTrue(result['evaluated']);self.assertEqual(result['sample_scope'],'finite_complete')
            self.assertEqual(result['origin'],origin)
            self.assertEqual([x[0] for x in result['numeric_samples']],values)

    def test_sample_overflow_does_not_destroy_formula_roc_or_cas_export(self):
        for expression in ['1-10^400/z','1/(1-1000000/z)','1/(z^3-1000000000000000000)', 'log(1-1000000/z)']:
            request=self.request(expression);request.update(start=0,count=65)
            actual=execute(request);expected=execute(dict(request,include_samples=False))
            self.assertTrue(actual['evaluated']);self.assertIsNone(actual['numeric_samples'])
            self.assertEqual(restore(actual['cas_encoded']),restore(expected['cas_encoded']))
            self.assertEqual(actual['roc'],expected['roc'])
            self.assertIn('No se generó el gráfico',actual['numeric_notice'])
            report=transform_summary(request,actual).plain_text()
            self.assertIn(actual['numeric_notice'],report)
            self.assertNotIn('Activá Graficar',report)

    def test_invalid_roc_and_inputs_are_still_rejected(self):
        for expression,extra in [('1/(z-1)',{'roc':'radius','radius':'1'}),('sin(n)',{})]:
            request=self.request(expression);request.update(extra)
            with self.assertRaises(ValueError):execute(request)

    def test_difference_equation_cancellation_is_zero_before_degree_analysis(self):
        from signallab_pc.difference_equations import forward_inverse
        for expression in ['1-1','(z-1)/(z-1)-1']:
            self.assertEqual(forward_inverse(parse(expression)),(sp.S.Zero,False))

    def test_optional_z_sampling_limits_do_not_block_exact_formulas(self):
        for formula in ['1/(z-1/2)','z/(z-1/2)','log(1-1/(2*z))']:
            base=dict(operation='z_inverse_expression',expression=formula,roc='right')
            exact=execute(dict(base,include_samples=False))
            for samples in (False,True):
                result=execute(dict(base,include_samples=samples,count=10**15))
                self.assertTrue(result['evaluated']);self.assertIsNone(result['numeric_samples'])
                self.assertEqual(restore(result['cas_encoded']),restore(exact['cas_encoded']))
                if samples:self.assertIn('memoria',result['numeric_notice'])
        for start,count in [('mal','65'),('0','0'),('0','3/2')]:
            result=execute(dict(base,start=start,count=count))
            self.assertTrue(result['evaluated']);self.assertIsNone(result['numeric_samples'])
            self.assertIn('numeric_notice',result)

    def test_optional_samples_never_replace_nonzero_underflow_by_zero(self):
        from signallab_pc.transform_samples import sample_pair,NumericSamplingError
        for number in [sp.exp(-1000),sp.I*sp.exp(-1000),1+sp.I*sp.exp(-1000)]:
            with self.assertRaises(NumericSamplingError):sample_pair(number)
        result=execute(dict(operation='z_inverse_expression',expression='exp(-1000)*z/(z-1/2)',start=0,count=3))
        self.assertTrue(result['evaluated']);self.assertIsNone(result['numeric_samples'])
        self.assertIn('no nula',result['numeric_notice'])
        self.assertEqual(sample_pair(sp.S.Zero),[0.,0.])

    def test_system_exact_scaling_precedes_float_conversion(self):
        common=execute(dict(operation='system_analysis',domain='digital',b=['10^400'],a=['10^400','-10^400/2']))
        self.assertEqual(common['numeric_b'],[[1.,0.]])
        self.assertEqual(common['numeric_a'],[[1.,0.],[-.5,0.]])
        for coefficient in ['10^400','exp(-1000)']:
            result=execute(dict(operation='system_analysis',domain='digital',b=[coefficient],a=['1','-1/2']))
            self.assertTrue(result['evaluated']);self.assertIn('numeric_notice',result)
            self.assertNotIn('numeric_b',result);self.assertIn('transfer',result)
        with self.assertRaises(ValueError):execute(dict(operation='system_analysis',domain='digital',b=['1'],a=['0']))

    def test_difference_optional_sampling_and_exact_common_factor(self):
        request=dict(operation='difference_equation',coefficients=['1','-1/2'],expression='10^400',count=8)
        result=execute(request)
        self.assertTrue(result['evaluated']);self.assertIsNone(result['numeric_samples']);self.assertIn('numeric_notice',result)
        result=execute(dict(request,coefficients=['10^400','-10^400/2']))
        self.assertEqual([v[0] for v in result['numeric_samples']],[2-2**(-n) for n in range(8)])
        self.assertTrue(result['residual_check']['normalized_equation'])
        result=execute(dict(request,expression='1',count=10**15))
        self.assertTrue(result['evaluated']);self.assertIsNone(result['numeric_samples']);self.assertIn('memoria',result['numeric_notice'])
        result=execute(dict(request,expression='exp(-1000)'))
        self.assertTrue(result['evaluated']);self.assertIsNone(result['numeric_samples']);self.assertIn('no nula',result['numeric_notice'])
        with self.assertRaises(ValueError):execute(dict(request,expression='1/(n-2)'))

    def test_conversion_reference_measurements_do_not_discard_converted_filters(self):
        from unittest.mock import patch
        from signallab_pc.filters import Transfer
        from signallab_pc.course_tools import convert_system
        from signallab_pc.conversion_details import enrich_conversion
        analog=Transfer([1],[1,1],'analog')
        converted=convert_system(analog,.1,'bilinear');system=converted['systems'][0]
        result=enrich_conversion(converted,analog,.1,'bilinear',[-1])
        self.assertIs(result['systems'][0],system);self.assertTrue(result['conversion_details']['notices'])
        with patch('signallab_pc.conversion_details.half_power',side_effect=ValueError('medición fuera de rango')):
            result=enrich_conversion(convert_system(analog,.1,'bilinear'),analog,.1,'bilinear')
        self.assertIn('Transferencia resultante',result['report']);self.assertIn('se conserva',result['report'])

    def test_optional_worker_explanation_cannot_erase_a_valid_transform(self):
        from unittest.mock import patch
        from signallab_pc.symbolic_process import worker
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source.json';destination=Path(folder)/'result.json'
            source.write_text(json.dumps(dict(operation='z_inverse_expression',expression='-18/(z+1)',include_samples=False)),encoding='utf-8')
            with patch('signallab_pc.transform_steps.build',side_effect=RuntimeError('fallo de explicación')),patch('signallab_pc.runtime_diagnostics.diagnostic'):
                code=worker(source,destination)
            result=json.loads(destination.read_text(encoding='utf-8'))
            self.assertEqual(code,0);self.assertTrue(result['evaluated']);self.assertIn('cas_encoded',result)
            self.assertTrue(result['derivation_notice']);self.assertNotIn('error',result)

    def test_optional_cas_presentation_preserves_exact_state_and_imports(self):
        from unittest.mock import patch
        from signallab_pc.cas_engine import calculate,empty_state
        from signallab_pc.cas_import import import_result
        from signallab_pc.cas_transfer import payload
        with patch('signallab_pc.cas_engine.presentation',side_effect=ValueError('fallo de formato')),patch('signallab_pc.runtime_diagnostics.diagnostic'):
            result=calculate(dict(source='factor(z^2-1)',cell=1,state=empty_state()))
            self.assertEqual(sp.expand(restore(result['state']['results']['1'])),Z**2-1)
            self.assertTrue(result['notices']);self.assertEqual(result['presentation']['latex'],'')
            calculation=dict(request=dict(operation='z_inverse_expression',expression='1-18/z'),result=execute(dict(operation='z_inverse_expression',expression='1-18/z',include_samples=False)))
            imported=import_result(dict(payload=payload(calculation),cell=1,state=empty_state()))
            self.assertEqual(restore(imported['encoded_value']),restore(calculation['result']['cas_encoded']))
            self.assertTrue(imported['notices']);self.assertTrue(imported['presentation']['text'])

    def test_optional_stages_do_not_hide_cancellation_or_primary_errors(self):
        from signallab_pc.auxiliary import optional,presentation
        from signallab_pc.jobs import OperationCancelled
        def cancelled():raise OperationCancelled('cancelado')
        with self.assertRaises(OperationCancelled):optional('Vista',cancelled)
        with self.assertRaises(OperationCancelled):presentation('Vista',cancelled,lambda:None)
        def wrong_name():raise NameError('error de programa')
        from unittest.mock import patch
        with patch('signallab_pc.runtime_diagnostics.diagnostic') as diagnostic:
            value,notice=optional('Análisis',wrong_name)
        self.assertIsNone(value);self.assertIn('falló',notice);diagnostic.assert_called_once()
        with self.assertRaises(ValueError):execute(dict(operation='z_inverse_expression',expression='sin(n)'))


if __name__=='__main__':unittest.main()
