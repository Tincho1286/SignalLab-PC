"""Parameter variations must use shared algebra, not literal sinc exceptions."""
import unittest
import numpy as np
import sympy as sp
from signallab_pc.symbolic import execute,parse,N,Z,W
from signallab_pc.cas_engine import restore


class ShiftedPairContracts(unittest.TestCase):
    def transform(self,source,operation='z_expression',lower='0',upper='oo'):
        return execute(dict(operation=operation,expression=source,lower=lower,upper=upper))

    def test_shifted_scaled_sinc_causal_z_against_defining_sum(self):
        for width,delay,gain in [('3/10',4,'1'),('1/2',5,'2'),('2/5',-3,'-1')]:
            source=f'({gain})*sin(({width})*pi*(n-({delay})))/(pi*(n-({delay})))'
            with self.subTest(width=width,delay=delay,gain=gain):
                result=self.transform(source);self.assertTrue(result['evaluated']);self.assertEqual(result['method'],'table_pairs')
                value=parse(result['branches'][0]['expression']);x=restore(result['input_definition']['encoded_expression'])
                samples=np.array([complex(sp.N(x.subs(N,n),18)) for n in range(90)])
                for z in (2+.3j,-1.8+.4j):
                    expected=np.sum(samples*z**(-np.arange(len(samples))))
                    self.assertAlmostEqual(abs(complex(sp.N(value.subs(Z,z),18))-expected),0,places=11)
                if delay>=0:self.assertEqual(sp.simplify(x.subs(N,delay)-parse(gain)*parse(width)),0)

    def test_bilateral_sinc_keeps_shift_and_rectangle_without_false_z_roc(self):
        for width,delay,gain in [('3/10',4,1),('1/2',5,2),('2/5',-3,-1)]:
            source=f'{gain}*sin(({width})*pi*(n-({delay})))/(pi*(n-({delay})))'
            with self.subTest(width=width,delay=delay):
                z=self.transform(source,lower='-oo');self.assertEqual(z['calculation_status']['code'],'no_convergence');self.assertIn('boundary_dtft',z)
                result=self.transform(source,'dtft_expression','-oo');self.assertTrue(result['evaluated'])
                value=parse(result['result']);a=sp.Rational(width)*sp.pi
                for w,height in [(0,gain),(a/2,gain),(a,sp.Rational(gain,2)),(sp.pi,0),(2*sp.pi,gain)]:
                    self.assertEqual(sp.simplify(value.subs(W,w)-height*sp.exp(-sp.I*w*delay)),0)

    def test_equivalent_grouping_trig_forms_and_assigned_sample(self):
        from signallab_pc.dtft_pairs import direct
        from signallab_pc.z_direct_pairs import direct_pairs
        sources=['sin(0.3*pi*(n-4))/(pi*(n-4))','sin((3*pi*n-12*pi)/10)/(pi*n-4*pi)',
                 'cos(pi*n/2)/(pi*(n-3))','sin(pi*(n-3)/2)/(pi*(n-3))','cos(pi/3)*sinc(0.3*(n-4))']
        for source in sources:
            with self.subTest(source=source):
                x=parse(source);self.assertIsNotNone(direct(x));self.assertIsNotNone(direct_pairs(x,sp.S.Zero,sp.oo))
        source='Piecewise((7,n==4),(sin(0.3*pi*(n-4))/(pi*(n-4)),True))'
        result=self.transform(source,'dtft_expression','-oo');self.assertTrue(result['evaluated'])
        value=parse(result['result']);self.assertEqual(sp.simplify(value.subs(W,0)-(1+7-sp.Rational(3,10))),0)

    def test_noninteger_centres_use_lerch_pair_instead_of_pending_sum(self):
        for delay in (sp.Rational(1,2),sp.Rational(7,3)):
            source=f'sin(0.3*pi*(n-({delay})))/(pi*(n-({delay})))'
            with self.subTest(delay=delay):
                result=self.transform(source);self.assertTrue(result['evaluated']);self.assertEqual(result['method'],'table_pairs')
                value=parse(result['branches'][0]['expression']);x=restore(result['input_definition']['encoded_expression']);z=2+.3j
                expected=sum(complex(sp.N(x.subs(N,n),18))*z**(-n) for n in range(90))
                self.assertAlmostEqual(abs(complex(sp.N(value.subs(Z,z),18))-expected),0,places=10)
                f=self.transform(source,'dtft_expression','-oo');self.assertTrue(f['evaluated']);spectrum=parse(f['result'])
                for w,height in [(0,1),(sp.pi/10,1),(3*sp.pi/10,sp.Rational(1,2)),(sp.pi,0),(2*sp.pi,1)]:
                    folded=sp.Mod(w+sp.pi,2*sp.pi)-sp.pi
                    self.assertEqual(sp.simplify(spectrum.subs(W,w)-height*sp.exp(-sp.I*folded*delay)),0)
                bilateral=self.transform(source,lower='-oo');self.assertEqual(bilateral['calculation_status']['code'],'no_convergence');self.assertIn('boundary_dtft',bilateral)

    def test_cutoffs_above_nyquist_include_spectral_images(self):
        for delay in (sp.Integer(2),sp.Rational(1,2)):
            source=f'sin(1.5*pi*(n-({delay})))/(pi*(n-({delay})))'
            f=self.transform(source,'dtft_expression','-oo');self.assertTrue(f['evaluated']);value=parse(f['result'])
            for w in (sp.S.Zero,sp.pi/4,3*sp.pi/4,sp.pi,2*sp.pi):
                theta=sp.Mod(w+sp.pi,2*sp.pi)-sp.pi
                images=[theta+2*sp.pi*k for k in (-1,0,1) if abs(theta+2*sp.pi*k)<3*sp.pi/2]
                want=sum(sp.exp(-sp.I*v*delay) for v in images)
                self.assertEqual(sp.simplify(value.subs(W,w)-want),0)

    def test_worker_returns_expression_notes_and_conditions_for_shifted_input(self):
        from signallab_pc.symbolic_process import run_request
        request=dict(operation='z_expression',expression='sin(0.3*pi*(n-4))/(pi*(n-4))',lower='0',upper='oo')
        result=run_request(request)
        self.assertTrue(result['evaluated']);self.assertEqual(result['method'],'table_pairs');self.assertTrue(result['branches']);self.assertTrue(result['derivation'])
        self.assertTrue(any(v['point']=='4' and v['value']=='3/10' for v in result['calculation_notes']))

    def test_modulation_and_shift_properties_compose(self):
        source='exp(i*pi*n/4)*sin(0.3*pi*(n-4))/(pi*(n-4))'
        result=self.transform(source,'dtft_expression','-oo');self.assertTrue(result['evaluated'])
        value=parse(result['result']);carrier=sp.pi/4
        for w,height in [(carrier,1),(carrier+sp.pi/10,1),(carrier+sp.pi/2,0),(carrier+3*sp.pi/10,sp.Rational(1,2))]:
            self.assertEqual(sp.simplify(value.subs(W,w)-height*sp.exp(-4*sp.I*(w-carrier))),0)


if __name__=='__main__':unittest.main()
