"""Lazy, independent option pages in a single public document."""
from .active_stack import ActiveStack
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QTabBar,QComboBox,QLabel
from .tool_groups import GROUPS,GROUP_ROUTES

class GroupedTool(QWidget):
    def __init__(self,window,group):
        super().__init__();self.window=window;self.group=group;self.pages={};self.current_page=None;self.current_route=None;self.selections={};self.previous_tab=None
        self.groups=GROUPS[group][3];root=QVBoxLayout(self);root.setContentsMargins(0,0,0,0)
        self.tabs=QTabBar(self);self.tabs.hide()
        for name,_ in self.groups:self.tabs.addTab(name)
        self.choice=QComboBox(self);self.choice.hide()
        self.stack=ActiveStack();root.addWidget(self.stack,1)
        self.tabs.currentChanged.connect(self.populate);self.choice.currentIndexChanged.connect(self.activate);self.populate(0)
    def populate(self,index):
        if self.previous_tab is not None:self.selections[self.previous_tab]=self.choice.currentIndex()
        self.previous_tab=index;self.choice.blockSignals(True);self.choice.clear()
        for label,key in self.groups[index][1]:self.choice.addItem(label,key)
        self.choice.setCurrentIndex(self.selections.get(index,0));self.choice.blockSignals(False)
        self.activate(self.choice.currentIndex())
    def activate(self,index):
        if index<0:return
        from .workspaces import ROUTES
        from .toolbox import ToolPage
        route=ROUTES[tuple(self.choice.itemData(index))]
        if route not in self.pages:self.pages[route]=ToolPage(self.window,route);self.stack.addWidget(self.pages[route])
        self.current_page=self.pages[route];self.current_route=route;self.stack.setCurrentWidget(self.current_page);self.stack.updateGeometry();self.window.pages[route]=self.current_page
        self.sync_view();self.window._configure_readable_layouts();self.window.operation_changed(route)
    def sync_view(self):
        view=self.window.views.get(GROUP_ROUTES[self.group])
        if view is not None:
            view.active_page=self.current_page;view.panel=getattr(self.current_page,'panel',None);view.context=getattr(self.current_page,'context',None)
    def select_route(self,item):
        for tab,(_,choices) in enumerate(self.groups):
            keys=[key for _,key in choices]
            if item[1:3] in keys:
                self.tabs.setCurrentIndex(tab);self.choice.setCurrentIndex(keys.index(item[1:3]));return self.current_page
        raise ValueError('La operación no pertenece a este documento.')
