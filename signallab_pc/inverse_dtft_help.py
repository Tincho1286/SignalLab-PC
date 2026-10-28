"""Colored native illustration of one angular period and integer samples."""
import math
from PySide6.QtCore import QPointF,QRectF,Qt
from PySide6.QtGui import QImage,QPainter,QColor,QPen,QFont
from .theme_tokens import COLORS as C

def inverse_dtft_help_image():
    image=QImage(960,400,QImage.Format.Format_ARGB32_Premultiplied);image.fill(QColor(C['report']));p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    def text(x,y,w,h,value,color,size=14):
        p.setPen(QColor(color));p.setFont(QFont('Segoe UI',size));p.drawText(QRectF(x,y,w,h),Qt.AlignmentFlag.AlignCenter|Qt.TextFlag.TextWordWrap,value)
    def line(x,y,x2,y2,color,width=2):p.setPen(QPen(QColor(color),width));p.drawLine(QPointF(x,y),QPointF(x2,y2))
    blue=C['accent'];green='#79c4ad';amber='#dfb374';ink=C['text'];muted=C['muted']
    text(25,12,400,55,'Azul: un período de X(ω)',blue)
    line(45,250,420,250,muted);line(233,80,233,265,muted)
    p.fillRect(QRectF(175,125,116,125),QColor('#294456'));line(60,250,175,250,blue,3);line(175,250,175,125,blue,3);line(175,125,291,125,blue,3);line(291,125,291,250,blue,3);line(291,250,405,250,blue,3)
    for x,label in ((60,'−π'),(233,'0'),(405,'π')):line(x,245,x,255,ink);text(x-30,268,60,28,label,ink)
    text(55,313,365,65,'Inicio y paso: cubren 2π en rad/muestra',blue)
    text(430,142,100,60,'1 / 2π\n∫',amber,20)
    text(535,12,400,55,'Verde: muestras x[n]',green)
    line(545,250,925,250,muted)
    for n in range(-5,6):
        x=735+n*33;value=1/3 if n==0 else math.sin(math.pi*n/3)/(math.pi*n);y=250-250*value
        line(x,250,x,y,green,2);p.setPen(QPen(QColor(green),1));p.setBrush(QColor(green));p.drawEllipse(QPointF(x,y),4,4)
        if n in (-5,0,5):text(x-20,268,40,28,str(n),ink)
    text(545,313,380,65,'Primer índice y cantidad: eligen qué n enteros mostrar',green)
    p.end();return image
