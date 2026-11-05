from .numeric_input import real_field,integer_field
from .expression_editor import ExpressionEditor
from .report_view import ReportView
"""Herramientas de muestreo y conversión accesibles desde la navegación HP."""
import json
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QFormLayout, QScrollArea,
    QPlainTextEdit, QLineEdit, QComboBox, QCheckBox, QPushButton, QLabel,
    QMessageBox, QFileDialog)
from . import sampling
from .design import install_tasks


class SamplingPanel(QWidget):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        root = QHBoxLayout(self)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        controls = QWidget(); form = QFormLayout(controls); scroll.setWidget(controls)
        root.addWidget(scroll, 1)
        self.report = ReportView(); self.report.setReadOnly(True)
        self.report.setPlainText("Los resultados y sus gráficos se muestran en esta herramienta. Los parámetros y conclusiones quedan aquí.\n\nDiezmado sin filtro: puede introducir aliasing. SINC usa todas las muestras del registro finito y supone cero fuera; no recupera información perdida por aliasing.")
        root.addWidget(self.report, 1)
        self._section(form, "Muestrear una expresión")
        self.expression = ExpressionEditor("cos(2*pi*10*t)"); form.addRow("x(t)", self.expression)
        from .expression_import import install_expression_import
        install_expression_import(self.expression,owner.window if hasattr(owner,'window') and not callable(owner.window) else owner,['t'])
        self.rate = self._field(form, "Fs (muestras/s)", "100")
        self.start = self._field(form, "Tiempo de la primera muestra (s)", "0")
        self.count = self._field(form, "Cantidad de muestras", "101")
        self._button(form, "Muestrear expresión", self.sample)
        self._button(form, "Leer Fs y tiempo de la señal de entrada", self.read_clock)
        self.frequency = self._field(form, "Frecuencia angular del tono Ω (rad/s)", "140*pi")
        self._button(form, "Analizar alias del tono", self.alias)
        self._section(form, "Cambiar tasa de la señal de entrada")
        self.factor = self._field(form, "Factor entero M / L", "2")
        self.phase = self._field(form, "Fase local para diezmado (0…M-1)", "0")
        self.rate_method = QComboBox()
        self.rate_method.addItems(["Diezmar (sin filtro)", "Expandir con ceros", "Interpolar lineal", "Interpolar ZOH", "Interpolar SINC"])
        form.addRow("Método", self.rate_method)
        self.rate_method.currentIndexChanged.connect(lambda index:self.phase.setEnabled(index==0))
        self._button(form, "Aplicar cambio de tasa", self.change_rate)
        self._section(form, "Reconstruir en tiempo continuo")
        self.reconstruction = QComboBox(); self.reconstruction.addItems(["ZOH", "Lineal", "SINC"])
        form.addRow("Modelo", self.reconstruction)
        self.clock_override=QCheckBox('Usar la Fs y el tiempo inicial del formulario')
        self.clock_override.setToolTip('Activá esta opción sólo si querés reinterpretar el reloj de las muestras.')
        form.addRow(self.clock_override)
        self._button(form, "Reconstruir señal", self.reconstruct)
        form.addRow(QLabel("Ventana de salida: primera a última muestra del registro."))
        self._section(form, "Cuantización de la señal de entrada")
        self.bits = self._field(form, "Bits (máximo 52 por precisión numérica)", "8")
        self.low = self._field(form, "Mínimo solicitado", "-1")
        self.high = self._field(form, "Máximo solicitado", "1")
        self.quant_method = QComboBox(); self.quant_method.addItems(["Redondeo", "Nivel inferior (FLOOR)"])
        form.addRow("Conversión", self.quant_method)
        self.zero = QCheckBox("Alinear un nivel con cero"); form.addRow(self.zero)
        self.first = self._field(form, "SNR: primera fila incluida (desde 0)", "0")
        self.last = self._field(form, "SNR: última fila incluida (vacío = final)", "")
        self._button(form, "Cuantizar y calcular SNR", self.quantize)
        self._section(form, "Punto fijo con aritmética exacta")
        self.fixed_value = self._field(form, "Valor decimal", "0.7")
        self.integer_bits = self._field(form, "Bits enteros, incluyendo signo", "2")
        self.fractional_bits = self._field(form, "Bits fraccionarios", "6")
        self.fixed_method = QComboBox(); self.fixed_method.addItems(["Redondeo", "Truncamiento hacia cero"])
        form.addRow("Método Q", self.fixed_method)
        self._button(form, "Representar en punto fijo", self.fixed)
        self._button(form, "Guardar informe…", self.save_report)
        self.task_selector=install_tasks(form,[
            ("Muestrear una expresión", "Pasá una expresión temporal a una secuencia de muestras.",
             [self.expression,self.rate,self.start,self.count],["Muestrear expresión","Leer Fs y tiempo de la señal de entrada"]),
            ("Nyquist y aliasing", "Consultá la frecuencia aparente de un tono para una Fs dada.",
             [self.rate,self.frequency],["Analizar alias del tono"]),
            ("Cambiar tasa", "Diezmá, expandí o interpolá la señal de entrada. El diezmado no agrega un filtro automáticamente.",
             [self.factor,self.phase,self.rate_method],["Aplicar cambio de tasa"]),
            ("Reconstruir una señal", "Elegí el modelo y la rejilla temporal de reconstrucción.",
             [self.rate,self.start,self.factor,self.reconstruction,self.clock_override],["Leer Fs y tiempo de la señal de entrada","Reconstruir señal"]),
            ("Cuantización y SNR", "Definí la resolución, el rango y el intervalo del análisis de ruido.",
             [self.bits,self.low,self.high,self.quant_method,self.zero,self.first,self.last],["Cuantizar y calcular SNR"]),
            ("Punto fijo", "Representá un valor con signo y precisión fraccionaria elegida.",
             [self.fixed_value,self.integer_bits,self.fractional_bits,self.fixed_method],["Representar en punto fijo"]),
            ("Guardar informe", "Exportá el informe del último cálculo.",[],["Guardar informe…"]),
        ])


    @staticmethod
    def _field(form, label, value):
        field = QLineEdit(value); form.addRow(label, field); return field

    @staticmethod
    def _section(form, title):
        form.addRow(QLabel(f"<h3>{title}</h3>"))

    def _button(self, form, title, callback):
        button = QPushButton(title)
        def invoke():
            try: callback()
            except Exception as exc: QMessageBox.warning(self, "Operación no aplicada", str(exc))
        button.clicked.connect(invoke); form.addRow(button)

    def _source(self):
        if self.owner.signal is None:
            raise ValueError("Primero creá o importá una señal.")
        return self.owner.signal

    def _job(self, title, calculation, callback):
        self.owner._run_operation(title, calculation, callback)

    def _accept_signal(self, result):
        from .result_summary import signal_summary
        self.report.set_readable(signal_summary(result))
        self.owner._set_signal(result)

    def sample(self):
        args = self.expression.text(), real_field(self.start), real_field(self.rate), integer_field(self.count)
        self._job("Muestreando expresión…", lambda: sampling.sample_expression(*args), self._accept_signal)

    def read_clock(self):
        source = self._source()
        if "sample_rate_hz" not in source.metadata:
            raise ValueError("Esta señal no tiene Fs registrada. Indicá Fs y el tiempo inicial para reconstruirla.")
        self.rate.setText(str(source.metadata["sample_rate_hz"]))
        if "time_start_s" in source.metadata:self.start.setText(str(source.metadata["time_start_s"]))

    def alias(self):
        result = sampling.alias_angular_frequency(real_field(self.frequency), real_field(self.rate))
        remember=getattr(self.owner,'_remember_calculation',None)
        if remember:remember(result)
        callback=getattr(self.owner,'on_alias',None)
        if callback:callback(result)
        from .result_summary import alias_summary
        self.report.set_readable(alias_summary(result))

    def change_rate(self):
        source, factor = self._source(), integer_field(self.factor)
        method = ["decimate", "expand", "linear", "zoh", "sinc"][self.rate_method.currentIndex()]
        phase = integer_field(self.phase) if method == 'decimate' else 0
        self._job("Cambiando tasa…", lambda: sampling.resample(source, factor, method, phase), self._accept_signal)

    def reconstruct(self):
        source=self._source();override=self.clock_override.isChecked()
        rate=real_field(self.rate) if override or source.metadata.get('sample_rate_hz') is None else None
        start=real_field(self.start) if override or source.metadata.get('time_start_s') is None else None
        factor=integer_field(self.factor);method=["zoh", "linear", "sinc"][self.reconstruction.currentIndex()]
        self._job("Reconstruyendo registro…", lambda: sampling.reconstruct(source,rate,start,factor,method,override_clock=override), self._accept_signal)

    def quantize(self):
        args = (self._source(), integer_field(self.bits), real_field(self.low), real_field(self.high),
                ["round", "floor"][self.quant_method.currentIndex()], self.zero.isChecked(),
                integer_field(self.first), integer_field(self.last) if self.last.text().strip() else None)
        def accept(result):
            self.owner._set_signal(result.signal)
            self.owner._remember_signal(result.error)
            if result.snr_db is None: snr = "N/D: señal y error nulos"
            elif result.snr_db == float("inf"): snr = "+∞: error nulo con señal no nula"
            elif result.snr_db == -float("inf"): snr = "−∞: señal nula con error no nulo"
            else: snr = f"{result.snr_db:.12g} dB"
            self.report.setPlainText(f"Cuantización completada\nPaso Δ: {result.step:.17g}\nNiveles: {result.levels}\nRango efectivo: {result.effective_min:.17g} … {result.effective_max:.17g}\nMuestras saturadas: {result.clipped_samples}\nSNR: {snr}\nFilas incluidas en SNR: {result.selected_samples}\n\nSNR usa energía de señal / energía del error sobre el mismo intervalo, sin restar la media. Incluye saturación. Se conserva también el error firmado xq−x durante esta sesión.")
            self.owner.tabs.setCurrentIndex(self.owner.sampling_tab)
        self._job("Cuantizando…", lambda: sampling.quantize(*args), accept)

    def fixed(self):
        args = self.fixed_value.text(), integer_field(self.integer_bits), integer_field(self.fractional_bits), ["round", "truncate"][self.fixed_method.currentIndex()]
        def accept(result):
            remember=getattr(self.owner,"_remember_calculation",None)
            if remember:remember(result)
            labels = {"format": "Formato", "input": "Entrada exacta", "represented_exact": "Valor representado exacto",
                      "signed_code": "Código con signo", "binary_twos_complement": "Binario (complemento a dos)",
                      "lsb_exact": "LSB", "minimum_exact": "Mínimo", "maximum_exact": "Máximo",
                      "total_error_exact": "Error total entrada−salida", "saturation_error_exact": "Error de saturación",
                      "conversion_error_exact": "Error de conversión", "rounding": "Método"}
            self.report.setPlainText("\n\n".join(f"{labels[key]}: {value}" for key, value in result.items()))
        self._job("Calculando representación exacta…", lambda: sampling.fixed_point(*args), accept)

    def save_report(self):
        from pathlib import Path
        path, _ = QFileDialog.getSaveFileName(self, "Guardar informe", "muestreo.txt", "Texto (*.txt)")
        if path: Path(path).write_text(self.report.toPlainText(), encoding="utf-8")
