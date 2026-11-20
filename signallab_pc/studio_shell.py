"""A compact navigation rail, app menu and task search for the refreshed desktop."""
from PySide6.QtCore import Qt,QSize,QEvent
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QToolButton,QPushButton,QScrollArea,QDockWidget,QToolBar,QMenu,QSizePolicy,QDialog,QLineEdit,QListWidget,QListWidgetItem
from PySide6.QtGui import QAction
from .design import icon
from .theme_tokens import COLORS as C,AREA_COLORS


class NavigationRail(QWidget):
    def __init__(self,window):
        super().__init__();self.setObjectName('navigationRail');self.buttons={};self.symbols={};root=QVBoxLayout(self);root.setContentsMargins(7,10,7,10);root.setSpacing(6)
        from .tool_catalog import AREAS
        items=[('home','Inicio','home',C['accent'],window.show_home)]
        labels={'signals':'Señales','systems':'Sistemas LTI','filters':'Filtros','spectra':'Fourier','sampling':'Muestreo','transforms':'Laplace y Z','random':'Aleatorias'}
        items.extend((key,labels[key],symbol,AREA_COLORS[key],lambda checked=False,k=key:window.show_area(k)) for key,_,_,symbol in AREAS);items.append(('cas','CAS','calculator',C['purple'],window.open_cas))
        for key,title,symbol,color,callback in items:
            button=QToolButton();button.setObjectName('railItem');button.setText(title);button.setIcon(icon(symbol,color));button.setIconSize(QSize(23,23));button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon);button.setCheckable(True);button.setAccessibleName(title);button.setToolTip(title);button.setCursor(Qt.CursorShape.PointingHandCursor);button.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed);button.clicked.connect(callback);root.addWidget(button);self.buttons[key]=button;self.symbols[key]=symbol
        root.addStretch()
    def select(self,area,category):
        selected='home' if category=='Inicio' else 'cas' if category=='CAS' else area
        for key,button in self.buttons.items():button.setChecked(key==selected)
    def refresh_theme(self):
        for key,button in self.buttons.items():button.setIcon(icon(self.symbols[key],C['accent'] if key=='home' else C['purple'] if key=='cas' else AREA_COLORS[key]))

    def set_expanded(self,expanded):
        style = Qt.ToolButtonStyle.ToolButtonTextBesideIcon if expanded else Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        short_labels = {'systems':'Sistemas', 'transforms':'Laplace/Z'}
        margins = 7 if expanded else 4
        self.layout().setContentsMargins(margins,8,margins,8)
        self.layout().setSpacing(6 if expanded else 3)
        for key,button in self.buttons.items():
            button.setToolButtonStyle(style)
            button.setText(button.accessibleName() if expanded else short_labels.get(key,button.accessibleName()))
            button.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Fixed)
            button.setMinimumHeight(42 if expanded else 49)


def install_navigation(window):
    dock=QDockWidget(window);dock.setObjectName('studioNavigation');dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures);dock.setTitleBarWidget(QWidget());dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea);dock.setFixedWidth(88)
    scroll=QScrollArea();scroll.setObjectName('railScroll');scroll.setWidgetResizable(True);scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff);scroll.setFrameShape(QScrollArea.Shape.NoFrame);rail=NavigationRail(window);scroll.setWidget(rail);dock.setWidget(scroll);window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea,dock);window.explorer_dock.hide();window.studio_rail=dock;window.navigation_rail=rail


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
    bar=window.findChild(QToolBar,'mainToolbar');bar.clear();bar.setObjectName('studioToolbar');bar.setIconSize(QSize(20,20));menu=QMenu(window)
    for action in window.menuBar().actions():menu.addAction(action)
    application=QToolButton();application.setObjectName('applicationMenu');application.setIcon(icon('menu',C['text']));application.setMenu(menu);application.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup);application.setAccessibleName('Menú de la aplicación');application.setToolTip('Archivo, herramientas, vista y ayuda');bar.addWidget(application)
    brand=QWidget();row=QHBoxLayout(brand);row.setContentsMargins(4,0,14,0);row.setSpacing(8);mark=QLabel();mark.setPixmap(window.windowIcon().pixmap(28,28));row.addWidget(mark);name=QLabel('SignalLab');name.setObjectName('studioBrand');row.addWidget(name);bar.addWidget(brand);window.studio_brand_name=name
    spacer=QWidget();spacer.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Preferred);bar.addWidget(spacer)
    search=QPushButton('Buscar herramientas     Ctrl+K');search.setObjectName('studioSearch');search.setIcon(icon('search'));search.setMinimumWidth(190);search.setMaximumWidth(540);search.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed);search.setToolTip('Buscar herramientas · Ctrl+K');search.clicked.connect(lambda:open_search(window));window.studio_search_action=bar.addWidget(search);window.studio_search=search
    spacer=QWidget();spacer.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Preferred);bar.addWidget(spacer)
    window.studio_aux_buttons=[]
    for title,symbol,callback in [('Resultados','table',lambda:window.show_menu('Proyecto')),('Biblioteca','book',lambda:window.show_menu('Biblioteca'))]:
        button=QToolButton();button.setObjectName('chromeAction');button.setText(title);button.setToolTip(title);button.setAccessibleName(title);button.setIcon(icon(symbol));button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon);button.clicked.connect(callback);bar.addWidget(button);window.studio_aux_buttons.append(button)
    shortcut=QAction(window);shortcut.setShortcut('Ctrl+K');shortcut.triggered.connect(lambda:open_search(window));window.addAction(shortcut);window.menuBar().hide()
    adapt_shell(window)


def adapt_shell(window):
    """Preserve task controls and reading space on small desktop windows."""
    compact=window.width()<960;short=window.height()<650;expanded=window.width()>=1240
    if getattr(window,'_studio_density',None)==(compact,short,expanded):return
    window._studio_density=compact,short,expanded
    window.studio_rail.setFixedWidth(152 if expanded else 88)
    window.navigation_rail.set_expanded(expanded)
    if hasattr(window,'studio_brand_name'):window.studio_brand_name.setVisible(not compact)
    if hasattr(window,'studio_search'):window.studio_search.setText('Buscar herramientas' if compact else 'Buscar herramientas     Ctrl+K')
    for button in getattr(window,'studio_aux_buttons',[]):button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly if compact else Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
    window.subtitle.setVisible(not short and not window.heading.isHidden());window.title.setStyleSheet('font-size:17pt;' if compact else '')
