import unittest
import numpy as np
import sympy as sp
from signallab_pc.symbolic import execute,parse,T,W
from signallab_pc.fourier import energy_density
from signallab_pc.model import Signal

class SymbolicFourierTests(unittest.TestCase):
    def transform(self,expression,inverse=False):return execute(dict(operation='inverse_fourier_angular' if inverse else 'fourier_angular',expression=expression))
    def test_gaussian_angular_and_inverse(self):
        direct=self.transform('exp(-t^2)');self.assertTrue(direct['evaluated']);self.assertEqual(direct['condition'],'True')
        self.assertEqual(sp.simplify(parse(direct['result'])-sp.sqrt(sp.pi)*sp.exp(-W**2/4)),0)
        inverse=self.transform(direct['result'],True)
        self.assertEqual(sp.simplify(parse(inverse['result'])-sp.exp(-T**2)),0)
    def test_two_sided_exponential(self):
        result=self.transform('exp(-abs(t))')
        self.assertEqual(sp.simplify(parse(result['result'])-2/(1+W**2)),0)
    def test_time_shift_phase(self):
        result=self.transform('exp(-(t-2)^2)')
        self.assertEqual(sp.simplify(parse(result['result'])-sp.sqrt(sp.pi)*sp.exp(-W**2/4)*sp.exp(-2*sp.I*W)),0)
    def test_unilateral_laplace_of_shifted_pulse_uses_a_complete_cycle(self):
        from signallab_pc.symbolic import S
        result=execute(dict(operation='laplace',interpretation='unilateral',expression='PulseTrain(t+1/4,1,1/2)'))
        self.assertTrue(result['evaluated']);self.assertEqual(result['convergence_abscissa'],'0')
        expected=(1-sp.exp(-S/4)+sp.exp(-3*S/4)-sp.exp(-S))/(S*(1-sp.exp(-S)))
        self.assertEqual(sp.simplify(parse(result['result'])-expected),0)
    def test_gated_periodic_transforms_respect_the_actual_support(self):
        from signallab_pc.symbolic import S,Z
        clipped='(Step(t-1)-Step(t-6))*PulseTrain(t,3,2)'
        for mode in ('unilateral','bilateral'):
            with self.subTest(mode=mode):
                r=execute(dict(operation='laplace',interpretation=mode,expression=clipped))
                self.assertTrue(r['evaluated'])
                self.assertEqual(r.get('roc_lower',r.get('convergence_abscissa')),'-oo')
                self.assertEqual(parse(r['result']).subs(S,0),3)
        sequence='Step(n-3)*PulseTrain(n,5,2)'
        r=execute(dict(operation='z_expression',expression=sequence,lower='-oo',upper='oo'))
        self.assertTrue(r['evaluated'])
        self.assertEqual(sp.cancel(parse(r['branches'][0]['expression'])-(Z**-5+Z**-6)/(1-Z**-5)),0)

    def test_bilateral_laplace_of_multiple_continuous_cycles(self):
        from signallab_pc.impulse_pairs import distribution_parts
        from signallab_pc.symbolic import S

        trains = 'PulseTrain(t,1,1/4)+PulseTrain(t,sqrt(2),1/2)'
        req = dict(operation='laplace', interpretation='bilateral')
        full = execute(dict(req, expression=trains))
        self.assertTrue(full['convergence_empty'])
        spectrum = parse(full['boundary_fourier'])
        ordinary, lines = distribution_parts(spectrum, W, -2*sp.pi, 2*sp.pi)
        self.assertEqual(ordinary, 0)
        self.assertEqual(sp.simplify(dict(lines)[0] - sp.pi*(1 + sp.sqrt(2))/2), 0)

        causal = execute(dict(req, expression=f'Step(t)*({trains})'))
        self.assertTrue(causal['evaluated'])
        self.assertEqual((causal['roc_lower'], causal['roc_upper']), ('0', 'oo'))
        expected = (1-sp.exp(-S/4))/(S*(1-sp.exp(-S))) + (1-sp.exp(-S/2))/(S*(1-sp.exp(-S*sp.sqrt(2))))
        self.assertEqual(sp.simplify(parse(causal['result']) - expected), 0)

    def test_inverse_of_a_copied_periodic_spectrum_has_no_provenance(self):
        forward=self.transform('PulseTrain(t-1/4,1,1/4)')
        inverse=self.transform(forward['result'],True)
        self.assertTrue(inverse['evaluated'])
        waveform=parse(inverse['result'])
        grid=[-sp.Rational(3,4),0,sp.Rational(1,4),sp.Rational(3,8),sp.Rational(1,2),sp.Rational(11,8)]
        self.assertEqual([sp.simplify(waveform.subs(T,point)) for point in grid],
                         [sp.S.Half,0,sp.S.Half,1,sp.S.Half,1])
    def test_a_finite_periodic_edit_preserves_lines_and_the_ordinary_correction(self):
        from signallab_pc.impulse_pairs import distribution_parts
        from signallab_pc.symbolic import N
        waveform='(1-(Step(t)-Step(t-4)))*PulseTrain(t,4,2)'
        spectrum=self.transform(waveform)
        self.assertTrue(spectrum['evaluated'] and spectrum['distribution'])
        ordinary,lines=distribution_parts(parse(spectrum['result']),W,-sp.pi,sp.pi,right_open=True)
        self.assertEqual(sp.simplify(ordinary.subs(W,0)),-2)
        self.assertEqual(sp.simplify(dict(lines)[0]),sp.pi)
        sequence='(1-(Step(n)-Step(n-5)))*ImpulseTrain(n,5)'
        req=dict(expression=sequence,lower='-oo',upper='oo')
        d=execute(dict(operation='dtft_expression',**req));z=execute(dict(operation='z_expression',**req))
        self.assertTrue(d['distribution'] and z['boundary_distribution'])
        self.assertEqual(d['result'],z['boundary_dtft'])
        inverse=execute(dict(operation='inverse_dtft_expression',expression=d['result']))
        x=parse(inverse['result'])
        self.assertTrue(inverse['evaluated'])
        for k in range(-6,7):self.assertEqual(sp.simplify(x.subs(N,k)),int(k%5==0 and k!=0))
    def test_fourier_of_a_window_and_a_periodic_tail(self):
        from signallab_pc.periodic_signals import PVCot
        clipped=self.transform('(Step(t-1)-Step(t-6))*PulseTrain(t,3,2)')
        self.assertTrue(clipped['evaluated']);self.assertEqual(sp.simplify(parse(clipped['result']).subs(W,0)),3)
        tail=self.transform('Step(t-1)*PulseTrain(t-1,4,2)')
        self.assertTrue(tail['evaluated'] and tail['distribution']);self.assertTrue(parse(tail['result']).has(PVCot))
        restored=self.transform(tail['result'],True)
        x=parse(restored['result'])
        self.assertTrue(restored['evaluated'])
        self.assertEqual([sp.simplify(x.subs(T,k)) for k in (0,1,2,3,4,5,6)], [0,sp.S.Half,1,sp.S.Half,0,sp.S.Half,1])

    def test_generalized_dtft_roundtrip_for_both_half_axes(self):
        from signallab_pc.periodic_signals import PVCot
        from signallab_pc.symbolic import N
        source='PulseTrain(n-1,4,2)'
        waveform=parse(source)
        for lo,hi,present in [('2','oo',lambda n:n>=2),('-oo','-1',lambda n:n<0)]:
            with self.subTest(lo=lo,hi=hi):
                response=execute(dict(operation='dtft_expression',expression=source,lower=lo,upper=hi))
                self.assertTrue(response['evaluated'] and response['distribution'])
                self.assertTrue(parse(response['result']).has(PVCot))
                inverse=execute(dict(operation='inverse_dtft_expression',expression=response['result']))
                self.assertTrue(inverse['evaluated'])
                recovered=parse(inverse['result'])
                for n in range(-7,9):
                    self.assertEqual(sp.simplify(recovered.subs(N,n)),sp.simplify(waveform.subs(N,n)) if present(n) else 0)
    def test_an_excluded_frequency_cannot_drop_an_impulse_train_line(self):
        request=dict(operation='inverse_fourier_angular',expression='2*pi*ImpulseTrain(w,2*pi)',input_frequency_condition='Ne(w,0)')
        with self.assertRaisesRegex(ValueError,'no está definida'):
            execute(request)
        request['input_frequency_condition']='Ne(w,pi)'
        result=execute(request)
        self.assertTrue(result['evaluated']);self.assertEqual(parse(result['result']),parse('ImpulseTrain(t,1)'))
    def test_complex_grid_and_constant(self):
        result=execute(dict(operation='expression_grid',variable='w',expression='exp(-i*w)',start=0,stop=1,count=5))
        values=np.array([complex(*v) for v in result['samples']]);np.testing.assert_allclose(values,np.exp(-1j*np.linspace(0,1,5)))
        result=execute(dict(operation='expression_grid',variable='t',expression='2',start=0,stop=1,count=3));self.assertEqual(result['samples'],[[2.,0.]]*3)
    def test_no_distribution_or_singular_grid(self):
        for expression in ['dirac(t)','a*t']:
            with self.assertRaises(ValueError):execute(dict(operation='expression_grid',variable='t',expression=expression,start=0,stop=1,count=5))
        with self.assertRaisesRegex(ValueError,'polo'):execute(dict(operation='expression_grid',variable='t',expression='1/t',start=0,stop=1,count=5))
    def test_output_variable_collision(self):
        with self.assertRaises(ValueError):self.transform('cos(w*t)')
        with self.assertRaises(ValueError):self.transform('exp(-t*w^2)',True)
    def test_dtft_finite_matches_definition(self):
        result=execute(dict(operation='dtft_expression',expression='1+i*n',lower='-2',upper='3'))
        self.assertTrue(result['evaluated'])
        expression=parse(result['result'])
        for omega in [0,.3,np.pi]:
            expected=sum((1+1j*n)*np.exp(-1j*omega*n) for n in range(-2,4))
            self.assertAlmostEqual(abs(complex(expression.subs(W,omega).evalf())-expected),0,places=11)
    def test_dtft_geometric_infinite(self):
        result=execute(dict(operation='dtft_expression',expression='(1/2)^n',lower='0',upper='oo'))
        self.assertTrue(result['evaluated'])
        self.assertEqual(sp.simplify(parse(result['result'])-1/(1-sp.exp(-sp.I*W)/2)),0)
        self.assertEqual(result['frequency_units'],'rad/muestra')
    def test_dtft_left_sided_and_divergent(self):
        result=execute(dict(operation='dtft_expression',expression='2^n',lower='-oo',upper='0'))
        self.assertTrue(result['evaluated'])
        self.assertEqual(sp.simplify(parse(result['result'])-1/(1-sp.exp(sp.I*W)/2)),0)
        divergent=execute(dict(operation='dtft_expression',expression='2^n',lower='0',upper='oo'))
        self.assertFalse(divergent['evaluated'])
    def test_dtft_invalid_limits(self):
        with self.assertRaises(ValueError):execute(dict(operation='dtft_expression',expression='n',lower='1/2',upper='5'))
    def test_spectral_density_rejects_temporal_samples(self):
        with self.assertRaises(ValueError):energy_density(Signal([1,2],0,.1,'s','x','continuous',metadata={'operation':'fourier_expression_samples'}))
        result=energy_density(Signal([1,2],0,.1,'rad/s','X','frequency',metadata={'operation':'fourier_expression_samples'}))
        np.testing.assert_array_equal(result.values,[1,4])

if __name__=='__main__':unittest.main()
