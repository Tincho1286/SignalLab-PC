"""Visual input for continuous and discrete realizations."""

from dataclasses import replace
import json
import math
from pathlib import Path
from tokenize import TokenError

from PySide6.QtCore import QByteArray, QLineF, QPoint, QPointF, QRect, QRectF, QSize, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPainterPathStroker, QPen
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QBoxLayout, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QFrame, QGraphicsEllipseItem, QGraphicsItem,
    QGraphicsPathItem, QGraphicsRectItem, QGraphicsScene, QGraphicsSimpleTextItem, QGraphicsView,
    QGridLayout, QHBoxLayout, QInputDialog, QLabel, QMenu, QMessageBox, QPushButton, QToolButton, QVBoxLayout, QWidget,
)

from .atomic_file import write_json
from .design import icon
from .math_display import latex
from .math_source import normalize
from .realization_diagram import DiagramView
from .realization_graph import BLOCK_NAMES, LEFT_INPUT, LOWER_INPUT, Block, RealizationGraph, Wire
from .resources import ensure_working_set
from .theme_tokens import COLORS as C
from .vector_math import render_latex
from .wrapping_row import WrappingRow


class PortItem(QGraphicsEllipseItem):
    def __init__(self, block, direction, *, output=False, index=LEFT_INPUT):
        super().__init__(-5, -5, 10, 10, block)
        self.block_id = block.block.id
        self.direction = direction
        self.output = output
        self.index = index
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setZValue(2)
        self.set_sign(1)

    def set_sign(self, sign):
        self.sign = sign
        self.color = QColor(C['blue' if self.output else 'amber' if sign < 0 else 'green'])
        self.set_highlight(False)
        if self.output:
            self.setToolTip('Salida · arrastrá desde acá hasta la entrada de otro bloque.')
        elif self.parentItem().block.kind == 'sum':
            self.setToolTip('Entrada de resta (−) · editá el sumador para cambiar el signo.' if sign < 0
                            else 'Entrada de suma (+) · editá el sumador para cambiar el signo.')
        else:
            self.setToolTip('Entrada · soltá acá el cable.')

    def set_highlight(self, active):
        self.setPen(QPen(self.color, 2.4 if active else 1.7))
        self.setBrush(self.color if self.output or active else QColor(C['panel']))


class BlockItem(QGraphicsRectItem):
    def __init__(self, block, domain, editor):
        bounds = {'sum': QRectF(-25, -25, 50, 50),
                  'input': QRectF(-36, -19, 72, 38),
                  'output': QRectF(-36, -19, 72, 38)}
        super().__init__(bounds.get(block.kind, QRectF(-65, -24, 130, 48)))
        self.block = block
        self.editor = editor
        self.domain = domain
        self.setPos(block.x, block.y)
        color = {'memory': 'green', 'gain': 'blue', 'transfer': 'blue', 'sum': 'amber'}.get(block.kind, 'muted')
        self.setPen(QPen(QColor(C[color]), 1.5))
        self.setBrush(QColor(C['panel']))
        self.setZValue(1)
        flags = QGraphicsItem.GraphicsItemFlag
        self.setFlags(flags.ItemIsSelectable | flags.ItemIsMovable | flags.ItemSendsGeometryChanges)
        self.inputs = {}
        if block.kind != 'input':
            self.inputs[LEFT_INPUT] = PortItem(self, QPointF(-1, 0))
        if block.kind == 'sum':
            self.inputs[LOWER_INPUT] = PortItem(self, QPointF(0, 1), index=LOWER_INPUT)
        self.output = PortItem(self, QPointF(1, 0), output=True) if block.kind != 'output' else None
        self.set_definition(block)

    def set_definition(self, block):
        self.block = block
        kind = block.kind
        if kind == 'sum':
            for index, port in self.inputs.items():
                port.set_sign(block.input_signs[index - 1])
        discrete = self.domain == 'digital'
        text = {
            'input': 'x[n]' if discrete else 'x(t)',
            'output': 'y[n]' if discrete else 'y(t)',
            'sum': '',
            'memory': 'z^(-1)' if discrete else '1/s',
            'gain': block.gain,
            'transfer': block.formula,
        }[kind]
        self.formula = None
        self.formula_size = (0, 0)
        self.fallback = text
        if text:
            try:
                vector = render_latex(latex(normalize(text)), size=15, color=C['text'])
            except (ValueError, SyntaxError, KeyError, TypeError, IndexError, TokenError, RecursionError):
                metrics = self.editor.fontMetrics()
                self.fallback = metrics.elidedText(text, Qt.TextElideMode.ElideRight, 175)
                self.formula_size = (metrics.horizontalAdvance(self.fallback), metrics.height())
            else:
                self.formula = QSvgRenderer(QByteArray(vector.svg))
                # Expand for fractions and longer expressions. The tooltip keeps the full input.
                scale = min(1, 190 / vector.width, 67 / vector.height)
                self.formula_size = (vector.width * scale, vector.height * scale)
        if kind in ('transfer', 'gain'):
            width, height = self.formula_size
            if kind == 'gain':
                # At the triangle's centroid there is room on both sides of the label.
                width, height = max(122, width * 1.55 + 24), max(54, height * 1.8 + 20)
            else:
                width, height = max(138, width + 26), max(50, height + 16)
            self.setRect(-width / 2, -height / 2, width, height)
        name = ('Retardo de una muestra' if discrete else 'Integrador') if kind == 'memory' else BLOCK_NAMES[kind]
        self.setToolTip(name + (f' · {text}' if text else ''))
        self.position_ports()
        self.update()

    def gain_direction(self):
        for item in self.editor.wires.values():
            if item.wire.source == self.block.id and item.target is not self:
                return -1 if item.target.x() < self.x() else 1
        return 1

    def position_ports(self):
        direction = self.gain_direction() if self.block.kind == 'gain' else 1
        if self.output is not None:
            self.output.direction = QPointF(direction, 0)
        if LEFT_INPUT in self.inputs:
            self.inputs[LEFT_INPUT].direction = QPointF(-direction, 0)
        bounds = self.rect()
        ports = list(self.inputs.values())
        if self.output is not None:
            ports.append(self.output)
        for port in ports:
            port.setPos(port.direction.x() * bounds.width() / 2, port.direction.y() * bounds.height() / 2)

    def paint(self, painter, option, widget=None):
        kind = self.block.kind
        painter.setPen(self.pen() if not self.isSelected() else QPen(QColor(C['green']), 2.5))
        painter.setBrush(self.brush())
        center_x = 0
        bounds = self.rect()
        if kind == 'gain':
            direction = self.gain_direction()
            half = bounds.width() / 2
            path = QPainterPath(QPointF(-direction * half, bounds.top()))
            path.lineTo(QPointF(direction * half, 0))
            path.lineTo(QPointF(-direction * half, bounds.bottom()))
            path.closeSubpath()
            painter.drawPath(path)
            center_x = -direction * half / 3
        elif kind == 'sum':
            painter.drawEllipse(bounds)
            painter.setPen(QColor(C['text']))
            for port in self.inputs.values():
                center = port.pos() - port.direction * 13
                painter.drawText(QRectF(center.x()-8, center.y()-8, 16, 16), Qt.AlignmentFlag.AlignCenter,
                                 '+' if port.sign > 0 else '−')
            return
        else:
            painter.drawRoundedRect(bounds, 5, 5)
        if self.formula is not None:
            width, height = self.formula_size
            self.formula.render(painter, QRectF(center_x - width / 2, -height / 2, width, height))
        else:
            painter.setPen(QColor(C['text']))
            painter.drawText(bounds.translated(center_x, 0), Qt.AlignmentFlag.AlignCenter, self.fallback)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged and self.scene() is not None:
            self.editor.redraw_wires(self.block.id)
        return super().itemChange(change, value)

    def definition(self):
        return replace(self.block, x=self.x(), y=self.y())


def cable_path(start, end, outgoing, incoming, opposite=False):
    """Leave and approach the ports along their normals."""
    path = QPainterPath(start)
    lead = 20
    advance = QPointF.dotProduct(end - start, outgoing)
    if outgoing == incoming and advance > 0:
        lead = min(lead, advance / 3)
    first, last = start + outgoing * lead, end - incoming * lead
    path.lineTo(first)
    if incoming.y():
        # Face the lower sum port from below, including for loops back to the same sum.
        lane = max(first.y(), last.y()) + (14 if start.y() <= end.y() else 0)
        path.lineTo(first.x(), lane)
        path.lineTo(last.x(), lane)
    else:
        same_direction = outgoing == incoming
        if same_direction and advance >= 0 and not opposite:
            middle = (first.x() + last.x()) / 2
            path.lineTo(middle, first.y())
            path.lineTo(middle, last.y())
        elif not same_direction and abs(start.y() - end.y()) >= 75:
            middle = max(first.x(), last.x()) if outgoing.x() > 0 else min(first.x(), last.x())
            path.lineTo(middle, first.y())
            path.lineTo(middle, last.y())
        else:
            lane = (max(first.y(), last.y()) + 75 if opposite and outgoing.x() > 0
                    else min(first.y(), last.y()) - 75)
            path.lineTo(first.x(), lane)
            path.lineTo(last.x(), lane)
    path.lineTo(last)
    path.lineTo(end)
    return path


class WireItem(QGraphicsPathItem):
    def __init__(self, wire, source, target):
        super().__init__()
        self.wire = wire
        self.source = source
        self.target = target
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.minus = None
        if wire.sign < 0 and target.block.kind != 'sum':
            self.minus = QGraphicsSimpleTextItem('−', self)
            self.minus.setBrush(QColor(C['amber']))

    def shape(self):
        stroker = QPainterPathStroker()
        stroker.setWidth(10)
        return stroker.createStroke(self.path())

    def boundingRect(self):
        return super().boundingRect().adjusted(-5, -5, 5, 5)

    def redraw(self, opposite=False):
        source = self.source.output
        sum_target = self.target.block.kind == 'sum'
        target = self.target.inputs[self.wire.sum_port if sum_target else LEFT_INPUT]
        sign = self.wire.sign_at(self.target.block)
        self.setPen(QPen(QColor(C['amber' if sign < 0 else 'blue']), 1.8))
        operation = 'resta' if sign < 0 else 'suma' if sum_target else ''
        self.setToolTip(f'{self.wire.source} → {self.wire.target}' + (f' · {operation}' if operation else ''))
        start, end = source.scenePos(), target.scenePos()
        tangent = -target.direction
        path = cable_path(start, end, source.direction, tangent, opposite)
        # Leave a small arrowhead in front of the visible input port.
        tip = end - tangent * 6
        side = QPointF(-tangent.y(), tangent.x())
        path.moveTo(tip - tangent * 7 + side * 4)
        path.lineTo(tip)
        path.lineTo(tip - tangent * 7 - side * 4)
        self.setPath(path)
        if self.minus is not None:
            self.minus.setPos(path.pointAtPercent(.60) + QPointF(-6, -18))


class EditorView(DiagramView):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.cable_source = self.cable_target = self.cable_preview = None

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        step = 24
        scale = max(abs(self.transform().m11()), .01)
        while scale * step < 16:
            step *= 2
        color = QColor(C['grid'])
        color.setAlpha(105)
        pen = QPen(color)
        pen.setCosmetic(True)
        painter.setPen(pen)
        vertical = (QLineF(x, rect.top(), x, rect.bottom()) for x in
                    range(math.ceil(rect.left()/step)*step, math.floor(rect.right()/step)*step + 1, step))
        horizontal = (QLineF(rect.left(), y, rect.right(), y) for y in
                      range(math.ceil(rect.top()/step)*step, math.floor(rect.bottom()/step)*step + 1, step))
        painter.drawLines([*vertical, *horizontal])

    def wheelEvent(self, event):
        scale = self.transform().m11()
        super().wheelEvent(event)
        if self.transform().m11() != scale:
            self.editor.fit_mode = False

    def block_at(self, position):
        item = self.itemAt(position)
        while item is not None and not isinstance(item, BlockItem):
            item = item.parentItem()
        return item

    def port_at(self, position, *, output):
        # Keep the handle easy to hit even when the view is zoomed out.
        radius = 10
        area = QRect(position - QPoint(radius, radius), position + QPoint(radius, radius))
        candidates = (item for item in self.items(area)
                      if isinstance(item, PortItem) and item.output == output)
        return min(candidates, key=lambda port: (position - self.mapFromScene(port.scenePos())).manhattanLength(),
                   default=None)

    def begin_cable(self, port):
        self.cable_source = port
        self.cable_preview = self.scene().addPath(QPainterPath())
        self.cable_preview.setZValue(3)
        self.cable_preview.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.viewport().setCursor(Qt.CursorShape.CrossCursor)
        self.editor.hint.setText('Soltá el cable sobre una entrada. En el sumador, elegí + o −. Esc cancela.')

    def trace_cable(self, position):
        target = self.port_at(position, output=False)
        if target is not self.cable_target:
            if self.cable_target is not None:
                self.cable_target.set_highlight(False)
            self.cable_target = target
            if target is not None:
                target.set_highlight(True)
        start = self.cable_source.scenePos()
        direction = self.cable_source.direction
        end = target.scenePos() if target is not None else self.mapToScene(position)
        incoming = -target.direction if target is not None else direction
        path = cable_path(start, end, direction, incoming)
        color = QColor(C['amber' if target is not None and target.sign < 0 else 'blue'])
        style = Qt.PenStyle.SolidLine if target is not None else Qt.PenStyle.DashLine
        self.cable_preview.setPen(QPen(color, 2, style))
        self.cable_preview.setPath(path)

    def cancel_cable(self):
        if self.cable_preview is None:
            return
        self.scene().removeItem(self.cable_preview)
        if self.cable_target is not None:
            self.cable_target.set_highlight(False)
        self.cable_source = self.cable_target = self.cable_preview = None
        self.viewport().unsetCursor()
        self.editor.start_connection(None)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            position = event.position().toPoint()
            if self.editor.connection_sign is not None:
                item = self.block_at(position)
                if item is not None:
                    self.editor.connect_block(item, self.port_at(position, output=False))
                event.accept()
                return
            port = self.port_at(position, output=True)
            if port is not None:
                self.setFocus()
                self.begin_cable(port)
                self.trace_cable(position)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.cable_source is not None:
            self.trace_cable(event.position().toPoint())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        position = event.position().toPoint()
        if self.port_at(position, output=True) is not None:
            self.mousePressEvent(event)
            return
        block = self.block_at(position)
        if block is not None and block.block.kind in ('gain', 'transfer', 'sum') and self.editor.connection_sign is None:
            self.editor.edit_block(block)
        else:
            super().mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event):
        if self.cable_source is not None and event.button() == Qt.MouseButton.LeftButton:
            source = self.cable_source
            target = self.port_at(event.position().toPoint(), output=False)
            self.cancel_cable()
            if target is not None:
                sum_target = target.parentItem().block.kind == 'sum'
                self.editor.finish_wire(Wire(source.block_id, target.block_id,
                                             target_port=target.index if sum_target else None))
            event.accept()
            return
        super().mouseReleaseEvent(event)
        self.editor.update_bounds()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.cable_source is not None:
                self.cancel_cable()
                event.accept()
                return
            if self.editor.connection_sign is not None:
                self.editor.start_connection(None)
                event.accept()
                return
        super().keyPressEvent(event)


class RealizationEditor(QDialog):
    def __init__(self, graph, parent=None, *, owner=None):
        super().__init__(parent)
        self.owner = owner
        self.setWindowTitle('Editor de realización')
        self.resize(940, 570)
        self.setMinimumSize(450, 350)
        self.connection_sign = None
        self.connection_source = None
        self.blocks = {}
        self.wires = {}
        self.saved_graph = graph
        self.fit_mode = True
        self.fit_timer = QTimer(self)
        self.fit_timer.setSingleShot(True)
        self.fit_timer.timeout.connect(self.fit_diagram)
        self.setObjectName('realizationEditor')
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 11, 14, 11)
        root.setSpacing(9)

        header = QHBoxLayout()
        title = QLabel('Editor de realización')
        title.setObjectName('diagramTitle')
        header.addWidget(title, 1)
        self.domain_label = QLabel()
        self.domain_label.setObjectName('diagramDomain')
        header.addWidget(self.domain_label)
        root.addLayout(header)

        commands = WrappingRow()
        commands.setObjectName('diagramCommands')
        root.addWidget(commands)
        file_button = self.menu_button('Archivo', 'folder', commands)
        file_button.setObjectName('diagramFileMenu')
        file_menu = QMenu(file_button)
        file_button.setMenu(file_menu)
        file_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        file_menu.addAction('Nuevo diagrama', self.new_diagram)
        file_menu.addAction('Abrir JSON…', self.open_file)
        file_menu.addAction('Guardar JSON…', self.save_file)
        fit = self.button('Ajustar vista', 'expand', self.fit_diagram, commands)
        fit.setToolTip('Encuadrar todos los bloques y cables')
        closer = self.button('Acercar', 'search', lambda: self.change_zoom(1.15), commands)
        closer.setToolTip('Acercar el diagrama')
        farther = self.button('Alejar', 'restore', lambda: self.change_zoom(1 / 1.15), commands)
        farther.setToolTip('Alejar el diagrama')
        self.connect_button = self.menu_button('Conectar', 'convert', commands)
        self.connect_button.setObjectName('diagramConnect')
        self.connect_button.setCheckable(True)
        self.connect_button.setToolTip('Conectar por clics. Elegí el origen y después el destino.')
        self.connect_button.clicked.connect(lambda: self.start_connection(1))
        links = QMenu(self.connect_button)
        self.connect_button.setMenu(links)
        self.connect_button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.subtract_button = links.addAction('Conectar restando')
        self.subtract_button.setCheckable(True)
        self.subtract_button.triggered.connect(lambda: self.start_connection(-1))

        self.workspace_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.workspace_layout.setSpacing(10)
        root.addLayout(self.workspace_layout, 1)
        self.palette = QFrame()
        self.palette.setObjectName('diagramPalette')
        palette_box = QVBoxLayout(self.palette)
        palette_box.setContentsMargins(9, 9, 9, 9)
        palette_box.setSpacing(7)
        block_title = QLabel('Bloques')
        block_title.setObjectName('diagramSectionTitle')
        palette_box.addWidget(block_title)
        self.palette_grid = QGridLayout()
        self.palette_grid.setSpacing(5)
        palette_box.addLayout(self.palette_grid)
        palette_box.addStretch()
        self.workspace_layout.addWidget(self.palette)

        self.transfer_button = self.block_button(
            'Transferencia', 'blocks', 'transfer',
            'Multiplica la señal por una función de transferencia. Escribila o cargala de Resultados.')
        gain = self.block_button('Ganancia · K', 'chart', 'gain', 'Multiplica la señal por una constante.')
        sum_button = self.block_button('Sumador · ±', 'math', 'sum',
                                       'Combina dos entradas. Editá el bloque para elegir sus signos.')
        self.memory = self.block_button('', 'sample', 'memory', '')
        self.palette_buttons = (self.transfer_button, gain, sum_button, self.memory)

        self.hint = QLabel()
        self.hint.setObjectName('diagramHint')
        self.hint.setWordWrap(True)
        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QColor(C['report']))
        self.view = EditorView(self)
        self.view.setObjectName('diagramCanvas')
        self.view.setScene(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setAccessibleName('Diagrama de bloques de la realización')
        self.view.setToolTip('Ctrl + rueda cambia el zoom. Arrastrá un espacio vacío para recorrer el diagrama.')
        self.view.setMinimumSize(0, 90)
        self.workspace_layout.addWidget(self.view, 1)
        root.addWidget(self.hint)

        selection = WrappingRow()
        self.selection_label = QLabel()
        self.selection_label.setObjectName('muted')
        selection.flow.addWidget(self.selection_label)
        self.edit_button = self.button('Editar bloque…', 'filter', self.edit_selected_block, selection)
        self.delete_button = self.button('Quitar selección', 'remove', self.delete_selection, selection)
        root.addWidget(selection)
        self.scene.selectionChanged.connect(self.update_selection)

        footer = QHBoxLayout()
        self.connection_state = QLabel()
        self.connection_state.setObjectName('diagramConnectionState')
        self.connection_state.setWordWrap(True)
        footer.addWidget(self.connection_state, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('Cancelar')
        accept = buttons.addButton('Usar diagrama', QDialogButtonBox.ButtonRole.AcceptRole)
        accept.setObjectName('primary')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        footer.addWidget(buttons)
        root.addLayout(footer)
        self.adapt_palette()
        self.set_graph(graph)

    @staticmethod
    def menu_button(title, symbol, row):
        button = QToolButton()
        button.setObjectName('diagramTool')
        button.setText(title)
        button.setIcon(icon(symbol))
        button.setIconSize(QSize(17, 17))
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        row.flow.addWidget(button)
        return button

    @classmethod
    def button(cls, title, symbol, action, row):
        button = cls.menu_button(title, symbol, row)
        button.clicked.connect(action)
        return button

    def block_button(self, title, symbol, kind, description):
        button = QPushButton(icon(symbol, C['accent']), title)
        button.setObjectName('diagramBlockButton')
        button.setIconSize(QSize(20, 20))
        button.setAutoDefault(False)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setToolTip(description)
        button.setAccessibleDescription(description)
        button.clicked.connect(lambda: self.add_block(kind))
        return button

    def adapt_palette(self):
        side = self.width() >= 850 or self.height() < 475 and self.width() >= 650
        self.palette.setMaximumWidth(214 if side else self.width())
        if getattr(self, '_side_palette', None) == side:
            return
        self._side_palette = side
        direction = QBoxLayout.Direction.LeftToRight if side else QBoxLayout.Direction.TopToBottom
        self.workspace_layout.setDirection(direction)
        self.palette.setMinimumWidth(190 if side else 0)
        columns = 1 if side else 2
        for index, button in enumerate(self.palette_buttons):
            self.palette_grid.removeWidget(button)
            row, column = divmod(index, columns)
            self.palette_grid.addWidget(button, row, column)
        for column in range(2):
            self.palette_grid.setColumnStretch(column, int(column < columns))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'palette_buttons'):
            self.adapt_palette()
            if self.fit_mode:
                self.fit_timer.start(0)

    def change_zoom(self, factor):
        view = self.view
        if .25 <= view.transform().m11() * factor <= 4:
            view.scale(factor, factor)
            self.fit_mode = False

    def showEvent(self, event):
        super().showEvent(event)
        self.fit_diagram()

    def set_graph(self, graph):
        self.view.cancel_cable()
        self.domain = graph.domain
        self.scene.clear()
        self.blocks.clear()
        self.wires.clear()
        for block in graph.blocks:
            item = BlockItem(block, graph.domain, self)
            self.scene.addItem(item)
            self.blocks[block.id] = item
        for wire in graph.wires:
            self.add_wire(wire)
        discrete = graph.domain == 'digital'
        variable = 'z' if discrete else 's'
        self.domain_label.setText('Discreto · H(z)' if discrete else 'Continuo · H(s)')
        self.transfer_button.setText(f'Transferencia · H({variable})')
        self.memory.setText('Retardo · z⁻¹' if discrete else 'Integrador · 1/s')
        description = ('Devuelve la muestra anterior de la señal.' if discrete
                       else 'Integra la señal en el tiempo con estado inicial nulo.')
        self.memory.setToolTip(description)
        self.memory.setAccessibleDescription(description)
        self.start_connection(None)
        self.update_selection()
        self.update_connection_state()
        self.fit_diagram()

    def graph(self):
        return RealizationGraph(self.domain, tuple(item.definition() for item in self.blocks.values()),
                                tuple(item.wire for item in self.wires.values()))

    def update_bounds(self):
        rect = self.scene.itemsBoundingRect().adjusted(-48, -48, 48, 48)
        self.scene.setSceneRect(rect.united(QRectF(-95, -170, 800, 385)))

    def fit_diagram(self):
        self.fit_mode = True
        self.update_bounds()
        bounds = self.scene.itemsBoundingRect().adjusted(-42, -42, 42, 42)
        self.view.fitInView(bounds, Qt.AspectRatioMode.KeepAspectRatio)
        if self.view.transform().m11() > 1:
            self.view.resetTransform()
            self.view.centerOn(bounds.center())

    def add_block(self, kind):
        self.start_connection(None)
        ident = max(self.blocks) + 1
        block = Block(ident, kind, 0, 0)
        if kind == 'transfer':
            block = self.edit_transfer(block)
            if block is None:
                return
        item = BlockItem(block, self.domain, self)
        occupied = [existing.sceneBoundingRect() for existing in self.blocks.values()]
        margin = item.boundingRect().adjusted(-25, -20, 25, 20)
        index = 0
        while True:
            x, y = 160 + index % 2 * 245, index // 2 * 120
            if not any(margin.translated(x, y).intersects(rect) for rect in occupied):
                item.setPos(x, y)
                break
            index += 1
        self.scene.addItem(item)
        self.blocks[ident] = item
        self.scene.clearSelection()
        item.setSelected(True)
        self.update_bounds()
        self.view.ensureVisible(item)
        self.update_connection_state()
        if kind == 'gain':
            self.edit_block(item)

    def start_connection(self, sign):
        self.connection_sign = None if sign == self.connection_sign else sign
        self.connection_source = None
        self.connect_button.setChecked(self.connection_sign is not None)
        self.connect_button.setText('Conectar −' if self.connection_sign == -1 else 'Conectar')
        self.subtract_button.setChecked(self.connection_sign == -1)
        if self.connection_sign is not None:
            self.view.setFocus()
            self.hint.setText('Seleccioná el bloque de origen y luego el de destino.')
        else:
            self.hint.setText('Arrastrá desde una salida ● hasta una entrada ○. Hacé doble clic en un bloque para editarlo.')

    def connect_block(self, item, port=None):
        if self.connection_source is None:
            if item.block.kind == 'output':
                self.hint.setText('Elegí un origen. La salida y sólo recibe conexiones.')
                return
            self.connection_source = item.block.id
            self.scene.clearSelection()
            item.setSelected(True)
            self.hint.setText(f'Origen {item.block.id} seleccionado. Elegí el bloque de destino.')
            return
        if item.block.kind == 'sum':
            if port is None or port.block_id != item.block.id:
                port = next((entry for entry in item.inputs.values() if entry.sign == self.connection_sign), None)
            if port is None:
                self.hint.setText('El sumador no tiene una entrada con ese signo. '
                                  'Elegí un puerto o editá los signos del sumador.')
                return
            wire = Wire(self.connection_source, item.block.id, target_port=port.index)
        else:
            wire = Wire(self.connection_source, item.block.id, self.connection_sign)
        self.finish_wire(wire)

    def finish_wire(self, wire):
        graph = self.graph()
        try:
            replace(graph, wires=graph.wires + (wire,)).connections()
        except ValueError as exc:
            self.hint.setText(str(exc))
            return
        self.add_wire(wire)
        self.start_connection(None)
        self.update_bounds()
        self.update_connection_state()

    def add_wire(self, wire):
        item = WireItem(wire, self.blocks[wire.source], self.blocks[wire.target])
        self.wires[wire.source, wire.target] = item
        self.scene.addItem(item)
        self.redraw_wires(wire.source)

    def reverse_wire(self, wire):
        if wire.source != wire.target:
            return self.wires.get((wire.target, wire.source))
        return None

    def redraw_wires(self, ident):
        affected={ident}
        affected.update(item.wire.source for item in self.wires.values()
                        if item.wire.target==ident and item.source.block.kind=='gain')
        for key in affected:
            self.blocks[key].position_ports()
            self.blocks[key].update()
        for item in self.wires.values():
            wire = item.wire
            if wire.source in affected or wire.target in affected:
                item.redraw(self.reverse_wire(wire) is not None)

    def update_selection(self):
        selected = self.scene.selectedItems()
        self.edit_button.setEnabled(any(isinstance(item, BlockItem) and item.block.kind in ('gain', 'transfer', 'sum')
                                       for item in selected))
        self.delete_button.setEnabled(any(isinstance(item, WireItem) or
                                          isinstance(item, BlockItem) and item.block.kind not in ('input', 'output')
                                          for item in selected))
        if len(selected) == 1 and isinstance(selected[0], BlockItem):
            block = selected[0].block
            label = f'{BLOCK_NAMES[block.kind]} {block.id}'
        elif len(selected) == 1 and isinstance(selected[0], WireItem):
            wire = selected[0].wire
            label = f'Conexión {wire.source} → {wire.target}'
        else:
            label = f'{len(selected)} elementos seleccionados' if selected else 'Seleccioná un bloque o un cable.'
        self.selection_label.setText(label)

    def update_connection_state(self):
        try:
            self.graph().connections_for_transfer()
            complete = True
            text = 'Conexiones listas para analizar.'
        except ValueError as error:
            complete = False
            text = str(error)
        label = self.connection_state
        if label.property('complete') != complete:
            label.setProperty('complete', complete)
            label.style().unpolish(label)
            label.style().polish(label)
        label.setText(text)

    def edit_selected_block(self):
        for item in self.scene.selectedItems():
            if isinstance(item, BlockItem) and item.block.kind in ('gain', 'transfer', 'sum'):
                self.edit_block(item)
                break

    def edit_block(self, item):
        block = item.block
        if block.kind == 'transfer':
            definition = self.edit_transfer(block)
            if definition is not None:
                self.apply_definition(item, definition)
        elif block.kind == 'sum':
            self.edit_sum(item)
        elif block.kind == 'gain':
            text, accepted = QInputDialog.getText(self, 'Ganancia', 'Valor exacto (por ejemplo, 1/3 o pi):', text=block.gain)
            if accepted and text.strip():
                self.apply_definition(item, replace(block, gain=text.strip()))

    def edit_sum(self, item):
        dialog = QDialog(self)
        dialog.setWindowTitle('Signos del sumador')
        layout = QFormLayout(dialog)
        selectors = []
        for label, sign in zip(('Entrada izquierda', 'Entrada inferior'), item.block.input_signs):
            selector = QComboBox(dialog)
            selector.addItem('+ Sumar', 1)
            selector.addItem('− Restar', -1)
            selector.setCurrentIndex(selector.findData(sign))
            layout.addRow(label, selector)
            selectors.append(selector)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Aplicar')
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('Cancelar')
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        try:
            if dialog.exec():
                signs = tuple(selector.currentData() for selector in selectors)
                self.apply_definition(item, replace(item.block, input_signs=signs))
        finally:
            dialog.deleteLater()

    def apply_definition(self, item, definition):
        item.set_definition(definition)
        self.redraw_wires(definition.id)
        self.update_bounds()

    def edit_transfer(self, block):
        from .realization_transfer_input import TransferBlockDialog

        dialog = TransferBlockDialog(block, self.domain, self.owner, self)
        try:
            return dialog.definition() if dialog.exec() else None
        finally:
            dialog.deleteLater()

    def delete_selection(self):
        selected = self.scene.selectedItems()
        blocks = {item.block.id for item in selected if isinstance(item, BlockItem) and
                  item.block.kind not in ('input', 'output')}
        wires = {item.wire for item in selected if isinstance(item, WireItem)}
        wires.update(item.wire for item in self.wires.values()
                     if item.wire.source in blocks or item.wire.target in blocks)
        for wire in wires:
            self.scene.removeItem(self.wires.pop((wire.source, wire.target)))
        for source in {wire.source for wire in wires}:
            self.redraw_wires(source)
        for ident in blocks:
            self.scene.removeItem(self.blocks.pop(ident))
        self.start_connection(None)
        self.update_bounds()
        self.update_connection_state()

    def can_replace(self):
        return self.graph() == self.saved_graph or QMessageBox.question(
            self, 'Cambiar diagrama', '¿Descartar los cambios del diagrama actual?') == QMessageBox.StandardButton.Yes

    def new_diagram(self):
        if self.can_replace():
            self.saved_graph = RealizationGraph.empty(self.domain)
            self.set_graph(self.saved_graph)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Abrir diagrama editable', '', 'Diagrama SignalLab (*.json)')
        if not path:
            return
        try:
            source = Path(path)
            ensure_working_set(source.stat().st_size, bytes_per_sample=1, live_arrays=8)
            graph = RealizationGraph.from_document(json.loads(source.read_text(encoding='utf-8-sig')))
        except (OSError, ValueError, MemoryError) as exc:
            QMessageBox.warning(self, 'No se pudo abrir el diagrama', str(exc))
            return
        if self.can_replace():
            self.saved_graph = graph
            self.set_graph(graph)

    def save_file(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Guardar diagrama editable', 'realizacion.json', 'Diagrama SignalLab (*.json)')
        if not path:
            return
        graph = self.graph()
        try:
            write_json(path if Path(path).suffix else path + '.json', graph.to_document())
        except OSError as exc:
            QMessageBox.warning(self, 'No se pudo guardar el diagrama', str(exc))
        else:
            self.saved_graph = graph


class RealizationInput(QWidget):
    textChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.graphs = {}
        self.domain = 'analog'
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.button = QPushButton('Armar o cargar diagrama…')
        self.label = QLabel()
        self.label.setWordWrap(True)
        layout.addWidget(self.button)
        layout.addWidget(self.label)
        self.label.hide()

    @property
    def graph(self):
        return self.graphs.get(self.domain)

    def set_domain(self, domain):
        self.domain = domain
        graph = self.graph
        self.label.setText(f'{len(graph.blocks)} bloques · {len(graph.wires)} conexiones' if graph else '')
        self.label.setVisible(graph is not None)
        self.button.setText('Editar o cargar diagrama…' if graph else 'Armar o cargar diagrama…')
        self.textChanged.emit()

    def set_graph(self, graph):
        self.graphs[graph.domain] = graph
        self.set_domain(graph.domain)

    def text(self):
        graph = self.graph
        if graph is not None:
            return tuple((block.id, block.kind, block.gain, block.formula, block.sample_period_s)
                         for block in graph.blocks), graph.wires
        return None
