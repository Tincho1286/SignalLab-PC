"""Desktop commands and search across the catalog."""
from PySide6.QtCore import Qt,QSize,QEvent
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QToolButton,QToolBar,QMenu,QSizePolicy,QDialog,QLineEdit,QListWidget,QListWidgetItem
from PySide6.QtGui import QAction
from .design import icon
from .theme_tokens import COLORS as C,AREA_COLORS


class TaskSearch(QDialog):
    def __init__(self,window):
        super().__init__(window);self.setWindowTitle('Buscar una herramienta');available=self.screen().availableGeometry();self.resize(min(720,available.width()-40),min(570,available.height()-40));self.selection=None;self.entries=[];root=QVBoxLayout(self);root.setContentsMargins(22,22,22,22);root.setSpacing(14)
        title=QLabel('¿Qué querés hacer?');title.setObjectName('searchTitle');root.addWidget(title);self.query=QLineEdit();self.query.setObjectName('commandSearch');self.query.setPlaceholderText('Una tarea o un concepto: convolución, polos, DTFT…');self.query.setClearButtonEnabled(True);self.query.installEventFilter(self);root.addWidget(self.query);self.list=QListWidget();self.list.setObjectName('commandResults');self.list.setWordWrap(True);self.list.itemClicked.connect(self.choose);self.list.itemActivated.connect(self.choose);root.addWidget(self.list,1);self.note=QLabel('Enter para abrir · Esc para cerrar');self.note.setObjectName('muted');root.addWidget(self.note);self.query.textChanged.connect(self.refresh);self.query.returnPressed.connect(lambda:self.choose(self.list.currentItem()));self.refresh('');self.query.setFocus()
    def eventFilter(self,watched,event):
        if watched is self.query and event.type()==QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Up,Qt.Key.Key_Down):
            offset=-1 if event.key()==Qt.Key.Key_Up else 1;self.list.setCurrentRow(max(0,min(self.list.count()-1,self.list.currentRow()+offset)));return True
        return super().eventFilter(watched,event)
    def refresh(self,text):
        from .tool_catalog import ENTRIES,matches,AREA_BY_ID,normalize
        from .cas_reference import CAS_SEARCH
        self.list.clear();self.entries=[entry for entry in ENTRIES if matches(entry,text)];query=normalize(text);words=set(query.split());self.entries.sort(key=lambda entry:(normalize(entry['title'])!=query,not words.issubset(set(normalize(entry['title']).split()))))
        for i,entry in enumerate(self.entries):
            item=QListWidgetItem(icon(AREA_BY_ID[entry['area']][3],AREA_COLORS[entry['area']]),entry['title']+'\n'+AREA_BY_ID[entry['area']][1]+' · '+entry['summary']);item.setData(Qt.ItemDataRole.UserRole,i);self.list.addItem(item)
        if not text.strip() or all(word in normalize(CAS_SEARCH) for word in normalize(text).split()):
            item=QListWidgetItem(icon('calculator',C['purple']),'Calculadora CAS\nÁlgebra, expresiones y cálculo simbólico');item.setData(Qt.ItemDataRole.UserRole,'cas')
            if words and words.issubset({'calculadora','cas'}):self.list.insertItem(0,item)
            else:self.list.addItem(item)
        self.note.setText('Enter para abrir · Esc para cerrar' if self.list.count() else 'No encontré coincidencias. Probá con otro nombre o concepto.');self.list.setCurrentRow(0)
    def choose(self,item):
        if item is None:return
        value=item.data(Qt.ItemDataRole.UserRole);self.selection='cas' if value=='cas' else self.entries[value];self.accept()


def open_search(window):
    dialog=TaskSearch(window)
    accepted=dialog.exec();selection=dialog.selection;query=dialog.query.text();dialog.deleteLater()
    if accepted:
        if selection=='cas':window.open_cas()
        elif selection is not None:window.open_workflow(selection,query)


def install_toolbar(window):
    bar = QToolBar('Navegación', window)
    bar.setObjectName('studioToolbar')
    bar.setMovable(False)
    bar.setFloatable(False)
    bar.setIconSize(QSize(20, 20))
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
    mark.setPixmap(window.windowIcon().pixmap(23, 23))
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

    action('Herramientas', 'blocks', window.show_home, 'studioCatalog')
    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    bar.addWidget(spacer)
    search, window.studio_search_action = action('Buscar', 'search', window.focus_tool_search)
    search.setToolTip('Buscar herramientas · Ctrl+K')
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
    compact = window.width() < 790
    if getattr(window, '_studio_compact', None) == compact:
        return
    window._studio_compact = compact
    window.studio_brand_name.setVisible(not compact)
    style = Qt.ToolButtonStyle.ToolButtonIconOnly if compact else Qt.ToolButtonStyle.ToolButtonTextBesideIcon
    for button in window.studio_aux_buttons:
        button.setToolButtonStyle(style)
    window.result_layout.setToolButtonStyle(style)
