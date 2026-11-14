"""Measurements of a captured analysis, with local controls beside its report."""
import csv,json
from copy import deepcopy
from dataclasses import replace
import numpy as np
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QComboBox,QLineEdit,QPushButton,QLabel,QScrollArea,QTableWidget,QTableWidgetItem,QHeaderView,QTableView,QMessageBox,QFileDialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT
from . import frequency_measurements as calc
from .spectral_measurements_panel import Rows
from .scalar_expression import real_value
from .numeric_input import real_field,integer_field
from .report_view import ReportView,report_panel
from .atomic_file import atomic_text_file


class Constraints(QWidget):
    textChanged=Signal()
    def __init__(self):
        super().__init__();layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);bar=QHBoxLayout();layout.addLayout(bar)
        add=QPushButton('+ Banda');remove=QPushButton('Quitar');bar.addWidget(add);bar.addWidget(remove);bar.addStretch()
        self.table=QTableWidget(0,5);self.table.setHorizontalHeaderLabels(['Nombre','Desde','Hasta','Mínimo |H|','Máximo |H|']);self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents);self.table.setMaximumHeight(180);layout.addWidget(self.table)
        note=QLabel('Desde/Hasta vacíos usan el intervalo analizado. Los límites de módulo son amplitudes lineales; vacío no impone ese límite. No agregues las transiciones a las bandas exigidas.');note.setWordWrap(True);layout.addWidget(note)
        self.table.itemChanged.connect(lambda *_:self.textChanged.emit());add.clicked.connect(self.add);remove.clicked.connect(self.remove);self.add()
    def add(self,*_):
        self.table.blockSignals(True);row=self.table.rowCount();self.table.insertRow(row)
        for col,text in enumerate(('Banda '+str(row+1),'','','','')):self.table.setItem(row,col,QTableWidgetItem(text))
        self.table.blockSignals(False);self.textChanged.emit()
    def remove(self):
        row=self.table.currentRow()
        if row>=0:self.table.removeRow(row);self.textChanged.emit()
    def text(self):return json.dumps([[self.table.item(r,c).text() for c in range(5)] for r in range(self.table.rowCount())])
    def read(self):
        rows=[]
        for row in json.loads(self.text()):rows.append((row[0] or 'Banda',*[real_value(v) if v.strip() else None for v in row[1:]]))
        return rows


COLUMNS={
'points':[('frequency','Frecuencia'),('real','Parte real'),('imag','Parte imaginaria'),('magnitude','|H|'),('db','Módulo (dB)'),('phase','Ángulo principal (rad)'),('delay','Retardo de grupo')],
'bands':[('name','Banda'),('low','Desde'),('high','Hasta'),('minimum','Mínimo |H|'),('minimum_at','En frecuencia'),('maximum','Máximo |H|'),('maximum_at','En frecuencia'),('lower_limit','Límite inferior'),('upper_limit','Límite superior'),('margin','Margen'),('status','Comprobación'),('undefined','No definidos'),('failed_refinements','Refinamientos pendientes')],
'delay':[('name','Banda'),('low','Desde'),('high','Hasta'),('delay_min','Menor retardo'),('delay_min_at','En frecuencia'),('delay_max','Mayor retardo'),('delay_max_at','En frecuencia'),('delay_median','Mediana'),('delay_spread','Variación'),('delay_points','Puntos válidos'),('delay_undefined','No definidos')]}
COLUMNS['level']=COLUMNS['points']


class FrequencyMeasurementsPanel(QWidget):
    def __init__(self,window):
        super().__init__();self.setProperty('keepLocalAction',True);self.window=window;self.source=None;self.source_id=None;self.result=None;self.revision=0
        root=QVBoxLayout(self);self.note=QLabel('Analizá un sistema para medir su resultado.');self.note.setWordWrap(True);root.addWidget(self.note)
        controls=QWidget();form=QFormLayout(controls);self.form=form;form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.mode=QComboBox()
        for title,key in [('Leer frecuencias elegidas','points'),('Buscar cruces de nivel','level'),('Comprobar bandas y tolerancias','bands'),('Medir retardo por banda','delay')]:self.mode.addItem(title,key)
        form.addRow('Medición',self.mode)
        self.points=QLineEdit('0');self.points.setToolTip('Lista de frecuencias reales en rad/s o rad/muestra según el resultado. Admite pi, fracciones y potencias. Se evalúa la definición, sin interpolar el gráfico.');form.addRow('Frecuencias a leer',self.points)
        self.low=QLineEdit();self.high=QLineEdit();self.count=QLineEdit('2049');self.count.setToolTip('Puntos adicionales de búsqueda. También se conservan puntos del análisis y se exploran vecindades de polos cuando el modelo lo permite.')
        form.addRow('Desde (vacío = inicio del análisis)',self.low);form.addRow('Hasta (vacío = final del análisis)',self.high);form.addRow('Puntos dentro del intervalo',self.count)
        self.level_mode=QComboBox();self.level_mode.addItems(['dB respecto de |H| en una frecuencia','Módulo absoluto en amplitud']);self.level=QLineEdit('-3.010299956639812');self.reference=QLineEdit('0')
        form.addRow('Nivel buscado',self.level_mode);form.addRow('Valor del nivel',self.level);form.addRow('Frecuencia de referencia',self.reference)
        self.bands=Constraints();form.addRow(self.bands)
        self.calculate_button=QPushButton('Medir resultado');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate)
        from .result_state import ResultState
        self.state=ResultState([self.mode,self.points,self.low,self.high,self.count,self.level_mode,self.level,self.reference,self.bands],self.calculate_button)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);scroll.setMinimumHeight(190);scroll.setMaximumHeight(300);root.addWidget(scroll);root.addWidget(self.calculate_button);root.addWidget(self.state)
        from .active_stack import ActiveTabs
        self.tabs=ActiveTabs();root.addWidget(self.tabs,1);self.report=ReportView();self.tabs.addTab(report_panel(self.report),'Informe')
        page=QWidget();layout=QVBoxLayout(page);self.model=Rows(COLUMNS['points']);self.table=QTableView();self.table.setModel(self.model);self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents);layout.addWidget(self.table,1)
        self.export=QPushButton('Exportar medidas (CSV)…');self.export.clicked.connect(self.save);self.export.setEnabled(False);layout.addWidget(self.export);self.tabs.addTab(page,'Medidas')
        page=QWidget();layout=QVBoxLayout(page);self.figure=Figure();self.canvas=FigureCanvasQTAgg(self.figure);self.canvas._signallab_explicit_plot=True;self.toolbar=NavigationToolbar2QT(self.canvas,self);layout.addWidget(self.toolbar);layout.addWidget(self.canvas,1);self.tabs.addTab(page,'Gráfico de medidas')
        self.scale=QComboBox();self.scale.addItems(['Módulo lineal','Módulo en dB']);self.scale.currentIndexChanged.connect(self.draw);self.toolbar.addWidget(self.scale)
        self.table.selectionModel().currentRowChanged.connect(lambda *_:self.draw());self.mode.currentIndexChanged.connect(self.update_fields);self.level_mode.currentIndexChanged.connect(self.update_level);self.update_fields();self.set_source(None)
    def update_level(self,*_):
        relative=self.level_mode.currentIndex()==0;self.reference.setProperty('calculationInput',relative);self.form_visibility(self.reference,self.mode.currentData()=='level' and relative)
        if self.level.text() in ('-3.010299956639812','0.7071067811865476'):self.level.setText('-3.010299956639812' if relative else '0.7071067811865476')
    def form_visibility(self,widget,visible):
        self.form.setRowVisible(widget,visible)
    def update_fields(self,*_):
        mode=self.mode.currentData()
        for widget,active in ((self.points,mode=='points'),(self.low,mode in ('level','delay')),(self.high,mode in ('level','delay')),(self.count,mode!='points'),(self.level_mode,mode=='level'),(self.level,mode=='level'),(self.reference,mode=='level' and self.level_mode.currentIndex()==0),(self.bands,mode=='bands')):
            self.form_visibility(widget,active);widget.setProperty('calculationInput',active)
        self.state.refresh()
    def set_source(self,data,key=None):
        self.revision+=1;self.source=replace(data,system=deepcopy(data.system)) if data is not None else None;self.source_id=key;self.result=None;self.model.set_rows([]);self.export.setEnabled(False);self.calculate_button.setEnabled(data is not None);self.state.completed=None;self.state.refresh()
        self.report.setPlainText('Elegí una medición del último resultado. Editar el sistema no cambia esta definición hasta analizarlo nuevamente.');self.figure.clear();self.canvas.draw_idle()
        self.note.setText('Último análisis: '+format(data.omega[0],'.8g')+' a '+format(data.omega[-1],'.8g')+' '+data.units+'. Retardo en '+('muestras' if data.system.domain=='digital' else 'segundos')+'.' if data is not None else 'Se necesita una respuesta en frecuencia calculada, sin parámetros pendientes.')
    def calculate(self):
        if self.source is None or getattr(self.window,'_workers',[]):return
        try:
            mode=self.mode.currentData();options={}
            if mode=='points':
                from .systems_panel import parse_list
                values=parse_list(self.points.text())
                if np.any(values.imag):raise ValueError('Las frecuencias deben ser reales.')
                options['frequencies']=values.real
            else:
                options['count']=integer_field(self.count,minimum=3)
                low=real_field(self.low) if self.low.text().strip() else None;high=real_field(self.high) if self.high.text().strip() else None
                if mode=='bands':options['bands']=self.bands.read()
                elif mode=='delay':options['bands']=[('Retardo en banda',low,high,None,None)]
                else:options.update(low=low,high=high,level=real_field(self.level),relative=self.level_mode.currentIndex()==0,reference=real_field(self.reference) if self.level_mode.currentIndex()==0 else 0.)
            data=self.source;parent=self.source_id;revision=self.revision;inputs=self.state.snapshot()
            def accept(result):
                from .result_journal import snapshot
                readable=calc.summary(result);payload={**snapshot({k:v for k,v in result.items() if k!='plot'},self.window),'operation':'frequency_measurements','report':readable.plain_text()};self.window.publish(payload,title=readable.title,operation='Medidas de frecuencia',parents=[parent] if parent else [])
                if revision!=self.revision:return
                self.result=result;self.report.set_readable(readable);self.model.beginResetModel();self.model.columns=COLUMNS[mode];self.model.rows=result['rows'];self.model.endResetModel();self.export.setEnabled(True);self.state.accept(inputs);self.draw();self.tabs.setCurrentIndex(0)
            self.window._run_operation('Midiendo la definición del sistema…',lambda:calc.analyze(data,mode,**options),accept)
        except Exception as exc:QMessageBox.warning(self,'Medidas del sistema',str(exc))
    def draw(self,*_):
        if self.result is None:return
        from .signal_plot import configure_axis
        from .plot_inspection import system_curve
        from .theme_tokens import COLORS as C
        result=self.result;db=self.scale.currentIndex()==1;self.figure.clear();axes=self.figure.subplots(2,1,sharex=True)
        # Connect only within each measured band; never bridge transitions or gaps.
        for values in result['plot']:
            w=values['omega'];order=np.argsort(w);h=values['db'] if db else values['magnitude']
            line,=axes[0].plot(w[order],np.where(np.isfinite(h[order]),h[order],np.nan),'.' if result['mode']=='points' else '-',color=C['blue'])
            system_curve(line,self.source.system,'db' if db else 'magnitude',advance=self.source.advance-self.source.system.advance,phase_kind=self.source.phase_kind)
            line,=axes[1].plot(w[order],values['delay'][order],'.' if result['mode']=='points' else '-',color=C['blue']);system_curve(line,self.source.system,'delay',advance=self.source.advance-self.source.system.advance)
        def amplitude(value):return 20*np.log10(value) if db and value>0 else np.nan if db else value
        if result['mode']=='level':
            level=result['target_db'] if db else 10**(result['target_db']/20) if result['target_db']<6160 else np.nan
            axes[0].axhline(level,color=C['amber'],linestyle='--',label='Nivel buscado')._signallab_reference=True
            for row in result['rows']:
                for axis in axes:axis.axvline(row['frequency'],color=C['amber'],alpha=.45,linestyle=':')._signallab_reference=True
        if result['mode']=='bands':
            for row in result['rows']:
                axes[0].axvspan(row['low'],row['high'],color=C['blue'],alpha=.08)._signallab_reference=True
                for key in ('lower_limit','upper_limit'):
                    if row[key] is not None:axes[0].plot([row['low'],row['high']],[amplitude(row[key])]*2,color=C['amber'],linestyle='--',label='Límite de módulo').pop()._signallab_reference=True
                for key in ('minimum','maximum'):
                    if row[key] is not None:axes[0].plot(row[key+'_at'],amplitude(row[key]),'o',color=C['green'],markersize=4)[0]._signallab_reference=True
        selected=self.table.currentIndex().row()
        if 0<=selected<len(result['rows']):
            row=result['rows'][selected];frequencies=[row[k] for k in ('frequency','minimum_at','maximum_at','delay_min_at','delay_max_at') if row.get(k) is not None]
            for w in frequencies:
                for axis in axes:axis.axvline(w,color=C['purple'],alpha=.6,linestyle=':')._signallab_reference=True
        axes[0].set_ylabel('Módulo (dB)' if db else '|H|');axes[1].set_ylabel('Retardo ('+result['delay_units']+')');configure_axis(axes[1],units=result['units'],label='Frecuencia ('+result['units']+')')
        if not any(np.isfinite(p['delay']).any() for p in result['plot']):axes[1].text(.5,.5,'Retardo no definido en estos puntos',ha='center',transform=axes[1].transAxes)
        if db and not any(np.isfinite(p['db']).any() for p in result['plot']):axes[0].text(.5,.5,'Módulo cero: −∞ dB' if all(np.all(p['magnitude']==0) for p in result['plot']) else 'Módulo no disponible en estos puntos',ha='center',transform=axes[0].transAxes)
        if self.source.logarithmic and all(np.all(p['omega']>0) for p in result['plot']):axes[1].set_xscale('log')
        for axis in axes:axis.grid(alpha=.2)
        self.figure.set_layout_engine('constrained');self.canvas.draw_idle()
    def save(self):
        if self.result is None:return
        path,_=QFileDialog.getSaveFileName(self,'Exportar medidas de frecuencia','medidas_frecuencia.csv','CSV (*.csv)')
        if not path:return
        try:
            with atomic_text_file(path,newline='') as stream:
                from .result_journal import snapshot
                metadata=snapshot({k:v for k,v in self.result.items() if k not in ('plot','rows')},self.window)
                stream.write('# '+json.dumps(metadata,ensure_ascii=False,allow_nan=False)+'\n');columns=list(dict.fromkeys([key for key,_ in COLUMNS[self.result['mode']]]+[key for row in self.result['rows'] for key in row]));writer=csv.DictWriter(stream,fieldnames=columns,extrasaction='ignore');writer.writeheader();writer.writerows(self.result['rows'])
        except (OSError,ValueError) as exc:QMessageBox.warning(self,'Exportar medidas',str(exc))
