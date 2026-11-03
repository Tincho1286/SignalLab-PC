"""Visible desktop failures with bounded local diagnostics; no network reporting."""
import logging,platform,sys,threading,traceback,uuid
from logging.handlers import RotatingFileHandler
from pathlib import Path
from . import __version__

_lock=threading.RLock()

def diagnostic(error,details='',context='',directory=None):
    identifier=uuid.uuid4().hex[:10]
    technical='SignalLab '+__version__+' · '+platform.platform()+'\nReferencia: '+identifier+'\nAcción: '+str(context)+'\n'+(details or str(error))
    technical=technical[:24000]
    path=None
    try:
        if directory is None:
            from PySide6.QtCore import QStandardPaths
            directory=Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation))/'diagnostics'
        folder=Path(directory);folder.mkdir(parents=True,exist_ok=True);path=folder/'errors.log'
        with _lock:
            handler=RotatingFileHandler(path,maxBytes=512*1024,backupCount=2,encoding='utf-8')
            try:
                handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
                handler.emit(logging.LogRecord('signallab',logging.ERROR,'',0,technical,(),None))
            finally:handler.close()
    except (OSError,ValueError):path=None
    return technical,path

def report_error(parent,title,error,*,details='',context=''):
    from PySide6.QtWidgets import QMessageBox,QApplication
    technical,path=diagnostic(error,details,context)
    box=QMessageBox(parent);box.setIcon(QMessageBox.Icon.Warning);box.setWindowTitle(title)
    box.setText('No se pudo completar esta acción.')
    box.setInformativeText(str(error)[:1800]+('\n\nDiagnóstico local: '+str(path) if path else '\n\nPodés copiar el diagnóstico desde Detalles.'))
    box.setDetailedText(technical);box.setStandardButtons(QMessageBox.StandardButton.Close)
    copy=box.addButton('Copiar diagnóstico',QMessageBox.ButtonRole.ActionRole)
    copy.clicked.connect(lambda:QApplication.clipboard().setText(technical));box.exec()

def install_exception_hook(app):
    previous=sys.excepthook;active=[False]
    def handle(kind,error,tb):
        if issubclass(kind,(KeyboardInterrupt,SystemExit)) or active[0]:return previous(kind,error,tb)
        active[0]=True
        try:
            parent=app.activeWindow()
            context=getattr(parent,'current_operation',None) or type(parent).__name__
            report_error(parent,'La acción no se pudo completar',error,details=''.join(traceback.format_exception(kind,error,tb)),context=context)
        except Exception:previous(kind,error,tb)
        finally:active[0]=False
    sys.excepthook=handle
    return previous
