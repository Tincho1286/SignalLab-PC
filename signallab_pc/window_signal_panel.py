"""Generate FIR windows without loading an existing signal or filter."""
from PySide6.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QFormLayout,QScrollArea,QComboBox,QLineEdit,QCheckBox,QPushButton,QLabel
from .window_signals import WINDOWS,WINDOW_PARAMETERS,generate_window,summary
from .numeric_input import integer_field,real_field
from .validation import passive_fields, show_input_error
from .result_state import ResultState


class WindowSignalPanel(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window;self.result=None
        from .toolbox import ResultView
        root=QHBoxLayout(self);root.setContentsMargins(6,6,6,6);controls=QWidget();form=QFormLayout(controls);form.setProperty('stackFields',True)
        self.kind=QComboBox()
        for name,key in WINDOWS:self.kind.addItem(name,key)
        self.kind.setCurrentIndex(self.kind.findData('hamming'));form.addRow('Ventana',self.kind)
        self.length=QLineEdit('51');form.addRow('Longitud L (muestras)',self.length)
        self.length.setToolTip('Cantidad total de muestras. L=51 genera 51 valores; el último índice es n₀+50. No es la semilongitud ni el orden M.')
        self.beta=QLineEdit('8.6');form.addRow('β de Kaiser',self.beta)
        self.parameters={'kaiser':self.beta}
        for key,(_,label,default) in WINDOW_PARAMETERS.items():
            if key not in self.parameters:
                entry=QLineEdit(str(default));self.parameters[key]=entry;form.addRow(label,entry)
        self.grid_mode=QComboBox()
        self.grid_mode.addItem('Simétrica · diseño FIR', True)
        self.grid_mode.addItem('Periódica · análisis DFT', False)
        form.addRow('Malla de la ventana',self.grid_mode)
        self.center=QCheckBox('Centrar alrededor de n=0');form.addRow(self.center)
        self.origin=QLineEdit('0');form.addRow('Índice inicial n₀',self.origin)
        self.range_note=QLabel();self.range_note.setWordWrap(True);form.addRow(self.range_note)
        note=QLabel('El resultado tiene L muestras y vale cero fuera del intervalo.');note.setWordWrap(True);form.addRow(note)
        self.calculate_button=QPushButton('Generar ventana');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);form.addRow(self.calculate_button)
        self.state=ResultState([self.kind,self.length,*self.parameters.values(),self.grid_mode,self.center,self.origin],self.calculate_button);form.insertRow(0,self.state)
        @passive_fields()
        def configure(*_):
            for key,entry in self.parameters.items():
                visible=self.kind.currentData()==key
                form.setRowVisible(entry,visible);entry.setProperty('calculationInput',visible)
            form.setRowVisible(self.origin,not self.center.isChecked());self.origin.setProperty('calculationInput',not self.center.isChecked())
            try:
                length=integer_field(self.length)
                if length<1:raise ValueError('L debe ser positivo.')
                origin=-(length//2) if self.center.isChecked() else integer_field(self.origin)
                self.range_note.setText('Índices: '+str(origin)+' a '+str(origin+length-1)+'.'+(' Con L par, el centro geométrico queda en n=−1/2; las muestras siguen en índices enteros.' if self.center.isChecked() and length%2==0 else ''))
            except ValueError:self.range_note.setText('Indicá una longitud positiva y un índice inicial entero.')
        self.kind.currentIndexChanged.connect(configure);self.length.textChanged.connect(configure);self.center.toggled.connect(configure);self.origin.textChanged.connect(configure);configure()
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);root.addWidget(scroll,1)
        self.output=ResultView();root.addWidget(self.output,2)
        from .window_spectrum_view import WindowSpectrumView
        self.spectrum_view=WindowSpectrumView();self.spectrum_index=self.output.views.addTab(self.spectrum_view,'Espectro de la ventana');self.output.views.setTabVisible(self.spectrum_index,False)

    def calculate(self):
        try:
            length=integer_field(self.length);origin=-(length//2) if self.center.isChecked() else integer_field(self.origin)
            kind=self.kind.currentData()
            options={'symmetric':self.grid_mode.currentData()}
            if kind in self.parameters:options[WINDOW_PARAMETERS[kind][0]]=real_field(self.parameters[kind])
            snapshot=self.state.snapshot()
            def accept(calculated):
                result,analysis=calculated
                self.result=result;key=self.window.publish(result,operation='Generación de ventana')
                self.output.show_result(result);self.output.result_ids=[key]
                report=summary(result)
                from .window_spectrum import measure_section
                report.sections.insert(1,measure_section(analysis));self.output.text.set_readable(report)
                self.spectrum_view.set_data(analysis);self.output.views.setTabVisible(self.spectrum_index,True)
                self.window.publish({'report':report.plain_text(),'window_metrics':analysis.get('metrics')},title=result.name+' · definición',operation='Informe de ventana',parents=[key]);self.state.accept(snapshot)
            def work():
                result=generate_window(kind,length,origin,**options)
                from .window_spectrum import analyze
                try:analysis=analyze(result)
                except (ValueError,MemoryError) as exc:analysis={'error':str(exc)}
                return result,analysis
            self.window._run_operation('Generando ventana…',work,accept)
        except Exception as exc:show_input_error(self,'Revisá la ventana',exc)
