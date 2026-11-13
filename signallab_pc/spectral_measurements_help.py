"""A compact diagram separates a spectral weight, a band and its cumulative fraction."""
import math
from PySide6.QtCore import QRectF,Qt,QLineF
from PySide6.QtGui import QImage,QPainter,QColor,QFont,QPen,QPainterPath
from .theme_tokens import COLORS as C


def image():
    picture=QImage(960,340,QImage.Format.Format_ARGB32);picture.fill(QColor(C['report']));p=QPainter(picture);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    def text(x,y,w,h,value,color='text',size=12):
        p.setPen(QColor(C[color]));p.setFont(QFont('Segoe UI',size));p.drawText(QRectF(x,y,w,h),Qt.TextFlag.TextWordWrap,value)
    text(20,10,920,35,'Medir una banda no es transformar otra vez el espectro',size=16)
    for left in (45,540):
        p.setPen(QPen(QColor(C['muted']),1));p.drawLine(QLineF(left,230,left+360,230));p.drawLine(QLineF(left,230,left,70))
    shade=QColor(C['amber']);shade.setAlpha(45);p.fillRect(QRectF(135,75,180,155),shade)
    path=QPainterPath();path.moveTo(45,230);path.lineTo(225,85);path.lineTo(405,230);p.setPen(QPen(QColor(C['blue']),3));p.drawPath(path)
    for x,name in ((135,'desde'),(315,'hasta')):
        p.setPen(QPen(QColor(C['amber']),1,Qt.PenStyle.DashLine));p.drawLine(QLineF(x,75,x,235));text(x-25,239,85,30,name,'amber',11)
    text(65,45,330,35,'Peso o densidad de entrada','blue');text(205,67,150,25,'pico medido','blue',10)
    path=QPainterPath()
    for index in range(61):
        x=index/30;y=.5*x*x if x<=1 else 1-.5*(2-x)**2;point=(540+180*x,230-145*y)
        if index:path.lineTo(*point)
        else:path.moveTo(*point)
    p.setPen(QPen(QColor(C['green']),3));p.drawPath(path);text(555,45,360,35,'Fracción acumulada (0 a 1)','green');text(907,73,30,25,'1','green',11)
    text(35,282,420,48,'La medida suma bins o integra la densidad dentro de los extremos indicados.','muted',11)
    text(540,282,380,48,'El centro y el ancho describen ese peso. La acumulada no conserva la fase.','muted',11)
    p.end();return picture
