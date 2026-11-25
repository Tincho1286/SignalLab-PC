"""Stack sizing follows the visible calculation, not all cached options."""
from PySide6.QtCore import QEvent,QSize
from PySide6.QtWidgets import QStackedWidget,QTabWidget
from shiboken6 import isValid
class ActiveStack(QStackedWidget):
    def minimumSizeHint(self):
        widget=self.currentWidget()
        return widget.minimumSizeHint() if widget is not None else QSize(0,0)
    def sizeHint(self):
        widget=self.currentWidget()
        return widget.sizeHint() if widget is not None else QSize(0,0)


class ActiveTabs(QTabWidget):
    """Size the visible page; hidden cached reports do not widen the document."""
    def __init__(self,parent=None):
        super().__init__(parent)
        self._measured_page = None
        self.currentChanged.connect(self.watch_page)

    def watch_page(self, *_):
        page = self.currentWidget()
        if self._measured_page is not None and isValid(self._measured_page):
            self._measured_page.removeEventFilter(self)
        self._measured_page = page
        if page is not None:
            page.installEventFilter(self)
        self.updateGeometry()

    def eventFilter(self, watched, event):
        if watched is self._measured_page and event.type() == QEvent.Type.LayoutRequest:
            self.updateGeometry()
        return super().eventFilter(watched, event)

    def minimumSizeHint(self):
        page=self.currentWidget()
        if page is None:return super().minimumSizeHint()
        size=page.minimumSizeHint();bar=self.tabBar().minimumSizeHint() if not self.tabBar().isHidden() else QSize(0,0)
        if self.tabPosition() in (QTabWidget.TabPosition.West,QTabWidget.TabPosition.East):
            return QSize(max(0,size.width())+max(0,bar.width())+4,max(size.height()+4,bar.height()))
        return QSize(max(size.width()+4,bar.width()),max(0,size.height())+max(0,bar.height())+4)
