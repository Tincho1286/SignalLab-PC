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
from .tool_catalog import AREAS, AREA_BY_ID, BY_KEY, DETAILS_BY_KEY, normalized_key
from .tool_search import find_tools, rank, tokens


@dataclass(frozen=True)
class Choice:
    target: tuple
    title: str
    detail: str
    symbol: str
    color: str
    keywords: str = ''

    def search_rank(self, query):
        return rank(query, (tokens(self.title),), tokens(self.detail + ' ' + self.keywords))


def tool_choice(key, hit=None, *, opened=False):
    entry = BY_KEY[key]
    _, area, _, symbol = AREA_BY_ID[entry['area']]
    detail = DETAILS_BY_KEY[key]
    target = ('tool', key, hit.settings) if hit is not None and hit.settings else ('tool', key)
    title = hit.title if hit is not None else detail['title']
    summary = hit.summary if hit is not None else detail['summary']
    state = ' · Abierto' if opened else ''
    return Choice(target, title, area + state + ' · ' + summary, symbol, AREA_COLORS[entry['area']])


def commands():
    return [
        Choice(('command', 'cas'), 'Calculadora CAS', 'Álgebra y cálculo simbólico',
               'calculator', COLORS['purple'], CAS_SEARCH + ' expresion simbolico derivada integral'),
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
    def __init__(self, window, query=''):
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
        if query:
            self.query.setText(query)
            self.query.selectAll()
        else:
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
            score = choice.search_rank(query)
            if score is not None:
                yield score, choice

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

        open_keys = {key for key, _ in opened}
        matched = [(hit.score, tool_choice(hit.key, hit, opened=hit.key in open_keys)) for hit in find_tools(query)]
        terms = tokens(query)
        action_titles = {choice.title for choice in actions}
        for key, choice in opened:
            if key is None and choice.title not in action_titles:
                score = choice.search_rank(terms)
                if score is not None:
                    matched.append((score, choice))
        for choice in actions:
            score = choice.search_rank(terms)
            if score is not None:
                matched.append((score, choice))
        for key, title, description, symbol in AREAS:
            score = rank(terms, (tokens(title),))
            if score is not None:
                matched.append((score, Choice(('area', key), title, 'Área de trabajo · ' + description,
                                              symbol, AREA_COLORS[key])))

        yield 'Herramientas y acciones', [choice for _, choice in sorted(matched, key=lambda entry: entry[0])]
        yield 'Resultados de la sesión', [choice for _, choice in sorted(self.saved_results(terms), key=lambda entry: entry[0])]

    def refresh(self, text):
        query = text.strip()
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


def open_search(window, query=''):
    dialog = TaskSearch(window, query)
    accepted = dialog.exec()
    selection = dialog.selection
    dialog.deleteLater()
    if not accepted or selection is None:
        return
    kind, target = selection[:2]
    if kind == 'tool':
        window.open_tool_search(tuple(target), selection[2] if len(selection) > 2 else ())
    elif kind == 'document':
        tabs = window.documents
        index = next((i for i in range(tabs.count()) if tabs.tabData(i) == target), -1)
        if index >= 0:
            tabs.setCurrentIndex(index)
    elif kind == 'result':
        window.focus_result(target)
    elif kind == 'area':
        window.show_area(target)
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
