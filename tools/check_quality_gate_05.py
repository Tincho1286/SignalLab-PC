"""Verify Phase 05 Preview evidence while retaining the accumulated Phase 04 gate."""

import argparse
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import re

from check_quality_gate_02c import PLATFORMS, read, within_threshold
from check_quality_gate_04 import evaluate as evaluate_channels


CRITICAL = ('probability.py', 'multivariate_probability.py', 'probability_cli.py',
            'descriptive_statistics.py', 'statistics_cli.py', 'statistical_inference.py',
            'statistics_results.py', 'stochastic_processes.py', 'stochastic_cli.py', 'realization_batch.py',
            'stochastic_noise.py', 'stochastic_covariance.py', 'ar_estimation.py', 'random_models.py',
            'time_series_identification.py', 'statistical_spectra.py', 'optimal_estimation.py',
            'wiener_filter.py', 'kalman_filter.py', 'adaptive_filter.py',
            'monte_carlo.py', 'monte_carlo_bootstrap.py', 'campaign_files.py')
SCIENTIFIC_REQUIREMENTS = tuple(f'ST-{number:02}' for number in range(1, 10))
DEMONSTRATORS = ('A', 'B', 'C', 'D', 'E')
RESOURCE_PROFILES = (
    'realizations', 'joint_covariance', 'identification', 'spectral',
    'kalman', 'adaptive', 'monte_carlo', 'archive',
)
NATIVE_LOCK_MODULE = 'campaign_files.py'


def phase_five_version(version):
    return isinstance(version, str) and re.fullmatch(r'2\.3\.(?:0|[1-9][0-9]*)', version) is not None


def _belongs_to(report, candidate):
    return (
        type(report.get('schema')) is int and report['schema'] == 1
        and report.get('phase') == '05' and report.get('commit') == candidate
        and report.get('clean_checkout') is True
    )


def science_checks(report, candidate):
    requirements = report.get('requirements', {})
    examples = report.get('demonstrators', {})
    count = lambda key: requirements.get(key, {}).get('reference_cases')
    return {
        'scientific_requirements': _belongs_to(report, candidate) and all(
            requirements.get(key, {}).get('passed') is True and type(count(key)) is int and count(key) > 0
            for key in SCIENTIFIC_REQUIREMENTS
        ),
        'demonstrators': _belongs_to(report, candidate) and all(
            examples.get(name, {}).get('passed') is True
            and isinstance(examples[name].get('sha256'), str)
            and re.fullmatch(r'[0-9a-f]{64}', examples[name]['sha256'])
            for name in DEMONSTRATORS
        ),
        'scientific_interface_parity': _belongs_to(report, candidate) and all(
            report.get(key) is True for key in ('headless', 'desktop', 'interface_parity')
        ),
        'defects': _belongs_to(report, candidate)
        and type(report.get('p0_open')) is int and report['p0_open'] == 0
        and type(report.get('p1_internal_open')) is int and report['p1_internal_open'] == 0,
    }


def science_artifacts(folders, report):
    integrals = [path for folder in folders for path in folder.rglob('integral-checks.json')]
    if len(integrals)!=1 or sha256(integrals[0].read_bytes()).hexdigest()!=report.get('integral_sha256'):
        return False
    evidence_root = integrals[0].parent/'demonstrators'
    entries = report.get('demonstrators',{})
    for name in DEMONSTRATORS:
        row = entries.get(name,{})
        relative = f'{name}/report.json'
        path = evidence_root/relative
        if row.get('report')!=relative or not path.is_file():
            return False
        data = path.read_bytes()
        if sha256(data).hexdigest()!=row.get('sha256'):
            return False
        try:
            study = json.loads(data)
        except (UnicodeError, json.JSONDecodeError):
            return False
        checks = study.get('checks') if isinstance(study,dict) else None
        if not isinstance(checks,list) or not checks or len(checks)!=row.get('reference_cases'):
            return False
        for check in checks:
            if not isinstance(check,dict):
                return False
            actual, reference, tolerance = (check.get(key) for key in ('actual','reference','absolute_tolerance'))
            if not all(type(value) in (int,float) and isfinite(value) for value in (actual,reference,tolerance)):
                return False
            if abs(actual-reference)>tolerance:
                return False
    return True


def _quantity(number, *, minimum=0, maximum=float('inf')):
    return type(number) in (float, int) and minimum < number < maximum


def _deadline(number, limit):
    return type(number) in (float, int) and 0 <= number <= limit


def _profile_valid(row, scale):
    return (row.get('verified') is True and row.get('scale') == scale and _quantity(row.get('seconds'))
            and _quantity(row.get('peak_rss_bytes')) and _quantity(row.get('work_estimate_bytes')))


def resource_checks(report, candidate):
    profiles = report.get('profiles', [])
    cancellation = report.get('cancellation', {})
    desktop = report.get('desktop', {})
    persistence = report.get('persistence', {})
    return {
        'statistical_profiles': _belongs_to(report, candidate)
        and report.get('threads') == 1
        and tuple(row.get('profile') for row in profiles) == RESOURCE_PROFILES
        and all(_profile_valid(row,2) and _profile_valid(row.get('reference_scale',{}),1) for row in profiles),
        'statistical_cancellation': _belongs_to(report, candidate) and all(
            cancellation.get(name, {}).get('discarded') is True
            and _deadline(cancellation[name].get('seconds_after_request'), 1.5)
            for name in ('numeric', 'campaign', 'persistence')
        ),
        'statistical_responsiveness': _belongs_to(report, candidate)
        and desktop.get('passed') is True and desktop.get('qt_platform') == 'offscreen'
        and _quantity(desktop.get('heartbeat_count'), minimum=1)
        and _quantity(desktop.get('maximum_gap_seconds')) and _deadline(desktop['maximum_gap_seconds'], 2),
        'statistical_persistence': _belongs_to(report, candidate) and all(
            persistence.get(key) is True for key in (
                'previous_file_preserved', 'campaign_resumed', 'corruption_rejected',
                'competing_request_rejected', 'retry_verified',
            )
        ),
    }


def native_lock_coverage(measurements):
    """Unite native Windows and POSIX paths over the full, identical source denominator."""
    keys = (('lines','num_statements','covered_lines'), ('branches','num_branches','covered_branches'))
    missing = within_threshold({}, 90, 85)
    if set(measurements) != set(PLATFORMS) or not all(measurements.values()):
        return missing
    totals = {}
    for kind,size_key,hit_key in keys:
        universes, combined = [], set()
        for row in measurements.values():
            def entries(name):
                values = row.get(name + '_' + kind, ())
                return set(values) if kind == 'lines' else {tuple(arc) for arc in values}

            executed, uncovered = entries('executed'), entries('missing')
            universe = executed | uncovered
            summary = row.get('summary', {})
            if (not executed or executed & uncovered or len(universe) != summary.get(size_key)
                    or len(executed) != summary.get(hit_key)):
                return missing
            universes.append(universe)
            combined.update(executed)
        if any(universe != universes[0] for universe in universes):
            return missing
        totals.update({size_key:len(universes[0]),hit_key:len(combined)})
    return within_threshold(totals,90,85)


def evaluate(folder, candidate, version):
    if not phase_five_version(version):
        raise ValueError('Fase 05 requiere una versión Preview 2.3.x.')
    if not isinstance(candidate, str) or not re.fullmatch(r'[0-9a-f]{40}', candidate):
        raise ValueError('Indicá el SHA completo del candidato.')
    previous = evaluate_channels(folder, candidate, version)
    platforms, native_coverage = {}, {}
    for platform in PLATFORMS:
        directories = sorted(path for path in folder.glob('engineering-*') if path.is_dir()
                             and f'-{platform}-' in path.name)
        base = previous['platforms'][platform]
        coverage = read(directories, 'coverage.json') or {}
        modules = {name.replace('\\', '/').rsplit('/', 1)[-1]: row
                   for name, row in coverage.get('files', {}).items()}
        critical = {name: within_threshold(modules.get(name, {}).get('summary', {}), 90, 85) for name in CRITICAL}
        native_coverage[platform] = modules.get(NATIVE_LOCK_MODULE)
        integral = read(directories, 'integral-checks.json') or {}
        passed = {row['id'] for row in integral.get('records', []) if row.get('passed') is True}
        packaged = read(directories, 'packaged-smoke.json') or {}
        science = read(directories, 'statistical-qualification.json') or {}
        resources = read(directories, 'statistical-performance.json') or {}
        checks = {
            'phase_04_controls': all(base['checks'].values()),
            'critical_coverage': all(cell['state'] == 'pass'
                                     for name,group in critical.items() if name != NATIVE_LOCK_MODULE
                                     for cell in group.values()),
            'statistical_unit_and_desktop_suite': all(
                any(test.startswith(prefix) for test in passed)
                for prefix in ('test_probability.', 'test_probability_desktop.', 'test_descriptive_statistics.',
                               'test_statistical_inference.', 'test_stochastic_processes.', 'test_stochastic_noise.',
                               'test_stochastic_covariance.', 'test_ar_estimation.', 'test_time_series_identification.',
                               'test_arma_desktop.', 'test_statistical_spectra.', 'test_optimal_estimation.',
                               'test_estimation_desktop.', 'test_kalman_filter.', 'test_adaptive_filter.',
                               'test_monte_carlo.', 'test_monte_carlo_desktop.')
            ),
            'native_campaign_lock': ('test_monte_carlo.MonteCarloTests.'
                                     'test_native_campaign_writer_excludes_a_separate_process_and_retries') in passed,
            'packaged_probability': packaged.get('executable_check', {}).get('checks', {}).get(
                'packaged_probability_and_project') is True,
            'statistical_evidence_integrity': science_artifacts(directories, science),
            'statistical_resource_platform': str(resources.get('platform','')).startswith(PLATFORMS[platform]),
            **science_checks(science, candidate),
            **resource_checks(resources, candidate),
        }
        platforms[platform] = {'checks': checks, 'critical': critical,
                               'candidate_bundle': base['historical']['candidate_bundle'],
                               'phase_04': base, 'science': science, 'resource_profiles': resources}
    lock_coverage = native_lock_coverage(native_coverage)
    passed = (previous['automated_passed'] and all(all(entry['checks'].values()) for entry in platforms.values())
              and all(cell['state'] == 'pass' for cell in lock_coverage.values()))
    return {'phase': '05', 'version': version, 'commit': candidate, 'automated_passed': passed,
            'platforms': platforms, 'combined_native_coverage': {NATIVE_LOCK_MODULE:lock_coverage}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--version', required=True)
    args = parser.parse_args()
    report = evaluate(args.input, args.candidate, args.version)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'quality-gate-05.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    lines = ['# Quality Gate automatizado de Fase 05', '', f"SHA `{args.candidate}` · {args.version} Preview", '',
             '| Plataforma | Control | Estado |', '| --- | --- | --- |']
    for platform, entry in report['platforms'].items():
        lines.extend(f"| {platform} | {key} | {'Aprobado' if status else 'Pendiente'} |"
                     for key, status in entry['checks'].items())
    for name, metrics in report['combined_native_coverage'].items():
        for metric, result in metrics.items():
            reading = f"{result['covered']}/{result['total']} (objetivo {result['goal']} %)"
            lines.append(f"| Windows y Linux | {name} · {metric} {reading} | {result['state']} |")
    (args.output / 'quality-gate-05.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('Quality Gate automatizado de Fase 05', 'PASS' if report['automated_passed'] else 'PENDIENTE')
    return 0 if report['automated_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
