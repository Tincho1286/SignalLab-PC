"""Finite-record studies within the existing energy and RMS tool."""
import csv
from copy import deepcopy
from PySide6.QtWidgets import QWidget,QVBoxLayout,QFormLayout,QLineEdit,QComboBox,QPushButton,QLabel,QScrollArea,QSplitter,QTableView,QHeaderView,QFileDialog,QMessageBox,QGridLayout,QBoxLayout
from PySide6.QtCore import Qt
from . import record_measurements as calc
from .numeric_input import real_field
from .result_state import ResultState
from .atomic_file import atomic_text_file
from .spectral_measurements_panel import Rows


class RecordMeasurePanel(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window;self.calculation_title='Medir un registro';self.result=None;self.signals={};self.ids={};self._domain_index=0;self._limits=[('',''),('','')]
        from .toolbox import LocalInput,ResultView
        from .choice_buttons import ChoiceButtons
        root=QVBoxLayout(self);root.setContentsMargins(0,0,0,0);split=QSplitter(Qt.Orientation.Horizontal);split.setChildrenCollapsible(False);root.addWidget(split,1)
        controls=QWidget();left=QVBoxLayout(controls);self.calculate_button=QPushButton('Medir registro');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);left.addWidget(self.calculate_button)
        self.domain=QComboBox();self.domain.addItems(['Discreta','Continua']);left.addWidget(ChoiceButtons(self.domain))
        self.discrete_source=LocalInput('Entrada x[n]','discrete');self.continuous_source=LocalInput('Entrada x(t)','continuous')
        for source in (self.discrete_source,self.continuous_source):
            source.bind_project(window);left.addWidget(source)
            selector=source.entry_modes;row=selector.layout()
            while row.count():row.takeAt(0)
            grid=QGridLayout();grid.setContentsMargins(0,0,0,0);grid.setSpacing(4);row.addLayout(grid)
            for i,button in enumerate(selector.buttons):grid.addWidget(button,i//2,i%2)
            source.interval.layout().setDirection(QBoxLayout.Direction.TopToBottom)
        self.continuous_source.hide();form=QFormLayout();form.setProperty('stackFields',True);form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows);left.addLayout(form)
        self.low=QLineEdit();self.high=QLineEdit();self.low.setPlaceholderText('Vacío: primer punto');self.high.setPlaceholderText('Vacío: último punto')
        form.addRow('Desde · índice n',self.low);form.addRow('Hasta · índice n',self.high)
        self.fraction=QLineEdit('90');form.addRow('Energía del intervalo central (%)',self.fraction)
        self.component=QComboBox()
        for title,key in [('Módulo','magnitude'),('Parte real','real'),('Parte imaginaria','imag')]:self.component.addItem(title,key)
        form.addRow('Componente para cruces de nivel',self.component);self.level=QLineEdit('0.5');form.addRow('Nivel de amplitud',self.level)
        self.note=QLabel();self.note.setWordWrap(True);left.addWidget(self.note);left.addStretch()
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);scroll.setMinimumWidth(250);split.addWidget(scroll)
        results=QWidget();out=QVBoxLayout(results);split.addWidget(results);split.setStretchFactor(1,1);split.setSizes([350,760])
        self.state=ResultState([self.domain,self.low,self.high,self.fraction,self.level,self.component],self.calculate_button,[self.discrete_source,self.continuous_source]);out.addWidget(self.state)
        self.choice=QComboBox();self.choice.setAccessibleName('Resultado del estudio de registro');self.choice.setEnabled(False);out.addWidget(self.choice)
        self.view=ResultView();out.addWidget(self.view,1);self.report=self.view.text
        page=QWidget();layout=QVBoxLayout(page);self.events=Rows([('kind','Evento'),('start','Desde'),('end','Hasta'),('span','Separación')]);self.table=QTableView();self.table.setModel(self.events);self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents);self.table.horizontalHeader().setStretchLastSection(True);layout.addWidget(self.table,1)
        self.export_events=QPushButton('Exportar cruces y contactos (CSV)…');self.export_events.setEnabled(False);self.export_events.clicked.connect(self.export_table);layout.addWidget(self.export_events);self.events_index=self.view.views.addTab(page,'Cruces y contactos');self.view.views.setTabVisible(self.events_index,False)
        self.choice.currentIndexChanged.connect(self.show_choice);self.domain.currentIndexChanged.connect(lambda index:self.change_domain(form,index));self.change_domain(form,0)
        self.discrete_source.sourceChanged.connect(lambda:self.loaded(0));self.continuous_source.sourceChanged.connect(lambda:self.loaded(1))

    @property
    def source(self):return self.discrete_source if self.domain.currentIndex()==0 else self.continuous_source

    def loaded(self,index):
        source=self.discrete_source if index==0 else self.continuous_source
        if source.mode.currentIndex()==2 and source.loaded is not None:self.domain.setCurrentIndex(index)

    def change_domain(self,form,index):
        self._limits[self._domain_index]=(self.low.text(),self.high.text());self._domain_index=index
        self.low.setText(self._limits[index][0]);self.high.setText(self._limits[index][1]);self.discrete_source.setVisible(index==0);self.continuous_source.setVisible(index==1)
        for field,label in [(self.low,'Desde'),(self.high,'Hasta')]:form.labelForField(field).setText(label+(' · índice n' if index==0 else ' · tiempo en la unidad de entrada'))
        self.note.setText('Los límites incluyen ambos índices. Energía = suma |x[n]|²; potencia = energía / cantidad de muestras. Los cruces se ubican en muestras, sin interpolar.' if index==0 else 'Se usan los puntos guardados incluidos en el intervalo, con al menos dos puntos. Energía y media integran el modelo lineal entre ellos; no se reevalúa la fórmula original. El informe muestra los límites realmente utilizados.')

    def calculate(self):
        try:
            original=self.source.read();source=original.copy_with(metadata=deepcopy(original.metadata));parents=[self.source.reference_id] if self.source.reference_id else []
            options=dict(low=self.low.text().strip() or None,high=self.high.text().strip() or None,fraction=real_field(self.fraction,minimum=0,maximum=100)/100,level=real_field(self.level),component=self.component.currentData());snapshot=self.state.snapshot()
            self.window._run_operation('Midiendo intervalo, energía y cruces…',lambda:calc.analyze(source,**options),lambda data:self.accept(data,parents,snapshot))
        except Exception as exc:QMessageBox.warning(self,'Medir un registro',str(exc))

    def accept(self,data,parents,snapshot):
        self.result=data;previous=self.choice.currentData();self.signals={key:data[key] for key in ('selected','dc','ac','cumulative') if data[key] is not None}
        self.ids={key:self.window.publish(value,operation='Medidas de registro: '+value.name,parents=parents) for key,value in self.signals.items()}
        report=calc.summary(data);payload={key:data[key] for key in ('mean','measures','distribution','events','level','component','notice','discrete','held','interval','samples','units','scope','duration')};payload.update(report=report.plain_text(),calculated_data={key:{'result_id':value} for key,value in self.ids.items()})
        self.window.publish(payload,title=report.title,operation='Medir un registro',parents=parents+list(self.ids.values()))
        journal=getattr(self.window,'_result_journal',None)
        if journal is not None:journal.reported(data,outputs_registered=True)
        labels={'selected':'Registro seleccionado','dc':'Componente continua (media)','ac':'Componente alterna','cumulative':'Fracción de energía acumulada en los puntos'}
        self.choice.blockSignals(True);self.choice.clear()
        for key in self.signals:self.choice.addItem(labels[key],key)
        self.choice.setCurrentIndex(max(0,self.choice.findData(previous)));self.choice.blockSignals(False);self.choice.setEnabled(True)
        self.events.set_rows(data['events']);self.export_events.setEnabled(True);self.view.views.setTabVisible(self.events_index,True);self.show_choice();self.state.accept(snapshot)

    def show_choice(self,*_):
        if self.result is None:return
        key=self.choice.currentData();self.view.show_result(self.signals[key]);self.view.result_ids=[self.ids[key]];self.report.set_readable(calc.summary(self.result));self.view.views.setTabVisible(self.events_index,True)

    def export_table(self):
        if self.result is None:return
        path,_=QFileDialog.getSaveFileName(self,'Exportar cruces y contactos','cruces.csv','CSV (*.csv)')
        if not path:return
        try:
            with atomic_text_file(path,newline='') as stream:
                import json
                stream.write('# '+json.dumps({key:self.result[key] for key in ('units','level','component','interval','discrete')},ensure_ascii=False)+'\n');writer=csv.DictWriter(stream,fieldnames=['kind','start','end','span']);writer.writeheader();writer.writerows(self.result['events'])
        except Exception as exc:QMessageBox.warning(self,'Exportar medidas',str(exc))
