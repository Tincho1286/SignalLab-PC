"""View-only inspector of an immutable state simulation snapshot."""
import csv,json
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QComboBox,QLineEdit,QLabel,QTableView,QHeaderView,QFileDialog,QMessageBox
from .active_stack import ActiveTabs
from .report_view import ReportView,report_panel
from .spectral_measurements_panel import Rows
from .numeric_input import integer_field
from .atomic_file import atomic_text_file
from . import state_response_studies as calc


class StateStepsPanel(QWidget):
    def __init__(self,window):
        super().__init__();self.setProperty('keepLocalAction',True);self.window=window;self.run=None;self.trace=None;self.data=None;self.revision=0
        layout=QVBoxLayout(self);self.prepare=QPushButton('Preparar inspector del último cálculo');self.prepare.clicked.connect(self.build);layout.addWidget(self.prepare)
        self.note=QLabel('Calculá una simulación para consultar los aportes.');self.note.setWordWrap(True);layout.addWidget(self.note)
        self.component=QComboBox();self.component.setAccessibleName('Componente del inspector de estados');layout.addWidget(self.component);self.component.currentIndexChanged.connect(self.component_changed)
        from .figure_controls import WrappedControls
        controls=QWidget();bar=WrappedControls(controls);policy=controls.sizePolicy();policy.setHeightForWidth(True);controls.setSizePolicy(policy);self.channel=QComboBox();self.position=QLineEdit('0');self.position.setMaximumWidth(160);self.previous=QPushButton('←');self.next=QPushButton('→');self.read=QPushButton('Ver paso');self.export=QPushButton('Exportar aportes…')
        for widget in (self.channel,self.previous,QLabel('Posición k ='),self.position,self.next,self.read,self.export):bar.addWidget(widget)
        layout.addWidget(controls);self.tabs=ActiveTabs();layout.addWidget(self.tabs,1);self.report=ReportView();self.tabs.addTab(report_panel(self.report),'Explicación');self.model=Rows([('source','Origen'),('channel','Canal / estado'),('coefficient','Coeficiente'),('value','Valor guardado'),('contribution','Aporte')]);table=QTableView();table.setModel(self.model);table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents);self.tabs.addTab(table,'Aportes')
        self.channel.currentIndexChanged.connect(self.show_step);self.position.returnPressed.connect(self.show_step);self.read.clicked.connect(self.show_step);self.previous.clicked.connect(lambda:self.move(-1));self.next.clicked.connect(lambda:self.move(1));self.export.clicked.connect(self.save);self.set_run(None)
    def set_run(self,run):
        self.run=run;self.component.blockSignals(True);self.component.clear()
        if run is not None:self.component.addItems([c['name'] for c in run['components']])
        self.component.blockSignals(False);self.component.setEnabled(run is not None);self.component_changed(prepare=False,reset=True)
    def component_changed(self,*_,prepare=True,reset=False):
        self.selected_step=None if reset else self.channel.currentData() or getattr(self,'selected_step',None);self.selected_position='0' if reset else self.position.text()
        self.revision+=1;self.trace=None;self.data=None;self.channel.clear();self.model.set_rows([]);self.prepare.setEnabled(self.run is not None);self.report.setPlainText('Abrí Paso a paso o prepará el inspector para consultar esta componente sin volver a simular.')
        for widget in (self.channel,self.position,self.read,self.previous,self.next,self.export):widget.setEnabled(False)
        if prepare and self.isVisible() and self.run is not None:self.build()
    def build(self):
        if self.run is None or getattr(self.window,'_workers',[]):return
        revision=self.revision;run=self.run;component=max(0,self.component.currentIndex());selected=self.channel.currentData() if self.trace is not None else self.selected_step;position=self.selected_position if self.trace is None else self.position.text()
        def accept(trace):
            if revision!=self.revision:return
            self.trace=trace;self.channel.blockSignals(True);self.channel.clear()
            for i in range(trace['model'].outputs):self.channel.addItem('Salida y'+str(i+1),('output',i))
            for i in range(trace['model'].states):self.channel.addItem('Estado siguiente x'+str(i+1),('state',i))
            chosen=next((i for i in range(self.channel.count()) if self.channel.itemData(i)==selected),0)
            self.channel.setCurrentIndex(chosen);self.channel.blockSignals(False);self.position.setText(position)
            for widget in (self.channel,self.position,self.read):widget.setEnabled(True)
            self.note.setText(trace['component']+'. Posiciones k=0…'+str(len(trace['axis'])-1)+'. El inspector conserva el cálculo aunque edites sus entradas. No hay transición simulada después del último punto.');self.show_step()
        getattr(self.window,'_run_view_operation',self.window._run_operation)('Preparando los aportes de estados…',lambda:calc.capture(run,component),accept)
    def show_step(self,*_):
        if self.trace is None or self.channel.currentData() is None:return
        try:
            family,channel=self.channel.currentData();trace=self.trace;index=integer_field(self.position)
            if trace['model'].states+trace['model'].inputs>512:
                if getattr(self.window,'_workers',[]):return
                revision=self.revision;selection=self.channel.currentData();requested=self.position.text();self.data=None;self.model.set_rows([]);self.export.setEnabled(False);self.report.setPlainText('Reconstruyendo los aportes del paso guardado…')
                def job():
                    try:return calc.inspect(trace,index,family=family,channel=channel)
                    except (ValueError,ArithmeticError) as exc:return {'error':str(exc)}
                def accept(data):
                    if revision!=self.revision:return
                    if self.channel.currentData()!=selection or self.position.text()!=requested:self.report.setPlainText('La selección cambió. Pulsá Ver paso para consultar los datos actuales.');return
                    if 'error' in data:self.report.setPlainText(data['error']);return
                    self.accept_step(data)
                getattr(self.window,'_run_view_operation',self.window._run_operation)('Reconstruyendo aportes de estados…',job,accept)
            else:self.accept_step(calc.inspect(trace,index,family=family,channel=channel))
        except (ValueError,ArithmeticError) as exc:self.data=None;self.export.setEnabled(False);self.model.set_rows([]);self.report.setPlainText(str(exc))
    def accept_step(self,data):
        self.data=data;self.model.set_rows(data['rows']);self.report.set_readable(calc.summary(self.trace,data));self.export.setEnabled(True);self.previous.setEnabled(data['index']>0);self.next.setEnabled(data['index']<(len(self.trace['axis'])-2 if data['family']=='state' else len(self.trace['axis'])-1))
    def move(self,delta):
        try:self.position.setText(str(integer_field(self.position)+delta));self.show_step()
        except ValueError as exc:self.report.setPlainText(str(exc))
    def save(self):
        if self.data is None:return
        path,_=QFileDialog.getSaveFileName(self,'Exportar aportes','aportes_estados.csv','CSV (*.csv)')
        if not path:return
        try:
            with atomic_text_file(path,newline='') as stream:
                stream.write('# '+json.dumps({key:str(value) for key,value in self.data.items() if key!='rows'},ensure_ascii=False)+'\n');writer=csv.DictWriter(stream,fieldnames=[key for key,_ in self.model.columns]);writer.writeheader();writer.writerows(self.data['rows'])
        except OSError as exc:QMessageBox.warning(self,'Exportar aportes',str(exc))
