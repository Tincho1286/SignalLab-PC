"""Native illustration of the conversion points in finite precision filtering."""
from PySide6.QtCore import QRectF,Qt,QPointF
from PySide6.QtGui import QImage,QPainter,QColor,QPen,QFont,QPolygonF
from .theme_tokens import COLORS as C

def arithmetic_help_image():
    image=QImage(1050,430,QImage.Format.Format_ARGB32);image.fill(QColor(C['report']))
    p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    def text(rect,value,color='text',size=14):
        p.setPen(QColor(C[color]));p.setFont(QFont('Segoe UI',size));p.drawText(QRectF(*rect),Qt.TextFlag.TextWordWrap,value)
    text((30,15,990,48),'Almacenar coeficientes y ejecutar un filtro son dos pasos distintos',size=18)
    text((30,72,990,48),'En ejecución, cada conversión puede cambiar un valor. El orden de productos y sumas forma parte del modelo.',color='muted',size=14)
    boxes=[(30,'blue','Productos','b[k] · x[n] y a[k] · y[n]','Q del formato elegido'),(380,'amber','Sumas','Se combinan productos y memorias','Q con bits extra de acumulador'),(730,'green','Salida y memorias','Se conserva el resultado para el próximo índice','Q de almacenamiento')]
    for x,color,title,body,footer in boxes:
        p.setPen(QPen(QColor(C[color]),2));p.setBrush(Qt.BrushStyle.NoBrush);p.drawRoundedRect(QRectF(x,145,285,155),8,8)
        text((x+14,156,257,34),title,color,17);text((x+14,198,257,58),body,size=14);text((x+14,263,257,34),footer,color,11)
    for x in (327,677):
        p.setPen(QPen(QColor(C['muted']),2));p.drawLine(x,222,x+36,222);p.setBrush(QColor(C['muted']));p.drawPolygon(QPolygonF([QPointF(x+36,222),QPointF(x+27,216),QPointF(x+27,228)]))
    text((30,329,470,76),'Q(2,2) tiene paso 0.25. Con redondeo, el producto 0.5 × 0.25 = 0.125 pasa a 0.25.','blue',14)
    text((540,329,475,76),'Una memoria puede repetirse con entrada cero. Comparar los estados exactos permite confirmar un ciclo, aunque no haya desbordes.','green',14)
    p.end();return image
