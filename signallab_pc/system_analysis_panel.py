from .numeric_input import real_field,integer_field
from .report_view import ReportView,report_panel
from .tool_guide import ToolGuide
from .coefficient_editor import CoefficientEditor,TransferPreview
"""Una definición de sistema, dos representaciones: algebraica y numérica."""
import numpy as np
from PySide6.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QFormLayout,QLineEdit,QComboBox,QPushButton,QLabel,QPlainTextEdit,QCheckBox,QMessageBox,QScrollArea,QTabWidget,QMenu,QSizePolicy,QFileDialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT
from .symbolic_process import run_request
from .filters import Transfer
from .resources import ensure_working_set
from .frequency_analysis import frequency_grid,analyze_frequency,frequency_summary,export_frequency

class SystemAnalysisPanel(QWidget):
    accepts_system_expressions=True
    def __init__(self,window):
        super().__init__();self.window=window;self.input_id=None
        root=QHBoxLayout(self);controls=QWidget();form=QFormLayout(controls);form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form.addRow(ToolGuide('Definí H(s) o H(z) con coeficientes o una fórmula. El análisis conserva la expresión y permite consultar módulo, fase y retardo. Copiar un resultado anterior es opcional.',('Coeficientes','Sistema H','Módulo / fase')))
        self.domain=QComboBox();self.domain.addItems(['Continuo · H(s)','Discreto · H(z)'])
        form.addRow('Sistema',self.domain)
        self.definition_mode=QComboBox();self.definition_mode.addItems(['Coeficientes','Fórmula H(s) / H(z)','Respuesta H(w)']);
        from .choice_buttons import ChoiceButtons
        self.definition_buttons=ChoiceButtons(self.definition_mode,['Coeficientes','Fórmula H','H(w)']);form.addRow(self.definition_buttons)
        self.transfer_formula=QLineEdit('1/(s+1)');form.addRow('Función de transferencia',self.transfer_formula)
        self.b=CoefficientEditor('1');self.a=CoefficientEditor('1, 1')
        form.addRow('Numerador b',self.b);form.addRow('Denominador a',self.a)
        self.transfer_preview=TransferPreview(self.b,self.a);form.addRow(self.transfer_preview)
        def definition_changed(*_):
            formula=self.definition_mode.currentIndex()!=0
            form.labelForField(self.transfer_formula).setText('Respuesta en frecuencia H(w)' if self.definition_mode.currentIndex()==2 else 'Función de transferencia')
            form.setRowVisible(self.transfer_formula,formula);form.setRowVisible(self.b,not formula);form.setRowVisible(self.a,not formula);form.setRowVisible(self.transfer_preview,not formula)
        self.definition_mode.currentIndexChanged.connect(definition_changed);definition_changed()
        self.system=None;self.analyzed_system=None;self.analysis_advance=0;self._roots_cache=None;self.frequency_data=None;self._drawn_frequency=None
        self.note=QLabel();self.note.setWordWrap(True);form.addRow(self.note)
        self.domain.currentIndexChanged.connect(self.update_note);self.definition_mode.currentIndexChanged.connect(self.update_note);self.update_note()
        self.w0=QLineEdit('0');self.w1=QLineEdit('10');self.count=QLineEdit('1001')
        self.w0.setAccessibleName('Frecuencia inicial');self.w1.setAccessibleName('Frecuencia final');self.count.setAccessibleName('Cantidad de frecuencias')
        
        frequency_range=QWidget();frequency_range.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed);range_row=QHBoxLayout(frequency_range);range_row.setContentsMargins(0,0,0,0)
        for label,field in [('Desde',self.w0),('Hasta',self.w1),('Puntos',self.count)]:
            column=QVBoxLayout();column.addWidget(QLabel(label));column.addWidget(field);range_row.addLayout(column,1)
        form.addRow('Frecuencias del análisis',frequency_range)
        self.frequency_scale=QComboBox();self.frequency_scale.addItems(['Lineal','Logarítmico'])
        self.frequency_scale.setToolTip('Logarítmico distribuye los puntos por décadas. Requiere Desde > 0; no sólo cambia las marcas del gráfico.')
        form.addRow('Eje de frecuencia',self.frequency_scale)
        self.log_note=QLabel('El eje logarítmico requiere frecuencias positivas.');self.log_note.setObjectName('muted');self.log_note.setWordWrap(True);form.addRow(self.log_note);self.log_note.hide()
        self.frequency_scale.currentIndexChanged.connect(lambda index:self.log_note.setVisible(index==1))
        self.margins=QCheckBox('Calcular cruces y márgenes de lazo abierto');form.addRow(self.margins)
        self.transfer_formula.textEdited.connect(lambda *_:self.set_definition_capabilities(self.definition_mode.currentIndex()!=2))
        self.margin_note=QLabel('H se interpreta como L, con realimentación negativa unitaria. Se buscan cruces dentro del intervalo, no un certificado global de estabilidad.');self.margin_note.setWordWrap(True);self.margin_note.setObjectName('muted');form.addRow(self.margin_note);self.margin_note.hide()
        self.margins.toggled.connect(self.margin_note.setVisible)

        self.roc_choice=QComboBox();self.roc_choice.addItems(['Secuencia derecha · exterior a polos','Secuencia izquierda · interior a polos','Anillo que contiene un radio','ROC no especificada']);form.addRow('Región de convergencia (ROC)',self.roc_choice)
        self.roc_radius=QLineEdit('1');form.addRow('Radio dentro de la ROC',self.roc_radius)
        self.roc_choice.currentIndexChanged.connect(lambda *_:form.setRowVisible(self.roc_radius,self.roc_choice.currentIndex()==2))
        self._form=form
        self.impulse=QCheckBox('Calcular también h(t) causal');form.addRow(self.impulse)
        choose=QPushButton('Copiar un sistema anterior…');choose.clicked.connect(self.choose);form.addRow(choose)
        from .system_import import install_system_import
        self.system_import=install_system_import(choose,window,self.set_system,self.choose)
        from .system_result_actions import SystemResultActions
        self.result_actions=SystemResultActions(window);self.result_actions.analysis.hide();self.result_actions.reuse_excluded={('system_analysis',0)}
        self.export_button=self.result_actions.export_button;self.send_button=self.result_actions.reuse
        self.export_button.setText('Exportar sistema…');self.send_button.setText('Usar sistema en…')
        # Editing the draft keeps the last calculated result available. ResultState
        # marks it stale, and every action uses its captured Transfer and record id.
        self.calculate_button=QPushButton('Analizar sistema');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);form.insertRow(0,self.calculate_button)
        from .result_state import ResultState
        self.result_state=ResultState([self.domain,self.definition_mode,self.b,self.a,self.transfer_formula,self.w0,self.w1,self.count,self.frequency_scale,self.margins,self.impulse,self.roc_choice,self.roc_radius],self.calculate_button);form.insertRow(1,self.result_state)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);root.addWidget(scroll,1)
        right=QWidget();layout=QVBoxLayout(right);root.addWidget(right,2)
        layout.addWidget(self.result_actions);self.frequency_export=QPushButton('Exportar respuesta…');self.frequency_export.clicked.connect(self.export_response);self.frequency_export.setEnabled(False);self.result_actions.layout().addWidget(self.frequency_export);self.result_actions.hide()
        self.expression_actions=QWidget();expression_row=QHBoxLayout(self.expression_actions);expression_row.setContentsMargins(0,0,0,0)
        expression_reuse=QPushButton('Usar sistema en…');expression_reuse.setProperty('actionRole','reuse');self.expression_menu=QMenu(expression_reuse);expression_reuse.setMenu(self.expression_menu);self.expression_menu.aboutToShow.connect(self.prepare_expression_reuse);expression_row.addWidget(expression_reuse)
        expression_cas=QPushButton('Enviar a CAS');expression_cas.setProperty('actionRole','cas')
        expression_cas.clicked.connect(self.send_expression_to_cas);expression_row.addWidget(expression_cas)
        expression_export=QPushButton('Exportar definición…');expression_export.clicked.connect(self.export_expression);expression_row.addWidget(expression_export)
        self.expression_frequency_export=QPushButton('Exportar respuesta…');self.expression_frequency_export.clicked.connect(self.export_response);expression_row.addWidget(self.expression_frequency_export)
        layout.addWidget(self.expression_actions);self.expression_actions.hide();self._definition_id=None;self._formula_context=None
        self.reuse_note=QLabel();self.reuse_note.setWordWrap(True);self.reuse_note.setObjectName('muted');layout.addWidget(self.reuse_note);self.reuse_note.hide()
        from .active_stack import ActiveTabs
        self.result_tabs=ActiveTabs();layout.addWidget(self.result_tabs)
        self.report=ReportView();self.report.setReadOnly(True);self.report.setPlainText('Ingresá coeficientes exactos (1/3, sqrt(2), pi) o parámetros.\n\nLa vista numérica se calcula cuando los coeficientes no contienen parámetros libres.');self.result_tabs.addTab(report_panel(self.report),'Definición y resultados')
        plot=QWidget();plot_layout=QVBoxLayout(plot);self.result_tabs.addTab(plot,'Respuesta en frecuencia')
        self.figure=Figure(figsize=(7,4));self.canvas=FigureCanvasQTAgg(self.figure);self.canvas.setMinimumHeight(260);self.frequency_toolbar=NavigationToolbar2QT(self.canvas,self);plot_layout.addWidget(self.frequency_toolbar);plot_layout.addWidget(self.canvas,1)
        self.magnitude_scale=QComboBox();self.magnitude_scale.addItems(['Módulo lineal','Módulo en dB']);self.magnitude_scale.setAccessibleName('Representación del módulo');self.magnitude_scale.setToolTip('Cambia la vista del resultado calculado; no modifica H ni recalcula.');self.magnitude_scale.currentIndexChanged.connect(self.draw_frequency);self.frequency_toolbar.addSeparator();self.frequency_toolbar.addWidget(self.magnitude_scale)
        self.response_components=QComboBox();self.response_components.addItems(['Módulo y ángulo','Parte real e imaginaria']);self.response_components.setAccessibleName('Componentes de la respuesta en frecuencia');self.response_components.currentIndexChanged.connect(self.draw_frequency);self.frequency_toolbar.addWidget(self.response_components)
        from .pole_zero_analysis import PoleZeroAnalysis
        self.roots_view=PoleZeroAnalysis();self.result_tabs.addTab(self.roots_view,'Polos y ceros');self.result_tabs.setTabVisible(2,False)
        from .realization_panel import RealizationPanel
        self.realization_view=RealizationPanel(window);self.result_tabs.addTab(self.realization_view,'Realización');self.result_tabs.setTabVisible(3,False)
        from .transfer_function_view import TransferFunctionView
        self.transfer_view=TransferFunctionView();self.transfer_index=self.result_tabs.addTab(self.transfer_view,'Función de transferencia');self.result_tabs.setTabVisible(self.transfer_index,False)
        from .frequency_measurements_panel import FrequencyMeasurementsPanel
        self.measurements=FrequencyMeasurementsPanel(window);self.measurements_index=self.result_tabs.addTab(self.measurements,'Medidas de frecuencia');self.result_tabs.setTabVisible(self.measurements_index,False)
        def update_roc(*_):
            digital=self.domain.currentIndex()==1
            labels=['Secuencia derecha · exterior a polos','Secuencia izquierda · interior a polos','Anillo que contiene un radio','ROC no especificada'] if digital else ['A la derecha de todos los polos','A la izquierda de todos los polos','Franja que contiene una línea σ','ROC no especificada']
            for index,label in enumerate(labels):self.roc_choice.setItemText(index,label)
            self._form.labelForField(self.roc_radius).setText('Radio dentro de la ROC' if digital else 'Parte real σ dentro de la ROC')
            self._form.setRowVisible(self.roc_radius,self.roc_choice.currentIndex()==2)
            if getattr(self,'_roc_domain',None)!=digital:self.roc_choice.setCurrentIndex(3)
            self._roc_domain=digital
        self.domain.currentIndexChanged.connect(update_roc);update_roc()
        self.result_tabs.currentChanged.connect(self._result_tab_changed);self.result_tabs.tabBar().tabBarClicked.connect(self._result_tab_changed)
        self.empty=QLabel('El análisis aparecerá después de calcular.');self.empty.setObjectName('muted');layout.addWidget(self.empty);self.result_tabs.hide()
    def inspect_system_roots(self,system,key=None):
        self.frequency_data=None;self.frequency_export.setEnabled(False);self.reuse_note.hide()
        self.measurements.set_source(None);self.result_tabs.setTabVisible(self.measurements_index,False)
        self.set_system(system,key);self.analyzed_system=system;self.analysis_advance=0;self.system=system
        self.empty.hide();self.result_tabs.show();self.result_actions.show();self.result_tabs.setTabVisible(1,False)
        self.result_tabs.setTabVisible(2,True);self.result_tabs.setTabEnabled(2,True);self.realization_view.clear_result();self.result_tabs.setTabVisible(3,True);self.export_button.setEnabled(True);self.send_button.setEnabled(True)
        from .result_summary import transfer_summary
        self.report.set_readable(transfer_summary(system));self.result_state.accept(self.result_state.snapshot())
        self.result_state.setText('Plano del filtro copiado. Analizar sistema calcula también su respuesta en frecuencia.')
        self.result_actions.set_result(self.system,self.input_id);self.result_actions.setEnabled(True)
        self.result_tabs.setTabVisible(self.transfer_index,True)
        self.show_poles_zeros()
    def _result_tab_changed(self,index):
        if index==1 and self.frequency_data is not None:
            from .plot_view import enlarge_plot
            enlarge_plot(self.canvas,self)
        elif index==2:self.show_poles_zeros()
        elif index==3:self.show_realization()
        elif index==self.transfer_index and self.analyzed_system is not None:
            self.transfer_view.set_system(self.analyzed_system)
            from .plot_view import enlarge_plot
            enlarge_plot(self.transfer_view.canvas,self.transfer_view)
    def show_realization(self):
        if self.analyzed_system is None:return
        self.realization_view.set_system(self.analyzed_system,self.analysis_advance,self.input_id if not self.analysis_advance else None)
        self.realization_view.open_diagram()
    def show_poles_zeros(self):
        if self.analyzed_system is None:return
        if self.result_tabs.currentWidget() is not self.roots_view:
            self.result_tabs.setCurrentWidget(self.roots_view);return
        system=self.analyzed_system;advance=self.analysis_advance;cached=self._roots_cache
        if cached is not None and cached[0] is system and cached[1]==advance:
            shown=self.roots_view.result
            if shown is None or shown[0] is not system or shown[3]!=advance:self.roots_view.set_result(system,*cached[2],advance)
            from .plot_view import enlarge_plot
            enlarge_plot(self.roots_view.canvas,self.roots_view);return
        if getattr(self.window,'_workers',[]):return
        from .pole_zero_analysis import analyze_roots
        self.roots_view.report.setPlainText('Calculando polos y ceros del sistema analizado…')
        def accept(result):
            if self.analyzed_system is not system or self.analysis_advance!=advance:return
            self._roots_cache=(system,advance,result)
            if self.result_tabs.currentWidget() is self.roots_view:self.show_poles_zeros()
        self.window._run_operation('Calculando polos y ceros del sistema analizado…',lambda:analyze_roots(system,advance),accept)
    def update_note(self,*_):
        digital=self.domain.currentIndex()==1;changed=digital!=getattr(self,'_noted_domain',None)
        self._noted_domain=digital
        if changed and self.transfer_formula.text() in ('1/(s+1)','1/(1-0.5*z^(-1))'):
            self.transfer_formula.setText('1/(1-0.5*z^(-1))' if digital else '1/(s+1)')
        self.b.set_domain(digital);self.a.set_domain(digital);self.transfer_preview.schedule()
        if self.definition_mode.currentIndex()==2:
            self.note.setText('Respuesta H(exp(iw)) en rad/muestra. Permite analizar filtros ideales sin atribuirles una ROC abierta.' if digital else 'Respuesta H(iw) en rad/s. No determina por sí sola una transformada de Laplace ni su ROC.')
        elif self.definition_mode.currentIndex()==1:
            self.note.setText('Fórmula en z, con potencias positivas o negativas, logaritmos u otras funciones. Frecuencia en rad/muestra.' if digital else 'Fórmula en s; se conserva como expresión cuando no es racional. Frecuencia en rad/s.')
        else:self.note.setText('b y a en potencias ascendentes de z⁻¹. Frecuencia en rad/muestra.' if digital else 'b y a en potencias descendentes de s. Frecuencia en rad/s.')
        if changed and hasattr(self,'w1'):self.w1.setText('pi' if digital else '10')
        if hasattr(self,'impulse'):
            if self.definition_mode.currentIndex()!=1:self.set_definition_capabilities(self.definition_mode.currentIndex()==0)
            self.impulse.setVisible(not digital and getattr(self,'_definition_rational',True))
            if digital:self.impulse.setChecked(False)
    def set_definition_capabilities(self,rational):
        self._definition_rational=bool(rational)
        if not hasattr(self,'_form'):return
        self._form.setRowVisible(self.roc_choice,rational)
        self._form.setRowVisible(self.roc_radius,rational and self.roc_choice.currentIndex()==2)
        self.impulse.setVisible(rational and self.domain.currentIndex()==0)
    def load_expression(self,expression,key=None,record=None,roc_spec=None):
        from copy import deepcopy
        from .transform_context import result_roc
        frequency=expression.variable=='w'
        if isinstance(record,dict) and record.get('cas_answer'):
            from .result_expressions import check_cas_destination
            check_cas_destination(record['cas_answer'],'frequency' if frequency else 'system')
        if frequency and expression.units not in ('rad/s','rad/muestra'):raise ValueError('Definí una unidad de frecuencia única: rad/s o rad/muestra. No se convierte entre ellas automáticamente.')
        from .cas_system_context import record_context
        context=record_context(record)
        target_domain='analog' if expression.variable=='s' or frequency and expression.units=='rad/s' else 'digital'
        if context and context.get('preserved') and context.get('domain')!=target_domain:raise ValueError('El sistema de origen pertenece a otro dominio. Una sustitución de letras no convierte H(s) en H(z); usá la herramienta de conversión o definí una transferencia nueva.')
        self.domain.setCurrentIndex(0 if expression.variable=='s' or frequency and expression.units=='rad/s' else 1);self.definition_mode.setCurrentIndex(2 if frequency else 1);self.transfer_formula.setText(expression.source)
        self._preserved_system=None;self._preserved_formula=None;self.input_id=key
        self._formula_context=deepcopy(record);self._formula_context_signature=(self.transfer_formula.text(),self.domain.currentIndex())
        spec=roc_spec if roc_spec is not None else result_roc(record)
        self.roc_choice.setCurrentIndex({'right':0,'left':1,'radius':2,'line':2}.get(spec.get('mode'),3) if spec else 3)
        if spec and ('radius' in spec or 'sigma' in spec):self.roc_radius.setText(str(spec.get('radius',spec.get('sigma'))))
        from .system_clock import remember_period
        from .transform_context import result_period
        remember_period(self,result_period(record) if context is not None else self.window.project.sample_period(key) if key else result_period(record))
        from .symbolic import parse,S,Z
        self.set_definition_capabilities(not frequency and bool(parse(expression.source).is_rational_function(S if expression.variable=='s' else Z)))
        self.note.setText('Fórmula cargada para análisis. Se conservan sus condiciones y soporte de origen; no se fuerza una conversión a coeficientes.')
    def prepare_expression_reuse(self):
        self.expression_menu.clear()
        if not self._definition_id:return
        from .result_expressions import populate_reuse_menu
        populate_reuse_menu(self.expression_menu,self.window,self._definition_id)
    def send_expression_to_cas(self):
        if self._definition_id:
            from .cas_transfer import send_to_cas
            send_to_cas(self.window,self._definition_id)
    def export_expression(self):
        if not self._definition_id:return
        path,_=QFileDialog.getSaveFileName(self,'Exportar definición del sistema','sistema_expresion.json','Resultado SignalLab (*.json)')
        if path:self.window.project.export_record(self._definition_id,path)
    def set_system(self,system,key=None):
        self._formula_context=None
        from .systems_panel import list_text
        from .transfer_input import remember_system
        self.definition_mode.setCurrentIndex(0);self.domain.setCurrentIndex(0 if system.domain=='analog' else 1)
        self.b.setText(list_text(system.b));self.a.setText(list_text(system.a));self.input_id=key;remember_system(self,system)
        spec=system.roc;self.roc_choice.setCurrentIndex({'right':0,'left':1,'radius':2,'line':2}.get(spec.get('mode'),3) if spec else 3)
        if spec and ('radius' in spec or 'sigma' in spec):self.roc_radius.setText(str(spec.get('radius',spec.get('sigma'))))
    def choose(self):
        key=self.window.choose_record('system')
        if not key:return
        system=self.window.project.get(key);self.set_system(system,key);record=next(r for r in self.window.project.headers() if r['id']==key)
        self.domain.setCurrentIndex(0 if system.domain=='analog' else 1);self.input_id=key
        exact=None
        for parent in record['parents']:
            candidate=self.window.project.get(parent)
            if isinstance(candidate,dict) and candidate.get('request',{}).get('operation') in ('system_analysis','system_formula'):exact=candidate['request'];break
        if exact and exact.get('operation')=='system_formula':
            self.definition_mode.setCurrentIndex(1);self.transfer_formula.setText(exact['expression'])
        elif exact:
            self.b.setText(', '.join(exact['b']));self.a.setText(', '.join(exact['a']))
        else:
            def coefficient(v):return str(float(v.real)) if not v.imag else '('+str(float(v.real))+'+'+str(float(v.imag))+'*i)'
            self.b.setText(', '.join(coefficient(v) for v in system.b));self.a.setText(', '.join(coefficient(v) for v in system.a))
            self.report.setPlainText('Se importaron coeficientes numéricos. El análisis algebraico representa estos decimales almacenados; no recupera una fórmula exacta anterior desconocida.')
    def calculate(self):
        try:
            request=dict(operation='system_analysis',domain='analog' if self.domain.currentIndex()==0 else 'digital',
                b=self.b.coefficients() if self.definition_mode.currentIndex()==0 else [],a=self.a.coefficients() if self.definition_mode.currentIndex()==0 else [],impulse=self.impulse.isChecked())
            if self.definition_mode.currentIndex()!=0:request=dict(operation='system_frequency_expression' if self.definition_mode.currentIndex()==2 else 'system_formula',expression=self.transfer_formula.text(),domain=request['domain'],impulse=self.impulse.isChecked())
            if self.definition_mode.currentIndex()!=0 and (self.transfer_formula.text(),self.domain.currentIndex())==getattr(self,'_formula_context_signature',None) and self._formula_context is not None:
                from copy import deepcopy
                request['source_calculation']=deepcopy(self._formula_context)
            preserved=getattr(self,'_preserved_system',None) if (self.definition_mode.currentIndex()==0 and (self.b.text(),self.a.text(),self.domain.currentIndex())==getattr(self,'_preserved_definition',None)) or (self.definition_mode.currentIndex()==1 and (self.transfer_formula.text(),self.domain.currentIndex())==getattr(self,'_preserved_formula',None)) else None
            from .auxiliary import optional
            logarithmic=self.frequency_scale.currentIndex()==1;with_margins=self.margins.isChecked()
            def read_grid():
                start,stop,count=real_field(self.w0),real_field(self.w1),integer_field(self.count,minimum=2)
                from .validation import ordered_interval
                ordered_interval(self.w0,self.w1,start,stop,logarithmic=logarithmic)
                return start,stop,count
            grid_request,grid_notice=optional('Intervalo de frecuencia',read_grid)
            from .system_clock import editor_period,apply_period
            period=editor_period(self)
            digital=request['domain']=='digital'
            roc_spec=({'mode':['right','left','radius' if digital else 'line'][self.roc_choice.currentIndex()],**({('radius' if digital else 'sigma'):real_field(self.roc_radius,minimum=0 if digital else None,strict=digital)} if self.roc_choice.currentIndex()==2 else {})} if self.roc_choice.currentIndex()<3 else None)
            request['roc_spec']=roc_spec
            parent=self.input_id;calculated_inputs=self.result_state.snapshot()
            def compute():
                if preserved is not None:
                    exact={'transfer':'B(z^(-1))/A(z^(-1))' if preserved.domain=='digital' else 'B(s)/A(s)','factored':'Cascada de secciones' if preserved.sos is not None else 'Numerador y denominador del filtro calculado','scope':'Se analizan los coeficientes numéricos cargados, con su realización preservada. B y A se definen en las tablas de coeficientes.','numeric_b':[[v.real,v.imag] for v in preserved.b],'numeric_a':[[v.real,v.imag] for v in preserved.a]}
                    from .phase_summary import transfer_formula
                    exact['transfer']=transfer_formula(preserved,digits=17)[0].text.split('=',1)[1].strip();exact['advance']=preserved.advance
                else:exact=run_request(request)
                omega_grid=None
                notice=grid_notice
                if grid_request is not None:
                    omega_grid,notice=optional('Rejilla de frecuencia',lambda:frequency_grid(*grid_request,logarithmic))
                system=None;data=None
                if 'numeric_b' in exact:
                    origin=request.get('source_calculation',{})
                    condition=origin.get('cas_answer',{}).get('domain_condition') or origin.get('result',{}).get('cas_domain_condition')
                    if condition:
                        from .cas_engine import restore
                        exact['cas_domain_condition']=condition
                        exact['cas_input_domain']=str(restore(condition))
                    from copy import deepcopy
                    system=deepcopy(preserved) if preserved is not None else Transfer([complex(*v) for v in exact['numeric_b']],[complex(*v) for v in exact['numeric_a']],request['domain'],'Sistema analizado',advance=exact.get('advance',0))
                    system=apply_period(system,period)
                    system.roc=roc_spec
                    from .transfer_plane import convergence
                    information=convergence(system);exact['roc']=information['text']
                    from .system_conditions import record
                    exact['mathematical_conditions']=record(system)
                    if omega_grid is not None and (not information['known'] or information['unit'] is True):
                        data,notice=optional('Respuesta en frecuencia',lambda:analyze_frequency(system,omega_grid,logarithmic=logarithmic,margins=with_margins))
                    elif information['known'] and information['unit'] is not True:exact['frequency_notice']='La ROC no contiene la frontera de Fourier. Se conservan la expresión y el análisis en el plano complejo: '+information['text']
                elif omega_grid is not None and exact.get('model_kind') in ('expression','frequency'):
                    request['roc_spec']=None;request['impulse']=False
                    from .analytic_frequency import analyze_expression
                    from .system_clock import UNSET
                    analyzed,notice=optional('Respuesta de la expresión',lambda:analyze_expression(exact,request,omega_grid,period=None if period is UNSET else period,logarithmic=logarithmic,margins=with_margins))
                    if analyzed is not None:exact,data=analyzed
                from .system_clock import UNSET
                if notice:exact['frequency_notice']=' '.join(filter(None,(exact.get('frequency_notice'),notice)))
                exact['sample_period_s']=system.sample_period_s if system is not None else None if period is UNSET else period
                return exact,system,data
            def accept(result):
                exact,system,data=result
                definition=self.window.publish({'request':request,'result':exact},title='Definición algebraica del sistema',operation='Análisis numérico y algebraico',parents=[parent] if parent else [])
                self._definition_id=definition;analytic=exact.get('model_kind') in ('expression','frequency')
                self.set_definition_capabilities(not analytic)
                self.system=None;self.analyzed_system=system;self.analysis_advance=0;self._roots_cache=None;self.realization_view.clear_result();self.result_tabs.setTabEnabled(2,False)
                self.frequency_data=data;self.frequency_export.setEnabled(data is not None)
                if system is not None:
                    self.system=system
                    if self.system is not None:self.input_id=self.window.publish(system,operation='Aproximación numérica de la definición',parents=[definition])
                else:self.input_id=definition
                self.measurements.set_source(data,self.input_id);self.result_tabs.setTabVisible(self.measurements_index,data is not None)
                if data is not None:self.draw_frequency()
                else:
                    self.figure.clear();empty=self.figure.add_subplot(111);empty.set_axis_off();empty.text(.5,.5,exact.get('frequency_notice','Asigná valores a los parámetros para obtener la respuesta numérica.'),ha='center',va='center',wrap=True,transform=empty.transAxes);self.canvas.draw_idle()
                self.result_actions.set_result(self.system,self.input_id);self.result_actions.setEnabled(True)
                message=exact.get('analysis_limits','La fórmula se conserva con sus parámetros y condiciones.') if analytic else ('El sistema conserva '+str(system.advance)+' muestras de avance. Podés exportarlo o reutilizarlo para análisis y Z inversa con ROC. La simulación causal no reemplaza ese avance por un retardo.' if system is not None and system.advance else exact.get('numeric_notice','La fórmula conserva parámetros libres. Asignales valores para exportar o reutilizar un sistema numérico.') if system is None else '')
                self.reuse_note.setText(message);self.reuse_note.setVisible(bool(message))
                self.empty.hide();self.result_tabs.show();self.result_actions.setVisible(system is not None);self.expression_actions.setVisible(analytic or system is None);self.expression_frequency_export.setEnabled(data is not None);self.result_tabs.setTabVisible(1,data is not None);self.result_tabs.setTabVisible(self.transfer_index,system is not None);self.result_tabs.setTabVisible(2,system is not None);self.result_tabs.setTabEnabled(2,system is not None);self.result_tabs.setTabVisible(3,system is not None)
                self.result_tabs.setCurrentIndex(0)
                summary=frequency_summary(exact,data)
                from .result_summary import Section
                if system is not None:
                    from .system_conditions import section
                    summary.sections.insert(0,section(system))
                if system is not None and system.sample_period_s is not None:
                    from .result_summary import Section,number
                    summary.sections.insert(0,Section('Reloj físico',rows=[('Período T (s)',number(system.sample_period_s))],paragraphs=['La frecuencia digital permanece en rad/muestra. El reloj se conserva al exportar o reutilizar el sistema.']))
                self.report.set_readable(summary);self.result_state.accept(calculated_inputs)
            self.window._run_operation('Analizando sistema algebraico y numérico…',compute,accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá el sistema',str(exc))


    def draw_frequency(self,*_):
        data=self.frequency_data
        if data is None:return
        keep=self.figure.axes[-1].get_xlim() if self.figure.axes and self._drawn_frequency is data else None
        self.figure.clear();axes=self.figure.subplots(3,1,sharex=True);omega=data.omega
        cartesian=self.response_components.currentIndex()==1;self.magnitude_scale.setEnabled(not cartesian)
        db=self.magnitude_scale.currentIndex()==1
        magnitude=np.where(np.isfinite(data.db),data.db,np.nan) if db else data.magnitude
        if cartesian:
            axes[0].plot(omega,data.response.real);axes[0].set_ylabel('Parte real')
            axes[1].plot(omega,data.response.imag);axes[1].set_ylabel('Parte imaginaria')
        else:
            axes[0].plot(omega,magnitude);axes[0].set_ylabel('Módulo (dB)' if db else '|H|')
            axes[1].plot(omega,data.phase);axes[1].set_ylabel('Fase continua (rad)' if data.phase_kind=='continuous' else 'Ángulo principal (rad)')
            if not np.isfinite(magnitude).any():
                if np.all(data.magnitude == 0):
                    message = 'Módulo cero: −∞ dB'
                elif not db and np.isfinite(data.db).any():
                    message = 'Módulo lineal fuera de rango. Usá la escala en dB.'
                else:
                    message = 'Respuesta no definida en el intervalo'
                axes[0].text(.5, .5, message, ha='center', transform=axes[0].transAxes)
            if not np.isfinite(data.phase).any():axes[1].text(.5,.5,'Ángulo no definido en el intervalo',ha='center',transform=axes[1].transAxes)
        axes[2].plot(omega,data.delay);axes[2].set_ylabel('Retardo de grupo (muestras)' if data.system.domain=='digital' else 'Retardo de grupo (s)')
        from .plot_inspection import system_curve
        components=('real','imag','delay') if cartesian else ('db' if db else 'magnitude','phase','delay')
        for axis,component in zip(axes,components):
            for line in axis.lines:system_curve(line,data.system,component,advance=data.advance-data.system.advance,phase_kind=data.phase_kind)
        if not np.isfinite(data.delay).any():axes[2].text(.5,.5,'Retardo no definido en el intervalo',ha='center',transform=axes[2].transAxes)
        from matplotlib.ticker import ScalarFormatter
        axes[2].yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
        # Exact coefficient symmetry identifies a linear-phase FIR. Do not let
        # floating derivative noise at deep notches expand a constant-delay axis.
        system=data.system
        if isinstance(system,Transfer) and system.domain=='digital' and len(system.a)==1 and not np.any(system.b.imag) and (np.array_equal(system.b,system.b[::-1]) or np.array_equal(system.b,-system.b[::-1])):
            expected=(len(system.b)-1)/2-data.advance;padding=max(.05,.05*abs(expected))
            axes[2].set_ylim(expected-padding,expected+padding)
        if data.logarithmic:axes[2].set_xscale('log')
        from .signal_plot import configure_axis
        configure_axis(axes[2],units=data.units,label=('ω' if system.domain=='digital' else 'Ω')+' ('+data.units+')')
        for axis in axes:axis.grid(alpha=.25,which='major')
        margins=data.margins
        if margins and margins['available']:
            from .theme_tokens import COLORS as C
            for key,color,label in [('gain_crossings',C['green'],'Cruce de ganancia'),('phase_crossings',C['amber'],'Cruce de fase')]:
                for index,row in enumerate(margins[key]):
                    frequency=row['frequency'];value=system.response(np.array([frequency]))[0]
                    amplitude=value.real if cartesian else 20*np.log10(abs(value)) if db else abs(value)
                    axes[0].plot([frequency],[amplitude],'o',color=color,markersize=4,label=label if index==0 else None)
                    if cartesian:axes[1].plot([frequency],[value.imag],'o',color=color,markersize=4)
                    for axis in axes:axis.axvline(frequency,color=color,alpha=.35,linestyle=':',linewidth=.8)
            if margins['gain_crossings'] or margins['phase_crossings']:
                if not cartesian:axes[0].axhline(0 if db else 1,color=C['muted'],alpha=.5,linestyle='--',linewidth=.7)
                axes[0].legend()
        axes[2].set_xlim(keep if keep is not None else (omega[0],omega[-1]))
        self.figure.set_layout_engine('constrained');self._drawn_frequency=data;self.canvas.draw_idle()

    def export_response(self):
        if self.frequency_data is None:return
        from pathlib import Path
        path,selected=QFileDialog.getSaveFileName(self,'Exportar respuesta en frecuencia','respuesta_frecuencia','Tabla CSV (*.csv);;Análisis completo JSON (*.json)')
        if not path:return
        if not Path(path).suffix:path+='.json' if 'JSON' in selected else '.csv'
        try:
            export_frequency(self.frequency_data,path);self.window.statusBar().showMessage('Respuesta calculada exportada: '+path)
        except Exception as exc:QMessageBox.warning(self,'No se pudo exportar la respuesta',str(exc))
