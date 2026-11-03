"""Release gate for a focused set of exact mathematical reference cases."""
from pathlib import Path
import json,platform,sys,time,unittest

ROOT=Path(__file__).resolve().parents[1]


def main():
    sys.path.insert(0,str(ROOT));begin=time.monotonic()
    import sympy,numpy,scipy
    print('Mathematical contract v1 | Python '+platform.python_version()+' | '+sys.platform+' | SymPy '+sympy.__version__,flush=True)
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_math_reliability.py')
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    success=result.wasSuccessful() and result.testsRun>=15
    record={'contract':'core-transform-contract-v1','passed':success,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'seconds':round(time.monotonic()-begin,3),'python':platform.python_version(),'platform':sys.platform,'sympy':sympy.__version__,'numpy':numpy.__version__,'scipy':scipy.__version__}
    folder=ROOT/'work';folder.mkdir(exist_ok=True);(folder/'math-checks.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print('Mathematical release gate: '+('PASS' if success else 'FAIL'),flush=True)
    return 0 if success else 1


if __name__=='__main__':raise SystemExit(main())
