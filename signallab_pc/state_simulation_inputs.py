"""Independent channel sources and explicit axes for state-space simulation."""
from dataclasses import dataclass
import math
import numpy as np
from PySide6.QtCore import Signal as QtSignal
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QComboBox,QStackedWidget
from .resources import ensure_working_set


@dataclass
class SimulationInputs:
    sources:list
    values:np.ndarray
    axis:np.ndarray
    step:float
    origin:float
    time_start:float
    discrete:bool


def prepare_inputs(model,sources):
    if len(sources)!=model.inputs:raise ValueError('Se requiere una señal por cada canal de entrada del modelo.')
    discrete=model.dt is not None;kind='discrete' if discrete else 'continuous'
    if any(source.domain!=kind for source in sources):raise ValueError('Las entradas deben tener el mismo dominio que el modelo.')
    first=sources[0];count=len(first.values);origin=first.origin;step=model.dt if discrete else first.step
    ensure_working_set(count*(model.inputs+model.outputs+model.states),live_arrays=8)
    if step<=0 or not math.isfinite(step):raise ValueError('El paso de entrada debe ser positivo y finito.')
    starts=[]
    for channel,source in enumerate(sources,1):
        if len(source.values)!=count:raise ValueError(f'u{channel}: todos los canales deben tener la misma cantidad de muestras ({count}).')
        if discrete:
            if source.origin!=origin:raise ValueError(f'u{channel}: el primer índice debe coincidir con el de u1 ({origin}). No se recortan ni desplazan canales automáticamente.')
            rate=source.metadata.get('sample_rate_hz')
            if rate is not None:
                rate=float(rate)
                if not math.isfinite(rate) or rate<=0 or not np.isclose(1/rate,step,rtol=1e-12,atol=0):raise ValueError(f'u{channel}: su tasa de muestreo no coincide con el período T={step:g} s del modelo. Revisá T o cambiá la tasa de la señal.')
            start=source.metadata.get('time_start_s')
            if start is not None:
                start=float(start)
                if not math.isfinite(start):raise ValueError(f'u{channel}: el inicio del reloj debe ser finito.')
                starts.append(start)
        else:
            from .distributions import regular_only
            regular_only(source,'La simulación de estados')
            if source.units!='s':raise ValueError(f'u{channel}: se requiere un eje temporal en segundos.')
            if not np.isclose(source.step,step,rtol=1e-12,atol=0) or source.origin!=origin:raise ValueError(f'u{channel}: todos los canales deben usar el mismo inicio y paso temporal. No se interpola automáticamente la entrada.')
    time_start=starts[0] if starts else float(origin)*step if discrete else float(origin)
    tolerance=max(1e-9*step,8*math.ulp(time_start))
    if any(abs(start-time_start)>tolerance for start in starts):raise ValueError('Los canales tienen distintos tiempos físicos para su primer índice. Revisá sus relojes antes de simular.')
    time=time_start+step*np.arange(count)
    if not np.isfinite(time).all() or (count>1 and np.any(np.diff(time)<=0)):raise ValueError('El reloj no permite distinguir los instantes de la simulación. Revisá su inicio y período.')
    return SimulationInputs(sources,np.column_stack([source.values for source in sources]),first.axis,step,origin,time_start,discrete)


class StateInputSources(QWidget):
    """One visible channel at a time; drafts survive channel/domain changes."""
    textChanged=QtSignal()
    def __init__(self,window):
        super().__init__();self.owner=window;self.kind='continuous';self.count=0;self.banks={'continuous':{},'discrete':{}}
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0)
        self.channel=QComboBox();self.channel.setAccessibleName('Canal de entrada del modelo');layout.addWidget(self.channel)
        self.stack=QStackedWidget();layout.addWidget(self.stack)
        self.note=QLabel();self.note.setWordWrap(True);layout.addWidget(self.note)
        self.channel.currentIndexChanged.connect(self.show_channel)
    def configure(self,count,discrete):
        kind='discrete' if discrete else 'continuous'
        if self.kind==kind and self.count==count:return
        ensure_working_set(max(1,count),bytes_per_sample=128,live_arrays=8)
        selected=self.channel.currentIndex();self.kind=kind;self.count=count
        self.channel.blockSignals(True);self.channel.clear()
        for index in range(count):self.channel.addItem('Entrada u'+str(index+1),index)
        self.channel.setCurrentIndex(min(max(0,selected),count-1));self.channel.blockSignals(False)
        self.channel.setVisible(count>1)
        self.note.setText('Cada canal admite fórmula, muestras, archivo o un resultado. Todos deben usar el mismo intervalo y cantidad de muestras. En discreto, n es entero; T fija el reloj físico.' if count else 'Completá B y D para definir las entradas del modelo.')
        self.stack.setVisible(count>0);self.show_channel();self.textChanged.emit()
    def field(self,index):
        bank=self.banks[self.kind]
        if index not in bank:
            from .toolbox import LocalInput
            field=LocalInput('Entrada u'+str(index+1)+('[n]' if self.kind=='discrete' else '(t)'),self.kind);field.bind_project(self.owner)
            field.expression.setText('1');field.count.setText('501');field.step.setText('0.01');field.layout().setContentsMargins(0,4,0,0)
            if index and 0 in bank:
                for name in ('origin','count','step'):getattr(field,name).setText(getattr(bank[0],name).text())
            for item in (field.mode,field.expression,field.samples,field.origin,field.count,field.step):
                signal=item.currentIndexChanged if item is field.mode else item.textChanged
                signal.connect(lambda *_:self.textChanged.emit())
            field.sourceChanged.connect(self.textChanged.emit);bank[index]=field;self.stack.addWidget(field)
        return bank[index]
    def show_channel(self,*_):
        index=self.channel.currentIndex()
        if index>=0:self.stack.setCurrentWidget(self.field(index))
    def read(self):
        return [self.field(index).read() for index in range(self.count)]
    def reference_ids(self):
        return [self.field(index).reference_id for index in range(self.count)]
    def text(self):
        bank=self.banks[self.kind]
        rows=[(index,field.mode.currentIndex(),field.expression.text(),field.samples.text(),field.origin.text(),field.count.text(),field.step.text(),getattr(field,'source_revision',0)) for index,field in bank.items() if index<self.count]
        return repr((self.kind,self.count,sorted(rows)))
