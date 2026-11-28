"""Bind Phase 06 demonstrators and input/desktop parity to an integral candidate run."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

from check_engineering_baseline import clean_revision
from qualify_statistics import WithoutQt

ROOT=Path(__file__).resolve().parents[1]

REQUIREMENTS={
    'RF-01':('test_rf_network',),
    'RF-02':('test_rf_network',),
    'RF-03':('test_rf_line_matching',),
    'RF-04':('test_rf_link_bessel','test_math_lti_workflows'),
    'RF-05':('test_rf_link_bessel',),
    'RF-06':('test_advanced_fourier',),
    'RF-07':('test_rf_experiments',),
    'RF-08':('test_touchstone_rf_storage','test_rf_application','test_rf_workbench'),
}


def qualify(folder, defects):
    revision=clean_revision()
    baseline=json.loads((folder/'baseline.json').read_bytes())
    raw=(folder/'integral-checks.json').read_bytes()
    integral=json.loads(raw)
    if (baseline.get('commit'),baseline.get('commit_after'),integral.get('passed'))!=(revision,revision,True):
        raise ValueError('La calificación RF requiere el candidato limpio y su suite integral aprobada.')
    rows=integral['records']
    by_group={}
    for row in rows:
        by_group.setdefault(row['id'].split('.')[0],[]).append(row)
    requirements={}
    for key,suites in REQUIREMENTS.items():
        included=[by_group.get(name,()) for name in suites]
        requirements[key]={'passed':all(group and all(row['passed'] is True for row in group) for group in included),
                           'reference_cases':sum(map(len,included)),'suites':list(suites)}
    tracked=json.loads(defects.read_bytes())['findings']
    current=[row for row in tracked if row['status']!='closed']
    finder=WithoutQt()
    sys.meta_path.insert(0,finder)
    try:
        from rf_demonstrators import run
        from signallab_pc.atomic_file import write_json
        examples=run(folder/'rf-demonstrators')
    finally:
        sys.meta_path.remove(finder)
    if clean_revision()!=revision:
        raise RuntimeError('Cambió el candidato mientras se ejecutaban los demostradores RF.')
    parity=any(row['id'].endswith('test_headless_cli_matches_python_and_reopens_existing_network')
               and row['passed'] is True for row in by_group.get('test_rf_application',()))
    gui=by_group.get('test_rf_workbench',[])
    report={'schema':1,'phase':'06','commit':revision,'clean_checkout':True,
            'integral_sha256':sha256(raw).hexdigest(),'requirements':requirements,'demonstrators':examples,
            'headless':True,'desktop':bool(gui and all(row['passed'] is True for row in gui)),
            'interface_parity':parity,'p0_open':sum(row['priority']=='P0' for row in current),
            'p1_internal_open':sum(row['priority']=='P1' and row['internal'] for row in current)}
    write_json(folder/'rf-qualification.json',report)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--defects',type=Path,required=True)
    args=parser.parse_args()
    sys.path.insert(0,str(ROOT))
    result=qualify(args.output,args.defects)
    if not all(row['passed'] for row in result['requirements'].values()) or not all(
        result[key] for key in ('headless','desktop','interface_parity')
    ) or result['p0_open'] or result['p1_internal_open']:
        raise SystemExit('La calificación RF contiene controles pendientes.')
