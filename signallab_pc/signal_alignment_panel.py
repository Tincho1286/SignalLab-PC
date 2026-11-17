"""Result-side, paginated pointwise calculation table."""
import csv
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QLineEdit,QTableWidget,QTableWidgetItem,QHeaderView,QFileDialog,QMessageBox
from .atomic_file import atomic_text_file
from .sample_paste import values_text


class AlignmentPanel(QWidget):
    def __init__(self):
        super().__init__();self.trace=None;self.offset=0;self.size=250
        root=QVBoxLayout(self);self.note=QLabel('Calculá para ver la alineación de las entradas.');self.note.setWordWrap(True);root.addWidget(self.note)
        bar=QHBoxLayout();self.coordinate=QLineEdit();self.coordinate.setPlaceholderText('Índice n o instante t');jump=QPushButton('Ir a…');jump.clicked.connect(self.jump);self.export=QPushButton('Exportar tabla…');self.export.clicked.connect(self.export_table);bar.addWidget(self.coordinate,1);bar.addWidget(jump);bar.addWidget(self.export);root.addLayout(bar)
        self.table=QTableWidget(0,5);self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);self.table.setHorizontalHeaderLabels(['Eje','x','Segunda','Resultado','Cobertura']);self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents);self.table.horizontalHeader().setStretchLastSection(True);root.addWidget(self.table,1)
        bar=QHBoxLayout();self.previous=QPushButton('← Anterior');self.next=QPushButton('Siguiente →');self.label=QLabel();self.previous.clicked.connect(lambda:self.move(-1));self.next.clicked.connect(lambda:self.move(1));bar.addWidget(self.previous);bar.addWidget(self.label,1);bar.addWidget(self.next);root.addLayout(bar);self.render()
    def set_trace(self,trace,error=''):
        self.trace=trace;self.offset=0;self.note.setText(error if trace is None else 'Valores del último cálculo; fuera de cada registro se usa 0. En continuo: interpolación lineal e instante de salida más cercano. Los impulsos ideales se consultan en el informe.');self.render()
    def render(self):
        rows=self.trace.page(self.offset,self.size) if self.trace else [];self.table.setRowCount(len(rows))
        for i,row in enumerate(rows):
            for j,value in enumerate(row):self.table.setItem(i,j,QTableWidgetItem(values_text([value]) if j in (1,2,3) else str(value)))
        count=len(self.trace.result.values) if self.trace else 0;self.label.setText(f'{self.offset+1}–{self.offset+len(rows)} de {count}' if rows else 'Sin resultado');self.previous.setEnabled(self.offset>0);self.next.setEnabled(self.offset+self.size<count);self.export.setEnabled(bool(rows))
    def move(self,direction):self.offset+=direction*self.size;self.render()
    def jump(self):
        if self.trace is None:return
        try:self.offset=(self.trace.offset_for(self.coordinate.text())//self.size)*self.size;self.render()
        except Exception as exc:QMessageBox.warning(self,'Coordenada inválida',str(exc))
    def export_table(self):
        if self.trace is None:return
        path,_=QFileDialog.getSaveFileName(self,'Exportar operación por muestra','','CSV (*.csv)')
        if not path:return
        try:
            with atomic_text_file(path,newline='') as stream:
                writer=csv.writer(stream);writer.writerow(['eje ('+self.trace.result.units+')','x','segunda','resultado','cobertura'])
                for offset in range(0,len(self.trace.result.values),self.size):
                    for row in self.trace.page(offset,self.size):writer.writerow([values_text([v]) if j in (1,2,3) else v for j,v in enumerate(row)])
        except Exception as exc:QMessageBox.warning(self,'No se pudo exportar',str(exc))
