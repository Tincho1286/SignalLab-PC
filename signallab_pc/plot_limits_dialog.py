"""Per-axis vertical ranges for the separate figure window."""
from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit

from .numeric_input import real_field
from .plot_scale import set_vertical_range, vertical_axes


class VerticalRangeDialog(QDialog):
    def __init__(self, canvas, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.axes = vertical_axes(canvas.figure)
        self.setWindowTitle('Escala vertical')
        form = QFormLayout(self)
        self.axis = QComboBox()
        for index, axis in enumerate(self.axes,1):
            self.axis.addItem(f'{index}. {axis.get_ylabel() or axis.get_title() or "Eje vertical"}')
        self.mode = QComboBox()
        for label, mode in (('Automática','auto'),('Rango completo','full'),('Límites manuales','manual')):
            self.mode.addItem(label,mode)
        self.minimum, self.maximum = QLineEdit(), QLineEdit()
        self.error = QLabel()
        self.error.setWordWrap(True)
        form.addRow('Panel',self.axis)
        form.addRow('Escala',self.mode)
        form.addRow('Mínimo',self.minimum)
        form.addRow('Máximo',self.maximum)
        hint = QLabel('La escala cambia sólo la vista. Los datos y el eje horizontal se conservan.')
        hint.setWordWrap(True)
        form.addRow(hint)
        form.addRow(self.error)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.apply)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)
        self.mode.currentIndexChanged.connect(self.update_inputs)
        self.axis.currentIndexChanged.connect(self.load_axis)
        self.load_axis()
        if not self.axes:
            buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
            self.error.setText('La figura no tiene un eje vertical ajustable.')

    def load_axis(self, *_):
        if self.axis.currentIndex()<0:
            return
        axis = self.axes[self.axis.currentIndex()]
        mode = getattr(axis,'_signallab_y_mode','auto') if axis.get_autoscaley_on() else 'manual'
        self.mode.setCurrentIndex(self.mode.findData(mode))
        low,high = axis.get_ylim()
        self.minimum.setText(format(low,'.12g'))
        self.maximum.setText(format(high,'.12g'))
        self.update_inputs()

    def update_inputs(self, *_):
        manual = self.mode.currentData()=='manual'
        self.minimum.setEnabled(manual)
        self.maximum.setEnabled(manual)
        self.error.clear()

    def apply(self):
        axis = self.axes[self.axis.currentIndex()]
        mode = self.mode.currentData()
        try:
            bounds = (real_field(self.minimum),real_field(self.maximum)) if mode=='manual' else None
            set_vertical_range(axis, mode, bounds)
        except ValueError as exc:
            self.error.setText(str(exc))
            return
        self.canvas.draw_idle()
        self.accept()
