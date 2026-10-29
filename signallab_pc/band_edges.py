from .numeric_input import real_field
"""Bordes ordenados, con significado visible y el mismo esquema en la biblioteca."""
import json,re
import numpy as np
from PySide6.QtCore import Qt,Signal,QRectF,QLineF
from PySide6.QtGui import QPainter,QColor,QPen,QFont,QImage
from PySide6.QtWidgets import QWidget,QVBoxLayout,QFormLayout,QComboBox,QLineEdit,QLabel,QToolButton
from .engine import evaluate_expression

KINDS={
'lowpass':('Pasa bajos',['Hasta dónde dejar pasar','Desde dónde rechazar'],['0.3*pi','0.4*pi']),
'highpass':('Pasa altos',['Hasta dónde rechazar','Desde dónde dejar pasar'],['0.3*pi','0.4*pi']),
'bandpass':('Pasa banda',['Hasta dónde rechazar abajo','Desde dónde dejar pasar','Hasta dónde dejar pasar','Desde dónde rechazar arriba'],['0.2*pi','0.3*pi','0.6*pi','0.7*pi']),
'bandstop':('Rechaza banda',['Hasta dónde dejar pasar abajo','Desde dónde rechazar','Hasta dónde rechazar','Desde dónde dejar pasar arriba'],['0.2*pi','0.3*pi','0.6*pi','0.7*pi'])}
EXPLAIN={
'lowpass':['Fin de la banda de paso. Las frecuencias menores deben conservarse dentro de la tolerancia.','Inicio de la banda de rechazo. Las frecuencias mayores deben quedar por debajo del máximo de rechazo.'],
'highpass':['Fin de la banda de rechazo. Las frecuencias menores deben quedar atenuadas.','Inicio de la banda de paso. Las frecuencias mayores deben conservarse.'],
'bandpass':['Fin del rechazo de frecuencias bajas.','Inicio de la banda que querés conservar.','Fin de la banda que querés conservar.','Inicio del rechazo de frecuencias altas.'],
'bandstop':['Fin de la banda de frecuencias bajas que querés conservar.','Inicio de la banda que querés eliminar.','Fin de la banda que querés eliminar.','Inicio de la banda de frecuencias altas que querés conservar.']}

def draw_bands(p,rect,kind,edges=None,analog=False):
    p.fillRect(rect,QColor('#1b2027'));p.setRenderHint(QPainter.RenderHint.Antialiasing)
    x0=rect.left()+45;x1=rect.right()-25;y0=rect.top()+62;y1=rect.bottom()-65
    values=edges if edges is not None else ([.3,.4] if kind in ('lowpass','highpass') else [.2,.3,.6,.7])
    positions=[x0]+[x0+v*(x1-x0) for v in values]+[x1]
    modes={'lowpass':['pass','transition','stop'],'highpass':['stop','transition','pass'],'bandpass':['stop','transition','pass','transition','stop'],'bandstop':['pass','transition','stop','transition','pass']}[kind]
    colors={'pass':'#79c4ad','stop':'#dfb374','transition':'#a6b2c1'}
    p.setFont(QFont('Segoe UI',10));p.setPen(QColor('#e1e7ee'));p.drawText(QRectF(x0,rect.top()+5,x1-x0,24),'Bandas del filtro')
    for i,(label,mode) in enumerate([('Paso','pass'),('Transición','transition'),('Rechazo','stop')]):
        x=x0+i*(x1-x0)/3;p.fillRect(QRectF(x,rect.top()+35,9,9),QColor(colors[mode]));p.setPen(QColor('#e1e7ee'));p.drawText(QRectF(x+14,rect.top()+28,(x1-x0)/3-14,23),label)
    for i,mode in enumerate(modes):
        color=QColor(colors[mode]);color.setAlpha(38);p.fillRect(QRectF(positions[i],y0,positions[i+1]-positions[i],y1-y0),color)
        if mode!='transition':
            y=y0+12 if mode=='pass' else y1-10;p.setPen(QPen(QColor(colors[mode]),2));p.drawLine(QLineF(positions[i],y,positions[i+1],y))
    p.setPen(QPen(QColor('#778493'),1));p.drawLine(QLineF(x0,y1,x1,y1))
    p.setFont(QFont('Segoe UI',9))
    for i,x in enumerate(positions[1:-1]):
        p.setPen(QPen(QColor('#778493'),1,Qt.PenStyle.DashLine));p.drawLine(QLineF(x,y0,x,y1))
        cy=y1+15+(i%2)*17;p.setBrush(QColor('#222831'));p.setPen(QColor('#8ab6df'));p.drawEllipse(QRectF(x-9,cy-9,18,18));p.drawText(QRectF(x-9,cy-9,18,18),Qt.AlignmentFlag.AlignCenter,str(i+1))
    p.setPen(QColor('#e1e7ee'));p.drawText(QRectF(x0-25,y0,22,24),Qt.AlignmentFlag.AlignCenter,'1');p.drawText(QRectF(x0-25,y1-22,22,24),Qt.AlignmentFlag.AlignCenter,'0')
    p.drawText(QRectF(x0-10,y1+4,20,20),Qt.AlignmentFlag.AlignCenter,'0');p.drawText(QRectF(x1-10,y1+4,20,20),Qt.AlignmentFlag.AlignCenter,'→' if analog else 'π')
    p.drawText(QRectF(x0,rect.bottom()-23,x1-x0,20),Qt.AlignmentFlag.AlignCenter,'Ω (rad/s) · esquema' if analog else 'ω (rad/muestra) · esquema')

def bands_image(kind,analog=False):
    image=QImage(860,270,QImage.Format.Format_ARGB32);p=QPainter(image);draw_bands(p,QRectF(0,0,860,270),kind,analog=analog);p.end();return image

class BandDiagram(QWidget):
    def __init__(self):
        super().__init__();self.kind='lowpass';self.edges=None;self.analog=False;self.setMinimumHeight(200);self.setMinimumWidth(285)
    def paintEvent(self,event):
        p=QPainter(self);draw_bands(p,QRectF(self.rect()),self.kind,self.edges,self.analog);p.end()

class BandEdgesEditor(QWidget):
    textChanged=Signal(str)
    def __init__(self,analog=False):
        super().__init__();self.analog=analog;self.unit='rad/s' if analog else 'rad/muestra';self.loading=False;self.saved={key:list(values[2]) for key,values in KINDS.items()};self.current='lowpass'
        if analog:self.saved={key:(['100','200'] if len(values[1])==2 else ['50','100','200','300']) for key,values in KINDS.items()}
        box=QVBoxLayout(self);box.setContentsMargins(0,0,0,0);self.kind=QComboBox()
        for key,(title,_,_) in KINDS.items():self.kind.addItem(title,key)
        box.addWidget(QLabel('Tipo de filtro'));box.addWidget(self.kind)
        self.diagram=BandDiagram();self.diagram.analog=analog;box.addWidget(self.diagram);self.diagram.hide()
        self.diagram_toggle=QToolButton();self.diagram_toggle.setText('Esquema de bandas');self.diagram_toggle.setCheckable(True);self.diagram_toggle.setToolTip('Mostrar los bordes en colores. F1 abre la explicación completa.');self.diagram_toggle.toggled.connect(self.diagram.setVisible);box.insertWidget(2,self.diagram_toggle)
        help=QLabel('Bordes de menor a mayor · '+self.unit);help.setObjectName('muted');help.setWordWrap(True);box.addWidget(help)
        self.form=QFormLayout();self.form.setProperty("stackFields",True);self.form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows);box.addLayout(self.form);self.edits=[];self.labels=[];self.hints=[]
        for i in range(4):
            label=QLabel();label.setWordWrap(True);container=QWidget();column=QVBoxLayout(container);column.setContentsMargins(0,0,0,0)
            edit=QLineEdit();edit.setPlaceholderText('Un valor, por ejemplo pi/4');hint=QLabel();hint.setWordWrap(True);hint.setObjectName('muted');column.addWidget(edit);column.addWidget(hint);hint.hide()
            self.form.addRow(label,container);self.edits.append(edit);self.labels.append(label);self.hints.append(hint);edit.textChanged.connect(self.changed)
        self.status=QLabel();self.status.setWordWrap(True);box.addWidget(self.status)
        self.kind.currentIndexChanged.connect(self.change_kind);self.change_kind()
    def text(self):return json.dumps([self.kind.currentData(),[edit.text() for edit in self.edits[:len(KINDS[self.kind.currentData()][1])]]])
    def change_kind(self,*_):
        self.loading=True;self.current=self.kind.currentData();_,labels,_=KINDS[self.current]
        for i,edit in enumerate(self.edits):
            self.form.setRowVisible(i,i<len(labels))
            if i<len(labels):
                self.labels[i].setText(f'{i+1}. '+labels[i]+' ('+self.unit+')');
                passing={'lowpass':[True,False],'highpass':[False,True],'bandpass':[False,True,True,False],'bandstop':[True,False,False,True]}[self.current][i]
                self.labels[i].setStyleSheet('color:'+('#79c4ad' if passing else '#dfb374')+';');self.hints[i].setText(EXPLAIN[self.current][i]);edit.setToolTip(EXPLAIN[self.current][i]);edit.setText(self.saved[self.current][i])
        self.loading=False;self.changed()
    def frequencies(self):
        result=[];labels=KINDS[self.current][1]
        for i,edit in enumerate(self.edits[:len(labels)]):
            text=edit.text().strip()
            if re.fullmatch(r'[+-]?\d+,\d+',text):text=text.replace(',','.')
            try:value=complex(real_field(edit))
            except Exception as exc:raise ValueError(f'Frecuencia {i+1}: ingresá un solo número o expresión, por ejemplo 0.8 o pi/4. No ingreses listas.') from exc
            if value.imag or not np.isfinite(value) or value.real<=0 or (not self.analog and value.real>=np.pi):raise ValueError(f'Frecuencia {i+1}: debe ser positiva y finita en rad/s.' if self.analog else f'Frecuencia {i+1}: debe estar entre 0 y pi, sin incluir los extremos.')
            result.append(value.real)
        if any(a>=b for a,b in zip(result,result[1:])):raise ValueError('Las frecuencias deben aumentar de izquierda a derecha: 1 < 2'+(' < 3 < 4' if len(result)==4 else '')+'. Dejá un ancho de transición mayor que cero.')
        return result
    def bands(self):
        f=self.frequencies()
        if self.current=='lowpass':return [f[0]],[f[1]]
        if self.current=='highpass':return [f[1]],[f[0]]
        if self.current=='bandpass':return [f[1],f[2]],[f[0],f[3]]
        return [f[0],f[3]],[f[1],f[2]]
    def changed(self,*_):
        if self.loading:return
        self.saved[self.current]=[edit.text() for edit in self.edits[:len(KINDS[self.current][1])]];self.diagram.kind=self.current
        try:
            f=self.frequencies();self.diagram.edges=[v/(f[-1]*1.25 if self.analog else np.pi) for v in f];self.status.setText('Transición especificada: '+f'{f[1]-f[0]:.6g} {self.unit}'+(f' (izquierda) y {f[3]-f[2]:.6g} {self.unit} (derecha).' if len(f)==4 else '.'))
        except ValueError as exc:self.diagram.edges=None;self.status.setText(str(exc)+' El dibujo muestra un ejemplo hasta que corrijas los datos.')
        self.diagram.update();self.textChanged.emit(self.text())
