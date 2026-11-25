from .validation import show_input_error
from .numeric_input import real_field,integer_field
"""Entrada visual de H por tramos, respuesta al impulso y filtrado espectral."""
from PySide6.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QFormLayout,QComboBox,QLineEdit,QCheckBox,QPushButton,QLabel,QScrollArea,QTabWidget
from .report_view import ReportView,report_panel
from .frequency_filter import analyze
from .choice_buttons import ChoiceButtons
from .field_section import FieldSection

class FrequencyFilterPanel(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window;self.results=[];self.result_keys=[];self.impulse_key=None
        from .toolbox import LocalInput,ResultView
        root=QHBoxLayout(self);controls=QWidget();form=QFormLayout(controls)
        self.domain=QComboBox();self.domain.addItems(['Discreto','Continuo']);form.addRow('Dominio',ChoiceButtons(self.domain))
        self.operation=QComboBox();self.operation.addItems(['Analizar','Aplicar a una señal']);form.addRow('Operación',ChoiceButtons(self.operation))
        self.h=LocalInput('Respuesta en frecuencia','frequency');self.h.set_role('frequency_response');self.h.bind_project(window)
        self.h.frequency_units.setProperty('fromDomain', True)
        self.h.layout().setRowVisible(self.h.frequency_units,False)
        self.h.expression.setProperty('variableHint','w');self.h.expression.setText('')
        self.h.expression.field.setPlaceholderText('Ingresá H en función de w')
        self.h.samples.clear();form.addRow(self.h)
        self.xd=LocalInput('Entrada x[n]','discrete');self.xc=LocalInput('Entrada x(t)','continuous')
        for source in (self.xd,self.xc):source.bind_project(window);form.addRow(source)
        self.impulse_settings=FieldSection('Ventana de la respuesta al impulso')
        impulse_form=self.impulse_settings.form
        self.start=QLineEdit();self.count=QLineEdit();self.step=QLineEdit()
        impulse_form.addRow('Primer punto',self.start);impulse_form.addRow('Cantidad de puntos',self.count);impulse_form.addRow('Paso temporal (s)',self.step)
        form.addRow(self.impulse_settings)
        self.periodic=QCheckBox('Permitir plegado periódico si la rejilla es corta')
        self.periodic.setToolTip('Las muestras separadas por el período de la rejilla se suman en el mismo índice de la salida.')
        form.addRow(self.periodic)
        self._ranges = {0:('-32','65','1','-pi','2049','pi/1024'),1:('-2','401','0.01','-10','2049','20/2048')}
        self._active_domain = None
        self.form=form;self.operation.currentIndexChanged.connect(self.update_inputs);self.domain.currentIndexChanged.connect(self.update_domain)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);left=QVBoxLayout();left.addWidget(scroll);self.calculate_button=QPushButton('Calcular');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);left.addWidget(self.calculate_button);root.addLayout(left,1)
        right=QVBoxLayout();self.selector=QComboBox();self.selector.setProperty('sessionTransient',True);self.selector.currentIndexChanged.connect(self.display)
        self.selector.setAccessibleName('Datos para el gráfico, la tabla y la reutilización')
        self.selector.setToolTip('Elegí la respuesta que querés ver en el gráfico y la tabla, o reutilizar como muestras.')
        self.tabs=QTabWidget();self.view=ResultView();self.report=ReportView()
        right.addWidget(self.view.actions)
        right.addWidget(self.selector)
        self.tabs.addTab(self.view,'Valores');self.tabs.addTab(report_panel(self.report),'Informe')
        right.addWidget(self.tabs);root.addLayout(right,2)
        self.algebraic_key=None
        self.reuse_button=self.view.send
        self.reuse_button.menu().aboutToShow.connect(self.add_filter_destinations)
        self.cas_button=self.view.cas_button
        menu=self.view.cas_menu;menu.aboutToShow.disconnect(self.view.prepare_cas)
        self.cas_definition=menu.addAction('Fórmula de H(w)',lambda: self.send_to_cas(self.algebraic_key))
        self.cas_impulse=menu.addAction('Fórmula de la respuesta al impulso',lambda: self.send_to_cas(self.impulse_key))
        self.cas_samples=menu.addAction('Muestras del resultado seleccionado',self.send_samples_to_cas)
        from .result_state import ResultState
        self.state=ResultState([self.domain,self.operation,self.start,self.count,self.step,self.periodic],self.calculate_button,[self.h,self.xd,self.xc]);right.insertWidget(0,self.state)
        self.update_domain()
    def scalar(self,field):
        return real_field(field)
    def update_inputs(self,*_):
        apply=self.operation.currentIndex()==1;digital=self.domain.currentIndex()==0
        self.form.setRowVisible(self.xd,apply and digital);self.form.setRowVisible(self.xc,apply and not digital)
        self.form.setRowVisible(self.periodic,apply and digital)
        self.periodic.setProperty('calculationInput',apply and digital)
    def update_domain(self,*_):
        domain = self.domain.currentIndex()
        digital = domain == 0
        units = 'rad/muestra' if digital else 'rad/s'
        self.h.frequency_units.setCurrentText(units)
        self.h.layout().labelForField(self.h.expression).setText(f'H(ω) en función de w ({units})' if digital else f'H(Ω) en función de w ({units})')
        interval = (self.start,self.count,self.step,self.h.origin,self.h.count,self.h.step)
        if self._active_domain != domain:
            if self._active_domain is not None:
                self._ranges[self._active_domain] = tuple(field.text() for field in interval)
            for field, value in zip(interval,self._ranges[domain]):
                field.setText(value)
            self._active_domain = domain
        form = self.impulse_settings.form
        form.labelForField(self.start).setText('Primer índice n' if digital else 'Tiempo inicial (s)')
        form.labelForField(self.count).setText('Cantidad de muestras' if digital else 'Cantidad de puntos')
        form.setRowVisible(self.step,not digital)
        self.update_inputs()
    def calculate(self):
        try:
            digital=self.domain.currentIndex()==0;domain='discrete' if digital else 'continuous';unit='rad/muestra' if digital else 'rad/s'
            response=self.h.read().copy_with(name='Respuesta H(ω)')
            parents=[self.h.reference_id] if self.h.reference_id else []
            if self.h.mode.currentIndex()==2 and response.units!=unit:raise ValueError('La respuesta importada debe usar '+unit+'.')
            from .signal_semantics import require_frequency_response
            require_frequency_response(response)
            response.units=unit;response.metadata={**response.metadata,'operation':'frequency_filter','time_domain':domain}
            from .auxiliary import optional
            interval,interval_notice=optional('Intervalo de la respuesta temporal',lambda:(integer_field(self.start) if digital else self.scalar(self.start),integer_field(self.count),self.scalar(self.step)))
            source=(self.xd if digital else self.xc).read() if self.operation.currentIndex()==1 else None
            allow_periodic=digital and self.periodic.isChecked()
            snapshot=self.state.snapshot()
            from .inverse_fourier_report import from_signal,exact_section,numeric_section
            from .result_summary import Formula,Summary,Section
            def compute():
                algebra=from_signal(response)
                def numerical():
                    if interval is None:raise ValueError(interval_notice)
                    start,count,step=interval
                    return analyze(response,domain,start,count,step,source,allow_periodic=allow_periodic)
                numerical_result,notice=optional('Muestras de la respuesta temporal',numerical)
                if numerical_result is None:
                    if algebra is None:raise ValueError(notice)
                    return [response],notice,algebra
                values,report=numerical_result
                return values,report,algebra
            def accept(result):
                values,report,algebra=result
                if len(values)>1 and algebra and algebra['inverse']:
                    from .temporal_formula import attach_temporal_formula
                    attach_temporal_formula(values[1],algebra['inverse'])
                self.results=values;self.selector.blockSignals(True);self.selector.clear()
                keys=[]
                for value in values:
                    keys.append(self.window.publish(value,operation='Filtro por respuesta en frecuencia',parents=parents))
                    self.selector.addItem(value.name)
                self.result_keys=keys;self.algebraic_key=None;self.impulse_key=None;sections=[]
                if algebra:
                    definition = algebra['definition']
                    self.algebraic_key=self.window.publish({'result':definition},title='Definición algebraica H(w)',
                        operation='Filtro por respuesta en frecuencia',parents=[keys[0]])
                    frequency = 'H(ω)' if digital else 'H(Ω)'
                    source=definition.get('display_result',definition['result'])
                    sections.append(Section('Respuesta en frecuencia '+frequency,paragraphs=[f'Frecuencia angular en {unit}.'],
                                            formulas=[Formula(source,frequency+' = '+source)]))
                    if algebra['inverse']:
                        inverse=algebra['inverse']
                        self.impulse_key=self.window.publish({'result':inverse},title='Expresión algebraica de la respuesta al impulso',
                            operation='Filtro por respuesta en frecuencia',parents=[self.algebraic_key]+keys[1:2])
                        sections.append(exact_section(inverse,'h'))
                if len(values)>1:sections.append(numeric_section(values[1].metadata['inverse_model'],'h'))
                else:sections.append(Section('Vista temporal no generada',paragraphs=[report]))
                if len(values)>2:
                    from .temporal_formula import sections as temporal_sections
                    sections.extend(temporal_sections(values[2]))
                sections.append(Section('Cómo interpretarlo',paragraphs=report.split('\n\n')[1:]))
                summary=Summary('Filtro definido en frecuencia',sections)
                self.selector.blockSignals(False);self.report.set_readable(summary)
                self.window.publish({'report':summary.plain_text()},title='Filtro por tramos',operation='Informe de filtro por tramos',parents=keys[:2])
                self.display();self.tabs.setCurrentIndex(1);self.state.accept(snapshot)
            self.window._run_operation('Calculando filtro por tramos…',compute,accept)
        except Exception as exc:show_input_error(self,'Revisá la definición',exc)
    def add_filter_destinations(self):
        from .result_expressions import populate_reuse_menu
        index=self.selector.currentIndex()
        key=self.algebraic_key if index==0 else self.impulse_key if index==1 else None
        menu=self.reuse_button.menu()
        if key is not None:
            before=menu.actions()[0] if menu.actions() else None
            populate_reuse_menu(menu,self.window,key,before=before)
        if self.impulse_key is not None and len(self.results)==1:
            impulse=menu.addMenu('Respuesta al impulso h')
            populate_reuse_menu(impulse,self.window,self.impulse_key)
            self.view.send_menu_refs.append(impulse)
        if index!=0 and self.algebraic_key is not None:
            definition=menu.addMenu('Filtro H(w)')
            populate_reuse_menu(definition,self.window,self.algebraic_key)
            self.view.send_menu_refs.append(definition)

    def display(self,*_):
        index=self.selector.currentIndex()
        if 0<=index<len(self.results):
            self.view.show_result(self.results[index])
            self.view.result_ids=[self.result_keys[index]]
        self.cas_definition.setEnabled(self.algebraic_key is not None)
        self.cas_impulse.setEnabled(self.impulse_key is not None)
        self.cas_samples.setEnabled(0<=index<len(self.result_keys))
        self.cas_button.setEnabled(bool(self.result_keys));self.cas_button.setVisible(bool(self.result_keys))
        if index==0:
            self.reuse_button.setText('Usar filtro en…')

    def send_to_cas(self,key):
        if key is not None:
            from .cas_transfer import send_to_cas
            send_to_cas(self.window,key)

    def send_samples_to_cas(self):
        index=self.selector.currentIndex()
        if 0<=index<len(self.result_keys):
            self.send_to_cas(self.result_keys[index])

    def receive_response(self,value,key=None):
        self.domain.setCurrentIndex(0 if value.units=='rad/muestra' else 1);self.h.set_source(value,key)
