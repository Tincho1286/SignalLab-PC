"""Orientación visual local: entradas, operación y resultado de cada herramienta."""
from html import escape
from PySide6.QtCore import QByteArray,Qt
from PySide6.QtGui import QPixmap,QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel

class ToolGuide(QWidget):
    def __init__(self,purpose,stages,parent=None):
        super().__init__(parent);layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,6)
        note=QLabel(purpose);note.setWordWrap(True);layout.addWidget(note)
        parts=[]
        for index,label in enumerate(stages):
            x=8+index*128
            parts.append(f'<rect x="{x}" y="8" width="110" height="48" rx="5" fill="#1c2c3b" stroke="#416273"/><text x="{x+55}" y="37" text-anchor="middle" fill="#dce4ef" font-family="Segoe UI" font-size="12">{escape(label)}</text>')
            if index<2:parts.append(f'<path d="M{x+113} 32h12m-4-4 4 4-4 4" fill="none" stroke="#53cbb6"/>')
        svg='<svg xmlns="http://www.w3.org/2000/svg" width="384" height="64">'+''.join(parts)+'</svg>'
        pixmap=QPixmap(384,64);pixmap.fill(Qt.GlobalColor.transparent);painter=QPainter(pixmap);QSvgRenderer(QByteArray(svg.encode())).render(painter);painter.end()
        drawing=QLabel();drawing.setPixmap(pixmap.scaledToWidth(300,Qt.TransformationMode.SmoothTransformation));drawing.setAccessibleName(' → '.join(stages));layout.addWidget(drawing)
