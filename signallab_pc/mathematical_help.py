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
    image=QImage(1000,460,QImage.Format.Format_ARGB32);image.fill(QColor(C['report']));p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    def text(x,y,w,h,value,color='text',size=12):
        p.setFont(QFont('Segoe UI',size));p.setPen(QColor(C[color]));p.drawText(QRectF(x,y,w,h),Qt.TextFlag.TextWordWrap,value)
    def line(x,y,xx,yy,color='muted',dashed=False):
        p.setPen(QPen(QColor(C[color]),2,Qt.PenStyle.DashLine if dashed else Qt.PenStyle.SolidLine));p.drawLine(QLineF(x,y,xx,yy))
    text(25,15,950,36,'H(s), H(z) y respuesta en frecuencia',size=19)
    for cx,symbol,title in [(245,'s','Continuo · plano s'),(745,'z','Discreto · plano z')]:
        cy=203;text(cx-170,64,350,36,title,'blue',15)
        line(cx-155,cy,cx+155,cy);line(cx,105,cx,308)
        text(cx+104,cy+14,90,26,'Re('+symbol+')','muted',11);text(cx+10,108,95,26,'Im('+symbol+')','muted',11)
        if symbol=='s':
            line(cx,112,cx,302,'green',True);text(cx-145,264,135,30,'s = jΩ','green',13)
            line(cx-82,169,cx-70,181,'amber');line(cx-70,169,cx-82,181,'amber')
        else:
            p.setBrush(Qt.BrushStyle.NoBrush);p.setPen(QPen(QColor(C['green']),2,Qt.PenStyle.DashLine));p.drawEllipse(QRectF(cx-93,cy-93,186,186));text(cx-147,271,140,28,'z = eʲω','green',13)
            line(cx-48,cy-7,cx-36,cy+5,'amber');line(cx-36,cy-7,cx-48,cy+5,'amber')
    text(30,330,940,48,'Plano completo: dos mallas de Re(H) / Im(H), o de |H| / Arg(H). Cada punto horizontal tiene una parte real y otra imaginaria; la altura representa la componente elegida.',size=12)
    text(30,395,940,48,'Frecuencia: se recorre sólo la línea verde, con Ω en rad/s o ω en rad/muestra. La ROC debe contener ese eje o círculo para interpretar la curva como transformada de Fourier.','green',12)
    p.end();return image
