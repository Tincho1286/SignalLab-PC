"""Version namespaces for publishing SignalLab LTS and engineering previews."""

LTS_BASE = '2.0.0'
LTS_FAMILY = (2, 0)
PREVIEW_MINIMUM = (2, 1, 0)


def publication_version(version, channel):
    from .update_manifest import version_tuple
    numeric = version_tuple(version)
    if channel == 'stable':
        if numeric[:2] != LTS_FAMILY:
            raise ValueError('El canal estable está reservado para el mantenimiento LTS 2.0.x.')
    elif channel == 'preview':
        if numeric < PREVIEW_MINIMUM:
            raise ValueError('Las preliminares de Engineering usan versiones 2.1.0 o superiores.')
    else:
        raise ValueError('Seleccioná el canal stable o preview.')
    return numeric
