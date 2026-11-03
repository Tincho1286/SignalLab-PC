"""One transform document: explicit inputs, conditions and optional output samples."""
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QComboBox,QLineEdit,QLabel,QPushButton,QScrollArea,QMessageBox,QCheckBox,QTabWidget
from .expression_editor import ExpressionEditor
from .report_view import ReportView,report_panel
from .symbolic_process import run_request
from .numeric_input import integer_field,real_field
from .model import Signal
from .choice_buttons import ChoiceButtons
from .result_state import ResultState
from .result_summary import transform_summary

class TransformLab(QWidget):
    def __init__(self,window,kind):
        super().__init__();self.window=window;self.kind=kind;self.last=None;self.records={};self._mode_index=0
        from .toolbox import ResultView,LocalInput
        root=QHBoxLayout(self);left=QWidget();form=QFormLayout(left);self.form=form;form.setProperty("stackFields",True)
        self.mode=QComboBox();self.mode.addItems(['Directa','Inversa']);form.addRow('Operación',ChoiceButtons(self.mode))
        self.direct_input=QComboBox();self.direct_input.addItems(['Expresión x[n]','Secuencia finita']);self.direct_buttons=ChoiceButtons(self.direct_input);form.addRow('Definición de la secuencia',self.direct_buttons)
        self.sample_scope=QComboBox();self.sample_scope.addItems(['Intervalo elegido','Soporte finito completo']);form.addRow('Muestras de la inversa',self.sample_scope)
        self.load_expression_button=QPushButton('Cargar expresión…');self.load_expression_button.clicked.connect(self.choose_expression);form.addRow(self.load_expression_button)
        self.interpretation=QComboBox();self.interpretation.addItems(['Unilateral / causal','Bilateral · con ROC']);form.addRow('Interpretación',self.interpretation)
        self.laplace_roc=QComboBox();self.laplace_roc.addItems(['A la derecha de todos los polos','A la izquierda de todos los polos','Franja que contiene una línea elegida']);form.addRow('Región de convergencia (ROC)',self.laplace_roc)
        self.sigma=QLineEdit('0');form.addRow('Parte real σ dentro de la ROC',self.sigma)
        self.definitions={0:'(1/2)^n' if kind=='z' else 'exp(-t)',1:'z/(z-1/2)' if kind=='z' else '1/(s+1)'}
        self.expression=ExpressionEditor(self.definitions[0],symbolic=True);form.addRow('Expresión',self.expression)
        self.lower=QLineEdit('0');self.upper=QLineEdit('oo');form.addRow('Primer índice del soporte',self.lower);form.addRow('Último índice del soporte',self.upper)
        self.roc=QComboBox();self.roc.addItems(['Exterior a los polos · secuencia derecha','Interior a los polos · secuencia izquierda','Anillo que contiene un radio elegido']);form.addRow('Región de convergencia (ROC)',self.roc)
        self.radius=QLineEdit('1');form.addRow('Radio dentro de la ROC',self.radius)
        self.include_samples=QCheckBox('Graficar un intervalo de la secuencia');self.include_samples.setChecked(True);form.addRow(self.include_samples)
        self.start=QLineEdit('-16');self.count=QLineEdit('65');form.addRow('Primer índice a visualizar',self.start);form.addRow('Cantidad de muestras',self.count)
        self.source=LocalInput('Secuencia finita','discrete');self.source.bind_project(window);form.addRow(self.source)
        self.note=QLabel();self.note.setObjectName('muted');self.note.setWordWrap(True);form.addRow(self.note)
        self.copy_note=QLabel();self.copy_note.setObjectName('muted');self.copy_note.setWordWrap(True);form.addRow(self.copy_note);self.copy_note.hide()
        self.expression.textChanged.connect(lambda *_:self.set_copy_note(''))
        self.calculate_button=QPushButton('Calcular transformada');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);form.addRow(self.calculate_button)
        fields=[self.mode,self.direct_input,self.sample_scope,self.interpretation,self.laplace_roc,self.sigma,self.expression,self.lower,self.upper,self.roc,self.radius,self.include_samples,self.start,self.count]
        self.result_state=ResultState(fields,self.calculate_button,[self.source]);form.insertRow(0,self.result_state)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(left);root.addWidget(scroll,1)
        right=QWidget();layout=QVBoxLayout(right);layout.setContentsMargins(0,0,0,0);root.addWidget(right,2)
        result_actions=QHBoxLayout();layout.addLayout(result_actions)
        self.copy_inverse=QPushButton('Copiar resultado a la inversa');self.copy_inverse.clicked.connect(self.to_inverse);self.copy_inverse.hide();result_actions.addWidget(self.copy_inverse)
        self.to_cas_button=QPushButton('Enviar a CAS');self.to_cas_button.setToolTip('Abrir la expresión del último resultado calculado como una celda de la hoja CAS.');self.to_cas_button.clicked.connect(self.to_cas);self.to_cas_button.hide();result_actions.addWidget(self.to_cas_button)
        self.analyze_system=QPushButton();self.analyze_system.clicked.connect(self.to_system);result_actions.addWidget(self.analyze_system);result_actions.addStretch()
        self.tabs=QTabWidget();layout.addWidget(self.tabs,1);self.report=ReportView();self.tabs.addTab(report_panel(self.report),'Expresión y condiciones')
        self.output=ResultView();self.tabs.addTab(self.output,'Muestras de la inversa');self.tabs.setTabVisible(1,False)
        self.steps=ReportView();self.steps_index=self.tabs.addTab(report_panel(self.steps),'Desarrollo');self.tabs.setTabVisible(self.steps_index,False)
        def update(*_):
            index=self.mode.currentIndex();changed=index!=self._mode_index
            if changed:
                self.definitions[self._mode_index]=self.expression.text();self._mode_index=index;self.expression.setText(self.definitions[index])
            inverse=index==1;z=kind=='z';finite=z and not inverse and self.direct_input.currentIndex()==1;samples=z and inverse and self.include_samples.isChecked();bilateral=not z and self.interpretation.currentIndex()==1
            form.setRowVisible(self.direct_buttons,z and not inverse);form.setRowVisible(self.sample_scope,samples);form.setRowVisible(self.load_expression_button,not finite)
            form.setRowVisible(self.interpretation,not z);form.setRowVisible(self.laplace_roc,bilateral and inverse);form.setRowVisible(self.sigma,bilateral and inverse and self.laplace_roc.currentIndex()==2)
            form.labelForField(self.expression).setText(('X(z)' if z else 'X(s)') if inverse else ('x[n]' if z else 'x(t)'))
            form.setRowVisible(self.expression,not finite);form.setRowVisible(self.source,finite)
            for field in (self.lower,self.upper):form.setRowVisible(field,z and not inverse and not finite)
            form.setRowVisible(self.roc,z and inverse);form.setRowVisible(self.radius,z and inverse and self.roc.currentIndex()==2)
            form.setRowVisible(self.include_samples,z and inverse)
            for field in (self.start,self.count):form.setRowVisible(field,samples and self.sample_scope.currentIndex()==0)
            form.setRowVisible(self.copy_note,inverse and bool(self.copy_note.text()))
            self.note.setText(('Los valores y el primer índice definen la secuencia finita; cero fuera de ella.' if finite else 'Índices inclusivos. Se admiten enteros, -oo y oo; cero fuera del soporte indicado.') if z and index==0 else (('Exterior: términos derechos.' if self.roc.currentIndex()==0 else 'Interior: términos izquierdos para los polos no nulos.' if self.roc.currentIndex()==1 else 'El radio elige un anillo sin polos; no fija sus bordes.')+' El intervalo numérico no limita la fórmula.') if z and inverse else 'Los valores y el primer índice definen el registro; cero fuera de él.' if finite else 'Ingresá X(s). La inversa se interpreta como causal: cero para t<0.' if inverse else 'Ingresá x(t). Laplace unilateral integra desde 0−; los valores para t<0 no intervienen.')
            if not z and bilateral:self.note.setText('Ingresá X(s) racional; admite un factor global exp(-d*s). La ROC decide el soporte de cada término. σ elige una franja, no sus bordes.' if inverse else 'Ingresá la señal completa, incluyendo t<0. Usá escalones o tramos para indicar su soporte. Se calcula la zona común de convergencia de ambas mitades.')
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
                if samples and self.sample_scope.currentIndex()==0:tracked += [self.start,self.count]
            self.result_state.widgets=tracked;self.result_state.sources=[self.source] if finite else []
            if changed:self.display_record(self.records.get(self.record_key()))
            self.update_system_action()
            self.result_state.refresh()
        self._update_form=update
        self.interpretation.currentIndexChanged.connect(update);self.laplace_roc.currentIndexChanged.connect(update)
        self.direct_input.currentIndexChanged.connect(lambda *_:(self.display_record(self.records.get(self.record_key())),update()));self.sample_scope.currentIndexChanged.connect(update)
        self.mode.currentIndexChanged.connect(update);self.roc.currentIndexChanged.connect(update);self.include_samples.toggled.connect(update);update();self.display_record(None)
    def record_key(self):
        return (self.mode.currentIndex(),self.direct_input.currentIndex() if self.kind=='z' and self.mode.currentIndex()==0 else 0)
    def choose_expression(self):
        variable=('z' if self.kind=='z' else 's') if self.mode.currentIndex()==1 else ('n' if self.kind=='z' else 't')
        key=self.window.choose_record('expression',variables=[variable,None])
        if not key:return
        value=self.window.project.expression(key)
        self.expression.setText(value.source);self._library_source=(self.expression.text(),key)
        self._library_conditions=tuple(value.conditions)
    def use_finite_input(self):
        self.mode.setCurrentIndex(0);self.direct_input.setCurrentIndex(1)
    def load_laplace_context(self,request,result=None,inverse=False):
        if self.kind!='laplace':return
        self.interpretation.setCurrentIndex(1 if request.get('interpretation')=='bilateral' else 0)
        hint=(result or {}).get('inverse_laplace_hint') if inverse else request
        if hint and self.interpretation.currentIndex()==1:
            self.laplace_roc.setCurrentIndex({'right':0,'left':1,'line':2}.get(hint.get('laplace_roc'),0))
            if hint.get('sigma') is not None:self.sigma.setText(str(hint['sigma']))
    def select_legacy(self,key):
        self.mode.setCurrentIndex(1 if key in (('symbolic',1),('symbolic',3),('course_tools','inverse_z')) else 0)
        if key==('symbolic',2):self.use_finite_input()
    def set_system(self,system,key=None):
        from .phase_summary import transfer_formula
        expression=transfer_formula(system,digits=17)[0].text.split('=',1)[1].strip()
        self.mode.setCurrentIndex(1);self.expression.setText(expression);self._system_source=(expression,key)
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
        self.form.setRowVisible(self.copy_note,self.mode.currentIndex()==1 and bool(text))
    def update_system_action(self):
        inverse=self.mode.currentIndex()==1;variable='z' if self.kind=='z' else 's'
        self.analyze_system.setText('Analizar X('+variable+') '+('ingresada' if inverse else 'calculada')+' como H('+variable+')…')
        self.analyze_system.setVisible(True);self.analyze_system.setEnabled(inverse or (self.last is not None and self.last.get('evaluated',True) and len(self.last.get('branches',[]))<=1))
        self.analyze_system.setToolTip('Copia la expresión racional al análisis de sistemas. Allí podés calcular frecuencia, retardo y polos/ceros. Se necesitan coeficientes numéricos; los parámetros libres requieren valores.')
    def display_record(self,record):
        self.to_cas_button.show();self.to_cas_button.setEnabled(False);self.copy_inverse.hide();self.tabs.setTabVisible(1,False);self.tabs.setTabVisible(self.steps_index,False);self.tabs.setCurrentIndex(0)
        if record is None:
            self.last=None;self.result_state.completed=None;self.report.setPlainText('Completá la entrada y calculá. Aquí aparecerán la expresión y sus condiciones.');self.update_system_action();return
        request,result,key,snapshot,signal=record;self.last=result;self.report.set_readable(transform_summary(request,result));self.result_state.accept(snapshot)
        from .transform_steps import summary as steps_summary
        self.steps.set_readable(steps_summary(result.get('derivation',[])));self.tabs.setTabVisible(self.steps_index,bool(result.get('derivation')))
        self.to_cas_button.setEnabled(result.get('evaluated',True) and len(result.get('branches',[]))<=1)
        direct=request['operation'] not in ('inverse_laplace','z_inverse_expression')
        self.copy_inverse.setVisible(direct and result.get('evaluated',True) and len(result.get('branches',[]))<=1)
        if signal is not None:self.output.show_result(signal);self.tabs.setTabVisible(1,True)
        self.update_system_action()
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
        condition=branches[0]['condition'] if branches else result.get('convergence',result.get('roc_finite_plane',''))
        self.set_copy_note('Se copió la expresión del último resultado.'+(' Condición original: '+condition+'. Elegí una ROC compatible para recuperar la misma señal.' if self.kind=='z' else (' La ROC se trasladó a la inversa; comprobá sus condiciones.' if result.get('inverse_laplace_hint') else ' Elegí una ROC compatible con las condiciones de la directa.' if request.get('interpretation')=='bilateral' else ' La inversa usa interpretación causal.')))
        self._inverse_source=(expression,record[2])
    def to_system(self):
        try:
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
                if result.get('evaluated') is False or len(branches)>1:raise ValueError('Elegí una expresión evaluada única antes de analizarla como sistema.')
                expression=branches[0]['expression'] if branches else result['result'];parents=[record[2]]
            from .transfer_input import formula_system
            from .workspaces import ROUTES
            domain='digital' if self.kind=='z' else 'analog'
            from .transform_context import result_roc
            roc_spec=({'mode':['right','left','radius'][self.roc.currentIndex()],**({'radius':real_field(self.radius)} if self.roc.currentIndex()==2 else {})} if self.kind=='z' and inverse else ({'mode':['right','left','line'][self.laplace_roc.currentIndex()],**({'sigma':real_field(self.sigma)} if self.laplace_roc.currentIndex()==2 else {})} if self.interpretation.currentIndex()==1 else {'mode':'right'}) if self.kind=='laplace' and inverse else result_roc({'request':record[0],'result':record[1]}) if record else None)
            from .filters import validate_roc
            roc_spec=validate_roc(roc_spec,domain)
            def accept(system):
                system.roc=roc_spec
                if self.kind=='z' and parents:system.sample_period_s=self.window.project.sample_period(parents[0])
                key=self.window.publish(system,operation='Transformada interpretada como transferencia',parents=parents)
                self.window.send_system(system,key,ROUTES['system_analysis',0])
                self.window.statusBar().showMessage('Expresión copiada como H('+('z' if domain=='digital' else 's')+'). Calculá el análisis con sus datos.')
            self.window._run_operation('Preparando sistema para analizar…',lambda:formula_system(expression,domain,'Sistema desde transformada '+self.kind.upper(),allow_advance=True),accept)
        except Exception as exc:QMessageBox.warning(self,'No se pudo analizar como sistema',str(exc))
    def validate_fields(self):
        from .validation import invalid
        inverse=self.mode.currentIndex()==1
        if self.kind=='z':
            if inverse:
                if self.roc.currentIndex()==2:real_field(self.radius,minimum=0,strict=True)
                if self.include_samples.isChecked() and self.sample_scope.currentIndex()==0:
                    integer_field(self.start);integer_field(self.count,minimum=1)
            elif self.direct_input.currentIndex()==0:
                lower_text=self.lower.text().strip().replace('−','-');upper_text=self.upper.text().strip()
                low=None if lower_text=='-oo' else integer_field(self.lower)
                high=None if upper_text=='oo' else integer_field(self.upper)
                if low is not None and high is not None and high<low:invalid(self.upper,'debe ser mayor o igual al primer índice.','Los límites son inclusivos; usá oo para un soporte sin final.')
        elif inverse and self.interpretation.currentIndex()==1 and self.laplace_roc.currentIndex()==2:real_field(self.sigma)

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
                samples=self.include_samples.isChecked();request.update(operation='z_inverse_expression',complete_finite=samples and self.sample_scope.currentIndex()==1,roc=['right','left','radius'][self.roc.currentIndex()],radius=self.radius.text(),include_samples=samples,start=integer_field(self.start) if samples and self.sample_scope.currentIndex()==0 else 0,count=integer_field(self.count) if samples and self.sample_scope.currentIndex()==0 else 1)
            else:
                source=self.source.read();request.pop('expression',None);request.update(operation='z_finite',origin=int(source.origin),samples=[[v.real,v.imag] for v in source.values]);parents=[self.source.reference_id] if self.source.reference_id else []
            source=getattr(self,'_library_source',None)
            if source and source[0]==request.get('expression'):request['input_conditions']=list(getattr(self,'_library_conditions',()))
            snapshot=self.result_state.snapshot()
            def accept(result):
                key=self.window.publish({'request':request,'result':result},title=('Z' if self.kind=='z' else 'Laplace')+(' inversa' if index==1 else ' directa')+' · '+request.get('expression','registro finito')[:120],operation=result['operation'],parents=parents)
                signal=None;values=result.get('numeric_samples')
                if values:
                    signal=Signal([complex(*v) for v in values],result['origin'],1,'n','Z inversa','discrete',metadata={'operation':'z_inverse_expression','roc':result['roc'],'expression':result['result']})
                    self.window.publish(signal,operation='Muestras de Z inversa',parents=[key])
                record=(request,result,key,snapshot,signal);self.records[record_key]=record
                if self.record_key()==record_key:self.display_record(record)
            self.window._run_operation('Calculando transformada…',lambda:run_request(request),accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá la transformada',str(exc))
