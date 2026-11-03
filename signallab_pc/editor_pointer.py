"""Root insertion glyphs whose center is the actual mouse hotspot."""
from PySide6.QtCore import Qt,QPointF
from PySide6.QtGui import QCursor,QPixmap,QPainter,QPen,QColor
from .theme_tokens import COLORS as C


def insertion_cursor(canvas,kind):
    ratio=float(canvas.devicePixelRatioF());size=32;center=16
    pixmap=QPixmap(round(size*ratio),round(size*ratio));pixmap.setDevicePixelRatio(ratio);pixmap.fill(Qt.GlobalColor.transparent)
    painter=QPainter(pixmap);painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    def shape():
        if kind=='pole':
            painter.drawLine(QPointF(center-6,center-6),QPointF(center+6,center+6));painter.drawLine(QPointF(center-6,center+6),QPointF(center+6,center-6))
        else:painter.drawEllipse(QPointF(center,center),7,7)
    painter.setPen(QPen(QColor(C['window']),4.5));shape()
    painter.setPen(QPen(QColor(C['red'] if kind=='pole' else C['blue']),2.));shape();painter.end()
    return QCursor(pixmap,center,center)
