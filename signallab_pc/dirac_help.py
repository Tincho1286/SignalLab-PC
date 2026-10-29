"""Show a continuous impulse as position and area, separately from samples."""
import math
from PySide6.QtCore import Qt,QRectF,QPointF
from PySide6.QtGui import QImage,QPainter,QColor,QPen,QFont,QPainterPath
from .theme_tokens import COLORS as C


def dirac_help_image():
    image=QImage(960,370,QImage.Format.Format_ARGB32_Premultiplied);image.fill(QColor(C['report']))
    p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    def text(x,y,w,h,value,color='text',size=12):
        p.setPen(QColor(C[color]));p.setFont(QFont('Segoe UI',size))
        p.drawText(QRectF(x,y,w,h),Qt.AlignmentFlag.AlignCenter|Qt.TextFlag.TextWordWrap,value)
    def line(x1,y1,x2,y2,color='muted',width=1):
        p.setPen(QPen(QColor(C[color]),width));p.drawLine(QPointF(x1,y1),QPointF(x2,y2))
    text(20,8,920,38,'Una señal continua puede tener muestras ordinarias e impulsos ideales',size=16)
    text(25,49,910,35,'x(t) = cos(2πt) + 2δ(t − 0.35)',size=16)
    text(35,92,400,30,'Parte ordinaria: cos(2πt)','blue',13)
    text(525,92,400,30,'Impulso: posición 0.35 s, peso 2','green',13)
    for left in (70,560):
        line(left,225,left+330,225);line(left,140,left,285)
        for fraction,label in ((0,'0'),(.5,'0.5'),(1,'1 s')):
            x=left+fraction*330;line(x,221,x,229);text(x-20,287,50,25,label,'muted',10)
    path=QPainterPath()
    for index in range(201):
        t=index/200;x=70+330*t;y=225-65*math.cos(2*math.pi*t)
        if index:path.lineTo(x,y)
        else:path.moveTo(x,y)
    p.setBrush(Qt.BrushStyle.NoBrush);p.setPen(QPen(QColor(C['blue']),2));p.drawPath(path)
    p.setBrush(QColor(C['blue']))
    for index in range(11):
        t=index/10;p.drawEllipse(QPointF(70+330*t,225-65*math.cos(2*math.pi*t)),3,3)
    x=560+330*.35
    line(x,225,x,157,'green',3);line(x,157,x-8,170,'green',3);line(x,157,x+8,170,'green',3)
    line(x,230,x,281,'purple',1);text(x+16,151,180,42,'Peso = 2\nNo es altura finita','green',11)
    text(x-42,249,84,27,'0.35 s','purple',11)
    text(25,321,910,40,'La posición 0.35 s queda entre dos puntos. Cambiar el paso de la rejilla no cambia el peso del impulso.',size=12)
    p.end();return image
