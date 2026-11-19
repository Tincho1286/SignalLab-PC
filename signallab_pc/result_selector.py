"""Show every available result view with readable, wrapping labels."""
from PySide6.QtCore import QObject,QEvent,QTimer,Qt
from PySide6.QtWidgets import QBoxLayout,QToolButton,QApplication,QWidget
from .wrapping_row import WrappingRow


class ResultSelector(QObject):
    def __init__(self,tabs,layout):
        super().__init__(tabs);self.tabs=tabs;self.row=WrappingRow(tabs.parentWidget());self.row.setObjectName('resultViews');self.row.setAccessibleName('Vistas disponibles del resultado');layout.insertWidget(layout.indexOf(tabs),self.row);self.signature=None;self.structure=None;self.buttons={};self.pending=False
        # A hidden native tab bar does not request a new layout for every
        # visibility change. Observe the public operations used by tools too.
        for name in ('setTabVisible','setTabEnabled','setTabText','addTab','insertTab','removeTab'):
            original=getattr(tabs,name)
            def changed(*args,method=original):
                value=method(*args);self.refresh();return value
            setattr(tabs,name,changed)
        tabs.installEventFilter(self);tabs.tabBar().installEventFilter(self);tabs.currentChanged.connect(self.refresh);self.refresh()
    def eventFilter(self,watched,event):
        if event.type() in (QEvent.Type.LayoutRequest,QEvent.Type.Show,QEvent.Type.Hide,QEvent.Type.ShowToParent,QEvent.Type.HideToParent,QEvent.Type.Resize) and not self.pending:self.pending=True;QTimer.singleShot(0,self,self.refresh)
        return False
    def refresh(self,*_):
        self.pending=False;tabs=self.tabs;tabs.tabBar().hide();snapshot=tuple((tabs.tabText(i),tabs.isTabVisible(i),tabs.isTabEnabled(i),i==tabs.currentIndex()) for i in range(tabs.count()))
        signature=(not tabs.isHidden(),snapshot)
        if signature==self.signature:return
        self.signature=signature;flow=self.row.flow;structure=tuple((title,shown) for title,shown,_,_ in snapshot)
        if structure!=self.structure:
            focused=QApplication.focusWidget();restore_focus=focused is not None and self.row.isAncestorOf(focused);self.structure=structure
            while flow.count():
                item=flow.takeAt(0)
                if item.widget() is not None:item.widget().hide();item.widget().deleteLater()
            self.buttons={}
            for index,(title,shown,_,_) in enumerate(snapshot):
                if not shown:continue
                button=QToolButton();button.setText(title);button.setProperty('segment',True);button.setCheckable(True);button.setFocusPolicy(Qt.FocusPolicy.StrongFocus);button.setAccessibleName(title);button.clicked.connect(lambda checked=False,i=index:self.select(i));flow.addWidget(button);self.buttons[index]=button
            sequence=list(self.buttons.values())
            for first,second in zip(sequence,sequence[1:]):QWidget.setTabOrder(first,second)
            if restore_focus and tabs.currentIndex() in self.buttons:self.buttons[tabs.currentIndex()].setFocus(Qt.FocusReason.OtherFocusReason)
        visible=0
        for index,(title,shown,enabled,selected) in enumerate(snapshot):
            if not shown:continue
            visible+=1;button=self.buttons[index];button.setChecked(selected);button.setEnabled(enabled);button.setToolTip(tabs.tabToolTip(index) or title)
        self.row.setVisible(not tabs.isHidden() and visible>1);self.row.updateGeometry()
    def select(self,index):
        self.tabs.setCurrentIndex(index);self.tabs.tabBar().tabBarClicked.emit(index)


def install(tabs):
    if hasattr(tabs,'result_selector') or not hasattr(tabs,'result_action_bar'):return
    parent=tabs.parentWidget();layout=parent.layout() if parent is not None else None
    if isinstance(layout,QBoxLayout) and layout.indexOf(tabs)>=0:tabs.result_selector=ResultSelector(tabs,layout)
