"""Ilustración del aliasing de un coseno con fase inicial cero."""
import numpy as np
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT
from .signal_plot import plot_samples

class AliasView(QWidget):
    def __init__(self):
        super().__init__();layout=QVBoxLayout(self)
        self.note=QLabel('Ingresá la frecuencia del tono y Fs, y presioná Analizar alias del tono.');self.note.setWordWrap(True);layout.addWidget(self.note)
        self.figure=Figure(figsize=(7,4));self.canvas=FigureCanvasQTAgg(self.figure);self.canvas.setMinimumHeight(300)
        layout.addWidget(NavigationToolbar2QT(self.canvas,self));layout.addWidget(self.canvas,1)
    def show_alias(self,result):
        fs=result['sample_rate_hz'];frequency=result.get('frequency_rad_s',2*np.pi*result['frequency_hz']);alias=result.get('signed_alias_rad_s',2*np.pi*result['signed_alias_hz'])
        original_ratio=frequency/(2*np.pi*fs);alias_ratio=alias/(2*np.pi*fs)
        n=np.arange(17);grid=np.linspace(0,16,4097)
        self.figure.clear();axis=self.figure.add_subplot(111)
        # Limitar sólo la curva ilustrativa para no representar falsamente oscilaciones subresueltas.
        draw_original=np.isfinite(original_ratio) and abs(original_ratio)<=16
        if draw_original:axis.plot(grid,np.cos(2*np.pi*original_ratio*grid),label=f'Original: {frequency:g} rad/s',alpha=.65)
        axis.plot(grid,np.cos(2*np.pi*alias_ratio*grid),'--',label=f'Alias: {abs(alias):g} rad/s')
        plot_samples(axis,n,np.cos(2*np.pi*alias_ratio*n),discrete=True,label='Muestras de ambos tonos')
        axis.set_xlabel('Tiempo en intervalos de muestreo: t · Fs');axis.set_ylabel('Amplitud');axis.grid(alpha=.2);axis.legend()
        self.figure.tight_layout();self.canvas.draw_idle()
        note='Ejemplo: coseno de amplitud 1 y fase inicial cero. Los dos tonos coinciden en los instantes de muestreo. Cada unidad horizontal equivale a 1/Fs segundos. Se muestran 17 muestras.'
        if not draw_original:note+=' La curva original se omite porque sus oscilaciones exceden la resolución de esta vista; el alias y las muestras siguen visibles.'
        self.note.setText(note)
