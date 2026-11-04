from .numeric_input import real_field,integer_field
"""Entrada visual de H por tramos, respuesta al impulso y filtrado espectral."""
import numpy as np
from PySide6.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QFormLayout,QComboBox,QLineEdit,QPushButton,QLabel,QScrollArea,QTabWidget,QMessageBox
from .report_view import ReportView,report_panel
from .engine import evaluate_expression
from .frequency_filter import analyze

class FrequencyFilterPanel(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window;self.results=[]
        from .toolbox import LocalInput,ResultView
        root=QHBoxLayout(self);controls=QWidget();form=QFormLayout(controls)
        self.domain=QComboBox();self.domain.addItems(['Discreto · ω en rad/muestra','Continuo · Ω en rad/s']);form.addRow('Dominio',self.domain)
        note=QLabel('Definí H por tramos. El valor es la ganancia (puede ser compleja); la condición indica en qué frecuencias se aplica. Usá w para la frecuencia.');note.setWordWrap(True);form.addRow(note)
        self.h=LocalInput('Respuesta del filtro H(ω)','frequency');self.h.bind_project(window)
        for label in self.h.findChildren(QLabel):
            if label.text()=='Paso (rad/s)':label.setText('Paso angular')
            if label.text().startswith('X(ω)'):label.setText('H(ω), usar w como frecuencia')
        self.preset=QComboBox();self.preset.addItems(['Pasa bajos','Pasa altos','Pasa banda','Rechaza banda'])
        self.cut1=QLineEdit('pi/4');self.cut2=QLineEdit('pi/2');form.addRow('Plantilla opcional',self.preset);form.addRow('Corte inferior / único',self.cut1);form.addRow('Corte superior (bandas)',self.cut2)
        template=QPushButton('Cargar plantilla en el editor');template.clicked.connect(self.template);form.addRow(template);form.addRow(self.h)
        self.operation=QComboBox();self.operation.addItems(['Ver H y respuesta al impulso','Aplicar a una señal']);form.addRow('Operación',self.operation)
        self.start=QLineEdit('-32');self.count=QLineEdit('65');self.step=QLineEdit('1');form.addRow('Inicio de h',self.start);form.addRow('Puntos de h',self.count);form.addRow('Paso temporal de h',self.step)
        self.xd=LocalInput('Entrada x[n]','discrete');self.xc=LocalInput('Entrada x(t)','continuous')
        for source in (self.xd,self.xc):source.bind_project(window);form.addRow(source)
        self.form=form;self.operation.currentIndexChanged.connect(self.update_inputs);self.domain.currentIndexChanged.connect(self.update_domain)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);left=QVBoxLayout();left.addWidget(scroll);self.calculate_button=QPushButton('Calcular');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);left.addWidget(self.calculate_button);root.addLayout(left,1)
        right=QVBoxLayout();self.selector=QComboBox();self.selector.currentIndexChanged.connect(self.display);right.addWidget(self.selector)
        self.tabs=QTabWidget();self.view=ResultView();self.report=ReportView();self.tabs.addTab(self.view,'Gráfico y valores');self.tabs.addTab(report_panel(self.report),'Explicación');right.addWidget(self.tabs);root.addLayout(right,2)
        from .result_state import ResultState
        self.state=ResultState([self.domain,self.operation,self.start,self.count,self.step],self.calculate_button,[self.h,self.xd,self.xc]);right.insertWidget(0,self.state)
        self.update_domain();self.template()
    def scalar(self,field):
        return real_field(field)
    def update_inputs(self,*_):
        apply=self.operation.currentIndex()==1;digital=self.domain.currentIndex()==0
        self.form.setRowVisible(self.xd,apply and digital);self.form.setRowVisible(self.xc,apply and not digital)
    def update_domain(self,*_):
        self.h.frequency_units.setCurrentText('rad/muestra' if self.domain.currentIndex()==0 else 'rad/s');self.h.frequency_units.setEnabled(False)
        digital=self.domain.currentIndex()==0
        self.step.setText('1' if digital else '0.01');self.step.setEnabled(not digital)
        self.start.setText('-32' if digital else '-2');self.count.setText('65' if digital else '401');self.update_inputs()
    def template(self):
        try:
            c1=self.scalar(self.cut1);c2=self.scalar(self.cut2) if self.preset.currentIndex()>1 else c1
            if c1<=0 or (self.preset.currentIndex()>1 and c2<=c1):raise ValueError('Cortes positivos y ordenados: inferior < superior.')
            digital=self.domain.currentIndex()==0
            if digital and max(c1,c2)>=np.pi:raise ValueError('Los cortes discretos deben ser menores que π rad/muestra.')
            a=repr(c1);b=repr(c2)
            conditions=[f'abs(w) <= {a}',f'abs(w) >= {a}',f'(abs(w) >= {a}) and (abs(w) <= {b})',f'(abs(w) <= {a}) or (abs(w) >= {b})']
            self.h.mode.setCurrentIndex(0);self.h.expression.setText('where('+conditions[self.preset.currentIndex()]+',1,0)');self.h.expression.mode.setCurrentIndex(1)
            bound=np.pi if digital else 4*max(c1,c2);self.h.origin.setText(str(-bound));self.h.step.setText(str(2*bound/2048));self.h.count.setText('2049')
        except Exception as exc:QMessageBox.warning(self,'Revisá los cortes',str(exc))
    def calculate(self):
        try:
            digital=self.domain.currentIndex()==0;domain='discrete' if digital else 'continuous';unit='rad/muestra' if digital else 'rad/s'
            response=self.h._read().copy_with(name='Respuesta H(ω)')
            if self.h.mode.currentIndex()==2 and response.units!=unit:raise ValueError('La respuesta importada debe usar '+unit+'.')
            response.units=unit;response.metadata={**response.metadata,'operation':'frequency_filter','time_domain':domain}
            start=integer_field(self.start) if digital else self.scalar(self.start)
            count=integer_field(self.count);step=self.scalar(self.step)
            source=(self.xd if digital else self.xc).read() if self.operation.currentIndex()==1 else None
            snapshot=self.state.snapshot()
            def accept(result):
                values,report=result;self.results=values;self.selector.blockSignals(True);self.selector.clear()
                for value in values:self.window.publish(value,operation='Filtro por respuesta en frecuencia');self.selector.addItem(value.name)
                self.selector.blockSignals(False);self.report.setPlainText(report);self.window.publish({'report':report},title='Filtro por tramos',operation='Informe de filtro por tramos');self.display();self.state.accept(snapshot)
            self.window._run_operation('Calculando filtro por tramos…',lambda:analyze(response,domain,start,int(count),step,source),accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá la definición',str(exc))
    def display(self,*_):
        index=self.selector.currentIndex()
        if 0<=index<len(self.results):self.view.show_result(self.results[index])
    def receive_response(self,value):
        self.domain.setCurrentIndex(0 if value.units=='rad/muestra' else 1);self.h.set_source(value)
