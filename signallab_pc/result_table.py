"""Paged, coordinate-aware inspection of sampled results."""

import numpy as np
from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSize, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QComboBox, QHeaderView, QLabel, QLineEdit,
    QMenu, QPushButton, QScrollArea, QTableView, QTabWidget, QToolButton, QVBoxLayout, QWidget,
)

from .distributions import dirac_terms
from .design import icon
from .numeric_input import integer_field, real_field
from .uniform_axis import sample_coordinate, sample_index
from .validation import invalid
from .wrapping_row import WrappingRow


class ResultRows(QAbstractTableModel):
    page_size = 500

    def __init__(self, parent=None):
        super().__init__(parent)
        self.source = None
        self.offset = 0

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid() or self.source is None:
            return 0
        return min(self.page_size, self.source.values.size - self.offset)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else 5

    def coordinate(self, index):
        return sample_coordinate(self.source, index)

    def axis_text(self, index, *, exact=False):
        coordinate = self.coordinate(index)
        if self.source.domain == 'discrete':
            return str(coordinate)
        if exact:
            return format(coordinate, '.17g')
        short = format(coordinate, '.12g')
        for neighbor in (index - 1, index + 1):
            if 0 <= neighbor < self.source.values.size:
                if format(self.coordinate(neighbor), '.12g') == short:
                    return repr(float(coordinate))
        return short

    def axis_label(self):
        source = self.source
        if source is None:
            return 'Coordenada'
        units = source.units
        if units in ('k', 'bin k'):
            return 'Índice k'
        if units == 'n':
            return 'Índice n'
        if units == 's' and source.domain == 'continuous':
            return 'Tiempo (s)'
        if units in ('Hz', 'rad/s', 'rad/muestra'):
            symbol = {'Hz': 'Frecuencia', 'rad/s': 'Ω', 'rad/muestra': 'ω'}[units]
            return f'{symbol} ({units})'
        return f'Eje ({units})' if units else 'Coordenada'

    def value(self, row, column, *, exact=True):
        index = self.offset + row
        if column == 0:
            return self.axis_text(index, exact=exact)
        value = self.source.values[index]
        if not np.isfinite(value):
            return 'No definido' if exact else 'N/D'
        if column == 1:
            component = value.real
        elif column == 2:
            component = value.imag
        elif column == 3:
            component = abs(value)
        elif value == 0:
            return 'No definida' if exact else 'N/D'
        else:
            component = np.angle(value)
        return format(component, '.17g' if exact else '.12g')

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or self.source is None:
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return self.value(index.row(), index.column(), exact=False)
        if role == Qt.ItemDataRole.ToolTipRole:
            value = self.value(index.row(), index.column())
            return 'Fase indefinida para módulo cero.' if value == 'No definida' else value
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.ToolTipRole and orientation == Qt.Orientation.Horizontal and section == 4:
            return 'Fase principal en radianes. N/D indica módulo cero o valor indefinido.'
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Vertical:
            return str(self.offset + section + 1)
        return (self.axis_label(), 'Real', 'Imaginaria', 'Módulo', 'Fase (rad)')[section]

    def set_source(self, source):
        self.beginResetModel()
        self.source = source
        self.offset = 0
        self.endResetModel()

    def set_offset(self, offset):
        if self.offset != offset:
            self.beginResetModel()
            self.offset = offset
            self.endResetModel()


class ResultTable(QWidget):
    def __init__(self):
        super().__init__()
        self.signals = []
        self.locations = {}
        self.signal_index = -1
        self.canvas = None
        self.prepare_figure = None
        self.reveal_values = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(7, 7, 7, 7)

        self.selector = QComboBox()
        self.selector.setAccessibleName('Serie mostrada en la tabla')
        self.selector.setToolTip('Elegí qué serie consultar.')
        self.selector.currentIndexChanged.connect(self.select)
        layout.addWidget(self.selector)

        controls = WrappingRow(self)
        self.search_mode = QComboBox()
        self.search_mode.addItems(['Coordenada', 'Fila'])
        self.search_mode.setAccessibleName('Forma de buscar en la tabla')
        self.search_mode.setToolTip('Buscá por coordenada del eje o por número de fila.')
        self.search_mode.setProperty('fitComboText', True)
        self.position = QLineEdit()
        self.position.setMaximumWidth(160)
        jump = QPushButton('Ir')
        jump.setToolTip('Selecciona el dato que corresponde a la posición ingresada.')
        self.copy = QPushButton('Copiar')
        self.copy.setObjectName('resultTableCopy')
        self.copy_menu = QMenu(self.copy)
        self.copy_selection_action = self.copy_menu.addAction('Copiar selección', self.copy_selection)
        self.copy_rows_action = self.copy_menu.addAction('Copiar filas completas', self.copy_rows)
        self.copy_menu.addAction('Copiar página completa', self.copy_page)
        self.copy_menu.aboutToShow.connect(self.update_copy_actions)
        self.copy.setMenu(self.copy_menu)
        self.columns = QComboBox()
        self.columns.addItems(['Automáticas', 'Real e imaginaria', 'Módulo y fase', 'Todas'])
        self.columns.setAccessibleName('Columnas visibles')
        self.columns.setToolTip('Elegí qué columnas mostrar.')
        self.columns.setProperty('fitComboText', True)
        for widget in (self.search_mode, self.position, jump, self.columns, self.copy):
            controls.flow.addWidget(widget)
        layout.addWidget(controls)

        self.coordinate_note = QLabel()
        self.coordinate_note.setWordWrap(True)
        self.coordinate_note.setTextFormat(Qt.TextFormat.PlainText)
        self.coordinate_note.setVisible(False)

        self.model = ResultRows(self)
        self.table = QTableView()
        self.table.setObjectName('resultValues')
        self.table.setAccessibleName('Valores calculados')
        self.table.setModel(self.model)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        header = self.table.horizontalHeader()
        header.setMinimumSectionSize(90)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(max(24, self.table.fontMetrics().height() + 9))
        pager = WrappingRow(self)
        self.previous = QToolButton()
        self.previous.setIcon(icon('back'))
        self.previous.setToolTip('Página anterior')
        self.previous.setAccessibleName(self.previous.toolTip())
        self.status = QLabel()
        self.status.setMinimumHeight(self.previous.sizeHint().height())
        self.next = QToolButton()
        self.next.setIcon(icon('forward'))
        self.next.setToolTip('Página siguiente')
        self.next.setAccessibleName(self.next.toolTip())
        for button in (self.previous, self.next):
            button.setObjectName('resultPageStep')
            button.setIconSize(QSize(15, 15))
            button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.locate_plot = QPushButton('Ver en gráfico')
        self.locate_plot.setToolTip('Abre la figura y marca la muestra seleccionada.')
        self.locate_plot.hide()
        for widget in (self.previous, self.status, self.next, self.locate_plot):
            pager.flow.addWidget(widget)
        layout.addWidget(pager)
        layout.addWidget(self.coordinate_note)
        layout.addWidget(self.table, 1)

        self.note = QLabel()
        self.note.setWordWrap(True)
        layout.addWidget(self.note)

        self.search_mode.currentIndexChanged.connect(self.update_search_hint)
        self.position.textChanged.connect(lambda _: self.show_message(''))
        self.position.returnPressed.connect(self.jump)
        jump.clicked.connect(self.jump)
        self.columns.currentIndexChanged.connect(self.update_columns)
        self.previous.clicked.connect(lambda: self.change(-1))
        self.next.clicked.connect(lambda: self.change(1))
        self.locate_plot.clicked.connect(self.show_in_figure)
        self.table.selectionModel().currentChanged.connect(self.update_plot_button)
        self.copy_shortcut = QShortcut(QKeySequence.StandardKey.Copy, self.table)
        self.copy_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.copy_shortcut.activated.connect(self.copy_selection)
        self.controls = controls
        self.select(-1)

    def set_signals(self, signals, *, preserve_position=False):
        signals = list(signals)
        same_values = preserve_position and len(signals) == len(self.signals) and all(
            new.values is old.values for new, old in zip(signals, self.signals)
        )
        if same_values:
            self.remember_position()
            index = self.signal_index
        else:
            self.locations.clear()
            index = 0 if signals else -1
        self.signals = signals
        self.signal_index = -1
        self.selector.blockSignals(True)
        self.selector.clear()
        counts = {}
        for signal in signals:
            counts[signal.name] = counts.get(signal.name, 0) + 1
            suffix = f' · {counts[signal.name]}' if counts[signal.name] > 1 else ''
            self.selector.addItem(signal.name + suffix)
        self.selector.setCurrentIndex(index)
        self.selector.blockSignals(False)
        self.selector.setVisible(len(signals) > 1)
        self.select(index)

    def remember_position(self):
        if self.signal_index >= 0:
            current = self.table.currentIndex()
            row = self.model.offset + current.row() if current.isValid() else None
            self.locations[self.signal_index] = (self.model.offset, row, current.column())

    def select(self, index):
        self.remember_position()
        self.signal_index = index
        source = self.signals[index] if 0 <= index < len(self.signals) else None
        self.model.set_source(source)
        if source is not None and source.domain == 'discrete':
            count = source.values.size
            wide_index = bool(count and max(len(str(self.model.coordinate(i))) for i in (0, count - 1)) >= 14)
        else:
            wide_index = False
        resize = QHeaderView.ResizeMode.ResizeToContents if wide_index else QHeaderView.ResizeMode.Stretch
        self.table.horizontalHeader().setSectionResizeMode(0, resize)
        self.position.clear()
        self.update_search_hint()
        self.update_columns()
        if source is not None and index in self.locations:
            offset, row, column = self.locations[index]
            self.model.set_offset(offset)
            if row is not None:
                self.select_cell(row, column)
        self.update_status()
        self.show_message('')
        terms = dirac_terms(source) if source is not None else []
        self.note.setText(f'Parte ordinaria. Consultá los impulsos Dirac ({len(terms)}) en el informe y en el gráfico.' if terms else '')
        self.note.setVisible(bool(terms))

    def update_status(self):
        source = self.model.source
        count = source.values.size if source is not None else 0
        start = self.model.offset
        end = start + self.model.rowCount()
        self.controls.setEnabled(bool(count))
        self.previous.setEnabled(start > 0)
        self.next.setEnabled(end < count)
        self.status.setText(f'Filas {start + 1}–{end} de {count}' if count else 'Sin datos')
        self.update_plot_button()

    def link_figure(self, canvas=None, *, prepare=None, reveal=None):
        self.canvas = canvas
        self.prepare_figure = prepare
        self.reveal_values = reveal
        if canvas is not None:
            canvas._signallab_sample_table = self
        self.update_plot_button()

    def update_plot_button(self, *_):
        source = self.model.source
        available = (self.canvas is not None or self.prepare_figure is not None) and source is not None and not source.metadata.get('lines_only')
        self.locate_plot.setVisible(available)
        self.locate_plot.setEnabled(available and self.table.currentIndex().isValid())

    def show_in_figure(self):
        current = self.table.currentIndex()
        if not current.isValid() or not self.locate_plot.isEnabled():
            return
        from .plot_view import ensure_figure_window, enlarge_plot
        canvas = self.prepare_figure() if self.prepare_figure is not None else self.canvas
        if canvas is None:
            return
        canvas._signallab_sample_table = self
        ensure_figure_window(canvas)
        probe = getattr(canvas, '_signallab_probe', None)
        if probe is not None:
            canvas.draw()
            if probe.focus_sample(self.model.source, self.model.offset + current.row()):
                enlarge_plot(canvas, self)
                return
        self.show_message('La figura actual no contiene esta serie de valores.')

    def series_index(self, source):
        for index, signal in enumerate(self.signals):
            if signal is source:
                return index
        for index, signal in enumerate(self.signals):
            if signal.values is source.values and (signal.origin, signal.step, signal.units) == (source.origin, source.step, source.units):
                return index
        return -1

    def show_plot_sample(self, source, row, component):
        index = self.series_index(source)
        if index < 0 or not 0 <= row < source.values.size:
            return False
        if self.reveal_values is not None:
            self.reveal_values()
        owner = self.window()
        tabs, scroll = [], None
        node = self.parentWidget()
        while node is not None:
            if isinstance(node, QTabWidget):
                for i in range(node.count()):
                    if node.widget(i) is self or node.widget(i).isAncestorOf(self):
                        tabs.append((node, i))
                        break
            if isinstance(node, QScrollArea):
                scroll = node
            route = getattr(node, 'tool_item', None)
            if route:
                if not node.isVisible() and hasattr(owner, 'open_tool'):
                    owner.open_tool(route)
                workspace = getattr(node, 'workspace', None)
                if workspace is not None:
                    workspace.show_results()
            node = node.parentWidget()
        for tab, page in reversed(tabs):
            tab.setCurrentIndex(page)
        self.selector.setCurrentIndex(index)
        column = {'real': 1, 'imag': 2, 'magnitude': 3, 'phase': 4}.get(component, 0)
        self.select_cell(row, column)
        self.update_status()
        query = str(row + 1) if self.search_mode.currentIndex() == 1 else self.model.axis_text(row, exact=True)
        self.position.setText(query)
        self.show_message(f'Fila {row + 1} · {self.model.axis_text(row)} · Desde el gráfico')
        if scroll is not None:
            scroll.ensureWidgetVisible(self.table, 0, 12)
        self.table.setFocus()
        return True

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_columns()

    def update_columns(self, *_):
        source = self.model.source
        mode = self.columns.currentIndex()
        if mode == 0:
            header = self.table.horizontalHeader()
            width = self.width() - 70  # Leave room for row numbers, margins and scroll bar.
            width_per_value = max(header.minimumSectionSize(), header.fontMetrics().horizontalAdvance('−1.234567e−100') + 18)
            axis_width = max(width_per_value, header.fontMetrics().horizontalAdvance(self.model.axis_label()) + 22)
            if width < axis_width + 4 * width_per_value:
                mode = 2 if source is not None and source.domain == 'frequency' else 1
        for column in (1, 2, 3, 4):
            hidden = (mode == 1 and column > 2) or (mode == 2 and column < 3)
            self.table.setColumnHidden(column, hidden)
        current = self.table.currentIndex()
        if current.isValid() and self.table.isColumnHidden(current.column()):
            self.table.setCurrentIndex(self.model.index(current.row(), 0))

    def change(self, direction):
        source = self.model.source
        offset = self.model.offset + direction * self.model.page_size
        if source is not None and 0 <= offset < source.values.size:
            self.model.set_offset(offset)
            self.table.scrollToTop()
            self.update_status()
            self.show_message('')

    def update_search_hint(self, *_):
        label = 'Número de fila' if self.search_mode.currentIndex() == 1 else self.model.axis_label()
        self.position.setAccessibleName(label)
        self.position.setPlaceholderText(label)
        self.position.setToolTip(
            'Posición del dato en la tabla, desde 1.' if self.search_mode.currentIndex() == 1
            else 'Ingresá una coordenada del eje. Para un eje real podés usar expresiones como pi/4.'
        )
        self.show_message('')

    def show_message(self, message):
        self.coordinate_note.setText(message)
        self.coordinate_note.setVisible(bool(message))

    def select_cell(self, row, column=0):
        offset = (row // self.model.page_size) * self.model.page_size
        self.model.set_offset(offset)
        if self.table.isColumnHidden(column):
            column = 0
        index = self.model.index(row - offset, column)
        self.table.clearSelection()
        self.table.setCurrentIndex(index)
        self.table.scrollTo(index, QAbstractItemView.ScrollHint.PositionAtCenter)

    def jump(self):
        source = self.model.source
        if source is None or not source.values.size:
            return
        count = source.values.size
        try:
            if self.search_mode.currentIndex() == 1:
                row = integer_field(self.position, minimum=1, maximum=count) - 1
                requested = None
            elif source.domain == 'discrete':
                coordinate = integer_field(
                    self.position, minimum=self.model.coordinate(0), maximum=self.model.coordinate(count - 1)
                )
                row = coordinate - self.model.coordinate(0)
                requested = None
            else:
                requested = real_field(self.position)
                first, last = self.model.coordinate(0), self.model.coordinate(count - 1)
                row = sample_index(source, requested)
                if row is None:
                    invalid(self.position, 'valor fuera del eje.',
                            f'Ingresá un valor entre {min(first, last):.17g} y {max(first, last):.17g}.')
        except ValueError as exc:
            self.show_message(str(exc))
            return
        self.select_cell(row)
        self.update_status()
        self.table.setFocus()
        axis = self.model.axis_text(row)
        units = f' {source.units}' if source.units and source.units not in ('n', 'k', 'bin k') else ''
        message = f'Fila {row + 1} · {axis}{units}'
        if requested is not None and requested != self.model.coordinate(row):
            difference = self.model.coordinate(row) - requested
            message += f' · Punto almacenado más cercano (Δ = {difference:.6g}{units})'
        self.show_message(message)

    def update_copy_actions(self):
        has_selection = bool(self.table.selectedIndexes())
        self.copy_selection_action.setEnabled(has_selection)
        self.copy_rows_action.setEnabled(has_selection)

    def copy_selection(self):
        selected = {(index.row(), index.column()) for index in self.table.selectedIndexes()}
        if not selected:
            return
        rows, columns = zip(*selected)
        visible = [column for column in range(min(columns), max(columns) + 1)
                   if not self.table.isColumnHidden(column)]
        lines = [
            '\t'.join(self.model.value(row, column) if (row, column) in selected else '' for column in visible)
            for row in range(min(rows), max(rows) + 1)
        ]
        QApplication.clipboard().setText('\n'.join(lines))
        self.show_message('Selección copiada con precisión completa.')

    def copy_rows(self):
        rows = sorted({index.row() for index in self.table.selectedIndexes()})
        if rows:
            self.copy_full_rows(rows, 'Filas copiadas con encabezados.')

    def copy_page(self):
        if self.model.rowCount():
            self.copy_full_rows(range(self.model.rowCount()), 'Página copiada con encabezados.')

    def copy_full_rows(self, rows, message):
        columns = range(self.model.columnCount())
        headings = '\t'.join(self.model.headerData(column, Qt.Orientation.Horizontal) for column in columns)
        values = ('\t'.join(self.model.value(row, column) for column in columns) for row in rows)
        QApplication.clipboard().setText('\n'.join([headings, *values]))
        self.show_message(message)
