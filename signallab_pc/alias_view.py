"""Complementary views of the same tone and its signed alias."""
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .model import Signal
from .signal_plot import plot_samples
from .theme_tokens import COLORS as C


class AliasPlot(QWidget):
    def __init__(self, description):
        super().__init__()
        layout = QVBoxLayout(self)
        self.note = QLabel(description)
        self.note.setWordWrap(True)
        layout.addWidget(self.note)
        self.figure = Figure(figsize=(7, 4))
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(NavigationToolbar2QT(self.canvas, self))
        layout.addWidget(self.canvas, 1)


class AliasView(AliasPlot):
    def __init__(self):
        super().__init__('Compará el tono original y el alias en los instantes de muestreo.')
        self.spectrum = AliasPlot('Ubicá el tono y su representante en la banda principal de Nyquist.')

    def show_alias(self, result):
        rate = result['sample_rate_hz']
        frequency = result['frequency_rad_s']
        alias = result['signed_alias_rad_s']
        nyquist = result['nyquist_rad_s']
        self.draw_time(frequency, alias, nyquist, rate)
        self.draw_frequency(frequency, alias, nyquist)

    def draw_time(self, frequency, alias, nyquist, rate):
        # Evaluate in sample intervals so large or small Fs does not corrupt the sampled phase.
        original_ratio = frequency/nyquist
        alias_ratio = alias/nyquist
        n = np.arange(17)
        grid = np.linspace(0, 16, 4097)
        in_seconds = 1e-90 < rate < 1e90
        time_unit = 1/rate if in_seconds else 1
        x = grid*time_unit
        self.figure.clear()
        axis = self.figure.add_subplot(111)
        visible = np.isfinite(original_ratio) and abs(original_ratio) <= 32
        if visible:
            self.add_tone(axis, x, np.cos(np.pi*original_ratio*grid), frequency, 'Tono original', 'accent', in_seconds)
        if frequency != alias or not visible:
            self.add_tone(axis, x, np.cos(np.pi*alias_ratio*grid), alias, 'Alias continuo', 'green', in_seconds, '--')
        y = np.cos(np.pi*alias_ratio*n)
        samples = plot_samples(axis, n*time_unit, y, discrete=True, label='Muestras coincidentes', color=C['amber'])
        samples.markerline._signallab_curve_input = (Signal(y,expression=f'cos(({alias_ratio!r})*pi*n)'), 'real')
        axis.set(xlabel='Tiempo t (s)' if in_seconds else 'Tiempo t/Ts (períodos de muestreo)', ylabel='Amplitud',
                 title='Coincidencia en los instantes de muestreo', ylim=(-1.14,1.14))
        axis.grid(alpha=.23)
        axis.legend()
        self.canvas.draw_idle()
        note = f'Coseno de fase inicial cero. Los 17 tallos están separados por Ts = 1/Fs = {time_unit:.6g} s.' if in_seconds else 'Coseno de fase inicial cero. Los 17 tallos están separados por un período de muestreo.'
        if not visible:
            note+=' El tono original supera la resolución de esta vista. Se muestran su alias y las muestras.'
        self.note.setText(note)

    @staticmethod
    def add_tone(axis, time, values, frequency, label, color, in_seconds, style='-'):
        line,=axis.plot(time,values,style,label=f'{label} · {frequency:.6g} rad/s',color=C[color],linewidth=1.25)
        if in_seconds:
            source=Signal(values,0,float(time[1]),'s',label,'continuous',f'cos(({frequency!r})*t)')
            line._signallab_curve_input=(source,'real')

    def draw_frequency(self, frequency, alias, nyquist):
        view = self.spectrum
        view.figure.clear()
        axis = view.figure.add_subplot(111)
        physical = 1e-90 < nyquist < 1e90
        outside = abs(frequency/nyquist)>6
        bound = nyquist if physical else 1
        original = frequency if physical else frequency/nyquist
        folded = alias if physical else alias/nyquist
        axis.axvspan(-bound,bound,color=C['green'],alpha=.13,label='Banda principal [−πFs, πFs)')
        axis.axvline(-bound,color=C['muted'],linestyle=':',linewidth=1)
        axis.axvline(bound,color=C['muted'],linestyle=':',linewidth=1)
        axis.plot([folded],[0],'o',color=C['green'],markersize=8,label=f'Alias Ωa · {alias:.6g} rad/s')
        if not outside:
            axis.plot([original],[1],'D',color=C['accent'],markersize=6,label=f'Tono Ω · {frequency:.6g} rad/s')
            axis.annotate('',(folded,.18),(original,.82),arrowprops={'arrowstyle':'->','color':C['muted'],'linewidth':1.2})
        axis.set(xlabel='Frecuencia angular (rad/s)' if physical else 'Frecuencia relativa al límite de Nyquist',
                 title='Ubicación del alias firmado',ylim=(-.48,1.5) if not outside else (-.55,.55))
        axis.set_yticks([0,1] if not outside else [0],['Alias','Entrada'] if not outside else ['Alias'])
        axis.grid(axis='x',alpha=.23)
        axis.legend()
        view.canvas.draw_idle()
        note=f'Entrada Ω = {frequency:.8g} rad/s · alias Ωa = {alias:.8g} rad/s.'
        if outside:
            note+=' Se amplía la banda principal para mostrar el alias con suficiente detalle.'
        view.note.setText(note)
