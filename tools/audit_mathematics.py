"""Bounded, reproducible parameter sweep that blocks releases on failure or timeout."""
from pathlib import Path
import argparse,hashlib,json,platform,subprocess,sys,tempfile,time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(Path(__file__).resolve().parent)]
from math_audit_cases import SEED,catalog
CONTRACT='preventive-math-audit-v1'


def worker(case_file,event_file,result_file):
    from math_audit_cases import check
    records=[]
    with Path(event_file).open('w',encoding='utf-8') as events:
        for case in json.loads(Path(case_file).read_text(encoding='utf-8')):
            events.write(json.dumps({'event':'started','id':case['id']})+'\n');events.flush();begin=time.monotonic()
            row=dict(case)
            try:row.update(passed=True,oracle=check(case))
            except Exception as exc:
                row.update(passed=False,error=type(exc).__name__+': '+str(exc)[:3000])
            row['seconds']=round(time.monotonic()-begin,3);records.append(row)
            events.write(json.dumps({'event':'finished','result':row})+'\n');events.flush()
    Path(result_file).write_text(json.dumps(records,indent=2),encoding='utf-8')
    return 0 if all(row['passed'] for row in records) else 1


def fingerprint():
    names=('engine','symbolic','impulse_pairs','singularities','expression_definition','laplace_algebra','z_algebra','z_direct_pairs','dtft_pairs','scalar_expression','difference_equations','filters','rational_frequency','transfer_plane','fourier','operations','sampling','state_space','windowing','precision','cas_engine','cas_assumptions','analytic_frequency','system_analysis_panel','system_import','result_expressions','transfer_input','transform_lab','frequency_analysis','system_conditions','symbolic_fourier_panel','runtime_diagnostics','ui','cas_context','cas_system_context','transform_context','system_clock','signal_notation','expression_dialects','continuous_expression','cas_transfer','cas_import','matlab_import','model','storage','project','expression_grid_view','plot_actions','plot_view','expression_measures_panel','measures_symbolic','control','temporal_panel','z_inverse','z_properties','z_series_inverse','radial_conditions','frequency_phase','fourier_phase','course_tools','course_tools_panel','systems_panel','fourier_panel','state_frequency','state_space_panel','realization','frequency_filter','amplitude_design','band_extrema','plot_scale','plot_limits_dialog')
    paths=[ROOT/'tools/math_audit_cases.py',*[ROOT/'signallab_pc'/(name+'.py') for name in names]]
    digest=hashlib.sha256()
    for path in paths:
        digest.update(path.relative_to(ROOT).as_posix().encode('utf-8'));digest.update(b'\0');digest.update(path.read_bytes().replace(b'\r\n',b'\n'));digest.update(b'\0')
    return digest.hexdigest()


def run_audit(report_path,*,seed=None,case_seconds=20):
    if not 0<case_seconds<=120:raise ValueError('The audit case budget must be between 0 and 120 seconds.')
    report_path=Path(report_path);report_path.parent.mkdir(parents=True,exist_ok=True);begin=time.monotonic();source=fingerprint()
    seeds=list(dict.fromkeys([SEED,int(source[:8],16)])) if seed is None else [seed]
    cases=[]
    for selected in seeds:
        for case in catalog(selected):
            case['seed']=selected;case['id']=str(selected)+'/'+case['id'];cases.append(case)
    records=[];timeout=None
    with tempfile.TemporaryDirectory(prefix='math-audit-',dir=report_path.parent) as folder:
        folder=Path(folder);case_file=folder/'cases.json';events=folder/'events.jsonl';result_file=folder/'result.json';errors=folder/'worker.stderr'
        case_file.write_text(json.dumps(cases),encoding='utf-8');events.write_text('',encoding='utf-8')
        command=[sys.executable,'-B','-X','utf8',str(Path(__file__).resolve()),'--worker',str(case_file),str(events),str(result_file)]
        with errors.open('w',encoding='utf-8') as stderr:
            process=subprocess.Popen(command,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=stderr,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            previous=None;last_progress=time.monotonic();active='worker_startup'
            try:
                while process.poll() is None:
                    text=events.read_text(encoding='utf-8')
                    valid=[]
                    for line in text.splitlines():
                        try:valid.append(json.loads(line))
                        except json.JSONDecodeError:continue
                    if valid:
                        key=(len(valid),valid[-1].get('event'),valid[-1].get('id'))
                        if key!=previous:previous=key;last_progress=time.monotonic()
                        if valid[-1]['event']=='started':active=valid[-1]['id']
                    if time.monotonic()-last_progress>case_seconds:
                        timeout={'case':active,'seconds':case_seconds};break
                    try:process.wait(timeout=.1)
                    except subprocess.TimeoutExpired:pass
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:process.wait(timeout=2)
                    except subprocess.TimeoutExpired:process.kill();process.wait(timeout=2)
        if result_file.exists():records=json.loads(result_file.read_text(encoding='utf-8'))
        else:
            for line in events.read_text(encoding='utf-8').splitlines():
                try:
                    event=json.loads(line)
                    if event['event']=='finished':records.append(event['result'])
                except json.JSONDecodeError:continue
        error=errors.read_text(encoding='utf-8')[-3000:]
    groups={}
    for case in cases:groups.setdefault(case['group'],{'expected':0,'completed':0,'failed':0})['expected']+=1
    for row in records:
        group=groups[row['group']];group['completed']+=1;group['failed']+=int(not row['passed'])
    passed=process.returncode==0 and timeout is None and len(records)==len(cases) and all(r['passed'] for r in records)
    report={'contract':CONTRACT,'passed':passed,'seeds':seeds,'source_fingerprint':source,'case_deadline_seconds':case_seconds,'expected_cases':len(cases),'completed_cases':len(records),'failed_cases':sum(not r['passed'] for r in records),'timeout':timeout,'groups':groups,'cases':records,'seconds':round(time.monotonic()-begin,3),'platform':sys.platform,'python':platform.python_version(),'worker_error':error or None}
    report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Preventive math sweep: '+('PASS' if passed else 'FAIL')+' | '+str(len(records))+'/'+str(len(cases))+' cases | seeds '+', '.join(map(str,seeds)),flush=True)
    for row in records:
        if not row['passed']:print(row['id']+': '+row['error'],flush=True)
    if timeout:print('Case deadline exceeded: '+timeout['case'],flush=True)
    if error:print(error,flush=True)
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--worker',nargs=3);parser.add_argument('--seed',type=int);parser.add_argument('--case-seconds',type=float,default=20);parser.add_argument('--report',default=str(ROOT/'work/math-audit.json'));args=parser.parse_args()
    if args.worker:return worker(*args.worker)
    return 0 if run_audit(args.report,seed=args.seed,case_seconds=args.case_seconds)['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
