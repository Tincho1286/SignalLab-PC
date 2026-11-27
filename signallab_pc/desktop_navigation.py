"""Navigation available beside every document."""
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QFrame, QScrollArea, QSizePolicy, QToolButton, QVBoxLayout, QWidget

from .design import icon
from .theme_tokens import AREA_COLORS, COLORS
from .tool_catalog import AREAS


SHORT_NAMES = {
    'signals': 'Señales', 'systems': 'Sistemas', 'filters': 'Filtros',
    'spectra': 'Fourier', 'sampling': 'Muestreo', 'transforms': 'Laplace / Z',
    'random': 'Aleatorias', 'communications': 'Comunic.',
}


class DesktopNavigation(QScrollArea):
    def __init__(self, window):
        super().__init__()
        self.setObjectName('desktopNavigation')
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName('desktopNavigationBody')
        layout = QVBoxLayout(content)
        layout.setContentsMargins(6, 10, 6, 8)
        layout.setSpacing(3)
        self.buttons = {}
        routes = [(None, 'Inicio', 'Ver todas las áreas de trabajo', 'home', 'Inicio')]
        routes += [(*area, SHORT_NAMES.get(area[0], area[1])) for area in AREAS]
        for key, title, description, symbol, short_name in routes:
            button = QToolButton()
            button.setObjectName('desktopNavigationButton')
            button.setText(short_name)
            button.setAccessibleName(title)
            button.setToolTip(title + ' · ' + description if key else description)
            button.setCheckable(True)
            button.setIconSize(QSize(23, 23))
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked=False, area=key: window.show_area(area))
            layout.addWidget(button)
            self.buttons[key] = (button, symbol)
        layout.addStretch()
        self.setWidget(content)
        self.adapt(1200, 800)
        self.refresh_theme()

    def adapt(self, width, height):
        compact = width < 930 or height < 640
        button_height = 30 if height < 400 else 36 if height < 530 else 40 if compact else 55
        if getattr(self, '_button_height', None) == button_height:
            return
        self._button_height = button_height
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded if button_height == 30
                                        else Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFixedWidth(55 if compact else 94)
        style = Qt.ToolButtonStyle.ToolButtonIconOnly if compact else Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        for button, _ in self.buttons.values():
            button.setToolButtonStyle(style)
            button.setFixedHeight(button_height)

    def select(self, area, *, catalog=False):
        for key, (button, _) in self.buttons.items():
            button.setChecked(key == area and (key is not None or catalog))

    def refresh_theme(self):
        for key, (button, symbol) in self.buttons.items():
            button.setIcon(icon(symbol, AREA_COLORS[key] if key else COLORS['accent']))
