"""Entradas locales y salidas exportables para Hilbert, STFT y bloques."""
import csv,json
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QComboBox,QLineEdit,QScrollArea,QPushButton,QLabel,QTabWidget,QMessageBox,QFileDialog,QSpinBox
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT
from .numeric_input import integer_field,real_field
from .result_state import ResultState
from .report_view import ReportView,report_panel
from .atomic_file import atomic_text_file
from . import dsp_extensions as calc

class DspExtensionsPanel(QWidget):
    def __init__(self,window,action):
        super().__init__();self.window=window;self.action=action;self.result=None;self.outputs=[]
        from .toolbox import LocalInput,ResultView
        root=QHBoxLayout(self);left=QWidget();column=QVBoxLayout(left);controls=QWidget();form=QFormLayout(controls);self.form=form
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
        note=QLabel({'hilbert':'La entrada debe ser real. La aproximación por FFT supone repetición periódica del registro; los bordes pueden verse afectados.','blocks':'La salida conserva toda la convolución, incluida la cola. Fuera de ambas secuencias se supone cero.','stft':'Frecuencia angular en rad/muestra o rad/s. Se completa con ceros sólo la última ventana incompleta. Más puntos FFT no aumentan la duración observada.'}[action]);note.setWordWrap(True);form.addRow(note)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);column.addWidget(scroll,1)
        self.button=QPushButton('Calcular');self.button.setObjectName('primary');self.button.clicked.connect(self.calculate);column.addWidget(self.button);root.addWidget(left,1)
        right=QWidget();out=QVBoxLayout(right);root.addWidget(right,2)
        watched=list(self.fields.values())+[self.domain]+([self.method] if action=='blocks' else [self.taper] if action=='stft' else [])
        self.state=ResultState(watched,self.button,self.sources+([self.kernel] if self.kernel else []));out.addWidget(self.state)
        self.selector=QComboBox();self.selector.currentIndexChanged.connect(self.display);out.addWidget(self.selector);self.selector.hide()
        self.view=ResultView();self.report=ReportView();self.view.views.removeTab(1);self.view.views.insertTab(1,report_panel(self.report),'Informe')
        if action=='stft':
            self.tabs=QTabWidget();map_page=QWidget();map_layout=QVBoxLayout(map_page);bar=QHBoxLayout()
            self.frame=QSpinBox();self.frame.setMinimum(1);self.frame.setMaximum(1);self.frame.setPrefix('Ventana ');self.frame.valueChanged.connect(self.select_frame);bar.addWidget(self.frame)
            self.export_button=QPushButton('Exportar STFT completa (CSV)…');self.export_button.setEnabled(False);self.export_button.clicked.connect(self.export_matrix);bar.addWidget(self.export_button);map_layout.addLayout(bar)
            self.figure=Figure();self.canvas=FigureCanvasQTAgg(self.figure);self.canvas.setMinimumHeight(260);map_layout.addWidget(NavigationToolbar2QT(self.canvas,self));map_layout.addWidget(self.canvas,1)
            self.tabs.addTab(map_page,'Espectrograma');self.tabs.addTab(self.view,'Espectro de una ventana');out.addWidget(self.tabs,1);self.tabs.hide();self.empty_output=QLabel('El espectrograma aparecerá después de calcular.');self.empty_output.setObjectName('muted');out.addWidget(self.empty_output)
        else:out.addWidget(self.view,1)
    def receive(self,source,key=None):
        index={'discrete':0,'continuous':1}[source.domain]
        self.domain.setCurrentIndex(index)
        self.sources[index].set_source(source,key)

    def calculate(self):
        try:
            source=self.sources[self.domain.currentIndex() if len(self.sources)>1 else 0].read();parents=[self.sources[self.domain.currentIndex() if len(self.sources)>1 else 0].reference_id];snapshot=self.state.snapshot()
            if self.action=='hilbert':job=lambda:calc.analytic_signal(source)
            elif self.action=='blocks':
                kernel=self.kernel.read();parents.append(self.kernel.reference_id);length=integer_field(self.fields['length']);method='ola' if self.method.currentIndex()==0 else 'ols';job=lambda:calc.block_convolution(source,kernel,length,method)
            else:
                args=(source,integer_field(self.fields['length']),integer_field(self.fields['overlap']),integer_field(self.fields['nfft']),self.taper.currentData(),real_field(self.fields['beta']) if self.taper.currentData()=='kaiser' else 5);job=lambda:calc.time_frequency(*args)
            parents=[key for key in parents if key]
            def accept(result):
                self.result=result;self.parents=parents
                if self.action=='hilbert':
                    self.outputs=result;report='Transformada de Hilbert y señal analítica\n\nz = x + j·H{x}\nEnvolvente = |z|\n\nSe obtienen tres registros con el mismo eje y longitud que la entrada. La parte real de z conserva x. La FFT presupone extensión periódica: el resultado depende del registro y sus extremos. En tiempo continuo se transforma el registro muestreado, no una expresión sobre todo el eje.'
                elif self.action=='blocks':
                    self.outputs=[result];m=result.metadata;report=f"Convolución por bloques · {m['method']}\n\nMuestras nuevas por bloque L: {m['block_new_samples']}\nLongitud de h: {m['kernel_length']}\nSolapamiento M−1: {m['overlap']}\nPuntos FFT: {m['fft_length']}\nBloques procesados: {m['blocks']}\nMuestras de salida: {result.values.size}\nOrigen de salida: {result.origin}\n\n"+('Se calcula la convolución de cada bloque y se suman sus colas superpuestas.' if m['method']=='ola' else 'Cada bloque incorpora M−1 muestras de historia; se descartan sus M−1 primeras salidas y se conservan L nuevas. La cola se completa con ceros.')+'\nFFT ≥ L+M−1 evita que el alias circular contamine las muestras conservadas. Se conserva la salida completa de N+M−1 muestras.'
                else:
                    self.tabs.show();self.empty_output.hide();self.outputs=[];m=result['metadata'];report='STFT y espectrograma\n\n'+f"Ventana: {m['window']}\nLongitud: {m['window_length']}\nSolapamiento: {m['overlap']}\nSalto: {m['hop']}\nPuntos FFT: {m['nfft']}\nVentanas: {m['frames']}\nCeros al final: {m['last_frame_zeros']}\n\n"+'X = FFT(tramo · ventana) / suma(ventana). El espectrograma muestra 20 log10(|X|/máximo global), entre −100 y 0 dB; no es una PSD calibrada. La fase de cada columna usa el inicio local del tramo como origen. Las frecuencias incluyen ambas mitades del espectro. Exportar guarda los valores complejos completos; la selección de ventana permite reutilizar una columna.'
                    self.frame.blockSignals(True);self.frame.setMaximum(m['frames']);self.frame.setValue(1);self.frame.blockSignals(False);self.export_button.setEnabled(True);self.draw_map();self.select_frame()
                for value in self.outputs:self.window.publish(value,operation=value.name,parents=parents)
                self.selector.blockSignals(True);self.selector.clear();self.selector.addItems([v.name for v in self.outputs]);self.selector.blockSignals(False);self.selector.setVisible(len(self.outputs)>1)
                if self.outputs:self.display()
                self.report.setPlainText(report);self.window.publish({'report':report},operation={'hilbert':'Hilbert','blocks':'Convolución por bloques','stft':'STFT'}[self.action],parents=parents);self.state.accept(snapshot)
            self.window._run_operation('Calculando '+self.action+'…',job,accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá los datos',str(exc))
    def display(self,*_):
        index=self.selector.currentIndex()
        if 0<=index<len(self.outputs):self.view.show_result(self.outputs[index])
    def draw_map(self):
        result=self.result;self.figure.clear();self.figure.set_layout_engine("constrained");axis=self.figure.add_subplot(111)
        magnitude=abs(result['values']);peak=float(magnitude.max());db=20*np.log10(np.maximum(magnitude/peak if peak else magnitude,1e-5))
        m=result['metadata'];dt=m['input_step'];half=m['hop']*dt/2;df=result['frequency'][1]-result['frequency'][0]
        extent=(result['centers'][0]-half,result['centers'][-1]+half,result['frequency'][0]-df/2,result['frequency'][-1]+df/2)
        c=axis.imshow(db,extent=extent,origin='lower',aspect='auto',interpolation='nearest',cmap='viridis',vmin=-100,vmax=0)
        axis.set_xlabel('Centro de ventana ('+result['metadata']['time_units']+')');axis.set_ylabel('ω ('+result['metadata']['frequency_units']+')');axis.set_title('Espectrograma · nivel relativo al máximo global');self.figure.colorbar(c,ax=axis,label='dB relativos');self.canvas.draw_idle()
    def select_frame(self,*_):
        if self.result is None:return
        value=calc.spectrum_slice(self.result,self.frame.value()-1);self.window.publish(value,operation='Espectro local STFT',parents=getattr(self,'parents',[]));self.view.show_result(value)
    def export_matrix(self):
        if self.result is None:return
        path,_=QFileDialog.getSaveFileName(self,'Exportar STFT completa','stft.csv','CSV (*.csv)')
        if not path:return
        try:
            result=self.result
            with atomic_text_file(path,newline='') as stream:
                stream.write('# '+json.dumps(result['metadata'],ensure_ascii=False)+'\n');writer=csv.writer(stream);writer.writerow(['ventana','centro','frecuencia_angular','real','imaginaria'])
                for column,center in enumerate(result['centers']):
                    for omega,value in zip(result['frequency'],result['values'][:,column]):writer.writerow([column+1,float(center),float(omega),float(value.real),float(value.imag)])
            self.window.statusBar().showMessage('STFT completa exportada: '+path)
        except Exception as exc:QMessageBox.warning(self,'No se pudo exportar',str(exc))
