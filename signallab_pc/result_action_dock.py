"""Keep result commands above every result view while retaining their own state."""
from PySide6.QtCore import QEvent,QTimer
from PySide6.QtWidgets import QWidget,QVBoxLayout,QTabWidget,QStackedWidget
from .result_toolbar import ResultActionBar


class ResultActionDock(QWidget):
    def __init__(self,surface):
        super().__init__(surface);self.surface=surface;surface.installEventFilter(self);self.setObjectName('resultActionDock');self.box=QVBoxLayout(self);self.box.setContentsMargins(0,0,0,0);self.box.setSpacing(7);self.entries=[];self.pending=False
    def add_bar(self,bar):
        if any(existing is bar for existing,_,_ in self.entries):return
        owner=bar.parentWidget();layout=owner.layout() if owner is not None else None
        if layout is None:return
        visible=not bar.isHidden();layout.removeWidget(bar);wrapper=QWidget(self);row=QVBoxLayout(wrapper);row.setContentsMargins(0,0,0,0);row.addWidget(bar);bar.setVisible(visible);bar._result_origin=owner;self.entries.append((bar,owner,wrapper));self.box.addWidget(wrapper);bar.installEventFilter(self);owner.installEventFilter(self)
        ancestor=owner
        while ancestor is not None and ancestor is not self.surface:
            if isinstance(ancestor,(QTabWidget,QStackedWidget)):ancestor.currentChanged.connect(self.schedule)
            ancestor=ancestor.parentWidget()
    def eventFilter(self,watched,event):
        if event.type() in (QEvent.Type.Show,QEvent.Type.Hide,QEvent.Type.ShowToParent,QEvent.Type.HideToParent,QEvent.Type.EnabledChange):self.schedule()
        return False
    def schedule(self,*_):
        if self.pending:return
        self.pending=True;QTimer.singleShot(0,self,self.refresh)
    def refresh(self):
        self.pending=False;shown=False
        for bar,owner,wrapper in self.entries:
            active=owner.isVisibleTo(self.surface) and not bar.isHidden();wrapper.setVisible(active);wrapper.setEnabled(owner.isEnabled());shown=shown or active
        self.setVisible(shown);self.updateGeometry()


def install(surface):
    dock=getattr(surface,'action_dock',None)
    if dock is None:
        dock=ResultActionDock(surface);surface.layout().insertWidget(2,dock);surface.action_dock=dock
    for bar in surface.content.findChildren(ResultActionBar):dock.add_bar(bar)
    dock.refresh();return dock
