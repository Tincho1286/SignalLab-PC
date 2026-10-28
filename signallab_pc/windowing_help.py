"""Illustrated index alignment and finite impulse windowing."""
from PySide6.QtCore import QPointF,QRectF,Qt
from PySide6.QtGui import QImage,QPainter,QColor,QPen,QFont
from .theme_tokens import COLORS as C

def windowing_help_image(sum_mode=False):
    image=QImage(960,400,QImage.Format.Format_ARGB32_Premultiplied);image.fill(QColor(C['report']));p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    def text(x,y,w,h,value,color,size=14):
        p.setFont(QFont('Segoe UI',size));p.setPen(QColor(color));p.drawText(QRectF(x,y,w,h),Qt.AlignmentFlag.AlignCenter|Qt.TextFlag.TextWordWrap,value)
    def line(x,y,a,b,color,width=2):p.setPen(QPen(QColor(color),width));p.drawLine(QPointF(x,y),QPointF(a,b))
    blue=C['accent'];amber='#dfb374';green='#79c4ad';ink=C['text'];gray=C['muted']
    for left,title,values,color in [(20,'Señal x[n]' if sum_mode else 'Señal / h[n]',[.2,.8,1,.8,.2],blue),(345,'Señal v[n]' if sum_mode else 'Ventana w[n]',[0,.5,1,.5,0],amber),(665,'Suma' if sum_mode else 'Producto',[.2,1.3,2,1.3,.2] if sum_mode else [0,.4,1,.4,0],green)]:
        text(left,15,270,50,title,color,17);line(left+15,245,left+265,245,gray)
        for j,value in enumerate(values):
            x=left+40+45*j;y=245-(65 if sum_mode else 130)*value;line(x,245,x,y,color,3);p.setPen(QColor(color));p.setBrush(QColor(color));p.drawEllipse(QPointF(x,y),5,5);text(x-20,260,40,30,str(j-2),ink,12)
    text(295,120,45,70,'+' if sum_mode else '×',ink,25);text(615,120,45,70,'=',ink,25)
    text(35,320,440,60,'Mismo índice n → sumar sus valores' if sum_mode else 'Mismo índice n → multiplicar sus valores',ink)
    text(505,320,420,60,'La salida abarca los dos registros; fuera de cada entrada se usa cero.' if sum_mode else 'Retardo opcional D=2: del registro −2…2 al registro 0…4',green)
    p.end();return image
