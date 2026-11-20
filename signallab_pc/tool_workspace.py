"""Input and result surfaces with one compact-screen navigation pattern."""
from PySide6.QtCore import Qt,QSize,QTimer,Signal
from PySide6.QtWidgets import QWidget,QFrame,QVBoxLayout,QHBoxLayout,QLabel,QScrollArea,QSplitter,QTabWidget,QBoxLayout,QSizePolicy,QFormLayout,QPushButton,QApplication
from .active_stack import ActiveStack,ActiveTabs


class Surface(QFrame):
    def __init__(self,title,caption,content,scroll=False):
        super().__init__();self.setObjectName('workspaceSurface');self.setMinimumWidth(0);root=QVBoxLayout(self);root.setContentsMargins(16,12,16,12);root.setSpacing(9)
        header=QHBoxLayout();self.title=QLabel(title);self.title.setObjectName('surfaceTitle');header.addWidget(self.title,1);root.addLayout(header);self.caption=QLabel(caption);self.caption.setObjectName('surfaceCaption');self.caption.setWordWrap(True);root.addWidget(self.caption)
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
    def minimumSizeHint(self):return QSize(0,max(100 if self.title.isHidden() else 180,super().minimumSizeHint().height()))


class ToolWorkspace(QWidget):
    expansionChanged = Signal(bool)

    def __init__(self,inputs,results,parent=None,*,titles=('Datos de entrada','Resultado'),captions=('', '')):
        super().__init__(parent);self.setObjectName('toolWorkspace');self.setProperty('workspaceLayout',True);self.compact=None;self.result_preferred=False;self.titles=titles;self.wide_sizes=[400,760]
        self.output_expanded = False
        self._compact_index_before_expansion = None
        root=QVBoxLayout(self);root.setContentsMargins(14,0,14,12);self.modes=ActiveStack();root.addWidget(self.modes)
        self.split=QSplitter(Qt.Orientation.Horizontal);self.split.setChildrenCollapsible(False);self.split.setHandleWidth(10);self.modes.addWidget(self.split)
        self.tabs=ActiveTabs();self.tabs.setObjectName('workspaceModes');self.modes.addWidget(self.tabs)
        self.inputs=Surface(titles[0],captions[0],inputs,True);self.results=Surface(titles[1],captions[1],results)
        self.inputs.setObjectName('inputSurface');self.results.setObjectName('resultSurface');self.switch_mode(False)
    def minimumSizeHint(self):return QSize(300,max(160 if self.compact else 240,self.modes.minimumSizeHint().height()+12))
    def sizeHint(self):return QSize(1040,620)
    def resizeEvent(self,event):super().resizeEvent(event);self.switch_mode(self.width()<870)
    def switch_mode(self,compact):
        if compact==self.compact:return
        focused=QApplication.focusWidget()
        if focused is not None and focused.window() is not self.window():focused=None
        focused_surface=0 if focused is not None and self.inputs.isAncestorOf(focused) else 1 if focused is not None and self.results.isAncestorOf(focused) else None
        if self.compact is False and compact:
            sizes=self.split.sizes()
            if all(size>0 for size in sizes):self.wide_sizes=sizes
        self.compact=compact
        for surface in (self.inputs,self.results):
            surface.title.setVisible(not compact)
            surface.caption.setVisible(not compact and bool(surface.caption.text()))
        if compact:
            for surface,title in zip((self.inputs,self.results),self.titles):self.tabs.addTab(surface,title)
            self.modes.setCurrentWidget(self.tabs)
            self.tabs.tabBar().setVisible(not self.output_expanded)
            index = focused_surface if focused_surface is not None else int(self.result_preferred)
            self.tabs.setCurrentIndex(1 if self.output_expanded else index)
        else:
            while self.tabs.count():self.tabs.removeTab(0)
            self.split.addWidget(self.inputs);self.split.addWidget(self.results);self.modes.setCurrentWidget(self.split);self.inputs.setVisible(not self.output_expanded);self.results.show();self.split.setStretchFactor(0,0);self.split.setStretchFactor(1,1);self.split.setSizes(self.wide_sizes)
        if focused_surface is not None and focused.isVisibleTo(self):focused.setFocus(Qt.FocusReason.OtherFocusReason)

    def set_output_expanded(self, expanded):
        if expanded == self.output_expanded:
            return
        if expanded:
            self._compact_index_before_expansion = self.tabs.currentIndex() if self.compact else None
            if not self.compact and all(self.split.sizes()):
                self.wide_sizes = self.split.sizes()
        self.output_expanded = expanded
        if self.compact:
            self.tabs.tabBar().setVisible(not expanded)
            previous = self._compact_index_before_expansion
            self.tabs.setCurrentIndex(1 if expanded or previous is None else previous)
        else:
            self.inputs.setVisible(not expanded)
            if not expanded:
                self.split.setSizes(self.wide_sizes)
        self.tabs.updateGeometry()
        self.modes.updateGeometry()
        self.updateGeometry()
        self.expansionChanged.emit(expanded)

    def show_inputs(self):
        self.set_output_expanded(False)
        if self.compact:
            self.tabs.setCurrentIndex(0)

    def show_results(self):
        self.result_preferred=True
        if self.compact:self.tabs.setCurrentIndex(1)


def install(page):
    """Adapt the two-column containers used by the existing tool families."""
    if getattr(page,'workspace',None) is not None:return page.workspace
    panel=getattr(page,'panel',page);layout=panel.layout()
    outer=page.layout()
    if outer is not None and any(isinstance(outer.itemAt(i).widget(),QSplitter) for i in range(outer.count())):panel=page;layout=outer
    if layout is None or not layout.count() or layout.count()==1 and not isinstance(layout.itemAt(0).widget(),QSplitter):panel=page;layout=page.layout()
    if layout is None:return None
    widgets=[layout.itemAt(i).widget() for i in range(layout.count()) if layout.itemAt(i).widget() is not None]
    split=next((widget for widget in widgets if isinstance(widget,QSplitter) and widget.count()==2 and widget.orientation()==Qt.Orientation.Horizontal),None)
    if split is not None:
        inputs,results=split.widget(0),split.widget(1);inputs.setParent(panel);results.setParent(panel);layout.removeWidget(split);split.deleteLater()
        for i in reversed(range(layout.count())):
            item=layout.itemAt(i);extra=item.layout()
            if extra is not None and extra.property('resultActionsRow'):
                layout.takeAt(i);extra.setParent(None);holder=QWidget(results);holder.setLayout(extra);results.layout().insertWidget(0,holder)
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
    context=getattr(page,'context',None)
    if context is not None:
        kind=page.tool_item[1]
        for button in workspace.inputs.findChildren(QPushButton):
            text=button.property('actionTitle') or button.text()
            redundant=kind=='fourier' and text.startswith(('Exportar resultado CSV','Guardar resultado JSON')) or kind=='systems' and text.startswith('Exportar respuesta CSV')
            if redundant:button.hide()
            elif kind=='symbolic' and text.startswith('Guardar resultado y supuestos'):
                parent=button.parentWidget();form=parent.layout()
                if form is not None:form.removeWidget(button)
                button.setText('Exportar resultado…');button.setToolTip('Guardar el resultado algebraico junto con su entrada, condiciones y supuestos.');context.output.actions.replace_action('export',button);button.setEnabled(False);context.result_export_actions=[button]
    from .result_selector import install as install_selector
    for tabs in workspace.results.findChildren(QTabWidget):install_selector(tabs)
    from .result_action_dock import install as install_action_dock
    install_action_dock(workspace.results)
    from .result_state import ResultState
    for state in workspace.findChildren(ResultState):
        visible=not state.isHidden();previous=state.parentWidget().layout()
        if isinstance(previous,QFormLayout) and previous.indexOf(state)>=0:previous.takeRow(state)
        elif previous is not None:previous.removeWidget(state)
        workspace.results.layout().insertWidget(3,state);state.setVisible(visible)
    return workspace
