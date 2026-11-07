"""Build per-user installers from verified, updater-capable portable builds."""
from pathlib import Path, PurePosixPath
import argparse
import gzip
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools')]
from distribution_receipt import verify_receipt, source_fingerprint
from signallab_pc import __version__
from signallab_pc.installations import MARKER, receipt
from signallab_pc.update_download import file_hash
from signallab_pc.update_manifest import version_tuple


def extract_linux(archive, destination):
    prefix = f'SignalLab-PC-{__version__}-linux-x86_64'
    count = total = 0
    with tarfile.open(archive, 'r:gz') as source:
        for member in source:
            parts = PurePosixPath(member.name).parts
            if not parts or parts[0] != prefix or '..' in parts or '\\' in member.name or PurePosixPath(member.name).is_absolute() or any(':' in p or any(ord(c) < 32 for c in p) for p in parts):
                raise ValueError('Unexpected Linux portable member.')
            if member.isdir():
                continue
            if not member.isfile() or len(parts) < 2:
                raise ValueError('Links and special files are not accepted in installer payloads.')
            count += 1; total += member.size
            if count > 10000 or total > 2 * 1024**3:
                raise ValueError('Portable payload is too large.')
            target = destination.joinpath(*parts[1:]); target.parent.mkdir(parents=True, exist_ok=True)
            with source.extractfile(member) as stream, target.open('xb') as out:
                shutil.copyfileobj(stream, out)
    return destination


def windows(binary, compiler, output, folder):
    if sys.platform != 'win32':
        raise ValueError('Build the Windows installer on Windows.')
    record = json.loads((ROOT / 'outputs/portable-build-windows.json').read_text(encoding='utf-8'))
    verify_receipt(record, binary, 'windows-x86_64')
    shutil.copyfile(binary, folder / 'SignalLab-PC.exe')
    for name in ('LICENSE', 'NOTICE.md', 'THIRD_PARTY_NOTICES.md'):
        shutil.copyfile(ROOT / name, folder / name)
    shutil.copytree(ROOT / 'LICENSES', folder / 'LICENSES')
    (folder / MARKER).write_text(json.dumps(receipt(__version__, 'windows-x86_64', 'windows-user-v1')), encoding='utf-8')
    subprocess.run([str(compiler), '/DAppVersion=' + __version__, '/DPayloadDir=' + str(folder),
                    '/DOutputDir=' + str(output), str(ROOT / 'packaging/windows-installer.iss')], check=True)
    return output / f'SignalLab-PC-{__version__}-setup.exe'


def linux(archive, output, folder):
    if sys.platform != 'linux':
        raise ValueError('Build the Linux installer on Linux.')
    extract_linux(archive, folder)
    record = json.loads((folder / 'build-provenance.json').read_text(encoding='utf-8'))
    verify_receipt(record, folder / 'SignalLab-PC', 'linux-x86_64')
    shutil.copyfile(ROOT / 'signallab_pc/assets/signallab.svg', folder / 'signallab.svg')
    destination = output / f'SignalLab-PC-{__version__}-linux-x86_64.run'
    temporary = output / (destination.name + '.partial')
    try:
        with temporary.open('wb') as target:
            target.write((ROOT / 'packaging/linux-installer-header.sh').read_bytes().replace(b'\r\n', b'\n'))
            with gzip.GzipFile(fileobj=target, mode='wb', mtime=0) as compressed:
                with tarfile.open(fileobj=compressed, mode='w|') as package:
                    for path in sorted(folder.rglob('*')):
                        if path.is_file():
                            package.add(path, arcname=path.relative_to(folder).as_posix(), recursive=False)
        temporary.chmod(0o755); temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('platform', choices=['windows', 'linux'])
    parser.add_argument('--binary', type=Path)
    parser.add_argument('--archive', type=Path)
    parser.add_argument('--iscc', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs')
    args = parser.parse_args(); version_tuple(__version__)
    args.output.mkdir(parents=True, exist_ok=True)
    work = ROOT / 'work'; work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='installer-', dir=work) as temporary:
        folder = Path(temporary)
        if args.platform == 'windows':
            compiler = args.iscc or Path(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')) / 'Inno Setup 6/ISCC.exe'
            if not compiler.is_file():
                raise SystemExit('Falta Inno Setup 6. Indicá --iscc o usá el flujo oficial de GitHub.')
            result = windows(args.binary or ROOT / f'outputs/SignalLab-PC-{__version__}.exe', compiler, args.output, folder)
        else:
            result = linux(args.archive or ROOT / f'outputs/SignalLab-PC-{__version__}-linux-x86_64.tar.gz', args.output, folder)
    proof = dict(version=__version__, filename=result.name, sha256=file_hash(result),
                 size=result.stat().st_size, platform=args.platform, source_fingerprint=source_fingerprint(),
                 source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                 windows_authenticode_signed=False if args.platform == 'windows' else None)
    (args.output / ('installer-' + args.platform + '.json')).write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
    print('Generated:', result)


if __name__ == '__main__':
    main()
