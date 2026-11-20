"""Search and browse tools in a single catalog."""
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from .design import icon
from .theme_tokens import AREA_COLORS, COLORS
from .tool_catalog import AREAS, AREA_BY_ID, BY_KEY, ENTRIES, matches, normalize
from .wallpaper import BackgroundSurface


SHORTCUTS = (('basic', 'generate'), ('system_analysis', 0), ('course_tools', 'fir'), ('fourier', 0))


def label(text, name):
    widget = QLabel(text)
    widget.setObjectName(name)
    widget.setWordWrap(True)
    return widget


class ToolLink(QPushButton):
    def __init__(self, entry, callback):
        super().__init__()
        self.entry = entry
        self.setObjectName('toolLink')
        self.setAccessibleName(entry['title'])
        self.setAccessibleDescription(entry['summary'])
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 9, 12, 9)
        row.setSpacing(12)
        self.mark = QLabel()
        self.mark.setFixedSize(26, 26)
        self.mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(self.mark)
        column = QVBoxLayout()
        column.setSpacing(2)
        self.title = label(entry['title'], 'linkTitle')
        self.summary = label(entry['summary'], 'muted')
        column.addWidget(self.title)
        column.addWidget(self.summary)
        row.addLayout(column, 1)
        row.addWidget(label('›', 'linkArrow'))
        for child in self.findChildren(QLabel):
            child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.clicked.connect(callback)
        self.refresh_theme()

    def sizeHint(self):
        return self.layout().sizeHint().expandedTo(QSize(100, 54))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        row = self.layout()
        contents = row.contentsMargins()
        arrow = row.itemAt(2).widget()
        text_width = max(1, self.width() - contents.left() - contents.right()
                         - self.mark.width() - arrow.sizeHint().width() - 2 * row.spacing())
        title_height = self.title.heightForWidth(text_width)
        summary_height = self.summary.heightForWidth(text_width)
        self.title.setFixedHeight(title_height)
        self.summary.setFixedHeight(summary_height)
        self.setMinimumHeight(max(54, contents.top() + contents.bottom() + title_height + summary_height + 4))

    def refresh_theme(self):
        _, _, _, symbol = AREA_BY_ID[self.entry['area']]
        self.mark.setPixmap(icon(symbol, AREA_COLORS[self.entry['area']]).pixmap(20, 20))


class ToolBrowser(BackgroundSurface):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.area = None
        self.setObjectName('workspaceWallpaper')
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        title = label('Herramientas', 'catalogTitle')
        self.home_search = QLineEdit()
        self.home_search.setObjectName('homeSearch')
        self.home_search.setAccessibleName('Buscar en todas las herramientas')
        self.home_search.setPlaceholderText('Buscar una herramienta · Ctrl+K')
        self.home_search.setClearButtonEnabled(True)
        self.home_search.addAction(icon('search'), QLineEdit.ActionPosition.LeadingPosition)
        header = QHBoxLayout()
        header.setSpacing(16)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.home_search, 3)
        root.addLayout(header)

        self.area_picker = QComboBox()
        self.area_picker.setAccessibleName('Área de trabajo')
        self.area_picker.textActivated.connect(lambda _: self.choose_area(self.area_picker.currentData()))
        self.area_picker.addItem('Accesos directos', None)
        root.addWidget(self.area_picker)

        body = QHBoxLayout()
        body.setSpacing(12)
        root.addLayout(body, 1)
        self.index = QScrollArea()
        self.index.setObjectName('catalogIndex')
        self.index.setFrameShape(QFrame.Shape.NoFrame)
        self.index.setWidgetResizable(True)
        self.index.setFixedWidth(222)
        self.index.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        index_content = QWidget()
        index_content.setObjectName('catalogIndexContent')
        index_layout = QVBoxLayout(index_content)
        index_layout.setContentsMargins(8, 8, 8, 8)
        index_layout.setSpacing(4)
        self.area_buttons = {}
        for key, text, description, symbol in [(None, 'Accesos directos', '', 'home'), *AREAS]:
            button = QPushButton(text)
            button.setObjectName('catalogArea')
            button.setCheckable(True)
            button.setToolTip(description or text)
            button.clicked.connect(lambda checked=False, area=key: self.choose_area(area))
            index_layout.addWidget(button)
            self.area_buttons[key] = (button, symbol)
            if key is not None:
                self.area_picker.addItem(text, key)
        index_layout.addStretch()
        self.index.setWidget(index_content)
        body.addWidget(self.index)

        self.list = QScrollArea()
        self.list.setObjectName('catalogList')
        self.list.setFrameShape(QFrame.Shape.NoFrame)
        self.list.setWidgetResizable(True)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName('catalogListContent')
        self.groups = QVBoxLayout(content)
        self.groups.setContentsMargins(14, 8, 14, 14)
        self.groups.setSpacing(12)
        self.empty = label('No hay coincidencias. Probá con Fourier, energía o polos.', 'muted')
        self.groups.addWidget(self.empty)
        self.quick = self.add_group('Accesos directos', [BY_KEY[key] for key in SHORTCUTS])
        self.sections = {}
        for key, _, _, _ in AREAS:
            entries = [entry for entry in ENTRIES if entry['area'] == key]
            for section in dict.fromkeys(entry['section'] for entry in entries):
                self.sections[key, section] = self.add_group(section, [e for e in entries if e['section'] == section])
        self.groups.addStretch()
        self.list.setWidget(content)
        body.addWidget(self.list, 1)

        self.home_search.textChanged.connect(self.apply_query)
        self.home_search.returnPressed.connect(self.open_search_match)
        self.refresh_theme()
        self.select_area(None)

    def choose_area(self, area):
        if area is None:
            self.window.show_home()
        else:
            self.window.show_area(area)

    def select_area(self, area):
        self.area = area
        self.area_picker.setCurrentIndex(list(self.area_buttons).index(area))
        for key, (button, _) in self.area_buttons.items():
            button.setChecked(key == area)
        if self.home_search.text():
            self.home_search.clear()
        else:
            self.apply_query('')

    def add_group(self, title, entries):
        group = QFrame()
        group.setObjectName('catalogGroup')
        box = QVBoxLayout(group)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(1)
        heading = label(title, 'sectionTitle')
        box.addWidget(heading)
        links = []
        for entry in entries:
            link = ToolLink(entry, lambda checked=False, value=entry: self.open_entry(value))
            box.addWidget(link)
            links.append(link)
        self.groups.addWidget(group)
        return group, heading, links

    def open_entry(self, entry):
        self.window.open_workflow(entry, self.home_search.text())

    def apply_query(self, text):
        query = text.strip()
        # Browsing an area shows its groups. Search spans the catalog in place.
        self.quick[0].setVisible(not query and self.area is None)
        found = False
        for (area, section), (group, heading, links) in self.sections.items():
            if query:
                heading.setText(AREA_BY_ID[area][1] + ' · ' + section)
                visible_links = [matches(link.entry, query) for link in links]
                visible = any(visible_links)
            else:
                heading.setText(section)
                visible = area == self.area
                visible_links = [visible] * len(links)
            for link, link_visible in zip(links, visible_links):
                link.setVisible(link_visible)
            group.setVisible(visible)
            found = found or visible
        self.empty.setVisible(bool(query) and not found)
        self.list.verticalScrollBar().setValue(0)

    def open_search_match(self):
        query = self.home_search.text().strip()
        candidates = [entry for entry in ENTRIES if query and matches(entry, query)]
        if candidates:
            self.open_entry(min(candidates, key=lambda entry: normalize(entry['title']) != normalize(query)))

    def refresh_theme(self):
        for key, (button, symbol) in self.area_buttons.items():
            button.setIcon(icon(symbol, AREA_COLORS[key] if key else COLORS['accent']))
        for _, _, links in [self.quick, *self.sections.values()]:
            for link in links:
                link.refresh_theme()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        compact = self.width() < 710
        self.index.setVisible(not compact)
        self.area_picker.setVisible(compact)
