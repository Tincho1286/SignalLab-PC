"""Interfaz de escritorio SignalLab PC (primera entrega)."""

import sys
import threading
import textwrap
from pathlib import Path

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Qt, Slot, QTimer, QSize, Signal as QtSignal
from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog,
    QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QInputDialog, QPushButton, QSplitter, QTabWidget, QTableWidget, QTableWidgetItem,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QScrollArea, QLayout, QSizePolicy, QFrame, QButtonGroup)

from .catalog import FUTURE_MENU_MAP, IMPLEMENTED, MODULES
from .engine import sequence_from_expression, sequence_from_values, replace_sample
from .model import Signal
from .operations import (add_sequences, dft, even_odd_parts, finite_measures, idft,
                         linear_convolution, linear_correlation, circular_convolution, correlation, reverse, scale_amplitude, shift)
from .storage import load_json, save_csv, save_json
from .systems_panel import SystemsPanel
from .sampling_panel import SamplingPanel
from .fourier_panel import FourierPanel
from .theory_panel import TheoryPanel
from .symbolic_panel import SymbolicPanel
from . import jobs
from .design import configure_theme, icon, STYLE


class _WorkerSignals(QObject):
    finished = QtSignal(object, object)
    failed = QtSignal(object, str)
    progressed = QtSignal(object, int)


class _OperationWorker(QRunnable):
    def __init__(self, function):
        super().__init__()
        self.function = function
        self.cancel_event = threading.Event()
        self.signals = _WorkerSignals()

    def run(self):
        try:
            jobs.bind(self.cancel_event, lambda progress: self.signals.progressed.emit(self, progress))
            jobs.checkpoint()
            result = self.function()
            jobs.checkpoint()
            self.signals.finished.emit(self, result)
        except Exception as exc:
            import traceback
            self.failure_details=''.join(traceback.format_exception(type(exc),exc,exc.__traceback__))
            self.signals.failed.emit(self, str(exc))
        finally:
            jobs.clear()


class SignalLabWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SignalLab PC — Sistemas y Señales")
        self.resize(1440, 900)
        self.setMinimumSize(960, 600)
        self.signal: Signal | None = None
        self.signal_bank: dict[str, Signal] = {}
        self.table_offset = 0
        self.table_page_size = 2000
        self.last_path: Path | None = None
        self._workers: list[_OperationWorker] = []
        self._thread_pool = QThreadPool(self)
        self._thread_pool.setMaxThreadCount(1)
        configure_theme()
        self._build()
        self._apply_style()
        self._configure_readable_layouts()
        self._update_preview()

    def _build(self):
        root=QWidget(); root.setObjectName("appRoot")
        layout=QHBoxLayout(root);layout.setContentsMargins(0,0,0,0);layout.setSpacing(0)
        sidebar=QWidget();sidebar.setObjectName("sidebar");sidebar.setFixedWidth(216)
        nav=QVBoxLayout(sidebar);nav.setContentsMargins(18,26,18,18);nav.setSpacing(6)
        brand=QLabel("SignalLab<span style='color:#58d1bd'>.</span>");brand.setObjectName("brand");nav.addWidget(brand)
        subtitle=QLabel("SEÑALES Y SISTEMAS");subtitle.setObjectName("eyebrow");nav.addWidget(subtitle)
        nav.addSpacing(28)
        self.nav_group=QButtonGroup(self);self.nav_group.setExclusive(True)
        self.nav_buttons={}
        nav_items=QWidget();navlist=QVBoxLayout(nav_items);navlist.setContentsMargins(0,0,0,0);navlist.setSpacing(3)
        for index,title,symbol in [(9,"Inicio","wave"),(0,"1  Preparar señal","sample"),(2,"2  Ver mi señal","chart"),(10,"3  Elegir una acción","filter")]:
            button=QPushButton(title);button.setIcon(icon(symbol));button.setObjectName("navButton");button.setCheckable(True)
            self.nav_group.addButton(button,index);self.nav_buttons[index]=button
            button.clicked.connect(lambda checked=False,i=index:self.tabs.setCurrentIndex(i));nav.addWidget(button)
        advanced=QPushButton("Más herramientas");advanced.setCheckable(True);advanced.setObjectName("chip");nav.addWidget(advanced)
        sections=[("LABORATORIO",[(0,"Señales","wave"),(4,"Filtros y control","filter"),(5,"Muestreo","sample"),(6,"Fourier","fourier"),(8,"Transformadas","math")]),
                  ("EXPLORAR",[(2,"Gráfico","chart"),(1,"Tabla de datos","table"),(3,"Archivos","folder"),(7,"Biblioteca","book")])]
        for heading,items in sections:
            label=QLabel(heading);label.setObjectName("eyebrow");navlist.addSpacing(12);navlist.addWidget(label)
            for index,title,symbol in items:
                button=QPushButton(title);button.setIcon(icon(symbol));button.setIconSize(QSize(20,20))
                button.setObjectName("navButton");button.setCheckable(True);self.nav_group.addButton(button,index+100)
                button.clicked.connect(lambda checked=False,i=index:self.tabs.setCurrentIndex(i))
                navlist.addWidget(button)
                if index not in self.nav_buttons:self.nav_buttons[index]=button
        navlist.addStretch()
        navscroll=QScrollArea();navscroll.setWidgetResizable(True);navscroll.setWidget(nav_items);navscroll.setFrameShape(QScrollArea.Shape.NoFrame);nav.addWidget(navscroll,1);navscroll.setVisible(False);advanced.toggled.connect(navscroll.setVisible);nav.addStretch()
        self.loaded_label=QLabel("SEÑAL ACTIVA\n\nNinguna todavía");self.loaded_label.setWordWrap(True);self.loaded_label.setObjectName("loadedSignal");nav.addWidget(self.loaded_label)
        version=QLabel("SignalLab PC  ·  0.4 dev");version.setObjectName("muted");nav.addWidget(version)
        layout.addWidget(sidebar)
        work=QWidget();work.setObjectName("workspace");wl=QVBoxLayout(work);wl.setContentsMargins(28,24,28,14);wl.setSpacing(14)
        top=QHBoxLayout();titlebox=QVBoxLayout();titlebox.setSpacing(5)
        eyebrow=QLabel("TU ESPACIO DE TRABAJO");eyebrow.setObjectName("eyebrow");titlebox.addWidget(eyebrow)
        self.page_title=QLabel("Diseñá tu próxima señal");self.page_title.setObjectName("pageTitle");titlebox.addWidget(self.page_title)
        self.page_subtitle=QLabel("Elegí una forma, ajustá sus parámetros y explorá el resultado.");self.page_subtitle.setObjectName("muted");self.page_subtitle.setWordWrap(True);titlebox.addWidget(self.page_subtitle)
        top.addLayout(titlebox,1);self.badge=QLabel("●  Laboratorio listo");self.badge.setObjectName("badge");top.addWidget(self.badge,0,Qt.AlignmentFlag.AlignTop);wl.addLayout(top)
        self.tabs=QTabWidget();self.tabs.tabBar().hide();wl.addWidget(self.tabs,1)
        self.tabs.addTab(self._build_create_tab(),"Señales")
        self.tabs.addTab(self._build_data_tab(),"Tabla")
        self.tabs.addTab(self._build_plot_tab(),"Gráfico")
        self.tabs.addTab(self._build_exchange_tab(),"Archivos")
        self.systems_panel=SystemsPanel(self);self.systems_tab=self.tabs.addTab(self.systems_panel,"Filtros")
        self.sampling_panel=SamplingPanel(self);self.sampling_tab=self.tabs.addTab(self.sampling_panel,"Muestreo")
        self.fourier_panel=FourierPanel(self);self.fourier_tab=self.tabs.addTab(self.fourier_panel,"Fourier")
        self.theory_panel=TheoryPanel();self.theory_tab=self.tabs.addTab(self.theory_panel,"Biblioteca")
        self.symbolic_panel=SymbolicPanel(self);self.symbolic_tab=self.tabs.addTab(self.symbolic_panel,"Transformadas")
        self.tabs.addTab(self._build_welcome(),"Inicio")
        self.tabs.addTab(self._build_actions(),"Elegir acción")
        self.tabs.currentChanged.connect(self._sync_workspace);self.tabs.setCurrentIndex(9)
        layout.addWidget(work,1);self.setCentralWidget(root)
        # El catálogo completo sigue disponible para las rutas de compatibilidad.
        self.tree=QTreeWidget(self);self.tree.hide()
        for module,entries in MODULES.items():
            parent=QTreeWidgetItem([module]);self.tree.addTopLevelItem(parent)
            for entry in entries:parent.addChild(QTreeWidgetItem([entry]))
        self.statusBar().showMessage("Listo  ·  Creá una señal o importá un archivo para comenzar")
        self.cancel_button=QPushButton("Cancelar cálculo");self.cancel_button.clicked.connect(self._cancel_operations)
        self.cancel_button.setEnabled(False);self.cancel_button.setVisible(False);self.statusBar().addPermanentWidget(self.cancel_button)

    def _sync_workspace(self,index):
        headings={9:("Empezá por una señal","Podés probar un ejemplo, crear tu señal o abrir una que ya guardaste."),
                  10:("¿Qué querés hacer?","Elegí una acción. Te llevamos a los controles que necesitás."),0:("Diseñá tu próxima señal","Elegí una forma, ajustá sus parámetros y explorá el resultado."),
                  1:("Tus datos, muestra a muestra","Inspeccioná y editá los valores de la señal activa."),
                  2:("Explorá la señal","Acercá, desplazá y compará sus componentes."),
                  3:("Archivos y resultados","Guardá tu trabajo o traé una señal al laboratorio."),
                  4:("Diseñá y analizá sistemas","Elegí una herramienta. Verás sólo los parámetros que necesita."),
                  5:("Del tiempo continuo al digital","Muestreo, reconstrucción y conversión en un mismo espacio."),
                  6:("Una nueva mirada en frecuencia","Transformadas, series y densidad espectral de tus señales."),
                  7:("Biblioteca de conceptos","Definiciones y fórmulas para acompañar tus cálculos."),
                  8:("Trabajá con expresiones","Transformadas simbólicas con sus condiciones y supuestos.")}
        title,subtitle=headings[index];self.page_title.setText(title);self.page_subtitle.setText(subtitle)
        self.nav_buttons[index].setChecked(True)
        if hasattr(self,"action_hint"):
            self.action_hint.setText("Trabajando con: "+self.signal.name if self.signal is not None else "Primero prepará una señal para analizarla. También podés diseñar un filtro o trabajar con expresiones.")
            for button in self.signal_action_buttons:button.setEnabled(self.signal is not None)
        if hasattr(self,"signal_tabs"):
            self.signal_tabs.setTabEnabled(1,self.signal is not None);self.signal_tabs.setTabEnabled(2,self.signal is not None)

    def _flow_page(self):
        content=QWidget();box=QVBoxLayout(content);box.setContentsMargins(0,8,0,0);box.setSpacing(16)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(content)
        return scroll,box

    def _build_welcome(self):
        page,box=self._flow_page()
        card,body=self._card("Tu primer recorrido","1. Prepará una señal  →  2. Mirá su gráfico  →  3. Elegí qué hacer con ella")
        button=QPushButton("Probar con una señal de ejemplo  →");button.setObjectName("primary");button.clicked.connect(self._start_example);body.addWidget(button)
        note=QLabel("Cargamos un coseno listo para explorar. No hace falta escribir una fórmula.");note.setObjectName("muted");note.setWordWrap(True);body.addWidget(note);box.addWidget(card)
        for title,description,label,callback in [
            ("Crear mi señal","Elegí una forma conocida, escribí una expresión o ingresá tus muestras.","Crear señal  →",lambda:self.tabs.setCurrentIndex(0)),
            ("Abrir una señal guardada","Retomá una señal exportada desde SignalLab en formato JSON.","Abrir archivo…",self._import_dialog)]:
            card,body=self._card(title,description);button=QPushButton(label);button.clicked.connect(callback);body.addWidget(button);box.addWidget(card)
        box.addStretch();return page

    def _start_example(self):
        self._choose_preview("cos(pi*n/4)");self.origin.setText("0");self.count.setText("33");self.signal_name.setText("Ejemplo · coseno")
        self._create_signal()

    def _build_actions(self):
        page,box=self._flow_page();self.signal_action_buttons=[]
        self.action_hint=QLabel();self.action_hint.setWordWrap(True);self.action_hint.setObjectName("loadedSignal");box.addWidget(self.action_hint)
        grid=QGridLayout();grid.setSpacing(16);box.addLayout(grid)
        choices=[("Ver frecuencias","Descubrí qué frecuencias componen tu señal.",6,True),
                 ("Modificar la señal","Cambiá amplitud, desplazá o combiná señales.",0,True),
                 ("Ver los valores","Consultá y editá cada muestra en una tabla.",1,True),
                 ("Guardar o exportar","Guardá la señal para retomarla o usar sus datos.",3,True),
                 ("Diseñar un filtro","Elegí un filtro y ajustá sus parámetros.",4,False),
                 ("Trabajar con expresiones","Calculá transformadas y ecuaciones simbólicas.",8,False)]
        for i,(title,description,target,needs_signal) in enumerate(choices):
            card,body=self._card(title,description);button=QPushButton("Elegir  →");button.clicked.connect(lambda checked=False,t=target:self._open_action(t));body.addWidget(button)
            if needs_signal:self.signal_action_buttons.append(button)
            grid.addWidget(card,i//2,i%2)
        box.addStretch();return page

    def _open_action(self,target):
        self.tabs.setCurrentIndex(target)
        if target==0:self.signal_tabs.setCurrentIndex(2)
        if target==6:self.fourier_panel.task_selector.setCurrentIndex(0)
        if target==4:self.systems_panel.task_selector.setCurrentIndex(0)

    @staticmethod
    def _card(title,subtitle=None):
        card=QFrame();card.setObjectName("card");box=QVBoxLayout(card);box.setContentsMargins(22,22,22,22);box.setSpacing(12)
        label=QLabel(title);label.setObjectName("cardTitle");box.addWidget(label)
        if subtitle:
            note=QLabel(subtitle);note.setObjectName("muted");note.setWordWrap(True);box.addWidget(note)
        return card,box

    def _build_create_tab(self):
        page=QWidget();outer=QVBoxLayout(page);outer.setContentsMargins(0,0,0,0)
        self.signal_tabs=QTabWidget();outer.addWidget(self.signal_tabs)
        create=QWidget();row=QHBoxLayout(create);row.setContentsMargins(0,8,0,0);row.setSpacing(18)
        card,box=self._card("Nueva señal","Definí la entrada y el intervalo que querés explorar.")
        card.setMinimumWidth(300);card.setMaximumWidth(410);row.addWidget(card,2)
        self.mode=QComboBox();self.mode.addItems(["Expresión matemática","Lista de muestras"])
        self.expression=QLineEdit("cos(pi*n/4)");self.expression.setPlaceholderText("Ej. cos(pi*n/4)")
        self.values=QLineEdit("1, 0, -1, 0, 1")
        self.origin=QLineEdit("-4");self.count=QLineEdit("33");self.signal_name=QLineEdit("x[n]")
        self.expression_label=QLabel("Expresión en n");self.values_label=QLabel("Muestras separadas por coma")
        box.addWidget(QLabel("¿Cómo querés ingresarla?"));self.mode.hide()
        modebar=QHBoxLayout();self.mode_buttons=QButtonGroup(self);self.mode_buttons.setExclusive(True)
        for index,title in enumerate(["Fórmula","Muestras"]):
            button=QPushButton(title);button.setCheckable(True);button.setObjectName("choice");button.setChecked(index==0)
            self.mode_buttons.addButton(button,index);button.clicked.connect(lambda checked=False,i=index:self.mode.setCurrentIndex(i));modebar.addWidget(button)
        self.mode.currentIndexChanged.connect(lambda i:self.mode_buttons.button(i).setChecked(True));box.addLayout(modebar)
        box.addWidget(self.expression_label);box.addWidget(self.expression)
        box.addWidget(self.values_label);box.addWidget(self.values)
        interval=QHBoxLayout()
        for label,widget in [("Índice inicial",self.origin),("Muestras",self.count)]:
            column=QVBoxLayout();column.setSpacing(8);column.addWidget(QLabel(label));column.addWidget(widget);interval.addLayout(column)
        box.addLayout(interval);box.addWidget(QLabel("Nombre de la señal"));box.addWidget(self.signal_name)
        make=QPushButton("Crear y ver señal  →");make.setObjectName("primary");make.clicked.connect(self._create_signal);box.addWidget(make)
        load=QPushButton("Importar archivo…");load.clicked.connect(self._import_dialog);box.addWidget(load)
        box.addStretch()
        preview,pv=self._card("Vista previa","Ajustá la expresión para ver su forma antes de crearla.")
        row.addWidget(preview,3)
        presets=QHBoxLayout()
        for title,expression in [("Seno","sin(pi*n/4)"),("Coseno","cos(pi*n/4)"),("Pulso","where(-4<=n<4,1,0)"),("Escalón","step(n)")]:
            button=QPushButton(title);button.setObjectName("chip")
            button.clicked.connect(lambda checked=False,e=expression:self._choose_preview(e));presets.addWidget(button)
        pv.addLayout(presets)
        self.preview_figure=Figure(figsize=(6,3),dpi=100);self.preview_canvas=FigureCanvasQTAgg(self.preview_figure);self.preview_canvas.setMinimumHeight(180);pv.addWidget(self.preview_canvas,1)
        self.preview_note=QLabel();self.preview_note.setWordWrap(True);self.preview_note.setObjectName("muted");pv.addWidget(self.preview_note)
        self.summary=QLabel("Tu señal aparecerá en el gráfico al crearla.");self.summary.setWordWrap(True);self.summary.setObjectName("summary");pv.addWidget(self.summary)
        self.signal_tabs.addTab(create,"Crear")
        editpage=QWidget();editlayout=QVBoxLayout(editpage);edit,eb=self._card("Ajustá tus muestras","Los cambios se aplican a la señal activa.");editlayout.addWidget(edit)
        ef=QFormLayout();eb.addLayout(ef)
        self.edit_origin=QLineEdit("0");self.edit_idx=QLineEdit("0");self.edit_value=QLineEdit("0")
        ef.addRow("Índice inicial",self.edit_origin)
        originbutton=QPushButton("Actualizar origen");originbutton.clicked.connect(self._edit_origin);ef.addRow(originbutton)
        ef.addRow("Fila de la muestra",self.edit_idx);ef.addRow("Nuevo valor",self.edit_value)
        apply=QPushButton("Aplicar cambio");apply.setObjectName("primary");apply.clicked.connect(self._edit_sample);ef.addRow(apply)
        editlayout.addStretch();self.signal_tabs.addTab(editpage,"Editar")
        operations=QWidget();ol=QVBoxLayout(operations);opcard,opbox=self._card("Transformá la señal","Elegí qué querés hacer con la señal activa.");ol.addWidget(opcard)
        opgrid=QGridLayout();opgrid.setSpacing(12);opbox.addLayout(opgrid)
        actions=[("Energía y potencia",self._show_energy),("DFT",self._show_dft),("IDFT",self._show_idft),("Convolución",lambda:self._binary_operation("convolution")),("Correlación",lambda:self._binary_operation("correlation")),("Sumar señales",lambda:self._binary_operation("sum")),("Partes par e impar",self._show_even_odd),("Desplazar",self._show_shift),("Invertir eje",self._show_reverse),("Escalar amplitud",self._show_scale),("Abrir resultado…",self._reuse_last),("Más plantillas…",self._signal_preset)]
        for i,(label,callback) in enumerate(actions):
            button=QPushButton(label);button.clicked.connect(callback);opgrid.addWidget(button,i//3,i%3)
        ol.addStretch();self.signal_tabs.addTab(operations,"Operaciones")
        self.mode.currentIndexChanged.connect(self._toggle_inputs)
        self._preview_timer=QTimer(self);self._preview_timer.setSingleShot(True);self._preview_timer.setInterval(300);self._preview_timer.timeout.connect(self._update_preview)
        for widget in (self.expression,self.values,self.origin,self.count):widget.textChanged.connect(lambda:self._preview_timer.start())
        self.mode.currentIndexChanged.connect(lambda:self._preview_timer.start());self._toggle_inputs()
        outer.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(page);scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        return scroll

    def _choose_preview(self,expression):
        self.mode.setCurrentIndex(0);self.expression.setText(expression)

    def _update_preview(self):
        try:
            if self.mode.currentIndex()==0:
                total=int(self.count.text())
                if total<1:raise ValueError("Ingresá una cantidad positiva de muestras.")
                source=sequence_from_expression(self.expression.text(),int(self.origin.text()),min(total,512))
            else:
                source=sequence_from_values(self.values.text(),int(self.origin.text()));total=source.values.size
            self.preview_figure.clear();axis=self.preview_figure.add_subplot(111)
            count=min(source.values.size,512);x=source.axis[:count];y=source.values[:count]
            axis.plot(x,y.real,color="#55d6c2",linewidth=1.8,marker="o" if count<80 else None,markersize=3)
            axis.fill_between(x,y.real,0,color="#55d6c2",alpha=.06)
            if np.any(y.imag):axis.plot(x,y.imag,color="#8b9cfa",linewidth=1.5)
            axis.axhline(0,color="#4b5e75",linewidth=.7);axis.grid(alpha=.28);axis.set_xlabel("Índice n");axis.set_ylabel("Amplitud")
            self.preview_figure.tight_layout(pad=1.6);self.preview_canvas.draw_idle()
            self.preview_note.setText(f"{total:,} muestras  ·  Eje discreto  ·  "+("Vista completa" if total<=512 else "Vista previa de las primeras 512 muestras"))
        except Exception as exc:
            self.preview_note.setText(str(exc));self.preview_figure.clear();self.preview_canvas.draw_idle()

    def _build_data_tab(self):
        page = QWidget(); layout = QVBoxLayout(page)
        intro = QLabel("Valores almacenados originales · editar una celda actualiza señal y gráfico")
        intro.setObjectName("muted"); layout.addWidget(intro)
        self.table = QTableWidget(0, 4); self.table.setHorizontalHeaderLabels(["n / eje", "Real", "Imaginaria", "Complejo"])
        self.table.itemChanged.connect(self._table_edited); layout.addWidget(self.table)
        pager = QHBoxLayout()
        self.page_prev = QPushButton("← Anterior"); self.page_prev.clicked.connect(lambda: self._change_table_page(-1)); pager.addWidget(self.page_prev)
        self.table_page_label = QLabel("Sin señal"); self.table_page_label.setObjectName("muted"); pager.addWidget(self.table_page_label, 1)
        self.page_next = QPushButton("Siguiente →"); self.page_next.clicked.connect(lambda: self._change_table_page(1)); pager.addWidget(self.page_next)
        layout.addLayout(pager)
        return page

    def _build_plot_tab(self):
        page = QWidget(); layout = QVBoxLayout(page)
        nextrow=QHBoxLayout()
        note=QLabel("Tu señal está lista. Elegí una acción para continuar.");note.setWordWrap(True);nextrow.addWidget(note,1)
        nextbutton=QPushButton("Elegir qué hacer  →");nextbutton.setObjectName("primary");nextbutton.clicked.connect(lambda:self.tabs.setCurrentIndex(10));nextrow.addWidget(nextbutton)
        save=QPushButton("Guardar…");save.clicked.connect(self._export_json);nextrow.addWidget(save);layout.addLayout(nextrow)
        self.figure = Figure(figsize=(8, 5), dpi=100); self.canvas = FigureCanvasQTAgg(self.figure)
        self.axes = self.figure.add_subplot(111); self.toolbar = NavigationToolbar2QT(self.canvas, page)
        layout.addWidget(self.toolbar); layout.addWidget(self.canvas, 1)
        return page

    def _build_exchange_tab(self):
        page = QWidget(); layout = QVBoxLayout(page)
        blurb = QLabel("JSON SignalLab preserva valores complejos, dominio, eje, unidades y metadatos. CSV incluye el eje y separa partes real e imaginaria.")
        blurb.setWordWrap(True); blurb.setObjectName("muted"); layout.addWidget(blurb)
        row = QHBoxLayout()
        for label, callback in [("Exportar JSON…", self._export_json), ("Exportar CSV…", self._export_csv),
                                ("Importar JSON…", self._import_dialog), ("Reutilizar última señal", self._reuse_last)]:
            b = QPushButton(label); b.clicked.connect(callback); row.addWidget(b)
        layout.addLayout(row)
        self.exchange_path = QLabel("No hay archivo de intercambio seleccionado."); self.exchange_path.setObjectName("muted"); layout.addWidget(self.exchange_path)
        layout.addStretch(); return page

    def _apply_style(self):
        self.setStyleSheet(STYLE)

    def _configure_readable_layouts(self):
        from .plot_view import install_enlarge
        for toolbar in self.findChildren(NavigationToolbar2QT):install_enlarge(toolbar)
        # Los formularios conservan su tamaño mínimo; el contenedor desplaza
        # el contenido que no cabe, en lugar de comprimir los controles.
        for field in self.findChildren(QLineEdit) + self.findChildren(QComboBox):
            field.setMinimumHeight(max(36, field.fontMetrics().height()+18))
            field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        for button in self.findChildren(QPushButton):
            if len(button.text()) > 42:
                button.setText(textwrap.fill(button.text(), width=42, break_long_words=False))
            lines = button.text().count("\n")+1
            button.setMinimumHeight(max(36, button.fontMetrics().height()*lines+18))
            button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        for form in self.findChildren(QFormLayout):
            form.setVerticalSpacing(12)
            form.setHorizontalSpacing(16)
            form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows if isinstance(form.parentWidget(), QGroupBox) or form.property('compactRows')
                                  else QFormLayout.RowWrapPolicy.WrapAllRows)
            for row in range(form.rowCount()):
                item = form.itemAt(row, QFormLayout.ItemRole.LabelRole)
                if item is not None and isinstance(item.widget(), QLabel):
                    item.widget().setWordWrap(True)
            form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
            form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
            form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        for label in self.findChildren(QLabel):
            if not label.wordWrap():
                label.setMinimumHeight(label.fontMetrics().height()+4)
        for group in self.findChildren(QGroupBox):
            group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        for scroll in self.findChildren(QScrollArea):
            content = scroll.widget()
            if content is not None and content.layout() is not None:
                content.layout().setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

    def _toggle_inputs(self):
        expr = self.mode.currentIndex() == 0
        self.expression.setVisible(expr); self.expression_label.setVisible(expr)
        self.values.setVisible(not expr); self.values_label.setVisible(not expr)
        self.count.setEnabled(expr)

    def _navigation_clicked(self, item, _column):
        if item.parent() is None:
            self.page_title.setText(item.text()); self.page_subtitle.setText(FUTURE_MENU_MAP.get(item.text(), "Herramienta de navegación"))
            return
        module, option = item.parent().text(), item.text()
        self.page_title.setText(option)
        if option == "Volver al inicio":
            self.tabs.setCurrentIndex(0)
            return
        if module == "Teoría" or option.startswith(("Teoría", "Conceptos")):
            self.page_subtitle.setText("Biblioteca de ayuda de SignalLab PC.")
            self.tabs.setCurrentIndex(self.theory_tab)
            return
        if (module == "Filtros" and option not in {"Teoría y estructuras de filtros", "Volver al inicio"}) or (
            module == "Sistemas LTI" and option in {"Resolver ecuación en diferencias",
            "Respuesta a impulso o escalón", "Polos, ceros y estabilidad"}):
            self.page_subtitle.setText("Coeficientes, diseño, respuesta y análisis del sistema.")
            self.tabs.setCurrentIndex(self.systems_tab)
            return
        if (module == "Control" and option not in {"Teoría de sistemas y control", "Volver al inicio"}) or (module == "Transformadas" and option == "Bilineal: H(s) a H(z)"):
            self.page_subtitle.setText("Control, respuesta temporal y frecuencial, realimentación y lugar de raíces.")
            self.tabs.setCurrentIndex(self.systems_tab)
            return
        if module == "Transformadas":
            operations = {"Laplace directa: x(t) a X(s)": 0, "Laplace inversa: X(s) a x(t)": 1,
                          "Transformada Z de secuencia": 2, "Z inversa: X(z) a x[n]": 3,
                          "Resolver una EDO simbólica": 4}
            if option in operations:
                self.symbolic_panel.operation.setCurrentIndex(operations[option])
                self.tabs.setCurrentIndex(self.symbolic_tab)
                self.page_subtitle.setText("Cálculo simbólico con supuestos explícitos y proceso cancelable.")
                return
        if module == "Fourier" and option == "Convolución y correlación":
            choice, ok = QInputDialog.getItem(self, "Operaciones de Fourier", "Operación:",
                ["Convolución", "Correlación / autocorrelación"], 0, False)
            if ok: self._binary_operation("convolution" if choice == "Convolución" else "correlation")
            return
        if module == "Fourier" and option not in {"Convolución y correlación", "Teoría y propiedades de Fourier", "Volver al inicio"}:
            self.page_subtitle.setText("Fourier numérica de registros finitos, series y densidades espectrales.")
            self.tabs.setCurrentIndex(self.fourier_tab)
            return
        if module == "Muestreo A/D" and option not in {"Conceptos de conversión A/D y D/A", "Volver al inicio"}:
            self.page_subtitle.setText("Muestreo, cambio de tasa, reconstrucción, cuantización y punto fijo.")
            self.tabs.setCurrentIndex(self.sampling_tab)
            return
        if module == "Acerca de":
            detail = {
                "Acerca de SignalLab": "SignalLab PC: laboratorio de señales, sistemas y aprendizaje. Consultá la biblioteca de ayuda para conocer los datos, resultados y alcance de cada herramienta.",
                "Dependencias y distribución": "PySide6, NumPy, SciPy, SymPy y Matplotlib. Revisá docs/DEPENDENCIAS.md. Existe una compilación portable de desarrollo. La paridad completa y la validación del ejecutable siguen pendientes.",
            }.get(option, "")
            self.page_subtitle.setText("Estado y vínculo de referencia")
            QMessageBox.information(self, option, detail)
            return
        if option in IMPLEMENTED.get(module, set()):
            self.page_subtitle.setText("Ruta implementada en esta entrega; se informa el alcance de la operación.")
            if module == "Recientes y banco":
                if option == "Reutilizar última señal": self._reuse_last()
                elif option == "Importar señal…": self._import_dialog()
                else: self.tabs.setCurrentIndex(3)
            elif module == "Señales" and option == "Calcular energía y potencia": self._show_energy()
            elif module == "Sistemas LTI" and option == "Convolución discreta x[n]*h[n]": self._binary_operation("convolution")
            elif module == "Sistemas LTI" and option == "Correlación y autocorrelación": self._binary_operation("correlation")
            elif module == "Fourier" and option == "Fourier discreta: DFT y DTFT": self._show_dft()
            else: self.tabs.setCurrentIndex(0)
            return
        self.page_subtitle.setText("Laboratorio de señales y sistemas")
        QMessageBox.information(self, "En desarrollo",
            f"{module} → {option}\n\nEsta herramienta aún no está disponible. No se generó ningún resultado.")

    def _signal_preset(self):
        presets = {"Impulso discreto δ[n]": "impulse(n)", "Escalón u[n]": "step(n)",
                   "Rampa causal": "n*step(n)", "Exponencial causal": "where(n>=0, exp(-0.2*n), 0)",
                   "Seno": "sin(pi*n/4)", "Coseno": "cos(pi*n/4)",
                   "Pulso rectangular": "where(-4<=n<4, 1, 0)",
                   "Por tramos": "where(n<0, 0, where(n<4, n, 4))",
                   "SINC normalizada": "sinc(n/4)"}
        selected, ok = QInputDialog.getItem(self, "Plantillas", "Elegí y luego ajustá la expresión y la ventana:", list(presets), 0, False)
        if ok:
            self.mode.setCurrentIndex(0)
            self.expression.setText(presets[selected])
            self.signal_tabs.setCurrentIndex(0)
            self.tabs.setCurrentIndex(0)

    def _create_signal(self):
        try:
            name = self.signal_name.text().strip() or "x[n]"
            if self.mode.currentIndex() == 0:
                expression = self.expression.text()
                origin, count = int(self.origin.text()), int(self.count.text())
                self._run_operation("Generando señal…",
                    lambda: sequence_from_expression(expression, origin, count, name=name),
                    lambda result: self._operation_succeeded(result, "Señal generada."))
            else:
                sig = sequence_from_values(self.values.text(), int(self.origin.text()), name=name)
                self._set_signal(sig)
        except Exception as exc: QMessageBox.warning(self, "No se pudo crear la señal", str(exc))

    def _remember_signal(self, signal):
        key = signal.name
        suffix = 2
        while key in self.signal_bank and self.signal_bank[key] is not signal:
            key = f"{signal.name} ({suffix})"
            suffix += 1
        self.signal_bank[key] = signal

    def _set_signal(self, signal: Signal):
        self.signal = signal; self.last_path = None
        self._remember_signal(signal)
        self.table_offset = 0
        self._refresh()

    def _refresh(self):
        if self.signal is None: return
        sig = self.signal
        eje = "n" if sig.units == "n" else sig.units
        axis_start = sig.origin
        axis_end = (int(sig.origin) + sig.values.size - 1 if sig.domain == "discrete"
                    else sig.origin + sig.step * (sig.values.size - 1))
        self.summary.setText(f"<b>{sig.name}</b> · {sig.values.size:,} muestras · {eje}={axis_start}…{axis_end} · paso {sig.step:g}<br>Entrada: {sig.expression or 'valores editados/importados'}<br>Se almacenan muestras complejas. El gráfico separa real e imaginaria; no cambia los datos.")
        self.badge.setText("●  Señal activa")
        self.loaded_label.setText(f"SEÑAL ACTIVA\n\n{sig.name}\n{sig.values.size:,} muestras")
        self.statusBar().showMessage(f"{sig.values.size} muestras · origen {sig.origin} · paso {sig.step:g} {sig.units} · valores complejos preservados")
        self.table_offset = min(self.table_offset, max(0, sig.values.size - 1))
        self._render_table_page()
        self._render_plot()
        self.edit_idx.setText("0")
        self.edit_origin.setText(str(sig.origin))
        self.tabs.setCurrentIndex(2)

    def _change_table_page(self, direction):
        if self.signal is None: return
        max_offset = max(0, ((self.signal.values.size - 1) // self.table_page_size) * self.table_page_size)
        self.table_offset = min(max(0, self.table_offset + direction * self.table_page_size), max_offset)
        self._render_table_page()

    def _render_table_page(self):
        if self.signal is None: return
        sig = self.signal
        start = self.table_offset
        stop = min(start + self.table_page_size, sig.values.size)
        self.table.blockSignals(True)
        self.table.setRowCount(stop - start)
        offsets = np.arange(start, stop, dtype=np.int64 if sig.domain == "discrete" else float)
        axis_page = (int(sig.origin) + offsets if sig.domain == "discrete"
                     else sig.origin + sig.step * offsets)
        for row, idx in enumerate(range(start, stop)):
            value = sig.values[idx]
            cells = [str(int(axis_page[row])) if sig.domain == "discrete" else f"{axis_page[row]:.17g}", f"{value.real:.12g}", f"{value.imag:.12g}", self._complex_text(value)]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                if col == 0: item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, col, item)
        self.table.blockSignals(False)
        self.page_prev.setEnabled(start > 0)
        self.page_next.setEnabled(stop < sig.values.size)
        self.table.resizeColumnsToContents()
        self.table_page_label.setText(
            f"Filas {start + 1:,}–{stop:,} de {sig.values.size:,} · vista paginada; señal completa preservada"
        )

    @staticmethod
    def _plot_indices(values, budget=60000):
        count = values.size
        if count <= budget:
            return np.arange(count, dtype=np.int64)
        block = int(np.ceil(count / (budget // 6)))
        chosen = [0,count-1]
        for start in range(0, count, block):
            stop = min(start + block, count)
            segment = values[start:stop]
            chosen.extend((start + int(np.argmin(segment.real)), start + int(np.argmax(segment.real)),
                           start + int(np.argmin(segment.imag)), start + int(np.argmax(segment.imag)),
                           start + int(np.argmin(abs(segment))), start + int(np.argmax(abs(segment)))))
        return np.unique(np.asarray(chosen, dtype=np.int64))

    def _render_plot(self):
        if self.signal is None: return
        sig = self.signal
        indices = self._plot_indices(sig.values)
        axis = (int(sig.origin) + indices if sig.domain == "discrete"
                else sig.origin + sig.step * indices)
        shown = sig.values[indices]
        self.axes.clear()
        from .signal_plot import plot_samples
        from .signal_plot import configure_signal_axis
        plot_samples(self.axes,axis,shown.real,discrete=sig.domain=='discrete',label='Parte real',source=sig,component='real')
        if np.any(sig.values.imag != 0):plot_samples(self.axes,axis,shown.imag,discrete=sig.domain=='discrete',label='Parte imaginaria',source=sig,component='imag')
        self.axes.axhline(0, color="#94a3b8", linewidth=.8); self.axes.grid(True, alpha=.22)
        note = " · vista reducida por densidad" if indices.size < sig.values.size else ""
        configure_signal_axis(self.axes,sig); self.axes.set_ylabel("Amplitud")
        self.axes.set_title(f"{sig.name} · datos originales{note}")
        self.axes.legend(); self.figure.tight_layout(); self.canvas.draw_idle()

    @staticmethod
    def _complex_text(value):
        return f"{value.real:.8g}{value.imag:+.8g}i" if value.imag else f"{value.real:.8g}"

    def _parse_complex(self, text):
        return complex(text.strip().replace("i", "j").replace("I", "j"))

    def _edit_sample(self):
        if self.signal is None: return
        try: self._set_signal(replace_sample(self.signal, int(self.edit_idx.text()), self._parse_complex(self.edit_value.text())))
        except Exception as exc: QMessageBox.warning(self, "Edición no aplicada", str(exc))

    def _edit_origin(self):
        if self.signal is None: return
        try:
            origin = int(self.edit_origin.text()) if self.signal.domain == "discrete" else float(self.edit_origin.text())
            self._set_signal(self.signal.copy_with(origin=origin))
        except Exception as exc: QMessageBox.warning(self, "Eje no actualizado", str(exc))

    def _show_energy(self):
        if self.signal is None: return self._need_signal()
        try:
            source = self.signal
            self._run_operation("Calculando medidas de la ventana…", lambda: finite_measures(source), self._show_measure_result)
        except Exception as exc: QMessageBox.warning(self, "No se pudo calcular", str(exc))

    def _show_measure_result(self, m):
        QMessageBox.information(self, "Medidas del registro finito",
            f"Energía de ventana  E = {m.energy:.12g}\nPotencia media de ventana  P = {m.average_power:.12g}\nRMS de ventana = {m.rms:.12g}\nMuestras = {m.sample_count}\n\nEsto mide el registro almacenado; no determina por sí solo energía o potencia global de una señal infinita.")

    def _show_dft(self):
        if self.signal is None: return self._need_signal()
        n_text, ok = QInputDialog.getText(self, "DFT", "N (vacío = longitud natural; otro N trunca o rellena con ceros):", text=str(self.signal.values.size))
        if not ok: return
        try:
            n = int(n_text) if n_text.strip() else None
            source = self.signal
            self._run_operation("Calculando DFT…", lambda: dft(source, n, centered=True),
                lambda result: self._operation_succeeded(result, "DFT sin normalizar · frecuencias de −π a π rad/muestra."))
        except Exception as exc: QMessageBox.warning(self, "No se pudo calcular DFT", str(exc))

    def _show_idft(self):
        if self.signal is None: return self._need_signal()
        try:
            source = self.signal
            self._run_operation("Calculando IDFT…", lambda: idft(source),
                lambda result: self._operation_succeeded(result, "IDFT: normalización 1/N aplicada; salida compleja en n entero desde cero."))
        except Exception as exc: QMessageBox.warning(self, "No se pudo calcular IDFT", str(exc))

    def _binary_operation(self, operation):
        if self.signal is None: return self._need_signal()
        circular = False
        normalization = "sum"
        auto = False
        if operation == "correlation":
            kind, ok = QInputDialog.getItem(self, "Correlación", "Tipo:",
                ["Cruzada lineal", "Auto lineal", "Cruzada circular", "Auto circular", "Auto periódica (promedio)"], 0, False)
            if not ok: return
            auto = kind.startswith("Auto")
            circular = "circular" in kind or "periódica" in kind
            scale, ok = QInputDialog.getItem(self, "Escala de correlación",
                "No se resta la media. La circular exige igual longitud en ambas entradas.",
                (["Suma", "Normalizada por energía", "Promedio por longitud"] if circular else ["Suma", "Normalizada por energía"]),
                2 if "periódica" in kind else 0, False)
            if not ok: return
            normalization = {"Suma": "sum", "Normalizada por energía": "energy", "Promedio por longitud": "mean"}[scale]
            if auto:
                source = self.signal
                self._run_operation("Calculando autocorrelación…",
                    lambda: correlation(source, circular=circular, normalization=normalization),
                    lambda result: self._operation_succeeded(result, "Autocorrelación calculada; escala registrada en los metadatos."))
                return
        elif operation == "convolution":
            kind, ok = QInputDialog.getItem(self, "Convolución", "Modelo:",
                ["Lineal: soporte completo", "Circular: relleno a longitud máxima, eje desde cero"], 0, False)
            if not ok: return
            circular = kind.startswith("Circular")
        values, ok = QInputDialog.getText(self, "Segunda secuencia",
            "Valores de h separados por coma (se admiten complejos):", text="1, 1")
        if not ok: return
        origin_text, ok = QInputDialog.getText(self, "Origen de la segunda secuencia",
            "Índice inicial entero de h[n]:", text="0")
        if not ok: return
        try:
            h = sequence_from_values(values, int(origin_text), name="h[n]")
            source = self.signal
            functions = {"convolution": circular_convolution if circular else linear_convolution,
                         "correlation": lambda x, h: correlation(x, h, circular=circular, normalization=normalization),
                         "sum": add_sequences}
            self._run_operation(f"Calculando {operation}…", lambda: functions[operation](source, h),
                lambda result: self._operation_succeeded(result, f"Resultado {operation} · convención y escala registradas en metadatos."))
        except Exception as exc: QMessageBox.warning(self, "Operación no aplicada", str(exc))

    def _run_operation(self, message, function, on_success):
        if self._workers:
            QMessageBox.information(self, "Cálculo en curso", "Esperá el resultado antes de iniciar otro cálculo.")
            return
        worker = _OperationWorker(function)
        worker.on_success = on_success
        worker.label = message
        worker.origin=getattr(self,'current_operation',None)
        worker.last_progress = -1
        self.cancel_button.setEnabled(True)
        self.cancel_button.setVisible(True)
        self._workers.append(worker)
        worker.signals.progressed.connect(self._worker_progress, Qt.ConnectionType.QueuedConnection)
        worker.signals.finished.connect(self._worker_finished, Qt.ConnectionType.QueuedConnection)
        worker.signals.failed.connect(self._worker_failed, Qt.ConnectionType.QueuedConnection)
        self.statusBar().showMessage(message)
        self._thread_pool.start(worker)

    def _cancel_operations(self):
        for worker in self._workers:
            worker.cancel_event.set()
        self.cancel_button.setEnabled(False)
        self.statusBar().showMessage("Cancelación solicitada; esperando el próximo bloque del cálculo…")

    @Slot(object, int)
    def _worker_progress(self, worker, progress):
        if worker in self._workers and not worker.cancel_event.is_set() and progress != worker.last_progress:
            worker.last_progress = progress
            self.statusBar().showMessage(f"{worker.label} {progress}%")

    @Slot(object, object)
    def _worker_finished(self, worker, result):
        if worker not in self._workers:return
        self._workers.remove(worker)
        self.cancel_button.setEnabled(bool(self._workers))
        self.cancel_button.setVisible(bool(self._workers))
        if worker.cancel_event.is_set():
            self.statusBar().showMessage("Cálculo cancelado; resultado descartado.")
            return
        try:
            worker.on_success(result)
            count=len(getattr(self,'_last_calculation_notes',[]))
            self.statusBar().showMessage("Cálculo finalizado · Indeterminaciones levantadas: "+str(count)+". Ver informe." if count else "Cálculo finalizado.")
        except Exception as exc:
            import traceback
            from .runtime_diagnostics import report_error
            self.statusBar().showMessage('El cálculo terminó, pero no se pudo presentar el resultado.')
            report_error(self,'No se pudo presentar el resultado',exc,details=''.join(traceback.format_exception(type(exc),exc,exc.__traceback__)),context=getattr(worker,'origin',None) or worker.label)

    @Slot(object, str)
    def _worker_failed(self, worker, error):
        if worker not in self._workers:return
        self._workers.remove(worker)
        self.cancel_button.setEnabled(bool(self._workers))
        self.cancel_button.setVisible(bool(self._workers))
        if worker.cancel_event.is_set():
            self.statusBar().showMessage("Cálculo cancelado; no se guardó un resultado parcial.")
            return
        self.statusBar().showMessage("El cálculo no terminó.")
        from .runtime_diagnostics import report_error
        report_error(self,'No se pudo completar el cálculo',error,details=getattr(worker,'failure_details',''),context=getattr(worker,'origin',None) or worker.label)

    def _operation_succeeded(self, result, message):
        self._set_signal(result)
        self.statusBar().showMessage(message)

    def _show_even_odd(self):
        if self.signal is None: return self._need_signal()
        source = self.signal
        self._run_operation("Separando partes par e impar…", lambda: even_odd_parts(source), self._show_even_odd_result)

    def _show_even_odd_result(self, result):
        even, odd = result
        self._set_signal(even)
        self._remember_signal(odd)
        QMessageBox.information(self, "Partes par e impar",
            "Se muestra x_par[n]. La parte impar quedó guardada en el banco de esta sesión; ambas partes conservan el eje entero.")
    def _table_edited(self, item):
        if self.signal is None or item.column() not in (1, 2): return
        row = item.row()
        try:
            values = self.signal.values.copy()
            real_item, imag_item = self.table.item(row, 1), self.table.item(row, 2)
            index = self.table_offset + row
            values[index] = complex(float(real_item.text()), float(imag_item.text()))
            self.signal = self.signal.copy_with(values=values)
            self._remember_signal(self.signal)
            self._refresh()
        except Exception:
            QMessageBox.warning(self, "Valor inválido", "Usá valores reales finitos en las columnas Real e Imaginaria.")
            self._refresh()

    def _show_shift(self):
        if self.signal is None: return self._need_signal()
        text, ok = QInputDialog.getText(self, "Desplazar secuencia", "Desplazamiento entero k (x[n-k] conserva valores y cambia el origen):", text="1")
        if ok:
            try:
                source, amount = self.signal, int(text)
                self._run_operation("Desplazando secuencia…", lambda: shift(source, amount), lambda r: self._operation_succeeded(r, "Desplazamiento aplicado."))
            except Exception as exc: QMessageBox.warning(self, "No se pudo desplazar", str(exc))

    def _show_reverse(self):
        if self.signal is None: return self._need_signal()
        try:
            source = self.signal
            self._run_operation("Invirtiendo secuencia…", lambda: reverse(source), lambda r: self._operation_succeeded(r, "Eje invertido."))
        except Exception as exc: QMessageBox.warning(self, "No se pudo invertir", str(exc))

    def _show_scale(self):
        if self.signal is None: return self._need_signal()
        text, ok = QInputDialog.getText(self, "Escalar amplitud", "Factor real o complejo:", text="2")
        if ok:
            try:
                source, factor = self.signal, self._parse_complex(text)
                self._run_operation("Escalando amplitud…", lambda: scale_amplitude(source, factor), lambda r: self._operation_succeeded(r, "Escala aplicada."))
            except Exception as exc: QMessageBox.warning(self, "No se pudo escalar", str(exc))

    def _export_json(self):
        if self.signal is None: return self._need_signal()
        path, _ = QFileDialog.getSaveFileName(self, "Exportar señal SignalLab", f"{self.signal.name}.json", "SignalLab JSON (*.json)")
        if path:
            try: save_json(self.signal, path); self.last_path = Path(path); self.exchange_path.setText(path)
            except Exception as exc: QMessageBox.critical(self, "Error de exportación", str(exc))

    def _export_csv(self):
        if self.signal is None: return self._need_signal()
        path, _ = QFileDialog.getSaveFileName(self, "Exportar tabla de señal", f"{self.signal.name}.csv", "CSV (*.csv)")
        if path:
            try: save_csv(self.signal, path); self.exchange_path.setText(path)
            except Exception as exc: QMessageBox.critical(self, "Error de exportación", str(exc))

    def _import_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Importar señal SignalLab", "", "SignalLab JSON (*.json)")
        if path:
            try:
                self._set_signal(load_json(path)); self.last_path = Path(path); self.exchange_path.setText(path)
                self.tabs.setCurrentIndex(1)
            except Exception as exc: QMessageBox.critical(self, "No se pudo importar", str(exc))

    def _reuse_last(self):
        names = list(self.signal_bank)
        if not names and self.last_path and self.last_path.exists():
            try:
                self._set_signal(load_json(self.last_path))
                return
            except Exception:
                pass
        if names:
            selected, ok = QInputDialog.getItem(self, "Banco de señales", "Seleccioná una señal de esta sesión:", names, max(0, len(names) - 1), False)
            if ok and selected:
                self.signal = self.signal_bank[selected]
                self._refresh()
            return
        self.tabs.setCurrentIndex(3)
        QMessageBox.information(self, "Banco de señales", "Creá o importá una señal para agregarla al banco de esta sesión.")

    def _need_signal(self):
        QMessageBox.information(self, "No hay señal", "Primero creá o importá una señal.")


def main():
    # Stable identity lets Windows associate all windows with the portable icon.
    if sys.platform=='win32':
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('SignalLab.PC.Desktop')
    app = QApplication(sys.argv)
    from PySide6.QtGui import QIcon
    app.setWindowIcon(QIcon(str(Path(__file__).parent/'assets'/'signallab.ico')))
    app.setStyle("Fusion")
    app.setApplicationName("SignalLab PC")
    from .runtime_diagnostics import install_exception_hook
    install_exception_hook(app)
    from .workbench import WorkbenchWindow
    window = WorkbenchWindow(); window.show()
    raise SystemExit(app.exec())




