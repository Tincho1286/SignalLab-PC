"""Colored finite-window illustration with inclusive integer support."""
from PySide6.QtGui import QImage,QPainter,QColor,QPen,QFont
from PySide6.QtCore import QRectF,QLineF,Qt
from scipy.signal import get_window


def window_signal_image():
    image=QImage(1000,520,QImage.Format.Format_ARGB32);image.fill(QColor('#172131'))
    p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    ink='#e1e7ee';muted='#a6b2c1';blue='#91b7ff';green='#78d6c2';amber='#edc27d'
    def text(x,y,w,h,s,color=ink,size=14):
        p.setPen(QColor(color));p.setFont(QFont('Segoe UI',size));p.drawText(QRectF(x,y,w,h),Qt.TextFlag.TextWordWrap,s)
    def line(x,y,xx,yy,color=muted,width=1):p.setPen(QPen(QColor(color),width));p.drawLine(QLineF(x,y,xx,yy))
    text(28,18,940,40,'Longitud L = cantidad total de muestras',ink,20)
    text(35,76,280,35,'Rectangular',blue);text(350,76,280,35,'Hann',green);text(665,76,280,35,'Hamming',amber)
    x0,step,baseline=85,51,310
    line(65,baseline,945,baseline);line(65,130,65,baseline)
    text(22,121,35,30,'1',muted,12);text(22,294,35,30,'0',muted,12)
    for window,color in [('boxcar',blue),('hamming',amber),('hann',green)]:
        values=get_window(window,17,fftbins=False)
        for k,value in enumerate(values):
            x=x0+step*k;y=baseline-160*value;line(x,baseline,x,y,color)
            p.setBrush(QColor(color));p.setPen(QPen(QColor(color),1));p.drawEllipse(QRectF(x-3,y-3,6,6))
    for k in range(17):
        x=x0+step*k;line(x,baseline,x,baseline+5);text(x-13,baseline+10,42,25,str(k-8),muted,11)
    line(x0,365,x0+step*16,365,green,3)
    text(210,376,680,40,'17 muestras: n = −8, −7, …, 7, 8',green,17)
    text(35,435,930,66,'Índice inicial n₀=−8; último índice n₀+L−1=8. Fuera de ese intervalo la ventana vale cero.\nCambiar n₀ desplaza la ventana; no cambia su forma ni el módulo de su DTFT.',ink,13)
    p.end();return image
