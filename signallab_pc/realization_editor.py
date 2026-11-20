"""Visual input for continuous and discrete realizations."""

from dataclasses import replace
import json
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPainterPathStroker, QPen
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QGraphicsItem, QGraphicsPathItem,
    QGraphicsRectItem, QGraphicsScene, QGraphicsSimpleTextItem, QGraphicsView,
    QInputDialog, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from .atomic_file import write_json
from .realization_diagram import DiagramView
from .realization_graph import BLOCK_NAMES, Block, RealizationGraph, Wire
from .resources import ensure_working_set
from .theme_tokens import COLORS as C
from .wrapping_row import WrappingRow


class BlockItem(QGraphicsRectItem):
    def __init__(self, block, domain, editor):
        bounds={'sum':QRectF(-23,-23,46,46), 'input':QRectF(-34,-16,68,32), 'output':QRectF(-34,-16,68,32)}
        super().__init__(bounds.get(block.kind,QRectF(-60,-23,120,46)))
        self.block = block
        self.editor = editor
        self.variable = 'z' if domain == 'digital' else 's'
        self.setPos(block.x, block.y)
        color = {'memory': 'green', 'gain': 'blue', 'transfer': 'blue', 'sum': 'amber'}.get(block.kind, 'muted')
        self.setPen(QPen(QColor(C[color]), 1.5))
        self.setBrush(QColor(C['panel']))
        self.setZValue(1)
        flags = QGraphicsItem.GraphicsItemFlag
        self.setFlags(flags.ItemIsSelectable | flags.ItemIsMovable | flags.ItemSendsGeometryChanges)
        self.label = QGraphicsSimpleTextItem(self)
        self.label.setBrush(QColor(C['text']))
        if block.kind in ('gain', 'transfer'):
            self.set_definition(block)
        else:
            names = {'input': 'x[n]' if domain=='digital' else 'x(t)',
                     'output': 'y[n]' if domain=='digital' else 'y(t)', 'sum': '',
                     'memory': 'Retardo z⁻¹' if domain == 'digital' else 'Integrador 1/s'}
            self.set_label(names[block.kind], BLOCK_NAMES[block.kind])

    def set_label(self, text, tooltip):
        self.label.setText(text)
        bounds = self.label.boundingRect()
        self.label.setPos(-bounds.width() / 2, -bounds.height() / 2)
        self.setToolTip(f'Bloque {self.block.id} · {tooltip}')

    def set_definition(self, block):
        self.block = block
        if block.kind == 'transfer':
            text = f'H{block.id}({self.variable}) = {block.formula}'
            tooltip = text
        else:
            text = block.gain
            tooltip = 'Ganancia ' + block.gain
        display = self.editor.fontMetrics().elidedText(text, Qt.TextElideMode.ElideRight, 68 if block.kind=='gain' else 108)
        self.set_label(display, tooltip)

    def gain_direction(self):
        for wire,item in self.editor.wires.items():
            if wire.source==self.block.id and item.target is not self:
                return -1 if item.target.x()<self.x() else 1
        return 1

    def edge(self, tangent):
        rect=self.rect()
        return QPointF(tangent.x()*rect.width()/2,tangent.y()*rect.height()/2)

    def paint(self,painter,option,widget=None):
        kind=self.block.kind
        if kind not in ('gain','sum','input','output'):
            super().paint(painter,option,widget)
            return
        painter.setPen(self.pen() if not self.isSelected() else QPen(QColor(C['green']),2.5))
        painter.setBrush(self.brush())
        if kind=='gain':
            direction=self.gain_direction()
            path=QPainterPath(QPointF(-direction*59,-22))
            path.lineTo(QPointF(direction*59,0));path.lineTo(QPointF(-direction*59,22));path.closeSubpath()
            painter.drawPath(path)
        elif kind=='sum':
            painter.drawEllipse(self.rect())
            incoming=[item for wire,item in self.editor.wires.items() if wire.target==self.block.id]
            painter.setPen(QColor(C['text']))
            for item in incoming:
                position=-item.incoming_direction*12
                painter.drawText(QRectF(position.x()-7,position.y()-7,14,14),Qt.AlignmentFlag.AlignCenter,
                                 '+' if item.wire.sign==1 else '−')
        elif self.isSelected():
            painter.drawRoundedRect(self.rect(),4,4)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged and self.scene() is not None:
            self.editor.redraw_wires(self.block.id)
        return super().itemChange(change, value)

    def definition(self):
        return replace(self.block, x=self.x(), y=self.y())


class WireItem(QGraphicsPathItem):
    def __init__(self, wire, source, target):
        super().__init__()
        self.wire = wire
        self.source = source
        self.target = target
        color = QColor(C['amber' if wire.sign < 0 else 'blue'])
        self.setPen(QPen(color, 1.8))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setToolTip(f'{wire.source} → {wire.target}' + (' · resta' if wire.sign < 0 else ''))
        self.minus = QGraphicsSimpleTextItem('−', self) if wire.sign < 0 else None
        if self.minus is not None:
            self.minus.setBrush(color)
        self.redraw()

    def shape(self):
        stroker = QPainterPathStroker()
        stroker.setWidth(10)
        return stroker.createStroke(self.path())

    def boundingRect(self):
        return super().boundingRect().adjusted(-5, -5, 5, 5)

    def redraw(self, opposite=False):
        source, target = self.source.pos(), self.target.pos()
        if self.source is self.target:
            start=source+self.source.edge(QPointF(1,0));end=source+self.target.edge(QPointF(0,-1))
            path = QPainterPath(start)
            path.cubicTo(source + QPointF(145, 0), source + QPointF(0, -100), end)
            tangent = QPointF(0, 1)
        else:
            dx, dy = target.x() - source.x(), target.y() - source.y()
            if abs(dx) >= 100 or abs(dy) < 30:
                tangent = QPointF(1 if dx >= 0 else -1, 0)
            else:
                tangent = QPointF(0, 1 if dy > 0 else -1)
            outgoing,incoming=tangent,tangent
            if self.source.block.kind in ('input','transfer','sum'):
                outgoing=QPointF(1,0)
            elif self.source.block.kind=='gain':
                outgoing=QPointF(self.source.gain_direction(),0)
            if self.target.block.kind in ('output','transfer'):
                incoming=QPointF(1,0)
            elif self.target.block.kind=='gain':
                incoming=QPointF(self.target.gain_direction(),0)
            elif self.target.block.kind=='sum' and dx<0:
                incoming=QPointF(0,-1 if dy<0 or (dy==0 and self.wire.sign<0) else 1)
            start,end=source+self.source.edge(outgoing),target-self.target.edge(incoming)
            path = QPainterPath(start)
            lead=18
            direction=outgoing.x() if outgoing.x() else outgoing.y()
            space=(end.x()-start.x()) if outgoing.x() else (end.y()-start.y())
            if outgoing==incoming and direction*space>0:lead=min(lead,direction*space/3)
            first,last=start+outgoing*lead,end-incoming*lead
            path.lineTo(first)
            if outgoing.x() and incoming.x():
                if outgoing.x()!=incoming.x():
                    middle=max(first.x(),last.x()) if outgoing.x()>0 else min(first.x(),last.x())
                else:
                    middle=(first.x()+last.x())/2
                lane=(35 if outgoing.x()>0 else -35) if opposite or (last.x()-first.x())*outgoing.x()<0 else 0
                path.lineTo(first.x(),first.y()+lane)
                path.lineTo(middle,first.y()+lane);path.lineTo(middle,last.y()+lane)
                path.lineTo(last.x(),last.y()+lane)
            elif outgoing.y() and incoming.y():
                middle=(first.y()+last.y())/2
                path.lineTo(first.x(),middle);path.lineTo(last.x(),middle)
            elif outgoing.x():
                path.lineTo(last.x(),first.y())
            else:
                path.lineTo(first.x(),last.y())
            path.lineTo(last);path.lineTo(end)
            tangent=incoming
        self.incoming_direction=tangent
        self.target.update()
        if self.minus is not None and self.target.block.kind!='sum':
            self.minus.setPos(path.pointAtPercent(.68) + QPointF(-6, -18))
        if self.minus is not None:self.minus.setVisible(self.target.block.kind!='sum')
        side = QPointF(-tangent.y(), tangent.x())
        path.moveTo(end - tangent * 10 + side * 5)
        path.lineTo(end)
        path.lineTo(end - tangent * 10 - side * 5)
        self.setPath(path)


class EditorView(DiagramView):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def block_at(self, position):
        item = self.itemAt(position.toPoint())
        while item is not None and not isinstance(item, BlockItem):
            item = item.parentItem()
        return item

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.editor.connection_sign is not None:
            item = self.block_at(event.position())
            if item is not None:
                self.editor.connect_block(item)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        block = self.block_at(event.position())
        if block is not None and block.block.kind in ('gain', 'transfer') and self.editor.connection_sign is None:
            self.editor.edit_block(block)
        else:
            super().mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.editor.update_bounds()


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
        layout = QVBoxLayout(self)

        file_row = WrappingRow()
        layout.addWidget(file_row)
        self._button(file_row, 'Nuevo', self.new_diagram)
        self._button(file_row, 'Abrir JSON…', self.open_file)
        self._button(file_row, 'Guardar JSON…', self.save_file)
        self._button(file_row, 'Ver todo', self.fit_diagram)
        tools = WrappingRow()
        layout.addWidget(tools)
        self.transfer_button = self._button(tools, '+ Transferencia', lambda: self.add_block('transfer'))
        self._button(tools, '+ Ganancia', lambda: self.add_block('gain'))
        self._button(tools, '+ Sumador', lambda: self.add_block('sum'))
        self.memory = self._button(tools, '', lambda: self.add_block('memory'))
        self.connect_button = self._button(tools, 'Conectar (+)', lambda: self.start_connection(1))
        self.subtract_button = self._button(tools, 'Restar (−)', lambda: self.start_connection(-1))
        for button in (self.connect_button, self.subtract_button):
            button.setCheckable(True)
        self.edit_button = self._button(tools, 'Editar bloque…', self.edit_selected_block)
        self.delete_button = self._button(tools, 'Quitar selección', self.delete_selection)

        self.hint = QLabel()
        self.hint.setWordWrap(True)
        layout.addWidget(self.hint)
        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QColor(C['report']))
        self.scene.selectionChanged.connect(self.update_selection)
        self.view = EditorView(self)
        self.view.setScene(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setAccessibleName('Diagrama de bloques de la realización')
        self.view.setToolTip('Ctrl + rueda cambia el zoom. Arrastrá un espacio vacío para recorrer el diagrama.')
        layout.addWidget(self.view, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('Cancelar')
        accept = buttons.addButton('Usar diagrama', QDialogButtonBox.ButtonRole.AcceptRole)
        accept.setObjectName('primary')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.set_graph(graph)

    @staticmethod
    def _button(row, text, action):
        button = QPushButton(text)
        button.setAutoDefault(False)
        button.clicked.connect(action)
        row.flow.addWidget(button)
        return button

    def showEvent(self, event):
        super().showEvent(event)
        self.fit_diagram()

    def set_graph(self, graph):
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
        self.memory.setText('+ Retardo' if graph.domain == 'digital' else '+ Integrador')
        self.start_connection(None)
        self.update_selection()
        self.fit_diagram()

    def graph(self):
        return RealizationGraph(self.domain, tuple(item.definition() for item in self.blocks.values()),
                                tuple(self.wires))

    def update_bounds(self):
        rect = self.scene.itemsBoundingRect().adjusted(-48, -48, 48, 48)
        self.scene.setSceneRect(rect.united(QRectF(-95, -170, 800, 385)))

    def fit_diagram(self):
        self.update_bounds()
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        if self.view.transform().m11() > 1:
            self.view.resetTransform()

    def add_block(self, kind):
        self.start_connection(None)
        ident = max(self.blocks) + 1
        positions = {(round(item.x()), round(item.y())) for item in self.blocks.values()}
        index = 0
        while (145 + index % 3 * 145, index // 3 * 85) in positions:
            index += 1
        block = Block(ident, kind, 145 + index % 3 * 145, index // 3 * 85)
        if kind == 'transfer':
            block = self.edit_transfer(block)
            if block is None:
                return
        item = BlockItem(block, self.domain, self)
        self.scene.addItem(item)
        self.blocks[ident] = item
        self.scene.clearSelection()
        item.setSelected(True)
        self.update_bounds()
        self.view.ensureVisible(item)
        if kind == 'gain':
            self.edit_block(item)

    def start_connection(self, sign):
        self.connection_sign = None if sign == self.connection_sign else sign
        self.connection_source = None
        self.connect_button.setChecked(self.connection_sign == 1)
        self.subtract_button.setChecked(self.connection_sign == -1)
        if self.connection_sign is not None:
            self.hint.setText('Seleccioná el bloque de origen y luego el de destino.')
        else:
            domain = 'Discreto · H(z)' if self.domain == 'digital' else 'Continuo · H(s)'
            self.hint.setText(f'{domain} · Arrastrá los bloques para ubicarlos. Usá Conectar o Restar para unirlos.')

    def connect_block(self, item):
        if self.connection_source is None:
            if item.block.kind == 'output':
                self.hint.setText('Elegí un origen. La salida y sólo recibe conexiones.')
                return
            self.connection_source = item.block.id
            self.scene.clearSelection()
            item.setSelected(True)
            self.hint.setText(f'Origen {item.block.id} seleccionado. Elegí el bloque de destino.')
            return
        wire = Wire(self.connection_source, item.block.id, self.connection_sign)
        graph = self.graph()
        try:
            replace(graph, wires=graph.wires + (wire,)).connections()
        except ValueError as exc:
            self.hint.setText(str(exc))
            return
        self.add_wire(wire)
        self.start_connection(None)
        self.update_bounds()

    def add_wire(self, wire):
        item = WireItem(wire, self.blocks[wire.source], self.blocks[wire.target])
        self.wires[wire] = item
        self.scene.addItem(item)
        self.redraw_wires(wire.source)

    def reverse_wire(self, wire):
        if wire.source != wire.target:
            return self.wires.get(Wire(wire.target, wire.source)) or self.wires.get(Wire(wire.target, wire.source, -1))
        return None

    def redraw_wires(self, ident):
        affected={ident}
        affected.update(wire.source for wire,item in self.wires.items()
                        if wire.target==ident and item.source.block.kind=='gain')
        for wire, item in self.wires.items():
            if wire.source in affected or wire.target in affected:
                item.redraw(self.reverse_wire(wire) is not None)
        for key in affected:self.blocks[key].update()

    def update_selection(self):
        selected = self.scene.selectedItems()
        self.edit_button.setEnabled(any(isinstance(item, BlockItem) and item.block.kind in ('gain', 'transfer') for item in selected))
        self.delete_button.setEnabled(any(isinstance(item, WireItem) or
                                          isinstance(item, BlockItem) and item.block.kind not in ('input', 'output')
                                          for item in selected))

    def edit_selected_block(self):
        for item in self.scene.selectedItems():
            if isinstance(item, BlockItem) and item.block.kind in ('gain', 'transfer'):
                self.edit_block(item)
                break

    def edit_block(self, item):
        block = item.block
        if block.kind == 'transfer':
            definition = self.edit_transfer(block)
            if definition is not None:
                item.set_definition(definition)
        else:
            text, accepted = QInputDialog.getText(self, 'Ganancia', 'Valor exacto (por ejemplo, 1/3 o pi):', text=block.gain)
            if accepted and text.strip():
                item.set_definition(replace(block, gain=text.strip()))

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
        wires.update(wire for wire in self.wires if wire.source in blocks or wire.target in blocks)
        for wire in wires:
            self.scene.removeItem(self.wires.pop(wire))
        for source in {wire.source for wire in wires}:
            self.redraw_wires(source)
        for ident in blocks:
            self.scene.removeItem(self.blocks.pop(ident))
        self.start_connection(None)
        self.update_bounds()

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
