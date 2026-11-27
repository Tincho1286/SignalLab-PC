"""Register a model and its sampled records in one verified transaction."""

from .execution import ExecutionContext
from .operation_provenance import settings_digest


def store_batch(project, document, records, execution, *, title, operation, tool):
    context = execution or ExecutionContext()
    settings = settings_digest(document)
    digest = settings_digest(['calculation', document])
    with project.stage_records(before_commit=context.checkpoint) as staged:
        model = staged.add(document, title=title, operation=operation,
                           tool=tool, verification=(digest, (), context.checkpoint))
        ids = []
        for record in records:
            source = getattr(record, '_realization_digest', None)
            if not source or record.metadata.get('settings_sha256') != settings:
                raise ValueError('La realización carece de procedencia válida para este modelo.')
            ids.append(staged.add(record, operation='Generar realización', parents=(model,), tool=tool,
                                  verification=(source, (digest,), context.checkpoint)))
        if not ids:
            raise ValueError('Se requiere al menos una realización.')
    return model, ids
