"""Compare Fourier models and their forward/inverse inputs in existing help."""
import math
from PySide6.QtCore import Qt,QRectF,QPointF
from PySide6.QtGui import QImage,QPainter,QColor,QPen,QFont,QPainterPath
from .theme_tokens import COLORS as C


def fourier_choice_image():
    image=QImage(960,420,QImage.Format.Format_ARGB32_Premultiplied);image.fill(QColor(C['report']))
    p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    def text(x,y,w,h,value,color='text',size=11):
        p.setPen(QColor(C[color]));p.setFont(QFont('Segoe UI',size))
        p.drawText(QRectF(x,y,w,h),Qt.AlignmentFlag.AlignCenter|Qt.TextFlag.TextWordWrap,value)
    def line(x1,y1,x2,y2,color='muted',width=1):
        p.setPen(QPen(QColor(C[color]),width));p.drawLine(QPointF(x1,y1),QPointF(x2,y2))
    text(20,10,920,35,'Elegir la transformada depende del modelo de la señal',size=17)
    for index,(title,source,output,unit,discrete,color) in enumerate([
        ('DFT / FFT','Registro x[n]: N muestras','X[k]: N coeficientes','k = 0, …, N−1',True,'blue'),
        ('DTFT','Secuencia x[n]','X(ω): curva periódica','Período 2π rad/muestra',False,'green'),
        ('Fourier continua','Señal x(t)','X(jΩ): curva continua','Ω en rad/s',False,'purple'),
    ]):
        left=20+index*315
        p.setPen(QPen(QColor(C['border']),1));p.setBrush(Qt.BrushStyle.NoBrush);p.drawRoundedRect(QRectF(left,58,300,275),10,10)
        text(left+10,69,280,32,title,color,15);text(left+12,106,276,29,source,size=12)
        line(left+118,145,left+118,190,color,2);line(left+118,190,left+112,182,color,2);line(left+118,190,left+124,182,color,2)
        text(left+15,150,91,28,'Directa',color,10)
        line(left+182,190,left+182,145,'muted',1);line(left+182,145,left+176,153,'muted',1);line(left+182,145,left+188,153,'muted',1)
        text(left+194,150,96,28,'Inversa','muted',10)
        text(left+10,203,280,28,output,color,12)
        line(left+35,287,left+265,287)
        if discrete:
            for n in range(9):
                x=left+45+n*26;y=287-43*(.2+abs(math.cos(n*.7)))
                line(x,287,x,y,color,2);p.setBrush(QColor(C[color]));p.drawEllipse(QPointF(x,y),2.5,2.5)
        else:
            path=QPainterPath()
            for n in range(101):
                u=n/100;x=left+35+230*u
                y=287-47*(.55+.4*math.cos(4*math.pi*u)) if index==1 else 287-52*math.exp(-((u-.5)/.23)**2)
                if n:path.lineTo(x,y)
                else:path.moveTo(x,y)
            p.setBrush(Qt.BrushStyle.NoBrush);p.setPen(QPen(QColor(C[color]),2));p.drawPath(path)
        text(left+10,293,280,30,unit,'muted',10)
    text(25,345,910,54,'FFT es un algoritmo para calcular la DFT. Agregar ceros densifica sus puntos; no alarga la observación ni mejora por sí solo la resolución.',size=12)
    p.end();return image
