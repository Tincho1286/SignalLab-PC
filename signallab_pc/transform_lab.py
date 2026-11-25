"""One transform document: explicit inputs, conditions and optional output samples."""
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QComboBox,QLineEdit,QLabel,QPushButton,QScrollArea,QMessageBox,QCheckBox,QTabWidget,QMenu
from .validation import show_input_error
from .expression_editor import ExpressionEditor
from .report_view import ReportView,report_panel
from .symbolic_process import run_request
from .numeric_input import integer_field,real_field
from .model import Signal
from .choice_buttons import ChoiceButtons
from .result_state import ResultState
from .result_summary import transform_summary
from .wrapping_row import WrappingRow
from .field_section import FieldSection

class TransformLab(QWidget):
    def __init__(self,window,kind):
        super().__init__();self.window=window;self.kind=kind;self.last=None;self.records={};self._mode_index=0
        self._sample_ids = {}
        from .toolbox import ResultView,LocalInput
        root=QHBoxLayout(self);left=QWidget();form=QFormLayout(left);self.form=form;form.setProperty("stackFields",True)
        self.mode=QComboBox();self.mode.addItems(['Directa','Inversa']);form.addRow('Operación',ChoiceButtons(self.mode))
        self.direct_input=QComboBox();self.direct_input.addItems(['Expresión x[n]','Secuencia finita']);self.direct_buttons=ChoiceButtons(self.direct_input);form.addRow('Definición de la secuencia',self.direct_buttons)
        self.interpretation=QComboBox();self.interpretation.addItems(['Unilateral / causal','Bilateral · con ROC']);form.addRow('Interpretación',self.interpretation)
        self.laplace_roc=QComboBox();self.laplace_roc.addItems(['A la derecha de todos los polos','A la izquierda de todos los polos','Franja que contiene una línea elegida']);form.addRow('Región de convergencia (ROC)',self.laplace_roc)
        self.sigma=QLineEdit('0');form.addRow('Parte real σ dentro de la ROC',self.sigma)
        self.definitions={0:'(1/2)^n' if kind=='z' else 'exp(-t)',1:'z/(z-1/2)' if kind=='z' else '1/(s+1)'}
        self.expression=ExpressionEditor(self.definitions[0],symbolic=True);form.addRow('Expresión',self.expression)
        self.expression_actions = WrappingRow()
        self.load_expression_button=QPushButton('Cargar expresión…');self.load_expression_button.clicked.connect(self.choose_expression)
        self.expression_actions.flow.addWidget(self.load_expression_button)
        self.input_reuse_button = QPushButton('Usar entrada en…')
        input_reuse = QMenu(self.input_reuse_button)
        variable = 'z' if kind == 'z' else 's'
        input_reuse.addAction(f'Analizar como H({variable})', self.to_system)
        self.input_reuse_button.setMenu(input_reuse)
        self.expression_actions.flow.addWidget(self.input_reuse_button)
        form.addRow(self.expression_actions)
        self.lower=QLineEdit('0');self.upper=QLineEdit('oo');form.addRow('Primer índice del soporte',self.lower);form.addRow('Último índice del soporte',self.upper)
        self.roc=QComboBox();self.roc.addItems(['Exterior a los polos · secuencia derecha','Interior a los polos · secuencia izquierda','Anillo que contiene un radio elegido']);form.addRow('Región de convergencia (ROC)',self.roc)
        self.radius=QLineEdit('1');form.addRow('Radio dentro de la ROC',self.radius)
        self.roc_button=QPushButton('Explorar ROC…');self.roc_button.setToolTip('Elegir una región abierta en el plano de polos y aplicarla a la inversa.');self.roc_button.clicked.connect(self.explore_roc);form.addRow(self.roc_button)
        self.sample_settings=FieldSection('Muestras de la inversa')
        samples_form = self.sample_settings.form
        self.include_samples=QCheckBox('Generar un registro numérico');self.include_samples.setChecked(True);samples_form.addRow(self.include_samples)
        self.sample_scope=QComboBox();self.sample_scope.addItems(['Intervalo indicado','Automático según el soporte']);self.sample_scope.setToolTip('Con soporte finito se muestra toda la secuencia. Con soporte infinito se usa el intervalo indicado.');samples_form.addRow('Intervalo',self.sample_scope)
        self.start=QLineEdit('-16');self.count=QLineEdit('65');samples_form.addRow('Primer índice a visualizar',self.start);samples_form.addRow('Cantidad de muestras',self.count)
        form.addRow(self.sample_settings)
        self.source=LocalInput('Secuencia finita','discrete');self.source.bind_project(window);form.addRow(self.source)
        self.note=QLabel();self.note.setObjectName('muted');self.note.setWordWrap(True);form.addRow(self.note)
        self.copy_note=QLabel();self.copy_note.setObjectName('muted');self.copy_note.setWordWrap(True);form.addRow(self.copy_note);self.copy_note.hide()
        self.expression.textChanged.connect(lambda *_:self.set_copy_note(''))
        self.calculate_button=QPushButton('Calcular transformada');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);form.addRow(self.calculate_button)
        fields=[self.mode,self.direct_input,self.sample_scope,self.interpretation,self.laplace_roc,self.sigma,self.expression,self.lower,self.upper,self.roc,self.radius,self.include_samples,self.start,self.count]
        self.result_state=ResultState(fields,self.calculate_button,[self.source]);form.insertRow(0,self.result_state)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(left);root.addWidget(scroll,1)
        right=QWidget();layout=QVBoxLayout(right);layout.setContentsMargins(0,0,0,0);root.addWidget(right,2)
        from .result_toolbar import ResultActionBar,attach
        self.result_actions=ResultActionBar();result_actions=self.result_actions.layout();layout.addWidget(self.result_actions)
        self.reuse_button=QPushButton('Usar expresión en…')
        self.reuse_button.setProperty('actionRole','reuse');self.reuse_button.setEnabled(False)
        menu=QMenu(self.reuse_button);self.reuse_button.setMenu(menu);menu.aboutToShow.connect(self.prepare_reuse)
        result_actions.addWidget(self.reuse_button)
        self.to_cas_button=QPushButton('Enviar a CAS');self.to_cas_button.setProperty('actionRole','cas');self.to_cas_button.setToolTip('Abrir la expresión del último resultado calculado como una celda de la hoja CAS.');self.to_cas_button.clicked.connect(self.to_cas);self.to_cas_button.hide();result_actions.addWidget(self.to_cas_button)
        self.cas_menu = QMenu(self.to_cas_button)
        self.cas_menu.aboutToShow.connect(self.prepare_cas)
        self.tabs=QTabWidget();layout.addWidget(self.tabs,1);self.report=ReportView();self.tabs.addTab(report_panel(self.report),'Expresión y condiciones');attach(self.tabs,self.result_actions);self.result_actions.use_report(self.report)
        self.output=ResultView();self.output.show_action_bar=False;self.tabs.addTab(self.output,'Muestras de la inversa');self.tabs.setTabVisible(1,False)
        self.steps=ReportView();self.steps_index=self.tabs.addTab(report_panel(self.steps),'Desarrollo');self.tabs.setTabVisible(self.steps_index,False)
        def update(*_):
            index=self.mode.currentIndex();changed=index!=self._mode_index
            if changed:
                self.definitions[self._mode_index]=self.expression.text();self._mode_index=index;self.expression.setText(self.definitions[index])
            inverse=index==1;z=kind=='z';finite=z and not inverse and self.direct_input.currentIndex()==1;samples=z and inverse and self.include_samples.isChecked();bilateral=not z and self.interpretation.currentIndex()==1
            self.expression.setProperty('variableHint', ('z' if z else 's') if inverse else ('n' if z else 't'))
            form.setRowVisible(self.direct_buttons,z and not inverse);form.setRowVisible(self.expression_actions,not finite)
            self.input_reuse_button.setVisible(inverse)
            form.setRowVisible(self.roc_button,inverse)
            form.setRowVisible(self.interpretation,not z);form.setRowVisible(self.laplace_roc,bilateral and inverse);form.setRowVisible(self.sigma,bilateral and inverse and self.laplace_roc.currentIndex()==2)
            form.labelForField(self.expression).setText(('X(z)' if z else 'X(s)') if inverse else ('x[n]' if z else 'x(t)'))
            form.setRowVisible(self.expression,not finite);form.setRowVisible(self.source,finite)
            for field in (self.lower,self.upper):form.setRowVisible(field,z and not inverse and not finite)
            form.setRowVisible(self.roc,z and inverse);form.setRowVisible(self.radius,z and inverse and self.roc.currentIndex()==2)
            form.setRowVisible(self.sample_settings,z and inverse)
            for field in (self.sample_scope,self.start,self.count):samples_form.setRowVisible(field,samples)
            form.setRowVisible(self.copy_note,not finite and bool(self.copy_note.text()))
            if z and inverse:
                note='La expresión describe toda la secuencia. El gráfico y la tabla muestran el intervalo de muestras.'
            elif z:
                note='La secuencia vale cero fuera del registro.' if finite else 'Podés usar -oo y oo para un soporte infinito. Se incluyen los extremos finitos.'
            elif bilateral:
                note='Elegí la región de convergencia para obtener la inversa.' if inverse else 'Incluí la señal para t<0. Usá escalones o tramos si necesitás indicar su soporte.'
            else:
                note='La inversa vale cero para t<0.' if inverse else 'La transformada unilateral comienza en 0−.'
            if inverse and ((z and self.roc.currentIndex()<0) or (bilateral and self.laplace_roc.currentIndex()<0)):
                note='El resultado de origen no indica una región de convergencia. Elegila antes de calcular.'
            self.note.setText(note)
            tracked=[self.mode]
            if not z:tracked.append(self.interpretation)
            if bilateral and inverse:
                tracked.append(self.laplace_roc)
                if self.laplace_roc.currentIndex()==2:tracked.append(self.sigma)
            if finite:tracked += [self.source.mode,self.source.expression,self.source.samples,self.source.origin,self.source.count,self.source.step]
            else:tracked.append(self.expression)
            if z and index==0:
                tracked.append(self.direct_input)
                if not finite:tracked += [self.lower,self.upper]
            if z and inverse:
                tracked += [self.roc,self.include_samples,self.sample_scope]
                if self.roc.currentIndex()==2:tracked.append(self.radius)
                if samples:tracked += [self.start,self.count]
            self.result_state.widgets=tracked;self.result_state.sources=[self.source] if finite else []
            if changed:self.display_record(self.records.get(self.record_key()))
            self.result_state.refresh()
        self._update_form=update
        self.interpretation.currentIndexChanged.connect(update);self.laplace_roc.currentIndexChanged.connect(update)
        self.direct_input.currentIndexChanged.connect(lambda *_:(self.display_record(self.records.get(self.record_key())),update()));self.sample_scope.currentIndexChanged.connect(update)
        self.mode.currentIndexChanged.connect(update);self.roc.currentIndexChanged.connect(update);self.include_samples.toggled.connect(update);update();self.display_record(None)
    def explore_roc(self):
        if self.mode.currentIndex()!=1:return
        expression=self.expression.text();request={'operation':'roc_regions','kind':self.kind,'expression':expression}
        def accept(data):
            if self.expression.text()!=expression or self.mode.currentIndex()!=1:
                self.window.statusBar().showMessage('La definición cambió. Abrí de nuevo el selector de ROC.');return
            from .roc_picker import RocPicker
            self.window.publish({'report':data['report']+'\n'+data['scope'],'roc_regions':data},title='Regiones de convergencia',operation='Explorar ROC')
            previous=getattr(self,'roc_picker',None)
            if previous is not None:previous.close()
            self.roc_picker=RocPicker(self,data);self.roc_picker.show()
        self.window._run_operation('Identificando polos y regiones de convergencia…',lambda:run_request(request),accept)

    def record_key(self):
        return (self.mode.currentIndex(),self.direct_input.currentIndex() if self.kind=='z' and self.mode.currentIndex()==0 else 0)
    def choose_expression(self):
        variable=('z' if self.kind=='z' else 's') if self.mode.currentIndex()==1 else ('n' if self.kind=='z' else 't')
        key=self.window.choose_record('expression',variables=[variable,None])
        if not key:return
        value=self.window.project.expression(key)
        self.expression.setText(value.source);self._library_source=(self.expression.text(),key)
        self._library_conditions=tuple(value.conditions)
        if self.mode.currentIndex()==1:
            self.load_transform_context(self.window.project.get(key))
        self.set_copy_note('Expresión cargada desde Resultados.'+(' Condiciones: '+'; '.join(value.conditions) if value.conditions else ''))
    def use_finite_input(self):
        self.mode.setCurrentIndex(0);self.direct_input.setCurrentIndex(1)
    def load_laplace_context(self,request,result=None,inverse=False):
        if self.kind!='laplace':return
        self.interpretation.setCurrentIndex(1 if request.get('interpretation')=='bilateral' else 0)
        hint=(result or {}).get('inverse_laplace_hint') if inverse else request
        if hint and self.interpretation.currentIndex()==1:
            self.laplace_roc.setCurrentIndex({'right':0,'left':1,'line':2}.get(hint.get('laplace_roc'),0))
            if hint.get('sigma') is not None:self.sigma.setText(str(hint['sigma']))
    def load_transform_context(self,record):
        from .transform_context import result_roc
        spec=result_roc(record)
        if self.kind=='z':
            self.roc.setCurrentIndex({'right':0,'left':1,'radius':2}.get(spec.get('mode'),-1) if spec else -1)
            if spec and 'radius' in spec:self.radius.setText(str(spec['radius']))
        else:
            self.interpretation.setCurrentIndex(1)
            self.laplace_roc.setCurrentIndex({'right':0,'left':1,'line':2}.get(spec.get('mode'),-1) if spec else -1)
            if spec and 'sigma' in spec:self.sigma.setText(str(spec['sigma']))
    def select_legacy(self,key):
        self.mode.setCurrentIndex(1 if key in (('symbolic',1),('symbolic',3),('course_tools','inverse_z')) else 0)
        if key==('symbolic',2):self.use_finite_input()
    def set_system(self,system,key=None):
        from .phase_summary import transfer_formula
        expression=transfer_formula(system,digits=17)[0].text.split('=',1)[1].strip()
        self.mode.setCurrentIndex(1);self.expression.setText(expression);self._system_source=(expression,key)
        if system.roc is None:
            if self.kind=='z':self.roc.setCurrentIndex(-1)
            else:self.interpretation.setCurrentIndex(1);self.laplace_roc.setCurrentIndex(-1)
        if self.kind=='z' and system.roc is not None:
            self.roc.setCurrentIndex({'right':0,'left':1,'radius':2}[system.roc['mode']])
            if 'radius' in system.roc:self.radius.setText(str(system.roc['radius']))
        if self.kind=='laplace' and system.roc is not None:
            self.interpretation.setCurrentIndex(1);self.laplace_roc.setCurrentIndex({'right':0,'left':1,'line':2}[system.roc['mode']])
            if 'sigma' in system.roc:self.sigma.setText(str(system.roc['sigma']))
    def set_copy_note(self,text):
        self.copy_note.setText(text)
        # QFormLayout owns row visibility. Showing only its hidden child leaves
        # an unmanaged widget over the controls, with its default 640x480 size.
        finite = self.kind=='z' and self.mode.currentIndex()==0 and self.direct_input.currentIndex()==1
        self.form.setRowVisible(self.copy_note,not finite and bool(text))
    def display_record(self,record):
        self.to_cas_button.setText('Enviar a CAS');self.to_cas_button.setMenu(None);self.to_cas_button.show();self.to_cas_button.setEnabled(False);self.tabs.setTabVisible(1,False);self.tabs.setTabVisible(self.steps_index,False);self.tabs.setCurrentIndex(0)
        self.reuse_button.setText('Usar señal en…' if self.mode.currentIndex()==1 else 'Usar espectro en…')
        if record is None:
            self.reuse_button.setEnabled(False)
            self.last=None;self.result_state.completed=None;self.report.setPlainText('Completá la entrada y calculá. Aquí aparecerán la expresión y sus condiciones.');return
        request,result,key,snapshot,signal=record;self.last=result;self.report.set_readable(transform_summary(request,result));self.result_state.accept(snapshot)
        from .transform_steps import summary as steps_summary
        self.steps.set_readable(steps_summary(result.get('derivation',[])));self.tabs.setTabVisible(self.steps_index,bool(result.get('derivation')))
        if result.get('boundary_dtft'):self.to_cas_button.setText('Enviar DTFT al CAS')
        elif result.get('boundary_fourier'):self.to_cas_button.setText('Enviar espectro de Fourier al CAS')
        expression = self.window.project.expression(key)
        sample_id = self._sample_ids.get(key)
        self.to_cas_button.setEnabled(expression is not None or sample_id is not None)
        if sample_id is not None:self.to_cas_button.setMenu(self.cas_menu)
        self.reuse_button.setEnabled(expression is not None or sample_id is not None)
        if expression is not None and expression.variable in ('z', 's'):
            self.reuse_button.setText('Usar expresión en…')
        if signal is not None:
            self.output.show_result(signal)
            self.output.result_ids = [sample_id]
            self.tabs.setTabVisible(1,True)
    def prepare_reuse(self):
        from .result_expressions import populate_reuse_menu
        menu=self.reuse_button.menu();menu.clear()
        record=self.records.get(self.record_key())
        if record is None:return
        handlers = None
        if self.mode.currentIndex()==0:
            result = record[1]
            variable = 'z' if self.kind=='z' else 's'
            inverse = 'Z inversa' if self.kind=='z' else 'Laplace inversa'
            analysis = 'Analizar respuesta H(exp(iw))' if result.get('boundary_dtft') else f'Analizar como H({variable})'
            handlers = {'inverse': (inverse, self.to_inverse), 'system': (analysis, self.to_system)}
            if result.get('boundary_fourier'):
                # The frequency destination must receive the angular spectrum and its units.
                handlers.pop('system')
        populate_reuse_menu(menu,self.window,record[2],handlers=handlers)
        sample_id = self._sample_ids.get(record[2])
        if sample_id is not None:
            from .toolbox import populate_signal_menu
            self._sample_routes = populate_signal_menu(menu.addMenu('Muestras de la inversa'),self.window,record[4],sample_id)
    def prepare_cas(self):
        self.cas_menu.clear()
        record = self.records.get(self.record_key())
        if record is None:return
        key = record[2]
        if self.window.project.expression(key) is not None:
            self.cas_menu.addAction('Fórmula de la secuencia',self.to_cas)
        sample_id = self._sample_ids.get(key)
        if sample_id is not None:
            from .cas_transfer import send_to_cas
            self.cas_menu.addAction('Muestras de la inversa',lambda:send_to_cas(self.window,sample_id))
    def to_cas(self):
        record=self.records.get(self.record_key())
        if record is not None:
            from .cas_transfer import send_to_cas
            send_to_cas(self.window,record[2])
    def to_inverse(self):
        record=self.records.get(self.record_key())
        if record is None:return
        request,result,*_=record;branches=result.get('branches',[])
        expression=branches[0]['expression'] if branches else result['result']
        self.definitions[1]=expression;self.mode.setCurrentIndex(1)
        if self.kind=='z':
            self.roc.setCurrentIndex(1 if result.get('inverse_roc_hint')=='left' else 0)
            if request['operation']=='z_finite':self.include_samples.setChecked(True);self.sample_scope.setCurrentIndex(1)
        else:self.load_laplace_context(request,result,inverse=True)
        self.load_transform_context({'request':request,'result':result})
        condition=branches[0]['condition'] if branches else result.get('convergence',result.get('roc_finite_plane',''))
        self.set_copy_note('Se copió la expresión del último resultado.'+(' Condición original: '+condition+'. Elegí una ROC compatible para recuperar la misma señal.' if self.kind=='z' else (' La ROC se trasladó a la inversa; comprobá sus condiciones.' if result.get('inverse_laplace_hint') else ' Elegí una ROC compatible con las condiciones de la directa.' if request.get('interpretation')=='bilateral' else ' La inversa usa interpretación causal.')))
        self._inverse_source=(expression,record[2])
    def to_system(self):
        try:
            origin_location=self.window.capture_handoff() if hasattr(self.window,'capture_handoff') else None
            inverse=self.mode.currentIndex()==1;record=self.records.get(self.record_key());parents=[]
            if inverse:
                expression=self.expression.text()
                if record is not None and expression==record[0].get('expression'):parents=[record[2]]
                else:
                    for attribute in ('_system_source','_inverse_source','_library_source'):
                        source=getattr(self,attribute,None)
                        if source and source[0]==expression and source[1]:parents=[source[1]];break
            else:
                if record is None:return
                result=record[1];branches=result.get('branches',[])
                if result.get('evaluated') is False and not result.get('boundary_dtft') or len(branches)>1:raise ValueError('Elegí una expresión evaluada única antes de analizarla como sistema.')
                expression=result['boundary_dtft'] if result.get('boundary_dtft') else branches[0]['expression'] if branches else result['result'];parents=[record[2]]
            from .workspaces import ROUTES
            from .result_expressions import ExpressionResult
            from .transform_context import result_roc
            domain='digital' if self.kind=='z' else 'analog'
            origin={'request':record[0],'result':record[1]} if record is not None and not inverse else self.window.project.get(parents[0]) if parents else None
            roc_spec=({'mode':['right','left','radius'][self.roc.currentIndex()],**({'radius':real_field(self.radius)} if self.roc.currentIndex()==2 else {})} if self.kind=='z' and inverse and self.roc.currentIndex()>=0 else ({'mode':['right','left','line'][self.laplace_roc.currentIndex()],**({'sigma':real_field(self.sigma)} if self.laplace_roc.currentIndex()==2 else {})} if self.interpretation.currentIndex()==1 and self.laplace_roc.currentIndex()>=0 else {'mode':'right'} if self.interpretation.currentIndex()==0 else None) if self.kind=='laplace' and inverse else result_roc(origin) if origin else None)
            self.window.open_tool(ROUTES['system_analysis',0]);panel=self.window.pages[self.window.current_operation].panel
            boundary=isinstance(origin,dict) and bool(origin.get('result',{}).get('boundary_dtft'))
            panel.load_expression(ExpressionResult(expression,'w' if boundary else 'z' if domain=='digital' else 's',units='rad/muestra' if boundary else ''),parents[0] if parents else None,origin,roc_spec)
            label='Fórmula cargada como H('+('exp(iw)' if boundary else 'z' if domain=='digital' else 's')+')'
            if hasattr(self.window,'finish_handoff'):
                self.window.finish_handoff(origin_location,label,parents[0] if parents else None,panel.transfer_formula)
            else:self.window.statusBar().showMessage(label+'. Revisá las condiciones y calculá el análisis.')
        except Exception as exc:QMessageBox.warning(self,'No se pudo analizar como sistema',str(exc))
    def validate_fields(self):
        from .validation import invalid
        inverse=self.mode.currentIndex()==1
        if self.kind=='z':
            if inverse:
                if self.roc.currentIndex()<0:invalid(self.roc,'elegí una región de convergencia.','La misma expresión puede representar secuencias distintas según su ROC.')
                if self.roc.currentIndex()==2:real_field(self.radius,minimum=0,strict=True)
            elif self.direct_input.currentIndex()==0:
                lower_text=self.lower.text().strip().replace('−','-');upper_text=self.upper.text().strip()
                low=None if lower_text=='-oo' else integer_field(self.lower)
                high=None if upper_text=='oo' else integer_field(self.upper)
                if low is not None and high is not None and high<low:invalid(self.upper,'debe ser mayor o igual al primer índice.','Los límites son inclusivos; usá oo para un soporte sin final.')
        elif inverse and self.interpretation.currentIndex()==1:
            if self.laplace_roc.currentIndex()<0:invalid(self.laplace_roc,'elegí una región de convergencia.','La misma expresión puede representar señales distintas según su ROC.')
            if self.laplace_roc.currentIndex()==2:real_field(self.sigma)

    def calculate(self):
        try:
            self.validate_fields()
            index=self.mode.currentIndex();record_key=self.record_key();finite=self.kind=='z' and index==0 and self.direct_input.currentIndex()==1;request={'expression':self.expression.text()};parents=[]
            for attribute in ('_library_source','_inverse_source','_system_source'):
                source=getattr(self,attribute,None)
                if source and source[0]==request['expression'] and source[1]:parents=[source[1]];break
            if self.kind=='laplace':
                request.update(operation='inverse_laplace' if index==1 else 'laplace',interpretation='bilateral' if self.interpretation.currentIndex()==1 else 'unilateral')
                if self.interpretation.currentIndex()==1 and index==1:
                    request.update(laplace_roc=['right','left','line'][self.laplace_roc.currentIndex()],sigma=self.sigma.text())
            elif index==0 and not finite:request.update(operation='z_expression',lower=self.lower.text(),upper=self.upper.text())
            elif index==1:
                samples=self.include_samples.isChecked();request.update(operation='z_inverse_expression',complete_finite=samples and self.sample_scope.currentIndex()==1,roc=['right','left','radius'][self.roc.currentIndex()],radius=self.radius.text(),include_samples=samples,start=self.start.text() if samples else 0,count=self.count.text() if samples else 1)
            else:
                source=self.source.read();request.pop('expression',None);request.update(operation='z_finite',origin=int(source.origin),samples=[[v.real,v.imag] for v in source.values]);parents=[self.source.reference_id] if self.source.reference_id else []
            source=getattr(self,'_library_source',None)
            if source and source[0]==request.get('expression'):request['input_conditions']=list(getattr(self,'_library_conditions',()))
            snapshot=self.result_state.snapshot()
            def accept(result):
                key=self.window.publish({'request':request,'result':result},title=('Z' if self.kind=='z' else 'Laplace')+(' inversa' if index==1 else ' directa')+' · '+request.get('expression','registro finito')[:120],operation=result['operation'],parents=parents)
                signal=None;values=result.get('numeric_samples')
                previous = self.records.get(record_key)
                if previous is not None:self._sample_ids.pop(previous[2],None)
                if values:
                    signal=Signal([complex(*v) for v in values],result['origin'],1,'n','Z inversa','discrete',metadata={'operation':'z_inverse_expression','roc':result['roc'],'expression':result['result']})
                    from .temporal_formula import attach_temporal_formula
                    attach_temporal_formula(signal,result)
                    self._sample_ids[key] = self.window.publish(signal,operation='Muestras de Z inversa',parents=[key])
                record=(request,result,key,snapshot,signal);self.records[record_key]=record
                if self.record_key()==record_key:self.display_record(record)
            self.window._run_operation('Calculando transformada…',lambda:run_request(request),accept)
        except Exception as exc:show_input_error(self,'Revisá la transformada',exc)
