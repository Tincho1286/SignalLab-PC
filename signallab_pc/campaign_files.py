"""File and single-writer rules shared by the numerical campaign engines."""

from contextlib import contextmanager
import os


def safe_file(folder, name, *, operation='barrido'):
    path = folder/name
    if path.is_symlink() or path.exists() and not path.is_file():
        raise ValueError(f'El catálogo requiere archivos regulares dentro de la carpeta del {operation}.')
    return path


@contextmanager
def campaign_writer(folder, *, operation='barrido', filename='campaign.lock'):
    path = safe_file(folder, filename, operation=operation)
    with path.open('a+b') as handle:
        if os.name == 'nt':
            from msvcrt import LK_NBLCK, LK_UNLCK, locking
            # CRT locks may extend past EOF. Leave a new file empty so
            # simultaneous first writers cannot race on a sentinel write.
            handle.seek(0)
            lock = lambda: locking(handle.fileno(), LK_NBLCK, 1)
            unlock = lambda: locking(handle.fileno(), LK_UNLCK, 1)
        else:
            from fcntl import LOCK_EX, LOCK_NB, LOCK_UN, flock
            lock = lambda: flock(handle, LOCK_EX | LOCK_NB)
            unlock = lambda: flock(handle, LOCK_UN)
        try:
            lock()
        except OSError as exc:
            raise ValueError(f'Otro proceso está escribiendo este {operation} o la carpeta impide obtener el bloqueo.') from exc
        try:
            yield
        finally:
            unlock()
