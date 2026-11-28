"""Bounded Touchstone 1.0 and 2.0 interchange for single-ended S, Z and Y."""

from hashlib import sha256
import math
from pathlib import Path
import re

import numpy as np

from .atomic_file import atomic_text_file
from .execution import ExecutionContext
from .input_files import regular_binary_file
from .resources import ResourceLimitError
from .rf_network import RFNetwork
from .rf_storage import MAX_RF_CELLS, MAX_RF_FREQUENCIES, MAX_RF_PORTS


MAX_BYTES = 64 * 1024**2
MAX_PORTS = MAX_RF_PORTS
MAX_CELLS = MAX_RF_CELLS
MAX_FREQUENCIES = MAX_RF_FREQUENCIES
_MAX_LINE = 1024**2
_UNITS = {'HZ':1, 'KHZ':1e3, 'MHZ':1e6, 'GHZ':1e9}
_NUMBER = re.compile(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[Ee][+-]?[0-9]+)?\Z')
_LEGACY_EXTENSION = re.compile(r'\.s([1-9][0-9]{0,3})p\Z', re.IGNORECASE)
_KEYWORD = re.compile(r'\[([A-Za-z -]+)\]\s*(.*)\Z')


def _numbers(tokens):
    result = []
    for token in tokens:
        if len(token)>80 or not _NUMBER.fullmatch(token):
            raise ValueError(f'Touchstone requiere números decimales válidos: {token[:25]}.')
        value = float(token)
        mantissa=token.lower().split('e',1)[0]
        if not math.isfinite(value) or (value==0 and any(char in '123456789' for char in mantissa)):
            raise ValueError('Touchstone requiere números representables en doble precisión.')
        result.append(value)
    return result


def _option(line):
    if not line.startswith('#'):
        raise ValueError('Falta la línea de opciones Touchstone (#).')
    fields = {}
    tokens = iter(line[1:].upper().split())
    for token in tokens:
        if token in _UNITS:
            key, value = 'scale', _UNITS[token]
        elif token in ('S','Y','Z'):
            key, value = 'parameters', token
        elif token in ('RI','MA','DB'):
            key, value = 'encoding', token
        elif token == 'R':
            key, value = 'reference', _numbers([next(tokens,'')])[0]
            if value <= 0:
                raise ValueError('La resistencia de referencia debe ser positiva.')
        else:
            raise ValueError(f'Opción Touchstone no admitida: {token[:25]}. Se admite S, Z o Y.')
        if key in fields:
            raise ValueError('La línea de opciones Touchstone contiene opciones repetidas.')
        fields[key] = value
    return (fields.get('scale',1e9),fields.get('parameters','S'),fields.get('encoding','MA'),
            fields.get('reference',50.))


def _lines(stream, expected, digest, context):
    seen = index = 0
    while raw := stream.readline(_MAX_LINE + 1):
        seen += len(raw)
        index += 1
        if len(raw) > _MAX_LINE or seen > expected:
            raise ResourceLimitError('El archivo cambió o contiene una línea Touchstone demasiado larga.')
        context.checkpoint()
        digest.update(raw)
        code = raw.split(b'!',1)[0]
        try:
            line = code.decode('utf-8-sig' if index==1 else 'ascii').strip()
        except UnicodeDecodeError as exc:
            raise ValueError(f'Touchstone requiere sintaxis de texto ASCII en la línea {index}.') from exc
        if line:
            yield line
    if seen != expected:
        raise ValueError('El archivo Touchstone cambió durante la lectura.')


def _tag(line):
    match = _KEYWORD.fullmatch(line)
    if match is None:
        raise ValueError('Definición de sección Touchstone inválida.')
    return match[1].casefold(),match[2]


def _size(text, title, maximum):
    if not re.fullmatch(r'[0-9]{1,9}', text):
        raise ValueError(f'{title} requiere un entero positivo.')
    number=int(text)
    if not 1 <= number <= maximum:
        raise ResourceLimitError(f'{title} debe estar entre 1 y {maximum}.')
    return number


def _header_v2(lines, options, filename_ports):
    key, value = _tag(next(lines,''))
    if key != 'number of ports':
        raise ValueError('La primera sección después de # debe indicar [Number of Ports].')
    ports = _size(value, 'Número de puertos', MAX_PORTS)
    if filename_ports is not None and filename_ports != ports:
        raise ValueError('La cantidad de puertos no coincide con la extensión.')
    references = [options[-1]]*ports
    count = order = None
    matrix = 'FULL'
    used = set()
    for line in lines:
        key, value = _tag(line)
        if key in used:
            raise ValueError(f'Sección Touchstone repetida: {key}.')
        used.add(key)
        if key == 'number of frequencies':
            count = _size(value, 'Número de frecuencias', MAX_FREQUENCIES)
        elif key == 'two-port data order' and ports == 2 and value.upper() in ('12_21','21_12'):
            order = value.upper()
        elif key == 'reference':
            tokens = value.split()
            while len(tokens) < ports:
                next_line = next(lines,'')
                if not next_line or next_line.startswith('['):
                    raise ValueError('[Reference] necesita una resistencia positiva por puerto.')
                tokens.extend(next_line.split())
            references = _numbers(tokens)
            if len(references) != ports or min(references)<=0:
                raise ValueError('[Reference] necesita una resistencia positiva por puerto.')
        elif key == 'matrix format' and value.upper() in ('FULL','LOWER','UPPER'):
            matrix = value.upper()
        elif key == 'network data' and not value:
            if count is None or (ports == 2 and order is None):
                raise ValueError('Falta [Number of Frequencies] o el orden explícito de dos puertos.')
            return ports, count, order, matrix, references
        else:
            raise ValueError(f'Sección Touchstone no admitida o inválida: [{key}].')
    raise ValueError('Falta [Network Data].')


def _matrix_indices(ports, matrix, order):
    if matrix == 'LOWER':
        return np.tril_indices(ports)
    if matrix == 'UPPER':
        return np.triu_indices(ports)
    row,col = np.indices((ports,ports)).reshape(2,-1)
    return (col,row) if ports == 2 and order == '21_12' else (row,col)


def _complex_values(flat, encoding):
    first, second = np.asarray(flat).reshape(-1,2).T
    if encoding == 'RI':
        return first + 1j*second
    if encoding == 'MA' and np.any(first < 0):
        raise ValueError('Una magnitud Touchstone en MA debe ser no negativa.')
    with np.errstate(over='ignore',under='ignore',invalid='ignore'):
        magnitude = np.power(10.,first/20) if encoding=='DB' else first
        if encoding=='DB' and np.any((magnitude==0) | ~np.isfinite(magnitude)):
            raise ValueError('El módulo Touchstone en dB queda fuera del rango lineal representable.')
        return magnitude * np.exp(1j*np.deg2rad(np.remainder(second,360)))


def _rescale(values,reference,parameters,*,export=False):
    if parameters=='S':
        return values
    with np.errstate(over='ignore',under='ignore',invalid='ignore',divide='ignore'):
        converted=values*reference if (parameters=='Z')!=export else values/reference
    if (not np.isfinite(converted).all() or np.any((values.real!=0)&(converted.real==0))
            or np.any((values.imag!=0)&(converted.imag==0))):
        raise ValueError('La normalización Touchstone 1.0 excede el rango numérico.')
    return converted


def _parse_rows(lines, frequency, matrices, settings, context):
    version, scale, encoding, order, matrix = settings
    ports = matrices.shape[-1]
    row,col = _matrix_indices(ports,matrix,order)
    stride = 1+2*len(row)
    datum = []
    count = 0
    ended = False
    for line in lines:
        if ended:
            raise ValueError('Encontré datos después de [End].')
        if line.startswith('['):
            key, value = _tag(line)
            if version=='2.0' and key=='end' and not value and not datum:
                ended=True
                continue
            raise ValueError(f'Sección Touchstone no admitida o fuera de lugar: [{key}].')
        tokens = line.split()
        if version == '1.0' and ports == 2 and not datum and len(tokens) == 5:
            raise ValueError('Los parámetros de ruido Touchstone 1.0 quedan fuera de este importador.')
        if len(datum)+len(tokens) > stride:
            raise ValueError('Una frecuencia contiene más datos que los esperados para la matriz.')
        datum.extend(_numbers(tokens))
        if len(datum) < stride:
            continue
        if count == len(frequency):
            raise ResourceLimitError('El archivo excede las frecuencias declaradas o el límite de lectura.')
        f = datum[0]*scale
        if not math.isfinite(f) or f < 0 or (count and frequency[count-1] >= f):
            raise ValueError('Las frecuencias Hz deben ser finitas, crecientes y no negativas.')
        frequency[count] = f
        values = _complex_values(datum[1:],encoding)
        matrices[count,row,col] = values
        if matrix != 'FULL':
            matrices[count,col,row] = values
        datum.clear()
        count += 1
        context.checkpoint()
    if datum or not count or (version=='2.0' and (not ended or count!=len(frequency))):
        raise ValueError('Archivo Touchstone incompleto. Revisá el número de frecuencias, las matrices y [End].')
    return count


def read_touchstone(path, *, context=None):
    """Import checked Touchstone text without evaluating expressions or opening references."""
    ctx = context if context is not None else ExecutionContext()
    ctx.checkpoint()
    path = Path(path)
    ext = _LEGACY_EXTENSION.fullmatch(path.suffix)
    name_ports = None if ext is None else _size(ext[1], 'Puertos indicados en el nombre', MAX_PORTS)
    digest=sha256()
    with regular_binary_file(path,'Seleccioná un archivo Touchstone regular.') as (stream,info):
        if not 0 < info.st_size <= MAX_BYTES:
            raise ResourceLimitError('El archivo Touchstone debe tener contenido y pesar hasta 64 MiB.')
        with ctx.reserve(2 * _MAX_LINE):
            lines = _lines(stream,info.st_size,digest,ctx)
            first = next(lines,'')
            version = '1.0'
            if first.startswith('['):
                if _tag(first) != ('version','2.0'):
                    raise ValueError('Versión Touchstone no admitida. Elegí 1.0 o 2.0.')
                version='2.0'
            scale, parameters, encoding, reference = _option(next(lines,'') if version=='2.0' else first)
            if version == '2.0':
                options = (scale,parameters,encoding,reference)
                ports, count, order, matrix, reference_values = _header_v2(lines,options,name_ports)
            else:
                if name_ports is None:
                    raise ValueError('En Touchstone 1.0, el nombre .sNp indica la cantidad de puertos.')
                ports = name_ports
                # Each point requires one token per component and one per frequency.
                count = min(MAX_FREQUENCIES, MAX_CELLS//ports**2, (info.st_size+1)//(2+4*ports**2))
                order,matrix,reference_values = '21_12','FULL',reference
            if count*ports**2 > MAX_CELLS:
                raise ResourceLimitError('El archivo Touchstone excede el máximo de 1 000 000 entradas de matriz.')
            with ctx.reserve(count*(64*ports**2 + 32*ports + 40)):
                matrices=np.empty((count,ports,ports), dtype=complex)
                frequency=np.empty(count)
                settings = (version,scale,encoding,order,matrix)
                actual=_parse_rows(lines,frequency,matrices,settings,ctx)
                values=matrices[:actual]
                if version=='1.0':
                    values=_rescale(values,reference,parameters)
                return RFNetwork(frequency[:actual],values,representation=parameters,reference_ohm=reference_values,
                                 name=path.stem,context=ctx,metadata={'touchstone_version':version,
                                     'source_file':path.name,'source_sha256':digest.hexdigest(),
                                     'matrix_format':matrix,'parameter_encoding':encoding})


def write_touchstone(path, network: RFNetwork, *, version='2.0', context=None):
    """Export an RI snapshot with exact port order and the file's representable references."""
    ctx = context if context is not None else ExecutionContext()
    ctx.checkpoint()
    path = Path(path)
    if version not in ('1.0','2.0') or network.representation not in ('S','Z','Y'):
        raise ValueError('Touchstone admite S, Z o Y, en versión 1.0 o 2.0.')
    ports = network.nports
    if ports > MAX_PORTS or network.values.size > MAX_CELLS or len(network.frequencies_hz)>MAX_FREQUENCIES:
        raise ResourceLimitError('La red supera la envolvente de intercambio Touchstone.')
    ext = _LEGACY_EXTENSION.fullmatch(path.suffix)
    if ext is not None and int(ext[1]) != ports or (version=='1.0' and ext is None):
        raise ValueError('La extensión .sNp debe coincidir con la cantidad de puertos.')
    reference=network.reference_ohm[0]
    if not np.all(network.reference_ohm == reference) or (version=='1.0' and not np.all(reference==reference[0])):
        raise ValueError('Renormalizá a referencias constantes. Touchstone 1.0 requiere además el mismo valor para todos los puertos.')
    legacy=version=='1.0'
    with atomic_text_file(path,newline='\n',before_commit=ctx.checkpoint) as stream:
        if not legacy:
            stream.write('[Version] 2.0\n')
        stream.write(f'# Hz {network.representation} RI R {reference[0]:.17g}\n')
        if not legacy:
            stream.write(f'[Number of Ports] {ports}\n')
            if ports == 2:
                stream.write('[Two-Port Data Order] 12_21\n')
            stream.write(f'[Number of Frequencies] {len(network.frequencies_hz)}\n')
            stream.write('[Reference] '+' '.join(f'{r:.17g}' for r in reference)+'\n')
            stream.write('[Matrix Format] Full\n[Network Data]\n')
        written=stream.tell()
        for frequency,values in zip(network.frequencies_hz,network.values,strict=True):
            ctx.checkpoint()
            if legacy:
                values=_rescale(values,reference[0],network.representation,export=True)
            if legacy and ports==2:
                values=values.T
            if ports <= 2:
                rows = (values.ravel(),)
            else:
                rows = (row[start:start+4] for row in values for start in range(0,len(row),4))
            for index,part in enumerate(rows):
                pairs = ' '.join(f'{v.real:.17g} {v.imag:.17g}' for v in part)
                line = (f'{frequency:.17g} ' if index==0 else ' ') + pairs + '\n'
                written += len(line)
                if written + 6 > MAX_BYTES:
                    raise ResourceLimitError('La salida Touchstone supera 64 MiB.')
                stream.write(line)
        if not legacy:
            stream.write('[End]\n')
