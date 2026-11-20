"""One export location, retaining the tools' original validated callbacks."""
from dataclasses import dataclass
from PySide6.QtCore import QObject,QEvent,QTimer
from PySide6.QtWidgets import QWidget,QAbstractButton,QPushButton,QMenu,QTabWidget,QStackedWidget
from shiboken6 import isValid


def mark_export(button):
    """Declare a contextual export; standalone views keep their local button."""
    button.setProperty('resultExport',True);return button


@dataclass
class Source:
    button:QAbstractButton
    owner:QWidget
    bar:QWidget|None=None


class ResultExports(QObject):
    def __init__(self,surface,dock):
        super().__init__(surface);self.surface=surface;self.dock=dock;self.sources=[];self.proxies={};self.pending=False

    def register(self,button,owner,bar=None):
        if any(source.button is button for source in self.sources):return
        self.sources.append(Source(button,owner,bar));button.setProperty('resultExportCaptured',True);button.installEventFilter(self);button.hide()
        ancestor=owner
        while ancestor is not None and ancestor is not self.surface:
            ancestor.installEventFilter(self)
            if isinstance(ancestor,(QTabWidget,QStackedWidget)):ancestor.currentChanged.connect(self.schedule)
            ancestor=ancestor.parentWidget()

    def add_bar(self,bar):
        if bar in self.proxies:return
        original=bar.slots.pop('export',None)
        if original is not None:
            bar.grid.removeWidget(original);self.register(original,getattr(original,'report_export',None) or getattr(bar,'_result_origin',bar.parentWidget()),bar)
        bar.export_source=original
        for button in bar.extras:
            if bar.role_for(button)=='export':self.register(button,getattr(bar,'_result_origin',bar.parentWidget()),bar)
        proxy=QPushButton('Exportar…');proxy.setProperty('resultExportProxy',True);proxy.setToolTip('Guardar datos, tablas e informes, o copiar el texto del informe.');menu=QMenu(proxy);proxy.setMenu(menu);menu.aboutToShow.connect(lambda b=bar:self.prepare(b));bar.add_action(proxy,'export');self.proxies[bar]=proxy

    def path(self,owner,ordered=False):
        """Available result tabs stay exportable without selecting each one."""
        titles=[];node=owner
        while node is not None and node is not self.surface:
            parent=node.parentWidget()
            if isinstance(parent,QStackedWidget) and isinstance(parent.parentWidget(),QTabWidget):
                tabs=parent.parentWidget();index=tabs.indexOf(node)
                if index<0 or not tabs.isTabVisible(index) or not tabs.isTabEnabled(index):return None
                titles.append(index if ordered else tabs.tabText(index))
            elif node.isHidden() and not isinstance(parent,QStackedWidget):return None
            node=parent
        return tuple(reversed(titles)) if node is self.surface else None

    def available(self,bar):
        result=[]
        for source in self.sources:
            if not isValid(source.button) or not isValid(source.owner):continue
            if source.bar is not None and source.bar is not bar:continue
            path=self.path(source.owner)
            if path is not None:result.append((source,path))
        return sorted(result,key=lambda item:(item[0].bar is None,self.path(item[0].owner,ordered=True) or ()))

    def prepare(self,bar):
        proxy=self.proxies[bar];menu=proxy.menu();menu.clear();previous=None
        for source,path in self.available(bar):
            button=source.button
            # A primary report export already contains the same formats.
            report=getattr(button,'report_export',None)
            if source.bar is not None and report is not None and any(other.bar is None and getattr(other.button,'report_export',None) is report for other,_ in self.available(bar)):continue
            title=' · '.join(path) if source.bar is None else 'Resultado seleccionado'
            if title!=previous:
                menu.addSection(title or 'Resultado');previous=title
            if button.menu() is not None:
                original_menu=button.menu();original_menu.aboutToShow.emit()
                for original in original_menu.actions():
                    if original.isSeparator():menu.addSeparator();continue
                    if original.menu() is not None:action=menu.addMenu(original.menu());action.setText(original.text())
                    else:action=menu.addAction(original.text(),original.trigger)
                    action.setEnabled(button.isEnabled() and original.isEnabled());action.setToolTip(original.toolTip())
            else:
                action=menu.addAction(button.text(),button.click);action.setEnabled(button.isEnabled());action.setToolTip(button.toolTip())
        if not menu.actions():
            action=menu.addAction('No hay datos para exportar.');action.setEnabled(False)

    def eventFilter(self,watched,event):
        kind=event.type()
        if kind in (QEvent.Type.Show,QEvent.Type.ShowToParent) and watched.property('resultExportCaptured'):watched.hide()
        if kind in (QEvent.Type.EnabledChange,QEvent.Type.Show,QEvent.Type.Hide,QEvent.Type.LayoutRequest):self.schedule()
        return False

    def schedule(self,*_):
        if not self.pending:self.pending=True;QTimer.singleShot(0,self,self.refresh)

    def refresh(self):
        self.pending=False
        for bar,proxy in self.proxies.items():proxy.setEnabled(any(source.button.isEnabled() for source,_ in self.available(bar)))


def install(surface,dock):
    hub=getattr(surface,'result_exports',None)
    if hub is None:hub=ResultExports(surface,dock);surface.result_exports=hub
    for bar,_,_ in dock.entries:hub.add_bar(bar)
    hub.add_bar(dock.fallback)
    for button in surface.content.findChildren(QAbstractButton):
        if button.property('resultExport') and not button.property('resultExportCaptured'):hub.register(button,button.parentWidget())
    hub.refresh();return hub
