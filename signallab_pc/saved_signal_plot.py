"""A separate figure for the signal selected in Results."""

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtCore import QSignalBlocker
from PySide6.QtWidgets import QComboBox, QVBoxLayout, QWidget

from .operations import is_centered_dft
from .plot_view import enlarge_plot, hide_plot, install_enlarge
from .signal_figure import centered_bins_view, draw_signal_figure, polar_label
from .wrapping_row import WrappingRow


class SavedSignalPlot(QWidget):
    def __init__(self, parent, table):
        super().__init__(parent)
        self.hide()
        self.table = table
        self.signal = None
        self.displayed = None
        layout = QVBoxLayout(self)
        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        toolbar = NavigationToolbar2QT(self.canvas, self)
        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)
        controls = WrappingRow(self)
        self.components = QComboBox()
        self.components.setAccessibleName('Componentes del gráfico')
        self.components.addItems(['Módulo y fase', 'Parte real e imaginaria'])
        self.axis = QComboBox()
        self.axis.setAccessibleName('Eje horizontal de la DFT')
        self.axis.addItems(['Frecuencia ω (rad/muestra)', 'Índice k centrado'])
        for field in (self.components, self.axis):
            controls.flow.addWidget(field)
        self.canvas._signallab_explicit_plot = True
        self.canvas._signallab_plot_controls = controls
        self.canvas._signallab_sample_table = table
        install_enlarge(toolbar, standalone=True)
        self.components.currentIndexChanged.connect(self.draw)
        self.axis.currentIndexChanged.connect(self.change_axis)

    def set_signal(self, value, title):
        if self.signal is value:
            return
        self.signal = value
        self.displayed = value
        with QSignalBlocker(self.axis), QSignalBlocker(self.components):
            self.axis.setCurrentIndex(0)
            self.axis.setVisible(is_centered_dft(value))
            self.components.setItemText(0, polar_label((value,)))
            self.components.setCurrentIndex(0 if value.domain == 'frequency' else 1)
            self.components.setVisible(not value.metadata.get('lines_only')
                                       and value.metadata.get('operation') != 'spectral_fraction')
        self.canvas._signallab_window.setWindowTitle(title + ' · SignalLab')
        self.draw()

    def open(self):
        enlarge_plot(self.canvas, self)

    def clear(self):
        hide_plot(self.canvas)
        self.signal = self.displayed = None
        self.figure.clear()
        self.canvas.draw_idle()

    def change_axis(self, index):
        if self.signal is None:
            return
        self.displayed = centered_bins_view(self.signal) if index == 1 and is_centered_dft(self.signal) else self.signal
        self.table.set_signals((self.displayed,), preserve_position=True)
        self.draw()

    def draw(self, *_):
        if self.displayed is None:
            return
        from .ui import SignalLabWindow
        draw_signal_figure(self.figure, (self.displayed,), polar=self.components.currentIndex() == 0,
                           select_indices=SignalLabWindow._plot_indices)
        self.canvas.draw_idle()
