"""Open tools, documents and saved results from a single keyboard launcher."""
from dataclasses import dataclass

from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import (
    QDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout,
)

from .cas_reference import CAS_ROUTE, CAS_SEARCH
from .catalog_delegate import DETAIL, TARGET, DetailListDelegate
from .design import icon
from .result_summary import operation_label
from .theme_tokens import AREA_COLORS, COLORS
from .tool_catalog import AREA_BY_ID, BY_KEY, DETAILS_BY_KEY, ENTRIES, matching_variants, normalize, normalized_key
from .workspaces import ROUTES


@dataclass(frozen=True)
class Choice:
    target: tuple
    title: str
    detail: str
    symbol: str
    color: str
    keywords: str = ''

    def matches(self, query):
        text = normalize(' '.join((self.title, self.detail, self.keywords)))
        return all(word in text for word in query.split())


def tool_choice(key):
    entry = BY_KEY[key]
    _, area, _, symbol = AREA_BY_ID[entry['area']]
    detail = DETAILS_BY_KEY[key]
    return Choice(('tool', key), detail['title'], area + ' · ' + detail['summary'],
                  symbol, AREA_COLORS[entry['area']])


def commands():
    return [
        Choice(('command', 'cas'), 'Calculadora CAS', 'Álgebra y cálculo simbólico',
               'calculator', COLORS['purple'], CAS_SEARCH),
        Choice(('command', 'results'), 'Resultados', 'Abrir la biblioteca de la sesión',
               'table', COLORS['blue'], 'resultados guardados señales sistemas exportar'),
        Choice(('command', 'compare'), 'Comparar resultados', 'Superponer señales o respuestas compatibles',
               'chart', COLORS['cyan'], 'comparar comparar curvas superposición'),
        Choice(('command', 'library'), 'Biblioteca', 'Ayuda, teoría y funciones de las fórmulas',
               'book', COLORS['green'], 'libro biblioteca ayuda manual teoría'),
        Choice(('command', 'home'), 'Inicio', 'Ver todas las áreas de trabajo',
               'home', COLORS['accent'], 'inicio catálogo herramientas'),
    ]


class TaskSearch(QDialog):
    def __init__(self, window):
        super().__init__(window)
        self.window_owner = window
        self.setWindowTitle('Acceso rápido · SignalLab')
        self.setObjectName('commandPalette')
        available = window.screen().availableGeometry()
        self.height_limit = min(560, available.height() - 40, max(300, window.height() - 32))
        self.resize(min(740, available.width() - 40, max(460, window.width() - 48)), self.height_limit)
        self.selection = None
        self.icons = {}
        root = QVBoxLayout(self)
        root.setContentsMargins(21, 17, 21, 15)
        root.setSpacing(11)
        self.title = QLabel('Acceso rápido')
        self.title.setObjectName('searchTitle')
        root.addWidget(self.title)
        self.query = QLineEdit()
        self.query.setObjectName('commandSearch')
        self.query.setAccessibleName('Buscar una herramienta, documento o resultado')
        self.query.setPlaceholderText('Herramienta, variante o nombre de un resultado…')
        self.query.addAction(icon('search'), QLineEdit.ActionPosition.LeadingPosition)
        self.query.setClearButtonEnabled(True)
        self.query.installEventFilter(self)
        root.addWidget(self.query)
        self.list = QListWidget()
        self.list.setObjectName('commandResults')
        self.list.setAccessibleName('Coincidencias')
        self.list.setMinimumHeight(45)
        self.list.setMouseTracking(True)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.setItemDelegate(DetailListDelegate(self.list))
        self.list.itemClicked.connect(self.choose)
        self.list.itemActivated.connect(self.choose)
        root.addWidget(self.list, 1)
        self.note = QLabel()
        self.note.setObjectName('commandHint')
        root.addWidget(self.note)
        self.query.textChanged.connect(self.refresh)
        self.query.returnPressed.connect(lambda: self.choose(self.list.currentItem()))
        self.refresh('')
        self.query.setFocus()

    def documents(self, *, include_current):
        owner = self.window_owner
        tabs = owner.documents
        for index in range(tabs.count()):
            if not include_current and tabs.currentIndex() == index:
                continue
            route = tabs.tabData(index)
            if not route or route == ('browser',):
                continue
            if len(route) > 1 and route[1] == 'workspace':
                key = normalized_key(owner.pages[route].current_route)
                choice = tool_choice(key)
                yield key, Choice(('document', route), choice.title, 'Documento abierto · ' + tabs.tabText(index),
                                  choice.symbol, choice.color)
            else:
                title = tabs.tabText(index)
                symbol = 'calculator' if route == CAS_ROUTE else 'book' if route == ('menu', 'Biblioteca') else 'table'
                yield None, Choice(('document', route), title, 'Documento abierto', symbol, COLORS['accent'])

    def saved_results(self, query):
        symbols = {'signal': 'wave', 'system': 'blocks', 'state_space': 'states', 'calculation': 'math'}
        for record in reversed(self.window_owner.project.headers()):
            choice = Choice(('result', record['id']), record['title'], operation_label(record['operation']),
                            symbols.get(record['kind'], 'table'), COLORS['cyan'])
            if choice.matches(query):
                yield choice

    def groups(self, query):
        owner = self.window_owner
        opened = list(self.documents(include_current=bool(query)))
        actions = commands()
        if not query:
            opened_keys = {key for key, _ in opened}
            favorites = owner.favorite_tools
            recent = [key for key in owner.recent_tools if key not in favorites and key not in opened_keys]
            yield 'Favoritos', [tool_choice(key) for key in favorites]
            yield 'Documentos abiertos', [choice for key, choice in opened if key not in favorites]
            yield 'Herramientas recientes', [tool_choice(key) for key in recent]
            if not favorites and not opened and not recent:
                from .tool_browser import SHORTCUTS
                yield 'Herramientas', [tool_choice(key) for key in SHORTCUTS]
            yield 'Acciones', actions
            return

        matched = {}
        for entry in ENTRIES:
            for key, _ in matching_variants(entry, query):
                matched[key] = tool_choice(key)
        for key, choice in opened:
            if key in matched or choice.matches(query):
                matched[key or choice.target] = choice
        for choice in actions:
            if choice.matches(query) and not any(other.title == choice.title for other in matched.values()):
                matched[choice.target] = choice

        words = set(query.split())

        def rank(choice):
            title = normalize(choice.title)
            return (title != query, not words.issubset(title.split()), not title.startswith(query),
                    query not in title, choice.target[0] != 'document')

        yield 'Herramientas y acciones', sorted(matched.values(), key=rank)
        yield 'Resultados de la sesión', sorted(self.saved_results(query), key=rank)

    def refresh(self, text):
        query = ' '.join(normalize(text).split())
        self.list.clear()
        for title, choices in self.groups(query):
            if not choices:
                continue
            heading = QListWidgetItem(title)
            heading.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list.addItem(heading)
            for choice in choices:
                mark = (choice.symbol, choice.color)
                if mark not in self.icons:
                    self.icons[mark] = icon(*mark)
                item = QListWidgetItem(self.icons[mark], choice.title)
                item.setData(TARGET, choice.target)
                item.setData(DETAIL, choice.detail)
                item.setData(Qt.ItemDataRole.AccessibleDescriptionRole, choice.detail)
                item.setToolTip(choice.title + '\n' + choice.detail)
                self.list.addItem(item)
        self.list.setCurrentRow(-1)
        self.move_selection(1)
        message = '↑ ↓ para recorrer    ·    Enter para abrir    ·    Esc para cerrar'
        self.note.setText(message if self.list.count() else 'No hay coincidencias. Probá con una variante o un nombre más corto.')
        self.fit_results()

    def fit_results(self):
        layout = self.layout()
        margins = layout.contentsMargins()
        height = margins.top() + margins.bottom() + 3 * layout.spacing() + 12
        height += sum(widget.sizeHint().height() for widget in (self.title, self.query, self.note))
        if not self.list.count():
            height += self.list.minimumHeight()
        for row in range(self.list.count()):
            height += self.list.sizeHintForRow(row)
            if height >= self.height_limit:
                break
        self.resize(self.width(), min(self.height_limit, height))

    def move_selection(self, offset):
        row = self.list.currentRow() + offset
        while 0 <= row < self.list.count():
            item = self.list.item(row)
            if item.data(TARGET) is not None:
                self.list.setCurrentRow(row)
                self.list.scrollToItem(item)
                return
            row += offset

    def eventFilter(self, watched, event):
        if watched is self.query and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down):
                self.move_selection(-1 if event.key() == Qt.Key.Key_Up else 1)
                return True
        return super().eventFilter(watched, event)

    def choose(self, item):
        if item is not None and item.data(TARGET) is not None:
            self.selection = item.data(TARGET)
            self.accept()


def open_search(window):
    dialog = TaskSearch(window)
    accepted = dialog.exec()
    selection = dialog.selection
    dialog.deleteLater()
    if not accepted or selection is None:
        return
    kind, target = selection
    if kind == 'tool':
        window.open_tool(ROUTES[tuple(target)])
    elif kind == 'document':
        tabs = window.documents
        index = next((i for i in range(tabs.count()) if tabs.tabData(i) == target), -1)
        if index >= 0:
            tabs.setCurrentIndex(index)
    elif kind == 'result':
        window.focus_result(target)
    elif target == 'cas':
        window.open_cas()
    elif target == 'results':
        window.show_menu('Proyecto')
    elif target == 'library':
        window.show_menu('Biblioteca')
    elif target == 'home':
        window.show_home()
    elif target == 'compare':
        from .result_comparison import open_comparison
        open_comparison(window)
