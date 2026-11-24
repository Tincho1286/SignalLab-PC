"""Searchable command templates for the CAS worksheet."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QHeaderView, QLineEdit,
                               QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout)

from .tool_catalog import normalize


GROUPS = (
    ('Álgebra', (
        ('Simplificar', 'simplify(expr)'), ('Desarrollar', 'expand(expr)'), ('Factorizar', 'factor(expr)'),
        ('Unificar fracción', 'together(expr)'), ('Fracciones parciales', 'apart(expr,x)'),
        ('Sustituir', 'subst(expr,x,valor)'), ('Aproximar', 'approx(expr,15)'),
        ('Proponer forma exacta', 'exact(expr)'), ('Declarar supuesto', 'assume(x>0)'),
        ('Exponenciales a trigonometría', 'exp2trig(expr)'), ('Trigonometría a exponenciales', 'trig2exp(expr)'),
    )),
    ('Cálculo', (
        ('Derivar', 'diff(expr,x)'), ('Integral', 'integrate(expr,x)'), ('Integral definida', 'integrate(expr,x,a,b)'),
        ('Límite', 'limit(expr,x,0)'), ('Serie', 'series(expr,x,0,6)'),
        ('Sumatoria', 'sum(expr,n,a,b)'), ('Producto', 'prod(expr,n,a,b)'),
    )),
    ('Ecuaciones', (
        ('Resolver en complejos', 'solve(expr,x)'), ('Resolver en reales', 'solve_real(expr,x)'),
        ('Sistema de ecuaciones', 'solve([ecuacion1,ecuacion2],[x,y])'),
        ('Sistema lineal', 'linsolve([ecuacion1,ecuacion2],[x,y])'),
        ('Raíz numérica local', 'nsolve(expr,x,1)'), ('Ecuación diferencial', 'dsolve(expr,y(x))'),
    )),
    ('Matrices', (
        ('Crear matriz', 'matrix([[a,b],[c,d]])'), ('Determinante', 'det(expr)'), ('Inversa', 'inv(expr)'),
        ('Transpuesta', 'transpose(expr)'), ('Rango', 'rank(expr)'),
        ('Autovalores', 'eigenvalues(expr)'), ('Forma escalonada reducida', 'rref(expr)'),
    )),
    ('Hiperbólicas', tuple((name, f'{name}(x)') for name in
                          ('sinh', 'cosh', 'tanh', 'sech', 'csch', 'coth', 'asinh', 'acosh', 'atanh', 'asech', 'acsch', 'acoth'))),
)


class CasCommandDialog(QDialog):
    def __init__(self, parent, on_insert, on_help=None):
        super().__init__(parent)
        self.on_insert = on_insert
        self.setWindowTitle('Comandos del CAS')
        self.resize(620, 475)
        root = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText('Buscar comando o sintaxis…')
        self.search.setAccessibleName('Buscar comandos del CAS')
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.populate)
        self.search.returnPressed.connect(self.insert_selected)
        root.addWidget(self.search)
        self.commands = QTreeWidget()
        self.commands.setHeaderLabels(['Operación', 'Sintaxis'])
        self.commands.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.commands.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.commands.setColumnWidth(0, 250)
        self.commands.setAccessibleName('Plantillas de comandos CAS')
        self.commands.itemActivated.connect(self.insert_selected)
        self.commands.currentItemChanged.connect(self.update_selection)
        root.addWidget(self.commands, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText('Cerrar')
        buttons.rejected.connect(self.reject)
        self.insert_button = QPushButton('Insertar comando')
        self.insert_button.setObjectName('primary')
        self.insert_button.setAutoDefault(False)
        buttons.addButton(self.insert_button, QDialogButtonBox.ButtonRole.ActionRole)
        self.insert_button.clicked.connect(self.insert_selected)
        if on_help is not None:
            help_button = buttons.addButton('Guía de argumentos', QDialogButtonBox.ButtonRole.HelpRole)
            help_button.setAutoDefault(False)
            help_button.clicked.connect(lambda: (self.close(), on_help()))
        root.addWidget(buttons)
        self.populate('')

    def open(self):
        self.search.clear()
        super().open()
        self.search.setFocus()

    def populate(self, value):
        words = normalize(value).split()
        self.commands.clear()
        first = None
        for group, records in GROUPS:
            entries = [(name, template) for name, template in records
                       if all(word in normalize(f'{group} {name} {template}') for word in words)]
            if not entries:
                continue
            branch = QTreeWidgetItem([group])
            branch.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.commands.addTopLevelItem(branch)
            for name, template in entries:
                item = QTreeWidgetItem([name, template])
                item.setData(0, Qt.ItemDataRole.UserRole, template)
                item.setToolTip(1, template)
                branch.addChild(item)
                if first is None:
                    first = item
            branch.setExpanded(bool(words) or group == 'Álgebra')
        if first is not None:
            self.commands.setCurrentItem(first)
        self.update_selection()

    def update_selection(self, *_):
        item = self.commands.currentItem()
        self.insert_button.setEnabled(item is not None and bool(item.data(0, Qt.ItemDataRole.UserRole)))

    def insert_selected(self, *_):
        item = self.commands.currentItem()
        template = item.data(0, Qt.ItemDataRole.UserRole) if item is not None else None
        if template:
            self.accept()
            self.on_insert(template)
