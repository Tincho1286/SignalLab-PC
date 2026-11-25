"""Inert, versioned CAS session data. Symbolic evaluation remains in the worker."""

from copy import deepcopy


_STATE_FIELDS = {'version', 'variables', 'functions', 'results', 'ans', 'assumptions'}
_CONTEXT_FIELDS = {'result_contexts', 'name_contexts'}
_SHEET_FIELDS = {'version', 'state', 'entries', 'input', 'commands', 'draft',
                 'command_position', 'selected', 'math_size', 'digits', 'bindings'}


def _state(value):
    if (not isinstance(value, dict) or not _STATE_FIELDS <= value.keys()
            or value.keys() - (_STATE_FIELDS | _CONTEXT_FIELDS)
            or type(value['version']) is not int or value['version'] != 1):
        raise ValueError('Versión de estado CAS incompatible.')
    for name in value.keys() - {'version', 'ans'}:
        if not isinstance(value[name], dict):
            raise ValueError('La hoja CAS contiene definiciones incompletas.')
    for name in ('variables', 'results'):
        if any(not isinstance(text, str) or not text for text in value[name].values()):
            raise ValueError('La hoja CAS contiene un valor simbólico inválido.')
    for function in value['functions'].values():
        if (not isinstance(function, dict) or set(function) != {'parameters', 'body'}
                or not isinstance(function['body'], str)
                or not isinstance(function['parameters'], list)
                or not all(isinstance(name, str) for name in function['parameters'])):
            raise ValueError('La hoja CAS contiene una función inválida.')
    for name in _CONTEXT_FIELDS | {'assumptions'}:
        if any(not isinstance(row, dict) for row in value.get(name, {}).values()):
            raise ValueError('La hoja CAS contiene condiciones inválidas.')
    return value['results']


def prepare(sheet, project):
    """Validate references and attach already published results without calculating."""
    if (not isinstance(sheet, dict) or set(sheet) != _SHEET_FIELDS
            or type(sheet['version']) is not int or sheet['version'] != 1):
        raise ValueError('Versión de hoja CAS incompatible.')
    results = _state(sheet['state'])
    for field in ('input', 'draft', 'digits'):
        if not isinstance(sheet[field], str):
            raise ValueError('La hoja CAS contiene una entrada inválida.')
    commands = sheet['commands']
    bindings = sheet['bindings']
    if (not isinstance(commands, list) or not all(isinstance(text, str) for text in commands)
            or type(sheet['command_position']) is not int or not 0 <= sheet['command_position'] <= len(commands)
            or type(sheet['math_size']) is not int or not 13 <= sheet['math_size'] <= 31
            or not isinstance(bindings, list)
            or any(not isinstance(row, list) or len(row) != 2
                   or not all(isinstance(text, str) for text in row) for row in bindings)
            or not isinstance(sheet['entries'], list)):
        raise ValueError('La hoja CAS contiene un historial o una configuración inválidos.')
    entries, linked = [], set()
    last_cell = 0
    for entry in sheet['entries']:
        if (not isinstance(entry, dict) or type(entry.get('cell')) is not int or entry['cell'] <= last_cell
                or not isinstance(entry.get('source'), str) or type(entry.get('imported')) is not bool):
            raise ValueError('La hoja CAS contiene celdas inválidas o repetidas.')
        last_cell = entry['cell']
        row = dict(entry)
        if row.get('status') == 'done' and set(row) == {'cell', 'source', 'imported', 'status', 'result_id'}:
            row['answer'] = _answer(project, row, results.get(str(last_cell)))
            linked.add(str(last_cell))
        elif (row.get('status') != 'error' or set(row) != {'cell', 'source', 'imported', 'status', 'error'}
              or not isinstance(row['error'], str)):
            raise ValueError('La hoja CAS contiene una celda incompleta.')
        entries.append(row)
    if linked != set(results):
        raise ValueError('Los resultados exactos no coinciden con las celdas de la hoja CAS.')
    for index in (sheet['selected'], sheet['state']['ans']):
        if index is not None and (type(index) is not int or str(index) not in linked):
            raise ValueError('La hoja CAS hace referencia a una celda sin resultado.')
    return {**deepcopy(sheet), 'entries': entries}


def _answer(project, row, encoded):
    try:
        record = project.get(row['result_id'])
    except (KeyError, TypeError) as error:
        raise ValueError('La hoja CAS hace referencia a un resultado ausente.') from error
    answer = record.get('cas_answer') if isinstance(record, dict) else None
    if (not isinstance(answer, dict) or record.get('source') != row['source']
            or not encoded or answer.get('encoded_value') != encoded
            or not isinstance(answer.get('text'), str)
            or answer.get('expression') is not None and not isinstance(answer['expression'], str)
            or not isinstance(answer.get('symbols'), list)
            or not all(isinstance(name, str) for name in answer['symbols'])
            or not isinstance(answer.get('notices'), list)
            or not all(isinstance(text, str) for text in answer['notices'])):
        raise ValueError('El resultado publicado no coincide con la celda CAS.')
    return answer
