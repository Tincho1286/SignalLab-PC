"""Keep a suggested signal period in sync with the current input."""

from PySide6.QtCore import QObject, QTimer

from .validation import invalid


class PeriodInput(QObject):
    def __init__(self, field, detect, *changes, source='Detectado automáticamente'):
        super().__init__(field)
        self.field = field
        self.detect = detect
        self.source = source
        self.updating = False
        self.suggestion = None
        field.setPlaceholderText('Ingresá el período')
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(220)
        self.timer.timeout.connect(self.refresh)
        for change in changes:
            change.connect(self.schedule)
        field.textChanged.connect(self.edited)
        self.refresh()

    def edited(self, *_):
        if not self.updating:
            self.timer.stop()
            self.suggestion = None
            self.field.setPlaceholderText('Ingresá el período')
            self.field.setToolTip('Período ingresado manualmente.' if self.field.text().strip() else '')

    def replace(self, value):
        self.updating = True
        try:
            self.field.setText(str(value) if value is not None else '')
        finally:
            self.updating = False

    def schedule(self, *_):
        self.suggestion = None
        self.replace(None)
        self.field.setPlaceholderText('Detectando período…')
        self.timer.start()

    def refresh(self):
        value = self.detect()
        self.suggestion = value
        self.replace(value)
        self.field.setPlaceholderText('Ingresá el período')
        self.field.setToolTip(self.source if value is not None else 'Ingresá el período si la herramienta lo requiere.')

    def text(self, *, required=True):
        if self.timer.isActive():
            self.timer.stop()
            self.refresh()
        text = self.field.text().strip()
        if required and not text:
            invalid(self.field, 'no se pudo detectar el período.', 'Ingresá un período para calcular.')
        return text
