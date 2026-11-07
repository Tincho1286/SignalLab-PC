"""Bind installer payloads to an updater-capable build of the current sources."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def source_fingerprint():
    digest = hashlib.sha256()
    paths = [p for p in (ROOT / 'signallab_pc').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc']
    paths += [ROOT / name for name in ('main.py', 'requirements-lock.txt', 'pyproject.toml', 'LICENSE', 'NOTICE.md', 'THIRD_PARTY_NOTICES.md')]
    paths += [p for p in (ROOT / 'LICENSES').rglob('*') if p.is_file()]
    for path in sorted(paths):
        raw = path.read_bytes()
        if path.suffix.lower() not in {'.ico', '.png', '.jpg', '.jpeg', '.gif', '.ttf', '.woff', '.woff2'}:
            raw = raw.replace(b'\r\n', b'\n')
        digest.update(path.relative_to(ROOT).as_posix().encode()); digest.update(b'\0'); digest.update(raw); digest.update(b'\0')
    return digest.hexdigest()


def verify_receipt(row, binary, target):
    from signallab_pc import __version__
    from signallab_pc.update_manifest import public_key
    from signallab_pc.update_download import file_hash
    import base64
    if (row.get('version') != __version__ or row.get('platform') != target
            or row.get('source_fingerprint') != source_fingerprint()
            or row.get('update_public_key') != base64.b64encode(public_key()).decode()
            or 'verified-updates-v1' not in row.get('features', [])
            or row.get('binary_sha256', row.get('sha256')) != file_hash(binary)):
        raise ValueError('El portable no corresponde a esta construcción con actualizador. Reconstruí el portable antes de generar el instalador.')


def main():
    from signallab_pc import __version__
    from signallab_pc.update_manifest import public_key
    from signallab_pc.update_download import file_hash
    import base64
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--platform', choices=['windows-x86_64', 'linux-x86_64'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    row = dict(version=__version__, platform=args.platform, sha256=file_hash(args.binary),
               features=['verified-updates-v1'], source_fingerprint=source_fingerprint(),
               update_public_key=base64.b64encode(public_key()).decode())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(row, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
