"""Recorded sample clocks populate fields and explain which clock is used."""
import math
from PySide6.QtWidgets import QLabel
from .sampling import positive_finite


def bind_clock(source,rate,start=None,override=None,*,optional_start=False):
    note=QLabel();note.setObjectName('muted');note.setWordWrap(True)
    copied = {}
    manual = {}
    fields = [field for field in (rate,start) if field is not None]
    if override is not None:
        for field in fields:field.setProperty('clockInput',True)
    def recorded():
        signal=source.loaded if source.mode.currentIndex()==2 else None
        data=signal.metadata if signal is not None else {}
        fs=data.get('sample_rate_hz');t0=data.get('time_start_s') if start is not None else None
        if fs is not None:fs=positive_finite(fs,'Fs registrada')
        if t0 is not None:
            t0=float(t0)
            if not math.isfinite(t0):raise ValueError('El primer instante registrado debe ser finito.')
        return fs,t0
    def explain(fs,t0):
        inherited=[]
        if fs is not None:inherited.append(f'Fs = {fs:.12g} muestras/s')
        if t0 is not None:inherited.append(f'primer instante = {t0:.12g} s')
        if not inherited:
            note.setText('Completá Fs'+(' y el tiempo inicial.' if start is not None and not optional_start else '.'));return
        message='Reloj del registro · '+', '.join(inherited)+'.'
        if fs is None or start is not None and t0 is None and not optional_start:message+=' Completá el dato faltante en el formulario.'
        note.setText(message)
    def copy(*_):
        if override is not None and override.isChecked():
            for field in fields:field.setReadOnly(False)
            note.setText('Se usa el reloj indicado en el formulario.')
            return
        try:fs,t0=recorded()
        except (TypeError,ValueError) as exc:
            for field in fields:field.setReadOnly(False)
            note.setText(str(exc));return
        for field, value in ((rate,fs),(start,t0)):
            if field is None:continue
            if override is not None:field.setReadOnly(value is not None)
            before = copied.pop(field,None)
            if value is not None:
                copied[field] = str(value)
                field.setText(copied[field])
            elif before is not None and field.text() == before:
                field.clear()
        explain(fs,t0)

    def toggle_override(enabled):
        if enabled:
            for field,value in manual.items():field.setText(value)
        else:
            manual.update((field,field.text()) for field in fields)
        copy()
    for field in (rate,start):
        if field is not None:
            field.textEdited.connect(lambda _,field=field:copied.pop(field,None))
    source.sourceChanged.connect(copy)
    source.mode.currentIndexChanged.connect(copy)
    if override is not None:override.toggled.connect(toggle_override)
    copy();return note
