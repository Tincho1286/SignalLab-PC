"""Scientific metadata and content verification for Core publication."""

from dataclasses import asdict
from hashlib import sha256
import json

import numpy as np

from .filters import Transfer
from .model import Signal


_FIELDS = {
    'signal': ('origin', 'step', 'units', 'name', 'domain', 'expression', 'metadata'),
    'system': ('domain', 'name', 'advance', 'sample_period_s', 'roc'),
}
_BLOCK = 16384


def _scalar(value):
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f'Valor de procedencia no serializable: {type(value).__name__}.')


def settings_digest(value):
    encoded = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False, default=_scalar)
    return sha256(encoded.encode('ascii')).hexdigest()


def _update_array(digest, values, dtype, checkpoint, *, pairs=False):
    shape = (len(values),) if pairs else values.shape
    digest.update(settings_digest(shape).encode('ascii'))
    for start in range(0, shape[0], _BLOCK):
        checkpoint()
        block = np.ascontiguousarray(values[start:start + _BLOCK], dtype='<f8' if pairs else dtype)
        digest.update(memoryview(block).cast('B'))


def _content(kind, data, checkpoint, *, encoded):
    if kind == 'signal' and data['domain'] == 'discrete':
        data = {**data, 'origin': int(data['origin']), 'step': float(data['step'])}
    fields = {key: data[key] for key in _FIELDS[kind]}
    digest = sha256(settings_digest([kind, fields]).encode('ascii'))
    for key in ('values',) if kind == 'signal' else ('b', 'a'):
        _update_array(digest, data[key], '<c16', checkpoint, pairs=encoded)
    if kind == 'system' and data['sos'] is not None:
        _update_array(digest, np.asarray(data['sos']), '<f8', checkpoint)
    return digest.hexdigest()


def content_digest(value, checkpoint):
    if isinstance(value, Signal):
        kind, arrays = 'signal', ('values',)
    elif isinstance(value, Transfer):
        kind, arrays = 'system', ('b', 'a', 'sos')
    else:
        raise TypeError('Se esperaba una señal o un sistema para verificar la procedencia.')
    data = {key: getattr(value, key) for key in (*_FIELDS[kind], *arrays)}
    return _content(kind, data, checkpoint, encoded=False)


def encoded_digest(kind, data, checkpoint):
    if kind not in _FIELDS:
        raise ValueError('El registro de procedencia debe ser una señal o un sistema.')
    return _content(kind, data, checkpoint, encoded=True)


def verify_inputs(inputs, expected, checkpoint):
    if tuple(content_digest(value, checkpoint) for value in inputs) != expected:
        raise ValueError('La entrada cambió durante el cálculo. Volvé a calcular antes de publicar.')


def scientific_metadata(operation, parameters, *, version=1):
    return {'schema': version, 'operation': operation, **asdict(parameters)}
