"""Exploración contextual en la biblioteca, separada de los datos del laboratorio."""
import html
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QListWidget,QPushButton,QButtonGroup,QScrollArea,QSlider
from .tool_help_catalog import GUIDES

class InteractiveLesson(QWidget):
    def __init__(self):
        super().__init__();self.box=QVBoxLayout(self);self.content=None
    def set_section(self,section):
        if self.content is not None:self.box.removeWidget(self.content);self.content.hide();self.content.setParent(None);self.content.deleteLater()
        self.content=QScrollArea();self.content.setWidgetResizable(True);self.box.addWidget(self.content);body=QWidget();self.content.setWidget(body);layout=QVBoxLayout(body)
        route=section['route']
        if route is None:
            label=QLabel('Consultá la explicación del concepto en Lectura. Para explorar entradas y resultados, elegí una herramienta.');label.setWordWrap(True);layout.addWidget(label);layout.addStretch();return
        guide=GUIDES[route[1],route[2]];heading=QLabel(section['title']);heading.setObjectName('cardTitle');layout.addWidget(heading)
        intro=QLabel('Explorá el recorrido y seleccioná un dato para entender su función. Estos ejemplos no modifican tus cálculos.');intro.setWordWrap(True);layout.addWidget(intro)
        row=QHBoxLayout();layout.addLayout(row);group=QButtonGroup(body);group.setExclusive(True)
        description=QLabel();description.setWordWrap(True);description.setMinimumHeight(70);description.setObjectName('loadedSignal')
        meanings=['Qué necesitás definir: '+guide['flow'][0]+'\nLos campos de esta herramienta se explican debajo.','Qué hace el cálculo: '+guide['flow'][1]+'\n'+guide['reading'],'Qué obtenés: '+guide['flow'][2]+'\nPodés consultar, exportar o copiar resultados compatibles a otra tarea.']
        for i,title in enumerate(['1 · Entrada','2 · Cálculo','3 · Resultado']):
            button=QPushButton(title);button.setCheckable(True);group.addButton(button);row.addWidget(button);button.clicked.connect(lambda checked=False,n=i:description.setText(meanings[n]))
            if i==0:button.setChecked(True)
        description.setText(meanings[0]);layout.addWidget(description)
        layout.addWidget(QLabel('Seleccioná el dato que querés entender'))
        fields=QListWidget();fields.setMaximumHeight(180);fields.addItems([name for name,_ in guide['parameters']]);layout.addWidget(fields)
        explanation=QLabel();explanation.setWordWrap(True);explanation.setObjectName('loadedSignal');explanation.setMinimumHeight(85);layout.addWidget(explanation)
        fields.currentRowChanged.connect(lambda index:explanation.setText(guide['parameters'][index][1]) if index>=0 else None);fields.setCurrentRow(0)
        if route[1]=='course_tools' and route[2] in ('fir','iir'):
            from .band_edges import BandEdgesEditor
            layout.addWidget(QLabel('Probá distintos bordes y observá el ancho de las transiciones'));layout.addWidget(BandEdgesEditor())
        if route[1:3]==('fourier',6):
            layout.addWidget(QLabel('Ejemplo: cambiá la amplitud de la señal original'))
            gain=QSlider(Qt.Orientation.Horizontal);gain.setRange(0,40);gain.setValue(10);layout.addWidget(gain);value=QLabel();value.setWordWrap(True);layout.addWidget(value)
            def update(v):value.setText(f'Amplitud multiplicada por {v/10:g} → espectro multiplicado por {v/10:g} → densidad multiplicada por {(v/10)**2:g}. La densidad depende del cuadrado del módulo.')
            gain.valueChanged.connect(update);update(10)
        if route[1]=='sampling' and route[2] in (0,1,3):
            layout.addWidget(QLabel('Ejemplo: relación entre tasa y separación temporal'))
            rate=QSlider(Qt.Orientation.Horizontal);rate.setRange(1,1000);rate.setValue(100);layout.addWidget(rate);value=QLabel();value.setWordWrap(True);layout.addWidget(value)
            def update(v):value.setText(f'Fs = {v} muestras/s → T = {1/v:.6g} s. Con 101 muestras desde t=0, el último instante es {100/v:.6g} s. Fs es tasa de muestreo; no es frecuencia angular.')
            rate.valueChanged.connect(update);update(100)
        layout.addStretch()
