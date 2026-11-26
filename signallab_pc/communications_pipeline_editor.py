"""Compact Workbench editor for ordered channel stages and source bindings."""

from dataclasses import replace
import json

from PySide6.QtCore import Signal as QtSignal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QListWidget,
    QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)

from .atomic_file import write_json
from .communications_channel import AWGNSpec, ChannelPath, MultipathSpec
from .communications_doppler import CarrierShift
from .communications_fading import FadingPath, FadingSpec
from .communications_impairments import IQImbalance, PhaseNoiseSpec, TimingOffset
from .communications_interference import BandInterference, ExternalInterference, InterferenceSpec, InterferenceTone, ToneInterference
from .communications_pipeline import ChannelPipelineSpec, ChannelStage, decode_pipeline_spec, encode_pipeline_spec, read_pipeline_spec
from .communications_propagation import FreeSpaceLoss, LogDistanceLoss, PropagationSpec
from .input_files import decode_finite_json
from .validation import show_input_error


_PRESETS = (
    ('Multitrayecto', ChannelStage(MultipathSpec((ChannelPath(0), ChannelPath(4, .3))))),
    ('Fading Rayleigh', ChannelStage(FadingSpec((FadingPath(),), 2026))),
    ('Fading Rician', ChannelStage(FadingSpec((FadingPath(k_linear=4),), 2026))),
    ('Doppler Clarke', ChannelStage(FadingSpec((FadingPath(),), 2026, 20))),
    ('Doppler o CFO', ChannelStage(CarrierShift(10))),
    ('Retardo', ChannelStage(TimingOffset(1))),
    ('Error de reloj', ChannelStage(TimingOffset(sfo_ppm=250))),
    ('Ruido de fase', ChannelStage(PhaseNoiseSpec(10, 2026))),
    ('Desequilibrio I/Q', ChannelStage(IQImbalance(1, .05))),
    ('Interferencia tonal', ChannelStage(InterferenceSpec(ToneInterference((InterferenceTone(20, .3),))))),
    ('Interferencia de banda', ChannelStage(InterferenceSpec(BandInterference(100, 200), sir_db=10))),
    ('Interferencia externa', ChannelStage(InterferenceSpec(ExternalInterference()), 'interferente')),
    ('AWGN', ChannelStage(AWGNSpec('snr', 15, 2026))),
    ('Atenuación fija', ChannelStage(PropagationSpec(gain_db=-3))),
    ('Espacio libre', ChannelStage(PropagationSpec(FreeSpaceLoss(100)))),
    ('Log-distancia', ChannelStage(PropagationSpec(LogDistanceLoss(100, 1, 2, 35)))),
)
_KINDS = {
    'multipath': 'Multitrayecto', 'fading': 'Fading', 'carrier': 'Doppler o CFO',
    'timing': 'Retardo y reloj', 'phase_noise': 'Ruido de fase', 'iq_imbalance': 'Desequilibrio I/Q',
    'interference': 'Interferencia', 'awgn': 'AWGN', 'propagation': 'Propagación',
}


def channel_stage_label(kind):
    return _KINDS.get(kind, kind)


class _ProjectSignalChoice(QComboBox):
    def __init__(self, project, selected=None):
        super().__init__()
        self.project = project
        self.refresh(selected)

    def refresh(self, selected):
        project = self.project()
        self.blockSignals(True)
        self.clear()
        self.addItem('Elegí una señal del proyecto', None)
        for row in reversed(project.headers('signal')):
            key = row['id']
            detail = project.describe(key)
            if detail['domain'] == 'discrete' and detail['data_kind'] == 'temporal':
                self.addItem(f"{row['title']} · {detail['count']} muestras · {key[:6]}", key)
        self.setCurrentIndex(max(0, self.findData(selected)))
        self.blockSignals(False)

    def showPopup(self):
        self.refresh(self.currentData())
        super().showPopup()


class ChannelPipelineEditor(QWidget):
    textChanged = QtSignal()

    def __init__(self, project):
        super().__init__()
        self.project = project
        self.choices = {}
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        actions = QHBoxLayout()
        self.preset = QComboBox()
        self.preset.setAccessibleName('Modelo de la nueva etapa')
        self.preset.addItems([name for name, _ in _PRESETS])
        add = QPushButton('Agregar etapa')
        add.clicked.connect(self.append)
        actions.addWidget(self.preset, 1)
        actions.addWidget(add)
        root.addLayout(actions)
        self.stages = QListWidget()
        self.stages.setAccessibleName('Orden de ejecución')
        self.stages.setMaximumHeight(128)
        root.addWidget(self.stages)
        actions = QHBoxLayout()
        for title, offset in (('Subir', -1), ('Bajar', 1), ('Quitar', 0)):
            button = QPushButton(title)
            button.clicked.connect(lambda _, step=offset: self.reorder(step))
            actions.addWidget(button)
        root.addLayout(actions)
        files = QHBoxLayout()
        load = QPushButton('Abrir JSON…')
        load.clicked.connect(self.load)
        save = QPushButton('Guardar JSON…')
        save.clicked.connect(self.save)
        files.addWidget(load)
        files.addWidget(save)
        root.addLayout(files)
        self.external_fields = QFormLayout()
        root.addLayout(self.external_fields)
        details = QCheckBox('Editar parámetros y semilla en JSON')
        root.addWidget(details)
        self.configuration = QPlainTextEdit()
        self.configuration.setAccessibleName('Parámetros y semilla de la cadena')
        self.configuration.setMaximumHeight(232)
        self.configuration.hide()
        root.addWidget(self.configuration)
        details.toggled.connect(self.configuration.setVisible)
        self.configuration.textChanged.connect(self.refresh)
        self.set_specification(ChannelPipelineSpec(seed=2026))

    def specification(self):
        return decode_pipeline_spec(decode_finite_json(self.configuration.toPlainText()))

    def bindings(self):
        return {name: choice.currentData() for name, choice in self.choices.items()}

    def text(self):
        return self.configuration.toPlainText(), tuple(self.bindings().items())

    def set_specification(self, spec):
        self.configuration.setPlainText(json.dumps(encode_pipeline_spec(spec), indent=2, ensure_ascii=False))

    def refresh(self):
        previous = self.stages.currentRow()
        self.stages.clear()
        try:
            spec = self.specification()
        except ValueError:
            self.stages.addItem('Configuración JSON incompleta o inválida')
            self.textChanged.emit()
            return
        for index, stage in enumerate(spec.stages, 1):
            label = channel_stage_label(stage.kind)
            tail = f' · {stage.external_input}' if stage.external_input else ''
            self.stages.addItem(f'{index}. {label}{tail}')
        self.stages.setCurrentRow(min(max(0, previous), len(spec.stages)-1))
        old = self.bindings()
        if tuple(self.choices) != spec.external_names:
            self.choices.clear()
            while self.external_fields.rowCount():
                self.external_fields.removeRow(0)
            for name in spec.external_names:
                choice = _ProjectSignalChoice(self.project, old.get(name))
                choice.setAccessibleName(name)
                choice.currentIndexChanged.connect(self.textChanged)
                self.external_fields.addRow(name, choice)
                self.choices[name] = choice
        self.textChanged.emit()

    def append(self):
        try:
            spec = self.specification()
            _, stage = _PRESETS[self.preset.currentIndex()]
            if stage.external_input in spec.external_names:
                count = 2
                while f'interferente_{count}' in spec.external_names:
                    count += 1
                stage = replace(stage, external_input=f'interferente_{count}')
            self.set_specification(replace(spec, stages=(*spec.stages, stage)))
            self.stages.setCurrentRow(len(spec.stages))
        except ValueError as exc:
            show_input_error(self, 'Revisá la configuración de la cadena', exc)

    def reorder(self, offset):
        try:
            spec = self.specification()
            stages = list(spec.stages)
            current = self.stages.currentRow()
            target = current + offset
            if current < 0 or not 0 <= target < len(stages):
                return
            stage = stages.pop(current)
            if offset:
                stages.insert(target, stage)
            self.set_specification(replace(spec, stages=tuple(stages)))
            self.stages.setCurrentRow(min(target, len(stages)-1))
        except ValueError as exc:
            show_input_error(self, 'Revisá la configuración de la cadena', exc)

    def load(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Abrir configuración de canal', '', 'Configuración JSON (*.json)')
        if path:
            try:
                self.set_specification(read_pipeline_spec(path))
            except (OSError, ValueError) as exc:
                show_input_error(self, 'No se pudo abrir la configuración', exc)

    def save(self):
        try:
            spec = self.specification()
            path, _ = QFileDialog.getSaveFileName(self, 'Guardar configuración de canal', 'canal.json',
                                                  'Configuración JSON (*.json)')
            if path:
                write_json(path, encode_pipeline_spec(spec))
        except (OSError, ValueError) as exc:
            show_input_error(self, 'No se pudo guardar la configuración', exc)
