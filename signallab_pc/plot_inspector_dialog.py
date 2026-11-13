"""Curve definitions, precise cursor placement and sampled extrema beside a figure."""
import csv,json,math
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QFormLayout,QComboBox,QLineEdit,QPushButton,QLabel,QTabWidget,QWidget,QCheckBox,QTableView,QHeaderView,QFileDialog
from . import plot_inspection as inspect
from .transfer_report import TransferResultReport
from .report_view import report_panel
from .spectral_measurements_panel import Rows
from .scalar_expression import real_value,integer_value
from .atomic_file import atomic_text_file


class PlotInspector(QDialog):
    def __init__(self,probe):
        super().__init__(probe.canvas._signallab_window);self.probe=probe;self.signature=None;self.traces=[];self.result=None;self.result_key=None
        self.setWindowTitle('Curvas y medidas · SignalLab');self.resize(820,680);self.setMinimumSize(500,380)
        layout=QVBoxLayout(self);self.selector=QComboBox();layout.addWidget(self.selector);self.axis_label=QLabel();self.axis_label.setWordWrap(True);layout.addWidget(self.axis_label)
        form=QFormLayout();form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows);layout.addLayout(form)
        row=QHBoxLayout();self.coordinate=QLineEdit();self.coordinate.setPlaceholderText('pi/2, 1e-3 o un índice entero');row.addWidget(self.coordinate,1)
        self.target=QComboBox();self.target.addItem('Lectura libre','live');self.target.addItem('Mover A','a');self.target.addItem('Mover B','b');row.addWidget(self.target)
        self.go=QPushButton('Ir');self.previous=QPushButton('←');self.next=QPushButton('→');self.previous.setToolTip('Muestra anterior de la curva seleccionada');self.next.setToolTip('Muestra siguiente de la curva seleccionada')
        for button in (self.previous,self.next,self.go):row.addWidget(button)
        form.addRow('Coordenada x para leer',row);self.go.clicked.connect(self.locate);self.coordinate.returnPressed.connect(self.locate);self.previous.clicked.connect(lambda:self.step(-1));self.next.clicked.connect(lambda:self.step(1))
        self.status=QLabel();self.status.setTextFormat(Qt.TextFormat.PlainText);self.status.setWordWrap(True);layout.addWidget(self.status)
        self.tabs=QTabWidget();layout.addWidget(self.tabs,1);self.report=TransferResultReport();self.tabs.addTab(report_panel(self.report),'Definición')
        page=QWidget();out=QVBoxLayout(page);settings=QHBoxLayout();self.scope=QComboBox();self.scope.addItems(['Tramo x visible','Todos los puntos disponibles']);self.local=QCheckBox('También extremos locales');self.search=QPushButton('Buscar extremos');self.search.setObjectName('primary');settings.addWidget(self.scope);settings.addWidget(self.local);settings.addWidget(self.search);out.addLayout(settings)
        note=QLabel('Se miden puntos finitos evaluados. Un extremo entre muestras o una singularidad necesita otro análisis.');note.setWordWrap(True);out.addWidget(note)
        self.model=Rows([('kind','Tipo'),('index','Posición en datos'),('x','Coordenada x'),('y','Valor y'),('plateau','Meseta (puntos)')]);self.table=QTableView();self.table.setModel(self.model);self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows);self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents);out.addWidget(self.table,1)
        buttons=QHBoxLayout();self.read=QPushButton('Leer punto');self.pin_a=QPushButton('Colocar A aquí');self.pin_b=QPushButton('Colocar B aquí');self.export=QPushButton('Exportar extremos (CSV)…')
        for button in (self.read,self.pin_a,self.pin_b,self.export):buttons.addWidget(button)
        out.addLayout(buttons);self.tabs.addTab(page,'Extremos');self.search.clicked.connect(self.find);self.read.clicked.connect(lambda:self.use_point('live'));self.pin_a.clicked.connect(lambda:self.use_point('a'));self.pin_b.clicked.connect(lambda:self.use_point('b'));self.export.clicked.connect(self.save)
        self.table.doubleClicked.connect(lambda *_:self.use_point('live'));self.selector.currentIndexChanged.connect(self.selection_changed);self.scope.currentIndexChanged.connect(self.invalidate);self.local.toggled.connect(self.invalidate);self.probe.canvas.mpl_connect('draw_event',self.drawn)
        self.refresh()

    def refresh(self):
        self.signature=self.probe.signature;self.traces=list(self.probe.traces);self.selector.blockSignals(True);self.selector.clear();self.selector.addItems([(t.axis.get_ylabel()+' · ' if t.axis.get_ylabel() and t.axis.get_ylabel()!=t.label else '')+t.label for t in self.traces]);self.selector.blockSignals(False);self.selection_changed()

    def drawn(self,*_):
        if not self.isVisible():return
        if self.signature!=self.probe.signature:self.refresh()
        elif self.result is not None and self.scope.currentIndex()==0 and self.selected() is not None:
            low,high=self.bounds(self.selected())
            if (low,high)!=(self.result['low'],self.result['high']):self.status.setText('Vista modificada: la tabla conserva el intervalo anterior. Pulsá Buscar extremos para actualizarla.')

    @staticmethod
    def bounds(trace):
        low,high=sorted(trace.axis.get_xlim());base=getattr(trace.axis,'_signallab_index_origin',None)
        return (base+math.ceil(low),base+math.floor(high)) if base is not None else (low,high)

    def show(self):
        if self.signature!=self.probe.signature:self.refresh()
        super().show()

    def selected(self):
        index=self.selector.currentIndex()
        return self.traces[index] if 0<=index<len(self.traces) else None

    def invalidate(self,*_):
        self.result=None;self.result_key=None;self.model.set_rows([])
        for button in (self.read,self.pin_a,self.pin_b,self.export):button.setEnabled(False)

    def selection_changed(self,*_):
        self.invalidate();trace=self.selected()
        if trace is None:
            self.report.setPlainText('No hay una curva disponible en esta figura.')
            for widget in (self.coordinate,self.target,self.go,self.previous,self.next,self.search):widget.setEnabled(False)
            return
        self.report.set_readable(inspect.definition(trace));self.axis_label.setText('Eje: '+(trace.axis.get_xlabel() or next((a.get_xlabel() for a in trace.axis.get_shared_x_axes().get_siblings(trace.axis) if a.get_xlabel()),'coordenada x')))
        try:
            x,y,_=inspect.values(trace);self.coordinate.setText(str(int(x[0])) if x.dtype.kind in 'iu' else format(float(x[0]),'.17g'));enabled=True
            self.status.setText('Ir y las flechas leen puntos originales, sin interpolar. Mover A o B conserva el otro cursor.')
        except ValueError as exc:enabled=False;self.status.setText(str(exc))
        for widget in (self.coordinate,self.target,self.go,self.previous,self.next,self.search):widget.setEnabled(enabled)

    def locate(self):
        try:
            trace=self.selected()
            if trace is None:return
            x,_,_=inspect.values(trace);value=integer_value(self.coordinate.text()) if x.dtype.kind in 'iu' else real_value(self.coordinate.text())
            self.place(trace,value,self.target.currentData())
        except (ValueError,ArithmeticError) as exc:self.status.setText(str(exc))

    def place(self,trace,coordinate,target):
        _,x,y=self.probe.focus(trace,coordinate,target);self.coordinate.setText(str(x) if isinstance(x,int) else format(x,'.17g'));self.status.setText('x = '+str(x)+' · y = '+format(y,'.17g')+' · '+('lectura libre' if target=='live' else 'cursor '+target.upper()))

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
            self.result=inspect.extrema(trace,low,high,self.local.isChecked());self.result_key=trace.key;self.model.set_rows(self.result['rows']);self.table.selectRow(0)
            for button in (self.read,self.pin_a,self.pin_b,self.export):button.setEnabled(True)
            self.status.setText(str(self.result['points'])+' puntos finitos. '+('Se utilizaron los datos originales disponibles.' if self.result['complete'] else 'Se utilizaron los puntos de la traza dibujada.'))
        except (ValueError,ArithmeticError,MemoryError) as exc:self.invalidate();self.status.setText(str(exc))

    def use_point(self,target):
        try:
            trace=self.selected();index=self.table.currentIndex().row()
            if self.result is not None and trace is not None and trace.key==self.result_key and 0<=index<len(self.model.rows):self.place(trace,self.model.rows[index]['x'],target)
        except (ValueError,ArithmeticError) as exc:self.status.setText(str(exc))

    def save(self):
        if self.result is None:return
        path,_=QFileDialog.getSaveFileName(self,'Exportar extremos','extremos.csv','CSV (*.csv)')
        if not path:return
        try:
            trace=self.selected()
            with atomic_text_file(path,newline='') as stream:
                stream.write('# '+json.dumps(dict(curve=trace.label,x_label=trace.axis.get_xlabel(),y_label=trace.axis.get_ylabel(),**{key:v for key,v in self.result.items() if key!='rows'}),ensure_ascii=False)+'\n');writer=csv.DictWriter(stream,fieldnames=[key for key,_ in self.model.columns]);writer.writeheader();writer.writerows(self.model.rows)
        except (OSError,ValueError) as exc:self.status.setText(str(exc))
