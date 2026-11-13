"""A paginated product table and stem alignment in the convolution result."""
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLineEdit,QLabel,QPushButton,QComboBox,QTableWidget,QTableWidgetItem,QHeaderView
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT
from .active_stack import ActiveTabs
from .convolution_steps import inspect,summary
from .numeric_input import integer_field
from .report_view import ReportView,report_panel
from .result_summary import number
from .signal_plot import plot_samples,configure_axis


class ConvolutionInspector(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent);self.trace=None;self.data=None;self.offset=0
        root=QVBoxLayout(self);root.setContentsMargins(0,0,0,0)
        row=QHBoxLayout();root.addLayout(row)
        self.previous=QPushButton('← n');self.next=QPushButton('n →');self.index=QLineEdit();self.index.setMaximumWidth(180);self.index.setAccessibleName('Muestra n de la convolución')
        row.addWidget(self.previous);row.addWidget(QLabel('n ='));row.addWidget(self.index);row.addWidget(self.next)
        self.range=QLabel();self.range.setWordWrap(True);row.addWidget(self.range,1)
        self.tabs=ActiveTabs();root.addWidget(self.tabs,1)
        self.report=ReportView();self.tabs.addTab(report_panel(self.report),'Explicación')
        page=QWidget();layout=QVBoxLayout(page);self.tabs.addTab(page,'Productos')
        bar=QHBoxLayout();layout.addLayout(bar);self.back=QPushButton('← Productos');self.forward=QPushButton('Productos →');self.page_note=QLabel();self.page_note.setWordWrap(True)
        bar.addWidget(self.back);bar.addWidget(self.forward);bar.addWidget(self.page_note,1)
        self.table=QTableWidget(0,5);self.table.setHorizontalHeaderLabels(['k','n−k','x[k]','h[n−k]','Producto'])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents);self.table.horizontalHeader().setStretchLastSection(True);layout.addWidget(self.table,1)
        page=QWidget();layout=QVBoxLayout(page);self.tabs.addTab(page,'Alineación')
        self.components=QComboBox();self.components.addItems(['Parte real','Parte imaginaria','Módulo'])
        self.figure=Figure(figsize=(7,5));self.canvas=FigureCanvasQTAgg(self.figure);self.toolbar=NavigationToolbar2QT(self.canvas,self)
        self.toolbar.addWidget(self.components);layout.addWidget(self.toolbar);layout.addWidget(self.canvas,1)
        self.canvas._signallab_explicit_plot=True
        from .plot_view import install_figure_layout
        install_figure_layout(self.canvas)
        self.previous.clicked.connect(lambda:self.move(-1));self.next.clicked.connect(lambda:self.move(1));self.index.returnPressed.connect(self.new_index)
        self.back.clicked.connect(lambda:self.page(-100));self.forward.clicked.connect(lambda:self.page(100));self.components.currentIndexChanged.connect(self.draw)

    def set_trace(self,trace,error=None):
        self.trace=trace;self.data=None;self.offset=0
        if trace is None:
            self.report.setPlainText('La convolución se calculó. El inspector no está disponible: '+str(error or 'sin muestras capturadas.'));self.table.setRowCount(0);self.figure.clear();self.canvas.draw_idle();self.index.setEnabled(False);return
        self.index.setEnabled(True);self.index.setText(str(trace.y0));self.range.setText(f'Intervalo: {trace.y0} a {trace.y0+len(trace.y)-1}');self.show_step()

    def new_index(self):self.offset=0;self.show_step()

    def move(self,delta):
        if self.trace is None:return
        try:self.index.setText(str(integer_field(self.index)+delta));self.new_index()
        except ValueError as exc:self.report.setPlainText(str(exc))

    def page(self,delta):self.offset=max(0,self.offset+delta);self.show_step()

    def show_step(self):
        if self.trace is None:return
        try:
            data=inspect(self.trace,integer_field(self.index),self.offset);self.data=data
            self.report.set_readable(summary(data));self.table.setRowCount(len(data['rows']))
            for i,row in enumerate(data['rows']):
                for j,key in enumerate(('k','h_index','x','h','product')):
                    text=str(row[key]) if j<2 else number(row[key]) if row[key] is not None else 'Fuera de rango float64'
                    item=QTableWidgetItem(text);item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable);self.table.setItem(i,j,item)
            self.previous.setEnabled(data['index']>self.trace.y0);self.next.setEnabled(data['index']<self.trace.y0+len(self.trace.y)-1)
            self.back.setEnabled(self.offset>0);self.forward.setEnabled(self.offset+len(data['rows'])<data['total'])
            self.page_note.setText(f"Productos {self.offset+1} a {self.offset+len(data['rows'])} de {data['total']} · la alineación usa esta misma página")
            self.draw()
        except ValueError as exc:
            self.data=None;self.report.setPlainText(str(exc));self.table.setRowCount(0);self.figure.clear();self.canvas.draw_idle()

    def draw(self,*_):
        self.figure.clear()
        if self.data is None:self.canvas.draw_idle();return
        rows=self.data['rows'];indices=np.array([r['k'] for r in rows],dtype=np.int64)
        convert=(np.real,np.imag,np.abs)[self.components.currentIndex()]
        a,b=self.figure.subplots(2,1,sharex=True)
        for key,label,color in [('x','x[k]','#91b7ff'),('h','h[n−k]','#78d6c2')]:
            plot_samples(a,indices,convert([r[key] for r in rows]),discrete=True,label=label,color=color)
        plot_samples(b,indices,convert([r['product'] if r['product'] is not None else complex(np.nan,np.nan) for r in rows]),discrete=True,label='x[k] · h[n−k]',color='#edc27d')
        for axis in (a,b):
            configure_axis(axis,discrete_index=True,index_symbol='k',units='n',label='Índice k (muestras)');axis.grid(alpha=.15);axis.legend(loc='upper left',bbox_to_anchor=(1.01,1));axis.set_ylabel(self.components.currentText())
        a.set_title('Alineación para n='+str(self.data['index'])+' · página de productos')
        self.canvas.draw_idle()
