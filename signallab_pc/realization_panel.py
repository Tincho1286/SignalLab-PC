"""Realization results inside system analysis, with a separate diagram window."""
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QLineEdit,QMenu,QMessageBox
from .report_view import ReportView,report_panel
from .realization import realize_system,realization_summary
from .numeric_input import real_field


class RealizationPanel(QWidget):
    def __init__(self,window):
        super().__init__();self.owner=window;self.source=None;self.advance=0;self.key=None;self.value=None;self.diagram=None
        root=QVBoxLayout(self);root.setContentsMargins(0,0,0,0)
        self.open_button=QPushButton('Abrir diagrama de realización');self.open_button.clicked.connect(self.open_diagram);root.addWidget(self.open_button)
        self.clock=QWidget();row=QHBoxLayout(self.clock);row.setContentsMargins(0,0,0,0);label=QLabel('Período T (s) para estados');label.setWordWrap(True);row.addWidget(label);self.period=QLineEdit('1');self.period.setMaximumWidth(130);row.addWidget(self.period);row.addStretch();root.addWidget(self.clock);self.clock.hide()
        self.period.setToolTip('Sólo establece el reloj al enviar el modelo a Espacio de estados. No cambia H(z) ni el diagrama.')
        self.states_button=QPushButton('Usar en espacio de estados…');menu=QMenu(self.states_button);self.states_button.setMenu(menu)
        for title,action in [('Estructura y estabilidad','analysis'),('Respuesta temporal','simulation'),('Respuesta en frecuencia','frequency'),('Obtener transferencia','transfer')]:menu.addAction(title,lambda checked=False,destination=action:self.send_model(destination))
        root.addWidget(self.states_button)
        self.report=ReportView();root.addWidget(report_panel(self.report),1);self.clear_result()
    def clear_result(self):
        self.source=None;self.value=None;self.open_button.setEnabled(False);self.states_button.setEnabled(False);self.clock.hide()
        self.report.setPlainText('Analizá H y seleccioná Realización para ver su estructura y sus ecuaciones.')
        if self.diagram is not None:self.diagram.hide()
    def set_system(self,system,advance=0,key=None):
        if self.source is system and self.advance==advance:
            self.key=key;return
        self.source=system;self.advance=advance;self.key=key;self.value=None
        if self.diagram is not None:self.diagram.hide()
        try:
            self.value=realize_system(system,advance);self.report.set_readable(realization_summary(self.value))
        except (ValueError,MemoryError,OverflowError) as exc:self.report.setPlainText('Realización no disponible\n\n'+str(exc))
        self.open_button.setEnabled(self.value is not None);self.states_button.setEnabled(self.value is not None);self.clock.setVisible(self.value is not None and self.value.domain=='digital')
        if system.sample_period_s is not None:self.period.setText(repr(float(system.sample_period_s)))
        self._diagram_value=None
    def open_diagram(self):
        if self.value is None:return
        try:
            from .realization_diagram import RealizationWindow
            if self.diagram is None:self.diagram=RealizationWindow(self)
            new_diagram=self._diagram_value is not self.value
            if new_diagram:self.diagram.set_realization(self.value);self._diagram_value=self.value
            self.diagram.show();self.diagram.raise_();self.diagram.activateWindow()
            if new_diagram:self.diagram.fit_width()
        except Exception as exc:QMessageBox.warning(self,'No se pudo abrir el diagrama',str(exc))
    def send_model(self,destination):
        if self.value is None:return
        try:
            dt=real_field(self.period) if self.value.domain=='digital' else None
            if dt is not None and dt<=0:raise ValueError('El período T debe ser positivo.')
            value=self.value;parent=self.key
            def accept(model):
                from .workspaces import ROUTES
                key=self.owner.publish(model,operation='Diagrama a espacio de estados',parents=[parent] if parent else [])
                route=ROUTES['state_space',destination];self.owner.send_model(model,key,route)
                self.owner.statusBar().showMessage('Matrices de la realización cargadas. Revisá los parámetros y calculá.')
            self.owner._run_operation('Obteniendo matrices de la realización…',lambda:value.to_model(dt),accept)
        except Exception as exc:QMessageBox.warning(self,'No se pudo obtener el modelo',str(exc))

