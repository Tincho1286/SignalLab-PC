"""Visible choices wrap at their natural widths instead of truncating labels."""
from PySide6.QtCore import Qt,QRect,QSize
from PySide6.QtWidgets import QLayout,QWidget


class FlowLayout(QLayout):
    def __init__(self,parent=None,spacing=6):super().__init__(parent);self.items=[];self.text_padding=34;self.setContentsMargins(0,0,0,0);self.setSpacing(spacing)
    def __del__(self):
        while self.items:self.takeAt(0)
    def addItem(self,item):self.items.append(item)
    def count(self):return len(self.items)
    def itemAt(self,index):return self.items[index] if 0<=index<len(self.items) else None
    def takeAt(self,index):return self.items.pop(index) if 0<=index<len(self.items) else None
    def expandingDirections(self):return Qt.Orientation(0)
    def hasHeightForWidth(self):return True
    def heightForWidth(self,width):return self.arrange(QRect(0,0,width,0),True)
    def setGeometry(self,rect):super().setGeometry(rect);self.arrange(rect,False)
    def natural(self,item):
        size=item.sizeHint();widget=item.widget()
        if widget is not None and hasattr(widget,'text'):
            widget.ensurePolished();size.setWidth(max(size.width(),widget.fontMetrics().horizontalAdvance(widget.text().replace('&',''))+self.text_padding))
        return size
    def sizeHint(self):
        visible=[self.natural(item) for item in self.items if not item.isEmpty()]
        return QSize(sum(size.width() for size in visible)+max(0,len(visible)-1)*self.spacing(),max((size.height() for size in visible),default=0))
    def minimumSize(self):
        visible=[item for item in self.items if not item.isEmpty()]
        return QSize(max((item.minimumSize().width() for item in visible),default=0),max((item.minimumSize().height() for item in visible),default=0))
    def arrange(self,rect,test):
        x,y,height=rect.x(),rect.y(),0;gap=self.spacing()
        for item in self.items:
            if item.isEmpty():continue
            size=self.natural(item);width=min(size.width(),rect.width())
            if x>rect.x() and x+width>rect.right()+1:x=rect.x();y+=height+gap;height=0
            if not test:item.setGeometry(QRect(x,y,width,size.height()))
            x+=width+gap;height=max(height,size.height())
        return y+height-rect.y()
    def addStretch(self,*_):pass


class WrappingRow(QWidget):
    def __init__(self,parent=None):super().__init__(parent);self.flow=FlowLayout(self)
    def minimumSizeHint(self):return QSize(0,self.flow.minimumSize().height())
