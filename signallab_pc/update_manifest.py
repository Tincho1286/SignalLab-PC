"""Authenticated update metadata; independent of Qt, installers and networking."""
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
import base64
import binascii
import json
import re

REPOSITORY = 'Tincho1286/SignalLab-PC'
FEED_URL = f'https://github.com/{REPOSITORY}/releases/latest/download/SignalLab-updates.json'
MAX_MANIFEST = 65536
MAX_ASSET = 2 * 1024**3
FILENAMES = {'windows-x86_64': 'SignalLab-PC-{version}-setup.exe',
             'linux-x86_64': 'SignalLab-PC-{version}-linux-x86_64.run'}


class UpdateError(ValueError):
    """A failed check must never turn into an executable update."""


def version_tuple(value):
    if not isinstance(value, str) or len(value) > 20 or not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', value):
        raise UpdateError('La versión de actualización debe tener formato mayor.menor.corrección.')
    result = tuple(map(int, value.split('.')))
    if any(v > 65535 for v in result):
        raise UpdateError('La versión excede el rango admitido.')
    return result


def strict_json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise UpdateError('El manifiesto contiene campos repetidos.')
            result[key] = value
        return result
    try:
        return json.loads(data, object_pairs_hook=unique,
                          parse_constant=lambda value: (_ for _ in ()).throw(UpdateError('Número no finito en el manifiesto.')))
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise UpdateError('No se pudo leer el manifiesto de actualización.') from exc


def decode(value, length=None):
    try:
        result = base64.b64decode(value, validate=True)
    except (ValueError, TypeError, binascii.Error) as exc:
        raise UpdateError('La firma de actualización tiene un formato inválido.') from exc
    if length is not None and len(result) != length:
        raise UpdateError('Longitud de clave o firma incorrecta.')
    return result


def public_key():
    value = strict_json((Path(__file__).parent / 'assets' / 'update-public-key.json').read_bytes())
    if value.get('algorithm') != 'Ed25519':
        raise UpdateError('La clave pública de actualizaciones no está configurada.')
    return decode(value.get('public_key'), 32)


def timestamp(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z', value):
        raise UpdateError('Fecha de actualización inválida.')
    try:
        result = datetime.fromisoformat(value[:-1] + '+00:00')
    except ValueError as exc:
        raise UpdateError('Fecha de actualización inválida.') from exc
    return result


@dataclass(frozen=True)
class Asset:
    platform: str
    version: str
    name: str
    url: str
    sha256: str
    size: int


@dataclass(frozen=True)
class Release:
    version: str
    notes: str
    url: str
    assets: dict
    verified: bool = True
    channel: str = "stable"
    notices: tuple = ()

    def newer_than(self, current):
        return version_tuple(self.version) > version_tuple(current)


def verify_manifest(data, *, key=None, now=None, expected_channel='stable', expected_version=None):
    """Verify exact payload bytes with the embedded key before using any URL."""
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    if not isinstance(data, bytes) or len(data) > MAX_MANIFEST:
        raise UpdateError('El manifiesto de actualización supera el tamaño permitido.')
    envelope = strict_json(data)
    if not isinstance(envelope, dict) or set(envelope) != {'payload', 'signature'}:
        raise UpdateError('La actualización no contiene una firma verificable.')
    payload = decode(envelope['payload'])
    try:
        Ed25519PublicKey.from_public_bytes(public_key() if key is None else key).verify(decode(envelope['signature'], 64), payload)
    except (InvalidSignature, ValueError) as exc:
        raise UpdateError('La firma no corresponde a SignalLab. No se instalará esta descarga.') from exc
    value = strict_json(payload)
    if not isinstance(value, dict) or set(value) != {'schema', 'channel', 'version', 'published_at', 'expires_at', 'notes', 'assets'}:
        raise UpdateError('El formato del manifiesto no es compatible.')
    if type(value['schema']) is not int or value['schema'] != 1 or expected_channel not in ('stable','preview') or value['channel'] != expected_channel:
        raise UpdateError('El canal de actualización no es compatible.')
    version = value['version']; version_tuple(version)
    if expected_version is not None and version!=expected_version:raise UpdateError('La versión firmada no coincide con la publicación consultada.')
    published, expires = timestamp(value['published_at']), timestamp(value['expires_at'])
    now = now or datetime.now(timezone.utc)
    if published > now + timedelta(minutes=5) or expires <= now or not published < expires <= published + timedelta(days=366):
        raise UpdateError('El manifiesto está vencido o la fecha del equipo es incorrecta. Consultá la descarga oficial.')
    notes = value['notes']
    if not isinstance(notes, str) or len(notes) > 12000:
        raise UpdateError('Las notas de actualización tienen un formato inválido.')
    if not isinstance(value['assets'], dict) or not value['assets'] or set(value['assets']) - set(FILENAMES):
        raise UpdateError('Plataformas de actualización no reconocidas.')
    assets = {}
    for platform, row in value['assets'].items():
        if not isinstance(row, dict) or set(row) != {'name', 'url', 'sha256', 'size'}:
            raise UpdateError('Datos incompletos del instalador.')
        name = FILENAMES[platform].format(version=version)
        expected = f'https://github.com/{REPOSITORY}/releases/download/v{version}/{name}'
        if row['name'] != name or row['url'] != expected:
            raise UpdateError('El instalador no pertenece a la descarga oficial de esta versión.')
        if not isinstance(row['sha256'], str) or not re.fullmatch('[a-f0-9]{64}', row['sha256']):
            raise UpdateError('Checksum de actualización inválido.')
        if type(row['size']) is not int or not 1 <= row['size'] <= MAX_ASSET:
            raise UpdateError('Tamaño de instalador inválido.')
        assets[platform] = Asset(platform, version, name, expected, row['sha256'], row['size'])
    return Release(version, notes, f'https://github.com/{REPOSITORY}/releases/tag/v{version}', assets, channel=value['channel'])
