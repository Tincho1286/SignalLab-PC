"""Explicit MATLAB variable/axis selection without flattening channels."""
from PySide6.QtWidgets import QDialog,QVBoxLayout,QFormLayout,QComboBox,QSpinBox,QLineEdit,QLabel,QPushButton,QMessageBox,QPlainTextEdit
from .matlab_import import MatlabFile,make_signal
from .numeric_input import real_field

class MatlabImportDialog(QDialog):
    def __init__(self,path,kind='import',parent=None):
        super().__init__(parent);self.data=MatlabFile(path);self.result_signal=None
        self.setWindowTitle('Importar señal de MATLAB');self.resize(680,560)
        layout=QVBoxLayout(self);form=QFormLayout();layout.addLayout(form)
        self.domain=QComboBox()
        for label,value in [('Secuencia discreta · índices n','discrete'),('Señal continua muestreada · segundos','continuous'),('Espectro angular','frequency')]:self.domain.addItem(label,value)
        if kind in ('discrete','continuous','frequency'):self.domain.setCurrentIndex(['discrete','continuous','frequency'].index(kind));self.domain.setEnabled(False)
        form.addRow('Interpretación de la señal',self.domain)
        self.variable=QComboBox();self.axis=QComboBox();self.axis.addItem('Generar eje con inicio y paso',None)
        for name,shape in self.data.entries.items():
            self.variable.addItem(name+' · '+(' × '.join(map(str,shape)) or 'escalar'),name)
            if len(shape)<=1 or 1 in shape:self.axis.addItem(name,name)
        form.addRow('Variable de la señal',self.variable)
        self.column=QSpinBox();self.column.setMinimum(1);form.addRow('Canal / columna de la matriz',self.column)
        form.addRow('Variable del eje',self.axis)
        self.origin=QLineEdit('0');self.step=QLineEdit('1' if kind!='continuous' else '0.01');form.addRow('Inicio del eje generado',self.origin);form.addRow('Paso del eje generado (o eje de un punto)',self.step)
        self.units=QComboBox();self.units.addItems(['rad/s','rad/muestra']);form.addRow('Unidad del espectro',self.units)
        note=QLabel('Elegí la variable que contiene las muestras. Para matrices, cada columna es un canal; no se concatenan canales. El eje debe ser uniforme y creciente. Los valores complejos se conservan.');note.setWordWrap(True);layout.addWidget(note)
        self.help=QPlainTextEdit();self.help.setReadOnly(True);self.help.setPlainText('MAT: vectores y matrices numéricos, incluidos complejos, versiones clásicas y 7.3. No se interpretan objetos, celdas ni tablas MATLAB.\n\nM: asignaciones numéricas, vectores/matrices, rangos inicio:paso:fin, linspace, zeros, ones, pi, i/j y funciones sin, cos, exp, sqrt, abs, real, imag, conj, log, log10, sinc. Se admiten operaciones escalares y .*, ./, .^. Para expresiones dentro de [ ], separá los elementos con comas.\n\nNo se ejecuta el script: bucles, funciones propias, indexación, gráficos y otras instrucciones requieren guardar las variables en MATLAB como .mat.\n\nImportar no normaliza ni remuestrea la señal. Para una señal continua sin variable de tiempo, ingresá el paso en segundos (por ejemplo 1/Fs, reemplazando Fs por su valor).');layout.addWidget(self.help,1)
        button=QPushButton('Importar señal');button.clicked.connect(self.load);layout.addWidget(button)
        def update(*_):
            shape=self.data.entries[self.variable.currentData()];matrix=len(shape)==2 and min(shape)>1
            self.column.setMaximum(shape[1] if matrix else 1);form.setRowVisible(self.column,matrix)
            form.setRowVisible(self.origin,self.axis.currentData() is None);form.setRowVisible(self.step,self.axis.currentData() is None or __import__('math').prod(self.data.entries[self.axis.currentData()])==1)
            form.setRowVisible(self.units,self.domain.currentData()=='frequency')
        self.variable.currentIndexChanged.connect(update);self.axis.currentIndexChanged.connect(update);self.domain.currentIndexChanged.connect(update);update()
    def load(self):
        try:
            domain=self.domain.currentData();axis=self.axis.currentData()
            # Hidden inputs do not block import of a complete axis.
            origin=real_field(self.origin) if axis is None else 0
            step=real_field(self.step) if axis is None or __import__('math').prod(self.data.entries[axis])==1 else 1
            self.result_signal=make_signal(self.data,self.variable.currentData(),self.column.value()-1,domain,axis,origin,step,self.units.currentText() if domain=='frequency' else None);self.accept()
        except Exception as exc:QMessageBox.warning(self,'Revisá la selección',str(exc))
