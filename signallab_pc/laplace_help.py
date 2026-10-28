"""Colour-coded example of a bilateral ROC and its two time supports."""
import math
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QImage, QPainter, QColor, QPen, QFont, QPainterPath
from .theme_tokens import COLORS as C


def laplace_help_image():
    image = QImage(980, 420, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(QColor(C['report']))
    p = QPainter(image); p.setRenderHint(QPainter.RenderHint.Antialiasing)
    def text(x, y, w, h, value, color='text', size=12):
        p.setPen(QColor(C[color])); p.setFont(QFont('Segoe UI', size))
        p.drawText(QRectF(x, y, w, h), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, value)
    def line(x, y, xx, yy, color='muted', width=1, dashed=False):
        pen = QPen(QColor(C[color]), width)
        if dashed: pen.setStyle(Qt.PenStyle.DashLine)
        p.setPen(pen); p.drawLine(QPointF(x, y), QPointF(xx, yy))
    text(15, 12, 445, 40, 'La ROC es una franja del plano s', size=16)
    text(510, 12, 445, 40, 'Cada polo determina un soporte', size=16)
    sx = lambda x: 220+60*x
    fill = QColor(C['green']); fill.setAlpha(38)
    p.fillRect(QRectF(sx(-1), 80, sx(2)-sx(-1), 190), fill)
    line(45, 180, 440, 180); line(sx(0), 75, sx(0), 278)
    line(sx(-1), 80, sx(-1), 270, 'blue', dashed=True)
    line(sx(2), 80, sx(2), 270, 'purple', dashed=True)
    line(sx(.5), 90, sx(.5), 262, 'green', 2, True)
    for real, color in ((-1, 'blue'), (2, 'purple')):
        x = sx(real)
        line(x-6, 174, x+6, 186, color, 2); line(x-6, 186, x+6, 174, color, 2)
        text(x-25, 277, 50, 25, str(real), color)
    text(390, 185, 70, 30, 'Re(s)', 'muted', 10)
    text(220, 53, 80, 25, 'Im(s)', 'muted', 10)
    text(265, 90, 75, 40, 'σ = 0.5', 'green', 11)
    text(35, 310, 420, 38, '−1 < Re(s) < 2', 'green', 15)
    text(25, 352, 440, 52, 'Elegí una línea interior. Los bordes reales los fijan los polos; no se incluyen.', size=11)
    tx = lambda t: 738+t*62
    ty = lambda amplitude: 264-amplitude*130
    line(530, 264, 946, 264); line(tx(0), 94, tx(0), 280)
    for side, color in ((True, 'blue'), (False, 'purple')):
        path = QPainterPath()
        for index in range(121):
            t = index/40 if side else -3+index/40
            y = math.exp(-t) if side else math.exp(2*t)
            point = QPointF(tx(t), ty(y))
            if index: path.lineTo(point)
            else: path.moveTo(point)
        p.setBrush(Qt.BrushStyle.NoBrush); p.setPen(QPen(QColor(C[color]), 3)); p.drawPath(path)
    text(790, 95, 145, 40, 'exp(−t) · u(t)', 'blue', 13)
    text(525, 95, 180, 40, 'exp(2t) · u(−t)', 'purple', 13)
    for tick in (-3, 0, 3): text(tx(tick)-18, 277, 36, 25, str(tick), 'muted', 10)
    text(910, 232, 50, 25, 't (s)', 'muted', 10)
    text(510, 310, 445, 38, 'X(s) = 1/(s+1) − 1/(s−2)', size=14)
    text(510, 352, 445, 52, 'Azul: término derecho. Violeta: término izquierdo. La franja común permite que ambos converjan.', size=11)
    p.end()
    return image
