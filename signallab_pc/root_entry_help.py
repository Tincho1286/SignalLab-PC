"""Exact-entry coordinates, list and conjugate illustrated on one root pair."""
from PySide6.QtGui import QImage,QPainter,QColor,QPen,QFont
from PySide6.QtCore import QRectF,QLineF,Qt
import math


def root_entry_image():
    image=QImage(1000,550,QImage.Format.Format_ARGB32);image.fill(QColor('#172131'))
    p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    blue='#91b7ff';green='#78d6c2';amber='#edc27d';ink='#e1e7ee';muted='#a6b2c1'
    def text(x,y,w,h,s,color=ink,size=14):
        p.setPen(QColor(color));p.setFont(QFont('Segoe UI',size));p.drawText(QRectF(x,y,w,h),Qt.TextFlag.TextWordWrap,s)
    def line(x,y,xx,yy,color=muted,width=2):p.setPen(QPen(QColor(color),width));p.drawLine(QLineF(x,y,xx,yy))
    def box(x,y,w,h,label,color):
        p.setPen(QPen(QColor(color),2));p.setBrush(QColor('#202e41'));p.drawRoundedRect(QRectF(x,y,w,h),10,10);text(x+16,y+12,w-32,h-20,label,color)
    text(28,18,945,42,'Una raíz, dos formas de cargar su posición',ink,20)
    box(30,86,420,110,'Binómica · a + bi\nParte real a = 0.5\nParte imaginaria b = 0.5',blue)
    box(30,216,420,110,'Polar · r · exp(iθ)\nMódulo r = sqrt(2)/2\nÁngulo θ = pi/4 rad',amber)
    cx,cy,scale=740,230,125
    p.setBrush(Qt.BrushStyle.NoBrush);p.setPen(QPen(QColor(muted),1,Qt.PenStyle.DashLine));p.drawEllipse(QRectF(cx-scale,cy-scale,2*scale,2*scale))
    line(cx-160,cy,cx+165,cy);line(cx,cy-165,cx,cy+160)
    text(cx+133,cy+5,85,30,'Real',muted,12);text(cx+8,cy-177,110,30,'Imaginaria',muted,12)
    x=cx+scale*.5;y=cy-scale*.5;line(cx,cy,x,y,amber,3);line(x,cy,x,y,blue,1);line(cx,y,x,y,blue,1)
    for yy,color in [(y,blue),(cy+scale*.5,green)]:line(x-7,yy-7,x+7,yy+7,color,3);line(x-7,yy+7,x+7,yy-7,color,3)
    text(x+15,y-30,155,55,'0.5 + 0.5i',blue);text(x+15,cy+45,165,55,'0.5 − 0.5i',green)
    text(cx+18,cy-48,70,30,'θ',amber,17);text(cx+14,cy-94,65,30,'r',amber,17)
    box(30,355,420,115,'Agregar a la lista\nPolo ×     0.5 + 0.5i\nPolo ×     0.5 − 0.5i',green)
    text(515,403,445,75,'Verde: conjugado opcional.\nLa lista conserva raíces repetidas.\nCada raíz real se agrega una sola vez.',green)
    text(30,501,940,34,'Agregar actualiza lista y plano. Calcular obtiene H y su respuesta. Los ejes del plano se eligen aparte.',muted,12)
    p.end();return image
