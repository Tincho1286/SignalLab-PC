from .numeric_input import real_field,integer_field
"""Respuesta temporal autónoma: una definición local del sistema por cálculo."""
import json
import numpy as np
from .model import Signal
from .resources import ensure_working_set
from PySide6.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QFormLayout,QComboBox,QLineEdit,QPushButton,QLabel,QScrollArea,QMessageBox,QFileDialog,QMenu,QTabWidget,QCheckBox
from .coefficient_editor import CoefficientEditor,TransferPreview
from .history_editor import HistoryEditor
from .tool_guide import ToolGuide
from .filters import Transfer
from .systems_panel import parse_list,list_text
from . import control

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
        self.result_tabs=QTabWidget();self.output=ResultView();self.input_view=ResultView();self.result_tabs.addTab(self.output,'Salida y');self.result_tabs.addTab(self.input_view,'Entrada x');self.result_tabs.setTabVisible(1,False);self.zero_state_view=ResultView();self.zero_input_view=ResultView();self.result_tabs.addTab(self.zero_state_view,'Estado cero');self.result_tabs.addTab(self.zero_input_view,'Entrada cero');self.result_tabs.setTabVisible(2,False);self.result_tabs.setTabVisible(3,False);root.addWidget(self.result_tabs,2)
        self.domain.currentIndexChanged.connect(self.change_domain);self.change_domain()
        from .result_state import ResultState
        editors=[self.domain,self.definition_mode,self.transfer_formula,self.b,self.a,self.stimulus,self.duration,self.count,self.sample_period,self.interpolation,self.initial_conditions,self.previous_inputs,self.previous_outputs]
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
        self.form.setRowVisible(self.initial_conditions,digital)
        histories=digital and self.initial_conditions.isChecked()
        for field in (self.previous_inputs,self.previous_outputs,self.history_note):self.form.setRowVisible(field,histories)
        if histories:
            self.note.setText('Respuesta total = respuesta de estado cero + respuesta de entrada cero. Las condiciones anteriores se refieren al inicio del registro. Extendé el registro para observar la evolución posterior.')
        elif custom:
            self.note.setText('Estado inicial nulo en el primer índice de la entrada. Se calcula la salida sobre ese mismo registro; extendé la entrada con ceros para observar la cola.' if digital else 'Estado inicial nulo en el instante inicial de la entrada. La fórmula se evalúa en los puntos indicados y se interpola entre ellos. Reducí el paso para representar cambios rápidos; extendé la ventana para observar la cola.')
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
    def calculate(self):
        try:
            from .transfer_input import read_system
            digital=self.domain.currentIndex()==1;system=read_system(self,name='Sistema de respuesta temporal')
            from .system_conditions import require_causal_roc
            require_causal_roc(system)
            custom=self.stimulus.currentIndex()==2
            source=None;parents=[]
            if custom:
                editor=self.discrete_input if digital else self.continuous_input
                source=editor.read();parents=[editor.reference_id] if editor.reference_id else []
                if digital and system.sample_period_s is not None:
                    from .system_clock import input_metadata
                    metadata=input_metadata(system,source)
                    if any(metadata.get(key)!=source.metadata.get(key) for key in ('sample_rate_hz','time_start_s')):
                        source=source.copy_with(metadata=metadata);parents=[self.window.publish(source,operation='Entrada con reloj del sistema',parents=parents)]
                interpolation='linear' if self.interpolation.currentIndex()==0 else 'hold'
                operation=lambda:control.forced_response(system,source,interpolation)
                title='Respuesta a entrada definida'
            else:
                count=integer_field(self.count);kind='step' if self.stimulus.currentIndex()==0 else 'impulse'
                if count<2:raise ValueError('Usá al menos dos puntos o muestras.')
                duration=real_field(self.duration) if not digital else None
                from .temporal_formula import add_excitation_formula
                def operation():
                    result=system.excitation_response(count,kind) if digital else control.analog_response(system,duration,count,kind)
                    return add_excitation_formula(result,system,kind)
                title='Respuesta al '+('escalón' if kind=='step' else 'impulso')
            separate=digital and self.initial_conditions.isChecked()
            if separate:
                self.previous_inputs.set_count(len(system.b)-1);self.previous_outputs.set_count(len(system.a)-1)
                previous_inputs=parse_list(self.previous_inputs.text(),allow_empty=True);previous_outputs=parse_list(self.previous_outputs.text(),allow_empty=True)
                if source is None:
                    ensure_working_set(count,live_arrays=16)
                    values=np.ones(count) if kind=='step' else np.zeros(count);values[0]=1
                    source=Signal(values,name='Entrada escalón' if kind=='step' else 'Entrada impulso',metadata={'excitation':kind})
                    from .system_clock import input_metadata
                    source.metadata=input_metadata(system,source)
                    parents.append(self.window.publish(source,operation='Entrada de respuesta temporal'))
                operation=lambda:control.discrete_response_parts(system,source,previous_inputs,previous_outputs)
            key=self.window.publish(system,operation='Definición local de respuesta temporal' ,parents=[self.parent_id] if self.parent_id else [])
            calculated_inputs=self.result_state.snapshot()
            def accept(signal):
                self.result_tabs.setTabVisible(2,separate);self.result_tabs.setTabVisible(3,separate)
                if separate:
                    total,forced,natural=signal
                    for result,view in ((total,self.output),(forced,self.zero_state_view),(natural,self.zero_input_view)):
                        self.window.publish(result,operation=result.name,parents=[key]+parents);view.show_result(result)
                    self.input_view.show_result(source);self.result_tabs.setTabVisible(1,True);self.result_tabs.setCurrentIndex(0)
                    report='Respuesta temporal discreta con memoria inicial\n\ny[n] = y_estado_cero[n] + y_entrada_cero[n]\n\nÍndice inicial n₀: '+str(source.origin)+'\nEntradas anteriores: '+(list_text(previous_inputs) or 'Todas cero')+'\nSalidas anteriores: '+(list_text(previous_outputs) or 'Todas cero')+'\n\nEstado cero: se aplica la entrada con memoria inicial nula. Entrada cero: se anula la entrada desde n₀ y se conserva la memoria previa. Total: entrada y memoria previa actúan juntas.\n\nLos historiales se ordenan n₀−1, n₀−2, …; los valores omitidos son cero. Cada pestaña permite exportar o reutilizar su señal. La descomposición puede presentar diferencias de redondeo numérico. No se calcula la cola posterior al registro.'
                    
                    if system.sos is not None:report+='\n\nRealización: cascada de secciones para memoria nula; ecuación polinómica para memoria no nula. En órdenes altos, esta última puede perder precisión.'
                    from .result_summary import signal_summary,Section
                    summary=signal_summary(total)
                    summary.sections.append(Section('Descomposición de la respuesta',paragraphs=report.split('\n\n')))
                    self.output.text.set_readable(summary);self.result_state.accept(calculated_inputs);return
                signal=signal.copy_with(name=title)
                signal_id=self.window.publish(signal,operation=title,parents=[key]+parents);self.output.show_result(signal);self.output.result_ids=[signal_id]
                formula=signal.metadata.get('temporal_formula')
                if formula:
                    self.output.expression_key=self.window.publish({'result':{'result':formula['source'],'display_result':formula['expression'],
                        'display_numeric':formula['numeric'],'output_variable':formula['variable'],'evaluated':True,'scope':formula['scope']}},
                        title='Expresión temporal · '+title,operation=title,parents=[signal_id,key])
                self.result_tabs.setTabVisible(1,custom);self.result_tabs.setCurrentIndex(0)
                if custom:
                    self.input_view.show_result(source)
                    interpretation='Secuencia discreta; ecuación en diferencias.' if digital else ('Interpolación lineal entre puntos.' if interpolation=='linear' else 'Entrada constante entre puntos: retención de orden cero.')
                    from .result_summary import signal_summary,Section
                    report=title+'\n\ny = H{x} · Respuesta de estado cero\n\nEntrada: '+source.name+f'\nInicio: {source.origin:g} · Final: {source.axis[-1]:g}\nPuntos: {source.values.size:,}\n\n'+interpretation+'\nEl sistema parte del reposo al inicio del registro, aunque éste no comience en cero. La salida conserva el eje de la entrada. No se simula la cola posterior a la ventana: extendé la entrada con ceros para verla.\n\nLa pestaña Entrada permite consultar y exportar x; la pestaña Salida permite exportar o reutilizar y. En Parte real e imaginaria se conserva el signo de las señales reales.'
                    from .distributions import dirac_terms
                    if dirac_terms(source):report+='\n\nLos impulsos de la entrada se aplican por su posición y peso exactos. La interpolación corresponde a la parte ordinaria.'
                    summary=signal_summary(signal)
                    summary.sections.append(Section('Entrada y condiciones de la simulación',paragraphs=report.split('\n\n')))
                    self.output.text.set_readable(summary)
                self.result_state.accept(calculated_inputs)
            self.window._run_operation('Calculando respuesta…',operation,accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá la definición',str(exc))
