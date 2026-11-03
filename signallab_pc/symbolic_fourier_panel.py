from .numeric_input import real_field,integer_field
from .report_view import ReportView,report_panel
from .expression_editor import ExpressionEditor
"""Fourier algebraica angular y registro numérico derivado de su resultado."""
from PySide6.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QFormLayout,QLineEdit,QPushButton,QLabel,QPlainTextEdit,QScrollArea,QMessageBox,QTabWidget
from .symbolic_process import run_request
from .model import Signal

class SymbolicFourierPanel(QWidget):
    def __init__(self,window,inverse=False,discrete=False):
        super().__init__();self.window=window;self.inverse=inverse;self.discrete=discrete;self.input_id=None;self.last=None
        from .toolbox import ResultView
        root=QHBoxLayout(self);controls=QWidget();form=QFormLayout(controls);form.setProperty("stackFields",True);form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.expression=ExpressionEditor('1/(1-0.5*exp(-i*w))' if discrete and inverse else '(1/2)^n' if discrete else 'sqrt(pi)*exp(-w^2/4)' if inverse else 'exp(-t^2)')
        form.addRow('X(w), con w en rad/muestra' if discrete and inverse else 'x[n]' if discrete else 'X(w), con w en rad/s' if inverse else 'x(t), con t en segundos',self.expression)
        self.expression.symbolic=True
        self.lower=QLineEdit('0');self.upper=QLineEdit('oo')
        if discrete and not inverse:
            form.addRow('Índice inicial (entero o -oo)',self.lower);form.addRow('Índice final (entero u oo)',self.upper)
        note=QLabel('DTFT inversa: x[n] = ∫ de −π a π X(w) exp(iwn) dw / (2π), con n entero.' if discrete and inverse else 'DTFT: X(w) = Σ x[n] exp(−iwn). w en rad/muestra; espectro periódico cada 2π.' if discrete else 'Inversa: x(t) = ∫ X(w) exp(iwt) dw / (2π).' if inverse else 'Directa: X(w) = ∫ x(t) exp(−iwt) dt.');note.setWordWrap(True);form.addRow(note)
        choose=QPushButton('Copiar un resultado algebraico…');choose.clicked.connect(self.choose);form.addRow(choose)
        self.source_note=QLabel();self.source_note.setWordWrap(True);self.source_note.setObjectName('muted');form.addRow(self.source_note);self.source_note.hide()
        self._expression_origin=None;self._input_conditions=();self.expression.textChanged.connect(self.refresh_origin)
        self.calculate_button=QPushButton('Calcular transformada algebraica');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);form.addRow(self.calculate_button)
        from .result_state import ResultState
        self.result_state=ResultState([self.expression]+([self.lower,self.upper] if discrete and not inverse else []),self.calculate_button);form.insertRow(0,self.result_state)
        self.numeric_controls=QWidget();numeric_form=QFormLayout(self.numeric_controls);form.addRow(self.numeric_controls);self.numeric_controls.hide()
        label=QLabel('Registro numérico del último resultado');label.setObjectName('cardTitle');numeric_form.addRow(label)
        self.start=QLineEdit('-16' if discrete and inverse else '-3.141592653589793' if discrete else '-5');self.stop=QLineEdit('3.141592653589793' if discrete else '5');self.count=QLineEdit('33' if discrete and inverse else '501')
        for title,field in [('Primer índice n' if discrete and inverse else 'Inicio (rad/muestra)' if discrete else 'Inicio (s)' if inverse else 'Inicio (rad/s)',self.start),('Final (rad/muestra)' if discrete else 'Final (s)' if inverse else 'Final (rad/s)',self.stop),('Cantidad de muestras' if discrete and inverse else 'Cantidad de puntos',self.count)]:
            if not (discrete and inverse and field is self.stop):numeric_form.addRow(title,field)
        self.sample_button=QPushButton('Graficar resultado');self.sample_button.setEnabled(False);self.sample_button.clicked.connect(self.sample);numeric_form.addRow(self.sample_button)
        scope=QLabel('La expresión algebraica y sus muestras se conservan como objetos distintos, vinculados por su procedencia. Las distribuciones y las expresiones no resueltas no se convierten en muestras finitas.');scope.setWordWrap(True);numeric_form.addRow(scope)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);root.addWidget(scroll,1)
        right=QWidget();layout=QVBoxLayout(right);layout.setContentsMargins(0,0,0,0);root.addWidget(right,2)
        actions=QHBoxLayout();self.to_cas_button=QPushButton('Enviar a CAS');self.to_cas_button.setEnabled(False);self.to_cas_button.clicked.connect(self.to_cas);actions.addWidget(self.to_cas_button);actions.addStretch();layout.addLayout(actions)
        self.tabs=QTabWidget();layout.addWidget(self.tabs,1);self.report=ReportView();self.report.setReadOnly(True);self.tabs.addTab(report_panel(self.report),'Expresión y condiciones')
        self.report.setPlainText('Ingresá la expresión y calculá. Si el resultado admite valores numéricos, aparecerán los campos para graficarlo.')
        self.output=ResultView();self.tabs.addTab(self.output,'Registro numérico');self.tabs.setTabVisible(1,False)
        from .expression_grid_view import ExpressionGridView
        self.masked=ExpressionGridView();self.masked_index=self.tabs.addTab(self.masked,'Valores condicionados');self.tabs.setTabVisible(self.masked_index,False)
        self.steps=ReportView();self.steps_index=self.tabs.addTab(report_panel(self.steps),'Desarrollo');self.tabs.setTabVisible(self.steps_index,False)
    def to_cas(self):
        if self.last is not None:
            from .cas_transfer import send_to_cas
            send_to_cas(self.window,self.last[0])
    def choose(self):
        expected='w' if self.inverse else 'n' if self.discrete else 't'
        key=self.window.choose_record('expression',variables=[expected,None],units=['rad/muestra' if self.discrete else 'rad/s'] if self.inverse else None)
        if not key:return
        self.load_expression(self.window.project.expression(key),key)
    def refresh_origin(self,*_):
        current=self._expression_origin and self._expression_origin[0]==self.expression.text()
        self.source_note.setVisible(bool(current));self.source_note.setText(('Expresión cargada desde Resultados. Sus condiciones acompañan al cálculo.' if self._expression_origin[1] else 'Definición copiada de otra variante. Su soporte y condiciones acompañan al cálculo.') if current else '')
    def load_expression(self,result,key=None):
        expected='w' if self.inverse else 'n' if self.discrete else 't'
        if result is None or result.variable not in (expected,None):
            QMessageBox.information(self,'Variable incompatible','Esta herramienta espera una expresión en '+expected+'.');return
        if self.inverse and result.units and result.units!=('rad/muestra' if self.discrete else 'rad/s'):
            QMessageBox.information(self,'Unidad incompatible','No se convierte automáticamente entre rad/s y rad/muestra.');return
        text=result.numerical_source or result.source
        self.expression.setText(text);self.input_id=key;self._expression_origin=(self.expression.text(),key);self._input_conditions=result.conditions
        if self.discrete and not self.inverse:self.lower.setText('-oo');self.upper.setText('oo')
        self.refresh_origin()
    def calculate(self):
        request=dict(operation='inverse_dtft_expression' if self.discrete and self.inverse else 'dtft_expression' if self.discrete else 'inverse_fourier_angular' if self.inverse else 'fourier_angular',expression=self.expression.text())
        intact=self._expression_origin and self._expression_origin[0]==request['expression'];parent=self._expression_origin[1] if intact else None
        request['input_conditions']=list(self._input_conditions) if intact else []
        if self.discrete and not self.inverse:request.update(lower=self.lower.text(),upper=self.upper.text())
        snapshot=self.result_state.snapshot()
        def accept(result):
            key=self.window.publish({'request':request,'result':result},title='DTFT inversa algebraica' if self.discrete and self.inverse else 'DTFT algebraica' if self.discrete else 'Fourier inversa algebraica' if self.inverse else 'Fourier algebraica',operation=request['operation'],parents=[parent] if parent else [])
            self.tabs.setTabVisible(1,False);self.tabs.setTabVisible(self.masked_index,False)
            self.last=(key,result);self.to_cas_button.setEnabled(result['evaluated']);self.sample_button.setEnabled(result['evaluated']);self.numeric_controls.setVisible(self.sample_button.isEnabled());self.tabs.setCurrentIndex(0);self.result_state.accept(snapshot)
            if self.discrete and self.inverse:
                from .inverse_dtft_summary import inverse_dtft_summary
                summary=inverse_dtft_summary(request,result)
            else:
                from .result_summary import Summary,Section,Formula
                title='DTFT algebraica' if self.discrete else 'Fourier inversa algebraica' if self.inverse else 'Fourier continua algebraica'
                formula=('x(t) = ' if self.inverse else 'X(w) = ')+result['result']
                sections=[Section('Definición de entrada',formulas=[Formula(request['expression'],request['expression'])])]
                if not result['evaluated']:sections.append(Section('Cálculo pendiente',paragraphs=['El motor conserva términos sin evaluar; no se presenta una solución cerrada.']))
                sections.append(Section('Expresión obtenida' if result['evaluated'] else 'Expresión sin resolver',formulas=[Formula(formula,formula)]))
                sections.append(Section('Condiciones y alcance',rows=([('Estado del cálculo',result['calculation_status']['label'])] if result.get('calculation_status') else [])+([('Condición',result['condition'])] if result['condition']!='True' else []),paragraphs=[result['scope']]))
                summary=Summary(title,sections)
            if request['input_conditions']:
                from .result_summary import Section
                summary.sections.append(Section('Condiciones de la expresión de entrada',paragraphs=request['input_conditions']))
            self.report.set_readable(summary)
            from .transform_steps import summary as steps_summary
            self.steps.set_readable(steps_summary(result.get('derivation',[])));self.tabs.setTabVisible(self.steps_index,bool(result.get('derivation')))
        self.window._run_operation('Calculando Fourier algebraica…',lambda:run_request(request),accept)
    def open_output_plot(self):
        from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
        from .plot_view import install_enlarge,enlarge_plot
        canvas=self.output.canvas
        if getattr(canvas,'_signallab_window',None) is None:
            for toolbar in self.output.findChildren(NavigationToolbar2QT):
                if toolbar.canvas is canvas:install_enlarge(toolbar);break
        self.output.views.setCurrentIndex(0)
        canvas.draw()
        enlarge_plot(canvas,self)
    def sample(self):
        if self.last is None:return
        key,result=self.last
        if not result['evaluated']:return
        if self.discrete and self.inverse:
            try:request=dict(operation='inverse_dtft_samples',expression=result['input_expression'],start=integer_field(self.start),count=integer_field(self.count))
            except ValueError as exc:QMessageBox.warning(self,'Revisá los índices',str(exc));return
            def accept(data):
                signal=Signal([complex(*v) for v in data['samples']],data['origin'],1,'n','DTFT inversa','discrete','',{'operation':'inverse_dtft_expression_samples','scope':result['scope'],'source_expression':result['input_expression']})
                output_id=self.window.publish(signal,operation='Muestras de DTFT inversa',parents=[key]);self.output.show_result(signal);self.output.result_ids=[output_id];self.tabs.setTabVisible(1,True);self.tabs.setCurrentIndex(1);self.open_output_plot()
            self.window._run_operation('Evaluando DTFT inversa…',lambda:run_request(request),accept);return
        try:request=dict(operation='expression_grid',expression=result['result'],variable=result['output_variable'],condition=result['condition'],allow_undefined=True,start=real_field(self.start),stop=real_field(self.stop),count=integer_field(self.count))
        except ValueError as exc:QMessageBox.warning(self,'Revisá la rejilla',str(exc));return
        def accept(data):
            if data.get('undefined_count'):
                units='s' if data['variable']=='t' else result['frequency_units']
                self.window.publish({'request':request,'result':{**data,'units':units}},operation='Valores condicionados del resultado algebraico',parents=[key])
                self.tabs.setTabVisible(1,False);self.tabs.setTabVisible(self.masked_index,True);self.tabs.setCurrentIndex(self.masked_index);self.masked.set_grid(data,units);return
            temporal=data['variable']=='t'
            signal=Signal([complex(*v) for v in data['samples']],data['origin'],data['step'],'s' if temporal else result['frequency_units'],'x(t)' if temporal else 'X(w)','continuous' if temporal else 'frequency',data['expression'],
                {'operation':'fourier_expression_samples','scope':data['scope'],'source_condition':result['condition'],'convention':result['convention']})
            self.tabs.setTabVisible(self.masked_index,False)
            self.window.publish(signal,operation='Muestreo de resultado Fourier algebraico',parents=[key]);self.output.show_result(signal);self.tabs.setTabVisible(1,True);self.tabs.setCurrentIndex(1);self.open_output_plot()
        self.window._run_operation('Evaluando expresión resuelta…',lambda:run_request(request),accept)
