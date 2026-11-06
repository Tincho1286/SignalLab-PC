"""Discover the complete suite and verify family coverage on one source snapshot."""
from pathlib import Path
import argparse,hashlib,json,os,sys,time,unittest
ROOT=Path(__file__).resolve().parents[1]


class RecordedResult(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.records=[];self.started={};self.bad=set()
    def startTest(self,test):self.started[test.id()]=time.monotonic();super().startTest(test)
    def addFailure(self,test,err):self.bad.add(test.id());super().addFailure(test,err)
    def addError(self,test,err):self.bad.add(test.id());super().addError(test,err)
    def addSkip(self,test,reason):self.bad.add(test.id());super().addSkip(test,reason)
    def addSubTest(self,test,subtest,outcome):
        if outcome is not None:self.bad.add(test.id())
        super().addSubTest(test,subtest,outcome)
    def stopTest(self,test):
        self.records.append({'id':test.id(),'passed':test.id() not in self.bad,'seconds':round(time.monotonic()-self.started[test.id()],3)})
        super().stopTest(test)


def identifiers(suite):
    for test in suite:
        if isinstance(test,unittest.TestSuite):yield from identifiers(test)
        else:yield test.id()



def source_snapshot():
    from audit_mathematics import fingerprint as math_fingerprint
    from check_static import fingerprint as static_fingerprint
    digest=hashlib.sha256()
    for path in sorted([*ROOT.joinpath('tests').glob('test_*.py'),*ROOT.joinpath('tools').glob('*.py')]):
        digest.update(path.relative_to(ROOT).as_posix().encode());digest.update(b'\0');digest.update(path.read_bytes().replace(b'\r\n',b'\n'));digest.update(b'\0')
    return dict(mathematics=math_fingerprint(),application=static_fingerprint(),tests_and_tools=digest.hexdigest())


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--list',action='store_true',help='Show test count without executing calculations.')
    parser.add_argument('--report',type=Path,default=ROOT/'work/integral-checks.json')
    args=parser.parse_args(argv)
    sys.path[:0]=[str(ROOT),str(ROOT/'tools'),str(ROOT/'tests')]
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
    from audit_mathematics import fingerprint,run_audit
    from check_math import FAMILIES
    source=source_snapshot();begin=time.monotonic()
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'));expected=list(identifiers(suite))
    print('Complete test discovery:',len(expected),flush=True)
    if args.list:return 0
    result=unittest.TextTestRunner(verbosity=1,resultclass=RecordedResult).run(suite)
    families={}
    for name,(prefix,minimum) in FAMILIES.items():
        rows=[row for row in result.records if row['id'].startswith(prefix+'.')]
        families[name]=dict(tests=len(rows),minimum=minimum,passed=len(rows)>=minimum and all(row['passed'] for row in rows))
    flows=[row for row in result.records if row['id'].startswith('test_workflow_contracts.WorkflowContracts.')]
    args.report.parent.mkdir(parents=True,exist_ok=True)
    audit=run_audit(args.report.with_name(args.report.stem+'-preventive.json'))
    coverage=sorted(expected)==sorted(row['id'] for row in result.records) and len(set(expected))==len(expected)
    unchanged=source==source_snapshot()
    passed=result.wasSuccessful() and not result.skipped and coverage and unchanged and audit['passed'] and all(row['passed'] for row in families.values()) and len(flows)>=47 and all(row['passed'] for row in flows)
    record=dict(passed=passed,tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),complete_discovery_coverage=coverage,source_unchanged=unchanged,source_fingerprint=source["mathematics"],source_snapshot=source,families=families,workflows=dict(tests=len(flows),passed=len(flows)>=47 and all(row['passed'] for row in flows)),preventive={key:audit[key] for key in ('passed','completed_cases','failed_cases','seeds')},seconds=round(time.monotonic()-begin,3),records=result.records)
    args.report.write_text(json.dumps(record,indent=2),encoding='utf-8')
    print('Integral audit: '+('PASS' if passed else 'FAIL'),flush=True)
    return 0 if passed else 1


if __name__=='__main__':raise SystemExit(main())
