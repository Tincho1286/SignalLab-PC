"""Illustration of Bode coordinates and loop crossover definitions."""
import math
import numpy as np
from PySide6.QtCore import Qt,QRectF,QPointF,QLineF
from PySide6.QtGui import QImage,QPainter,QPen,QColor,QFont,QPolygonF
from .theme_tokens import COLORS as C


def bode_help_image():
    image=QImage(960,520,QImage.Format.Format_ARGB32);image.fill(QColor(C['report']))
    p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    def text(x,y,w,h,value,color='text',size=12):
        p.setPen(QColor(C[color]));p.setFont(QFont('Segoe UI',size));p.drawText(QRectF(x,y,w,h),Qt.TextFlag.TextWordWrap,value)
    def line(x0,y0,x1,y1,color='muted',style=Qt.PenStyle.SolidLine,width=1):
        p.setPen(QPen(QColor(C[color]),width,style));p.drawLine(QLineF(x0,y0,x1,y1))
    def xpos(w):return 65+(math.log10(w)+1)*290
    def mag_y(value):return 225-(value+60)*155/85
    def phase_y(value):return 445-(value+1.5*np.pi)*140/(1.05*np.pi)
    text(60,8,830,38,'Módulo y fase del mismo lazo abierto L',size=18)
    text(65,43,570,24,'Módulo (dB) · 20 log₁₀ |L|','muted',11)
    text(65,275,570,24,'Fase (rad)','muted',11)
    w=np.geomspace(.1,10,301);s=1j*w;h=2/(s*(s+1)*(s+2));db=20*np.log10(abs(h));phase=np.unwrap(np.angle(h))
    for yfun,values,top,bottom in [(mag_y,db,70,225),(phase_y,phase,305,445)]:
        for value in (.1,1,10):line(xpos(value),top,xpos(value),bottom,'rule')
        line(65,bottom,645,bottom,'disabled');line(65,top,65,bottom,'disabled')
        p.save();p.setClipRect(QRectF(65,top,580,bottom-top));p.setPen(QPen(QColor(C['blue']),2));p.drawPolyline(QPolygonF([QPointF(xpos(x),yfun(y)) for x,y in zip(w,values)]));p.restore()
    line(65,mag_y(0),645,mag_y(0),'muted',Qt.PenStyle.DashLine)
    text(13,mag_y(0)-12,48,25,'0 dB','muted',10)
    line(65,phase_y(-np.pi),645,phase_y(-np.pi),'amber',Qt.PenStyle.DashLine)
    text(20,phase_y(-np.pi)-12,42,25,'−π','amber',11)
    root=next(v.real for v in np.roots([1,5,4,-4]) if abs(v.imag)<1e-12 and v.real>0)
    wg=math.sqrt(root);wp=math.sqrt(2)
    for frequency,color,label in [(wg,'green','Ωg'),(wp,'amber','Ωp')]:
        x=xpos(frequency)
        for top,bottom in [(70,225),(305,445)]:line(x,top,x,bottom,color,Qt.PenStyle.DotLine)
        text(x-14,233,45,25,label,color,12)
    for x,y0,y1,color in [(xpos(wp),mag_y(20*math.log10(1/3)),mag_y(0),'amber'),
            (xpos(wg),phase_y(float(np.angle(2/(1j*wg*(1j*wg+1)*(1j*wg+2))))),phase_y(-np.pi),'green')]:
        line(x,y0,x,y1,color,width=3)
        for y in (y0,y1):line(x-5,y,x+5,y,color,width=2)
    for value,label in [(.1,'0.1'),(1,'1'),(10,'10')]:text(xpos(value)-15,451,60,22,label,'muted',10)
    text(245,480,380,28,'Frecuencia angular Ω (rad/s)','muted',12)
    text(700,60,225,26,'Cruce de ganancia','green',14)
    text(700,94,225,78,'|L| = 1 equivale a 0 dB. En esa frecuencia se lee el margen de fase MF.','text',12)
    text(700,185,225,50,'MF: distancia angular hasta una fase impar·π.','green',12)
    text(700,275,225,26,'Cruce de fase','amber',14)
    text(700,309,225,80,'L está en el eje real negativo. En esa frecuencia se lee el margen de ganancia MG.','text',12)
    text(700,404,225,62,'MG = 1 / |L|\nMG en dB = −20 log₁₀ |L|','amber',12)
    p.end();return image
