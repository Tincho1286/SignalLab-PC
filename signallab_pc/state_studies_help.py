"""Coordinate invariance, constant equilibria and response components."""
import numpy as np
from PySide6.QtCore import QRectF,QPointF,Qt
from PySide6.QtGui import QImage,QPainter,QColor,QFont,QPen,QPolygonF
from .theme_tokens import COLORS as C


def image():
    image=QImage(1040,620,QImage.Format.Format_ARGB32_Premultiplied);image.fill(QColor(C['report']));p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    def text(x,y,w,h,s,color='text',size=12):
        p.setFont(QFont('Segoe UI',size));p.setPen(QColor(C[color]));p.drawText(QRectF(x,y,w,h),Qt.TextFlag.TextWordWrap,s)
    def line(a,b,c,d,color='rule'):
        p.setPen(QPen(QColor(C[color]),1.3));p.drawLine(QPointF(a,b),QPointF(c,d))
    text(24,12,990,38,'Un mismo modelo: coordenadas, equilibrio y evolución',size=19)
    text(28,66,475,30,'1. Cambiar la descripción','blue',16);text(542,66,475,30,'2. Buscar un equilibrio','green',16)
    text(28,112,475,150,'Ejemplo: dx/dt = −x + u,  y = x.\nCon x = 2q: dq/dt = −q + u/2,  y = 2q.\nx₀ = 2 corresponde a q₀ = 1.\nLa entrada y la salida físicas son las mismas.',size=12)
    text(542,112,475,150,'Con uₑ = 1:  0 = −xₑ + 1.\nEntonces xₑ = 1 e yₑ = 1.\nEn discreto se exige x[n+1] = x[n].\nTener equilibrio no demuestra estabilidad.',size=12)
    line(24,269,1016,269);text(28,290,980,32,'3. Total = estado cero + entrada cero','purple',16)
    left,top,width,height=64,350,570,190
    line(left,top+height,left+width,top+height,'muted');line(left,top,left,top+height,'muted')
    t=np.linspace(0,4,150);natural=2*np.exp(-t);forced=1-np.exp(-t)
    for values,color in [(natural+forced,'blue'),(forced,'green'),(natural,'amber')]:
        p.setPen(QPen(QColor(C[color]),2));p.drawPolyline(QPolygonF([QPointF(left+x/4*width,top+height-v/2.1*height) for x,v in zip(t,values)]))
    text(43,542,35,24,'0','muted',10);text(600,542,70,24,'t (s)','muted',10)
    text(680,350,330,35,'Azul: respuesta total','blue',12);text(680,395,330,35,'Verde: respuesta con x₀ = 0','green',12);text(680,440,330,55,'Ámbar: memoria inicial, con u = 0','amber',12)
    text(28,576,985,30,'Paso a paso utiliza los estados y entradas guardados; en continuo explica Ad y Bd de ZOH, no una derivada aproximada.',size=11)
    p.end();return image
