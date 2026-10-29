"""Explain what to enter for each filter definition without duplicate tools."""
from PySide6.QtCore import Qt,QRectF,QPointF
from PySide6.QtGui import QImage,QPainter,QColor,QPen,QFont
from .theme_tokens import COLORS as C


def filter_design_image():
    image=QImage(960,470,QImage.Format.Format_ARGB32_Premultiplied);image.fill(QColor(C['report']))
    p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    def text(x,y,w,h,value,color='text',size=11):
        p.setPen(QColor(C[color]));p.setFont(QFont('Segoe UI',size))
        p.drawText(QRectF(x,y,w,h),Qt.AlignmentFlag.AlignCenter|Qt.TextFlag.TextWordWrap,value)
    def box(x,y,w,h,color):
        p.setBrush(Qt.BrushStyle.NoBrush);p.setPen(QPen(QColor(C[color]),1.3));p.drawRoundedRect(QRectF(x,y,w,h),10,10)
    def line(x1,y1,x2,y2,color='muted'):
        p.setPen(QPen(QColor(C[color]),1.4));p.drawLine(QPointF(x1,y1),QPointF(x2,y2))
    text(20,9,920,36,'Distintas entradas para diseñar, un mismo lugar para el resultado',size=16)
    rows=[
        ('Bandas y tolerancias','Bordes de paso/rechazo y variaciones permitidas','blue'),
        ('Respuesta FIR','Cortes + longitud, o h[n] propia + ventana','green'),
        ('Polos y ceros','Raíces, ganancia y plano s o z','purple'),
        ('Segundo orden / RC','ω₀ y Q; ω₀, ζ y K; o R y C','amber'),
    ]
    for i,(title,meaning,color) in enumerate(rows):
        y=62+i*81;box(24,y,542,68,color);text(34,y+5,185,56,title,color,12);text(224,y+5,330,56,meaning,size=11)
        line(566,y+34,615,y+34,color);line(615,y+34,615,218,color)
    line(615,218,659,218);line(659,218,650,212);line(659,218,650,224)
    box(668,139,268,157,'border');text(682,151,240,39,'Filtro H(s) o H(z)','blue',17)
    text(682,196,240,84,'Ver su respuesta\nExportar o reutilizar\nEnviar al análisis',size=12)
    text(25,393,910,62,'Digital: ω en rad/muestra. Analógico: Ω en rad/s. Cambiar de método conserva los datos de cada formulario; para convertir un filtro usá Conversión.',size=12)
    p.end();return image
