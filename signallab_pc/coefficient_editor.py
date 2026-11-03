"""Coeficientes ligados visualmente a sus potencias, sin evaluar la entrada."""
import re
from PySide6.QtCore import Qt,QAbstractTableModel,QModelIndex,Signal,QTimer
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QTableView,QHeaderView,QPushButton,QLineEdit,QToolButton,QSizePolicy
from .report_view import ReportView

def split_coefficients(value):
    parts=[];start=0;depth=0
    for index,char in enumerate(value):
        if char in '([{':depth+=1
        elif char in ')]}':depth=max(0,depth-1)
        elif char in ',;' and depth==0:parts.append(value[start:index].strip());start=index+1
    parts.append(value[start:].strip());return parts

class CoefficientRows(QAbstractTableModel):
    def __init__(self,parent=None):
        super().__init__(parent);self.values=['1'];self.digital=False
    def rowCount(self,parent=QModelIndex()):return 0 if parent.isValid() else len(self.values)
    def columnCount(self,parent=QModelIndex()):return 0 if parent.isValid() else 2
    def power(self,row):return -row if self.digital else len(self.values)-row-1
    def data(self,index,role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():return None
        if role in (Qt.ItemDataRole.DisplayRole,Qt.ItemDataRole.EditRole,Qt.ItemDataRole.ToolTipRole):
            if index.column()==1:return self.values[index.row()]
            exponent=self.power(index.row());variable='z' if self.digital else 's'
            return '1' if exponent==0 else variable if exponent==1 else variable+str(exponent).translate(str.maketrans('-0123456789','⁻⁰¹²³⁴⁵⁶⁷⁸⁹'))
    def headerData(self,section,orientation,role=Qt.ItemDataRole.DisplayRole):
        if role==Qt.ItemDataRole.DisplayRole:return ('Potencia','Coeficiente')[section] if orientation==Qt.Orientation.Horizontal else str(section)
    def flags(self,index):return super().flags(index)|(Qt.ItemFlag.ItemIsEditable if index.column()==1 else Qt.ItemFlag.NoItemFlags)
    def setData(self,index,value,role=Qt.ItemDataRole.EditRole):
        if not index.isValid() or index.column()!=1 or role!=Qt.ItemDataRole.EditRole:return False
        self.values[index.row()]=str(value).strip();self.dataChanged.emit(index,index);return True

class CoefficientEditor(QWidget):
    textChanged=Signal(str)
    def __init__(self,value='1',parent=None,digital=False):
        super().__init__(parent);self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed);box=QVBoxLayout(self);box.setContentsMargins(0,0,0,0);box.setSpacing(4)
        quick=QHBoxLayout();self.inline=QLineEdit();self.inline.setPlaceholderText('Coeficientes separados por coma');self.inline.setToolTip('Admite pi, fracciones, 10^(-x), notación científica y complejos.');quick.addWidget(self.inline,1);self.detail_button=QToolButton();self.detail_button.setText('Potencias');self.detail_button.setCheckable(True);self.detail_button.setToolTip('Ver y editar cada coeficiente junto a su potencia');quick.addWidget(self.detail_button);box.addLayout(quick)
        self.model=CoefficientRows(self);self.model.digital=digital;self.table=QTableView();self.table.setModel(self.model);self.table.setToolTip('Coeficientes constantes: pi, 10^(-3), 1e-3, fracciones y complejos. Una celda por coeficiente; conservá los ceros intermedios.');self.table.setMinimumHeight(110);self.table.setMaximumHeight(170);self.table.verticalHeader().hide();self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.ResizeToContents);self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.Stretch);box.addWidget(self.table)
        row=QHBoxLayout();add=QPushButton('+ Mayor orden');remove=QPushButton('− Mayor orden');row.addWidget(add);row.addWidget(remove);self.term_actions=QWidget();self.term_actions.setLayout(row);box.addWidget(self.term_actions);self.table.hide();self.term_actions.hide();self.detail_button.toggled.connect(self.table.setVisible);self.detail_button.toggled.connect(self.term_actions.setVisible)
        add.setToolTip('Agrega un coeficiente cero en la potencia de mayor orden, sin cambiar el polinomio.');remove.setToolTip('Quita el coeficiente de mayor orden; los otros términos conservan su potencia.')
        add.clicked.connect(self.add_term);remove.clicked.connect(self.remove_term);self.model.dataChanged.connect(self.model_changed);self.inline.textEdited.connect(self.inline_changed);self.setText(value)
    def inline_changed(self,value):
        self.model.beginResetModel();self.model.values=split_coefficients(value);self.model.endResetModel();self.fit_table();self.textChanged.emit(self.text())
    def model_changed(self,*_):
        self.inline.setText(self.text());self.textChanged.emit(self.text())
    def fit_table(self):self.table.setFixedHeight(48+30*min(max(1,len(self.model.values)),5))
    def text(self):return ', '.join(self.model.values)
    def coefficients(self):
        import sympy as sp
        from .symbolic import parse,T,S,N,Z,W
        from .numeric_input import field_name
        from .validation import invalid
        for index,value in enumerate(self.model.values):
            try:
                expression=parse(value)
                if expression.has(T,S,N,Z,W):raise ValueError('El coeficiente debe ser constante respecto de los ejes t, s, n, z y w.')
                if expression.has(sp.zoo,sp.nan,sp.oo):raise ValueError('El coeficiente debe ser finito.')
            except Exception as exc:
                invalid(self.inline,'coeficiente '+str(index+1)+' incorrecto: '+str(exc),'Se admiten pi, 10^(-3), 1e-3, fracciones y complejos; separá los coeficientes con comas.',name=field_name(self))
        if not self.model.values:invalid(self.inline,'la lista está vacía.','Ingresá al menos un coeficiente; por ejemplo 1, 0, pi/4.',name=field_name(self))
        return list(self.model.values)
    def setText(self,value):
        values=split_coefficients(str(value))
        self.model.beginResetModel();self.model.values=values;self.model.endResetModel();self.fit_table();self.model_changed()
    def set_domain(self,digital):
        self.model.beginResetModel();self.model.digital=bool(digital);self.model.endResetModel()
    def add_term(self):
        self.model.beginResetModel()
        if self.model.digital:self.model.values.append('0')
        else:self.model.values.insert(0,'0')
        self.model.endResetModel();self.fit_table();self.model_changed()
    def remove_term(self):
        if len(self.model.values)<=1:return
        self.model.beginResetModel();self.model.values.pop(-1 if self.model.digital else 0);self.model.endResetModel();self.fit_table();self.model_changed()
    def expression(self):
        terms=[];variable='z' if self.model.digital else 's'
        for index,value in enumerate(self.model.values):
            if not value:raise ValueError('Completá todos los coeficientes.')
            if re.fullmatch(r'[+-]?(?:0+(?:\.0*)?|\.0+)(?:[eE][+-]?\d+)?(?:[ij])?',value):continue
            value=re.sub(r'(?<=[0-9.)])i\b','*i',value)
            power=self.model.power(index)
            factor=variable if power==1 else variable+'^('+str(power)+')'
            if power and value in ('1','1.0','+1'):terms.append(factor)
            elif power and value in ('-1','-1.0'):terms.append('-'+factor)
            else:terms.append('('+value+')'+('*'+factor if power else ''))
        return '+'.join(terms) or '0'

class TransferPreview(ReportView):
    def __init__(self,numerator,denominator,parent=None):
        super().__init__(parent);self.numerator=numerator;self.denominator=denominator;self.setFixedHeight(88)
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.setInterval(180);self.timer.timeout.connect(self.refresh)
        numerator.textChanged.connect(self.schedule);denominator.textChanged.connect(self.schedule);self.schedule()
    def schedule(self,*_):self.timer.start()
    def refresh(self):
        if len(self.numerator.coefficients())+len(self.denominator.coefficients())>16:
            self.setPlainText('La vista previa se omite para listas largas. Todos los coeficientes permanecen en las tablas y se usan en el cálculo.');return
        try:
            denominator=self.denominator.expression()
            if denominator=='0':
                self.setPlainText('El denominador no puede ser cero. Editá al menos uno de sus coeficientes.');return
            variable='z' if self.numerator.model.digital else 's';expression='H('+variable+') = ('+self.numerator.expression()+')/('+denominator+')'
            self._formula_number=0;rendered=self._render_formula(expression)
            if not rendered:raise ValueError('Vista no disponible')
            self._raw=expression;self.setHtml('<html><body style="color:#dce4ef">'+rendered+'</body></html>')
        except (ValueError,RecursionError):self.setPlainText('Vista previa pendiente. Completá los coeficientes; su validez matemática se comprueba al calcular.')
