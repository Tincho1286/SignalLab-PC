"""Time-frequency results: figure controls, frame records and reversible synthesis."""
import csv,json
import numpy as np
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QComboBox,QLineEdit,QSpinBox,QPushButton,QLabel,QTabWidget,QMessageBox,QFileDialog,QAbstractSpinBox
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT
from .report_view import ReportView,report_panel
from .atomic_file import atomic_text_file
from .numeric_input import real_field
from . import stft_tools as math


class StftExplorer(QWidget):
    def __init__(self,owner):
        super().__init__();self.owner=owner;self.data=None;self.parents=[];self.saved={};self.selection=None
        from .toolbox import ResultView
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0)
        self.frame_controls=QWidget();row=QHBoxLayout(self.frame_controls);row.setContentsMargins(0,0,0,0);layout.addWidget(self.frame_controls);self.frame=QSpinBox();self.frame.setRange(1,1);self.frame.setPrefix('Ventana ');self.frame.setAccessibleName('Ventana temporal seleccionada');self.frame.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.previous=QPushButton('‹');self.next=QPushButton('›')
        for button,name in ((self.previous,'Ventana anterior'),(self.next,'Ventana siguiente')):button.setMaximumWidth(36);button.setAccessibleName(name);row.addWidget(button)
        self.previous.clicked.connect(self.frame.stepDown);self.next.clicked.connect(self.frame.stepUp);row.insertWidget(1,self.frame)
        self.part=QComboBox();self.part.addItems(['Espectro de la ventana','Tramo de entrada','Ventana aplicada','Tramo enventanado','Densidad bilateral de la ventana']);row.addWidget(self.part,1)
        self.tabs=QTabWidget();layout.addWidget(self.tabs,1)
        page=QWidget();plot=QVBoxLayout(page);self.tabs.addTab(page,'Espectrograma')
        controls=QWidget();form=QFormLayout(controls);form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.scale=QComboBox()
        for name,key in [('Nivel relativo (dB)','relative_db'),('Amplitud lineal','amplitude'),('Densidad bilateral','density'),('Densidad bilateral (dB)','density_db')]:self.scale.addItem(name,key)
        self.clock=QComboBox();self.clock.addItems(['Índices y rad/muestra','Segundos y rad/s'])
        self.range=QLineEdit('100');self.range.setMaximumWidth(160);self.range.setAccessibleName('Rango visible en dB')
        self.phase=QComboBox();self.phase.addItems(['Origen del registro','Inicio local del tramo'])
        form.addRow('Escala del mapa',self.scale);form.addRow('Ejes',self.clock);form.addRow('Rango visible (dB)',self.range);form.addRow('Fase del espectro exportado',self.phase)
        self.figure=Figure();self.canvas=FigureCanvasQTAgg(self.figure);self.toolbar=NavigationToolbar2QT(self.canvas,self)
        self.canvas._signallab_plot_controls=controls;plot.addWidget(controls);plot.addWidget(self.toolbar);plot.addWidget(self.canvas,1)
        self.canvas._signallab_explicit_plot=True
        self.canvas.mpl_connect('button_press_event',self.pick_frame)
        self.frame_view=ResultView();self.tabs.addTab(self.frame_view,'Ventana seleccionada')
        page=QWidget();inverse_layout=QVBoxLayout(page);self.tabs.addTab(page,'Reconstrucción')
        self.reconstruct=QPushButton('Reconstruir registro desde STFT');self.reconstruct.setObjectName('primary');self.reconstruct.clicked.connect(self.inverse);inverse_layout.addWidget(self.reconstruct)
        self.inverse_note=QLabel('La inversa verifica que las ventanas conserven información en cada muestra.');self.inverse_note.setWordWrap(True);inverse_layout.addWidget(self.inverse_note)
        self.inverse_view=ResultView();inverse_layout.addWidget(self.inverse_view,1)
        from .spectral_measurements_panel import StftBandPowerView
        self.band_power=StftBandPowerView(owner);self.tabs.addTab(self.band_power,'Potencia por banda')
        self.report=ReportView();self.tabs.addTab(report_panel(self.report),'Informe');self.tabs.currentChanged.connect(lambda index:self.frame_controls.setVisible(index in (0,1)))
        self.export=QPushButton('Exportar STFT completa (CSV)…');self.export.clicked.connect(self.export_matrix);layout.addWidget(self.export)
        for combo in (self.scale,self.clock):combo.currentIndexChanged.connect(self.redraw)
        self.phase.currentIndexChanged.connect(self.show_frame);self.frame.valueChanged.connect(self.show_frame);self.part.currentIndexChanged.connect(self.show_frame);self.range.editingFinished.connect(self.redraw)

    def set_data(self,data,parents):
        self.data=data;self.parents=list(parents);self.saved={};m=data['metadata']
        self.band_power.set_data(data,parents)
        self.figure.clear();self.axis=None;self.selection=None;self.canvas._signallab_has_plot_result=False
        self.frame_view.clear_result()
        self.frame.blockSignals(True);self.frame.setMaximum(m['frames']);self.frame.setValue(1);self.frame.blockSignals(False)
        self.clock.blockSignals(True);continuous=m['input_domain']=='continuous';self.clock.setCurrentIndex(1 if continuous else 0)
        self.clock.setEnabled(not continuous and 'sample_rate_hz' in m['input_clock']);self.clock.blockSignals(False)
        self.clock.setToolTip('El reloj registrado permite convertir los ejes.' if self.clock.isEnabled() or continuous else 'Sin Fs registrada, se utilizan índices y rad/muestra.')
        self.inverse_view.clear_result();self.inverse_note.setText('La inversa verifica cobertura muestra a muestra antes de publicar el registro.')
        self.report.setPlainText('STFT y espectrograma\n\n'+f"Ventana periódica: {m['window']}\nLongitud: {m['window_length']}\nSolapamiento: {m['overlap']}\nSalto: {m['hop']}\nPuntos FFT: {m['nfft']}\nVentanas: {m['frames']}\nCeros iniciales: {m['left_padding']}\nCeros en la última ventana: {m['last_frame_zeros']}\n\n"+
            'Amplitud = FFT(tramo·ventana)/Σventana. La densidad bilateral divide |FFT(tramo·ventana)|² por 2π·Fs·Σventana²; Fs=1 en rad/muestra. Su integral por suma de bins es la potencia del tramo ponderada por ventana², no una certificación del espectro del proceso. No se resta la media.\n\nEl rango en dB sólo recorta la vista: el CSV conserva la matriz compleja. Más puntos FFT densifican el eje sin aumentar la duración de la ventana. Hacé clic sobre el mapa para seleccionar un tramo; durante zoom o desplazamiento se conserva la navegación.\n\nVentana seleccionada permite reutilizar el tramo, los pesos, su producto o el espectro. La fase puede usar el origen temporal original o el inicio local. El reloj y las unidades de cada salida se conservan.\n\nLa reconstrucción aplica IFFT y suma ponderada, dividiendo por la suma de ventanas². Si hay muestras sin cobertura suficiente se informa y no se inventa una señal completa.')
        self.redraw()

    @property
    def physical(self):return self.clock.currentIndex()==1

    def redraw(self,*_):
        if self.data is None:return
        try:
            frequency,centers,unit,time_unit,_=math.axes(self.data,self.physical)
            logarithmic=self.scale.currentData() in ('relative_db','density_db');self.range.setEnabled(logarithmic)
            values,label,limits=math.map_values(self.data,self.scale.currentData(),self.physical,real_field(self.range,minimum=0,strict=True) if logarithmic else 100)
            m=self.data['metadata'];spacing=m['input_step'] if m['input_domain']=='continuous' or not self.physical else 1/float(m['input_clock']['sample_rate_hz'])
            half=m['hop']*spacing/2;df=frequency[1]-frequency[0]
            self.figure.clear();self.figure.set_layout_engine('constrained');self.axis=self.figure.add_subplot(111)
            image=self.axis.imshow(values,extent=(centers[0]-half,centers[-1]+half,frequency[0]-df/2,frequency[-1]+df/2),origin='lower',aspect='auto',interpolation='nearest',cmap='viridis',**(dict(vmin=limits[0],vmax=limits[1]) if limits else {}))
            self.axis.set_xlabel('Centro de ventana ('+time_unit+')');self.axis.set_ylabel('ω ('+unit+')');self.axis.set_title('STFT · '+self.scale.currentText());self.figure.colorbar(image,ax=self.axis,label=label)
            self.selection=None;self._centers=centers;self._spacing=spacing;self.canvas.draw_idle()
        except Exception as exc:
            self.figure.clear();self.axis=None;self.selection=None;self.canvas._signallab_has_plot_result=False
            axis=self.figure.add_subplot(111);axis.set_axis_off();axis.text(.04,.5,'Vista no disponible.\n'+str(exc),transform=axis.transAxes,wrap=True);self.canvas.draw_idle()
            QMessageBox.warning(self,'Vista del espectrograma',str(exc))
        self.show_frame(notify=False)

    def pick_frame(self,event):
        if self.data is None or event.inaxes is not getattr(self,'axis',None) or event.button!=1 or event.xdata is None or self.toolbar.mode:return
        self.frame.setValue(int(np.argmin(abs(self._centers-event.xdata)))+1)

    def show_frame(self,*_,notify=True):
        if self.data is None:return
        try:
            index=self.frame.value()-1;part=self.part.currentIndex();phase='global' if self.phase.currentIndex()==0 else 'local'
            self.previous.setEnabled(index>0);self.next.setEnabled(index+1<self.data['metadata']['frames'])
            value=math.spectrum(self.data,index,physical=self.physical,phase=phase) if part==0 else math.density_spectrum(self.data,index,self.physical) if part==4 else math.frame_signals(self.data,index)[part-1]
            key=(index,part,self.physical,phase)
            if key not in self.saved:self.saved[key]=self.owner.publish(value,operation='Inspección STFT · '+value.name,parents=self.parents)
            self.frame_view.show_result(value);self.frame_view.result_ids=[self.saved[key]]
            if getattr(self,'axis',None) is not None:
                if self.selection is not None:self.selection.remove()
                center=self._centers[index];half=self.data['metadata']['window_length']*self._spacing/2
                self.selection=self.axis.axvspan(center-half,center+half,facecolor='#ffffff',alpha=.12,edgecolor='#ffffff')
                self.selection._signallab_probe=True;self.selection._signallab_reference=True;self.canvas.draw_idle()
        except Exception as exc:
            self.frame_view.clear_result('No se obtuvo esta vista: '+str(exc))
            if notify:QMessageBox.warning(self,'Ventana seleccionada',str(exc))

    def inverse(self):
        if self.data is None:return
        data=self.data
        def accept(result):
            key=self.owner.publish(result,operation='STFT inversa',parents=self.parents);self.inverse_view.show();self.inverse_view.show_result(result);self.inverse_view.result_ids=[key]
            peak=max(np.max(abs(data['source'].values.real)),np.max(abs(data['source'].values.imag)))
            error=float(np.max(abs(result.values/peak-data['source'].values/peak))) if peak else float(np.max(abs(result.values)))
            self.inverse_note.setText(f'Registro reconstruido: {len(result.values)} muestras. Error máximo respecto al registro de entrada, dividido por su amplitud máxima de componente: {error:.6g}. Cobertura mínima: {result.metadata["coverage_min"]:.6g}.')
        self.owner._run_operation('Reconstruyendo registro desde STFT…',lambda:math.synthesize(data),accept)

    def export_matrix(self):
        if self.data is None:return
        path,_=QFileDialog.getSaveFileName(self,'Exportar STFT completa','stft.csv','CSV (*.csv)')
        if not path:return
        try:
            data=self.data;m=data['metadata'];phase='global' if self.phase.currentIndex()==0 else 'local';frequency,centers,unit,time_unit,_=math.axes(data,self.physical)
            with atomic_text_file(path,newline='') as stream:
                stream.write('# '+json.dumps(dict(m,export_phase=phase,export_frequency_units=unit,export_time_units=time_unit),ensure_ascii=False)+'\n');writer=csv.writer(stream);writer.writerow(['ventana','centro','frecuencia_angular','real','imaginaria'])
                for index,center in enumerate(centers):
                    spectrum=math.spectrum(data,index,physical=self.physical,phase=phase)
                    for omega,value in zip(frequency,spectrum.values):writer.writerow([index+1,float(center),float(omega),float(value.real),float(value.imag)])
            self.owner.statusBar().showMessage('STFT completa exportada: '+path)
        except Exception as exc:QMessageBox.warning(self,'No se pudo exportar',str(exc))
