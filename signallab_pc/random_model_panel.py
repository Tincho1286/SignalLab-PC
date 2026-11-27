"""Independent model analysis and AR estimation, sharing one workflow."""
from PySide6.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QFormLayout,QScrollArea,QComboBox,QLineEdit,QCheckBox,QPushButton,QTabWidget,QLabel
from .validation import show_input_error
from .numeric_input import real_field,integer_field
from .systems_panel import parse_list,list_text
from .result_state import ResultState
from .report_view import ReportView,report_panel
from .result_summary import Section,number
from .system_result_actions import SystemResultActions
from . import random_models as models


class RandomModelPanel(QWidget):
    def __init__(self,window,action):
        super().__init__();self.window=window;self.action=action;self.source_key=None;self.sample_period_s=None;self.model=None;self.records=[];self.signals=[];self.comparison=[]
        from .toolbox import LocalInput,ResultView
        root=QHBoxLayout(self);root.setContentsMargins(6,6,6,6)
        controls=QWidget();form=QFormLayout(controls);form.setProperty('stackFields',True);form.setContentsMargins(4,4,4,4)
        self.kind=QComboBox();self.kind.addItems(['AR: autorregresivo','MA: promedio móvil','ARMA: combinación'])
        self.b=QLineEdit('1');self.a=QLineEdit('1, -0.8')
        self.mean=QLineEdit('0');self.std=QLineEdit('1')
        self.count=QLineEdit('1024');self.seed=QLineEdit('12345');self.origin=QLineEdit('0')
        self.lag=QLineEdit('40');self.points=QLineEdit('2049');self.order=QLineEdit('2')
        self.generate=QCheckBox('Generar una realización');self.generate.setChecked(action=='model')
        self.initialization=QComboBox()
        for label,mode in (('Estado estacionario','stationary'),('Reposo de x−media','rest'),('Estado manual','manual')):
            self.initialization.addItem(label,mode)
        self.initial_state=QLineEdit()
        self.initial_state.setPlaceholderText('Componentes separadas por coma')
        self.initial_state.setToolTip('Estado del filtro de las fluctuaciones x−media, en forma directa II transpuesta.')
        self.warm_up=QLineEdit('0')
        self.warm_up.setToolTip('Muestras simuladas antes del índice inicial. Se descartan y sirven para reducir el transitorio.')
        self.partial=QCheckBox('Incluir autocorrelación parcial (PACF)')
        self.sources=[];widgets=[self.lag,self.points,self.generate,self.partial,self.count,self.seed,self.origin,
                                self.initialization,self.initial_state,self.warm_up]
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
            self.sensitivity=QComboBox()
            for label,parameter in (('Sin comparación',None),('Numerador b[k]','b'),('Denominador a[k]','a'),
                                    ('Media del ruido','noise_mean'),('Desviación del ruido','noise_std')):
                self.sensitivity.addItem(label,parameter)
            self.sensitivity_index=QLineEdit('1')
            self.sensitivity_index.setToolTip('k de z⁻ᵏ. El denominador se normaliza con a[0] fijo en 1.')
            self.sensitivity_values=QLineEdit()
            self.sensitivity_values.setPlaceholderText('Valores absolutos separados por coma')
            form.addRow('Comparar variaciones de',self.sensitivity)
            form.addRow('Índice k del coeficiente',self.sensitivity_index)
            form.addRow('Valores para comparar',self.sensitivity_values)
            widgets.extend((self.sensitivity,self.sensitivity_index,self.sensitivity_values))

            def comparison_fields(*_):
                selected=self.sensitivity.currentData()
                for field,visible in ((self.sensitivity_index,selected in ('b','a')),
                                      (self.sensitivity_values,selected is not None)):
                    form.setRowVisible(field,visible)
                    field.setProperty('calculationInput',visible)

            self.sensitivity.currentIndexChanged.connect(comparison_fields)
            comparison_fields()
        else:
            self.source=LocalInput('Registro real x[n]','discrete');self.source.bind_project(window);form.addRow(self.source);self.sources=[self.source]
            form.addRow('Orden AR p',self.order);widgets.append(self.order)
        form.addRow('Retardo máximo k (muestras)',self.lag);form.addRow('Puntos del espectro',self.points);form.addRow(self.partial);form.addRow(self.generate)
        form.addRow('Muestras de la realización',self.count);form.addRow('Índice inicial',self.origin);form.addRow('Semilla reproducible',self.seed)
        form.addRow('Condición inicial',self.initialization)
        form.addRow('Vector de estado inicial',self.initial_state)
        form.addRow('Muestras de calentamiento',self.warm_up)
        def generation_fields(*_):
            enabled=self.generate.isChecked()
            for field in (self.count,self.seed,self.origin,self.initialization,self.warm_up,self.initial_state):
                visible=enabled and (field is not self.initial_state or self.initialization.currentData()=='manual')
                form.setRowVisible(field,visible)
                field.setProperty('calculationInput',visible)
        self.generate.toggled.connect(generation_fields)
        self.initialization.currentIndexChanged.connect(generation_fields)
        generation_fields()
        note=QLabel('Modelo real, causal y estable. Las curvas teóricas describen el proceso; una realización finita puede tener otros promedios. Las frecuencias se expresan en rad/muestra.');note.setWordWrap(True);form.addRow(note)
        self.calculate_button=QPushButton('Analizar modelo' if action=='model' else 'Estimar modelo AR');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);form.addRow(self.calculate_button)
        self.state=ResultState(widgets,self.calculate_button,self.sources);form.insertRow(0,self.state)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);root.addWidget(scroll,1)
        right=QWidget();box=QVBoxLayout(right);box.setContentsMargins(0,0,0,0);root.addWidget(right,2)
        self.tabs=QTabWidget();box.addWidget(self.tabs,1)
        self.report=ReportView();self.tabs.addTab(report_panel(self.report),'Informe')
        self.output=ResultView();self.selector=QComboBox();self.selector.setProperty('sessionTransient',True);result=QWidget();results=QVBoxLayout(result);results.setContentsMargins(0,0,0,0);results.addWidget(self.selector);results.addWidget(self.output,1);self.tabs.addTab(result,'Curvas y realizaciones')
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
        elif index==len(self.signals) and self.comparison:
            self.output.show_result(tuple(self.signals[k] for k in self.comparison))
            self.output.result_ids=[self.records[k] for k in self.comparison]

    def generation_parameters(self):
        mode=self.initialization.currentData()
        state=None
        if mode=='manual':
            parsed=parse_list(self.initial_state.text(),allow_empty=True)
            if parsed.imag.any():
                raise ValueError('El estado inicial de este modelo debe ser real.')
            state=parsed.real
        return (integer_field(self.count), integer_field(self.seed), integer_field(self.origin)), {
            'initialization':mode, 'warm_up':integer_field(self.warm_up,minimum=0),
            'initial_state':state,
        }

    def sensitivity_parameters(self):
        parameter=self.sensitivity.currentData()
        values=parse_list(self.sensitivity_values.text())
        if values.imag.any():
            raise ValueError('Los valores para comparar deben ser reales.')
        index=integer_field(self.sensitivity_index) if parameter in ('a','b') else None
        return parameter,values.real,index

    def calculate(self):
        try:
            lag=integer_field(self.lag);points=integer_field(self.points)
            if lag<0:raise ValueError('El retardo máximo debe ser un entero no negativo.')
            if self.action=='model':
                args=(parse_list(self.b.text()) if self.kind.currentIndex()!=0 else [1],parse_list(self.a.text()) if self.kind.currentIndex()!=1 else [1],real_field(self.mean),real_field(self.std),lag,points)
                job=lambda:models.analyze(*args);parents=[self.source_key] if self.source_key else []
            else:
                source=self.source.read();args=(source,integer_field(self.order),lag,points);job=lambda:models.fit_ar(*args);parents=[self.source.reference_id] if self.source.reference_id else []
            from .auxiliary import optional
            generate=self.generate.isChecked()
            include_partial=self.partial.isChecked()
            generation,generation_notice=optional('Datos de la realización',self.generation_parameters) if generate else (None,None)
            compare=self.action=='model' and self.sensitivity.currentData() is not None
            sensitivity,sensitivity_notice=optional('Datos del análisis de sensibilidad',self.sensitivity_parameters) if compare else (None,None)
            snapshot=self.state.snapshot()
            computed={}
            period=self.sample_period_s
            def compute():
                model=job()
                if self.action=='model':model.system.sample_period_s=period
                computed['model']=model;values=list(model.signals)
                realization,notice=optional('Realización del proceso',lambda:models.realization(model,*generation[0],**generation[1])) if generation is not None else (None,generation_notice)
                if realization is not None:values.insert(0,realization)
                computed['realization']=realization
                computed['generation_notice']=notice
                if include_partial:
                    partial,notice=optional('Autocorrelación parcial',lambda:models.model_pacf(model))
                    if partial is not None:values.append(partial)
                    computed['partial_notice']=notice
                if sensitivity is not None:
                    parameter,variants,index=sensitivity
                    comparison,notice=optional('Análisis de sensibilidad',lambda:models.sensitivity(model,parameter,variants,index=index))
                    computed['sensitivity']=comparison
                    computed['sensitivity_notice']=notice
                    if comparison is not None:
                        reference=next(index for index,value in enumerate(values) if value is model.signals[2])
                        computed['comparison']=[reference,*range(len(values),len(values)+len(comparison['spectra']))]
                        values.extend(comparison['spectra'])
                return {'system':model.system,'signals':values,'noise_mean':model.noise_mean,'noise_variance':model.noise_variance,'process_mean':model.mean,'process_variance':model.variance,'fit':model.fit}
            def accept(result):
                journal=getattr(self.window,'_result_journal',None)
                if journal is not None:
                    journal.reported(result,outputs_registered=True)
                model=computed.pop('model');values=result['signals']
                summary=models.summary(model)
                realization=computed.pop('realization')
                if realization is not None:
                    metadata=realization.metadata
                    mode=metadata['initialization_mode']
                    labels={'stationary':'Estacionaria', 'rest':'Reposo de x−media', 'manual':'Estado manual de x−media'}
                    rows=[('Condición inicial',labels[mode]),('Muestras descartadas',str(metadata['warm_up_samples']))]
                    if mode=='manual':
                        rows.append(('Estado inicial',list_text(metadata['initial_state'])))
                    explanation=('La realización puede contener transitorios. Las estadísticas teóricas describen el régimen estacionario.'
                                 if mode!='stationary' else 'El estado se sortea con la covarianza estacionaria del modelo.')
                    summary.sections.append(Section('Realización',rows=rows,paragraphs=[explanation]))
                notice=computed.pop('generation_notice',None)
                if notice:
                    summary.sections.append(Section('Realización no generada',paragraphs=[notice]))
                partial_notice=computed.pop('partial_notice',None)
                if partial_notice:
                    summary.sections.append(Section('Autocorrelación parcial',paragraphs=[partial_notice]))
                comparison_indices=computed.pop('comparison',[])
                comparison=computed.pop('sensitivity',None)
                warning=computed.pop('sensitivity_notice',sensitivity_notice)
                if comparison is not None:
                    rows=[('Modelo de referencia',f"{comparison['parameter']} = {number(comparison['reference'])}")]
                    for row in comparison['rows']:
                        detail=row.get('error')
                        if detail is None:
                            detail=f"Media {number(row['mean'])}, varianza {number(row['variance'])}, máx. |polo| {number(row['pole_radius'])}"
                        rows.append((row['label'],detail))
                    summary.sections.append(Section('Sensibilidad de las estadísticas estacionarias',rows=rows,
                        paragraphs=['Los modelos se comparan con la misma rejilla espectral y los demás parámetros fijos.']))
                elif warning:
                    summary.sections.append(Section('Sensibilidad',paragraphs=[warning]))
                report={key:value for key,value in result.items() if key not in ('signals','system')}
                report['report']=summary.plain_text()
                if comparison is not None:
                    report['sensitivity']={key:value for key,value in comparison.items() if key!='spectra'}
                system_key,keys,report_key=models.store_analysis(self.window.project,model,values,report,parents=parents,
                                                                tool=journal.origin if journal else None)
                self.window.register_publication(system_key,model.system)
                for key,value in zip(keys,values,strict=True):
                    self.window.register_publication(key,value)
                self.window.register_publication(report_key,report)
                self.model,self.signals,self.records,self.comparison=model,values,keys,comparison_indices
                self.report.set_readable(summary)
                self.selector.blockSignals(True);self.selector.clear();self.selector.addItems([value.name for value in values])
                if len(self.comparison)>1:self.selector.addItem('Comparación de densidades espectrales')
                self.selector.blockSignals(False)
                self.actions.set_result(model.system,system_key);self.actions.show();self.tabs.setCurrentIndex(0);self.state.accept(snapshot)
            self.window._run_operation('Calculando el modelo aleatorio…',compute,accept)
        except Exception as exc:show_input_error(self,'Revisá el modelo aleatorio',exc)
