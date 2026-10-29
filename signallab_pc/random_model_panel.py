"""Independent model analysis and AR estimation, sharing one workflow."""
from PySide6.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QFormLayout,QScrollArea,QComboBox,QLineEdit,QCheckBox,QPushButton,QTabWidget,QLabel,QMessageBox
from .numeric_input import real_field,integer_field
from .systems_panel import parse_list,list_text
from .result_state import ResultState
from .report_view import ReportView,report_panel
from .system_result_actions import SystemResultActions
from . import random_models as models


class RandomModelPanel(QWidget):
    def __init__(self,window,action):
        super().__init__();self.window=window;self.action=action;self.source_key=None;self.sample_period_s=None;self.model=None;self.records=[];self.signals=[]
        from .toolbox import LocalInput,ResultView
        root=QHBoxLayout(self);root.setContentsMargins(6,6,6,6)
        controls=QWidget();form=QFormLayout(controls);form.setProperty('stackFields',True);form.setContentsMargins(4,4,4,4)
        self.kind=QComboBox();self.kind.addItems(['AR: autorregresivo','MA: promedio móvil','ARMA: combinación'])
        self.b=QLineEdit('1');self.a=QLineEdit('1, -0.8')
        self.mean=QLineEdit('0');self.std=QLineEdit('1')
        self.count=QLineEdit('1024');self.seed=QLineEdit('12345');self.origin=QLineEdit('0')
        self.lag=QLineEdit('40');self.points=QLineEdit('2049');self.order=QLineEdit('2')
        self.generate=QCheckBox('Generar una realización estacionaria');self.generate.setChecked(action=='model')
        self.sources=[];widgets=[self.lag,self.points,self.generate,self.count,self.seed,self.origin]
        if action=='model':
            form.addRow('Modelo',self.kind);form.addRow('Numerador b (1, z⁻¹, z⁻²…)',self.b);form.addRow('Denominador a (1, z⁻¹, z⁻²…)',self.a)
            form.addRow('Media del ruido e[n]',self.mean);form.addRow('Desviación del ruido e[n]',self.std)
            self.import_button=QPushButton('Cargar sistema…');form.addRow(self.import_button)
            from .system_import import install_system_import
            self.system_import=install_system_import(self.import_button,window,self.set_system,lambda:None,domains=['digital'],allow_advance=False)
            widgets.extend([self.kind,self.b,self.a,self.mean,self.std])
            def configure(*_):
                form.setRowVisible(self.b,self.kind.currentIndex()!=0);form.setRowVisible(self.a,self.kind.currentIndex()!=1)
                self.b.setProperty('calculationInput',self.kind.currentIndex()!=0);self.a.setProperty('calculationInput',self.kind.currentIndex()!=1)
            self.kind.currentIndexChanged.connect(configure);configure()
        else:
            self.source=LocalInput('Registro real x[n]','discrete');self.source.bind_project(window);form.addRow(self.source);self.sources=[self.source]
            form.addRow('Orden AR p',self.order);widgets.append(self.order)
        form.addRow('Retardo máximo k (muestras)',self.lag);form.addRow('Puntos del espectro',self.points);form.addRow(self.generate)
        form.addRow('Muestras de la realización',self.count);form.addRow('Índice inicial',self.origin);form.addRow('Semilla reproducible',self.seed)
        def generation_fields(*_):
            for field in (self.count,self.seed,self.origin):
                form.setRowVisible(field,self.generate.isChecked());field.setProperty('calculationInput',self.generate.isChecked())
        self.generate.toggled.connect(generation_fields);generation_fields()
        note=QLabel('Modelo real, causal y estable. Las curvas teóricas describen el proceso; una realización finita puede tener otros promedios. Las frecuencias se expresan en rad/muestra.');note.setWordWrap(True);form.addRow(note)
        self.calculate_button=QPushButton('Analizar modelo' if action=='model' else 'Estimar modelo AR');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);form.addRow(self.calculate_button)
        self.state=ResultState(widgets,self.calculate_button,self.sources);form.insertRow(0,self.state)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);root.addWidget(scroll,1)
        right=QWidget();box=QVBoxLayout(right);box.setContentsMargins(0,0,0,0);root.addWidget(right,2)
        self.tabs=QTabWidget();box.addWidget(self.tabs,1)
        self.report=ReportView();self.tabs.addTab(report_panel(self.report),'Informe')
        self.output=ResultView();self.selector=QComboBox();result=QWidget();results=QVBoxLayout(result);results.setContentsMargins(0,0,0,0);results.addWidget(self.selector);results.addWidget(self.output,1);self.tabs.addTab(result,'Curvas y realizaciones')
        self.actions=SystemResultActions(window);self.actions.reuse.setText('Usar modelo en…');self.actions.export_button.setText('Exportar modelo…');box.addWidget(self.actions);self.actions.hide()
        self.selector.currentIndexChanged.connect(self.show_signal);self.tabs.currentChanged.connect(self.show_signal)

    def set_system(self,system,key=None):
        if self.action!='model' or system.domain!='digital' or system.advance:
            raise ValueError('El modelo requiere un sistema digital causal, sin avances temporales.')
        self.kind.setCurrentIndex(2);self.b.setText(list_text(system.b));self.a.setText(list_text(system.a));self.source_key=key;self.sample_period_s=system.sample_period_s

    def show_signal(self,*_):
        if self.tabs.currentIndex()!=1:return
        index=self.selector.currentIndex()
        if 0<=index<len(self.signals):
            self.output.show_result(self.signals[index]);self.output.result_ids=[self.records[index]]

    def calculate(self):
        try:
            lag=integer_field(self.lag);points=integer_field(self.points)
            if lag<0:raise ValueError('El retardo máximo debe ser un entero no negativo.')
            if self.action=='model':
                args=(parse_list(self.b.text()) if self.kind.currentIndex()!=0 else [1],parse_list(self.a.text()) if self.kind.currentIndex()!=1 else [1],real_field(self.mean),real_field(self.std),lag,points)
                job=lambda:models.analyze(*args);parents=[self.source_key] if self.source_key else []
            else:
                source=self.source.read();args=(source,integer_field(self.order),lag,points);job=lambda:models.fit_ar(*args);parents=[self.source.reference_id] if self.source.reference_id else []
            generate=self.generate.isChecked();generation=(integer_field(self.count),integer_field(self.seed),integer_field(self.origin)) if generate else None
            snapshot=self.state.snapshot()
            computed={}
            period=self.sample_period_s
            def compute():
                model=job()
                if self.action=='model':model.system.sample_period_s=period
                computed['model']=model;values=list(model.signals)
                if generation is not None:values.insert(0,models.realization(model,*generation))
                return {'system':model.system,'signals':values,'noise_mean':model.noise_mean,'noise_variance':model.noise_variance,'process_mean':model.mean,'process_variance':model.variance,'fit':model.fit}
            def accept(result):
                model=computed.pop('model');values=result['signals'];self.model=model;self.signals=values
                system_key=self.window.publish(model.system,operation='Modelo de proceso aleatorio',parents=parents)
                self.records=[self.window.publish(value,operation=value.name,parents=[system_key,*parents]) for value in values]
                summary=models.summary(model);self.report.set_readable(summary)
                self.selector.blockSignals(True);self.selector.clear();self.selector.addItems([value.name for value in values]);self.selector.blockSignals(False)
                self.actions.set_result(model.system,system_key);self.actions.show();self.tabs.setCurrentIndex(0);self.state.accept(snapshot)
            self.window._run_operation('Calculando el modelo aleatorio…',compute,accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá el modelo aleatorio',str(exc))
