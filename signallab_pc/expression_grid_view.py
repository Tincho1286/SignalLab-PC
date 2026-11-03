"""Explicit missing positions: plot, paginated values and lossless export."""
from types import SimpleNamespace
import numpy as np
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QComboBox,QPushButton,QTabWidget,QFileDialog,QMessageBox
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT

class ExpressionGridView(QWidget):
    def __init__(self):
        super().__init__();self.data=None;layout=QVBoxLayout(self);self.note=QLabel();self.note.setWordWrap(True);layout.addWidget(self.note)
        row=QHBoxLayout();self.components=QComboBox();self.components.addItems(['Módulo y fase','Parte real e imaginaria']);row.addWidget(self.components)
        export=QPushButton('Exportar datos…');export.clicked.connect(self.export);row.addWidget(export);layout.addLayout(row)
        self.tabs=QTabWidget();layout.addWidget(self.tabs);plot=QWidget();box=QVBoxLayout(plot)
        self.figure=Figure(figsize=(7,4));self.canvas=FigureCanvasQTAgg(self.figure);self.toolbar=NavigationToolbar2QT(self.canvas,self);box.addWidget(self.toolbar);box.addWidget(self.canvas);self.tabs.addTab(plot,'Gráfico')
        from .result_table import ResultTable
        self.table=ResultTable();self.tabs.addTab(self.table,'Valores');self.components.currentIndexChanged.connect(self.draw)
    def set_grid(self,data,units):
        self.data={**data,'units':units};values=np.array([complex(*v) if v is not None else complex(np.nan,np.nan) for v in data['samples']])
        self.source=SimpleNamespace(values=values,origin=data['origin'],step=data['step'],units=units,name='Resultado condicionado',domain='continuous' if data['variable']=='t' else 'frequency',metadata={})
        self.table.set_signals([self.source]);self.table.note.setText('N/D conserva su posición; no se interpola ni se convierte en cero. Para reutilizar la función usá el resultado algebraico.')
        self.note.setText(str(data['undefined_count'])+' posiciones no definidas. Condición: '+data['condition']+'. '+data['scope'])
        self.tabs.setCurrentIndex(0);self.draw()
        from .plot_view import install_enlarge,enlarge_plot
        install_enlarge(self.toolbar);self.canvas.draw();enlarge_plot(self.canvas,self)
    def draw(self,*_):
        if self.data is None:return
        source=self.source;values=source.values;axis=source.origin+source.step*np.arange(len(values));self.figure.clear();axes=self.figure.subplots(2,1,sharex=True)
        polar=self.components.currentIndex()==0
        first=abs(values) if polar else values.real
        second=np.where(abs(values)>0,np.angle(values),np.nan) if polar else values.imag
        for plot,component,label in zip(axes,(first,second),('Módulo' if polar else 'Parte real','Fase (rad)' if polar else 'Parte imaginaria')):
            line=plot.plot(axis,component)[0];line._signallab_probe_values=(source.origin,source.step,component);plot.set_ylabel(label);plot.grid(alpha=.2)
        if not np.isfinite(values).any():axes[0].text(.5,.5,'No hay valores definidos en este intervalo',ha='center',transform=axes[0].transAxes)
        from .signal_plot import configure_signal_axis
        configure_signal_axis(axes[-1],source);self.canvas.draw_idle()
    def save(self,path):
        from pathlib import Path
        if Path(path).suffix.lower()=='.json':
            from .atomic_file import write_json
            write_json(path,self.data);return
        import csv
        from .atomic_file import atomic_text_file
        with atomic_text_file(path,encoding='utf-8-sig',newline='') as stream:
            writer=csv.writer(stream);writer.writerow(['# SignalLab expression grid','units='+self.data['units'],'condition='+self.data['condition']]);writer.writerow(['axis','real','imag','defined'])
            for index,pair in enumerate(self.data['samples']):writer.writerow([format(self.data['origin']+index*self.data['step'],'.17g'),*(pair if pair is not None else ('','')),pair is not None])
    def export(self):
        path,selected=QFileDialog.getSaveFileName(self,'Exportar valores con N/D','resultado_condicionado','SignalLab JSON (*.json);;Tabla CSV (*.csv)')
        if not path:return
        try:
            from pathlib import Path
            if not Path(path).suffix:path+='.csv' if 'CSV' in selected else '.json'
            self.save(path)
        except (OSError,ValueError) as exc:QMessageBox.warning(self,'No se pudo exportar',str(exc))
