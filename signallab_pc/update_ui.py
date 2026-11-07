"""Update checks and verified downloads alongside the existing Help menu."""
from pathlib import Path
from threading import Event
import sys
from PySide6.QtCore import QObject, QThread, Signal, Qt, QTimer, QStandardPaths, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QPlainTextEdit, QProgressBar, QPushButton, QMessageBox)
from . import __version__
from .installations import installed, platform_tag, start_update
from .update_download import fetch_release, download, Cancelled


class Job(QThread):
    completed = Signal(object)
    failed = Signal(str)
    progressed = Signal(object, object)

    def __init__(self, function, parent):
        super().__init__(parent); self.function = function; self.cancel = Event()

    def run(self):
        try:
            result = self.function(self.cancel, self.progressed.emit)
            if not self.cancel.is_set():
                self.completed.emit(result)
        except Cancelled:
            self.failed.emit('Operación cancelada.')
        except Exception as exc:
            from .runtime_diagnostics import diagnostic
            diagnostic(exc, context='Actualizaciones')
            self.failed.emit(str(exc))


class UpdateDialog(QDialog):
    def __init__(self, controller):
        super().__init__(controller.window); self.controller = controller
        self.setWindowTitle('Actualizaciones de SignalLab PC'); self.resize(540, 380)
        layout = QVBoxLayout(self)
        self.heading = QLabel('Versión instalada: ' + __version__); layout.addWidget(self.heading)
        self.status = QLabel('Comprobá si hay una versión estable nueva.'); self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText); layout.addWidget(self.status)
        self.notes = QPlainTextEdit(); self.notes.setReadOnly(True); layout.addWidget(self.notes, 1)
        self.automatic = QCheckBox('Comprobar actualizaciones al iniciar')
        self.automatic.setChecked(controller.installation is not None and controller.window.settings.value('updates/check_at_startup', True, type=bool))
        self.automatic.setEnabled(controller.installation is not None)
        self.automatic.toggled.connect(lambda value: controller.window.settings.setValue('updates/check_at_startup', value))
        layout.addWidget(self.automatic)
        self.progress = QProgressBar(); self.progress.hide(); layout.addWidget(self.progress)
        buttons = QHBoxLayout(); layout.addLayout(buttons)
        self.check = QPushButton('Buscar actualizaciones'); self.check.clicked.connect(controller.check); buttons.addWidget(self.check)
        self.apply = QPushButton('Descargar actualización'); self.apply.setObjectName('primary'); self.apply.setEnabled(False)
        self.apply.clicked.connect(controller.apply); buttons.addWidget(self.apply)
        self.cancel = QPushButton('Cerrar'); self.cancel.clicked.connect(self.close); buttons.addWidget(self.cancel)
        versions = QPushButton('Ver descargas en GitHub')
        versions.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://github.com/Tincho1286/SignalLab-PC/releases/latest')))
        layout.addWidget(versions)
        if controller.installation is None:
            self.status.setText('Esta es la edición portable o de desarrollo. Podés consultar las versiones; la instalación automática corresponde a la edición instalada.')

    def closeEvent(self, event):
        self.controller.cancel(); event.accept()


class UpdateController(QObject):
    def __init__(self, window):
        super().__init__(window); self.window = window; self.installation = installed()
        self.dialog = UpdateDialog(self); self.job = None; self.release = None; self.asset = None
        self.path = None; self.manual = False; self.close_when_done = False
        if self.installation is not None:
            from .update_cache import prune
            cache=Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.CacheLocation))/'updates'
            prune(cache,__version__)
        # Packaged diagnostics must not contact the release service.
        if self.installation is not None and '--self-check' not in sys.argv and window.settings.value('updates/check_at_startup', True, type=bool):
            QTimer.singleShot(12000, self.background_check)

    @property
    def busy(self):
        return self.job is not None

    def show(self):
        self.dialog.show(); self.dialog.raise_(); self.dialog.activateWindow()

    def background_check(self):
        if not self.busy and not self.close_when_done:
            self._check(False)

    def check(self):
        self._check(True)

    def _check(self, manual):
        if self.busy:
            return
        self.manual = manual; self.path = None; self.asset = None; self.release = None
        self.dialog.notes.clear(); self.dialog.status.setText('Consultando versiones estables…')
        self._start(lambda cancel, progress: fetch_release(cancel=cancel), self._checked)

    def _start(self, function, accept):
        self.dialog.check.setEnabled(False); self.dialog.apply.setEnabled(False)
        self.dialog.cancel.setText('Cancelar'); self.dialog.progress.setRange(0, 0); self.dialog.progress.show()
        self.job = Job(function, self)
        self.job.completed.connect(accept)
        self.job.failed.connect(self._failed)
        self.job.progressed.connect(self._progress)
        self.job.finished.connect(self._finished)
        self.job.start()

    def _progress(self, done, total):
        self.dialog.progress.setRange(0, 100); self.dialog.progress.setValue(int(done * 100 / total))

    def _finished(self):
        job = self.job; self.job = None
        if job is not None and job.cancel.is_set():
            self.dialog.status.setText('Operación cancelada.')
        if job is not None:
            job.deleteLater()
        self.dialog.check.setEnabled(True); self.dialog.cancel.setText('Cerrar'); self.dialog.progress.hide()
        self.dialog.apply.setEnabled(self.asset is not None and self.installation is not None)
        if self.close_when_done:
            QTimer.singleShot(0, self.window.close)

    def _failed(self, message):
        self.dialog.status.setText(message)
        if not self.manual:
            self.window.statusBar().showMessage('No se pudo comprobar la actualización. Consultá Ayuda → Buscar actualizaciones.', 10000)

    def _checked(self, release):
        self.release = release; self.dialog.notes.setPlainText(release.notes)
        if not release.newer_than(__version__):
            self.dialog.status.setText('Ya tenés la última versión estable del canal firmado.'); return
        self.asset = release.assets.get(platform_tag())
        if self.asset is None:
            self.dialog.status.setText('Hay una versión nueva, pero todavía no hay un instalador compatible para este equipo.'); return
        self.dialog.status.setText('Disponible: ' + release.version + '. La descarga se verificará antes de ejecutarse.')
        self.dialog.apply.setText('Descargar actualización')
        self.window.statusBar().showMessage('SignalLab ' + release.version + ' disponible · Ayuda → Buscar actualizaciones', 30000)

    def apply(self):
        if self.busy or self.asset is None or self.installation is None:
            return
        if self.path is None:
            self.manual = True; self.dialog.status.setText('Descargando y comprobando integridad…')
            cache = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.CacheLocation)) / 'updates'
            self._start(lambda cancel, progress: download(self.asset, cache, cancel=cancel, progress=progress), self._downloaded)
            return
        if self.window._workers:
            QMessageBox.information(self.dialog, 'Cálculo en curso', 'Terminá o cancelá el cálculo antes de instalar. La descarga ya está preparada.'); return
        answer = QMessageBox.question(self.dialog, 'Instalar actualización',
            'SignalLab se cerrará para instalar la versión nueva y volver a abrirse. Guardá o exportá los resultados que quieras conservar: los resultados de esta sesión no se recuperan automáticamente. Los temas y la configuración se conservan.\n\n¿Instalar ahora?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            start_update(self.asset, self.path, self.installation)
        except Exception as exc:
            QMessageBox.warning(self.dialog, 'No se pudo iniciar la actualización', str(exc)); return
        self.dialog.hide(); self.window.close()

    def _downloaded(self, path):
        self.path = path; self.dialog.status.setText('Descarga verificada. Podés instalar cuando termines de trabajar.')
        self.dialog.apply.setText('Instalar y reiniciar')

    def cancel(self):
        if self.job is not None:
            self.dialog.status.setText('Cancelando operación…')
            self.job.cancel.set()

    def prepare_close(self):
        if self.busy:
            self.close_when_done = True; self.cancel(); return False
        return True
