"""Versioned desktop sessions, separate from exports of project records."""
from pathlib import Path

from .atomic_file import write_json
from .project import Project, read_document


def save(path, project, workspace, *, before_commit=None):
    document = dict(format='signallab-session', schema_version=3,
                    project=project.document(), workspace=workspace)
    write_json(Path(path), document, before_commit=before_commit)


def load(path):
    document = read_document(path)
    if isinstance(document, dict) and document.get('format') == 'signallab-project':
        return Project.from_document(document), empty_workspace()
    if (not isinstance(document, dict) or document.get('format') != 'signallab-session'
            or type(document.get('schema_version')) is not int or document['schema_version'] not in (1,2,3)):
        raise ValueError('Formato o versión de sesión SignalLab incompatible.')
    project = Project.from_document(document.get('project'))
    workspace = document.get('workspace')
    if not isinstance(workspace, dict) or set(workspace) != {'tools', 'tabs', 'active'}:
        raise ValueError('El archivo no contiene un escritorio válido.')
    if not isinstance(workspace['tools'], list) or not isinstance(workspace['tabs'], list):
        raise ValueError('Las herramientas y pestañas de la sesión deben ser listas.')
    active = workspace['active']
    if type(active) is not int or not -1 <= active < len(workspace['tabs']):
        raise ValueError('La pestaña activa de la sesión no existe.')
    return project, workspace


def empty_workspace():
    return dict(tools=[], tabs=[], active=-1)
