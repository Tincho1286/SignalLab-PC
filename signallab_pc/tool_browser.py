"""Responsive catalog with direct access to tools and recent work."""
from math import exp, sin, tau

from PySide6.QtCore import QPointF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget,
)

from .design import icon
from .theme_tokens import AREA_COLORS, COLORS
from .tool_catalog import AREAS, AREA_BY_ID, BY_KEY, DETAILS_BY_KEY, ENTRIES, matches, normalize
from .workspaces import ROUTES


SHORTCUTS = (('basic', 'generate'), ('system_analysis', 0), ('course_tools', 'fir'), ('fourier', 0))


def label(text, name):
    widget = QLabel(text)
    widget.setObjectName(name)
    widget.setWordWrap(True)
    return widget


class SamplingIllustration(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(225, 140)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAccessibleName('Una señal continua y sus muestras sobre el mismo eje')

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width = self.width() - 30
        top, bottom = 26, self.height() - 21
        zero = (top + bottom) / 2
        amplitude = (bottom - top) * 0.42

        def point(t):
            y = sin(tau * (1.45 * t + 0.035)) * exp(-0.58 * t)
            return QPointF(12 + width * t, zero - amplitude * y)

        grid = QColor(COLORS['grid'])
        grid.setAlpha(140)
        painter.setPen(QPen(grid))
        for i in range(13):
            x = point(i / 12).x()
            painter.drawLine(QPointF(x, top), QPointF(x, bottom))
        for y in (top, (zero + top) / 2, (zero + bottom) / 2, bottom):
            painter.drawLine(QPointF(12, y), QPointF(12 + width, y))
        painter.setPen(QPen(QColor(COLORS['disabled'])))
        painter.drawLine(QPointF(12, zero), QPointF(18 + width, zero))
        painter.drawText(QPointF(22 + width, zero + 5), 't')

        continuous = QColor(COLORS['blue'])
        discrete = QColor(COLORS['green'])
        path = QPainterPath(point(0))
        for i in range(1, 181):
            path.lineTo(point(i / 180))
        painter.setPen(QPen(continuous, 2.0))
        painter.drawPath(path)

        painter.setPen(QPen(discrete, 1.25))
        painter.setBrush(discrete)
        for i in range(1, 13):
            sample = point(i / 13)
            painter.drawLine(QPointF(sample.x(), zero), sample)
            painter.drawEllipse(sample, 2.9, 2.9)

        for x, color, title in ((14, continuous, 'x(t)'), (78, discrete, 'x[n]')):
            painter.setPen(QPen(color, 2))
            painter.drawLine(QPointF(x, 12), QPointF(x + 12, 12))
            painter.setPen(QColor(COLORS['text']))
            painter.drawText(QPointF(x + 18, 17), title)


class CatalogCard(QPushButton):
    def __init__(self, title, summary, symbol, area, callback, *, role='toolLink'):
        super().__init__()
        self.area = area
        self.symbol = symbol
        self.setObjectName(role)
        self.setAccessibleName(title)
        self.setAccessibleDescription(summary)
        self.setToolTip(summary or title)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        size_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        size_policy.setHeightForWidth(True)
        self.setSizePolicy(size_policy)
        self.setMinimumWidth(0)
        row = QHBoxLayout(self)
        row.setContentsMargins(13, 11, 12, 11)
        row.setSpacing(11)
        self.mark = QLabel()
        self.mark.setObjectName('catalogMark')
        self.mark.setFixedSize(34, 34)
        self.mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(self.mark, 0, Qt.AlignmentFlag.AlignVCenter)
        column = QVBoxLayout()
        column.setSpacing(3)
        self.title = label(title, 'linkTitle')
        self.summary = label(summary, 'catalogSummary')
        column.addWidget(self.title)
        column.addWidget(self.summary)
        row.addLayout(column, 1)
        self.arrow = label('›', 'linkArrow')
        self.arrow.setWordWrap(False)
        row.addWidget(self.arrow)
        for child in self.findChildren(QLabel):
            child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.summary.setVisible(bool(summary))
        self.clicked.connect(callback)
        self.refresh_theme()

    def minimumSizeHint(self):
        return QSize(0, 58)

    def sizeHint(self):
        return QSize(245, self.heightForWidth(245))

    def heightForWidth(self, width):
        row = self.layout()
        margins = row.contentsMargins()
        text_width = max(30, width - margins.left() - margins.right()
                         - self.mark.width() - self.arrow.sizeHint().width() - 2 * row.spacing())
        title_height = self.title.heightForWidth(text_width)
        summary_height = 0
        if not self.summary.isHidden():
            summary_height = self.summary.heightForWidth(text_width) + 3
        return max(58, margins.top() + margins.bottom() + title_height + summary_height + 4)

    def refresh_theme(self):
        color = AREA_COLORS.get(self.area, COLORS['accent'])
        self.mark.setPixmap(icon(self.symbol, color).pixmap(22, 22))


class CardGrid(QWidget):
    def __init__(self):
        super().__init__()
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(10)
        self.cards = []
        self.columns = 1

    def arrange(self, cards, columns):
        if self.cards == cards and self.columns == columns:
            return
        for index in range(self.grid.count() - 1, -1, -1):
            self.grid.takeAt(index)
        for column in range(max(self.columns, columns)):
            self.grid.setColumnStretch(column, int(column < columns))
        self.cards = list(cards)
        self.columns = columns
        for index, card in enumerate(cards):
            row, column = divmod(index, columns)
            self.grid.addWidget(card, row, column)


class CatalogSection(QWidget):
    def __init__(self, title):
        super().__init__()
        box = QVBoxLayout(self)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(8)
        self.heading = label(title, 'catalogSectionTitle')
        box.addWidget(self.heading)
        self.cards = CardGrid()
        self.shown_cards = []
        box.addWidget(self.cards)


class ToolBrowser(QScrollArea):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.area = None
        self.setObjectName('catalogScroll')
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content = QWidget()
        self.content.setObjectName('catalogCanvas')
        self.setWidget(self.content)
        self.groups = QVBoxLayout(self.content)
        self.groups.setContentsMargins(26, 21, 26, 26)
        self.groups.setSpacing(16)

        self.hero = QFrame()
        self.hero.setObjectName('welcomeCard')
        header = QHBoxLayout(self.hero)
        header.setContentsMargins(25, 18, 24, 18)
        header.setSpacing(18)
        introduction = QVBoxLayout()
        introduction.setSpacing(8)
        self.title = label('Laboratorio de señales y sistemas', 'welcomeTitle')
        self.description = label('Elegí un área o buscá directamente el cálculo que querés hacer.', 'catalogIntro')
        introduction.addWidget(self.title)
        introduction.addWidget(self.description)
        self.launcher = QPushButton('  Acceso rápido   ·   Ctrl+K')
        self.launcher.setObjectName('launchPalette')
        self.launcher.setAccessibleName('Acceso rápido')
        self.launcher.setToolTip('Buscar herramientas, documentos y resultados')
        self.launcher.setIcon(icon('search', COLORS['accent']))
        self.launcher.clicked.connect(window.focus_tool_search)
        introduction.addWidget(self.launcher)
        self.home_search = QLineEdit()
        self.home_search.setObjectName('homeSearch')
        self.home_search.setAccessibleName('Filtrar las herramientas de esta área')
        self.home_search.setPlaceholderText('Filtrar en esta área…')
        self.home_search.setClearButtonEnabled(True)
        self.search_icon = self.home_search.addAction(icon('search'), QLineEdit.ActionPosition.LeadingPosition)
        introduction.addWidget(self.home_search)
        header.addLayout(introduction, 6)
        self.illustration = SamplingIllustration()
        header.addWidget(self.illustration, 4)
        self.groups.addWidget(self.hero)

        self.favorites = CatalogSection('Favoritos')
        self.groups.addWidget(self.favorites)
        self.areas = CatalogSection('Áreas de trabajo')
        self.area_cards = [
            CatalogCard(title, description, symbol, key, lambda checked=False, area=key: window.show_area(area),
                        role='catalogArea')
            for key, title, description, symbol in AREAS
        ]
        self.groups.addWidget(self.areas)
        self.quick = CatalogSection('Accesos directos')
        self.groups.addWidget(self.quick)

        self.empty = label('No hay coincidencias en esta área. Buscá en toda la app con Ctrl+K.', 'catalogIntro')
        self.groups.addWidget(self.empty)
        self.sections = {}
        for entry in ENTRIES:
            key = entry['area'], entry['section']
            if key not in self.sections:
                section = CatalogSection(key[1])
                self.sections[key] = section, []
                self.groups.addWidget(section)
            section, links = self.sections[key]
            links.append((entry, self.tool_link(entry)))
        self.groups.addStretch()
        self.home_search.textChanged.connect(self.apply_query)
        self.home_search.returnPressed.connect(self.open_search_match)
        self.select_area(None)

    def tool_link(self, entry, *, role='toolLink', key=None):
        _, area, _, symbol = AREA_BY_ID[entry['area']]
        callback = (lambda: self.window.open_tool(ROUTES[key])) if key else (lambda: self.open_entry(entry))
        title = DETAILS_BY_KEY[key]['title'] if key is not None else entry['title']
        summary = entry['summary'] if role == 'toolLink' else area if key is not None else ''
        return CatalogCard(title, summary, symbol, entry['area'], callback, role=role)

    def refresh_shortcuts(self):
        favorite = tuple(self.window.favorite_tools)
        recent = tuple(key for key in self.window.recent_tools if key not in favorite)
        keys = recent or (() if favorite else SHORTCUTS)
        self.quick.heading.setText('Herramientas recientes' if recent else 'Accesos directos')
        self.set_shortcuts(self.favorites, favorite, 'favoriteShortcut', exact=True)
        self.set_shortcuts(self.quick, keys, 'catalogShortcut', exact=bool(recent))
        self.show_home_sections()

    def set_shortcuts(self, section, keys, role, *, exact):
        signature = (keys, exact)
        if signature == getattr(section, 'shortcut_signature', None):
            return
        for card in section.shown_cards:
            card.hide()
            card.deleteLater()
        section.shortcut_signature = signature
        section.shown_cards = [self.tool_link(BY_KEY[key], role=role, key=key if exact else None) for key in keys]

    def show_home_sections(self):
        at_home = self.area is None and not self.home_search.text().strip()
        self.areas.setVisible(at_home)
        for section in (self.favorites, self.quick):
            section.setVisible(at_home and bool(section.shown_cards))

    def select_area(self, area):
        self.area = area
        catalog = area is None
        self.launcher.setVisible(catalog)
        self.home_search.setVisible(not catalog)
        self.title.setText('Laboratorio de señales y sistemas' if catalog else AREA_BY_ID[area][1])
        self.description.setText('Elegí un área o buscá directamente el cálculo que querés hacer.' if catalog else AREA_BY_ID[area][2])
        self.refresh_shortcuts()
        if self.home_search.text():
            self.home_search.clear()
        else:
            self.apply_query('')

    def open_entry(self, entry):
        self.window.open_workflow(entry, self.home_search.text())

    def apply_query(self, text):
        query = text.strip()
        self.show_home_sections()
        found = False
        for (area, topic), (section, links) in self.sections.items():
            shown = [link for entry, link in links if not query or matches(entry, query)] if area == self.area else []
            for _, link in links:
                link.setVisible(link in shown)
            section.shown_cards = shown
            section.setVisible(bool(shown))
            found = found or bool(shown)
        self.empty.setVisible(bool(query) and not found)
        self.adapt_grid()
        self.verticalScrollBar().setValue(0)

    def adapt_grid(self):
        width = self.viewport().width()
        area_columns = 4 if width >= 1060 else 3 if width >= 780 else 2 if width >= 490 else 1
        tool_columns = 2 if width >= 670 else 1
        self.areas.cards.arrange(self.area_cards, area_columns)
        for section in (self.favorites, self.quick):
            section.cards.arrange(section.shown_cards, area_columns)
        for section, _ in self.sections.values():
            section.cards.arrange(section.shown_cards, tool_columns)
        self.illustration.setVisible(self.area is None and width >= 710)

    def open_search_match(self):
        query = self.home_search.text().strip()
        candidates = [entry for entry in ENTRIES if entry['area'] == self.area and query and matches(entry, query)]
        if candidates:
            self.open_entry(min(candidates, key=lambda entry: normalize(entry['title']) != normalize(query)))

    def refresh_theme(self):
        self.search_icon.setIcon(icon('search'))
        self.launcher.setIcon(icon('search', COLORS['accent']))
        for card in self.findChildren(CatalogCard):
            card.refresh_theme()
        self.illustration.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'sections'):
            self.adapt_grid()
