from .numeric_input import real_field,integer_field
from .signal_plot import plot_samples
from .signal_plot import configure_signal_axis, is_discrete_plot
from .report_view import ReportView
from .expression_editor import ExpressionEditor
"""Panel de Fourier numérica; conserva unidades y convenciones del registro."""
import json
import math
import numpy as np
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QScrollArea,
    QPlainTextEdit, QLineEdit, QComboBox, QCheckBox, QPushButton, QLabel,
    QMessageBox, QFileDialog)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

from . import fourier
from .design import install_tasks
from .engine import evaluate_expression
from .model import Signal
from .operations import _discrete
from .storage import save_csv, save_json


class FourierPanel(QWidget):
    def __init__(self, owner):
        super().__init__(); self.owner = owner; self.result = None
        root = QHBoxLayout(self)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        controls = QWidget(); form = QFormLayout(controls); scroll.setWidget(controls); root.addWidget(scroll, 1)
        right = QWidget(); layout = QVBoxLayout(right); root.addWidget(right, 2)
        self.comparison=None;self.plot_mode=QComboBox();self.plot_mode.addItems(['Módulo y fase','Parte real e imaginaria','Análisis ampliado: dB y retardo']);self.plot_mode.currentIndexChanged.connect(self.draw_result);layout.addWidget(self.plot_mode)
        self.figure = Figure(figsize=(8, 6)); self.canvas = FigureCanvasQTAgg(self.figure)
        empty = self.figure.add_subplot(111); empty.set_axis_off()
        empty.text(0.5, 0.5, 'El espectro de tu señal aparecerá aquí', ha="center", va="center", color="#8194ae", transform=empty.transAxes)
        layout.addWidget(NavigationToolbar2QT(self.canvas, self)); layout.addWidget(self.canvas, 3)
        self.report = ReportView(); self.report.setReadOnly(True); layout.addWidget(self.report, 1)
        self.report.setPlainText("La DTFT usa los índices globales de la señal. CTFT e inversa son cuadraturas de ventanas finitas. Las series continuas usan centros de celda en un periodo. PSD es bilateral y conserva la media salvo selección explícita.")
        self._section(form, "Rejilla de frecuencia")
        self.w0 = self._field(form, "ω inicial", str(-math.pi))
        self.w1 = self._field(form, "ω final", str(math.pi))
        self.nw = self._field(form, "Puntos de frecuencia", "1025")
        self._button(form, "DTFT del registro discreto (rad/muestra)", self.dtft)
        self._button(form, "Superponer DFT y DTFT", self.compare)
        self._button(form, "CTFT del registro temporal (rad/s)", self.ctft)
        self._button(form, "Densidad de energía del último espectro", self.energy_density)
        self._section(form, "Expresión y rejilla temporal")
        self.expression = ExpressionEditor("cos(2*pi*t)"); form.addRow("x(t)", self.expression)
        from .expression_import import install_expression_import
        install_expression_import(self.expression,owner.window if hasattr(owner,'window') and not callable(owner.window) else owner,['t'])
        self.t0 = self._field(form, "t inicial (s)", "0")
        self.t1 = self._field(form, "t final (s)", "1")
        self.nt = self._field(form, "Puntos / celdas temporales", "1024")
        self._button(form, "Crear registro temporal para CTFT", self.temporal)
        self._button(form, "Inversa del espectro continuo cargado", self.inverse)
        self._section(form, "Series de Fourier")
        self.period = self._field(form, "Periodo continuo T (s)", "1")
        self.harmonics = self._field(form, "Armónicos a cada lado (K)", "10")
        self._button(form, "Serie continua de la expresión", self.continuous_series)
        self._button(form, "Reconstruir serie continua cargada", self.continuous_synthesis)
        self._button(form, "Serie discreta: registro = un periodo", self.discrete_series)
        self._button(form, "Reconstruir serie discreta cargada", self.discrete_synthesis)
        self._section(form, "PSD / periodograma")
        self.rate = self._field(form, "Fs (Hz)", "100")
        self.estimator = QComboBox(); self.estimator.addItems(["Welch calibrado", "Un segmento calibrado", "Periodograma sin calibración: |DFT|²/N"])
        form.addRow("Estimador", self.estimator)
        self.segment = self._field(form, "Muestras por segmento Welch", "256")
        self.overlap = self._field(form, "Solape Welch", "128")
        self.window = QComboBox(); self.window.addItems(["Rectangular", "Hann", "Hamming", "Blackman", "Kaiser"])
        form.addRow("Ventana simétrica", self.window)
        self.beta = self._field(form, "Beta Kaiser", "5")
        self.demean = QCheckBox("Restar media de cada segmento"); form.addRow(self.demean)
        self._button(form, "Calcular densidad espectral", self.psd)
        self._section(form, "Resultado del panel")
        self._button(form, "Usar resultado en tabla / otras operaciones", self.use_result)
        self._button(form, "Exportar resultado CSV…", lambda: self.export(False))
        self._button(form, "Guardar resultado JSON…", lambda: self.export(True))
        self.task_selector=install_tasks(form,[
            ("DTFT y DFT", "Mostrá la DTFT como curva y superponé las muestras de la DFT en el mismo intervalo.",
             [self.w0,self.w1,self.nw],["DTFT del registro discreto (rad/muestra)","Superponer DFT y DTFT"]),
            ("Fourier continua · directa", "Transformá el registro temporal de entrada dentro de una ventana de frecuencia.",
             [self.w0,self.w1,self.nw],["CTFT del registro temporal (rad/s)"]),
            ("Crear registro temporal", "Prepará una expresión y una ventana para la transformada continua.",
             [self.expression,self.t0,self.t1,self.nt],["Crear registro temporal para CTFT"]),
            ("Fourier continua · inversa", "Reconstruí en tiempo a partir del espectro continuo activo.",
             [self.t0,self.t1,self.nt],["Inversa del espectro continuo cargado"]),
            ("Serie continua", "Calculá coeficientes de una expresión periódica o sintetizá los coeficientes activos.",
             [self.expression,self.t0,self.t1,self.nt,self.period,self.harmonics],["Serie continua de la expresión","Reconstruir serie continua cargada"]),
            ("Serie discreta", "Interpretá el registro de entrada como un periodo de la secuencia.",
             [],["Serie discreta: registro = un periodo","Reconstruir serie discreta cargada"]),
            ("Densidad de energía", "Obtené |X|² del último espectro calculado en este panel.",
             [],["Densidad de energía del último espectro"]),
            ("PSD y Welch", "Elegí un estimador de potencia, su ventana y la frecuencia de muestreo.",
             [self.rate,self.estimator,self.segment,self.overlap,self.window,self.beta,self.demean],["Calcular densidad espectral"]),
            ("Usar o guardar resultado", "Enviá el resultado a la tabla, reutilizalo o exportalo.",
             [],["Usar resultado en tabla / otras operaciones","Exportar resultado CSV…","Guardar resultado JSON…"]),
        ])


    @staticmethod
    def _field(form, label, value):
        result = QLineEdit(value); form.addRow(label, result); return result

    @staticmethod
    def _section(form, title): form.addRow(QLabel(f"<h3>{title}</h3>"))

    def _button(self, form, title, callback):
        button = QPushButton(title)
        def invoke():
            try: callback()
            except Exception as exc: QMessageBox.warning(self, "Operación no aplicada", str(exc))
        button.clicked.connect(invoke); form.addRow(button)

    def _source(self):
        if self.owner.signal is None: raise ValueError("Creá o importá una señal primero.")
        return self.owner.signal

    def _frequency_args(self): return real_field(self.w0), real_field(self.w1), integer_field(self.nw)
    def _time_args(self): return real_field(self.t0), real_field(self.t1), integer_field(self.nt)
    def _job(self, calculation): self.owner._run_operation("Calculando Fourier…", calculation, self._accept)

    def dtft(self):
        args = self._source(), *self._frequency_args()
        self._job(lambda: fourier.dtft(*args))

    def ctft(self):
        args = self._source(), *self._frequency_args()
        self._job(lambda: fourier.ctft(*args))

    def inverse(self):
        args = self._source(), *self._time_args()
        self._job(lambda: fourier.ictft(*args))

    def temporal(self):
        expression = self.expression.text(); start, stop, count = self._time_args()
        def calculate():
            times = fourier.grid(start, stop, count+1)[:-1]
            from .continuous_expression import sample_continuous
            result=sample_continuous(expression,start,(stop-start)/count,count)
            result.metadata.update(operation='time_record',convention='Ordinary samples on the stored interval; ideal impulses by position and area')
            return result
        self._job(calculate)

    def continuous_series(self):
        args = self.expression.text(), real_field(self.t0), real_field(self.period), integer_field(self.nt), integer_field(self.harmonics)
        self._job(lambda: fourier.continuous_series(*args))

    def continuous_synthesis(self):
        source=self._source()
        if source.metadata.get('operation')!='continuous_fourier_series':
            period=real_field(self.period)
            if period<=0:raise ValueError('El período T debe ser positivo.')
            source=source.copy_with(metadata={**source.metadata,'operation':'continuous_fourier_series','period_s':period})
        args=source,*self._time_args()
        self._job(lambda: fourier.synthesize_continuous(*args))

    def discrete_series(self):
        source = self._source(); self._job(lambda: fourier.discrete_series(source))

    def discrete_synthesis(self):
        source=self._source()
        if source.metadata.get('operation')!='discrete_fourier_series':
            if source.origin!=0:raise ValueError('Para síntesis discreta manual, ingresá c[0]…c[N−1] con inicio 0.')
            source=source.copy_with(metadata={**source.metadata,'operation':'discrete_fourier_series','period_samples':len(source.values),'input_origin':0})
        self._job(lambda: fourier.synthesize_discrete(source))

    def energy_density(self):
        source = self._source(); self._job(lambda: fourier.energy_density(source))

    def psd(self):
        source, rate = self._source(), real_field(self.rate)
        kwargs = dict(method=["welch", "periodogram", "legacy"][self.estimator.currentIndex()],
                      segment=integer_field(self.segment), overlap=integer_field(self.overlap),
                      window=["boxcar", "hann", "hamming", "blackman", "kaiser"][self.window.currentIndex()],
                      beta=real_field(self.beta), remove_mean=self.demean.isChecked())
        self._job(lambda: fourier.spectral_density(source, rate, **kwargs))

    def compare(self):
        args=self._source(),*self._frequency_args()
        def accept(pair):
            spectrum,samples=pair;self._accept(spectrum)
            self.comparison=samples;self.draw_result()
            self.report.setPlainText('DTFT y DFT superpuestas\n\nLa curva es la misma DTFT del cálculo individual, con el intervalo y la cantidad de puntos elegidos. Los tallos muestran la DFT de la misma señal, sin unir sus muestras ni modificar la curva.\n\nAmbas respetan el índice inicial de la señal y usan rad/muestra. Las muestras de DFT se repiten cada 2π si el intervalo abarca varios períodos. Exportar conserva la DTFT mostrada. En el análisis ampliado, la fase desenrollada y el retardo corresponden a la DTFT.')
        self.owner._run_operation('Superponiendo DFT y DTFT…',lambda:fourier.dtft_with_dft(*args),accept)

    def _accept(self, result):
        self.result = result; self.comparison=None;self.owner._remember_signal(result)
        self.report.setPlainText(f"{result.name}\n{result.values.size} puntos · eje {result.units}\n\n" + json.dumps(result.metadata, ensure_ascii=False, indent=2))
        self.draw_result()

    def draw_result(self,*_):
        result=self.result
        if result is None:return
        self.figure.clear()
        if self.plot_mode.currentIndex()!=2:
            axes=self.figure.subplots(2,1,sharex=True);index=self.owner._plot_indices(result.values)
            coordinates=result.axis[index];values=result.values[index]
            discrete=is_discrete_plot(result)
            power=result.metadata.get('operation') in {'spectral_density','energy_density'}
            polar=self.plot_mode.currentIndex()==0
            if not polar:first,second=values.real,values.imag;labels=('Parte real','Parte imaginaria')
            elif power:
                first=values.real;second=np.full(values.size,np.nan);valid=first>0;second[valid]=10*np.log10(first[valid]);labels=('Densidad','Densidad (dB)')
            else:
                first=np.abs(values);second=np.full(values.size,np.nan);valid=first>0;second[valid]=np.angle(values[valid]);labels=('Módulo','Fase principal (rad)')
            for axis,data,label in zip(axes,(first,second),labels):
                plot_samples(axis,coordinates,data,discrete=discrete,label=result.name,phase=polar and not power and label.startswith('Fase'));axis.set_ylabel(label);axis.grid(alpha=.2)
            if self.comparison is not None:
                frequencies,bins=self.comparison
                selected=self.owner._plot_indices(bins) if bins.size else np.array([],dtype=int)
                frequencies=frequencies[selected];bins=bins[selected]
                parts=(np.abs(bins),np.angle(bins)) if polar else (bins.real,bins.imag)
                if polar:parts[1][np.abs(bins)==0]=np.nan
                for axis,part in zip(axes,parts):
                    plot_samples(axis,frequencies,part,discrete=True,label='DFT',color='#efb56c');axis.legend()
                    axis.set_xlim(*result.metadata.get('frequency_bounds', (result.origin, result.axis[-1])))
            configure_signal_axis(axes[1],result)
            if polar:axes[1].set_title('Ceros: dB = −∞, no trazado' if power else 'Fase no definida donde el módulo es cero',fontsize=9)
            self.figure.tight_layout();self.canvas.draw_idle();return
        axes = self.figure.subplots(2, 2, sharex=True)
        index = self.owner._plot_indices(result.values)
        coordinate = result.origin+result.step*index
        discrete = is_discrete_plot(result)
        magnitude = abs(result.values)
        is_power = result.metadata.get("operation") in {"spectral_density", "energy_density"}
        plot_samples(axes[0, 0],coordinate, (result.values.real if is_power else magnitude)[index], label=result.name,discrete=discrete)
        axes[0, 0].set_title("Densidad" if is_power else "Magnitud")
        db = np.full(magnitude.shape, np.nan)
        valid = magnitude > 0
        db[valid] = (10 if is_power else 20)*np.log10(magnitude[valid])
        plot_samples(axes[0, 1],coordinate, db[index],discrete=discrete); axes[0, 1].set_title("dB; cero → −∞ (no trazado)")
        if not is_power:
            phase = np.full(magnitude.shape, np.nan)
            delay = np.full(magnitude.shape, np.nan)
            # Desenrollar cada tramo sin cruzar ceros; fase y retardo no definidos allí.
            edges = np.diff(np.r_[False, valid, False].astype(int))
            for left, right in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)):
                phase[left:right] = np.unwrap(np.angle(result.values[left:right]))
                if right-left >= 2 and result.units in {"rad/muestra", "rad/s"}:
                    delay[left:right] = -np.gradient(phase[left:right], result.step)
            plot_samples(axes[1, 0],coordinate, phase[index],discrete=discrete); axes[1, 0].set_title("Fase desenrollada (rad)")
            plot_samples(axes[1, 1],coordinate, delay[index],discrete=discrete); axes[1, 1].set_title("Retardo de grupo (muestras)" if result.units=="rad/muestra" else "Retardo de grupo (s)" if result.units=="rad/s" else "Retardo no definido para este eje")
        else:
            plot_samples(axes[1, 0],coordinate, result.values.real[index],discrete=discrete); axes[1, 0].set_title("Vista lineal")
            axes[1, 1].axis("off")
        if self.comparison is not None:
            frequencies,bins=self.comparison
            selected=self.owner._plot_indices(bins) if bins.size else np.array([],dtype=int)
            magnitude_dft=np.abs(bins[selected]);db_dft=np.full(magnitude_dft.shape,np.nan)
            valid_dft=magnitude_dft>0;db_dft[valid_dft]=20*np.log10(magnitude_dft[valid_dft])
            for axis,part in ((axes[0,0],magnitude_dft),(axes[0,1],db_dft)):
                plot_samples(axis,frequencies[selected],part,discrete=True,label='DFT',color='#efb56c');axis.legend()
                axis.set_xlim(*result.metadata.get('frequency_bounds', (result.origin, result.axis[-1])))
        for axis in axes.flat: configure_signal_axis(axis,result); axis.grid(alpha=.2)
        self.figure.tight_layout(); self.canvas.draw_idle()

    def use_result(self):
        if self.result is None: raise ValueError("Primero calculá un resultado.")
        self.owner._set_signal(self.result)

    def export(self, as_json):
        if self.result is None: raise ValueError("Primero calculá un resultado.")
        ext = "json" if as_json else "csv"
        path, _ = QFileDialog.getSaveFileName(self, "Guardar resultado Fourier", f"fourier.{ext}", f"{ext.upper()} (*.{ext})")
        if path: (save_json if as_json else save_csv)(self.result, path)
