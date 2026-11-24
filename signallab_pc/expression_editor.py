"""Dos vistas de una misma definición: edición de tramos y notación matemática."""
import ast
import html
from math import ceil
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLineEdit,QComboBox,QTableWidget,QTableWidgetItem,QHeaderView,QPushButton,QLabel,QInputDialog,QMenu,QSizePolicy,QToolButton
from .design import icon
from .report_view import ReportView
from .expression_structure import parse_cases,serialize_cases
from .wrapping_row import WrappingRow


FORMULA_HELP = 'reference:Guía de funciones y sintaxis'
SCALAR_HELP = 'reference:Coeficientes · constantes, pi y notación científica'


class ExpressionEditor(QWidget):
    textChanged=Signal(str)
    textEdited=Signal(str)
    def __init__(self,value='',parent=None,symbolic=False):
        super().__init__(parent);self.symbolic=symbolic;self._loading=False;self._has_cases=False
        box=QVBoxLayout(self);box.setContentsMargins(0,0,0,0);box.setSpacing(6)
        self.mode=QComboBox();self.mode.addItems(['Fórmula','Por tramos']);
        from .choice_buttons import ChoiceButtons
        self.method_buttons=ChoiceButtons(self.mode);box.addWidget(self.method_buttons)
        self.field=QLineEdit();self.field.setPlaceholderText('Ingresá la expresión');self.field.setAccessibleName('Fórmula');self.setFocusProxy(self.field);box.addWidget(self.field)
        tools = WrappingRow()
        self.functions_button = QToolButton()
        self.functions_button.setObjectName('formulaMenu')
        self.functions_button.setText('Funciones')
        self.functions_button.setIcon(icon('book'))
        self.functions_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.functions_button.setToolTip('Insertar funciones o consultar la sintaxis')
        self.functions_button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.functions_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.functions_menu = QMenu(self.functions_button)
        self.functions_menu.aboutToShow.connect(self.prepare_functions)
        self.functions_button.setMenu(self.functions_menu)
        tools.flow.addWidget(self.functions_button)
        self.preview_toggle = QToolButton()
        self.preview_toggle.setText('Vista previa')
        self.preview_toggle.setCheckable(True)
        self.preview_toggle.setChecked(True)
        self.preview_toggle.setProperty('segment', True)
        self.preview_toggle.toggled.connect(self.update_view)
        tools.flow.addWidget(self.preview_toggle)
        self.replace_button=QPushButton('Reemplazar los tramos…');self.replace_button.clicked.connect(self.replace_formula);tools.flow.addWidget(self.replace_button)
        box.addWidget(tools)
        self.preview=ReportView();self.preview.setObjectName('formulaPreview');self.preview.setReadOnly(True)
        self.preview.setAccessibleName('Vista previa de la expresión')
        self.preview.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self.preview.setFixedHeight(62)
        self.preview.document().documentLayout().documentSizeChanged.connect(self.fit_preview)
        box.addWidget(self.preview)
        self.table=QTableWidget(0,2);self.table.setHorizontalHeaderLabels(['Valor','Cuando']);self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);self.table.setMinimumHeight(180);box.addWidget(self.table)
        self.other_label=QLabel('En los demás casos');box.addWidget(self.other_label)
        self.other=QLineEdit('0');self.other.setPlaceholderText('Vacío: sin valor definido fuera de los tramos');box.addWidget(self.other)
        self.actions=QWidget();row=QHBoxLayout(self.actions);row.setContentsMargins(0,0,0,0)
        add=QPushButton('+ Tramo');remove=QPushButton('Quitar tramo');row.addWidget(add);row.addWidget(remove);box.addWidget(self.actions)
        self.hint=QLabel('Se usa el primer tramo que cumple su condición.');self.hint.setWordWrap(True);box.addWidget(self.hint)
        add.clicked.connect(self.append_case);remove.clicked.connect(self.remove_row)
        self.preview_timer=QTimer(self);self.preview_timer.setSingleShot(True);self.preview_timer.setInterval(180);self.preview_timer.timeout.connect(self.render_preview)
        self.field.textChanged.connect(self.changed);self.other.textChanged.connect(self.changed);self.table.itemChanged.connect(self.changed);self.mode.currentIndexChanged.connect(self.change_mode)
        def edited(*_):
            if not self._loading:self.textEdited.emit(self.text())
        self.field.textEdited.connect(edited);self.other.textEdited.connect(edited);self.table.itemChanged.connect(edited)
        self.setText(value)
    def selectAll(self):
        if not self._has_cases:self.field.selectAll()
    def variable(self):
        expected = self.property('variableHint')
        if expected:
            return expected
        try:
            from .math_source import normalize
            tree=ast.parse(normalize(self.text()),mode='eval')
            names={node.id for node in ast.walk(tree) if isinstance(node,ast.Name)}
            return next((name for name in ('n','k','t','w','s','z','x') if name in names),'t')
        except SyntaxError:return 't'

    def prepare_functions(self):
        menu = self.functions_menu
        menu.clear()
        variable = self.variable()
        if not self._has_cases:
            if variable in ('t', 'n', 'k', 'x', 'w'):
                for name, expression in (
                    ('Escalón', f'Step({variable})'),
                    ('Impulso', f'Impulse({variable})'),
                    ('Seno cardinal', f'sinc({variable})'),
                    ('Seno', f'sin({variable})'),
                    ('Exponencial', f'exp({variable})'),
                    ('Valor absoluto', f'abs({variable})'),
                ):
                    menu.addAction(f'{name}  ·  {expression}', lambda checked=False, value=expression: self.insert_formula(value))
                if variable in ('t', 'n'):
                    periodic = menu.addMenu('Señales periódicas')
                    for source in (f'PulseTrain({variable}, 2, 1)', f'ImpulseTrain({variable}, 2)'):
                        periodic.addAction(source, lambda checked=False, value=source: self.insert_formula(value))
                menu.addSeparator()
            for name, expression in (('Constante π', 'pi'), ('Unidad imaginaria', 'i')):
                menu.addAction(f'{name}  ·  {expression}', lambda checked=False, value=expression: self.insert_formula(value))
            menu.addSeparator()
        elif self.mode.currentIndex() == 1:
            fill = menu.addMenu('Completar condición del tramo')
            fill.setEnabled(self.table.currentRow() >= 0)
            for op in ('>=', '<', '=='):
                value = f'{variable} {op} 0'
                fill.addAction(value, lambda checked=False, condition=value: self.set_case_condition(condition))
        show_help = getattr(self.window(), 'show_function_help', None)
        if show_help is not None:
            reference = SCALAR_HELP if variable in ('s', 'z') else FORMULA_HELP
            menu.addAction('Sintaxis y argumentos…', lambda: show_help(reference))

    def insert_formula(self, source):
        self.field.insert(source)
        self.field.setFocus()

    def set_case_condition(self, condition):
        row = self.table.currentRow()
        if row >= 0:
            self.table.item(row, 1).setText(condition)
            self.table.setCurrentCell(row, 1)
            self.table.setFocus()

    def append_case(self):
        self.add_row('1', self.variable()+' >= 0')
        self.table.setCurrentCell(self.table.rowCount() - 1, 0)
        self.table.setFocus()

    def fit_preview(self, size):
        height = max(58, min(210, ceil(size.height()) + 10))
        if self.preview.height() != height:
            self.preview.setFixedHeight(height)
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
        if self.preview.isVisible():
            self.preview_timer.stop()
            self.render_preview()
    def change_mode(self,*args):
        if self._loading:return
        if self.mode.currentIndex()==1 and not self._has_cases:
            value=self.field.text() or '0';variable=self.variable();self._loading=True;self._has_cases=True
            self.table.setRowCount(0);self.add_row(value,variable+' >= 0');self.other.setText(value);self._loading=False
        self.update_view();self.changed()
    def update_view(self):
        editing=self.mode.currentIndex()==1
        self.mode.setItemText(0,'Vista matemática' if self._has_cases else 'Fórmula')
        self.field.setVisible(not self._has_cases and not editing)
        self.preview_toggle.setVisible(not self._has_cases)
        self.preview.setVisible(not editing and (self._has_cases or self.preview_toggle.isChecked()))
        self.replace_button.setVisible(self._has_cases and not editing)
        for widget in (self.table,self.other_label,self.other,self.actions,self.hint):widget.setVisible(editing)
    def replace_formula(self):
        value,accepted=QInputDialog.getText(self,'Nueva definición','Fórmula que reemplazará todos los tramos:')
        if accepted and value.strip():self.setText(value.strip())
    def render_preview(self):
        source=self.text()
        self.preview._raw = source
        self.preview._formula_number = 0
        rendered = self.preview._render_formula(source) if source.strip() else ''
        body = rendered or html.escape(source)
        self.preview.setHtml(f'<html><body style="margin:9px">{body}</body></html>')
        self.fit_preview(self.preview.document().size())
    def changed(self,*args):
        if self._loading:return
        self.preview_timer.start();self.textChanged.emit(self.text())
