"""Build and check a disposable portable without retaining the executable."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from inspect_packaged_runtimes import PINNED_QT_VERSION, inspect_portable, require_pinned_qt
from check_python_runtime import require_pinned_python
from build_pillow_runtime import prepare_pillow


ROOT = Path(__file__).resolve().parents[1]


def main():
    expected_python = require_pinned_python()
    require_pinned_qt()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    prepare_pillow()
    with TemporaryDirectory(prefix='signallab-package-') as directory:
        temp = Path(directory)
        subprocess.run(
            [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onefile', '--noupx',
             '--name', 'SignalLab-PC', '--distpath', str(temp), '--workpath', str(temp/'work'),
             '--specpath', str(temp), '--add-data', f"{ROOT/'signallab_pc/assets'}:signallab_pc/assets",
             str(ROOT/'main.py')],
            cwd=ROOT, check=True, timeout=900)
        binary = temp/('SignalLab-PC.exe' if os.name == 'nt' else 'SignalLab-PC')
        env = os.environ | {'QT_QPA_PLATFORM': 'offscreen', 'OPENBLAS_NUM_THREADS': '1',
                            'OMP_NUM_THREADS': '1', 'MPLCONFIGDIR': str(temp/'matplotlib')}
        report = temp/'self-check.json'
        check = subprocess.run([str(binary), '--self-check', str(report)],
                               cwd=temp, env=env, timeout=180)
        inventory = inspect_portable(binary)
        diagnostics = json.loads(report.read_text(encoding='utf-8')) if report.exists() else {}
        args.output.write_text(json.dumps({'executable_check': diagnostics, 'runtime': inventory['runtime'],
                                          'sha256': inventory['sha256']}, indent=2)+'\n', encoding='utf-8')
        return int(check.returncode != 0 or not diagnostics.get('ok') or not diagnostics.get('frozen')
                   or not diagnostics.get('checks') or not all(diagnostics['checks'].values())
                   or inventory['runtime']['python']['version'] != expected_python
                   or diagnostics.get('runtime', {}).get('python') != expected_python
                   or diagnostics.get('runtime', {}).get('pillow_jpeg2000') is not False
                   or inventory['runtime']['qt']['version'] != PINNED_QT_VERSION
                   or 'qt_svg' not in inventory['runtime'])


if __name__ == '__main__':
    raise SystemExit(main())
