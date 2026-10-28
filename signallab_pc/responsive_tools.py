"""Stack the main tool columns when the available viewport becomes narrow."""
from PySide6.QtCore import QObject,QEvent,QTimer,Qt
from PySide6.QtWidgets import QBoxLayout,QScrollArea,QSplitter,QWidget,QPushButton

class ToolColumns(QObject):
    def __init__(self,view):
        super().__init__(view);self.view=view;self.last=None;self.rows=[];self.scrolls=[]
        page=view.widget();panel=getattr(page,'panel',None)
        nested=[widget for widget in page.findChildren(QWidget) if hasattr(widget,'tool_item')]
        for widget in [page,panel,*nested,*[getattr(widget,'panel',None) for widget in nested]]:
            if widget is None:continue
            layout=widget.layout()
            if isinstance(layout,QBoxLayout) and (layout.direction()==QBoxLayout.Direction.LeftToRight or layout.property('signallabHorizontal')):
                layout.setProperty('signallabHorizontal',True);self.rows.append(layout)
        # Result actions and the basic tools also contain horizontal layouts
        # below their main page. Stack these when the document becomes narrow.
        for layout in page.findChildren(QBoxLayout):
            if layout in self.rows:continue
            widgets=[layout.itemAt(i).widget() for i in range(layout.count()) if layout.itemAt(i).widget() is not None]
            action_row=sum(isinstance(widget,QPushButton) for widget in widgets)>=2
            basic_body=any(widget.__class__.__name__=='ResultView' for widget in widgets)
            if (layout.direction()==QBoxLayout.Direction.LeftToRight and (action_row or basic_body)) or layout.property('signallabHorizontal'):
                layout.setProperty('signallabHorizontal',True);self.rows.append(layout)
        self.splits=[]
        for split in page.findChildren(QSplitter):
            if split.orientation()==Qt.Orientation.Horizontal or split.property('signallabHorizontal'):
                split.setProperty('signallabHorizontal',True);self.splits.append(split)
        self.scrolls=[]
        for scroll in page.findChildren(QScrollArea):
            original=scroll.property('signallabMinimumHeight')
            if original is None:original=scroll.minimumHeight();scroll.setProperty('signallabMinimumHeight',original)
            policy=scroll.property('signallabScrollPolicy')
            if policy is None:policy=scroll.verticalScrollBarPolicy().value;scroll.setProperty('signallabScrollPolicy',policy)
            self.scrolls.append((scroll,original,policy))
            if scroll.widget() is not None:scroll.widget().installEventFilter(self)
        view.viewport().installEventFilter(self);QTimer.singleShot(0,self,self.update)
    def eventFilter(self,obj,event):
        if event.type()==QEvent.Type.Resize and obj is self.view.viewport():self.update()
        elif event.type()==QEvent.Type.LayoutRequest and not getattr(self,'_pending_layout',False):
            self._pending_layout=True;QTimer.singleShot(0,self,self.refresh_controls)
        return False
    def update(self):
        narrow=self.view.viewport().width()<850
        if narrow==self.last:self.refresh_controls();return
        self.last=narrow
        for row in self.rows:row.setDirection(QBoxLayout.Direction.TopToBottom if narrow else QBoxLayout.Direction.LeftToRight)
        for split in self.splits:split.setOrientation(Qt.Orientation.Vertical if narrow else Qt.Orientation.Horizontal)
        self.refresh_controls()
        self.view.widget().updateGeometry()
    def refresh_controls(self):
        self._pending_layout=False;narrow=self.view.viewport().width()<850
        for scroll,height,policy in self.scrolls:
            widget=scroll.widget()
            natural=widget.heightForWidth(scroll.viewport().width()) if widget is not None else -1
            if natural<0:natural=widget.sizeHint().height() if widget is not None else 0
            target=max(height,260,natural+6) if narrow else height
            if scroll.minimumHeight()!=target:scroll.setMinimumHeight(target)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff if narrow else Qt.ScrollBarPolicy(policy))

def install_tool_columns(view):
    if not isinstance(view,QScrollArea):return
    count=len(view.widget().findChildren(QWidget))
    if getattr(view,'_columns_widget_count',None)==count:return
    previous=getattr(view,'_tool_columns',None)
    if previous is not None:view.viewport().removeEventFilter(previous);previous.deleteLater()
    view._columns_widget_count=count;view._tool_columns=ToolColumns(view)
