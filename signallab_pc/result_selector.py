"""Pick a result view without using a second row on a narrow surface."""
from PySide6.QtCore import QObject,QEvent,QTimer,Qt
from PySide6.QtWidgets import (
    QApplication, QBoxLayout, QComboBox, QHBoxLayout, QLabel, QToolButton,
    QVBoxLayout, QWidget,
)
from .wrapping_row import WrappingRow


class ResultSelector(QObject):
    def __init__(self,tabs,layout):
        super().__init__(tabs)
        self.tabs = tabs
        self.container = QWidget(tabs.parentWidget())
        controls = QVBoxLayout(self.container)
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(0)
        self.row = WrappingRow()
        self.row.setObjectName('resultViews')
        self.row.setAccessibleName('Vistas disponibles del resultado')
        controls.addWidget(self.row)
        self.menu_row = QWidget()
        menu = QHBoxLayout(self.menu_row)
        menu.setContentsMargins(0, 0, 0, 0)
        menu.addWidget(QLabel('Vista'))
        self.picker = QComboBox()
        self.picker.setAccessibleName('Vista del resultado')
        self.picker.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.picker.setMinimumContentsLength(12)
        self.picker.setProperty('calculationInput', False)
        self.picker.activated.connect(lambda index: self.select(self.picker.itemData(index)))
        menu.addWidget(self.picker, 1)
        controls.addWidget(self.menu_row)
        self.menu_row.hide()
        self.signature = None
        self.structure = None
        self.buttons = {}
        self.pending = False
        self.container.installEventFilter(self)
        layout.insertWidget(layout.indexOf(tabs), self.container)
        # A hidden native tab bar does not request a new layout for every
        # visibility change. Observe the public operations used by tools too.
        for name in ('setTabVisible','setTabEnabled','setTabText','addTab','insertTab','removeTab'):
            original=getattr(tabs,name)
            def changed(*args,method=original):
                value=method(*args);self.refresh();return value
            setattr(tabs,name,changed)
        tabs.installEventFilter(self);tabs.tabBar().installEventFilter(self);tabs.currentChanged.connect(self.refresh);self.refresh()
    def eventFilter(self,watched,event):
        if watched is self.container and event.type() == QEvent.Type.Resize:
            self.adapt()
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
        self.picker.clear()
        for index,(title,shown,enabled,selected) in enumerate(snapshot):
            if not shown:continue
            button=self.buttons[index];button.setChecked(selected);button.setEnabled(enabled);button.setToolTip(tabs.tabToolTip(index) or title)
            self.picker.addItem(title, index)
            choice = self.picker.model().item(self.picker.count() - 1)
            choice.setEnabled(enabled)
            choice.setToolTip(button.toolTip())
            if selected:
                self.picker.setCurrentIndex(self.picker.count() - 1)
        self.container.setVisible(not tabs.isHidden() and self.picker.count() > 1)
        self.adapt()

    def adapt(self):
        compact = self.container.width() < self.row.flow.sizeHint().width()
        if self.menu_row.isHidden() != compact:
            return
        focused = QApplication.focusWidget()
        restore = focused is not None and self.container.isAncestorOf(focused)
        self.row.setVisible(not compact)
        self.menu_row.setVisible(compact)
        if restore:
            destination = self.picker if compact else self.buttons.get(self.tabs.currentIndex())
            if destination is not None:
                destination.setFocus(Qt.FocusReason.OtherFocusReason)

    def select(self,index):
        self.tabs.setCurrentIndex(index);self.tabs.tabBar().tabBarClicked.emit(index)


def install(tabs):
    if hasattr(tabs,'result_selector') or not hasattr(tabs,'result_action_bar'):return
    parent=tabs.parentWidget();layout=parent.layout() if parent is not None else None
    if isinstance(layout,QBoxLayout) and layout.indexOf(tabs)>=0:tabs.result_selector=ResultSelector(tabs,layout)
