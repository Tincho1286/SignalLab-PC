"""Escritorio científico: explorador acoplable, documentos y espacio de trabajo."""
from pathlib import Path
import json
import unicodedata
from PySide6.QtCore import Qt,QThreadPool,QSize,QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QApplication,QHeaderView,QComboBox,QMainWindow,QWidget,QHBoxLayout,QVBoxLayout,QLabel,QLineEdit,
    QPushButton,QStackedWidget,QSplitter,QTabBar,QToolButton,QScrollArea,QFrame,QDockWidget,QTreeWidget,QTreeWidgetItem,QStyle,QButtonGroup,QSizePolicy)
from .toolbox import ToolboxWindow,ToolPage
from .project import Project
from .design import configure_theme,icon
from .desktop_theme import desktop_style,configure_desktop
from .desktop_settings import desktop_settings
from .workspaces import STATIONS,STATION_FOR,ROUTES
from .theory_panel import TheoryPanel
from .result_summary import operation_label
from . import __version__
from .theme_tokens import COLORS as C,AREA_COLORS
from .cas_reference import CAS_ROUTE,CAS_SEARCH


def calculation_buttons(page):
    """Only commands in this document, never those in owned auxiliary windows."""
    def belongs(button):
        node=button
        while node is not page:
            if node is None or node.isWindow() or node.property('keepLocalAction'):return False
            node=node.parentWidget()
        return True
    return [button for button in page.findChildren(QPushButton)
            if (button.objectName()=='primary' or button.property('primaryAction')) and belongs(button)]


class WorkbenchWindow(ToolboxWindow):
    _signallab_wallpaper_host=True
    def __init__(self, *, recovery_directory=None):
        QMainWindow.__init__(self);self.setWindowTitle('SignalLab '+__version__+' · Escritorio de señales y sistemas');self.resize(1440,900);self.setMinimumSize(640,420)
        self.project=Project();self._published_signals={};self._workers=[];self._thread_pool=QThreadPool(self);self._thread_pool.setMaxThreadCount(1)
        self.current_operation=None;self.pages={};self.views={};self.category='Inicio';self.active_route=None
        from .theme_presets import restore
        restore();configure_theme();configure_desktop()
        self.setWindowIcon(QIcon(str(Path(__file__).parent/'assets'/'signallab.ico')));self.setStyleSheet(desktop_style())
        from .wallpaper import BackgroundSurface
        from .desktop_navigation import DesktopNavigation
        root = BackgroundSurface()
        root.setObjectName('desktop')
        frame = QHBoxLayout(root)
        frame.setContentsMargins(0, 0, 0, 0)
        frame.setSpacing(0)
        self.navigation = DesktopNavigation(self)
        frame.addWidget(self.navigation)
        desktop = QWidget()
        frame.addWidget(desktop, 1)
        body = QVBoxLayout(desktop)
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        self.documents=QTabBar();self.documents.setObjectName('documents');self.documents.setExpanding(False);self.documents.setMovable(True);self.documents.setUsesScrollButtons(True);self.documents.setElideMode(Qt.TextElideMode.ElideRight);self.documents.currentChanged.connect(self.activate_document);self.documents.tabCloseRequested.connect(self.close_document);body.addWidget(self.documents)
        heading=QWidget();self.heading=heading;heading.setObjectName('documentHeading');row=QHBoxLayout(heading);row.setContentsMargins(24,12,24,13);row.setSpacing(9)
        titles=QVBoxLayout();titles.setSpacing(0);row.addLayout(titles,1)
        self.area_path=QToolButton();self.area_path.setObjectName('documentArea');self.area_path.setCursor(Qt.CursorShape.PointingHandCursor);self.area_path.clicked.connect(lambda:self.show_area(self.navigation_area));self.area_path.hide()
        titles.addWidget(self.area_path,0,Qt.AlignmentFlag.AlignLeft)
        self.title=QLabel('Herramientas');self.title.setObjectName('pageTitle');self.title.setWordWrap(True);titles.addWidget(self.title)
        self.subtitle=QLabel();self.subtitle.setObjectName('muted');self.subtitle.setWordWrap(True);self.subtitle.hide();titles.addWidget(self.subtitle)
        self.back=QPushButton('Volver a resultados');self.back.clicked.connect(lambda:self.show_menu('Proyecto'));self.back.hide();row.addWidget(self.back)
        self.favorite_action = QToolButton()
        self.favorite_action.setObjectName('favoriteTool')
        self.favorite_action.setCheckable(True)
        self.favorite_action.setIconSize(QSize(18, 18))
        self.favorite_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.favorite_action.clicked.connect(self.toggle_favorite)
        self.favorite_action.hide()
        row.addWidget(self.favorite_action)
        self.operation_menu=QToolButton();self.operation_menu.setText('Operaciones');self.operation_menu.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup);row.addWidget(self.operation_menu)
        self.calculate_action=QPushButton('Calcular');self.calculate_action.setObjectName('primary');self.calculate_action.setIcon(icon('run',C['on_primary']));self.calculate_action.setIconSize(QSize(16,16));self.calculate_action.setMinimumWidth(124);self.calculate_action.setToolTip('Calcular con los datos actuales · Ctrl+Enter');self.calculate_action.clicked.connect(self.calculate_active);row.addWidget(self.calculate_action);self.current_calculate=None
        self.result_layout = QToolButton()
        self.result_layout.setObjectName('resultLayoutAction')
        self.result_layout.setCheckable(True)
        self.result_layout.setIconSize(QSize(17,17))
        self.result_layout.setCursor(Qt.CursorShape.PointingHandCursor)
        self.result_layout.clicked.connect(lambda: self.desktop_keys.toggle_output())
        self.result_layout.hide()
        row.addWidget(self.result_layout)
        self._layout_workspace = None
        self.help=QToolButton();self.help.setText('Ayuda');self.help.setObjectName('contextHelp');self.help.setIcon(icon('book',C['green']));self.help.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon);self.help.clicked.connect(self.open_help);row.addWidget(self.help);body.addWidget(heading)
        from .workflow_selector import WorkflowSelector
        self.variant_strip=WorkflowSelector(self)
        body.addWidget(self.variant_strip)
        self.stack=QStackedWidget();body.addWidget(self.stack,1);self.setCentralWidget(root)
        self.build_explorer();self.build_workspace()
        from .studio_shell import install_toolbar
        self.build_menus();install_toolbar(self)
        from .desktop_keys import DesktopKeys
        self.desktop_keys=DesktopKeys(self)
        self.cancel_button=QPushButton('Cancelar cálculo');self.cancel_button.clicked.connect(self._cancel_operations);self.cancel_button.hide();self.statusBar().addPermanentWidget(self.cancel_button)
        self._primary_timer=QTimer(self);self._primary_timer.setInterval(300);self._primary_timer.timeout.connect(self._refresh_primary_action);self._primary_timer.start()
        self.settings=desktop_settings();geometry=self.settings.value('geometry');state=self.settings.value('studio/panels')
        self.recent_tools = self._load_tool_keys('studio/recent-tools')[:4]
        self.favorite_tools = self._load_tool_keys('studio/favorite-tools')
        if geometry:self.restoreGeometry(geometry)
        if state:self.restoreState(state)
        self.explorer_dock.hide()
        available=self.screen().availableGeometry()
        self.resize(min(self.width(),available.width()),min(self.height(),available.height()))
        self.move(max(available.left(),min(self.x(),available.right()-self.width()+1)),max(available.top(),min(self.y(),available.bottom()-self.height()+1)))
        self.show_home()
        from .update_ui import UpdateController
        self.updates=UpdateController(self)
        from .wallpaper import refresh
        refresh(self)
        from .session_desktop import SessionController
        self.sessions = SessionController(self, recovery_directory)
    def paintEvent(self,event):
        super().paintEvent(event)
        from .wallpaper import paint_window
        paint_window(self)
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if hasattr(self,'studio_toolbar'):
            from .studio_shell import adapt_shell
            adapt_shell(self)
        if hasattr(self, '_primary_timer'):
            self._refresh_primary_action()
    def import_matlab(self):
        from PySide6.QtWidgets import QFileDialog,QMessageBox
        from .matlab_import_dialog import MatlabImportDialog
        path,_=QFileDialog.getOpenFileName(self,'Importar señal MATLAB','','MATLAB (*.mat *.m)')
        if not path:return
        try:
            dialog=MatlabImportDialog(path,parent=self)
            if dialog.exec():
                value=dialog.result_signal;self.publish(value,operation='Importación MATLAB');self.workspace_dock.show();self.statusBar().showMessage('Señal importada: '+value.name+' · disponible para reutilizar en las herramientas.')
        except Exception as exc:QMessageBox.warning(self,'No se pudo importar',str(exc))
    def build_explorer(self):
        from .tool_catalog import AREAS
        self.explorer_dock=QDockWidget('Herramientas',self);self.explorer_dock.setObjectName('toolsDock');self.explorer_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea|Qt.DockWidgetArea.RightDockWidgetArea)
        panel=QWidget();panel.setObjectName('explorerPanel');layout=QVBoxLayout(panel);layout.setContentsMargins(8,8,8,8);layout.setSpacing(2)
        brand=QWidget();brand_row=QHBoxLayout(brand);brand_row.setContentsMargins(3,2,3,7);brand_row.setSpacing(9)
        mark=QLabel();mark.setPixmap(self.windowIcon().pixmap(34,34));mark.setFixedSize(36,36);brand_row.addWidget(mark)
        wordmark=QVBoxLayout();wordmark.setSpacing(1);name=QLabel('SignalLab');name.setObjectName('brand');wordmark.addWidget(name)
        caption=QLabel('SEÑALES Y SISTEMAS');caption.setObjectName('brandCaption');wordmark.addWidget(caption);brand_row.addLayout(wordmark,1);layout.addWidget(brand)
        self.search=QLineEdit();self.search.setObjectName('toolSearch');self.search.setPlaceholderText('Buscar herramientas…');self.search.setToolTip('Buscar en toda la app · Ctrl+K');self.search.addAction(icon('search'),QLineEdit.ActionPosition.LeadingPosition);self.search.setClearButtonEnabled(True);layout.addWidget(self.search)
        self.cas_button=QToolButton();self.cas_button.setText('Calculadora CAS');self.cas_button.setIcon(icon('calculator'));self.cas_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon);self.cas_button.setObjectName('areaNavigation');self.cas_button.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed);self.cas_button.setCheckable(True);self.cas_button.clicked.connect(self.open_cas);layout.addWidget(self.cas_button)
        self.area_buttons={};self.area_group=QButtonGroup(self);self.area_group.setExclusive(True)
        for key,title,description,symbol in AREAS:
            button=QToolButton();button.setText(title);button.setIcon(icon(symbol,AREA_COLORS[key]));button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon);button.setCheckable(True);button.setObjectName('areaNavigation');button.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed);button.setToolTip(description)
            button.clicked.connect(lambda checked=False,value=key:self.show_area(value));self.area_group.addButton(button);self.area_buttons[key]=button;layout.addWidget(button)
        self.tool_list_title=QLabel('Acceso directo');self.tool_list_title.setObjectName('sectionTitle');layout.addWidget(self.tool_list_title)
        self.tree=QTreeWidget();self.tree.setMouseTracking(True);self.tree.setHeaderHidden(True);self.tree.setRootIsDecorated(False);self.tree.setIndentation(0);self.tree.setWordWrap(True);self.tree.setUniformRowHeights(False);self.tree.setTextElideMode(Qt.TextElideMode.ElideNone);self.tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff);layout.addWidget(self.tree,1)
        from .catalog_delegate import CatalogDelegate
        self.tree.setItemDelegate(CatalogDelegate(self.tree));self.current_entry=None;self.navigation_area=None;self._render_tools('')
        self.tree.itemClicked.connect(self.choose_tool);self.tree.itemActivated.connect(self.choose_tool);self.search.textChanged.connect(self.filter_tools);self.search.returnPressed.connect(self.open_first_match)
        self.explorer_dock.setWidget(panel);self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea,self.explorer_dock);self.resizeDocks([self.explorer_dock],[265],Qt.Orientation.Horizontal)
    def _render_tools(self,query):
        from .tool_catalog import ENTRIES,AREA_BY_ID,BY_KEY
        from .tool_search import find_tools, rank, tokens
        self.tree.blockSignals(True);self.tree.clear();self.tool_nodes=[];self.area_nodes={};self.operation_nodes={}
        shortcuts={('basic','generate'),('system_analysis',0),('course_tools','fir'),('fourier',0),('sampling',0)}
        hits,entries=[],[]
        if query.strip():hits=find_tools(query)
        elif self.navigation_area:entries=[e for e in ENTRIES if e['area']==self.navigation_area]
        else:entries=[e for e in ENTRIES if e['key'] in shortcuts]
        self.tool_list_title.setText('Resultados de búsqueda' if query.strip() else AREA_BY_ID[self.navigation_area][1] if self.navigation_area else 'Acceso directo')
        for entry in entries:
            text=entry['title'];target=entry['route']
            node=QTreeWidgetItem([text]);node.setData(0,Qt.ItemDataRole.UserRole,target);node.setToolTip(0,entry['summary']);self.tree.addTopLevelItem(node);self.tool_nodes.append((node,entry['title']));self.operation_nodes[entry['key']]=node
        for hit in hits:
            node=QTreeWidgetItem([hit.title+'\n'+AREA_BY_ID[hit.area][1]])
            node.setData(0,Qt.ItemDataRole.UserRole+2,(hit.key,hit.settings))
            node.setToolTip(0,hit.summary);self.tree.addTopLevelItem(node);self.tool_nodes.append((node,hit.title))
            self.operation_nodes.setdefault(BY_KEY[hit.key]['key'],node)
        cas_match=rank(tokens(query),(tokens('Calculadora CAS'),),tokens(CAS_SEARCH)) is not None
        if cas_match:
            node=QTreeWidgetItem(['Calculadora CAS\nMatemática simbólica']);node.setData(0,Qt.ItemDataRole.UserRole,CAS_ROUTE);self.tree.addTopLevelItem(node);self.tool_nodes.append((node,'Calculadora CAS'))
        if not entries and not hits and not cas_match:
            node=QTreeWidgetItem(['No se encontraron herramientas. Probá con otro nombre, como FIR, polos o energía.']);node.setFlags(Qt.ItemFlag.NoItemFlags);self.tree.addTopLevelItem(node)
        self.tree.itemDelegate().update_heights();self.tree.blockSignals(False);self._select_navigation()
    def _select_navigation(self):
        self.navigation.select(self.navigation_area, catalog=self.stack.currentWidget() is self.pages.get(('browser',)))
        self.cas_button.setChecked(self.category=='CAS')
        self.area_group.setExclusive(False)
        for area,button in self.area_buttons.items():button.setChecked(area==self.navigation_area)
        self.area_group.setExclusive(True)
        entry=getattr(self,'current_entry',None)
        node=self.operation_nodes.get(entry['key']) if entry else None
        if node is not None:self.tree.setCurrentItem(node);self.tree.scrollToItem(node)
    def _sync_navigation(self):
        entry=getattr(self,'current_entry',None)
        if entry is not None and self.navigation_area!=entry['area']:
            self.navigation_area=entry['area'];self._render_tools(self.search.text())
        else:self._select_navigation()

    def build_workspace(self):
        self.workspace_dock=QDockWidget('Espacio de trabajo · resultados calculados',self);self.workspace_dock.setObjectName('workspaceDock')
        self.workspace_tree=QTreeWidget();self.workspace_tree.setHeaderLabels(['Nombre','Tipo','Operación']);self.workspace_tree.setRootIsDecorated(False);self.workspace_tree.setAlternatingRowColors(True);self.workspace_tree.itemDoubleClicked.connect(self.open_workspace_record);self.workspace_dock.setWidget(self.workspace_tree);self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea,self.workspace_dock);self.workspace_dock.hide()
    def build_menus(self):
        from .tool_catalog import AREAS,ENTRIES
        file = self.menuBar().addMenu('Archivo')
        file.addAction('Importar señal MATLAB…', self.import_matlab)
        self.populate_session_menu(file.addMenu('Sesiones'))
        from .result_comparison import open_comparison
        results=self.menuBar().addMenu('Resultados');results.addAction('Comparar resultados…',lambda:open_comparison(self))
        tools=self.menuBar().addMenu('Herramientas');tools.addAction('Calculadora CAS',self.open_cas,'Ctrl+Shift+C');tools.addSeparator()
        for area,title,_,_ in AREAS:
            menu=tools.addMenu(title);menu.addAction('Ver herramientas',lambda checked=False,value=area:self.show_area(value));menu.addSeparator()
            for entry in [e for e in ENTRIES if e['area']==area]:menu.addAction(entry['title'],lambda checked=False,value=entry:self.open_workflow(value))
        view=self.menuBar().addMenu('Vista');view.addAction(self.explorer_dock.toggleViewAction());view.addAction(self.workspace_dock.toggleViewAction());view.addSeparator();view.addAction('Concentrarse en el documento',self.focus_document,'F11');view.addAction('Restablecer distribución',self.reset_layout)
        from .appearance import install_menu
        install_menu(self,view.addMenu('Tema'))
        help_menu=self.menuBar().addMenu('Ayuda');help_menu.addAction('Ayuda de la herramienta',self.open_help,'F1');help_menu.addAction('Biblioteca',lambda:self.show_menu('Biblioteca'));help_menu.addAction('Funciones de las fórmulas…',self.show_function_help)
        help_menu.addAction('Interfaz de trabajo',self.show_interface_help);help_menu.addAction('Atajos de teclado…',lambda:self.desktop_keys.show_help())
        help_menu.addSeparator();help_menu.addAction('Buscar actualizaciones…',lambda:self.updates.show());help_menu.addAction('Acerca de SignalLab…',self.about)

    def about(self):
        from PySide6.QtWidgets import QMessageBox
        message=QMessageBox(self);message.setWindowTitle('Acerca de SignalLab')
        message.setIconPixmap(self.windowIcon().pixmap(64,64))
        message.setTextFormat(Qt.TextFormat.RichText)
        message.setText('<h2>SignalLab PC '+__version__+'</h2><p>Laboratorio de Sistemas y Señales.</p>')
        message.setInformativeText('Señales, sistemas, filtros, Fourier, Laplace, Z y calculadora CAS.\n\nF1 abre la ayuda de la herramienta. Los métodos numéricos y simbólicos conservan sus unidades, condiciones y límites documentados.')
        message.setStandardButtons(QMessageBox.StandardButton.Ok);message.exec()

    def show_home(self):
        self.show_area(None)

    def _load_tool_keys(self, setting):
        from .tool_catalog import BY_KEY
        try:
            data = json.loads(self.settings.value(setting, '[]', type=str))
            return list(dict.fromkeys(tuple(key) for key in data if tuple(key) in BY_KEY))
        except (TypeError, ValueError):
            return []

    def _remember_tool(self, key, entry):
        from .tool_catalog import BY_KEY
        recent = [key, *(previous for previous in self.recent_tools if BY_KEY[previous] is not entry)][:4]
        if recent != self.recent_tools:
            self.recent_tools = recent
            self.settings.setValue('studio/recent-tools', json.dumps(recent))

    def toggle_favorite(self, checked):
        from .tool_catalog import normalized_key
        key = normalized_key(self.current_operation)
        if checked == (key in self.favorite_tools):
            return
        if checked:
            self.favorite_tools.append(key)
        else:
            self.favorite_tools.remove(key)
        self.settings.setValue('studio/favorite-tools', json.dumps(self.favorite_tools))
        self.refresh_favorite(key)
        self.statusBar().showMessage('Agregada a favoritos.' if checked else 'Retirada de favoritos.', 3000)

    def refresh_favorite(self, key):
        pinned = key in self.favorite_tools
        self.favorite_action.setChecked(pinned)
        self.favorite_action.setIcon(icon('star', C['amber'] if pinned else C['muted']))
        what = 'esta variante' if len(self.current_entry['variants']) > 1 else 'esta herramienta'
        label = f'Quitar {what} de favoritos' if pinned else f'Guardar {what} en favoritos'
        self.favorite_action.setAccessibleName(label)
        self.favorite_action.setToolTip(label)
        self.favorite_action.show()

    def show_area(self,area,*,preserve_query=False):
        from .tool_browser import ToolBrowser
        from .tool_catalog import AREA_BY_ID
        key=('browser',)
        if key not in self.pages:
            self.pages[key]=ToolBrowser(self)
            self.stack.addWidget(self.pages[key])
        browser=self.pages[key]
        self._browser_location=area
        if browser.area != area or not preserve_query:
            browser.select_area(area)
        else:
            browser.refresh_shortcuts()
            browser.adapt_grid()
        self.variant_strip.hide()
        self.active_route=self.current_operation=self.current_entry=self.current_calculate=None
        self.category=AREA_BY_ID[area][1] if area else 'Inicio'
        self.activate_view(key,'Herramientas',browser)
        for control in (self.help,self.back,self.operation_menu,self.calculate_action):
            control.hide()
        self.navigation_area=area
        self._render_tools(self.search.text())
        self.tree.clearSelection()
    def route_for_key(self,key):return ROUTES[key]
    def open_workflow(self,entry):
        key=self.variant_strip.memory.get(entry['key'],entry['key'])
        self.open_tool(ROUTES[key])

    def open_tool_search(self,key,settings=()):
        route=ROUTES[tuple(key)]
        self.open_tool(route)
        if settings:
            panel=self.pages[route].panel
            for field,index in settings:
                getattr(panel,field).setCurrentIndex(index)
    def operation_changed(self,item):
        from .tool_catalog import locate,AREA_BY_ID,ENTRIES,normalized_key
        entry=locate(item)
        if entry is None:return
        from .workflow_choices import variant_title
        option=variant_title(entry,normalized_key(item))
        detail_label=f"{entry['title']} · {option}" if option else entry['title']
        view=self.views.get(getattr(self,'active_route',None))
        if view is not None and self.stack.currentWidget() is view:
            page=getattr(view,'active_page',view.widget())
            if locate(page.tool_item) is entry:
                for index in range(self.documents.count()):
                    if self.documents.tabData(index)==self.active_route:self.documents.setTabText(index,entry['title']);self.documents.setTabToolTip(index,detail_label)
        self.current_operation=tuple(item);self.variant_strip.set_entry(entry,item)
        self.current_entry=entry;self.title.setText(entry['title']);self.title.setToolTip(entry['summary']);self.category=AREA_BY_ID[entry['area']][1];self._sync_navigation();self.help.show()
        self.refresh_favorite(normalized_key(item))
        self.area_path.setText(self.category+'  ›');self.area_path.setAccessibleName('Ver herramientas de '+self.category);self.refresh_context_path()
        self.operation_menu.hide();page=self.pages.get(tuple(item));self.current_calculate=None
        if page is not None:
            buttons=calculation_buttons(page)
            if buttons:self.current_calculate=buttons[0]
        self.refresh_result_layout_action()
        self._refresh_primary_action();self.statusBar().showMessage(self.category+' / '+entry['title'])

    def refresh_context_path(self):
        tool_active = self.current_entry is not None and self.category not in ('Proyecto', 'Biblioteca', 'CAS')
        self.area_path.setVisible(tool_active and not self._studio_short)

    def _refresh_primary_action(self):
        page=self.pages.get(getattr(self,'current_operation',None))
        candidates=[]
        if page is not None:
            candidates=calculation_buttons(page)
        visible=[button for button in candidates if button.isVisibleTo(page)]
        migrated=[button for button in candidates if button.property('commandBarAction')]
        button=next(iter(visible or migrated),None) if self.active_route is not None and self.category not in ('Proyecto','Biblioteca') else None
        self.current_calculate=button;self.calculate_action.setVisible(button is not None)
        if button is not None:
            state=getattr(page,'result_state',None) or getattr(getattr(page,'panel',None),'result_state',None)
            if state is not None:state.set_button(button)
            label = button.text()
            compact = self.width() < 850
            button.setProperty('commandBarAction', True)
            button.hide()
            self.calculate_action.setText(label if len(label) <= (12 if compact else 27) else 'Calcular')
            self.calculate_action.setAccessibleName(label)
            self.calculate_action.setToolTip(label + ' · Ctrl+Enter')
            self.calculate_action.setEnabled(button.isEnabled())
    def calculate_active(self):
        self._refresh_primary_action();button=self.current_calculate
        if button is not None and button.isEnabled():button.click();self._refresh_primary_action()

    def _document_index(self, key):
        return next((i for i in range(self.documents.count()) if self.documents.tabData(i) == key), -1)

    def _add_document_tab(self, key, title):
        index = self.documents.addTab(title)
        self.documents.setTabData(index, key)
        self.documents.setTabToolTip(index, title)
        slot = QWidget()
        spacing = QHBoxLayout(slot)
        spacing.setContentsMargins(4, 0, 7, 0)
        close = QToolButton(slot)
        close.setObjectName('documentClose')
        close.setIcon(icon('close'))
        close.setIconSize(QSize(14, 14))
        close.setFixedSize(22, 22)
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.setAccessibleName(f'Cerrar pestaña {title}')
        close.setToolTip('Cerrar pestaña')
        close.clicked.connect(lambda: self.documents.tabCloseRequested.emit(self._document_index(key)))
        spacing.addWidget(close)
        self.documents.setTabButton(index, QTabBar.ButtonPosition.RightSide, slot)
        return index

    def activate_view(self,key,title,page):
        browser=key==('browser',)
        self.documents.blockSignals(True)
        index = self._document_index(key)
        if index < 0:
            index = self._add_document_tab(key, title)
        self.documents.setCurrentIndex(index);self.documents.blockSignals(False);self.title.setText(title);self.stack.setCurrentWidget(page)
        self.title.setToolTip('')
        self.heading.setVisible(not browser)
        self.area_path.hide()
        self.subtitle.hide()
        self.favorite_action.hide()
        self.studio_search_action.setVisible(not browser or self._browser_location is not None)
        self._refresh_document_tabs()
        workspace = self.desktop_keys.workspace()
        if workspace is not self._layout_workspace:
            if self._layout_workspace is not None:
                self._layout_workspace.expansionChanged.disconnect(self.refresh_result_layout_action)
            self._layout_workspace = workspace
            if workspace is not None:
                workspace.expansionChanged.connect(self.refresh_result_layout_action)
        self.refresh_result_layout_action()
        self.statusBar().showMessage(title)

    def refresh_result_layout_action(self, *_):
        workspace = self._layout_workspace
        expanded = workspace is not None and workspace.output_expanded
        self.result_layout.setVisible(workspace is not None)
        if workspace is not None:
            self.result_layout.setChecked(expanded)
            label = 'Restaurar paneles' if expanded else 'Ampliar resultado'
            self.result_layout.setText(label)
            self.result_layout.setAccessibleName(label)
            self.result_layout.setToolTip(label+' · Ctrl+Mayús+R')
            self.result_layout.setIcon(icon('restore' if expanded else 'expand'))
    def activate_document(self,index):
        key=self.documents.tabData(index)
        if not key:return
        if key[0]=='browser':
            self.show_area(self._browser_location, preserve_query=True)
        elif key==CAS_ROUTE:self.open_cas()
        elif key[0]=='home':self.show_home()
        elif key[0]=='menu':self.show_menu(key[1], browse=None)
        elif key[0]=='area':self.show_area(key[1])
        elif key in self.views:self.open_tool(key)
    def close_document(self,index):
        if not 0 <= index < self.documents.count():
            return
        self.documents.blockSignals(True);self.documents.removeTab(index);self.documents.blockSignals(False)
        if self.documents.count():self.activate_document(self.documents.currentIndex())
        else:self.show_home()
        self.statusBar().showMessage('Documento cerrado. Sus datos se conservan durante esta sesión.')

    def _refresh_document_tabs(self):
        browser_only=self.documents.count()==1 and self.documents.tabData(0)==('browser',)
        self.documents.setVisible(not browser_only and getattr(self,'_focus_panels',None) is None)
    def open_tool(self,item):
        from .tool_catalog import BY_KEY,locate,normalized_key,AREA_BY_ID
        from .problem_document import ProblemDocument,document_route
        from .tool_groups import members
        item=tuple(item);requested=item
        if item==CAS_ROUTE:self.open_cas();return
        if item[1]=='workspace':
            entry=BY_KEY[tuple(item[2])];doc_route=document_route(entry)
            document=self.pages.get(doc_route)
            item=document.current_route if document is not None else ROUTES[entry['key']]
        elif item[1]=='tool_group':item=ROUTES[members(item[2])[0]]
        elif item[1]=='filter_lab':item=ROUTES['system_analysis',0]
        key=normalized_key(item);route=ROUTES[key];entry=locate(route)
        if entry is None:raise ValueError('La herramienta no tiene una ubicación pública: '+str(key))
        doc_route=document_route(entry)
        if doc_route not in self.pages:
            document=ProblemDocument(entry);self.pages[doc_route]=document
            view=QScrollArea();view.setWidgetResizable(True);view.setFrameShape(QFrame.Shape.NoFrame);view.setWidget(document);self.views[doc_route]=view;self.stack.addWidget(view)
        document=self.pages[doc_route]
        if route not in self.pages:self.pages[route]=ToolPage(self,route)
        page=self.pages[route];document.select_page(page);self.pages[requested]=page if requested[1]!='workspace' else document
        from .tool_workspace import install as install_workspace
        workspace=install_workspace(page)
        view=self.views[doc_route];view.active_page=page;view.panel=getattr(page,'panel',None);view.context=getattr(page,'context',None)
        from .navigation import TRANSFORM_ALIASES
        if item[1:3] in TRANSFORM_ALIASES:page.panel.select_legacy(item[1:3])
        if item[1:3]==('systems',7):page.panel.fields['method'].setCurrentIndex(1)
        self.active_route=doc_route;self.category=AREA_BY_ID[entry['area']][1];self.activate_view(doc_route,entry['title'],view);self.back.hide();self.help.show()
        self._configure_readable_layouts();self.operation_changed(route)
        self._remember_tool(key, entry)
        if workspace is not None:
            view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded);view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    def ensure_cas(self):
        from .cas_panel import CasWorksheet
        if CAS_ROUTE not in self.pages:
            page=CasWorksheet(self);self.pages[CAS_ROUTE]=page;self._add_auxiliary_view(CAS_ROUTE,page,scroll=False)
        return self.pages[CAS_ROUTE]

    def open_cas(self,*_):
        page=self.ensure_cas();self.active_route=CAS_ROUTE;self.current_operation=CAS_ROUTE;self.current_entry=None;self.category='CAS';self.navigation_area=None
        self.variant_strip.hide();self.operation_menu.hide();self.back.hide();self.help.show();self.activate_view(CAS_ROUTE,'Calculadora CAS',self.views[CAS_ROUTE])
        self._render_tools(self.search.text());self._configure_readable_layouts();self._refresh_primary_action();page.input.setFocus()

    def open_station(self,index):self.open_tool(ROUTES[STATIONS[index][3][0]])
    def _add_auxiliary_view(self,key,page,*,scroll=True):
        view = page
        if scroll:
            view=QScrollArea();view.setWidgetResizable(True);view.setFrameShape(QFrame.Shape.NoFrame);view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff);view.setWidget(page);view.active_page=page
        view.setProperty('auxiliaryDocument',True);self.views[key]=view;self.stack.addWidget(view)
    def show_menu(self,category, *, browse=True):
        if category not in ('Proyecto','Biblioteca'):self.show_home();return
        key=('menu',category)
        if key not in self.pages:
            if category=='Proyecto':
                page=self.build_project_page();self._add_auxiliary_view(key,page)
            else:
                page=TheoryPanel(self.open_tool,self.open_library_example);self._add_auxiliary_view(key,page,scroll=False)
            self.pages[key]=page;self._configure_readable_layouts()
        if category=='Biblioteca' and browse is not None:self.pages[key].set_return_route(None)
        self.variant_strip.hide();self.current_calculate=None;self.operation_menu.hide();self.calculate_action.hide()
        self.category=category;self.activate_view(key,'Resultados' if category=='Proyecto' else 'Biblioteca',self.views[key]);self.help.hide();self.back.hide()
        self.navigation.select(None)
        if category=='Biblioteca' and browse:
            library=self.pages[key];library.topic_toggle.setChecked(True);library.search.setFocus()
    def open_library_example(self,example):
        from .library_actions import apply_example
        apply_example(self,example)
    def show_function_help(self, article=None):
        origin = self.current_operation if self.category not in ('Inicio','Proyecto','Biblioteca') else None
        self.show_menu('Biblioteca', browse=False)
        library = self.pages['menu','Biblioteca']
        library.set_return_route(origin)
        if isinstance(article, str):library.select_article(article, kind=3)
        else:library.select_functions()
    def show_interface_help(self):
        from .desktop_help import ARTICLE_ID
        self.show_menu('Biblioteca', browse=False);self.pages['menu','Biblioteca'].select_article(ARTICLE_ID)
    def open_help(self):
        if self.current_operation and self.category not in ('Inicio','Proyecto','Biblioteca'):self.show_tool_help(self.current_operation)
        else:self.show_menu('Biblioteca')
    def show_tool_help(self,item):
        from .guide_context import configured_guide, field_in_focus
        page=self.pages.get(tuple(item))
        context=configured_guide(item,getattr(page,'panel',None))
        field=field_in_focus(page,QApplication.focusWidget())
        self.show_menu('Biblioteca', browse=False)
        self.pages['menu','Biblioteca'].select_tool(item,context=context,focused_field=field)
    def choose_tool(self,node,column=0):
        hit=node.data(0,Qt.ItemDataRole.UserRole+2)
        if hit:
            self.open_tool_search(*hit)
            return
        route=node.data(0,Qt.ItemDataRole.UserRole)
        if route:
            if tuple(route)==CAS_ROUTE:self.open_cas();return
            from .tool_catalog import locate
            self.open_workflow(locate(tuple(route)));return
        branch=node.data(0,Qt.ItemDataRole.UserRole+1)
        if branch:
            self.show_area(branch[1])
            if branch[0]=='section':node.setExpanded(True)
    def filter_tools(self,text):self._render_tools(text)
    def open_first_match(self):
        if self.tool_nodes:self.choose_tool(self.tool_nodes[0][0])

    def focus_tool_search(self,query=''):
        from .command_palette import open_search
        open_search(self,query if isinstance(query,str) else '')

    def focus_document(self):
        panels=(self.explorer_dock,self.workspace_dock)
        previous=getattr(self,'_focus_panels',None)
        if previous is None:
            self._focus_panels=tuple(panel.isVisible() for panel in panels)
            for panel in panels:panel.hide()
            self.navigation.hide()
        else:
            self._focus_panels=None
            for panel,visible in zip(panels,previous):panel.setVisible(visible)
            self.navigation.show()
        self._refresh_document_tabs()

    def reset_layout(self):
        self._focus_panels=None
        self.navigation.show()
        self.explorer_dock.hide();self.workspace_dock.hide();self._refresh_document_tabs()
    def refresh_project(self):
        super().refresh_project()
        if not hasattr(self,'workspace_tree'):return
        self.workspace_tree.clear()
        for record in reversed(self.project.headers()):
            node=QTreeWidgetItem([record['title'],{'signal':'Señal','system':'Sistema','state_space':'Estados','calculation':'Cálculo'}.get(record['kind'],record['kind']),operation_label(record['operation'])]);node.setData(0,Qt.ItemDataRole.UserRole,record['id']);self.workspace_tree.addTopLevelItem(node)
        self.workspace_tree.resizeColumnToContents(0)
    def open_workspace_record(self,node,column=0):
        self.focus_result(node.data(0,Qt.ItemDataRole.UserRole))
    def focus_result(self,key):
        self.show_menu('Proyecto')
        if not self.pages['menu','Proyecto'].focus_record(key):
            self.statusBar().showMessage('Este resultado ya no está en la sesión.')

    def capture_handoff(self):
        from .input_handoff import HandoffOrigin
        document=self.documents.tabData(self.documents.currentIndex())
        if not document:return None
        space=self.desktop_keys.workspace()
        result=space is not None and (not space.compact or space.tabs.currentWidget() is space.results)
        key=None
        if document==('menu','Proyecto'):
            row=self.project_list.currentRow()
            if 0<=row<len(self.visible_records):key=self.visible_records[row]['id']
        route=self.current_operation if document==CAS_ROUTE or len(document)>1 and document[1]=='workspace' else None
        return HandoffOrigin(document,route,key,self.title.text(),result)

    def return_to_handoff(self,origin):
        if origin.record is not None:
            self.focus_result(origin.record)
        elif origin.route is not None:
            self.open_tool(origin.route)
            space=self.desktop_keys.workspace()
            if origin.result and space is not None:space.show_results()
        elif origin.document[0]=='menu':
            self.show_menu(origin.document[1],browse=None)
        else:
            self.show_area(self._browser_location,preserve_query=True)

    def finish_handoff(self,origin,summary,key=None,field=None,*,worksheet=None):
        from .input_handoff import InputHandoff
        space=worksheet or self.desktop_keys.workspace()
        if space is None:return
        current=(CAS_ROUTE,CAS_ROUTE) if worksheet is not None else (self.documents.tabData(self.documents.currentIndex()),self.current_operation)
        back=None
        if origin is not None and current!=(origin.document,origin.route):
            back=lambda:self.return_to_handoff(origin)
        show_record=(lambda:self.focus_result(key)) if key is not None else None
        space.show_handoff(InputHandoff(summary,origin.title if origin else '',back,show_record))
        if worksheet is None:
            space.show_inputs()
            if field is not None and space.inputs.isAncestorOf(field):
                self.desktop_keys.reveal(field.focusProxy() or field)
        self.statusBar().showMessage(summary)

    def show_record(self,index):
        before=self.stack.currentWidget()
        super().show_record(index)
        if self.stack.currentWidget() is not before:
            self.subtitle.show()
    def _run_operation(self,message,function,on_success):
        from .result_journal import ResultJournal
        journal=ResultJournal(self,message)
        from .calculation_notes import capture
        def calculate():
            with capture() as records:result=function()
            journal.calculation_notes=list(records.values())
            return result
        route=self.current_operation
        page=self.pages.get(route)
        workspace=getattr(page,'workspace',None)
        if workspace is not None and not self._workers:
            workspace.clear_input_issue()
        def accepted(result):
            journal.accept(result,on_success)
            if workspace is not None:workspace.show_results()
        return super()._run_operation(message,calculate,accepted,input_context=workspace is not None)

    def present_input_failure(self, worker, message):
        page = self.pages.get(worker.origin)
        workspace = getattr(page, 'workspace', None)
        if workspace is None:
            return False
        current = self.desktop_keys.active_page() is page
        workspace.show_input_issue(message, reveal=current)
        if current:
            self.statusBar().showMessage('Revisá los datos del cálculo.')
        return True

    def _run_view_operation(self,message,function,on_success):
        """Build a view cache from already registered data, without duplicating it."""
        def accept(result):
            self._last_calculation_notes=[];on_success(result)
        return super()._run_operation(message,function,accept)
    def send_system(self,value,key,item):
        origin=self.capture_handoff()
        target=self._load_system(value,key,item)
        if target is not None:
            self.finish_handoff(origin,'Sistema cargado · '+str(value.name),key)
        elif origin is not None:
            self.return_to_handoff(origin)

    def _load_system(self,value,key,item):
        from .navigation import FILTER_KEYS,TRANSFORM_ALIASES
        if item[1:3] in FILTER_KEYS or item[1:3] in TRANSFORM_ALIASES:
            self.open_tool(item);panel=self.stack.currentWidget().panel
            if hasattr(panel,'set_system'):panel.set_system(value,key)
            else:
                page=self.pages[item]
                if hasattr(page,'context'):page.context.parents=[key] if key else [];page.context.system_id=key
                panel._accept_system(value)
                if hasattr(page,'pole_editor'):
                    from .systems_panel import list_text
                    import numpy as np
                    zeros,poles=value.poles_zeros();panel.domain.setCurrentIndex(0 if value.domain=='digital' else 1)
                    panel.fields['zeros'].setText(list_text(zeros));panel.fields['poles'].setText(list_text(poles))
                    nonzero=value.b[np.flatnonzero(value.b)];panel.fields['gain'].setText(list_text([nonzero[0] if len(nonzero) else 0]));page.pole_editor.redraw()
                    callback=getattr(page.context,'on_system_loaded',None)
                    if callback:callback(value)
                    if hasattr(page,'result_state'):page.result_state.accept(page.result_state.snapshot())
            return panel
        return super().send_system(value,key,item)
    def open_root_analysis(self,system,key=None):
        route=ROUTES['system_analysis',0];self.open_tool(route);self.pages[route].panel.inspect_system_roots(system,key)
    def send_signal(self,value,key,item):
        origin=self.capture_handoff()
        field=self._load_signal(value,key,item)
        if field is None:
            if origin is not None:self.return_to_handoff(origin)
            return
        label=field.title() if hasattr(field,'title') and callable(field.title) else None
        source_key=getattr(field,'loaded_reference_id',None) or key
        self.finish_handoff(origin,'Entrada cargada'+(f' en {label}' if label else '')+' · '+str(value.name),source_key,field)

    def send_model(self,value,key,item):
        origin=self.capture_handoff()
        if super().send_model(value,key,item) is not None:
            self.finish_handoff(origin,'Modelo de estados cargado · '+str(value.name),key)

    def _load_signal(self,value,key,item):
        if item[1:3] in (('communications','pulse'),('communications','awgn'),
                          ('communications','multipath'),('communications','fading'),('communications','carrier'),
                          ('communications','impairments'),('communications','interference'),
                          ('communications','propagation'),('communications','channel_pipeline'),
                          ('communications','receive'),('communications','decide')):
            self.open_tool(item);panel=self.pages[tuple(item)].panel
            return panel.receive_signal(self.project.get(key) if key else value,key)
        if item[1:3]==('state_space','simulation'):
            self.open_tool(item);panel=self.pages[tuple(item)].panel;panel.domain.setCurrentIndex(1 if value.domain=='discrete' else 0)
            index=max(0,panel.inputs.channel.currentIndex())
            if panel.inputs.count<1:self.statusBar().showMessage('Definí las entradas del modelo en B y D antes de cargar la señal.');return
            field=panel.inputs.field(index);field.set_source(self.project.get(key) if key else value,key)
            return field
        if item[1]=='fir_window':
            self.open_tool(item);field=self.pages[tuple(item)].panel.h;field.set_source(self.project.get(key) if key else value,key);return field
        if item[1]=='signal_product' or item[1:3]==('basic','sum'):
            self.open_tool(item);self.pages[tuple(item)].panel.domain.setCurrentIndex(0 if value.domain=='discrete' else 1)
        if item[1]=='signal_editor':
            self.open_tool(item);panel=self.pages[tuple(item)].panel;panel.receive(value,key);return panel
        if item[1]=='basic' and item[2] in ('generate','measures'):
            self.open_tool(item)
            page=self.pages[tuple(item)]
            selector=page.panel.domain if item[2]=='measures' else page.source_domain
            selector.setCurrentIndex(0 if value.domain=='discrete' else 1)
        if item[1]=='dsp_extensions' and item[2] in ('hilbert','stft'):
            self.open_tool(item);panel=self.pages[tuple(item)].panel;panel.domain.setCurrentIndex(0 if value.domain=='discrete' else 1)
        if item[1:3]==('fourier',6):
            self.open_tool(item);return self.pages[tuple(item)].panel.receive(value,key)
        return super().send_signal(value,key,item)
    def save_project(self):
        return self.sessions.save_dialog()

    def populate_session_menu(self, menu):
        menu.addAction('Guardar sesión completa…', self.save_project)
        menu.addAction('Abrir sesión completa…', lambda: self.sessions.open_dialog())
        menu.addAction('Incorporar resultados…', self.import_project)
        menu.addAction('Recuperar sesión anterior…', lambda: self.sessions.offer_recovery())

    def session_has_changes(self):
        return self.sessions.changed()

    def closeEvent(self,event):
        if not self.sessions.prepare_close():
            event.ignore();return
        if hasattr(self,'updates') and not self.updates.prepare_close():
            event.ignore();return
        super().closeEvent(event)
        if event.isAccepted():
            self.sessions.finish()
            self.settings.setValue('geometry',self.saveGeometry())
            self.settings.setValue('studio/panels',self.saveState())
    def _configure_readable_layouts(self):
        from PySide6.QtWidgets import QFormLayout,QScrollArea,QSizePolicy,QTabWidget
        from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
        from .plot_view import install_enlarge
        from .tool_guide import ToolGuide
        # Each registered document owns its form layout. The catalog has its own responsive cards.
        def document_widgets(widget_type):
            return [widget for view in self.views.values() for widget in view.findChildren(widget_type)]

        for toolbar in document_widgets(NavigationToolbar2QT):install_enlarge(toolbar)
        for guide in document_widgets(ToolGuide):guide.hide()
        for field in document_widgets(QLineEdit)+document_widgets(QComboBox):
            field.setMinimumHeight(34);field.setMinimumWidth(0);field.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
            if isinstance(field,QComboBox):
                if field.property('fitComboText'):
                    field.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
                else:
                    field.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon);field.setMinimumContentsLength(16)
                ancestor=field.parentWidget()
                while ancestor is not None and ancestor.objectName()!='inputSurface':ancestor=ancestor.parentWidget()
                if ancestor is not None:field.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Fixed)
        for form in document_widgets(QFormLayout):
            form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows if form.property('stackFields') else QFormLayout.RowWrapPolicy.WrapLongRows);form.setVerticalSpacing(6);form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
            form.setFormAlignment(Qt.AlignmentFlag.AlignTop);form.setAlignment(Qt.AlignmentFlag.AlignTop)
            if form.property('stackFields'):
                form.setLabelAlignment(Qt.AlignmentFlag(0))
                for row in range(form.rowCount()):
                    item=form.itemAt(row,QFormLayout.ItemRole.LabelRole)
                    if item is not None and item.widget() is not None:item.widget().setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        for tabs in document_widgets(QTabWidget):
            bar=tabs.tabBar();bar.setUsesScrollButtons(True);bar.setElideMode(Qt.TextElideMode.ElideRight)
            for index in range(tabs.count()):
                if not tabs.tabToolTip(index):tabs.setTabToolTip(index,tabs.tabText(index))
            from .result_selector import install as install_result_selector
            install_result_selector(tabs)
        for label in document_widgets(QLabel):
            if label.objectName() not in {'brand','pageTitle','resultEmpty'}:
                label.setWordWrap(True);label.setSizePolicy(label.sizePolicy().horizontalPolicy(),QSizePolicy.Policy.Fixed)
        for scroll in document_widgets(QScrollArea):scroll.setWidgetResizable(True)
        from .wallpaper import refresh
        refresh(self)
        from .responsive_tools import install_tool_columns
        for view in self.views.values():
            page=getattr(view,'active_page',view)
            workspace=getattr(page,'workspace',None)
            if workspace is None:
                if not view.property('auxiliaryDocument'):install_tool_columns(view)
            else:
                from .result_action_dock import install as install_action_dock
                install_action_dock(workspace.results)
