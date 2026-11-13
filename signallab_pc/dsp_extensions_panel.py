"""Local inputs for Hilbert, reversible STFT and inspected block convolution."""
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QComboBox,QLineEdit,QScrollArea,QPushButton,QLabel,QMessageBox,QCheckBox
from .numeric_input import integer_field,real_field
from .result_state import ResultState
from . import dsp_extensions as calc


class DspExtensionsPanel(QWidget):
    def __init__(self,window,action):
        super().__init__();self.window=window;self.action=action;self.result=None;self.outputs=[]
        from .toolbox import LocalInput,ResultView
        root=QHBoxLayout(self);left=QWidget();column=QVBoxLayout(left);controls=QWidget();form=QFormLayout(controls);self.form=form
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.domain=QComboBox();self.domain.addItems(['Secuencia discreta x[n]','Registro continuo x(t)'])
        self.sources=[LocalInput('Entrada x[n]','discrete')]
        if action!='blocks':self.sources.append(LocalInput('Entrada x(t)','continuous'));form.addRow('Dominio',self.domain)
        for source in self.sources:source.bind_project(window);form.addRow(source)
        if len(self.sources)>1:
            def domain_changed(*_):
                for i,source in enumerate(self.sources):form.setRowVisible(source,i==self.domain.currentIndex())
            self.domain.currentIndexChanged.connect(domain_changed);domain_changed()
        self.kernel=None;self.fields={}
        def field(key,label,value):
            edit=QLineEdit(value);self.fields[key]=edit;form.addRow(label,edit)
        if action=='blocks':
            self.kernel=LocalInput('Respuesta al impulso h[n]','discrete');self.kernel.bind_project(window);form.addRow(self.kernel)
            self.method=QComboBox();self.method.addItems(['Solapamiento-suma · overlap-add','Solapamiento-almacenamiento · overlap-save']);form.addRow('Método',self.method);field('length','Muestras nuevas por bloque L','32')
        elif action=='stft':
            field('length','Muestras de cada ventana','32');field('overlap','Muestras compartidas entre ventanas','16');field('nfft','Puntos de FFT por ventana','128')
            self.taper=QComboBox()
            for label,value in [('Rectangular','boxcar'),('Hann','hann'),('Hamming','hamming'),('Blackman','blackman'),('Bartlett','bartlett'),('Kaiser','kaiser')]:self.taper.addItem(label,value)
            self.taper.setCurrentIndex(1);form.addRow('Ventana',self.taper);field('beta','β de Kaiser','5');self.taper.currentIndexChanged.connect(lambda *_:form.setRowVisible(self.fields['beta'],self.taper.currentData()=='kaiser'));form.setRowVisible(self.fields['beta'],False)
            self.padding=QCheckBox('Completar ambos extremos con ceros');self.padding.setChecked(True);form.addRow(self.padding)
        note=QLabel({'hilbert':'La entrada debe ser real. La FFT supone repetición periódica del registro; los bordes pueden verse afectados.','blocks':'Se conserva toda la convolución, incluida la cola. El inspector distingue historia, descartes y contribuciones.','stft':'La ayuda explica escalas, reloj y reconstrucción. Completar ambos extremos evita perder muestras en los ceros de una ventana; la inversa comprueba la cobertura efectiva.'}[action]);note.setWordWrap(True);form.addRow(note)
        self.button=QPushButton('Calcular');self.button.setObjectName('primary');self.button.clicked.connect(self.calculate);column.addWidget(self.button)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);column.addWidget(scroll,1);root.addWidget(left,1)
        right=QWidget();out=QVBoxLayout(right);root.addWidget(right,2)
        watched=list(self.fields.values())+[self.domain]+([self.method] if action=='blocks' else [self.taper,self.padding] if action=='stft' else [])
        self.state=ResultState(watched,self.button,self.sources+([self.kernel] if self.kernel else []));out.addWidget(self.state)
        if action=='stft':
            from .stft_view import StftExplorer
            self.explorer=StftExplorer(window);out.addWidget(self.explorer,1);self.explorer.hide();self.empty_output=QLabel('El espectrograma aparecerá después de calcular.');out.addWidget(self.empty_output)
            self.view=self.explorer.frame_view;self.report=self.explorer.report;self.tabs=self.explorer.tabs;self.frame=self.explorer.frame;self.figure=self.explorer.figure;self.canvas=self.explorer.canvas
        else:
            self.selector=QComboBox();self.selector.currentIndexChanged.connect(self.display);out.addWidget(self.selector);self.selector.hide()
            self.view=ResultView();self.report=self.view.text;out.addWidget(self.view,1)
            if action=='blocks':
                from .block_inspection_view import BlockInspector
                self.inspector=BlockInspector(window);self.inspector_index=self.view.views.addTab(self.inspector,'Inspeccionar bloques');self.view.views.setTabVisible(self.inspector_index,False)

    def receive(self,source,key=None):
        index={'discrete':0,'continuous':1}[source.domain];self.domain.setCurrentIndex(index);self.sources[index].set_source(source,key)

    def calculate(self):
        try:
            local=self.sources[self.domain.currentIndex() if len(self.sources)>1 else 0];source=local.read();parents=[local.reference_id];snapshot=self.state.snapshot()
            if self.action=='hilbert':job=lambda:calc.analytic_signal(source)
            elif self.action=='blocks':
                kernel=self.kernel.read();parents.append(self.kernel.reference_id);length=integer_field(self.fields['length']);method='ola' if self.method.currentIndex()==0 else 'ols'
                def job():
                    from .block_inspection import capture
                    result=calc.block_convolution(source,kernel,length,method);return result,capture(source,kernel,result)
            else:
                args=(source,integer_field(self.fields['length']),integer_field(self.fields['overlap']),integer_field(self.fields['nfft']),self.taper.currentData(),real_field(self.fields['beta']) if self.taper.currentData()=='kaiser' else 5)
                boundary='centered' if self.padding.isChecked() else 'tail';job=lambda:calc.time_frequency(*args,boundary=boundary)
            parents=[key for key in parents if key]
            def accept(calculated):
                self.parents=parents
                if self.action=='stft':
                    self.result=calculated;self.explorer.show();self.empty_output.hide();self.explorer.set_data(calculated,parents)
                    report_key=self.window.publish({'report':self.report.toPlainText()},operation='STFT',parents=parents)
                    self.explorer.band_power.parents=parents+[report_key]
                else:
                    if self.action=='hilbert':
                        self.result=calculated;self.outputs=calculated
                        report='Transformada de Hilbert y señal analítica\n\nz = x + j·H{x}\nEnvolvente = |z|\n\nSe conservan el eje y la longitud. La FFT presupone extensión periódica: los extremos del registro afectan al resultado. En continuo se transforma el registro muestreado, no una expresión sobre todo el eje.'
                    else:
                        result,trace=calculated;self.result=result;self.outputs=[result];m=result.metadata
                        report=f"Convolución por bloques · {m['method']}\n\nMuestras nuevas L: {m['block_new_samples']}\nLongitud de h: {m['kernel_length']}\nSolapamiento: {m['overlap']}\nPuntos FFT: {m['fft_length']}\nBloques: {m['blocks']}\nMuestras de salida: {len(result.values)}\n\nEl inspector permite recorrer entradas, salidas FFT y contribuciones. OLA suma las colas; OLS descarta las primeras M−1 salidas circulares. La salida completa tiene N+M−1 muestras y supone extensión por ceros."
                    keys=[self.window.publish(value,operation=value.name,parents=parents) for value in self.outputs]
                    self.selector.blockSignals(True);self.selector.clear();self.selector.addItems([v.name for v in self.outputs]);self.selector.blockSignals(False);self.selector.setVisible(len(self.outputs)>1);self.display();self.report.setPlainText(report)
                    self.window.publish({'report':report},operation='Hilbert' if self.action=='hilbert' else 'Convolución por bloques',parents=parents)
                    if self.action=='blocks':
                        self.view.views.setCurrentIndex(1)
                        self._block_trace=trace;self._block_parents=parents+keys;self.view.views.setTabVisible(self.inspector_index,True)
                        # Start the optional inspection after the current calculation releases its worker.
                        self.inspector.trace=None;self.inspector.data=None
                        self.inspector.view.clear_result()
                        self.view.views.currentChanged.connect(self.prepare_inspector) if not hasattr(self,'_inspector_connected') else None;self._inspector_connected=True
                self.state.accept(snapshot)
            self.window._run_operation('Calculando '+self.action+'…',job,accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá los datos',str(exc))

    def prepare_inspector(self,index):
        if index==self.inspector_index and self.inspector.trace is None:self.inspector.set_trace(self._block_trace,self._block_parents)

    def display(self,*_):
        index=self.selector.currentIndex()
        if 0<=index<len(self.outputs):self.view.show_result(self.outputs[index])

    def export_matrix(self):
        if self.action=='stft':self.explorer.export_matrix()
