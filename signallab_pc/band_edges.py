"""Frequency bands and their exact, ordered inputs."""
import json
import math
from PySide6.QtCore import QEvent, Qt,Signal,QRectF,QLineF
from PySide6.QtGui import QPainter,QColor,QPen,QFont,QImage
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QComboBox,QLineEdit,QLabel,QScrollArea
from .choice_buttons import ChoiceButtons
from .numeric_input import real_field
from .theme_tokens import COLORS as C
from .validation import FieldError, invalid, passive_fields

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
EDGE_NAMES={'lowpass':['Fin del paso','Inicio del rechazo'],'highpass':['Fin del rechazo','Inicio del paso'],'bandpass':['Fin del rechazo inferior','Inicio del paso','Fin del paso','Inicio del rechazo superior'],'bandstop':['Fin del paso inferior','Inicio del rechazo','Fin del rechazo','Inicio del paso superior']}
REGIONS={'lowpass':('pass','transition','stop'),'highpass':('stop','transition','pass'),
         'bandpass':('stop','transition','pass','transition','stop'),'bandstop':('pass','transition','stop','transition','pass')}
PASS_EDGES={'lowpass':(0,), 'highpass':(1,), 'bandpass':(1,2), 'bandstop':(0,3)}

def draw_bands(p,rect,kind,edges=None,analog=False,*,active=-1,pending=False):
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QColor(C['rule']));p.setBrush(QColor(C['input']));p.drawRoundedRect(rect.adjusted(.5,.5,-.5,-.5),9,9)
    x0=rect.left()+14;x1=rect.right()-14;y0=rect.top()+34;y1=rect.bottom()-66
    values=edges if edges is not None else ([.3,.4] if kind in ('lowpass','highpass') else [.2,.3,.6,.7])
    positions=[x0]+[x0+v*(x1-x0) for v in values]+[x1]
    colors={'pass':C['green'],'stop':C['amber'],'transition':C['muted']}
    p.setFont(QFont('Segoe UI',9));font=p.fontMetrics()
    legend=[('Paso','pass'),('Transición','transition'),('Rechazo','stop')]
    width=sum(font.horizontalAdvance(label)+14 for label,_ in legend)
    gap=max(4,min(15,(x1-x0-width)/2))
    x=max(x0,rect.center().x()-(width+2*gap)/2)
    for label,mode in legend:
        p.fillRect(QRectF(x,rect.top()+14,8,8),QColor(colors[mode]))
        p.setPen(QColor(C['text']));p.drawText(QRectF(x+13,rect.top()+6,font.horizontalAdvance(label)+1,24),Qt.AlignmentFlag.AlignVCenter,label)
        x+=font.horizontalAdvance(label)+14+gap
    for i,mode in enumerate(REGIONS[kind]):
        color=QColor(colors[mode]);color.setAlpha(30 if pending else 56)
        p.fillRect(QRectF(positions[i],y0,positions[i+1]-positions[i],y1-y0),color)
        edge=y0+3 if mode=='pass' else y1-3
        if mode!='transition':
            p.setPen(QPen(QColor(colors[mode]),2));p.drawLine(QLineF(positions[i],edge,positions[i+1],edge))
    p.setPen(QPen(QColor(C['border']),1));p.drawLine(QLineF(x0,y1,x1,y1))
    markers=[]
    previous=x0-12
    for i,x in enumerate(positions[1:-1]):
        # Let the marker use its own horizontal space while its leader stays on the exact edge.
        center=max(previous+20,min(x,x1-8-20*(len(values)-i-1)))
        previous=center
        cy=y1+25+(i%2)*15
        dot=QRectF(center-8,cy-8,16,16)
        role='accent' if i==active else 'green' if i in PASS_EDGES[kind] else 'amber'
        p.setPen(QPen(QColor(C[role]),1,Qt.PenStyle.DashLine if pending else Qt.PenStyle.SolidLine))
        p.drawLine(QLineF(x,y0,x,y1+4));p.drawLine(QLineF(x,y1+4,center,cy-8))
        p.setBrush(QColor(C['selected'] if i==active else C['panel']));p.drawEllipse(dot)
        p.setPen(QColor(C['text']));p.drawText(dot,Qt.AlignmentFlag.AlignCenter,str(i+1));markers.append(dot)
    p.setPen(QColor(C['muted']));p.drawText(QRectF(x0-5,y1+2,20,16),Qt.AlignmentFlag.AlignLeft,'0')
    p.drawText(QRectF(x1-12,y1+2,16,16),Qt.AlignmentFlag.AlignRight,'→' if analog else 'π')
    p.drawText(QRectF(x0,rect.bottom()-21,x1-x0,18),Qt.AlignmentFlag.AlignCenter,'Ω (rad/s)' if analog else 'ω (rad/muestra)')
    return markers

def bands_image(kind,analog=False):
    image=QImage(490,155,QImage.Format.Format_ARGB32);image.fill(QColor(C['report']));p=QPainter(image);draw_bands(p,QRectF(0,0,490,155),kind,analog=analog);p.end();return image

class BandDiagram(QWidget):
    edgeSelected=Signal(int)

    def __init__(self):
        super().__init__();self.kind='lowpass';self.edges=None;self.analog=False;self.active=-1;self.markers=[]
        self.setFixedHeight(134)
        self.setMinimumWidth(220)
        self.setAccessibleName('Bandas de paso, transición y rechazo')
        self.setToolTip('Seleccioná un número para editar ese borde.')

    def paintEvent(self,event):
        p=QPainter(self);self.markers=draw_bands(p,QRectF(self.rect()),self.kind,self.edges,self.analog,active=self.active,pending=self.edges is None);p.end()

    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:
            for index,marker in enumerate(self.markers):
                if marker.contains(event.position()):
                    self.edgeSelected.emit(index)
                    event.accept()
                    return
        super().mousePressEvent(event)

class BandEdgesEditor(QWidget):
    textChanged=Signal(str)
    def __init__(self,analog=False):
        super().__init__();self.setObjectName('bandEdgesEditor');self.analog=analog;self.unit='rad/s' if analog else 'rad/muestra';self.loading=False;self.saved={key:list(values[2]) for key,values in KINDS.items()};self.current='lowpass'
        if analog:self.saved={key:(['100','200'] if len(values[1])==2 else ['50','100','200','300']) for key,values in KINDS.items()}
        box=QVBoxLayout(self);box.setContentsMargins(0,0,0,0);self.kind=QComboBox()
        for key,(title,_,_) in KINDS.items():self.kind.addItem(title,key)
        box.addWidget(QLabel('Tipo de filtro'));box.addWidget(ChoiceButtons(self.kind))
        self.diagram=BandDiagram();self.diagram.analog=analog;box.addWidget(self.diagram)
        self.diagram.edgeSelected.connect(self.focus_edge)
        self.order_note=QLabel('Bordes crecientes en '+self.unit+'. '+('Usá valores positivos.' if analog else 'Usá valores entre 0 y π.'));self.order_note.setObjectName('muted');self.order_note.setWordWrap(True);box.addWidget(self.order_note)
        self.edits=[];self.labels=[];self.badges=[];self.rows=[]
        for i in range(4):
            container=QWidget();row=QHBoxLayout(container);row.setContentsMargins(0,0,0,0);row.setSpacing(7)
            badge=QLabel(str(i+1));badge.setObjectName('bandEdgeBadge');badge.setFixedSize(21,21);badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label=QLabel();label.setWordWrap(True)
            edit=QLineEdit();edit.setPlaceholderText('Ω' if analog else 'ω');edit.setMaximumWidth(116);edit.installEventFilter(self)
            row.addWidget(badge);row.addWidget(label,1);row.addWidget(edit)
            box.addWidget(container);self.rows.append(container);self.edits.append(edit);self.labels.append(label);self.badges.append(badge)
            edit.textChanged.connect(self.changed)
        self.status=QLabel();self.status.setObjectName('bandStatus');self.status.setWordWrap(True);box.addWidget(self.status)
        self.kind.currentIndexChanged.connect(self.change_kind);self.change_kind()

    def focus_edge(self,index):
        edit=self.edits[index]
        parent=self.parentWidget()
        area=None
        while parent is not None:
            if isinstance(parent,QScrollArea) and area is None:area=parent
            if parent.objectName()=='toolWorkspace':
                parent.show_inputs()
                break
            parent=parent.parentWidget()
        if area is not None:area.ensureWidgetVisible(edit,8,12)
        edit.setFocus(Qt.FocusReason.MouseFocusReason)
        edit.selectAll()

    def place_diagram(self, destination=None):
        if destination is None:
            self.layout().insertWidget(2,self.diagram)
        else:
            destination.addWidget(self.diagram)
        self.diagram.show()

    def eventFilter(self,watched,event):
        if event.type() in (QEvent.Type.FocusIn,QEvent.Type.FocusOut):
            self.diagram.active=self.edits.index(watched) if event.type()==QEvent.Type.FocusIn else -1
            self.diagram.update()
        return super().eventFilter(watched,event)
    def text(self):return json.dumps([self.kind.currentData(),[edit.text() for edit in self.edits[:len(KINDS[self.kind.currentData()][1])]]])
    def change_kind(self,*_):
        self.loading=True;self.current=self.kind.currentData();_,labels,_=KINDS[self.current]
        for i,edit in enumerate(self.edits):
            self.rows[i].setVisible(i<len(labels))
            if i<len(labels):
                name=EDGE_NAMES[self.current][i]
                self.labels[i].setText(name);edit.setAccessibleName(f'{i+1}. {name} ({self.unit})')
                badge=self.badges[i];badge.setProperty('bandRole','pass' if i in PASS_EDGES[self.current] else 'stop')
                badge.style().unpolish(badge);badge.style().polish(badge)
                edit.setText(self.saved[self.current][i]);edit.setToolTip(EXPLAIN[self.current][i]+' Podés usar pi y fracciones.')
        self.loading=False;self.changed()
    def frequencies(self):
        result=[];labels=KINDS[self.current][1]
        for i,edit in enumerate(self.edits[:len(labels)]):
            value=real_field(edit,minimum=0,strict=True)
            if not self.analog and value>=math.pi:
                invalid(edit,'debe ser menor que π.')
            if result and value<=result[-1]:
                invalid(edit,f'debe ser mayor que el borde {i}.')
            result.append(value)
        return result
    def bands(self):
        f=self.frequencies()
        if self.current=='lowpass':return [f[0]],[f[1]]
        if self.current=='highpass':return [f[1]],[f[0]]
        if self.current=='bandpass':return [f[1],f[2]],[f[0],f[3]]
        return [f[0],f[3]],[f[1],f[2]]
    @passive_fields()
    def changed(self,*_):
        if self.loading:return
        self.saved[self.current]=[edit.text() for edit in self.edits[:len(KINDS[self.current][1])]];self.diagram.kind=self.current
        try:
            f=self.frequencies();self.diagram.edges=[v/(f[-1]*1.25 if self.analog else math.pi) for v in f]
            width=f'{f[1]-f[0]:.6g} {self.unit}'
            self.status.setText(f'Transición de {width}' if len(f)==2 else f'Transición izquierda de {width}\nTransición derecha de {f[3]-f[2]:.6g} {self.unit}')
        except FieldError as exc:
            self.diagram.edges=None
            self.status.setText(str(exc).split(' Detalle:',1)[0]+' Esquema de referencia.')
        self.diagram.update();self.textChanged.emit(self.text())
