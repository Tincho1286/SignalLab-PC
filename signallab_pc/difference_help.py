"""Explain coefficient order and prehistory on the integer axis."""
from PySide6.QtGui import QImage,QPainter,QColor,QPen,QFont
from PySide6.QtCore import QRectF,QLineF,Qt


def difference_image():
    image=QImage(1000,480,QImage.Format.Format_ARGB32);image.fill(QColor('#172131'))
    p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    blue='#91b7ff';green='#78d6c2';amber='#edc27d';ink='#e1e7ee';muted='#a6b2c1'
    def text(x,y,w,h,s,color=ink,size=14):
        p.setPen(QColor(color));p.setFont(QFont('Segoe UI',size));p.drawText(QRectF(x,y,w,h),Qt.TextFlag.TextWordWrap,s)
    def line(x,y,xx,yy,color,width=2):p.setPen(QPen(QColor(color),width));p.drawLine(QLineF(x,y,xx,yy))
    text(28,18,940,40,'Ecuación en diferencias: los coeficientes acompañan retardos',ink,20)
    text(35,80,930,40,'a = [1, −0.5]     →     y[n] − 0.5·y[n−1] = f[n]',blue,19)
    text(35,133,930,40,'Al despejar: y[n] = 0.5·y[n−1] + f[n]',green,19)
    line(85,275,935,275,muted)
    for index,value in [(-2,.5),(-1,1),(0,1.5),(1,1.75),(2,1.875),(3,1.9375)]:
        x=120+(index+2)*150;y=275-value*45;color=amber if index<0 else green
        line(x,275,x,y,color,3);p.setBrush(QColor(color));p.drawEllipse(QRectF(x-4,y-4,8,8));text(x-30,286,95,30,str(index),color)
    line(345,200,345,318,blue,2)
    text(35,341,440,85,'Ámbar: valores anteriores conocidos.\nCon n₀=0 y orden 1 se carga y[−1].\nNo es y[0]: y[0] se calcula.',amber)
    text(535,341,430,85,'Verde: solución desde n₀=0.\nEl ejemplo usa y[−1]=1 y f[n]=1.\nMás muestras no cambian la fórmula.',green)
    text(35,445,930,27,'Para orden p, el historial se carga y[n₀−1], y[n₀−2], …, y[n₀−p].',muted,12)
    p.end();return image
