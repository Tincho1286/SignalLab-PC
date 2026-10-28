import unittest
import sympy as sp
from signallab_pc.cas_engine import calculate,empty_state,restore


class CasWorksheetTests(unittest.TestCase):
    def setUp(self):self.state=empty_state();self.cell=0
    def run_cas(self,source):
        self.cell+=1;result=calculate({'source':source,'cell':self.cell,'state':self.state});self.state=result['state'];return restore(self.state['results'][str(self.cell)])
    def test_exact_arithmetic_implicit_multiplication_and_independent_x(self):
        self.assertEqual(self.run_cas('0.1+1/3'),sp.Rational(13,30));self.assertEqual(self.run_cas('2x+3(x+1)'),5*sp.Symbol('x')+3)
        self.assertEqual(self.run_cas('pi(x+1)'),sp.pi*(sp.Symbol('x')+1));self.assertEqual(self.run_cas('3j+2i'),5*sp.I)
        self.assertNotEqual(self.run_cas('x-t'),0)
    def test_definitions_history_and_purge(self):
        self.run_cas('a:=3');self.run_cas('f(x):=a*x^2');self.assertEqual(self.run_cas('f(2)'),12)
        self.assertEqual(self.run_cas('ans+r1'),15);self.run_cas('purge(a)');self.assertEqual(self.run_cas('a'),sp.Symbol('a'))
        self.run_cas('n:=5');self.assertEqual(self.run_cas('n+1'),6)
    def test_calculus_and_serialized_pending_result(self):
        x=sp.Symbol('x');self.assertEqual(self.run_cas('diff(sin(x),x)'),sp.cos(x))
        self.assertEqual(self.run_cas('integrate(x^2,x,0,1)'),sp.Rational(1,3));self.assertEqual(self.run_cas('limit(sin(x)/x,x,0)'),1)
        self.assertEqual(self.run_cas('sum(n,n,1,10)'),55)
        pending=self.run_cas('integrate(f(x),x)');self.assertTrue(pending.has(sp.Integral));self.assertEqual(self.run_cas('ans'),pending)
    def test_equations_sets_and_systems(self):
        self.assertEqual(self.run_cas('solve(x^2=1,x)'),sp.FiniteSet(-1,1));self.assertEqual(self.run_cas('solve_real(x^2+1,x)'),sp.EmptySet)
        self.assertEqual(self.run_cas('solve([x+y=3,x-y=1],[x,y])'),sp.FiniteSet((2,1)))
        interval=self.run_cas('solve_real(x>1,x)');self.assertEqual(self.run_cas('ans'),interval)
        self.assertEqual(self.run_cas('solve(sin(x)=0,x)'),self.run_cas('ans'))
    def test_matrices_and_nested_outputs(self):
        matrix=self.run_cas('A:=matrix([[1,2],[3,4]])');self.assertEqual(matrix,sp.Matrix([[1,2],[3,4]]))
        self.assertEqual(self.run_cas('det(A)'),-2);self.assertEqual(self.run_cas('A[0,1]'),2)
        self.assertEqual(self.run_cas('inv(A)*A'),sp.eye(2));self.assertEqual(self.run_cas('rref(A)'),(sp.eye(2),(0,1)))
    def test_substitution_approximation_and_atomic_failure(self):
        self.assertEqual(self.run_cas('subst(x+y,{x:1,y:2})'),3);self.assertIsInstance(self.run_cas('N(pi,30)'),sp.Float)
        self.assertEqual(self.run_cas('subst(x^2,x=3)'),9)
        before=str(self.state)
        for source in ('a:=__import__(x)','open(x).read()','[x for x in [1]]','x:=x+1','1+2\n3+4'):
            with self.assertRaises((ValueError,TypeError)):calculate({'source':source,'cell':99,'state':self.state})
            self.assertEqual(str(self.state),before)
    def test_numerical_root_and_large_exact_integer(self):
        self.assertAlmostEqual(float(self.run_cas('nsolve(cos(x)-x,x,1)')),0.7390851332151607)
        self.assertEqual(self.run_cas('factorial(2000)'),sp.factorial(2000))
        self.assertEqual(self.run_cas('1e400'),10**400);self.assertEqual(self.run_cas('1e-400'),sp.Rational(1,10**400))
        self.assertEqual(self.run_cas('3e400j'),3*10**400*sp.I)
    def test_approximating_containers_keeps_structure_and_values(self):
        result=self.run_cas('approx({x:1/3},20)');self.assertIsInstance(result,dict);self.assertAlmostEqual(float(result[sp.Symbol('x')]),1/3)
        result=self.run_cas('approx([1/3,[2/3]],20)');self.assertIsInstance(result[1],list);self.assertAlmostEqual(float(result[1][0]),2/3)
        result=self.run_cas('approx(solve(x^2-2,x),20)');self.assertIsInstance(result,sp.FiniteSet);self.assertEqual(len(result),2)


if __name__=='__main__':unittest.main()
