"""Keep result commands above every result view while retaining their own state."""
from PySide6.QtCore import QEvent,QTimer
from PySide6.QtWidgets import QWidget,QVBoxLayout,QTabWidget,QStackedWidget,QHBoxLayout,QLabel,QComboBox,QSizePolicy
from .result_toolbar import ResultActionBar


class ResultActionDock(QWidget):
    def __init__(self,surface):
        super().__init__(surface);self.surface=surface;surface.installEventFilter(self);self.setObjectName('resultActionDock');self.box=QVBoxLayout(self);self.box.setContentsMargins(0,0,0,0);self.box.setSpacing(7);self.entries=[];self.pending=False;self.graph=None;self.chosen=None;self.choices=[]
        self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self.target_row=QWidget();row=QHBoxLayout(self.target_row);row.setContentsMargins(10,6,10,0);row.addWidget(QLabel('Trabajar con'));self.target=QComboBox();self.target.setMinimumWidth(0);self.target.setProperty('calculationInput',False);self.target.setToolTip('Elegí qué resultado querés reutilizar, enviar al CAS o exportar. No recalcula.');row.addWidget(self.target,1);self.target.currentIndexChanged.connect(self.choose);self.box.addWidget(self.target_row);self.target_row.hide();self.fallback=ResultActionBar(self);self.box.addWidget(self.fallback);self.fallback.hide()
    def set_graph(self,graph):self.graph=graph;self.schedule()
    def candidates(self):return [bar for bar,owner,_ in self.entries if owner.isVisibleTo(self.surface) and not bar.isHidden()]
    def select_bar(self):
        candidates=self.candidates()
        def ready_action(bar,role,button):
            if role=='export' and hasattr(bar,'export_source'):button=bar.export_source
            return role!='graph' and button is not None and button.isEnabled()
        ready=[bar for bar in candidates if bar.isEnabled() and any(ready_action(bar,role,button) for role,button in bar.slots.items())];pool=ready or [bar for bar in candidates if bar.isEnabled()] or candidates
        selected=self.chosen if self.chosen in pool else next((bar for bar in pool if bar.property('systemResultActions')),next(iter(pool),None))
        return selected,ready
    def current_bar(self):
        selected,_=self.select_bar();return selected if selected is not None and (selected.isEnabled() or self.graph is None) else self.fallback
    def title(self,bar):
        owner=getattr(bar,'result_view',None) or getattr(bar,'_result_origin',None);value=getattr(owner,'result',None);value=getattr(bar,'system',None) or getattr(bar,'model',None) or value
        if isinstance(value,tuple):value=next(iter(value),None)
        if bar.property('resultCaption'):kind=bar.property('resultCaption')
        elif bar.property('systemResultActions'):kind='Sistema / filtro'
        elif getattr(value,'domain',None)=='frequency':kind='Respuesta en frecuencia' if getattr(value,'data_kind',None)=='frequency_response' else 'Espectro'
        elif getattr(value,'domain',None) in ('continuous','discrete'):kind='Señal'
        elif getattr(owner,'expression_key',None):kind='Expresión'
        else:kind='Resultado'
        name=getattr(value,'name','');return kind+(' · '+name if name and name!=kind else '')
    def choose(self,index):
        if 0<=index<len(self.choices):self.chosen=self.choices[index];self.schedule()
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
        self.pending=False;selected,ready=self.select_bar();self.chosen=selected;self.choices=ready;self.target.blockSignals(True);self.target.clear()
        for bar in ready:self.target.addItem(self.title(bar))
        self.target.setCurrentIndex(ready.index(selected) if selected in ready else -1);self.target.blockSignals(False);self.target_row.setVisible(len(ready)>1);shown=False
        for bar,owner,wrapper in self.entries:
            active=bar is selected;wrapper.setVisible(active);wrapper.setEnabled(owner.isEnabled());shown=shown or active
        target=self.current_bar();fallback=self.graph is not None and target is self.fallback
        if fallback:
            for _,_,wrapper in self.entries:wrapper.hide()
        self.fallback.setVisible(fallback)
        if self.graph is not None:
            if self.graph.parentWidget() is not target:target.claim_graph(self.graph)
        self.setVisible(shown or self.graph is not None);self.updateGeometry()


def install(surface):
    dock=getattr(surface,'action_dock',None)
    if dock is None:
        dock=ResultActionDock(surface);surface.layout().insertWidget(2,dock);surface.action_dock=dock
    for bar in surface.content.findChildren(ResultActionBar):dock.add_bar(bar)
    from .plot_actions import install_context_actions
    install_context_actions(surface,dock)
    from .result_exports import install as install_exports
    install_exports(surface,dock)
    from .result_reuse import install as install_reuse
    install_reuse(surface,dock);dock.refresh();return dock
