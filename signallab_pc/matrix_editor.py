"""Editor de matriz con celdas visibles bajo demanda y dimensiones explícitas."""
from PySide6.QtGui import QKeySequence
from PySide6.QtCore import Qt,QAbstractTableModel,QModelIndex
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QSpinBox,QTableView,QHeaderView,QApplication,QAbstractItemView,QMessageBox
from .resources import ensure_working_set

class MatrixCells(QAbstractTableModel):
    def __init__(self,parent=None):
        super().__init__(parent);self.rows=0;self.columns=0;self.cells={}
    def rowCount(self,parent=QModelIndex()):return 0 if parent.isValid() else self.rows
    def columnCount(self,parent=QModelIndex()):return 0 if parent.isValid() else self.columns
    def data(self,index,role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():return None
        if role in (Qt.ItemDataRole.DisplayRole,Qt.ItemDataRole.EditRole):return self.cells.get((index.row(),index.column()),'0')
        if role==Qt.ItemDataRole.ToolTipRole:return self.cells.get((index.row(),index.column()),'0')
        if role==Qt.ItemDataRole.TextAlignmentRole:return Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter
    def headerData(self,section,orientation,role=Qt.ItemDataRole.DisplayRole):
        if role==Qt.ItemDataRole.DisplayRole:return str(section+1)
    def flags(self,index):return super().flags(index)|Qt.ItemFlag.ItemIsEditable
    def setData(self,index,value,role=Qt.ItemDataRole.EditRole):
        if role!=Qt.ItemDataRole.EditRole or not index.isValid():return False
        self.cells[(index.row(),index.column())]=str(value).strip()
        self.dataChanged.emit(index,index,[Qt.ItemDataRole.DisplayRole,Qt.ItemDataRole.EditRole]);return True
    def resize(self,rows,columns):
        self.beginResetModel();self.rows=rows;self.columns=columns;self.endResetModel()

class MatrixTable(QTableView):
    def keyPressEvent(self,event):
        if event.matches(QKeySequence.StandardKey.Paste):
            try:self.parentWidget().paste_text(QApplication.clipboard().text())
            except (ValueError,MemoryError) as exc:QMessageBox.warning(self,'No se pudo pegar la matriz',str(exc))
            event.accept();return
        if event.matches(QKeySequence.StandardKey.Copy):
            ranges=self.selectionModel().selection()
            try:ensure_working_set(sum(r.width()*r.height() for r in ranges),bytes_per_sample=128,live_arrays=3)
            except MemoryError as exc:
                QMessageBox.warning(self,'No se pudo copiar la matriz',str(exc));event.accept();return
            indexes=self.selectedIndexes()
            if indexes:
                top,bottom=min(i.row() for i in indexes),max(i.row() for i in indexes)
                left,right=min(i.column() for i in indexes),max(i.column() for i in indexes)
                QApplication.clipboard().setText('\n'.join('\t'.join(str(self.model().data(self.model().index(r,c))) for c in range(left,right+1)) for r in range(top,bottom+1)))
            event.accept();return
        super().keyPressEvent(event)

class MatrixEditor(QWidget):
    def __init__(self,value='',parent=None):
        super().__init__(parent);self._loading=False
        box=QVBoxLayout(self);box.setContentsMargins(0,0,0,0);bar=QHBoxLayout();box.addLayout(bar)
        self.rows=QSpinBox();self.columns=QSpinBox()
        for title,field in [('Filas',self.rows),('Columnas',self.columns)]:
            field.setRange(0,2147483647);field.setKeyboardTracking(False);field.setMinimumHeight(44);bar.addWidget(QLabel(title));bar.addWidget(field)
        self.model=MatrixCells(self);self.table=MatrixTable(self);self.table.setSelectionMode(QAbstractItemView.SelectionMode.ContiguousSelection);self.table.setModel(self.model);self.table.setMinimumHeight(160);self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive);self.table.horizontalHeader().setDefaultSectionSize(145);box.addWidget(self.table)
        hint=QLabel('Una celda por coeficiente. Se admiten números complejos, por ejemplo 1+2i. Las celdas nuevas valen cero. Podés pegar un bloque de una planilla (Ctrl+V).');hint.setWordWrap(True);box.addWidget(hint)
        self.rows.setToolTip('Reducir la matriz oculta celdas; al ampliar se recuperan hasta cargar otro modelo.');self.columns.setToolTip(self.rows.toolTip())
        self.rows.valueChanged.connect(self.resize_matrix);self.columns.valueChanged.connect(self.resize_matrix);self.setText(value)
    def resize_matrix(self):
        if not self._loading:self.model.resize(self.rows.value(),self.columns.value())
    def setText(self,value):
        value=str(value).strip();rows=[row.strip().split(',') for row in value.split(';')] if value else []
        columns=len(rows[0]) if rows else 0
        if any(len(row)!=columns for row in rows):raise ValueError('Todas las filas deben tener la misma cantidad de columnas.')
        if len(rows)>self.rows.maximum() or columns>self.columns.maximum():raise ValueError('La matriz supera las dimensiones admitidas por el editor.')
        self._loading=True;self.model.beginResetModel();self.model.cells={(r,c):cell.strip() for r,row in enumerate(rows) for c,cell in enumerate(row)};self.model.rows=len(rows);self.model.columns=columns;self.model.endResetModel();self.rows.setValue(len(rows));self.columns.setValue(columns);self._loading=False
    def paste_text(self,value):
        value=value.strip('\r\n')
        if not value.strip():return
        lines=value.replace(';','\n').splitlines();separator='\t' if '\t' in value else ','
        rows=[line.split(separator) for line in lines];columns=len(rows[0])
        if any(len(row)!=columns for row in rows):raise ValueError('El bloque pegado debe tener igual cantidad de columnas en cada fila.')
        ensure_working_set(len(rows)*columns,bytes_per_sample=128,live_arrays=3)
        current=self.table.currentIndex();top=current.row() if current.isValid() else 0;left=current.column() if current.isValid() else 0
        if top+len(rows)>self.rows.maximum() or left+columns>self.columns.maximum():raise ValueError('El bloque excede las dimensiones admitidas por la tabla.')
        self._loading=True;self.rows.setValue(max(self.rows.value(),top+len(rows)));self.columns.setValue(max(self.columns.value(),left+columns));self._loading=False
        self.model.resize(self.rows.value(),self.columns.value())
        for r,row in enumerate(rows):
            for c,cell in enumerate(row):self.model.cells[(top+r,left+c)]=cell.strip() or '0'
        self.model.dataChanged.emit(self.model.index(top,left),self.model.index(top+len(rows)-1,left+columns-1))
    def text(self):
        ensure_working_set(self.model.rows*self.model.columns,bytes_per_sample=128,live_arrays=3)
        if not self.model.rows or not self.model.columns:return ''
        return '; '.join(', '.join(self.model.cells.get((r,c),'0') for c in range(self.model.columns)) for r in range(self.model.rows))
