"""Explain observed training, held-out validation and future prediction in color."""
import math
from PySide6.QtCore import QRectF,QLineF,Qt
from PySide6.QtGui import QImage,QPainter,QColor,QPen,QFont
from .theme_tokens import COLORS as C


def image():
    image=QImage(960,395,QImage.Format.Format_ARGB32);image.fill(QColor(C['report']));p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    def text(x,y,w,h,value,color='text',size=12):
        p.setPen(QColor(C[color]));p.setFont(QFont('Segoe UI',size));p.drawText(QRectF(x,y,w,h),Qt.TextFlag.TextWordWrap,value)
    text(24,12,920,37,'Ajustar, validar y pronosticar son tres pasos distintos',size=17)
    for left,width,color in ((40,425,'blue'),(465,220,'amber'),(685,235,'green')):
        shade=QColor(C[color]);shade.setAlpha(25);p.fillRect(QRectF(left,75,width,150),shade)
        p.setPen(QPen(QColor(C[color]),2));p.drawLine(QLineF(left,174,left+width,174))
    for i in range(39):
        x=50+22*i;color='blue' if x<465 else 'amber' if x<685 else 'green';y=174-42*(math.sin(i*.7)+.25*math.cos(i*1.7))
        p.setPen(QPen(QColor(C[color]),2));p.drawLine(QLineF(x,174,x,y));p.setBrush(QColor(C[color]));p.drawEllipse(QRectF(x-3,y-3,6,6))
    for x in (465,685):p.setPen(QPen(QColor(C['muted']),1,Qt.PenStyle.DashLine));p.drawLine(QLineF(x,66,x,235))
    text(55,77,385,30,'Entrenamiento observado','blue');text(480,77,195,30,'Reserva observada','amber');text(705,77,200,30,'Futuro sin observar','green')
    text(45,245,395,83,'Se estiman coeficientes y constante. Para comparar órdenes se conservan las mismas filas de respuesta.','blue')
    text(480,245,190,113,'No se utiliza para ajustar. Cada predicción de un paso usa el pasado observado.','amber')
    text(705,245,210,113,'El pronóstico reutiliza sus propias salidas. El intervalo supone un modelo de innovaciones.','green')
    text(28,363,910,28,'Los residuos y sus pruebas son diagnósticos: no demuestran independencia ni el orden verdadero.','muted',11)
    p.end();return image
