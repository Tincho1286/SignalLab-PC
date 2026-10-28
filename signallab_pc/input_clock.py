"""Recorded sample clocks populate local fields without removing manual input."""
from PySide6.QtWidgets import QLabel
from .sampling import positive_finite
import math

def bind_clock(source,rate,start=None):
    note=QLabel();note.setObjectName('muted');note.setWordWrap(True)
    def recorded():
        signal=source.loaded if source.mode.currentIndex()==2 else None
        return signal.metadata if signal is not None else {}
    def explain(*_):
        data=recorded()
        if 'sample_rate_hz' not in data:
            note.setText('La entrada no tiene reloj registrado: definí Fs'+(' y el tiempo de su primera muestra.' if start is not None else '.'));return
        try:
            fs=positive_finite(data['sample_rate_hz'],'Fs registrada');t0=float(data.get('time_start_s',0))
            if not math.isfinite(t0):raise ValueError('Tiempo no finito')
        except (ValueError,TypeError):note.setText('El reloj registrado no es válido. Definí Fs'+(' y el tiempo inicial en los campos.' if start is not None else ' en el campo.'));return
        if rate.text()==str(fs) and (start is None or start.text()==str(t0)):note.setText('Reloj de la entrada cargado. Podés editar los campos para reinterpretar sus tiempos.')
        else:note.setText('La entrada conserva Fs='+format(fs,'.12g')+' muestras/s'+(', primer instante '+format(t0,'.12g')+' s' if start is not None else '')+'. Los campos visibles determinan el reloj usado al calcular.')
    def copy(*_):
        data=recorded()
        if 'sample_rate_hz' in data:
            try:
                fs=positive_finite(data['sample_rate_hz'],'Fs registrada');t0=float(data.get('time_start_s',0))
                if not math.isfinite(t0):raise ValueError('Tiempo no finito')
            except (ValueError,TypeError):explain();return
            rate.setText(str(fs))
            if start is not None:start.setText(str(t0))
        explain()
    source.sourceChanged.connect(copy);source.mode.currentIndexChanged.connect(explain);rate.textChanged.connect(explain)
    if start is not None:start.textChanged.connect(explain)
    explain();return note
