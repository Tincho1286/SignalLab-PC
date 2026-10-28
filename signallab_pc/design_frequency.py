"""Frequency inspection beside the pole/zero editor, without changing its canvas."""
import numpy as np
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QComboBox,QPushButton,QFileDialog,QMessageBox
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT
from .frequency_analysis import frequency_grid,analyze_frequency,export_frequency
from .numeric_input import real_field,integer_field
from .result_state import ResultState


class DesignFrequency(QWidget):
    def __init__(self,window,domain='digital'):
        super().__init__();self.owner=window;self.system=None;self.data=None;self.domain=domain
        root=QVBoxLayout(self);row=QHBoxLayout();root.addLayout(row)
        self.start=QLineEdit('0');self.stop=QLineEdit('pi' if domain=='digital' else '10');self.count=QLineEdit('2049')
        for title,field in [('Desde',self.start),('Hasta',self.stop),('Puntos',self.count)]:
            column=QVBoxLayout();column.addWidget(QLabel(title));column.addWidget(field);row.addLayout(column)
        self.magnitude=QComboBox();self.magnitude.addItems(['Módulo lineal','Módulo en dB']);row.addWidget(self.magnitude)
        self.calculate_button=QPushButton('Actualizar respuesta');self.calculate_button.clicked.connect(self.calculate);root.addWidget(self.calculate_button)
        self.calculate_button.setEnabled(False)
        self.state=ResultState([self.start,self.stop,self.count],self.calculate_button);root.addWidget(self.state)
        self.note=QLabel('Diseñá un sistema para consultar módulo, fase y retardo de grupo.');self.note.setWordWrap(True);root.addWidget(self.note)
        self.figure=Figure(figsize=(7,6));self.canvas=FigureCanvasQTAgg(self.figure);root.addWidget(NavigationToolbar2QT(self.canvas,self));root.addWidget(self.canvas,1)
        self.export_button=QPushButton('Exportar respuesta…');self.export_button.clicked.connect(self.export);self.export_button.setEnabled(False);root.addWidget(self.export_button)
        self.magnitude.currentIndexChanged.connect(self.draw)
    def request(self,domain):
        if domain!=self.domain:
            self.start.setText('0');self.stop.setText('pi' if domain=='digital' else '10');self.domain=domain
        return real_field(self.start),real_field(self.stop),integer_field(self.count)
    def set_result(self,system,data,snapshot=None):
        self.system=system;self.data=data;self.domain=system.domain
        self.calculate_button.setEnabled(True);self.export_button.setEnabled(True);self.state.accept(snapshot if snapshot is not None else self.state.snapshot())
        self.note.setText('H incluye '+str(system.advance)+' muestras de avance. La frecuencia se evalúa en rad/muestra. Elegir una secuencia bilateral requiere además una ROC.' if system.advance else 'Frecuencia en '+data.units+'. En ceros de H, la fase y el retardo no están definidos. El criterio de estabilidad temporal también depende de la ROC y del soporte.')
        self.draw()
    def clear_result(self,system):
        self.system=system;self.data=None;self.figure.clear();self.canvas.draw_idle()
        if system.domain!=self.domain:
            self.start.setText('0');self.stop.setText('pi' if system.domain=='digital' else '10');self.domain=system.domain
        self.calculate_button.setEnabled(True);self.export_button.setEnabled(False)
        self.note.setText('Sistema cargado. Actualizar respuesta calcula su módulo, fase y retardo en el intervalo indicado.')
    def calculate(self):
        if self.system is None:return
        try:
            system=self.system;start,stop,count=self.request(system.domain);snapshot=self.state.snapshot()
            self.owner._run_operation('Calculando respuesta del diseño…',lambda:analyze_frequency(system,frequency_grid(start,stop,count)),lambda data:self.set_result(system,data,snapshot))
        except Exception as exc:QMessageBox.warning(self,'Revisá las frecuencias',str(exc))
    def mark_dirty(self):
        if self.data is not None:self.note.setText('Diseño editado. Esta respuesta corresponde al último sistema calculado; actualizá el diseño para ver los cambios.')
    def draw(self,*_):
        if self.data is None:return
        data=self.data;self.figure.clear();axes=self.figure.subplots(3,1,sharex=True)
        db=self.magnitude.currentIndex()==1
        curves=[(np.where(np.isfinite(data.db),data.db,np.nan) if db else data.magnitude,'Módulo (dB)' if db else '|H|'),(data.phase,'Fase (rad)'),(data.delay,'Retardo (muestras)' if data.system.domain=='digital' else 'Retardo (s)')]
        for index,(axis,(values,label)) in enumerate(zip(axes,curves)):
            axis.plot(data.omega,values);axis.set_ylabel(label);axis.grid(alpha=.25)
            if not np.isfinite(values).any():axis.text(.5,.5,'Módulo nulo: −∞ dB' if index==0 and db and np.all(data.magnitude==0) else 'No definido en este intervalo',ha='center',transform=axis.transAxes)
        from .signal_plot import configure_axis
        configure_axis(axes[2],units=data.units,label=('ω' if data.system.domain=='digital' else 'Ω')+' ('+data.units+')')
        axes[2].set_xlim(float(data.omega[0]),float(data.omega[-1]));self.figure.set_layout_engine('constrained');self.canvas.draw_idle()
    def open_plot(self):
        if self.data is not None:
            from .plot_view import enlarge_plot
            enlarge_plot(self.canvas,self)
    def export(self):
        if self.data is None:return
        path,selected=QFileDialog.getSaveFileName(self,'Exportar frecuencia del diseño','respuesta.csv','Tabla CSV (*.csv);;Documento JSON (*.json)')
        if not path:return
        from pathlib import Path
        if not Path(path).suffix:path+='.json' if 'JSON' in selected else '.csv'
        try:export_frequency(self.data,path)
        except Exception as exc:QMessageBox.warning(self,'No se pudo exportar la respuesta',str(exc))
