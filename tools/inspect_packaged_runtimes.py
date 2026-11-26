"""Inventory the actual libraries in SignalLab PyInstaller portables without executing them."""

import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tarfile
from tempfile import TemporaryDirectory

from PyInstaller.archive.readers import CArchiveReader


PINNED_QT_VERSION = '6.12.1'


def require_pinned_qt():
    from PySide6 import __version__ as pyside_version
    from PySide6.QtCore import qVersion
    from shiboken6 import __version__ as shiboken_version

    versions = qVersion(), pyside_version, shiboken_version
    if any(version != PINNED_QT_VERSION for version in versions):
        raise SystemExit(f'Se requiere Qt, PySide6 y shiboken6 {PINNED_QT_VERSION}. '
                         f'El entorno contiene {", ".join(versions)}. Instalá requirements-lock.txt.')
    return PINNED_QT_VERSION


def inspect_binary(path):
    archive = CArchiveReader(str(path))
    native = {}
    runtime = {}
    for entry, record in archive.toc.items():
        if record[-1] not in ('b', 'n'):
            continue
        name = PurePosixPath(entry.replace('\\', '/')).name
        native[entry] = record[2]
        if record[-1] != 'b':
            continue
        if re.fullmatch(r'python3\d+\.dll|libpython3\.\d+\.so(?:\.\d+)*', name):
            data = archive.extract(entry)
            versions = set(re.findall(rb'(?<![.\d])(3\.\d+\.\d+)\x00', data))
            if len(versions) != 1:
                raise ValueError(f'No se pudo identificar una versión única de CPython en {entry}.')
            runtime['python'] = {'file': entry, 'version': versions.pop().decode()}
        elif re.fullmatch(r'(?:lib)?Qt6Core(?:\.dll|\.so(?:\.\d+)*)', name):
            data = archive.extract(entry)
            version = re.search(rb'Qt (6\.\d+\.\d+) \(', data)
            if not version:
                raise ValueError(f'No se pudo identificar la versión de QtCore en {entry}.')
            runtime['qt'] = {'file': entry, 'version': version[1].decode()}
        elif re.fullmatch(r'(?:lib)?Qt6Svg(?:\.dll|\.so(?:\.\d+)*)', name):
            runtime['qt_svg'] = {'file': entry}
    if not {'python', 'qt'} <= runtime.keys():
        raise ValueError('El portable no contiene referencias identificables de CPython y Qt.')
    return {'runtime': runtime, 'native_members_uncompressed_bytes': native}


@contextmanager
def portable_executable(path):
    if path.name.endswith('.tar.gz'):
        with TemporaryDirectory(prefix='signallab-linux-package-') as folder:
            binary = Path(folder)/'SignalLab-PC'
            with tarfile.open(path, 'r:gz') as archive:
                members = [item for item in archive.getmembers()
                           if item.isfile() and PurePosixPath(item.name).name == binary.name]
                if len(members) != 1 or not 0 < members[0].size < 2*1024**3:
                    raise ValueError('Se esperaba un único binario portable de Linux.')
                with archive.extractfile(members[0]) as source, binary.open('wb') as target:
                    shutil.copyfileobj(source, target, 4*1024**2)
            yield binary
    else:
        yield path


def inspect_portable(path):
    with portable_executable(path) as binary:
        result = inspect_binary(binary)
    with path.open('rb') as stream:
        checksum = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'filename': path.name, 'sha256': checksum, **result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('portables', type=Path, nargs='+')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    inventories = [inspect_portable(portable) for portable in args.portables]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(inventories, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    for row in inventories:
        print(row['filename'], row['runtime'], len(row['native_members_uncompressed_bytes']))


if __name__ == '__main__':
    main()
