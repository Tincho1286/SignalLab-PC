"""Task shortcuts, area navigation and search from the desktop start page."""
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from .design import icon
from .studio_cards import QuickAction, SamplingIllustration
from .theme_tokens import AREA_COLORS
from .tool_catalog import AREAS, AREA_BY_ID, BY_KEY, ENTRIES, matches, normalize
from .wallpaper import BackgroundSurface


SHORTCUTS = (
    ('Crear señal', 'Fórmulas, muestras y ventanas', ('basic', 'generate'), 'signal', 'green'),
    ('Analizar sistema', 'Transferencia, frecuencia y tiempo', ('system_analysis', 0), 'response', 'blue'),
    ('Diseñar filtro', 'Bandas, ventanas o polos y ceros', ('course_tools', 'fir'), 'design', 'purple'),
    ('Transformada de Fourier', 'DTFT, DFT y Fourier continua', ('fourier', 0), 'spectrum', 'amber'),
)

AREA_SUMMARIES = {
    'signals': 'Edición, operaciones y medidas',
    'systems': 'Transferencias y respuestas',
    'filters': 'FIR, IIR, ideales y conversión',
    'spectra': 'Series, transformadas y densidades',
    'sampling': 'Aliasing, reconstrucción y tasa',
    'transforms': 'Transformadas y ecuaciones',
    'random': 'Estadística, correlación y modelos',
}


def label(text, name):
    widget = QLabel(text)
    widget.setObjectName(name)
    widget.setWordWrap(True)
    return widget


class ToolLink(QPushButton):
    def __init__(self, entry, callback):
        super().__init__()
        self.setObjectName('toolLink')
        self.setAccessibleName(entry['title'])
        self.setAccessibleDescription(entry['summary'])
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 8, 12, 8)
        column = QVBoxLayout()
        column.setSpacing(2)
        for text, name in [(entry['title'], 'linkTitle'), (entry['summary'], 'muted')]:
            item = label(text, name)
            item.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            column.addWidget(item)
        row.addLayout(column, 1)
        arrow = label('›', 'linkArrow')
        arrow.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        row.addWidget(arrow)
        self.clicked.connect(callback)

    def sizeHint(self):
        return self.layout().sizeHint().expandedTo(QSize(100, 49))


class ToolBrowser(QScrollArea):
    def __init__(self, window, area=None):
        super().__init__()
        self.window = window
        self.area = area
        self.sections = []
        self.quick_buttons = []
        self.area_buttons = []
        self.columns = None
        self.card_columns = None
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content = BackgroundSurface()
        self.content.setObjectName('workspaceWallpaper')
        self.setWidget(self.content)
        root = QVBoxLayout(self.content)
        root.setContentsMargins(18, 12, 18, 16)
        root.setSpacing(12)
        if area is None:
            self.build_home(root)
        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        root.addLayout(self.grid)
        root.addStretch()

        if area:
            entries = [entry for entry in ENTRIES if entry['area'] == area]
            for title in dict.fromkeys(entry['section'] for entry in entries):
                self.add_section(area, title, [entry for entry in entries if entry['section'] == title])
        else:
            for key, title, _, _ in AREAS:
                self.add_section(key, title, [entry for entry in ENTRIES if entry['area'] == key])
            self.home_search.textChanged.connect(self.apply_query)
            self.home_search.returnPressed.connect(self.open_search_match)
            self.apply_query('')
        self.reflow()

    def build_home(self, root):
        hero = QFrame()
        hero.setObjectName('studioHero')
        hero_row = QHBoxLayout(hero)
        hero_row.setContentsMargins(22, 12, 18, 12)
        hero_row.setSpacing(24)
        introduction = QVBoxLayout()
        introduction.setSpacing(8)
        introduction.addStretch()
        introduction.addWidget(label('Señales y sistemas', 'welcomeTitle'))
        introduction.addWidget(label('Análisis de señales, diseño de filtros y cálculo simbólico.', 'heroDescription'))
        self.home_search = QLineEdit()
        self.home_search.setObjectName('homeSearch')
        self.home_search.setAccessibleName('Buscar herramientas')
        self.home_search.setPlaceholderText('Buscar por nombre o concepto…')
        self.home_search.setClearButtonEnabled(True)
        self.home_search.addAction(icon('search'), QLineEdit.ActionPosition.LeadingPosition)
        introduction.addWidget(self.home_search)
        introduction.addStretch()
        hero_row.addLayout(introduction, 6)
        self.illustration = SamplingIllustration()
        hero_row.addWidget(self.illustration, 5)
        root.addWidget(hero)

        self.home_links = QWidget()
        shortcuts = QVBoxLayout(self.home_links)
        shortcuts.setContentsMargins(0, 0, 0, 0)
        shortcuts.setSpacing(8)
        shortcuts.addWidget(label('Accesos directos', 'browseHeading'))
        self.quick_grid = QGridLayout()
        self.quick_grid.setSpacing(8)
        shortcuts.addLayout(self.quick_grid)
        for title, description, key, symbol, role in SHORTCUTS:
            self.quick_buttons.append(QuickAction(title, description, symbol, role,
                lambda checked=False, entry=BY_KEY[key]: self.window.open_workflow(entry)))
        shortcuts.addSpacing(6)
        shortcuts.addWidget(label('Áreas de trabajo', 'browseHeading'))
        self.area_grid = QGridLayout()
        self.area_grid.setSpacing(8)
        shortcuts.addLayout(self.area_grid)
        for key, title, _, symbol in AREAS:
            self.area_buttons.append(QuickAction(title, AREA_SUMMARIES[key], symbol, None,
                lambda checked=False, area=key: self.window.show_area(area), area=key))
        cas = QuickAction('Calculadora CAS', 'Álgebra y cálculo simbólico',
                          'calculator', 'purple', self.window.open_cas)
        cas.setObjectName('areaCard')
        self.area_buttons.append(cas)
        root.addWidget(self.home_links)
        self.search_heading = label('Resultados de búsqueda', 'browseHeading')
        self.search_empty = label('No hay coincidencias. Probá con Fourier, energía o polos.', 'muted')
        root.addWidget(self.search_heading)
        root.addWidget(self.search_empty)

    def add_section(self, area, title, entries):
        frame = QFrame(self.content)
        frame.setObjectName('browserSection')
        heading = label(title, 'sectionTitle')
        box = QVBoxLayout(frame)
        box.setContentsMargins(10, 10, 10, 10)
        box.setSpacing(4)
        box.addWidget(heading)
        links = []
        for entry in entries:
            link = ToolLink(entry, lambda checked=False, value=entry: self.open_entry(value))
            box.addWidget(link)
            links.append((entry, link))
        box.addStretch()
        self.sections.append((frame, heading, area, links))
        heading.setStyleSheet('color:'+AREA_COLORS[area])

    def query(self):
        return self.home_search.text().strip() if self.area is None else ''

    def open_entry(self, entry):
        self.window.open_workflow(entry, self.query())

    def apply_query(self, text):
        query = text.strip()
        self.home_links.setVisible(not query)
        self.search_heading.setVisible(bool(query))
        found = False
        for frame, _, _, links in self.sections:
            visible = False
            for entry, link in links:
                matching = bool(query) and matches(entry, query)
                link.setVisible(matching)
                visible = visible or matching
            frame.setVisible(visible)
            found = found or visible
        self.search_empty.setVisible(bool(query) and not found)
        self.layout_sections()

    def open_search_match(self):
        query = self.query()
        if not query:
            return
        candidates = [entry for entry in ENTRIES if matches(entry, query)]
        if candidates:
            selected = min(candidates, key=lambda entry: normalize(entry['title']) != normalize(query))
            self.open_entry(selected)

    def refresh_theme(self):
        for _, heading, area, _ in self.sections:
            heading.setStyleSheet('color:'+AREA_COLORS[area])
        for button in self.quick_buttons + self.area_buttons:
            button.refresh_theme()
        if self.area is None:
            self.illustration.update()
        self.content.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reflow()

    def layout_sections(self):
        columns = self.columns or 1
        visible = (frame for frame, _, _, _ in self.sections if not frame.isHidden())
        for index, frame in enumerate(visible):
            self.grid.addWidget(frame, index // columns, index % columns)
        for column in range(2):
            self.grid.setColumnStretch(column, int(column < columns))

    def reflow(self):
        width = self.viewport().width()
        if self.area is None:
            self.illustration.setVisible(width >= 720)
            columns = 4 if width >= 1000 else 2 if width >= 480 else 1
            if columns != self.card_columns:
                self.card_columns = columns
                for grid, buttons in ((self.quick_grid, self.quick_buttons), (self.area_grid, self.area_buttons)):
                    for index, button in enumerate(buttons):
                        grid.addWidget(button, index // columns, index % columns)
                    for column in range(4):
                        grid.setColumnStretch(column, int(column < columns))
        columns = 2 if width >= 730 else 1
        if columns != self.columns:
            self.columns = columns
            self.layout_sections()
