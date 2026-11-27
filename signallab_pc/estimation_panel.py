"""Workbench for Gaussian estimation and causal Wiener filtering."""

from PySide6.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QScrollArea, QTabWidget, QVBoxLayout, QWidget)

from .matrix_editor import MatrixEditor
from .numeric_input import integer_field, real_field
from .optimal_estimation import linear_gaussian, store_gaussian_estimate
from .report_view import ReportView, report_panel
from .result_state import ResultState
from .result_summary import Section, Summary, number
from .state_space_panel import matrix
from .system_result_actions import SystemResultActions
from .systems_panel import parse_list
from .validation import show_input_error
from .wiener_filter import store_wiener, store_wiener_model, wiener_fir, wiener_hopf


def _vector_text(values):
    return ', '.join(number(value) for value in values)


def _value(metric):
    if metric['value'] is None:
        return 'Fuera del rango numérico'
    return number(metric['value'])


def _gaussian_summary(result):
    rows = [('Observaciones', str(result['samples'])), ('Parámetros', str(result['parameters'])),
            ('Rango del modelo', str(result['rank']))]
    ml, posterior, reference = result['ml'], result['posterior'], result['reference']
    if ml is None:
        rows.append(('Máxima verosimilitud', 'Las observaciones no identifican una solución única'))
    else:
        rows.extend([('Estimación ML', _vector_text(ml['estimate'])), ('Varianza por parámetro', _vector_text(ml['variance'])),
                     ('MSE de ML', _value(ml['mse'])), ('Log-verosimilitud en ML', _value(ml['log_likelihood']))])
    sections = [Section('Modelo de observación', rows=rows, paragraphs=[result['scope']])]
    information = result['fisher_information']
    sections.append(Section('Información de Fisher', paragraphs=[_vector_text(row) for row in information]))
    if ml is not None:
        sections.append(Section('Cota de Cramér–Rao', paragraphs=[_vector_text(row) for row in ml['cramer_rao']]))
    if posterior is not None:
        sections.append(Section('Estimación bayesiana', rows=[
            ('MAP, MMSE y LMMSE', _vector_text(posterior['map'])),
            ('MSE bajo el modelo a priori', _value(posterior['bayes_mse']))],
            paragraphs=[posterior['scope'], 'Covarianza posterior', *(_vector_text(row) for row in posterior['covariance'])]))
    if reference is not None:
        rows = [('Log-verosimilitud en la referencia', _value(reference['log_likelihood']))]
        if posterior is not None:
            rows.extend([('Sesgo del estimador bayesiano en la referencia', _vector_text(reference['posterior_estimator_bias'])),
                         ('Varianza por parámetro', _vector_text(reference['posterior_estimator_variance'])),
                         ('MSE en la referencia', _value(reference['posterior_estimator_mse']))])
        sections.append(Section('Parámetro de referencia fijo', rows=rows))
    return Summary('Estimación gaussiana lineal', sections)


def _wiener_summary(result):
    taps = result['coefficients']
    entries = [('Coeficientes h[0], h[1], …', _vector_text(complex(re, im) for re, im in zip(taps['real'], taps['imag']))),
               ('Rango efectivo', str(result['rank']))]
    if result['method'] == 'wiener_hopf':
        entries.append(('MSE teórico', _value(result['theoretical_mse'])))
        description = 'Los coeficientes se obtienen a partir de correlaciones de un modelo estacionario.'
    else:
        offset = result['offset']
        entries.extend([('Término constante', number(complex(offset['real'], offset['imag']))),
                        ('Muestras de entrenamiento', str(result['training_samples'])),
                        ('MSE durante el entrenamiento', _value(result['training_mse']))])
        if result['validation_mse'] is not None:
            entries.extend([('Muestras de validación', str(result['validation_samples'])),
                            ('MSE fuera del entrenamiento', _value(result['validation_mse']))])
        description = result['scope']
        if result['fit_offset']:
            description += ' La transferencia reutilizable aplica los coeficientes FIR. Sumá el término constante para reproducir la estimación completa.'
    return Summary('Filtro de Wiener', [Section('Solución causal', rows=entries, paragraphs=[description])])


class EstimationPanel(QWidget):
    def __init__(self, window, task):
        super().__init__()
        from .toolbox import LocalInput, ResultView
        self.window = window
        self.task = task
        root = QHBoxLayout(self)
        controls = QWidget()
        self.form = QFormLayout(controls)
        self.form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.button = QPushButton('Calcular')
        self.button.setObjectName('primary')
        self.button.clicked.connect(self.calculate)
        if task == 'gaussian':
            fields, signals = self._gaussian_controls(), []
        else:
            fields = self._wiener_controls()
            self.observed = LocalInput('Registro observado x[n]', 'discrete')
            self.desired = LocalInput('Registro limpio o deseado d[n]', 'discrete')
            signals = [self.observed, self.desired]
            for field in signals:
                field.bind_project(window)
                self.form.addRow(field)
        self.form.addRow(self.button)
        self.state = ResultState(fields, self.button, signals)
        self.form.insertRow(0, self.state)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(controls)
        root.addWidget(scroll, 1)
        results = QWidget()
        layout = QVBoxLayout(results)
        root.addWidget(results, 2)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self.report = ReportView()
        self.tabs.addTab(report_panel(self.report), 'Informe')
        self.output = ResultView()
        self.tabs.addTab(self.output, 'Señales')
        self.tabs.setTabVisible(1, False)
        self.actions = SystemResultActions(window)
        layout.addWidget(self.actions)
        self.actions.setVisible(task == 'wiener')
        if task == 'wiener':
            self.mode.currentIndexChanged.connect(self._configure_wiener)
            self._configure_wiener()

    def _field(self, label, placeholder=''):
        widget = QLineEdit()
        widget.setPlaceholderText(placeholder)
        self.form.addRow(label, widget)
        return widget

    def _gaussian_controls(self):
        description = QLabel('Cada fila de A relaciona los parámetros con una observación de y. R es la covarianza conocida del ruido. Para estimación bayesiana, ingresá además la media previa y su covarianza P.')
        description.setWordWrap(True)
        self.form.addRow(description)
        self.data = self._field('Observaciones y', 'Separadas por comas')
        self.prior = self._field('Media a priori (opcional)', 'Una entrada por parámetro')
        self.truth = self._field('Parámetro fijo para comparar (opcional)')
        matrices = QTabWidget()
        self.design, self.noise, self.prior_covariance = (MatrixEditor() for _ in range(3))
        for label, field in [('Diseño A', self.design), ('Ruido R', self.noise), ('Previa P', self.prior_covariance)]:
            matrices.addTab(field, label)
        self.form.addRow(matrices)
        return [self.data, self.prior, self.truth, self.design, self.noise, self.prior_covariance]

    def _wiener_controls(self):
        self.mode = QComboBox()
        self.mode.addItems(['Ajustar desde registros', 'Diseñar desde correlaciones'])
        self.form.addRow('Datos disponibles', self.mode)
        self.length = self._field('Cantidad de coeficientes')
        self.reserve = self._field('Muestras finales de validación', '0')
        self.offset = QCheckBox('Ajustar también un término constante')
        self.form.addRow(self.offset)
        self.autocorrelation = self._field('Autocorrelación Rxx[k]', 'Separá desde k = 0 por comas')
        self.cross = self._field('Correlación Rdx[k]', 'E(d[n] · conjugado de x[n−k])')
        self.power = self._field('Potencia E(|d[n]|²)')
        return [self.mode, self.length, self.reserve, self.offset, self.autocorrelation, self.cross, self.power]

    def _configure_wiener(self):
        empirical = self.mode.currentIndex() == 0
        for widget, enabled in [(field, empirical) for field in
                                (self.observed, self.desired, self.length, self.reserve, self.offset)] + [
                                (field, not empirical) for field in (self.autocorrelation, self.cross, self.power)]:
            self.form.setRowVisible(widget, enabled)
            widget.setProperty('calculationInput', enabled)
        self.state.refresh()

    def calculate(self):
        try:
            registrations = ()
            if self.task == 'gaussian':
                mode = 'gaussian'
                data = parse_list(self.data.text())
                design, noise = matrix(self.design.text()), matrix(self.noise.text())
                prior = parse_list(self.prior.text()) if self.prior.text().strip() else None
                prior_covariance = matrix(self.prior_covariance.text()) if self.prior_covariance.text() else None
                truth = parse_list(self.truth.text()) if self.truth.text().strip() else None

                def compute():
                    return linear_gaussian(data, design, noise, prior_mean=prior,
                                           prior_covariance=prior_covariance, parameter=truth)
            elif self.mode.currentIndex() == 1:
                mode = 'wiener_model'
                auto = parse_list(self.autocorrelation.text())
                cross = parse_list(self.cross.text())
                power = real_field(self.power, minimum=0)

                def compute():
                    return wiener_hopf(auto, cross, power)
            else:
                mode = 'wiener_data'
                fields = (self.observed, self.desired)
                data = tuple(field.read(register=False) for field in fields)
                registrations = tuple((value, *field.input_registration(value)) for field, value in zip(fields, data))
                length = integer_field(self.length, minimum=1)
                reserve = integer_field(self.reserve, minimum=0) if self.reserve.text().strip() else 0
                offset = self.offset.isChecked()

                def compute():
                    return wiener_fir(*data, length, reserve=reserve, fit_offset=offset)
            snapshot = self.state.snapshot()
            self.window._run_operation('Calculando estimación…', compute,
                                       lambda result: self._accept(result, mode, registrations, snapshot))
        except Exception as error:
            show_input_error(self, 'Revisá los datos de estimación', error)

    def _accept(self, result, mode, registrations, snapshot):
        project = self.window.project
        journal = getattr(self.window, '_result_journal', None)
        tool = journal.origin if journal else None
        if journal is not None:
            journal.reported(result, outputs_registered=True)
        empirical = mode == 'wiener_data'
        if mode == 'gaussian':
            parent = store_gaussian_estimate(project, result, tool=tool)
            summary = _gaussian_summary(result)
            self.window.register_publication(parent, result)
        else:
            if empirical:
                inputs = tuple((value, key, origins) for value, key, _, origins in registrations)
                keys = store_wiener(project, result, inputs, tool=tool)
                for key, (value, _, _, _) in zip(keys['sources'], registrations, strict=True):
                    self.window.register_publication(key, value)
                report, system, estimate, error, reference, measurement = result
                labels = ['observed', 'reference', 'estimate', 'error']
                signals = (measurement, reference, estimate, error)
                for label, item in zip(labels, signals, strict=True):
                    self.window.register_publication(keys[label], item)
                self.output.show_result(signals)
                self.output.result_ids = [keys[label] for label in labels]
            else:
                report = result
                keys = store_wiener_model(project, report, tool=tool)
                system = project.get(keys['system'])
            self.window.register_publication(keys['report'], report)
            self.window.register_publication(keys['system'], system)
            self.actions.set_result(system, keys['system'])
            summary = _wiener_summary(report)
        self.tabs.setTabVisible(1, empirical)
        self.report.set_readable(summary)
        self.state.accept(snapshot)
