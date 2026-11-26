"""Record both kinds of distribution artifact without publishing a release."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.distribution_receipt import source_fingerprint
from signallab_pc import __release_channel__, __version__
from signallab_pc.release_policy import publication_version
from signallab_pc.update_download import file_hash
from signallab_pc.update_manifest import FILENAMES


def artifact_names(version, platform):
    files = {
        'windows': (f'SignalLab-PC-{version}.exe', FILENAMES['windows-x86_64'].format(version=version)),
        'linux': (f'SignalLab-PC-{version}-linux-x86_64.tar.gz', FILENAMES['linux-x86_64'].format(version=version)),
    }
    return files[platform]


def record(outputs, platform, destination, *, source_archive=False):
    publication_version(__version__, __release_channel__)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip()
    if dirty:
        raise ValueError('La preparación requiere un árbol limpio.')
    receipt_file = outputs/f'installer-{platform}.json'
    installer_receipt = json.loads(receipt_file.read_text(encoding='utf-8'))
    source = source_fingerprint()
    portable, installer = artifact_names(__version__, platform)
    if (installer_receipt.get('source_commit') != commit or installer_receipt.get('source_fingerprint') != source
            or installer_receipt.get('version') != __version__ or installer_receipt.get('filename') != installer):
        raise ValueError('El comprobante del instalador no corresponde al candidato.')
    names = [portable, installer, receipt_file.name]
    if source_archive:
        source_name = f'SignalLab-PC-{__version__}-source.zip'
        subprocess.run(['git', 'archive', '--format=zip', f'--prefix=SignalLab-PC-{__version__}/',
                        '-o', str((outputs/source_name).resolve()), commit], cwd=ROOT, check=True)
        names.append(source_name)
    files = {name: {'sha256': file_hash(outputs/name), 'size': (outputs/name).stat().st_size}
             for name in names}
    if (files[installer]['sha256'] != installer_receipt.get('sha256')
            or files[installer]['size'] != installer_receipt.get('size')):
        raise ValueError('El instalador cambió desde su construcción.')
    document = {
        'schema': 1, 'commit': commit, 'version': __version__, 'channel': __release_channel__,
        'source_fingerprint': source, 'platform': platform, 'files': files,
        'installer_sha256': files[installer]['sha256'], 'portable_sha256': files[portable]['sha256'],
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(document, indent=2)+'\n'
    destination.write_text(payload, encoding='utf-8')
    (outputs/f'candidate-{platform}.json').write_text(payload, encoding='utf-8')
    return document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform', choices=('windows', 'linux'), required=True)
    parser.add_argument('--outputs', type=Path, default=ROOT/'outputs')
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--source-archive', action='store_true')
    args = parser.parse_args()
    report = record(args.outputs, args.platform, args.report, source_archive=args.source_archive)
    print('Prepared', report['platform'], report['version'], report['commit'])


if __name__ == '__main__':
    main()
