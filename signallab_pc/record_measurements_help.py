"""Colored explanation of finite-record energy, components and crossings."""
from PySide6.QtCore import QRectF,QPointF,QLineF,Qt
from PySide6.QtGui import QImage,QPainter,QColor,QPen,QFont,QPolygonF


def image():
    canvas=QImage(1040,630,QImage.Format.Format_ARGB32);canvas.fill(QColor('#172131'));p=QPainter(canvas);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    ink='#e1e7ee';muted='#a6b2c1';blue='#91b7ff';green='#78d6c2';amber='#edc27d'
    def text(x,y,w,h,value,color=ink,size=14):
        p.setPen(QColor(color));p.setFont(QFont('Segoe UI',size));p.drawText(QRectF(x,y,w,h),Qt.TextFlag.TextWordWrap,value)
    def line(x,y,xx,yy,color=muted,width=2):p.setPen(QPen(QColor(color),width));p.drawLine(QLineF(x,y,xx,yy))
    text(25,16,990,42,'Medir un registro: intervalo, energía y componentes',ink,20)
    text(30,78,470,34,'1. Mismas muestras, intervalo explícito',blue,17)
    p.fillRect(QRectF(140,130,260,128),QColor('#24394b'));line(50,235,480,235)
    for k,value in enumerate((1,1,2,3,1,0)):
        x=65+k*78;y=235-value*29;line(x,235,x,y,blue,3);p.setBrush(QColor(blue));p.drawEllipse(QRectF(x-4,y-4,8,8));text(x-5,266,50,25,str(k),muted,12)
    text(35,310,455,76,'Desde n=1 hasta n=4: cuatro muestras. Ambos extremos se incluyen; no se confunde longitud con separación.',ink,14)
    text(540,78,470,34,'2. Energía acumulada, no amplitud',green,17)
    line(560,260,990,260);line(560,270,560,135)
    p.setPen(QPen(QColor(green),3));p.drawPolyline(QPolygonF([QPointF(560+420*k/100,260-110*(k/100)**3) for k in range(101)]))
    line(560,150,980,150,amber,1);text(578,120,350,28,'Fracción final: 1 = 100 %',amber,12)
    text(550,310,450,76,'Para x(t)=t en [0,1], E=t³/3 y la fracción es t³. Unir sólo sus nodos con rectas no integra la energía.',ink,14)
    line(25,405,1010,405,muted,1)
    text(30,424,470,32,'3. Separar media y alterna',amber,17)
    text(42,472,450,78,'x = [1, 2, 3]\nMedia = 2; alterna = [−1, 0, 1]',ink,15)
    text(42,564,450,44,'P = 14/3 = 4 + 2/3',green,16)
    text(540,424,470,32,'4. Cruce en una muestra o segmento',blue,17)
    text(550,472,455,125,'Discreta: de −1 a 1 cruza el nivel 0 en la segunda muestra.\nContinua: el modelo lineal cruza en el punto medio. El módulo también puede tocar o cruzar dentro del segmento.',ink,14)
    p.end();return canvas
