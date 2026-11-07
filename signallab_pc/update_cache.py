"""Remove only registered updater cache files, never arbitrary user documents."""
from pathlib import Path
import json
import time
from .update_manifest import FILENAMES, version_tuple, UpdateError

MARKER = '.signallab-update-cache.json'


def register(folder, asset):
    (Path(folder) / MARKER).write_text(json.dumps(dict(schema=1, platform=asset.platform,
        version=asset.version, filename=asset.name)), encoding='utf-8')


def prune(cache, current, *, now=None):
    cache = Path(cache); removed = 0; now = time.time() if now is None else now
    if not cache.is_dir():
        return removed
    for folder in cache.iterdir():
        if not folder.name.startswith('signallab-update-') or folder.is_symlink() or not folder.is_dir():
            continue
        marker = folder / MARKER
        try:
            if marker.is_symlink() or not marker.is_file() or marker.stat().st_size > 4096:
                continue
            row = json.loads(marker.read_text(encoding='utf-8'))
            expected = FILENAMES[row['platform']].format(version=row['version'])
            version = version_tuple(row['version'])
            if row.get('schema') != 1 or row['filename'] != expected:
                continue
            names = {p.name for p in folder.iterdir()}
            if names - {expected, MARKER, 'download.partial'} or any(p.is_symlink() for p in folder.iterdir()):
                continue
            age = now - marker.stat().st_mtime
            if version > version_tuple(current) and age < 7 * 86400:
                continue
            # Interrupted downloads get at least a day; an active transfer is bounded to 30 min.
            if 'download.partial' in names and age < 86400:
                continue
            for name in (expected, 'download.partial'):
                path = folder / name
                if path.is_file():
                    path.unlink()
            marker.unlink(); folder.rmdir(); removed += 1
        except (OSError, ValueError, KeyError, TypeError, UpdateError):
            continue
    return removed
