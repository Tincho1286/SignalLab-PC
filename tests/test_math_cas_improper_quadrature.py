"""Worksheet oracles for real improper integration and linear solving."""
import sys
import unittest

import sympy as sp

from signallab_pc.cas_engine import calculate, restore


class CASQuadratureContracts(unittest.TestCase):
    def setUp(self):
        self.addCleanup(sys.set_int_max_str_digits,sys.get_int_max_str_digits())

    def evaluate(self, source):
        result=calculate({'source':source,'cell':1})
        return restore(result['state']['results']['1'])

    def test_rational_poles_use_the_approach_from_inside_the_interval(self):
        for source,expected in (
            ('integrate(1/x,(x,0,1))',sp.oo),
            ('integrate(-1/x,x,0,1)',-sp.oo),
            ('integrate(1/x,(x,-1,0))',-sp.oo),
            ('integrate(1/(1-x),(x,0,1))',sp.oo),
            ('integrate(1/(1-x),(x,1,0))',-sp.oo),
            ('integrate((x-2)^(-3),(x,0,2))',-sp.oo),
            ('integrate(-1/(x^2-2)^2,(x,-2,2))',-sp.oo),
            ('integrate(1/(x^3-2),(x,0,2))',sp.nan),
            ('integrate(1/x^2-1/(x-2)^2,(x,0,2))',sp.nan),
        ):
            with self.subTest(source=source):
                self.assertEqual(self.evaluate(source),expected)

    def test_rational_continuation_and_distributions_share_the_real_integrator(self):
        for source,expected in (
            ('integrate((x^2-1)/(x-1),(x,0,2))',sp.Integer(4)),
            ('integrate(1/(x+1),(x,0,1))',sp.log(2)),
            ('integrate(1/(x^2+1),(x,0,1))',sp.pi/4),
            ('integrate(Dirac(x-0.5)-1/x,(x,0,1))',-sp.oo),
            ('integrate(Dirac(x)+x,(x,0,1))',sp.S.One),
        ):
            with self.subTest(source=source):
                self.assertEqual(self.evaluate(source),expected)

    def test_linear_command_enforces_linearity_with_one_unknown(self):
        self.assertEqual(self.evaluate('linsolve(3*x=6,x)'), sp.FiniteSet(2))
        self.assertEqual(self.evaluate('linsolve(0,x)'), sp.S.Complexes)
        with self.assertRaisesRegex(ValueError,'requiere ecuaciones lineales'):
            self.evaluate('linsolve(x^2-1,x)')
        self.assertEqual(self.evaluate('solve(x^2-1,x)'), sp.FiniteSet(-1,1))
