"""Scrollable vector block diagrams, at a readable scale rather than fit-to-height."""
import html,math
from PySide6.QtCore import Qt,QRectF,QPointF,QSize,QByteArray,QBuffer,QIODevice,QSaveFile
from PySide6.QtGui import QBrush,QColor,QPen,QPainter,QPolygonF,QImage
from PySide6.QtWidgets import (QGraphicsScene,QGraphicsView,QDialog,QVBoxLayout,QToolBar,
    QFileDialog,QMessageBox)
from .theme_tokens import COLORS as C
from .resources import ensure_working_set


def diagram_scene(value,parent=None):
    from .result_summary import number
    ensure_working_set(max(1,value.states+len(value.stages)),bytes_per_sample=24000,live_arrays=4)
    scene=QGraphicsScene(parent);scene.setBackgroundBrush(QBrush(QColor(C['report'])))
    def text(x,y,w,h,content,color='text',size=12,center=True):
        item=scene.addText('');item.setTextWidth(w)
        item.setHtml('<div style="font-family:Segoe UI;font-size:'+str(size)+'pt;color:'+C[color]+';text-align:'+('center' if center else 'left')+'">'+content+'</div>')
        bounds=item.boundingRect();item.setPos(x-w/2,y-bounds.height()/2);return item
    def wire(x0,y0,x1,y1,color='muted',arrow=True):
        scene.addLine(x0,y0,x1,y1,QPen(QColor(C[color]),1.6))
        if arrow:
            theta=math.atan2(y1-y0,x1-x0);length=9
            points=[QPointF(x1,y1),QPointF(x1-length*math.cos(theta-.42),y1-length*math.sin(theta-.42)),QPointF(x1-length*math.cos(theta+.42),y1-length*math.sin(theta+.42))]
            scene.addPolygon(QPolygonF(points),QPen(QColor(C[color])),QBrush(QColor(C[color])))
    def dot(x,y):scene.addEllipse(x-3,y-3,6,6,QPen(QColor(C['green'])),QBrush(QColor(C['green'])))
    def summer(x,y):
        scene.addEllipse(x-15,y-15,30,30,QPen(QColor(C['muted']),1.5),QBrush(QColor(C['panel'])))
        text(x,y,29,29,'+',size=15)
    def block(x,y,w,content,color):
        scene.addRect(x-w/2,y-25,w,50,QPen(QColor(C[color]),1.5),QBrush(QColor(C['panel'])))
        text(x,y,w-6,46,content,color,size=11)
    top=50
    for section,stage in enumerate(value.stages,1):
        n=stage.order;title=('Sección '+str(section)+' de '+str(len(value.stages))+' · ' if value.cascade else '')+('Forma directa II · retardos' if value.domain=='digital' else 'Cadena de integradores')
        text(440,top,870,32,html.escape(title),size=16)
        y0=top+88
        if value.cascade:
            text(440,top+34,850,30,'Entrada: '+('u' if section==1 else 'salida de sección '+str(section-1))+' · Salida: '+('y' if section==len(value.stages) else 'entrada de sección '+str(section+1)),color='muted',size=10)
        if not n:
            wire(90,y0,355,y0,'green');block(440,y0,170,'b[0] = '+html.escape(number(stage.b[0])),'blue');wire(525,y0,810,y0,'blue')
            text(55,y0,70,28,'u');text(850,y0,70,28,'y');top=y0+95;continue
        text(48,y0-26,85,30,'u[n]' if value.domain=='digital' else 'u(t)',size=11)
        wire(20,y0,115,y0,'green');summer(130,y0);wire(145,y0,440,y0,'green');dot(440,y0)
        text(385,y0-26,100,28,'v[n]' if value.domain=='digital' else 'v(t)',color='green',size=11)
        wire(440,y0,510,y0,'blue');block(595,y0,170,'b[0] = '+html.escape(number(stage.b[0])),'blue');wire(680,y0,735,y0,'blue');summer(750,y0);wire(765,y0,870,y0,'blue')
        text(840,y0-26,95,28,'y[n]' if value.domain=='digital' else 'y(t)',size=11)
        for k in range(1,n+1):
            y=y0+k*130;previous=y-130
            wire(440,previous,440,previous+40,'green');block(440,previous+65,90,'z<sup>−1</sup>' if value.domain=='digital' else '1 / s','green');wire(440,previous+90,440,y,'green');dot(440,y)
            text(455,y+19,130,28,'q['+str(k)+']',color='green',size=11)
            wire(440,y,370,y,'amber');block(285,y,170,'−a['+str(k)+'] = '+html.escape(number(-stage.a[k])),'amber');wire(200,y,145 if k<n else 130,y,'amber')
            wire(440,y,510,y,'blue');block(595,y,170,'b['+str(k)+'] = '+html.escape(number(stage.b[k])),'blue');wire(680,y,735 if k<n else 750,y,'blue')
            if k<n:summer(130,y);summer(750,y)
            wire(130,y-(15 if k<n else 0),130,previous+15,'amber');wire(750,y-(15 if k<n else 0),750,previous+15,'blue')
        bottom=y0+n*130
        text(130,bottom+43,200,40,'Realimentación · Σ(−a[k]·q[k])',color='amber',size=10)
        text(740,bottom+43,250,40,'Salida · Σ(b[k]·q[k])',color='blue',size=10)
        top=bottom+140
    scene.setSceneRect(QRectF(0,0,900,max(260,top)));return scene


def scene_image(scene):
    rect=scene.sceneRect();width,height=math.ceil(rect.width()),math.ceil(rect.height())
    ensure_working_set(width*height,bytes_per_sample=4,live_arrays=3)
    image=QImage(width,height,QImage.Format.Format_ARGB32);image.fill(QColor(C['report']))
    painter=QPainter(image);painter.setRenderHint(QPainter.RenderHint.Antialiasing);scene.render(painter);painter.end();return image


class DiagramView(QGraphicsView):
    def wheelEvent(self,event):
        if event.modifiers()&Qt.KeyboardModifier.ControlModifier:
            factor=1.15 if event.angleDelta().y()>0 else 1/1.15
            if .25<=self.transform().m11()*factor<=4:self.scale(factor,factor)
            event.accept();return
        super().wheelEvent(event)


class RealizationWindow(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent,Qt.WindowType.Window);self.setWindowTitle('Realización · SignalLab');self.setWindowIcon(parent.window().windowIcon())
        available=parent.screen().availableGeometry();self.resize(min(1000,available.width()-32),min(700,available.height()-48));self.setMinimumSize(360,280);root=QVBoxLayout(self);toolbar=QToolBar();root.addWidget(toolbar)
        self.view=DiagramView();self.view.setRenderHint(QPainter.RenderHint.Antialiasing);self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag);self.view.setAlignment(Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignHCenter);root.addWidget(self.view,1)
        toolbar.addAction('−',lambda:self.zoom(1/1.15));toolbar.addAction('+',lambda:self.zoom(1.15));toolbar.addAction('100 %',lambda:self.view.resetTransform());toolbar.addAction('Ajustar ancho',self.fit_width);toolbar.addSeparator();toolbar.addAction('Exportar…',self.export)
        self.view.setToolTip('Arrastrá para recorrer el diagrama. Ctrl+rueda cambia el zoom. Ajustar ancho conserva el desplazamiento vertical.')
    def closeEvent(self,event):self.hide();event.ignore()
    def zoom(self,factor):
        if .25<=self.view.transform().m11()*factor<=4:self.view.scale(factor,factor)
    def set_realization(self,value):
        scene=diagram_scene(value,self);previous=self.view.scene();self.view.setScene(scene)
        if previous is not None:previous.deleteLater()
        self.view.resetTransform();self.view.verticalScrollBar().setValue(0);self.view.horizontalScrollBar().setValue(0)
    def fit_width(self):
        if self.view.scene() is None:return
        scale=max(.25,min(2,(self.view.viewport().width()-24)/self.view.scene().sceneRect().width()));self.view.resetTransform();self.view.scale(scale,scale)
    def export(self):
        scene=self.view.scene()
        if scene is None:return
        path,selected=QFileDialog.getSaveFileName(self,'Exportar diagrama completo','realizacion','Diagrama vectorial SVG (*.svg);;Imagen PNG (*.png)')
        if not path:return
        from pathlib import Path
        if not Path(path).suffix:path+='.svg' if 'SVG' in selected else '.png'
        try:
            data=QByteArray();buffer=QBuffer(data);buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            if Path(path).suffix.lower()=='.svg':
                from PySide6.QtSvg import QSvgGenerator
                generator=QSvgGenerator();generator.setOutputDevice(buffer);rect=scene.sceneRect();generator.setSize(QSize(math.ceil(rect.width()),math.ceil(rect.height())));generator.setViewBox(rect);generator.setTitle('Realización · SignalLab')
                painter=QPainter(generator);painter.setRenderHint(QPainter.RenderHint.Antialiasing);scene.render(painter);painter.end()
            else:
                if not scene_image(scene).save(buffer,'PNG'):raise OSError('No se pudo generar la imagen.')
            buffer.close();output=QSaveFile(path)
            if not output.open(QIODevice.OpenModeFlag.WriteOnly) or output.write(data)!=len(data) or not output.commit():raise OSError('No se pudo guardar el diagrama completo.')
        except Exception as exc:QMessageBox.warning(self,'No se pudo exportar',str(exc))


def realization_help_image():
    from .filters import Transfer
    from .realization import realize_system
    return scene_image(diagram_scene(realize_system(Transfer([.25,.5,.25],[1,-.4,.1]))))
