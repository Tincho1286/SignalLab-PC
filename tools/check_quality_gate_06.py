"""Check the cumulative RF Preview gate for the same clean Windows and Linux revision."""

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import re

from check_quality_gate_02c import PLATFORMS, read, within_threshold
from check_quality_gate_05 import evaluate as evaluate_statistics


CRITICAL = (
    'rf_network.py','rf_analysis.py','rf_line.py','rf_matching.py','rf_link.py','rf_experiments.py',
    'rf_storage.py','rf_application.py','rf_cli.py','touchstone.py',
    'advanced_fourier.py','analog_design.py','window_signals.py','window_spectrum.py','project_archive.py',
)
REQUIREMENTS = tuple(f'RF-{number:02}' for number in range(1,9))
DEMONSTRATORS = ('A','B','C','D','E','F')
PROFILES = ('multiport','cascade','touchstone','filter','spectral','uncertainty','archive')


def phase_six_version(version):
    return isinstance(version,str) and re.fullmatch(r'2\.4\.(?:0|[1-9][0-9]*)',version) is not None


def _belongs(row,candidate):
    return (row.get('schema')==1 and row.get('phase')=='06' and row.get('commit')==candidate
            and row.get('clean_checkout') is True)


def _bounded(value,limit,*,empty=False):
    return (type(value) in (int,float) and math.isfinite(value) and 0<=value<=limit
            and (empty or value>0))


def science_checks(folders,row,candidate):
    files=[file for folder in folders for file in folder.rglob('integral-checks.json')]
    identity=(_belongs(row,candidate) and len(files)==1
              and sha256(files[0].read_bytes()).hexdigest()==row.get('integral_sha256'))
    requirements=row.get('requirements',{})
    return {
        'rf_candidate_integrity':identity,
        'rf_science_and_regressions':identity and tuple(requirements)==REQUIREMENTS and all(
            entry.get('passed') is True and type(entry.get('reference_cases')) is int
            and entry['reference_cases']>0 for entry in requirements.values()),
        'rf_interface_parity':identity and all(row.get(key) is True for key in ('desktop','headless','interface_parity')),
        'rf_open_defects':identity and type(row.get('p0_open')) is int and row['p0_open']==0
            and type(row.get('p1_internal_open')) is int and row['p1_internal_open']==0,
        'rf_demonstrators':identity and _demonstrators(files[0].parent/'rf-demonstrators',row.get('demonstrators',{})),
    }


def _demonstrators(folder, reports):
    if tuple(reports)!=DEMONSTRATORS:
        return False
    for label in DEMONSTRATORS:
        key=f'{label}/report.json'
        summary=reports[label]
        report=folder/key
        if (summary.get('passed') is not True or summary.get('report')!=key or not report.is_file()
                or sha256(report.read_bytes()).hexdigest()!=summary.get('sha256')):
            return False
        content=json.loads(report.read_bytes())
        entries=content.get('checks',[])
        if not entries or len(entries)!=summary.get('reference_cases') or content.get('demonstrator')!=label:
            return False
        for row in entries:
            actual,reference,tolerance=(row.get(name) for name in ('actual','reference','absolute_tolerance'))
            if not all(type(value) in (int,float) and math.isfinite(value) for value in (actual,reference,tolerance)):
                return False
            if abs(actual-reference)>tolerance:
                return False
    return True


def resource_checks(row,candidate,platform):
    identity=_belongs(row,candidate) and row.get('threads')==1 and str(row.get('platform','')).startswith(
        PLATFORMS[platform])
    profiles=row.get('profiles',{})
    guards=tuple(profiles)==PROFILES and all(
        isinstance(values,list) and len(values)==2 and all(
            probe.get('verified') is True and probe.get('scale')==i
            and _bounded(probe.get('seconds'),30)
            and _bounded(probe.get('peak_rss_bytes'),1024**3)
            and _bounded(probe.get('max_observed_reservation_bytes'),256*1024**2)
            and bool(probe.get('parameters')) for i,probe in enumerate(values,1))
        for values in profiles.values())
    cancel=row.get('cancellation',{})
    gui=row.get('desktop',{})
    cold=gui.get('cold_open_seconds',{})
    return {
        'rf_profiles':identity and guards,
        'rf_cancellation':identity and cancel.get('discarded') is True and cancel.get('retry') is True
            and _bounded(cancel.get('seconds_after_request'),1.5,empty=True),
        'rf_desktop_profiles':identity and gui.get('platform_plugin')=='offscreen' and gui.get('verified') is True
            and all(_bounded(gui.get(key),limit) for key,limit in (
                ('seconds_startup',15),('warm_navigation_median_seconds',.5),
                ('warm_navigation_max_seconds',1.5),('seconds_render',3),('peak_rss_bytes',1024**3)))
            and set(cold)=={'network','line','link','spectral'} and all(_bounded(value,3) for value in cold.values()),
    }


def evaluate(folder,candidate,version):
    if not phase_six_version(version):
        raise ValueError('Fase 06 requiere una versión Preview 2.4.x.')
    previous=evaluate_statistics(folder,candidate,version,cumulative=True)
    platforms={}
    for platform in PLATFORMS:
        directories=sorted(path for path in folder.glob('engineering-*')
                           if path.is_dir() and f'-{platform}-' in path.name)
        prior=previous['platforms'][platform]
        raw=read(directories,'coverage.json') or {}
        modules={path.replace('\\','/').rsplit('/',1)[-1]:row for path,row in raw.get('files',{}).items()}
        critical={name:within_threshold(modules.get(name,{}).get('summary',{}),90,85) for name in CRITICAL}
        global_coverage=within_threshold(raw.get('totals',{}),85,75)
        science=read(directories,'rf-qualification.json') or {}
        resources=read(directories,'rf-performance.json') or {}
        packaged=read(directories,'packaged-smoke.json') or {}
        package=packaged.get('executable_check',{}).get('checks',{})
        checks={'cumulative_phase_05':all(prior['checks'].values()),
                'rf_critical_coverage':all(cell['state']=='pass' for results in critical.values() for cell in results.values()),
                'global_coverage':all(cell['state']=='pass' for cell in global_coverage.values()),
                'packaged_rf':package.get('packaged_rf_network_and_project') is True
                and package.get('packaged_rf_workbench') is True,
                **science_checks(directories,science,candidate),**resource_checks(resources,candidate,platform)}
        platforms[platform]={'checks':checks,'critical':critical,'global_coverage':global_coverage,
                             'science':science,'resources':resources,'candidate_bundle':prior['candidate_bundle'],
                             'phase_05':prior}
    passed=previous['automated_passed'] and all(all(row['checks'].values()) for row in platforms.values())
    return {'schema':1,'phase':'06','version':version,'commit':candidate,'automated_passed':passed,
            'platforms':platforms,'combined_native_coverage':previous['combined_native_coverage']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--candidate',required=True)
    parser.add_argument('--version',required=True)
    args=parser.parse_args()
    report=evaluate(args.input,args.candidate,args.version)
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'quality-gate-06.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    words=['# Quality Gate de Fase 06','',f"SHA `{args.candidate}`",
           '', 'Aprobado' if report['automated_passed'] else 'Pendiente', '',
           '| Plataforma | Control | Resultado |','| --- | --- | --- |']
    for platform,row in report['platforms'].items():
        for key,passed in row['checks'].items():
            words.append(f"| {platform} | {key} | {'Aprobado' if passed else 'Pendiente'} |")
    (args.output/'quality-gate-06.md').write_text('\n'.join(words)+'\n',encoding='utf-8')
    return 0 if report['automated_passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
