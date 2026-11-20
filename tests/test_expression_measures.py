import unittest
import numpy as np
from signallab_pc.symbolic import execute

class ExpressionMeasureTests(unittest.TestCase):
    def measure(self,expression,**options):return execute(dict(operation='signal_measures_expression',expression=expression,**options))
    def test_continuous_interval_complex(self):
        r=self.measure('1+i*t',domain='continuous',mode='interval',lower='-1',upper='2')
        self.assertEqual(r['energy']['exact'],'6');self.assertEqual(r['mean_square']['exact'],'2');self.assertEqual(r['rms']['exact'],'sqrt(2)')
    def test_discrete_interval_includes_both_ends(self):
        r=self.measure('1+i*n',domain='discrete',mode='interval',lower='-1',upper='2')
        self.assertEqual(r['energy']['exact'],'10');self.assertEqual(r['mean_square']['exact'],'5/2')
        r=self.measure('3',domain='discrete',mode='interval',lower='-4',upper='-4');self.assertEqual(r['energy']['exact'],'9')
    def test_total_energy_does_not_use_window_mean(self):
        r=self.measure('exp(-abs(t))',mode='global')
        self.assertEqual(r['energy']['exact'],'1');self.assertEqual(r['mean_square']['exact'],'0');self.assertEqual(r['classification'],'Señal de energía')
    def test_discrete_bilateral_geometric_energy(self):
        r=self.measure('(1/2)^abs(n)',domain='discrete',mode='global')
        self.assertEqual(r['energy']['exact'],'5/3');self.assertEqual(r['mean_square']['exact'],'0')
    def test_constant_complex_power(self):
        for domain in ('continuous','discrete'):
            r=self.measure('1+2*i',domain=domain,mode='global')
            self.assertEqual(r['energy']['status'],'divergent');self.assertEqual(r['mean_square']['exact'],'5');self.assertEqual(r['classification'],'Señal de potencia')
    def test_half_axis_step_symmetric_power(self):
        r=self.measure('heaviside(t)',mode='global')
        self.assertEqual(r['mean_square']['exact'],'1/2')
    def test_global_energy_and_power_with_mixed_tails(self):
        for variable,domain in (('n','discrete'),('t','continuous')):
            with self.subTest(domain=domain):
                gated=self.measure(f'Step({variable})*cos({variable})',domain=domain,mode='global')
                self.assertEqual(gated['mean_square']['exact'],'1/4')
                decaying=self.measure(f'exp(-abs({variable}))*cos({variable})',domain=domain,mode='global')
                self.assertEqual(decaying['energy']['status'],'finite')
                self.assertEqual(decaying['mean_square']['exact'],'0')
                mixed=self.measure(f'1+exp(-abs({variable}))*cos({variable})',domain=domain,mode='global')
                self.assertEqual(mixed['energy']['exact'],'oo')
                self.assertEqual(mixed['mean_square']['exact'],'1')
    def test_oscillatory_envelopes_have_exact_zero_power(self):
        cases=(('n','discrete',1.8113713486543286),('t','continuous',np.pi*(1+np.exp(-2))/2))
        for variable,domain,energy in cases:
            with self.subTest(domain=domain):
                result=self.measure(f'cos({variable})/sqrt(1+{variable}^2)',domain=domain,mode='global')
                self.assertEqual(result['mean_square']['exact'],'0')
                self.assertAlmostEqual(result['energy']['approximation'],energy,places=12)
        result=self.measure('cos(n)/sqrt(1+abs(n))',domain='discrete',mode='global')
        self.assertEqual(result['energy']['exact'],'oo')
        self.assertEqual(result['mean_square']['exact'],'0')
    def test_harmonic_power_without_requiring_a_period(self):
        cases=(('discrete','Cos(n)','1/2'),('discrete','cos(pi*n)','1'),
               ('discrete','cos(n)+cos((2*pi+1)*n)','2'),('discrete','cos(pi*n)/sqrt(2)','1/2'),
               ('discrete','exp(i*n)+2*exp(3*i*n)','5'),('continuous','cos(pi*t)','1/2'))
        for domain, expression, power in cases:
            with self.subTest(expression=expression):
                result=self.measure(expression,domain=domain,mode='global')
                self.assertEqual(result['mean_square']['exact'],power)
                self.assertEqual(result['energy']['status'],'divergent')
    def test_period_proof_continuous_and_discrete(self):
        r=self.measure('sin(t)',mode='periodic',period='2*pi')
        self.assertTrue(r['period_verified']);self.assertEqual(r['mean_square']['exact'],'1/2');self.assertEqual(r['period_energy']['exact'],'pi')
        r=self.measure('exp(i*pi*n/2)',domain='discrete',mode='periodic',period='4')
        self.assertEqual(r['mean_square']['exact'],'1');self.assertEqual(r['period_energy']['exact'],'4')
        with self.assertRaises(ValueError):self.measure('sin(t)',mode='periodic',period='1')
    def test_periodic_waveforms_use_one_complete_cycle(self):
        cases=(('discrete','Repeat(n,n,4,1)','15/2'),('discrete','ImpulseTrain(n-1,5)','1/5'),
               ('discrete','PulseTrain(n-1,5,2)','2/5'),('continuous','Repeat(t,t,1)','1/3'),
               ('continuous','PulseTrain(t-1/4,1,1/4)','1/4'),
               ('discrete','PulseTrain(n,2,1)+PulseTrain(n-1,3,1)','7/6'),
               ('continuous','RepeatSamples(t,0,(0,1),1)','1/3'))
        for domain, expression, power in cases:
            with self.subTest(expression=expression):
                result=self.measure(expression,domain=domain,mode='global')
                self.assertEqual(result['mean_square']['exact'],power)
                self.assertEqual(result['energy']['exact'],'oo')
        with self.assertRaisesRegex(ValueError,'función ordinaria'):
            self.measure('ImpulseTrain(t,1)',mode='global')
        with self.assertRaisesRegex(ValueError,'periodo indicado|período indicado'):
            self.measure('(-1)^n*Repeat(n,n,3)',domain='discrete',mode='periodic',period='3')
    def test_parameters_preserve_conditions(self):
        r=self.measure('a*exp(-abs(t))',mode='global')
        self.assertEqual(r['parameters'],['a']);self.assertEqual(r['energy']['status'],'conditional')
    def test_zero_and_unbounded_power(self):
        r=self.measure('0',mode='global');self.assertEqual(r['energy']['exact'],'0');self.assertEqual(r['classification'],'Energía nula')
        r=self.measure('t',mode='global');self.assertEqual(r['mean_square']['status'],'divergent')
    def test_reject_distribution_and_invalid_domains_or_bounds(self):
        for args in [dict(expression='dirac(t)'),dict(expression='1',lower='1',upper='0'),dict(expression='n',domain='continuous'),dict(expression='1',domain='discrete',lower='.2',upper='3'),dict(expression='1',mode='periodic',period='0')]:
            with self.assertRaises(ValueError):execute(dict(operation='signal_measures_expression',**args))
    def test_numeric_window_keeps_clock_and_approximates_integral(self):
        r=execute(dict(operation='signal_measures_window',expression='1+i*t',domain='continuous',start=-1,stop=2,count=1001))
        self.assertAlmostEqual(r['energy'],6,delta=1e-5);self.assertEqual(r['origin'],-1);self.assertEqual(r['step'],.003)
        self.assertAlmostEqual(r['mean_square'],2,delta=1e-5)
    def test_discrete_negative_powers_and_complex_square_root(self):
        r=execute(dict(operation='signal_measures_window',expression='(1/2)^abs(n)',domain='discrete',start='-2',stop='2'))
        np.testing.assert_allclose(np.array(r['samples'])[:,0],[.25,.5,1,.5,.25])
        r=execute(dict(operation='signal_measures_window',expression='sqrt(n)',domain='discrete',start='-1',stop='1'))
        self.assertEqual(r['samples'],[[0.,1.],[0.,0.],[1.,0.]])
    def test_numeric_discrete_window_and_singular_rejection(self):
        r=execute(dict(operation='signal_measures_window',expression='1+i*n',domain='discrete',start='-1',stop='2'))
        self.assertEqual(r['energy'],10);self.assertEqual(len(r['samples']),4);self.assertEqual(r['origin'],-1)
        with self.assertRaises(ValueError):execute(dict(operation='signal_measures_window',expression='1/t',domain='continuous',start=-1,stop=1,count=3))
        with self.assertRaises(ValueError):execute(dict(operation='signal_measures_window',expression='a*t',domain='continuous',start=0,stop=1,count=3))

if __name__=='__main__':unittest.main()
