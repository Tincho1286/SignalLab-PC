"""Color illustration for sign, exponent and stored fraction."""
from fractions import Fraction
from PySide6.QtCore import Qt,QRectF
from PySide6.QtGui import QImage,QPainter,QColor,QPen,QFont
from .precision import Encoding
from .theme_tokens import COLORS as C

def precision_help_image():
    encoded=Encoding('float16').encode(Fraction(7,10));word=encoded['word']
    image=QImage(960,340,QImage.Format.Format_ARGB32);image.fill(QColor(C['report']));p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    def text(x,y,w,h,value,color='text',size=14):
        p.setPen(QColor(C[color]));p.setFont(QFont('Segoe UI',size));p.drawText(QRectF(x,y,w,h),Qt.TextFlag.TextWordWrap,value)
    text(30,12,900,44,'Un mismo número, una palabra de almacenamiento',size=19)
    text(30,65,900,35,'Ejemplo: 0.7 en IEEE 754 binary16',color='muted',size=15)
    for x,width,label,bits,color in [(35,100,'Signo',word[:1],'amber'),(155,270,'Exponente',word[1:6],'blue'),(445,470,'Fracción',word[6:],'green')]:
        text(x,110,width,32,label,color,14);p.setPen(QPen(QColor(C[color]),2));p.drawRect(QRectF(x,149,width,55));text(x+8,158,width-16,40,bits,color,21)
    text(35,225,400,72,'1 bit de signo + 5 de exponente + 10 de fracción = 16 bits.','muted',14)
    text(470,225,445,78,'Valor almacenado: 0.7001953125. La diferencia con 0.7 es el error de conversión.','text',14)
    p.end();return image
