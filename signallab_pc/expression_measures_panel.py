from .numeric_input import real_field,integer_field
"""Medidas algebraicas y aproximaciones de una misma definición de señal."""
import json
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QFormLayout,QLineEdit,QComboBox,QPushButton,QLabel,QScrollArea,QSplitter,QTabWidget,QMessageBox,QFileDialog
from .report_view import ReportView,report_panel
from .expression_editor import ExpressionEditor
from .symbolic_process import run_request
from .model import Signal

STATES={'finite':'Finito','divergent':'Divergente (+∞)','conditional':'Sujeto a parámetros o condiciones','unevaluated':'Pendiente de evaluación','undetermined':'No determinado','undefined':'No definido'}
class ExpressionMeasuresPanel(QWidget):
    def __init__(self,window,mode):
        super().__init__();self.window=window;self.mode=mode;self.parent_id=None;self.last=None
        from .toolbox import ResultView
        root=QVBoxLayout(self);split=QSplitter(Qt.Orientation.Horizontal);split.setChildrenCollapsible(False);root.addWidget(split)
        controls=QWidget();form=QFormLayout(controls)
        self.domain=QComboBox();self.domain.addItems(['Continua · x(t)','Discreta · x[n]']);form.addRow('Dominio',self.domain)
        self.expression=ExpressionEditor('sin(t)' if mode=='periodic' else 'exp(-abs(t))');self.expression.symbolic=True;form.addRow('Expresión',self.expression)
        self.lower=QLineEdit('-5');self.upper=QLineEdit('5');self.period=QLineEdit('2*pi')
        if mode=='interval':form.addRow('Límite inicial',self.lower);form.addRow('Límite final',self.upper)
        if mode=='periodic':form.addRow('Periodo',self.period)
        descriptions={'interval':'Energía y promedio cuadrático del intervalo. No se clasifica toda la señal a partir de esa ventana.',
            'global':'Energía en todo el eje y potencia mediante un límite de ventanas simétricas. Las integrales o sumas no resueltas se muestran como pendientes.',
            'periodic':'Se comprueba que la expresión se repita con el periodo indicado. La potencia se obtiene promediando un periodo.'}
        note=QLabel(descriptions[mode]);note.setWordWrap(True);form.addRow(note)
        choose=QPushButton('Reutilizar una definición de señal…');choose.clicked.connect(self.choose);form.addRow(choose)
        from .expression_import import install_expression_import
        install_expression_import(self.expression,window,lambda:['t' if self.domain.currentIndex()==0 else 'n'],receiver=self.load_expression)
        self._expression_origin=None;self._input_conditions=()
        self.source_note=QLabel();self.source_note.setWordWrap(True);self.source_note.setObjectName('muted');form.addRow(self.source_note);self.source_note.hide();self.expression.textChanged.connect(self.refresh_origin)
        self.calculate_button=QPushButton('Calcular energía y potencia');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);form.addRow(self.calculate_button)
        heading=QLabel('Ventana numérica');heading.setObjectName('cardTitle');form.addRow(heading)
        self.start=QLineEdit('-5');self.stop=QLineEdit('5');self.count=QLineEdit('501')
        form.addRow('Inicio de la ventana',self.start);form.addRow('Final de la ventana',self.stop);form.addRow('Puntos en continuo',self.count)
        self.sample_button=QPushButton('Graficar y guardar muestras');self.sample_button.setEnabled(False);self.sample_button.clicked.connect(self.sample);self.sample_button.setToolTip('Crear la ventana numérica indicada, guardar sus muestras y abrir la figura.')
        note=QLabel('La ventana genera una señal reutilizable. Su energía y promedio son locales: no reemplazan el análisis de todo el eje. En discreto se incluyen todos los índices de inicio a final.');note.setWordWrap(True);form.addRow(note)
        self.save_report=QPushButton('Guardar informe…');self.save_report.clicked.connect(self.save)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);scroll.setMinimumWidth(300);split.addWidget(scroll)
        results=QWidget();result_layout=QVBoxLayout(results);result_layout.setContentsMargins(0,0,0,0);result_layout.addWidget(self.save_report,0,Qt.AlignmentFlag.AlignRight)
        self.tabs=QTabWidget();result_layout.addWidget(self.tabs,1);split.addWidget(results);split.setSizes([350,740]);split.setStretchFactor(1,1)
        from .plot_actions import install_result_button
        install_result_button(self.tabs,self.sample_button)
        self.report=ReportView();self.numeric_report=ReportView();self.output=ResultView(details=False);self.tabs.addTab(report_panel(self.report),'Algebraico');self.tabs.addTab(report_panel(self.numeric_report),'Ventana numérica');self.tabs.addTab(self.output,'Gráfico')
        self.report.setPlainText('Ingresá una expresión con t o n. Se conservan los valores exactos, sus condiciones y las aproximaciones disponibles. Los parámetros sin asignar permanecen simbólicos.')
        self.numeric_report.setPlainText('Después del cálculo algebraico podés crear una ventana de muestras y consultar sus medidas aquí.')
        for field in (self.expression,self.lower,self.upper,self.period):field.textChanged.connect(lambda _:self.sample_button.setEnabled(False))
        self.domain.currentIndexChanged.connect(self.change_domain);self.domain.currentIndexChanged.connect(self.refresh_origin)
    def change_domain(self,index):
        self.sample_button.setEnabled(False);self.count.setEnabled(index==0)
        defaults={'exp(-abs(t))':'(1/2)^abs(n)','sin(t)':'sin(pi*n/2)'}
        current=self.expression.text()
        if index and current in defaults:self.expression.setText(defaults[current])
        elif not index and current in defaults.values():self.expression.setText(next(k for k,v in defaults.items() if v==current))
        if self.mode=='periodic' and self.period.text() in ('2*pi','4'):self.period.setText('4' if index else '2*pi')
    def request(self):
        intact=self._expression_origin and self._expression_origin[0]==self.expression.text() and self._expression_origin[2]==self.domain.currentIndex()
        return dict(input_conditions=list(self._input_conditions) if intact else [],operation='signal_measures_expression',expression=self.expression.text(),domain='continuous' if self.domain.currentIndex()==0 else 'discrete',mode=self.mode,lower=self.lower.text(),upper=self.upper.text(),period=self.period.text())
    def refresh_origin(self,*_):
        current=self._expression_origin and self._expression_origin[0]==self.expression.text() and self._expression_origin[2]==self.domain.currentIndex()
        self.source_note.setVisible(bool(current));self.source_note.setText('Definición cargada desde Resultados. Sus condiciones acompañan al cálculo.' if current else '')
    def load_expression(self,expression,key=None):
        if expression is None or expression.variable not in ('t','n',None):raise ValueError('Elegí una expresión temporal en t o n.')
        if expression.variable is not None:self.domain.setCurrentIndex(0 if expression.variable=='t' else 1)
        text=expression.numerical_source or expression.source
        self.expression.setText(text);self.parent_id=key;self._expression_origin=(self.expression.text(),key,self.domain.currentIndex());self._input_conditions=expression.conditions;self.refresh_origin()
    def choose(self):
        key=self.window.choose_record('temporal_expression')
        if not key:return
        from .reuse_sources import temporal_expression
        self.load_expression(temporal_expression(self.window.project,key),key)
    def calculate(self):
        request=self.request();intact=self._expression_origin and self._expression_origin[0]==request['expression'] and self._expression_origin[2]==self.domain.currentIndex();parent=self._expression_origin[1] if intact else None;parents=[parent] if parent else []
        def accept(result):
            key=self.window.publish({'request':request,'result':result},title='Energía y potencia · '+request['expression'],operation='Medidas algebraicas de señal',parents=parents)
            self.last=(request,result,key);self.sample_button.setEnabled(request==self.request())
            from .result_summary import expression_measure_summary
            self.report.set_readable(expression_measure_summary(request,result));self.tabs.setCurrentIndex(0)
        self.window._run_operation('Calculando medidas algebraicas…',lambda:run_request(request),accept)
    def open_output_plot(self):
        from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
        from .plot_view import install_enlarge,enlarge_plot
        canvas=self.output.canvas
        if getattr(canvas,'_signallab_window',None) is None:
            for toolbar in self.output.findChildren(NavigationToolbar2QT):
                if toolbar.canvas is canvas:install_enlarge(toolbar);break
        canvas.draw();enlarge_plot(canvas,self)
    def sample(self):
        if not self.last:return
        definition,result,parent=self.last
        try:
            request=dict(operation='signal_measures_window',expression=definition['expression'],domain=definition['domain'],start=self.start.text(),stop=self.stop.text(),count=integer_field(self.count) if definition['domain']=='continuous' else None)
            def accept(data):
                summary={k:v for k,v in data.items() if k!='samples'}
                report_id=self.window.publish({'request':request,'result':summary},title='Medidas de ventana · '+definition['expression'],operation='Aproximación de energía y potencia',parents=[parent])
                signal=Signal([complex(*v) for v in data['samples']],data['origin'],data['step'],'s' if data['domain']=='continuous' else 'n',definition['expression'],data['domain'],definition['expression'],{'operation':'expression_measure_window','energy':data['energy'],'mean_square':data['mean_square'],'rms':data['rms'],'scope':data['scope'],'method':data['method']})
                self.window.publish(signal,operation='Muestras de expresión analizada',parents=[report_id]);self.tabs.setCurrentIndex(2);self.output.show_result(signal)
                self.numeric_report.setPlainText('Medidas de la ventana\n\nEnergía: '+str(data['energy'])+'\nPromedio cuadrático: '+str(data['mean_square'])+'\nRMS: '+str(data['rms'])+'\nMétodo: '+data['method']+'\n\n'+data['scope']);self.tabs.setCurrentIndex(2);self.open_output_plot()
            self.window._run_operation('Evaluando ventana numérica…',lambda:run_request(request),accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá la ventana',str(exc))
    def save(self):
        path,_=QFileDialog.getSaveFileName(self,'Guardar informe','energia-potencia.txt','Texto (*.txt)')
        if path:
            try:Path(path).write_text(self.report.toPlainText()+'\n\nVENTANA NUMÉRICA\n\n'+self.numeric_report.toPlainText(),encoding='utf-8')
            except OSError as exc:QMessageBox.warning(self,'No se pudo guardar',str(exc))
