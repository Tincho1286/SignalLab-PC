"""Result-side FIR table; selection targets the existing system actions."""
from PySide6.QtCore import Qt,Signal
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QTableWidget,QTableWidgetItem,QAbstractItemView,QHeaderView,QFileDialog,QMessageBox


class FirComparisonView(QWidget):
    selected=Signal(int)

    def __init__(self,parent=None):
        super().__init__(parent);self.data=None
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0)
        self.note=QLabel();self.note.setWordWrap(True);layout.addWidget(self.note)
        self.table=QTableWidget(0,9);self.table.setHorizontalHeaderLabels(['Ventana','L','M','Tipo','D (muestras)','Desvío paso','Máximo rechazo','Cumple','Tiempo (s)'])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers);self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows);self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents);self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAccessibleName('Comparación de diseños FIR');layout.addWidget(self.table,1)
        row=QHBoxLayout();layout.addLayout(row);self.export=QPushButton('Exportar comparación CSV…');self.export.clicked.connect(self.save);row.addWidget(self.export);row.addStretch()
        self.table.currentCellChanged.connect(self.choose)

    def set_result(self,data):
        self.data=data;self.table.blockSignals(True);self.table.clearContents();self.table.setRowCount(len(data['rows']) if data else 0)
        self.export.setEnabled(data is not None)
        if data:
            self.note.setText(data['scope']+' Seleccioná una fila para analizar, exportar o reutilizar ese filtro. Los desvíos están en amplitud lineal.')
            for i,r in enumerate(data['rows']):
                values=[r['name'],r['length'],r['order'],r['fir_type'],r['delay'],r['pass_deviation'],r['stop_maximum'],'Sí' if r['met'] else 'No',r['seconds']]
                for j,value in enumerate(values):
                    item=QTableWidgetItem('—' if value is None else format(value,'.8g') if isinstance(value,float) else str(value))
                    item.setToolTip(r['error'] or 'Cumplimiento numérico; el informe muestra los extremos y límites por banda.')
                    if j==0:item.setData(Qt.ItemDataRole.UserRole,r['system_index'])
                    self.table.setItem(i,j,item)
        self.table.clearSelection();self.table.setCurrentCell(-1,-1);self.table.blockSignals(False)

    def choose(self,row,*_):
        if not self.data or row<0:return
        index=self.data['rows'][row]['system_index']
        self.selected.emit(index if index is not None else -1)

    def save(self):
        if self.data is None:return
        path,_=QFileDialog.getSaveFileName(self,'Exportar comparación FIR','comparacion_fir.csv','Tabla CSV (*.csv)')
        if not path:return
        if not path.lower().endswith('.csv'):path+='.csv'
        try:
            from .fir_comparison import export_csv
            export_csv(self.data,path)
        except (OSError,ValueError) as exc:QMessageBox.warning(self,'No se pudo exportar',str(exc))
