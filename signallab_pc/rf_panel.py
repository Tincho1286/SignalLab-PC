"""Workbench forms for the shared RF and advanced Fourier requests."""

from pathlib import Path

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QInputDialog,
    QLabel, QLineEdit, QPushButton, QScrollArea, QTabWidget, QVBoxLayout, QWidget,
)

from .numeric_input import integer_field, real_field
from .report_view import ReportView, report_panel
from .result_state import ResultState
from .result_summary import Section, Summary, number
from .result_toolbar import ResultActionBar, attach
from .rf_analysis import measure
from .rf_application import RFRequest, run_rf, store_rf
from .rf_line import smith_grid, smith_values
from .rf_storage import is_rf_data, load_network
from .scalar_expression import constant_value
from .touchstone import read_touchstone, write_touchstone
from .validation import show_input_error
from .visible_curve import VisibleCurve


MODES = {
    'network': (
        ('Analizar parámetros y puertos','analyze'), ('Definir una red','define'),
        ('Convertir representación','convert'), ('Cambiar referencias (renormalizar)','renormalize'),
        ('Conectar en cascada','cascade'), ('Terminar puertos','terminate'), ('Interpolar en banda','interpolate'),
    ),
    'line': (
        ('Línea uniforme','line'), ('Línea RLGC','rlgc'), ('Adaptación L, cuarto de onda o stub','match'),
        ('Sensibilidad de un adaptador','matching_sweep'),
    ),
    'link': (
        ('Presupuesto de enlace','link'), ('Ruido en cascada','noise'), ('Compresión y distorsión','device'),
        ('Barrido de figura de ruido','noise_sweep'), ('Incertidumbre de enlace','link_campaign'),
    ),
    'spectral': (('Zoom FFT','zoom'), ('Chirp-Z','czt')),
}
NETWORK_INPUTS = {'analyze', 'convert', 'renormalize', 'cascade', 'terminate', 'interpolate'}
_LINK_SETTINGS = ('link','noise','noise_sweep','link_campaign')
_LINK_PATH = ('link','link_campaign')
_POWER_FIELDS = {
    'eirp_dbm':'Potencia isotrópica equivalente (dBm)', 'received_at_antenna_dbm':'Potencia en la antena RX (dBm)',
    'receiver_output_dbm':'Potencia a la salida del receptor (dBm)', 'snr_db':'SNR (dB)',
    'margin_db':'Margen de enlace (dB)', 'path_loss_db':'Pérdida de trayecto (dB)',
    'shadow_loss_db':'Pérdida por sombra (dB)', 'noise_figure_db':'Figura de ruido (dB)',
    'noise_factor':'Factor de ruido', 'equivalent_temperature_k':'Temperatura equivalente (K)',
    'input_density_dbm_per_hz':'Densidad de entrada (dBm/Hz)', 'input_noise_dbm':'Ruido integrado de entrada (dBm)',
    'output_noise_dbm':'Ruido integrado de salida (dBm)', 'sensitivity_dbm':'Sensibilidad (dBm)',
    'gain_db':'Ganancia (dB)', 'iip3_dbm':'IIP3 (dBm)', 'oip3_dbm':'OIP3 (dBm)',
    'input_p1db_dbm':'P1dB de entrada (dBm)', 'output_p1db_dbm':'P1dB de salida (dBm)',
    'fundamental_per_tone_dbm':'Fundamental por tono (dBm)', 'compression_db':'Compresión (dB)',
    'third_harmonic_dbm':'Tercer armónico (dBm)', 'im3_per_product_dbm':'IM3 por producto (dBm)',
    'sfdr_db':'SFDR de dos tonos (dB)', 'input_limit_per_tone_dbm':'Límite por tono (dBm)',
}


def _display(value):
    if value is None or np.isnan(value):
        return 'Indefinido'
    if np.isinf(value):
        return '∞' if value > 0 else '−∞'
    return number(value)


def _vectors(text, *, complex_values=False):
    values = [constant_value(part.strip()) for part in text.split(',')]
    if complex_values:
        return [[float(value.real),float(value.imag)] for value in values]
    if any(value.imag for value in values):
        raise ValueError('La lista requiere valores reales.')
    return [float(value.real) for value in values]


class RFPanel(QWidget):
    def __init__(self, window, task):
        super().__init__()
        self.window,self.task=window,task
        self.active_result=None
        self.active_record=None
        self.inputs=[None,None]
        self.input_tokens=[]
        self.editors={}
        self.visible_in={}
        root=QHBoxLayout(self)
        controls=QWidget()
        self.form=QFormLayout(controls)
        self.form.setProperty('stackFields',True)
        self.mode=self._choice('operation','Operación',MODES[task])
        if task=='network':
            self._network_fields()
        elif task=='line':
            self._line_fields()
        elif task=='link':
            self._link_fields()
        else:
            self._spectral_fields()
        self.calculate_button=QPushButton('Calcular')
        self.calculate_button.setObjectName('primary')
        self.calculate_button.clicked.connect(self.calculate)
        self.form.addRow(self.calculate_button)
        observed=[entry for entry in self.editors.values() if isinstance(entry,(QLineEdit,QComboBox,QCheckBox))]
        self.state=ResultState([*observed,*self.input_tokens],self.calculate_button,
                               [self.source] if task=='spectral' else [])
        self.form.insertRow(0,self.state)
        scroll=QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(controls)
        root.addWidget(scroll,1)
        root.addWidget(self._build_output(),2)
        self.mode.currentIndexChanged.connect(self._configure)
        self._configure()

    def _add(self,key,label,widget,modes):
        self.editors[key]=widget
        self.visible_in[key]=tuple(modes.split()) if modes else ()
        widget.setAccessibleName(label)
        self.form.addRow(label,widget)
        return widget

    def _text(self,key,label,value='',modes=''):
        widget=QLineEdit(value)
        widget.setClearButtonEnabled(True)
        return self._add(key,label,widget,modes)

    def _choice(self,key,label,options,modes=''):
        widget=QComboBox()
        for title,value in options:
            widget.addItem(title,value)
        return self._add(key,label,widget,modes)

    def _network_fields(self):
        for index in (0,1):
            box=QWidget()
            layout=QVBoxLayout(box)
            layout.setContentsMargins(0,0,0,0)
            caption=QLabel('Elegí una red.')
            caption.setWordWrap(True)
            setattr(self,'source_label_'+str(index),caption)
            layout.addWidget(caption)
            for title,action in (('Abrir Touchstone…',self._select_file),('Cargar de resultados…',self._select_project)):
                button=QPushButton(title)
                button.clicked.connect(lambda _checked=False,i=index,handler=action:handler(i))
                layout.addWidget(button)
            modes=' '.join(NETWORK_INPUTS) if index==0 else 'cascade'
            self._add('network_'+str(index),f'Red {index+1}',box,modes)
            token=QLineEdit(box)
            token.hide()
            self.input_tokens.append(token)
        self._choice('representation','Representación',[(key,key) for key in ('S','Z','Y','ABCD')],'define convert')
        self._text('name','Nombre de la red','Red RF','define')
        self._text('frequencies','Frecuencias en Hz, separadas por coma','','define interpolate')
        self._text('reference','Referencias en Ω, común o por puerto','50','define renormalize')
        self._text('matrix','Entradas por filas; separá matrices con ;','','define').setToolTip(
            'En cada matriz, ingresá los elementos en orden 11, 12, 21, 22 para dos puertos. Usá i o j en la parte imaginaria.')
        self._text('keep','Puertos a conservar, desde 1','1','terminate')
        self._text('load','Carga de los otros puertos en Ω, o matched/open/short','matched','terminate')
        option=QCheckBox('Igualar las referencias de la conexión')
        self._add('renormalize_internal','Cascada',option,'cascade')

    def _line_fields(self):
        for key,label,value in (
            ('minimum','Frecuencia inicial (Hz)','5e8'), ('maximum','Frecuencia final (Hz)','1.5e9'),
            ('points','Puntos de la rejilla','401'), ('source_ohm','Referencia de entrada (Ω)','50'),
            ('load','Carga en Ω, o matched/open/short',''),
        ):
            self._text(key,label,value)
        self._text('length_m','Longitud (m)','0.1','line rlgc')
        self._text('characteristic_ohm','Impedancia característica (Ω)','50','line')
        self._text('velocity_factor','Factor de velocidad','0.8','line match matching_sweep')
        self._text('attenuation_db_per_m','Atenuación (dB/m)','0','line')
        for key,label,value in (
            ('resistance_ohm_per_m','Resistencia serie (Ω/m)','1'),
            ('inductance_h_per_m','Inductancia serie (H/m)','250e-9'),
            ('conductance_s_per_m','Conductancia transversal (S/m)','0'),
            ('capacitance_f_per_m','Capacitancia transversal (F/m)','100e-12'),
        ):
            self._text(key,label,value,'rlgc')
        self._text('frequency_hz','Frecuencia de adaptación (Hz)','1e9','match matching_sweep')
        self._choice('method','Red de adaptación',[('L','l'),('Cuarto de onda','quarter_wave'),
                     ('Stub en derivación','stub')],'match matching_sweep')
        self._choice('stub','Terminación del stub',[('Abierto','open'),('Cortocircuitado','short')],'match matching_sweep')
        self._choice('parameter','Parámetro a variar',[
            ('Resistencia de carga (Ω)','resistance_ohm'), ('Reactancia de carga (Ω)','reactance_ohm'),
            ('Longitud de línea (m)','line_m'), ('Longitud de stub (m)','stub_m'),
            ('Inductancia serie (H)','series_L_H'), ('Capacitancia serie (F)','series_C_F'),
            ('Inductancia paralelo (H)','shunt_L_H'), ('Capacitancia paralelo (F)','shunt_C_F'),
            ('Factor de velocidad','velocity_factor'),
        ],'matching_sweep')
        self._text('sweep_values','Lista de valores crecientes','90,100,110','matching_sweep')
        self._text('solution','Número de solución, desde 1','1','matching_sweep')
        self.editors['method'].currentIndexChanged.connect(self._configure)

    def _link_fields(self):
        path_modes=' '.join(_LINK_PATH)
        link_modes=' '.join(_LINK_SETTINGS)
        self._text('transmitted_dbm','Potencia transmitida (dBm)','0',path_modes)
        self._text('carrier_hz','Portadora (Hz)','2.4e9',path_modes)
        self._text('distance_m','Distancia (m)','100',path_modes)
        self._text('tx_antenna_dbi','Antena TX (dBi)','0',path_modes)
        self._text('rx_antenna_dbi','Antena RX (dBi)','0',path_modes)
        self._text('tx_loss','Pérdidas TX por etapa (dB)','',path_modes)
        self._text('rx_loss','Pérdida de cable RX (dB)','0',link_modes)
        self._text('gain_db','Ganancia (dB)','15',link_modes+' device')
        self._text('noise_figure_db','Figura de ruido del receptor (dB)','3','link noise link_campaign')
        self._text('figures_db','Figuras de ruido a comparar (dB)','1,3,6','noise_sweep')
        self._text('bandwidth_hz','Ancho equivalente de ruido (Hz)','1e6',link_modes)
        self._text('source_temperature_k','Temperatura de la fuente (K)','290',link_modes)
        self._text('required_snr_db','SNR requerida (dB)','10',link_modes)
        self._text('input_per_tone_dbm','Entrada por tono (dBm)','-30','device')
        self._choice('tones','Excitación',[('Dos tonos',2),('Un tono',1)],'device')
        self._choice('calibration','Calibrar por',[('IIP3 de entrada','iip3_dbm'),
                     ('P1dB de entrada','input_p1db_dbm')],'device')
        self._text('level','Nivel de calibración (dBm)','0','device')
        self._text('output_noise_dbm','Ruido integrado de salida (dBm), opcional','','device')
        self._text('propagation_std_db','Desvío de pérdida de propagación (dB)','2','link_campaign')
        self._text('gain_std_db','Desvío de ganancia (dB)','1','link_campaign')
        self._text('noise_level_std_db','Desvío del piso de ruido (dB)','0','link_campaign')
        self._text('seed','Semilla de la campaña','2026','link_campaign')
        self._text('replicas','Réplicas','64','link_campaign')
        self._choice('metric','Estimar',[('Margen medio (dB)','mean'),('Probabilidad de margen ≥ 0','probability')],
                     'link_campaign')
        campaign_folder=self._text('directory','Carpeta de campaña','','link_campaign')
        folder_button=QPushButton('Elegir carpeta…')
        self._add('select_directory','Guardado y reanudación',folder_button,'link_campaign')

        def select_directory():
            selected=QFileDialog.getExistingDirectory(self,'Carpeta de la campaña RF')
            if selected:campaign_folder.setText(selected)
        folder_button.clicked.connect(select_directory)

    def _spectral_fields(self):
        from .toolbox import LocalInput
        from .window_signals import WINDOWS,WINDOW_PARAMETERS
        self.source=LocalInput('Señal discreta', 'discrete')
        self.source.bind_project(self.window)
        self.form.addRow(self.source)
        self._text('count','Puntos de la transformación','1025')
        self._choice('units','Unidad del eje',[('rad/muestra','rad/muestra'),('Hz','Hz')],'zoom')
        self._text('start','Inicio del intervalo','-pi','zoom')
        self._text('stop','Fin del intervalo','pi','zoom')
        self._text('rate_hz','Frecuencia de muestreo en Hz, si falta en la señal','','zoom')
        self._choice('window','Ventana',WINDOWS,'zoom')
        self._choice('symmetric','Malla de la ventana',[('Periódica',False),('Simétrica',True)],'zoom')
        for key,label,default in WINDOW_PARAMETERS.values():
            self._text(key,label,str(default),'zoom')
        self._text('complex_tone_peaks','Picos de tonos complejos aislados (0 = desactivado)','0','zoom')
        self._add('compare_dft','Comparación',QCheckBox('Superponer bins de la DFT'),'zoom')
        self._text('initial_radius','Radio inicial','1','czt')
        self._text('radius_ratio','Razón entre radios','1','czt')
        self._text('initial_angle_rad','Ángulo inicial (rad)','0','czt')
        self._text('angle_step_rad','Paso angular (rad). Vacío: 2π / puntos','','czt')
        self.editors['window'].currentIndexChanged.connect(self._configure)
        self.editors['units'].currentIndexChanged.connect(self._configure)

    def _build_output(self):
        panel=QWidget()
        layout=QVBoxLayout(panel)
        self.tabs=QTabWidget()
        self.report=ReportView()
        self.actions=ResultActionBar()
        attach(self.tabs,self.actions)
        layout.addWidget(self.actions)
        layout.addWidget(self.tabs,1)
        self.tabs.addTab(report_panel(self.report),'Informe')
        self.report.setPlainText('Cargá los datos de una operación para obtener su informe.')
        graph=QWidget()
        graph_layout=QVBoxLayout(graph)
        controls=QWidget()
        toolbar=QHBoxLayout(controls)
        self.figure_choice=QComboBox()
        self.figure_choice.setAccessibleName('Magnitud del gráfico')
        toolbar.addWidget(self.figure_choice,2)
        self.channel=QComboBox()
        self.channel.setAccessibleName('Parámetro de red o solución')
        toolbar.addWidget(self.channel,1)
        self.figure_choice.currentIndexChanged.connect(self.draw)
        self.channel.currentIndexChanged.connect(self.draw)
        self.figure=Figure(layout='constrained')
        self._smith=None
        self.canvas=FigureCanvasQTAgg(self.figure)
        self.canvas._signallab_explicit_plot=True
        self.canvas._signallab_plot_controls=controls
        self.canvas.mpl_connect('button_press_event',self._mark_smith)
        graph_layout.addWidget(controls)
        graph_layout.addWidget(NavigationToolbar2QT(self.canvas,graph))
        graph_layout.addWidget(self.canvas,1)
        self.graph_tab=self.tabs.addTab(graph,'Gráfico')
        self.tabs.setTabVisible(self.graph_tab,False)
        self.actions.use_report(self.report)
        self.export=self.actions.slots['export'].menu().addAction('Red Touchstone 2.0…',self._export)
        self.export.setVisible(False)
        self.reuse=QPushButton('Usar red en…')
        self.reuse.clicked.connect(self._reuse)
        self.reuse.setEnabled(False)
        self.actions.add_action(self.reuse,'reuse')
        return panel

    def _configure(self,*_):
        op=self.mode.currentData()
        for key,widget in self.editors.items():
            visible = not self.visible_in[key] or op in self.visible_in[key]
            if key=='stub':
                visible=visible and self.editors['method'].currentData()=='stub'
            if key=='rate_hz':
                visible=visible and self.editors['units'].currentData()=='Hz'
            if self.task=='spectral':
                from .window_signals import WINDOW_PARAMETERS
                controls={item[0]:name for name,item in WINDOW_PARAMETERS.items()}
                if key in controls:
                    visible=visible and self.editors['window'].currentData()==controls[key]
            self.form.setRowVisible(widget,visible)
            widget.setProperty('calculationInput',visible)
        self.state.refresh()

    def _select_file(self,index):
        filename,_=QFileDialog.getOpenFileName(self,'Importar red Touchstone','','Touchstone (*.ts *.s*p);;Todos los archivos (*)')
        if filename:
            self._set_input(index,Path(filename),None)

    def _select_project(self,index):
        records=[row for row in self.window.project.headers('calculation')
                 if is_rf_data(self.window.project._records[row['id']]['data']) and 'verified_provenance' in row]
        if not records:
            self.window.statusBar().showMessage('Todavía no hay redes RF en los resultados.')
            return
        labels=[f"{row['title']} · {row['id'][:8]}" for row in records]
        text,accepted=QInputDialog.getItem(self,'Cargar una red','Red guardada',labels,0,False)
        if accepted:
            row=records[labels.index(text)]
            self._set_input(index,row['title'],row['id'])

    def _set_input(self,index,value,record):
        self.inputs[index]=(value,record)
        getattr(self,'source_label_'+str(index)).setText(value.name if isinstance(value,Path) else value)
        self.input_tokens[index].setText(record or str(value))

    def _settings(self):
        op=self.mode.currentData()
        field=self.editors
        text=lambda key:field[key].text().strip()
        real=lambda key:real_field(field[key])
        choice=lambda key:field[key].currentData()
        params={}
        values=[]
        if op=='define':
            frequency=_vectors(text('frequencies'))
            matrices=[_vectors(row,complex_values=True) for row in text('matrix').split(';')]
            width=int(np.sqrt(len(matrices[0])))
            if width**2!=len(matrices[0]) or any(len(row)!=width**2 for row in matrices):
                raise ValueError('Cada frecuencia requiere una matriz cuadrada del mismo tamaño.')
            params={'frequencies_hz':frequency,'value_pairs':np.asarray(matrices).reshape(-1,width,width,2).tolist(),
                    'name':text('name'),'representation':choice('representation')}
        if op in ('define','renormalize'):
            reference=_vectors(text('reference'))
            params['reference_ohm']=reference[0] if len(reference)==1 else reference
        if op=='convert':params['representation']=choice('representation')
        if op=='interpolate':params['frequencies_hz']=_vectors(text('frequencies'))
        if op=='cascade':params['renormalize_internal']=field['renormalize_internal'].isChecked()
        if op=='terminate':
            indices=_vectors(text('keep'))
            if any(int(value)!=value for value in indices):
                raise ValueError('Ingresá números enteros de puerto.')
            params['keep']=[int(value)-1 for value in indices]
        if op in NETWORK_INPUTS:
            values=self.inputs[:2 if op=='cascade' else 1]
            if any(value is None for value in values):
                raise ValueError('Cargá las redes indicadas para la operación.')
        if op in ('line','rlgc','match','matching_sweep'):
            points=integer_field(field['points'])
            low,high=real('minimum'),real('maximum')
            if not 2<=points<=10001 or not low<high:
                raise ValueError('Ingresá un intervalo creciente con 2 a 10 001 puntos.')
            params['frequencies_hz']=np.linspace(low,high,points).tolist()
            if op in ('match','matching_sweep'):
                keys=('frequency_hz','source_ohm','velocity_factor')
                params.update(method=choice('method'),stub=choice('stub'))
                center=real('frequency_hz')
                if low <= center <= high:
                    closest=int(np.argmin(np.abs(np.asarray(params['frequencies_hz'])-center)))
                    if abs(params['frequencies_hz'][closest]-center) <= 4*abs(np.spacing(center)):
                        params['frequencies_hz'][closest]=center
                    else:
                        params['frequencies_hz']=sorted([*params['frequencies_hz'],center])
            else:
                keys=('length_m',)
                params['reference_ohm']=real('source_ohm')
                keys += ('characteristic_ohm','velocity_factor','attenuation_db_per_m') if op=='line' else (
                    'resistance_ohm_per_m','inductance_h_per_m','conductance_s_per_m','capacitance_f_per_m')
            params.update({key:real(key) for key in keys})
        if op in ('terminate','line','rlgc','match','matching_sweep'):
            adapting=op in ('match','matching_sweep')
            load=text('load') or ('100' if adapting else 'matched')
            if load in ('matched','open','short') and not adapting:params['load_ohm']=load
            else:
                load=constant_value(load)
                params['load_ohm_pairs']=[float(load.real),float(load.imag)]
        if op=='matching_sweep':
            grids=params.pop('frequencies_hz')
            params={'design':params,'frequencies_hz':grids,'values':_vectors(text('sweep_values')),
                    'parameter':choice('parameter'),'solution':integer_field(field['solution'])-1}
        if op in (*_LINK_SETTINGS,'device'):
            if op=='device':
                params={'gain_db':real('gain_db'),'input_per_tone_dbm':real('input_per_tone_dbm'),
                        'tones':choice('tones'),choice('calibration'):real('level')}
                if text('output_noise_dbm'):params['output_noise_dbm']=real('output_noise_dbm')
            else:
                stages=[{'name':'Cable RX','loss_db':real('rx_loss')},
                        {'name':'Receptor','gain_db':real('gain_db'),
                         'noise_figure_db':0 if op=='noise_sweep' else real('noise_figure_db')}]
                params={key:real(key) for key in ('bandwidth_hz','source_temperature_k','required_snr_db')}
                params['receive_stages' if op in _LINK_PATH else 'stages']=stages
                if op=='noise_sweep':params.update(stage_index=1,figures_db=_vectors(text('figures_db')))
                if op in _LINK_PATH:
                    params.update({key:real(key) for key in ('transmitted_dbm','carrier_hz','tx_antenna_dbi','rx_antenna_dbi')})
                    params['propagation']={'model':{'kind':'free_space','distance_m':real('distance_m')}}
                    if text('tx_loss'):
                        params['transmit_stages']=[{'name':f'Pérdida TX {i+1}','loss_db':value}
                                                   for i,value in enumerate(_vectors(text('tx_loss')))]
                if op=='link_campaign':
                    if not text('directory'):
                        raise ValueError('Elegí una carpeta para guardar y reanudar la campaña.')
                    scenarios=[{'name':'Enlace RF','link':params,**{key:real(key) for key in (
                        'propagation_std_db','gain_std_db','noise_level_std_db')}}]
                    params={'scenarios':scenarios,'directory':text('directory'),'seed':integer_field(field['seed']),
                            'replicas':integer_field(field['replicas']),'metric':choice('metric')}
        registration=None
        if op in ('zoom','czt'):
            source=self.source.read(register=False)
            stored,signature,_=self.source.input_registration(source)
            registration=(getattr(self.source,'source_revision',0),signature)
            values=[(source,stored)]
            params['count']=integer_field(field['count'])
            if op=='zoom':
                from .window_signals import WINDOW_PARAMETERS
                window=choice('window')
                options={'symmetric':choice('symmetric')}
                if window in WINDOW_PARAMETERS:
                    key=WINDOW_PARAMETERS[window][0]
                    options[key]=real(key)
                params.update(start=real('start'),stop=real('stop'),units=choice('units'),window=window,
                              window_options=options,complex_tone_peaks=integer_field(field['complex_tone_peaks']),
                              compare_dft=field['compare_dft'].isChecked())
                if choice('units')=='Hz' and text('rate_hz'):params['rate_hz']=real('rate_hz')
            else:
                params.update({key:real(key) for key in ('initial_radius','initial_angle_rad','radius_ratio')})
                if text('angle_step_rad'):params['angle_step_rad']=real('angle_step_rad')
        return RFRequest(op,params),values,registration

    def calculate(self):
        try:
            request,values,registration=self._settings()
            snapshot=self.state.snapshot()
            route=getattr(self.window,'current_operation',None)
            tool={'title':route[0],'route':list(route)} if route else None
            project=self.window.project

            def work():
                from .model import Signal
                inputs=[item if isinstance(item,Signal) else load_network(project,key) if key else read_touchstone(item)
                        for item,key in values]
                result=run_rf(request,inputs)
                figures=None
                if result.network is not None and request.operation not in ('line','rlgc','match','analyze'):
                    try:figures=measure(result.network)
                    except ValueError:pass  # The requested representation can be valid at an undefined S point.
                ids=[key for _,key in values]
                if project is not self.window.project:
                    raise ValueError('El proyecto cambió durante el cálculo RF.')
                receipt=store_rf(project,result,source_ids=ids,tool=tool)
                return result,figures,receipt

            def accept(completed):
                result,figures,receipt=completed
                if project is not self.window.project:
                    return
                if registration is not None and getattr(self.source,'source_revision',0)==registration[0]:
                    self.source.remember_registration(receipt['source_ids'][0],registration[1])
                self.active_result,self.measurements=result,figures
                self.active_record=receipt['product_id']
                self.alternate_records=receipt['alternative_ids']
                self.window.refresh_project()
                self._results()
                self.state.accept(snapshot)

            self.window._run_operation('Calculando…',work,accept)
        except (ValueError,TypeError,OSError,IndexError) as exc:
            show_input_error(self,'Revisá la entrada',exc)

    def _results(self):
        result=self.active_result
        op=result.request.operation
        natural=result.data
        rows=[]
        for key,label in _POWER_FIELDS.items():
            if hasattr(natural,key):
                rows.append((label,_display(getattr(natural,key))))
        if hasattr(natural,'noise'):
            rows.extend((label,_display(getattr(natural.noise,key))) for key,label in _POWER_FIELDS.items()
                        if hasattr(natural.noise,key) and not hasattr(natural,key))
        options={}
        channels=[]
        self.export.setVisible(result.network is not None)
        self.export.setEnabled(result.network is not None)
        self.reuse.setText('Usar señal en…' if result.signal is not None else 'Usar red en…')
        self.reuse.setEnabled(self.active_record is not None and op!='czt')
        if result.network is not None:
            net=result.network
            rows.extend((('Parámetros',net.representation),('Puertos',', '.join(net.port_names)),
                         ('Frecuencias',f'{len(net.frequencies_hz)} puntos de {number(net.frequencies_hz[0])} a {number(net.frequencies_hz[-1])} Hz')))
            if op in ('line','rlgc','match'):
                options={'Reflexión de entrada (dB)':'reflection','VSWR':'vswr',
                         'Carta de Smith Z':'impedance','Carta de Smith Y':'admittance'}
                if op=='match':
                    from .rf_matching import element_label
                    options['Potencia entregada (%)']='power'
                    for i,design in enumerate(natural['designs']):
                        channels.append((f'Solución {i+1}',i))
                        rows.extend((f'{i+1} · {element_label(key)}',_display(value)) for key,value in design.elements)
                else:
                    rows.append(('Longitud (m)',_display(natural.length_m)))
                    options.update({'Pérdida intrínseca (dB)':'loss','Impedancia de entrada (Ω)':'zin',
                                    'Longitud eléctrica (rad)':'electrical','Longitud de onda (m)':'wavelength',
                                    'Onda estacionaria de tensión':'standing'})
                    channels=[(f'{number(net.frequencies_hz[index])} Hz',index)
                              for index in sorted({0,len(net.frequencies_hz)//2,len(net.frequencies_hz)-1})]
                    center=len(net.frequencies_hz)//2
                    rows.extend((('Frecuencia de lectura (Hz)',_display(net.frequencies_hz[center])),
                                 ('Velocidad de fase (m/s)',_display(natural.phase_velocity_m_s[center])),
                                 ('Atenuación (Np/m)',_display(natural.propagation_per_m[center].real)),
                                 ('Constante de fase (rad/m)',_display(natural.propagation_per_m[center].imag))))
            else:
                metrics=natural if op=='analyze' else self.measurements
                if metrics is not None:
                    options={'Módulo de S (dB)':'db','Módulo de S':'magnitude','Fase de S (rad)':'phase',
                             'Retardo de grupo (s)':'delay','Pérdida de retorno (dB)':'return',
                             'Pérdida de inserción (dB)':'insertion','Aislamiento (dB)':'isolation',
                             'VSWR':'vswr','Carta de Smith Z':'impedance','Carta de Smith Y':'admittance'}
                    rows.extend((('Pasiva en la rejilla','Sí' if metrics.passive.all() else 'No'),
                                 ('Recíproca en la rejilla','Sí' if metrics.reciprocal.all() else 'No')))
                options['Partes real e imaginaria · '+net.representation]='complex'
                channels=[(f'{out+1},{inp+1} · {out_name} ← {in_name}',(out,inp))
                          for inp,in_name in enumerate(net.port_names) for out,out_name in enumerate(net.port_names)]
        elif op=='link':
            options={'Potencia por etapa (dBm)':'ledger'}
        elif op=='matching_sweep':
            rows.append(('Valores evaluados',str(natural.values.size)))
            rows.append(('Frecuencias por valor',str(natural.frequencies_hz.size)))
            for value,gamma in zip(natural.values,natural.reflection,strict=True):
                rows.append((f'{number(value)} · mayor |Γ|',_display(np.max(np.abs(gamma)))))
            options={'Mayor reflexión en banda':'matching_sweep'}
        elif op=='noise_sweep':
            rows.extend((f'{number(fig)} dB · sensibilidad',_display(noise.sensitivity_dbm)+' dBm')
                        for fig,noise in zip(natural['figures_db'],natural['noise'],strict=True))
            options={'Sensibilidad frente a figura de ruido':'noise_sweep'}
        elif op=='link_campaign':
            report=natural.report
            rows.extend((('Réplicas utilizadas',str(report['replicas'])),
                         ('Semilla',str(natural.spec.seed)),('Configuración',natural.fingerprint)))
            for result in report['summaries']:
                interval=result['interval']
                rows.append((result['scenario'],_display(result['value'])))
                if interval is not None:rows.append(('Intervalo',f'[{_display(interval[0])}, {_display(interval[1])}]'))
            options={'Convergencia por réplica':'campaign'}
        elif result.signal is not None:
            options={'Módulo':'signal','Partes real e imaginaria':'complex'}
            if op=='czt':options['Contorno en el plano z']='contour'
            if op=='zoom':
                unit=result.signal.units
                rows.extend((('Paso de rejilla',f'{number(natural.grid_step)} {unit}'),
                             ('Separación nominal DFT',f'{number(natural.nominal_dft_spacing)} {unit}'),
                             ('Duración del registro (s)',_display(natural.duration_s))))
                for index,peak in enumerate(natural.peaks,1):
                    rows.append((f'Pico {index}',f'{number(peak.refined_frequency)} {unit} · amplitud {_display(peak.amplitude)} · fase {_display(peak.phase_rad)} rad'))
        notes=[]
        if op=='zoom':notes.append('Más puntos densifican la rejilla. La duración y la ventana determinan qué componentes pueden separarse.')
        if op=='device':notes.append('Modelo cúbico para tonos no coincidentes. El cálculo se limita a 1 dB de compresión de la fundamental.')
        if op=='match':notes.append('Los elementos se mantienen fijos en toda la banda. La adaptación se sintetiza a una frecuencia.')
        self.report.set_readable(Summary(self.mode.currentText(),[Section('Resultados',rows=rows,paragraphs=notes)]))
        for control,data in ((self.figure_choice,list(options.items())),(self.channel,channels)):
            control.blockSignals(True)
            control.clear()
            for label,value in data:control.addItem(label,value)
            control.setVisible(bool(data))
            control.blockSignals(False)
        self.tabs.setTabVisible(self.graph_tab,bool(options))
        self.draw()

    def _reuse(self):
        from .workspaces import ROUTES
        if self.active_result.signal is not None:
            self.window.send_signal(self.active_result.signal,self.active_record,ROUTES[('course_tools','band')])
            return
        if self.active_result.network is None:
            return
        _,current=self._selected_network()
        self.window.send_rf_network(current)

    def _selected_network(self):
        if self.active_result.request.operation=='match':
            index=self.channel.currentData() or 0
            network=self.active_result.data['responses'][index].network
            return network,[self.active_record,*self.alternate_records][index]
        return self.active_result.network,self.active_record

    def _export(self):
        filename,_=QFileDialog.getSaveFileName(self,'Guardar red Touchstone','','Touchstone 2.0 (*.ts)')
        if filename:
            net,_=self._selected_network()
            try:
                write_touchstone(filename,net)
            except (ValueError,OSError) as exc:
                show_input_error(self,'No se pudo exportar la red',exc)

    def draw(self,*_):
        self.figure.clear()
        self._smith=None
        mode=self.figure_choice.currentData()
        self.canvas._signallab_has_plot_result=bool(mode and self.active_result)
        if mode and self.active_result:
            self._draw_axis(self.figure.add_subplot(111),mode)
        self.canvas.draw_idle()
        refresh=getattr(self.canvas,'_signallab_plot_action_refresh',None)
        if refresh:refresh()

    def _draw_axis(self,axis,mode):
        result=self.active_result
        data=result.data
        op=result.request.operation
        channel=self.channel.currentData()
        if result.network is not None:
            self._draw_network(axis,mode,channel,result,data)
        elif mode=='ledger':
            labels,_,powers=zip(*data.ledger,strict=True)
            axis.bar(range(len(labels)),powers)
            axis.set_xticks(range(len(labels)),labels,rotation=28,ha='right')
            axis.set_ylabel('Potencia (dBm)')
        elif mode=='matching_sweep':
            VisibleCurve(axis,data.values,np.max(np.abs(data.reflection),axis=1),label='Mayor |Γ|')
            axis.set(xlabel=self.editors['parameter'].currentText(),ylabel='Mayor |Γ| en la banda')
        elif mode=='noise_sweep':
            VisibleCurve(axis,data['figures_db'],[row.sensitivity_dbm for row in data['noise']],label='Sensibilidad')
            axis.set(xlabel='Figura de ruido (dB)',ylabel='Sensibilidad (dBm)')
        elif mode=='campaign':
            from .monte_carlo import campaign_trajectory
            replicas,trajectory=campaign_trajectory(data)
            for scenario,values in zip(data.spec.scenarios,trajectory.T,strict=True):
                VisibleCurve(axis,replicas,values,label=scenario.name)
            axis.set(xlabel='Réplicas',ylabel='Margen (dB)' if data.spec.metric=='mean' else 'Probabilidad')
        elif mode=='contour':
            VisibleCurve(axis,data.z.real,data.z.imag,label='z[k]')
            axis.set(xlabel='Parte real',ylabel='Parte imaginaria',aspect='equal')
        else:
            signal=result.signal
            coords=signal.axis
            if mode=='complex':
                VisibleCurve(axis,coords,signal.values.real,label='Parte real')
                VisibleCurve(axis,coords,signal.values.imag,label='Parte imaginaria')
                axis.legend()
            else:
                VisibleCurve(axis,coords,np.abs(signal.values),label='Módulo')
                if op=='zoom' and data.dft_bins is not None and data.dft_bins.size:
                    from .visible_curve import VisibleStem
                    VisibleStem(axis,data.dft_bins,np.abs(data.dft_values),label='DFT del mismo registro')
                    axis.legend()
                if op=='zoom' and data.peaks:
                    positions=[row.refined_frequency for row in data.peaks]
                    axis.scatter(positions,np.interp(positions,coords,np.abs(signal.values)),marker='x',zorder=4)
            axis.set_xlabel(f'Frecuencia ({signal.units})' if op=='zoom' else 'Índice k del contorno')
        axis.grid(alpha=.15)

    def _draw_network(self,axis,mode,channel,result,data):
        hz=result.network.frequencies_hz
        op=result.request.operation
        if op in ('line','rlgc','match'):
            selected=data['responses'][channel or 0] if op=='match' else data
            gamma=selected.reflection if op=='match' else selected.input_reference_reflection
            if mode=='standing':
                distance=np.linspace(0,selected.length_m,401)
                voltage,_=selected.standing_waves(channel or 0,distance)
                VisibleCurve(axis,distance,voltage,label='Tensión normalizada')
                axis.set(xlabel='Distancia a la carga (m)',ylabel='|V| / |V incidente al inicio|')
                return
            with np.errstate(divide='ignore'):
                values={'reflection':20*np.log10(np.abs(gamma)),
                        'vswr':selected.vswr if op=='match' else selected.input_reference_vswr,
                        'loss':getattr(selected,'intrinsic_loss_db',None),
                        'zin':np.abs(selected.input_impedance_ohm),
                        'electrical':getattr(selected,'phase_rad',None),
                        'wavelength':getattr(selected,'wavelength_m',None),
                        'power':100*selected.delivered_power_fraction if op=='match' else None}
        else:
            metrics=data if op=='analyze' else self.measurements
            i,j=channel if channel is not None else (0,0)
            values={'complex':result.network.values[:,i,j]}
            if metrics is not None:
                gamma=metrics.reflection[:,j]
                values.update({label:field[:,i,j] for label,field in (
                    ('db',metrics.magnitude_db),('magnitude',metrics.magnitude),
                    ('phase',metrics.phase_rad),('delay',metrics.group_delay_s),
                    ('insertion',metrics.insertion_loss_db),('isolation',metrics.isolation_db))})
                values.update(vswr=metrics.vswr[:,j],return_=metrics.return_loss_db[:,j])
                values['return']=values.pop('return_')
        if mode in ('impedance','admittance'):
            grid=smith_grid(mode)
            for collection in (grid['constant_real'],grid['constant_imaginary']):
                for _,curve in collection:
                    axis.plot(curve.real,curve.imag,color='0.55',lw=.6,alpha=.55)
            axis.plot(grid['real_axis'],np.zeros(len(grid['real_axis'])),color='0.55',lw=.7)
            axis.plot(gamma.real,gamma.imag,marker='.' if len(gamma)==1 else None,lw=1.6)
            axis.plot(0,0,marker='+',color='0.6')
            axis.set(xlabel='Re Γ',ylabel='Im Γ',aspect='equal',title='Carta de Smith · '+('impedancia' if mode=='impedance' else 'admitancia'))
            self._smith=(axis,hz,gamma,None)
        elif mode=='complex':
            VisibleCurve(axis,hz,values[mode].real,label='Parte real')
            VisibleCurve(axis,hz,values[mode].imag,label='Parte imaginaria')
            axis.legend()
        else:
            ordinate=np.asarray(values[mode])
            finite=ordinate[np.isfinite(ordinate)]
            label=self.figure_choice.currentText()
            if mode in ('db','reflection','return','insertion','isolation') and np.any(np.isinf(ordinate)):
                lower=min(-120.,float(finite.min())-12) if finite.size else -120.
                upper=max(0.,float(finite.max())+12) if finite.size else 120.
                visible=np.where(np.isneginf(ordinate),lower,np.where(np.isposinf(ordinate),upper,ordinate))
                VisibleCurve(axis,hz,visible,label=label)
                axis.text(.02,.04,'Los límites ±∞ se muestran en los bordes de la escala.',
                          transform=axis.transAxes,fontsize=8)
            elif finite.size:
                VisibleCurve(axis,hz,np.where(np.isfinite(ordinate),ordinate,np.nan),label=label)
            else:
                axis.text(.5,.5,'La magnitud no tiene valores finitos en esta rejilla.',
                          transform=axis.transAxes,ha='center',wrap=True)
            axis.set_ylabel(self.figure_choice.currentText())
        if mode not in ('impedance','admittance'):
            axis.set_xlabel('Frecuencia (Hz)')

    def _mark_smith(self,event):
        if self._smith is None or event.inaxes is not self._smith[0] or event.button!=1 or event.xdata is None:
            return
        axis,hz,gamma,previous=self._smith
        if event.ydata is None:
            return
        index=int(np.argmin(np.abs(gamma-complex(event.xdata,event.ydata))))
        point=gamma[index]
        z,y=smith_values(point)
        if previous is not None:previous.remove()
        mark=axis.annotate(f'{number(hz[index])} Hz\nz = {complex(z):.4g}\ny = {complex(y):.4g}',(point.real,point.imag),
                           xytext=(10,10),textcoords='offset points',arrowprops={'arrowstyle':'->'})
        self._smith=(axis,hz,gamma,mark)
        self.canvas.draw_idle()
