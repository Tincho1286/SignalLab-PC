from .pole_zero_marks import draw_root_markers
from .numeric_input import real_field,integer_field
from .signal_plot import plot_samples
from .report_view import ReportView,report_panel
from .matrix_editor import MatrixEditor
from .tool_guide import ToolGuide
"""Herramientas MIMO conectadas al proyecto y a las transferencias existentes."""
import json
from pathlib import Path
import numpy as np
from PySide6.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QFormLayout,QLineEdit,QComboBox,QPushButton,QLabel,QPlainTextEdit,QScrollArea,QMessageBox,QToolButton,QTabWidget,QFileDialog,QCheckBox
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT
from .state_space import StateModel
from .model import Signal
from .state_simulation_inputs import StateInputSources,prepare_inputs
from .result_state import ResultState
from .result_summary import Summary,Section,Formula,number,transfer_summary
from .state_result_actions import StateModelResultActions,install_model_import
from .resources import ensure_working_set


def matrix(text):
    text=text.strip()
    if not text:return np.empty((0,0),complex)
    from .systems_panel import parse_list
    rows=[parse_list(row.strip()) for row in text.split(';')]
    if not rows or any(len(row)!=len(rows[0]) for row in rows):raise ValueError('Todas las filas de una matriz deben tener igual cantidad de columnas.')
    ensure_working_set(len(rows)*len(rows[0]),live_arrays=4)
    return np.asarray(rows,dtype=complex)


def matrix_text(value):
    def cell(value):
        z=complex(value)
        return repr(z.real) if not z.imag else str(z).strip('()').replace('j','i')
    return '; '.join(', '.join(cell(z) for z in row) for row in value)

class StateSpacePanel(QWidget):
    def __init__(self,window,action):
        super().__init__();self.window=window;self.action=action;self.model_parent=None;self.last_simulation=None
        root=QHBoxLayout(self);controls=QWidget();form=QFormLayout(controls);form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        purpose={'analysis':'Ingresá las matrices A, B, C y D de un sistema. Este análisis indica si sus estados se pueden controlar desde las entradas, observar desde las salidas y si el sistema es estable.','simulation':'Ingresá un modelo A, B, C, D y la entrada aplicada para obtener sus estados y salidas en el tiempo.','frequency':'Ingresá un modelo A, B, C, D para ver cómo responde cada salida a cada entrada según la frecuencia.','discretize':'Convertí un modelo continuo A, B, C, D a un modelo discreto usando un periodo de muestreo.','transfer':'Obtené la función de transferencia entre una entrada y una salida del modelo A, B, C, D.'}
        form.addRow(ToolGuide(purpose[action],('Entradas u','A, B, C, D','Salidas y')))
        labels={'analysis':'Analizar modelo','simulation':'Simular sistema','frequency':'Calcular respuesta','discretize':'Discretizar modelo','transfer':'Obtener transferencia'}
        self.calculate_button=QPushButton(labels[action]);self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);form.addRow(self.calculate_button)
        reuse=QToolButton();reuse.setText('Cargar modelo o sistema…');reuse.setCheckable(True);form.addRow(reuse)
        reusable=QWidget();reuse_layout=QVBoxLayout(reusable);reuse_layout.setContentsMargins(0,0,0,0)
        for title,callback in [('Copiar matrices de un modelo…',self.choose_model),('Obtener matrices desde una transferencia…',self.choose_transfer)]:
            button=QPushButton(title);button.clicked.connect(callback);reuse_layout.addWidget(button)
            if callback==self.choose_model:self.model_import=install_model_import(button,window,self.receive_model,self.choose_model,continuous_only=action=='discretize')
            if callback==self.choose_transfer:
                from .system_import import install_system_import
                self.transfer_import=install_system_import(button,window,self.receive_transfer,self.choose_transfer,domains=['analog'] if action=='discretize' else None,allow_advance=False)
        form.addRow(reusable);reusable.hide();reuse.toggled.connect(reusable.setVisible)
        self.domain=QComboBox();self.domain.addItems(['Continuo: dx/dt = Ax + Bu','Discreto: x[n+1] = Ax[n] + Bu[n]']);form.addRow('Dominio',self.domain)
        if action=='discretize':self.domain.setEnabled(False)
        self.step=QLineEdit('0.01');form.addRow('Periodo T (s)',self.step);self.form=form
        note=QLabel('Editá cada matriz en su tabla. A: estados × estados; B: estados × entradas; C: salidas × estados; D: salidas × entradas. Salida: y = Cx + Du.');note.setWordWrap(True);form.addRow(note)
        self.fields={}
        matrices=QTabWidget()
        for label,value in [('A','-1, 0; 0, -2'),('B','1; 1'),('C','1, 0; 0, 1'),('D','0; 0')]:
            self.fields[label]=MatrixEditor(value);matrices.addTab(self.fields[label],label+' · '+{'A':'Estados','B':'Entradas','C':'Salidas','D':'Paso directo'}[label])
        if action!='transfer':form.addRow(matrices)
        self.count=QLineEdit('501');self.initial=QLineEdit('0, 0');self.inputs=None
        if action=='simulation':
            self.inputs=StateInputSources(window);form.addRow(self.inputs)
            form.addRow('Estado inicial en el primer instante / índice',self.initial)
            self.decompose=QCheckBox('Separar estado cero y entrada cero');form.addRow(self.decompose)
            self.initial.setToolTip('Un valor por estado, separado por coma; vacío usa ceros. Se admiten pi, 10^(-3), fracciones y complejos. Es el estado al inicio del registro, no necesariamente en cero.')
            self.simulation_note=QLabel('');self.simulation_note.setWordWrap(True);form.addRow(self.simulation_note)
        self.w0=QLineEdit('0');self.w1=QLineEdit('10');self._frequency_domain=None;self._frequency_ranges={False:('0','10'),True:('0','pi')}
        if action=='frequency':
            form.addRow('Ω inicial (rad/s)',self.w0);form.addRow('Ω final (rad/s)',self.w1);form.addRow('Puntos',self.count)
            self.frequency_note=QLabel();self.frequency_note.setWordWrap(True);form.addRow(self.frequency_note)
        self.method=QComboBox();self.method.addItems(['Retención de orden cero (ZOH)','Bilineal (Tustin)','Euler hacia adelante','Euler hacia atrás'])
        if action=='discretize':form.addRow('Método',self.method)
        self.input_channel=QLineEdit('1');self.output_channel=QLineEdit('1')
        if action=='transfer':
            form.addRow('Canal de entrada (desde 1)',self.input_channel);form.addRow('Canal de salida (desde 1)',self.output_channel);form.addRow(matrices)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);scroll.setMinimumWidth(330);root.addWidget(scroll,1)
        right=QWidget();layout=QVBoxLayout(right);root.addWidget(right,2)
        from .active_stack import ActiveTabs
        self.result_tabs=ActiveTabs();self.result_tabs.setUsesScrollButtons(True);layout.addWidget(self.result_tabs)
        self.report=ReportView();self.report.setReadOnly(True);self.result_tabs.addTab(report_panel(self.report),'Informe')
        plot=QWidget();plot_layout=QVBoxLayout(plot);self.result_tabs.addTab(plot,'Gráfico');self.result_tabs.setTabVisible(1,action not in ('discretize','transfer'))
        self.plot_data=None
        self.plot_mode=QComboBox();self.plot_mode.addItems(['Módulo y fase','Parte real e imaginaria'])
        self.plot_channel=QComboBox();self.plot_channel.setAccessibleName('Canal que se muestra')
        self.export_plot=QPushButton('Exportar todos los canales CSV…');self.export_plot.setEnabled(False);self.export_plot.clicked.connect(self.export_channels)
        from .figure_controls import WrappedControls
        plot_controls=QWidget();plot_bar=WrappedControls(plot_controls);policy=plot_controls.sizePolicy();policy.setHeightForWidth(True);plot_controls.setSizePolicy(policy)
        if action in ('simulation','frequency'):
            for widget in (self.plot_mode,self.plot_channel,self.export_plot):plot_bar.addWidget(widget)
            plot_layout.addWidget(plot_controls)
        self.plot_mode.currentIndexChanged.connect(self.redraw_channels);self.plot_channel.currentIndexChanged.connect(self.redraw_channels)
        if self.action=='simulation':self.plot_channel.currentIndexChanged.connect(self.show_simulation_formula)
        self.figure=Figure(figsize=(7,4));self.canvas=FigureCanvasQTAgg(self.figure);self.canvas.setMinimumHeight(260);plot_layout.addWidget(NavigationToolbar2QT(self.canvas,self));plot_layout.addWidget(self.canvas,1)
        if action in ('simulation','frequency'):self.canvas._signallab_plot_controls=plot_controls
        self.model_actions=None;self.system_actions=None
        if action=='transfer':
            from .system_result_actions import SystemResultActions
            self.system_actions=SystemResultActions(window);layout.addWidget(self.system_actions)
        else:
            self.model_actions=StateModelResultActions(window,action);layout.insertWidget(0,self.model_actions)
        if action=='simulation':
            from PySide6.QtWidgets import QMenu
            bar=QHBoxLayout();layout.insertLayout(1,bar)
            self.reuse_signal=QPushButton('Usar señal en…');self.reuse_signal.setProperty('actionRole','reuse')
            self.signal_menu=QMenu(self.reuse_signal);self.reuse_signal.setMenu(self.signal_menu)
            self.signal_menu.aboutToShow.connect(self.prepare_signal_reuse);bar.addWidget(self.reuse_signal)
            self.cas_signal=QPushButton('Enviar salida a CAS');self.cas_signal.setProperty('actionRole','cas')
            self.cas_signal.clicked.connect(self.send_signal_to_cas);bar.addWidget(self.cas_signal);bar.addStretch()
            self.reuse_signal.setEnabled(False);self.cas_signal.setEnabled(False)
            from .state_simulation_results import StateSimulationResults
            self.simulation_results=StateSimulationResults(self,plot_bar)
        if action=='analysis':
            from .state_studies_panel import StateDiagnostics,StateStudy
            self.diagnostics=StateDiagnostics();self.result_tabs.addTab(self.diagnostics,'Controlabilidad / observabilidad')
            self.coordinate_study=StateStudy(window,'coordinates');self.result_tabs.addTab(self.coordinate_study,'Coordenadas')
            self.equilibrium_study=StateStudy(window,'equilibrium');self.result_tabs.addTab(self.equilibrium_study,'Equilibrio')
        self.report.setPlainText('Completá el modelo y presioná '+labels[action]+'. Los resultados se guardan en la biblioteca.')
        empty=self.figure.add_subplot(111);empty.set_axis_off();empty.text(.5,.5,'El resultado aparecerá aquí',ha='center',va='center',color='#91a0b5',transform=empty.transAxes)
        tracked=[self.domain,self.step,*self.fields.values()]
        if action=='simulation':tracked.extend([self.inputs,self.initial,self.decompose])
        elif action=='frequency':tracked.extend([self.w0,self.w1,self.count])
        elif action=='discretize':tracked.append(self.method)
        elif action=='transfer':tracked.extend([self.input_channel,self.output_channel])
        self.result_state=ResultState(tracked,self.calculate_button);form.insertRow(1,self.result_state)
        self.domain.currentIndexChanged.connect(self.configure_domain)
        if self.inputs is not None:
            for field in self.fields.values():field.model.modelReset.connect(self.configure_inputs)
        self.configure_domain()
    def configure_inputs(self,*_):
        if self.inputs is not None:
            count=(self.fields['B'] if self.fields['A'].rows.value() else self.fields['D']).columns.value()
            self.inputs.configure(count,self.domain.currentIndex()==1)
    def configure_domain(self,*_):
        discrete=self.domain.currentIndex()==1
        self.form.setRowVisible(self.step,discrete or self.action=='discretize')
        if self.inputs is not None:
            self.configure_inputs()
            self.simulation_note.setText('La entrada se evalúa en índices enteros n. El período T sólo fija su reloj físico. El estado inicial corresponde al primer índice cargado.' if discrete else 'Las entradas se mantienen constantes entre muestras (ZOH); el estado se propaga con la exponencial matricial. El estado inicial corresponde al primer instante cargado.')
        if self.action=='frequency':
            if self._frequency_domain is not None:self._frequency_ranges[self._frequency_domain]=(self.w0.text(),self.w1.text())
            self._frequency_domain=discrete;start,stop=self._frequency_ranges[discrete];self.w0.setText(start);self.w1.setText(stop)
            for title,field in [('inicial',self.w0),('final',self.w1)]:self.form.labelForField(field).setText(('ω' if discrete else 'Ω')+' '+title+(' (rad/muestra)' if discrete else ' (rad/s)'))
            self.frequency_note.setText('Se evalúa z=exp(iω), con ω en rad/muestra. El período T corresponde al modelo; no cambia el significado del eje.' if discrete else 'Se evalúa s=iΩ, con Ω en rad/s.')
    def run(self,label,job,accept):
        snapshot=self.result_state.snapshot()
        def accepted(value):
            accept(value);self.result_state.accept(snapshot)
        self.window._run_operation(label,job,accepted)
    def set_model(self,model,key=None):
        for name,field in self.fields.items():field.setText(matrix_text(getattr(model,name)))
        self.domain.setCurrentIndex(0 if model.dt is None else 1)
        if model.dt is not None:self.step.setText(str(model.dt))
        self.initial.setText(', '.join('0' for _ in range(model.states)));self.model_parent=key;self._model_name=model.name
    def read_model(self):
        data={name:matrix(field.text()) for name,field in self.fields.items()}
        if data['A'].size==0:
            if data['D'].size==0:raise ValueError('Un modelo estático necesita la matriz D.')
            if data['B'].size or data['C'].size:raise ValueError('Sin estados, B y C deben quedar vacías.')
            data['B']=np.empty((0,data['D'].shape[1]));data['C']=np.empty((data['D'].shape[0],0))
        return StateModel(**data,dt=None if self.domain.currentIndex()==0 else real_field(self.step),name=getattr(self,'_model_name','Sistema de estados'))
    def receive_model(self,model,key=None):
        if self.action=='discretize' and model.dt is not None:raise ValueError('Discretizar requiere un modelo continuo. El modelo de archivo es discreto.')
        if key is None:key=self.window.publish(model,operation='Modelo de estados cargado desde archivo')
        self.set_model(model,key)
    def choose_model(self):
        key=self.window.choose_record('state_space',domains=['continuous'] if self.action=='discretize' else None)
        if key:self.set_model(self.window.project.get(key),key)
    def choose_transfer(self):
        key=self.window.choose_record('system',domains=['analog'] if self.action=='discretize' else None)
        if not key:return
        self.receive_transfer(self.window.project.get(key),key)
    def receive_transfer(self,system,key=None):
        try:
            dt=(system.sample_period_s if system.sample_period_s is not None else real_field(self.step)) if system.domain=='digital' else None
            def accept(model):
                model_id=self.window.publish(model,operation='Transferencia a espacio de estados',parents=[key] if key else []);self.set_model(model,model_id)
            self.window._run_operation('Convirtiendo transferencia…',lambda:StateModel.from_transfer(system,dt),accept)
        except Exception as exc:QMessageBox.warning(self,'No se pudo convertir',str(exc))
    def calculate(self):
        try:
            model=self.read_model();step=real_field(self.step) if self.action=='discretize' else model.dt
            if self.action=='discretize' and (not np.isfinite(step) or step<=0):raise ValueError('El periodo debe ser positivo y finito.')
            model_id=self.window.publish(model,operation='Modelo de entrada: '+self.action,parents=[self.model_parent] if self.model_parent else [])
            if self.action=='analysis':
                def accept(data):
                    from .result_journal import snapshot as stored
                    data_id=self.window.publish(stored(data,self.window),title='Análisis de estados',operation='Controlabilidad, observabilidad y estabilidad',parents=[model_id])
                    self.diagnostics.set_result(data['diagnostics']);self.coordinate_study.set_model(model,model_id);self.equilibrium_study.set_model(model,model_id)
                    explanation=(['No hay estados dinámicos que controlar u observar.'] if model.states==0 else [
                        'Controlabilidad completa: las entradas permiten alcanzar cualquier estado.' if data['controllability_rank']==model.states else 'Controlabilidad incompleta: hay estados que no pueden alcanzarse desde las entradas.',
                        'Observabilidad completa: el estado inicial puede deducirse de las salidas y entradas conocidas.' if data['observability_rank']==model.states else 'Observabilidad incompleta: estados distintos pueden producir las mismas salidas.'])
                    self.report.set_readable(Summary('Estructura y estabilidad del modelo',[
                        Section('Modelo',rows=[('Nombre',model.name),('Dominio','Continuo' if model.dt is None else 'Discreto · T='+number(model.dt)+' s'),('Estados / entradas / salidas',f'{model.states} / {model.inputs} / {model.outputs}')]),
                        Section('Resultados',rows=[('Controlabilidad: rango / estados',str(data['controllability_rank'])+' / '+str(model.states)),('Observabilidad: rango / estados',str(data['observability_rank'])+' / '+str(model.states)),('Estabilidad interna',data['stability'])],paragraphs=explanation),
                        Section('Alcance numérico',paragraphs=['Los rangos dependen de la escala del modelo. '+data['rank_method']+'.','La estabilidad corresponde a los estados del modelo; no se deduce sólo de una transferencia con cancelaciones. Los polos se muestran en el gráfico.','Usar modelo calculado en copia estas matrices a otro estudio sin tener que recuperarlas de Resultados.'])]))
                    self.model_actions.set_result(model,model_id)
                    self.window.publish({'report':self.report.toPlainText(),'calculated_data':{'result_id':data_id}},title='Estructura y estabilidad del modelo',operation='Informe de estados',parents=[model_id,data_id])
                    journal=getattr(self.window,'_result_journal',None)
                    if journal is not None:journal.reported(data)
                    self.figure.clear();axis=self.figure.add_subplot(111);poles=[complex(*v) for v in data['poles']];draw_root_markers(axis,poles=poles);axis.legend() if poles else None
                    if model.states and not poles:axis.text(.5,.5,'Autovalores no disponibles con esta precisión',ha='center',transform=axis.transAxes)
                    if model.dt is not None:
                        angle=np.linspace(0,2*np.pi,361);axis.plot(np.cos(angle),np.sin(angle),':',alpha=.5)
                    axis.axvline(0,color='#667b97');axis.axhline(0,color='#667b97');axis.set_aspect('equal',adjustable='datalim');axis.set_xlabel('Real');axis.set_ylabel('Imaginaria');axis.grid(alpha=.2);self.figure.tight_layout();self.canvas.draw_idle()
                self.run('Analizando estados…',lambda:model.analysis(details=True),accept)
            elif self.action=='simulation':self.simulate(model,model_id)
            elif self.action=='frequency':self.frequency(model,model_id)
            elif self.action=='discretize':
                method=['zoh','bilinear','euler','backward_diff'][self.method.currentIndex()]
                def accept(discrete):
                    key=self.window.publish(discrete,operation='Discretización '+method,parents=[model_id]);self.model_actions.set_result(discrete,key)
                    self.report.set_matrices(f'Modelo discreto: {discrete.name}\n\nPeriodo T: {discrete.dt} s\nMétodo: {method}\n\nx[n+1] = A x[n] + B u[n]\ny[n] = C x[n] + D u[n]\n\nUsar modelo calculado en permite simular, analizar u obtener H(z) directamente. La entrada continua se conserva para cambiar T. ZOH supone entrada constante en cada intervalo; los demás métodos usan su aproximación correspondiente. La interpretación de los estados iniciales puede cambiar según el método.',{name:getattr(discrete,name) for name in ('A','B','C','D')});self.result_tabs.setCurrentIndex(0)
                self.run('Discretizando modelo…',lambda:model.discretize(step,method),accept)
            else:
                input_index=integer_field(self.input_channel)-1;output_index=integer_field(self.output_channel)-1
                def accept(system):
                    key=self.window.publish(system,operation='Canal de estados a transferencia',parents=[model_id]);self.system_actions.set_result(system,key)
                    summary=transfer_summary(system);rows=[('Canal',f'u{input_index+1} → y{output_index+1}'),('Estados del modelo',str(model.states))]
                    if model.dt is not None:rows.append(('Periodo T del modelo (s)',number(model.dt)))
                    summary.sections.insert(0,summary.sections.pop(1))
                    summary.sections.insert(1,Section('Canal calculado',rows=rows,paragraphs=['La transferencia relaciona la entrada y salida elegidas con estado inicial nulo. Puede ocultar modos internos no controlables u observables. Los factores exactamente comunes se cancelan antes de convertir los coeficientes a doble precisión.']))
                    self.report.set_readable(summary);self.result_tabs.setCurrentIndex(0)
                self.run('Obteniendo transferencia…',lambda:model.to_transfer(input_index,output_index),accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá el modelo',str(exc))
    def simulate(self,model,model_id):
        from .state_response_studies import simulate
        self.inputs.configure(model.inputs,model.dt is not None)
        sources=self.inputs.read();grid=prepare_inputs(model,sources)
        from .systems_panel import parse_list
        initial=np.zeros(model.states,complex) if not self.initial.text().strip() else parse_list(self.initial.text())
        source_keys=self.inputs.reference_ids();parents=[model_id]+[key for key in source_keys if key]
        separate=self.decompose.isChecked()
        self.run('Simulando sistema y componentes…',lambda:simulate(model,grid,initial,separate),lambda result:self.simulation_results.accept(result,model_id,parents,source_keys))

    def simulation_channel_id(self):
        saved=getattr(self,'_simulation_formula_report',None)
        if saved is None:return None
        _,keys=saved
        if not keys:return None
        selected=self.plot_channel.currentData()
        return keys[selected if selected is not None and 0<=selected<len(keys) else 0]

    def prepare_signal_reuse(self):
        from .toolbox import populate_signal_menu
        self.signal_menu.clear();key=self.simulation_channel_id()
        if key:populate_signal_menu(self.signal_menu,self.window,self.window.project.get(key),key)

    def send_signal_to_cas(self):
        from .cas_transfer import send_to_cas
        key=self.simulation_channel_id()
        if key:send_to_cas(self.window,key)

    def show_simulation_formula(self,*_):
        saved=getattr(self,'_simulation_formula_report',None)
        if saved is None:return
        from .temporal_formula import sections as temporal_sections
        summary,_=saved
        key=self.simulation_channel_id()
        if key is None:
            self.report.set_readable(Summary(summary.title,[Section('Sin variables en esta vista',paragraphs=['Este modelo no tiene estados dinámicos. Las entradas y salidas siguen disponibles en el selector de la figura.']),*summary.sections]));return
        channel=self.window.project.get(key)
        self.cas_signal.setText('Enviar '+channel.name+' a CAS')
        self.reuse_signal.setToolTip('Reutilizar '+channel.name+' en otra herramienta.')
        formulas=temporal_sections(channel)
        note=Section('Canal de la fórmula',paragraphs=[channel.name+' · Elegí otro canal en el selector del gráfico para consultar su expresión.'])
        self.report.set_readable(Summary(summary.title,[note,*formulas,*summary.sections]))

    def frequency(self,model,model_id):
        start,stop,count=real_field(self.w0),real_field(self.w1),integer_field(self.count)
        if not np.isfinite([start,stop]).all() or stop<=start or count<2:raise ValueError('Indicá un intervalo creciente y al menos dos puntos.')
        ensure_working_set(count*model.inputs*model.outputs,live_arrays=12);omega=np.linspace(start,stop,count);digital=model.dt is not None;units='rad/muestra' if digital else 'rad/s'
        def accept(response):
            channels=[];names=[];missing=0
            for out in range(model.outputs):
                for inp in range(model.inputs):
                    values=response[:,out,inp];finite=np.isfinite(values);missing+=int(np.count_nonzero(~finite))
                    if finite.all():
                        signal=Signal(values,start,(stop-start)/(count-1),units,f'H{out+1},{inp+1}','frequency','',{'operation':'state_space_frequency','system_domain':model.domain,'dt':model.dt,'convention':'C*(zI-A)^-1*B+D; z=exp(i*w)' if digital else 'C*(sI-A)^-1*B+D; s=i*Omega'})
                        self.window.publish(signal,operation='Respuesta de canal MIMO',parents=[model_id])
                    else:
                        self.window.publish({'omega':omega.tolist(),'units':units,'response':[[float(v.real),float(v.imag)] if good else None for v,good in zip(values,finite)],'output':out+1,'input':inp+1,'scope':'null = singular o no representable'},title=f'H{out+1},{inp+1} con puntos no finitos',operation='Respuesta MIMO con singularidades',parents=[model_id])
                    channels.append(values);names.append(f'y{out+1}/u{inp+1}')
            self.result_tabs.setCurrentIndex(1)
            self.model_actions.set_result(model,model_id)
            self.set_channels(omega,channels,names,'ω (rad/muestra)' if digital else 'Ω (rad/s)',False)
            self.report.setPlainText(f'{model.outputs} × {model.inputs} canales · {count} frecuencias\nPuntos no finitos: {missing}\n\nLa vista conjunta muestra hasta 16 canales. El selector permite ver cualquiera de ellos; el CSV incluye todos. Los puntos singulares se conservan como no disponibles, sin reemplazarlos por ceros.')
        self.run('Calculando matriz de respuesta…',lambda:model.response(omega, normalized=digital),accept)

    def set_channels(self,coordinates,channels,names,xlabel,discrete):
        if getattr(self,'_plot_axis_kind',None)!=xlabel:
            self.plot_mode.blockSignals(True);self.plot_mode.setCurrentIndex(1 if discrete or xlabel=='t (s)' else 0);self.plot_mode.blockSignals(False)
        self._plot_axis_kind=xlabel
        self.plot_data=(coordinates,channels,names,xlabel,discrete)
        self.plot_channel.blockSignals(True);self.plot_channel.clear()
        self.plot_channel.addItem('Vista conjunta (primeros 16 canales)' if len(names)>16 else 'Todos los canales',-1)
        for index,name in enumerate(names):self.plot_channel.addItem(name,index)
        self.plot_channel.blockSignals(False);self.export_plot.setEnabled(True);self.redraw_channels()

    def redraw_channels(self,*_):
        if self.plot_data is None:return
        coordinates,channels,names,xlabel,discrete=self.plot_data
        selected=self.plot_channel.currentData();selected=-1 if selected is None else selected
        indices=range(min(16,len(channels))) if selected<0 else [selected]
        polar=self.plot_mode.currentIndex()==0
        self.figure.clear();axes=self.figure.subplots(2,1,sharex=True);has_phase=False
        from .ui import SignalLabWindow
        for index in indices:
            values=channels[index];shown=SignalLabWindow._plot_indices(values)
            values=values[shown];x=coordinates[shown];finite=np.isfinite(values)
            if polar:
                first=np.where(finite,np.abs(values),np.nan);second=np.full(values.size,np.nan)
                valid=finite & (np.abs(values)>0);second[valid]=np.angle(values[valid]);has_phase=has_phase or bool(valid.any())
            else:first=np.where(finite,values.real,np.nan);second=np.where(finite,values.imag,np.nan)
            source=getattr(self,'_plot_signals',None);source=source[index] if source else None
            plot_samples(axes[0],x,first,discrete=discrete,label=names[index],source=source,component='magnitude' if polar else 'real')
            plot_samples(axes[1],x,second,discrete=discrete,label=names[index],phase=polar,source=source,component='phase' if polar else 'imag')
        axes[0].set_ylabel('Módulo' if polar else 'Parte real')
        axes[1].set_ylabel('Fase principal (rad)' if polar else 'Parte imaginaria');axes[1].set_xlabel(xlabel)
        from .signal_plot import configure_axis
        configure_axis(axes[1],discrete_index=discrete,units='rad/muestra' if 'rad/muestra' in xlabel else '')
        if polar and not has_phase:axes[1].text(.5,.5,'Fase no definida: módulo nulo o valor no finito',ha='center',transform=axes[1].transAxes)
        for axis in axes:
            axis.grid(alpha=.2)
            if channels:axis.legend(fontsize=8)
        self.figure.tight_layout();self.canvas.draw_idle()

    def export_channels(self):
        if self.plot_data is None:return
        path,_=QFileDialog.getSaveFileName(self,'Exportar todos los canales','canales.csv','Tabla CSV (*.csv)')
        if not path:return
        if not path.lower().endswith('.csv') and not Path(path).suffix:path+='.csv'
        try:
            import csv
            coordinates,channels,names,xlabel,_=self.plot_data
            # Exportar fila por fila evita duplicar todos los canales en memoria.
            with open(path,'w',newline='',encoding='utf-8-sig') as output:
                writer=csv.writer(output)
                writer.writerow([xlabel]+[name+' '+part for name in names for part in ('real','imag')])
                for row,x in enumerate(coordinates):
                    cells=[x]
                    for channel in channels:
                        value=channel[row];cells.extend((value.real,value.imag) if np.isfinite(value) else ('',''))
                    writer.writerow(cells)
            self.window.statusBar().showMessage('Canales exportados. Las celdas vacías indican valores no finitos: '+path)
        except Exception as exc:QMessageBox.warning(self,'No se pudo exportar',str(exc))
