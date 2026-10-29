from .numeric_input import real_field,integer_field,constant_value
from .report_view import ReportView
from .coefficient_editor import CoefficientEditor,TransferPreview,split_coefficients
"""Panel de filtros/LTI compartido por navegación de ambos módulos."""
import json
from .atomic_file import write_json
from pathlib import Path

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QComboBox, QLineEdit, QPushButton, QPlainTextEdit, QScrollArea, QSplitter,
    QLabel, QMessageBox, QFileDialog)
from PySide6.QtCore import Qt

from .pole_zero_marks import draw_root_markers
from .filters import Transfer, fir, biquad, rc, rc_design, bilinear, from_poles_zeros
from .resources import ensure_working_set
from . import control
from .design import install_tasks


def parse_list(text, allow_empty=False):
    if not str(text).strip():
        if allow_empty:return np.array([],dtype=complex)
        raise ValueError('Ingresá al menos un coeficiente.')
    values=[]
    for index,part in enumerate(split_coefficients(str(text)),1):
        try:values.append(constant_value(part))
        except ValueError as exc:raise ValueError(f'Coeficiente {index} ({part or "vacío"}): {exc}') from exc
    return np.array(values,dtype=complex)


def list_text(values):
    return ", ".join(str(float(complex(v).real)) if not complex(v).imag else str(complex(v)).strip("()").replace("j", "i") for v in values)


class SystemsPanel(QWidget):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.system = Transfer([1], [1])
        self.last_response = None
        root = QHBoxLayout(self)
        split = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(split)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        controls = QWidget(); form = QFormLayout(controls)
        scroll.setWidget(controls); split.addWidget(scroll)
        form.addRow(QLabel("<h3>Control y respuestas continuas</h3>"))
        self.control_fields = {}
        for key, label, default in [("wn", "ω natural (rad/s)", "1"), ("zeta", "Amortiguamiento ζ", "0.5"),
                ("gain", "Ganancia K", "1"), ("duration", "Duración (s)", "10"),
                ("points", "Puntos temporales / ganancias", "1001"), ("kstart", "K inicial del lugar", "0"),
                ("kstop", "K final del lugar", "20")]:
            field = QLineEdit(default); self.control_fields[key] = field; form.addRow(label, field)
        self._button(form, "Crear sistema de segundo orden", self.design_second_order)
        self._button(form, "Realimentación unitaria negativa", lambda: self.close_loop(False))
        self._button(form, "Realimentación unitaria positiva", lambda: self.close_loop(True))
        self._button(form, "Respuesta continua al escalón", lambda: self.continuous_response("step"))
        self._button(form, "Respuesta continua al impulso", lambda: self.continuous_response("impulse"))
        self._button(form, "Lugar de raíces (realimentación negativa)", self.root_locus)
        form.addRow(QLabel("<h3>Transferencia y filtros</h3>"))
        self.domain = QComboBox(); self.domain.addItems(["Digital · z⁻¹", "Analógico · s"])
        self.b = CoefficientEditor("1",digital=True); self.a = CoefficientEditor("1",digital=True)
        form.addRow("Dominio", self.domain)
        form.addRow("Numerador b", self.b); form.addRow("Denominador a", self.a)
        self.transfer_preview=TransferPreview(self.b,self.a);form.addRow("Función de transferencia",self.transfer_preview)
        self.domain.currentIndexChanged.connect(self.update_coefficient_domain)
        self._button(form, "Usar coeficientes b/a", self.load_coefficients)
        self.kind = QComboBox()
        self.kind.addItems(["Pasa bajos", "Pasa altos", "Pasa banda", "Rechaza banda"])
        form.addRow("Tipo de filtro", self.kind)
        self.fields = {}
        for key, label, value in [
            ("taps", "Coeficientes FIR", "51"), ("f1", "ω₁ / ω₀ · rad/muestra", str(0.2*np.pi)),
            ("f2", "ω₂ · rad/muestra", str(0.4*np.pi)), ("beta", "Beta de Kaiser", "8.6"),
            ("q", "Q del biquad", "0.7071067811865476"),
            ("r", "Resistencia · Ω", "1000"), ("c", "Capacitancia · F", "0.000001"),
            ("fc", "Corte RC · Hz", "1000"),
            ("stages", "Etapas RC", "1"), ("period", "Período T · s", "0.001"),
            ("count", "Muestras de respuesta", "256"),
            ("wmin", "ω inicial", "0"), ("wmax", "ω final", str(np.pi)),
            ("points", "Puntos de frecuencia", "1025"),
            ("zeros", "Ceros · lista compleja", ""), ("poles", "Polos · lista compleja", ""),
            ("gain", "Ganancia polos/ceros", "1")]:
            edit = QLineEdit(value); self.fields[key] = edit; form.addRow(label, edit)
        self.window = QComboBox()
        self.window.addItems(["Rectangular", "Hann", "Hamming", "Blackman", "Kaiser", "Bartlett"])
        self.window.setCurrentIndex(2); form.addRow("Ventana FIR", self.window)
        self.known = QComboBox(); self.known.addItems(["Resistencia conocida", "Capacitor conocido"])
        form.addRow("Diseño RC por frecuencia", self.known)
        self.spacing = QComboBox(); self.spacing.addItems(["Lineal", "Logarítmica"])
        form.addRow("Escala de frecuencia", self.spacing)
        for label, action in [
            ("Diseñar FIR", self.design_fir), ("Diseñar biquad", self.design_biquad),
            ("Diseñar RC", self.design_rc), ("Aplicar bilineal H(s) → H(z)", self.convert_bilinear),
            ("Calcular componente RC desde fc", self.design_rc_component),
            ("Diseñar desde polos y ceros", self.design_roots),
            ("Filtrar señal de entrada", self.apply_signal),
            ("Respuesta al impulso", lambda: self.excitation("impulse")),
            ("Respuesta al escalón", lambda: self.excitation("step")),
            ("Respuesta en frecuencia", self.analyze), ("Plano de polos y ceros", self.plot_roots),
            ("Exportar respuesta CSV…", self.export_response),
            ("Guardar filtro…", self.save_system), ("Cargar filtro…", self.open_system)]:
            self._button(form, label, action)
        f=self.fields;c=self.control_fields
        self.task_selector=install_tasks(form,[
            ("Filtro FIR", "Diseñá un filtro por ventanas. Las frecuencias se expresan en rad/muestra.",
             [self.kind,f["taps"],f["f1"],f["f2"],self.window,f["beta"]], ["Diseñar FIR"]),
            ("Filtro IIR · biquad", "Ajustá la frecuencia central y el factor Q del filtro.",
             [self.kind,f["f1"],f["q"]],["Diseñar biquad"]),
            ("Filtro analógico RC", "Definí los componentes o calculá uno a partir de la frecuencia de corte.",
             [self.kind,f["r"],f["c"],f["fc"],f["stages"],self.known],["Diseñar RC","Calcular componente RC desde fc"]),
            ("Transferencia b/a", "Cargá una transferencia y elegí su dominio.",
             [self.domain,self.b,self.a,self.transfer_preview],["Usar coeficientes b/a","Cargar filtro…"]),
            ("Respuesta en frecuencia", "Analizá el sistema definido aquí con escala lineal o logarítmica.",
             [f["wmin"],f["wmax"],f["points"],self.spacing],["Respuesta en frecuencia","Exportar respuesta CSV…"]),
            ("Filtrar y excitar", "Aplicá el sistema digital definido aquí a una señal, un impulso o un escalón.",
             [f["count"]],["Filtrar señal de entrada","Respuesta al impulso","Respuesta al escalón"]),
            ("Polos y ceros", "Inspeccioná el plano o diseñá una transferencia desde sus raíces.",
             [self.domain,f["zeros"],f["poles"],f["gain"]],["Diseñar desde polos y ceros","Plano de polos y ceros"]),
            ("Transformación bilineal", "Convertí el sistema continuo definido aquí usando el periodo T.",
             [f["period"]],["Aplicar bilineal H(s) → H(z)"]),
            ("Control · segundo orden", "Definí frecuencia natural, amortiguamiento y ganancia.",
             [c["wn"],c["zeta"],c["gain"]],["Crear sistema de segundo orden"]),
            ("Control · respuesta temporal", "Observá la respuesta continua del sistema definido aquí.",
             [c["duration"],c["points"]],["Respuesta continua al escalón","Respuesta continua al impulso"]),
            ("Control · realimentación", "Cerrá el lazo con realimentación unitaria.",
             [c["gain"]],["Realimentación unitaria negativa","Realimentación unitaria positiva"]),
            ("Control · lugar de raíces", "Explorá cómo se desplazan los polos al variar K.",
             [c["kstart"],c["kstop"],c["points"]],["Lugar de raíces (realimentación negativa)"]),
            ("Guardar o abrir sistema", "Conservá coeficientes y dominio para retomarlos más tarde.",
             [],["Guardar filtro…","Cargar filtro…"]),
        ])
        right = QWidget(); layout = QVBoxLayout(right); split.addWidget(right)
        note = QLabel("Digital: b y a en potencias ascendentes de z⁻¹; ω en rad/muestra.\n"
                      "Analógico: coeficientes en potencias descendentes de s; ω en rad/s.\n"
                      "Las respuestas al impulso/escalón y filtrado digital parten del reposo.")
        note.setWordWrap(True); layout.addWidget(note)
        self.report = ReportView(); self.report.setReadOnly(True); self.report.setMaximumHeight(145)
        layout.addWidget(self.report)
        self.figure = Figure(figsize=(8, 6)); self.canvas = FigureCanvasQTAgg(self.figure)
        empty = self.figure.add_subplot(111); empty.set_axis_off()
        empty.text(0.5, 0.5, 'Diseñá un sistema para explorar su respuesta', ha="center", va="center", color="#8194ae", transform=empty.transAxes)
        layout.addWidget(NavigationToolbar2QT(self.canvas, self)); layout.addWidget(self.canvas, 1)
        split.setSizes([360, 720]); self._accept_system(self.system)

    def update_coefficient_domain(self,index):
        self.b.set_domain(index==0);self.a.set_domain(index==0);self.transfer_preview.schedule()

    def _button(self, form, text, action):
        button = QPushButton(text)
        button.clicked.connect(lambda checked=False: self.guard(action))
        form.addRow(button)

    def guard(self, action):
        try:
            prepare=getattr(self.owner,"prepare_system",None)
            if prepare:prepare(self)
            action()
        except Exception as exc:
            QMessageBox.warning(self, "Revisá los datos", str(exc))

    def number(self,key):return real_field(self.fields[key])

    def angular_cutoff(self,key):
        omega=self.number(key)
        if not 0<omega<np.pi:raise ValueError('La frecuencia debe estar entre 0 y π rad/muestra (sin incluir extremos).')
        return omega/(2*np.pi)

    def integer(self, key):
        return integer_field(self.fields[key])

    def selected_kind(self):
        return ["lowpass", "highpass", "bandpass", "bandstop"][self.kind.currentIndex()]

    def _job(self, label, function, callback=None):
        self.owner._run_operation(label, function, callback or self._accept_system)

    def _accept_system(self, system):
        self.system = system
        remember=getattr(self.owner,"_remember_system",None)
        if remember:remember(system)
        self.last_response = None
        self.b.setText(list_text(system.b)); self.a.setText(list_text(system.a))
        self.domain.setCurrentIndex(0 if system.domain == "digital" else 1)
        from .transfer_input import remember_system
        remember_system(self,system)
        self.fields["zeros"].clear(); self.fields["poles"].clear()
        self.report.setPlainText(f"{system.name}\n"
            f"{len(system.b)} coeficientes b; {len(system.a)} coeficientes a.\n"
            "Usá «Plano de polos y ceros» para calcular raíces y estabilidad.\n"
            "Sin cancelación aproximada de polos y ceros.")
        self.figure.clear(); self.canvas.draw_idle()
        callback=getattr(self.owner,'on_system_loaded',None)
        if callback and getattr(self.owner,'ready',True):callback(system)

    def load_coefficients(self):
        self._accept_system(Transfer(parse_list(self.b.text()), parse_list(self.a.text()),
            "digital" if self.domain.currentIndex() == 0 else "analog"))

    def design_fir(self):
        args = (self.selected_kind(), self.integer("taps"), self.angular_cutoff("f1"),
                self.angular_cutoff("f2") if self.kind.currentIndex()>=2 else .2, ["boxcar", "hann", "hamming", "blackman", "kaiser", "bartlett"][self.window.currentIndex()],
                self.number("beta") if self.window.currentIndex()==4 else 8.6)
        if self.kind.currentIndex()>=2 and not args[2]<args[3]:raise ValueError("La banda requiere 0 < ω₁ < ω₂ < π rad/muestra.")
        def compute():
            system=fir(*args)
            omega=np.linspace(0,np.pi,2049)
            return system,(omega,system.response(omega),'digital',False)
        def accept(result):
            system,response=result
            self._accept_system(system);self._show_response(response)
            from .fir_formula import design_summary
            cuts=np.array(args[2:4] if args[0] in ('bandpass','bandstop') else [args[2]])*2*np.pi
            summary=design_summary(args[0],args[1],cuts,args[4],args[5],title=system.name)
            self.report.set_readable(summary)
            callback=getattr(self.owner,'on_system_designed',None)
            if callback:callback(system)
        self._job("Diseñando FIR y calculando su respuesta…",compute,accept)

    def design_biquad(self):
        args = self.selected_kind(), self.angular_cutoff("f1"), self.number("q")
        if args[2]<=0:raise ValueError("Q debe ser positivo; ω₀ debe estar entre 0 y π rad/muestra.")
        def compute():
            system=biquad(*args);omega=np.linspace(0,np.pi,2049)
            return system,(omega,system.response(omega),'digital',False)
        self._job("Diseñando IIR y calculando su respuesta…",compute,self._show_filter_design)

    def design_rc(self):
        args = self.selected_kind(), self.number("r"), self.number("c"), self.integer("stages")
        def compute():
            system=rc(*args);omega=np.geomspace(.01/(args[1]*args[2]),100/(args[1]*args[2]),2049)
            return system,(omega,system.response(omega),'analog',True)
        self._job("Diseñando RC y calculando su respuesta…",compute,self._show_filter_design)

    def _show_filter_design(self,result):
        system,response=result
        self._accept_system(system);self._show_response(response)
        convention='Potencias ascendentes de z⁻¹; frecuencias en rad/muestra.' if system.domain=='digital' else 'Potencias descendentes de s; frecuencias en rad/s.'
        self.report.setPlainText(system.name+'\n\nNumerador: '+str(len(system.b))+' coeficientes\nDenominador: '+str(len(system.a))+' coeficientes\n\n'+convention+'\n\nLa pestaña Coeficientes muestra el numerador y el denominador completos. El gráfico presenta módulo, ganancia en dB y fase.\n\nUsá «Usar filtro en…» para copiar el diseño a otra herramienta o «Exportar filtro…» para guardarlo.')
        callback=getattr(self.owner,'on_system_designed',None)
        if callback:callback(system)

    def convert_bilinear(self):
        system, period = self.system, self.number("period")
        def accept(result):
            # Conservar la definición continua de entrada para poder variar T.
            if hasattr(self.owner,'tool_title'):
                self.system=result
                input_id=self.owner.system_id
                self.owner._remember_system(result)
                self.owner.system_id=input_id
                self.report.setPlainText('Transformación bilineal\n\nEntrada continua H(s) conservada en el editor.\nPeriodo T: '+str(period)+' s\n\nSalida discreta H(z)\nNumerador: '+list_text(result.b)+'\nDenominador: '+list_text(result.a)+'\n\nCoeficientes en potencias ascendentes de z⁻¹. Copiá la salida desde Resultados anteriores en una herramienta digital.')
                callback=getattr(self.owner,'on_system_loaded',None)
                if callback:callback(result)
            else:self._accept_system(result)
        self._job("Transformando H(s)…", lambda: bilinear(system, period),accept)

    def design_rc_component(self):
        known = "resistance" if self.known.currentIndex() == 0 else "capacitance"
        value = self.number("r" if known == "resistance" else "c")
        args = self.selected_kind(), self.number("fc"), known, value
        mode=getattr(self,'rc_mode',None);known_widget=self.fields['r' if known=='resistance' else 'c'];unknown_widget=self.fields['c' if known=='resistance' else 'r']
        def definition():
            return self.kind.currentIndex(),self.known.currentIndex(),self.fields['fc'].text(),known_widget.text(),mode.currentIndex() if mode is not None else None
        original_definition=definition();original_unknown=unknown_widget.text()
        def accept(result):
            system, r, c, response = result
            if definition()==original_definition and unknown_widget.text()==original_unknown:
                unknown_widget.setText(str(c if known=='resistance' else r))
            self._show_filter_design((system,response))
            self.report.appendPlainText(f"R = {r:.12g} Ω; C = {c:.12g} F; fc = {args[1]:.12g} Hz.")
        def compute():
            system,r,c=rc_design(*args);omega=np.geomspace(.01/(r*c),100/(r*c),2049)
            return system,r,c,(omega,system.response(omega),'analog',True)
        self._job("Calculando componentes RC y su respuesta…",compute,accept)

    def design_roots(self):
        args = (parse_list(self.fields["zeros"].text(), True),
                parse_list(self.fields["poles"].text(), True),
                constant_value(self.fields["gain"].text()),
                "digital" if self.domain.currentIndex() == 0 else "analog")
        view=getattr(self,'design_frequency',None)
        frequency_error=None
        try:frequency_request=view.request(args[3]) if view is not None else None
        except ValueError as exc:frequency_request=None;frequency_error=str(exc)
        frequency_snapshot=view.state.snapshot() if view is not None else None
        def compute():
            system=from_poles_zeros(*args)
            zeros,poles=system.poles_zeros()
            data=None;error=frequency_error
            if frequency_request is not None:
                from .frequency_analysis import frequency_grid,analyze_frequency
                try:data=analyze_frequency(system,frequency_grid(*frequency_request))
                except ValueError as exc:error=str(exc)
            return system,(zeros,poles,system.domain,system.stability(poles)),data,error
        def accept(result):
            draft=[self.fields[key].text() for key in ('zeros','poles','gain')];draft_domain=self.domain.currentIndex()
            system,roots,data,error=result;self._accept_system(system);self._show_roots(roots)
            for key,value in zip(('zeros','poles','gain'),draft):self.fields[key].setText(value)
            self.domain.setCurrentIndex(draft_domain)
            from .result_summary import transfer_summary
            self.report.set_readable(transfer_summary(system))
            if view is not None:
                if data is not None:view.set_result(system,data,frequency_snapshot)
                else:view.clear_result(system);view.note.setText('Diseño calculado. Revisá el intervalo de frecuencia: '+str(error))
            callback=getattr(self.owner,'on_system_designed',None)
            if callback:callback(system)
        self._job("Construyendo sistema y plano de polos y ceros…",compute,accept)

    def apply_signal(self):
        source, system = self.owner.signal, self.system
        if source is None:
            raise ValueError("Primero creá o importá una señal.")
        self._job("Resolviendo ecuación en diferencias…", lambda: system.apply(source), self.owner._set_signal)

    def excitation(self, kind):
        system, count = self.system, self.integer("count")
        self._job("Calculando respuesta…", lambda: system.excitation_response(count, kind), self.owner._set_signal)

    def analyze(self):
        system = self.system
        start, stop, count = self.number("wmin"), self.number("wmax"), self.integer("points")
        if count < 2 or not np.isfinite(start) or not np.isfinite(stop) or stop <= start:
            raise ValueError("Usá al menos dos puntos y un intervalo finito creciente.")
        ensure_working_set(count, live_arrays=8)
        logarithmic = self.spacing.currentIndex() == 1
        if logarithmic and start <= 0:
            raise ValueError("La escala logarítmica requiere ω inicial > 0.")
        def calculate():
            omega = np.geomspace(start, stop, count) if logarithmic else np.linspace(start, stop, count)
            return omega, system.response(omega), system.domain, logarithmic
        self._job("Calculando respuesta en frecuencia…", calculate, self._show_response)

    def _show_response(self, result):
        omega, response, domain, logarithmic = result
        self.last_response = result
        magnitude = abs(response)
        phase = np.full(omega.shape, np.nan)
        valid = np.isfinite(response) & (magnitude != 0)
        # Desenrollar cada tramo válido sin unir polos ni fase de cero.
        edges = np.flatnonzero(np.diff(np.r_[False, valid, False]))
        for start, stop in zip(edges[::2], edges[1::2]):
            phase[start:stop] = np.unwrap(np.angle(response[start:stop]))
        with np.errstate(divide="ignore", invalid="ignore"):
            db = 20*np.log10(magnitude)
        self.figure.clear()
        shared=None
        for position, values, label in [(1, magnitude, "|H|"), (2, db, "Magnitud · dB"),
                                         (3, phase, "Fase · rad"), (4,self.system.group_delay(omega),"Retardo (muestras)" if domain=="digital" else "Retardo (s)")]:
            axis = self.figure.add_subplot(4, 1, position,sharex=shared)
            if shared is None:shared=axis
            axis.plot(omega, values); axis.set_ylabel(label); axis.grid(alpha=.25)
            if logarithmic:
                axis.set_xscale("log")
        self.figure.axes[0].set_title("Frecuencia en escala logarítmica: comparar razones, no anchos" if logarithmic else "Frecuencia en escala lineal",fontsize=9)
        from .signal_plot import configure_axis
        configure_axis(axis,units="rad/muestra" if domain=="digital" else "rad/s")
        axis.set_xlabel("ω · rad/muestra" if domain == "digital" else "ω · rad/s")
        self.figure.tight_layout(); self.canvas.draw_idle()
        self.report.appendPlainText(f"Respuesta: {len(omega)} puntos; "
            f"{np.count_nonzero(~np.isfinite(response))} N/D. Fase de magnitud cero: N/D.")

    def plot_roots(self):
        system = self.system
        def calculate():
            zeros, poles = system.poles_zeros()
            return zeros, poles, system.domain, system.stability(poles)
        self._job("Calculando polos, ceros y estabilidad…", calculate, self._show_roots)

    def _show_roots(self, result):
        zeros, poles, domain, stability = result
        self.fields["zeros"].setText(list_text(zeros)); self.fields["poles"].setText(list_text(poles))
        self.report.appendPlainText(stability)
        self.figure.clear(); axis = self.figure.add_subplot(111)
        draw_root_markers(axis,zeros,poles)
        if domain == "digital":
            theta = np.linspace(0, 2*np.pi, 400)
            axis.plot(np.cos(theta), np.sin(theta), "--", color="grey")
        axis.axhline(0, color="grey", lw=.5); axis.axvline(0, color="grey", lw=.5)
        from .pole_zero_marks import frame_root_plane
        frame_root_plane(axis,zeros,poles,digital=domain=='digital');axis.grid(alpha=.25);axis.legend()
        axis.set_xlabel("Parte real"); axis.set_ylabel("Parte imaginaria")
        self.figure.tight_layout(); self.canvas.draw_idle()

    def export_response(self):
        if self.last_response is None:
            raise ValueError("Primero calculá la respuesta en frecuencia.")
        path, _ = QFileDialog.getSaveFileName(self, "Guardar respuesta", "respuesta.csv", "CSV (*.csv)")
        if path:
            omega, response, domain, _ = self.last_response
            np.savetxt(path, np.column_stack((omega, response.real, response.imag)),
                       delimiter=",", header=f"omega_{domain},real,imag; nan=N/D")

    def save_system(self):
        path, _ = QFileDialog.getSaveFileName(self, "Guardar filtro", "filtro.json", "JSON (*.json)")
        if path:
            s = self.system
            write_json(path,s.to_document())

    def open_system(self):
        path, _ = QFileDialog.getOpenFileName(self, "Cargar filtro", "", "JSON (*.json)")
        if path:
            doc = json.loads(Path(path).read_text(encoding="utf-8"))
            self._accept_system(Transfer.from_document(doc))

    def design_second_order(self):
        args = tuple(real_field(self.control_fields[key]) for key in ("wn", "zeta", "gain"))
        def compute():
            system=control.second_order(*args);omega=np.geomspace(args[0]*.01,args[0]*100,2049)
            return system,(omega,system.response(omega),'analog',True)
        self._job("Creando sistema y calculando su respuesta…",compute,self._show_filter_design)

    def close_loop(self, positive):
        source, gain = self.system, constant_value(self.control_fields["gain"].text())
        def accept(result):
            if hasattr(self.owner,'tool_title'):
                input_id=self.owner.system_id
                self.system=result;self.owner._remember_system(result);self.owner.system_id=input_id
                self.report.set_matrices('Sistema con realimentación '+('positiva' if positive else 'negativa')+' calculado.\n\nLa entrada se conserva para cambiar la ganancia. La tabla muestra los coeficientes de salida.\nGanancia: '+str(gain),{'Numerador b':np.atleast_2d(result.b),'Denominador a':np.atleast_2d(result.a)})
                callback=getattr(self.owner,'on_system_loaded',None)
                if callback:callback(result)
            else:self._accept_system(result)
        self._job("Calculando lazo cerrado…",lambda:control.feedback(source,gain,positive),accept)

    def continuous_response(self, kind):
        args = self.system, real_field(self.control_fields["duration"]), integer_field(self.control_fields["points"]), kind
        def accept(result):
            self.owner._set_signal(result)
            self.report.setPlainText(json.dumps(result.metadata, ensure_ascii=False, indent=2))
            if "dirac_at_zero" in result.metadata:
                QMessageBox.information(self, "Impulso ideal en t=0",
                    "El gráfico muestra la parte regular. La respuesta también incluye una Dirac ideal en cero, "
                    f"de peso {result.metadata['dirac_at_zero']}. Su peso queda registrado en los metadatos.")
        self._job("Calculando respuesta continua…", lambda: control.analog_response(*args), accept)

    def root_locus(self):
        args = self.system, real_field(self.control_fields["kstart"]), real_field(self.control_fields["kstop"]), integer_field(self.control_fields["points"])
        def accept(result):
            gains, roots, domain = result
            self.figure.clear(); axis = self.figure.add_subplot(111)
            for branch in roots.T: axis.plot(branch.real, branch.imag, linewidth=1)
            axis.scatter(roots[0].real, roots[0].imag, marker="x", color="red", label="K inicial")
            axis.scatter(roots[-1].real, roots[-1].imag, marker="o", facecolors="none", edgecolors="blue", label="K final")
            if domain == "digital":
                theta = np.linspace(0, 2*np.pi, 400); axis.plot(np.cos(theta), np.sin(theta), "--", color="grey")
            axis.axhline(0, color="grey", lw=.5); axis.axvline(0, color="grey", lw=.5)
            axis.set_aspect("equal", adjustable="datalim"); axis.grid(alpha=.25); axis.legend()
            axis.set_xlabel("Parte real"); axis.set_ylabel("Parte imaginaria")
            self.figure.tight_layout(); self.canvas.draw_idle()
            self.report.setPlainText(f"Lugar de raíces: A + K B = 0\nDominio: {domain}\nK: {gains[0]:g} a {gains[-1]:g}; {len(gains)} valores.\nRamas conectadas por proximidad entre ganancias; aumentar resolución cerca de cruces.\nSi baja el grado, los polos en infinito se omiten del gráfico. No se cancelan factores por tolerancia.")
        self._job("Calculando lugar de raíces…", lambda: control.root_locus(*args), accept)
