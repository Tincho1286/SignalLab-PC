"""Inputs for the third study of the existing phase/compensation document."""
from PySide6.QtWidgets import QWidget,QFormLayout,QComboBox,QLineEdit,QLabel,QCheckBox
from .numeric_input import real_field,integer_field
from .coefficient_editor import split_coefficients


class ReconstructionControls(QWidget):
    def __init__(self,window):
        super().__init__();form=QFormLayout(self);form.setContentsMargins(0,0,0,0);form.setProperty('stackFields',True);form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        from .toolbox import LocalInput
        self.kind=QComboBox()
        for title,key in [('Módulo lineal → fase mínima','magnitude'),('Módulo en dB → fase mínima','db'),('Fase desenrollada → módulo','phase')]:self.kind.addItem(title,key)
        form.addRow('Dato conocido',self.kind)
        self.source=LocalInput('Datos en un período completo','frequency');self.source.layout().setContentsMargins(4,10,4,6);self.source.bind_project(window);self.source.frequency_units.setCurrentIndex(1);self.source.layout().setRowVisible(self.source.frequency_units,False)
        self.source.origin.setText('-pi');self.source.origin.setReadOnly(True);self.source.step.setReadOnly(True);self.source.count.setText('2049')
        for field in (self.source.origin,self.source.step):field.parentWidget().hide()
        self.source.coordinate_labels[self.source.count].setText('Puntos, incluidos −π y π')
        self.defaults={'magnitude':'1/sqrt(1.25-cos(w))','db':'-10*log(1.25-cos(w))/log(10)','phase':'-atan(0.5*sin(w)/(1-0.5*cos(w)))'}
        self.drafts={};self.last_kind='magnitude';self.source.expression.setText(self.defaults['magnitude'])
        form.addRow(self.source)
        self.real_half=QCheckBox('Completar 0…π por simetría real');self.real_half.setToolTip('Para archivos de un sistema real: se completa el módulo par o la fase impar después de quitar el desplazamiento. No se supone esa simetría para un sistema complejo.');form.addRow(self.real_half)
        note=QLabel('Fórmulas y listas cubren −π…π, con ambos extremos. Archivos: un período completo o 0…π si indicás simetría real.');note.setWordWrap(True);note.setObjectName('muted');form.addRow(note)
        self.delay=QLineEdit('0');form.addRow('Desplazamiento d · positivo retrasa, negativo adelanta',self.delay)
        self.constant_phase=QLineEdit('0');form.addRow('Fase constante elegida (rad)',self.constant_phase)
        self.reference_gain=QLineEdit('2');form.addRow('Módulo conocido en ω=0',self.reference_gain)
        self.floor=QLineEdit('0');form.addRow('Piso del módulo lineal (0 = sin modificar)',self.floor)
        self.scope=QLabel('Se reconstruye un modelo de fase mínima. El dato no revela factores paso todo ni desplazamientos desconocidos.');self.scope.setWordWrap(True);form.addRow(self.scope)
        self.editors=[self.kind,self.delay,self.constant_phase,self.reference_gain,self.floor,self.real_half]
        self.source.count.textChanged.connect(self.update_grid);self.source.samples.textChanged.connect(self.update_grid);self.source.mode.currentIndexChanged.connect(self.update_grid);self.kind.currentIndexChanged.connect(self.update_kind)
        self.update_grid();self.update_kind()
    def update_grid(self,*_):
        self.source.frequency_units.setCurrentIndex(1);self.source.layout().setRowVisible(self.source.frequency_units,False)
        if self.source.mode.currentIndex()==2:return
        count=self.source.count.text()
        if self.source.mode.currentIndex()==1:
            try:count=str(len(split_coefficients(self.source.samples.text())))
            except ValueError:return
        self.source.step.setText('2*pi/('+count+'-1)')
    def update_kind(self,*_):
        key=self.kind.currentData()
        if key!=self.last_kind:
            self.drafts[self.last_kind]=(self.source.expression.text(),self.source.samples.text())
            expression,samples=self.drafts.get(key,(self.defaults[key],'1,1,1' if key=='magnitude' else '0,0,0'))
            self.source.expression.setText(expression);self.source.samples.setText(samples);self.last_kind=key
        phase=key=='phase';self.layout().setRowVisible(self.constant_phase,not phase);self.layout().setRowVisible(self.reference_gain,phase);self.layout().setRowVisible(self.floor,not phase)
        self.source.layout().labelForField(self.source.expression).setText('Φ(ω) desenrollada · rad' if phase else '20·log10 M(ω)' if key=='db' else 'M(ω) · amplitud lineal')
        self.scope.setText('La fase debe estar desenrollada. Indicá d si contiene un retardo/avance: se quita antes de reconstruir el módulo. La escala se fija con el módulo conocido en frecuencia cero.' if phase else 'Se elige fase mínima para el modelo base. d y la fase constante se agregan después; no se obtienen del módulo. El piso, si se aplica, cambia los datos y se informa.')
    def request(self):
        phase=self.kind.currentData()=='phase'
        return self.source.read(),self.kind.currentData(),dict(delay=integer_field(self.delay),constant_phase=0. if phase else real_field(self.constant_phase),reference_gain=real_field(self.reference_gain) if phase else 1.,floor=0. if phase else real_field(self.floor),real_half_period=self.real_half.isChecked())
