"""Colored diagrams explain finite windows and FFT block bookkeeping."""
from PySide6.QtCore import QRectF,Qt,QLineF
from PySide6.QtGui import QImage,QPainter,QColor,QFont,QPen
from .theme_tokens import COLORS as C


def image(kind):
    image=QImage(960,340,QImage.Format.Format_ARGB32);image.fill(QColor(C['report']));p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    def text(x,y,w,h,value,color='text',size=12):
        p.setPen(QColor(C[color]));p.setFont(QFont('Segoe UI',size));p.drawText(QRectF(x,y,w,h),Qt.TextFlag.TextWordWrap,value)
    def band(x,y,w,h,color):p.fillRect(QRectF(x,y,w,h),QColor(C[color]))
    if kind=='stft':
        text(20,12,900,35,'Una ventana selecciona un tramo; la FFT describe ese tramo',size=16)
        p.setPen(QPen(QColor(C['muted']),1));p.drawLine(QLineF(40,175,510,175))
        for index,value in enumerate([0,1,.5,-.3,-1,.2,.9,0,-.5,-.3,.8,1,.1,-1,-.8,0,.7,.8,0,-.4]):
            x=55+22*index;p.setPen(QPen(QColor(C['blue']),2));p.drawLine(QLineF(x,175,x,175-28*value))
        for row,start in enumerate((1,5,9)):
            p.setPen(QPen(QColor(C[('blue','purple','green')[row]]),3));p.drawRect(QRectF(55+22*start,65+row*29,22*8,23))
        text(42,220,480,70,'Los tramos se solapan. El salto es L−solapamiento. Los ceros en los extremos completan el registro observado.','muted')
        for y,title,color in [(65,'Amplitud: |FFT(x·w)| / Σw','blue'),(133,'Densidad: |FFT(x·w)|² / (2π·Fs·Σw²)','purple'),(211,'Inversa: IFFT, suma ponderada y división por Σw²','green')]:
            band(550,y,5,55,color);text(570,y,360,65,title,color)
        text(550,285,370,45,'Fs=1 si el eje usa rad/muestra.','muted')
    else:
        text(20,12,900,35,'El mismo resultado lineal, con dos formas de manejar el solapamiento',size=15)
        text(35,68,360,32,'OLA · solapamiento-suma','blue',14)
        band(40,114,250,32,'blue');band(290,114,100,32,'amber');band(190,164,250,32,'purple');band(440,164,100,32,'amber')
        text(40,211,490,70,'Las colas naranjas se suman en sus índices. La contribución de un bloque no es, por sí sola, la salida total.','muted')
        text(560,68,360,32,'OLS · solapamiento-almacenamiento','green',14)
        band(560,114,95,32,'amber');band(655,114,260,32,'green');text(560,155,95,50,'M−1 descartadas','amber',11);text(670,155,245,50,'L salidas nuevas','green',11)
        text(560,215,365,75,'La entrada incluye M−1 muestras de historia. Se descarta el comienzo de la salida circular, no la historia de entrada.','muted')
    p.end();return image
