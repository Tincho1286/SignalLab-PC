"""Bounded UTF-8 and JSON reads for user-selected documents."""

import json
import os
from pathlib import Path
import stat

from .resources import ensure_working_set


def read_text(path, *, live_arrays=8):
    path = Path(path)
    if not path.is_file():
        raise ValueError('La entrada debe ser un archivo regular.')
    with path.open('rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise ValueError('La entrada debe ser un archivo regular.')
        ensure_working_set(info.st_size,bytes_per_sample=1,live_arrays=live_arrays)
        content = stream.read(info.st_size + 1)
        if len(content) != info.st_size:
            raise ValueError('El archivo cambió de tamaño durante la lectura.')
    return content.decode('utf-8-sig')


def _unique_object(pairs):
    content = {}
    for key, value in pairs:
        if key in content:
            raise ValueError('El documento JSON contiene claves repetidas.')
        content[key] = value
    return content


def read_json(path, *, live_arrays=8):
    try:
        return json.loads(read_text(path,live_arrays=live_arrays),object_pairs_hook=_unique_object)
    except RecursionError as error:
        raise ValueError('El documento JSON tiene demasiados niveles.') from error
