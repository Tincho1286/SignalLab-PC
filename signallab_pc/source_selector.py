"""Four visible input sources, preserving the calculation's three data modes."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget,QGridLayout,QToolButton,QButtonGroup,QSizePolicy

class SourceSelector(QWidget):
    viewChanged=Signal()
    def __init__(self,combo):
        super().__init__();self.combo=combo;combo.setParent(self);combo.hide();self.view=0;self.buttons=[]
        self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        row=QGridLayout(self);row.setContentsMargins(0,0,0,0);row.setSpacing(4);self.group=QButtonGroup(self)
        for i,label in enumerate(['Definir','Muestras','Archivo','Resultado']):
            button=QToolButton();button.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed);button.setText(label);button.setAccessibleName('Entrada desde '+label.lower());button.setCheckable(True);button.setProperty('segment',True);button.setToolTip(['Definir una expresión o una función por tramos','Ingresar valores o pegar una tabla con vista previa','Abrir MATLAB, CSV o JSON','Copiar una señal calculada en otra herramienta'][i]);self.group.addButton(button,i);row.addWidget(button,i//2,i%2);self.buttons.append(button)
        self.group.idClicked.connect(self.select);combo.currentIndexChanged.connect(self.sync);self.sync(combo.currentIndex())
    def select(self,index):
        self.view=index
        self.combo.setCurrentIndex(min(index,2))
        for i,button in enumerate(self.buttons):button.setChecked(i==self.view)
        self.viewChanged.emit()
    def sync(self,index):
        if index!=2 or self.view<2:self.view=index
        for i,button in enumerate(self.buttons):button.setChecked(i==self.view)
        self.viewChanged.emit()
