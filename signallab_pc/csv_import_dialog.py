"""Asignación explícita de columnas para archivos de laboratorio."""
import csv
from pathlib import Path
from PySide6.QtWidgets import QDialog,QVBoxLayout,QFormLayout,QComboBox,QSpinBox,QLineEdit,QCheckBox,QPushButton,QLabel,QMessageBox,QPlainTextEdit
from .storage import load_csv

class CsvImportDialog(QDialog):
    def __init__(self,path,kind,parent=None):
        super().__init__(parent);self.path=path;self.result_signal=None;self.setWindowTitle('Importar tabla CSV');self.resize(650,580)
        layout=QVBoxLayout(self);form=QFormLayout();layout.addLayout(form)
        self.domain=QComboBox()
        for title,value in [('Secuencia discreta','discrete'),('Señal continua muestreada','continuous'),('Espectro angular','frequency')]:self.domain.addItem(title,value)
        if kind in ('discrete','continuous','frequency'):self.domain.setCurrentIndex(['discrete','continuous','frequency'].index(kind));self.domain.setEnabled(False)
        form.addRow('Interpretación',self.domain)
        self.units=QComboBox();form.addRow('Unidades del eje del archivo',self.units)
        self.domain.currentIndexChanged.connect(self.update_units);self.update_units()
        self.delimiter=QComboBox()
        for label,value in [('Coma',','),('Punto y coma',';'),('Tabulación','\t')]:self.delimiter.addItem(label,value)
        form.addRow('Separador',self.delimiter);self.decimal=QCheckBox('Coma decimal');form.addRow(self.decimal)
        self.skip=QSpinBox();self.skip.setRange(0,1000000);self.skip.setValue(1);form.addRow('Filas de encabezado que se omiten',self.skip)
        self.axis=QSpinBox();self.axis.setRange(0,1000000);self.axis.setSpecialValueText('Sin columna: generar eje');self.axis.setValue(1)
        self.real=QSpinBox();self.real.setRange(1,1000000);self.real.setValue(2)
        self.imag=QSpinBox();self.imag.setRange(0,1000000);self.imag.setSpecialValueText('Sin parte imaginaria')
        form.addRow('Columna del eje (desde 1)',self.axis);form.addRow('Columna real',self.real);form.addRow('Columna imaginaria',self.imag)
        self.origin=QLineEdit('0');self.step=QLineEdit('1' if kind=='discrete' else '0.01');form.addRow('Inicio si se genera el eje',self.origin);form.addRow('Paso si se genera el eje o hay un solo punto',self.step)
        note=QLabel('Inicio y paso usan las unidades elegidas. El eje debe ser uniforme y creciente. Se conservan los valores; no se remuestrea. Vista previa de las primeras líneas:');note.setWordWrap(True);layout.addWidget(note)
        preview=QPlainTextEdit();preview.setReadOnly(True)
        with Path(path).open(encoding='utf-8-sig') as stream:
            lines=[]
            for _ in range(10):
                line=stream.readline(2000)
                if not line:break
                lines.append(line)
        preview.setPlainText(''.join(lines));layout.addWidget(preview,1)
        try:
            guessed=csv.Sniffer().sniff(''.join(lines),delimiters=',;\t').delimiter;self.delimiter.setCurrentIndex([',',';','\t'].index(guessed))
        except csv.Error:pass
        apply=QPushButton('Importar señal');apply.setObjectName('primary');apply.clicked.connect(self.load);layout.addWidget(apply)
    def update_units(self):
        self.units.clear()
        choices={'discrete':[('Índice n','n')],'continuous':[('Segundos','s'),('Milisegundos → segundos','ms'),('Microsegundos → segundos','us')],'frequency':[('Radianes por segundo','rad/s'),('Radianes por muestra','rad/muestra')]}
        for title,value in choices[self.domain.currentData()]:self.units.addItem(title,value)

    def load(self):
        try:
            self.result_signal=load_csv(self.path,domain=self.domain.currentData(),delimiter=self.delimiter.currentData(),skip_rows=self.skip.value(),axis_column=self.axis.value()-1 if self.axis.value() else None,real_column=self.real.value()-1,imag_column=self.imag.value()-1 if self.imag.value() else None,decimal_comma=self.decimal.isChecked(),origin=self.origin.text(),step=float(self.step.text().replace(',','.') if self.decimal.isChecked() else self.step.text()),axis_units=self.units.currentData())
            self.accept()
        except Exception as exc:QMessageBox.warning(self,'No se pudo importar',str(exc))
