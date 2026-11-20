"""Stable result action slots, shared by numeric and algebraic tools."""
from PySide6.QtCore import Qt,QEvent,QSize,QTimer
from PySide6.QtWidgets import QWidget,QGridLayout,QPushButton,QSizePolicy,QMenu,QToolButton
from .design import icon

ORDER=('graph','reuse','cas','export')
LABELS={'graph':'Abrir gráfico','reuse':'Usar resultado en…','cas':'Enviar a CAS','export':'Exportar…'}
SYMBOLS={'graph':'chart','reuse':'convert','cas':'calculator','export':'export'}


class ActionLayout(QGridLayout):
    def __init__(self,owner):super().__init__(owner);self.owner=owner
    def addWidget(self,widget,*position):
        if position:return super().addWidget(widget,*position)
        self.owner.add_action(widget)
    def insertWidget(self,index,widget,*_):self.owner.add_action(widget)
    def addStretch(self,*_):pass


class ResultActionBar(QWidget):
    """The same four locations, including disabled explanations when unavailable."""
    def __init__(self,parent=None):
        super().__init__(parent);self.setObjectName('resultActionBar');self.setProperty('fixedActionRow',True);self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed);self.slots={};self.extras=[];self.placeholders={};self._columns=0;self._pending=False
        self.grid=ActionLayout(self);self.grid.setContentsMargins(0,0,0,0);self.grid.setSpacing(7)
        for role in ORDER:
            button=QPushButton(LABELS[role],self);button.setEnabled(False);button.setProperty('resultAction',role);button.setToolTip('Esta acción estará disponible cuando el resultado de la herramienta la admita.');self.placeholders[role]=button
        self.reflow()
    def showEvent(self,event):super().showEvent(event);QTimer.singleShot(0,self,self.sync_graph)
    def scope(self):
        widget=self.parentWidget()
        while widget is not None:
            if widget.objectName()=='resultSurface':return widget
            widget=widget.parentWidget()
        return None
    def sync_graph(self):
        scope=self.scope()
        if scope is None:return
        if getattr(getattr(scope,'action_dock',None),'graph',None) is not None:scope.action_dock.schedule();return
        bars=scope.findChildren(ResultActionBar);active=[bar for bar in bars if bar.isVisibleTo(scope)]
        for bar in active:
            home=getattr(bar,'home_graph',None)
            if home is not None and home.parentWidget() is not bar:bar.claim_graph(home)
        for bar in active:
            if not bar.property('systemResultActions') or 'graph' in bar.slots:continue
            source=next((other for other in bars if other is not bar and 'graph' in other.slots and getattr(other,'_result_origin',other.parentWidget()).isVisibleTo(scope)),None)
            if source is not None:bar.claim_graph(source.slots['graph'])
    def claim_graph(self,button):
        previous=button.parentWidget()
        if isinstance(previous,ResultActionBar) and previous is not self and previous.slots.get('graph') is button:previous.slots.pop('graph');previous.reflow()
        self.add_action(button,'graph');button.show()
    def role_for(self,button):
        role=button.property('resultAction') or button.property('actionRole');text=button.text() if hasattr(button,'text') else ''
        if button.property('plotLauncher') or role=='graph':return 'graph'
        if role in ORDER:return role
        if text.startswith('Usar '):return 'reuse'
        if text.startswith('Enviar a CAS'):return 'cas'
        if text.startswith(('Exportar','Guardar resultado')):return 'export'
        return None
    def add_action(self,button,role=None):
        role=role or self.role_for(button)
        if role in ORDER and self.slots.get(role) is button:pass
        elif role in ORDER and role not in self.slots:
            self.slots[role]=button;button.setProperty('resultAction',role)
        elif button not in self.extras:self.extras.append(button)
        if role in SYMBOLS and self.slots.get(role) is button and button.icon().isNull():
            button.setIcon(icon(SYMBOLS[role]))
            button.setIconSize(QSize(15,15))
            if isinstance(button,QToolButton):
                button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        shortcut={'graph':'Alt+G','reuse':'Alt+R','export':'Alt+E'}.get(role)
        if shortcut and shortcut not in button.toolTip():button.setToolTip((button.toolTip()+' · ' if button.toolTip() else '')+shortcut)
        visible=not button.isHidden() or not button.testAttribute(Qt.WidgetAttribute.WA_WState_ExplicitShowHide)
        button.setParent(self);button.setVisible(visible);button.installEventFilter(self);button.setMinimumWidth(0);button.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed);self.reflow()
        if role=='graph' and not hasattr(button,'graph_home'):
            button.graph_home=self;self.home_graph=button
        QTimer.singleShot(0,self,self.sync_graph)
    def replace_action(self,role,button):
        previous=self.slots.pop(role,None)
        if previous is not None:self.grid.removeWidget(previous);previous.setProperty('retiredResultAction',True);previous.hide()
        self.add_action(button,role)
    def resizeEvent(self,event):super().resizeEvent(event);self.reflow()
    def eventFilter(self,watched,event):
        if watched.property('retiredResultAction') and event.type() in (QEvent.Type.Show,QEvent.Type.ShowToParent):watched.hide()
        if event.type()==QEvent.Type.EnabledChange:
            scope=self.scope()
            if scope is not None and hasattr(scope,'action_dock'):scope.action_dock.schedule()
        if event.type() in (QEvent.Type.ShowToParent,QEvent.Type.HideToParent) and not self._pending:
            self._pending=True;QTimer.singleShot(0,self,self.reflow)
        return False
    def reflow(self):
        self._pending=False
        active = [self.slots.get(role) or self.placeholders[role] for role in ORDER]
        single_row_min = sum(button.sizeHint().width() for button in active) + 3*self.grid.spacing()
        columns=4 if self.width()>=max(600,single_row_min) else 2 if self.width()>=330 else 1
        for i,role in enumerate(ORDER):
            button=self.slots.get(role);placeholder=self.placeholders[role];visible=button is not None and not button.isHidden();placeholder.setVisible(not visible)
            QGridLayout.addWidget(self.grid,placeholder,i//columns,i%columns)
            if button is not None:QGridLayout.addWidget(self.grid,button,i//columns,i%columns)
        row=(len(ORDER)+columns-1)//columns
        for i,button in enumerate(self.extras):QGridLayout.addWidget(self.grid,button,row+i//columns,i%columns)
        for i in range(4):self.grid.setColumnStretch(i,1 if i<columns else 0)
        sequence=[self.slots.get(role) for role in ORDER]+self.extras;sequence=[button for button in sequence if button is not None and not button.isHidden()]
        for first,second in zip(sequence,sequence[1:]):QWidget.setTabOrder(first,second)
        self._columns=columns
        self.setMinimumHeight(self.grid.minimumSize().height())
        self.updateGeometry()
    def minimumSizeHint(self):return QSize(0,self.grid.minimumSize().height())
    def use_report(self,report):
        if 'export' in self.slots:return
        button=QPushButton('Exportar informe…');button.report_export=report;button.setProperty('resultAction','export');menu=QMenu(button);button.setMenu(menu)
        menu.addAction('Informe con formato (HTML)…',lambda:report.export_document(True));menu.addAction('Texto sin formato…',lambda:report.export_document(False));self.add_action(button,'export')
        report.textChanged.connect(lambda:button.setEnabled(bool(report.toPlainText().strip())));button.setEnabled(bool(report.toPlainText().strip()))


def attach(tabs,bar):
    """Declare the toolbar that owns all figures of this result collection."""
    tabs.result_action_bar=bar
    launcher=getattr(tabs,'_signallab_plot_actions',None) or getattr(tabs,'_signallab_custom_plot_action',None)
    if launcher is not None:
        previous=launcher.parentWidget()
        if isinstance(previous,ResultActionBar) and previous is not bar and previous.slots.get('graph') is launcher:previous.slots.pop('graph');previous.reflow()
        tabs.setCornerWidget(None,Qt.Corner.TopRightCorner);bar.add_action(launcher,'graph');launcher.show()
