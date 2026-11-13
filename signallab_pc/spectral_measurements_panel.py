"""One measurement workspace for independent spectra, densities and FFT bins."""
import csv,json
from copy import deepcopy
import numpy as np
from PySide6.QtCore import Qt,Signal,QAbstractTableModel
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QLineEdit,QComboBox,QPushButton,QLabel,QScrollArea,QCheckBox,QTableWidget,QTableWidgetItem,QTableView,QHeaderView,QFileDialog,QMessageBox
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT
from matplotlib.widgets import SpanSelector
from . import spectral_measurements as calc
from .scalar_expression import real_value
from .numeric_input import real_field
from .result_state import ResultState
from .atomic_file import atomic_text_file


class BandEditor(QWidget):
    textChanged=Signal()
    def __init__(self):
        super().__init__();layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0)
        row=QHBoxLayout();layout.addLayout(row);add=QPushButton('+ Banda');remove=QPushButton('Quitar banda');row.addWidget(add);row.addWidget(remove);row.addStretch()
        self.table=QTableWidget(0,3);self.table.setHorizontalHeaderLabels(['Nombre','Desde','Hasta']);self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);self.table.setMaximumHeight(220);layout.addWidget(self.table)
        note=QLabel('Un extremo vacío usa el límite disponible. Se admiten pi, fracciones y notación científica. En bins, el extremo derecho no se incluye.');note.setWordWrap(True);layout.addWidget(note)
        self.table.itemChanged.connect(lambda *_:self.textChanged.emit());add.clicked.connect(self.add);remove.clicked.connect(self.remove);self.add()
    def add(self,*_):
        self.table.blockSignals(True);row=self.table.rowCount();self.table.insertRow(row)
        for column,text in enumerate(('Banda '+str(row+1),'','')):self.table.setItem(row,column,QTableWidgetItem(text))
        self.table.setCurrentCell(row,1);self.table.blockSignals(False);self.textChanged.emit()
    def remove(self):
        row=self.table.currentRow()
        if row>=0:self.table.removeRow(row);self.textChanged.emit()
    def text(self):return json.dumps([[self.table.item(r,c).text() if self.table.item(r,c) is not None else '' for c in range(3)] for r in range(self.table.rowCount())],ensure_ascii=False)
    def read(self):
        rows=json.loads(self.text());result=[]
        for index,(name,low,high) in enumerate(rows):
            try:result.append((name,real_value(low.replace('π','pi')) if low.strip() else None,real_value(high.replace('π','pi')) if high.strip() else None))
            except Exception as exc:raise ValueError('Banda '+str(index+1)+': indicá extremos reales finitos. '+str(exc)) from exc
        if not result:raise ValueError('Agregá al menos una banda.')
        return result
    def select_range(self,low,high):
        row=self.table.currentRow()
        if row<0:self.add();row=self.table.currentRow()
        self.table.item(row,1).setText(format(low,'.16g'));self.table.item(row,2).setText(format(high,'.16g'))


class Rows(QAbstractTableModel):
    def __init__(self,columns):super().__init__();self.columns=columns;self.rows=[]
    def set_rows(self,rows):self.beginResetModel();self.rows=rows;self.endResetModel()
    def rowCount(self,parent=None):return 0 if parent is not None and parent.isValid() else len(self.rows)
    def columnCount(self,parent=None):return 0 if parent is not None and parent.isValid() else len(self.columns)
    def headerData(self,index,orientation,role=Qt.ItemDataRole.DisplayRole):
        if role==Qt.ItemDataRole.DisplayRole:return self.columns[index][1] if orientation==Qt.Orientation.Horizontal else str(index+1)
    def data(self,index,role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role not in (Qt.ItemDataRole.DisplayRole,Qt.ItemDataRole.ToolTipRole):return None
        value=self.rows[index.row()].get(self.columns[index.column()][0]);return 'No definido' if value is None else format(value,'.17g' if role==Qt.ItemDataRole.ToolTipRole else '.10g') if isinstance(value,float) else str(value)


class SpectralMeasurePanel(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window;self.calculation_title='Medir un espectro';self.result=None;self._source=None;self._span=None;self._probe_restore=False
        from .toolbox import LocalInput,ResultView
        root=QHBoxLayout(self);controls=QWidget();left=QVBoxLayout(controls)
        self.calculate_button=QPushButton('Medir espectro');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);left.addWidget(self.calculate_button)
        self.source=LocalInput('Espectro o densidad','frequency');self.source.accepted_kinds={'spectrum','density','frequency_values','frequency_response','dft_bins','spectral_lines','harmonics'};self.source.cross_domain_kinds={'dft_bins','harmonics'};self.source.frequency_units.addItem('Hz');self.source.bind_project(window);left.addWidget(self.source)
        form=QFormLayout();form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows);left.addLayout(form)
        self.interpretation=QComboBox()
        for title,key in [('Automática según el resultado','auto'),('Espectro complejo X','spectrum'),('Densidad de energía |X|²','energy_density'),('PSD Sx: angular /2π o en Hz directa','power_density'),('Potencia por unidad de eje: integral directa','density_per_unit'),('Área de |H|² (sin Parseval)','area')]:self.interpretation.addItem(title,key)
        form.addRow('Qué representan los valores',self.interpretation)
        self.units=QLabel('Bandas en la unidad del eje cargado.');self.units.setWordWrap(True);left.addWidget(self.units)
        self.bands=BandEditor();left.addWidget(self.bands)
        self.level=QLineEdit('-40');self.prominence=QLineEdit('1');form.addRow('Picos: nivel mínimo respecto del máximo (dB)',self.level);form.addRow('Prominencia mínima (% del máximo)',self.prominence)
        self.interpolate=QCheckBox('Estimar frecuencia del pico entre bins');form.addRow(self.interpolate)
        note=QLabel('Las fórmulas se evalúan en la rejilla indicada. Las bandas no extrapolan ese intervalo. Una respuesta H se mide como área, sin presentarla como energía de una señal.');note.setWordWrap(True);left.addWidget(note);left.addStretch()
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);root.addWidget(scroll,1)
        results=QWidget();out=QVBoxLayout(results);root.addWidget(results,2);self.state=ResultState([self.interpretation,self.bands,self.level,self.prominence,self.interpolate],self.calculate_button,[self.source]);out.addWidget(self.state)
        self.view=ResultView();out.addWidget(self.view,1);self.tabs=self.view.views;self.report=self.view.text
        self.band_model=Rows([('name','Banda'),('low','Desde'),('high','Hasta'),('value_text','Medida'),('percent','% disponible')]);self.peak_model=Rows([('frequency','Coordenada medida'),('estimated_frequency','Estimación sub-bin'),('input_level','Módulo de entrada'),('level','Peso / densidad'),('relative_db','dB relativos'),('prominence_percent','Prominencia %'),('plateau','Meseta (puntos)'),('kind','Tipo')])
        for title,model,key in [('Bandas',self.band_model,'bands'),('Picos',self.peak_model,'peaks')]:
            page=QWidget();layout=QVBoxLayout(page);table=QTableView();table.setModel(model);table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents);table.horizontalHeader().setStretchLastSection(True);layout.addWidget(table,1)
            button=QPushButton('Exportar '+title.lower()+' (CSV)…');button.clicked.connect(lambda checked=False,k=key:self.export_table(k));layout.addWidget(button);self.tabs.addTab(page,title)
        self.cumulative=ResultView();self.cumulative.plot_mode.hide();self.cdf_index=self.tabs.addTab(self.cumulative,'Acumulada')
        page=QWidget();plot=QVBoxLayout(page);self.plot_index=self.tabs.addTab(page,'Espectro y bandas')
        self.pick=QPushButton('Seleccionar banda con el mouse');self.pick.setCheckable(True);self.pick.setEnabled(False);self.pick.setToolTip('Arrastrá sobre el gráfico para llenar la fila elegida. Después recalculá.');self.pick.toggled.connect(self.pick_mode)
        plot_controls=QWidget();bar=QHBoxLayout(plot_controls);bar.addWidget(self.pick);bar.addStretch()
        self.figure=Figure();self.canvas=FigureCanvasQTAgg(self.figure);self.toolbar=NavigationToolbar2QT(self.canvas,self);self.canvas._signallab_plot_controls=plot_controls;self.canvas._signallab_explicit_plot=True;plot.addWidget(plot_controls);plot.addWidget(self.toolbar);plot.addWidget(self.canvas,1)
        for action in self.toolbar.actions():action.triggered.connect(self.navigation_changed)
        def units_changed(*_):
            units=self.source.loaded.units if self.source.mode.currentIndex()==2 and self.source.loaded is not None else self.source.frequency_units.currentText()
            self.units.setText('Bandas en '+units+'.')
        self.source.sourceChanged.connect(units_changed);self.source.mode.currentIndexChanged.connect(units_changed);self.source.frequency_units.currentIndexChanged.connect(units_changed);units_changed()

    def calculate(self):
        try:
            original=self.source.read();source=original.copy_with(metadata=deepcopy(original.metadata));parents=[self.source.reference_id] if self.source.reference_id else []
            bands=self.bands.read();options=dict(interpretation=self.interpretation.currentData(),level_db=real_field(self.level,maximum=0),prominence_percent=real_field(self.prominence,minimum=0,maximum=100),interpolate=self.interpolate.isChecked());snapshot=self.state.snapshot()
            def accept(data):
                self.result=data;self._source=source;self.units.setText('Bandas en '+data['units']+' · '+data['quantity'])
                cdf_key=self.window.publish(data['cumulative'],operation='Fracción espectral acumulada',parents=parents) if data['cumulative'] is not None else None
                payload=dict(report=data['report'],bands=data['bands'],peaks=data['peaks'],moments=data['moments'],rule=data['rule'],total=data['total'],units=data['units'],quantity=data['quantity'])
                record=self.window.publish(payload,title=self.calculation_title,operation='Medir espectro',parents=parents+([cdf_key] if cdf_key else []))
                self.view.show_result(payload);self.view.result_ids=[record];self.report.setPlainText(data['report'])
                rows=[dict(row,value_text=row['measure']['text'],percent=None if row['fraction'] is None else 100*row['fraction']) for row in data['bands']];self.band_model.set_rows(rows);self.peak_model.set_rows(data['peaks'])
                self.tabs.setTabVisible(self.cdf_index,data['cumulative'] is not None)
                if data['cumulative'] is not None:
                    self.cumulative.show_result(data['cumulative']);self.cumulative.result_ids=[cdf_key]
                else:self.cumulative.clear_result('La medida es nula; una fracción acumulada no está definida.')
                self.draw(options['interpretation']);self.state.accept(snapshot)
            self.window._run_operation('Midiendo bandas, distribución y picos…',lambda:calc.analyze(source,bands,**options),accept)
        except Exception as exc:QMessageBox.warning(self,'Medir espectro',str(exc))

    def draw(self,interpretation):
        if self._span is not None:self._span.disconnect_events();self._span=None
        self.pick.setChecked(False);self.pick.setEnabled(True);data=self.result;self.figure.clear();axis=self.figure.add_subplot(111);logs=calc.logarithmic_magnitude(self._source.values)
        if data['interpretation'] not in ('energy_density','power_density','density_per_unit'):logs=2*logs
        finite=logs[np.isfinite(logs)];peak=float(np.max(finite)) if finite.size else 0.
        y=np.maximum(10/np.log(10)*(logs-peak),-160)
        from .visible_curve import VisibleCurve,VisibleStem
        self.curve=(VisibleStem(axis,self._source.axis,y,bottom=-160) if data['bins'] else VisibleCurve(axis,self._source.axis,y))
        for row in self.result['bands']:
            patch=axis.axvspan(row['low'],row['high'],alpha=.15);patch._signallab_reference=True
        from .signal_plot import configure_axis
        configure_axis(axis,discrete_index=data['units'] in ('k','bin k'),units=data['units'],label='Índice k' if data['units'] in ('k','bin k') else 'Frecuencia ('+data['units']+')',index_symbol='k');axis.set_ylabel('Peso relativo visible (dB; piso −160)');axis.set_ylim(-162,4);axis.set_xlim(*data['limits']);axis.grid(alpha=.15)
        self._span=SpanSelector(axis,self.select_range,'horizontal',useblit=False,props=dict(facecolor='#efc38d',alpha=.25),button=1);self._span.set_active(False);self.canvas.draw_idle()

    def pick_mode(self,enabled):
        if self._span is None:return
        if enabled and self.toolbar.mode:self.pick.setChecked(False);return
        probe=getattr(self.canvas,'_signallab_probe',None)
        if probe is not None:
            if getattr(probe,'_band_peer',None) is not self:probe.action.toggled.connect(self.probe_mode);probe._band_peer=self
            if enabled:self._probe_restore=probe.action.isChecked();probe.action.setChecked(False)
            elif self._probe_restore:probe.action.setChecked(True);self._probe_restore=False
        self._span.set_active(enabled)

    def probe_mode(self,enabled):
        if enabled and self.pick.isChecked():self._probe_restore=False;self.pick.setChecked(False)

    def navigation_changed(self,*_):
        if self.toolbar.mode and self.pick.isChecked():self.pick.setChecked(False)

    def select_range(self,low,high):
        if self.result is None or self.toolbar.mode:return
        low=max(self.result['limits'][0],float(low));high=min(self.result['limits'][1],float(high))
        if low<high:self.bands.select_range(low,high)

    def export_table(self,kind):
        if self.result is None:return
        path,_=QFileDialog.getSaveFileName(self,'Exportar '+kind,kind+'.csv','CSV (*.csv)')
        if not path:return
        try:
            model=self.band_model if kind=='bands' else self.peak_model;rows=model.rows;columns=[key for key,_ in model.columns]
            with atomic_text_file(path,newline='') as stream:
                stream.write('# '+json.dumps(dict(units=self.result['units'],quantity=self.result['quantity'],rule=self.result['rule']),ensure_ascii=False)+'\n');writer=csv.DictWriter(stream,fieldnames=columns,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
        except Exception as exc:QMessageBox.warning(self,'Exportar medidas',str(exc))


class StftBandPowerView(QWidget):
    def __init__(self,owner):
        super().__init__();self.owner=owner;self.data=None;self.parents=[];self.outputs=[];layout=QVBoxLayout(self)
        self.units=QComboBox();self.units.addItems(['Bandas en rad/muestra','Bandas en rad/s']);layout.addWidget(self.units);self.bands=BandEditor();layout.addWidget(self.bands)
        self.button=QPushButton('Calcular potencia por ventana');self.button.setObjectName('primary');self.button.clicked.connect(self.calculate);layout.addWidget(self.button)
        self.state=ResultState([self.bands,self.units],self.button);layout.addWidget(self.state)
        self.selector=QComboBox();self.selector.currentIndexChanged.connect(self.display);layout.addWidget(self.selector)
        from .toolbox import ResultView
        self.view=ResultView();layout.addWidget(self.view,1);self.note=QLabel('Integra la densidad de cada ventana. El relleno en los extremos puede reducir su potencia respecto de las ventanas completas.');self.note.setWordWrap(True);layout.addWidget(self.note)
    def set_data(self,data,parents):
        self.data=data;self.parents=list(parents);self.outputs=[];self.view.clear_result();self.selector.clear();self.state.completed=None
        continuous=data['metadata']['input_domain']=='continuous';self.units.setCurrentIndex(1 if continuous else 0);self.units.setEnabled(not continuous and 'sample_rate_hz' in data['metadata']['input_clock']);self.state.refresh()
    def calculate(self):
        if self.data is None:return
        try:
            bands=self.bands.read();data=self.data;physical=self.units.currentIndex()==1;snapshot=self.state.snapshot()
            def accept(outputs):
                self.outputs=outputs;self.keys=[self.owner.publish(value,operation='Potencia STFT por banda',parents=self.parents) for value in outputs]
                self.selector.blockSignals(True);self.selector.clear();self.selector.addItems([v.name for v in outputs]);self.selector.blockSignals(False);self.display();self.state.accept(snapshot)
            self.owner._run_operation('Integrando potencia por banda en las ventanas…',lambda:calc.stft_band_series(data,bands,physical),accept)
        except Exception as exc:QMessageBox.warning(self,'Potencia por banda',str(exc))
    def display(self,*_):
        index=self.selector.currentIndex()
        if 0<=index<len(self.outputs):self.view.show_result(self.outputs[index]);self.view.result_ids=[self.keys[index]]
