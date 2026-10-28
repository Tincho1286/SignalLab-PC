"""Window an independently supplied h[n] inside the existing FIR workflow."""
from PySide6.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QFormLayout,QComboBox,QLineEdit,QPushButton,QScrollArea,QCheckBox,QTabWidget,QMessageBox,QLabel
from .numeric_input import real_field,integer_field
from .result_state import ResultState
from .report_view import ReportView,report_panel
from .result_summary import transfer_summary,Section,Formula
from .windowing import window_impulse
from .frequency_analysis import frequency_grid,analyze_frequency
from .design_frequency import DesignFrequency
from .system_result_actions import SystemResultActions

class FirWindowPanel(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window;self.result=None;self.system=None;self.series_values=[];self.series_keys=[]
        from .toolbox import LocalInput,ResultView
        root=QHBoxLayout(self);root.setContentsMargins(6,6,6,6);controls=QWidget();form=QFormLayout(controls);form.setContentsMargins(4,4,4,4);form.setProperty('stackFields',True)
        self.h=LocalInput('Respuesta al impulso h[n] propia','discrete');self.h.bind_project(window);self.h.layout().setContentsMargins(4,6,4,4);self.h.expression.setText('sinc(n/3)/3');self.h.origin.setText('-25');self.h.count.setText('51');form.addRow(self.h)
        self.window_type=QComboBox()
        for title,value in [('Hamming','hamming'),('Hann','hann'),('Blackman','blackman'),('Kaiser','kaiser'),('Bartlett','bartlett'),('Rectangular','boxcar'),('Señal de ventana propia','custom')]:self.window_type.addItem(title,value)
        form.addRow('Ventana',self.window_type);self.beta=QLineEdit('8.6');form.addRow('β de Kaiser',self.beta)
        self.length=QLineEdit('51');form.addRow('Longitud L de la ventana (muestras)',self.length)
        self.length.setToolTip('Cantidad total de muestras de la ventana, independiente de la longitud del registro de h[n]. Convención: orden nominal M=L−1. No es la semilongitud.')
        self.position=QComboBox();self.position.addItems(['Centrada','Desde un índice elegido']);form.addRow('Ubicación de la ventana',self.position)
        self.start=QLineEdit('-25');form.addRow('Primer índice n_w',self.start)
        self.support_note=QLabel();self.support_note.setWordWrap(True);form.addRow(self.support_note)
        self.w=LocalInput('Ventana w[n] propia','discrete');self.w.bind_project(window);self.w.layout().setContentsMargins(4,6,4,4);self.w.expression.setText('1');self.w.coordinate_labels[self.w.count].setText('Longitud L (muestras)');form.addRow(self.w)
        self.retard=QCheckBox('Retardar si empieza antes de n=0');self.retard.setChecked(True)
        self.retard.setToolTip('Agrega D=−n₀ si el inicio del registro es negativo, para llevarlo a n=0. Se conserva un origen ya positivo. Desactivado mantiene los índices y admite un FIR no causal. El retardo modifica la fase y el retardo de grupo.');form.addRow(self.retard)
        self.calculate_button=QPushButton('Enventanar h[n] y obtener FIR');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);form.addRow(self.calculate_button)
        self.state=ResultState([self.window_type,self.beta,self.length,self.position,self.start,self.retard],self.calculate_button,[self.h,self.w]);form.insertRow(0,self.state)
        self._custom_initialized=False
        def configure(*_):
            custom=self.window_type.currentData()=='custom';formula=self.h.mode.currentIndex()==0
            form.setRowVisible(self.beta,self.window_type.currentData()=='kaiser');form.setRowVisible(self.w,custom)
            form.setRowVisible(self.length,not custom);form.setRowVisible(self.position,not custom);form.setRowVisible(self.start,not custom and self.position.currentIndex()==1)
            self.h.layout().setRowVisible(self.h.interval,not formula and self.h.mode.currentIndex()!=2)
            self.support_note.setText('La ventana propia define su longitud y sus índices. Si h[n] es fórmula, se evalúa en ese intervalo; si es un registro, se usa cero fuera de él.' if custom else 'L es la cantidad de muestras de la ventana; M=L−1 es el orden nominal. Centrada: en n=0 para una fórmula, o en el registro para muestras/archivo/resultado. Con L par el centro puede quedar a medio índice. La fórmula se evalúa en el intervalo elegido.')
            if custom and not self._custom_initialized:
                try:size=integer_field(self.length);origin=integer_field(self.start) if self.position.currentIndex()==1 else -(size//2)
                except ValueError:size=51;origin=-25
                self.w.origin.setText(str(origin));self.w.count.setText(str(size));self._custom_initialized=True
        self.window_type.currentIndexChanged.connect(configure);self.position.currentIndexChanged.connect(configure);self.h.mode.currentIndexChanged.connect(configure);configure()
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);root.addWidget(scroll,1)
        right=QWidget();out=QVBoxLayout(right);out.setContentsMargins(0,0,0,0);root.addWidget(right,2)
        self.tabs=QTabWidget();out.addWidget(self.tabs,1);self.frequency=DesignFrequency(window);self.tabs.addTab(self.frequency,'Respuesta en frecuencia')
        time=QWidget();time_layout=QVBoxLayout(time);self.selector=QComboBox();time_layout.addWidget(self.selector);self.series=ResultView();time_layout.addWidget(self.series);self.tabs.addTab(time,'h[n] y ventana')
        self.report=ReportView();self.tabs.addTab(report_panel(self.report),'Informe')
        self.actions=SystemResultActions(window);out.addWidget(self.actions)
        self.selector.currentIndexChanged.connect(self.show_series);self.tabs.currentChanged.connect(self.show_series)
    def show_series(self,*_):
        if self.tabs.currentIndex()!=1:return
        index=self.selector.currentIndex()
        if 0<=index<len(self.series_values):self.series.show_result(self.series_values[index]);self.series.result_ids=[self.series_keys[index]]
    def calculate(self):
        try:
            custom=self.w.read() if self.window_type.currentData()=='custom' else None
            h=None if self.h.mode.currentIndex()==0 else self.h.read()
            if custom is not None:size=len(custom.values);origin=custom.origin
            else:
                size=integer_field(self.length)
                if size<1:raise ValueError('L debe ser una cantidad entera positiva de muestras.')
                origin=integer_field(self.start) if self.position.currentIndex()==1 else -(size//2) if h is None else (2*h.origin+len(h.values)-size)//2
            if h is None:self.h.origin.setText(str(origin));self.h.count.setText(str(size));h=self.h.read()
            h_key=self.h.reference_id
            name=self.window_type.currentData();beta=real_field(self.beta) if name=='kaiser' else 0;retard=self.retard.isChecked();snapshot=self.state.snapshot()
            parents=[field.reference_id for field in ([self.h,self.w] if custom is not None else [self.h]) if field.reference_id]
            error='';grid=None
            try:grid=frequency_grid(*self.frequency.request('digital'))
            except ValueError as exc:error=str(exc)
            frequency_snapshot=self.frequency.state.snapshot()
            def compute():
                result=window_impulse(h,name,beta,retard,custom,length=size,start=origin)
                data=analyze_frequency(result.system,grid) if grid is not None else None
                return result,data
            def accept(pair):
                result,data=pair;self.result=result;self.system=result.system
                entries=[('h[n] cargada',result.original,h_key),('Ventana w[n]',result.window,None),('Producto h[n]·w[n]',result.windowed,None)]
                if result.delay:entries.append(('h[n] retardada para el FIR',result.impulse,None))
                keys={};self.series_values=[];self.series_keys=[];self.selector.blockSignals(True);self.selector.clear()
                for label,value,key in entries:
                    if key is None:key=keys.get(id(value)) or self.window.publish(value,operation='Enventanado de h[n]',parents=parents)
                    keys[id(value)]=key;self.series_values.append(value);self.series_keys.append(key);self.selector.addItem(label)
                self.selector.setCurrentIndex(len(entries)-1);self.selector.blockSignals(False)
                impulse_key=keys[id(result.impulse)];system_key=self.window.publish(result.system,operation='FIR desde h[n] enventanada',parents=[impulse_key]);self.actions.set_result(result.system,system_key)
                if data is not None:self.frequency.set_result(result.system,data,frequency_snapshot)
                else:self.frequency.clear_result(result.system);self.frequency.note.setText(error)
                summary=transfer_summary(result.system)
                summary.sections.insert(0,Section('Enventanado',rows=[('Ventana',result.window_name),('Longitud L de la ventana (muestras)',str(len(result.window.values))),('Orden nominal M = L−1',str(len(result.window.values)-1)),('Índices de la ventana',str(result.window.origin)+' a '+str(result.window.origin+len(result.window.values)-1)),('Primer índice de h cargada',str(h.origin)),('Primer índice del FIR',str(result.impulse.origin)),('Retardo agregado D',str(result.delay)+' muestras')],formulas=[Formula('h_w[n] = h[n]*w[n]','h_w[n] = h[n] · w[n]'),Formula('h_F[n] = h_w[n-'+str(result.delay)+']','h_F[n] = h_w[n−'+str(result.delay)+']')],paragraphs=['La longitud y ubicación de la ventana se eligen por separado de h[n]. La salida conserva el intervalo de la ventana. Para una fórmula se evalúa h[n] en esos índices; para un registro finito se usa cero fuera de sus datos. El orden efectivo puede cambiar si hay extremos nulos o desplazamientos. El producto conserva su ganancia; podés ajustarla desde Normalizar ganancia. El retardo usa el inicio del registro, no busca un retardo mínimo.']))
                self.report.set_readable(summary);self.window.publish({'report':self.report.toPlainText()},title='Enventanado de h[n] · '+result.window_name,operation='Informe de FIR enventanado',parents=[system_key]);self.state.accept(snapshot);self.show_series()
            self.window._run_operation('Enventanando h[n]…',compute,accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá h[n] y la ventana',str(exc))
