"""Curve definitions, precise cursor placement and sampled extrema beside a figure."""
import csv,json,math
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFormLayout, QFrame, QHeaderView, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QTableView, QToolButton, QVBoxLayout, QWidget,
)
from . import plot_inspection as inspect
from .transfer_report import TransferResultReport
from .report_view import report_panel
from .spectral_measurements_panel import Rows
from .scalar_expression import real_value,integer_value
from .atomic_file import atomic_text_file
from .active_stack import ActiveTabs
from .probe_data import trace_name
from .signal_plot import vertical_axis_name
from .wrapping_row import WrappingRow


class PlotInspector(QFrame):
    dismissed = Signal()

    def __init__(self, probe, parent, *, embedded):
        super().__init__(parent)
        self.probe = probe
        self.signature = None
        self.traces = []
        self.result = None
        self.result_key = None
        self.setObjectName('curveInspector')
        self.setProperty('keepLocalAction', True)
        if not embedded:
            self.setWindowFlag(Qt.WindowType.Window)
            self.setWindowTitle('Curvas y medidas · SignalLab')
            self.resize(640, 650)

        from .extrema_overlay import ExtremaOverlay
        self.overlay = ExtremaOverlay(probe.canvas)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(6)
        heading = QHBoxLayout()
        title = QLabel('Curvas y medidas')
        title.setObjectName('curveInspectorTitle')
        heading.addWidget(title, 1)
        close = QToolButton()
        close.setText('×')
        close.setObjectName('curveInspectorClose')
        close.setAccessibleName('Cerrar Curvas y medidas')
        close.setToolTip('Cerrar Curvas y medidas')
        close.clicked.connect(self.close)
        heading.addWidget(close)
        layout.addLayout(heading)

        self.selector = QComboBox()
        self.selector.setAccessibleName('Curva para inspeccionar')
        self.selector.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.selector.setMinimumContentsLength(14)
        layout.addWidget(self.selector)
        self.axis_label = QLabel()
        self.axis_label.setObjectName('muted')
        self.axis_label.setWordWrap(True)
        layout.addWidget(self.axis_label)

        self.tabs = ActiveTabs()
        self.tabs.setObjectName('curveInspectorTabs')
        layout.addWidget(self.tabs, 1)
        self.report = TransferResultReport()
        self.tabs.addTab(report_panel(self.report), 'Definición')
        self.add_extrema_page()
        self.add_reading_page()
        if embedded:
            self.readings_page = QWidget()
            self.readings_layout = QVBoxLayout(self.readings_page)
            self.readings_layout.setContentsMargins(0, 3, 0, 0)
            self.readings_hint = QLabel('Fijá A y B sobre el gráfico para leer sus valores y diferencias.')
            self.readings_hint.setWordWrap(True)
            self.readings_layout.addWidget(self.readings_hint)
            self.tabs.addTab(self.readings_page, 'Tabla A/B')

        self.selector.currentIndexChanged.connect(self.selection_changed)
        self.selector.activated.connect(self.choose_cursor_reference)
        self.scope.currentIndexChanged.connect(self.options_changed)
        self.local.toggled.connect(self.options_changed)
        self.tabs.currentChanged.connect(self.measure_tab_changed)
        self.probe.canvas.mpl_connect('draw_event', self.drawn)
        self.refresh()

    @staticmethod
    def form_page():
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        body.setObjectName('curveInspectorPage')
        box = QVBoxLayout(body)
        box.setContentsMargins(1, 3, 1, 4)
        box.setSpacing(7)
        scroll.setWidget(body)
        return scroll, box

    def add_extrema_page(self):
        page, box = self.form_page()
        self.scope = QComboBox()
        self.scope.setAccessibleName('Intervalo para buscar extremos')
        self.scope.addItems(['Tramo visible', 'Toda la curva', 'Entre A y B'])
        self.local = QCheckBox('Incluir extremos locales')
        self.local.setToolTip('Agregar picos y valles dentro de los tramos de la curva.')
        self.search = QPushButton('Medir extremos')
        self.search.setObjectName('primary')
        options = WrappingRow()
        for widget in (self.scope, self.local, self.search):
            options.flow.addWidget(widget)
        box.addWidget(options)

        self.measure_note = QLabel('Elegí un intervalo para medir el máximo y el mínimo.')
        self.measure_note.setObjectName('curveMeasureSummary')
        self.measure_note.setWordWrap(True)
        self.measure_note.setTextFormat(Qt.TextFormat.PlainText)
        box.addWidget(self.measure_note)
        self.measure_status = QLabel()
        self.measure_status.setObjectName('muted')
        self.measure_status.setWordWrap(True)
        box.addWidget(self.measure_status)

        self.model = Rows([('kind', 'Extremo'), ('x', 'Desde x'), ('x_end', 'Hasta x'), ('y', 'Valor'), ('plateau', 'Puntos')])
        self.table = QTableView()
        self.table.setAccessibleName('Extremos de la curva')
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.verticalHeader().hide()
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setResizeContentsPrecision(80)
        self.table.setMinimumHeight(125)
        box.addWidget(self.table, 1)

        self.read = QPushButton('Ir al punto')
        self.pin_a = QPushButton('Fijar A')
        self.pin_b = QPushButton('Fijar B')
        self.export = QPushButton('CSV…')
        self.export.setAccessibleName('Exportar extremos a CSV')
        self.mark = QCheckBox('Marcar en el gráfico')
        self.mark.setToolTip('▼ Máximo, ▲ mínimo y ○ punto de la fila elegida.')
        self.mark.setChecked(True)
        actions = WrappingRow()
        for widget in (self.read, self.pin_a, self.pin_b, self.export, self.mark):
            actions.flow.addWidget(widget)
        box.addWidget(actions)
        self.tabs.addTab(page, 'Extremos')
        self.search.clicked.connect(self.find)
        self.read.clicked.connect(lambda: self.use_point('live'))
        self.pin_a.clicked.connect(lambda: self.use_point('a'))
        self.pin_b.clicked.connect(lambda: self.use_point('b'))
        self.export.clicked.connect(self.save)
        self.table.doubleClicked.connect(lambda *_: self.use_point('live'))
        self.table.selectionModel().selectionChanged.connect(self.update_marks)
        self.mark.toggled.connect(self.update_marks)

    def add_reading_page(self):
        page, box = self.form_page()
        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.coordinate = QLineEdit()
        self.coordinate.setPlaceholderText('pi/2, 1e-3 o un índice entero')
        form.addRow('Coordenada x', self.coordinate)
        self.target = QComboBox()
        self.target.addItem('Lectura libre', 'live')
        self.target.addItem('Mover A', 'a')
        self.target.addItem('Mover B', 'b')
        form.addRow('Cursor', self.target)
        box.addLayout(form)

        actions = WrappingRow()
        self.previous = QPushButton('← Anterior')
        self.next = QPushButton('Siguiente →')
        self.go = QPushButton('Ir a x')
        self.go.setObjectName('primary')
        for button in (self.go, self.previous, self.next):
            actions.flow.addWidget(button)
        box.addWidget(actions)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        box.addWidget(self.status)
        box.addStretch()
        self.tabs.addTab(page, 'Leer punto')
        self.go.clicked.connect(self.locate)
        self.coordinate.returnPressed.connect(self.locate)
        self.previous.clicked.connect(lambda: self.step(-1))
        self.next.clicked.connect(lambda: self.step(1))

    def refresh(self):
        previous = self.selector.currentText()
        self.signature = self.probe.signature
        self.traces = list(self.probe.traces)
        labels = [trace_name(trace) for trace in self.traces]
        reference = self.probe.preferred_trace
        if not previous and reference is None:
            reference = self.probe.live_key
        position = next((index for index, trace in enumerate(self.traces) if trace.key == reference), -1)
        self.selector.blockSignals(True)
        self.selector.clear()
        self.selector.addItems(labels)
        if position >= 0:
            self.selector.setCurrentIndex(position)
        elif previous in labels:
            self.selector.setCurrentIndex(labels.index(previous))
        self.selector.blockSignals(False)
        self.selection_changed()

    def refresh_theme(self,previous):self.update_marks()

    def drawn(self,*_):
        if not self.isVisible():return
        if self.signature!=self.probe.signature:self.refresh()
        elif self.result is not None and self.scope.currentIndex() in (0,2) and self.selected() is not None:
            trace=self.selected()
            if self.scope.currentIndex()==0:bounds=self.bounds(trace)
            else:
                a,b=self.probe.a,self.probe.b
                bounds=tuple(sorted((a[trace.key][0],b[trace.key][0]))) if a is not None and b is not None and trace.key in a and trace.key in b else None
            self.measure_status.setText('El intervalo cambió. Pulsá Medir extremos para actualizar la tabla.'
                                        if bounds != (self.result['low'], self.result['high']) else self.measure_source())

    @staticmethod
    def bounds(trace):
        low,high=sorted(trace.axis.get_xlim());base=getattr(trace.axis,'_signallab_index_origin',None)
        return (base+math.ceil(low),base+math.floor(high)) if base is not None else (low,high)

    def showEvent(self, event):
        if self.signature!=self.probe.signature:self.refresh()
        super().showEvent(event)

    def closeEvent(self, event):
        self.dismissed.emit()
        super().closeEvent(event)

    def selected(self):
        index=self.selector.currentIndex()
        return self.traces[index] if 0<=index<len(self.traces) else None

    def select_trace(self, key):
        index = next((index for index, trace in enumerate(self.traces) if trace.key == key), -1)
        if index >= 0:
            self.selector.setCurrentIndex(index)

    def choose_cursor_reference(self, _):
        trace = self.selected()
        if trace is not None:
            self.probe.choose_curve(trace.key if trace.key in self.probe.curve_actions else None)

    def invalidate(self,*_):
        self.result=None;self.result_key=None;self.model.set_rows([]);self.overlay.clear()
        self.measure_status.clear()
        for button in (self.read,self.pin_a,self.pin_b,self.export):button.setEnabled(False)

    def selection_changed(self,*_):
        self.invalidate();trace=self.selected()
        self.axis_label.clear()
        self.status.clear()
        self.measure_note.setText('Elegí un intervalo para medir el máximo y el mínimo.')
        if trace is None:
            self.report.setPlainText('No hay una curva disponible en esta figura.')
            self.measure_note.setText('No hay una curva disponible en esta figura.')
            for widget in (self.coordinate,self.target,self.go,self.previous,self.next,self.search):widget.setEnabled(False)
            return
        self.report.set_readable(inspect.definition(trace));self.axis_label.setText('Eje: '+(trace.axis.get_xlabel() or next((a.get_xlabel() for a in trace.axis.get_shared_x_axes().get_siblings(trace.axis) if a.get_xlabel()),'coordenada x')))
        try:
            x,y,_=inspect.values(trace);self.coordinate.setText(str(int(x[0])) if x.dtype.kind in 'iu' else format(float(x[0]),'.17g'));enabled=True
            self.status.setText('Ir y las flechas leen puntos originales, sin interpolar. Mover A o B conserva el otro cursor.')
        except ValueError as exc:enabled=False;self.status.setText(str(exc))
        for widget in (self.coordinate,self.target,self.go,self.previous,self.next,self.search):widget.setEnabled(enabled)
        if enabled and self.tabs.currentIndex()==1:self.find()
        elif not enabled:self.measure_note.setText(self.status.text())

    def options_changed(self,*_):
        self.invalidate()
        if self.tabs.currentIndex()==1:self.find()

    def measure_tab_changed(self,index):
        if index==1 and self.result is None:self.find()

    def update_marks(self,*_):
        row=self.table.currentIndex().row();trace=self.selected()
        if self.mark.isChecked() and self.result is not None and trace is not None:
            self.overlay.show(trace,self.model.rows,self.model.rows[row] if 0<=row<len(self.model.rows) else None)
        else:self.overlay.clear()

    def locate(self):
        try:
            trace=self.selected()
            if trace is None:return
            x,_,_=inspect.values(trace);value=integer_value(self.coordinate.text()) if x.dtype.kind in 'iu' else real_value(self.coordinate.text())
            self.place(trace,value,self.target.currentData())
        except (ValueError,ArithmeticError) as exc:self.status.setText(str(exc))

    def place(self,trace,coordinate,target):
        _,x,y=self.probe.focus(trace,coordinate,target);self.coordinate.setText(str(x) if isinstance(x,int) else format(x,'.17g'));self.status.setText('x = '+str(x)+' · y = '+format(y,'.17g')+' · '+('lectura libre' if target=='live' else 'cursor '+target.upper()))

    def measure_source(self):
        source = 'datos originales' if self.result['complete'] else 'puntos dibujados'
        return f"{self.result['points']} puntos finitos · {source}"

    def step(self,direction):
        try:
            trace=self.selected()
            if trace is None:return
            x,_,_=inspect.values(trace);coordinate=integer_value(self.coordinate.text()) if x.dtype.kind in 'iu' else real_value(self.coordinate.text())
            self.place(trace,inspect.adjacent(trace,coordinate,direction),self.target.currentData())
        except (ValueError,ArithmeticError) as exc:self.status.setText(str(exc))

    def find(self):
        try:
            trace=self.selected()
            if trace is None:return
            low=high=None
            if self.scope.currentIndex()==0:low,high=self.bounds(trace)
            elif self.scope.currentIndex()==2:
                a,b=self.probe.a,self.probe.b
                if a is None or b is None or trace.key not in a or trace.key not in b:raise ValueError('Colocá A y B sobre esta curva para medir entre los dos cursores.')
                low,high=sorted((a[trace.key][0],b[trace.key][0]))
            self.result=inspect.extrema(trace,low,high,self.local.isChecked());self.result_key=trace.key;self.model.set_rows(self.result['rows']);self.table.selectRow(0)
            plateaus=any(row['plateau']>1 for row in self.model.rows)
            self.table.setColumnHidden(2,not plateaus);self.table.setColumnHidden(4,not plateaus)
            for button in (self.read,self.pin_a,self.pin_b,self.export):button.setEnabled(True)
            self.measure_status.setText(self.measure_source())
            self.measure_note.setText('Máximo: '+format(self.result['maximum'],'.10g')+' · Mínimo: '+format(self.result['minimum'],'.10g')
                                      +'\nPuntos entre x = '+str(self.result['first'])+' y '+str(self.result['last']))
            self.update_marks()
        except (ValueError,ArithmeticError,MemoryError) as exc:self.invalidate();self.measure_note.setText(str(exc))

    def use_point(self,target):
        try:
            trace=self.selected();index=self.table.currentIndex().row()
            if self.result is not None and trace is not None and trace.key==self.result_key and 0<=index<len(self.model.rows):self.place(trace,self.model.rows[index]['x'],target)
        except (ValueError,ArithmeticError) as exc:self.measure_status.setText(str(exc))

    def save(self):
        if self.result is None:return
        path,_=QFileDialog.getSaveFileName(self,'Exportar extremos','extremos.csv','CSV (*.csv)')
        if not path:return
        try:
            trace=self.selected()
            with atomic_text_file(path,newline='') as stream:
                stream.write('# '+json.dumps(dict(curve=trace.label,x_label=trace.axis.get_xlabel(),y_label=vertical_axis_name(trace.axis),**{key:v for key,v in self.result.items() if key!='rows'}),ensure_ascii=False)+'\n');writer=csv.DictWriter(stream,fieldnames=['index',*[key for key,_ in self.model.columns]]);writer.writeheader();writer.writerows(self.model.rows)
        except (OSError,ValueError) as exc:self.measure_status.setText(str(exc))
