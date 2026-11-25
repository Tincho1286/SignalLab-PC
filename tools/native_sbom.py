"""Inventory the native files of a disposable build and attribute by exact bytes."""

import argparse
from collections import defaultdict
import hashlib
from importlib.metadata import distributions
import json
from pathlib import Path, PurePosixPath
import platform
import subprocess
import sys
import sysconfig

from PyInstaller.archive.readers import CArchiveReader

from inspect_packaged_runtimes import inspect_binary, portable_executable


OPENSSL = {'libssl.so.3', 'libcrypto.so.3'}
UBUNTU_OPENSSL_MINIMUM = '3.0.2-0ubuntu1.30'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def candidates(names):
    by_path = {}
    for dist in distributions():
        for file in dist.files or ():
            path = Path(dist.locate_file(file))
            if path.name.casefold() in names:
                by_path.setdefault(path, ('PyPI', dist.metadata['Name'], dist.version))
    python_dirs = (Path(sysconfig.get_path('platstdlib'))/'lib-dynload',
                   Path(sys.base_prefix)/'DLLs', Path(sys.base_prefix))
    if sysconfig.get_config_var('LIBDIR'):
        python_dirs += (Path(sysconfig.get_config_var('LIBDIR')),)
    for directory in python_dirs:
        for name in names:
            path = directory/name
            if path.is_file():
                by_path.setdefault(path, ('CPython', 'CPython', platform.python_version()))
    if sys.platform == 'linux':
        for package in sorted(Path('/var/lib/dpkg/info').glob('*.list')):
            paths = [Path(line) for line in package.read_text(errors='replace').splitlines()
                     if line.startswith('/') and Path(line).name.casefold() in names]
            if not paths:
                continue
            query = ['dpkg-query', '-W', '-f=${Package}\t${Version}\t${Architecture}', package.stem]
            name, version, architecture = subprocess.check_output(query, text=True).split('\t')
            for path in paths:
                if path.is_file():
                    by_path.setdefault(path, ('Ubuntu', f'{name}:{architecture}', version))
    index = defaultdict(list)
    for path, (source, name, version) in by_path.items():
        if path.is_file():
            match = dict(source=source, package=name, version=version)
            bucket = index[digest(path)]
            if match not in bucket:
                bucket.append(match)
    return index


def pe_version(data):
    if sys.platform != 'win32':
        return None
    import pefile
    try:
        pe = pefile.PE(data=data, fast_load=True)
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE']])
        for version in getattr(pe, 'VS_FIXEDFILEINFO', ()):
            words = (version.FileVersionMS, version.FileVersionLS)
            numbers = [str(part) for word in words for part in (word >> 16, word & 0xffff)]
            return '.'.join(numbers) if any(part!='0' for part in numbers) else None
    except pefile.PEFormatError:
        return None
    return None


def inspect(path):
    with portable_executable(path) as executable:
        archive = CArchiveReader(str(executable))
        runtime = inspect_binary(executable)['runtime']
        hashes, versions, links = {}, {}, {}
        for member, entry in archive.toc.items():
            if entry[-1] == 'n':
                links[member] = archive.extract(member).decode('utf-8').rstrip('\0')
            elif entry[-1] == 'b':
                data = archive.extract(member)
                if data.startswith((b'MZ', b'\x7fELF')):
                    hashes[member] = hashlib.sha256(data).hexdigest()
                    if version := pe_version(data):
                        versions[member] = version
        binary_sha = digest(executable)
    names = {PurePosixPath(member.replace('\\', '/')).name.casefold() for member in hashes}
    owners = candidates(names)
    entries = []
    for member, checksum in sorted(hashes.items()):
        row = dict(path=member, sha256=checksum, sources=owners.get(checksum, []))
        if member in versions:
            row['embedded_version'] = versions[member]
        entries.append(row)
    return dict(artifact=path.name, artifact_sha256=digest(path), executable_sha256=binary_sha,
                runtime=runtime, native_files=entries, symbolic_links=links, platform=platform.platform())


def cyclonedx(inventory, source):
    files = []
    for entry in inventory['native_files']:
        component = {'type': 'file', 'name': entry['path'],
                     'hashes': [{'alg': 'SHA-256', 'content': entry['sha256']}]}
        matches = entry['sources']
        if entry.get('embedded_version'):
            component['version'] = entry['embedded_version']
        elif len(matches)==1:
            component['version'] = matches[0]['version']
        properties = [
            {'name':'signallab:byte-identical-origin',
             'value':f"{match['source']}:{match['package']}@{match['version']}"}
            for match in matches
        ]
        component['properties'] = properties or [{'name':'signallab:attribution','value':'unconfirmed'}]
        files.append(component)
    return {
        'bomFormat':'CycloneDX', 'specVersion':'1.6', 'version':1,
        'metadata':{
            'component':{'type':'application','name':'SignalLab PC','bom-ref':'signallab-pc',
                         'hashes':[{'alg':'SHA-256','content':inventory['artifact_sha256']}]},
            'properties':[{'name':'signallab:source-commit','value':source},
                          {'name':'signallab:artifact','value':inventory['artifact']}],
        },
        'components':files,
    }


def verify_linux_tls(entries):
    missing = OPENSSL.copy()
    for item in entries:
        filename = PurePosixPath(item['path']).name
        if filename not in OPENSSL:
            continue
        ubuntu = [match['version'] for match in item['sources']
                  if match['source']=='Ubuntu' and match['package']=='libssl3:amd64']
        if len(ubuntu)!=1 or subprocess.run(
                ['dpkg', '--compare-versions', ubuntu[0], 'ge', UBUNTU_OPENSSL_MINIMUM]).returncode:
            raise SystemExit(f'No se pudo acreditar la revisión corregida de {filename} de Ubuntu.')
        missing.discard(filename)
        print('TLS:', filename, ubuntu[0], item['sha256'], flush=True)
    if missing:
        raise SystemExit('Faltan archivos de OpenSSL en el inventario.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifact', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    inventory = inspect(args.artifact)
    inventory['source_commit'] = source
    args.output.mkdir(parents=True, exist_ok=True)
    for name, data in (('native-inventory.json', inventory), ('native.cdx.json', cyclonedx(inventory, source))):
        (args.output/name).write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')
    print('Native files:', len(inventory['native_files']), flush=True)
    if sys.platform == 'linux':
        verify_linux_tls(inventory['native_files'])


if __name__ == '__main__':
    main()
