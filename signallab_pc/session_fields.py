"""Capture named, inert inputs from tool pages without executing a calculation."""
import math

from PySide6.QtWidgets import (QCheckBox, QComboBox, QLineEdit, QRadioButton, QSpinBox,
                               QDoubleSpinBox, QStackedWidget)

from .band_edges import BandEdgesEditor, KINDS
from .coefficient_editor import CoefficientEditor
from .expression_editor import ExpressionEditor
from .matrix_editor import MatrixEditor
from .project import decode, encode
from .realization_editor import RealizationInput
from .realization_graph import RealizationGraph
from .resources import ensure_working_set
from .signal_editor_panel import SignalEditorPanel, edited_metadata
from .state_simulation_inputs import StateInputSources
from .toolbox import LocalInput


TEXT_TYPES = (ExpressionEditor, CoefficientEditor, QLineEdit)
SELECT_TYPES = (QCheckBox, QRadioButton, QComboBox, QSpinBox, QDoubleSpinBox)
INPUT_TYPES = TEXT_TYPES + SELECT_TYPES + (
    BandEdgesEditor, LocalInput, RealizationInput, MatrixEditor, StateInputSources,
)


def controls(owner):
    named = {}
    seen = set()
    permanent = ('discrete_source', 'continuous_source')
    candidates = [(name, getattr(owner, name)) for name in permanent if hasattr(owner,name)]
    candidates.extend(vars(owner).items())
    fields = getattr(owner, 'fields', None)
    candidates.extend(('fields.' + name, widget)
                      for name, widget in (fields.items() if isinstance(fields, dict) else ())
                      if isinstance(name, str))
    for name, widget in list(candidates):
        if isinstance(widget, QStackedWidget):
            candidates.extend((f'{name}.{index}', widget.widget(index))
                              for index in range(widget.count()) if isinstance(widget.widget(index), LocalInput))
    inputs = getattr(owner, 'inputs', None)
    if isinstance(inputs, (tuple, list)):
        channels = []
        for index, group in enumerate(inputs):
            if isinstance(group, (list, tuple)):
                channels.extend((f'inputs.{index}.{slot}', entry) for slot, entry in enumerate(group)
                                if isinstance(entry, LocalInput))
            elif isinstance(group, LocalInput):
                channels.append((f'inputs.{index}', group))
        candidates = channels + candidates
    for name, widget in candidates:
        if name.startswith('_') or id(widget) in seen or not isinstance(widget, INPUT_TYPES):
            continue
        if isinstance(widget, QLineEdit) and (widget.echoMode() != QLineEdit.EchoMode.Normal
                                             or widget.isReadOnly() or 'path' in name.lower()):
            continue
        if isinstance(owner, LocalInput) and name in ('mode', 'recent'):
            continue
        named[name] = widget
        seen.add(id(widget))
    return named


def source_document(value, key, records):
    if key is not None and key in records:
        return {'record': key}
    kind, data = encode(value)
    return {'kind': kind, 'data': data}


def source_value(document, project, kind):
    if not isinstance(document, dict):
        raise ValueError('La sesión contiene una referencia de entrada inválida.')
    if set(document) == {'record'}:
        key = document['record']
        if not isinstance(key, str) or project.describe(key)['kind'] != kind:
            raise ValueError('La entrada no apunta a un objeto del tipo esperado.')
        return project.get(key), key
    if set(document) == {'kind', 'data'} and document['kind'] == kind:
        return decode(kind, document['data']), None
    raise ValueError('El tipo de entrada de la sesión no coincide con la herramienta.')


def snapshot(widget, records):
    if isinstance(widget, LocalInput):
        slots = {str(view): source_document(source, key, records)
                 for view, (source, key, _, _) in widget._external_sources.items()
                 if source is not None}
        view = widget.entry_modes.view
        if view >= 2 and widget.loaded is not None:
            slots[str(view)] = source_document(widget.loaded, widget.loaded_reference_id, records)
        origin = getattr(widget, '_expression_origin', None)
        expression = None
        if origin and origin[0] == widget.expression.text():
            expression = {'record': origin[1] if origin[1] in records else None,
                          'conditions': list(getattr(widget, '_expression_conditions', ())),
                          'frequency_condition': getattr(widget, '_expression_frequency_condition', 'True')}
        return dict(view=view, fields=field_values(widget, records), sources=slots,
                    expression=expression)
    if isinstance(widget, BandEdgesEditor):
        return dict(kind=widget.current, values={kind: list(values) for kind, values in widget.saved.items()})
    if isinstance(widget, RealizationInput):
        return {domain: graph.to_document() for domain, graph in widget.graphs.items()}
    if isinstance(widget, MatrixEditor):
        return {'shape': [widget.model.rows, widget.model.columns],
                'cells': [[row, col, value] for (row,col),value in sorted(widget.model.cells.items())]}
    if isinstance(widget, StateInputSources):
        return {'channel':widget.channel.currentIndex(),
                'banks': {kind: [[index, snapshot(field, records)] for index, field in sorted(bank.items())]
                          for kind, bank in widget.banks.items()}}
    if isinstance(widget, TEXT_TYPES):
        return widget.text()
    if isinstance(widget, QComboBox):
        return widget.currentIndex()
    if isinstance(widget, (QCheckBox, QRadioButton)):
        return widget.isChecked()
    return widget.value()


def field_values(owner, records):
    return {name: snapshot(widget, records) for name, widget in controls(owner).items()
            if not widget.property('sessionTransient')}


def restore_fields(owner, values, project):
    named = controls(owner)
    if not isinstance(values, dict) or not values.keys() <= named.keys():
        raise ValueError('La sesión contiene un campo incompatible con la herramienta.')
    # Set parent selectors before the texts that their callbacks initialize.
    for name, widget in named.items():
        if name in values and isinstance(widget, SELECT_TYPES) and not widget.property('sessionTransient'):
            restore(widget, values[name], project)
    banks = []
    for name, widget in controls(owner).items():
        if name not in values or isinstance(widget, SELECT_TYPES) or widget.property('sessionTransient'):
            continue
        if isinstance(widget, StateInputSources):
            banks.append((widget, values[name]))
        else:
            restore(widget, values[name], project)
    for widget, state in banks:
        restore(widget, state, project)


def restore(widget, value, project):
    if isinstance(widget, LocalInput):
        if (not isinstance(value, dict) or set(value) != {'view','fields','sources','expression'}
                or type(value['view']) is not int or not 0 <= value['view'] <= 3
                or not isinstance(value['sources'], dict) or not value['sources'].keys() <= {'2','3'}):
            raise ValueError('La sesión contiene un selector de entrada inválido.')
        for view, document in value['sources'].items():
            source, key = source_value(document, project, 'signal')
            widget.set_source(source, key, view=int(view))
        widget.entry_modes.select(value['view'])
        restore_fields(widget, value['fields'], project)
        context = value['expression']
        if context is not None:
            if (not isinstance(context, dict) or set(context) != {'record','conditions','frequency_condition'}
                    or not isinstance(context['conditions'], list)
                    or not all(isinstance(condition, str) for condition in context['conditions'])
                    or not isinstance(context['frequency_condition'], str)):
                raise ValueError('Las condiciones de la expresión no son válidas.')
            key = context['record']
            if key is not None and project.describe(key)['kind'] != 'calculation':
                raise ValueError('La expresión no apunta a un cálculo de la sesión.')
            widget._expression_origin = (widget.expression.text(), key)
            widget._expression_conditions = tuple(context['conditions'])
            widget._expression_frequency_condition = context['frequency_condition']
        return
    if isinstance(widget, BandEdgesEditor):
        if (not isinstance(value, dict) or set(value) != {'kind','values'}
                or value['kind'] not in KINDS or not isinstance(value['values'], dict)
                or value['values'].keys() != KINDS.keys()):
            raise ValueError('La sesión contiene bordes de filtro inválidos.')
        for kind, fields in value['values'].items():
            if not isinstance(fields, list) or len(fields) != len(KINDS[kind][1]) or not all(isinstance(field,str) for field in fields):
                raise ValueError('La especificación de bordes de la sesión es inválida.')
        widget.saved = value['values']
        widget.kind.setCurrentIndex(widget.kind.findData(value['kind']))
        widget.change_kind()
        return
    if isinstance(widget, RealizationInput):
        if not isinstance(value, dict) or not value.keys() <= {'analog', 'digital'}:
            raise ValueError('El diagrama guardado tiene un dominio inválido.')
        graphs = {domain: RealizationGraph.from_document(graph) for domain, graph in value.items()}
        if any(domain != graph.domain for domain, graph in graphs.items()):
            raise ValueError('El dominio del diagrama no coincide con la entrada.')
        widget.graphs = graphs
        widget.set_domain(widget.domain)
        return
    if isinstance(widget, MatrixEditor):
        restore_matrix(widget, value)
        return
    if isinstance(widget, StateInputSources):
        restore_banks(widget, value, project)
        return
    if isinstance(widget, TEXT_TYPES) and isinstance(value, str):
        widget.setText(value)
        return
    if isinstance(widget, QComboBox) and type(value) is int and -1 <= value < widget.count():
        widget.setCurrentIndex(value)
        return
    if isinstance(widget, (QCheckBox, QRadioButton)) and type(value) is bool:
        widget.setChecked(value)
        return
    if (isinstance(widget, (QSpinBox, QDoubleSpinBox)) and type(value) in (int, float)
            and widget.minimum() <= value <= widget.maximum()):
        widget.setValue(value)
        return
    raise ValueError('Un valor de entrada no coincide con su tipo o intervalo.')


def restore_matrix(widget, value):
    if (not isinstance(value,dict) or set(value) != {'shape','cells'}
            or not isinstance(value['shape'],list) or len(value['shape']) != 2
            or not isinstance(value['cells'],list)):
        raise ValueError('La sesión contiene una matriz inválida.')
    rows, columns = value['shape']
    if (type(rows) is not int or type(columns) is not int or not 0 <= rows <= widget.rows.maximum()
            or not 0 <= columns <= widget.columns.maximum()):
        raise ValueError('Las dimensiones de la matriz son inválidas.')
    ensure_working_set(rows+columns+len(value['cells']),bytes_per_sample=128,live_arrays=3)
    cells = {}
    for entry in value['cells']:
        if not isinstance(entry,list) or len(entry) != 3:
            raise ValueError('Hay una celda de matriz inválida.')
        row, column, text = entry
        if (type(row) is not int or type(column) is not int or not 0 <= row < widget.rows.maximum()
                or not 0 <= column < widget.columns.maximum() or not isinstance(text,str)
                or (row,column) in cells):
            raise ValueError('Hay una celda de matriz inválida o repetida.')
        cells[row,column] = text
    widget.replace_cells(rows, columns, cells)


def restore_banks(widget, value, project):
    if (not isinstance(value,dict) or set(value) != {'channel','banks'}
            or not isinstance(value['banks'],dict) or value['banks'].keys() != widget.banks.keys()
            or type(value['channel']) is not int or not -1 <= value['channel'] < widget.count):
        raise ValueError('La sesión contiene bancos de entradas inválidos.')
    for kind, drafts in value['banks'].items():
        if not isinstance(drafts,list):
            raise ValueError('El banco de entradas no contiene borradores válidos.')
        ensure_working_set(len(drafts),bytes_per_sample=2**20,live_arrays=1)
        seen = set()
        for entry in drafts:
            if (not isinstance(entry,list) or len(entry)!=2 or type(entry[0]) is not int
                    or not 0<=entry[0]<2**31-1 or entry[0] in seen):
                raise ValueError('La sesión contiene un canal inválido o repetido.')
            index, draft = entry
            seen.add(index)
            restore(widget.field(index,kind=kind),draft,project)
    widget.channel.setCurrentIndex(value['channel'])


PARENT_FIELDS = ('input_id', 'parent_id', 'system_id', 'model_parent')


def snapshot_page(page, records):
    panel = getattr(page, 'panel', page)
    saved = dict(fields=field_values(panel, records))
    if (page.context is not None and isinstance(page.context.source, LocalInput)
            and page.context.source not in controls(panel).values()):
        saved['source'] = snapshot(page.context.source, records)
    if page.context is not None and page.context.system_id in records:
        saved['context_system'] = page.context.system_id
    if isinstance(panel, SignalEditorPanel) and panel.current is not None:
        edits = []
        for index in sorted(panel.changed_rows):
            original = panel.history.baseline[index]
            edits.append([index, float(original.real), float(original.imag)])
        saved['table'] = {'signal': source_document(panel.current, None, records),
                          'pending': panel.pending, 'offset': panel.offset, 'edits': edits}
    for name in PARENT_FIELDS:
        key = getattr(panel, name, None)
        if isinstance(key, str) and key in records:
            saved[name] = key
    preserved = getattr(panel, '_preserved_system', None)
    if preserved is not None:
        from .system_clock import signature
        fields = signature(panel)
        if fields[3] in (None, 0):
            intact = (fields[1], fields[2], fields[0]) == getattr(panel, '_preserved_definition', None)
        else:
            intact = (fields[4], fields[0]) == getattr(panel, '_preserved_formula', None)
        if intact:
            saved['system'] = source_document(preserved, None, records)
    context = getattr(panel, '_formula_context', None)
    if (context is not None and (panel.transfer_formula.text(), panel.domain.currentIndex())
            == getattr(panel, '_formula_context_signature', None)):
        saved['formula_context'] = source_document(context, saved.get('input_id'), records)
    context = snapshot_expression_context(panel, records)
    if context is not None:
        saved['expression_context'] = context
    return saved


TRANSFORM_SOURCES = ('_library_source', '_inverse_source', '_system_source')


def snapshot_expression_context(panel, records):
    from .expression_measures_panel import ExpressionMeasuresPanel
    from .symbolic_fourier_panel import SymbolicFourierPanel
    from .transform_lab import TransformLab

    if isinstance(panel, TransformLab):
        references = {}
        for name in TRANSFORM_SOURCES:
            source = getattr(panel, name, None)
            if source and source[0] == panel.expression.text():
                references[name] = source[1] if source[1] in records else None
        if references:
            return {'references': references, 'conditions': list(getattr(panel, '_library_conditions', ()))
                    if '_library_source' in references else []}
    if isinstance(panel, (ExpressionMeasuresPanel, SymbolicFourierPanel)):
        source = panel._expression_origin
        if not source or source[0] != panel.expression.text():
            return None
        if isinstance(panel, ExpressionMeasuresPanel) and source[2] != panel.domain.currentIndex():
            return None
        return {'record': source[1] if source[1] in records else None,
                'conditions': list(panel._input_conditions),
                'frequency_condition': getattr(panel, '_frequency_condition', 'True'),
                'frequency_origin': getattr(panel, '_frequency_origin', None)}
    return None


def restore_expression_context(panel, context, project):
    from .expression_measures_panel import ExpressionMeasuresPanel
    from .symbolic_fourier_panel import SymbolicFourierPanel
    from .transform_lab import TransformLab

    if not isinstance(context, dict) or not isinstance(context.get('conditions'), list):
        raise ValueError('La sesión contiene condiciones de expresión inválidas.')
    conditions = tuple(context['conditions'])
    if not all(isinstance(item,str) for item in conditions):
        raise ValueError('Las condiciones guardadas deben ser expresiones de texto.')

    def checked_key(key):
        if key is not None:
            if not isinstance(key,str):
                raise ValueError('La procedencia de la expresión es inválida.')
            project.describe(key)
        return key

    if isinstance(panel, TransformLab) and set(context) == {'references','conditions'}:
        refs = context['references']
        if not isinstance(refs,dict) or not refs.keys() <= set(TRANSFORM_SOURCES):
            raise ValueError('Las referencias de la transformada son inválidas.')
        for name, key in refs.items():
            setattr(panel, name, (panel.expression.text(), checked_key(key)))
        panel._library_conditions = conditions
        return
    if (isinstance(panel, (ExpressionMeasuresPanel, SymbolicFourierPanel))
            and set(context) == {'record','conditions','frequency_condition','frequency_origin'}
            and isinstance(context['frequency_condition'], str)
            and (context['frequency_origin'] is None or isinstance(context['frequency_origin'],str))):
        source = (panel.expression.text(), checked_key(context['record']))
        if isinstance(panel, ExpressionMeasuresPanel):
            source += (panel.domain.currentIndex(),)
        else:
            panel._frequency_condition = context['frequency_condition']
            panel._frequency_origin = context['frequency_origin']
        panel._expression_origin = source
        panel._input_conditions = conditions
        panel.refresh_origin()
        return
    raise ValueError('Las condiciones de la sesión no corresponden a la herramienta.')


def restore_table(panel, table, parent_id, project):
    base = {'signal','pending','offset'}
    if (not isinstance(panel, SignalEditorPanel) or not isinstance(table, dict)
            or not base <= table.keys() <= base | {'edits'}
            or type(table['pending']) is not bool or type(table['offset']) is not int):
        raise ValueError('El borrador de la tabla no corresponde a este editor.')
    current, _ = source_value(table['signal'], project, 'signal')
    if (current.domain not in ('discrete','continuous') or not 0 <= table['offset'] < current.values.size
            or table['offset'] % panel.page_size):
        raise ValueError('El borrador no contiene una página válida de muestras.')
    if 'edits' not in table and table['pending']:
        # Legacy drafts did not distinguish sample edits from field edits.
        current = current.copy_with(expression='', metadata=edited_metadata(current))
    edits = table.get('edits', [])
    if not isinstance(edits, list) or (edits and not table['pending']):
        raise ValueError('El borrador contiene ediciones de muestras inválidas.')
    originals = {}
    for row in edits:
        if (not isinstance(row, list) or len(row) != 3 or type(row[0]) is not int
                or not 0 <= row[0] < len(current.values) or row[0] in originals
                or any(type(part) not in (int,float) or not math.isfinite(part) for part in row[1:])):
            raise ValueError('El borrador contiene una fila editada inválida.')
        index, real, imag = row
        originals[index] = complex(real, imag)
        if originals[index] == current.values[index]:
            raise ValueError('La fila guardada no difiere de la muestra original.')
    panel._prepare_source(current)
    panel._open_source(current, parent_id)
    panel.offset = table['offset']
    for index, original in originals.items():
        panel.history.baseline[index] = original
    panel.changed_rows = set(originals)


def restore_page(page, saved, project):
    known = {'fields','source','system','formula_context','table','expression_context',
             'context_system',*PARENT_FIELDS}
    if not isinstance(saved, dict) or not saved.keys() <= known or 'fields' not in saved:
        raise ValueError('La herramienta tiene datos de sesión incompatibles.')
    panel = getattr(page, 'panel', page)
    if 'table' in saved:
        restore_table(panel, saved['table'], saved.get('parent_id'), project)
        panel._setting_fields = True
        try:
            restore_fields(panel, saved['fields'], project)
        finally:
            panel._setting_fields = False
        panel.history.last_fields = {key: getattr(panel,key).text() for key in panel.history.fields}
        panel.pending = saved['table']['pending']
        panel.render()
    else:
        restore_fields(panel, saved['fields'], project)
    if 'source' in saved:
        if page.context is None or not isinstance(page.context.source, LocalInput):
            raise ValueError('La entrada de la sesión no existe en esta herramienta.')
        restore(page.context.source, saved['source'], project)
    if 'context_system' in saved:
        key = saved['context_system']
        if page.context is None or not isinstance(key,str) or project.describe(key)['kind'] != 'system':
            raise ValueError('La transferencia referenciada no existe en esta herramienta.')
        page.context.system_id = key
    for name in PARENT_FIELDS:
        if name in saved:
            if not hasattr(panel, name) or not isinstance(saved[name], str):
                raise ValueError('La procedencia guardada no corresponde a esta herramienta.')
            project.describe(saved[name])
            setattr(panel, name, saved[name])
    if 'system' in saved:
        from .system_clock import selected_domain, signature
        from .systems_panel import SystemsPanel
        system, _ = source_value(saved['system'], project, 'system')
        fields = signature(panel)
        if system.domain != selected_domain(panel):
            raise ValueError('El sistema guardado no coincide con el dominio de su editor.')
        panel._preserved_system = system
        panel._preserved_definition = (fields[1], fields[2], fields[0])
        panel._preserved_formula = (fields[4], fields[0]) if fields[3] == 1 else None
        panel._clock_signature, panel._clock_period = fields, system.sample_period_s
        if isinstance(panel, SystemsPanel):
            panel.system = system
    if 'formula_context' in saved:
        record, _ = source_value(saved['formula_context'], project, 'calculation')
        panel._formula_context = record
        panel._formula_context_signature = (panel.transfer_formula.text(), panel.domain.currentIndex())
    if 'expression_context' in saved:
        restore_expression_context(panel, saved['expression_context'], project)
