"""Atomic Linux per-user installations. User settings live outside this tree."""
from pathlib import Path
import json
import os
import re
import shutil
import tempfile
import uuid
from .installations import MARKER, receipt, read_receipt
from .update_manifest import UpdateError, version_tuple
from .update_download import file_hash


def default_root():
    return Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))) / 'SignalLab-PC'


def checked_root(root, home=None):
    home = Path(home or Path.home()).resolve()
    root = Path(root).absolute()
    if any(value.is_symlink() for value in (root, *root.parents)) or not root.resolve().is_relative_to(home) or root.resolve() == home:
        raise UpdateError('La instalación debe estar en una carpeta propia del usuario, sin enlaces simbólicos en su ruta.')
    if root.exists() and any(root.iterdir()):
        row = read_receipt(root)
        if row.get('layout') != 'linux-user-v1':
            raise UpdateError('La carpeta pertenece a otra instalación.')
    return root


def atomic_text(path, content):
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('x', encoding='utf-8') as target:
            target.write(content); target.flush(); os.fsync(target.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_link(path, target):
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temporary.symlink_to(target)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _managed_version(path, root):
    if path.is_symlink() or path.parent != root / 'versions' or not re.fullmatch(r'\d+\.\d+\.\d+-[a-f0-9]{12}', path.name):
        raise UpdateError('Ruta de versión no administrada por SignalLab.')
    row = read_receipt(path)
    if row.get('layout') != 'linux-user-v1':
        raise UpdateError('Carpeta de versión no reconocida.')
    return row


def _entry_path(path):
    # Desktop Entry Exec is not a shell command. Percent signs are field codes.
    value = str(path)
    if any(ord(c) < 32 for c in value):
        raise UpdateError('La ruta de instalación contiene caracteres no admitidos.')
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%') + '"'


def integrate(root, *, home=None, data_home=None):
    home = Path(home or Path.home())
    data = Path(data_home or os.environ.get('XDG_DATA_HOME', str(home / '.local/share')))
    applications = data / 'applications'; applications.mkdir(parents=True, exist_ok=True)
    binary = root / 'current' / 'SignalLab-PC'
    launcher = home / '.local/bin/signallab-pc'; launcher.parent.mkdir(parents=True, exist_ok=True)
    if launcher.exists() or launcher.is_symlink():
        if not launcher.is_symlink() or os.readlink(launcher) != str(binary):
            raise UpdateError('Ya existe otro archivo en ~/.local/bin/signallab-pc. No se reemplazó.')
    desktop = applications / 'org.signallab.PC.desktop'
    if desktop.exists() and 'X-SignalLab-Managed=true' not in desktop.read_text(encoding='utf-8'):
        raise UpdateError('El acceso del menú pertenece a otra instalación.')
    previous_launcher = os.readlink(launcher) if launcher.is_symlink() else None
    previous_desktop = desktop.read_text(encoding='utf-8') if desktop.is_file() else None
    content = '[Desktop Entry]\nType=Application\nName=SignalLab PC\nComment=Laboratorio de señales y sistemas\n'
    content += 'Exec=' + _entry_path(binary) + '\nIcon=' + str(root / 'current' / 'signallab.svg') + '\n'
    content += 'Terminal=false\nCategories=Education;Science;Math;\nStartupNotify=true\nX-SignalLab-Managed=true\nActions=Uninstall;\n'
    content += '\n[Desktop Action Uninstall]\nName=Desinstalar SignalLab PC\nExec=' + _entry_path(binary) + ' --install-linux --uninstall --target ' + _entry_path(root) + '\n'

    def undo():
        if previous_launcher is None:
            if launcher.is_symlink() and os.readlink(launcher) == str(binary):
                launcher.unlink()
        else:
            atomic_link(launcher, previous_launcher)
        if previous_desktop is None:
            if desktop.is_file() and 'X-SignalLab-Managed=true' in desktop.read_text(encoding='utf-8'):
                desktop.unlink()
        else:
            atomic_text(desktop, previous_desktop)
    try:
        atomic_link(launcher, binary); atomic_text(desktop, content)
    except Exception:
        try:
            undo()
        except OSError:
            pass
        raise
    return undo


def install(source, root, version, *, home=None, data_home=None, activate=None):
    """Stage a complete version before atomically changing the active link."""
    if os.name != 'posix':
        raise UpdateError('Este instalador corresponde a Linux.')
    source = Path(source).resolve(); root = checked_root(root, home)
    if source == root.resolve() or source.is_relative_to(root.resolve()) or root.resolve().is_relative_to(source):
        raise UpdateError('La carpeta de origen y la instalación deben estar separadas.')
    version_tuple(version)
    previous_marker = (root / MARKER).read_text(encoding='utf-8') if (root / MARKER).is_file() else None
    previous_link = os.readlink(root / 'previous') if (root / 'previous').is_symlink() else None
    binary = source / 'SignalLab-PC'
    if binary.is_symlink() or not binary.is_file():
        raise UpdateError('Falta el ejecutable Linux del paquete.')
    with binary.open('rb') as stream:
        header = stream.read(20)
    if len(header) < 20 or header[:6] != b'\x7fELF\x02\x01' or int.from_bytes(header[18:20], 'little') != 62:
        raise UpdateError('El paquete no contiene un ejecutable Linux x86_64.')
    old = None
    if (root / 'current').is_symlink():
        old = (root / 'current').resolve(); row = _managed_version(old, root)
        if version_tuple(version) < version_tuple(row['version']):
            raise UpdateError('No se permite instalar una versión anterior sobre la actual.')
    elif (root / 'current').exists():
        raise UpdateError('La ruta activa no es un enlace administrado.')
    files = []
    for path in source.rglob('*'):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise UpdateError('El paquete contiene enlaces o archivos especiales no permitidos.')
        if path.is_file():
            if path.name == MARKER:
                raise UpdateError('El paquete contiene datos de instalación inesperados.')
            files.append(path)
    if len(files) > 10000 or sum(p.stat().st_size for p in files) > 2 * 1024**3:
        raise UpdateError('El paquete supera los límites de instalación.')
    # Validate the desktop path before activating a version.
    _entry_path(root)
    root.mkdir(parents=True, exist_ok=True); versions = root / 'versions'; versions.mkdir(exist_ok=True)
    if versions.is_symlink():
        raise UpdateError('La carpeta de versiones no puede ser un enlace.')
    name = version + '-' + file_hash(binary)[:12]; destination = versions / name
    pending = Path(tempfile.mkdtemp(prefix='.pending-', dir=versions))
    try:
        for path in files:
            target = pending / path.relative_to(source); target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        (pending / 'SignalLab-PC').chmod(0o755)
        marker = receipt(version, 'linux-x86_64', 'linux-user-v1')
        atomic_text(pending / MARKER, json.dumps(marker, indent=2) + '\n')
        if destination.exists():
            _managed_version(destination, root)
            if file_hash(destination / 'SignalLab-PC') != file_hash(binary):
                raise UpdateError('La carpeta de destino contiene otra compilación.')
        else:
            pending.replace(destination)
        undo = None
        try:
            atomic_text(root / MARKER, json.dumps(marker, indent=2) + '\n')
            undo = integrate(root, home=home, data_home=data_home)
            if old is not None and old != destination:
                atomic_link(root / 'previous', old.relative_to(root))
            (activate or atomic_link)(root / 'current', destination.relative_to(root))
        except Exception:
            if undo is not None:
                undo()
            if previous_marker is not None:
                atomic_text(root / MARKER, previous_marker)
            if previous_link is not None:
                atomic_link(root / 'previous', previous_link)
            elif (root / 'previous').is_symlink():
                (root / 'previous').unlink()
            raise
        previous = (root / 'previous').resolve() if (root / 'previous').is_symlink() else None
        for path in versions.iterdir():
            if path in (destination, old, previous):
                continue
            try:
                _managed_version(path, root)
                shutil.rmtree(path)
            except (OSError, UpdateError):
                pass  # Cleanup cannot invalidate a successfully activated release.
        return destination / 'SignalLab-PC'
    finally:
        # Only this invocation's private staging directory can be removed.
        if pending.exists() and pending.parent.resolve() == versions.resolve() and pending.name.startswith('.pending-') and not pending.is_symlink():
            shutil.rmtree(pending)


def uninstall(root, *, home=None, data_home=None):
    root = checked_root(root, home)
    home = Path(home or Path.home())
    data = Path(data_home or os.environ.get('XDG_DATA_HOME', str(home / '.local/share')))
    launcher = home / '.local/bin/signallab-pc'
    if launcher.is_symlink() and os.readlink(launcher) == str(root / 'current/SignalLab-PC'):
        launcher.unlink()
    desktop = data / 'applications/org.signallab.PC.desktop'
    if desktop.is_file() and not desktop.is_symlink():
        text = desktop.read_text(encoding='utf-8')
        if 'X-SignalLab-Managed=true' in text and _entry_path(root / 'current/SignalLab-PC') in text:
            desktop.unlink()
    versions = root / 'versions'
    if versions.is_symlink():
        raise UpdateError('Carpeta de versiones inválida.')
    if versions.is_dir():
        for path in versions.iterdir():
            try:
                _managed_version(path, root)
            except UpdateError:
                continue
            shutil.rmtree(path)
        if not any(versions.iterdir()):
            versions.rmdir()
    for name in ('current', 'previous'):
        path = root / name
        if path.is_symlink():
            path.unlink()
    if set(p.name for p in root.iterdir()) <= {MARKER}:
        (root / MARKER).unlink()
    # Preserve any user-created, unrecognized files rather than delete them.
    if not any(root.iterdir()):
        root.rmdir()
