"""Frequency mapping in radians, with visible alias folding for impulse invariance."""
import math
from PySide6.QtCore import Qt,QRectF,QPointF
from PySide6.QtGui import QImage,QPainter,QPen,QColor,QFont,QPainterPath
from .theme_tokens import COLORS as C


def conversion_help_image():
    image=QImage(960,400,QImage.Format.Format_ARGB32_Premultiplied);image.fill(QColor(C['report']))
    p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    def text(x,y,w,h,value,color='text',size=12):
        p.setPen(QColor(C[color]));p.setFont(QFont('Segoe UI',size));p.drawText(QRectF(x,y,w,h),Qt.AlignmentFlag.AlignCenter|Qt.TextFlag.TextWordWrap,value)
    def line(a,b,color='muted',width=1):p.setPen(QPen(QColor(C[color]),width));p.drawLine(QPointF(*a),QPointF(*b))
    text(20,10,920,40,'Una frecuencia analógica y dos mapeos diferentes',size=17)
    xy=lambda x,y:(90+x/(2*math.pi)*760,270-y/math.pi*170)
    line((90,270),(870,270));line((90,270),(90,75))
    for tick,label in ((0,'0'),(math.pi,'π'),(2*math.pi,'2π')):
        x,y=xy(tick,0);line((x,y),(x,y+5));text(x-24,278,48,26,label,'muted',11)
    x,y=xy(0,math.pi);text(35,y-15,45,30,'π','muted',11);line((90,y),(850,y),'grid')
    for color,function in (('blue',lambda value:2*math.atan(value/2)),('green',lambda value:abs(math.remainder(value,2*math.pi)))):
        path=QPainterPath()
        for index in range(301):
            value=index*2*math.pi/300;point=QPointF(*xy(value,function(value)))
            if index:path.lineTo(point)
            else:path.moveTo(point)
        p.setBrush(Qt.BrushStyle.NoBrush);p.setPen(QPen(QColor(C[color]),3));p.drawPath(path)
    text(105,57,380,34,'Bilineal: ω = 2·atan(ΩT/2)','blue',13)
    text(495,57,415,34,'Invarianza: ΩT, plegado módulo 2π','green',13)
    text(55,48,40,30,'ω','muted',12);text(850,276,100,30,'Ω·T (rad)','muted',11)
    text(25,319,910,65,'Azul: deformación de frecuencia sin plegado. Verde: distintas frecuencias analógicas pueden coincidir. En invarianza, el aliasing puede mover el corte efectivo; por eso el informe distingue el corte mapeado del medido en H(z).',size=12)
    p.end();return image
