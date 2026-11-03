"""A bounded release gate with an explicit contract for each math family."""
from pathlib import Path
import json,platform,sys,time,unittest

ROOT=Path(__file__).resolve().parents[1]
CONTRACT='mathematical-families-v2'
# Requiring each named family prevents a missing import/file from becoming a pass.
FAMILIES={
    'transforms':('test_math_reliability.MathematicalReliabilityTests',21),
    'transform_properties':('test_math_shifted_pairs.ShiftedPairContracts',7),
    'preventive_regressions':('test_math_preventive.PreventiveContracts',6),
    'expression_systems':('test_math_expression_systems.ExpressionSystemContracts',5),
    'scalar_input':('test_math_contracts.ScalarContracts',5),
    'systems_filters':('test_math_contracts.SystemContracts',9),
    'equations':('test_math_contracts.EquationContracts',5),
    'fourier_measures':('test_math_contracts.FourierContracts',5),
    'signals_windows':('test_math_contracts.SignalContracts',5),
    'state_space':('test_math_contracts.StateContracts',2),
    'sampling_precision':('test_math_contracts.SamplingContracts',3),
    'random_signals':('test_math_contracts.RandomContracts',1),
}


class FamilyResult(unittest.TextTestResult):
    def startTest(self,test):
        self.family=next((key for key,(prefix,_) in FAMILIES.items() if test.id().startswith(prefix+'.')),'unregistered')
        row=self.families.setdefault(self.family,{'tests':0,'failures':0,'errors':0,'skipped':0})
        row['tests']+=1
        super().startTest(test)
    def addFailure(self,test,err):self.families[self.family]['failures']+=1;super().addFailure(test,err)
    def addError(self,test,err):self.families[self.family]['errors']+=1;super().addError(test,err)
    def addSkip(self,test,reason):self.families[self.family]['skipped']+=1;super().addSkip(test,reason)
    def addSubTest(self,test,subtest,outcome):
        if outcome is not None:
            kind='failures' if issubclass(outcome[0],test.failureException) else 'errors'
            self.families[self.family][kind]+=1
        super().addSubTest(test,subtest,outcome)
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.families={}


def main():
    sys.path[:0]=[str(ROOT),str(ROOT/'tests')];begin=time.monotonic()
    import sympy,numpy,scipy
    print(CONTRACT+' | Python '+platform.python_version()+' | '+sys.platform+' | SymPy '+sympy.__version__,flush=True)
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name,_ in FAMILIES.values())
    result=unittest.TextTestRunner(verbosity=2,resultclass=FamilyResult).run(suite)
    for family,(_,minimum) in FAMILIES.items():
        row=result.families.setdefault(family,{'tests':0,'failures':0,'errors':0,'skipped':0})
        row['minimum']=minimum
        row['passed']=row['tests']>=minimum and not any(row[k] for k in ('failures','errors','skipped'))
    success=result.wasSuccessful() and not result.skipped and all(row.get('passed',False) for row in result.families.values())
    from audit_mathematics import run_audit
    audit=run_audit(ROOT/'work/math-audit.json')
    success=success and audit['passed'] and audit['completed_cases']>=112 and len(audit['seeds'])==2
    summary={name:audit[name] for name in ('contract','passed','seeds','source_fingerprint','case_deadline_seconds','expected_cases','completed_cases','failed_cases','timeout','groups','seconds')}
    record={'preventive_audit':summary,'contract':CONTRACT,'passed':success,'families':result.families,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'seconds':round(time.monotonic()-begin,3),'python':platform.python_version(),'platform':sys.platform,'sympy':sympy.__version__,'numpy':numpy.__version__,'scipy':scipy.__version__}
    folder=ROOT/'work';folder.mkdir(exist_ok=True);(folder/'math-checks.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print('Mathematical release gate: '+('PASS' if success else 'FAIL'),flush=True)
    return 0 if success else 1


if __name__=='__main__':raise SystemExit(main())
