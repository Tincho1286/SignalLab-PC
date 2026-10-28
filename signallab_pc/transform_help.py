"""Coloured diagrams of the operation actually selected in the tool."""
from PySide6.QtCore import Qt,QRectF,QPointF
from PySide6.QtGui import QImage,QPainter,QColor,QPen,QFont,QPainterPath
from .theme_tokens import COLORS as C

def transform_help_image(operation,continuous=False):
    image=QImage(960,350,QImage.Format.Format_ARGB32_Premultiplied);image.fill(QColor(C['report']));p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    x=[-3,-2,-1,0,1,2,3];values=[0,0,0,1,2,0,0]
    if operation=='parity':panels=[('Original',x,values,C['blue']),('Parte par',x,[0,0,1,1,1,0,0],C['green']),('Parte impar',x,[0,0,-1,0,1,0,0],C['purple'])];caption='Par: simétrica alrededor de cero. Impar: cambia de signo al reflejarla. La suma recupera la señal.'
    else:
        after={'shift':[0,0,0,0,1,2,0],'reverse':[0,0,2,1,0,0,0],'scale':[0,0,0,.5,1,0,0],'affine':values}[operation]
        xx=[value/2 for value in x] if operation=='affine' else x
        panels=[('Original',x,values,C['blue']),('Transformada',xx,after,C['green'])]
        caption={'shift':'Desplazamiento +1: cada valor aparece una unidad más a la derecha.','reverse':'Inversión: los valores de la derecha pasan a la izquierda, con la misma amplitud.','scale':'Amplitud A=1/2: cada valor se divide por dos y su posición se conserva.','affine':'Escala a=2: cada punto pasa de τ a τ/2. El registro se comprime a la mitad.'}[operation]
    def text(rect,value,color,size=12):p.setFont(QFont('Segoe UI',size));p.setPen(QColor(color));p.drawText(rect,Qt.AlignmentFlag.AlignCenter|Qt.TextFlag.TextWordWrap,value)
    def line(a,b,color,width=1):p.setPen(QPen(QColor(color),width));p.drawLine(QPointF(*a),QPointF(*b))
    for index,(title,coords,ys,color) in enumerate(panels):
        left=20+index*(940/len(panels));width=900/len(panels)-20
        text(QRectF(left,14,width+15,45),title,color,16)
        pos=lambda value:left+30+(value+3)*width/6
        line((pos(-3),200),(pos(3),200),C['muted']);line((pos(0),100),(pos(0),247),C['grid'])
        for tick in (-3,0,3):text(QRectF(pos(tick)-18,255,36,22),str(tick),C['muted'],10)
        for tick in (-1,1,2):text(QRectF(left-3,190-tick*40,28,20),str(tick),C['muted'],9)
        points=[(pos(value),200-y*40) for value,y in zip(coords,ys)]
        if continuous:
            path=QPainterPath();path.moveTo(*points[0])
            for point in points[1:]:path.lineTo(*point)
            p.setBrush(Qt.BrushStyle.NoBrush);p.setPen(QPen(QColor(color),2));p.drawPath(path)
        for (xx,yy),value in zip(points,ys):
            if not continuous:line((xx,200),(xx,yy),color,2)
            p.setBrush(QColor(color));p.setPen(QPen(QColor(color),1));p.drawEllipse(QPointF(xx,yy),3,3)
        text(QRectF(left+30,278,width,20),'Tiempo t (s)' if continuous else 'Índice n',C['text'],10)
    text(QRectF(30,304,900,40),caption,C['text'],12);p.end();return image
