from .numeric_input import real_field,integer_field
"""Respuesta temporal autónoma: una definición local del sistema por cálculo."""
import numpy as np
from PySide6.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QFormLayout,QComboBox,QLineEdit,QPushButton,QLabel,QScrollArea,QMessageBox,QCheckBox
from .coefficient_editor import CoefficientEditor,TransferPreview
from .history_editor import HistoryEditor
from .tool_guide import ToolGuide
from .systems_panel import parse_list,list_text

class TemporalPanel(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window;self.parent_id=None
        from .toolbox import ResultView,LocalInput
        root=QHBoxLayout(self);controls=QWidget();form=QFormLayout(controls);form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form.addRow(ToolGuide('Definí el sistema y elegí impulso, escalón o una entrada propia para ver su respuesta. Importar otro sistema es opcional.',('Entrada','Sistema H','Salida')))
        self.domain=QComboBox();self.domain.addItems(['Continuo · H(s)','Discreto · H(z)']);form.addRow('1. Tipo de sistema',self.domain)
        self.b=CoefficientEditor('1');self.a=CoefficientEditor('1,1');form.addRow('Numerador',self.b);form.addRow('Denominador',self.a)
        self.preview=TransferPreview(self.b,self.a);self.preview.setFixedHeight(100);form.addRow(self.preview)
        choose=QPushButton('Cargar sistema…');form.addRow(choose)
        from .system_import import install_system_import
        self.system_import=install_system_import(choose,window,self.set_system,self.choose,allow_advance=False);self.import_menu=self.system_import.menu;self.import_actions=self.import_menu.actions()
        self.stimulus=QComboBox();self.stimulus.addItems(['Escalón unitario','Impulso unitario','Entrada definida por mí']);form.addRow('2. Entrada aplicada',self.stimulus)
        self.duration=QLineEdit('10');self.count=QLineEdit('501');form.addRow('Duración (s)',self.duration);form.addRow('Puntos / muestras',self.count)
        taken=form.takeRow(self.stimulus);form.insertRow(2,taken.labelItem.widget(),self.stimulus)
        interval=QWidget();interval_layout=QHBoxLayout(interval);interval_layout.setContentsMargins(0,0,0,0)
        self.window_labels={}
        for field in (self.duration,self.count):
            taken=form.takeRow(field);self.window_labels[field]=taken.labelItem.widget();column=QVBoxLayout();column.addWidget(taken.labelItem.widget());column.addWidget(field);interval_layout.addLayout(column)
        form.insertRow(3,interval)
        form.takeRow(self.preview);form.insertRow(4,self.preview)
        from .transfer_input import install_formula_editor
        install_formula_editor(self,form)
        # Keep domain and definition together, before the stimulus.
        definitions=[]
        for field in (self.domain,self.definition_buttons,self.transfer_formula,self.b,self.a,self.preview):
            taken=form.takeRow(field);definitions.append((taken.labelItem.widget() if taken.labelItem else None,field))
        for i,(label,field) in enumerate(definitions):
            if label is None:form.insertRow(i,field)
            else:form.insertRow(i,label,field)
        self.definition_mode.setCurrentIndex(1);self.definition_mode.setCurrentIndex(0)
        self.form=form;self.interval=interval
        self.sample_period=QLineEdit();self.sample_period.setPlaceholderText('Sin reloj físico asignado');self.sample_period.setToolTip('T en segundos. Opcional: no cambia las muestras ni ω en rad/muestra. Si está vacío se usa el reloj de la entrada, cuando existe. Si se indica T, la entrada debe ser compatible.');form.addRow('Período T (s, opcional)',self.sample_period)
        self.continuous_input=LocalInput('Entrada x(t)','continuous');self.continuous_input.bind_project(window);self.continuous_input.count.setText('1001')
        self.discrete_input=LocalInput('Entrada x[n]','discrete');self.discrete_input.bind_project(window)
        form.addRow(self.continuous_input);form.addRow(self.discrete_input)
        self.interpolation=QComboBox();self.interpolation.addItems(['Lineal entre puntos','Constante entre puntos (retención)']);form.addRow('Interpretación de la entrada',self.interpolation)
        self.extra_count=QLineEdit('0');self.extra_count.setToolTip('Cantidad de ceros que se agregan al registro cargado. En continuo cada punto conserva el paso original y la interpolación elegida hacia el primer cero. Cero conserva el intervalo cargado.');form.addRow('Extender entrada con ceros (puntos)',self.extra_count)
        self.settling_percent=QLineEdit('2');self.settling_percent.setToolTip('Banda relativa para medir la respuesta al escalón desde reposo. Se usa el valor final del modelo estable; no se toma la última muestra como referencia.');form.addRow('Banda del escalón (%)',self.settling_percent)
        self.suggest_button=QPushButton('Sugerir intervalo desde los polos');self.suggest_button.setProperty('keepLocalAction',True);self.suggest_button.clicked.connect(self.suggest_interval);form.addRow(self.suggest_button)
        self.suggestion_note=QLabel();self.suggestion_note.setWordWrap(True);form.addRow(self.suggestion_note)
        self.stimulus.currentIndexChanged.connect(self.change_stimulus)
        self.initial_conditions=QCheckBox('Definir valores anteriores y separar respuestas');form.addRow(self.initial_conditions)
        self.previous_inputs=HistoryEditor('x');self.previous_outputs=HistoryEditor('y')
        self.b.textChanged.connect(lambda *_:self.previous_inputs.set_count(len(self.b.coefficients())-1));self.a.textChanged.connect(lambda *_:self.previous_outputs.set_count(len(self.a.coefficients())-1))
        self.previous_inputs.set_count(len(self.b.coefficients())-1);self.previous_outputs.set_count(len(self.a.coefficients())-1)
        form.addRow('Entradas anteriores x[n₀−1], x[n₀−2], …',self.previous_inputs);form.addRow('Salidas anteriores y[n₀−1], y[n₀−2], …',self.previous_outputs)
        self.history_note=QLabel('n₀ es el primer índice del registro. Editá cada valor junto a su índice. Las filas dependen del orden del sistema y comienzan en cero. La memoria previa incluye entradas y salidas; no representa necesariamente un estado interno mínimo.');self.history_note.setWordWrap(True);form.addRow(self.history_note)
        self.initial_conditions.toggled.connect(self.change_stimulus)
        self.note=QLabel();self.note.setWordWrap(True);form.addRow(self.note)
        self.calculate_button=QPushButton('Calcular respuesta');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);scroll.setMinimumWidth(330);left=QWidget();left_layout=QVBoxLayout(left);left_layout.setContentsMargins(0,0,0,0);left_layout.addWidget(scroll,1);left_layout.addWidget(self.calculate_button);root.addWidget(left,1)
        from .active_stack import ActiveTabs
        from .report_view import ReportView,report_panel
        from .response_steps_panel import ResponseStepsPanel
        self.result_tabs=ActiveTabs();self.result_tabs.setUsesScrollButtons(True);self.output=ResultView();self.input_view=ResultView();self.result_tabs.addTab(self.output,'Salida y');self.result_tabs.addTab(self.input_view,'Entrada x');self.result_tabs.setTabVisible(1,False);self.zero_state_view=ResultView();self.zero_input_view=ResultView();self.result_tabs.addTab(self.zero_state_view,'Estado cero');self.result_tabs.addTab(self.zero_input_view,'Entrada cero');self.result_tabs.setTabVisible(2,False);self.result_tabs.setTabVisible(3,False);root.addWidget(self.result_tabs,2)
        comparison=QWidget();comparison_layout=QVBoxLayout(comparison);selectors=QHBoxLayout();self.compare_input=QCheckBox('Entrada x');self.compare_parts=QCheckBox('Estado cero y entrada cero')
        for check in (self.compare_input,self.compare_parts):check.setChecked(True);selectors.addWidget(check);check.toggled.connect(self.draw_comparison)
        comparison_layout.addLayout(selectors);self.comparison=ResultView();comparison_layout.addWidget(self.comparison,1);self.comparison_index=self.result_tabs.addTab(comparison,'Comparación');self.result_tabs.setTabVisible(self.comparison_index,False)
        self.measure_report=ReportView();self.measure_index=self.result_tabs.addTab(report_panel(self.measure_report),'Medidas');self.result_tabs.setTabVisible(self.measure_index,False)
        self.steps=ResponseStepsPanel(window);self.steps_index=self.result_tabs.addTab(self.steps,'Paso a paso');self.result_tabs.setTabVisible(self.steps_index,False)
        for view in (self.input_view,self.zero_state_view,self.zero_input_view,self.comparison):view.canvas._signallab_explicit_plot=True
        self.last_snapshot=None;self.last_ids=None
        self.result_tabs.currentChanged.connect(self.open_response_tab)
        self.domain.currentIndexChanged.connect(self.change_domain);self.change_domain()
        from .result_state import ResultState
        editors=[self.domain,self.definition_mode,self.transfer_formula,self.b,self.a,self.stimulus,self.duration,self.count,self.sample_period,self.interpolation,self.extra_count,self.settling_percent,self.initial_conditions,self.previous_inputs,self.previous_outputs]
        self.result_state=ResultState(editors,self.calculate_button,[self.continuous_input,self.discrete_input])
        left_layout.insertWidget(1,self.result_state)
    def change_domain(self,*_):
        digital=self.domain.currentIndex()==1;self.b.set_domain(digital);self.a.set_domain(digital);self.preview.schedule();self.duration.setVisible(not digital);self.window_labels[self.duration].setVisible(not digital);self.window_labels[self.count].setText('Cantidad de muestras' if digital else 'Puntos de cálculo')
        self.note.setText('Escalón: 1 desde n = 0. Impulso δ[n]: 1 sólo en n = 0. Estado inicial: reposo.' if digital else 'El sistema parte del reposo. El impulso continuo δ(t) se interpreta como una distribución: si aparece en la salida, se indica su peso junto al gráfico.')
        self.form.setRowVisible(self.sample_period,digital)
        self.change_stimulus()
    def change_stimulus(self,*_):
        custom=self.stimulus.currentIndex()==2;digital=self.domain.currentIndex()==1
        self.form.setRowVisible(self.interval,not custom)
        self.form.setRowVisible(self.continuous_input,custom and not digital)
        self.form.setRowVisible(self.discrete_input,custom and digital)
        self.form.setRowVisible(self.interpolation,custom and not digital)
        self.form.setRowVisible(self.extra_count,custom);self.extra_count.setProperty('calculationInput',custom)
        self.form.setRowVisible(self.settling_percent,self.stimulus.currentIndex()==0);self.settling_percent.setProperty('calculationInput',self.stimulus.currentIndex()==0)
        self.form.setRowVisible(self.suggest_button,not custom);self.form.setRowVisible(self.suggestion_note,not custom and bool(self.suggestion_note.text()))
        self.form.setRowVisible(self.initial_conditions,digital)
        histories=digital and self.initial_conditions.isChecked()
        for field in (self.previous_inputs,self.previous_outputs,self.history_note):self.form.setRowVisible(field,histories)
        if histories:
            self.note.setText('Respuesta total = respuesta de estado cero + respuesta de entrada cero. Las condiciones anteriores se refieren al inicio del registro. Extendé el registro para observar la evolución posterior.')
        elif custom:
            self.note.setText('Estado inicial nulo en el primer índice de la entrada. Extender entrada con ceros agrega muestras posteriores para observar la cola sin reescribir la señal.' if digital else 'Estado inicial nulo en el instante inicial de la entrada. Se interpola entre puntos. La extensión agrega ceros con el mismo paso: la transición al primer cero también usa la interpolación elegida. No se reevalúa la fórmula fuera del registro.')
        else:
            self.note.setText('Escalón: 1 desde n = 0. Impulso δ[n]: 1 sólo en n = 0. Estado inicial: reposo.' if digital else 'Estado inicial: reposo en t = 0. El impulso continuo δ(t) se interpreta como una distribución; si aparece en la salida, se indica su peso junto al gráfico.')
    def set_system(self,system,key=None):
        from .transfer_input import remember_system
        self.domain.setCurrentIndex(0 if system.domain=='analog' else 1)
        self.b.setText(list_text(system.b));self.a.setText(list_text(system.a));self.parent_id=key
        remember_system(self,system)
        if system.sos is not None:self.note.setText('Filtro en secciones: se conserva la cascada al calcular desde reposo. Editar coeficientes o usar memoria inicial no nula utiliza la ecuación polinómica.')

    def choose(self):
        key=self.window.choose_record('system')
        if key:
            self.set_system(self.window.project.get(key),key)
    def open_system_file(self):
        self.system_import.open_file()
    def suggest_interval(self):
        from .transfer_input import read_system
        from .system_clock import signature
        from .temporal_analysis import suggest_window
        if getattr(self.window,'_workers',[]):return
        try:
            system=read_system(self,name='Sistema de sugerencia temporal');memory=False
            if self.domain.currentIndex()==1 and self.initial_conditions.isChecked():
                self.previous_inputs.set_count(len(system.b)-1);self.previous_outputs.set_count(len(system.a)-1)
                memory=bool(np.any(parse_list(self.previous_inputs.text(),allow_empty=True)) or np.any(parse_list(self.previous_outputs.text(),allow_empty=True)))
            current=lambda:(signature(self),self.initial_conditions.isChecked(),self.previous_inputs.text(),self.previous_outputs.text())
            original=current()
            def accept(result):
                report='Intervalo sugerido: '+str(result['count'])+' puntos.'+(' Duración: '+repr(result['duration'])+' s.' if result['duration'] is not None else '')+' '+' '.join(result['notes'])
                self.window.publish({'operation':'temporal_interval_suggestion',**result,'system':system.to_document(),'report':report},title='Intervalo temporal sugerido',operation='Sugerencia desde polos')
                if current()!=original:
                    self.suggestion_note.setText('La definición cambió: no se aplicó la sugerencia al formulario actual.')
                else:
                    self.count.setText(str(result['count']))
                    if result['duration'] is not None:self.duration.setText(repr(result['duration']))
                    self.suggestion_note.setText('Intervalo preparado; presioná Calcular respuesta. '+' '.join(result['notes']))
                self.form.setRowVisible(self.suggestion_note,True)
            self.window._run_operation('Estimando un intervalo desde los polos…',lambda:suggest_window(system,include_memory=memory),accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá el sistema',str(exc))

    def draw_comparison(self,*_):
        if self.last_snapshot is None:return
        snapshot=self.last_snapshot;signals=[snapshot['outputs'][0]];keys=[self.last_ids['outputs'][0]]
        if self.compare_input.isChecked():signals.append(snapshot['input']);keys.append(self.last_ids['input'])
        if len(snapshot['outputs'])>1 and self.compare_parts.isChecked():signals.extend(snapshot['outputs'][1:]);keys.extend(self.last_ids['outputs'][1:])
        self.comparison.show_result(tuple(signals));self.comparison.result_ids=keys

    def open_response_tab(self,index):
        if index==self.steps_index and not getattr(self,'_updating_result',False) and self.last_snapshot is not None and self.steps.trace is None:self.steps.build()

    def _accept_snapshot(self,*args):
        self._updating_result=True
        try:self._show_snapshot(*args)
        finally:self._updating_result=False

    def _show_snapshot(self,snapshot,key,parents,title,calculated_inputs):
        from .temporal_analysis import context_sections,measurement_summary
        from .result_summary import signal_summary
        key=self.window.publish(snapshot['system'],operation='Definición local de respuesta temporal',parents=[key] if key else [])
        source=snapshot['input'];separate=len(snapshot['outputs'])>1;digital=source.domain=='discrete'
        original=snapshot.get('original_input')
        if original is not None:
            parents=[self.window.publish(original,operation='Entrada cargada de respuesta temporal',parents=parents)]
        input_key=self.window.publish(source,operation='Entrada usada de respuesta temporal',parents=parents)
        outputs=list(snapshot['outputs'])
        if not separate:outputs[0]=outputs[0].copy_with(name=title)
        snapshot['outputs']=tuple(outputs);ids=[]
        for output,view in zip(outputs,(self.output,self.zero_state_view,self.zero_input_view)):
            result_id=self.window.publish(output,operation=output.name,parents=[key,input_key]);view.show_result(output);view.result_ids=[result_id];ids.append(result_id)
        if not separate:
            from .plot_view import hide_plot
            for view in (self.zero_state_view,self.zero_input_view):view.clear_result();hide_plot(view.canvas)
        self.input_view.show_result(source);self.input_view.result_ids=[input_key]
        for index in (2,3):self.result_tabs.setTabVisible(index,separate)
        self.result_tabs.setTabVisible(1,True);self.result_tabs.setTabText(1,'Entrada y extensión' if source.metadata.get('response_extension') else 'Entrada x')
        formula=outputs[0].metadata.get('temporal_formula')
        if formula:
            self.output.expression_key=self.window.publish({'result':{'result':formula['source'],'display_result':formula['expression'],'display_numeric':formula['numeric'],'output_variable':formula['variable'],'evaluated':True,'scope':formula['scope']}},title='Expresión temporal · '+title,operation=title,parents=[ids[0],key])
        summary=signal_summary(outputs[0]);summary.sections.extend(context_sections(snapshot));self.output.text.set_readable(summary)
        self.last_snapshot=snapshot;self.last_ids=dict(input=input_key,outputs=ids)
        self.compare_parts.setVisible(separate);self.draw_comparison();self.result_tabs.setTabVisible(self.comparison_index,True)
        metrics=snapshot['metrics'];self.measure_report.set_readable(measurement_summary(metrics));self.result_tabs.setTabVisible(self.measure_index,metrics is not None)
        if metrics is not None:self.window.publish({'operation':'temporal_step_measures','data':metrics,'report':self.measure_report.toPlainText()},title='Medidas del escalón',operation='Medidas del escalón',parents=[ids[0],key])
        self.steps.set_snapshot(snapshot if digital else None);self.result_tabs.setTabVisible(self.steps_index,digital)
        self.result_tabs.setCurrentIndex(0);self.result_state.accept(calculated_inputs)

    def calculate(self):
        try:
            from .transfer_input import read_system
            from .system_conditions import require_causal_roc
            from .temporal_analysis import unit_input,simulate
            digital=self.domain.currentIndex()==1;system=read_system(self,name='Sistema de respuesta temporal');require_causal_roc(system)
            custom=self.stimulus.currentIndex()==2;parents=[];kind=None;duration=None;extra=0
            interpolation='linear' if self.interpolation.currentIndex()==0 else 'hold'
            if custom:
                editor=self.discrete_input if digital else self.continuous_input;source=editor.read();parents=[editor.reference_id] if editor.reference_id else []
                extra=integer_field(self.extra_count)
                if extra<0:raise ValueError('Los puntos de extensión deben ser cero o un entero positivo.')
                title='Respuesta a entrada definida'
            else:
                count=integer_field(self.count);duration=real_field(self.duration) if not digital else None;kind='step' if self.stimulus.currentIndex()==0 else 'impulse'
                source=unit_input(system,count,kind,duration);title='Respuesta al '+('escalón' if kind=='step' else 'impulso')
            separate=digital and self.initial_conditions.isChecked();previous_inputs=();previous_outputs=()
            if separate:
                self.previous_inputs.set_count(len(system.b)-1);self.previous_outputs.set_count(len(system.a)-1)
                previous_inputs=parse_list(self.previous_inputs.text(),allow_empty=True);previous_outputs=parse_list(self.previous_outputs.text(),allow_empty=True)
            # Resolve clocks before creating any records, including optional
            # extensions. A mismatch never publishes an apparently valid input.
            if digital:
                from .system_clock import input_metadata
                source=source.copy_with(metadata=input_metadata(system,source))
            key=self.parent_id
            calculated_inputs=self.result_state.snapshot();percent=self.settling_percent.text()
            self.window._run_operation('Calculando respuesta…',lambda:simulate(system,source,kind=kind,duration=duration,extra=extra,interpolation=interpolation,separate=separate,previous_inputs=previous_inputs,previous_outputs=previous_outputs,percent=percent),lambda snapshot:self._accept_snapshot(snapshot,key,parents,title,calculated_inputs))
        except Exception as exc:QMessageBox.warning(self,'Revisá la definición',str(exc))
