"""Historiales de una recurrencia, asociados a índices relativos al inicio."""
from PySide6.QtCore import Qt,QAbstractTableModel,QModelIndex
from PySide6.QtWidgets import QWidget,QVBoxLayout,QTableView,QHeaderView,QLabel,QPushButton
from .resources import ensure_working_set

class HistoryRows(QAbstractTableModel):
    def __init__(self,symbol,parent=None):
        super().__init__(parent);self.symbol=symbol;self.count=0;self.entries={}
    def rowCount(self,parent=QModelIndex()):return 0 if parent.isValid() else self.count
    def columnCount(self,parent=QModelIndex()):return 0 if parent.isValid() else 2
    def data(self,index,role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():return None
        if role in (Qt.ItemDataRole.DisplayRole,Qt.ItemDataRole.EditRole):
            return f'{self.symbol}[n₀−{index.row()+1}]' if index.column()==0 else self.entries.get(index.row(),'0')
        if role==Qt.ItemDataRole.ToolTipRole:return 'Valor anterior al comienzo del registro. Admite complejos como 1+2i; vacío equivale a cero.'
    def headerData(self,section,orientation,role=Qt.ItemDataRole.DisplayRole):
        if role==Qt.ItemDataRole.DisplayRole:return ('Índice','Valor')[section] if orientation==Qt.Orientation.Horizontal else str(section+1)
    def flags(self,index):return super().flags(index)|(Qt.ItemFlag.ItemIsEditable if index.column()==1 else Qt.ItemFlag.NoItemFlags)
    def setData(self,index,value,role=Qt.ItemDataRole.EditRole):
        if not index.isValid() or index.column()!=1 or role!=Qt.ItemDataRole.EditRole:return False
        text=str(value).strip() or '0'
        if text=='0':self.entries.pop(index.row(),None)
        else:self.entries[index.row()]=text
        self.dataChanged.emit(index,index);return True
    def resize(self,count):
        self.beginResetModel();self.count=max(0,int(count));self.endResetModel()
    def clear(self):
        self.beginResetModel();self.entries.clear();self.endResetModel()

class HistoryEditor(QWidget):
    def __init__(self,symbol,parent=None):
        super().__init__(parent);layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0)
        self.model=HistoryRows(symbol,self);self.table=QTableView();self.table.setModel(self.model);self.table.verticalHeader().hide();self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.ResizeToContents);self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.Stretch);layout.addWidget(self.table)
        self.note=QLabel();self.note.setWordWrap(True);layout.addWidget(self.note)
        self.reset=QPushButton('Poner todos en cero');self.reset.clicked.connect(self.model.clear);layout.addWidget(self.reset);self.set_count(0)
    def set_count(self,count):
        self.model.resize(count);self.table.setVisible(count>0);self.reset.setVisible(count>0);self.table.setFixedHeight(48+30*min(max(1,count),5))
        self.note.setText('Este sistema no requiere valores anteriores de esta variable.' if count==0 else f'{count} valores anteriores. n₀ es el inicio del registro. Al reducir el orden, las filas ocultas se conservan para recuperarlas si lo aumentás.')
    def text(self):
        ensure_working_set(self.model.count,bytes_per_sample=128,live_arrays=4)
        return ', '.join(self.model.entries.get(index,'0') for index in range(self.model.count))
