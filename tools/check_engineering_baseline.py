"""Run the engineering baseline on one clean Git revision and retain its evidence."""

import argparse
from collections import deque
from importlib.metadata import distributions, version
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch
from check_python_runtime import require_pinned_python


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
            return main(['--verbose', '--report', str(output/'integral-checks.json')])


def run_stage(output, name, env, *arguments):
    print(name, flush=True)
    log_path = output/(name+'.log')
    with log_path.open('wb') as log:
        result = subprocess.run([sys.executable, '-B', '-X', 'utf8', *arguments], cwd=ROOT,
                                env=env, stdout=log, stderr=subprocess.STDOUT)
    print(f'{name}: {result.returncode}', flush=True)
    if result.returncode:
        with log_path.open(encoding='utf-8', errors='replace') as log:
            print(''.join(deque(log, maxlen=45)), end='', flush=True)
    return result.returncode


def coverage_parts(output):
    from coverage import CoverageData
    from inspect import getsourcelines
    from signallab_pc.symbolic_process import worker

    source_lines, first_line = getsourcelines(worker)
    worker_lines = set(range(first_line+1, first_line+len(source_lines)))
    parts = list(output.glob('.coverage.*'))
    instrumented = 0
    for path in parts:
        part = CoverageData(basename=str(path))
        part.read()
        for name in part.measured_files():
            if Path(name).name == 'symbolic_process.py' and worker_lines.intersection(part.lines(name) or []):
                instrumented += 1
                break
    return {'data_files_before_combine': len(parts), 'data_files_executing_symbolic_worker': instrumented}


def run(output):
    require_pinned_python()
    revision = clean_revision()
    output.mkdir(parents=True, exist_ok=False)
    env = os.environ | {'QT_QPA_PLATFORM': 'offscreen', 'OPENBLAS_NUM_THREADS': '1',
                        'OMP_NUM_THREADS': '1', 'PYTHONDONTWRITEBYTECODE': '1',
                        'PYTHONFAULTHANDLER': '1',
                        'MPLCONFIGDIR': str(output/'matplotlib'),
                        'COVERAGE_RCFILE': str(ROOT/'tools/engineering.coveragerc'),
                        'COVERAGE_FILE': str(output/'.coverage')}
    stages = {
        'static': run_stage(output, 'static', env, 'tools/check_static.py'),
        'integral': run_stage(output, 'integral', env, '-m', 'coverage', 'run',
                              'tools/check_engineering_baseline.py', '--integral', str(output)),
    }
    sys.path.insert(0, str(ROOT))
    parts = coverage_parts(output)
    stages['coverage_combine'] = run_stage(output, 'coverage-combine', env, '-m', 'coverage', 'combine')
    stages['coverage_json'] = run_stage(output, 'coverage-json', env, '-m', 'coverage', 'json',
                                       '-o', str(output/'coverage.json'))
    line_and_branch_coverage = None
    if not stages['coverage_json']:
        data = json.loads((output/'coverage.json').read_text(encoding='utf-8'))
        selected = {'sampling.py', 'fourier.py', 'filters.py', 'model.py', 'session.py', 'symbolic_process.py',
                    'execution.py', 'dft_application.py', 'dsp_application.py', 'dsp_pipeline.py',
                    'scientific_storage.py', 'cli_session.py', 'project.py', 'operation_provenance.py'}
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
                  stages=stages, coverage=line_and_branch_coverage, coverage_parts=parts,
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
