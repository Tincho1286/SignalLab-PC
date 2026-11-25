"""Aggregate one clean candidate's Windows and Linux engineering evidence."""

import argparse
import json
from math import ceil
from pathlib import Path


COMPONENTS = {
    'sampling.py': (90, 85), 'fourier.py': (90, 85),
    'execution.py': (90, 85), 'dft_application.py': (None, 85),
    'dsp_application.py': (90, 85), 'dsp_pipeline.py': (90, 85),
    'scientific_storage.py': (90, 85), 'project_archive.py': (90, 85),
    'cas_worksheet.py': (90, 85), 'session_desktop.py': (90, 85),
    'cli_session.py': (90, 85), 'operation_provenance.py': (None, 85), 'project.py': (None, 85),
}
PLATFORMS = {'windows-2022': 'Windows', 'ubuntu-22.04': 'Linux'}
CANCELLATION_OPERATIONS = {
    'dft', 'idft', 'fir', 'resample', 'psd', 'pipeline', 'slbin_write', 'archive_save',
    'json_write', 'session_load', 'archive_load', 'mat_classic', 'mat_hdf5', 'slbin_read',
}


def read(folders, filename):
    matches = [path for folder in folders for path in folder.rglob(filename)]
    if len(matches) != 1:
        return None
    return json.loads(matches[0].read_text(encoding='utf-8'))


def within_threshold(summary, lines, branches):
    checks = {}
    for measured, target, total, covered in (
        ('lines', lines, 'num_statements', 'covered_lines'),
        ('branches', branches, 'num_branches', 'covered_branches'),
    ):
        if target is None:
            continue
        size, hit = summary.get(total, 0), summary.get(covered, 0)
        valid = type(size) is int and type(hit) is int and 0 <= hit <= size
        state = ('fail' if not valid else 'missing' if not size else
                 'pass' if 100*hit >= target*size else 'fail')
        checks[measured] = {
            'goal': target, 'covered': hit, 'total': size, 'state': state,
            'additional_required': max(0, ceil(target*size/100)-hit) if valid and size else None,
        }
    return checks


def evidence(folder, revision, platform):
    baseline = read(folder, 'baseline.json') or {}
    suite = read(folder, 'integral-checks.json') or {}
    preventive = read(folder, 'integral-checks-preventive.json') or {}
    coverage = read(folder, 'coverage.json') or {}
    performance = read(folder, 'core-performance.json') or {}
    campaign = read(folder, 'scientific-campaign.json') or {}
    recovery = read(folder, 'recovery-responsiveness.json') or {}
    inventory = read(folder, 'native-inventory.json') or {}
    sbom = read(folder, 'native.cdx.json') or {}
    portable = read(folder, 'packaged-smoke.json') or {}
    installer = read(folder, 'update.json') or {}
    upgrade = installer.get('upgrade_from_stable', {})

    def verdict(document, condition):
        return 'pass' if document and condition else 'fail' if document else 'missing'

    def modules_by_name():
        return {Path(path.replace('\\', '/')).name: row['summary']
                for path, row in coverage.get('files', {}).items()}

    coverage_matches = coverage.get('totals') == (baseline.get('coverage') or {}).get('total')
    modules = modules_by_name()
    native = {(row['path'], row['sha256']) for row in inventory.get('native_files', [])}
    declared = {(row['name'], row['hashes'][0]['content']) for row in sbom.get('components', [])}
    stages = baseline.get('stages', {})
    executable = portable.get('executable_check', {})
    cancellations = performance.get('cancellation', [])
    cancellation_states = [row.get('status') == 'completed_before_acknowledgement'
                           or row.get('status') == 'cancelled' and row.get('files_preserved') is True
                           for row in cancellations]
    gaps = [
        dict(file=path.replace('\\', '/'), lines=row['summary']['missing_lines'],
             branches=row['summary']['num_branches']-row['summary']['covered_branches'])
        for path, row in coverage.get('files', {}).items()
    ]
    return {
        'checks': {
            'clean_revision': verdict(baseline, baseline.get('commit') == revision == baseline.get('commit_after')
                                      and baseline.get('os', '').startswith(platform)),
            'integral': verdict(suite, suite.get('passed') is True and suite.get('source_unchanged') is True
                                and suite.get('complete_discovery_coverage') is True and suite.get('tests', 0) >= 890
                                and stages.get('integral') == 0),
            'static': verdict(baseline, stages.get('static') == 0),
            'preventive': verdict(preventive, preventive.get('passed') is True
                                  and preventive.get('completed_cases', 0) >= 150
                                  and preventive.get('source_fingerprint') == suite.get('source_fingerprint')),
            'coverage_matches': verdict(coverage, coverage_matches),
            'performance': verdict(performance, performance.get('commit') == revision
                                   and performance.get('clean_checkout') is True
                                   and len(performance.get('measurements', [])) >= 71),
            'cancellation_profiles': verdict(performance, len(cancellations) >= 22
                                             and {row.get('operation') for row in cancellations} >= CANCELLATION_OPERATIONS
                                             and all(cancellation_states)
                                             and bool(performance.get('symbolic_cancellation'))),
            'campaign': verdict(campaign, campaign.get('commit') == revision
                                and campaign.get('clean_checkout') is True
                                and campaign.get('integrity_verified') is True
                                and len(campaign.get('runs', [])) == 48
                                and campaign.get('interruption', {}).get('catalog_preserved') is True),
            'recovery_responsiveness_measured': verdict(recovery, recovery.get('commit') == revision
                                                       and recovery.get('clean_checkout') is True
                                                       and len(recovery.get('trials', [])) == 6),
            'portable': verdict(portable, executable.get('ok') is True and executable.get('frozen') is True
                                and executable.get('checks', {}).get('packaged_cas_session') is True),
            'sbom': verdict(inventory, inventory.get('source_commit') == revision and bool(native)
                            and declared == native and all(row.get('sources') for row in inventory['native_files'])),
            'isolated_upgrade': verdict(installer, installer.get('temporary_signature_verified') is True
                                        and installer.get('production_key_rejected_test_signature') is True
                                        and installer.get('native_installation', {}).get('passed') is True
                                        and upgrade.get('from') == '2.0.0' and upgrade.get('to') != '2.0.0'
                                        and all(upgrade.get(key) is True for key in
                                                ('session_preserved', 'corrupt_download_rejected', 'in_place'))),
        },
        'tests': suite.get('tests', 0),
        'coverage': within_threshold(coverage.get('totals', {}), 85, 75),
        'components': {name: within_threshold(modules.get(name, {}), *target)
                       for name, target in COMPONENTS.items()},
        'coverage_priority': {
            metric: sorted(gaps, key=lambda item: (-item[metric], item['file']))[:15]
            for metric in ('lines', 'branches')
        },
    }


def render(report):
    lines = ['# Quality Gate de Fase 02C', '', f"Candidato `{report['commit']}`.", '',
             '| Plataforma | Criterio | Estado |', '| --- | --- | --- |']
    for platform, result in report['platforms'].items():
        for check, status in result['checks'].items():
            lines.append(f'| {platform} | {check} | {status} |')
        for name, coverage in {'global': result['coverage'], **result['components']}.items():
            for metric, values in coverage.items():
                hit, total, goal, state = (values[key] for key in ('covered', 'total', 'goal', 'state'))
                lines.append(f'| {platform} | {name} · {metric} {hit}/{total} (objetivo {goal} %) | {state} |')
    lines += ['', 'El resultado automático requiere revisión de los hallazgos y de la evidencia externa.',
              '', '| Control externo | Estado |', '| --- | --- |']
    lines.extend(f'| {name} | {state} |' for name, state in report['external'].items())
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--require-automated', action='store_true')
    args = parser.parse_args()
    data = {}
    for name, platform in PLATFORMS.items():
        artifacts = [folder for folder in args.input.glob('engineering-*')
                     if folder.is_dir() and f'-{name}-' in folder.name]
        data[name] = evidence(artifacts, args.candidate, platform)
    report = {'commit': args.candidate, 'platforms': data,
              'automated_passed': all(
                  all(state == 'pass' for state in result['checks'].values())
                  and all(item['state'] == 'pass' for group in
                          [result['coverage'], *result['components'].values()] for item in group.values())
                  for result in data.values()
              ),
              'external': {'escritorio físico y DPI': 'review_required',
                           'avisos nativos y mitigaciones': 'review_required',
                           'firma y canal público': 'review_required',
                           'hallazgos y decisiones de cierre': 'review_required'}}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'quality-gate.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    markdown = render(report)
    (args.output/'quality-gate.md').write_text(markdown, encoding='utf-8')
    print('Quality Gate automatizado:', 'PASS' if report['automated_passed'] else 'PENDIENTE')
    return int(args.require_automated and not report['automated_passed'])


if __name__ == '__main__':
    raise SystemExit(main())
