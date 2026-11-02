"""Authored field diagrams; no application computations or screenshots."""
from PySide6.QtCore import QRectF,QLineF,Qt
from PySide6.QtGui import QImage,QPainter,QColor,QPen,QFont
import math
from .theme_tokens import COLORS as C


def amplitude_image():
    image=QImage(960,430,QImage.Format.Format_ARGB32);image.fill(QColor(C['report']));p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    def text(x,y,w,h,value,color='text',size=12):
        p.setFont(QFont('Segoe UI',size));p.setPen(QColor(C[color]));p.drawText(QRectF(x,y,w,h),Qt.TextFlag.TextWordWrap,value)
    def line(x,y,xx,yy,color='muted',style=Qt.PenStyle.SolidLine):p.setPen(QPen(QColor(C[color]),2,style));p.drawLine(QLineF(x,y,xx,yy))
    text(25,15,910,40,'Rechazabanda · dos amplitudes de paso independientes',size=19)
    base=305;scale=92;left=82;right=892
    for lo,hi,amplitude,color,label in [(left,290,1,'green','A inferior = 1'),(680,right,2,'blue','A superior = 2')]:
        y=base-scale*amplitude;p.fillRect(QRectF(lo,y-12,hi-lo,24),QColor(C['panel']))
        line(lo,y,hi,y,color);line(lo,y-12,hi,y-12,color,Qt.PenStyle.DashLine);line(lo,y+12,hi,y+12,color,Qt.PenStyle.DashLine)
        text(lo,y-54,hi-lo,32,label,color);text(lo,y+20,hi-lo,48,'A−δp ≤ |H| ≤ A+δp',color,10)
    line(365,base-10,605,base-10,'amber',Qt.PenStyle.DashLine);line(365,base,605,base,'purple');text(380,252,245,36,'Rechazo: |H| ≤ δs','amber')
    line(left,base,right,base);line(left,75,left,base)
    for x,label in [(290,'ωp₁'),(365,'ωs₁'),(605,'ωs₂'),(680,'ωp₂')]:
        line(x,base,x,base+8);text(x-24,base+15,70,30,label,'muted')
    text(25,357,910,60,'Línea continua: ideal. Líneas discontinuas: límites. El FIR combina ambos ideales antes de aplicar la ventana; una ganancia global no sustituye estas dos amplitudes.',size=12)
    p.end();return image


def z_plane_image():
    image=QImage(960,390,QImage.Format.Format_ARGB32);image.fill(QColor(C['report']));p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    def text(x,y,w,h,value,color='text',size=12):
        p.setFont(QFont('Segoe UI',size));p.setPen(QColor(C[color]));p.drawText(QRectF(x,y,w,h),Qt.TextFlag.TextWordWrap,value)
    text(25,15,900,38,'H(z) y H(eʲω) son representaciones distintas',size=19)
    cx,cy,r=220,206,110
    p.setPen(QPen(QColor(C['muted']),1));p.drawLine(QLineF(58,cy,382,cy));p.drawLine(QLineF(cx,65,cx,348))
    p.setBrush(Qt.BrushStyle.NoBrush);p.setPen(QPen(QColor(C['green']),2,Qt.PenStyle.DashLine));p.drawEllipse(QRectF(cx-r,cy-r,2*r,2*r))
    angle=.6;x=cx+r*math.cos(angle);y=cy-r*math.sin(angle);p.setPen(QPen(QColor(C['blue']),2));p.drawLine(QLineF(cx,cy,x,y));p.setBrush(QColor(C['blue']));p.drawEllipse(QRectF(x-4,y-4,8,8))
    text(270,110,145,50,'z = eʲω','green',12);text(244,191,80,35,'ω','blue',14);text(339,214,65,30,'Re(z)','muted',11);text(230,65,65,30,'Im(z)','muted',11)
    text(440,90,485,60,'Plano complejo: z = a + jb','blue',16)
    text(440,155,485,70,'El mapa de colores muestra |H(z)| en dos dimensiones. Polos y ceros pertenecen a ese plano.',size=12)
    text(440,241,485,100,'Respuesta en frecuencia: se recorre sólo el círculo |z|=1. H(eʲω) es la DTFT cuando ese círculo pertenece a la ROC. La ROC no se deduce sólo de la fórmula.',color='green',size=12)
    p.end();return image
