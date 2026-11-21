"""Session commands and periodic recovery for the production workbench."""
from pathlib import Path

from PySide6.QtCore import QLockFile, QObject, QStandardPaths, QTimer
from PySide6.QtWidgets import QFileDialog, QMessageBox

from . import session
from .cas_reference import CAS_ROUTE
from .problem_document import document_route
from .session_fields import restore_page, snapshot_page
from .tool_catalog import AREA_BY_ID, locate, normalized_key
from .toolbox import LocalInput, ToolPage
from .workspaces import ROUTES


def capture(window):
    records = {record['id'] for record in window.project.headers()}
    tools = {}
    for page in window.pages.values():
        if isinstance(page, ToolPage):
            route = normalized_key(page.tool_item)
            if route not in tools:
                tools[route] = snapshot_page(page, records)
    tabs = []
    active = -1
    for index in range(window.documents.count()):
        key = window.documents.tabData(index)
        if key == ('browser',):
            tab = ['browser', window._browser_location]
        elif key == CAS_ROUTE:
            continue
        elif key[0] == 'menu':
            tab = list(key)
        elif key[1] == 'workspace':
            route = normalized_key(window.pages[key].current_route)
            tab = ['tool', *route]
        else:
            continue
        if index == window.documents.currentIndex():
            active = len(tabs)
        tabs.append(tab)
    return dict(tools=[dict(route=list(key), inputs=state) for key,state in tools.items()],
                tabs=tabs, active=active)


def _route(key):
    if (not isinstance(key, list) or len(key) != 2 or not isinstance(key[0], str)
            or type(key[1]) not in (str, int) or tuple(key) not in ROUTES
            or locate(ROUTES[tuple(key)]) is None):
        raise ValueError('La sesión contiene una herramienta desconocida.')
    return ROUTES[tuple(key)]


def _tab_keys(tabs, pages):
    keys = set()
    for tab in tabs:
        if not isinstance(tab, list) or len(tab) < 2:
            raise ValueError('Hay una pestaña inválida en la sesión.')
        if tab[0] == 'tool':
            route = _route(tab[1:])
            if route not in pages:
                raise ValueError('Una pestaña referencia una herramienta ausente.')
            key = document_route(locate(route))
        elif tab[0] == 'browser' and len(tab) == 2 and (tab[1] is None or isinstance(tab[1], str) and tab[1] in AREA_BY_ID):
            key = ('browser',)
        elif tab in (['menu','Proyecto'], ['menu','Biblioteca']):
            key = tuple(tab)
        else:
            raise ValueError('La sesión contiene una pestaña desconocida.')
        if key in keys:
            raise ValueError('La sesión contiene pestañas repetidas.')
        keys.add(key)


def prepare(window, project, state):
    """Prepare disconnected pages before touching the active session."""
    pages = {}
    try:
        for tool in state['tools']:
            if not isinstance(tool, dict) or set(tool) != {'route','inputs'}:
                raise ValueError('La definición de una herramienta está incompleta.')
            route = _route(tool['route'])
            if route in pages:
                raise ValueError('Una herramienta está repetida en el archivo.')
            page = ToolPage(window, route)
            pages[route] = page
            restore_page(page, tool['inputs'], project)
        _tab_keys(state['tabs'], pages)
    except (KeyError, TypeError, IndexError, AttributeError, ArithmeticError) as exc:
        for page in pages.values():
            page.deleteLater()
        raise ValueError('Una entrada de la sesión tiene datos o referencias inválidos.') from exc
    except Exception:
        for page in pages.values():
            page.deleteLater()
        raise
    return pages


def restore(window, project, state, pages):
    # Keep the navigation widget and make all previous result panes unreachable.
    window.show_home()
    window.documents.blockSignals(True)
    while window.documents.count():
        window.documents.removeTab(0)
    window.documents.blockSignals(False)
    window.variant_strip.setParent(window.centralWidget())
    window.variant_strip.memory.clear()
    auxiliary = {key: page for key, page in window.pages.items() if key[0] == 'menu'}
    for key, view in list(window.views.items()):
        if key not in auxiliary:
            window.stack.removeWidget(view)
            view.deleteLater()
            del window.views[key]
    for page in {page for page in window.pages.values() if isinstance(page, ToolPage) and page.parent() is None}:
        page.deleteLater()
    window.pages = {('browser',): window.pages[('browser',)], **auxiliary, **pages}
    window.project = project
    window._published_signals.clear()
    getattr(window, '_published_values', {}).clear()
    for page in pages.values():
        for field in page.findChildren(LocalInput):
            field.refresh_recent()
    for tab in state['tabs']:
        if tab[0] == 'tool':
            window.open_tool(_route(tab[1:]))
        elif tab[0] == 'menu':
            window.show_menu(tab[1])
        else:
            window.show_area(tab[1])
    if state['active'] >= 0:
        window.documents.setCurrentIndex(state['active'])
    elif not state['tabs']:
        window.show_home()
    window.refresh_project()


class SessionController(QObject):
    def __init__(self, window, directory=None):
        super().__init__(window)
        self.window = window
        base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.GenericDataLocation)
        self.directory = Path(directory) if directory is not None else (Path(base) / 'SignalLab' / 'PC' if base else None)
        self.path = self.directory / 'recovery.signallab.json' if self.directory is not None else None
        self.lock = QLockFile(str(self.directory / 'recovery.lock')) if self.directory is not None else None
        if self.lock is not None:
            self.lock.setStaleLockTime(0)
        self.protected = bool(self.path and self.path.exists())
        self.owns_checkpoint = False
        self.saved = capture(window)
        self.checkpoint = None
        self.recovery_error = None
        self.timer = QTimer(self)
        self.timer.setInterval(30_000)
        self.timer.timeout.connect(self.autosave)
        self.timer.start()
        if self.protected:
            QTimer.singleShot(0, self, self.offer_recovery)

    def take_lock(self):
        if self.lock is None:
            return False
        if self.lock.isLocked():
            return True
        self.directory.mkdir(parents=True, exist_ok=True)
        return self.lock.tryLock(0)

    def busy(self):
        if self.window._workers:
            self.window.statusBar().showMessage('Esperá a que termine el cálculo antes de cambiar de sesión.')
            return True
        return False

    def changed(self):
        return self.window.project.dirty or capture(self.window) != self.saved

    def save_dialog(self):
        path, _ = QFileDialog.getSaveFileName(self.window, 'Guardar sesión completa',
                                               'sesion.signallab.json', 'Sesión SignalLab (*.json)')
        if not path or self.busy():
            return False
        try:
            workspace = capture(self.window)
            session.save(path, self.window.project, workspace)
        except (ValueError, OSError, TypeError, MemoryError) as exc:
            QMessageBox.warning(self.window, 'No se pudo guardar la sesión', str(exc))
            return False
        self.saved = workspace
        self.window.project.dirty = False
        self.window.statusBar().showMessage('Sesión guardada con sus herramientas y resultados. '+self.scope())
        return True

    @staticmethod
    def scope():
        return 'Los informes previos quedan en Resultados. La recuperación excluye gráficos abiertos, historial del CAS y borradores de editores especiales.'

    def can_replace(self):
        if self.busy():
            return False
        if not self.changed():
            return True
        button = QMessageBox.question(
            self.window, 'Cambiar de sesión', 'Hay cambios en la sesión activa. ¿Querés guardarlos antes de abrir otra?',
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save)
        return button == QMessageBox.StandardButton.Discard or button == QMessageBox.StandardButton.Save and self.save_dialog()

    def open_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self.window, 'Abrir sesión completa', '', 'Sesión SignalLab (*.json)')
        if path:
            self.open_path(path)

    def open_path(self, path, *, recovery=False):
        if self.busy():
            return False
        try:
            project, workspace = session.load(path)
            pages = prepare(self.window, project, workspace)
            if not self.can_replace():
                for page in pages.values():
                    page.deleteLater()
                return False
            restore(self.window, project, workspace, pages)
        except (OSError, ValueError, TypeError, MemoryError, RecursionError) as exc:
            QMessageBox.warning(self.window, 'No se pudo abrir la sesión', str(exc))
            return False
        self.saved = capture(self.window)
        project.dirty = recovery
        self.checkpoint = None
        if recovery:
            self.protected = False
            self.owns_checkpoint = True
        verb = 'Recuperaste' if recovery else 'Abriste'
        records = len(project.headers())
        tools = len(workspace['tools'])
        message = f'{verb} {records} objetos de la biblioteca y las entradas compatibles de {tools} herramientas. '+self.scope()
        self.window.statusBar().showMessage(message)
        if recovery:
            QMessageBox.information(self.window, 'Sesión recuperada', message)
        return True

    def offer_recovery(self):
        try:
            if self.path is None or not self.path.exists():
                self.protected = False
                return
            if not self.take_lock():
                self.window.statusBar().showMessage('Otra instancia está usando la recuperación de sesiones.')
                return
            answer = QMessageBox.question(
                self.window, 'Sesión anterior disponible',
                '¿Querés recuperar el último punto local? «No» conserva el archivo para abrirlo más adelante.',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Discard,
                QMessageBox.StandardButton.Yes)
            if answer == QMessageBox.StandardButton.Yes:
                self.open_path(self.path, recovery=True)
            elif answer == QMessageBox.StandardButton.Discard:
                self.path.unlink(missing_ok=True)
                self.protected = False
        except OSError as exc:
            self.window.statusBar().showMessage('No se pudo abrir la recuperación. '+str(exc))

    def autosave(self):
        if self.protected or self.window._workers or not self.window.isVisible():
            return
        try:
            current = capture(self.window)
            project = self.window.project
            key = (id(project), len(project.headers()), current)
            if key == self.checkpoint or (not project.dirty and current == self.saved):
                return
            if self.take_lock():
                if self.path.exists() and not self.owns_checkpoint:
                    self.protected = True
                    self.window.statusBar().showMessage('Hay una sesión anterior disponible en Archivo → Sesiones → Recuperar sesión anterior.')
                    return
                session.save(self.path, project, current)
                self.owns_checkpoint = True
                self.checkpoint = key
                self.recovery_error = None
        except (ValueError, OSError, TypeError, MemoryError, RecursionError) as exc:
            message = 'No se pudo actualizar la recuperación local. '+str(exc)
            if message != self.recovery_error:
                self.recovery_error = message
                self.window.statusBar().showMessage(message)

    def finish(self):
        self.timer.stop()
        if self.lock is not None and self.lock.isLocked():
            try:
                if not self.protected and self.owns_checkpoint:
                    self.path.unlink(missing_ok=True)
            except OSError as exc:
                QMessageBox.warning(self.window, 'Recuperación local', 'El punto anterior sigue disponible. '+str(exc))
            finally:
                self.lock.unlock()
