"""Native scientific illustration and navigation cards for the desktop."""
import math

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from .design import icon
from .theme_tokens import AREA_COLORS, COLORS


class SamplingIllustration(QWidget):
    """Draw a continuous sinusoid and its uniformly spaced samples on one axis."""

    def __init__(self):
        super().__init__()
        self.setMinimumSize(300, 150)
        self.setAccessibleName('Una señal continua y sus muestras sobre el mismo eje')

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        left, right = 17, self.width() - 18
        top, bottom = 12, self.height() - 29
        middle = (top + bottom) / 2
        amplitude = (bottom - top) * 0.36

        def point(fraction):
            return QPointF(left + (right - left) * fraction,
                           middle - amplitude * math.sin(4 * math.pi * fraction))

        painter.setPen(QPen(QColor(COLORS['grid']), 1))
        for row in range(5):
            y = top + (bottom - top) * row / 4
            painter.drawLine(QPointF(left, y), QPointF(right, y))
        for column in range(9):
            x = left + (right - left) * column / 8
            painter.drawLine(QPointF(x, top), QPointF(x, bottom))
        painter.setPen(QPen(QColor(COLORS['muted']), 1))
        painter.drawLine(QPointF(left, middle), QPointF(right, middle))

        curve = QPainterPath(point(0))
        for index in range(1, 161):
            curve.lineTo(point(index / 160))
        painter.setPen(QPen(QColor(COLORS['accent']), 2.2))
        painter.drawPath(curve)
        sample = QColor(COLORS['amber'])
        painter.setPen(QPen(sample, 1.5))
        painter.setBrush(sample)
        for index in range(17):
            marker = point(index / 16)
            painter.drawLine(QPointF(marker.x(), middle), marker)
            painter.drawEllipse(marker, 2.6, 2.6)

        painter.setPen(QColor(COLORS['accent']))
        painter.drawText(QRectF(left, bottom + 6, 105, 18), 'Señal continua')
        painter.setPen(sample)
        painter.drawText(QRectF(left + 116, bottom + 6, 100, 18), 'Muestras')
        painter.end()


class QuickAction(QPushButton):
    def __init__(self, title, description, symbol, role, callback, *, area=None):
        super().__init__()
        self.symbol = symbol
        self.role = role
        self.area = area
        self.setObjectName('areaCard' if area else 'quickAction')
        self.setAccessibleName(title)
        self.setAccessibleDescription(description)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 10, 12, 10)
        row.setSpacing(10)
        self.badge = QLabel()
        self.badge.setFixedSize(34, 34)
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        row.addWidget(self.badge)
        copy = QVBoxLayout()
        copy.setSpacing(2)
        for text, name in ((title, 'quickTitle'), (description, 'quickDescription')):
            label = QLabel(text)
            label.setObjectName(name)
            label.setWordWrap(True)
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            copy.addWidget(label)
        row.addLayout(copy, 1)
        arrow = QLabel('›')
        arrow.setObjectName('linkArrow')
        arrow.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        row.addWidget(arrow)
        self.clicked.connect(callback)
        self.refresh_theme()

    def sizeHint(self):
        return self.layout().sizeHint().expandedTo(QSize(145, 62))

    def refresh_theme(self):
        color = AREA_COLORS[self.area] if self.area else COLORS[self.role]
        tint = QColor(color)
        self.badge.setPixmap(icon(self.symbol, color).pixmap(20, 20))
        self.badge.setStyleSheet(
            f'background:rgba({tint.red()},{tint.green()},{tint.blue()},28);border-radius:8px;'
        )
