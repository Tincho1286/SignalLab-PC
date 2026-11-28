"""History browser with typed records and navigation through calculation links."""

from collections import defaultdict
from datetime import datetime
import html

from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMenu, QPushButton, QSizePolicy, QToolButton, QVBoxLayout, QWidget,
)
from .active_stack import ActiveTabs
from .catalog_delegate import DETAIL, TARGET, DetailListDelegate
from .design import icon
from .report_view import ReportView
from .result_summary import number, operation_label
from .result_table import ResultTable
from .result_toolbar import ResultActionBar
from .theme_tokens import COLORS
from .tool_workspace import ToolWorkspace
from .wrapping_row import WrappingRow


RESULT_TYPES = {
    'signal': ('Señal', 'wave', 'green'),
    'system': ('Sistema', 'blocks', 'blue'),
    'state_space': ('Espacio de estados', 'states', 'cyan'),
    'calculation': ('Cálculo', 'table', 'amber'),
    'expression': ('Expresión', 'math', 'purple'),
}
SPECTRAL_KINDS = {'dft_bins', 'harmonics', 'spectrum', 'density', 'frequency_values',
                  'frequency_response', 'spectral_lines', 'spectral_measurement','z_samples'}
SIGNAL_KINDS = {
    'dft_bins': 'Coeficientes DFT', 'harmonics': 'Armónicos', 'spectrum': 'Espectro',
    'density': 'Densidad espectral', 'frequency_values': 'Datos de frecuencia',
    'frequency_response': 'Respuesta en frecuencia', 'spectral_lines': 'Líneas espectrales',
    'spectral_measurement': 'Medición espectral', 'z_samples':'Contorno de Chirp-Z',
}
RECORD_KIND = Qt.ItemDataRole.UserRole + 2


def record_description(record, info, *, compact=False):
    if record['kind'] == 'signal':
        label = SIGNAL_KINDS.get(info.get('data_kind'))
        if label is None:
            label = 'Secuencia discreta' if info['domain'] == 'discrete' else 'Señal continua'
        origin = info['origin']
        count = info['count']
        if info['domain'] == 'discrete':
            axis = 'k' if info.get('data_kind') in ('dft_bins', 'harmonics') else 'n'
            origin = int(origin)
            end = origin + count - 1
            span = f'{axis} {origin}…{end}'
        else:
            end = origin + (count - 1) * info['step']
            start_text, end_text = (format(value, '.4g') for value in (origin, end)) if compact else (number(origin), number(end))
            if origin != end and start_text == end_text:
                start_text, end_text = repr(float(origin)), repr(float(end))
            span = f"{start_text}…{end_text} {info['units']}".rstrip()
        return label, f'{count} valores · {span}'
    if record['kind'] == 'system':
        return ('Sistema H(z)' if info['domain'] == 'digital' else 'Sistema H(s)'), ''
    if record['kind'] == 'state_space':
        return ('Estados discretos' if info['domain'] == 'discrete' else 'Estados continuos'), ''
    if info.get('data_kind')=='rf_network':
        return 'Red RF',f"{info['parameters']} · {info['ports']} puertos · {info['count']} frecuencias"
    if info.get('expression'):
        variable = info.get('variable')
        return 'Expresión', f'Variable {variable}' if variable else ''
    return 'Cálculo', ''


def record_timestamp(record):
    try:
        stamp = datetime.fromisoformat(record.get('created', '')).astimezone()
    except (TypeError, ValueError, OSError, OverflowError):
        return ''
    return stamp.strftime('%d/%m/%Y · %H:%M:%S')


class ResultList(QListWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName('savedResults')
        self.setAccessibleName('Resultados guardados')
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMouseTracking(True)
        self.setItemDelegate(DetailListDelegate(self))
        self.setMinimumHeight(132)
        self.icons = {}

    def add_record(self, record, kind, detail, tooltip):
        entry = QListWidgetItem(self.kind_icon(kind), record['title'])
        entry.setData(TARGET, record['id'])
        entry.setData(DETAIL, detail)
        entry.setData(RECORD_KIND, kind)
        entry.setData(Qt.ItemDataRole.AccessibleDescriptionRole, detail)
        entry.setToolTip(tooltip)
        self.addItem(entry)

    def kind_icon(self, kind):
        if kind not in self.icons:
            _, symbol, color = RESULT_TYPES[kind]
            self.icons[kind] = icon(symbol, COLORS[color])
        return self.icons[kind]

    def refresh_icons(self):
        self.icons.clear()
        for index in range(self.count()):
            item = self.item(index)
            item.setIcon(self.kind_icon(item.data(RECORD_KIND)))


class ResultsBrowser(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window_owner = window
        window.result_browser = self
        self.records = []
        self.by_id = {}
        self.record_info = {}
        self.dependents = {}
        self.revealed_id = None
        self.trail = []
        self.active_record = None
        self.active_value = None
        self.project = None
        self.link_ids = []
        self.signal_plot = None
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        selection = QWidget()
        left = QVBoxLayout(selection)
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(8)
        window.result_search = QLineEdit()
        window.result_search.setObjectName('resultHistorySearch')
        window.result_search.setAccessibleName('Buscar resultados')
        window.result_search.setPlaceholderText('Buscar nombre, operación o dominio…')
        window.result_search.addAction(icon('search'), QLineEdit.ActionPosition.LeadingPosition)
        window.result_search.setClearButtonEnabled(True)
        left.addWidget(window.result_search)
        window.result_kind = QComboBox()
        window.result_kind.setAccessibleName('Tipo de resultado')
        window.result_kind.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        for label, kind in [('Todos los tipos', None), ('Señales', 'signal'), ('Espectros y respuestas', 'spectral'), ('Sistemas', 'system'),
                            ('Modelos de estados', 'state_space'), ('Expresiones', 'expression'),
                            ('Cálculos e informes', 'calculation')]:
            window.result_kind.addItem(label, kind)
        left.addWidget(window.result_kind)
        window.include_inputs = QCheckBox('Mostrar también las entradas')
        left.addWidget(window.include_inputs)

        commands = WrappingRow()
        from .result_comparison import open_comparison
        compare = QPushButton(icon('chart'), 'Comparar…')
        compare.setAccessibleName('Comparar resultados')
        compare.clicked.connect(lambda: open_comparison(window))
        commands.flow.addWidget(compare)
        sessions = QToolButton()
        sessions.setObjectName('resultHistoryMenu')
        sessions.setText('Sesión')
        sessions.setIcon(icon('folder'))
        sessions.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        sessions.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.session_menu = QMenu(sessions)
        populate = getattr(window, 'populate_session_menu', None)
        if populate is None:
            self.session_menu.addAction('Guardar resultados…', window.save_project)
            self.session_menu.addAction('Incorporar resultados…', window.import_project)
        else:
            populate(self.session_menu)
        sessions.setMenu(self.session_menu)
        commands.flow.addWidget(sessions)
        left.addWidget(commands)
        window.result_count = QLabel()
        window.result_count.setObjectName('muted')
        left.addWidget(window.result_count)
        window.project_list = ResultList()
        left.addWidget(window.project_list, 1)

        detail = QWidget()
        right = QVBoxLayout(detail)
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(8)
        self.actions = ResultActionBar()
        right.addWidget(self.actions)
        window.view_selection = QPushButton('Abrir resultado')
        window.view_selection.setEnabled(False)
        window.view_selection.clicked.connect(self.open_detail)
        self.actions.add_action(window.view_selection, 'graph')
        window.reuse_selection = QPushButton('Usar resultado en…')
        window.reuse_selection.setEnabled(False)
        window.reuse_menu = QMenu(window.reuse_selection)
        window.reuse_selection.setMenu(window.reuse_menu)
        window.reuse_menu.aboutToShow.connect(window.prepare_selected_reuse)
        self.actions.add_action(window.reuse_selection, 'reuse')
        window.cas_selection = QPushButton('Enviar a CAS')
        window.cas_selection.setEnabled(False)
        window.cas_selection.clicked.connect(self.send_cas)
        self.actions.add_action(window.cas_selection, 'cas')
        window.export_selection_button = QPushButton('Exportar resultado…')
        window.export_selection_button.clicked.connect(window.export_selected)
        self.actions.add_action(window.export_selection_button, 'export')

        self.selected_title = QLabel()
        self.selected_title.setObjectName('resultHistoryTitle')
        self.selected_title.setTextFormat(Qt.TextFormat.PlainText)
        self.selected_title.setWordWrap(True)
        right.addWidget(self.selected_title)
        self.provenance = WrappingRow()
        self.origin_tool = QPushButton(icon('blocks'), 'Abrir herramienta')
        self.origin_tool.clicked.connect(self.open_tool)
        self.provenance.flow.addWidget(self.origin_tool)
        self.back_link = QPushButton(icon('back'), 'Volver al resultado anterior')
        self.back_link.clicked.connect(self.follow_back)
        self.provenance.flow.addWidget(self.back_link)
        right.addWidget(self.provenance)
        window.result_origin = QLabel()
        window.result_origin.setWordWrap(True)
        window.result_origin.setTextFormat(Qt.TextFormat.PlainText)
        window.result_origin.setObjectName('muted')
        right.addWidget(window.result_origin)
        self.detail_tabs = ActiveTabs()
        self.detail_tabs.setObjectName('historyDetails')
        window.project_details = ReportView()
        window.project_details.setReadOnly(True)
        window.project_details.setMinimumHeight(145)
        self.report_index = self.detail_tabs.addTab(window.project_details, 'Informe')
        self.values = ResultTable()
        self.values.link_figure(prepare=self.prepare_signal_plot, reveal=self.reveal_values)
        self.values_index = self.detail_tabs.addTab(self.values, 'Valores')
        self.links = ReportView()
        self.links.setAccessibleName('Datos de origen y cálculos vinculados')
        self.links.anchorClicked.connect(self.open_link)
        self.links_index = self.detail_tabs.addTab(self.links, 'Recorrido')
        right.addWidget(self.detail_tabs, 1)

        self.workspace = ToolWorkspace(selection, detail, self, titles=('Resultados', 'Detalle'))
        root.addWidget(self.workspace)
        self.tool_route = None
        window.result_search.textChanged.connect(self.apply_filters)
        window.result_kind.currentIndexChanged.connect(self.apply_filters)
        window.include_inputs.toggled.connect(self.apply_filters)
        window.result_search.returnPressed.connect(self.show_current_detail)
        window.project_list.currentRowChanged.connect(window.show_record)
        window.project_list.itemActivated.connect(lambda *_:self.show_current_detail())
        window.refresh_project()

    def refresh(self):
        window = self.window_owner
        if self.project is not window.project:
            self.project = window.project
            self.active_record = self.active_value = self.revealed_id = None
            self.trail.clear()
            if self.signal_plot is not None:self.signal_plot.clear()
        headers = list(reversed(window.project.headers()))
        self.records = headers
        self.by_id = {record['id']: record for record in headers}
        self.record_info = {record['id']: window.project.describe(record['id']) for record in headers}
        references = defaultdict(list)
        for record in headers:
            for parent in record['parents']:
                references[parent].append(record['id'])
        self.dependents = references
        self.trail = [(key, tab) for key, tab in self.trail if key in self.by_id]
        if self.revealed_id not in self.by_id:
            self.revealed_id = None
        self.filter_records()

    def apply_filters(self, *_):
        self.revealed_id = None
        self.filter_records()

    def filter_records(self, *, selected=None):
        from .tool_catalog import normalize
        window = self.window_owner
        row = window.project_list.currentRow()
        previous = getattr(window, 'visible_records', ())
        if selected is None and 0 <= row < len(previous):
            selected = previous[row]['id']
        query = normalize(window.result_search.text()).split()
        kind = window.result_kind.currentData()
        include_inputs = window.include_inputs.isChecked()
        visible = []
        matches = 0
        with QSignalBlocker(window.project_list):
            window.project_list.clear()
            for record in self.records:
                key = record['id']
                info = self.record_info[key]
                actual = 'expression' if info.get('expression') else record['kind']
                label, axis = record_description(record, info)
                operation = operation_label(record['operation'])
                tool = (record.get('tool') or {}).get('title') or ''
                text = normalize(' '.join((record['title'], operation, tool, label, axis)))
                compatible = kind is None or kind == actual or kind == 'spectral' and info.get('data_kind') in SPECTRAL_KINDS
                input_record = record['operation'].startswith(('Entrada:', 'Modelo de entrada:', 'Entrada de simulación'))
                matches_filters = compatible and (include_inputs or not input_record) and all(word in text for word in query)
                if not matches_filters and key != self.revealed_id:
                    continue
                matches += int(matches_filters)
                visible.append(record)
                _, short_axis = record_description(record, info, compact=True)
                summary = ' · '.join(part for part in (label, short_axis or operation) if part)
                stamp = record_timestamp(record)
                tooltip = '\n'.join(part for part in (record['title'], label, axis, operation, tool if tool != operation else '', stamp) if part)
                if not matches_filters:
                    summary = 'Vinculado · ' + summary
                    tooltip += '\nEl vínculo permite consultar este resultado desde el filtro actual.'
                window.project_list.add_record(record, actual, summary, tooltip)
            window.visible_records = visible
            index = next((i for i, record in enumerate(visible) if record['id'] == selected), 0 if visible else -1)
            window.project_list.setCurrentRow(index)
        count = '1 resultado' if matches == 1 else f'{matches} resultados'
        if matches != len(visible):
            count += ' · 1 vinculado'
        window.result_count.setText(count)
        window.show_record(index)

    def show_current_detail(self):
        if self.active_record is not None:
            self.workspace.show_results()

    def focus_record(self, key):
        if key not in self.by_id:
            return False
        self.revealed_id = key
        self.filter_records(selected=key)
        self.show_current_detail()
        return True

    def follow_record(self, key):
        current = self.active_record
        if current is not None and current['id'] != key and key in self.by_id:
            self.trail.append((current['id'], self.detail_tabs.currentIndex()))
            self.focus_record(key)

    def follow_back(self):
        if self.trail:
            key, tab = self.trail.pop()
            if self.focus_record(key) and self.detail_tabs.isTabVisible(tab):
                self.detail_tabs.setCurrentIndex(tab)

    def open_link(self, url):
        path = url.path()
        if url.scheme() == 'result' and path.isascii() and path.isdigit():
            index = int(path)
            if index < len(self.link_ids):
                self.follow_record(self.link_ids[index])

    def set_record(self, record):
        previous = self.active_record
        same = previous is not None and record is not None and previous['id'] == record['id']
        self.active_record = record
        if not same:
            self.active_value = None
            self.detail_tabs.setCurrentIndex(self.report_index)
            if self.signal_plot is not None and self.signal_plot.signal is not None:
                self.signal_plot.clear()
        self.tool_route = None
        self.provenance.setVisible(record is not None)
        self.window_owner.result_origin.setVisible(record is not None)
        self.selected_title.setVisible(record is not None)
        if not same:
            self.detail_tabs.setTabVisible(self.values_index, False)
        if record is None:
            self.detail_tabs.setTabVisible(self.links_index, False)
            self.values.set_signals(())
            return None

        from .cas_reference import CAS_ROUTE
        from .tool_catalog import normalized_key
        from .workspaces import ROUTES
        origin = record.get('tool') or {}
        route = origin.get('route')
        if isinstance(route, (list, tuple)) and len(route) >= 3:
            try:
                self.tool_route = CAS_ROUTE if tuple(route) == CAS_ROUTE else ROUTES.get(normalized_key(route))
            except TypeError:
                self.tool_route = None
        self.origin_tool.setVisible(self.tool_route is not None)
        stamp = record_timestamp(record)
        operation = operation_label(record['operation'])
        header = ' · '.join(dict.fromkeys(part for part in (operation, origin.get('title'), stamp) if part))
        self.selected_title.setText(record['title'])
        self.window_owner.result_origin.setText(header)

        parents = record['parents']
        self.back_link.setVisible(bool(self.trail))
        self.provenance.setVisible(not self.origin_tool.isHidden() or bool(self.trail))
        outputs = self.dependents.get(record['id'], ())
        self.detail_tabs.setTabVisible(self.links_index, bool(parents or outputs))
        if parents or outputs:
            self.set_links(parents, outputs)
        return self.active_value

    def set_value(self, value):
        from .model import Signal
        if self.active_value is value:
            return
        self.active_value = value
        signal = isinstance(value, Signal)
        self.window_owner.view_selection.setText('Abrir gráfico' if signal else 'Ampliar informe')
        self.detail_tabs.setTabVisible(self.values_index, signal)
        self.values.set_signals((value,) if signal else ())

    def open_detail(self):
        from .model import Signal
        if isinstance(self.active_value, Signal):
            self.prepare_signal_plot()
            self.signal_plot.open()
        elif self.active_record is not None:
            self.window_owner.open_selected_signal()

    def prepare_signal_plot(self):
        from .model import Signal
        if not isinstance(self.active_value, Signal):
            return None
        if self.signal_plot is None:
            from .saved_signal_plot import SavedSignalPlot
            self.signal_plot = SavedSignalPlot(self, self.values)
        self.signal_plot.set_signal(self.active_value, self.active_record['title'])
        return self.signal_plot.canvas

    def reveal_values(self):
        self.window_owner.show_menu('Proyecto')
        self.workspace.show_results()

    def set_links(self, parents, outputs):
        markup = []
        self.link_ids = []
        for heading, keys, empty in (('Datos de origen', parents, 'Este registro no tiene datos de origen vinculados.'),
                                     ('Usado en', outputs, 'Todavía no hay otros resultados vinculados.')):
            markup.append(f'<h2>{heading}</h2>')
            if not keys:
                markup.append(f'<p>{empty}</p>')
            for key in keys:
                record = self.by_id.get(key)
                if record is None:
                    continue
                title = html.escape(record['title'])
                operation = html.escape(operation_label(record['operation']))
                label, axis = record_description(record, self.record_info[key])
                detail = html.escape(' · '.join(part for part in (label, operation, axis) if part))
                href = f'result:{len(self.link_ids)}'
                self.link_ids.append(key)
                markup.append(f'<p><b><a href="{href}">{title}</a></b><br>{detail}</p>')
        self.links.setHtml(''.join(markup))
        self.links._raw = self.links.document().toPlainText()

    def open_tool(self):
        if self.tool_route is not None:
            self.window_owner.open_tool(self.tool_route)

    def send_cas(self):
        window = self.window_owner
        index = window.project_list.currentRow()
        if 0 <= index < len(window.visible_records):
            from .cas_transfer import send_to_cas
            send_to_cas(window, window.visible_records[index]['id'])
