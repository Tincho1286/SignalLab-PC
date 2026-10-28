"""Color explanation of the missing delay/gain information."""
import numpy as np
from PySide6.QtCore import Qt,QRectF,QPointF,QLineF
from PySide6.QtGui import QImage,QPainter,QColor,QPen,QFont,QPainterPath
from .theme_tokens import COLORS as C

def reconstruction_help_image():
    image=QImage(1050,440,QImage.Format.Format_ARGB32);image.fill(QColor(C['report']));p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    def text(x,y,width,height,value,color='text',size=14):
        p.setPen(QColor(C[color]));p.setFont(QFont('Segoe UI',size));p.drawText(QRectF(x,y,width,height),Qt.TextFlag.TextWordWrap,value)
    text(28,10,994,46,'Un módulo puede corresponder a fases diferentes',size=19)
    text(28,63,470,40,'Mismo módulo: H y H con tres retardos','blue',15)
    text(565,63,455,40,'La fase sí cambia al agregar retardos','amber',15)
    w=np.linspace(0,np.pi,301);base=1/(1-.5*np.exp(-1j*w));phase=np.unwrap(np.angle(base))
    def axes(left):
        p.setPen(QPen(QColor(C['muted']),1));p.drawLine(QLineF(left,290,left+445,290));p.drawLine(QLineF(left,115,left,290));text(left+405,296,45,30,'π','muted',12);text(left-5,296,45,30,'0','muted',12)
    axes(40);axes(570)
    def curve(left,values,low,high,color):
        path=QPainterPath()
        for index,(x,value) in enumerate(zip(w,values)):
            point=QPointF(left+445*x/np.pi,290-175*(value-low)/(high-low))
            if index:path.lineTo(point)
            else:path.moveTo(point)
        p.setPen(QPen(QColor(C[color]),3));p.drawPath(path)
    curve(40,abs(base),0,2.2,'blue');curve(570,phase,-10,.8,'blue');curve(570,phase-3*w,-10,.8,'amber')
    text(32,331,476,89,'Azul: modelo de fase mínima. El módulo no informa los tres retardos ni otros factores paso todo.','blue',14)
    text(563,331,459,89,'Ámbar: mismo módulo, fase con −3ω adicional. A la inversa, conocer sólo la fase tampoco fija la ganancia.','amber',14)
    p.end();return image
