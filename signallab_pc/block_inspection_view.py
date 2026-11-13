"""A block navigator shares the standard report, data and reuse actions."""
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QSpinBox,QComboBox,QLabel,QPushButton,QAbstractSpinBox
from . import block_inspection as math


class BlockInspector(QWidget):
    def __init__(self,owner):
        super().__init__();self.owner=owner;self.trace=None;self.data=None;self.parents=[];self.saved={}
        from .toolbox import ResultView
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);row=QHBoxLayout();layout.addLayout(row)
        self.index=QSpinBox();self.index.setMinimum(1);self.index.setPrefix('Bloque ');self.index.setAccessibleName('Bloque de convolución');self.index.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.previous=QPushButton('‹');self.next=QPushButton('›')
        for button,name in ((self.previous,'Bloque anterior'),(self.next,'Bloque siguiente')):button.setMaximumWidth(36);button.setAccessibleName(name);row.addWidget(button)
        self.previous.clicked.connect(self.index.stepDown);self.next.clicked.connect(self.index.stepUp);row.insertWidget(1,self.index)
        self.part=QComboBox();self.part.addItems(['Entrada con historia','Salida de la FFT','Contribución / salida válida','Salida total en ese intervalo']);row.addWidget(self.part,1)
        self.note=QLabel();self.note.setWordWrap(True);layout.addWidget(self.note)
        self.view=ResultView();layout.addWidget(self.view,1)
        self.index.valueChanged.connect(self.calculate);self.part.currentIndexChanged.connect(self.display)

    def set_trace(self,trace,parents):
        self.trace=trace;self.parents=list(parents);self.saved={};self.index.blockSignals(True);self.index.setMaximum(trace['result'].metadata['blocks']);self.index.setValue(1);self.index.blockSignals(False);self.data=None
        self.part.setItemText(0,'Entrada con historia' if trace['result'].metadata['method']=='ols' else 'Entrada del bloque')
        self.part.setItemText(2,'Salida válida' if trace['result'].metadata['method']=='ols' else 'Contribución para sumar')
        self.calculate()

    def calculate(self,*_):
        if self.trace is None:return
        index=self.index.value()-1;trace=self.trace;self.data=None;self.view.clear_result('Calculando bloque…');self.note.setText('Calculando bloque…')
        def accept(data):
            if trace is not self.trace:return
            self.data=data;self.index.blockSignals(True);self.index.setValue(index+1);self.index.blockSignals(False);self.display()
        self.owner._run_operation('Inspeccionando bloque de convolución…',lambda:math.inspect(trace,index),accept)
        workers=getattr(self.owner,'_workers',[])
        if workers:
            self.index.setEnabled(False);self.previous.setEnabled(False);self.next.setEnabled(False)
            workers[-1].signals.finished.connect(self.finished);workers[-1].signals.failed.connect(self.finished)

    def finished(self,*_):
        self.index.setEnabled(True)
        self.previous.setEnabled(self.index.value()>1);self.next.setEnabled(self.index.value()<self.index.maximum())
        if self.data is None:self.note.setText('No se obtuvo el bloque. Revisá el diagnóstico del cálculo y elegí otro bloque o corregí los parámetros.')

    def display(self,*_):
        if self.data is None:return
        data=self.data;part=self.part.currentIndex();value=data['signals'][part];key=(data['block'],part)
        self.previous.setEnabled(data['block']>0);self.next.setEnabled(data['block']+1<data['blocks'])
        self.note.setText(f"Bloque {data['block']+1} de {data['blocks']} · L={data['new_samples']} · FFT={data['fft_size']} · descartadas al inicio: {data['discard']} · puntos FFT finales no utilizados: {data['unused']}. "+data['explanation'])
        value.metadata['discarded_first_samples']=data['discard'] if part==1 else 0
        value.metadata['unused_trailing_samples']=data['unused'] if part==1 else 0
        if key not in self.saved:self.saved[key]=self.owner.publish(value,operation='Inspección por bloques · '+value.name,parents=self.parents)
        self.view.show();self.view.show_result(value);self.view.result_ids=[self.saved[key]]
        if part==1 and data['discard']:
            for axis in self.view.figure.axes:
                start=value.origin-(getattr(axis,'_signallab_index_origin',None) or 0)
                patch=axis.axvspan(start-.5,start+data['discard']-.5,color='#edc27d',alpha=.18,label='Descartadas')
                patch._signallab_reference=True
                if data['unused']:
                    patch=axis.axvspan(start+len(value.values)-data['unused']-.5,start+len(value.values)-.5,color='#8194ae',alpha=.18,label='No utilizadas')
                    patch._signallab_reference=True
            self.view.canvas.draw_idle()
