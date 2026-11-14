"""Illustrated meanings of levels, limits and observed delay ranges."""
import numpy as np
from PySide6.QtCore import QRectF,QPointF,Qt
from PySide6.QtGui import QImage,QPainter,QPen,QColor,QFont,QPolygonF
from .theme_tokens import COLORS as C


def image():
    image=QImage(1040,600,QImage.Format.Format_ARGB32_Premultiplied);image.fill(QColor(C['report']));p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    def text(x,y,w,h,value,color='text',size=12):
        p.setPen(QColor(C[color]));p.setFont(QFont('Segoe UI',size));p.drawText(QRectF(x,y,w,h),Qt.TextFlag.TextWordWrap,value)
    def line(x0,y0,x1,y1,color='muted',dashed=False):
        p.setPen(QPen(QColor(C[color]),1.5,Qt.PenStyle.DashLine if dashed else Qt.PenStyle.SolidLine));p.drawLine(QPointF(x0,y0),QPointF(x1,y1))
    text(24,12,992,38,'Medir la definición del último sistema analizado',size=19)
    text(28,61,460,32,'1. Cruce de un nivel','blue',16);text(544,61,465,32,'2. Límites de una banda','green',16)
    for left in (64,576):
        line(left,285,left+392,285);line(left,118,left,285);text(left-25,286,40,25,'0','muted',10);text(left+282,311,115,24,'Frecuencia','muted',10)
    w=np.linspace(0,3,200);m=1/np.sqrt(1+w*w)
    p.setPen(QPen(QColor(C['blue']),2));p.drawPolyline(QPolygonF([QPointF(64+x/3*392,285-y*150) for x,y in zip(w,m)]))
    y=285-150/np.sqrt(2);x=64+392/3;line(64,y,456,y,'amber',True);line(x,y,x,285,'green',True)
    text(78,111,310,30,'|H| = 1 / √(1 + Ω²)','blue',12);text(220,y+9,225,45,'1/√2: −3.0103 dB','amber',12);text(x-2,288,45,24,'1','green',11)
    line(576,285-150*.9,968,285-150*.9,'amber',True);line(576,285-150*1.05,968,285-150*1.05,'amber',True)
    p.setPen(QPen(QColor(C['green']),2));p.drawPolyline(QPolygonF([QPointF(576+x/.5*392,285-y*150) for x,y in zip(w[w<=.5],m[w<=.5])]))
    text(585,180,345,46,'Mínimo permitido 0.9\nMáximo permitido 1.05','amber',12);text(888,288,75,24,'0.5','green',11)
    text(28,339,460,95,'El nivel relativo compara con |H| en una frecuencia elegida. Un cruce se refina evaluando la definición. Un salto que no alcanza el nivel no se inventa como cruce.',size=12)
    text(544,339,465,95,'Cada banda tiene sus límites. El margen compara el peor valor medido con ellos: positivo deja holgura; negativo indica un exceso. Las transiciones pueden quedar fuera.',size=12)
    line(24,452,1016,452,'rule');text(28,474,970,33,'3. Retardo por banda: τg = −dφ/dω','purple',16)
    text(28,521,970,63,'Se informa mínimo, máximo, mediana y variación de los puntos válidos. En discreto son muestras; en continuo, segundos. En un cero, polo o salto no se asigna un retardo ordinario.',size=12)
    p.end();return image
