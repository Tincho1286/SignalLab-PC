"""Colored illustrations of stochastic models and record correlation."""
from PySide6.QtGui import QImage,QPainter,QColor,QPen,QFont
from PySide6.QtCore import QRectF,QLineF,Qt
import numpy as np


def model_image(cross=False,fit=False):
    image=QImage(1000,520,QImage.Format.Format_ARGB32);image.fill(QColor('#172131'))
    p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    blue='#91b7ff';green='#78d6c2';amber='#edc27d';ink='#e1e7ee';muted='#a6b2c1'
    def text(x,y,w,h,s,color=ink,size=14):
        p.setPen(QColor(color));p.setFont(QFont('Segoe UI',size));p.drawText(QRectF(x,y,w,h),Qt.TextFlag.TextWordWrap,s)
    def line(x,y,xx,yy,color=muted,width=2):p.setPen(QPen(QColor(color),width));p.drawLine(QLineF(x,y,xx,yy))
    def box(x,y,w,h,s,color):
        p.setPen(QPen(QColor(color),2));p.setBrush(QColor('#202e41'));p.drawRoundedRect(QRectF(x,y,w,h),10,10);text(x+16,y+12,w-32,h-22,s,color)
    def stem(x,y,w,values,color):
        line(x,y,x+w,y,muted,1)
        for i,v in enumerate(values):
            xx=x+w*i/(len(values)-1);yy=y-30*v
            line(xx,y,xx,yy,color,2);p.setBrush(QColor(color));p.drawEllipse(QRectF(xx-3,yy-3,6,6))
    if cross:
        text(28,18,945,43,'Dos registros: primero se alinean sus índices',ink,20)
        text(30,80,160,35,'x[n] · azul',blue);stem(205,122,680,[.3,1,-.4,.8,-1,.2,1,.1,-.5],blue)
        text(30,167,160,35,'y[n] · verde',green);stem(290,207,595,[1,-.4,.8,-1,.2,1,.1,-.5],green)
        line(290,245,885,245,amber,4);text(300,255,600,50,'Ámbar: intervalo realmente observado en ambos.',amber)
        box(30,325,440,130,'Rxy[k] = promedio de x[n+k]·conj(y[n])\nAl restar medias: covarianza cruzada.',blue)
        box(510,325,460,130,'Con k>0 se compara una muestra posterior de x con una de y.\nLos extremos usan menos pares.',green)
    else:
        text(28,18,945,43,'Estimar un modelo desde un registro' if fit else 'Ruido blanco → modelo → proceso correlacionado',ink,20)
        box(30,86,265,125,'Registro x[n]\nOrden AR p\nMedia estimada' if fit else 'Ruido e[n]\nMedia μe\nVarianza σe²',blue)
        box(365,86,270,125,'Yule–Walker\nCovarianza con divisor N\nResolver a[1]…a[p]' if fit else 'H(z) = B(z⁻¹)/A(z⁻¹)\nAR: b=[1]\nMA: a=[1]',amber)
        box(705,86,265,125,'Modelo AR(p)\nVarianza de innovación\nResiduo en tramo válido' if fit else 'Proceso x[n]\nMedia y covarianza\nDensidad de potencia',green)
        for x in (300,640):line(x,146,x+60,146,ink);line(x+49,138,x+60,146,ink);line(x+49,154,x+60,146,ink)
        stem(40,300,360,[.2,-.7,1,.1,-.6,.8,-1,.2,.4,-.5,.9],blue)
        stem(590,300,360,[.2,.0,.4,.5,.2,.6,.3,.2,.7,.5,.6],green)
        text(30,345,450,125,'Coeficientes a=[1, −0.8] y b=[1]:\nx[n] = 0.8·x[n−1] + e[n].\nEl signo de a[1] cambia en la recurrencia.',blue)
        text(520,345,450,125,'Con σe²=1 y μe=0:\nVarianza teórica = 1/(1−0.8²).\nCovarianza: Cx[k] = 0.8^|k|/(1−0.8²).',green)
    text(30,479,940,27,'Ilustración conceptual: los resultados de tu cálculo usan los datos cargados.',muted,11)
    p.end();return image
