"""A result-local sample inspector; preparing it never recalculates the response."""
import csv,json
from PySide6.QtWidgets import QWidget,QVBoxLayout,QPushButton,QLabel,QLineEdit,QComboBox,QTabWidget,QTableView,QHeaderView,QFileDialog
from .report_view import ReportView,report_panel
from .spectral_measurements_panel import Rows
from .numeric_input import integer_field
from .atomic_file import atomic_text_file
from . import response_steps as steps


class ResponseStepsPanel(QWidget):
    def __init__(self,window):
        super().__init__();self.setProperty('keepLocalAction',True);self.window=window;self.snapshot=None;self.trace=None;self.data=None;self.revision=0
        layout=QVBoxLayout(self);self.prepare=QPushButton('Preparar inspector del último cálculo');self.prepare.setObjectName('primary');self.prepare.clicked.connect(self.build);layout.addWidget(self.prepare)
        self.note=QLabel('Calculá una respuesta discreta para consultar los aportes de cada muestra.');self.note.setWordWrap(True);layout.addWidget(self.note)
        from .figure_controls import WrappedControls
        controls=QWidget();bar=WrappedControls(controls);policy=controls.sizePolicy();policy.setHeightForWidth(True);controls.setSizePolicy(policy);self.section=QComboBox();self.index=QLineEdit();self.index.setAccessibleName('Índice n de la respuesta');self.index.setMaximumWidth(180);self.previous=QPushButton('←');self.next=QPushButton('→');self.read=QPushButton('Ver muestra');self.export=QPushButton('Exportar aportes…')
        for widget in (self.section,self.previous,QLabel('n ='),self.index,self.next,self.read,self.export):bar.addWidget(widget)
        layout.addWidget(controls);self.tabs=QTabWidget();layout.addWidget(self.tabs,1);self.report=ReportView();self.tabs.addTab(report_panel(self.report),'Explicación')
        self.model=Rows([('family','Término'),('lag','Retardo k'),('index','Índice de la muestra'),('raw_coefficient','Coeficiente con signo'),('normalization','Divisor a₀'),('value','Valor de la muestra'),('contribution','Aporte'),('source','Origen')]);self.table=QTableView();self.table.setModel(self.model);self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents);self.tabs.addTab(self.table,'Aportes')
        self.index.returnPressed.connect(self.show_step);self.read.clicked.connect(self.show_step);self.section.currentIndexChanged.connect(self.show_step);self.previous.clicked.connect(lambda:self.move(-1));self.next.clicked.connect(lambda:self.move(1));self.export.clicked.connect(self.save)
        self.set_snapshot(None)
    def set_snapshot(self,snapshot):
        self.revision+=1;self.snapshot=snapshot;self.trace=None;self.data=None;self.model.set_rows([]);self.section.clear();self.report.setPlainText('Prepará el inspector para leer los datos del último cálculo.');self.prepare.setEnabled(snapshot is not None)
        for widget in (self.section,self.previous,self.next,self.index,self.read,self.export):widget.setEnabled(False)
    def build(self):
        if self.snapshot is None or getattr(self.window,'_workers',[]):return
        snapshot=self.snapshot;revision=self.revision
        def job():
            try:return steps.capture(snapshot)
            except (ValueError,ArithmeticError,RuntimeError) as exc:return {'error':str(exc)}
        def accept(result):
            if revision!=self.revision:return
            self.prepare.setEnabled(True)
            if 'error' in result:self.report.setPlainText(result['error']);return
            self.trace=result;self.section.blockSignals(True);self.section.clear();self.section.addItems([frame['name'] for frame in result['frames']]);self.section.blockSignals(False);self.index.setText(str(result['origin']));self.note.setText('Intervalo n = '+str(result['origin'])+' a '+str(result['origin']+result['count']-1)+'. Se conserva el último cálculo, aunque edites el formulario.')
            for widget in (self.section,self.index,self.read):widget.setEnabled(True)
            self.show_step()
        run=getattr(self.window,'_run_view_operation',self.window._run_operation);run('Preparando los aportes de la respuesta…',job,accept)
    def show_step(self,*_):
        if self.trace is None:return
        try:
            trace=self.trace;index=integer_field(self.index);section=self.section.currentIndex();frame=trace['frames'][section]
            if len(frame['a'])+len(frame['b'])>512:
                if getattr(self.window,'_workers',[]):return
                revision=self.revision;request=(self.index.text(),section);self.data=None;self.model.set_rows([]);self.export.setEnabled(False);self.report.setPlainText('Reconstruyendo esta muestra con los coeficientes guardados…')
                def job():
                    try:return steps.inspect(trace,index,section)
                    except (ValueError,ArithmeticError) as exc:return {'error':str(exc)}
                def accept(data):
                    if revision!=self.revision:return
                    if request!=(self.index.text(),self.section.currentIndex()):self.report.setPlainText('El índice o la sección cambió. Pulsá Ver muestra para leer los aportes actuales.');return
                    if 'error' in data:self.report.setPlainText(data['error']);return
                    self.accept_step(data)
                run=getattr(self.window,'_run_view_operation',self.window._run_operation);run('Reconstruyendo los aportes de una muestra…',job,accept)
            else:self.accept_step(steps.inspect(trace,index,section))
        except (ValueError,ArithmeticError) as exc:self.data=None;self.model.set_rows([]);self.export.setEnabled(False);self.report.setPlainText(str(exc))
    def accept_step(self,data):
        self.data=data;self.model.set_rows(data['rows']);self.report.set_readable(steps.summary(self.trace,data));self.export.setEnabled(True);self.previous.setEnabled(data['index']>self.trace['origin']);self.next.setEnabled(data['index']<self.trace['origin']+self.trace['count']-1)
    def move(self,delta):
        try:self.index.setText(str(integer_field(self.index)+delta));self.show_step()
        except ValueError as exc:self.report.setPlainText(str(exc))
    def save(self):
        if self.data is None:return
        path,_=QFileDialog.getSaveFileName(self,'Exportar los aportes de esta muestra','aportes_respuesta.csv','CSV (*.csv)')
        if not path:return
        def text(value):
            if value is None:return ''
            if isinstance(value,complex):return repr(value)
            return str(value)
        try:
            with atomic_text_file(path,newline='') as stream:
                stream.write('# '+json.dumps(dict(index=self.data['index'],section=self.data['name'],computed=text(self.data['computed']),reconstructed=text(self.data['reconstructed']),residual=text(self.data['residual']),scope='Racionales de valores binarios; comparación con la realización guardada.'),ensure_ascii=False)+'\n')
                writer=csv.DictWriter(stream,fieldnames=[key for key,_ in self.model.columns]);writer.writeheader();writer.writerows({key:text(row[key]) for key,_ in self.model.columns} for row in self.data['rows'])
        except OSError as exc:self.note.setText(str(exc))
