"""Keep scientific controls visible instead of overflowing the navigation toolbar."""
from PySide6.QtCore import Qt,QRect,QPoint,QSize
from PySide6.QtWidgets import QWidget,QLayout,QMenu,QToolButton,QWidgetAction,QSizePolicy
from .design import icon


NAVIGATION = {
    'home': ('Restablecer vista', 'home'),
    'back': ('Vista anterior', 'back'),
    'forward': ('Vista siguiente', 'forward'),
    'pan': ('Desplazar ejes', 'pan'),
    'zoom': ('Zoom por región', 'search'),
    'configure_subplots': ('Ajustar paneles', 'filter'),
    'edit_parameters': ('Editar propiedades de las curvas', 'chart'),
    'save_figure': ('Guardar figura…', 'export'),
}


def style_navigation(toolbar):
    toolbar.setObjectName('figureNavigation')
    toolbar.setIconSize(QSize(18, 18))
    toolbar.setMovable(False)
    toolbar.setFloatable(False)
    toolbar.setAccessibleName('Navegación y guardado de la figura')
    for key, (label, symbol) in NAVIGATION.items():
        action = toolbar._actions.get(key)
        if action is None:
            continue
        action.setText(label)
        action.setToolTip(label)
        action.setIcon(icon(symbol))
        button = toolbar.widgetForAction(action)
        if button is not None:
            button.setAccessibleName(label)
    location = getattr(toolbar, 'locLabel', None)
    if location is not None:
        location.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        location.hide()

    view = QToolButton()
    view.setObjectName('figureViewMenu')
    view.setText('Vista')
    view.setAccessibleName('Opciones de vista de la figura')
    view.setToolTip('Historial del zoom y ajustes de los paneles')
    view.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
    menu = QMenu(view)
    view.setMenu(menu)
    for key in ('back', 'forward', 'configure_subplots', 'edit_parameters'):
        action = toolbar._actions.get(key)
        if action is not None:
            toolbar.removeAction(action)
            menu.addAction(action)
    toolbar.addWidget(view)


class WrappedControls(QLayout):
    def __init__(self,parent):super().__init__(parent);self.items=[];self.setContentsMargins(0,2,0,2);self.setSpacing(6)
    def addItem(self,item):self.items.append(item)
    def count(self):return len(self.items)
    def itemAt(self,index):return self.items[index] if 0<=index<len(self.items) else None
    def takeAt(self,index):return self.items.pop(index) if 0<=index<len(self.items) else None
    def expandingDirections(self):return Qt.Orientation.Horizontal
    def hasHeightForWidth(self):return True
    def heightForWidth(self,width):return self.arrange(QRect(0,0,width,0),True)
    def setGeometry(self,rect):super().setGeometry(rect);self.arrange(rect,False)
    def sizeHint(self):return self.minimumSize()
    def minimumSize(self):
        size=QSize()
        for item in self.items:
            if not item.isEmpty():size=size.expandedTo(item.minimumSize())
        left,top,right,bottom=self.getContentsMargins();return size+QSize(left+right,top+bottom)
    def arrange(self,rect,measure):
        left,top,right,bottom=self.getContentsMargins();area=rect.adjusted(left,top,-right,-bottom);x=area.x();y=area.y();height=0;gap=self.spacing()
        for item in self.items:
            if item.isEmpty():continue
            wanted=item.sizeHint();width=min(wanted.width(),max(1,area.width()))
            if x+width>area.right()+1 and height:y+=height+gap;x=area.x();height=0
            if not measure:item.setGeometry(QRect(QPoint(x,y),QSize(width,wanted.height())))
            x+=width+gap;height=max(height,wanted.height())
        return y-rect.y()+height+bottom


class ScientificControls(QWidget):
    def __init__(self,toolbar,parent):
        super().__init__(parent);self.setObjectName('figureMeasureTools');self.setAccessibleName('Representación y medidas de la figura');self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Minimum);policy=self.sizePolicy();policy.setHeightForWidth(True);self.setSizePolicy(policy);self.flow=WrappedControls(self);self.projected=[]
        navigation=set(getattr(toolbar,'_actions',{}).values());coordinates=getattr(toolbar,'locLabel',None)
        for action in list(toolbar.actions()):
            widget=action.defaultWidget() if isinstance(action,QWidgetAction) else None
            if action in navigation or widget is coordinates and widget is not None:continue
            toolbar.removeAction(action)
            if action.isSeparator():continue
            if widget is None:
                widget=QToolButton();widget.setDefaultAction(action);widget.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon);widget.setProperty('figureControl',True)
            else:widget.setMinimumWidth(0)
            self.flow.addWidget(widget);self.projected.append((action,widget));widget.setVisible(action.isVisible())
            action.changed.connect(lambda a=action,w=widget:self.synchronize(a,w))
        style_navigation(toolbar)
    def synchronize(self,action,widget):widget.setVisible(action.isVisible());self.flow.invalidate();self.updateGeometry()


def install(toolbar,layout,canvas):
    controls=ScientificControls(toolbar,layout.parentWidget());layout.insertWidget(layout.indexOf(toolbar)+1,controls);canvas._signallab_scientific_controls=controls
