"""Recorded sample clocks populate fields and explain which clock is used."""
import math
from PySide6.QtWidgets import QLabel
from .sampling import positive_finite


def bind_clock(source,rate,start=None,override=None):
    note=QLabel();note.setObjectName('muted');note.setWordWrap(True)
    def recorded():
        signal=source.loaded if source.mode.currentIndex()==2 else None
        data=signal.metadata if signal is not None else {}
        fs=data.get('sample_rate_hz');t0=data.get('time_start_s') if start is not None else None
        if fs is not None:fs=positive_finite(fs,'Fs registrada')
        if t0 is not None:
            t0=float(t0)
            if not math.isfinite(t0):raise ValueError('El primer instante registrado debe ser finito.')
        return fs,t0
    def explain(*_):
        try:fs,t0=recorded()
        except (TypeError,ValueError) as exc:note.setText(str(exc));return
        if override is not None and override.isChecked():
            note.setText('Se usa el reloj indicado en el formulario.');return
        fields=[]
        if fs is not None:fields.append(f'Fs = {fs:.12g} muestras/s')
        if t0 is not None:fields.append(f'primer instante = {t0:.12g} s')
        if not fields:
            note.setText('Completá Fs'+(' y el tiempo inicial.' if start is not None else '.'));return
        message='Se usa el reloj registrado: '+', '.join(fields)+'.'
        if fs is None or start is not None and t0 is None:message+=' Completá el dato faltante en el formulario.'
        note.setText(message)
    def copy(*_):
        try:fs,t0=recorded()
        except (TypeError,ValueError):explain();return
        if override is None or not override.isChecked():
            if fs is not None:rate.setText(str(fs))
            if t0 is not None:start.setText(str(t0))
        explain()
    source.sourceChanged.connect(copy);source.mode.currentIndexChanged.connect(explain)
    if override is not None:override.toggled.connect(copy)
    explain();return note
