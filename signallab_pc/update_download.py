"""Bounded HTTPS transport. Downloaded programs are never run by this module."""
from pathlib import Path
import hashlib
import hmac
import os
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from .update_manifest import FEED_URL, MAX_MANIFEST, UpdateError, verify_manifest

HOSTS = {'github.com', 'release-assets.githubusercontent.com', 'objects.githubusercontent.com'}


class Cancelled(UpdateError):
    pass


def check_url(url):
    value = urllib.parse.urlsplit(url)
    try:
        valid = value.scheme == 'https' and value.hostname in HOSTS and value.port in (None, 443) and not value.username and not value.password
    except ValueError:
        valid = False
    if not valid:
        raise UpdateError('Se rechazó una dirección de actualización no autorizada.')


class Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def open_url(url):
    check_url(url)
    from . import __version__
    request = urllib.request.Request(url, headers={'User-Agent': 'SignalLab-PC/' + __version__, 'Accept': 'application/octet-stream'})
    return urllib.request.build_opener(Redirect()).open(request, timeout=15)


def checkpoint(cancel):
    if cancel is not None and cancel.is_set():
        raise Cancelled('Actualización cancelada.')


def fetch_release(*, cancel=None, opener=open_url, key=None, now=None):
    checkpoint(cancel)
    try:
        with opener(FEED_URL) as response:
            check_url(response.geturl())
            data = response.read(MAX_MANIFEST + 1)
        checkpoint(cancel)
        return verify_manifest(data, key=key, now=now)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise UpdateError('Todavía no hay un canal de actualizaciones firmado publicado. Podés consultar las versiones en GitHub.') from exc
        raise UpdateError('GitHub no pudo entregar la actualización. Intentá nuevamente más tarde.') from exc
    except (TimeoutError, OSError) as exc:
        raise UpdateError('No se pudo conectar con GitHub. Revisá la conexión e intentá nuevamente.') from exc


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1024**2), b''):
            digest.update(block)
    return digest.hexdigest()


def verify_file(path, asset):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size != asset.size or not hmac.compare_digest(file_hash(path), asset.sha256):
        raise UpdateError('La descarga está incompleta o fue modificada. No se ejecutará.')


def download(asset, cache, *, cancel=None, progress=None, opener=open_url):
    """Private temporary directory; clean only files created by this request."""
    checkpoint(cancel); check_url(asset.url)
    cache = Path(cache); cache.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix='signallab-update-', dir=cache))
    from .update_cache import register, MARKER
    register(folder, asset)
    partial = folder / 'download.partial'; target = folder / asset.name
    begin = time.monotonic(); count = 0; digest = hashlib.sha256()
    try:
        with opener(asset.url) as response, partial.open('xb') as output:
            check_url(response.geturl())
            length = response.headers.get('Content-Length')
            if length is not None and (not length.isdecimal() or int(length) != asset.size):
                raise UpdateError('El servidor entregó un tamaño distinto del instalador firmado.')
            while True:
                checkpoint(cancel)
                if time.monotonic() - begin > 1800:
                    raise UpdateError('La descarga tardó demasiado. Volvé a intentarlo.')
                block = response.read(min(1024**2, asset.size - count + 1))
                if not block:
                    break
                count += len(block)
                if count > asset.size:
                    raise UpdateError('La descarga supera el tamaño firmado.')
                output.write(block); digest.update(block)
                if progress is not None:
                    progress(count, asset.size)
            output.flush(); os.fsync(output.fileno())
        checkpoint(cancel)
        if count != asset.size or not hmac.compare_digest(digest.hexdigest(), asset.sha256):
            raise UpdateError('La descarga no coincide con la actualización firmada. No se ejecutará.')
        partial.replace(target)
        return target
    except Exception:
        partial.unlink(missing_ok=True)
        (folder / MARKER).unlink(missing_ok=True)
        try:
            folder.rmdir()
        except OSError:
            pass
        raise
