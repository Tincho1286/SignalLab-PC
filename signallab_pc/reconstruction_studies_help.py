"""Colored finite-kernel reconstruction guide."""
import math
from PySide6.QtCore import QRectF,QPointF,QLineF,Qt
from PySide6.QtGui import QImage,QPainter,QColor,QPen,QFont,QPolygonF


def image():
    canvas=QImage(1040,650,QImage.Format.Format_ARGB32);canvas.fill(QColor('#172131'));p=QPainter(canvas);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    ink='#e1e7ee';muted='#a6b2c1';blue='#91b7ff';green='#78d6c2';amber='#edc27d'
    def text(x,y,w,h,value,color=ink,size=14):
        p.setPen(QColor(color));p.setFont(QFont('Segoe UI',size));p.drawText(QRectF(x,y,w,h),Qt.TextFlag.TextWordWrap,value)
    def line(x,y,xx,yy,color=muted,width=2):p.setPen(QPen(QColor(color),width));p.drawLine(QLineF(x,y,xx,yy))
    text(25,16,990,42,'Reconstrucción: mismos nudos, distintos modelos',ink,20)
    text(30,75,560,34,'ZOH, lineal y SINC sobre [0, 1, 0]',ink,16)
    def xy(t,y):return QPointF(115+t*140,275-y*125)
    line(45,275,530,275);line(115,115,115,315)
    curves=[(blue,lambda t:1. if 1<=t<2 else 0.),(green,lambda t:max(0.,1-abs(t-1))),(amber,lambda t:1. if t==1 else math.sin(math.pi*(t-1))/(math.pi*(t-1)))]
    for color,f in curves:
        p.setPen(QPen(QColor(color),2));p.drawPolyline(QPolygonF([xy(-.5+3*k/300,f(-.5+3*k/300)) for k in range(301)]))
    for k,y in enumerate((0,1,0)):
        point=xy(k,y);p.setBrush(QColor(ink));p.setPen(QPen(QColor(ink),2));p.drawEllipse(point,4,4);text(point.x()-5,300,50,24,str(k),muted,12)
    text(35,345,530,48,'Azul: retención. Verde: triángulos. Ámbar: SINC.',muted,13)
    text(600,78,410,34,'Reloj y ventana',green,17)
    text(610,128,390,110,'tₖ = t₀ + k/Fs\nEl índice n original puede comenzar en cualquier entero. t₀ es el tiempo de la primera muestra.',ink,15)
    text(610,260,390,127,'Ampliar agrega períodos a la vista, sin nuevas muestras. ZOH retiene la última un período; lineal vuelve a cero y SINC conserva colas infinitas.',ink,14)
    line(25,414,1010,414,muted,1)
    text(30,435,490,34,'Aportes en t = 0.5, con Fs = 1',amber,17)
    text(40,485,470,135,'ZOH: [1, 0, 0] → 0\nLineal: [1/2, 1/2, 0] → 1/2\nSINC: [2/π, 2/π, −2/(3π)] → 2/π\nCada peso multiplica su muestra.',ink,14)
    text(550,435,460,34,'Referencia y error',blue,17)
    text(560,485,450,135,'Error = reconstrucción − referencia.\nRMS y SNR usan puntos de la misma rejilla. No son una integral continua.\nCoincidir en los nudos no demuestra ausencia de aliasing.',ink,14)
    p.end();return canvas
