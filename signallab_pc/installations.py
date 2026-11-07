"""Per-user installation detection and handoff to verified installers."""
from dataclasses import dataclass
from pathlib import Path
import json
import os
import platform
import subprocess
import sys
from .update_manifest import UpdateError, version_tuple
from .update_download import verify_file
from .process_handoff import launch_independent

INSTALL_ID = '91b68a45-9170-44b7-b40b-a171bde5938d'
MARKER = 'signallab-installation.json'


def platform_tag():
    if platform.machine().lower() not in ('x86_64', 'amd64'):
        return None
    return {'win32': 'windows-x86_64', 'linux': 'linux-x86_64'}.get(sys.platform)


def receipt(version, target, layout, **extra):
    version_tuple(version)
    return dict(schema=1, application='SignalLab PC', install_id=INSTALL_ID,
                version=version, platform=target, layout=layout, **extra)


def read_receipt(folder):
    path = Path(folder) / MARKER
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 65536:
        raise UpdateError('No se reconoce esta instalación de SignalLab.')
    try:
        row = json.loads(path.read_text(encoding='utf-8-sig'))
        if row['schema'] != 1 or row['install_id'] != INSTALL_ID or row['application'] != 'SignalLab PC':
            raise ValueError('identity')
        version_tuple(row['version'])
        return row
    except (ValueError, KeyError, TypeError) as exc:
        raise UpdateError('Los datos de instalación no son válidos.') from exc


@dataclass(frozen=True)
class Installation:
    root: Path
    platform: str
    version: str
    executable: Path


def installed(*, executable=None, frozen=None):
    if not (getattr(sys, 'frozen', False) if frozen is None else frozen):
        return None
    executable = Path(executable or sys.executable).resolve()
    try:
        row = read_receipt(executable.parent)
        if row['layout'] == 'windows-user-v1' and row['platform'] == 'windows-x86_64' and executable.name == 'SignalLab-PC.exe':
            return Installation(executable.parent, row['platform'], row['version'], executable)
        if row['layout'] == 'linux-user-v1' and row['platform'] == 'linux-x86_64' and executable.name == 'SignalLab-PC':
            root = executable.parent.parent.parent
            root_row = read_receipt(root)
            if executable.parent.parent.name != 'versions' or root_row.get('layout') != 'linux-user-v1':
                return None
            if (root / 'current').resolve() != executable.parent:
                return None
            return Installation(root, row['platform'], row['version'], executable)
    except (OSError, UpdateError, KeyError, RuntimeError):
        pass
    return None


def start_update(asset, path, installation, *, launch=subprocess.Popen):
    if installation is None or asset.platform != installation.platform:
        raise UpdateError('La instalación automática sólo está disponible en la edición instalada correspondiente.')
    current_executable = installation.root / ('SignalLab-PC.exe' if installation.platform == 'windows-x86_64' else 'current/SignalLab-PC')
    current = installed(executable=current_executable, frozen=True)
    if current is None or current.root != installation.root or current.platform != installation.platform:
        raise UpdateError('La instalación cambió desde que se abrió SignalLab. Revisá su carpeta antes de actualizar.')
    if version_tuple(asset.version) <= version_tuple(current.version):
        raise UpdateError('Ya hay una versión igual o más nueva instalada. No se reemplazará por esta descarga.')
    verify_file(path, asset)
    if installation.platform == 'windows-x86_64':
        command = [str(path), '/SP-', '/SILENT', '/NORESTART', '/NOCLOSEAPPLICATIONS',
                   '/SIGNALLABPARENTPID=' + str(os.getpid()), '/DIR=' + str(installation.root)]
        return launch_independent(command, launch=launch, close_fds=True)
    if installation.platform == 'linux-x86_64':
        command = ['/bin/sh', str(path), '--update', str(os.getpid()), '--target', str(installation.root)]
        return launch_independent(command, launch=launch, start_new_session=True, stdin=subprocess.DEVNULL,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    raise UpdateError('No hay instalador para esta plataforma.')
