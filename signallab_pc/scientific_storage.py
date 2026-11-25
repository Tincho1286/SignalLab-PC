"""Experimental single-file exchange for one typed scientific signal."""

import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import stat
import struct

import numpy as np

from .atomic_file import atomic_binary_file
from .execution import ExecutionContext
from .model import Signal
from .resources import ensure_working_set


_MAGIC = b'SLPCBIN\x01'
_MAX_HEADER = 1024 * 1024
_CHUNK = 1024 * 1024
_DTYPE = np.dtype('<c16')
_FIELDS = ('origin', 'step', 'units', 'name', 'domain', 'expression', 'metadata')


def save_binary_signal(signal: Signal, path, execution: ExecutionContext | None = None):
    ctx = execution or ExecutionContext()
    ctx.checkpoint()
    count = int(signal.values.size)
    ctx.require(32 * count)
    header = dict(count=count, **{field:getattr(signal,field) for field in _FIELDS})
    encoded = json.dumps(header,ensure_ascii=False,allow_nan=False,separators=(',', ':')).encode('utf-8')
    if not 0 < len(encoded) <= _MAX_HEADER:
        raise ValueError('Los metadatos del archivo científico superan 1 MiB.')
    prefix = _MAGIC + struct.pack('<I',len(encoded))
    payload = memoryview(np.asarray(signal.values,dtype=_DTYPE,order='C')).cast('B')
    digest = hashlib.sha256(prefix + encoded)
    with atomic_binary_file(path,before_commit=ctx.checkpoint) as stream:
        stream.write(prefix)
        stream.write(encoded)
        for offset in range(0, len(payload), _CHUNK):
            ctx.checkpoint()
            block = payload[offset:offset+_CHUNK]
            digest.update(block)
            stream.write(block)
        stream.write(digest.digest())


def _reject_constant(value):
    raise ValueError(f'Constante JSON no admitida: {value}.')


def _finite_number(value):
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError('Los metadatos requieren números finitos.')
    return parsed


def load_binary_signal(path, execution: ExecutionContext | None = None) -> Signal:
    ctx = execution or ExecutionContext()
    ctx.checkpoint()
    with Path(path).open('rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise ValueError('Se requiere un archivo científico regular.')
        prefix = stream.read(len(_MAGIC)+4)
        if len(prefix) != len(_MAGIC)+4 or not prefix.startswith(_MAGIC):
            raise ValueError('Formato científico desconocido.')
        header_size = struct.unpack('<I',prefix[len(_MAGIC):])[0]
        if not 0 < header_size <= _MAX_HEADER:
            raise ValueError('Tamaño de cabecera científica inválido.')
        header = stream.read(header_size)
        if len(header) != header_size:
            raise ValueError('Cabecera científica incompleta.')
        try:
            fields = json.loads(header.decode('utf-8'),parse_constant=_reject_constant,parse_float=_finite_number)
        except RecursionError as error:
            raise ValueError('Anidamiento excesivo en los metadatos científicos.') from error
        if not isinstance(fields,dict) or fields.keys() != {'count', *_FIELDS}:
            raise ValueError('Esquema de metadatos científico inválido.')
        count = fields.pop('count')
        if type(count) is not int or count <= 0:
            raise ValueError('Cantidad de muestras inválida.')
        if info.st_size != len(prefix) + header_size + count * _DTYPE.itemsize + 32:
            raise ValueError('El tamaño de datos no coincide con la cabecera científica.')
        if (not isinstance(fields['metadata'],dict)
                or any(type(fields[name]) not in (int,float) for name in ('origin','step'))
                or any(not isinstance(fields[name],str) for name in ('units','name','domain','expression'))):
            raise ValueError('Los tipos de los metadatos científicos no son válidos.')
        ctx.require(64 * count)
        ensure_working_set(count,live_arrays=4)
        samples = np.empty(count,dtype=_DTYPE)
        payload = memoryview(samples).cast('B')
        digest = hashlib.sha256(prefix + header)
        for offset in range(0,len(payload),_CHUNK):
            ctx.checkpoint()
            block = payload[offset:offset+_CHUNK]
            if stream.readinto(block) != len(block):
                raise ValueError('Datos científicos incompletos.')
            digest.update(block)
        if not hmac.compare_digest(stream.read(32),digest.digest()) or stream.read(1):
            raise ValueError('Falló la integridad del archivo científico.')
    try:
        signal = Signal(samples,**fields)
    except (OverflowError,TypeError) as error:
        raise ValueError('Coordenadas científicas inválidas.') from error
    ctx.checkpoint()
    return signal
