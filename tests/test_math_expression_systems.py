"""General transfer definitions and numerical boundary interpretation."""
import unittest
import numpy as np
import sympy as sp
from numpy.testing import assert_allclose
from signallab_pc.symbolic import execute
from signallab_pc.analytic_frequency import analyze_expression


class ExpressionSystemContracts(unittest.TestCase):
    def test_logarithmic_system_is_not_converted_to_polynomial_coefficients(self):
        r=execute(dict(operation='system_formula',domain='digital',expression='-log(1-1/z)'))
        self.assertEqual(r['model_kind'],'expression');self.assertNotIn('numeric_b',r);self.assertEqual(r['parameters'],[])
        self.assertTrue(r['evaluated'])

    def test_removable_frequency_value_and_derivative_have_separate_limits(self):
        request=dict(operation='system_formula',domain='analog',expression='log(1+s)/s');exact=execute(request)
        exact,data=analyze_expression(exact,request,np.array([0.,.1,.5]))
        assert_allclose(data.response[0],1,atol=1e-14);assert_allclose(data.delay[0],.5,atol=1e-14)
        self.assertIn('no determina',data.system.interpretation)

    def test_unassigned_parameters_do_not_invent_numerical_coefficients(self):
        request=dict(operation='system_formula',domain='analog',expression='exp(-a*s)');exact=execute(request)
        exact,data=analyze_expression(exact,request,np.array([0.,1.]))
        self.assertEqual(exact['parameters'],['a']);self.assertIsNone(data);self.assertIn('a',exact['frequency_notice'])

    def test_special_function_transfer_has_numerical_frequency_values(self):
        request=dict(operation='system_formula',domain='digital',expression='polylog(2,1/z)');exact=execute(request)
        exact,data=analyze_expression(exact,request,np.array([.2,.5,1.]))
        self.assertTrue(np.isfinite(data.response).all());self.assertTrue(np.isfinite(data.delay).all())
        for w,value in zip(data.omega,data.response):assert_allclose(value,complex(sp.polylog(2,sp.exp(-sp.I*float(w))).evalf(18)),atol=1e-13)

    def test_wrong_domain_and_stale_transform_context_are_rejected(self):
        for domain,source in [('digital','log(1+s)'),('analog','log(1+z)')]:
            with self.assertRaisesRegex(ValueError,'otro dominio'):execute(dict(operation='system_formula',domain=domain,expression=source))
        origin=dict(request=dict(operation='z_expression',expression='1/n',lower='1',upper='oo'),result=dict(evaluated=True,output_variable='z',result='-log(1-1/z)'))
        request=dict(operation='system_formula',domain='digital',expression='-2*log(1-1/z)',source_calculation=origin)
        with self.assertRaisesRegex(ValueError,'no coinciden'):analyze_expression(execute(request),request,np.array([.1,.5]))


if __name__=='__main__':unittest.main()
