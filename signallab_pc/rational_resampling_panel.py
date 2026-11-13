from .numeric_input import real_field,integer_field
from .report_view import ReportView
"""Cambio racional de tasa con filtro antialias y reloj físico explícitos."""
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QLineEdit,QComboBox,QPushButton,QLabel,QScrollArea,QMessageBox,QCheckBox
from .sampling import resample_rational

class RationalResamplingPanel(QWidget):
    def __init__(self,window):
        super().__init__()
        from .toolbox import LocalInput,ResultView
        self.window=window;root=QHBoxLayout(self);controls=QWidget();layout=QVBoxLayout(controls)
        self.source=LocalInput('Señal de entrada');self.source.bind_project(window);layout.addWidget(self.source)
        form=QFormLayout();form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows);layout.addLayout(form)
        self.start=QLineEdit('0');self.rate=QLineEdit('48000');self.up=QLineEdit('147');self.down=QLineEdit('160');self.width=QLineEdit('10');self.beta=QLineEdit('5')
        for label,field in [('Fs de entrada (muestras/s)',self.rate),('Tiempo de la primera muestra (s)',self.start),('Multiplicador L',self.up),('Divisor M',self.down),('Semilongitud FIR por fase',self.width),('Beta de ventana Kaiser',self.beta)]:form.addRow(label,field)
        self.mode=QComboBox();self.mode.addItems(['Relación L/M','Frecuencia de salida']);form.insertRow(2,'Definir conversión',self.mode)
        self.target=QLineEdit('44100');form.insertRow(3,'Fs de salida deseada (muestras/s)',self.target)
        def mode_changed(*_):
            target=self.mode.currentIndex()==1
            form.setRowVisible(self.target,target);self.target.setProperty('calculationInput',target)
            for field in (self.up,self.down):form.setRowVisible(field,not target);field.setProperty('calculationInput',not target)
        self.mode.currentIndexChanged.connect(mode_changed);mode_changed()
        self.boundary=QComboBox();self.boundary.addItems(['Cero fuera del registro','Continuación lineal de los extremos']);form.addRow('Bordes',self.boundary)
        self.override=QCheckBox('Reinterpretar el reloj con estos valores');form.addRow(self.override)
        clock=QPushButton('Restaurar reloj registrado');clock.clicked.connect(self.read_clock);form.addRow(clock)
        note=QLabel('Fs de salida = Fs de entrada × L/M. El filtro atenúa imágenes y aliasing; su transición y los bordes son finitos. El retardo se compensa para análisis fuera de tiempo real.');note.setWordWrap(True);form.addRow(note)
        self.calculate_button=QPushButton('Convertir tasa con filtro');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);layout.insertWidget(0,self.calculate_button)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);root.addWidget(scroll,1)
        self.result=ResultView();root.addWidget(self.result,2)
        from .system_result_actions import SystemResultActions
        from .design_frequency import DesignFrequency
        self.filter_page=QWidget();filter_layout=QVBoxLayout(self.filter_page)
        self.filter_actions=SystemResultActions(window);filter_layout.addWidget(self.filter_actions)
        self.filter_view=DesignFrequency(window);filter_layout.addWidget(self.filter_view,1)
        self.filter_index=self.result.views.addTab(self.filter_page,'Filtro antialias');self.result.views.setTabVisible(self.filter_index,False)
        from .input_clock import bind_clock
        from .result_state import ResultState
        form.addRow(bind_clock(self.source,self.rate,self.start,self.override))
        self.result_state=ResultState([self.rate,self.start,self.up,self.down,self.width,self.beta,self.boundary,self.override,self.mode,self.target],self.calculate_button,[self.source]);layout.insertWidget(1,self.result_state)
    def read_clock(self):
        try:
            source=self.source.read()
            clock=source.metadata
            if 'sample_rate_hz' not in clock and 'time_start_s' not in clock:raise ValueError('La entrada no tiene reloj registrado.')
            self.override.setChecked(False)
            for key,field in (('sample_rate_hz',self.rate),('time_start_s',self.start)):
                if key in clock:field.setText(str(clock[key]))
        except Exception as exc:QMessageBox.warning(self,'Reloj de entrada',str(exc))
    def calculate(self):
        try:
            source=self.source.read();parent=self.source.reference_id
            override=self.override.isChecked()
            rate=real_field(self.rate) if override or source.metadata.get('sample_rate_hz') is None else None
            start=real_field(self.start) if override or source.metadata.get('time_start_s') is None else None
            arguments=dict(rate=rate,start=start,override_clock=override,half_width=integer_field(self.width),beta=real_field(self.beta),boundary='zero' if self.boundary.currentIndex()==0 else 'line')
            target=self.target.text() if self.mode.currentIndex()==1 else None
            up,down=(1,1) if target is not None else (integer_field(self.up),integer_field(self.down));calculated_inputs=self.result_state.snapshot()
            def accept(calculated):
                result=calculated['signal'];system=calculated['filter'];parents=[parent] if parent else []
                filter_key=self.window.publish(system,operation='Filtro antialias de conversión',parents=parents) if system is not None else None
                key=self.window.publish(result,operation='Cambio racional de tasa con antialias',parents=parents+([filter_key] if filter_key else []))
                self.result.show_result(result);self.result.result_ids=[key]
                from .resampling_tools import summary
                self.result.text.set_readable(summary(result,system,calculated['filter_note']))
                self.filter_actions.set_result(system,filter_key);self.result.views.setTabVisible(self.filter_index,system is not None)
                if system is not None:
                    self.filter_view.clear_result(system)
                    self.filter_view.note.setText('FIR de la rejilla intermedia: Fs intermedia = Fs de entrada × L. Actualizar respuesta muestra módulo, fase y retardo. El cambio de tasa compensa ese retardo al generar la salida.')
                self.result_state.accept(calculated_inputs)
            from .resampling_tools import convert
            self.window._run_operation('Convirtiendo tasa con filtro polifásico…',lambda:convert(source,up,down,target=target,**arguments),accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá los parámetros',str(exc))
