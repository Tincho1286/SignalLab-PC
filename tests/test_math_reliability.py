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
            with patch('signallab_pc.procedure.views',side_effect=RuntimeError('fallo de explicación')),patch('signallab_pc.runtime_diagnostics.diagnostic'):
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


    def test_continuous_sinc_pairs_keep_shift_modulation_width_and_edge_values(self):
        for width,delay,carrier in [(sp.pi/3,sp.Rational(3,2),sp.Rational(2,7)),(-2*sp.pi/5,-2,sp.S.Zero),(sp.S.Zero,1,2)]:
            source=f'(1+i/2)*sin(({width})*(t-({delay})))/(t-({delay}))*exp(i*({carrier})*t)'
            result=execute(dict(operation='fourier_angular',expression=source))
            self.assertTrue(result['evaluated']);actual=restore(result['cas_encoded'])
            if width==0:self.equivalent(actual,0);continue
            radius=abs(width)
            for w,fraction in [(carrier,1),(carrier+radius,sp.Rational(1,2)),(carrier-radius,sp.Rational(1,2)),(carrier+2*radius,0)]:
                want=(1+sp.I/2)*sp.pi*sp.sign(width)*sp.exp(-sp.I*(w-carrier)*delay)*fraction
                self.equivalent(sp.simplify(actual.subs(W,w)),sp.simplify(want))

    def test_fourier_envelope_properties_avoid_generic_unresolved_integrals(self):
        base=4*sp.exp(-3*sp.I*W)/(4+W**2)
        gaussian=sp.sqrt(sp.pi/2)*sp.exp(-W**2/8)*sp.exp(-sp.Rational(3,2)*sp.I*W)
        cases=[('exp(-2*abs(t-3))*cos(3*t+pi/4)',(sp.exp(sp.I*sp.pi/4)*base.subs(W,W-3)+sp.exp(-sp.I*sp.pi/4)*base.subs(W,W+3))/2),
               ('t*exp(-2*abs(t-3))',sp.I*sp.diff(base,W)),
               ('exp(-2*(t-3/2)^2)*cos(3*t)',(gaussian.subs(W,W-3)+gaussian.subs(W,W+3))/2),
               ('(t-2)^2*exp(-3*(t-2))*Step(t-2)',2*sp.exp(-2*sp.I*W)/(3+sp.I*W)**3),
               ('exp(2*(t+1))*Step(-t-1)',sp.exp(sp.I*W)/(2-sp.I*W))]
        for source,want in cases:
            with self.subTest(source=source):
                result=execute(dict(operation='fourier_angular',expression=source));self.assertTrue(result['evaluated'])
                actual=restore(result['cas_encoded'])
                for w in [sp.S.Zero,sp.Rational(2,7),sp.Rational(7,5)]:
                    self.assertLess(abs(complex((actual-want).subs(W,w).evalf(18))),3e-12)

    def test_fourier_distribution_pairs_survive_ordinary_pair_extraction(self):
        cases=[('cos(t)^2',sp.pi*sp.DiracDelta(W)+sp.pi*(sp.DiracDelta(W-2)+sp.DiracDelta(W+2))/2),('1',2*sp.pi*sp.DiracDelta(W)),('sin(2*t)',-sp.I*sp.pi*(sp.DiracDelta(W-2)-sp.DiracDelta(W+2))),
               ('t^2',-2*sp.pi*sp.DiracDelta(W,2)),('sin(t)/t+t',sp.Piecewise((sp.pi,abs(W)<1),(sp.pi/2,sp.Eq(abs(W),1)),(0,True))+2*sp.pi*sp.I*sp.DiracDelta(W,1))]
        for source,want in cases:
            result=execute(dict(operation='fourier_angular',expression=source))
            self.assertTrue(result['evaluated']);self.equivalent(restore(result['cas_encoded']),want)

    def test_bilateral_absolute_exponential_uses_both_tail_supports(self):
        for r,delay in [(sp.Rational(1,2),-3),(sp.Rational(1,3),2)]:
            source=f'2*({r})^abs(n-({delay}))'
            result=execute(dict(operation='z_expression',expression=source,lower='-oo',upper='oo'))
            actual=expression(result);want=2*Z**(-delay)*(1-r**2)/((1-r/Z)*(1-r*Z))
            self.equivalent(actual,want)
            transformed=execute(dict(operation='dtft_expression',expression=source,lower='-oo',upper='oo'))
            self.assertTrue(transformed['evaluated']);actual=restore(transformed['cas_encoded'])
            want=2*sp.exp(-sp.I*W*delay)*(1-r**2)/(1-2*r*sp.cos(W)+r**2)
            for w in (sp.S.Zero,sp.pi/3,sp.pi):self.assertLess(abs(complex((actual-want).subs(W,w).evalf(18))),3e-13)

    def test_zero_order_equations_solve_without_transform_or_initial_history(self):
        request=dict(operation='difference_equation',expression='sin(n^2)',coefficients=['2','0','0'],rest=False,initial=['mal'],start=-2,count=5)
        result=execute(request);self.assertTrue(result['closed_form']);self.assertEqual(result['order'],0)
        self.equivalent(restore(result['cas_encoded']),sp.sin(N**2)/2)
        from numpy.testing import assert_allclose
        assert_allclose([v[0] for v in result['numeric_samples']],[float(sp.sin(n*n)/2) for n in range(-2,3)],atol=1e-15)
        ode=execute(dict(operation='ode',expression='sin(t^2)',coefficients=['2','0'],initial=[]))
        self.assertTrue(ode['evaluated']);self.equivalent(parse(ode['result']),sp.sin(T**2)/2)
        self.assertEqual(ode['output_variable'],'t');self.assertEqual(ode['order'],0)
        for point,source in [(0,'Piecewise((7,t==0),(sin(t)/t,True))'),(1,'Piecewise((7,t==1),(t,True))')]:
            answer=execute(dict(operation='ode',expression=source,coefficients=['2','0'],initial=[]))
            self.equivalent(parse(answer['result']).subs(T,point),sp.Rational(7,2))
        source='Piecewise((7,t==0),(sin(t)/t,True))'
        transformed=execute(dict(operation='fourier_angular',expression=source))
        self.equivalent(restore(transformed['cas_encoded']).subs(W,0),sp.pi)

        for kind in ('difference_equation','ode'):
            with self.assertRaises(ValueError):execute(dict(operation=kind,expression='1',coefficients=['0','0'],initial=[]))

    def test_short_firs_and_one_sample_window_fft_are_valid(self):
        from signallab_pc.filters import fir
        from signallab_pc.course_tools import window_fft
        from signallab_pc.model import Signal
        from scipy.signal import firwin
        from numpy.testing import assert_allclose
        for length in (1,2):
            for window in ('boxcar','hamming'):
                result=fir('lowpass',length,.2,window=window)
                assert_allclose(result.b,firwin(length,.2,fs=1.,window=window,scale=False),atol=1e-15)
        with self.assertRaises(ValueError):fir('highpass',2,.2)
        result=window_fft(Signal([2],origin=5),1,1,'boxcar',0,9)
        assert_allclose(result['signals'][0].values,[2])
        self.assertEqual(result['signals'][0].metadata['nfft'],1)

    def test_ode_results_keep_time_variable_and_domain_for_reuse(self):
        from signallab_pc.result_expressions import expression_result
        for coefficients,initial in [(['2','0'],[]),(['1','1'],['0'])]:
            request=dict(operation='ode',expression='1',coefficients=coefficients,initial=initial)
            result=execute(request);self.assertTrue(result['evaluated'])
            definition=expression_result({'request':request,'result':result})
            self.assertEqual(definition.variable,'t');self.assertTrue(any('t >= 0' in c for c in definition.conditions))


    def test_hyperbolic_shared_vocabulary_and_complex_branches(self):
        import numpy as np
        from numpy.testing import assert_allclose
        from signallab_pc.hyperbolic import NAMES,ALIASES,NUMERIC
        from signallab_pc.engine import evaluate_expression
        from signallab_pc.signal_notation import read,latex
        from signallab_pc.singularities import sample_symbolic
        from signallab_pc.scalar_expression import constant_value
        from signallab_pc.analytic_frequency import _sample
        from signallab_pc.matlab_import import expression as matlab_expression
        from signallab_pc.cas_engine import calculate,empty_state
        values=[sp.Integer(-2),-sp.Rational(1,2),sp.Integer(0),sp.Rational(1,2),sp.Integer(2),-2*sp.I,2*sp.I,1+sp.I,-1-sp.I]
        for name in (*NAMES,*ALIASES):
            canonical=ALIASES.get(name,name);fn=getattr(sp,canonical)
            for exact in values:
                expected=fn(exact)
                if expected.is_finite is not True:continue
                want=complex(expected.evalf(17));source=name+'('+sp.sstr(exact).replace('I','i')+')'
                with self.subTest(function=name,value=exact):
                    with np.errstate(all='raise'):actual=NUMERIC[name](complex(exact))
                    assert_allclose(actual,want,rtol=2e-14,atol=2e-14)
                    assert_allclose(constant_value(source),want,rtol=2e-14,atol=2e-14)
            with self.subTest(function=name,transport=True):
                want=complex(fn(sp.Rational(1,2)).evalf(17))
                assert_allclose(evaluate_expression(name+'(x)',np.array([.5])),[want],rtol=2e-14,atol=2e-14)
                assert_allclose(sample_symbolic(parse(name+'(t)'),T,[.5]),[want],rtol=2e-14,atol=2e-14)
                assert_allclose(_sample(parse(name+'(w)'),np.array([.5])),[want],rtol=2e-14,atol=2e-14)
                assert_allclose(matlab_expression(name+'(x)',{'x':np.array([.5])}),[want],rtol=2e-14,atol=2e-14)
                value=read(name+'(t)');self.assertFalse(value.atoms(sp.core.function.AppliedUndef));self.assertIn('t',latex(value))
                result=calculate(dict(state=empty_state(),source=name+'(1/2)',cell=1))
                assert_allclose(complex(restore(result['state']['results']['1']).evalf(17)),want,atol=2e-14)

    def test_hyperbolic_poles_and_principal_cut_sampling(self):
        import numpy as np
        from numpy.testing import assert_allclose
        from signallab_pc.hyperbolic import NUMERIC
        from signallab_pc.singularities import sample_symbolic
        from signallab_pc.engine import evaluate_expression
        from signallab_pc.cas_domains import function_domain
        for name in ('csch','coth','asech','acsch'):
            with self.subTest(pole=name),np.errstate(all='ignore'):
                self.assertFalse(np.isfinite(NUMERIC[name](0)))
                self.assertEqual(function_domain(name,[sp.S.Zero]),sp.false)
        from signallab_pc.matlab_import import expression as matlab_expression
        with np.errstate(all='raise'):
            assert_allclose(matlab_expression('acoth(x)',{'x':np.array([0,.5,-.5])}),[1j*np.pi/2,complex(sp.acoth(sp.Rational(1,2)).evalf()),complex(sp.acoth(-sp.Rational(1,2)).evalf())],atol=2e-14)
        for source,coords in [('atanh(t)',[2,-2]),('asinh(i*t)',[-2,2]),('acoth(t)',[0,.5,-.5]),('asech(t)',[-.5,.5]),('acsch(i*t)',[-.5,.5])]:
            with self.subTest(source=source):
                value=parse(source);want=[complex(value.subs(T,sp.Rational(str(x))).evalf(17)) for x in coords]
                assert_allclose(sample_symbolic(value,T,coords),want,atol=2e-14)
                assert_allclose(evaluate_expression(source,np.asarray(coords)),want,atol=2e-14)

    def test_hyperbolic_transform_pairs_and_convergence(self):
        from signallab_pc.fourier_ordinary_pairs import pairs
        for name,want in [('sinh',1/(S**2-1)),('cosh',S/(S**2-1))]:
            with self.subTest(transform='laplace',function=name):
                result=execute(dict(operation='laplace',expression=name+'(t)'))
                self.assertTrue(result['evaluated']);self.equivalent(expression(result),want)
        q=sp.exp(sp.Rational(1,3))
        for name,want in [('sinh',(Z/(Z-q)-Z/(Z-1/q))/2),('cosh',(Z/(Z-q)+Z/(Z-1/q))/2)]:
            with self.subTest(transform='z',function=name):
                result=self.direct(name+'(n/3)');self.assertTrue(result['evaluated']);self.equivalent(expression(result),want)
        for name,want in [('cosh',1/(1+W**2)+3/(9+W**2)),('sinh',1/(1+W**2)-3/(9+W**2))]:
            # sinh(t) is odd, so its transform is imaginary and odd.
            if name=='sinh':want=1/(1+sp.I*W)/2+1/(3-sp.I*W)/2-1/(3+sp.I*W)/2-1/(1-sp.I*W)/2
            with self.subTest(transform='fourier',function=name):
                result=execute(dict(operation='fourier_angular',expression='exp(-2*abs(t))*'+name+'(t)'))
                self.assertTrue(result['evaluated']);self.equivalent(expression(result),want)
        found,remainder=pairs(parse('exp(-abs(t))*cosh(2*t)'),T,W)
        self.assertEqual(found,0);self.assertNotEqual(remainder,0)



    def test_audit_ode_origin_impulse_preserves_prejump_initial_data(self):
        from signallab_pc.symbolic_process import explain
        req=dict(operation='ode',expression='3*Dirac(t)',coefficients=['1','1'],initial=['2'])
        r=explain(req,execute(req));self.equivalent(parse(r['result']),5*sp.exp(-T)*sp.Heaviside(T))
        self.assertEqual(r['initial_convention'],'0-')
        check=r['residual_check'];self.assertEqual(check['symbolic_residual'],'0')
        self.assertTrue(check['initial'][0]['satisfied']);self.assertEqual(check['initial'][0]['right_limit'],'5')
        self.assertEqual(check['initial'][0]['obtained'],'2')

    def test_audit_ode_without_derivatives_records_only_the_actual_division(self):
        from unittest.mock import patch
        from signallab_pc.symbolic_process import explain
        req=dict(operation='ode',expression='sin(t)',coefficients=['2','0'],initial=[])
        with patch('signallab_pc.impulse_pairs.unilateral_laplace',side_effect=AssertionError('Unexpected transform')):
            r=explain(req,execute(req))
        self.equivalent(parse(r['result']),sp.sin(T)/2)
        self.assertEqual(len(r['procedure']),1)
        self.assertNotIn('Laplace',' '.join(v['operation'] for v in r['procedure']))
        self.assertIn('División',' '.join(v['text'] for v in r['derivation']))

    def test_audit_ode_recorded_polynomial_identity_and_input_context(self):
        req=dict(operation='ode',expression='1',coefficients=['2','3','1'],initial=['4','5'],input_conditions=['a > 0'])
        r=execute(req)
        self.equivalent(parse(r['operator_polynomial'])*parse(r['Y(s)'])-parse(r['initial_correction']),parse(r['forcing_transform']))
        self.assertEqual(r['input_definition']['input_conditions'],['a > 0'])
        self.assertTrue(all(s['recorded'] and s['source'] for s in r['procedure']))
        json.dumps(r)

    def test_audit_stability_respects_anticausal_roc_in_both_domains(self):
        from signallab_pc.filters import Transfer
        for a,domain in [([1,-2],'digital'),([1,-1],'analog')]:
            with self.subTest(domain=domain):
                anti=Transfer([1],a,domain,roc={'mode':'left'})
                causal=Transfer([1],a,domain,roc={'mode':'right'})
                self.assertTrue(anti.stability().startswith('Estable'))
                self.assertTrue(causal.stability().startswith('Inestable'))
                self.assertTrue(anti.causal_pole_stability().startswith('Inestable'))

    def test_audit_improper_and_unspecified_roc_are_not_unconditional_stability(self):
        from signallab_pc.filters import Transfer
        for roc in (None,{'mode':'right'}):
            self.assertIn('Inestable',Transfer([1,0],[1],'analog',roc=roc).stability())
        self.assertIn('Falta especificar la ROC',Transfer([1],[1,-.5]).stability())
        for domain in ('analog','digital'):
            self.assertTrue(Transfer([0],[1,0],domain).stability().startswith('Estable'))

    def test_audit_difference_formula_is_checked_independently_of_sample_count(self):
        for start in (-3,0,4):
            with self.subTest(start=start):
                req=dict(operation='difference_equation',coefficients=['1','-1/2'],initial=['4'],rest=False,start=start,count=1,expression='1')
                r=execute(req)
                self.assertTrue(r['symbolic_check']['verified'],r['symbolic_check'])
                self.assertEqual(len(r['numeric_samples']),1)
                y=parse(r['result']);self.equivalent(y.subs(N,start),3)
                self.equivalent(parse(r['unilateral_output']),Z*(3*Z-2)/((Z-1)*(Z-sp.Rational(1,2))))
                self.assertTrue(r['procedure'])

    def test_audit_recurrence_checker_detects_an_incorrect_formula(self):
        from signallab_pc.equation_checks import difference_symbolic
        req=dict(operation='difference_equation',coefficients=['1','-1/2'],initial=['4'],rest=False,start=0,count=1,expression='1')
        r=execute(req);r['result']='2'
        self.assertIs(difference_symbolic(req,r)['verified'],False)

    def test_audit_procedure_views_preserve_legacy_records_and_serialization(self):
        from signallab_pc.procedure import views,step
        old={'title':'Guardado','text':'Explicación','formula':'x=1'}
        self.assertEqual(views([old]),[old])
        records=[step('Despejar','División','2*x=4','x=2',conditions='2 != 0',source='test')]
        self.assertEqual(views(json.loads(json.dumps(records))),views(records))
        self.assertIn('Validez',views(records)[0]['text'])



    def test_audit_library_examples_match_independent_expected_expressions(self):
        from signallab_pc.library_catalog import example_records
        from signallab_pc.filters import Transfer
        from signallab_pc.system_conditions import record
        for example in example_records():
            with self.subTest(example=example['id']):
                req=example['request'];r=execute(req);self.assertTrue(r['evaluated'])
                actual=parse(r['transfer']) if 'transfer' in r else restore(r['cas_encoded']) if r.get('cas_encoded') else expression(r)
                expected=parse(example['expected']);variable={'t':T,'n':N,'w':W,'z':Z}[example['variable']]
                points=[sp.Rational(1,3),1,2] if req['operation']=='ode' else range(5) if req['operation']=='difference_equation' else [-3,-1,0,1,3]
                if variable==Z:self.equivalent(actual,expected)
                else:
                    for point in points:self.equivalent(sp.simplify(actual.subs(variable,point)),sp.simplify(expected.subs(variable,point)))
                if 'system' in example:self.assertTrue(record(Transfer(**example['system']))['bibo_stability'].startswith('Sí:'))

    def test_audit_library_catalog_preserves_existing_articles_and_routes(self):
        from signallab_pc.library_catalog import sections,CATEGORIES
        from signallab_pc.help_content import sections as old_sections
        from signallab_pc.library_articles import article_blocks
        values=sections();self.assertEqual(len({v['article_id'] for v in values}),len(values))
        self.assertTrue(all(v.get('purpose') and v.get('usage') for v in values))
        self.assertEqual(set(v['category'] for v in values),set(CATEGORIES))
        for old in old_sections():
            matches=[v for v in values if v['route']==old['route'] and v.get('content_kind')=='tool']
            self.assertEqual(len(matches),1,old['route']);self.assertEqual(matches[0]['blocks'],article_blocks(old['route']))
        self.assertEqual(sum(bool(v.get('example')) for v in values),8)

    def test_audit_transform_receipts_never_claim_pending_answers_are_solved(self):
        from signallab_pc.procedure import transform_records
        req=dict(operation='laplace',expression='f(t)')
        r=dict(result='LaplaceTransform(f(t),t,s)',evaluated=False,condition='True')
        rows=transform_records(req,r)
        self.assertIn('sin resolver',rows[0]['operation']);self.assertEqual(rows[0]['after'],r['result'])
        r=execute(dict(operation='z_inverse_expression',expression='z/(z-2)',roc='left',include_samples=False))
        self.assertTrue(r['procedure']);self.assertIn('|z| < 2',r['procedure'][-1]['conditions'])



    def test_audit_optional_procedure_failure_cannot_discard_a_transform(self):
        from unittest.mock import patch
        with patch('signallab_pc.procedure.transform_records',side_effect=RuntimeError('record failure')),patch('signallab_pc.runtime_diagnostics.diagnostic'):
            r=execute(dict(operation='laplace',expression='exp(-t)'))
        self.assertTrue(r['evaluated']);self.equivalent(expression(r),1/(S+1))
        self.assertTrue(r['derivation_notice']);self.assertEqual(r['procedure'],[])



    def test_audit_true_poles_cannot_become_large_finite_roundoff_values(self):
        import numpy as np
        from signallab_pc.engine import evaluate_expression,ExpressionError
        from signallab_pc.singularities import sample_symbolic
        from signallab_pc.analytic_frequency import _sample
        for source in ('tan(pi*n/2)','1/sin(pi*n)','sech(i*pi*n/2)','10^(-20)*tan(pi*n/2)'):
            with self.subTest(source=source):
                with self.assertRaises(ExpressionError):evaluate_expression(source,np.array([1]))
        with self.assertRaises(ValueError):sample_symbolic(parse('tan(pi*t/2)'),T,[1])
        self.assertFalse(np.isfinite(_sample(parse('tan(pi*w/2)'),np.array([1.]))[0]))

    def test_audit_pole_checks_preserve_finite_neighbours_and_inactive_branches(self):
        import numpy as np
        from numpy.testing import assert_allclose
        from signallab_pc.engine import evaluate_expression
        assert_allclose(evaluate_expression('cos(pi*n/2)*tan(pi*n/2)',np.array([1.])),[1],atol=1e-14)
        assert_allclose(evaluate_expression('where(n==1,7,tan(pi*n/2))',np.array([1.])),[7])
        assert_allclose(evaluate_expression('step(n-2)*tan(pi*n/2)',np.array([1.])),[0])
        assert_allclose(evaluate_expression('n^2%3',np.arange(5)),[0,1,1,0,1])
        self.equivalent(parse('n^2%3'),sp.Mod(N**2,3))
        for value in [.99999999,1.00000001]:
            actual=evaluate_expression('tan(pi*n/2)',np.array([value]))
            self.assertTrue(np.isfinite(actual).all())


if __name__=='__main__':unittest.main()
