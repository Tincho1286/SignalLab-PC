"""Desktop commands and search across the catalog."""
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QToolButton, QToolBar, QMenu, QSizePolicy
from PySide6.QtGui import QAction
from .design import icon


def install_toolbar(window):
    bar = QToolBar('Navegación', window)
    bar.setObjectName('studioToolbar')
    bar.setMovable(False)
    bar.setFloatable(False)
    bar.setIconSize(QSize(19, 19))
    window.addToolBar(bar)
    window.studio_toolbar = bar

    menu = QMenu(window)
    for action in window.menuBar().actions():
        menu.addAction(action)
    application = QToolButton()
    application.setObjectName('applicationMenu')
    application.setIcon(icon('menu'))
    application.setMenu(menu)
    application.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
    application.setAccessibleName('Menú de la aplicación')
    application.setToolTip('Archivo, herramientas, vista y ayuda')
    bar.addWidget(application)
    brand = QWidget()
    brand_row = QHBoxLayout(brand)
    brand_row.setContentsMargins(4, 0, 5, 0)
    mark = QLabel()
    mark.setPixmap(window.windowIcon().pixmap(28, 28))
    brand_row.addWidget(mark)
    window.studio_brand_name = QLabel('SignalLab')
    window.studio_brand_name.setObjectName('studioBrand')
    brand_row.addWidget(window.studio_brand_name)
    bar.addWidget(brand)

    def action(title, symbol, callback, role='chromeAction'):
        button = QToolButton()
        button.setObjectName(role)
        button.setText(title)
        button.setAccessibleName(title)
        button.setToolTip(title)
        button.setIcon(icon(symbol))
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        button.clicked.connect(callback)
        return button, bar.addWidget(button)

    def stretch():
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        bar.addWidget(spacer)

    stretch()
    search, window.studio_search_action = action('Acceso rápido   ·   Ctrl+K', 'search', window.focus_tool_search, 'studioSearch')
    search.setToolTip('Buscar herramientas, documentos y resultados · Ctrl+K')
    window.studio_search_button = search
    stretch()
    window.studio_aux_buttons = [
        search,
        action('Resultados', 'table', lambda: window.show_menu('Proyecto'))[0],
        action('Biblioteca', 'book', lambda: window.show_menu('Biblioteca'))[0],
        action('CAS', 'calculator', window.open_cas)[0],
    ]
    shortcut = QAction(window)
    shortcut.setShortcut('Ctrl+K')
    shortcut.triggered.connect(window.focus_tool_search)
    window.addAction(shortcut)
    window.menuBar().hide()
    adapt_shell(window)


def adapt_shell(window):
    """Preserve task controls and reading space on small desktop windows."""
    width, height = window.width(), window.height()
    window.navigation.adapt(width, height)
    short = height < 580
    if getattr(window, '_studio_short', None) != short:
        window._studio_short = short
        window.refresh_context_path()
        window.title.setProperty('shortHeader', short)
        window.title.style().unpolish(window.title)
        window.title.style().polish(window.title)
        window.title.updateGeometry()
    compact = width < 825
    if getattr(window, '_studio_compact', None) == compact:
        return
    window._studio_compact = compact
    window.studio_brand_name.setVisible(not compact)
    style = Qt.ToolButtonStyle.ToolButtonIconOnly if compact else Qt.ToolButtonStyle.ToolButtonTextBesideIcon
    window.studio_search_button.setMinimumWidth(0 if compact else 216)
    for button in window.studio_aux_buttons:
        button.setToolButtonStyle(style)
    window.result_layout.setToolButtonStyle(style)
    heading_margins = (13, 8, 13, 9) if compact else (24, 12, 24, 13)
    window.heading.layout().setContentsMargins(*heading_margins)
