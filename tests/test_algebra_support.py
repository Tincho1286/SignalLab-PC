"""Independent checks for poles, support and real-axis boundary conventions."""
import unittest

import numpy as np
import sympy as sp

from signallab_pc.symbolic import execute,parse,S,T,TAU,W,Z


class AlgebraSupportTests(unittest.TestCase):
    def assert_value(self, expression, variable, point, expected):
        actual = parse(expression).subs(variable,point)
        self.assertEqual(sp.simplify(actual-expected),0)

    def test_convolution_uses_full_impulse_weights_inside_the_causal_support(self):
        for left,right,expected in (
            ('Dirac(t)','exp(-t)',sp.exp(-2)),
            ('exp(-t)','Dirac(2*t)',sp.exp(-2)/2),
            ('3*Dirac(t-1)','exp(-t)',3*sp.exp(-1)),
            ('Dirac(t+1)','exp(-t)',0),
        ):
            with self.subTest(left=left,right=right):
                result = execute(dict(operation='continuous_convolution',left=left,right=right,causal=True))
                self.assertTrue(result['evaluated'])
                self.assert_value(result['result'],T,2,expected)
        result = execute(dict(operation='continuous_convolution',left='2*Dirac(t)',right='3*Dirac(t-1)',causal=True))
        self.assertEqual(sp.simplify(parse(result['result'])-6*sp.DiracDelta(T-1)),0)
        result = execute(dict(operation='continuous_convolution',left='Dirac(t)',right='exp(-t)',causal=True))
        self.assert_value(result['result'],T,0,1)
        result = execute(dict(operation='continuous_convolution',left='Dirac(t,1)',
                              right='exp(-t)*Step(t)',causal=True))
        expected = sp.DiracDelta(T)-sp.exp(-T)*sp.Heaviside(T,1)
        self.assertEqual(sp.simplify(parse(result['result'])-expected),0)

    def test_cross_correlation_integrates_the_overlap_on_both_sides(self):
        for b in (1,3):
            result = execute(dict(operation='continuous_correlation',left='exp(-t)*Step(t)',
                                  right=f'exp(-{b}*t)*Step(t)'))
            self.assertTrue(result['evaluated'])
            for lag in (-2,0,3):
                expected = sp.exp(b*lag-(1+b)*max(0,lag))/(1+b)
                self.assert_value(result['result'],TAU,lag,expected)

    def test_laplace_uses_the_tail_after_partitioning_bounded_support(self):
        for source,abscissa,point,value in (
            ('Step(t-1)-Step(t-3)','-oo',0,2),
            ('t*exp(-2*t)*(Step(t)-Step(t-1))','-oo',-2,sp.S.Half),
            ('exp(t)*(Step(t)-Step(t-1))+exp(-2*t)*Step(t)','-2',1,sp.Rational(4,3)),
        ):
            with self.subTest(source=source):
                result = execute(dict(operation='laplace',interpretation='unilateral',expression=source))
                self.assertTrue(result['evaluated'])
                self.assertEqual(result['convergence_abscissa'],abscissa)
                self.assert_value(result['result'],S,point,value)

    def test_weighted_impulses_are_evaluated_at_real_simple_roots(self):
        for source,expected in (('(t+2)*Dirac(t^2-1)',3*sp.exp(-S)/2),
                                ('(t+3)*Dirac(t^2-4)',5*sp.exp(-2*S)/4),
                                ('(Step(t)-Step(t-2))*Dirac(t^2-1)',sp.exp(-S)/2)):
            with self.subTest(source=source):
                result = execute(dict(operation='laplace',interpretation='unilateral',expression=source))
                self.assertTrue(result['evaluated'])
                self.assertEqual(sp.simplify(parse(result['result'])-expected),0)

    def test_bilateral_inverse_keeps_shifts_and_drops_only_canceled_poles(self):
        cases = (
            ('(1-exp(-s))/s','0','-oo',(.5,1)),
            ('(1-exp(-3*(s+2)))/(s+2)','-2','-oo',(1,sp.exp(-2))),
            ('(1-exp(-s))/s+1/(s+3)','0','-3',(2,sp.exp(-6))),
        )
        for source,sigma,lower,(point,expected) in cases:
            with self.subTest(source=source):
                result = execute(dict(operation='inverse_laplace',interpretation='bilateral',
                                      laplace_roc='line',sigma=sigma,expression=source))
                self.assertTrue(result['evaluated'])
                self.assertEqual((result['roc_lower'],result['roc_upper']),(lower,'oo'))
                self.assert_value(result['result'],T,sp.Rational(str(point)),expected)

    def test_fourier_of_bounded_support_can_be_used_at_zero(self):
        for source,area in (('Step(t)-Step(t-1)',1),('Step(t-1)-Step(t-3)',2),
                            ('t*(Step(t)-Step(t-1))',sp.S.Half)):
            with self.subTest(source=source):
                result = execute(dict(operation='fourier_angular',expression=source))
                self.assertTrue(result['evaluated'])
                self.assertEqual(result['condition'],'True')
                self.assert_value(result['result'],W,0,area)
                grid = execute(dict(operation='expression_grid',expression=result['result'],
                                    variable='w',start=-1,stop=1,count=3,allow_undefined=True,
                                    condition=result['condition'],encoded=result.get('cas_encoded')))
                self.assertEqual(grid['samples'][1],[float(area),0])

    def test_improper_energy_distinguishes_divergent_and_integrable_poles(self):
        for source,status,energy in (
            ('1/sqrt(abs(t-1))','divergent','oo'),
            ('exp(-2*t)/(t-1)','divergent','oo'),
            ('abs(t-1)^(-1/4)','finite','4'),
        ):
            with self.subTest(source=source):
                result = execute(dict(operation='signal_measures_expression',expression=source,
                                      domain='continuous',mode='interval',lower='0',upper='2'))
                self.assertEqual((result['energy']['status'],result['energy']['exact']),(status,energy))
        whole = execute(dict(operation='signal_measures_expression',domain='continuous',mode='global',
                             expression='exp(-abs(t))/sqrt(abs(t))'))
        self.assertEqual((whole['energy']['exact'],whole['mean_square']['exact']),('oo','oo'))

    def test_discrete_measure_uses_the_cycle_or_parseval_as_applicable(self):
        cases = (
            ('where(Eq(Mod(n,2),0),cos(pi*n/2),0)','oo','1/2'),
            ('sin(0.3*pi*(n-4))/(pi*(n-4))','3/10','0'),
            ('2*sin(pi*(n+3)/4)/(pi*(n+3))','1','0'),
            ('where(Eq(n,0),1,sin(pi*n/2)/(pi*n))','5/4','0'),
        )
        for source,energy,power in cases:
            with self.subTest(source=source):
                result = execute(dict(operation='signal_measures_expression',expression=source,
                                      domain='discrete',mode='global'))
                self.assertEqual((result['energy']['exact'],result['mean_square']['exact']),(energy,power))

    def test_z_annulus_excludes_only_an_actual_origin_pole(self):
        for source,stop,defined in (('1','1',False),('2^n','2',False),('cos(pi*n)','0',True)):
            with self.subTest(source=source,stop=stop):
                result = execute(dict(operation='z_expression',expression=source,lower='-oo',upper=stop))
                condition = sp.sympify(result['branches'][0]['condition'],locals={'z':Z})
                self.assertEqual(bool(condition.subs(Z,0)),defined)
                self.assertTrue(bool(condition.subs(Z,sp.S.Half)))

    def test_cas_shares_laplace_and_integer_piecewise_summation(self):
        from signallab_pc.cas_engine import restore

        result = execute(dict(operation='cas_worksheet',cell=1,
                              source='laplace_transform(t*exp(-2*t)*Step(t),t,s)'))
        value,abscissa,condition = restore(result['state']['results']['1'])
        self.assertEqual(sp.simplify(value-1/(next(iter(value.free_symbols))+2)**2),0)
        self.assertEqual((abscissa,condition),(-2,sp.true))
        for text,expected in (
            ('sum(where(Eq(n,0),1,sin(pi*n)/(pi*n)),n,-oo,oo)','1'),
            ('sum(where(Eq(k,2),3,sin(pi*(k-2))/(pi*(k-2))),k,-oo,oo)','3'),
        ):
            result = execute(dict(operation='cas_worksheet',cell=1,source=text))
            self.assertEqual(result['text'],expected)

    def test_group_delay_detects_continuous_phase_corners(self):
        from signallab_pc.analytic_frequency import analyze_expression

        for formula,points,values in (
            ('exp(-i*abs(w))',[-.5,0,.5],[-1,np.nan,1]),
            ('where(w<1,exp(-i*w),exp(-i*(2*w-1)))',[.75,1,1.25],[1,np.nan,2]),
            ('(1+abs(w))*exp(-3*i*w)',[-.5,0,.5],[3,3,3]),
        ):
            request = dict(operation='system_frequency_expression',domain='digital',expression=formula)
            _,data = analyze_expression(execute(request),request,np.array(points,dtype=float))
            np.testing.assert_allclose(data.delay,values,atol=1e-12,equal_nan=True)
