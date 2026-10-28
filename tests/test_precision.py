from fractions import Fraction
import unittest
import numpy as np
from scipy import signal
from signallab_pc.precision import Encoding,represent,quantize_coefficients
from signallab_pc.filters import Transfer

class PrecisionTests(unittest.TestCase):
    def test_ieee_bits_rounding_and_no_double_round(self):
        for kind,hexword in [('float16','0x399a'),('float32','0x3f333333'),('float64','0x3fe6666666666666')]:
            self.assertEqual(represent('0.7',Encoding(kind))['hex'],hexword)
        encoder=Encoding('float16');self.assertEqual(encoder.encode(1+Fraction(1,2048))['hex'],'0x3c00')
        self.assertEqual(encoder.encode(1+Fraction(3,2048))['hex'],'0x3c02')
        self.assertEqual(encoder.encode(1+Fraction(1,2048)+Fraction(1,2**80))['hex'],'0x3c01')
        for x in [0.,-0.,.7,-.7,2**-24,2**-14,65504.,-65504.]:
            actual=encoder.encode(Fraction.from_float(x),np.signbit(x))
            self.assertEqual(int(actual['hex'],16),int(np.float16(x).view(np.uint16)))
    def test_subnormal_overflow_and_exact_fixed_point(self):
        encoder=Encoding('float16');self.assertEqual(encoder.encode(Fraction(1,2**24))['hex'],'0x1')
        self.assertEqual(encoder.encode(Fraction(1,2**25))['hex'],'0x0')
        self.assertEqual(encoder.encode(65520)['classification'],'desborde a infinito')
        self.assertEqual(represent('-0.0',encoder)['hex'],'0x8000')
        self.assertEqual(represent('1e400',Encoding('float64'))['classification'],'desborde a infinito')
        fixed=represent('0.7',Encoding('fixed',2,3));self.assertEqual(fixed['represented_exact'],'3/4');self.assertEqual(fixed['error_exact'],'1/20')
        self.assertEqual(represent('-1/16',Encoding('fixed',2,3))['represented_exact'],'-1/8')
        self.assertEqual(represent('-1/16',Encoding('fixed',2,3,'truncate'))['represented_exact'],'0')
        self.assertEqual(represent('100',Encoding('fixed',2,3))['classification'],'saturado')
        self.assertFalse(represent('pi',Encoding('float32'))['reference_exact'])
    def test_coefficient_rounding_moves_pole_and_keeps_a0_implicit(self):
        original=Transfer([.2],[1,-.99]);data=quantize_coefficients(original,Encoding('fixed',1,3))
        np.testing.assert_array_equal(data['system'].a,[1,-1]);self.assertEqual(data['metrics']['stored_pole_radius'],1)
        self.assertIn('Frontera',data['metrics']['stored_poles']);np.testing.assert_array_equal(original.a,[1,-.99])
        self.assertEqual(data['metrics']['undefined_points'],1)
        with self.assertRaises(ValueError):quantize_coefficients(Transfer([1e10],[1]),Encoding('float16'))
        with self.assertRaises(ValueError):quantize_coefficients(Transfer([1],[1],'analog'),Encoding())
    def test_sos_complex_and_binary64_identity(self):
        source=Transfer.from_sos(signal.butter(4,.5,fs=2*np.pi,output='sos'));before=source.sos.copy()
        data=quantize_coefficients(source,Encoding('float16'));self.assertTrue(data['sections']);self.assertIsNotNone(data['system'].sos)
        np.testing.assert_array_equal(data['system'].sos[:,3],1);np.testing.assert_array_equal(source.sos,before)
        data=quantize_coefficients(source,Encoding('float64'));self.assertEqual(data['metrics']['changed'],0);self.assertEqual(data['metrics']['scaled_response_error_max'],0)
        data=quantize_coefficients(Transfer([.25+.1j],[1]),Encoding('fixed',2,3));self.assertEqual(data['system'].b[0],.25+.125j)

if __name__=='__main__':unittest.main()
