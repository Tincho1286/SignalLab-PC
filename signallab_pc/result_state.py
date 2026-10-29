"""Estado de resultados respecto de los datos editados, sin recalcular."""
from PySide6.QtWidgets import QLabel,QComboBox,QCheckBox

class ResultState(QLabel):
    def __init__(self,widgets,button,sources=(),parent=None):
        super().__init__(parent)
        self.widgets=list(widgets);self.sources=list(sources);self.button=button
        self.default_button=button.text();self.completed=None
        self.setWordWrap(True);self.setObjectName('muted');self.setToolTip('Modificar los datos no recalcula automáticamente. Exportar o reutilizar conserva el último resultado calculado.')
        for source in self.sources:
            self.widgets.extend([source.mode,source.expression,source.samples,source.origin,source.count,source.step])
            if hasattr(source,'frequency_units'):self.widgets.append(source.frequency_units)
            source.sourceChanged.connect(self.refresh)
        for widget in self.widgets:
            if isinstance(widget,QComboBox):widget.currentIndexChanged.connect(self.refresh)
            elif isinstance(widget,QCheckBox):widget.toggled.connect(self.refresh)
            elif hasattr(widget,'textChanged'):widget.textChanged.connect(self.refresh)
            elif hasattr(widget,'model'):
                widget.model.dataChanged.connect(self.refresh)
                widget.model.modelReset.connect(self.refresh)
        self.refresh()

    def set_button(self,button):
        if button is self.button:return
        self.button.setText(self.default_button);self.button=button;self.default_button=button.property('actionTitle') or button.text();self.refresh()

    @staticmethod
    def is_input(widget):
        # A hidden selector can still be the value behind visible choice buttons.
        # Use semantic task roles, not visibility, to exclude derived controls.
        current=widget
        while current is not None:
            role=current.property('calculationInput')
            if role is not None:return bool(role)
            current=current.parentWidget()
        return True

    def snapshot(self):
        values=[]
        for widget in self.widgets:
            if not self.is_input(widget):values.append(None);continue
            if isinstance(widget,QComboBox):values.append(widget.currentIndex())
            elif isinstance(widget,QCheckBox):values.append(widget.isChecked())
            else:values.append(widget.text())
        values.extend(getattr(source,'source_revision',0) for source in self.sources)
        return tuple(values)

    def accept(self,snapshot):
        self.completed=snapshot;self.refresh()

    def refresh(self,*_):
        changed=self.completed is not None and self.snapshot()!=self.completed
        self.button.setText('Recalcular' if changed else self.default_button)
        self.setVisible(self.completed is not None)
        self.setText('Datos modificados · resultado anterior. Recalculá para actualizarlo.' if changed else 'Resultado actualizado.' if self.completed is not None else 'Completá los datos para calcular.')
