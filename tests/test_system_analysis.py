import unittest
from signallab_pc.symbolic import execute

class SystemAnalysisTests(unittest.TestCase):
    def analyze(self,b,a,domain='analog',**extra):
        return execute(dict(operation='system_analysis',b=b,a=a,domain=domain,**extra))
    def test_exact_fraction_and_numeric_view(self):
        result=self.analyze(['1/3'],['1','1'])
        self.assertEqual(result['exact_b'],['1/3'])
        self.assertEqual(result['transfer'],'1/(3*s + 3)')
        self.assertAlmostEqual(result['numeric_b'][0][0],1/3)
    def test_digital_delay_convention(self):
        result=self.analyze(['0','1'],['1'],'digital')
        self.assertEqual(result['transfer'],'1/z')
    def test_symbolic_parameter_has_no_numeric_projection(self):
        result=self.analyze(['K'],['1','1'])
        self.assertNotIn('numeric_b',result)
        self.assertIn('K',result['parameters'])
    def test_invalid_denominator(self):
        with self.assertRaises(ValueError):self.analyze(['1'],['0'])
    def test_causal_impulse(self):
        result=self.analyze(['1'],['1','1'],impulse=True)
        self.assertEqual(result['causal_impulse'],'exp(-t)*Heaviside(t)')

if __name__=='__main__':unittest.main()
