"""Session commands and periodic recovery for the production workbench."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

from PySide6.QtCore import QLockFile, QObject, QStandardPaths, QTimer
from PySide6.QtWidgets import QFileDialog, QMessageBox

from . import session
from .cas_reference import CAS_ROUTE
from .execution import ExecutionContext
from .jobs import OperationCancelled
from .problem_document import document_route
from .session_fields import restore_page, snapshot_page
from .tool_catalog import AREA_BY_ID, locate, normalized_key
from .toolbox import LocalInput, ToolPage
from .workspaces import ROUTES

_JSON_SESSION = 'Sesión SignalLab (*.json)'
_BINARY_SESSION = 'Proyecto científico SignalLab (*.slproj)'
_SESSION_FILTERS = _JSON_SESSION + ';;' + _BINARY_SESSION


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
            tab = ['cas', 'worksheet']
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
    workspace = dict(tools=[dict(route=list(key), inputs=state) for key,state in tools.items()],
                     tabs=tabs, active=active)
    if CAS_ROUTE in window.pages:
        workspace['cas'] = window.pages[CAS_ROUTE].session_snapshot()
    return workspace


def _route(key):
    if (not isinstance(key, list) or len(key) != 2 or not isinstance(key[0], str)
            or type(key[1]) not in (str, int) or tuple(key) not in ROUTES
            or locate(ROUTES[tuple(key)]) is None):
        raise ValueError('La sesión contiene una herramienta desconocida.')
    return ROUTES[tuple(key)]


def _tab_keys(tabs, pages, has_cas):
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
        elif tab == ['cas', 'worksheet'] and has_cas:
            key = CAS_ROUTE
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
        _tab_keys(state['tabs'], pages, 'cas' in state)
    except (KeyError, TypeError, IndexError, AttributeError, ArithmeticError) as exc:
        for page in pages.values():
            page.deleteLater()
        raise ValueError('Una entrada de la sesión tiene datos o referencias inválidos.') from exc
    except Exception:
        for page in pages.values():
            page.deleteLater()
        raise
    return pages


def restore(window, project, state, pages, worksheet):
    # Keep the navigation widget and make all previous result panes unreachable.
    window.show_home()
    window.documents.blockSignals(True)
    while window.documents.count():
        window.documents.removeTab(0)
    window.documents.blockSignals(False)
    window.variant_strip.reset()
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
    if worksheet is not None:
        window.ensure_cas().restore_session(worksheet)
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
        elif tab[0] == 'cas':
            window.open_cas()
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
        self.path = self.directory / 'recovery.slproj' if self.directory is not None else None
        self.legacy_path = self.directory / 'recovery.signallab.json' if self.directory is not None else None
        self.lock = QLockFile(str(self.directory / 'recovery.lock')) if self.directory is not None else None
        if self.lock is not None:
            self.lock.setStaleLockTime(0)
        self.protected = self.recovery_path() is not None
        self.owns_checkpoint = False
        self.recovered_legacy = False
        self.saved = capture(window)
        self.checkpoint = None
        self.generation = 0
        self.recovery_error = None
        self.writer = ThreadPoolExecutor(max_workers=1, thread_name_prefix='signallab-recovery')
        self.writing = None
        self.closing = False
        self.writer_timer = QTimer(self)
        self.writer_timer.setInterval(50)
        self.writer_timer.timeout.connect(self.collect_checkpoint)
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

    def recovery_path(self):
        return next((path for path in (self.path, self.legacy_path)
                     if path is not None and path.is_file()), None)

    def changed(self):
        return self.window.project.dirty or capture(self.window) != self.saved

    def save_dialog(self):
        path, selected = QFileDialog.getSaveFileName(self.window, 'Guardar sesión completa',
                                                      'sesion.signallab.json', _SESSION_FILTERS)
        if not path or self.busy():
            return False
        if selected == _BINARY_SESSION and Path(path).suffix.lower() != '.slproj':
            path = str(Path(path).with_suffix('.slproj'))
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
        return 'La hoja CAS, sus variables y el borrador se guardan con la sesión. Los gráficos abiertos se pueden volver a generar desde sus herramientas.'

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
        path, _ = QFileDialog.getOpenFileName(self.window, 'Abrir sesión completa', '', _SESSION_FILTERS)
        if path:
            self.open_path(path)

    def open_path(self, path, *, recovery=False):
        if self.busy():
            return False
        try:
            project, workspace = session.load(path)
            from .cas_worksheet import prepare as prepare_cas
            worksheet = prepare_cas(workspace['cas'], project) if 'cas' in workspace else None
            pages = prepare(self.window, project, workspace)
            if not self.can_replace():
                for page in pages.values():
                    page.deleteLater()
                return False
            restore(self.window, project, workspace, pages, worksheet)
        except (OSError, ValueError, TypeError, MemoryError, RecursionError) as exc:
            QMessageBox.warning(self.window, 'No se pudo abrir la sesión', str(exc))
            return False
        self.saved = capture(self.window)
        project.dirty = recovery
        self.generation += 1
        if self.writing is not None:
            self.writing[2].set()
        self.checkpoint = None
        if recovery:
            self.protected = False
            self.owns_checkpoint = True
            self.recovered_legacy = Path(path) == self.legacy_path
        verb = 'Recuperaste' if recovery else 'Abriste'
        records = len(project.headers())
        tools = len(workspace['tools'])
        message = f'{verb} {records} objetos de la biblioteca y las entradas compatibles de {tools} herramientas. '+self.scope()
        self.window.statusBar().showMessage(message)
        if recovery:
            QMessageBox.information(self.window, 'Sesión recuperada', message)
        return True

    def offer_recovery(self):
        if self.writing is not None:
            self.window.statusBar().showMessage('Esperá a que termine el guardado de recuperación.')
            return
        try:
            path = self.recovery_path()
            if path is None:
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
                self.open_path(path, recovery=True)
            elif answer == QMessageBox.StandardButton.Discard:
                for target in (self.path, self.legacy_path):
                    target.unlink(missing_ok=True)
                self.protected = False
        except OSError as exc:
            self.window.statusBar().showMessage('No se pudo abrir la recuperación. '+str(exc))

    def autosave(self):
        if self.protected or self.writing is not None or self.window._workers or not self.window.isVisible():
            return
        try:
            current = capture(self.window)
            project = self.window.project
            key = (self.generation, len(project._stable_records()), current)
            if key == self.checkpoint or (not project.dirty and current == self.saved):
                return
            if self.take_lock():
                if self.recovery_path() is not None and not self.owns_checkpoint:
                    self.protected = True
                    self.window.statusBar().showMessage('Hay una sesión anterior disponible en Archivo → Sesiones → Recuperar sesión anterior.')
                    return
                cancel = Event()
                execution = ExecutionContext(cancel=cancel)
                future = self.writer.submit(session.save, self.path, project.snapshot(), current,
                                            checkpoint=execution.checkpoint)
                self.writing = future, key, cancel
                self.writer_timer.start()
        except (ValueError, OSError, TypeError, MemoryError, RecursionError) as exc:
            self.report_recovery_error(exc)

    def report_recovery_error(self, exc):
        message = 'No se pudo actualizar la recuperación local. '+str(exc)
        if message != self.recovery_error:
            self.recovery_error = message
            self.window.statusBar().showMessage(message)

    def collect_checkpoint(self):
        future, key, _ = self.writing
        if not future.done():
            return
        self.writing = None
        self.writer_timer.stop()
        try:
            future.result()
        except OperationCancelled:
            pass
        except (ValueError, OSError, TypeError, MemoryError, RecursionError) as exc:
            self.report_recovery_error(exc)
        else:
            self.owns_checkpoint = True
            self.checkpoint = key
            self.recovery_error = None
        if self.closing:
            self.closing = False
            QTimer.singleShot(0, self.window, self.window.close)

    def prepare_close(self):
        if self.writing is None:
            return True
        self.closing = True
        self.writing[2].set()
        self.window.statusBar().showMessage('Terminando el guardado de recuperación antes de cerrar…')
        return False

    def finish(self):
        self.timer.stop()
        self.writer_timer.stop()
        self.writer.shutdown(wait=False)
        if self.lock is not None and self.lock.isLocked():
            try:
                if not self.protected and self.owns_checkpoint:
                    self.path.unlink(missing_ok=True)
                    if self.recovered_legacy:
                        self.legacy_path.unlink(missing_ok=True)
            except OSError as exc:
                QMessageBox.warning(self.window, 'Recuperación local', 'El punto anterior sigue disponible. '+str(exc))
            finally:
                self.lock.unlock()
