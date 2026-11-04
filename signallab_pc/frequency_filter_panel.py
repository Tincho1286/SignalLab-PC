from .numeric_input import real_field,integer_field
"""Entrada visual de H por tramos, respuesta al impulso y filtrado espectral."""
from PySide6.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QFormLayout,QComboBox,QLineEdit,QCheckBox,QPushButton,QLabel,QScrollArea,QTabWidget,QMessageBox
from .report_view import ReportView,report_panel
from .frequency_filter import analyze

class FrequencyFilterPanel(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window;self.results=[]
        from .toolbox import LocalInput,ResultView
        root=QHBoxLayout(self);controls=QWidget();form=QFormLayout(controls)
        self.domain=QComboBox();self.domain.addItems(['Discreto · ω en rad/muestra','Continuo · Ω en rad/s']);form.addRow('Dominio',self.domain)
        note=QLabel('Definí H por tramos. El valor es la ganancia (puede ser compleja); la condición indica en qué frecuencias se aplica. Usá w para la frecuencia.');note.setWordWrap(True);form.addRow(note)
        self.h=LocalInput('Respuesta del filtro H(ω)','frequency');self.h.set_role('frequency_response');self.h.bind_project(window)
        for label in self.h.findChildren(QLabel):
            if label.text()=='Paso (rad/s)':label.setText('Paso angular')
            if label.text().startswith('X(ω)'):label.setText('H(ω), usar w como frecuencia')
        self.h.expression.setProperty('variableHint','w');self.h.expression.setText('')
        self.h.expression.field.setPlaceholderText('Ingresá H en función de w')
        self.h.samples.clear();form.addRow(self.h)
        self.operation=QComboBox();self.operation.addItems(['Ver H y respuesta al impulso','Aplicar a una señal']);form.addRow('Operación',self.operation)
        self.start=QLineEdit('-32');self.count=QLineEdit('65');self.step=QLineEdit('1');form.addRow('Inicio de h',self.start);form.addRow('Puntos de h',self.count);form.addRow('Paso temporal de h',self.step)
        self.xd=LocalInput('Entrada x[n]','discrete');self.xc=LocalInput('Entrada x(t)','continuous')
        for source in (self.xd,self.xc):source.bind_project(window);form.addRow(source)
        self.periodic=QCheckBox('Permitir plegado periódico si la rejilla es corta')
        self.periodic.setToolTip('Las muestras separadas por el período de la rejilla se suman en el mismo índice de la salida.')
        form.addRow(self.periodic)
        self.form=form;self.operation.currentIndexChanged.connect(self.update_inputs);self.domain.currentIndexChanged.connect(self.update_domain)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);left=QVBoxLayout();left.addWidget(scroll);self.calculate_button=QPushButton('Calcular');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);left.addWidget(self.calculate_button);root.addLayout(left,1)
        right=QVBoxLayout();self.selector=QComboBox();self.selector.currentIndexChanged.connect(self.display);right.addWidget(self.selector)
        self.tabs=QTabWidget();self.view=ResultView();self.report=ReportView();self.tabs.addTab(self.view,'Gráfico y valores');self.tabs.addTab(report_panel(self.report),'Fórmula e informe');right.addWidget(self.tabs);root.addLayout(right,2)
        self.algebraic_key=None
        self.algebraic_button=QPushButton('Abrir H en Fourier inversa algebraica')
        self.algebraic_button.setEnabled(False);self.algebraic_button.clicked.connect(self.open_algebraic)
        right.addWidget(self.algebraic_button)
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
        self.h.frequency_units.setCurrentText('rad/muestra' if self.domain.currentIndex()==0 else 'rad/s');self.h.frequency_units.setEnabled(False)
        digital=self.domain.currentIndex()==0
        self.step.setText('1' if digital else '0.01');self.step.setEnabled(not digital)
        self.start.setText('-32' if digital else '-2');self.count.setText('65' if digital else '401')
        self.h.origin.setText('-pi' if digital else '-10')
        self.h.step.setText('pi/1024' if digital else '20/2048');self.h.count.setText('2049')
        self.update_inputs()
    def calculate(self):
        try:
            digital=self.domain.currentIndex()==0;domain='discrete' if digital else 'continuous';unit='rad/muestra' if digital else 'rad/s'
            response=self.h._read().copy_with(name='Respuesta H(ω)')
            if self.h.mode.currentIndex()==2 and response.units!=unit:raise ValueError('La respuesta importada debe usar '+unit+'.')
            from .signal_semantics import require_frequency_response
            require_frequency_response(response)
            response.units=unit;response.metadata={**response.metadata,'operation':'frequency_filter','time_domain':domain}
            start=integer_field(self.start) if digital else self.scalar(self.start)
            count=integer_field(self.count);step=self.scalar(self.step)
            source=(self.xd if digital else self.xc).read() if self.operation.currentIndex()==1 else None
            allow_periodic=digital and self.periodic.isChecked()
            snapshot=self.state.snapshot()
            from .inverse_fourier_report import from_signal,exact_section,numeric_section
            from .result_summary import Summary,Section
            def compute():
                values,report=analyze(response,domain,start,int(count),step,source,allow_periodic=allow_periodic)
                return values,report,from_signal(response)
            def accept(result):
                values,report,algebra=result
                if algebra and algebra['inverse']:
                    from .temporal_formula import attach_temporal_formula
                    attach_temporal_formula(values[1],algebra['inverse'])
                self.results=values;self.selector.blockSignals(True);self.selector.clear()
                keys=[]
                for value in values:
                    keys.append(self.window.publish(value,operation='Filtro por respuesta en frecuencia'))
                    self.selector.addItem(value.name)
                self.algebraic_key=None;sections=[]
                if algebra:
                    self.algebraic_key=self.window.publish({'result':algebra['definition']},title='Definición algebraica H(w)',
                        operation='Filtro por respuesta en frecuencia',parents=[keys[0]])
                    if algebra['inverse']:
                        inverse=algebra['inverse']
                        self.window.publish({'result':inverse},title='Expresión algebraica de la respuesta al impulso',
                            operation='Filtro por respuesta en frecuencia',parents=[self.algebraic_key,keys[1]])
                        sections.append(exact_section(inverse,'h'))
                sections.append(numeric_section(values[1].metadata['inverse_model'],'h'))
                if len(values)>2:
                    from .temporal_formula import sections as temporal_sections
                    sections.extend(temporal_sections(values[2]))
                sections.append(Section('Cómo interpretarlo',paragraphs=report.split('\n\n')[1:]))
                summary=Summary('Filtro definido en frecuencia',sections)
                self.algebraic_button.setText('Abrir H en DTFT inversa algebraica' if digital else 'Abrir H en Fourier inversa algebraica')
                self.algebraic_button.setEnabled(self.algebraic_key is not None)
                self.selector.blockSignals(False);self.report.set_readable(summary)
                self.window.publish({'report':summary.plain_text()},title='Filtro por tramos',operation='Informe de filtro por tramos',parents=keys[:2])
                self.display();self.tabs.setCurrentIndex(1);self.state.accept(snapshot)
            self.window._run_operation('Calculando filtro por tramos…',compute,accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá la definición',str(exc))
    def open_algebraic(self):
        if self.algebraic_key is None:return
        from .result_expressions import send_expression
        expression=self.window.project.expression(self.algebraic_key)
        destination='inverse_dtft' if expression.units=='rad/muestra' else 'fourier_inverse'
        send_expression(self.window,self.algebraic_key,destination)

    def display(self,*_):
        index=self.selector.currentIndex()
        if 0<=index<len(self.results):self.view.show_result(self.results[index])
    def receive_response(self,value):
        self.domain.setCurrentIndex(0 if value.units=='rad/muestra' else 1);self.h.set_source(value)
