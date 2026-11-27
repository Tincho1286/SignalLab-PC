"""Workbench adapter for the discrete Kalman estimator."""

import numpy as np
from PySide6.QtWidgets import (QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QScrollArea, QTabWidget, QVBoxLayout, QWidget)

from .kalman_filter import kalman_filter, store_kalman
from .matrix_editor import MatrixEditor
from .numeric_input import integer_field, real_field
from .report_view import ReportView, report_panel
from .result_state import ResultState
from .result_summary import Section, Summary, number
from .state_result_actions import install_model_import
from .state_space import StateModel
from .state_space_panel import matrix, matrix_text
from .systems_panel import parse_list
from .validation import show_input_error


class KalmanPanel(QWidget):
    def __init__(self, window):
        super().__init__()
        from .toolbox import ResultView
        self.window = window
        self.model_parent = None
        self.results = []
        root = QHBoxLayout(self)
        controls = QWidget()
        form = QFormLayout(controls)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        note = QLabel('Cada fila de las mediciones es un instante. En la máscara opcional, 1 indica un dato presente y 0 un dato ausente. Dejá vacíos los controles si la entrada aplicada es cero.')
        note.setWordWrap(True)
        form.addRow(note)
        load = QPushButton('Cargar modelo…')
        self.model_import = install_model_import(load, window, self.set_model, self.choose_model)
        form.addRow(load)
        self.period = QLineEdit()
        self.origin = QLineEdit('0')
        self.initial = QLineEdit()
        form.addRow('Período de muestreo (s)', self.period)
        form.addRow('Primer índice n', self.origin)
        form.addRow('Estado inicial (media por componente)', self.initial)
        pages = QTabWidget()
        self.matrices = {}
        for title, items in (
            ('Modelo', [('A', 'Evolución A'), ('B', 'Entradas B'), ('C', 'Observación C'), ('D', 'Paso directo D')]),
            ('Covarianzas', [('Q', 'Proceso Q'), ('R', 'Medición R'), ('P', 'Estado inicial P₀')]),
            ('Datos', [('y', 'Mediciones y'), ('u', 'Controles u'), ('mask', 'Máscara')]),
        ):
            group = QTabWidget()
            for key, label in items:
                field = MatrixEditor()
                self.matrices[key] = field
                group.addTab(field, label)
            pages.addTab(group, title)
        form.addRow(pages)
        self.button = QPushButton('Estimar estados')
        self.button.setObjectName('primary')
        self.button.clicked.connect(self.calculate)
        form.addRow(self.button)
        self.state = ResultState([self.period, self.origin, self.initial, *self.matrices.values()], self.button)
        form.insertRow(0, self.state)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(controls)
        root.addWidget(scroll, 1)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 2)
        self.report = ReportView()
        self.tabs.addTab(report_panel(self.report), 'Informe')
        graph = QWidget()
        view = QVBoxLayout(graph)
        self.selector = QComboBox()
        self.selector.setProperty('sessionTransient', True)
        self.selector.setAccessibleName('Componentes estimadas y varianzas')
        self.selector.currentIndexChanged.connect(self.show_result)
        view.addWidget(self.selector)
        self.output = ResultView()
        view.addWidget(self.output, 1)
        self.tabs.addTab(graph, 'Trayectorias')
        self.tabs.setTabVisible(1, False)

    def choose_model(self):
        key = self.window.choose_record('state_space', ['digital'])
        if key is not None:
            self.set_model(self.window.project.get(key), key)

    def set_model(self, model, key=None):
        if model.dt is None:
            show_input_error(self, 'Modelo de Kalman', ValueError('Convertí el modelo continuo a un modelo discreto.'))
            return
        for label in 'ABCD':
            self.matrices[label].setText(matrix_text(getattr(model, label)))
        self.period.setText(repr(model.dt))
        self.model_parent = key

    def calculate(self):
        try:
            fields = {key: matrix(field.text()) for key, field in self.matrices.items()}
            period = real_field(self.period, minimum=0, strict=True)
            origin = integer_field(self.origin)
            initial = parse_list(self.initial.text())
            control = fields['u'] if fields['u'].size else None
            raw_mask = fields['mask']
            if raw_mask.size and not np.isin(raw_mask, (0, 1)).all():
                raise ValueError('La máscara solo admite 0 para ausente y 1 para presente.')
            mask = raw_mask.real.astype(bool) if raw_mask.size else None
            parent = self.model_parent
            registered = self.window.project.get(parent) if parent is not None else None
            components = [fields[key] for key in 'ABCD']
            if registered is not None and registered.dt == period and all(
                np.array_equal(getattr(registered, label), values) for label, values in zip('ABCD', components)
            ):
                model = registered
            else:
                model, parent = StateModel(*components, period, 'Modelo para Kalman'), None
            snapshot = self.state.snapshot()

            def compute():
                return kalman_filter(model, fields['y'], fields['Q'], fields['R'], initial, fields['P'],
                                     controls=control, mask=mask)

            self.window._run_operation('Estimando estados…', compute,
                                       lambda result: self.accept(model, parent, origin, result, snapshot))
        except Exception as error:
            show_input_error(self, 'Revisá el modelo y las observaciones', error)

    def accept(self, model, parent, origin, result, snapshot):
        journal = getattr(self.window, '_result_journal', None)
        if journal is not None:
            journal.reported(result.report, outputs_registered=True)
        project = self.window.project
        saved = store_kalman(project, model, result, model_id=parent, origin=origin,
                             tool=journal.origin if journal else None)
        self.window.register_publication(saved['model'], model)
        self.window.register_publication(saved['report'], project.get(saved['report']))
        self.selector.blockSignals(True)
        self.selector.clear()
        self.results = []
        for key, record in saved['outputs']:
            self.window.register_publication(key, record)
        for index in range(model.states):
            prediction, correction, variance = saved['outputs'][3*index:3*index+3]
            self.results.extend(((prediction, correction), (variance,)))
            self.selector.addItem(f'Predicción y corrección · estado {index+1}')
            self.selector.addItem(f'Varianza posterior · estado {index+1}')
        self.selector.blockSignals(False)
        report = result.report
        final_state = ', '.join(number(value) for value in result.corrected[-1])
        final_var = ', '.join(number(value.real) for value in result.posterior_covariance[-1].diagonal())
        last_measurement = np.flatnonzero(result.observed.any(axis=1))
        diagnostics = []
        if last_measurement.size:
            last = last_measurement[-1]
            gains = result.gains[last][:, result.observed[last]]
            innovation = result.innovations[last, result.observed[last]]
            diagnostics.append(Section('Última corrección disponible', rows=[
                ('Índice', str(origin+last)), ('Innovación', ', '.join(number(value) for value in innovation))],
                paragraphs=['Ganancia K por estado', *(', '.join(number(value) for value in row) for row in gains)]))
        summary = Summary('Filtro lineal de Kalman', [Section('Estados y observaciones', rows=[
            ('Muestras', str(report['samples'])), ('Componentes medidas', str(report['observed_components'])),
            ('Componentes ausentes', str(report['missing_components'])),
            ('Instantes con solo predicción', str(report['prediction_only_steps'])),
            ('Último estado estimado', final_state), ('Última varianza por estado', final_var),
        ], paragraphs=[report['scope'], 'El proyecto guarda la covarianza y la ganancia de cada instante.']), *diagnostics])
        self.report.set_readable(summary)
        self.tabs.setTabVisible(1, True)
        self.show_result()
        self.state.accept(snapshot)

    def show_result(self, *_):
        index = self.selector.currentIndex()
        if 0 <= index < len(self.results):
            keys, curves = zip(*self.results[index], strict=True)
            self.output.show_result(curves)
            self.output.result_ids = list(keys)
