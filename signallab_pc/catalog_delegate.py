"""Wrap operation names to keep navigation readable on narrow screens."""
from PySide6.QtCore import Qt,QSize,QRect,QTimer,QEvent
from PySide6.QtWidgets import QStyledItemDelegate,QStyleOptionViewItem,QStyle,QTreeWidgetItemIterator
class CatalogDelegate(QStyledItemDelegate):
    def __init__(self,parent):
        super().__init__(parent);parent.viewport().installEventFilter(self);self.pending=False
    def eventFilter(self,obj,event):
        if event.type()==QEvent.Type.Resize and not self.pending:
            self.pending=True;QTimer.singleShot(0,self,self.update_heights)
        return super().eventFilter(obj,event)
    def update_heights(self):
        self.pending=False;view=self.parent();iterator=QTreeWidgetItemIterator(view)
        while iterator.value() is not None:
            item=iterator.value();depth=0;parent=item.parent()
            while parent is not None:depth+=1;parent=parent.parent()
            width=max(60,view.viewport().width()-view.indentation()*(depth+1)-34)
            metrics=view.fontMetrics();rect=metrics.boundingRect(QRect(0,0,width,2000),Qt.TextFlag.TextWordWrap,item.text(0))
            item.setSizeHint(0,QSize(width,max(30,rect.height()+12)));iterator+=1
    def sizeHint(self,option,index):
        depth=0;parent=index.parent()
        while parent.isValid():depth+=1;parent=parent.parent()
        view=self.parent();width=max(60,view.viewport().width()-view.indentation()*(depth+1)-34)
        rect=option.fontMetrics.boundingRect(QRect(0,0,width,1000),Qt.TextFlag.TextWordWrap,str(index.data() or ''))
        return QSize(width,max(28,rect.height()+12))
    def paint(self,painter,option,index):
        from PySide6.QtGui import QColor,QPen
        from .theme_tokens import COLORS as C
        opt=QStyleOptionViewItem(option);self.initStyleOption(opt,index)
        selected=bool(option.state & QStyle.StateFlag.State_Selected);hovered=bool(option.state & QStyle.StateFlag.State_MouseOver)
        painter.save()
        if selected or hovered:
            painter.setPen(QPen(QColor('#4c6891' if selected else C['rule']),1));painter.setBrush(QColor(C['selected'] if selected else C['hover']));painter.drawRoundedRect(option.rect.adjusted(1,2,-1,-2),8,8)
        rect=option.rect.adjusted(10,5,-9,-5)
        if not opt.icon.isNull():
            opt.icon.paint(painter,QRect(rect.left(),rect.center().y()-9,18,18));rect.adjust(25,0,0,0)
        painter.setFont(option.font);painter.setPen(QColor(C['text'] if selected else C['muted']));painter.drawText(rect,Qt.TextFlag.TextWordWrap|Qt.AlignmentFlag.AlignVCenter,opt.text);painter.restore()
