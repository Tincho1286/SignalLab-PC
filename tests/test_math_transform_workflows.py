"""Distribution scaling, transform conventions and energy over exact supports."""
import unittest

import numpy as np
import sympy as sp

from signallab_pc.cas_engine import encode, restore
from signallab_pc.analytic_frequency import analyze_expression
from signallab_pc.measures_symbolic import measure_expression
from signallab_pc.symbolic import N, S, T, TAU, W, Z, execute, parse


class DistributionTransformContracts(unittest.TestCase):
    def transform(self, operation, expression, **options):
        result = execute(dict(operation=operation, expression=expression, **options))
        self.assertTrue(result['evaluated'], result.get('scope'))
        return restore(result['cas_encoded']) if 'cas_encoded' in result else parse(result['result'])

    def test_fourier_applies_product_rule_and_negative_affine_scale_to_delta_derivative(self):
        transformed = self.transform('fourier_angular', '(t+1)*DiracDelta(4-2*t,1)')
        expected = (1-3*sp.I*W)*sp.exp(-2*sp.I*W)/4
        self.assertEqual(sp.simplify(transformed-expected), 0)
        inverse = self.transform('inverse_fourier_angular', 'exp(-2*i*w)*(1-3*i*w)/4')
        expected_inverse = (sp.DiracDelta(T-2)-3*sp.DiracDelta(T-2,1))/4
        self.assertEqual(sp.simplify(inverse-expected_inverse), 0)

    def test_laplace_preserves_zero_endpoint_and_discards_impulses_before_it(self):
        result = self.transform('laplace',
                                '2*DiracDelta(t)+DiracDelta(t+1)+(t+1)*DiracDelta(4-2*t,1)'
                                '+Step(t-3)*exp(-2*(t-3))')
        expected = 2+(1-3*S)*sp.exp(-2*S)/4+sp.exp(-3*S)/(S+2)
        self.assertEqual(sp.simplify(result-expected), 0)

    def test_fourier_harmonic_derivative_pairs_keep_the_locations_and_areas(self):
        result = self.transform('fourier_angular', 't*cos(3*t)+2*sin(4*t)')
        expected = (
            sp.I*sp.pi*(sp.DiracDelta(W-3,1)+sp.DiracDelta(W+3,1))
            +2*sp.I*sp.pi*(sp.DiracDelta(W+4)-sp.DiracDelta(W-4))
        )
        self.assertEqual(sp.simplify(result-expected), 0)
        result = self.transform('inverse_fourier_angular', '3*DiracDelta(w-2)+DiracDelta(w+1)')
        expected = (3*sp.exp(2*sp.I*T)+sp.exp(-sp.I*T))/(2*sp.pi)
        self.assertEqual(sp.simplify(result-expected), 0)

    def test_dtft_inverse_counts_the_periodic_seam_only_once_even_with_regular_part(self):
        result = self.transform('inverse_dtft_expression',
                                '2*pi*(DiracDelta(w-pi)+DiracDelta(w+pi))+3*exp(-2*i*w)')
        for n in range(-4,6):
            self.assertEqual(sp.simplify(result.subs(N,n)), sp.Integer((-1)**abs(n)+3*(n==2)))

    def test_distribution_weight_at_a_jump_is_rejected_with_cause(self):
        for expression in ['Step(t)*DiracDelta(t)', 'sign(t)*DiracDelta(t,1)',
                           'DiracDelta(t)*DiracDelta(t-1)', 'DiracDelta(t)**2']:
            with self.subTest(expression=expression), self.assertRaisesRegex(ValueError, 'Dirac|impulsos'):
                self.transform('fourier_angular', expression)


class EnergyAndPowerContracts(unittest.TestCase):
    def test_partial_and_multi_cycle_intervals_match_sample_by_sample(self):
        expression = 'Repeat(n+i,n,3,0)'
        for a,b in [(-2,-2), (-1,0), (-4,8)]:
            with self.subTest(a=a,b=b):
                result = measure_expression(dict(expression=expression, domain='discrete', lower=str(a), upper=str(b)))
                expected = sum((n%3)**2+1 for n in range(a,b+1))
                self.assertEqual(parse(result['energy']['exact']), expected)
                self.assertEqual(sp.simplify(parse(result['mean_square']['exact'])-sp.Rational(expected,b-a+1)), 0)
                self.assertEqual(result['energy']['status'], 'finite')
                self.assertEqual(result['bounds'], [str(a),str(b)])

    def test_discrete_explicit_period_requires_integers_and_preserves_harmonic_aliasing(self):
        request = dict(expression='cos(pi*n/3)+cos(7*pi*n/3)', domain='discrete', mode='periodic')
        result = measure_expression({**request, 'period':'12'})
        self.assertEqual(parse(result['mean_square']['exact']), 2)
        self.assertEqual(parse(result['period_energy']['exact']), 24)
        self.assertEqual(result['energy']['status'], 'divergent')
        self.assertTrue(result['period_verified'])
        for period, reason in [('0','positivo'), ('3','repita'), ('3/2','enteros')]:
            with self.subTest(period=period), self.assertRaisesRegex(ValueError,reason):
                measure_expression({**request, 'period':period})

    def test_prevents_ordinary_energy_for_distributions_and_reversed_or_nonreal_bounds(self):
        for options, reason in [
            ({'expression':'DiracDelta(t)'}, 'función ordinaria'),
            ({'expression':'cos(w)'}, 'Usá sólo t'),
            ({'lower':'i'}, 'constantes reales'),
            ({'upper':'-1'}, 'creciente'),
            ({'domain':'frequency'}, 'Dominio o alcance'),
        ]:
            with self.subTest(options=options), self.assertRaisesRegex(ValueError, reason):
                measure_expression({'expression':'cos(t)', **options})


class ExpressionGridContracts(unittest.TestCase):
    def test_grid_preserves_exact_line_areas_and_excludes_one_periodic_endpoint(self):
        expression = 'exp(i*w)+2*DiracDelta(w+pi)+2*DiracDelta(w-pi)+3*DiracDelta(w)'
        base = dict(operation='expression_grid', variable='w', expression=expression,
                    start=-np.pi, stop=np.pi, start_exact='-pi', stop_exact='pi', count=17,
                    periodic_frequency=True, allow_distribution=True)
        regular = execute(base)
        self.assertEqual(regular['dirac_at_zero'], [3.,0.])
        self.assertEqual(regular['dirac_terms'], [[-np.pi,[2.,0.]]])
        np.testing.assert_allclose([complex(*pair) for pair in regular['samples']],
                                   np.exp(1j*np.linspace(-np.pi,np.pi,17)), atol=1e-13)
        conditioned = execute({**base, 'encoded':encode(parse(expression)),
                               'condition':'Ne(w,0)', 'allow_undefined':True})
        self.assertNotIn('dirac_at_zero', conditioned)
        self.assertEqual(conditioned['dirac_terms'], regular['dirac_terms'])
        self.assertIsNone(conditioned['samples'][8])
        self.assertEqual(conditioned['undefined_count'], 1)

    def test_invalid_or_unrepresentable_grid_cannot_change_number_of_samples(self):
        base = dict(operation='expression_grid', variable='w', expression='1/(1+w^2)',
                    start=-1., stop=1., count=9)
        for options, reason in [
            ({'count':2.9}, 'entero'),
            ({'count':True}, 'entero'),
            ({'count':1}, 'dos puntos'),
            ({'start':-1e308, 'stop':1e308}, 'excede el rango'),
            ({'start':1., 'stop':np.nextafter(1.,2.)}, 'precisión'),
            ({'start':-np.inf}, 'rejilla finita'),
            ({'variable':'s'}, 'variable de muestreo'),
            ({'expression':'a+w'}, 'parámetros: a'),
            ({'expression':'DiracDelta(w)'}, 'distribución'),
            ({'condition':'w>0'}, 'condiciones'),
        ]:
            with self.subTest(options=options), self.assertRaisesRegex(ValueError,reason):
                execute({**base, **options})
        result = execute(base)
        self.assertEqual(result['step'],.25)
        np.testing.assert_allclose([complex(*p) for p in result['samples']], 1/(1+np.linspace(-1,1,9)**2))


class ContinuousCombinationContracts(unittest.TestCase):
    def test_convolving_a_shifted_delta_derivative_produces_the_pulse_edges(self):
        spec = dict(operation='continuous_convolution',causal=False,
                    left='DiracDelta(t-1,1)',right='Piecewise((1,0<=t<2),(0,True))')
        response=execute(spec)
        self.assertTrue(response['evaluated'])
        expected=sp.DiracDelta(T-1)-sp.DiracDelta(T-3)
        self.assertEqual(sp.simplify(parse(response['result'])-expected),0)
        response=execute({**spec,'causal':True, 'left':'DiracDelta(t+1)+DiracDelta(t)',
                          'right':'exp(-2*t)'})
        value=parse(response['result'])
        for p in [-2,-1,0,1,2]:
            target=sp.exp(-2*p) if p>=0 else 0
            self.assertEqual(sp.simplify(value.subs(T,p)-target),0)

    def test_complex_bilateral_correlation_conjugates_the_weight_and_flips_lag(self):
        request=dict(operation='continuous_correlation',
                     left='(1+2*i)*DiracDelta(t-2)',right='(3+i)*DiracDelta(t+1,1)')
        result=execute(request)
        self.assertTrue(result['evaluated'])
        self.assertEqual(result['output_variable'],'tau')
        self.assertIsNone(result['period'])
        expected=-(1+2*sp.I)*(3-sp.I)*sp.DiracDelta(TAU-3,1)
        self.assertEqual(sp.simplify(parse(result['result'])-expected),0)

    def test_periodic_correlation_uses_the_declared_interval_and_complex_gain(self):
        request=dict(operation='continuous_correlation',left='1+i*sin(t)',right='cos(t)',period='2*pi')
        result=execute(request)
        self.assertTrue(result['evaluated'])
        self.assertEqual(parse(result['period']).simplify(),2*sp.pi)
        self.assertEqual(sp.simplify(parse(result['result'])-sp.I*sp.pi*sp.sin(TAU)),0)
        for change,reason in [
            ({'period':'-1'}, 'positiva'),
            ({'period':'p'}, 'constante'),
            ({'left':'tau*cos(t)'},'retardo tau'),
        ]:
            with self.subTest(change=change), self.assertRaisesRegex(ValueError,reason):
                execute({**request, **change})


class SystemFormulaContracts(unittest.TestCase):
    def test_hz_and_hs_reject_infinite_values_and_nonordinary_distributions(self):
        for domain,variable in [('analog',S),('digital',Z)]:
            request=dict(operation='system_formula',domain=domain)
            for expression,reason in [
                ('-oo','no finito'), ('+oo','no finito'), ('1/(2-2)','no finito'),
                (f'2+DiracDelta({variable}-1)','distribución'), ('exp(-t)','sin variables temporales'),
            ]:
                with self.subTest(expression=expression, domain=domain),self.assertRaisesRegex(ValueError,reason):
                    execute({**request,'expression':expression})
            defined=execute({**request,'expression':f'exp(-2*{variable})'})
            self.assertTrue(defined['evaluated'])
            self.assertEqual(defined['model_kind'],'expression')
            self.assertEqual(sp.simplify(parse(defined['transfer'])-sp.exp(-2*variable)),0)

    def test_expression_frequency_reports_removable_values_and_preserves_phase_and_delay(self):
        from signallab_pc.frequency_measurements import readings

        request=dict(operation='system_frequency_expression',domain='digital',
                     expression='exp(-2*i*w)*sin(w)/w')
        declared=execute(request)
        omega=np.array([-.6,-.1,0.,.1,.6])
        exact,data=analyze_expression(declared,request,omega,period=.01,margins=True)
        self.assertEqual(data.phase_kind,'principal')
        np.testing.assert_allclose(data.response,np.exp(-2j*omega)*np.sinc(omega/np.pi),atol=1e-14)
        np.testing.assert_allclose(data.delay,2,atol=1e-13)
        self.assertEqual(data.system.sample_period_s,.01)
        self.assertFalse(data.margins['available'])
        self.assertIn('no racional',data.margins['reason'])
        self.assertEqual(exact['group_delay_jump_samples'],0)
        self.assertNotIn('frequency_limit_extensions',declared)
        rows,_=readings(data,[0.])
        self.assertEqual(rows[0]['real'],1.)
        self.assertAlmostEqual(rows[0]['delay'],2.)

    def test_pointwise_assignments_need_a_common_derivative_for_group_delay(self):
        omega=np.array([np.pi-.1,np.pi,np.pi+.1])
        regular='exp(-3*i*(w-pi))'
        for condition,pair,measurable in [
            ('Eq(w,pi)', f'(1,Eq(w,pi)),({regular},True)', True),
            ('Ne(w,pi)', f'({regular},Ne(w,pi)),(3,True)', False),
        ]:
            with self.subTest(condition=condition):
                request=dict(operation='system_frequency_expression', domain='digital',
                             expression=f'Piecewise({pair})')
                exact,data=analyze_expression(execute(request),request,omega)
                np.testing.assert_allclose(data.delay[[0,2]],3.,atol=1e-13)
                if measurable:
                    self.assertAlmostEqual(data.delay[1],3.)
                    self.assertEqual(exact['group_delay_jump_samples'],0)
                else:
                    self.assertEqual(data.response[1],3.)
                    self.assertTrue(np.isnan(data.delay[1]))
                    self.assertEqual(exact['group_delay_jump_samples'],1)

    def test_frequency_jump_masks_delay_and_periodic_equal_limits_preserve_it(self):
        omega=np.array([-.1,0.,.1,.9,1.,1.1])
        for expression,junctions,expected in [
            ('exp(-i*Mod(w,1))',[1,4],1.),
            ('exp(-2*pi*i*Mod(w,1))',[],2*np.pi),
            ('exp(-2*i*w)*Step(w)',[0,1],2.),
        ]:
            with self.subTest(expression=expression):
                request=dict(operation='system_frequency_expression',domain='digital',expression=expression)
                exact,data=analyze_expression(execute(request),request,omega)
                self.assertEqual(np.flatnonzero(~np.isfinite(data.delay)).tolist(),junctions)
                np.testing.assert_allclose(data.delay[np.isfinite(data.delay)],expected,atol=1e-13)
                self.assertGreaterEqual(exact['group_delay_jump_samples'],len(junctions)-(1 if expression.endswith('Step(w)') else 0))

    def test_cas_frequency_context_excludes_exact_resonance_without_masking_nearby_samples(self):
        omega=np.array([-np.pi,-1e-30,0.,1e-30,np.pi,2*np.pi])
        request=dict(operation='system_frequency_expression',domain='digital',expression='exp(-i*w)')
        imported={'cas_answer':{'frequency_units':'rad/muestra','frequency_condition':'Ne(cos(w)-1,0)'}}
        exact,data=analyze_expression(execute(request),{**request,'source_calculation':imported},omega)
        self.assertEqual(exact['masked_frequency_samples'],2)
        expected=np.exp(-1j*omega)
        mask=np.array([True,True,False,True,True,False])
        np.testing.assert_array_equal(np.isfinite(data.response),mask)
        np.testing.assert_allclose(data.response[mask],expected[mask],atol=1e-14)
        np.testing.assert_allclose(data.delay[mask],1.,atol=1e-14)
        incompatible={'cas_answer':{**imported['cas_answer'],'frequency_units':'rad/s'}}
        with self.assertRaisesRegex(ValueError,'unidad de frecuencia'):
            analyze_expression(execute(request),{**request,'source_calculation':incompatible},omega)
