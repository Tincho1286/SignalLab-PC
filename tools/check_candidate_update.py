"""Transport a real candidate installer through the updater with a disposable key."""

import argparse
import base64
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from signallab_pc import __release_channel__, __version__
from signallab_pc.update_download import download, file_hash
from signallab_pc.update_manifest import FILENAMES, REPOSITORY, UpdateError, verify_manifest


class FileResponse:
    def __init__(self, path, url):
        self.path = path
        self.url = url
        self.headers = {'Content-Length': str(path.stat().st_size)}

    def geturl(self):
        return self.url

    def __enter__(self):
        self.stream = self.path.open('rb')
        return self

    def __exit__(self, *error):
        self.stream.close()

    def read(self, size):
        return self.stream.read(size)


def envelope(value, key):
    payload = json.dumps(value).encode()
    return json.dumps({'payload': base64.b64encode(payload).decode(),
                       'signature': base64.b64encode(key.sign(payload)).decode()}).encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('installer', type=Path)
    parser.add_argument('--iscc', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--from-stable', action='store_true')
    args = parser.parse_args()
    windows = sys.platform == 'win32'
    target = 'windows-x86_64' if windows else 'linux-x86_64'
    name = FILENAMES[target].format(version=__version__)
    if args.installer.name != name or windows and args.iscc is None:
        raise ValueError('Se requiere el instalador nativo del candidato y su compilador en Windows.')
    now = datetime.now(timezone.utc).replace(microsecond=0)
    url = f'https://github.com/{REPOSITORY}/releases/download/v{__version__}/{name}'
    checksum = file_hash(args.installer)
    channel = __release_channel__
    payload = dict(schema=1, channel=channel, version=__version__,
                   published_at=now.isoformat().replace('+00:00','Z'),
                   expires_at=(now+timedelta(days=1)).isoformat().replace('+00:00','Z'),
                   notes='Instalador descartable del candidato', assets={target:dict(
                       name=name, url=url, sha256=checksum, size=args.installer.stat().st_size)})
    key = Ed25519PrivateKey.generate()
    signed = envelope(payload,key)
    try:
        verify_manifest(signed, expected_channel=channel, expected_version=__version__, now=now)
    except UpdateError:
        pass
    else:
        raise ValueError('La clave de producción no debe aceptar la firma de prueba.')
    public = key.public_key().public_bytes_raw()
    source = verify_manifest(signed, key=public, expected_channel=channel, expected_version=__version__, now=now)
    isolated_channel = 'stable' if channel == 'preview' else 'preview'
    try:
        verify_manifest(signed, key=public, expected_channel=isolated_channel, now=now)
    except UpdateError:
        pass
    else:
        raise ValueError('El manifiesto de prueba no puede cruzar entre Stable/LTS y Preview.')
    if source.newer_than(__version__) or not source.newer_than('0.0.1'):
        raise ValueError('El actualizador no interpretó correctamente la versión.')
    with TemporaryDirectory(prefix='signallab-update-audit-') as folder:
        path = download(source.assets[target], Path(folder),
                        opener=lambda address: FileResponse(args.installer,address))
        if file_hash(path) != checksum:
            raise ValueError('El instalador entregado al comprobador debe coincidir byte por byte.')
        if windows:
            check = ['tools/check_windows_installer.py', '--iscc', str(args.iscc),
                     '--installer', str(path)]
        else:
            check = ['tools/check_linux_installer.py', str(path)]
        subprocess.run([sys.executable,'-B','-X','utf8',*check], cwd=ROOT, check=True, timeout=900)
        upgrade = None
        if args.from_stable:
            from check_stable_upgrade import verify_upgrade
            if not source.newer_than('2.0.0'):
                raise RuntimeError('El salto aislado necesita un candidato posterior a la estable 2.0.0.')
            upgrade = verify_upgrade(path, source.assets[target], folder)
    proof = json.loads((ROOT/'work'/('installer-contract-windows.json' if windows
                                   else 'installer-contract-linux.json')).read_text())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(dict(platform=target, sha256=checksum,
        temporary_signature_verified=True, production_key_rejected_test_signature=True,
        channel=channel, other_channel_rejected=True, download_verified=True,
        native_installation=proof, upgrade_from_stable=upgrade), indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
