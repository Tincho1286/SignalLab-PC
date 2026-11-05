"""Independent frequency input and integer output interval for inverse DTFT."""
from PySide6.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QFormLayout,QScrollArea,QLineEdit,QPushButton,QLabel,QMessageBox
from .inverse_dtft import inverse_dtft
from .numeric_input import integer_field
from .result_state import ResultState
from .report_view import ReportView,report_panel
from .result_summary import Summary,Section,Formula

class InverseDtftPanel(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window;self.result=None
        from .toolbox import LocalInput,ResultView
        root=QHBoxLayout(self);root.setContentsMargins(6,6,6,6);controls=QWidget();form=QFormLayout(controls);form.setContentsMargins(4,4,4,4);form.setProperty('stackFields',True)
        self.source=LocalInput('X(ω): un período de la DTFT','frequency');self.source.bind_project(window)
        self.source.frequency_units.setCurrentIndex(1);self.source.expression.setText('1/(1-0.5*exp(-i*w))')
        self.source.origin.setText('-pi');self.source.count.setText('1025');self.source.step.setText('2*pi/1024');form.addRow(self.source)
        self.source.layout().setContentsMargins(4,6,4,4)
        self.source.step.setToolTip('Para N valores: 2*pi/N sin extremo repetido, o 2*pi/(N-1) con ambos extremos.')
        def frequency_grid(*_):
            mode=self.source.mode.currentIndex()
            if mode!=2:self.source.frequency_units.setCurrentIndex(1)
            self.source.layout().setRowVisible(self.source.frequency_units,False)
            self.source.step.parentWidget().setVisible(mode==1)
            if mode==0:
                try:
                    count=integer_field(self.source.count)
                    if count>=2:self.source.step.setText('2*pi/'+str(count-1))
                except ValueError:pass
        self.source.mode.currentIndexChanged.connect(frequency_grid);self.source.count.textChanged.connect(frequency_grid);frequency_grid()
        self.start=QLineEdit('-16');self.count=QLineEdit('33');form.addRow('Primer índice n de salida',self.start);form.addRow('Cantidad de muestras de salida',self.count)
        self.start.setToolTip('Entero, positivo o negativo. No es un tiempo continuo.');self.count.setToolTip('Cantidad de índices consecutivos, no el último índice.')
        self.note=QLabel('X(ω) debe cubrir un período completo de 2π en rad/muestra. La salida es x[n], con n entero. La ayuda explica la rejilla y la diferencia con la DFT inversa.');self.note.setWordWrap(True);form.addRow(self.note)
        self.calculate_button=QPushButton('Calcular DTFT inversa');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);form.addRow(self.calculate_button)
        self.state=ResultState([self.start,self.count],self.calculate_button,[self.source]);form.insertRow(0,self.state)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);root.addWidget(scroll,1)
        self.output=ResultView();root.addWidget(self.output,2);self.report=self.output.text
    def calculate(self):
        try:
            source=self.source.read();start=integer_field(self.start);count=integer_field(self.count);parents=[self.source.reference_id] if self.source.reference_id else [];snapshot=self.state.snapshot()
            from .inverse_fourier_report import from_signal,exact_section,numeric_section
            def compute():
                return inverse_dtft(source,start,count),from_signal(source)
            def accept(data):
                result,algebra=data
                exact=algebra['inverse'] if algebra else None
                if exact:
                    from .temporal_formula import attach_temporal_formula
                    attach_temporal_formula(result,exact)
                self.result=result;key=self.window.publish(result,operation='DTFT inversa numérica',parents=parents)
                self.output.show_result(result);self.output.result_ids=[key]
                sections=[]
                if exact:
                    sections.append(exact_section(exact,'x'))
                    self.output.expression_key=self.window.publish({'result':exact},title='Expresión algebraica de x[n]',operation='DTFT inversa algebraica',parents=[key])
                sections.append(numeric_section(result.metadata['inverse_model'],'x'))
                self.report.set_readable(Summary('DTFT inversa numérica',sections+[
                    Section('Regla de la transformada',formulas=[Formula('x[n] = Integral(X(w)*exp(i*w*n),(w,-pi,pi))/(2*pi)','x[n] = (1/2π) ∫ de −π a π X(ω)e^(iωn)dω')]),
                    Section('Entrada y salida',rows=[('Unidad de frecuencia','rad/muestra'),('Puntos ingresados',str(len(source.values))),('Frecuencias independientes',str(result.metadata['independent_frequencies'])),('Índices de salida',str(start)+' a '+str(start+count-1)),('Integración',result.metadata['quadrature'])]),
                    Section('Cómo interpretarlo',paragraphs=[result.metadata['scope'],'Aumentá la resolución de X(ω) para estudiar la aproximación. El intervalo elegido muestra una parte de la secuencia; no impone que la secuencia completa sea finita.']),
                ]));self.state.accept(snapshot)
            self.window._run_operation('Calculando DTFT inversa…',compute,accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá la DTFT inversa',str(exc))
