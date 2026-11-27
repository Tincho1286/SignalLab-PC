"""Atomic registration of a statistical report and its input records."""

from .execution import ExecutionContext
from .operation_provenance import settings_digest


def store_statistics(project, result, inputs, operation, *, execution=None, tool=None):
    context = execution or ExecutionContext()
    checksums = (result['input_sha256'],) if 'input_sha256' in result else tuple(result['input_hashes'])
    report_digest = settings_digest(['calculation', result])
    keys = []
    with project.stage_records(before_commit=context.checkpoint) as staged:
        for (source, key, origins), checksum in zip(inputs, checksums, strict=True):
            if key is None:
                # The report still verifies the contents of a draft loaded from a formula.
                proof = None if origins else (checksum, (), context.checkpoint)
                key = staged.add(source, operation='Entrada estadística', parents=origins,
                                 tool=tool, verification=proof)
            keys.append(key)
        record = staged.add(result, title=operation + ' · ' + inputs[0][0].name,
                            operation=operation, parents=keys, tool=tool,
                            verification=(report_digest, checksums, context.checkpoint))
    return keys, record
