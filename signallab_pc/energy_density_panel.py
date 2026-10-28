"""Densidad de energía desde una señal local o un espectro definido aquí."""
import numpy as np
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QComboBox,QLineEdit,QPushButton,QLabel,QScrollArea,QSplitter,QMessageBox
from PySide6.QtCore import Qt
from .numeric_input import real_field,integer_field
from . import fourier
from .result_state import ResultState

class EnergyDensityPanel(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window;self.results=[]
        from .toolbox import LocalInput,ResultView
        root=QHBoxLayout(self);root.setContentsMargins(0,0,0,0);split=QSplitter(Qt.Orientation.Horizontal);split.setChildrenCollapsible(False);root.addWidget(split)
        controls=QWidget();form=QFormLayout(controls);form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.input_kind=QComboBox();self.input_kind.addItems(['Señal discreta x[n]','Señal continua x(t)','Espectro X(ω) definido por mí']);form.addRow('Partir de',self.input_kind)
        self.inputs=[LocalInput('Señal discreta','discrete'),LocalInput('Señal continua','continuous'),LocalInput('Espectro complejo','frequency')]
        for source in self.inputs:source.bind_project(window);form.addRow(source)
        self.w0=QLineEdit('-pi');self.w1=QLineEdit('pi');self.points=QLineEdit('1025')
        form.addRow('Frecuencia inicial',self.w0);form.addRow('Frecuencia final',self.w1);form.addRow('Puntos del espectro',self.points)
        self.note=QLabel();self.note.setWordWrap(True);form.addRow(self.note)
        button=QPushButton('Calcular densidad de energía');button.setObjectName('primary');button.clicked.connect(self.calculate)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);scroll.setMinimumWidth(300);left=QWidget();left_box=QVBoxLayout(left);left_box.setContentsMargins(0,0,0,0);left_box.addWidget(scroll,1);left_box.addWidget(button);split.addWidget(left)
        right=QWidget();out=QVBoxLayout(right);self.state=ResultState([self.input_kind,self.w0,self.w1,self.points],button,self.inputs);out.addWidget(self.state)
        self.selector=QComboBox();self.selector.addItems(['Densidad de energía |X|²','Espectro complejo X']);self.selector.currentIndexChanged.connect(self.display);out.addWidget(self.selector)
        self.view=ResultView();out.addWidget(self.view,1);split.addWidget(right);split.setSizes([370,850]);split.setStretchFactor(1,1)
        self.form=form;self.input_kind.currentIndexChanged.connect(self.update_inputs);self.update_inputs()
    def update_inputs(self,*_):
        index=self.input_kind.currentIndex()
        for i,source in enumerate(self.inputs):self.form.setRowVisible(source,i==index)
        for field in (self.w0,self.w1,self.points):self.form.setRowVisible(field,index!=2)
        unit='rad/muestra' if index==0 else 'rad/s'
        self.form.labelForField(self.w0).setText('Frecuencia inicial ('+unit+')');self.form.labelForField(self.w1).setText('Frecuencia final ('+unit+')')
        self.note.setText('Se calcula la transformada y luego |X|² en una sola operación. No necesitás un espectro previo.' if index!=2 else 'Definí el espectro complejo y su eje. No cargues una PSD ni una densidad ya elevada al cuadrado.')
    def receive(self,value,key=None):
        index={'discrete':0,'continuous':1,'frequency':2}[value.domain];self.input_kind.setCurrentIndex(index);self.inputs[index].set_source(value,key)
    def calculate(self):
        try:
            index=self.input_kind.currentIndex();source=self.inputs[index].read();parents=[self.inputs[index].reference_id] if self.inputs[index].reference_id else []
            args=(real_field(self.w0),real_field(self.w1),integer_field(self.points)) if index!=2 else None
            snapshot=self.state.snapshot()
            def compute():
                spectrum=fourier.dtft(source,*args) if index==0 else fourier.ctft(source,*args) if index==1 else source
                density=fourier.energy_density(spectrum)
                report=fourier.energy_report(spectrum,source if index!=2 else None,density)
                return density,spectrum,report
            def accept(result):
                density,spectrum,self.energy_report=result
                spectrum_id=self.window.publish(spectrum,operation='Espectro para densidad de energía',parents=parents)
                self.window.publish(density,operation='Densidad de energía',parents=[spectrum_id]);self.window.publish({'report':self.energy_report},operation='Informe de energía y Parseval',parents=[spectrum_id]);self.results=[density,spectrum];self.display();self.state.accept(snapshot)
            self.window._run_operation('Calculando espectro y densidad de energía…',compute,accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá la entrada',str(exc))
    def display(self,*_):
        if self.results:
            self.view.show_result(self.results[self.selector.currentIndex()]);self.view.text.setPlainText(self.energy_report)
