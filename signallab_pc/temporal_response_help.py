"""Colored reading guide for finite inputs, transients and initial memory."""
import math
from PySide6.QtCore import QRectF,QPointF,QLineF,Qt
from PySide6.QtGui import QImage,QPainter,QColor,QPen,QFont,QPolygonF


def image():
    canvas=QImage(1040,640,QImage.Format.Format_ARGB32);canvas.fill(QColor('#172131'));p=QPainter(canvas);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    ink='#e1e7ee';muted='#a6b2c1';blue='#91b7ff';green='#78d6c2';amber='#edc27d'
    def text(x,y,w,h,value,color=ink,size=14):
        p.setPen(QColor(color));p.setFont(QFont('Segoe UI',size));p.drawText(QRectF(x,y,w,h),Qt.TextFlag.TextWordWrap,value)
    def line(x,y,xx,yy,color=muted,width=2):p.setPen(QPen(QColor(color),width));p.drawLine(QLineF(x,y,xx,yy))
    text(25,16,990,40,'Respuesta temporal: ventana, referencia y memoria',ink,20)
    text(28,70,465,36,'1. Extender una entrada con ceros',blue,17)
    line(50,228,480,228)
    for index,value in enumerate((1,1,0,0,0)):
        x=75+index*90;y=228-value*70;color=blue if index<2 else amber
        line(x,228,x,y,color,3);p.setBrush(QColor(color));p.drawEllipse(QRectF(x-4,y-4,8,8));text(x-12,240,60,25,str(index),color,12)
    text(35,112,440,40,'Azul: datos cargados. Ámbar: puntos agregados.',muted,13)
    text(35,280,450,85,'Se conserva el origen y el paso. En continuo, el tramo hacia el primer cero usa la interpolación elegida: lineal o retención.',ink,14)
    text(540,70,470,36,'2. Medir un escalón desde reposo',green,17)
    def xy(t,y):return QPointF(560+t*68,237-y*100)
    p.fillRect(QRectF(560,135,408,4),QColor('#355f58'))
    line(552,237,982,237);line(560,246,560,126)
    p.setPen(QPen(QColor(green),3));p.drawPolyline(QPolygonF([xy(k*.05,1-math.exp(-k*.05)) for k in range(121)]))
    line(560,137,968,137,amber,1);text(777,108,225,27,'Valor final del modelo',amber,12)
    for value in (.1,.9):
        t=-math.log(1-value);point=xy(t,value);line(point.x(),237,point.x(),point.y(),blue,1);line(560,point.y(),point.x(),point.y(),blue,1)
    text(550,278,455,90,'La subida compara los cruces del 10 % y 90 %. La banda usa el valor final del modelo estable, no la última muestra.',ink,14)
    line(25,383,1010,383,muted,1)
    text(28,401,980,35,'3. Leer los aportes y comparar componentes',ink,18)
    text(40,457,280,80,'Entrada actual\nx[0] = 1',blue,18)
    text(336,457,335,80,'Memoria previa\n0.5 · y[−1] = 0.5',amber,18)
    text(729,457,285,80,'Salida calculada\ny[0] = 1.5',green,18)
    line(285,487,325,487,muted);line(667,487,707,487,muted)
    text(38,561,960,58,'Total = estado cero + entrada cero. El inspector usa los coeficientes y las muestras guardadas; comparar o navegar no vuelve a resolver el sistema.',muted,14)
    p.end();return canvas
