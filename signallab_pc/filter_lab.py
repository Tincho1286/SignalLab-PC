"""One filter document, with options for definition, design, conversion and use."""
from .active_stack import ActiveStack
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QTabBar,QComboBox,QPushButton,QLabel,QMessageBox
from .navigation import MENUS,FILTER_ALIASES as ALIASES
ROUTES={item[1:3]:item for group in MENUS.values() for item in group}
GROUPS=[('Analizar',[('system_analysis',0)]),
        ('Diseñar',[('course_tools','fir'),('course_tools','iir'),('course_tools','analog'),('systems',6),('systems',0),('fir_window',0),('systems',1),('systems',2),('systems',8)]),
        ('Ajustar',[('course_tools','gain'),('course_tools','phase')]),
        ('Ideales y por tramos',[('frequency_filter',0)]),
        ('Convertir',[('course_tools','convert')]),('Respuesta temporal',[('systems',9)])]

class FilterLab(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window;self.pages={};self.current_page=None;self.current_route=None;self.selections={};self.previous_tab=None
        root=QVBoxLayout(self);root.setContentsMargins(0,0,0,0)
        self.tabs=QTabBar(self);self.tabs.hide()
        for name,_ in GROUPS:self.tabs.addTab(name)
        self.choice=QComboBox(self);self.choice.hide()
        self.analyze_button=QPushButton('Llevar resultado al análisis');self.analyze_button.clicked.connect(self.analyze_current);self.analyze_button.hide()
        self.stack=ActiveStack();root.addWidget(self.stack,1)
        self.tabs.currentChanged.connect(self.populate);self.choice.currentIndexChanged.connect(self.activate);self.populate(0)
    def populate(self,index):
        if self.previous_tab is not None:self.selections[self.previous_tab]=self.choice.currentIndex()
        self.previous_tab=index;self.choice.blockSignals(True);self.choice.clear()
        for key in GROUPS[index][1]:self.choice.addItem(ROUTES[key][0],key)
        self.choice.setCurrentIndex(self.selections.get(index,0));self.choice.blockSignals(False);self.activate(self.choice.currentIndex())
    def activate(self,index):
        if index<0:return
        key=self.choice.itemData(index);route=ROUTES[tuple(key)]
        if route not in self.pages:
            from .toolbox import ToolPage
            self.pages[route]=ToolPage(self.window,route);self.stack.addWidget(self.pages[route])
        self.current_page=self.pages[route];self.current_route=route;self.stack.setCurrentWidget(self.current_page);self.stack.updateGeometry()
        # Existing exports/reuse keep addressing the active internal tool.
        self.window.pages[route]=self.current_page
        self.sync_view()
        self.window._configure_readable_layouts();self.window.operation_changed(route)
    def sync_view(self):
        from .navigation import FILTER_ROUTE
        view=self.window.views.get(FILTER_ROUTE)
        if view is not None:
            view.active_page=self.current_page;view.panel=getattr(self.current_page,'panel',None);view.context=getattr(self.current_page,'context',None)
    def select_route(self,item):
        key=ALIASES.get(item[1:3],item[1:3])
        for group,(_,keys) in enumerate(GROUPS):
            if key in keys:
                self.tabs.setCurrentIndex(group);self.choice.setCurrentIndex(keys.index(key));break
        if item[1:3]==('systems',7):self.current_page.panel.fields['method'].setCurrentIndex(1)
        return self.current_page
    def analyze_current(self):
        try:
            page=self.current_page;panel=page.panel;system=None;key=None
            if getattr(page,'context',None) is not None:system=getattr(page.context,'last_system',None);key=getattr(page.context,'last_system_id',None)
            if system is None and hasattr(panel,'items'):
                from .filters import Transfer
                selected=panel.selector.currentIndex()
                candidate=panel.items[selected] if 0<=selected<len(panel.items) else None
                system=candidate if isinstance(candidate,Transfer) else next((v for v in panel.items if isinstance(v,Transfer)),None)
                if system is not None and hasattr(panel,'records'):key=panel.records[next(i for i,v in enumerate(panel.items) if v is system)]
            if system is None:system=getattr(panel,'system',None)
            if system is None:raise ValueError('Calculá un filtro de coeficientes primero. Los ideales se analizan en su propia vista de H; podés convertirlos con ventana para obtener un FIR.')
            page=self.select_route(ROUTES['system_analysis',0]);page.panel.set_system(system,key);page.panel.calculate()
        except Exception as exc:QMessageBox.warning(self,'Filtro para analizar',str(exc))
