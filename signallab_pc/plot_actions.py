"""A single figure launcher in the header of each results/report area."""
import weakref
from shiboken6 import isValid
from PySide6.QtCore import Qt,QEvent
from PySide6.QtWidgets import QToolButton,QMenu,QTabWidget


def style_launcher(button):
    button.setText('Abrir gráfico');button.setObjectName('plotLauncher')
    button.setProperty('plotLauncher',True);button.setMinimumWidth(0)
    button.setAccessibleName('Abrir gráfico del resultado')


def install_result_button(tabs,button):
    """Tools that must sample a formula keep their original, validated action."""
    style_launcher(button);tabs._signallab_custom_plot_action=button
    tabs.setCornerWidget(button,Qt.Corner.TopRightCorner)


def _alive(reference):
    value=reference()
    return value if value is not None and isValid(value) else None


class PlotLauncher(QToolButton):
    def __init__(self,parent):
        super().__init__(parent);style_launcher(self);self.entries=[];self._refreshing=False
        self.setToolTip('Abrir la figura del resultado. La flecha permite elegir otra figura disponible.')
        self.menu=QMenu(self);self.setMenu(self.menu);self.menu.aboutToShow.connect(self.rebuild)
        self.clicked.connect(self.open_default);self.setEnabled(False)
    def register(self,canvas,routes,label):
        if any(_alive(entry[0]) is canvas for entry in self.entries):return
        self.entries.append((weakref.ref(canvas),[(weakref.ref(tabs),weakref.ref(page)) for tabs,page in routes],label))
        for tabs,_ in routes:tabs.tabBar().installEventFilter(self)
        canvas._signallab_plot_action_refresh=self.refresh;self.refresh()
    def available(self):
        result=[]
        for entry in self.entries:
            canvas=_alive(entry[0])
            if canvas is None or not getattr(canvas,'_signallab_has_plot_result',False):continue
            visible=True
            for tabs_ref,page_ref in entry[1]:
                tabs,page=_alive(tabs_ref),_alive(page_ref)
                if tabs is None or page is None:visible=False;break
                index=tabs.indexOf(page)
                if index<0 or not tabs.isTabVisible(index) or not tabs.isTabEnabled(index):visible=False;break
            if visible:result.append(entry)
        return result
    def refresh(self):
        if self._refreshing:return
        self._refreshing=True
        try:
            entries=self.available();self.setEnabled(bool(entries))
            self.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup if len(entries)>1 else QToolButton.ToolButtonPopupMode.DelayedPopup)
        finally:self._refreshing=False
    def eventFilter(self,watched,event):
        if event.type() in (QEvent.Type.Show,QEvent.Type.LayoutRequest,QEvent.Type.Resize):self.refresh()
        return super().eventFilter(watched,event)
    def open_default(self):
        entries=self.available()
        if not entries:return
        selected=entries[0]
        for entry in entries:
            if entry[1]:
                tabs,page=_alive(entry[1][-1][0]),_alive(entry[1][-1][1])
                if tabs is not None and tabs.currentWidget() is page:selected=entry;break
        self.open_entry(selected)
    def open_entry(self,entry):
        canvas=_alive(entry[0])
        if canvas is not None:
            from .plot_view import enlarge_plot
            enlarge_plot(canvas,self)
    def rebuild(self):
        self.menu.clear();used={}
        for entry in self.available():
            label=entry[2] or 'Resultado';used[label]=used.get(label,0)+1
            if used[label]>1:label+=' · '+str(used[label])
            self.menu.addAction(label,lambda checked=False,item=entry:self.open_entry(item))


def bind_canvas(canvas,origin):
    routes=[];ancestor=origin
    while ancestor is not None:
        if getattr(ancestor,'tool_item',None) is not None:break
        if isinstance(ancestor,QTabWidget):
            for index in range(ancestor.count()):
                page=ancestor.widget(index)
                if page is origin or page.isAncestorOf(origin):routes.append((ancestor,page));break
        ancestor=ancestor.parentWidget()
    custom=next((tabs._signallab_custom_plot_action for tabs,_ in routes if getattr(tabs,'_signallab_custom_plot_action',None) is not None),None)
    if custom is not None:
        canvas._signallab_plot_action_scope=custom;return
    if routes:
        tabs,page=routes[-1];launcher=getattr(tabs,'_signallab_plot_actions',None)
        if launcher is None:
            launcher=PlotLauncher(tabs);tabs._signallab_plot_actions=launcher
            tabs.setCornerWidget(launcher,Qt.Corner.TopRightCorner)
        label=tabs.tabText(tabs.indexOf(page))
    else:
        launcher=getattr(origin,'_signallab_plot_actions',None)
        if launcher is None:
            launcher=PlotLauncher(origin);origin._signallab_plot_actions=launcher
            layout=origin.layout()
            if hasattr(layout,'insertWidget'):layout.insertWidget(0,launcher,0,Qt.AlignmentFlag.AlignRight)
            else:layout.addWidget(launcher)
        label='Resultado'
    canvas._signallab_plot_action_scope=launcher
    launcher.register(canvas,routes,label)
