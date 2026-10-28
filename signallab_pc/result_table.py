"""Consulta paginada de resultados sin materializar todo el eje ni duplicar muestras."""
import numpy as np
from .engine import evaluate_expression
from PySide6.QtCore import Qt,QAbstractTableModel,QModelIndex
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QComboBox,QTableView,QHeaderView,QPushButton,QLabel,QLineEdit,QMessageBox,QApplication

class ResultRows(QAbstractTableModel):
    page_size=500
    def __init__(self,parent=None):
        super().__init__(parent);self.source=None;self.offset=0
    def rowCount(self,parent=QModelIndex()):
        return 0 if parent.isValid() or self.source is None else min(self.page_size,self.source.values.size-self.offset)
    def columnCount(self,parent=QModelIndex()):return 0 if parent.isValid() else 5
    def value(self,row,column):
        index=self.offset+row;source=self.source;value=source.values[index]
        if column==0:
            if source.domain=='discrete':return str(int(source.origin)+index)
            return format(source.origin+source.step*index,'.17g')
        if column==1:return format(value.real,'.17g')
        if column==2:return format(value.imag,'.17g')
        if column==3:return format(abs(value),'.17g')
        return 'No definida' if value==0 else format(np.angle(value),'.17g')
    def data(self,index,role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or self.source is None:return None
        if role in (Qt.ItemDataRole.DisplayRole,Qt.ItemDataRole.ToolTipRole):return self.value(index.row(),index.column())
        if role==Qt.ItemDataRole.TextAlignmentRole:return Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter
    def headerData(self,section,orientation,role=Qt.ItemDataRole.DisplayRole):
        if role!=Qt.ItemDataRole.DisplayRole:return None
        if orientation==Qt.Orientation.Vertical:return str(self.offset+section+1)
        return [('Eje ('+self.source.units+')') if self.source is not None else 'Eje','Real','Imaginaria','Módulo','Fase (rad)'][section]
    def set_source(self,source):
        self.beginResetModel();self.source=source;self.offset=0;self.endResetModel()
    def set_offset(self,offset):
        self.beginResetModel();self.offset=offset;self.endResetModel()

class ResultTable(QWidget):
    def __init__(self):
        super().__init__();self.signals=[];layout=QVBoxLayout(self)
        self.selector=QComboBox();self.selector.setAccessibleName('Señal mostrada en la tabla');self.selector.currentIndexChanged.connect(self.select);layout.addWidget(self.selector)
        self.model=ResultRows(self);self.table=QTableView();self.table.setModel(self.model);self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);self.table.setAlternatingRowColors(True);layout.addWidget(self.table,1)
        bar=QHBoxLayout();self.previous=QPushButton('← Anterior');self.next=QPushButton('Siguiente →');self.status=QLabel();self.position=QLineEdit();self.position.setPlaceholderText('Fila desde 1');self.position.setMaximumWidth(120);jump=QPushButton('Ir');self.copy=QPushButton('Copiar página')
        for item in (self.previous,self.status,self.next):bar.addWidget(item)
        layout.addLayout(bar);search_bar=QHBoxLayout();self.search_mode=QComboBox();self.search_mode.addItems(['Número de fila','Valor del eje']);self.search_mode.setAccessibleName('Buscar por fila o por coordenada')
        for item in (self.search_mode,self.position,jump,self.copy):search_bar.addWidget(item)
        layout.addLayout(search_bar);self.coordinate_note=QLabel();self.coordinate_note.setWordWrap(True);layout.addWidget(self.coordinate_note);self.search_mode.currentIndexChanged.connect(self.update_search_hint)
        note=QLabel('Consulta sin editar · 500 filas por página · La fase es principal y no está definida para módulo cero. Copiar página incluye encabezados y todas sus filas.');note.setWordWrap(True);layout.addWidget(note)
        self.previous.clicked.connect(lambda:self.change(-1));self.next.clicked.connect(lambda:self.change(1));jump.clicked.connect(self.jump);self.position.returnPressed.connect(self.jump);self.copy.clicked.connect(self.copy_page);self.update_status()
    def set_signals(self,signals):
        self.signals=list(signals);self.selector.blockSignals(True);self.selector.clear()
        for signal in self.signals:self.selector.addItem(signal.name)
        self.selector.blockSignals(False);self.selector.setVisible(len(self.signals)>1);self.select(self.selector.currentIndex())
    def select(self,index):
        self.model.set_source(self.signals[index] if 0<=index<len(self.signals) else None);self.coordinate_note.clear();self.update_status();self.update_search_hint()
    def update_status(self):
        source=self.model.source;active=source is not None;start=self.model.offset;end=start+self.model.rowCount()
        self.previous.setEnabled(active and start>0);self.next.setEnabled(active and end<source.values.size);self.copy.setEnabled(active)
        self.status.setText(f'{start+1:,}–{end:,} de {source.values.size:,}' if active else 'Sin datos')
    def change(self,direction):
        if self.model.source is None:return
        offset=self.model.offset+direction*self.model.page_size
        if 0<=offset<self.model.source.values.size:self.model.set_offset(offset);self.update_status()
    def update_search_hint(self,*_):
        source=self.model.source
        self.position.setPlaceholderText('Fila desde 1' if self.search_mode.currentIndex()==0 else ('Índice entero' if source is not None and source.domain=='discrete' else 'Valor, por ej. pi/4'))
        self.position.setToolTip('Se selecciona el punto almacenado más cercano; no se interpola.' if self.search_mode.currentIndex() else 'Posición del dato en la tabla, desde 1.')
    def jump(self):
        source=self.model.source
        if source is None:return
        try:
            if self.search_mode.currentIndex()==0:
                index=int(self.position.text())-1
                if not 0<=index<source.values.size:raise ValueError('La fila debe estar dentro del resultado, comenzando en 1.')
                message=''
            elif source.domain=='discrete':
                coordinate=int(self.position.text());index=coordinate-int(source.origin)
                if not 0<=index<source.values.size:raise ValueError('El índice debe pertenecer al registro.')
                message=f'Índice seleccionado: {coordinate} · fila {index+1:,}.'
            else:
                coordinate=complex(evaluate_expression(self.position.text(),np.array([0.]))[0])
                if coordinate.imag or not np.isfinite(coordinate):raise ValueError('La coordenada debe ser real y finita.')
                coordinate=coordinate.real;last=source.origin+source.step*(source.values.size-1)
                if not np.isfinite(last) or not min(source.origin,last)<=coordinate<=max(source.origin,last):raise ValueError('El valor debe estar dentro del intervalo disponible.')
                index=int(round((coordinate-source.origin)/source.step));index=min(max(index,0),source.values.size-1)
                actual=source.origin+index*source.step
                message=f'Solicitado: {coordinate:.12g} · punto almacenado: {actual:.12g} {source.units} · diferencia: {actual-coordinate:.6g}. Sin interpolación.'
            offset=(index//self.model.page_size)*self.model.page_size;self.model.set_offset(offset);self.update_status();self.table.selectRow(index-offset);self.table.scrollTo(self.model.index(index-offset,0));self.coordinate_note.setText(message)
        except (ValueError,OverflowError) as exc:QMessageBox.warning(self,'Ubicación inválida',str(exc))
    def copy_page(self):
        if self.model.source is None:return
        rows=['\t'.join(self.model.headerData(c,Qt.Orientation.Horizontal) for c in range(5))]
        rows+=['\t'.join(self.model.value(r,c) for c in range(5)) for r in range(self.model.rowCount())]
        QApplication.clipboard().setText('\n'.join(rows))
