"""User-facing algebra contracts for the worksheet and sampled distributions."""
import math
import sys
import unittest

import numpy as np
import sympy as sp

from signallab_pc.cas_engine import calculate, empty_state, encode, restore
from signallab_pc.continuous_expression import finite_definition, sample_continuous
from signallab_pc.distributions import dirac_terms
from signallab_pc.symbolic import parse


class WorksheetAlgebraContracts(unittest.TestCase):
    def setUp(self):
        old=sys.get_int_max_str_digits()
        self.addCleanup(sys.set_int_max_str_digits,old)
        self.state=empty_state()
        self.cell=0

    def evaluate(self, source):
        self.cell+=1
        result=calculate({'state':self.state,'source':source,'cell':self.cell})
        self.state=result['state']
        return restore(self.state['results'][str(self.cell)])

    def test_typed_mathematical_values_survive_encoding_and_indexing(self):
        for expression, expected in [
            ('+3.25',sp.Rational(13,4)),('7-2*i',7-2*sp.I),('9%4',sp.Integer(1)),
            ('matrix([[1,2],[3,4]])[1,0]',sp.Integer(3)),
            ('(2,3,4)[-1]',sp.Integer(4)),('[[1,2],[3,4]][0][1]',sp.Integer(2)),
            ('{1:3, 2:5}[2]',sp.Integer(5)),
            ('{1,2,2}',sp.FiniteSet(1,2)),('factorial(110)',sp.Integer(math.factorial(110))),
            ('det(eye(2))',sp.Integer(1)),('ones(1,3)',sp.ImmutableMatrix([[1,1,1]])),
            ('exact(0.125)',sp.Rational(1,8)),('ans()',sp.Rational(1,8)),
        ]:
            with self.subTest(expression=expression):
                result=self.evaluate(expression)
                self.assertEqual(result,expected)
                self.assertEqual(restore(encode(result)),expected)
        self.assertEqual(self.evaluate('r1+1'),sp.Rational(17,4))

    def test_predicates_and_assumptions_control_the_scoped_answers(self):
        x=sp.Symbol('x')
        for expression,expected in [
            ('0 < x <= 2',lambda t: 0<t<=2),
            ('(x<0) or (x>2)',lambda t:t<0 or t>2),
            ('(x>=0) & (x<2)',lambda t:0<=t<2),
            ('(x==1) | (x==2)',lambda t:t in (1,2)),
            ('not (x==0)',lambda t:t!=0),
        ]:
            with self.subTest(expression=expression):
                result=self.evaluate(expression)
                self.assertEqual([bool(result.subs(x,n)) for n in (-1,0,1,2,3)],
                                 [expected(n) for n in (-1,0,1,2,3)])
        self.assertEqual(self.evaluate('assume(x,real)'),sp.true)
        self.assertEqual(self.evaluate('assume(x>1,x<3)'),sp.true)
        self.assertEqual(self.evaluate('solve(x^2-4,x)'),sp.FiniteSet(2))
        self.assertEqual(self.evaluate('nsolve(x^2-4,x,1.5)').evalf(10),sp.Float(2,10))
        self.assertEqual(self.evaluate('purge(x)'),sp.true)
        self.assertEqual(self.evaluate('solve_real(x^2<4,x)'),sp.Interval.open(-2,2))

    def test_function_and_substitutions_preserve_removable_exclusions(self):
        self.evaluate('ratio(x) := (x^2-1)/(x-1)')
        self.assertEqual(self.evaluate('ratio(3)'),4)
        with self.assertRaisesRegex(ValueError,'fuera del dominio'):
            self.evaluate('ratio(1)')
        for expression,expected in [('subst(x+y,{x:2,y:3})',5),('subst(x^2,(x==3))',9),
                                    ('subst(x^3,x,2)',8),('int(x^2,x,0,3)',9),
                                    ('sum(2*n,n,1,3)',12),('product(n,n,1,5)',120),
                                    ('limit(1/x,x,0,left)',-sp.oo),
                                    ('limit(1/x,x,0,right)',sp.oo)]:
            with self.subTest(expression=expression):
                self.assertEqual(self.evaluate(expression),expected)
        result=self.evaluate('linsolve([x+y-4,x-y-2],[x,y])')
        self.assertEqual(result,sp.FiniteSet(sp.Tuple(3,1)))
        result=self.evaluate('solve([x+y-4,x-y-2],(x,y))')
        self.assertEqual(result,sp.FiniteSet(sp.Tuple(3,1)))

    def test_numeric_approximation_preserves_collections_and_rejects_colliding_keys(self):
        result=self.evaluate('approx({1/2:(sqrt(2),[pi]), 2/3:{1/7,2/7}},10)')
        self.assertAlmostEqual(float(next(iter(result))),.5)
        entry=next(iter(result.values()))
        self.assertAlmostEqual(float(entry[0]),np.sqrt(2),places=8)
        self.assertAlmostEqual(float(entry[1][0]),np.pi,places=8)
        self.assertIsInstance(self.evaluate('approx(x>1/3,9)'),sp.StrictGreaterThan)
        for expression,pattern in [('approx({1/2:1,5001/10000:2},1)','claves distintas'),
                                   ('approx({1/2,5001/10000},1)','soluciones distintas')]:
            with self.subTest(expression=expression),self.assertRaisesRegex(ValueError,pattern):
                self.evaluate(expression)

    def test_invalid_commands_never_change_previous_worksheet_answers(self):
        self.assertEqual(self.evaluate('a := 7'),7)
        for expression,reason in [
            ('','Escribí'),('r100','resultado válido'),('ans(1)','recuperar'),
            ('purge()','recibe'),('assume()','Usá assume'),('assume(a,real)','Purgá'),
            ('assume(x>y)','constante'),('f(a,a) := a','parámetros'),
            ('zz := zz+1','sí misma'),('f(x) := f(x)','recursivas'),
            ('vec(x) := [x]','expresión o matriz'),('f(x) := x+1',''),
            ('f(1,2)','requiere'),('sqrt := 3','reservado'),
            ('zeros(-1)','dimensiones'),('det(1)','matrix'),
            ('{1:7}[2]','clave'),('[1,2][1/2]','índices deben'),
            ('x[1]','Sólo se indexan'),('subst(x,[1])','Usá subst'),
            ('subst(x,x,[2])','escalares'),('solve(x)','Indicá ecuación'),
            ('solve(x,1)','incógnita'),('solve(x>1,x)','desigualdades'),
            ('solve_real([x-1],[x])','una variable real'),('solve([x],[x,2])','símbolos libres'),
            ('approx()','Usá approx'),('approx(pi,0)','dígitos'),
        ]:
            with self.subTest(expression=expression):
                if not reason:
                    self.assertEqual(self.evaluate(expression),sp.Symbol('x')+1)
                    continue
                snapshot=self.state
                with self.assertRaisesRegex(ValueError,reason):
                    self.evaluate(expression)
                self.assertIs(self.state,snapshot)
        self.assertEqual(self.evaluate('a+r1'),14)


class ContinuousDistributionContracts(unittest.TestCase):
    def test_affine_impulses_keep_weight_under_scaling_and_piecewise_selection(self):
        for formula,expected,ordinary in [
            ('DiracDelta((t-1)/2,0)+3',[(1,2)],3),
            ('+DiracDelta((t**1)+1)',[(-1,1)],0),
            ('-DiracDelta(-t-1)+DiracDelta(2)',[(-1,-1)],0),
            ('(t+3)*DiracDelta(2*t-1)/2',[(.5,.875)],0),
            ('DiracDelta(t+1) - DiracDelta(t-1)',[(-1,1),(1,-1)],0),
            ('where(-2<t<0,2*dirac(t+1),3*dirac(t-1))+2',[(-1,2),(1,3)],2),
            ('dirac(t-1) if not (t<0) else dirac(t+1)',[(-1,1),(1,1)],0),
            ('where(t<0 and t==t,dirac(t+1),0)',[(-1,1)],0),
            ('where(t<0 or t>3,dirac(t-1),dirac(t+1))',[],0),
            ('(DiracDelta(t-1))**1',[(1,1)],0),
            ('DiracDelta(t)+0*DiracDelta(t-1)',[(0,1)],0),
            ('ImpulseTrain(2*t,2)',[(-2,.5),(-1,.5),(0,.5),(1,.5),(2,.5)],0),
        ]:
            with self.subTest(formula=formula):
                result=sample_continuous(formula,-2,.5,9)
                self.assertEqual(dirac_terms(result),expected)
                np.testing.assert_allclose(result.values,ordinary)
        result=sample_continuous('DiracDelta(t-2)+DiracDelta(t+2)+DiracDelta(t-8)',-2,.5,9,right_open=True)
        self.assertEqual(dirac_terms(result),[(-2,1)])
        self.assertEqual(result.metadata['excluded_dirac_positions'],[2.,8.])

    def test_undefined_operations_on_distributions_report_the_cause(self):
        for formula,reason in [
            ('KroneckerDelta(t)','discreto'),('dirac(n)','variable'),
            ('dirac(0)','varíe'),('dirac(1j*t)','reales'),
            ('dirac(t,1)','orden cero'),('dirac(t*t)','lineal'),
            ('dirac(t)*dirac(t-1)','producto de impulsos'),('sin(dirac(t))','no está definida'),
            ('dirac(t)/0','división por cero'),('1/dirac(t)','no está definida'),
            ('ImpulseTrain(t)','período constante'),('ImpulseTrain(t,t)','período constante'),
            ('ImpulseTrain(t,-1)','positivo'),('ImpulseTrain(t,1j)','real'),
            ('where(t>=0,dirac(t),0)','borde'),('where(True,dirac(t),0)',''),
            ('(where(t<0,1,2))*dirac(t)','borde'),
            ('(1 if t<0 else 2)*dirac(t)','borde'),
            ('(t>=0)*dirac(t)','cambia'),('floor(t)*dirac(t)','discontinuo'),
            ('step(t)*dirac(t)','discontinuo'),
        ]:
            with self.subTest(formula=formula):
                if not reason:
                    self.assertEqual(dirac_terms(sample_continuous(formula,-2,.5,9)),[(0,1)])
                    continue
                with self.assertRaisesRegex(ValueError,reason):
                    sample_continuous(formula,-2,.5,9)
        for origin,step,count,reason in [
            (float('inf'),1,2,'rejilla'), (0,0,3,'rejilla'),
            (0,1,0,'rejilla'), (1e20,1,2,'coordenadas'),
        ]:
            with self.subTest(origin=origin,step=step,count=count),self.assertRaisesRegex(ValueError,reason):
                sample_continuous('dirac(t)',origin,step,count)

    def test_finite_formula_keeps_whole_endpoint_impulse_areas(self):
        exact=parse(finite_definition('3+2*DiracDelta(t-2)+DiracDelta(t+3)',-2,2)).expand()
        t=next(iter(exact.free_symbols))
        impulse, = exact.atoms(sp.DiracDelta)
        self.assertEqual(sp.simplify(impulse.args[0]),t-2)
        self.assertEqual(exact.coeff(impulse),2)
        self.assertEqual(exact.subs(t,0),3)
        self.assertEqual(exact.subs(t,3),0)
        self.assertEqual(finite_definition('dirac(t-9)',-2,2),'0')
