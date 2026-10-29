"""Exact scalar root entry, backed by the editor's existing root lists."""
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QGroupBox,QComboBox,QLineEdit,QPushButton,QCheckBox,QLabel,QTableWidget,QTableWidgetItem,QHeaderView,QAbstractItemView
from .numeric_input import real_field,constant_value
from .coefficient_editor import split_coefficients


def scalar_source(field):return field.text().strip().replace('π','pi').replace('−','-')


def polar_expression(radius,angle):
    """Keep the expression; make exact multiples of pi/2 truly axial."""
    r=real_field(radius);theta=real_field(angle)
    if r<0:raise ValueError('El módulo debe ser no negativo. Para un punto real negativo usá ángulo pi, o forma binómica.')
    if r==0:return '0'
    rs=scalar_source(radius);ts=scalar_source(angle);quadrant=None
    try:
        import sympy as sp
        from .symbolic import parse
        ratio=sp.cancel(2*parse(ts)/sp.pi)
        if isinstance(ratio,sp.Integer):quadrant=int(ratio)%4
    except (ValueError,TypeError,NotImplementedError):pass
    if quadrant is not None:return [f'({rs})',f'({rs})*i',f'-({rs})',f'-({rs})*i'][quadrant]
    return f'({rs})*exp(i*({ts}))'


class RootEntry(QWidget):
    def __init__(self,editor):
        super().__init__();self.editor=editor;self.panel=editor.panel;self.updating=False
        self.setProperty('calculationInput',False)
        box=QVBoxLayout(self);box.setContentsMargins(0,0,0,0)
        group=QGroupBox('Agregar polo o cero');form=QFormLayout(group);form.setProperty('stackFields',False)
        self.kind=QComboBox();self.kind.addItems(['Polo ×','Cero ○']);form.addRow('Tipo',self.kind)
        self.representation=QComboBox();self.representation.addItems(['Binómica · a + bi','Polar · r y θ']);form.addRow('Formato',self.representation)
        self.real=QLineEdit('0');self.imag=QLineEdit('0');self.radius=QLineEdit('1');self.angle=QLineEdit('0')
        for label,field in [('Parte real a',self.real),('Parte imaginaria b',self.imag),('Módulo r',self.radius),('Ángulo θ (rad)',self.angle)]:
            form.addRow(label,field);field.returnPressed.connect(self.add_root)
        self.real.setToolTip('Valor real exacto o expresión constante: pi/4, -0.5, 10^(-3).')
        self.imag.setToolTip('Coeficiente real que multiplica i. Puede ser positivo, cero o negativo.')
        self.radius.setToolTip('Distancia al origen, mayor o igual que cero. Se admiten fracciones y expresiones constantes.')
        self.angle.setToolTip('Ángulo en radianes: pi/4, -pi/2, pi. La forma de carga es independiente de los ejes del gráfico.')
        self.pairs=QCheckBox('Agregar también el conjugado');self.pairs.setChecked(editor.pairs.isChecked());form.addRow(self.pairs)
        self.pairs.setToolTip('Para una raíz no real agrega también su conjugada. Las raíces reales se agregan una sola vez. Se sincroniza con Pares conjugados del editor del plano.')
        self.pairs.toggled.connect(editor.pairs.setChecked);editor.pairs.toggled.connect(self.pairs.setChecked)
        self.add_button=QPushButton('Agregar a la lista');self.add_button.setProperty('primaryAction',False);self.add_button.clicked.connect(self.add_root);form.addRow(self.add_button)
        def configure(*_):
            polar=self.representation.currentIndex()==1
            for field in (self.real,self.imag):form.setRowVisible(field,not polar)
            for field in (self.radius,self.angle):form.setRowVisible(field,polar)
        self.representation.currentIndexChanged.connect(configure);configure();box.addWidget(group)
        self.heading=QLabel('Polos y ceros del diseño');self.heading.setWordWrap(True);box.addWidget(self.heading)
        self.table=QTableWidget(0,2);self.table.setHorizontalHeaderLabels(['Raíz','Valor exacto']);self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows);self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked|QAbstractItemView.EditTrigger.EditKeyPressed)
        self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.ResizeToContents);self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.Stretch)
        self.table.setWordWrap(True);self.table.setMinimumHeight(120);self.table.setMaximumHeight(240);box.addWidget(self.table)
        self.table.setToolTip('Cada fila es una raíz. Doble clic en su valor para corregirlo. Ctrl o Mayús permiten seleccionar varias; las raíces repetidas conservan su multiplicidad.')
        self.remove_button=QPushButton('Quitar seleccionados');self.remove_button.setProperty('primaryAction',False);self.remove_button.clicked.connect(self.remove_selected);box.addWidget(self.remove_button)
        self.note=QLabel('Diseñar desde polos y ceros actualiza H.');self.note.setWordWrap(True);box.addWidget(self.note)
        box.removeWidget(self.heading);box.removeWidget(self.remove_button)
        list_bar=QHBoxLayout();list_bar.addWidget(self.heading,1);list_bar.addWidget(self.remove_button);box.insertLayout(1,list_bar)
        self.table.cellChanged.connect(self.edit_value);self.table.itemSelectionChanged.connect(self.update_selection)
        for key in ('zeros','poles'):self.panel.fields[key].textChanged.connect(self.refresh)
        self.refresh()

    def available(self):
        if self.editor.busy():self.note.setText('Esperá a que termine el cálculo para editar las raíces.');return False
        return True

    def source_lists(self):return {key:split_coefficients(self.panel.fields[key].text()) if self.panel.fields[key].text().strip() else [] for key in ('zeros','poles')}

    def changed(self,message):
        self.editor.manual();self.note.setText(message+' Usá Diseñar desde polos y ceros para actualizar H y su respuesta.')

    def add_root(self):
        if not self.available():return
        try:
            self.editor.data()
            if self.representation.currentIndex()==1:expression=polar_expression(self.radius,self.angle)
            else:
                real_field(self.real);real_field(self.imag)
                expression=f'({scalar_source(self.real)})+i*({scalar_source(self.imag)})'
            value=constant_value(expression)
            if not np.isfinite([value.real,value.imag]).all():raise ValueError('La raíz debe ser finita.')
            key='poles' if self.kind.currentIndex()==0 else 'zeros';entries=self.source_lists()[key];entries.append(expression)
            if self.pairs.isChecked() and value.imag:entries.append('conj('+expression+')')
            self.panel.fields[key].setText(', '.join(entries))
            self.changed(('Polo' if key=='poles' else 'Cero')+' agregado'+(' con su conjugado.' if self.pairs.isChecked() and value.imag else '.'))
        except (ValueError,TypeError,OverflowError) as exc:self.note.setText(str(exc))

    def refresh(self,*_):
        if self.updating:return
        try:
            entries=self.source_lists();values={key:[constant_value(expr) for expr in items] for key,items in entries.items()}
        except ValueError:self.note.setText('Hay un valor inválido en las listas; corregilo antes de continuar.');return
        self.updating=True;self.table.blockSignals(True)
        try:
            self.table.setRowCount(sum(len(items) for items in entries.values()));row=0
            for key in ('poles','zeros'):
                for index,(expression,value) in enumerate(zip(entries[key],values[key])):
                    label=QTableWidgetItem('Polo ×' if key=='poles' else 'Cero ○');label.setFlags(label.flags()&~Qt.ItemFlag.ItemIsEditable);label.setData(Qt.ItemDataRole.UserRole,(key,index))
                    item=QTableWidgetItem(expression);item.setData(Qt.ItemDataRole.UserRole,(key,index))
                    item.setToolTip(expression+f'\nReal: {value.real:.17g}\nImaginaria: {value.imag:.17g}\nMódulo: {abs(value):.17g}\nÁngulo: '+(f'{np.angle(value):.17g} rad' if value else 'no definido en el origen'))
                    self.table.setItem(row,0,label);self.table.setItem(row,1,item);row+=1
            self.table.resizeRowsToContents()
            height=self.table.horizontalHeader().height()+sum(self.table.rowHeight(i) for i in range(self.table.rowCount()))+4
            self.table.setFixedHeight(max(106,min(220,height)))
            self.heading.setText(f'Polos: {len(entries["poles"])} · Ceros: {len(entries["zeros"])}')
        finally:self.table.blockSignals(False);self.updating=False;self.update_selection()

    def update_selection(self):self.remove_button.setEnabled(bool(self.table.selectionModel().selectedRows()))

    def edit_value(self,row,column):
        if self.updating or column!=1:return
        item=self.table.item(row,column)
        if item is None:return
        if not self.available():self.refresh();return
        try:
            value=item.text().strip();constant_value(value);key,index=item.data(Qt.ItemDataRole.UserRole);entries=self.source_lists()[key];entries[index]=value
            self.panel.fields[key].setText(', '.join(entries));self.changed('Raíz modificada.')
        except (ValueError,TypeError,IndexError) as exc:self.refresh();self.note.setText('Se conservó el valor anterior. '+str(exc))

    def remove_selected(self):
        if not self.available():return
        selected=[self.table.item(index.row(),0).data(Qt.ItemDataRole.UserRole) for index in self.table.selectionModel().selectedRows()]
        entries=self.source_lists()
        for key in entries:
            remove={index for kind,index in selected if kind==key}
            if remove:self.panel.fields[key].setText(', '.join(value for index,value in enumerate(entries[key]) if index not in remove))
        if selected:self.changed('Raíces seleccionadas quitadas.')
