"""Offline Ed25519 key creation and signing of installer manifests; never print secrets."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import argparse
import base64
import json
import os
import sys
import subprocess
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from signallab_pc.update_download import file_hash
from signallab_pc.update_manifest import FILENAMES, REPOSITORY, public_key, verify_manifest, version_tuple
from signallab_pc import __version__ as APP_VERSION


def generate(private_path, public_path):
    if private_path.exists() or public_path.exists():
        raise ValueError('Las claves ya existen. No se reemplazan automáticamente: las instalaciones publicadas dependen de esa identidad.')
    private = Ed25519PrivateKey.generate()
    private_path.parent.mkdir(parents=True, exist_ok=True)
    if os.name == 'posix':
        private_path.parent.chmod(0o700)
    data = private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    descriptor = os.open(private_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'wb') as target:
        target.write(data)
    public_path.parent.mkdir(parents=True, exist_ok=True)
    record = dict(algorithm='Ed25519', public_key=base64.b64encode(private.public_key().public_bytes_raw()).decode())
    with public_path.open('x', encoding='utf-8') as target:
        target.write(json.dumps(record, indent=2) + '\n')
    print('Clave de actualización creada. Conservá la clave privada fuera del repositorio.')


def sign(version, paths, key_bytes, notes, days=90, now=None):
    version_tuple(version)
    if not 1 <= days <= 366:
        raise ValueError('La vigencia debe estar entre 1 y 366 días.')
    private = serialization.load_pem_private_key(key_bytes, password=None)
    if not isinstance(private, Ed25519PrivateKey) or private.public_key().public_bytes_raw() != public_key():
        raise ValueError('La clave privada no corresponde a la clave pública de esta aplicación.')
    if version != APP_VERSION:
        raise ValueError('La versión a firmar no corresponde al código de origen actual.')
    from tools.distribution_receipt import source_fingerprint
    fingerprint = source_fingerprint()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    now = now or datetime.now(timezone.utc)
    assets = {}
    for tag, template in FILENAMES.items():
        name = template.format(version=version)
        matches = [p for p in paths if p.name == name]
        if len(matches) != 1:
            raise ValueError('Hace falta exactamente un instalador para ' + tag + ': ' + name)
        path = matches[0]
        proof = json.loads((path.parent / ('installer-' + tag.split('-')[0] + '.json')).read_text(encoding='utf-8'))
        digest = file_hash(path)
        if (proof.get('version') != version or proof.get('filename') != name or proof.get('sha256') != digest
                or proof.get('size') != path.stat().st_size or proof.get('source_fingerprint') != fingerprint
                or proof.get('source_commit') != commit):
            raise ValueError('El instalador no coincide con la prueba de construcción del código actual: ' + name)
        assets[tag] = dict(name=name, url=f'https://github.com/{REPOSITORY}/releases/download/v{version}/{name}',
                           sha256=digest, size=path.stat().st_size)
    if len(paths) != len(assets):
        raise ValueError('Se indicaron adjuntos que no corresponden a los instaladores.')
    payload = dict(schema=1, channel='stable', version=version, published_at=now.isoformat().replace('+00:00', 'Z'),
                   expires_at=(now + timedelta(days=days)).isoformat().replace('+00:00', 'Z'), notes=notes, assets=assets)
    raw = json.dumps(payload, ensure_ascii=False, separators=(',', ':'), sort_keys=True).encode()
    envelope = json.dumps(dict(payload=base64.b64encode(raw).decode(), signature=base64.b64encode(private.sign(raw)).decode()), indent=2).encode()
    verify_manifest(envelope, now=now)
    return envelope


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    create = sub.add_parser('generate')
    create.add_argument('--private-key', type=Path, required=True)
    create.add_argument('--public-key', type=Path, default=ROOT / 'signallab_pc/assets/update-public-key.json')
    release = sub.add_parser('sign')
    release.add_argument('--version', required=True)
    release.add_argument('--installer', action='append', type=Path, required=True)
    release.add_argument('--notes', type=Path, required=True)
    release.add_argument('--private-key', type=Path, required=True)
    release.add_argument('--days', type=int, default=90)
    release.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.action == 'generate':
        generate(args.private_key, args.public_key); return
    if subprocess.run(['git','diff','--quiet','HEAD','--'],cwd=ROOT).returncode:
        raise SystemExit('Guardá los cambios del código antes de firmar una entrega.')
    key_bytes = args.private_key.read_bytes()
    data = sign(args.version, args.installer, key_bytes, args.notes.read_text(encoding='utf-8'), args.days)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    print('Manifiesto firmado y verificado:', args.output)


if __name__ == '__main__':
    main()
