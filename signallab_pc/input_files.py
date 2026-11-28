"""Bounded UTF-8 and JSON reads for user-selected documents."""

from contextlib import contextmanager
import base64
import binascii
import json
import math
import os
from pathlib import Path
import stat

from .execution import ExecutionContext
from .jobs import checkpoint as check_job
from .resources import ensure_working_set

_READ_BLOCK = 1024**2


def decode_base64_exact(text, size):
    if not isinstance(text, str) or len(text) != 4*((size+2)//3):
        raise ValueError('La longitud codificada del registro no coincide con el encabezado.')
    try:
        raw = base64.b64decode(text, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError('El registro contiene Base64 inválido.') from exc
    if len(raw) != size or base64.b64encode(raw).decode('ascii') != text:
        raise ValueError('La codificación binaria del registro es inconsistente.')
    return raw


@contextmanager
def regular_binary_file(path, description):
    path = Path(path)
    if not path.is_file():
        raise ValueError(description)
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NONBLOCK', 0)
    with open(path, 'rb', opener=lambda filename, _: os.open(filename, flags)) as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise ValueError(description)
        yield stream, info


@contextmanager
def _bounded_text(path, live_arrays, check):
    with regular_binary_file(path, 'La entrada debe ser un archivo regular.') as (stream, info):
        budget = ensure_working_set(info.st_size, bytes_per_sample=1, live_arrays=live_arrays)
        with ExecutionContext().reserve(budget):
            text = _read_utf8(stream, info.st_size, check)
            yield text


def _read_utf8(stream, size, check):
    content = bytearray()
    for start in range(0, size, _READ_BLOCK):
        check()
        count = min(_READ_BLOCK, size - start)
        block = stream.read(count)
        if len(block) != count:
            raise ValueError('El archivo cambió de tamaño durante la lectura.')
        content.extend(block)
    if stream.read(1):
        raise ValueError('El archivo cambió de tamaño durante la lectura.')
    check()
    return content.decode('utf-8-sig')


def read_text(path, *, live_arrays=8, checkpoint=None):
    with _bounded_text(path, live_arrays, checkpoint or check_job) as text:
        return text


def _unique_object(pairs):
    content = {}
    for key, value in pairs:
        if key in content:
            raise ValueError('El documento JSON contiene claves repetidas.')
        content[key] = value
    return content


def read_json(path, *, live_arrays=8, checkpoint=None):
    check = checkpoint or check_job
    with _bounded_text(path, live_arrays, check) as text:
        document = decode_json(text)
        check()
        return document


def decode_json(text, **options):
    try:
        return json.loads(text, object_pairs_hook=_unique_object, **options)
    except RecursionError as error:
        raise ValueError('El documento JSON tiene demasiados niveles.') from error


def decode_finite_json(text):
    def reject(value):
        raise ValueError(f'Constante JSON no admitida: {value}.')

    def real(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError('Los metadatos requieren números finitos.')
        return number

    return decode_json(text, parse_constant=reject, parse_float=real)
