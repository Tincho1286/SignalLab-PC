"""Installer entry point run from the downloaded self-extracting Linux package."""
from pathlib import Path
import argparse
import os
import subprocess
import sys
import time
from .linux_installation import default_root, install, uninstall
from .update_manifest import UpdateError
from .process_handoff import launch_independent


def wait_for_parent(pid):
    if not pid:
        return
    if pid <= 1 or pid == os.getpid():
        raise UpdateError('Identificador del proceso anterior inválido.')
    end = time.monotonic() + 120
    while time.monotonic() < end:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        except PermissionError as exc:
            raise UpdateError('El proceso anterior pertenece a otro usuario.') from exc
        time.sleep(.2)
    raise UpdateError('SignalLab sigue abierto. Cerralo antes de actualizar.')


def main(arguments):
    parser = argparse.ArgumentParser(description='Instalación por usuario de SignalLab PC')
    parser.add_argument('--source', type=Path)
    parser.add_argument('--target', type=Path, default=default_root())
    parser.add_argument('--update', type=int, default=0)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--uninstall', action='store_true')
    args = parser.parse_args(arguments)
    if sys.platform != 'linux':
        raise SystemExit('Este instalador corresponde a Linux.')
    from . import __version__
    if args.headless:
        wait_for_parent(args.update)
        if args.uninstall:
            uninstall(args.target)
        else:
            if args.source is None:
                parser.error('Falta --source.')
            print(install(args.source, args.target, __version__))
        return 0
    from PySide6.QtCore import QThread, Signal
    from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox
    app = QApplication([]); app.setApplicationName('SignalLab PC'); app.setStyle('Fusion')
    box = QDialog(); box.setWindowTitle('SignalLab PC · ' + ('Desinstalar' if args.uninstall else 'Instalar')); box.resize(510, 220)
    layout = QVBoxLayout(box)
    text = QLabel(('Se quitarán los archivos del programa. Los temas, la configuración y tus documentos se conservan.' if args.uninstall else
        'Instalación para tu usuario, sin permisos de administrador. Las siguientes versiones se podrán instalar sobre ésta.') + '\n\nCarpeta: ' + str(args.target))
    text.setWordWrap(True); layout.addWidget(text)
    action = QPushButton('Desinstalar' if args.uninstall else 'Instalar SignalLab ' + __version__); layout.addWidget(action)

    class Worker(QThread):
        result = Signal(object)
        failed = Signal(str)

        def run(self):
            try:
                wait_for_parent(args.update)
                if args.uninstall:
                    uninstall(args.target); self.result.emit(None)
                elif args.source is None:
                    raise UpdateError('Falta la carpeta del paquete.')
                else:
                    self.result.emit(install(args.source, args.target, __version__))
            except Exception as exc:
                self.failed.emit(str(exc))

    worker = Worker(box)

    def succeeded(binary):
        if binary is not None:
            launch_independent([str(binary)], start_new_session=True, stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        app.quit()

    def failed(message):
        QMessageBox.warning(box, 'No se pudo completar', message); app.quit()

    worker.result.connect(succeeded); worker.failed.connect(failed)

    def start():
        action.setEnabled(False); text.setText('Esperando el cierre de SignalLab…' if args.update else 'Preparando los archivos del programa…')
        worker.start()

    action.clicked.connect(start)
    # Closing during a copy must not destroy a running QThread.
    def close(event):
        if worker.isRunning():
            event.ignore()
        else:
            event.accept()
    box.closeEvent = close
    box.show()
    if args.update:
        start()
    result = app.exec(); worker.wait(); return result
