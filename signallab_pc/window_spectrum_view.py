"""Spectrum of the generated window, independent of its reusable sample data."""
import numpy as np
from PySide6.QtWidgets import QWidget,QVBoxLayout,QComboBox
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT
from .signal_plot import configure_axis


class WindowSpectrumView(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent);self.data=None
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0)
        self.scale=QComboBox();self.scale.addItems(['Módulo relativo en dB','Módulo relativo lineal'])
        self.figure=Figure(figsize=(7,4));self.canvas=FigureCanvasQTAgg(self.figure);self.toolbar=NavigationToolbar2QT(self.canvas,self)
        self.toolbar.addWidget(self.scale);layout.addWidget(self.toolbar);layout.addWidget(self.canvas,1)
        self.canvas._signallab_explicit_plot=True
        from .plot_view import install_figure_layout
        install_figure_layout(self.canvas);self.scale.currentIndexChanged.connect(self.draw)

    def set_data(self,data):self.data=data;self.draw()

    def draw(self,*_):
        self.figure.clear()
        if not self.data:self.canvas.draw_idle();return
        axis=self.figure.add_subplot(111)
        if self.data.get('error'):
            axis.set_axis_off();axis.text(.03,.5,'La ventana se conserva.\n'+self.data['error'],transform=axis.transAxes,wrap=True);self.canvas.draw_idle();return
        data=self.data;frequency=data['frequency'];magnitude=data['magnitude'];db=self.scale.currentIndex()==0
        # Decimation affects display only; the measures use complete samples.
        ids=np.unique(np.r_[np.linspace(0,len(frequency)-1,min(12000,len(frequency)),dtype=int),len(frequency)-1])
        if db:
            with np.errstate(divide='ignore'):values=20*np.log10(magnitude[ids])
        else:values=magnitude[ids]
        axis.plot(frequency[ids],values,label='Ventana / |W(0)|' if data['metrics']['normalizable'] else 'Ventana nula')
        cutoff=data['metrics']['half_power_frequency']
        if cutoff is not None:
            for artist in (axis.axvline(cutoff,color='#edc27d',ls='--',lw=.8,label='Media potencia'),axis.axhline(-10*np.log10(2) if db else 1/np.sqrt(2),color='#edc27d',ls=':',lw=.7)):
                artist._signallab_reference=True
        if db:axis.set_ylim(-120,3)
        else:axis.set_ylim(0,1.05)
        configure_axis(axis,units='rad/muestra',label='ω (rad/muestra)');axis.set_xlim(0,np.pi);axis.set_ylabel('Módulo relativo (dB)' if db else 'Módulo relativo')
        axis.set_title('DTFT de la ventana · referencia en ω=0');axis.grid(alpha=.15);axis.legend(loc='upper left',bbox_to_anchor=(1.01,1));self.canvas.draw_idle()
