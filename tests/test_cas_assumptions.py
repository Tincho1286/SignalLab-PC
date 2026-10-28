import unittest
import sympy as sp
from signallab_pc.cas_engine import calculate,empty_state,restore

class WorksheetAssumptionTests(unittest.TestCase):
    def setUp(self):self.state=empty_state();self.cell=0
    def run_cas(self,source):
        self.cell+=1;result=calculate(dict(source=source,state=self.state,cell=self.cell));self.state=result['state'];return restore(self.state['results'][str(self.cell)])
    def test_euler_conversions(self):
        x=sp.Symbol('x');self.assertEqual(self.run_cas('exp2trig(exp(i*x))'),sp.cos(x)+sp.I*sp.sin(x))
        self.assertEqual(sp.simplify(self.run_cas('trig2exp(sin(x))')-sp.sin(x).rewrite(sp.exp)),0)
    def test_domains_and_previous_expressions(self):
        self.run_cas('a:=sqrt(x^2)');self.run_cas('assume(x>0,x<3)')
        self.assertEqual(self.run_cas('a'),self.run_cas('x'));self.assertEqual(self.run_cas('solve((x-1)*(x-4),x)'),sp.FiniteSet(1))
        self.run_cas('purge(x)');x=sp.Symbol('x');self.assertEqual(self.run_cas('sqrt(x^2)'),sp.sqrt(x*x))
        self.run_cas('assume(n,integer)');self.assertEqual(self.run_cas('solve(n^2=2,n)'),sp.EmptySet)
    def test_contradictions_assignments_and_numeric_roots_are_atomic(self):
        self.run_cas('assume(x>0)');before=str(self.state)
        for source in ('assume(x<0)','x:=-2','assume(x>y)','nsolve(x^2-1,x,-2)'):
            with self.assertRaises(ValueError):self.run_cas(source)
            self.assertEqual(str(self.state),before)
        self.run_cas('assume(y=0)');before=str(self.state)
        with self.assertRaises(ValueError):self.run_cas('assume(y!=0)')
        self.assertEqual(str(self.state),before)
    def test_complex_nonzero_and_system_solutions(self):
        self.run_cas('assume(z!=0)');self.assertEqual(self.run_cas('solve(z^2+1,z)'),sp.FiniteSet(-sp.I,sp.I))
        self.run_cas('assume(y>0)');self.assertEqual(self.run_cas('solve([y+q=0,q=1],[y,q])'),sp.EmptySet)

if __name__=='__main__':unittest.main()

