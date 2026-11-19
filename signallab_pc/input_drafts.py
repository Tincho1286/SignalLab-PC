"""Swap complete input drafts without evaluating them or losing loaded references."""
from copy import copy


def capture(field):
    return dict(text={name:getattr(field,name).text() for name in ('expression','samples','origin','count','step')},mode=field.mode.currentIndex(),view=field.entry_modes.view,
                attributes={name:copy(getattr(field,name)) for name in ('loaded','loaded_reference_id','reference_id','fingerprint','_expression_origin','_expression_conditions','_expression_frequency_condition') if hasattr(field,name)},
                note=(field.file_note.text(),field.file_note.objectName()),external_sources=copy(field._external_sources))


def restore(field,draft):
    for name,value in draft['text'].items():getattr(field,name).setText(value)
    for name in ('loaded','loaded_reference_id','reference_id','fingerprint','_expression_origin','_expression_conditions','_expression_frequency_condition'):
        if name in draft['attributes']:setattr(field,name,draft['attributes'][name])
        elif hasattr(field,name):delattr(field,name)
    field.file_note.setText(draft['note'][0]);field.file_note.setObjectName(draft['note'][1]);field.file_note.style().unpolish(field.file_note);field.file_note.style().polish(field.file_note)
    field._restoring_source=True
    try:field.mode.setCurrentIndex(draft['mode']);field.entry_modes.select(draft['view'])
    finally:field._restoring_source=False
    field._source_view=draft['view'];field._external_sources=copy(draft.get('external_sources',{}));field.remember_external_source();field.refresh_source_note();field.refresh_recent();field.source_revision=getattr(field,'source_revision',0)+1;field.sourceChanged.emit()


def swap(first,second):
    if first.kind!=second.kind:raise ValueError('Las entradas deben usar el mismo dominio.')
    left,right=capture(first),capture(second);restore(first,right);restore(second,left)
