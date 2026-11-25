"""Read-only inspection of a signal before it is used as a calculation input."""

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QVBoxLayout, QWidget

from .active_stack import ActiveTabs
from .distributions import dirac_terms
from .report_view import ReportView
from .result_summary import Formula, Section, Summary, number, signal_record_rows
from .result_table import ResultTable
from .signal_figure import draw_signal_figure, polar_label


class SignalInspector(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.signal = None
        self.drawn = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.tabs = ActiveTabs()
        layout.addWidget(self.tabs)
        self.info = ReportView()
        self.tabs.addTab(self.info, 'Datos')
        preview = QWidget()
        box = QVBoxLayout(preview)
        self.components = QComboBox()
        self.components.setAccessibleName('Componentes de la señal')
        self.components.addItems(['Real e imaginaria', 'Módulo y fase'])
        box.addWidget(self.components)
        self.figure = Figure(figsize=(6, 3))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setAccessibleName('Vista previa de la señal')
        self.canvas.setMinimumHeight(140)
        box.addWidget(self.canvas, 1)
        self.plot_index = self.tabs.addTab(preview, 'Gráfico')
        self.table = ResultTable()
        self.tabs.addTab(self.table, 'Valores')
        self.tabs.currentChanged.connect(self.draw)
        self.components.currentIndexChanged.connect(self.draw)

    def set_signal(self, signal, provenance=''):
        if self.signal is None or self.signal.domain != signal.domain:
            self.components.blockSignals(True)
            self.components.setCurrentIndex(int(signal.domain == 'frequency'))
            self.components.blockSignals(False)
        self.signal = signal
        self.drawn = None
        self.components.setItemText(1, polar_label((signal,)))
        self.components.setVisible(not signal.metadata.get('lines_only')
                                   and signal.metadata.get('operation') != 'spectral_fraction')
        self.table.set_signals((signal,))
        rows = signal_record_rows(signal)
        if provenance:
            rows.insert(0, ('Procedencia', provenance))
        if signal.metadata.get('source_file'):
            rows.append(('Archivo', signal.metadata['source_file']))
        if signal.metadata.get('source_variable'):
            rows.append(('Variable importada', signal.metadata['source_variable']))
        terms = dirac_terms(signal)
        if terms:
            rows.append(('Impulsos ideales', str(len(terms))))
        expression = signal.expression.strip()
        sections = [Section('', rows=rows)]
        if expression and expression != 'lista ingresada':
            sections.append(Section('Expresión de origen', formulas=[Formula(expression, expression)]))
        if terms:
            sections.append(Section('Impulsos ideales', rows=[
                (number(coordinate) + ' ' + signal.units, 'Peso ' + number(weight))
                for coordinate, weight in terms[:12]
            ], paragraphs=['Primeros 12 impulsos del registro.'] if len(terms) > 12 else []))
        self.info.set_readable(Summary(signal.name, sections))
        self.draw()

    def draw(self, *_):
        signal = self.signal
        if signal is None or self.tabs.currentIndex() != self.plot_index:
            return
        mode = self.components.currentIndex()
        if self.drawn == mode:
            return
        self.drawn = mode
        from .ui import SignalLabWindow
        draw_signal_figure(self.figure, (signal,), polar=mode == 1,
                           select_indices=lambda values: SignalLabWindow._plot_indices(values, budget=6000))
        from .plot_view import prepare_figure
        prepare_figure(self.figure)
        self.canvas.draw_idle()

def inspect_signal(parent, signal, provenance):
    dialog = QDialog(parent)
    dialog.setWindowTitle('Revisar datos de entrada')
    dialog.setWindowIcon(parent.window().windowIcon())
    dialog.setMinimumSize(380, 390)
    available = parent.screen().availableGeometry()
    dialog.resize(min(770, available.width() - 32), min(570, available.height() - 48))
    box = QVBoxLayout(dialog)
    inspector = SignalInspector()
    inspector.set_signal(signal, provenance)
    box.addWidget(inspector, 1)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    buttons.button(QDialogButtonBox.StandardButton.Close).setText('Cerrar')
    buttons.rejected.connect(dialog.reject)
    box.addWidget(buttons)
    dialog.exec()
