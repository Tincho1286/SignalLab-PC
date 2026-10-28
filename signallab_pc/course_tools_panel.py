from .numeric_input import real_field,integer_field,constant_value
"""Paneles independientes para diseño y análisis, sin datos de ejercicios precargados."""
import numpy as np
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QLineEdit,QComboBox,QPushButton,QLabel,QScrollArea,QMessageBox,QTabWidget,QCheckBox
from .tool_guide import ToolGuide
from .band_edges import BandEdgesEditor
from .coefficient_editor import CoefficientEditor,TransferPreview
from .systems_panel import parse_list,list_text
from .filters import Transfer
from .engine import evaluate_expression
from .report_view import ReportView,report_panel
from .transfer_report import TransferResultReport
from .navigation import MENUS
from . import course_tools as calc

TITLES={'lines':'Potencia periódica y líneas espectrales','mapping':'Mapeo de frecuencias','fft':'Ventanas y FFT','fir':'FIR por especificaciones','iir':'IIR por especificaciones','convert':'Conversión de sistemas','gain':'Normalización de ganancia','phase':'Fase y compensación','inverse_z':'Z inversa con región de convergencia','band':'Energía por banda'}
GUIDES={'lines':'Ingresá o copiá coeficientes de serie continua para calcular potencia y pesos de líneas espectrales.','mapping':'Relacioná frecuencia continua, frecuencia discreta y período de transformación.',
'fft':'Elegí el registro observado, la ventana y NFFT por separado. Compará la FFT, la DTFT y las señales intermedias.',
'fir':'Elegí el tipo de filtro y seguí las frecuencias numeradas del dibujo. Luego indicá cuánto puede variar el paso y cuánto puede quedar en el rechazo.',
'iir':'Elegí una familia y definí bandas y tolerancias. Compará orden, fase y respuesta temporal; los resultados se pueden reutilizar.',
'convert':'Convertí una transferencia usando bilineal, bilineal inversa o invarianza al impulso.',
'gain':'Ajustá el módulo del sistema en una frecuencia angular sin cambiar sus polos y ceros.',
'phase':'Reflejá ceros exteriores y separá un factor paso todo. Identificá simetría y retardo en FIR reales.',
'inverse_z':'Elegí la región de convergencia mediante un contorno y aproximá muestras de una secuencia bilateral.',
'band':'Integrá |X(ω)|²/(2π) en una banda explícita del espectro disponible.'}

TITLES['bandpass_sampling']='Tasas de muestreo pasabanda'
GUIDES['bandpass_sampling']='Definí la banda positiva de una señal real y consultá las tasas que evitan solapamiento.'

TITLES['analog']='Filtro analógico por especificaciones'
GUIDES['analog']='Definí bandas en rad/s y tolerancias de amplitud. Diseñá una familia o compará las cuatro con los mismos requisitos.'

class CourseToolsPanel(QWidget):
    def __init__(self,window,action):
        super().__init__();self.window=window;self.action=action;self.parent_id=None;self.items=[];self.fields={};self.records=[];self.specifications=None
        from .toolbox import LocalInput,ResultView
        root=QHBoxLayout(self);controls=QWidget();form=QFormLayout(controls);form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows);self.form=form
        if action=='phase':form.setProperty('stackFields',True);form.setContentsMargins(6,9,6,9)
        form.addRow(ToolGuide(GUIDES[action],('Definición','Parámetros','Resultado')))
        if action in ('fft','band','lines'):
            self.source=LocalInput('Entrada local','frequency' if action=='band' else 'discrete');self.source.bind_project(window);form.addRow(self.source)
            if action=='lines':self.source.setTitle('Coeficientes de serie continua c[k]');self.source.set_role('series_coefficients')
        if action in ('convert','gain','phase','inverse_z'):
            self.domain=QComboBox();self.domain.addItems(['Continuo · H(s)','Discreto · H(z)']);form.addRow('Dominio',self.domain)
            self.b=CoefficientEditor('1');self.a=CoefficientEditor('1, -0.5' if action in ('phase','inverse_z') else '1, 1');self.preview=TransferPreview(self.b,self.a);form.addRow(self.preview);form.addRow('Numerador',self.b);form.addRow('Denominador',self.a)
            button=QPushButton('Copiar un sistema anterior…');self.copy_system_button=button;button.clicked.connect(self.choose_system);form.addRow(button)
            self.domain.currentIndexChanged.connect(self.change_domain)
            if action in ('phase','inverse_z'):self.domain.setCurrentIndex(1);form.setRowVisible(self.domain,False)
            self.change_domain()
        def field(key,label,value):
            edit=QLineEdit(value);self._last_field=edit;self.fields[key]=edit;form.addRow(label,edit);return edit
        def choice(key,label,values):
            combo=QComboBox();self.fields[key]=combo
            for title,data in values:combo.addItem(title,data)
            form.addRow(label,combo);return combo
        if action=='fft':
            field('length','Longitud observada L (0 = toda la entrada)','0');field('nfft','Cantidad de puntos de FFT','1024')
            choice('window','Ventana simétrica',[(s,v) for s,v in [('Rectangular','boxcar'),('Hann','hann'),('Hamming','hamming'),('Blackman','blackman'),('Bartlett','bartlett'),('Kaiser','kaiser')]])
            field('beta','β de Kaiser','5');field('points','Frecuencias para DTFT','2049')
            self.fields['window'].currentIndexChanged.connect(lambda *_:form.setRowVisible(self.fields['beta'],self.fields['window'].currentData()=='kaiser'));form.setRowVisible(self.fields['beta'],False)
        elif action in ('fir','iir','analog'):
            self.band_edges=BandEdgesEditor(analog=action=="analog");self.fields['band_edges']=self.band_edges;form.addRow(self.band_edges)
            def hint(text):
                self._last_field.setToolTip(text)
            field('dp','Variación permitida en paso δp (amplitud)','0.05')
            hint('Ingresá un valor entre 0 y 1. Ejemplo: 0.05 permite un módulo entre 0.95 y '+('1.05.' if action=='fir' else '1.')+' No se ingresa en dB ni como porcentaje.')
            field('ds','Máximo permitido en rechazo δs (amplitud)','0.01')
            hint('Ingresá un valor entre 0 y 1. Ejemplo: 0.01 permite como máximo el 1 % de amplitud (−40 dB). Un valor menor exige más rechazo.')
            if action=='fir':
                choice('window','Ventana',[(name,name) for name in ('kaiser','boxcar','hann','hamming','blackman','bartlett')]);field('taps','Cantidad de coeficientes (0 = estimar Kaiser)','0');field('search','Buscar menor longitud hasta (0 = sin búsqueda)','0')
                hint('Coeficientes: 51 significa orden 50. Cero estima con Kaiser. Buscar hasta: cero desactiva la búsqueda; otro entero fija la mayor longitud a probar con la ventana elegida.')
            else:
                choice('method','Método',[('Butterworth digital','butter'),('Chebyshev I digital','cheby1'),('Chebyshev II digital','cheby2'),('Elíptico (Cauer) digital','ellip'),('Comparar las cuatro familias digitales','compare'),('Butterworth + bilineal con predeformación','bilinear'),('Butterworth + invarianza al impulso','impulse')]);field('period','T de la transformación (s)','1')
                if action=='analog':
                    self.fields['method'].clear()
                    for title,value in [('Butterworth analógico','butter'),('Chebyshev I analógico','cheby1'),('Chebyshev II analógico','cheby2'),('Elíptico analógico','ellip'),('Comparar familias analógicas','compare')]:self.fields['method'].addItem(title,value)
                self.fields['method'].currentIndexChanged.connect(lambda *_:form.setRowVisible(self.fields['period'],self.fields['method'].currentData() in ('bilinear','impulse')));form.setRowVisible(self.fields['period'],False)
                self.family_note=QLabel();self.family_note.setWordWrap(True);form.addRow(self.family_note)
                def explain_family(*_):
                    descriptions={'compare':'Calcula las cuatro familias digitales con los mismos bordes y tolerancias. Cada filtro queda disponible por separado.', 'butter':'Butterworth: módulo plano en paso, sin ondulación.',
                        'cheby1':'Chebyshev I: ondulación en paso y rechazo monótono.',
                        'cheby2':'Chebyshev II: paso monótono y ondulación en rechazo.',
                        'ellip':'Elíptico: ondulación en ambas bandas. Compará también la fase y la respuesta temporal.',
                        'bilinear':'Prototipo Butterworth con bordes predeformados; conserva el prototipo analógico.',
                        'impulse':'Prototipo Butterworth por invarianza al impulso; el aliasing puede alterar las tolerancias digitales.'}
                    self.family_note.setText(descriptions[self.fields['method'].currentData()].replace('digitales','analógicas' if action=='analog' else 'digitales')+' En IIR, la banda de paso se diseña entre 1−δp y 1.')
                self.fields['method'].currentIndexChanged.connect(explain_family);explain_family()

        elif action=='bandpass_sampling':
            field('low','Borde inferior ΩL (rad/s)','');field('high','Borde superior ΩH (rad/s)','')
            field('candidate','Ωs a consultar (rad/s; opcional)','')
            note=QLabel('Ωs = 2π Fs. Dejá la tasa vacía para obtener sólo los intervalos admisibles.');note.setWordWrap(True);form.addRow(note)
        elif action=='convert':
            choice('method','Transformación',[('Invarianza al impulso','impulse'),('Bilineal','bilinear'),('Bilineal inversa','inverse'),('Inversa de invarianza: candidatos','impulse_inverse')]);field('period','Período T (s)','1')
            field('analog_cutoffs','Cortes de referencia Ωc (rad/s; opcional)','')
            self.fields['analog_cutoffs'].setToolTip('Uno o varios cortes analógicos separados por coma. Admite pi y potencias decimales. Sólo se usan para mostrar el mapeo; no modifican el filtro. Vacío busca cruces de media potencia respecto del máximo evaluado.')
            self.fields['method'].currentIndexChanged.connect(lambda *_:self.domain.setCurrentIndex(1 if self.fields['method'].currentData() in ('inverse','impulse_inverse') else 0))
            choice('definition','Definir filtro como',[('Transferencia H(s) o H(z), por coeficientes','rational'),('Respuesta analógica ideal / por tramos','response')])
            taken=form.takeRow(self.fields['definition']);form.insertRow(0,taken.labelItem.widget(),self.fields['definition'])
            from .expression_editor import ExpressionEditor
            self.ideal_expression=ExpressionEditor('where(abs(w)<=1,1,0)');self.ideal_expression.mode.setCurrentIndex(1)
            self.fields['ideal_expression']=self.ideal_expression;form.addRow('Ha(jΩ): w representa Ω en rad/s',self.ideal_expression)
            choice('ideal_method','Conversión de la respuesta',[('Bilineal: Ω = (2/T) tan(ω/2)','bilinear'),('Invarianza al impulso, soporte finito','impulse')])
            field('ideal_support','Ωmáx (rad/s); fuera de ±Ωmáx, Ha = 0','1')
            field('ideal_points','Puntos de la respuesta digital','2049')
            field('ideal_length','Longitud del FIR (impar)','65')
            choice('ideal_window','Ventana del FIR',[('Hamming','hamming'),('Hann','hann'),('Blackman','blackman'),('Kaiser','kaiser'),('Rectangular','boxcar')])
            field('ideal_beta','β de la ventana Kaiser','5')
            self.ideal_note=QLabel('Se obtiene un FIR aproximado aplicando una ventana a la respuesta al impulso. También se conserva H ideal para comparar. La ventana modifica la respuesta y el desplazamiento causal agrega retardo.');self.ideal_note.setWordWrap(True);form.addRow(self.ideal_note)
            def update_definition(*_):
                ideal=self.fields['definition'].currentData()=='response'
                for widget in (self.domain,self.b,self.a,self.preview,self.copy_system_button,self.fields['method']):form.setRowVisible(widget,not ideal)
                for widget in (self.ideal_expression,self.fields['ideal_method'],self.fields['ideal_points'],self.fields['ideal_length'],self.fields['ideal_window'],self.ideal_note):form.setRowVisible(widget,ideal)
                form.setRowVisible(self.fields['ideal_beta'],ideal and self.fields['ideal_window'].currentData()=='kaiser')
                form.setRowVisible(self.fields['ideal_support'],ideal and self.fields['ideal_method'].currentData()=='impulse')
            self.fields['definition'].currentIndexChanged.connect(update_definition);self.fields['ideal_method'].currentIndexChanged.connect(update_definition);self.fields['ideal_window'].currentIndexChanged.connect(update_definition);update_definition()
            def reference_visibility(*_):form.setRowVisible(self.fields['analog_cutoffs'],self.fields['definition'].currentData()=='response' or self.fields['method'].currentData() in ('bilinear','impulse'))
            self.fields['definition'].currentIndexChanged.connect(reference_visibility);self.fields['method'].currentIndexChanged.connect(reference_visibility);reference_visibility()

        elif action=='phase':
            choice('phase_mode','Estudio',[('Fase mínima y paso todo','factor'),('Compensar módulo y fase · FIR','compensate'),('Reconstruir módulo y fase','reconstruct')])
            from .reconstruction_controls import ReconstructionControls
            self.reconstruction_controls=ReconstructionControls(window);form.addRow(self.reconstruction_controls)
            field('eq_low','Banda · desde (rad/muestra)','0');field('eq_high','Banda · hasta (rad/muestra)','pi')
            field('eq_taps','Coeficientes del compensador FIR','31');field('eq_delay','Retardo objetivo (muestras)','15')
            field('eq_gain','Ganancia objetivo de H·C','1');field('eq_reg','Regularización λ (0 = sin penalización)','0.0001')
            self.eq_note=QLabel('Se aproxima H·C a una ganancia con retardo dentro de la banda. Más regularización limita coeficientes grandes a costa del ajuste. El informe muestra el error obtenido.');self.eq_note.setWordWrap(True);form.addRow(self.eq_note)
            def eq_fields(*_):
                enabled=self.fields['phase_mode'].currentData()=='compensate'
                self.reconstruction_controls.setVisible(self.fields['phase_mode'].currentData()=='reconstruct')
                for key in ('eq_low','eq_high','eq_taps','eq_delay','eq_gain','eq_reg'):form.setRowVisible(self.fields[key],enabled)
                self.eq_note.setVisible(enabled)
            self.fields['phase_mode'].currentIndexChanged.connect(eq_fields);eq_fields()
        elif action=='gain':field('omega','Frecuencia angular (rad/s o rad/muestra)','0');field('target','Módulo objetivo','1')
        elif action=='inverse_z':
            choice('roc','Elección de región',[('Exterior a todos los polos','causal'),('Interior a todos los polos','anticausal'),('Incluye círculo unidad (estable)','stable'),('Radio especificado por mí','manual')]);field('radius','Radio del contorno','1');field('start','Índice inicial','-32');field('count','Cantidad de muestras','65');field('points','Puntos del contorno','8192')
            self.fields['roc'].currentIndexChanged.connect(lambda *_:form.setRowVisible(self.fields['radius'],self.fields['roc'].currentData()=='manual'));form.setRowVisible(self.fields['radius'],False)
        elif action=='lines':field('period','Período T (s); se conserva el del resultado importado','1')
        elif action=='mapping':
            choice('method','Mapeo',[('Bilineal','bilinear'),('Muestreo / invarianza al impulso','impulse')]);choice('direction','Obtener',[('Frecuencia continua Ω','to_analog'),('Frecuencia discreta ω','to_digital'),('Período T','period')])
            field('omega','ω (rad/muestra)','pi/4');field('analog','Ω (rad/s)','10');field('period','T (s)','0.1');field('branch','Rama entera k','0')
            def mapping_fields(*_):
                direction=self.fields['direction'].currentData();form.setRowVisible(self.fields['omega'],direction!='to_digital');form.setRowVisible(self.fields['analog'],direction!='to_analog');form.setRowVisible(self.fields['period'],direction!='period');form.setRowVisible(self.fields['branch'],self.fields['method'].currentData()=='impulse' and direction!='to_digital')
            self.fields['method'].currentIndexChanged.connect(mapping_fields);self.fields['direction'].currentIndexChanged.connect(mapping_fields);mapping_fields()
        elif action=='band':field('low','Frecuencia inferior','-1');field('high','Frecuencia superior','1')
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);left=QWidget();box=QVBoxLayout(left);box.addWidget(scroll,1)
        button=QPushButton('Calcular');self.calculate_button=button;button.setObjectName('primary');button.clicked.connect(self.calculate);box.addWidget(button);root.addWidget(left,1)
        right=QWidget();out=QVBoxLayout(right);self.selector=QComboBox();self.selector.hide();self.selector.currentIndexChanged.connect(self.display);result_options=QHBoxLayout();result_options.addWidget(self.selector,1);out.addLayout(result_options)
        self.view=ResultView();self.view.layout().setContentsMargins(0,0,0,0);self.tabs=self.view.views;self.report=TransferResultReport() if action=='phase' else ReportView();self.tabs.removeTab(1);self.tabs.insertTab(1,report_panel(self.report),"Informe");out.addWidget(self.view,1)
        self.system_view=QComboBox();self.system_view.addItems(['Módulo, fase y retardo','Módulo (dB)','Retardo de grupo','Módulo |H| · amplitud']);self.system_view.setAccessibleName('Vista de la respuesta del sistema');self.system_view.hide();result_options.addWidget(self.system_view,1);self.system_view.currentIndexChanged.connect(self.display)
        self.conversion_info=None
        if action=='convert':
            self.system_view.blockSignals(True);self.system_view.clear();self.system_view.addItems(['Módulo, fase y retardo','Sólo módulo','Retardo de grupo']);self.system_view.blockSignals(False)
            self.magnitude_scale=QComboBox();self.magnitude_scale.addItems(['|H| · lineal','Módulo · dB']);self.magnitude_scale.setAccessibleName('Escala del módulo');self.magnitude_scale.currentIndexChanged.connect(self.display);result_options.addWidget(self.magnitude_scale)
            from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
            toolbar=self.view.findChild(NavigationToolbar2QT)
            if toolbar is not None:
                toolbar.addSeparator();toolbar.addWidget(QLabel('Módulo:'))
                self.figure_magnitude=QComboBox(toolbar);self.figure_magnitude.addItems(['Lineal |H|','dB']);self.figure_magnitude.setAccessibleName('Escala del módulo del gráfico');toolbar.addWidget(self.figure_magnitude)
                self.figure_magnitude.currentIndexChanged.connect(self.magnitude_scale.setCurrentIndex);self.magnitude_scale.currentIndexChanged.connect(self.figure_magnitude.setCurrentIndex)
        self.comparing_systems=False
        self.show_all_systems=QCheckBox('Superponer familias · exportar y reutilizar usa el filtro seleccionado');self.show_all_systems.setChecked(True);self.show_all_systems.hide();out.insertWidget(1,self.show_all_systems);self.show_all_systems.toggled.connect(self.display)
        self.reference_spectrum=None
        if action=='fft':
            comparison=QWidget();self.comparison_controls=comparison;comparison.hide();row=QVBoxLayout(comparison);row.setContentsMargins(0,0,0,0)
            buttons=QHBoxLayout();self.overlay_enabled=QCheckBox('Superponer DFT y DTFT');self.overlay_enabled.setChecked(True);buttons.addWidget(self.overlay_enabled)
            self.pin_button=QPushButton('Conservar curva de referencia');self.pin_button.setEnabled(False);buttons.addWidget(self.pin_button)
            self.clear_reference=QPushButton('Quitar referencia');self.clear_reference.setEnabled(False);buttons.addWidget(self.clear_reference);row.addLayout(buttons)
            self.comparison_note=QLabel('La DFT se muestra con tallos; la DTFT, como curva.');self.comparison_note.setWordWrap(True);row.addWidget(self.comparison_note);out.insertWidget(1,comparison)
            self.overlay_enabled.toggled.connect(self.redraw_comparison);self.pin_button.clicked.connect(self.pin_spectrum);self.clear_reference.clicked.connect(self.remove_reference)
            self.view.plot_mode.currentIndexChanged.connect(self.draw_comparison)
        from .system_result_actions import SystemResultActions
        self.system_actions=SystemResultActions(window);self.system_actions.hide();out.addWidget(self.system_actions);root.addWidget(right,2)
        self.compensation_data=None;self.reconstruction_data=None
        if action=='phase':
            self.compensation_export=QPushButton('Exportar comparación CSV…');self.compensation_export.hide();self.compensation_export.clicked.connect(self.export_compensation);out.addWidget(self.compensation_export)
        self.bandpass_result=None
        if hasattr(self,'copy_system_button'):
            from .system_import import install_system_import
            self.system_import=install_system_import(self.copy_system_button,window,self.set_system,self.choose_system,domains=['digital'] if action in ('phase','inverse_z') else None,allow_advance=action in ('gain','inverse_z'))
        if action=='bandpass_sampling':
            self.export_bands_button=QPushButton('Exportar intervalos CSV…');self.export_bands_button.setEnabled(False);self.export_bands_button.hide();self.export_bands_button.clicked.connect(self.export_sampling_bands);out.addWidget(self.export_bands_button)
            self.use_rate_button=QPushButton('Usar tasa en Muestrear una expresión');self.use_rate_button.setEnabled(False);self.use_rate_button.hide();self.use_rate_button.clicked.connect(self.use_sampling_rate);out.addWidget(self.use_rate_button)
            for control in (self.view.label,self.view.send,self.view.save,self.view.plot_mode):control.hide()
            self.tabs.setTabVisible(self.view.table_index,False)
        from .result_state import ResultState
        if hasattr(self,'b'):
            from .transfer_input import install_formula_editor
            install_formula_editor(self,form)
        if action=='phase':
            def phase_definition(*_):
                reconstruct=self.fields['phase_mode'].currentData()=='reconstruct';formula=self.definition_mode.currentIndex()==1
                for widget in (self.definition_buttons,self.copy_system_button):form.setRowVisible(widget,not reconstruct)
                form.setRowVisible(self.transfer_formula,not reconstruct and formula)
                for widget in (self.b,self.a,self.preview):form.setRowVisible(widget,not reconstruct and not formula)
                form.setRowVisible(self.domain,False)
            self.fields['phase_mode'].currentIndexChanged.connect(phase_definition);self.definition_mode.currentIndexChanged.connect(phase_definition);phase_definition()
        editors=list(self.fields.values())+([self.domain,self.b,self.a,self.definition_mode,self.transfer_formula] if hasattr(self,'b') else [])
        if action=='phase':editors+=self.reconstruction_controls.editors
        sources=([self.source] if hasattr(self,'source') else [])+([self.reconstruction_controls.source] if action=='phase' else [])
        self.result_state=ResultState(editors,self.calculate_button,sources)
        out.insertWidget(0,self.result_state)
    def change_domain(self,*_):
        digital=self.domain.currentIndex()==1;self.b.set_domain(digital);self.a.set_domain(digital);self.preview.schedule()
    def choose_system(self):
        key=self.window.choose_record('system')
        if not key:return
        self.set_system(self.window.project.get(key),key)
    def set_system(self,value,key=None):
        if self.action=='phase' and self.fields['phase_mode'].currentData()=='reconstruct':self.fields['phase_mode'].setCurrentIndex(0)
        if self.action in ('phase','inverse_z') and value.domain!='digital':QMessageBox.warning(self,'Dominio incompatible','Esta herramienta requiere un sistema discreto.');return
        if self.action=='convert':
            self.fields['definition'].setCurrentIndex(0);self.fields['method'].setCurrentIndex(2 if value.domain=='digital' else 0)
        self.domain.setCurrentIndex(1 if value.domain=='digital' else 0);self.b.setText(list_text(value.b));self.a.setText(list_text(value.a));self.parent_id=key
        from .transfer_input import remember_system
        remember_system(self,value)
    def scalar(self,key):return real_field(self.fields[key])
    def integer(self,key):return integer_field(self.fields[key])
    def vector(self,key):
        result=[]
        for term in self.fields[key].text().split(','):
            value=constant_value(term)
            if value.imag:raise ValueError('Los bordes deben ser reales.')
            result.append(value.real)
        return result
    def calculate(self):
        try:
            parents=[];action=self.action
            if hasattr(self,'source'):
                source=self.source.read();parents=[self.source.reference_id] if self.source.reference_id else []
            ideal_conversion=action=='convert' and self.fields['definition'].currentData()=='response'
            reconstructing=action=='phase' and self.fields['phase_mode'].currentData()=='reconstruct'
            if hasattr(self,'b') and not ideal_conversion and not reconstructing:
                from .transfer_input import read_system
                system=read_system(self,allow_advance=action in ('inverse_z','gain'))
                parents=[self.window.publish(system,operation='Definición local de '+TITLES[action],parents=[self.parent_id] if self.parent_id else [])]
            if action=='fft':
                args=(source,self.integer('length') or source.values.size,self.integer('nfft'),self.fields['window'].currentData(),self.scalar('beta') if self.fields['window'].currentData()=='kaiser' else 0,self.integer('points'));job=lambda:calc.window_fft(*args)
            elif action=='bandpass_sampling':
                from .bandpass_sampling import analyze
                args=(self.scalar('low'),self.scalar('high'),self.scalar('candidate') if self.fields['candidate'].text().strip() else None);job=lambda:analyze(*args)
            elif action=='analog':
                from .analog_design import design
                wp,ws=self.band_edges.bands();args=(wp,ws,self.scalar('dp'),self.scalar('ds'),self.fields['method'].currentData());job=lambda:design(*args)
            elif action in ('fir','iir'):
                wp,ws=self.band_edges.bands()
                args=(wp,ws,self.scalar('dp'),self.scalar('ds'),'kaiser' if action=='fir' else self.fields['method'].currentData(),self.scalar('period') if action=='iir' and self.fields['method'].currentData() in ('bilinear','impulse') else 1,self.integer('taps') if action=='fir' else 0,self.fields['window'].currentData() if action=='fir' else 'kaiser',self.integer('search') if action=='fir' else 0);job=lambda:calc.design_filter(*args)
                if action=='iir' and self.fields['method'].currentData()=='compare':job=lambda:calc.compare_iir(*args[:4])
            elif action=='convert':
                if ideal_conversion:
                    from .ideal_conversion import windowed_conversion
                    method=self.fields['ideal_method'].currentData()
                    args=(self.ideal_expression.text(),self.scalar('period'),method,self.integer('ideal_points'),self.scalar('ideal_support') if method=='impulse' else None)
                    window_args=(self.integer('ideal_length'),self.fields['ideal_window'].currentData(),self.scalar('ideal_beta') if self.fields['ideal_window'].currentData()=='kaiser' else 0)
                    job=lambda:windowed_conversion(*args,*window_args)
                else:
                    args=(system,self.scalar('period'),self.fields['method'].currentData());job=lambda:calc.convert_system(*args)
            elif action=='gain':
                args=(system,self.scalar('omega'),self.scalar('target'));job=lambda:calc.normalize_gain(*args)
            elif action=='phase':
                if reconstructing:
                    from .phase_reconstruction import reconstruct
                    source,kind,options=self.reconstruction_controls.request();parent=self.reconstruction_controls.source.reference_id;parents=[parent] if parent else [];system=None
                    job=lambda:reconstruct(source,kind,**options)
                elif self.fields['phase_mode'].currentData()=='factor':job=lambda:calc.phase_structure(system)
                else:
                    from .phase_compensation import design_compensator
                    args=(system,self.scalar('eq_low'),self.scalar('eq_high'),self.integer('eq_taps'),self.integer('eq_delay'),self.scalar('eq_gain'),self.scalar('eq_reg'));job=lambda:design_compensator(*args)
            elif action=='inverse_z':
                args=(system,self.fields['roc'].currentData(),self.scalar('radius') if self.fields['roc'].currentData()=='manual' else 1,self.integer('start'),self.integer('count'),self.integer('points'));job=lambda:calc.inverse_z_contour(*args)
            elif action=='lines':
                args=(source,self.scalar('period'));job=lambda:calc.periodic_lines(*args)
            elif action=='mapping':
                direction=self.fields['direction'].currentData();method=self.fields['method'].currentData()
                args=(self.scalar('omega') if direction!='to_digital' else 0,self.scalar('analog') if direction!='to_analog' else 0,self.scalar('period') if direction!='period' else 1,method,direction,self.integer('branch') if method=='impulse' and direction!='to_digital' else 0);job=lambda:calc.frequency_mapping(*args)
            else:
                args=(source,self.scalar('low'),self.scalar('high'));job=lambda:calc.band_energy(*args)
            if action=='convert':
                from .conversion_details import enrich_conversion
                conversion_job=job;conversion_method=self.fields['ideal_method' if ideal_conversion else 'method'].currentData();conversion_period=self.scalar('period')
                references=self.vector('analog_cutoffs') if conversion_method in ('bilinear','impulse') and self.fields['analog_cutoffs'].text().strip() else []
                conversion_source=None if ideal_conversion else system;conversion_expression=self.ideal_expression.text() if ideal_conversion else None
                job=lambda:enrich_conversion(conversion_job(),conversion_source,conversion_period,conversion_method,references,input_expression=conversion_expression)
            calculated_inputs=self.result_state.snapshot()
            def accept(result):
                self.view.show_content();self.view.actions.setVisible(bool(result['systems']+result['signals']))
                if hasattr(self,'comparison_controls'):self.comparison_controls.show()
                self.comparing_systems=result.get('comparison',False);self.show_all_systems.setVisible(self.comparing_systems)
                self.items=result['systems']+result['signals'];self.records=[];self.specifications=result.get('specifications')
                for value in self.items:self.records.append(self.window.publish(value,operation=TITLES[action],parents=parents))
                self.window.publish({'report':result['report'],'specifications':self.specifications},title=TITLES[action],operation='Informe de '+TITLES[action],parents=parents)
                if action=='phase':
                    self.phase_input=system;self.phase_report=result['report'];self._phase_report_value=None;self.compensation_data=result.get('compensation');self.reconstruction_data=result.get('reconstruction')
                    self.compensation_export.setText('Exportar reconstrucción CSV…' if self.reconstruction_data is not None else 'Exportar comparación CSV…');self.compensation_export.setVisible(self.compensation_data is not None or self.reconstruction_data is not None)
                    figure_window=getattr(self.view.canvas,'_signallab_window',None)
                    if figure_window is not None:figure_window.setWindowTitle(('Reconstrucción de módulo/fase' if self.reconstruction_data is not None else 'Compensación FIR' if self.compensation_data is not None else 'Fase mínima y paso todo')+' · SignalLab')
                    self.show_all_systems.setText('Comparar original, compensado y objetivo');self.show_all_systems.setToolTip('Las acciones de exportación y reutilización toman el sistema elegido en el selector, aunque la figura muestre las tres curvas.')
                    self.show_all_systems.setVisible(self.compensation_data is not None)
                self.conversion_info=result.get('conversion_details')
                if self.conversion_info is not None:
                    from .conversion_details import conversion_summary
                    self.report.set_readable(conversion_summary(self.conversion_info))
                else:self.report.setPlainText(result['report'])
                self.selector.blockSignals(True);self.selector.clear()
                for value in self.items:self.selector.addItem(value.name)
                self.selector.blockSignals(False);self.selector.setVisible(bool(self.items))
                self.tabs.setTabVisible(0,bool(self.items));self.tabs.setCurrentIndex(0 if self.items else 1)
                self.display();self.tabs.setCurrentIndex(1)
                if action=='bandpass_sampling':
                    self.bandpass_result=result['bandpass'];self.export_bands_button.show();self.use_rate_button.show();self.export_bands_button.setEnabled(True);self.draw_sampling_bands();self.use_rate_button.setEnabled(self.bandpass_result['status']=='Admisible con margen espectral')
                self.result_state.accept(calculated_inputs)
            self.window._run_operation('Calculando '+TITLES[action]+'…',job,accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá los datos',str(exc))
    def export_compensation(self):
        if self.reconstruction_data is None and self.compensation_data is None:return
        from PySide6.QtWidgets import QFileDialog
        from pathlib import Path
        path,_=QFileDialog.getSaveFileName(self,'Exportar comparación de compensación','comparacion_compensacion.csv','Tabla CSV (*.csv)')
        if not path:return
        if not Path(path).suffix:path+='.csv'
        try:
            if self.reconstruction_data is not None:
                from .phase_reconstruction import export_reconstruction
                export_reconstruction(self.reconstruction_data,path)
            else:
                from .phase_compensation import export_comparison
                export_comparison(self.compensation_data,path)
            self.window.statusBar().showMessage('Comparación del último cálculo exportada.')
        except Exception as exc:QMessageBox.warning(self,'No se pudo exportar',str(exc))
    def draw_reconstruction(self):
        from .phase_reconstruction import draw_reconstruction
        draw_reconstruction(self.reconstruction_data,self.view.figure,self.system_view.currentIndex());self.view.canvas.draw_idle()
    def use_sampling_rate(self):
        if self.bandpass_result is None or self.bandpass_result['status']!='Admisible con margen espectral':return
        route=next(item for item in MENUS['Muestreo'] if item[1:3]==('sampling',0))
        self.window.open_tool(route)
        self.window.pages[route].panel.rate.setText(format(self.bandpass_result['candidate']/(2*np.pi),'.17g'))
    def export_sampling_bands(self):
        if self.bandpass_result is None:return
        from PySide6.QtWidgets import QFileDialog
        from .bandpass_sampling import export_intervals
        path,_=QFileDialog.getSaveFileName(self,'Exportar intervalos','muestreo-pasabanda.csv','CSV (*.csv)')
        if path:
            try:export_intervals(path,self.bandpass_result)
            except Exception as exc:QMessageBox.warning(self,'No se pudo exportar',str(exc))
    def draw_sampling_bands(self):
        data=self.bandpass_result;figure=self.view.figure;figure.clear();axis=figure.subplots()
        count=min(len(data['m']),40);right=float(data['lower'][0]*1.15)
        for i in range(count):
            m=int(data['m'][i]);lo=data['lower'][i];hi=min(data['upper'][i],right)
            axis.plot([lo,hi],[m,m],color='#178775',linewidth=4,solid_capstyle='butt')
            axis.plot([lo],[m],'o',markerfacecolor='white',color='#178775',markersize=5)
            if np.isfinite(data['upper'][i]):axis.plot([hi],[m],'o',markerfacecolor='white',color='#178775',markersize=5)
            else:axis.annotate('',xy=(right,m),xytext=(lo,m),arrowprops=dict(arrowstyle='->',color='#178775'))
        candidate=data['candidate']
        if candidate is not None and candidate<=right:axis.axvline(candidate,color='#b27524',linestyle='--',label='Ωs consultada');axis.legend()
        axis.set(xlabel='Ωs · frecuencia angular de muestreo (rad/s)',ylabel='Zona m',xlim=(0,right),ylim=(count+.6,.4))
        axis.set_yticks(np.arange(1,count+1,max(1,count//12)))
        axis.set_title('Intervalos admisibles · extremos sin margen'+(f' · primeros {count}' if len(data['m'])>count else ''))
        if candidate is not None and candidate>right:axis.text(.98,.02,'Ωs consultada supera el rango mostrado; ver Informe.',transform=axis.transAxes,ha='right',va='bottom',fontsize=8)
        axis.grid(alpha=.2);figure.tight_layout();self.view.canvas.draw_idle()
        self.tabs.setTabVisible(0,True);self.tabs.setCurrentIndex(1)
    def display(self,*_):
        index=self.selector.currentIndex()
        if not 0<=index<len(self.items):self.system_actions.hide();return
        value=self.items[index];is_system=isinstance(value,Transfer);self.system_actions.setVisible(is_system);self.system_actions.set_result(value if is_system else None,self.records[index]);self.view.actions.setVisible(not is_system);self.view.plot_mode.setVisible(not is_system);self.system_view.setVisible(is_system)
        if self.action=='convert':
            self.magnitude_scale.setVisible(is_system);self.magnitude_scale.setEnabled(is_system and self.system_view.currentIndex()!=2)
            if hasattr(self,'figure_magnitude'):self.figure_magnitude.setEnabled(is_system and self.system_view.currentIndex()!=2)
        for control in (self.view.label,self.view.send,self.view.save):control.setVisible(not is_system)
        if not is_system:
            self.view.show_result(value)
            if self.action=='phase' and self.reconstruction_data is not None:
                from .phase_reconstruction import reconstruction_summary
                self.report.set_readable(reconstruction_summary(self.reconstruction_data))
                is_response=value is self.reconstruction_data['response'];self.view.plot_mode.setVisible(not is_response);self.system_view.setVisible(is_response)
                if is_response:self.draw_reconstruction()
            if self.action=='fft':self.pin_button.setEnabled(len(self.items)>1);self.draw_comparison()
            return
        self.view.table_view.set_signals(());self.view.views.setTabVisible(self.view.table_index,False)
        self.view.views.setTabVisible(self.view.details_index,False)
        self.view.result=None;self.view.save.setEnabled(False);self.view.send.setEnabled(False);self.view.label.setText(value.name)
        if self.action=='phase' and getattr(self,'_phase_report_value',None) is not value:
            from .phase_summary import phase_summary
            if self.compensation_data is not None:
                from .phase_compensation import compensation_summary
                self.report.set_readable(compensation_summary(self.compensation_data,value))
            else:self.report.set_readable(phase_summary(self.phase_input,self.items,index,self.phase_report))
            self._phase_report_value=value
        if self.action=='phase' and self.compensation_data is not None and self.show_all_systems.isChecked():
            from .compensation_plot import draw_comparison
            draw_comparison(self,self.compensation_data);return
        spec=self.specifications if (index==0 or self.comparing_systems) else None
        mode=self.system_view.currentIndex();linear=(self.magnitude_scale.currentIndex()==0) if self.action=='convert' else mode==3
        previous=self.view.figure.axes[-1].get_xlim() if self.action=='convert' and self.view.figure.axes and getattr(self,'_conversion_plot',None)==(id(value),mode) else None
        self.view.figure.clear();axes=np.atleast_1d(self.view.figure.subplots(3 if mode==0 else 1,1,sharex=True));w=np.linspace(0,np.pi,2049) if value.domain=='digital' else np.geomspace(.01,100,2049)
        if self.action=='convert':
            from .conversion_details import response_grid
            w=response_grid(value)
            if value.domain=='analog':w=w[w>0]
            self._conversion_plot=(id(value),mode)
        if spec and spec.get('domain')=='analog':w=np.geomspace(*spec['plot_range'],2049)
        if spec:
            w=np.unique(np.r_[w,spec['wp'],spec['ws']])
        plotted=self.items if self.comparing_systems and self.show_all_systems.isChecked() else [value]
        magnitude_label='|H| · amplitud' if linear else 'Módulo (dB)'
        labels=(magnitude_label,'Fase (rad)','Retardo de grupo (muestras)' if value.domain=='digital' else 'Retardo de grupo (s)') if mode==0 else (magnitude_label,) if mode in (1,3) else ('Retardo (muestras)' if value.domain=='digital' else 'Retardo (s)',)
        palette=['#68c7b4','#e8b56b','#91a5f6','#dd8baf']
        for curve_index,system in enumerate(plotted):
            h=system.response(w)
            finite=np.isfinite(h);scale=float(np.max(abs(h[finite]))) if np.any(finite) else 1
            scale=scale if scale else 1
            valid=finite&(abs(h)>np.finfo(float).eps*scale)
            db_valid=finite&(abs(h)>0)
            magnitude=np.full(w.size,np.nan);magnitude[db_valid]=20*np.log10(abs(h[db_valid]));phase=np.full(w.size,np.nan);delay=np.full(w.size,np.nan)
            for indices in np.split(np.flatnonzero(valid),np.flatnonzero(np.diff(np.flatnonzero(valid))>1)+1):
                if indices.size>1:phase[indices]=np.unwrap(np.angle(h[indices]))
            if mode in (0,2):delay=system.group_delay(w)
            shown_magnitude=abs(h) if linear else magnitude
            values=(shown_magnitude,phase,delay) if mode==0 else (shown_magnitude,) if mode in (1,3) else (delay,)
            selected=system is value
            for axis,y,label in zip(axes,values,labels):
                axis.plot(w,y,label=system.name+(' · seleccionado' if selected and self.comparing_systems else ''),color=palette[(curve_index if len(plotted)>1 else index)%len(palette)],linewidth=1.8 if selected else 1.1,alpha=1 if selected else .75)
                axis.set_ylabel(label);axis.grid(alpha=.2)
                if value.domain=='analog':axis.set_xscale('log')
                else:axis.set_xscale('linear');axis.set_xlim(0,np.pi)
        if self.comparing_systems:
            axes[0].legend(fontsize=8)
            self.view.label.setText('Filtro seleccionado: '+value.name)
        if spec and mode!=2:self.draw_specifications(axes[0],spec,linear=linear)
        from .signal_plot import configure_axis
        configure_axis(axes[-1],units='rad/muestra' if value.domain=='digital' else 'rad/s')
        if previous is not None:axes[-1].set_xlim(previous)
        axes[-1].set_xlabel('ω (rad/muestra)' if value.domain=='digital' else 'Ω (rad/s)');self.view.figure.tight_layout();self.view.canvas.draw_idle()
        self.view.text.setPlainText('Sistema calculado\n\nNumerador: '+list_text(value.b)+'\nDenominador: '+list_text(value.a)+'\n\nEl retardo de grupo se calcula mediante la derivada analítica de la transferencia, sin diferencias entre puntos de la gráfica. Se omiten ceros, polos y evaluaciones mal condicionadas. Las unidades son muestras en discreto y segundos en continuo. En continuo se muestra Ω entre 0.01 y 100 rad/s; usá Respuesta en frecuencia para elegir otro rango.')
    def draw_specifications(self,axis,spec,linear=False):
        wp=spec['wp'];ws=spec['ws'];kind=spec['kind'];analog=spec.get('domain')=='analog';low,high=spec.get('plot_range',[0,np.pi]);unit='rad/s' if analog else 'rad/muestra'
        if kind=='lowpass':passing=[(low,wp[0])];stopping=[(ws[0],high)]
        elif kind=='highpass':passing=[(wp[0],high)];stopping=[(low,ws[0])]
        elif kind=='bandpass':passing=[(wp[0],wp[1])];stopping=[(low,ws[0]),(ws[1],high)]
        else:passing=[(low,wp[0]),(wp[1],high)];stopping=[(ws[0],ws[1])]
        convert=(lambda x:x) if linear else (lambda x:20*np.log10(x))
        lower=convert(1-spec['dp']);upper=convert(spec.get('pass_upper',1+spec['dp']));stop=convert(spec['ds'])
        transitions=sorted((min(p,s),max(p,s)) for p,s in zip(wp,ws))
        for i,(left,right) in enumerate(transitions):
            axis.axvspan(left,right,color='#91a5f6',alpha=.15,label='Transición (sin restricciones)' if i==0 else None)
        widths=' · '.join(('Izquierda' if i==0 else 'Derecha')+f': Δω = {right-left:.6g} {unit}' for i,(left,right) in enumerate(transitions)) if len(transitions)==2 else f'Δω = {transitions[0][1]-transitions[0][0]:.6g} {unit}'
        axis.set_xscale('log' if analog else 'linear');axis.set_xlim(low,high)
        for i,(left,right) in enumerate(passing):
            axis.axvspan(left,right,color='#68c7b4',alpha=.08)
            axis.plot([left,right],[lower,lower],color='#68c7b4',linestyle='--',linewidth=1,label='Límites de paso' if i==0 else None)
            axis.plot([left,right],[upper,upper],color='#68c7b4',linestyle='--',linewidth=1)
        for i,(left,right) in enumerate(stopping):
            axis.axvspan(left,right,color='#efb56c',alpha=.06)
            axis.plot([left,right],[stop,stop],color='#efb56c',linestyle='--',linewidth=1,label='Máximo en rechazo' if i==0 else None)
        for edge in wp+ws:axis.axvline(edge,color='#8194ae',linestyle=':',linewidth=.6)
        axis.set_title('Especificaciones · escala '+('logarítmica' if analog else 'lineal')+'\n'+widths,fontsize=9)
        axis.legend(fontsize=8,loc='lower center' if not linear else 'best')
    def pin_spectrum(self):
        if self.action!='fft' or len(self.items)<2:return
        meta=self.items[0].metadata
        name='Referencia: '+str(meta.get('window','ventana'))+f" · L={meta.get('window_length','?')} · NFFT={meta.get('nfft','?')}"
        self.reference_spectrum=self.items[1].copy_with(name=name)
        self.clear_reference.setEnabled(True);self.comparison_note.setText(name+'. Se conserva al recalcular. Exportar guarda el resultado seleccionado.')
        self.redraw_comparison()
    def remove_reference(self):
        self.reference_spectrum=None;self.clear_reference.setEnabled(False);self.comparison_note.setText('La DFT se muestra con tallos; la DTFT, como curva.');self.redraw_comparison()
    def redraw_comparison(self,*_):
        if self.action!='fft' or self.view.result is None:return
        self.view.draw_signal();self.draw_comparison()
    def draw_comparison(self,*_):
        if self.action!='fft' or self.selector.currentIndex() not in (0,1) or len(self.items)<2:return
        from .signal_plot import plot_samples, configure_frequency_overlay, validate_overlay
        axes=self.view.figure.axes
        if len(axes)!=2:return
        overlays=[]
        if self.overlay_enabled.isChecked():
            index=1 if self.selector.currentIndex()==0 else 0
            overlays.append((self.items[index],index==0,'#68c7b4'))
        if self.reference_spectrum is not None:overlays.append((self.reference_spectrum,False,'#efb56c'))
        compared=[self.items[self.selector.currentIndex()]]+[entry[0] for entry in overlays]
        validate_overlay(compared)
        polar=self.view.plot_mode.currentIndex()==0
        for source,discrete,color in overlays:
            shown=self.window._plot_indices(source.values);values=source.values[shown];axis=source.axis[shown]
            magnitude=abs(values)
            first=magnitude if polar else values.real
            second=np.where(magnitude>0,np.angle(values),np.nan) if polar else values.imag
            plot_samples(axes[0],axis,first,discrete=discrete,label=source.name,color=color)
            valid=np.isfinite(second)
            if np.any(valid):plot_samples(axes[1],axis[valid] if discrete else axis,second[valid] if discrete else second,discrete=discrete,label=source.name,color=color,phase=polar)
        if overlays:configure_frequency_overlay(axes,compared)
        for axis in axes:
            if axis.get_legend_handles_labels()[0]:axis.legend(fontsize=8)
        self.view.figure.tight_layout();self.view.canvas.draw_idle()
    def send(self,task):
        index=self.selector.currentIndex();value=self.items[index]
        item=next(it for group in MENUS.values() for it in group if it[1]=='systems' and it[2]==task);self.window.send_system(value,self.records[index],item)
    def export_system(self):self.window.export_transfer(self.items[self.selector.currentIndex()])


