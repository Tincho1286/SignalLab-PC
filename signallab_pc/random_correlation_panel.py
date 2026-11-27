"""Auto/cross correlation, covariance matrices and trajectory comparisons."""
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox,
                               QCheckBox, QPushButton, QLabel, QScrollArea, QDialog, QDialogButtonBox,
                               QListWidget, QListWidgetItem, QAbstractItemView)

from .numeric_input import integer_field
from .result_state import ResultState
from .result_summary import Section, Summary, number
from .statistics_results import store_statistics
from .stochastic_covariance import covariance_matrix, ensemble_moments, estimate_correlation
from .validation import show_input_error


class RandomCorrelationPanel(QWidget):
    def __init__(self, window):
        super().__init__()
        from .toolbox import LocalInput, ResultView
        self.window = window
        self._selection = ()
        root = QHBoxLayout(self)
        controls = QWidget()
        layout = QVBoxLayout(controls)
        self.mode = QComboBox()
        for label, key in [('Autocorrelación', 'auto'), ('Correlación cruzada', 'cross'),
                           ('Matrices de covarianza y correlación', 'matrix'), ('Momentos de conjunto', 'ensemble')]:
            self.mode.addItem(label, key)
        layout.addWidget(self.mode)
        self.source = LocalInput('Registro x[n]', 'discrete')
        self.second = LocalInput('Registro y[n]', 'discrete')
        for field in (self.source, self.second):
            field.bind_project(window)
            layout.addWidget(field)
        self.select = QPushButton('Elegir registros del proyecto…')
        self.select.clicked.connect(self._select_records)
        layout.addWidget(self.select)
        self.selection = QLabel('Elegí uno o más registros de Resultados.')
        self.selection.setWordWrap(True)
        layout.addWidget(self.selection)
        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        layout.addLayout(form)
        self.mean = QCheckBox('Restar la media para calcular covarianza')
        form.addRow(self.mean)
        self.lag = QLineEdit()
        self.lag.setPlaceholderText('Automático: hasta 50 o N−1')
        form.addRow('Retardo máximo (muestras)', self.lag)
        self.divisor = QComboBox()
        self.divisor.addItems(['N: longitud observada', 'N−|k|: pares disponibles'])
        form.addRow('Divisor de la suma', self.divisor)
        self.method = QComboBox()
        for label, key in [('Automático', 'auto'), ('Suma directa', 'direct'), ('FFT', 'fft')]:
            self.method.addItem(label, key)
        form.addRow('Método', self.method)
        self.normalized = QCheckBox()
        form.addRow(self.normalized)
        self.sample = QCheckBox('Usar divisor muestral')
        self.sample.setChecked(True)
        form.addRow(self.sample)
        self.first_offset, self.second_offset = QLineEdit('0'), QLineEdit('1')
        form.addRow('Primera posición desde el inicio', self.first_offset)
        form.addRow('Segunda posición desde el inicio', self.second_offset)
        self.independent = QCheckBox('Las trayectorias son realizaciones independientes')
        form.addRow(self.independent)
        self.note = QLabel()
        self.note.setWordWrap(True)
        layout.addWidget(self.note)
        self.button = QPushButton('Calcular')
        self.button.setObjectName('primary')
        self.button.clicked.connect(self.calculate)
        layout.addWidget(self.button)
        fields = [self.mode, self.mean, self.lag, self.divisor, self.method, self.normalized, self.sample,
                  self.first_offset, self.second_offset, self.independent, self.selection]
        self.state = ResultState(fields, self.button, [self.source, self.second])
        layout.insertWidget(0, self.state)

        def configure(*_):
            mode = self.mode.currentData()
            series = mode in ('auto', 'cross')
            ensemble = mode == 'ensemble'
            self.source.setVisible(series)
            self.second.setVisible(mode == 'cross')
            self.source.setProperty('calculationInput', series)
            self.second.setProperty('calculationInput', mode == 'cross')
            self.select.setVisible(not series)
            self.selection.setVisible(not series)
            self.selection.setProperty('calculationInput', not series)
            self.normalized.setText('Dividir por √(Px·Py)' if mode == 'cross' else 'Dividir por el valor en retardo cero')
            self.sample.setText('Dividir por R−1' if ensemble else 'Dividir por N−1')
            for widget in (self.mean, self.lag, self.divisor, self.normalized, self.method):
                form.setRowVisible(widget, series)
                widget.setProperty('calculationInput', series)
            for widget in (self.first_offset, self.second_offset, self.independent, self.sample):
                enabled = not series if widget is self.sample else ensemble
                form.setRowVisible(widget, enabled)
                widget.setProperty('calculationInput', enabled)
            self.note.setText({
                'cross': 'Rxy[k] compara x[n+k] con y[n]. Un retardo positivo significa que el patrón aparece más tarde en x. Solo se usa el intervalo observado en ambos registros.',
                'auto': 'Los retardos grandes tienen menos pares. En cero se estima la potencia o, al restar la media, la varianza con divisor N.',
                'matrix': 'Cada registro es un canal. El cálculo toma las observaciones de los índices en común.',
                'ensemble': 'Cada registro es una trayectoria. Elegí dos posiciones medidas desde el inicio para estimar medias, covarianza e incrementos.',
            }[mode])
            self.state.refresh()

        self.mode.currentIndexChanged.connect(configure)
        configure()
        layout.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(controls)
        root.addWidget(scroll,1)
        self.output = ResultView()
        root.addWidget(self.output,2)

    def _select_records(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Registros del proyecto')
        layout = QVBoxLayout(dialog)
        choices = QListWidget()
        choices.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        choices.setMinimumHeight(200)
        layout.addWidget(choices)
        project = self.window.project
        for header in project.headers('signal'):
            key = header['id']
            data = project.describe(key)
            if data.get('domain') != 'discrete' or data.get('data_kind') != 'temporal':
                continue
            item = QListWidgetItem(f"{header['title']} · {data['count']} muestras")
            item.setData(Qt.ItemDataRole.UserRole, key)
            choices.addItem(item)
            item.setSelected(key in self._selection)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.select_records([item.data(Qt.ItemDataRole.UserRole) for item in choices.selectedItems()])

    def select_records(self, keys):
        self._selection = tuple(dict.fromkeys(keys))
        titles = [self.window.project.describe(key)['name'] for key in self._selection]
        self.selection.setText(
            f'{len(titles)} registros seleccionados. ' + ', '.join(titles[:3]) + ('…' if len(titles)>3 else '') if titles else
            'Elegí uno o más registros de Resultados.')
        self.state.refresh()

    def calculate(self):
        try:
            mode = self.mode.currentData()
            if mode in ('auto', 'cross'):
                fields = (self.source, self.second) if mode == 'cross' else (self.source,)
                values = [field.read(register=False) for field in fields]
                registrations = [field.input_registration(value) for field, value in zip(fields,values,strict=True)]
                sources = tuple((value,key,origins) for value,(key,_,origins) in zip(values,registrations,strict=True))
                revisions = [(field.entry_modes.view, getattr(field,'source_revision',0)) for field in fields]
                lag = integer_field(self.lag, minimum=0) if self.lag.text().strip() else None
                params = {'max_lag': lag, 'remove_mean': self.mean.isChecked(),
                          'denominator': 'N' if self.divisor.currentIndex() == 0 else 'overlap',
                          'normalize': self.normalized.isChecked(), 'method': self.method.currentData()}

                def calculate():
                    return estimate_correlation(*values, **params)
            else:
                fields, revisions, registrations = (), (), ()
                if not self._selection:
                    raise ValueError('Elegí registros en el proyecto.')
                sources = tuple((self.window.project.get(key), key, ()) for key in self._selection)
                values = [value for value, _, _ in sources]
                sample = self.sample.isChecked()
                if mode == 'ensemble':
                    if not self.independent.isChecked():
                        raise ValueError('Confirmá que las trayectorias son independientes.')
                    first, second = integer_field(self.first_offset,minimum=0), integer_field(self.second_offset,minimum=0)

                def calculate():
                    if mode == 'matrix':
                        return covariance_matrix(values, sample=sample)
                    return ensemble_moments(values, first, second, sample=sample)

            snapshot = self.state.snapshot()

            def accept(result):
                if isinstance(result, dict):
                    title = 'Matriz de covarianza' if mode == 'matrix' else 'Momentos de conjunto'
                    report = _set_report(result, title)
                else:
                    title, report = result.name, _lag_report(result)
                journal = getattr(self.window, '_result_journal', None)
                if journal is not None:
                    journal.reported(result, outputs_registered=True)
                keys, record = store_statistics(self.window.project, result, sources, title,
                                                tool=journal.origin if journal else None)
                for key, source in zip(keys, values, strict=True):
                    self.window.register_publication(key, source)
                for field, key, (_, signature, _), (view, revision) in zip(
                    fields, keys[:len(fields)], registrations, revisions, strict=True,
                ):
                    if field.entry_modes.view == view and getattr(field,'source_revision',0) == revision:
                        field.remember_registration(key, signature)
                self.window.register_publication(record, result)
                self.output.show_result(result, summary=report)
                self.output.result_ids = [record]
                self.state.accept(snapshot)

            self.window._run_operation('Estimando medidas estocásticas…', calculate, accept)
        except Exception as error:
            show_input_error(self, 'Revisá las entradas', error)


def _lag_report(result):
    meta = result.metadata
    report = Section('Estimación por retardo', rows=[
        ('Intervalo común', f"{meta['common_origin']} a {meta['common_last_index']}"),
        ('Muestras observadas', meta['input_samples']), ('Divisor', meta['denominator']),
        ('Pares en cada retardo', meta['pair_count_rule']),
        ('Algoritmo', 'FFT' if meta['method'].startswith('FFT') else 'Suma directa'),
    ], paragraphs=[meta['scope'], 'Rxy[k] multiplica x[n+k] por el conjugado de y[n] antes de sumar.'])
    return Summary(result.name, [report])


def _matrix_text(data):
    size = min(len(data['real']),6)
    result = np.empty((size,size), dtype=object)
    for index in np.ndindex(result.shape):
        re = data['real'][index[0]][index[1]]
        im = data['imag'][index[0]][index[1]]
        result[index] = 'N/D' if re is None else number(complex(re,im))
    text = np.array2string(result, threshold=36, formatter={'object': str})
    return text + '\nPrimeros 6 canales. La exportación conserva la matriz completa.' if len(data['real']) > size else text


def _set_report(result, title):
    rows = [('Divisor', result['divisor']), ('Observaciones', result.get('observations', result.get('replicas')))]
    if 'channels' in result:
        rows.append(('Canales en orden', ', '.join(result['channels'])))
    if 'offsets' in result:
        rows.extend([('Posiciones desde el inicio', ' y '.join(map(str,result['offsets']))),
                     ('Media en cada posición', ' y '.join(number(complex(*value)) for value in result['means'])),
                     ('Media del incremento', ', '.join(str(item['value']) for item in result['increment_mean'])),
                     ('Varianza del incremento', result['increment_variance']['value'])])
    scope = [result['scope']]
    if 'reference_notice' in result:
        scope.append(result['reference_notice'])
    sections = [Section('Datos observados', rows=rows, paragraphs=scope)]
    names = {'covariance': 'Covarianza', 'pseudocovariance': 'Pseudocovarianza', 'correlation': 'Correlación normalizada'}
    for key, label in names.items():
        if key in result:
            sections.append(Section(label, paragraphs=[_matrix_text(result[key])]))
    if 'recorded_model_reference' in result:
        reference = result['recorded_model_reference']
        sections.append(Section('Modelo registrado', rows=[
            ('Medias teóricas', ', '.join(str(item['value']) for item in reference['means'])),
            ('Varianzas teóricas', ', '.join(str(item['value']) for item in reference['variances'])),
            ('Covarianza teórica entre posiciones', reference['covariance']['value']),
        ]))
    return Summary(title, sections)
