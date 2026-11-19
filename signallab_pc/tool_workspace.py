"""Input and result surfaces with one compact-screen navigation pattern."""
from PySide6.QtCore import Qt,QSize,QTimer
from PySide6.QtWidgets import QWidget,QFrame,QVBoxLayout,QHBoxLayout,QLabel,QScrollArea,QSplitter,QTabWidget,QBoxLayout,QSizePolicy,QFormLayout
from .active_stack import ActiveStack,ActiveTabs


class Surface(QFrame):
    def __init__(self,title,caption,content,scroll=False):
        super().__init__();self.setObjectName('workspaceSurface');self.setMinimumWidth(0);root=QVBoxLayout(self);root.setContentsMargins(18,16,18,16);root.setSpacing(12)
        header=QHBoxLayout();label=QLabel(title);label.setObjectName('surfaceTitle');header.addWidget(label,1);root.addLayout(header);self.caption=QLabel(caption);self.caption.setObjectName('surfaceCaption');self.caption.setWordWrap(True);root.addWidget(self.caption)
        if scroll and not isinstance(content,QScrollArea):
            inner=content.layout()
            if inner is not None:
                for i in range(inner.count()):
                    candidate=inner.itemAt(i).widget()
                    if isinstance(candidate,QScrollArea) and candidate.widget() is not None:
                        body=candidate.takeWidget();item=inner.replaceWidget(candidate,body);del item;candidate.deleteLater()
            area=QScrollArea();area.setWidgetResizable(True);area.setFrameShape(QFrame.Shape.NoFrame);area.setWidget(content);content=area
        content.setMinimumWidth(0)
        if isinstance(content,QScrollArea):content.setFrameShape(QFrame.Shape.NoFrame);content.setMinimumHeight(0);content.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
        root.addWidget(content,1);self.content=content
        if scroll:
            for form in content.findChildren(QFormLayout):form.setProperty('stackFields',True)
    def minimumSizeHint(self):return QSize(0,180)


class ToolWorkspace(QWidget):
    def __init__(self,inputs,results,parent=None):
        super().__init__(parent);self.setObjectName('toolWorkspace');self.setProperty('workspaceLayout',True);self.compact=None;self.result_preferred=False
        root=QVBoxLayout(self);root.setContentsMargins(0,0,0,0);self.modes=ActiveStack();root.addWidget(self.modes)
        self.split=QSplitter(Qt.Orientation.Horizontal);self.split.setChildrenCollapsible(False);self.split.setHandleWidth(10);self.modes.addWidget(self.split)
        self.tabs=ActiveTabs();self.tabs.setObjectName('workspaceModes');self.modes.addWidget(self.tabs)
        self.inputs=Surface('Datos de entrada','Definí qué querés calcular.',inputs,True);self.results=Surface('Resultado','Consultá, graficá o continuá con lo calculado.',results)
        self.inputs.setObjectName('inputSurface');self.results.setObjectName('resultSurface');self.switch_mode(False)
    def minimumSizeHint(self):return QSize(300,240)
    def sizeHint(self):return QSize(1040,620)
    def resizeEvent(self,event):super().resizeEvent(event);self.switch_mode(self.width()<870)
    def switch_mode(self,compact):
        if compact==self.compact:return
        self.compact=compact
        if compact:
            for surface,title in ((self.inputs,'Datos de entrada'),(self.results,'Resultado')):self.tabs.addTab(surface,title)
            self.modes.setCurrentWidget(self.tabs);self.tabs.setCurrentIndex(1 if self.result_preferred else 0)
        else:
            while self.tabs.count():self.tabs.removeTab(0)
            self.split.addWidget(self.inputs);self.split.addWidget(self.results);self.split.setStretchFactor(0,0);self.split.setStretchFactor(1,1);self.split.setSizes([400,760]);self.modes.setCurrentWidget(self.split)
    def show_results(self):
        self.result_preferred=True
        if self.compact:self.tabs.setCurrentIndex(1)


def install(page):
    """Adapt the two-column containers used by the existing tool families."""
    if getattr(page,'workspace',None) is not None:return page.workspace
    panel=getattr(page,'panel',page);layout=panel.layout()
    if layout is None or not layout.count() or layout.count()==1 and not isinstance(layout.itemAt(0).widget(),QSplitter):panel=page;layout=page.layout()
    if layout is None:return None
    widgets=[layout.itemAt(i).widget() for i in range(layout.count()) if layout.itemAt(i).widget() is not None]
    split=next((widget for widget in widgets if isinstance(widget,QSplitter) and widget.count()==2 and widget.orientation()==Qt.Orientation.Horizontal),None)
    if split is not None:
        inputs,results=split.widget(0),split.widget(1);inputs.setParent(panel);results.setParent(panel);layout.removeWidget(split);split.deleteLater()
    elif isinstance(layout,QBoxLayout) and layout.direction()==QBoxLayout.Direction.LeftToRight and layout.count()==2:
        if any(layout.itemAt(i).widget() is None and layout.itemAt(i).layout() is None for i in range(2)):return None
        parts=[layout.takeAt(0),layout.takeAt(0)];surfaces=[]
        for part in parts:
            if part.widget() is not None:surfaces.append(part.widget())
            elif part.layout() is not None:
                container=QWidget(panel);inner=part.layout();inner.setParent(None);container.setLayout(inner);surfaces.append(container)
            else:
                for previous in parts:layout.addItem(previous)
                return None
        inputs,results=surfaces
    else:return None
    layout.setContentsMargins(0,0,0,0);workspace=ToolWorkspace(inputs,results,panel)
    if isinstance(layout,QBoxLayout):layout.setDirection(QBoxLayout.Direction.TopToBottom)
    layout.addWidget(workspace);page.workspace=workspace;panel.setMinimumWidth(0)
    from .result_selector import install as install_selector
    for tabs in workspace.results.findChildren(QTabWidget):install_selector(tabs)
    from .result_action_dock import install as install_action_dock
    install_action_dock(workspace.results)
    return workspace
