"""Illustrations of period, pulse width and impulse area for the formula guide."""

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen


def periodic_function_diagram(kind):
    image = QImage(900, 340, QImage.Format.Format_ARGB32)
    background = QColor('#15202b')
    image.fill(background)
    example = {
        'repeat_period': 'Repeat(n+2,n,3,-1)',
        'repeat_samples_period': 'RepeatSamples(n,0,(1,3,2))',
        'pulse_train': 'PulseTrain(t-1,4,2)',
        'impulse_train': 'ImpulseTrain(t-1,4)',
    }[kind]
    discrete = kind in ('repeat_period', 'repeat_samples_period')
    left, right = (-4, 9) if discrete else (-4, 10)
    start, period = (-1, 3) if kind == 'repeat_period' else (0, 3) if discrete else (1, 4)
    axis = 246
    text = QColor('#e5eef7')
    grid = QColor('#8298ad')
    wave = QColor('#73dbc0')
    ruler = QColor('#a7b8ff')

    def x(value):
        return 57+786*(value-left)/(right-left)

    with QPainter(image) as painter:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(QFont('Segoe UI', 15))
        painter.setPen(text)
        painter.drawText(QRectF(52, 15, 790, 34), Qt.AlignmentFlag.AlignLeft, example)
        painter.fillRect(QRectF(x(start), 111, x(start+period)-x(start), axis-111), QColor('#23364c'))
        painter.setPen(QPen(grid, 1))
        painter.drawLine(QLineF(x(left), axis, x(right), axis))
        for index in range(left, right+1):
            painter.drawLine(QLineF(x(index), axis, x(index), axis+6))
            painter.drawText(QRectF(x(index)-17, axis+10, 34, 30), Qt.AlignmentFlag.AlignCenter, str(index))
        painter.drawText(QRectF(770, 293, 100, 26), Qt.AlignmentFlag.AlignRight, 'n' if discrete else 't (s)')

        def bracket(a, b, height, label, color):
            painter.setPen(QPen(color, 2))
            painter.drawLine(QLineF(x(a), height, x(b), height))
            for edge in (a, b):
                painter.drawLine(QLineF(x(edge), height-5, x(edge), height+5))
            painter.drawText(QRectF(x(a), height-31, x(b)-x(a), 26), Qt.AlignmentFlag.AlignCenter, label)

        bracket(start, start+period, 95, f'Período = {period}'+(' muestras' if discrete else ' s'), ruler)
        painter.setPen(QPen(wave, 3))
        painter.setBrush(wave)
        if discrete:
            samples = (1, 2, 3) if kind == 'repeat_period' else (1, 3, 2)
            for index in range(left, right+1):
                height = axis-38*samples[(index-start) % period]
                painter.drawLine(QLineF(x(index), axis, x(index), height))
                painter.drawEllipse(QPointF(x(index), height), 5, 5)
        elif kind == 'pulse_train':
            height = 167
            for edge in (-3, 1, 5, 9):
                stop = min(edge+2, right)
                painter.drawLine(QLineF(x(edge), height, x(stop), height))
                painter.drawLine(QLineF(x(edge), axis, x(edge), height))
                painter.setBrush(wave)
                painter.drawEllipse(QPointF(x(edge), height), 5, 5)
                if edge+2 <= right:
                    painter.drawLine(QLineF(x(stop), axis, x(stop), height))
                    painter.setBrush(QColor('#23364c') if stop == 3 else background)
                    painter.drawEllipse(QPointF(x(stop), height), 5, 5)
            bracket(1, 3, 213, 'Ancho = 2 s', QColor('#f2cd8b'))
        else:
            for position in (-3, 1, 5, 9):
                point = x(position)
                painter.drawLine(QLineF(point, axis, point, 151))
                painter.drawLine(QLineF(point-7, 161, point, 151))
                painter.drawLine(QLineF(point+7, 161, point, 151))
            painter.drawText(QRectF(x(1)+12, 128, 155, 28), Qt.AlignmentFlag.AlignLeft, 'Área = 1')
    return image
