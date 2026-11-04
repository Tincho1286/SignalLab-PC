"""Dos vistas de una misma definición: edición de tramos y notación matemática."""
import ast
from PySide6.QtCore import Signal,QTimer
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLineEdit,QComboBox,QTableWidget,QTableWidgetItem,QHeaderView,QPushButton,QLabel,QInputDialog
from .report_view import ReportView
from .expression_structure import parse_cases,serialize_cases


class ExpressionEditor(QWidget):
    textChanged=Signal(str)
    def __init__(self,value='',parent=None,symbolic=False):
        super().__init__(parent);self.symbolic=symbolic;self._loading=False;self._has_cases=False
        box=QVBoxLayout(self);box.setContentsMargins(0,0,0,0);box.setSpacing(6)
        self.mode=QComboBox();self.mode.addItems(['Fórmula','Por tramos']);
        from .choice_buttons import ChoiceButtons
        self.method_buttons=ChoiceButtons(self.mode);box.addWidget(self.method_buttons)
        self.field=QLineEdit();self.field.setPlaceholderText('Ingresá la expresión de la señal');box.addWidget(self.field)
        self.preview=ReportView();self.preview.setMinimumHeight(80);self.preview.setMaximumHeight(220);box.addWidget(self.preview)
        self.continuity_note=QLabel('Indeterminaciones removibles: se completa por límite bilateral finito. El informe registra los casos; el criterio se explica en Ayuda (F1).');self.continuity_note.setWordWrap(True);self.continuity_note.setObjectName('muted');box.addWidget(self.continuity_note)
        self.replace_button=QPushButton('Reemplazar por otra fórmula…');self.replace_button.clicked.connect(self.replace_formula);box.addWidget(self.replace_button)
        self.table=QTableWidget(0,2);self.table.setHorizontalHeaderLabels(['Valor','Cuando']);self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);self.table.setMinimumHeight(180);box.addWidget(self.table)
        self.other_label=QLabel('En los demás casos');box.addWidget(self.other_label)
        self.other=QLineEdit('0');self.other.setPlaceholderText('Vacío: sin valor definido fuera de los tramos');box.addWidget(self.other)
        self.actions=QWidget();row=QHBoxLayout(self.actions);row.setContentsMargins(0,0,0,0)
        add=QPushButton('+ Tramo');remove=QPushButton('Quitar tramo');row.addWidget(add);row.addWidget(remove);box.addWidget(self.actions)
        self.hint=QLabel('Se usa el primer tramo que cumple su condición. La vista matemática muestra esta misma definición.');self.hint.setWordWrap(True);box.addWidget(self.hint)
        add.clicked.connect(lambda:self.add_row('1',self.variable()+' >= 0'));remove.clicked.connect(self.remove_row)
        self.preview_timer=QTimer(self);self.preview_timer.setSingleShot(True);self.preview_timer.setInterval(180);self.preview_timer.timeout.connect(self.render_preview)
        self.field.textChanged.connect(self.changed);self.other.textChanged.connect(self.changed);self.table.itemChanged.connect(self.changed);self.mode.currentIndexChanged.connect(self.change_mode)
        self.setText(value)
    def variable(self):
        try:
            from .math_source import normalize
            tree=ast.parse(normalize(self.text()),mode='eval')
            names={node.id for node in ast.walk(tree) if isinstance(node,ast.Name)}
            return next((name for name in ('n','k','t','w','s','z','x') if name in names),self.property('variableHint') or 't')
        except SyntaxError:return self.property('variableHint') or 't'
    def add_row(self,value,condition):
        loading=self._loading;self._loading=True
        row=self.table.rowCount();self.table.insertRow(row);self.table.setItem(row,0,QTableWidgetItem(value));self.table.setItem(row,1,QTableWidgetItem(condition))
        self._loading=loading;self.changed()
    def remove_row(self):
        if self.table.currentRow()>=0:self.table.removeRow(self.table.currentRow());self.changed()
    def text(self):
        if not self._has_cases:return self.field.text()
        rows=[(self.table.item(r,0).text() if self.table.item(r,0) else '0',self.table.item(r,1).text() if self.table.item(r,1) else 'False') for r in range(self.table.rowCount())]
        return serialize_cases(rows,self.other.text().strip() or None,self.symbolic)
    def setText(self,value):
        self._loading=True;self.field.setText(value)
        try:cases=parse_cases(value)
        except (SyntaxError,ValueError,RecursionError):cases=None
        self._has_cases=cases is not None;self.table.setRowCount(0)
        if cases:
            rows,otherwise=cases
            for expression,condition in rows:self.add_row(expression,condition)
            self.other.setText(otherwise if otherwise is not None else '')
        else:self.other.setText('0')
        self.mode.blockSignals(True);self.mode.setCurrentIndex(1 if self._has_cases else 0);self.mode.blockSignals(False)
        self._loading=False;self.update_view();self.changed()
    def change_mode(self,*args):
        if self._loading:return
        if self.mode.currentIndex()==1 and not self._has_cases:
            value=self.field.text() or '0';variable=self.variable();self._loading=True;self._has_cases=True
            self.table.setRowCount(0);self.add_row(value,variable+' >= 0');self.other.setText(value);self._loading=False
        self.update_view();self.changed()
    def update_view(self):
        editing=self.mode.currentIndex()==1
        self.mode.setItemText(0,'Vista matemática' if self._has_cases else 'Fórmula')
        self.field.setVisible(not self._has_cases and not editing);self.preview.setVisible(not editing)
        self.replace_button.setVisible(self._has_cases and not editing)
        for widget in (self.table,self.other_label,self.other,self.actions,self.hint):widget.setVisible(editing)
    def replace_formula(self):
        value,accepted=QInputDialog.getText(self,'Nueva definición','Fórmula que reemplazará todos los tramos:')
        if accepted and value.strip():self.setText(value.strip())
    def render_preview(self):
        source=self.text()
        self.preview.setPlainText(source)
        # Incluso una constante sola merece notación matemática en este editor.
        from .math_source import normalize
        try:source=normalize(source)
        except Exception:
            return
        rendered=self.preview._render_formula(source)
        if rendered:self.preview.setHtml('<html><body style="color:#dce4ef">'+rendered+'</body></html>')
    def changed(self,*args):
        if self._loading:return
        self.preview_timer.start();self.textChanged.emit(self.text())
