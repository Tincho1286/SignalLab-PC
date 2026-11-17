"""Clipboard preview that validates every cell before changing an input."""
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QDialog,QVBoxLayout,QFormLayout,QPlainTextEdit,QComboBox,QLineEdit,QCheckBox,QLabel,QTableWidget,QTableWidgetItem,QDialogButtonBox,QHeaderView
from . import sample_paste


class PasteSignalDialog(QDialog):
    def __init__(self,text,kind='discrete',origin='0',step='1',units=None,parent=None):
        super().__init__(parent);self.kind=kind;self.units=units;self.result_signal=None;self.setWindowTitle('Pegar muestras');self.resize(700,650)
        root=QVBoxLayout(self);self.text=QPlainTextEdit();self.text.setPlaceholderText('Pegá una fila, una columna o una tabla. Se admiten pi, 10^(-3) y valores complejos.');self.text.setPlainText(text);self.text.setMaximumHeight(150);root.addWidget(self.text,1)
        form=QFormLayout();form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows);root.addLayout(form);self.layout_choice=QComboBox()
        for key,title in sample_paste.LAYOUTS.items():self.layout_choice.addItem(title,key)
        form.addRow('Columnas',self.layout_choice);self.origin=QLineEdit(str(origin));self.step=QLineEdit(str(step));form.addRow('Inicio si no hay columna de eje',self.origin);form.addRow('Paso si no hay eje o hay un solo punto',self.step);self.step.setEnabled(kind!='discrete')
        self.header=QCheckBox('La primera fila es un encabezado');self.decimal=QCheckBox('Coma decimal · columnas con tabulación o punto y coma');root.addWidget(self.header);root.addWidget(self.decimal)
        self.preview=QTableWidget(0,3);self.preview.setHorizontalHeaderLabels(['Eje','Real','Imaginaria']);self.preview.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);self.preview.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);self.preview.setMaximumHeight(180);root.addWidget(self.preview,1)
        self.status=QLabel();self.status.setWordWrap(True);root.addWidget(self.status);self.buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Usar datos');self.buttons.accepted.connect(self.apply);self.buttons.rejected.connect(self.reject);root.addWidget(self.buttons)
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.setInterval(250);self.timer.timeout.connect(self.update_preview)
        for field in (self.text,self.origin,self.step):field.textChanged.connect(lambda:self.timer.start())
        self.layout_choice.currentIndexChanged.connect(lambda:self.timer.start());self.header.toggled.connect(lambda:self.timer.start());self.decimal.toggled.connect(lambda:self.timer.start());self.update_preview()
    def read(self):return sample_paste.parse(self.text.toPlainText(),self.kind,layout=self.layout_choice.currentData(),origin=self.origin.text(),step=self.step.text(),units=self.units,decimal_comma=self.decimal.isChecked(),header=self.header.isChecked())
    def update_preview(self):
        self.preview.setRowCount(0);self.result_signal=None
        try:
            value=self.read();self.result_signal=value;count=min(12,len(value.values));self.preview.setRowCount(count)
            for row in range(count):
                coordinate=int(value.origin)+row if value.domain=='discrete' else value.origin+row*value.step
                for column,text in enumerate((str(coordinate),format(value.values[row].real,'.12g'),format(value.values[row].imag,'.12g'))):self.preview.setItem(row,column,QTableWidgetItem(text))
            self.status.setText(str(len(value.values))+' muestras válidas · vista de las primeras '+str(count)+'. Todos los datos se validan antes de usarlos.');self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        except Exception as exc:self.status.setText(str(exc));self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
    def apply(self):
        self.timer.stop();self.update_preview()
        if self.result_signal is not None:self.accept()
