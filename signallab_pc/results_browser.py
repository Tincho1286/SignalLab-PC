"""History browser with record details, origin and immediate input links."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMenu, QPushButton, QSizePolicy, QToolButton, QVBoxLayout, QWidget,
)
from .catalog_delegate import DETAIL, TARGET, DetailListDelegate
from .design import icon
from .report_view import ReportView
from .result_summary import operation_label
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
RECORD_KIND = Qt.ItemDataRole.UserRole + 2


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

    def add_record(self, record, kind):
        label = RESULT_TYPES[kind][0]
        detail = f"{label} · {operation_label(record['operation'])}"
        entry = QListWidgetItem(self.kind_icon(kind), record['title'])
        entry.setData(TARGET, record['id'])
        entry.setData(DETAIL, detail)
        entry.setData(RECORD_KIND, kind)
        entry.setData(Qt.ItemDataRole.AccessibleDescriptionRole, detail)
        entry.setToolTip(record['title'] + '\n' + detail)
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
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        selection = QWidget()
        left = QVBoxLayout(selection)
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(8)
        window.result_search = QLineEdit()
        window.result_search.setObjectName('resultHistorySearch')
        window.result_search.setAccessibleName('Buscar resultados')
        window.result_search.setPlaceholderText('Buscar por nombre u operación…')
        window.result_search.addAction(icon('search'), QLineEdit.ActionPosition.LeadingPosition)
        window.result_search.setClearButtonEnabled(True)
        left.addWidget(window.result_search)
        window.result_kind = QComboBox()
        window.result_kind.setAccessibleName('Tipo de resultado')
        window.result_kind.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        for label, kind in [('Todos los tipos', None), ('Señales', 'signal'), ('Sistemas', 'system'),
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
        window.view_selection.clicked.connect(window.open_selected_signal)
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

        self.provenance = WrappingRow()
        self.origin_tool = QPushButton(icon('blocks'), 'Abrir herramienta')
        self.origin_tool.clicked.connect(self.open_tool)
        self.provenance.flow.addWidget(self.origin_tool)
        self.inputs_button = QToolButton()
        self.inputs_button.setObjectName('resultHistoryMenu')
        self.inputs_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.inputs_menu = QMenu(self.inputs_button)
        self.inputs_button.setMenu(self.inputs_menu)
        self.provenance.flow.addWidget(self.inputs_button)
        right.addWidget(self.provenance)
        window.result_origin = QLabel()
        window.result_origin.setWordWrap(True)
        window.result_origin.setTextFormat(Qt.TextFormat.PlainText)
        window.result_origin.setObjectName('muted')
        right.addWidget(window.result_origin)
        window.project_details = ReportView()
        window.project_details.setReadOnly(True)
        window.project_details.setMinimumHeight(145)
        right.addWidget(window.project_details, 1)

        self.workspace = ToolWorkspace(selection, detail, self, titles=('Resultados', 'Detalle'))
        root.addWidget(self.workspace)
        self.tool_route = None
        window.result_search.textChanged.connect(window.refresh_project)
        window.result_kind.currentIndexChanged.connect(window.refresh_project)
        window.include_inputs.toggled.connect(window.refresh_project)
        window.project_list.currentRowChanged.connect(window.show_record)
        window.project_list.itemDoubleClicked.connect(lambda *_:window.open_selected_signal())
        window.refresh_project()

    def set_record(self, record, titles):
        self.tool_route = None
        self.inputs_menu.clear()
        self.provenance.setVisible(record is not None)
        self.window_owner.result_origin.setVisible(record is not None)
        if record is None:
            return

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
        self.window_owner.result_origin.setText(origin.get('title') or operation_label(record['operation']))

        focus = getattr(self.window_owner, 'focus_result', None)
        parents = record['parents']
        self.inputs_button.setVisible(bool(parents and focus))
        if focus:
            for key in parents:
                self.inputs_menu.addAction(titles.get(key, key), lambda checked=False, result=key: focus(result))
        self.inputs_button.setText(f'Entradas ({len(parents)})')
        self.provenance.setVisible(not self.origin_tool.isHidden() or not self.inputs_button.isHidden())

    def open_tool(self):
        if self.tool_route is not None:
            self.window_owner.open_tool(self.tool_route)

    def send_cas(self):
        window = self.window_owner
        index = window.project_list.currentRow()
        if 0 <= index < len(window.visible_records):
            from .cas_transfer import send_to_cas
            send_to_cas(window, window.visible_records[index]['id'])
