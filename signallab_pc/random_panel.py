from .validation import show_input_error
from .numeric_input import real_field,integer_field
"""Herramientas independientes para señales aleatorias y sus registros."""
import secrets
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QLineEdit,QComboBox,QPushButton,QLabel,QScrollArea,QSplitter,QTabWidget,QCheckBox
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT
from . import random_signals
from .descriptive_statistics import PROJECTIONS, describe_record
from .probability import FAMILIES, Distribution, distribution_value, generate_realizations, interval_probability, moment, population, store_realizations
from .multivariate_probability import Gaussian, Multinomial, gaussian_density, generate_gaussian, generate_multinomial
from .matrix_editor import MatrixEditor
from .report_view import ReportView,report_panel
from .result_summary import Section, Summary, number
from .statistical_inference import (FIT_FAMILIES, FIT_INTERVALS, METHODS, NULL_PARAMETER,
                                    TWO_SAMPLES, fit_distribution, infer_record)
from .statistics_results import store_statistics
from .stochastic_noise import COLORS as NOISE_COLORS, FREQUENCY_NOISES, NOISES, Noise, generate_noise, noise_spectrum, store_noise
from .stochastic_processes import (PHYSICAL_PROCESSES, PROCESSES, Process, generate_process,
                                  process_moments, process_transition, store_processes)
from .tool_guide import ToolGuide


_LEGACY = {'gaussian': 'Gaussiana', 'uniform': 'Uniforme', 'bernoulli': 'Bernoulli (0 o 1)'}
_JOINT = {'normal_vector': 'Normal multivariada', 'complex_vector': 'Normal compleja',
          'multinomial': 'Multinomial'}
_METHODS = {'generate': 'Generar realización', 'population': 'Propiedades poblacionales',
            'density': 'Densidad o masa', 'cdf': 'Probabilidad acumulada (CDF)',
            'survival': 'Probabilidad de excedencia (CCDF)', 'quantile': 'Cuantil',
            'interval': 'Probabilidad en un intervalo', 'moment': 'Momento no central'}
_PARAMETERS = {
    'mean': ('Media de la distribución', '0'), 'std': ('Desviación estándar', '1'),
    'trials': ('Cantidad de ensayos', '10'), 'successes': ('Cantidad de éxitos', '3'),
    'population': ('Tamaño de la población', '20'), 'draws': ('Extracciones sin reemplazo', '5'),
    'p': ('Probabilidad de éxito', '0.5'), 'rate': ('Media de recuentos λ', '4'),
    'low': ('Límite inferior', '0'), 'high': ('Límite superior', '5'),
    'probabilities': ('Probabilidades por categoría', '0.25, 0.50, 0.25'),
    'shape': ('Parámetro de forma', '2'), 'scale': ('Escala', '1'),
    'ratio': ('Relación amplitud fija / desviación', '1'), 'alpha': ('Forma α', '2'),
    'beta': ('Forma β', '3'), 'log_mean': ('Media del logaritmo', '0'),
    'log_std': ('Desviación del logaritmo', '1'), 'df': ('Grados de libertad', '5'),
    'df_num': ('Grados de libertad del numerador', '5'),
    'df_den': ('Grados de libertad del denominador', '10'), 'location': ('Ubicación', '0'),
}
_PROCESS_FIELDS = {
    'initial': ('Valor o estado inicial', '0'), 'drift': ('Deriva', '0'),
    'std': ('Intensidad de la fluctuación', '1'), 'event_rate': ('Eventos por segundo', '2'),
    'mean': ('Nivel de equilibrio', '0'), 'reversion': ('Tasa de retorno (1/s)', '1'),
    'low': ('Nivel bajo', '-1'), 'high': ('Nivel alto', '1'),
    'rate_up': ('Tasa baja a alta (1/s)', '1'), 'rate_down': ('Tasa alta a baja (1/s)', '1'),
    'transition': ('Probabilidades de transición por fila', '0.75, 0.25; 0.5, 0.5'),
}
_PROCESS_NOTES = {
    'random_walk': 'La deriva y la desviación de los incrementos se expresan por muestra. El primer valor es la condición inicial.',
    'wiener': 'La deriva se expresa por segundo. La desviación del incremento de duración Δt es la difusión multiplicada por √Δt.',
    'poisson_process': 'La tasa fija el número medio de eventos por segundo. El resultado es un recuento acumulado.',
    'ornstein_uhlenbeck': 'Dejá vacío el valor inicial para empezar en equilibrio. La intensidad se expresa por raíz de segundo.',
    'telegraph': 'Estado inicial 0: nivel bajo. Estado 1: nivel alto. Dejá el campo vacío para empezar en equilibrio.',
    'markov': 'Cada fila suma uno. Las filas y columnas representan estados desde 0. Cargá un estado o probabilidades iniciales separadas por comas. Dejá vacío el inicio para usar una distribución estacionaria única.',
}
_NOISE_FIELDS = {
    'color': ('Color espectral', ''), 'variance': ('Varianza', '1'), 'complex': ('Salida compleja propia', ''),
    'low_hz': ('Corte inferior (Hz)', '1'), 'high_hz': ('Corte superior (Hz)', '40'),
    'background_std': ('Desviación de fondo', '0.2'), 'impulse_std': ('Desviación de los impulsos', '2'),
    'impulse_probability': ('Probabilidad de impulso', '0.01'),
    'frequency_hz': ('Frecuencias en Hz', '0, 40'), 'density': ('PSD bilateral por Hz', '0.01, 0.01'),
    'taps': ('Coeficientes h[n] del FIR', '0.5, 0.5'),
}
_NOISE_NOTES = {
    'white_noise': 'Cada muestra es independiente. Para ruido complejo propio, I y Q tienen la mitad de la varianza indicada.',
    'colored_noise': 'Elegí la banda y el color. Rosa y marrón requieren un corte inferior positivo. La varianza se ajusta en esperanza sobre la grilla de la realización.',
    'impulsive_noise': 'En cada muestra se elige la desviación de fondo o de impulso. El color de la mezcla sigue siendo blanco.',
    'specified_noise': 'Escribí una densidad bilateral por Hz en cada frecuencia. Usá solo f ≥ 0 para una señal real. La aplicación interpola y usa cero fuera del intervalo.',
    'fir_noise': 'La varianza corresponde al ruido blanco de entrada. Se genera una prehistoria independiente para que la salida empiece en régimen estacionario.',
}
_STATES = {'undefined': 'Indefinido', 'divergent': 'Divergente', 'unbounded': 'Sin cota',
           'singular_density': 'Densidad infinita en el borde', 'singular_measure': 'Distribución singular',
           'out_of_range': 'Fuera del rango numérico', 'numerically_unavailable': 'Sin valor numérico fiable',
           'underflow': 'Por debajo del rango numérico', 'zero_or_underflow': 'Cero o por debajo del rango',
           'zero_joint_likelihood': 'Verosimilitud nula: alguna observación quedó fuera del soporte ajustado'}
_PROJECTION_LABELS = dict(zip(PROJECTIONS, ('Parte real', 'Parte imaginaria', 'Módulo', 'Fase (rad)'), strict=True))


class RandomPanel(QWidget):
    def __init__(self,window,action):
        super().__init__();self.window=window;self.action=action
        from .toolbox import LocalInput,ResultView
        root=QVBoxLayout(self);split=QSplitter(Qt.Orientation.Horizontal);split.setChildrenCollapsible(False);root.addWidget(split)
        controls=QWidget();form=QFormLayout(controls);form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form.addRow(ToolGuide('Generá una realización reproducible y usala en filtrado o análisis espectral.' if action=='generate' else 'Medí un registro finito. Sus estadísticas no prueban las propiedades de todo un proceso aleatorio.',('Distribución','Muestras','Análisis') if action=='generate' else ('Registro','Estadísticas','Histograma')))
        if action=='generate':
            self._generation_controls(form)
        else:
            self._statistics_controls(form, LocalInput)
        button=QPushButton('Calcular' if action=='generate' else 'Calcular estadísticas');button.setObjectName('primary');button.clicked.connect(self.calculate);form.addRow(button)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);scroll.setMinimumWidth(320);split.addWidget(scroll)
        self.tabs=QTabWidget();split.addWidget(self.tabs);split.setSizes([350,740]);split.setStretchFactor(1,1)
        self.output=ResultView()
        if action=='generate':
            signals=QWidget(); signal_layout=QVBoxLayout(signals)
            self.sample_choice=QComboBox()
            self.sample_choice.setAccessibleName('Realización o componente mostrada')
            self.sample_choice.setProperty('sessionTransient', True)
            self.sample_choice.currentIndexChanged.connect(self._show_sample)
            self.sample_choice.hide()
            signal_layout.addWidget(self.sample_choice);signal_layout.addWidget(self.output,1)
            self.tabs.addTab(signals,'Realizaciones')
            self._samples=()
        else:
            self.tabs.addTab(self.output,'Señal')
        self.report=ReportView();self.tabs.addTab(report_panel(self.report),'Informe' if action=='generate' else 'Estadísticas')
        self.report.setPlainText('Completá los datos y calculá. Los resultados describen una realización finita, no toda la distribución.')
        if action!='generate':
            plot=QWidget();box=QVBoxLayout(plot)
            self.plot_kind=QComboBox()
            self.plot_kind.setProperty('sessionTransient',True)
            self.plot_kind.setAccessibleName('Diagnóstico estadístico')
            self.plot_kind.currentIndexChanged.connect(self._draw_statistics)
            self._statistics=None
            box.addWidget(self.plot_kind)
            self.figure=Figure(figsize=(7,4),layout='constrained');self.canvas=FigureCanvasQTAgg(self.figure);self.canvas.setMinimumHeight(280)
            box.addWidget(NavigationToolbar2QT(self.canvas,self));box.addWidget(self.canvas,1);self.tabs.addTab(plot,'Gráficos')

    def _statistics_controls(self, form, source_type):
        self.source = source_type('Registro para analizar')
        self.source.bind_project(self.window)
        form.addRow(self.source)
        self.component = QComboBox()
        self.component.addItems(list(_PROJECTION_LABELS.values()))
        form.addRow('Componente para analizar', self.component)

        def choices(label, values):
            widget = QComboBox()
            for key, name in values.items():
                widget.addItem(name, key)
            form.addRow(label, widget)
            return widget

        def entry(label, value):
            widget = QLineEdit(value)
            form.addRow(label, widget)
            return widget

        self.analysis = choices('Análisis', {'describe': 'Estadística descriptiva',
                                             'fit': 'Ajustar una distribución', 'infer': 'Contrastar una hipótesis'})
        self.bins = entry('Intervalos del histograma', '30')
        self.diagnostics = QCheckBox('Incluir CDF, CCDF y diagrama de caja')
        self.reference_normal = QCheckBox('Comparar con una distribución de parámetros conocidos')
        form.addRow(self.diagnostics)
        form.addRow(self.reference_normal)
        self.reference_family = choices('Distribución de referencia', {key: law.label for key,law in FAMILIES.items()})
        self.reference_family.setCurrentIndex(self.reference_family.findData('normal'))
        self.reference_mean = entry('Media de referencia', '0')
        self.reference_std = entry('Desviación de referencia', '1')
        families = {key: FAMILIES[key].label for key in FIT_FAMILIES}
        self.fit_family = choices('Distribución para ajustar', families)
        self.fit_method = choices('Estimador', {'ml': 'Máxima verosimilitud', 'moments': 'Método de los momentos'})
        self.fit_trials = entry('Ensayos por observación binomial', '10')
        self.fit_interval = QCheckBox('Incluir intervalos para los parámetros')
        form.addRow(self.fit_interval)
        self.inference_method = choices('Contraste', METHODS)
        self.second_source = source_type('Segunda muestra independiente')
        self.second_source.bind_project(self.window)
        form.addRow(self.second_source)
        self.null_value = entry('Valor bajo la hipótesis nula', '')
        self.known_std = entry('Desviación poblacional conocida', '')
        self.confidence_level = entry('Nivel de confianza (1 − α)', '0.95')
        self.alternative = choices('Hipótesis alternativa', {'two-sided': 'Distinta', 'less': 'Menor', 'greater': 'Mayor'})
        self.lags = entry('Cantidad de retardos', '10')
        self.fitted_parameters = entry('Parámetros estimados del modelo', '0')
        self.ks_family = choices('Distribución continua conocida', {
            key: law.label for key, law in FAMILIES.items() if not law.discrete})
        self.fields = {}
        for key in dict.fromkeys(key for law in FAMILIES.values() for key, _, _ in law.parameters):
            self.fields[key] = entry(*_PARAMETERS[key])
        self.iid = QCheckBox('Confirmo observaciones independientes bajo la hipótesis nula')
        self.iid.setToolTip('En pruebas de dos muestras, también deben ser independientes entre sí.')
        form.addRow(self.iid)
        note = QLabel()
        note.setWordWrap(True)
        form.addRow(note)

        def update(*_):
            mode = self.analysis.currentData()
            method = self.inference_method.currentData()
            described, fitted, inferred = (mode == option for option in ('describe', 'fit', 'infer'))
            diagnostic = described and self.diagnostics.isChecked()
            known = diagnostic and self.reference_normal.isChecked()
            reference = self.reference_family.currentData()
            normal_reference = known and reference == 'normal'
            ks = inferred and method == 'ks'
            ljung = inferred and method == 'ljung_box'
            family = self.fit_family.currentData()
            interval_available = fitted and family in FIT_INTERVALS
            use_level = inferred or interval_available and self.fit_interval.isChecked()
            moments = 'moments' in FIT_FAMILIES[family]
            self.fit_method.model().item(1).setEnabled(moments)
            if not moments:
                self.fit_method.setCurrentIndex(0)
            settings = (
                (self.bins, described), (self.diagnostics, described), (self.reference_normal, diagnostic),
                (self.reference_family, known), (self.reference_mean, normal_reference),
                (self.reference_std, normal_reference), (self.fit_family, fitted),
                (self.fit_method, fitted), (self.fit_trials, fitted and family == 'binomial'),
                (self.inference_method, inferred), (self.iid, use_level), (self.confidence_level, use_level),
                (self.fit_interval, interval_available),
                (self.second_source, inferred and method in TWO_SAMPLES), (self.ks_family, ks),
                (self.null_value, inferred and method in NULL_PARAMETER), (self.known_std, inferred and method == 'z'),
                (self.alternative, inferred and (method in NULL_PARAMETER or method == 'mann_whitney')),
                (self.lags, ljung), (self.fitted_parameters, ljung), (note, inferred),
            )
            for widget, visible in settings:
                form.setRowVisible(widget, visible)
            parameters = self.ks_family.currentData() if ks else reference if known and not normal_reference else None
            active = {key for key, _, _ in FAMILIES[parameters].parameters} if parameters is not None else set()
            for key, widget in self.fields.items():
                form.setRowVisible(widget, key in active)
            note.setText({
                'ks': 'Usá parámetros conocidos antes de observar la muestra. Los parámetros de un ajuste no sirven para esta calibración.',
                'ljung_box': 'La hipótesis nula es ausencia de autocorrelación hasta el retardo indicado. Usá un registro discreto contiguo.',
                'mann_whitney': 'Contrasta las distribuciones por rangos. Una diferencia de rangos no implica por sí sola un cambio de mediana.',
                'ad': 'Contrasta normalidad y estima los parámetros normales durante la prueba.',
                'shapiro': 'Contrasta normalidad. El valor p tiene exactitud limitada con más de 5000 observaciones.',
                'proportion': 'Ingresá observaciones de 0 y 1. El intervalo se calcula con el método exacto de Clopper–Pearson.',
                'f': 'Ingresá el cociente hipotético de varianzas, primera muestra sobre segunda. Se supone normalidad en ambas.',
                'variance': 'Ingresá la varianza de la población bajo H₀. La calibración supone normalidad.',
                'welch': 'Ingresá la diferencia hipotética de medias, primera muestra menos segunda. Las varianzas pueden diferir.',
            }.get(method, 'Ingresá la media poblacional bajo H₀. La calibración supone normalidad.'))

        for selector in (self.analysis, self.fit_family, self.inference_method, self.ks_family, self.reference_family):
            selector.currentIndexChanged.connect(update)
        for checkbox in (self.diagnostics, self.reference_normal, self.fit_interval):
            checkbox.toggled.connect(update)
        update()

    def _generation_controls(self, form):
        self.distribution = QComboBox()
        options = {**_LEGACY, **{key: family.label for key, family in FAMILIES.items()
                                if key not in ('uniform', 'normal', 'bernoulli')}, **_JOINT}
        for key, label in options.items():
            self.distribution.addItem(label, key)
        self.distribution.insertSeparator(self.distribution.count())
        for key, (label, _) in PROCESSES.items():
            self.distribution.addItem(label, key)
        self.distribution.insertSeparator(self.distribution.count())
        for key, (label, _) in NOISES.items():
            self.distribution.addItem(label, key)
        self.method = QComboBox()
        for key, label in _METHODS.items():
            self.method.addItem(label, key)
        form.addRow('Distribución o proceso', self.distribution)
        form.addRow('Operación', self.method)
        self.mean, self.std, self.probability = QLineEdit('0'), QLineEdit('1'), QLineEdit('0.5')
        form.addRow('Media teórica', self.mean)
        form.addRow('Desviación estándar', self.std)
        form.addRow('Probabilidad de obtener 1', self.probability)
        self.fields = {}
        for family in options:
            if (family in _JOINT and family != 'multinomial') or family in _LEGACY:
                continue
            keys = ('trials', 'probabilities') if family == 'multinomial' else (
                entry[0] for entry in FAMILIES[family].parameters)
            for key in keys:
                label, default = _PARAMETERS[key]
                widget = QLineEdit(default)
                self.fields[f'{family}.{key}'] = widget
                form.addRow(label, widget)
        for family, (_, keys) in PROCESSES.items():
            for key in keys:
                label, default = _PROCESS_FIELDS[key]
                if key == 'initial' and family in ('ornstein_uhlenbeck', 'telegraph'):
                    default = ''
                widget = MatrixEditor(default) if key == 'transition' else QLineEdit(default)
                self.fields[f'{family}.{key}'] = widget
                form.addRow(label, widget)
        for family, (_, keys) in NOISES.items():
            for key in keys:
                label, default = _NOISE_FIELDS[key]
                if key == 'color':
                    widget = QComboBox()
                    for color, title in zip(NOISE_COLORS, ('Rosa', 'Marrón', 'Azul', 'Violeta'), strict=True):
                        widget.addItem(title, color)
                elif key == 'complex':
                    widget = QCheckBox(label)
                else:
                    widget = QLineEdit(default)
                self.fields[f'{family}.{key}'] = widget
                if key == 'complex':
                    form.addRow(widget)
                else:
                    form.addRow(label, widget)
        self.theory_first, self.theory_second = QLineEdit('0'), QLineEdit('1')
        form.addRow('Primera posición desde el inicio', self.theory_first)
        form.addRow('Segunda posición desde el inicio', self.theory_second)
        self.location = QLineEdit('0, 0')
        self.covariance = MatrixEditor('1, 0; 0, 1')
        self.pseudocovariance = MatrixEditor()
        form.addRow('Vector de medias', self.location)
        form.addRow('Covarianza', self.covariance)
        form.addRow('Pseudocovarianza opcional', self.pseudocovariance)

        self.argument, self.upper, self.order = QLineEdit('0'), QLineEdit('1'), QLineEdit('2')
        self.observation = QLineEdit()
        form.addRow('Punto o extremo inferior', self.argument)
        form.addRow('Extremo superior', self.upper)
        form.addRow('Orden del momento (0–4)', self.order)
        form.addRow('Punto conjunto', self.observation)
        self.count, self.seed, self.origin = QLineEdit('1024'), QLineEdit('12345'), QLineEdit('0')
        self.replicas, self.sample_rate = QLineEdit('1'), QLineEdit()
        form.addRow('Cantidad de muestras', self.count)
        self.advanced = QCheckBox('Opciones avanzadas')
        form.addRow(self.advanced)
        form.addRow('Réplicas independientes', self.replicas)
        form.addRow('Índice inicial', self.origin)
        form.addRow('Frecuencia de muestreo opcional (Hz)', self.sample_rate)
        form.addRow('Semilla reproducible', self.seed)
        fresh = QPushButton('Elegir otra semilla')
        fresh.clicked.connect(lambda: self.seed.setText(str(secrets.randbits(32))))
        form.addRow(fresh)
        self.distribution_note = QLabel()
        self.distribution_note.setWordWrap(True)
        form.addRow(self.distribution_note)

        def update(*_):
            key = self.distribution.currentData()
            joint = key in _JOINT
            process = key in PROCESSES
            noise = key in NOISES
            allowed = ('generate', 'population') if process or noise else ('generate', 'population', 'density') if joint else _METHODS
            for index, option in enumerate(_METHODS):
                self.method.model().item(index).setEnabled(option in allowed)
            if self.method.currentData() not in allowed:
                self.method.setCurrentIndex(0)
            mode = self.method.currentData()
            generating = mode == 'generate'
            advanced = generating and self.advanced.isChecked()
            for widget in (self.mean, self.std):
                form.setRowVisible(widget, key in ('gaussian', 'uniform'))
            form.setRowVisible(self.probability, key == 'bernoulli')
            for name, widget in self.fields.items():
                form.setRowVisible(widget, name.split('.', 1)[0] == key)
            for widget in (self.location, self.covariance):
                form.setRowVisible(widget, key in ('normal_vector', 'complex_vector'))
            form.setRowVisible(self.pseudocovariance, key == 'complex_vector')
            form.setRowVisible(self.count, generating or noise)
            form.labelForField(self.count).setText('Bins de la PSD' if noise and not generating else 'Cantidad de muestras')
            form.setRowVisible(self.advanced, generating)
            for widget in (self.replicas, self.origin, self.seed, fresh):
                form.setRowVisible(widget, advanced)
            physical = key in PHYSICAL_PROCESSES or key in FREQUENCY_NOISES or (noise and not generating)
            form.setRowVisible(self.sample_rate, advanced or physical)
            form.labelForField(self.sample_rate).setText('Frecuencia de muestreo (Hz)' if physical else 'Frecuencia de muestreo opcional (Hz)')
            for widget in (self.theory_first, self.theory_second):
                form.setRowVisible(widget, process and not generating)
            form.setRowVisible(self.argument, not joint and not process and mode in ('density', 'cdf', 'survival', 'quantile', 'interval'))
            form.setRowVisible(self.upper, mode == 'interval')
            form.setRowVisible(self.order, mode == 'moment')
            form.setRowVisible(self.observation, joint and mode == 'density')
            self.argument.setToolTip('Probabilidad entre 0 y 1.' if mode == 'quantile' else 'Valor de la variable aleatoria.')
            note = {
                'uniform': 'Los límites son media ± √3·desviación. La teoría continua requiere desviación positiva.',
                'geometric': 'Cuenta ensayos hasta el primer éxito, empezando en 1.',
                'negative_binomial': 'Cuenta fallos anteriores al último éxito necesario.',
                'categorical': 'Las probabilidades suman uno y las categorías se numeran desde 0.',
                'multinomial': 'Cada observación contiene un recuento por categoría.',
                'complex_vector': 'La pseudocovarianza vacía representa un modelo propio. La densidad usa coordenadas real e imaginaria.',
            }
            fallback = 'Una realización finita puede diferir de las propiedades de la distribución.'
            self.distribution_note.setText(_NOISE_NOTES.get(key) or _PROCESS_NOTES.get(key) or note.get(key, fallback))

        self.distribution.currentIndexChanged.connect(update)
        self.method.currentIndexChanged.connect(update)
        self.advanced.toggled.connect(update)
        update()

    def _model_inputs(self, key):
        from .systems_panel import parse_list

        def weights(text):
            values = parse_list(text)
            if np.any(values.imag):
                raise ValueError('Las probabilidades por categoría deben ser reales.')
            return values.real

        if key in ('normal_vector', 'complex_vector'):
            from .state_space_panel import matrix
            pseudo = self.pseudocovariance.text().strip()
            return Gaussian, (parse_list(self.location.text()), matrix(self.covariance.text()),
                              key == 'complex_vector', matrix(pseudo) if pseudo and key == 'complex_vector' else None)
        if key == 'multinomial':
            return Multinomial, (integer_field(self.fields[f'{key}.trials']),
                                 weights(self.fields[f'{key}.probabilities'].text()))
        if key == 'bernoulli':
            return Distribution, (key, {'p': real_field(self.probability)})
        if key in ('gaussian', 'uniform'):
            mean, deviation = real_field(self.mean), real_field(self.std)
            if key == 'gaussian':
                return Distribution, ('normal', {'mean': mean, 'std': deviation})
            if deviation <= 0:
                raise ValueError('La desviación de la uniforme continua debe ser positiva.')
            width = np.sqrt(3) * deviation
            return Distribution, (key, {'low': mean - width, 'high': mean + width})
        parameters = {}
        for name, _, rule in FAMILIES[key].parameters:
            field = self.fields[f'{key}.{name}']
            if rule == 'vector':
                parameters[name] = weights(field.text())
            else:
                parser = integer_field if rule in ('integer', 'count', 'positive_count') else real_field
                parameters[name] = parser(field)
        return Distribution, (key, parameters)

    def _show_sample(self, index):
        if 0 <= index < len(self._samples):
            self.output.show_result(self._samples[index])

    def _calculate_distribution(self):
        key, method = self.distribution.currentData(), self.method.currentData()
        label = self.distribution.currentText()
        if key in PROCESSES:
            self._calculate_process(key, method == 'generate')
            return
        if key in NOISES:
            self._calculate_noise(key, method == 'generate')
            return
        if method == 'generate':
            count, seed = integer_field(self.count), integer_field(self.seed)
            origin, replicas = integer_field(self.origin), integer_field(self.replicas)
            rate = real_field(self.sample_rate) if self.sample_rate.text().strip() else None
            if key in _LEGACY and replicas == 1 and rate is None:
                args = (key, count, real_field(self.mean) if key != 'bernoulli' else 0,
                        real_field(self.std) if key != 'bernoulli' else 1,
                        real_field(self.probability) if key == 'bernoulli' else .5, seed, origin)

                def accept(signal):
                    self.window.publish(signal, operation='Generación aleatoria')
                    self._display_realizations((signal,))
                    self._population_report(label, {
                        'mean': {'value': signal.metadata['theoretical_mean'], 'status': 'finite'},
                        'variance': {'value': signal.metadata['theoretical_variance'], 'status': 'finite'},
                    }, (signal,))

                self.window._run_operation('Generando señal aleatoria…', lambda: random_signals.generate(*args), accept)
                return
        builder, args = self._model_inputs(key)
        argument = real_field(self.argument) if method in ('density','cdf','survival','quantile','interval') and key not in _JOINT else None
        upper = real_field(self.upper) if method == 'interval' else None
        order = integer_field(self.order) if method == 'moment' else None
        observation = None
        if method == 'density' and key in _JOINT:
            from .systems_panel import parse_list
            observation = parse_list(self.observation.text())
            if key == 'multinomial':
                if np.any(observation.imag) or np.any(observation.real != np.floor(observation.real)):
                    raise ValueError('Ingresá un recuento entero por categoría.')
                observation = [int(value) for value in observation.real]

        def calculate():
            model = builder(*args)
            if method in ('population', 'generate'):
                theory = {Distribution: population, Gaussian: Gaussian.document,
                          Multinomial: Multinomial.population}[type(model)](model)
                records = ()
                if method == 'generate':
                    generator = {Distribution: generate_realizations, Gaussian: generate_gaussian,
                                 Multinomial: generate_multinomial}[type(model)]
                    records = generator(model, count, seed, replicas=replicas, origin=origin, rate=rate)
                return {'population': theory, 'records': records, 'distribution': model.document()}
            if isinstance(model, Gaussian):
                result = gaussian_density(model, observation)
            elif isinstance(model, Multinomial):
                result = model.mass(observation)
            elif method == 'interval':
                result = interval_probability(model, argument, upper)
            elif method == 'moment':
                result = moment(model, order)
            else:
                result = distribution_value(model, method, argument)
            return {'result': result, 'distribution': model.document()}

        def accept(data):
            if 'population' in data:
                records = data['records']
                if records:
                    journal = getattr(self.window, '_result_journal', None)
                    parent, ids = store_realizations(self.window.project, data['distribution'], records,
                                                     tool=journal.origin if journal else None)
                    self.window.register_publication(parent, data['distribution'])
                    for record_id, record in zip(ids, records, strict=True):
                        self.window.register_publication(record_id, record)
                    self._display_realizations(records)
                self._population_report(label, data['population'], records)
            else:
                result = data['result']
                rows = [('Valor', _result_text(result))] if 'status' in result else [
                    ({'density': 'Densidad conjunta', 'log_density': 'Log densidad', 'mass': 'Masa conjunta',
                      'log_mass': 'Log masa'}[name], _result_text(value)) for name, value in result.items()]
                if result.get('log_value') is not None:
                    rows.append(('Log probabilidad', number(result['log_value'])))
                self.report.set_readable(Summary(label, [Section(_METHODS[method], rows=rows)]))
            self.tabs.setCurrentIndex(0 if data.get('records') else 1)

        self.window._run_operation('Calculando probabilidad…', calculate, accept)

    def _calculate_process(self, key, generating):
        parameters = {}
        for name in PROCESSES[key][1]:
            field = self.fields[f'{key}.{name}']
            if name == 'transition':
                from .state_space_panel import matrix
                transition = matrix(field.text())
                if np.any(transition.imag):
                    raise ValueError('Las probabilidades de transición deben ser reales.')
                parameters[name] = transition.real
            elif name == 'initial' and key == 'markov':
                from .systems_panel import parse_list
                start = field.text().strip()
                if ',' in start:
                    weights = parse_list(start)
                    if np.any(weights.imag):
                        raise ValueError('Las probabilidades iniciales deben ser reales.')
                    parameters[name] = weights.real
                else:
                    parameters[name] = integer_field(field) if start else 'stationary'
            elif name == 'initial' and key in ('telegraph', 'ornstein_uhlenbeck') and not field.text().strip():
                parameters[name] = None
            else:
                parser = integer_field if name == 'initial' and key in ('telegraph', 'poisson_process') else real_field
                parameters[name] = parser(field)
        rate = real_field(self.sample_rate) if key in PHYSICAL_PROCESSES or (
            generating and self.sample_rate.text().strip()) else None
        if generating:
            count, seed = integer_field(self.count, minimum=1), integer_field(self.seed)
            replicas, origin = integer_field(self.replicas), integer_field(self.origin)
            first, second = 0, min(1, count-1)
        else:
            first = integer_field(self.theory_first, minimum=0)
            second = integer_field(self.theory_second, minimum=0)
        label = PROCESSES[key][0]

        def calculate():
            model = Process(key, parameters)
            moments = process_moments(model, first, second, rate=rate)
            transition = process_transition(model, abs(second-first), rate=rate)
            records = (generate_process(model, count, seed, replicas=replicas, origin=origin, rate=rate)
                       if generating else ())
            return {'moments': moments, 'transition': transition, 'records': records}

        def accept(data):
            records = data['records']
            summary = _process_report(label, data)
            if records:
                self._publish_batch(store_processes, data['moments']['model'], data)
            else:
                self.window.publish(data, title=label, operation='Propiedades teóricas de un proceso')
            self.report.set_readable(summary)
            self.tabs.setCurrentIndex(0 if records else 1)

        self.window._run_operation('Calculando proceso estocástico…', calculate, accept)

    def _calculate_noise(self, key, generating):
        from .systems_panel import parse_list

        label, names = NOISES[key]
        parameters = {}
        for name in names:
            field = self.fields[f'{key}.{name}']
            if name == 'complex':
                parameters[name] = field.isChecked()
            elif name == 'color':
                parameters[name] = field.currentData()
            elif name in ('frequency_hz', 'density', 'taps'):
                values = parse_list(field.text())
                if name != 'taps' and np.any(values.imag):
                    raise ValueError('La frecuencia y la densidad deben contener valores reales.')
                parameters[name] = values if name == 'taps' else values.real
            else:
                parameters[name] = real_field(field)
        rate = real_field(self.sample_rate) if (self.sample_rate.text().strip() or key in FREQUENCY_NOISES
                                               or not generating) else None
        count = integer_field(self.count, minimum=1)
        if generating:
            seed, replicas = integer_field(self.seed), integer_field(self.replicas)
            origin = integer_field(self.origin)

        def calculate():
            model = Noise(key, parameters)
            if not generating:
                return noise_spectrum(model, count, rate=rate)
            records = generate_noise(model, count, seed, replicas=replicas, origin=origin, rate=rate)
            return {'model': model.document(), 'records': records}

        def accept(result):
            if generating:
                records = result['records']
                variance = records[0].metadata['theoretical_variance']
                self._publish_batch(store_noise, result['model'], result)
                sections = [Section('Modelo', rows=[('Media teórica', '0'), ('Varianza teórica', number(variance)),
                                                   ('Réplicas independientes', len(records))])]
            else:
                key = self.window.publish(result, operation='PSD teórica de ruido')
                self.output.show_result(result)
                self.output.result_ids = [key]
                self.sample_choice.hide()
                sections = [Section('Densidad espectral de potencia',
                                    rows=[('Varianza teórica', number(result.metadata['variance'])),
                                          ('Espaciado (Hz)', number(result.step))],
                                    paragraphs=['La PSD es bilateral y se expresa en unidades de amplitud al cuadrado por Hz.'])]
            self.report.set_readable(Summary(label, sections))
            self.tabs.setCurrentIndex(0)

        self.window._run_operation('Calculando ruido estocástico…', calculate, accept)

    def _publish_batch(self, store, document, data):
        records = data['records']
        journal = getattr(self.window, '_result_journal', None)
        if journal is not None:
            journal.reported(data, outputs_registered=True)
        parent, ids = store(self.window.project, document, records, tool=journal.origin if journal else None)
        self.window.register_publication(parent, document)
        for key, record in zip(ids, records, strict=True):
            self.window.register_publication(key, record)
        self._display_realizations(records)

    def _display_realizations(self, records):
        self._samples = records
        self.sample_choice.blockSignals(True)
        self.sample_choice.clear()
        self.sample_choice.addItems([record.name for record in records])
        self.sample_choice.blockSignals(False)
        self.sample_choice.setVisible(len(records) > 1)
        self._show_sample(0)
        self.tabs.setCurrentIndex(0)

    def _population_report(self, label, theory, records):
        keys = {'mean': 'Media', 'variance': 'Varianza', 'covariance': 'Covarianza',
                'pseudocovariance': 'Pseudocovarianza', 'real_rank': 'Rango en coordenadas reales'}
        rows = [(title, _result_text(theory[name])) for name, title in keys.items()
                if name in theory and theory[name] is not None]
        sections = [Section('Propiedades poblacionales', rows=rows)]
        if records:
            sample_rows = [
                ('Registros', len(records)), ('Muestras por registro', len(records[0].values)),
                ('Semilla', records[0].metadata['seed']),
            ]
            if 'sample_rate_hz' in records[0].metadata:
                sample_rows.append(('Frecuencia de muestreo (Hz)', number(records[0].metadata['sample_rate_hz'])))
            sections.append(Section('Muestras generadas', rows=sample_rows,
                                    paragraphs=['Elegí una realización en la pestaña de resultados o reutilizala desde la biblioteca.']))
        self.report.set_readable(Summary(label, sections))

    def calculate(self):
        try:
            if self.action=='generate':
                self._calculate_distribution()
            elif self.analysis.currentData() != 'describe':
                self._calculate_inference()
            else:
                source=self.source.read();parent=self.source.reference_id;component=PROJECTIONS[self.component.currentIndex()]
                from .auxiliary import optional
                bins,bins_notice=optional('Intervalos del histograma',lambda:integer_field(self.bins))
                diagnostics=self.diagnostics.isChecked()
                reference=None
                if diagnostics and self.reference_normal.isChecked():
                    family=self.reference_family.currentData()
                    if family=='normal':
                        reference=Distribution(family,{'mean':real_field(self.reference_mean),'std':real_field(self.reference_std)})
                    else:
                        reference=Distribution(family,self._statistical_parameters(family))

                def calculate():
                    data=random_signals.statistics(source,component,bins,histogram_notice=bins_notice)
                    data['descriptive']=describe_record(source,component,diagnostics=diagnostics,reference=reference)
                    return data

                def accept(data):
                    self.window.publish(data,title='Estadísticas de '+source.name,operation='Estadísticas de registro',parents=[parent] if parent else [])
                    self.output.show_result(source)
                    labels = {'variance_N': 'Varianza con divisor N', 'variance_N_minus_1': 'Varianza con divisor N−1',
                              'mean_square': 'Valor cuadrático medio', 'rms': 'RMS'}
                    states = {'underflow': 'Por debajo del rango de float64',
                              'overflow': 'Excede el rango de float64', 'undefined': 'No definida con una muestra'}
                    lines = [f"Registro: {source.name}", f"Muestras: {data['samples']}",
                             f"Media real: {data['mean_real']}", f"Media imaginaria: {data['mean_imag']}"]
                    for key, label in labels.items():
                        lines.append(f"{label}: {states.get(data['range_status'][key], data[key])}")
                    lines.extend(('', data['scope'], '', 'El histograma estima la densidad por intervalos. El área total es 1.'))
                    self.report.setPlainText('\n'.join(lines) + '\n\n' + _descriptive_report(data['descriptive']))
                    if data.get('histogram_notice'):self.report.appendPlainText('\n'+data['histogram_notice'])
                    self._statistics=data
                    self.tabs.setTabEnabled(2, True)
                    choices=[('Histograma','histogram')]
                    if 'empirical' in data['descriptive']:
                        choices.extend([('CDF empírica','cdf'),('CCDF empírica','survival'),('Diagrama de caja','boxplot')])
                    if 'qq' in data['descriptive']:
                        choices.append(('Gráfico Q–Q','qq'))
                    self.plot_kind.blockSignals(True)
                    self.plot_kind.clear()
                    for label,key in choices:
                        self.plot_kind.addItem(label,key)
                    self.plot_kind.blockSignals(False)
                    self._draw_statistics()
                    self.tabs.setCurrentIndex(1)
                self.window._run_operation('Calculando estadísticas…',calculate,accept)
        except Exception as exc:show_input_error(self,'Revisá las entradas',exc)

    def _statistical_parameters(self, family):
        from .systems_panel import parse_list

        parameters={}
        for name,_,rule in FAMILIES[family].parameters:
            field=self.fields[name]
            if rule=='vector':
                values=parse_list(field.text())
                if np.any(values.imag):
                    raise ValueError('Las probabilidades por categoría deben ser reales.')
                parameters[name]=values.real
            else:
                parser=integer_field if rule in ('integer','count','positive_count') else real_field
                parameters[name]=parser(field)
        return parameters

    def _calculate_inference(self):
        fitting = self.analysis.currentData() == 'fit'
        method = self.inference_method.currentData()
        projection = PROJECTIONS[self.component.currentIndex()]
        fields = (self.source, self.second_source) if not fitting and method in TWO_SAMPLES else (self.source,)
        signals = [field.read(register=False) for field in fields]
        registrations = [field.input_registration(signal) for field, signal in zip(fields, signals, strict=True)]
        records = tuple((signal, key, parents) for signal, (key, _, parents) in zip(signals, registrations, strict=True))
        if len(records) == 2 and records[0][1] is not None and records[0][1] == records[1][1]:
            raise ValueError('Elegí otro registro para la segunda muestra.')
        revisions = [(field.entry_modes.view, getattr(field, 'source_revision', 0)) for field in fields]
        if fitting:
            operation, service = 'Ajuste de distribución', fit_distribution
            family = self.fit_family.currentData()
            parameters = {'family': family, 'estimator': self.fit_method.currentData(),
                          'trials': integer_field(self.fit_trials) if family == 'binomial' else None}
            if family in FIT_INTERVALS and self.fit_interval.isChecked():
                parameters.update(level=real_field(self.confidence_level), iid=self.iid.isChecked())
        else:
            operation, service = 'Inferencia estadística', infer_record
            parameters = {'method': method, 'iid': self.iid.isChecked(), 'level': real_field(self.confidence_level)}
            if len(signals) == 2:
                parameters['second'] = signals[1]
            if method in NULL_PARAMETER:
                parameters['null'] = real_field(self.null_value)
            if method in NULL_PARAMETER or method == 'mann_whitney':
                parameters['alternative'] = self.alternative.currentData()
            if method == 'z':
                parameters['known_std'] = real_field(self.known_std)
            if method == 'ljung_box':
                parameters.update(lags=integer_field(self.lags), fitted_parameters=integer_field(self.fitted_parameters))
            elif method == 'ks':
                family = self.ks_family.currentData()
                parameters['reference'] = Distribution(family,self._statistical_parameters(family))

        def calculate():
            return service(signals[0], component=projection, **parameters)

        def accept(result):
            summary = _inference_report(result)
            journal = getattr(self.window, '_result_journal', None)
            if journal is not None:
                journal.reported(result)
            keys, report_id = store_statistics(self.window.project, result, records, operation,
                                               tool=journal.origin if journal else None)
            for field, key, signal, (_, signature, _), (view, revision) in zip(
                fields, keys, signals, registrations, revisions, strict=True,
            ):
                self.window.register_publication(key, signal)
                if field.entry_modes.view == view and getattr(field, 'source_revision', 0) == revision:
                    field.remember_registration(key, signature)
            self.window.register_publication(report_id, result)
            self.output.show_result(signals[0])
            self.report.set_readable(summary)
            self.tabs.setTabEnabled(2, False)
            self.tabs.setCurrentIndex(1)

        self.window._run_operation('Calculando ' + operation.lower() + '…', calculate, accept)

    def _draw_statistics(self,*_):
        if self._statistics is None:
            return
        data=self._statistics
        self.figure.clear()
        axis=self.figure.add_subplot(111)
        _statistical_plot(axis,self.plot_kind.currentData(),data)
        self.canvas.draw_idle()


def _descriptive_report(result):
    labels={'mean':'Media','median':'Mediana','variance_N':'Varianza con divisor N',
            'variance_N_minus_1':'Varianza con divisor N−1','standard_deviation_N':'Desviación estándar',
            'rms':'RMS','skewness':'Asimetría','excess_kurtosis':'Exceso de curtosis',
            'iqr':'Rango intercuartílico','mad':'Mediana de las desviaciones absolutas'}
    rows=[('Observaciones',result['sample_count']),('Excluidas',result['excluded'])]
    rows.extend((label,_result_text(result[key])) for key,label in labels.items())
    modes=result['mode']['values']
    rows.append(('Moda',_result_text(modes) if modes else 'Sin valores repetidos'))
    if 'circular' in result:
        circular=result['circular']
        rows.extend((('Dirección media (rad)',_result_text(circular['mean_direction_rad'])),
                     ('Varianza circular',_result_text(circular['circular_variance']))))
    sections=[
        Section('Medidas de la componente',rows=rows,paragraphs=[result['scope']]),
        Section('Cuantiles',rows=[(f"{100*q['probability']:g} %",_result_text(q)) for q in result['quantiles']]),
        Section('Momentos',rows=[
            (f'Orden {i}',f"No central {_result_text(raw)} · Central {_result_text(centered)}")
            for i,(raw,centered) in enumerate(zip(result['raw_moments'],result['central_moments'],strict=True))]),
    ]
    if 'boxplot' in result:
        sections.append(Section('Diagrama de caja',rows=[('Atípicos',result['boxplot']['outliers'])],
                                paragraphs=['Los bigotes alcanzan observaciones dentro de 1,5 rangos intercuartílicos.']))
    if 'reference' in result:
        law=result['reference']
        section=Section('Comparación teórica',rows=[('Distribución',FAMILIES[law['family']].label)])
        section.rows.extend((_PARAMETERS[key][0],_result_text(value)) for key,value in law['parameters'].items())
        sections.append(section)
    return Summary(_PROJECTION_LABELS[result['component']],sections).plain_text()


def _inference_report(result):
    sections = []
    if result['operation'] == 'distribution_fit':
        model = result['estimated_distribution']
        method = {'ml': 'Máxima verosimilitud', 'moments': 'Método de los momentos'}[result['estimator']]
        rows = [('Estimador', method), ('Log verosimilitud', _result_text(result['log_likelihood']))]
        rows.extend((_PARAMETERS[key][0], number(value)) for key, value in model['parameters'].items())
        sections.append(Section(FAMILIES[model['family']].label, rows=rows))
        if 'confidence_intervals' in result:
            intervals = result['confidence_intervals']
            rows = [(_PARAMETERS[key][0], _interval_text(bounds)) for key, bounds in intervals['parameters'].items()]
            sections.append(Section(f"Intervalos bilaterales ({100 * intervals['level']:g} %)", rows=rows,
                                    paragraphs=[intervals['method']]))
        title = 'Ajuste de distribución'
    else:
        title = METHODS[result['method']]
        decision = {True: 'Rechazar H₀', False: 'Sin evidencia suficiente para rechazar H₀',
                    None: 'La tabla de calibración no permite decidir con el nivel elegido'}[result['reject_null']]
        relation = {'at_most': '≤ ', 'at_least': '≥ '}.get(result.get('p_value_relation'), '')
        rows = [('Hipótesis nula', result.get('null_description', 'El parámetro coincide con el valor indicado.')),
                ('Estadístico', _result_text(result['statistic'])), ('Valor p', relation + number(result['p_value'])),
                ('Significación α', number(result['alpha'])), ('Decisión', decision)]
        if 'estimate' in result:
            rows.extend((('Valor bajo H₀', number(result['null_value'])), ('Estimación', _result_text(result['estimate'])),
                         (f"Intervalo bilateral ({100 * result['level']:g} %)",
                          _interval_text(result['interval']))))
        if result['method'] in NULL_PARAMETER or result['method'] == 'mann_whitney':
            rows.append(('Alternativa', {'two-sided': 'Distinta', 'less': 'Menor', 'greater': 'Mayor'}[result['alternative']]))
        if 'known_std' in result:
            rows.append(('Desviación conocida', number(result['known_std'])))
        if 'lags' in result:
            rows.extend((('Cantidad de retardos', result['lags']), ('Parámetros estimados', result['fitted_parameters'])))
        if 'degrees_of_freedom' in result and result['degrees_of_freedom'] is not None:
            rows.append(('Grados de libertad', _result_text(result['degrees_of_freedom'])))
        if 'reference' in result:
            reference = result['reference']
            rows.append(('Distribución de referencia', FAMILIES[reference['family']].label))
            rows.extend((_PARAMETERS[key][0], number(value)) for key, value in reference['parameters'].items())
        sections.append(Section('Contraste', rows=rows, paragraphs=[result['calibration']]))
    observations = [('Componente', _PROJECTION_LABELS[result['component']])]
    for index, (count, excluded, axes) in enumerate(zip(result['sample_counts'], result['excluded'], result['inputs'], strict=True), 1):
        suffix = f' ({index})' if len(result['inputs']) > 1 else ''
        observations.extend((('Observaciones'+suffix, count), ('Excluidas'+suffix, excluded)))
        if axes['amplitude_units']:
            observations.append(('Unidad de amplitud'+suffix, axes['amplitude_units']))
    sections.append(Section('Muestras', rows=observations, paragraphs=[result['scope']]))
    return Summary(title, sections)


def _interval_text(bounds):
    return '[' + ', '.join(map(_result_text, bounds)) + ']'


def _process_report(label, data):
    moments, transition = data['moments'], data['transition']
    rows = []
    for offset, mean, variance in zip(moments['offsets'], moments['means'], moments['variances'], strict=True):
        rows.extend(((f'Media en {offset}', _result_text(mean)), (f'Varianza en {offset}', _result_text(variance))))
    rows.append(('Covarianza entre ambas posiciones', _result_text(moments['covariance'])))
    rows.append(('Inicio en equilibrio', 'Sí' if moments['stationary_initialization'] else 'No'))
    rate = moments['sample_rate_hz']
    if rate is not None:
        rows.append(('Frecuencia de muestreo (Hz)', number(rate)))
    sections = [Section('Momentos teóricos', rows=rows, paragraphs=[moments['scope']])]
    rows = [('Pasos desde un estado al otro', transition['steps'])]
    labels = {'transition': 'Matriz de transición', 'state_values': 'Valores de los estados',
              'initial_distribution': 'Probabilidades iniciales', 'stationary_distribution': 'Distribución estacionaria única',
              'conditional_std': 'Desviación condicional', 'stationary_std': 'Desviación en equilibrio',
              'location_increment': 'Término independiente de la media', 'state_coefficient': 'Coeficiente del estado previo',
              'event_mean': 'Media de eventos en el intervalo'}
    rows.extend((label, _result_text(transition[key]) if transition[key] is not None else 'No identificada')
                for key, label in labels.items() if key in transition)
    sections.append(Section('Transición', rows=rows))
    if data['records']:
        sections.append(Section('Trayectorias', rows=[('Réplicas independientes', len(data['records'])),
                                                     ('Muestras por réplica', len(data['records'][0].values))]))
    return Summary(label, sections)


def _statistical_plot(axis,choice,data):
    result=data['descriptive']
    label=_PROJECTION_LABELS[result['component']]
    if choice=='histogram':
        edges=np.asarray(data['histogram_edges'])
        axis.bar(edges[:-1],data['histogram_density'],width=np.diff(edges),align='edge',alpha=.8)
        axis.set_xlabel(label);axis.set_ylabel('Densidad empírica')
        if data.get('histogram_notice'):
            axis.set_axis_off()
            axis.text(.5,.5,data['histogram_notice'],ha='center',va='center',wrap=True,transform=axis.transAxes)
    elif choice in ('cdf','survival'):
        empirical=result['empirical']
        axis.step(empirical['x'],empirical[choice],where='post',label='Registro')
        reference=empirical.get('reference_'+choice)
        if reference is not None:
            law=FAMILIES[result['reference']['family']]
            style={'linestyle':'None','marker':'.'} if law.discrete else {}
            axis.plot(empirical['reference_axis'],[row['value'] if row['status']=='finite' else np.nan for row in reference],
                      label=law.label+' de referencia',**style)
            axis.legend()
        axis.set_xlabel(label)
        axis.set_ylabel('P(X ≤ x)' if choice=='cdf' else 'P(X > x)')
        axis.set_ylim(-.03,1.03)
    elif choice=='boxplot':
        lower,middle,upper=[row['value'] for row in result['boxplot']['quartiles']]
        first,last=[row['value'] for row in result['boxplot']['whiskers']]
        axis.bxp([dict(label=label,q1=lower,med=middle,q3=upper,whislo=first,whishi=last)],showfliers=False)
    else:
        qq=result['qq']
        theoretical=[row['value'] if row['status']=='finite' else np.nan for row in qq['theoretical']]
        axis.scatter(theoretical,qq['observed'],s=12)
        axis.set_xlabel('Cuantiles de '+FAMILIES[result['reference']['family']].label)
        axis.set_ylabel('Observados · '+label)
    axis.grid(alpha=.2)


def _result_text(result):
    if isinstance(result, dict) and 'status' in result:
        return number(result['value']) if result['status'] == 'finite' else _STATES.get(result['status'], result['status'])
    if isinstance(result, dict) and set(result) == {'real', 'imag'}:
        result = np.asarray(result['real']) + 1j * np.asarray(result['imag'])
    return np.array2string(np.asarray(result), precision=6, threshold=24)
