from .numeric_input import real_field,integer_field
from .report_view import ReportView
from .expression_editor import ExpressionEditor
"""Panel CAS: resultados exactos, supuestos y exportación recuperable."""
import json
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QComboBox,
    QLineEdit, QPushButton, QPlainTextEdit, QMessageBox, QFileDialog, QLabel, QScrollArea)
from .symbolic_process import run_request
from .model import Signal
from .resources import ensure_working_set


class SymbolicPanel(QWidget):
    def __init__(self, owner):
        super().__init__(); self.owner=owner; self.result=None
        root=QHBoxLayout(self); controls=QWidget(); form=QFormLayout(controls)
        scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(controls); root.addWidget(scroll,1)
        self.operation=QComboBox(); self.operation.addItems(["Laplace directa unilateral", "Laplace inversa causal", "Z del registro finito cargado", "Z inversa racional (rama derecha)", "EDO lineal de coeficientes constantes"])
        form.addRow("Operación",self.operation)
        self.expression=ExpressionEditor("exp(-t)"); self.expression.symbolic=True; form.addRow("Expresión",self.expression)
        from .expression_import import install_expression_import
        install_expression_import(self.expression,owner.window if hasattr(owner,'window') and not callable(owner.window) else owner,lambda:[['t','s','n','z','t'][self.operation.currentIndex()]])
        self.count=QLineEdit("64"); form.addRow("Términos de la Z inversa",self.count)
        self.coefficients=QLineEdit("1, 1"); form.addRow("EDO: a0, a1, …, am",self.coefficients)
        self.initial=QLineEdit("0"); form.addRow("EDO: y(0), y′(0), …",self.initial)
        help_text=QLabel("EDO: a0·y + a1·y′ + … = f(t).\n\nUse t, s, z, n, pi, i y funciones matemáticas. Ejemplos: exp(-t), 1/(s+1), z/(z-1/2).\n\nLa inversa Z elige soporte acotado por la izquierda; otra región de convergencia puede dar una señal distinta. N controla cuántos términos se muestran, no trunca la definición matemática.")
        help_text.setWordWrap(True); form.addRow(help_text)
        self._button(form,"Calcular",self.calculate)
        self._button(form,"Ver las muestras de Z inversa",self.use_sequence)
        self._button(form,"Guardar resultado y supuestos…",self.save)
        def select_operation(index):
            form.setRowVisible(self.expression,index!=2)
            form.setRowVisible(self.count,index==3)
            form.setRowVisible(self.coefficients,index==4)
            form.setRowVisible(self.initial,index==4)
            help_text.setText(["Laplace unilateral: x(t), con t ≥ 0. Ejemplo: exp(-t).",
                "Inversa causal. Ejemplo: 1/(s+1). Revisá los supuestos del resultado.",
                "Se utiliza la secuencia de entrada, con sus índices originales.",
                "Expansión racional alrededor de z=infinito. Ejemplo: z/(z-1/2). Otra ROC puede definir otra señal.",
                "a0·y + a1·y′ + … = f(t). Indicá una condición inicial por derivada."][index])
        self.operation.currentIndexChanged.connect(select_operation);select_operation(0)
        self.report=ReportView();self.report.setReadOnly(True);root.addWidget(self.report,2)
        self.report.setPlainText("Las operaciones simbólicas se ejecutan por separado. Cancelar detiene ese proceso y conserva el último resultado. Una transformada que el motor deja sin evaluar se informa como pendiente de resolución.")

    def _button(self,form,title,callback):
        button=QPushButton(title)
        if title=="Calcular":button.setObjectName("primary")
        def invoke():
            try:callback()
            except Exception as exc:QMessageBox.warning(self,"Operación no aplicada",str(exc))
        button.clicked.connect(invoke);form.addRow(button)

    def calculate(self):
        operation=["laplace","inverse_laplace","z_finite","inverse_z","ode"][self.operation.currentIndex()]
        request={"operation":operation,"expression":self.expression.text()}
        if operation=="z_finite":
            source=self.owner.signal
            if source is None or source.domain!="discrete":raise ValueError("Cargá una secuencia discreta con índices enteros.")
            ensure_working_set(int(source.values.size),bytes_per_sample=1024,live_arrays=12)
            request.update(origin=int(source.origin),samples=[[float(v.real),float(v.imag)] for v in source.values])
        if operation=="inverse_z":request["count"]=integer_field(self.count)
        if operation=="ode":
            request.update(coefficients=[v.strip() for v in self.coefficients.text().split(",")],
                           initial=[v.strip() for v in self.initial.text().split(",")])
        def accept(result):
            self.result={"request":request,"result":result}
            remember=getattr(self.owner,"_remember_calculation",None)
            if remember:remember(self.result)
            lines=[result.get("operation","Resultado")]
            labels={"result":"Resultado", "convergence":"Semiplano de convergencia", "condition":"Condición",
                    "scope":"Alcance", "roc":"Región de convergencia", "roc_finite_plane":"ROC finita",
                    "infinity_included":"Incluye z=infinito", "origin":"Primer índice", "Y(s)":"Y(s)",
                    "forcing_convergence":"Convergencia de la entrada"}
            for key,label in labels.items():
                if key in result:lines.append(f"{label}: {result[key]}")
            if "evaluated" in result:
                lines.append("Estado: expresión resuelta por el motor." if result["evaluated"] else "Estado: el motor dejó parte del cálculo sin evaluar; no se declara resuelto.")
            if "coefficients" in result:
                terms=result["coefficients"];origin=result["origin"]
                lines.append("\nTérminos exactos:")
                lines.extend(f"x[{origin+i}] = {value}" for i,value in enumerate(terms[:200]))
                if len(terms)>200:lines.append(f"Se muestran 200 de {len(terms)} términos. Guardar exporta todos; usar muestras conserva la secuencia completa.")
            self.report.setPlainText("\n\n".join(lines))
        self.owner._run_operation("Calculando expresión simbólica…",lambda:run_request(request),accept)

    def use_sequence(self):
        if not self.result:raise ValueError("Calculá una Z inversa primero.")
        result=self.result["result"]
        values=result.get("numeric_samples")
        if values is None:raise ValueError("No hay muestras numéricas finitas: puede haber parámetros simbólicos pendientes.")
        sequence=Signal([complex(*v) for v in values],result["origin"],1,"n","Z_inversa","discrete","",
                        {"operation":"inverse_z_finite_window","roc":result["roc"],"scope":result["scope"],"source_expression":self.result["request"]["expression"]})
        self.owner._set_signal(sequence)

    def save(self):
        if self.result is None:raise ValueError("Primero calculá un resultado.")
        path,_=QFileDialog.getSaveFileName(self,"Guardar cálculo simbólico","simbolico.json","JSON (*.json)")
        if path:Path(path).write_text(json.dumps(self.result,ensure_ascii=False,indent=2),encoding="utf-8")
