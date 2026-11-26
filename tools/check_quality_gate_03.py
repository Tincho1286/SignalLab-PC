"""Verify Phase 03 coverage, measurements and release preparation on one SHA."""

import argparse
import json
from pathlib import Path

from check_quality_gate_02c import PLATFORMS, evidence, read, within_threshold


CRITICAL = (
    'communications_data.py', 'communications_modulation.py', 'communications_pulses.py',
    'communications_channel.py', 'communications_receiver.py', 'communications_metrics.py',
    'communications_experiment.py', 'communications_storage.py', 'communications_sweep.py',
    'communications_cli.py',
)


def _platform(folders, candidate, operating_system):
    core = evidence(folders, candidate, operating_system)
    coverage = read(folders, 'coverage.json') or {}
    tests = read(folders, 'integral-checks.json') or {}
    performance = read(folders, 'communications-performance.json') or {}
    native = read(folders, 'native-inventory.json') or {}
    portable = read(folders, 'packaged-smoke.json') or {}
    update = read(folders, 'update.json') or {}
    bundle = read(folders, 'candidate-bundle.json') or {}
    modules = {name.replace('\\', '/').rsplit('/', 1)[-1]: row['summary']
               for name, row in coverage.get('files', {}).items()}
    critical = {name: within_threshold(modules.get(name, {}), 90, 85) for name in CRITICAL}
    runs = [row for row in tests.get('records', []) if row['id'].startswith('test_communications_')]
    profiles = performance.get('profiles', [])
    cancellations = performance.get('cancellation', {})
    desktop = performance.get('desktop', {})
    runtime = portable.get('executable_check', {}).get('runtime', {})
    checks = {
        'core': all(value == 'pass' for value in core['checks'].values()) and all(
            cell['state'] == 'pass' for group in (core['coverage'], *core['components'].values())
            for cell in group.values()),
        'scientific_suite': len(runs) >= 64 and all(row.get('passed') is True for row in runs),
        'critical_coverage': all(cell['state'] == 'pass' for metrics in critical.values() for cell in metrics.values()),
        'performance': performance.get('commit') == candidate and performance.get('clean_checkout') is True
        and [row.get('symbols') for row in profiles] == [128, 2048, 65536]
        and all(row.get('archive_verified') is True and row.get('peak_rss_bytes', 0) > 0 for row in profiles),
        'cancellation': set(cancellations) == {'fir', 'awgn', 'persistence'} and all(
            row.get('discarded') is True and 0 <= row.get('seconds_after_request', 2) <= 1.5
            for row in cancellations.values()),
        'sweep_and_archive': performance.get('sweep', {}).get('verified') is True
        and performance['sweep'].get('runs') == 8,
        'desktop_responsiveness': desktop.get('passed') is True and desktop.get('heartbeat_count', 0) >= 2
        and 0 < desktop.get('maximum_gap_seconds', 3) <= 2,
        'packaged_link': portable.get('executable_check', {}).get('checks', {}).get(
            'packaged_communications_link_and_project') is True,
        'fixed_native_runtime': runtime.get('qt') == '6.12.1' and runtime.get('pillow_jpeg2000') is False
        and native.get('runtime', {}).get('qt', {}).get('version') == '6.12.1'
        and not any('openjp' in row['path'].lower() for row in native.get('native_files', [])),
        'isolated_preview': update.get('channel') == 'preview' and update.get('other_channel_rejected') is True
        and update.get('production_key_rejected_test_signature') is True,
        'candidate_bundle': bundle.get('commit') == candidate and bundle.get('channel') == 'preview'
        and bundle.get('version') == (update.get('upgrade_from_stable') or {}).get('to')
        and bundle.get('installer_sha256') == update.get('sha256')
        and bundle.get('portable_sha256') == native.get('artifact_sha256') and bool(bundle.get('files')),
    }
    return {'checks': checks, 'coverage': core['coverage'], 'critical': critical,
            'communications_tests': len(runs), 'integral_tests': core['tests'], 'portable_version': bundle.get('version'),
            'candidate_bundle': bundle if checks['candidate_bundle'] else None}


def evaluate(folder, candidate):
    platforms = {}
    for name, operating_system in PLATFORMS.items():
        reports = [path for path in folder.glob('engineering-*') if path.is_dir() and f'-{name}-' in path.name]
        platforms[name] = _platform(reports, candidate, operating_system)
    versions = {value['portable_version'] for value in platforms.values()}
    source = {value['candidate_bundle'].get('source_fingerprint') if value['candidate_bundle'] else None
              for value in platforms.values()}
    passed = len(versions) == 1 and None not in versions and len(source) == 1 and None not in source and all(
        all(platform['checks'].values()) for platform in platforms.values()
    )
    return {'phase': '03', 'commit': candidate, 'platforms': platforms, 'automated_passed': passed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--candidate', required=True)
    args = parser.parse_args()
    report = evaluate(args.input, args.candidate)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'quality-gate-03.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    lines = ['# Quality Gate automatizado de Fase 03', '', f"SHA `{report['commit']}`.", '',
             '| Plataforma | Control | Estado |', '| --- | --- | --- |']
    for name, data in report['platforms'].items():
        lines.extend(f"| {name} | {key} | {'Aprobado' if passed else 'Pendiente'} |"
                     for key, passed in data['checks'].items())
    (args.output/'quality-gate-03.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print('Quality Gate automatizado de Fase 03', 'PASS' if report['automated_passed'] else 'PENDIENTE')
    return 0 if report['automated_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
