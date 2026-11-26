"""Workbench tools for independent or integrated digital communications."""

from dataclasses import asdict, replace
from functools import partial
from pathlib import Path

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLineEdit, QMenu,
    QMessageBox, QVBoxLayout, QWidget, QPushButton,
)

from . import communications_figures as figures, session
from .communications_channel import AWGNSpec, add_awgn
from .communications_data import ConstellationSpec, SymbolClock, SymbolSequence, iq_signal
from .communications_experiment import ExperimentSpec, run_experiment
from .communications_metrics import QualitySpec, measure_quality
from .communications_modulation import build_constellation, decide_symbols, generate_bits, group_bits, modulate, parse_bits, ungroup_symbols
from .communications_pulses import PulseSpec, apply_pulse, design_pulse, matched_pulse_isi, upsample_symbols
from .communications_receiver import SynchronizationSpec, recover_symbols
from .communications_storage import decode_symbols, encode_bits, encode_symbols, load_experiment, store_experiment
from .communications_sweep import AXES, SweepSpec, axis_from_text, export_sweep_csv, load_sweep, load_sweep_run, run_sweep
from .execution import ExecutionContext
from .numeric_input import integer_field, real_field
from .plot_view import hide_plot
from .project import Project
from .result_state import ResultState
from .result_summary import Section, Summary, number
from .tool_workspace import ToolWorkspace
from .validation import show_input_error


_LABELS = {
    'link': 'Ejecutar enlace', 'modulate': 'Modular bits', 'pulse': 'Calcular pulso',
    'awgn': 'Aplicar AWGN', 'receive': 'Recuperar símbolos', 'decide': 'Decidir símbolos',
    'measure': 'Medir calidad', 'sweep': 'Ejecutar barrido',
}
_CONSTE = 'Constelación'
_IQ = 'I/Q'
_EYE = 'Ojo'
_SPECTRUM = 'Espectro'
_PSD = 'PSD'
_IMPULSE = 'Impulso del filtro'
_FREQUENCY = 'Respuesta del filtro'
_ERRORS = 'Tasas de error'
_COMPARISON = 'Comparación de corridas'
_VIEWS = {
    'link': (_CONSTE, _IQ, _EYE, _SPECTRUM, _PSD, _IMPULSE, _FREQUENCY, _ERRORS),
    'modulate': (_CONSTE, _IQ), 'pulse': (_IMPULSE, _FREQUENCY, _IQ), 'awgn': (_IQ, _PSD),
    'receive': (_IQ,), 'decide': (_CONSTE,), 'measure': (), 'sweep': (_COMPARISON,),
}


class _SymbolChoice(QComboBox):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.refresh()

    def refresh(self):
        previous = self.currentData()
        self.blockSignals(True)
        self.clear()
        self.addItem('Ingresar etiquetas', None)
        project = self.window.project
        for row in reversed(project.headers('calculation')):
            payload = project.get(row['id'])
            if payload.get('format') == 'signallab-communications' and payload.get('kind') == 'symbols':
                self.addItem(row['title'], row['id'])
        self.setCurrentIndex(max(0, self.findData(previous)))
        self.blockSignals(False)

    def showPopup(self):
        self.refresh()
        super().showPopup()


def _quality_section(metrics):
    rows = []
    notes = []
    for caption, rate in (('BER', metrics.ber), ('SER', metrics.ser)):
        rows.append((caption, f'{rate.errors:,} / {rate.evaluated:,} · {rate.value:.6g}'))
        if rate.confidence is not None:
            bound = rate.confidence
            rows.append((f'{caption} · intervalo al {bound.level:.0%}', f'{bound.lower:.4g} a {bound.upper:.4g}'))
        if rate.evidence == 'zero_observed':
            notes.append(f'{caption} observó cero errores en el registro evaluado.')
        elif rate.evidence == 'few_errors':
            notes.append(f'{caption} se estima a partir de pocos errores.')
    evm = metrics.evm
    if evm.rms is not None:
        rows.append(('EVM RMS', number(evm.rms)))
    if evm.percent is not None:
        rows.append(('EVM (%)', number(evm.percent)))
    if evm.db is not None:
        rows.append(('EVM (dB)', number(evm.db)))
    if evm.reference_name:
        rows.append(('Referencia I/Q', evm.reference_name))
    rows.extend([('Símbolos TX excluidos', metrics.transmitted_excluded_symbols),
                 ('Símbolos RX excluidos', metrics.received_excluded_symbols),
                 ('Bits de relleno excluidos', metrics.excluded_padding_bits)])
    if evm.status == 'reference_unavailable':
        notes.append('La EVM se obtiene al aportar las dos secuencias I/Q alineadas.')
    elif evm.status == 'zero_reference':
        notes.append('La EVM queda indefinida porque la referencia tiene energía cero.')
    return Section('Calidad de recepción', paragraphs=notes, rows=rows)


def _noise_section(stats):
    values = [('Potencia media del registro', stats.measured_signal_power), ('Potencia de referencia', stats.reference_power),
              ('Energía Es', stats.symbol_energy), ('Energía Eb', stats.bit_energy), ('N₀', stats.n0),
              ('SNR por muestra (dB)', stats.snr_db), ('Es/N₀ (dB)', stats.es_n0_db), ('Eb/N₀ (dB)', stats.eb_n0_db),
              ('Varianza nominal I', stats.nominal_variance_i), ('Varianza nominal Q', stats.nominal_variance_q),
              ('Varianza observada I', stats.measured_variance_i), ('Varianza observada Q', stats.measured_variance_q)]
    return Section('Canal AWGN', rows=[(label, number(value)) for label, value in values if value is not None])


def _sync_section(sync):
    names = {'ideal': 'Referencia conocida', 'assisted': 'Alineación asistida',
             'estimated': 'Estimación con piloto', 'unavailable': 'Sin sincronización disponible'}
    rows = [('Estado', names[sync.state])]
    for label, value in (('Desplazamiento (muestras)', sync.sample_offset), ('Índice del registro', sync.source_index),
                         ('Fase compensada (rad)', sync.phase_rad), ('Correlación', sync.score),
                         ('Segunda correlación', sync.runner_up)):
        if value is not None:
            rows.append((label, number(value)))
    if sync.searched_offsets is not None:
        rows.append(('Intervalo de búsqueda', f'{sync.searched_offsets[0]} a {sync.searched_offsets[1]}'))
    return Section('Sincronización', paragraphs=[] if sync.reason is None else [sync.reason], rows=rows)


class CommunicationsPanel(QWidget):
    def __init__(self, window, mode):
        super().__init__()
        from .toolbox import ResultView
        self.window, self.mode = window, mode
        self.fields, self.sources, self.canvas = {}, [], {}
        self.records, self.artifact = {}, None
        root = QHBoxLayout(self)
        controls = QWidget()
        rows = QVBoxLayout(controls)
        self.form = QFormLayout()
        self.form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.calculate_button = QPushButton(_LABELS[mode])
        self.calculate_button.setObjectName('primary')
        self.calculate_button.clicked.connect(self.calculate)
        rows.addWidget(self.calculate_button)
        rows.addLayout(self.form)
        getattr(self, f'_build_{mode}')()
        rows.addStretch()
        self.result_state = ResultState(list(self.fields.values()), self.calculate_button, self.sources)
        rows.insertWidget(1, self.result_state)
        root.addWidget(controls, 1)
        self.result = ResultView()
        root.addWidget(self.result, 2)
        self.result.views.setTabVisible(0, False)
        for title in _VIEWS[mode]:
            page = QWidget()
            layout = QVBoxLayout(page)
            canvas = FigureCanvasQTAgg(Figure(figsize=(7, 4)))
            layout.addWidget(NavigationToolbar2QT(canvas, page))
            layout.addWidget(canvas)
            index = self.result.views.addTab(page, title)
            self.result.views.setTabVisible(index, False)
            self.canvas[title] = canvas, index
        self.output_choice = QComboBox()
        self.output_choice.setAccessibleName('Resultado numérico disponible')
        self.output_choice.currentIndexChanged.connect(self._select_output)
        self.output_choice.hide()
        self.result.layout().insertWidget(2, self.output_choice)
        if mode == 'link':
            self.export_experiment = QPushButton('Exportar…')
            menu = QMenu(self.export_experiment)
            menu.addAction('Señal seleccionada…', self.result.export)
            menu.addAction('Experimento completo…', self._export_experiment)
            self.export_experiment.setMenu(menu)
            self.export_experiment.setEnabled(False)
            self.result.actions.replace_action('export', self.export_experiment)
        elif mode == 'sweep':
            self.campaign = None
            self.run_choice = QComboBox()
            self.run_choice.setAccessibleName('Corrida guardada')
            self.run_choice.hide()
            self.result.layout().insertWidget(2, self.run_choice)
            save = QPushButton('Exportar CSV…')
            save.clicked.connect(self._export_sweep)
            save.setEnabled(False)
            self.result.actions.replace_action('export', save)
            self.sweep_export = save
            load = QPushButton('Incorporar corrida')
            load.clicked.connect(self._import_run)
            load.setEnabled(False)
            self.result.actions.replace_action('reuse', load)
            self.import_run = load
            resume = QPushButton('Continuar barrido')
            resume.setEnabled(False)
            resume.clicked.connect(self._continue_sweep)
            self.result.actions.add_action(resume)
            self.resume_sweep = resume

    def _set(self, key, label, widget, tip=''):
        widget.setAccessibleName(label)
        if tip:
            widget.setToolTip(tip)
        self.form.addRow(label, widget)
        self.fields[key] = widget
        return widget

    def _line(self, key, label, value='', tip=''):
        return self._set(key, label, QLineEdit(str(value)), tip)

    def _combo(self, key, label, items):
        widget = QComboBox()
        for name, value in items:
            widget.addItem(name, value)
        return self._set(key, label, widget)

    def _check(self, key, label, checked=False):
        widget = QCheckBox(label)
        widget.setChecked(checked)
        self.form.addRow(widget)
        self.fields[key] = widget
        return widget

    def _source(self, title):
        from .toolbox import LocalInput
        source = LocalInput(title)
        source.bind_project(self.window)
        self.sources.append(source)
        self.form.addRow(source)
        return source

    def _visible(self, widget, shown):
        self.form.setRowVisible(widget, shown)
        widget.setProperty('calculationInput', shown)

    def _bits(self, *, manual=True):
        self._line('bit_count', 'Cantidad de bits aleatorios', 4096)
        if manual:
            field = self._line('manual_bits', 'Bits manuales', '', 'Ingresá ceros y unos. Podés separarlos con espacios.')
            field.setPlaceholderText('Opcional · si queda vacío, se genera la secuencia')
            field.textChanged.connect(lambda text: self._visible(self.fields['bit_count'], not text.strip()))
        self._line('seed', 'Semilla', 2026)
        self._line('symbol_rate', 'Tasa de símbolos Rs (símbolos/s)', 12000)
        self._check('padding', 'Completar el último símbolo con ceros', True)

    def _constellation(self):
        self._combo('family', 'Familia', (('PSK', 'psk'), ('QAM cuadrada', 'qam')))
        self._line('order', 'Orden de modulación M', 4, 'PSK requiere una potencia de dos. QAM cuadrada requiere una potencia de cuatro.')
        self._combo('labeling', 'Mapeo de bits', (('Gray', 'gray'), ('Binario natural', 'natural')))
        field = self._line('rotation', 'Rotación (rad)')
        field.setPlaceholderText('Opcional · π/4 para QPSK y 0 para las demás')
        self._combo('normalization', 'Normalización de la constelación',
                    (('Energía media unitaria', 'unit_energy'), ('Escala geométrica', 'raw')))

    def _pulse_fields(self):
        family = self._combo('pulse', 'Pulso', (('Raíz de coseno alzado (RRC)', 'rrc'),
                                                ('Coseno alzado (RC)', 'rc'), ('Rectangular', 'rectangular')))
        self._line('sps', 'Muestras por símbolo L', 8)
        self._line('span', 'Duración del pulso (símbolos)', 10)
        beta = self._line('rolloff', 'Roll-off β', 0.35)
        self._combo('pulse_normalization', 'Normalización del pulso',
                    (('Energía discreta unitaria', 'unit_energy'), ('Pico teórico unitario', 'unit_peak')))

        def changed(*_):
            rectangular = family.currentData() == 'rectangular'
            self._visible(beta, not rectangular)
            self.fields['span'].setText('1' if rectangular else '10')

        family.currentIndexChanged.connect(changed)

    def _synchronization(self, *, chain=False):
        mode = self._combo('sync', 'Sincronización',
                           (('Referencia conocida', 'ideal'), ('Alineación asistida', 'assisted'), ('Estimar con piloto', 'estimated')))
        offset = self._line('offset', 'Desplazamiento del primer símbolo (muestras)', 0)
        phase = self._line('phase', 'Fase que se compensa (rad)', 0)
        first = self._line('search_first', 'Primer desplazamiento de búsqueda', 0)
        last = self._line('search_last', 'Último desplazamiento de búsqueda')
        last.setPlaceholderText('Opcional · hasta el último válido')
        pilot = self._line('pilot_symbols', 'Longitud del piloto (símbolos)', 24) if chain else self._source('Piloto conocido')
        if not chain:
            self.pilot_input = pilot

        def changed(*_):
            selected = mode.currentData()
            manual = selected == 'assisted' or selected == 'ideal' and not chain
            self._visible(offset, manual)
            self._visible(phase, manual)
            for widget in (first, last, pilot):
                self._visible(widget, selected == 'estimated')

        mode.currentIndexChanged.connect(changed)
        changed()

    def _link_fields(self, *, manual=True):
        self._bits(manual=manual)
        self._constellation()
        self._pulse_fields()
        noise = self._check('noise_enabled', 'Incluir canal AWGN', True)
        field = self._line('eb_n0', 'Eb/N₀ (dB)', 6)
        noise.toggled.connect(lambda enabled: self._visible(field, enabled))
        self._synchronization(chain=True)

    def _build_link(self):
        self._link_fields()

    def _build_sweep(self):
        self._line('directory', 'Carpeta del barrido')
        select = QPushButton('Elegir carpeta…')
        select.clicked.connect(self._choose_sweep_folder)
        self.form.addRow(select)
        restore = QPushButton('Abrir barrido guardado')
        restore.clicked.connect(self._open_sweep)
        self.form.addRow(restore)
        self._combo('axis', 'Parámetro que varía', [(caption, name) for name, caption in AXES.items()])
        self._line('axis_values', 'Valores separados por coma', '0, 2, 4, 6, 8', 'Para decimales usá punto.')
        self._combo('seed_policy', 'Semillas',
                    (('Independientes por corrida', 'per_run'), ('Común a las corridas', 'common')))
        self._link_fields(manual=False)

    def _build_modulate(self):
        self._bits()
        self._constellation()

    def _build_pulse(self):
        use = self._check('apply', 'Aplicar el filtro a una señal')
        self.source = self._source('Entrada I/Q')
        kind = self._combo('filter_kind', 'Operación',
                           (('Interpolar símbolos y filtrar TX', 'interpolate'),
                            ('Filtrar registro sobremuestreado', 'filter'), ('Filtro adaptado RX', 'matched')))
        rate = self._line('symbol_rate', 'Tasa de símbolos Rs (símbolos/s)', 12000)
        self._pulse_fields()

        def changed(enabled):
            self._visible(self.source, enabled)
            self._visible(kind, enabled)
            self._visible(rate, not enabled)

        use.toggled.connect(changed)
        changed(False)

    def _build_awgn(self):
        self.source = self._source('Señal de entrada')
        reference = self._combo('reference', 'Referencia', (('SNR por muestra', 'snr'), ('Es/N₀', 'es_n0'), ('Eb/N₀', 'eb_n0')))
        self._line('db', 'Relación señal a ruido (dB)', 10)
        self._line('seed', 'Semilla', 2026)
        self._combo('domain', 'Ruido', (('Complejo circular', 'complex'), ('Real', 'real')))
        energy = self._line('symbol_energy', 'Energía discreta Es', 1)
        width = self._line('bits_per_symbol', 'Bits por símbolo', 2)
        power = self._line('signal_power', 'Potencia de referencia')
        power.setPlaceholderText('Opcional · usar potencia del registro')

        def changed(*_):
            mode = reference.currentData()
            self._visible(energy, mode != 'snr')
            self._visible(width, mode == 'eb_n0')

        reference.currentIndexChanged.connect(changed)
        changed()

    def _build_receive(self):
        self.source = self._source('Registro después del filtro adaptado')
        self._line('count', 'Símbolos a recuperar', 16)
        self._line('sps', 'Muestras por símbolo L', 8)
        self._line('gain', 'Ganancia que se divide del registro', 1)
        self._synchronization()

    def _build_decide(self):
        self.source = self._source('Observaciones alineadas I/Q')
        self._constellation()
        self._line('valid_bits', 'Bits útiles', '', 'Opcional. Si la señal registra relleno, conserva la longitud útil.')

    def _build_measure(self):
        self._line('order', 'Orden de las etiquetas M', 4)
        for side, label in (('tx', 'Transmitidas'), ('rx', 'Recibidas')):
            choose = self._set(side+'_record', label+' del proyecto', _SymbolChoice(self.window))
            manual = self._line(side+'_labels', 'Etiquetas '+label.lower(), '', 'Ingresá enteros separados por espacios o comas.')
            choose.currentIndexChanged.connect(lambda _, a=choose, b=manual: self._visible(b, a.currentData() is None))
            self._line(side+'_start', 'Primer símbolo '+('TX' if side == 'tx' else 'RX'), 0)
        self._line('count', 'Símbolos a comparar')
        enabled = self._check('measure_evm', 'Incluir EVM con referencias I/Q')
        self.reference, self.observation = self._source('Símbolos I/Q de referencia'), self._source('Símbolos I/Q observados')
        for widget in (self.reference, self.observation):
            self._visible(widget, False)
        enabled.toggled.connect(lambda checked: [self._visible(widget, checked) for widget in (self.reference, self.observation)])

    def _int(self, key, default=None):
        field = self.fields[key]
        return integer_field(field) if field.text().strip() else default

    def _real(self, key, default=None):
        field = self.fields[key]
        return real_field(field) if field.text().strip() else default

    def _choice(self, key):
        return self.fields[key].currentData()

    def _constellation_spec(self):
        import math
        mode, order = self._choice('family'), self._int('order')
        rotation = self._real('rotation', math.pi/4 if mode == 'psk' and order == 4 else 0)
        return ConstellationSpec(mode, order, self._choice('labeling'), rotation, self._choice('normalization'))

    def _pulse_spec(self):
        family = self._choice('pulse')
        return PulseSpec(family, self._int('sps'), self._int('span'),
                         None if family == 'rectangular' else self._real('rolloff'), self._choice('pulse_normalization'))

    def _sync_spec(self, *, chain=False):
        mode = self._choice('sync')
        if mode == 'estimated':
            return SynchronizationSpec(mode, search_first=self._int('search_first', 0), search_last=self._int('search_last'))
        if mode == 'ideal' and chain:
            return SynchronizationSpec()
        return SynchronizationSpec(mode, self._int('offset'), self._real('phase'))

    def calculate(self):
        try:
            task, complete = getattr(self, f'_run_{self.mode}')()
            captured = self.result_state.snapshot()

            def accept(value):
                complete(value)
                journal = getattr(self.window, '_result_journal', None)
                if journal is not None:
                    journal.reported(value, outputs_registered=True)
                self.result_state.accept(captured)

            self.window._run_operation('Calculando comunicaciones…', task, accept)
        except Exception as exc:
            show_input_error(self, 'Revisá los datos', exc)

    def _experiment_spec(self, count):
        return ExperimentSpec(
            bit_count=count, seed=self._int('seed'), symbol_rate_hz=self._real('symbol_rate'),
            constellation=self._constellation_spec(), pulse=self._pulse_spec(),
            eb_n0_db=real_field(self.fields['eb_n0']) if self.fields['noise_enabled'].isChecked() else None,
            synchronization=self._sync_spec(chain=True), pilot_symbols=self._int('pilot_symbols', 24),
            allow_padding=self.fields['padding'].isChecked(),
        )

    def _run_link(self):
        text = self.fields['manual_bits'].text()
        count = self._int('bit_count') if not text.strip() else len(''.join(text.split()))
        spec = self._experiment_spec(count)

        def task():
            with ExecutionContext().aggregate_progress() as ctx:
                bits = parse_bits(text, replace(ctx, progress=None)) if text.strip() else None
                child = replace(ctx, progress=lambda percentage: ctx.checkpoint(percentage*9//10))
                output = run_experiment(spec, bits=bits, execution=child)
                project = Project()
                key = store_experiment(project, output, ctx)
                ctx.checkpoint(100)
            return output, project, key

        return task, self._show_experiment

    def _campaign_directory(self):
        text = self.fields['directory'].text().strip()
        if not text:
            raise ValueError('Elegí una carpeta para los archivos del barrido.')
        return Path(text).expanduser()

    def _choose_sweep_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Carpeta del barrido', self.fields['directory'].text())
        if folder:
            self.fields['directory'].setText(folder)

    def _open_sweep(self):
        try:
            directory = self._campaign_directory()
            self.window._run_view_operation('Verificando las corridas…', lambda: load_sweep(directory), self._show_sweep)
        except ValueError as exc:
            show_input_error(self, 'Revisá la carpeta', exc)

    def _run_sweep(self):
        directory = self._campaign_directory()
        axis = axis_from_text(self._choice('axis'), self.fields['axis_values'].text())
        plan = SweepSpec(self._experiment_spec(self._int('bit_count')), (axis,), self._choice('seed_policy'))

        def accept(result):
            self.window.publish({'directory': str(result.directory), 'planned': result.planned,
                                 'completed': len(result.runs), 'axes': [asdict(axis) for axis in result.specification.axes]},
                                title='Barrido de comunicaciones', operation='Barrido paramétrico')
            self._show_sweep(result)

        return lambda: run_sweep(plan, directory), accept

    def _continue_sweep(self):
        campaign = self.campaign
        self.window._run_view_operation('Continuando barrido…',
                                        lambda: run_sweep(campaign.specification, campaign.directory), self._show_sweep)

    def _show_sweep(self, value):
        self.campaign = value
        self.sweep_export.setEnabled(bool(value.runs))
        self.import_run.setEnabled(bool(value.runs))
        self.resume_sweep.setEnabled(not value.complete)
        self.run_choice.clear()
        for row in value.runs:
            name = ', '.join(f'{AXES[key]}={number(item)}' for key, item in row['parameters'].items())
            self.run_choice.addItem(f"{row['ordinal']}. {name}", row['ordinal'])
        self.run_choice.setVisible(bool(value.runs))
        paragraphs = [] if value.complete else ['El catálogo conserva las corridas ya verificadas.']
        if len(value.runs) > 40:
            paragraphs.append('La tabla muestra las primeras 40 corridas. El CSV incluye todas las corridas verificadas.')
        rows = [('Carpeta', str(value.directory)), ('Corridas verificadas', f'{len(value.runs)} de {value.planned}'),
                ('Semillas', 'Común' if value.specification.seed_policy == 'common' else 'Independientes por corrida')]
        comparisons = []
        for row in value.runs[:40]:
            name = ', '.join(f'{AXES[key]}={number(item)}' for key, item in row['parameters'].items())
            metrics = row['metrics']
            if metrics is None:
                detail = 'Sin sincronización disponible'
            else:
                ber, ser, evm = metrics['ber'], metrics['ser'], metrics['evm']['percent']
                detail = f"BER {ber['errors']}/{ber['evaluated']} · SER {ser['errors']}/{ser['evaluated']}"
                if evm is not None:
                    detail += f' · EVM {evm:.4g} %'
            comparisons.append((name, detail))
        axes = {_COMPARISON: (partial(figures.sweep_figure, sweep=value), None)} if value.runs else {}
        self._display(Summary('Barrido de comunicaciones', [
            Section('Catálogo', paragraphs=paragraphs, rows=rows),
            Section('Corridas', rows=comparisons),
        ]), axes, {})
        workspace = self.findChild(ToolWorkspace)
        if workspace is not None:
            workspace.show_results()

    def _import_run(self):
        campaign, ordinal = self.campaign, self.run_choice.currentData()

        def accept(output):
            project, key = output
            mapping = self.window.project.incorporate(project, root=key)
            self.window.refresh_project()
            self.window.focus_result(mapping[key])

        self.window._run_view_operation('Incorporando corrida…', lambda: load_sweep_run(campaign, ordinal), accept)

    def _export_sweep(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Exportar tabla de corridas', 'barrido.csv', 'Tabla CSV (*.csv)')
        if path:
            destination = Path(path)
            if not destination.suffix:
                destination = destination.with_suffix('.csv')
            campaign = self.campaign
            self.window._run_view_operation('Exportando corridas…', lambda: export_sweep_csv(campaign, destination),
                                            lambda _: self.window.statusBar().showMessage(f'Tabla guardada en {destination}'))

    def _show_experiment(self, payload):
        result, project, key = payload
        recorded = load_experiment(project, key)
        mapping = self.window.project.incorporate(project, root=key)
        self.window.register_publication(mapping[key], recorded.report)
        for role, value in result.signals().items():
            self.window.register_publication(mapping[recorded.records[role]], value)
        self.artifact = project
        self.export_experiment.setEnabled(True)
        spec = result.specification
        axes = {
            _CONSTE: self._constellation_plot(spec.constellation, result.reception.symbols),
            _IQ: (partial(figures.iq_figure, signal=result.transmitted), None),
            _SPECTRUM: self._spectral_plot(result.transmitted),
            _PSD: self._spectral_plot(result.transmitted, density=True),
            _IMPULSE: (partial(figures.pulse_figure, pulse=result.pulse), None),
            _FREQUENCY: (partial(figures.filter_frequency_figure, pulse=result.pulse), None),
        }
        sync = result.reception.synchronization
        if sync.sample_offset is not None and result.matched.values.size > 2*spec.pulse.samples_per_symbol:
            axes[_EYE] = (partial(figures.eye_figure, signal=result.matched, sps=spec.pulse.samples_per_symbol,
                                  sample_offset=sync.sample_offset, count=result.transmitted_labels.labels.size), None)
        if result.metrics is not None and spec.eb_n0_db is not None:
            axes[_ERRORS] = (partial(figures.performance_figure, specification=spec.constellation,
                                     eb_n0_db=spec.eb_n0_db, metrics=result.metrics), None)
        sections = [
            Section('Transmisión', rows=[('Modulación', f'{spec.constellation.order}-{spec.constellation.family.upper()}'),
                                        ('Mapeo', 'Gray' if spec.constellation.labeling == 'gray' else 'Natural'),
                                        ('Bits útiles', spec.bit_count), ('Semilla', spec.seed),
                                        ('Rs (símbolos/s)', spec.symbol_rate_hz),
                                        ('Fs (muestras/s)', result.transmitted.metadata['sample_rate_hz']),
                                        ('Pulso', spec.pulse.family.upper()), ('Coeficientes', result.pulse.taps.size),
                                        ('Retardo por FIR (muestras)', result.pulse.group_delay_samples)]),
            _sync_section(sync),
        ]
        if result.metrics is not None:
            sections.insert(0, _quality_section(result.metrics))
        if result.channel is not None:
            sections.append(_noise_section(result.channel.statistics))
        names = {'symbols': 'Símbolos transmitidos', 'upsampled': 'Tren de símbolos', 'tx': 'I/Q transmitida',
                 'awgn': 'Después del canal', 'matched': 'Después del filtro adaptado',
                 'observed': 'Símbolos recibidos', 'pilot': 'Piloto'}
        saved = {names[role]: (signal, mapping[recorded.records[role]]) for role, signal in result.signals().items()}
        self._display(Summary('Enlace digital', sections), axes, saved)

    def _run_modulate(self):
        text = self.fields['manual_bits'].text()
        count, seed, clock = self._int('bit_count'), self._int('seed'), SymbolClock(self._real('symbol_rate'))
        spec, padding = self._constellation_spec(), self.fields['padding'].isChecked()

        def task():
            bits = parse_bits(text) if text.strip() else generate_bits(count, seed)
            labels = group_bits(bits, spec, pad=padding, clock=clock)
            return bits, labels, modulate(labels, spec)

        def accept(output):
            bits, labels, waveform = output
            bit_key = self.window.publish(encode_bits(bits), title='Bits transmitidos')
            label_key = self.window.publish(encode_symbols(labels), title='Etiquetas transmitidas', parents=(bit_key,))
            key = self.window.publish(waveform, operation='Modulación digital', parents=(label_key,))
            axes = {_CONSTE: self._constellation_plot(spec), _IQ: (partial(figures.iq_figure, signal=waveform), None)}
            summary = Summary('Modulación digital', [Section('Símbolos I/Q', rows=[
                ('Bits útiles', labels.valid_bits), ('Bits de relleno', labels.padding_bits), ('Símbolos', labels.labels.size),
                ('Tasa de símbolos (símbolos/s)', clock.symbol_rate_hz),
            ])])
            self._display(summary, axes, {'Símbolos I/Q': (waveform, key)})

        return task, accept

    def _run_pulse(self):
        spec = self._pulse_spec()
        source, register = self.source.capture_input() if self.fields['apply'].isChecked() else (None, None)
        mode = self._choice('filter_kind')
        clock = None if source is not None else SymbolClock(self._real('symbol_rate'), spec.samples_per_symbol)

        def task():
            pulse = design_pulse(spec)
            if source is None:
                wave = iq_signal(pulse.taps, clock, name='Respuesta del pulso')
            else:
                signal = upsample_symbols(source, spec.samples_per_symbol) if mode == 'interpolate' else source
                wave = apply_pulse(signal, pulse, matched=mode == 'matched')
            return pulse, wave, matched_pulse_isi(pulse)

        def accept(payload):
            pulse, wave, isi = payload
            system = self.window.publish(pulse.transfer(wave.metadata.get('sample_rate_hz'), matched=mode == 'matched'),
                                         operation='Diseño de pulso')
            parent = None if register is None else register()
            key = self.window.publish(wave, operation='Pulso y filtrado', parents=(system,) if not parent else (parent, system))
            axes = {_IMPULSE: (partial(figures.pulse_figure, pulse=pulse), None),
                    _FREQUENCY: (partial(figures.filter_frequency_figure, pulse=pulse), None)}
            if source is not None:
                axes[_IQ] = (partial(figures.iq_figure, signal=wave), None)
            summary = Summary('Pulso y filtro adaptado', [Section('Respuesta', rows=[
                ('Familia', spec.family.upper()), ('Coeficientes', pulse.taps.size), ('Energía', number(pulse.energy)),
                ('Retardo por FIR (muestras)', pulse.group_delay_samples), ('Pico relativo de ISI TX/RX', number(isi.peak)),
            ])])
            self._display(summary, axes, {wave.name: (wave, key)})

        return task, accept

    def _run_awgn(self):
        source, register = self.source.capture_input()
        reference = self._choice('reference')
        spec = AWGNSpec(reference, self._real('db'), self._int('seed'), self._choice('domain'),
                        None if reference == 'snr' else self._real('symbol_energy'),
                        self._int('bits_per_symbol') if reference == 'eb_n0' else None,
                        self._real('signal_power'))

        def accept(result):
            signal = result.signal
            key = self.window.publish(signal, operation='Canal AWGN', parents=(register(),))
            axes = {_IQ: (partial(figures.iq_figure, signal=signal), None)}
            if signal.metadata.get('sample_rate_hz') and signal.values.size >= 2:
                axes[_PSD] = self._spectral_plot(signal, density=True)
            self._display(Summary('Adición de ruido', [_noise_section(result.statistics)]), axes, {signal.name: (signal, key)})

        return lambda: add_awgn(source, spec), accept

    def _run_receive(self):
        source, register = self.source.capture_input()
        spec, count, sps, gain = self._sync_spec(), self._int('count'), self._int('sps'), self._real('gain')
        pilot, register_pilot = self.pilot_input.capture_input() if spec.mode == 'estimated' else (None, None)

        def accept(result):
            parents = [register()]
            if register_pilot is not None:
                parents.append(register_pilot())
            signal = result.symbols
            axes, records = {}, {}
            if signal is not None:
                key = self.window.publish(signal, operation='Recuperar símbolos', parents=tuple(parents))
                axes[_IQ] = (partial(figures.iq_figure, signal=signal), None)
                records[signal.name] = (signal, key)
            self.window.publish(asdict(result.synchronization), title='Sincronización', parents=tuple(parents))
            self._display(Summary('Recuperación de símbolos', [_sync_section(result.synchronization)]), axes, records)

        return lambda: recover_symbols(source, count, sps, spec, pilot=pilot, sample_gain=gain), accept

    def _run_decide(self):
        source, register = self.source.capture_input()
        spec, useful = self._constellation_spec(), self._int('valid_bits')

        def task():
            labels = decide_symbols(source, spec, valid_bits=useful)
            return labels, ungroup_symbols(labels)

        def accept(result):
            labels, bits = result
            parent = register()
            key = self.window.publish(encode_symbols(labels), title='Etiquetas recibidas', parents=(parent,))
            self.window.publish(encode_bits(bits), title='Bits recuperados', parents=(key,))
            preview = ' '.join(str(int(value)) for value in labels.labels[:24])
            self._display(Summary('Decisión de constelación', [Section('Resultado', rows=[
                ('Símbolos decididos', labels.labels.size), ('Bits útiles', labels.valid_bits),
                ('Primeras etiquetas', preview),
            ])]), {_CONSTE: self._constellation_plot(spec, source)}, {source.name: (source, parent)})

        return task, accept

    def _run_measure(self):
        order = self._int('order')
        chosen, parents = [], []
        for side in ('tx', 'rx'):
            identifier = self._choice(side+'_record')
            if identifier is not None:
                chosen.append(decode_symbols(self.window.project.get(identifier)))
                parents.append(identifier)
            else:
                text = self.fields[side+'_labels'].text().replace(',', ' ')
                chosen.append(SymbolSequence([int(value) for value in text.split()], order))
        spec = QualitySpec(self._int('tx_start'), self._int('rx_start'), self._int('count'))
        capture = self.fields['measure_evm'].isChecked()
        reference, register_ref = self.reference.capture_input() if capture else (None, None)
        observation, register_obs = self.observation.capture_input() if capture else (None, None)

        def accept(metrics):
            if capture:
                parents.extend((register_ref(), register_obs()))
            self.window.publish(asdict(metrics), title='BER, SER y EVM', parents=tuple(parents))
            self._display(Summary('Calidad de recepción', [_quality_section(metrics)]), {}, {})

        return lambda: measure_quality(*chosen, reference=reference, observation=observation, spec=spec), accept

    def _spectral_plot(self, signal, density=False):
        return partial(figures.spectrum_figure, density=density), partial(figures.spectrum_data, signal, density=density)

    def receive_signal(self, signal, identifier):
        self.source.set_source(signal, identifier)
        sps = signal.metadata.get('samples_per_symbol')
        if self.mode == 'pulse':
            self.fields['apply'].setChecked(True)
            self.fields['filter_kind'].setCurrentIndex(1 if isinstance(sps, int) and sps > 1 else 0)
        if 'sps' in self.fields and type(sps) is int and (sps > 1 or self.mode != 'pulse') and sps >= 1:
            self.fields['sps'].setText(str(sps))
        return self.source

    def _constellation_plot(self, spec, observed=None):
        def draw(figure, points):
            values = () if observed is None else observed.values
            figures.constellation_figure(figure, points.points, values)

        return draw, partial(build_constellation, spec)

    def _display(self, summary, axes, records):
        self.records = records
        self.result.show_content()
        self.result.label.hide()
        self.result.views.setTabVisible(0, False)
        self.result.views.setCurrentIndex(1)
        self.result.text.set_readable(summary)
        self.output_choice.blockSignals(True)
        self.output_choice.clear()
        self.output_choice.addItems(list(records))
        self.output_choice.setVisible(len(records) > 1)
        self.output_choice.blockSignals(False)
        self._select_output()
        for name, (canvas, index) in self.canvas.items():
            hide_plot(canvas)
            canvas._signallab_has_plot_result = False
            canvas._signallab_prepare_plot = None
            self.result.views.setTabVisible(index, name in axes)
            if name in axes:
                render, task = axes[name]
                canvas._signallab_prepare_plot = self._plot_preparation(canvas, render, task)
            refresh = getattr(canvas, '_signallab_plot_action_refresh', None)
            if refresh is not None:
                refresh()

    def _select_output(self, *_):
        selected = self.records.get(self.output_choice.currentText())
        if selected is None:
            self.result.bind_action_result(None, exportable=False)
        else:
            signal, key = selected
            self.result.bind_action_result(signal, (key,))
        self.result.table_view.set_signals(() if selected is None else (selected[0],))
        self.result.views.setTabVisible(self.result.table_index, selected is not None)

    def _plot_preparation(self, canvas, render, task):
        ready = False

        def prepare(present):
            def draw(value=None):
                nonlocal ready
                try:
                    canvas.figure.clear()
                    if task is None:
                        render(canvas.figure)
                    else:
                        render(canvas.figure, value)
                    ready = True
                    present()
                except Exception as exc:
                    QMessageBox.warning(self, 'No se pudo abrir la figura', str(exc))

            if ready:
                present()
            elif task is not None:
                self.window._run_view_operation('Preparando figura…', task, draw)
            else:
                draw()

        return prepare

    def _export_experiment(self):
        path, _ = QFileDialog.getSaveFileName(
            self, 'Guardar experimento', 'experimento.slproj', 'Proyecto científico (*.slproj);;Proyecto JSON (*.json)',
        )
        if not path or self.artifact is None:
            return
        target = Path(path)
        if not target.suffix:
            target = target.with_suffix('.slproj')
        project = self.artifact.snapshot()
        self.window._run_view_operation(
            'Guardando experimento…', lambda: session.save(target, project, session.empty_workspace()),
            lambda _: self.window.statusBar().showMessage(f'Experimento guardado en {target}'),
        )
