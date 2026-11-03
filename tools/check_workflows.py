"""Required UI-workflow contracts, offscreen and isolated from user settings."""
from pathlib import Path
import json,os,platform,signal,subprocess,sys,time,unittest
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')


def worker(destination):
    sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
    suite=unittest.defaultTestLoader.loadTestsFromName('test_workflow_contracts.WorkflowContracts')
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    record=dict(contract='system-expression-workflows-v1',passed=result.wasSuccessful() and result.testsRun>=14 and not result.skipped,tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),checks=['transform_button','result_library','system_import','general_hs','export_reload','rational_regression','bilateral_boundary_analysis','dtft_plot_visibility','dtft_system_reuse','qt_error_visibility','presentation_failure_recovery','worker_diagnostic','cas_frequency_context','conditional_dtft_plot_export'])
    Path(destination).write_text(json.dumps(record,indent=2),encoding='utf-8')
    return 0 if record['passed'] else 1


def main():
    if len(sys.argv)==3 and sys.argv[1]=='--worker':return worker(sys.argv[2])
    folder=ROOT/'work';folder.mkdir(exist_ok=True);destination=folder/'workflow-checks.json';temporary=folder/'workflow-checks.pending.json';temporary.unlink(missing_ok=True)
    begin=time.monotonic();budget=300
    command=[sys.executable,'-B','-X','utf8',str(Path(__file__).resolve()),'--worker',str(temporary)]
    options=dict(cwd=ROOT,stdin=subprocess.DEVNULL)
    if sys.platform=='win32':options['creationflags']=subprocess.CREATE_NO_WINDOW|subprocess.CREATE_NEW_PROCESS_GROUP
    else:options['start_new_session']=True
    process=subprocess.Popen(command,**options);timed_out=False
    try:code=process.wait(timeout=budget)
    except subprocess.TimeoutExpired:
        timed_out=True
        if sys.platform=='win32':subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
        else:os.killpg(process.pid,signal.SIGTERM)
        try:process.wait(timeout=3)
        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=3)
        code=1
    record=json.loads(temporary.read_text(encoding='utf-8')) if temporary.exists() else dict(contract='system-expression-workflows-v1',passed=False,tests=0,error='Workflow worker did not complete.')
    record.update(passed=record['passed'] and code==0 and not timed_out,timed_out=timed_out,deadline_seconds=budget,seconds=round(time.monotonic()-begin,3),platform=sys.platform,python=platform.python_version())
    sys.path.insert(0,str(ROOT/'tools'));from audit_mathematics import fingerprint
    record['source_fingerprint']=fingerprint();destination.write_text(json.dumps(record,indent=2),encoding='utf-8');temporary.unlink(missing_ok=True)
    print('System-expression UI workflows: '+('PASS' if record['passed'] else 'FAIL'),flush=True)
    return 0 if record['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
