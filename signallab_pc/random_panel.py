from .numeric_input import real_field,integer_field
"""Herramientas independientes para señales aleatorias y sus registros."""
import secrets
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QLineEdit,QComboBox,QPushButton,QLabel,QScrollArea,QSplitter,QTabWidget,QMessageBox
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT
from . import random_signals
from .report_view import ReportView,report_panel
from .tool_guide import ToolGuide

class RandomPanel(QWidget):
    def __init__(self,window,action):
        super().__init__();self.window=window;self.action=action
        from .toolbox import LocalInput,ResultView
        root=QVBoxLayout(self);split=QSplitter(Qt.Orientation.Horizontal);split.setChildrenCollapsible(False);root.addWidget(split)
        controls=QWidget();form=QFormLayout(controls);form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form.addRow(ToolGuide('Generá una realización reproducible y usala en filtrado o análisis espectral.' if action=='generate' else 'Medí un registro finito. Sus estadísticas no prueban las propiedades de todo un proceso aleatorio.',('Distribución','Muestras','Análisis') if action=='generate' else ('Registro','Estadísticas','Histograma')))
        if action=='generate':
            self.distribution=QComboBox();self.distribution.addItems(['Gaussiana','Uniforme','Bernoulli (0 o 1)']);form.addRow('Distribución',self.distribution)
            self.mean=QLineEdit('0');self.std=QLineEdit('1');self.probability=QLineEdit('0.5');self.count=QLineEdit('1024');self.origin=QLineEdit('0');self.seed=QLineEdit('12345')
            for label,field in [('Media teórica',self.mean),('Desviación estándar',self.std),('Probabilidad de obtener 1',self.probability),('Cantidad de muestras',self.count),('Índice inicial',self.origin),('Semilla reproducible',self.seed)]:form.addRow(label,field)
            fresh=QPushButton('Elegir otra semilla');fresh.clicked.connect(lambda:self.seed.setText(str(secrets.randbits(32))));form.addRow(fresh)
            def update(*_):
                bernoulli=self.distribution.currentIndex()==2
                form.setRowVisible(self.mean,not bernoulli);form.setRowVisible(self.std,not bernoulli);form.setRowVisible(self.probability,bernoulli)
            self.distribution.currentIndexChanged.connect(update);update()
            note=QLabel('La misma semilla y parámetros reproducen el registro en esta versión. En uniforme, los límites son media ± √3·desviación. La media medida puede diferir de la teórica.');note.setWordWrap(True);form.addRow(note)
        else:
            self.source=LocalInput('Registro para analizar');self.source.bind_project(window);form.addRow(self.source)
            self.component=QComboBox();self.component.addItems(['Parte real','Parte imaginaria','Módulo']);form.addRow('Componente del histograma',self.component)
            self.bins=QLineEdit('30');form.addRow('Intervalos del histograma',self.bins)
        button=QPushButton('Generar señal' if action=='generate' else 'Calcular estadísticas');button.setObjectName('primary');button.clicked.connect(self.calculate);form.addRow(button)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);scroll.setMinimumWidth(320);split.addWidget(scroll)
        self.tabs=QTabWidget();split.addWidget(self.tabs);split.setSizes([350,740]);split.setStretchFactor(1,1)
        self.output=ResultView();self.tabs.addTab(self.output,'Señal')
        self.report=ReportView();self.tabs.addTab(report_panel(self.report),'Estadísticas')
        self.report.setPlainText('Completá los datos y calculá. Los resultados describen una realización finita, no toda la distribución.')
        if action!='generate':
            plot=QWidget();box=QVBoxLayout(plot);self.figure=Figure(figsize=(7,4));self.canvas=FigureCanvasQTAgg(self.figure);self.canvas.setMinimumHeight(280);box.addWidget(NavigationToolbar2QT(self.canvas,self));box.addWidget(self.canvas,1);self.tabs.addTab(plot,'Histograma')
    def calculate(self):
        try:
            if self.action=='generate':
                kind=['gaussian','uniform','bernoulli'][self.distribution.currentIndex()]
                args=(kind,integer_field(self.count),real_field(self.mean) if kind!='bernoulli' else 0,real_field(self.std) if kind!='bernoulli' else 1,real_field(self.probability) if kind=='bernoulli' else .5,integer_field(self.seed),integer_field(self.origin))
                def accept(signal):
                    self.window.publish(signal,operation='Generación aleatoria');self.output.show_result(signal);self.tabs.setCurrentIndex(0)
                    meta=signal.metadata;self.report.setPlainText(f"Distribución: { {'gaussian':'Gaussiana','uniform':'Uniforme','bernoulli':'Bernoulli'}[kind] }\nMuestras: {signal.values.size}\nSemilla: {meta['seed']}\nMedia teórica: {meta['theoretical_mean']}\nVarianza teórica: {meta['theoretical_variance']}\n\nLa generación produce muestras independientes del modelo elegido. Usá Estadísticas e histograma para medir esta realización, o Usar señal en… para filtrarla.")
                self.window._run_operation('Generando señal aleatoria…',lambda:random_signals.generate(*args),accept)
            else:
                source=self.source.read();parent=self.source.reference_id;component=['real','imag','magnitude'][self.component.currentIndex()]
                from .auxiliary import optional
                bins,bins_notice=optional('Intervalos del histograma',lambda:integer_field(self.bins))
                def accept(data):
                    self.window.publish(data,title='Estadísticas de '+source.name,operation='Estadísticas de registro',parents=[parent] if parent else [])
                    self.output.show_result(source)
                    self.report.setPlainText(f"Registro: {source.name}\nMuestras: {data['samples']}\nMedia real: {data['mean_real']}\nMedia imaginaria: {data['mean_imag']}\nVarianza con divisor N: {data['variance_N']}\nVarianza con divisor N−1: {data['variance_N_minus_1'] if data['variance_N_minus_1'] is not None else 'No definida con una muestra'}\nValor cuadrático medio: {data['mean_square']}\nRMS: {data['rms']}\n\n"+data['scope']+'\n\nEl histograma estima una densidad por intervalos, no una distribución exacta. El área total es 1; la altura depende del ancho de cada intervalo.')
                    if data.get('histogram_notice'):self.report.appendPlainText('\n'+data['histogram_notice'])
                    self.figure.clear();axis=self.figure.add_subplot(111);edges=np.asarray(data['histogram_edges']);axis.bar(edges[:-1],data['histogram_density'],width=np.diff(edges),align='edge',alpha=.8);axis.set_xlabel({'real':'Parte real','imag':'Parte imaginaria','magnitude':'Módulo'}[component]);axis.set_ylabel('Densidad estimada');axis.grid(alpha=.2);self.figure.tight_layout();self.canvas.draw_idle();self.tabs.setCurrentIndex(1)
                    if data.get('histogram_notice'):
                        axis.clear();axis.set_axis_off();axis.text(.5,.5,data['histogram_notice'],ha='center',va='center',wrap=True,transform=axis.transAxes);self.canvas.draw_idle()
                self.window._run_operation('Calculando estadísticas…',lambda:random_signals.statistics(source,component,bins,histogram_notice=bins_notice),accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá las entradas',str(exc))
