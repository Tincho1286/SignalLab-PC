"""Run the engineering baseline on one clean Git revision and retain its evidence."""

import argparse
from importlib.metadata import distributions, version
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def clean_revision():
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()

    if git('status', '--porcelain'):
        raise SystemExit('La línea base requiere un checkout limpio. Guardá los cambios antes de medir.')
    return git('rev-parse', 'HEAD')


def isolated_integral(output):
    from PySide6.QtCore import QSettings, QStandardPaths
    from check_integral import main

    writable = QStandardPaths.writableLocation
    locations = QStandardPaths.StandardLocation
    isolated = {locations.GenericCacheLocation, locations.GenericDataLocation,
                locations.AppLocalDataLocation, locations.AppConfigLocation}
    with TemporaryDirectory(prefix='signallab-profile-', dir=output) as profile:
        def scratch(location):
            return str(Path(profile)/location.name) if location in isolated else writable(location)

        QSettings.setDefaultFormat(QSettings.Format.IniFormat)
        QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, profile)
        with patch.object(QStandardPaths, 'writableLocation', side_effect=scratch):
            return main(['--report', str(output/'integral-checks.json')])


def run_stage(output, name, env, *arguments):
    print(name, flush=True)
    with (output/(name+'.log')).open('wb') as log:
        result = subprocess.run([sys.executable, '-B', '-X', 'utf8', *arguments], cwd=ROOT,
                                env=env, stdout=log, stderr=subprocess.STDOUT)
    print(f'{name}: {result.returncode}', flush=True)
    return result.returncode


def run(output):
    revision = clean_revision()
    output.mkdir(parents=True, exist_ok=False)
    env = os.environ | {'QT_QPA_PLATFORM': 'offscreen', 'OPENBLAS_NUM_THREADS': '1',
                        'OMP_NUM_THREADS': '1', 'PYTHONDONTWRITEBYTECODE': '1',
                        'MPLCONFIGDIR': str(output/'matplotlib'),
                        'COVERAGE_RCFILE': str(ROOT/'tools/engineering.coveragerc'),
                        'COVERAGE_FILE': str(output/'.coverage')}
    stages = {
        'static': run_stage(output, 'static', env, 'tools/check_static.py'),
        'integral': run_stage(output, 'integral', env, '-m', 'coverage', 'run',
                              'tools/check_engineering_baseline.py', '--integral', str(output)),
        'coverage_combine': run_stage(output, 'coverage-combine', env, '-m', 'coverage', 'combine'),
        'coverage_json': run_stage(output, 'coverage-json', env, '-m', 'coverage', 'json',
                                   '-o', str(output/'coverage.json')),
    }
    line_and_branch_coverage = None
    if not stages['coverage_json']:
        data = json.loads((output/'coverage.json').read_text(encoding='utf-8'))
        selected = {'sampling.py', 'fourier.py', 'filters.py', 'model.py', 'session.py'}
        line_and_branch_coverage = {
            'total': data['totals'],
            'modules': {Path(name).name: row['summary'] for name, row in data['files'].items()
                        if Path(name).name in selected},
        }
    fingerprint_end = clean_revision()
    report = dict(commit=revision, commit_after=fingerprint_end, os=platform.platform(),
                  machine=platform.machine(), python=platform.python_version(),
                  coverage_version=version('coverage'), profile='Qt offscreen, BLAS/OMP 1 thread',
                  packages={dist.metadata['Name']: dist.version for dist in distributions()},
                  stages=stages, coverage=line_and_branch_coverage,
                  passed=revision == fingerprint_end and all(code == 0 for code in stages.values()))
    (output/'baseline.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print('Engineering baseline:', 'PASS' if report['passed'] else 'FAIL', revision, flush=True)
    return 0 if report['passed'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    paths = parser.add_mutually_exclusive_group(required=True)
    paths.add_argument('--output', type=Path, help='New directory for the baseline reports')
    paths.add_argument('--integral', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    return isolated_integral(args.integral) if args.integral else run(args.output.resolve())


if __name__ == '__main__':
    raise SystemExit(main())
