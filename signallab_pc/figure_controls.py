"""Keep scientific controls visible instead of overflowing the navigation toolbar."""
from PySide6.QtCore import Qt,QRect,QPoint,QSize
from PySide6.QtWidgets import QWidget,QLayout,QToolButton,QWidgetAction,QSizePolicy
from .theme_tokens import COLORS as C


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
        super().__init__(parent);self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Minimum);policy=self.sizePolicy();policy.setHeightForWidth(True);self.setSizePolicy(policy);self.flow=WrappedControls(self);self.projected=[]
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
        self.refresh_theme(None)
    def synchronize(self,action,widget):widget.setVisible(action.isVisible());self.flow.invalidate();self.updateGeometry()
    def refresh_theme(self,previous):
        self.setStyleSheet('QToolButton[figureControl="true"] {background:'+C['panel']+';color:'+C['text']+';border:1px solid '+C['border']+';border-radius:6px;padding:5px 9px;} QToolButton[figureControl="true"]:hover {border-color:'+C['accent']+';} QToolButton[figureControl="true"]:checked {border-color:'+C['accent']+';background:'+C['report']+';}')


def install(toolbar,layout,canvas):
    controls=ScientificControls(toolbar,layout.parentWidget());layout.insertWidget(layout.indexOf(toolbar)+1,controls);canvas._signallab_scientific_controls=controls
