"""Illustrations of the conventions shared by the RF tools."""

import math

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPen


_INK='#e1e7ee'
_BLUE='#8ab6df'
_GREEN='#79c4ad'
_AMBER='#dfb374'
_GRID='#445260'


def diagram(task):
    image=QImage(960,360,QImage.Format.Format_ARGB32)
    image.fill(QColor('#1b2027'))
    p=QPainter(image)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    def text(x,y,w,h,body,color=_INK,size=15):
        p.setFont(QFont('Segoe UI',size))
        p.setPen(QColor(color))
        p.drawText(QRectF(x,y,w,h),Qt.TextFlag.TextWordWrap,body)

    def line(x,y,u,v,color=_GRID,width=2):
        p.setPen(QPen(QColor(color),width))
        p.drawLine(QLineF(x,y,u,v))

    def arrow(x,y,u,v,color):
        line(x,y,u,v,color,3)
        a=math.atan2(v-y,u-x)
        for side in (-.45,.45):
            line(u,v,u-13*math.cos(a+side),v-13*math.sin(a+side),color,3)

    def box(x,y,w,h,body,color):
        p.setPen(QPen(QColor(color),2))
        p.setBrush(QColor('#24303b'))
        p.drawRoundedRect(QRectF(x,y,w,h),10,10)
        text(x+15,y+16,w-25,h-15,body,color)

    def circle(x,y,r,color,width=1):
        p.setPen(QPen(QColor(color),width))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(x,y),r,r)

    if task=='network':
        title='Dirección de las ondas'
        note='La columna identifica el puerto excitado. S₂₁ mide la onda que sale por el puerto 2 al excitar el puerto 1.'
        text(64,20,820,44,'Ejemplo de una red de dos puertos',_INK,19)
        box(338,91,284,164,'Matriz S\nRelación b = S · a\n\nS₁₁     S₁₂\nS₂₁     S₂₂',_INK)
        for x,y,u,label,color in (
            (82,132,336,'a₁ · incidente',_BLUE),(336,209,82,'b₁ · saliente',_GREEN),
            (878,132,624,'a₂ · incidente',_BLUE),(624,209,878,'b₂ · saliente',_GREEN),
        ):
            arrow(x,y,u,y,color)
            text(min(u,x)+7,y-38,236,32,label,color)
        text(70,283,310,45,'Puerto 1 · referencia R₁',_AMBER)
        text(628,283,305,45,'Puerto 2 · referencia R₂',_AMBER)
    elif task=='line':
        title='Ubicar una impedancia en Smith'
        note='Los puntos usan la referencia de entrada. Al cambiar la frecuencia se forma una trayectoria de Γ.'
        x,y,r=231,184,136
        circle(x,y,r,_BLUE,2)
        line(x-r,y,x+r,y)
        line(x,y-r,x,y+r)
        for resistance in (.2,.5,1,2,5):
            circle(x+r*resistance/(1+resistance),y,r/(1+resistance),_GRID)
        for fraction,title_at in ((-1,'Corto'),(0,'Adaptación'),(1/3,'2 R'),(1,'Abierto')):
            point=x+r*fraction
            circle(point,y,5,_GREEN,3)
            text(point-29,y-41 if fraction==1/3 else y+17,113,36,title_at,_GREEN,11)
        text(423,66,493,57,'Cada punto es un Γ complejo',_BLUE,18)
        text(423,146,493,62,'Centro · Γ = 0 y Z = R',_GREEN)
        text(423,217,493,65,'La referencia R se fija en Ω. El valor z de la carta es Z/R.',_AMBER)
    elif task=='link':
        title='Balance de potencias RF'
        note='El margen se compara en un único plano de referencia, la entrada del receptor.'
        text(45,19,870,42,'Del transmisor a la sensibilidad',_INK,19)
        stages=((45,'TX\nPotencia absoluta\nen dBm',_BLUE),
                (272,'EIRP\nGanancia de antena\ny pérdida de cable',_AMBER),
                (498,'Trayecto\nPérdida en dB',_AMBER),
                (724,'RX\nPotencia recibida\nen dBm',_GREEN))
        for x,body,color in stages:
            box(x,94,189,114,body,color)
        for x in (235,462,688):
            arrow(x,149,x+36,149,_INK)
        text(46,263,842,64,'Ruido integrado + SNR requerida → sensibilidad.\nPotencia recibida − sensibilidad → margen.',_GREEN)
    else:
        title='Rejillas para un mismo registro'
        note='Los tallos conservan las posiciones de la DFT. Zoom FFT evalúa más frecuencias dentro del intervalo elegido.'
        text(59,19,840,41,'Mismo lóbulo, más puntos de evaluación',_INK,19)
        left,right,bottom=82,905,282
        line(left,bottom,right,bottom)
        line(left,71,left,bottom)
        line(345,69,345,bottom,_AMBER,1)
        line(639,69,639,bottom,_AMBER,1)
        def peak(x):
            delta=(x-487)/130
            return (math.sin(math.pi*delta)/(math.pi*delta))**2 if delta else 1
        path=QPainterPath()
        path.moveTo(left,bottom-181*peak(left))
        for x in range(left+1,right):
            path.lineTo(x,bottom-181*peak(x))
        p.setPen(QPen(QColor(_GREEN),3))
        p.drawPath(path)
        for x in range(112,900,84):
            level=bottom-181*peak(x)
            line(x,bottom,x,level,_BLUE,2)
            circle(x,level,4,_BLUE)
        text(350,53,280,39,'Banda de Zoom FFT',_AMBER,12)
        text(88,307,720,36,'Azul · bins DFT     Verde · respuesta del registro finito',_INK,13)
    p.end()
    return title,image,note
