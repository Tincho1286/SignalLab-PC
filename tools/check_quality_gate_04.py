"""Evaluate the Phase 04 numerical, resource and packaging evidence on one SHA."""

import argparse
import json
from pathlib import Path

from check_quality_gate_02c import COMPONENTS as CORE_COMPONENTS, PLATFORMS, read, within_threshold
from check_quality_gate_03 import CRITICAL as COMMUNICATIONS_COMPONENTS, _platform as phase_three_platform


CHANNEL_CRITICAL = (
    'communications_fading.py', 'communications_fading_distributions.py', 'communications_doppler.py',
    'communications_impairments.py', 'communications_interference.py', 'communications_pipeline.py',
    'communications_propagation.py',
)
PROFILES = (128, 2048, 65536)
CHANNEL_STAGES = 6


def assess_resource_evidence(report, candidate):
    profiles = report.get('profiles', [])
    latencies = report.get('cancellation', {})
    desktop = report.get('desktop', {})
    concurrency = report.get('concurrency', {})
    profile_check = (
        report.get('commit') == candidate and report.get('clean_checkout') is True
        and report.get('threads') == 1 and tuple(row.get('symbols') for row in profiles) == PROFILES
        and all(row.get('archive_verified') is True and row.get('archive_bytes', 0) > 0
                and row.get('peak_rss_bytes', 0) > 0 and row.get('model_stages') == CHANNEL_STAGES
                and row.get('sample_rate_hz') == 96000 and row.get('pulse_taps') == 81
                and set(row.get('seconds', {})) == {'compute', 'load', 'save', 'verify'}
                and all(seconds > 0 for seconds in row['seconds'].values()) for row in profiles)
    )
    cancellation = set(latencies) == {'clarke_transform', 'atomic_archive'} and all(
        row.get('discarded') is True and 0 <= row.get('seconds_after_request', float('inf')) <= 1.5
        for row in latencies.values()
    )
    responsive = (desktop.get('passed') is True and desktop.get('qt_platform') == 'offscreen'
                  and desktop.get('model_stages') == CHANNEL_STAGES and desktop.get('bit_count') == 2*PROFILES[-1]
                  and desktop.get('heartbeat_count', 0) >= 2 and 0 < desktop.get('maximum_gap_seconds', 3) <= 2)
    return {
        'channel_performance': profile_check,
        'channel_cancellation': cancellation and report.get('archive_rejected_without_changes') is True,
        'channel_concurrency': (concurrency.get('budget_bytes', 0) > concurrency.get('estimate_bytes', 0) > 0
                                and concurrency.get('competing_request_rejected') is True
                                and concurrency.get('retry_verified') is True),
        'channel_offscreen_heartbeat': responsive,
    }


def evaluate(folder, candidate, version='2.2.0'):
    platforms = {}
    for platform, label in PLATFORMS.items():
        folders = sorted(path for path in folder.glob('engineering-*') if path.is_dir() and f'-{platform}-' in path.name)
        historical = phase_three_platform(folders, candidate, label)
        coverage = read(folders, 'coverage.json') or {}
        modules = {name.replace('\\', '/').rsplit('/', 1)[-1]: row['summary']
                   for name, row in coverage.get('files', {}).items()}
        components = (*CORE_COMPONENTS, *COMMUNICATIONS_COMPONENTS, *CHANNEL_CRITICAL)
        critical = {name: within_threshold(modules.get(name, {}), 90, 85) for name in components}
        performance = read(folders, 'channel-modeling-performance.json') or {}
        portable = read(folders, 'packaged-smoke.json') or {}
        checks = {
            'phase_03_controls': all(historical['checks'].values()),
            'critical_coverage': all(cell['state'] == 'pass' for group in critical.values() for cell in group.values()),
            'preview_' + version.replace('.', '_'): historical['portable_version'] == version,
            'packaged_channel_chain': portable.get('executable_check', {}).get('checks', {}).get(
                'packaged_channel_chain') is True,
            **assess_resource_evidence(performance, candidate),
        }
        if platform == 'ubuntu-22.04' and version != '2.2.0':
            fedora = read(folders, 'fedora-updates.json') or {}
            checks['fedora_packed_updates'] = (
                fedora.get('passed') is True and fedora.get('frozen') is True
                and fedora.get('version') == version and fedora.get('target') == 'linux-x86_64'
            )
        platforms[platform] = {'checks': checks, 'critical': critical, 'historical': historical,
                               'performance': performance}
    sources = {(entry['historical']['candidate_bundle'] or {}).get('source_fingerprint')
               for entry in platforms.values()}
    passed = len(sources) == 1 and None not in sources and all(
        all(entry['checks'].values()) for entry in platforms.values()
    )
    return {'phase': '04', 'commit': candidate, 'automated_passed': passed, 'platforms': platforms}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--version', default='2.2.0')
    args = parser.parse_args()
    report = evaluate(args.input, args.candidate, args.version)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'quality-gate-04.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    lines = ['# Quality Gate automatizado de Fase 04', '', f"SHA `{args.candidate}`.", '',
             '| Plataforma | Control | Estado |', '| --- | --- | --- |']
    for platform, entry in report['platforms'].items():
        lines.extend(f"| {platform} | {key} | {'Aprobado' if status else 'Pendiente'} |"
                     for key, status in entry['checks'].items())
    lines.extend(('', 'El escritorio real y los dictámenes de cierre se registran por separado.'))
    (args.output/'quality-gate-04.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print('Quality Gate automatizado de Fase 04', 'PASS' if report['automated_passed'] else 'PENDIENTE')
    return 0 if report['automated_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
