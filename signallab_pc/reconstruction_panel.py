"""Common-clock reconstruction comparison and result-side kernel inspection."""
import csv,json
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QFormLayout,QComboBox,QLineEdit,QPushButton,QLabel,QCheckBox,QScrollArea,QSplitter,QTableView,QHeaderView,QFileDialog,QMessageBox,QGridLayout,QBoxLayout
from .toolbox import LocalInput,ResultView
from . import reconstruction_studies as calc
from .expression_editor import ExpressionEditor
from .result_state import ResultState
from .numeric_input import real_field,integer_field
from .atomic_file import atomic_text_file
from .spectral_measurements_panel import Rows


class ReconstructionView(ResultView):
    def __init__(self):self.study=None;self.include_samples=False;super().__init__()
    def draw_signal(self,*_):
        super().draw_signal()
        if self.study is None or not self.include_samples or self.result is None or len(self.figure.axes)!=2:return
        from .signal_plot import plot_samples
        source=self.study['source'];indices=np.unique(np.linspace(0,len(source.values)-1,min(1000,len(source.values))).astype(int));values=source.values[indices];times=self.study['source_start']+indices/self.study['source_rate'];polar=self.plot_mode.currentIndex()==0
        parts=(abs(values),np.where(abs(values)>0,np.angle(values),np.nan)) if polar else (values.real,values.imag)
        for axis,y in zip(self.figure.axes,parts):
            plot_samples(axis,times,y,discrete=True,label='Muestras originales'+(' · vista reducida' if len(indices)<len(source.values) else ''),color='#edc27d');axis.legend(loc='upper left',bbox_to_anchor=(1.01,1))
        self.figure.tight_layout();self.canvas.draw_idle()


class ReconstructionPanel(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window;self.calculation_title='Reconstruir una señal';self.run=None;self.record_id=None;self.signals={};self.ids={};self.inspection=None
        root=QVBoxLayout(self);root.setContentsMargins(0,0,0,0);split=QSplitter(Qt.Orientation.Horizontal);split.setChildrenCollapsible(False);root.addWidget(split,1)
        controls=QWidget();left=QVBoxLayout(controls);self.calculate_button=QPushButton('Comparar reconstrucciones');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);left.addWidget(self.calculate_button)
        self.source=LocalInput('Muestras x[n]','discrete');self.source.bind_project(window);left.addWidget(self.source)
        self.source.interval.layout().setDirection(QBoxLayout.Direction.TopToBottom)
        form=QFormLayout();form.setProperty('stackFields',True);form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows);left.addLayout(form)
        self.rate=QLineEdit('100');self.start=QLineEdit('0');self.factor=QLineEdit('16');self.before=QLineEdit('0');self.after=QLineEdit('0')
        for label,field in [('Fs de entrada (muestras/s)',self.rate),('Tiempo de la primera muestra (s)',self.start),('Subdivisiones por período',self.factor),('Períodos antes del registro',self.before),('Períodos después del registro',self.after)]:form.addRow(label,field)
        self.override=QCheckBox('Reinterpretar el reloj con los valores del formulario');form.addRow(self.override)
        from .input_clock import bind_clock
        form.addRow(bind_clock(self.source,self.rate,self.start,self.override))
        self.use_reference=QCheckBox('Comparar con una referencia r(t)');form.addRow(self.use_reference);self.reference=ExpressionEditor('');form.addRow('Referencia r(t)',self.reference)
        def reference_enabled(enabled):form.setRowVisible(self.reference,enabled);self.reference.setProperty('calculationInput',enabled)
        self.use_reference.toggled.connect(reference_enabled);reference_enabled(False)
        note=QLabel('La extensión nula se aplica a la secuencia. ZOH retiene cada muestra un período; lineal usa triángulos y SINC tiene colas infinitas. La ventana elige qué parte se dibuja.');note.setWordWrap(True);left.addWidget(note);left.addStretch()
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);scroll.setMinimumWidth(250);split.addWidget(scroll)
        results=QWidget();out=QVBoxLayout(results);split.addWidget(results);split.setSizes([350,760]);split.setStretchFactor(1,1)
        self.state=ResultState([self.rate,self.start,self.factor,self.before,self.after,self.override,self.use_reference,self.reference],self.calculate_button,[self.source]);out.addWidget(self.state)
        self.choice=QComboBox();self.choice.setAccessibleName('Curvas de reconstrucción');self.choice.setEnabled(False);out.addWidget(self.choice)
        self.view=ReconstructionView();out.addWidget(self.view,1);self.report=self.view.text
        self.nodes=Rows([('label','Método'),('maximum','Máximo desvío nodal'),('rms','RMS nodal'),('error','Observación')]);self.node_index=self.add_table('Nudos originales',self.nodes,self.export_nodes)
        page=QWidget();layout=QVBoxLayout(page);self.inspect_index=self.view.views.addTab(page,'Aportes por muestra');self.view.views.setTabVisible(self.inspect_index,False)
        fields=QFormLayout();fields.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows);layout.addLayout(fields);self.method=QComboBox()
        for key,label in calc.METHODS.items():self.method.addItem(label,key)
        self.time=QLineEdit('0');fields.addRow('Método',self.method);fields.addRow('Instante t (s)',self.time)
        self.inspect_button=QPushButton('Evaluar este instante');self.inspect_button.setProperty('keepLocalAction',True);self.inspect_button.clicked.connect(self.inspect);self.inspect_button.setEnabled(False);layout.addWidget(self.inspect_button)
        self.inspection_state=ResultState([self.time,self.method],self.inspect_button);layout.addWidget(self.inspection_state)
        self.inspection_view=ResultView();layout.addWidget(self.inspection_view,1);self.parts=Rows([('index','Índice n original'),('time','Tiempo de muestra (s)'),('weight','Peso del núcleo'),('sample','Muestra'),('contribution','Aporte')]);self.parts_index=self.add_table('Aportes',self.parts,self.export_parts,target=self.inspection_view)
        self.choice.currentIndexChanged.connect(self.show_choice);self.method.currentIndexChanged.connect(self.method_changed)

    def add_table(self,title,model,export,target=None):
        view=target or self.view;page=QWidget();layout=QVBoxLayout(page);table=QTableView();table.setModel(model);table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents);table.horizontalHeader().setStretchLastSection(True);layout.addWidget(table,1)
        button=QPushButton('Exportar '+title.lower()+' (CSV)…');button.clicked.connect(export);layout.addWidget(button);index=view.views.addTab(page,title);view.views.setTabVisible(index,False);return index

    def calculate(self):
        try:
            source=self.source.read();parents=[self.source.reference_id] if self.source.reference_id else [];override=self.override.isChecked()
            rate=real_field(self.rate) if override or source.metadata.get('sample_rate_hz') is None else None;start=real_field(self.start) if override or source.metadata.get('time_start_s') is None else None
            options=dict(factor=integer_field(self.factor),before=integer_field(self.before),after=integer_field(self.after),override_clock=override,reference=self.reference.text() if self.use_reference.isChecked() else None);snapshot=self.state.snapshot()
            self.window._run_operation('Comparando reconstrucciones…',lambda:calc.analyze(source,rate,start,**options),lambda data:self.accept(data,parents,snapshot))
        except Exception as exc:QMessageBox.warning(self,'Reconstruir una señal',str(exc))

    def accept(self,data,parents,snapshot):
        self.run=data;self.signals={('models',key):value for key,value in data['signals'].items()}
        if data['reference'] is not None:self.signals['reference',None]=data['reference']
        for key,error in data['errors'].items():
            if error['signal'] is not None:self.signals['errors',key]=error['signal']
        self.ids={key:self.window.publish(value,operation='Reconstrucción: '+value.name,parents=parents) for key,value in self.signals.items()};summary=calc.summary(data);metrics={key:{k:v for k,v in value.items() if k!='signal'} for key,value in data['errors'].items()}
        self.record_id=self.window.publish(dict(report=summary.plain_text(),methods=data['methods'],errors=metrics,reference_notice=data['reference_notice'],interval=data['interval'],calculated_data={str(key):{'result_id':value} for key,value in self.ids.items()}),title=summary.title,operation='Comparar reconstrucciones',parents=parents+list(self.ids.values()))
        journal=getattr(self.window,'_result_journal',None)
        if journal is not None:journal.reported(data,outputs_registered=True)
        self.choice.blockSignals(True);self.choice.clear();self.choice.addItem('Comparar métodos y referencia',('all',None))
        for key,value in self.signals.items():self.choice.addItem(value.name,key)
        self.choice.blockSignals(False);self.choice.setEnabled(True)
        self.nodes.set_rows([dict(label=row['label'],maximum=row['nodes']['maximum']['text'] if row['nodes'] else None,rms=row['nodes']['rms']['text'] if row['nodes'] else None,error=row['error'] or 'Nudos conservados por construcción') for row in data['methods']])
        self.time.setText(format(data['source_start'],'.17g'));self.inspection=None;self.parts.set_rows([]);self.inspection_view.clear_result('Elegí un instante y evaluá sus pesos sobre el último cálculo.');self.inspection_state.completed=None;self.inspection_state.refresh();self.inspect_button.setEnabled(True)
        self.view.study=data;self.show_choice();self.state.accept(snapshot)

    def show_choice(self,*_):
        if self.run is None:return
        category,method=self.choice.currentData();keys=[key for key in self.signals if key[0] in ('models','reference')] if category=='all' else [(category,method)]
        values=tuple(self.signals[key] for key in keys);self.view.include_samples=category in ('all','models');self.view.show_result(values if len(values)>1 else values[0]);self.view.result_ids=[self.ids[key] for key in keys];self.report.set_readable(calc.summary(self.run));self.view.views.setTabVisible(self.node_index,True);self.view.views.setTabVisible(self.inspect_index,True)
        if method is not None:
            self.method.blockSignals(True);self.method.setCurrentIndex(self.method.findData(method));self.method.blockSignals(False);self.inspection_state.refresh()

    def method_changed(self,*_):
        if self.run is None:return
        category,selected=self.choice.currentData()
        if selected is not None:
            target=(category,self.method.currentData());index=next((i for i in range(self.choice.count()) if self.choice.itemData(i)==target),-1)
            if index>=0:self.choice.setCurrentIndex(index)

    def inspect(self):
        if self.run is None:return
        try:
            time=real_field(self.time);method=self.method.currentData();run=self.run;parent=self.record_id;snapshot=self.inspection_state.snapshot()
            def accept(data):
                from .result_journal import snapshot as result_snapshot
                self.inspection=data;values=[data['weights']]+([data['contributions']] if data['contributions'] is not None else []);ids=[self.window.publish(value,operation='Aportes de reconstrucción',parents=[parent]) for value in values];summary=calc.inspection_summary(data)
                self.window.publish(dict(report=summary.plain_text(),rows=result_snapshot(data['rows'],self.window),method=data['method'],time=data['time'],calculated_data=[{'result_id':key} for key in ids]),title=summary.title,operation='Evaluar núcleo de reconstrucción',parents=[parent,*ids]);journal=getattr(self.window,'_result_journal',None)
                if journal is not None:journal.reported(data,outputs_registered=True)
                self.inspection_view.show_result(tuple(values) if len(values)>1 else values[0]);self.inspection_view.result_ids=ids;self.inspection_view.text.set_readable(summary);self.parts.set_rows(data['rows']);self.inspection_view.views.setTabVisible(self.parts_index,True);self.inspection_state.accept(snapshot)
            self.window._run_operation('Evaluando aportes en el instante elegido…',lambda:calc.inspect(run,time,method),accept)
        except Exception as exc:QMessageBox.warning(self,'Inspeccionar reconstrucción',str(exc))

    def export_nodes(self):self.export_rows('nudos',self.nodes.rows,['label','maximum','rms','error'])
    def export_parts(self):
        if self.inspection is not None:self.export_rows('aportes',self.parts.rows,['index','time','weight','sample','contribution'])
    def export_rows(self,name,rows,columns):
        if self.run is None:return
        path,_=QFileDialog.getSaveFileName(self,'Exportar '+name,name+'.csv','CSV (*.csv)')
        if not path:return
        try:
            with atomic_text_file(path,newline='') as stream:
                metadata=dict(source_rate_hz=self.run['source_rate'],source_time_start_s=self.run['source_start'],interval=self.run['interval'])
                if name=='aportes':metadata.update(method=self.inspection['method'],query_time_s=self.inspection['time'])
                stream.write('# '+json.dumps(metadata,ensure_ascii=False)+'\n');writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader();writer.writerows(rows)
        except Exception as exc:QMessageBox.warning(self,'Exportar reconstrucción',str(exc))
