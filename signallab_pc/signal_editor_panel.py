"""Editar un registro local y obtener una salida exportable e independiente."""
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget,QHBoxLayout,QVBoxLayout,QFormLayout,QLabel,
    QPushButton,QLineEdit,QTableWidget,QTableWidgetItem,QMessageBox,QScrollArea,
    QComboBox)
from .numeric_input import real_field,integer_field
from .resources import ensure_working_set
from .distributions import regular_only
from .active_stack import ActiveTabs,ActiveStack


class SignalEditorPanel(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window;self.current=None;self.parent_id=None
        self.pending=False;self.offset=0;self.page_size=1000;self.changed_rows=set()
        self.applied=None;self._setting_fields=False
        from .toolbox import LocalInput,ResultView
        from .choice_buttons import ChoiceButtons
        root=QHBoxLayout(self);controls=QWidget();left=QVBoxLayout(controls)
        self.domain=QComboBox();self.domain.addItems(['Discreta · x[n]','Continua · x(t)'])
        left.addWidget(ChoiceButtons(self.domain));self.sources=ActiveStack();left.addWidget(self.sources)
        for kind in ('discrete','continuous'):
            source=LocalInput('Señal para editar',kind);source.bind_project(window);self.sources.addWidget(source)
        self.domain.currentIndexChanged.connect(self.sources.setCurrentIndex)
        self.load_button=QPushButton('Abrir en tabla');self.load_button.setObjectName('primary')
        self.load_button.clicked.connect(self.load);left.addWidget(self.load_button)
        form=QFormLayout();self.axis_form=form;form.setProperty('stackFields',True);left.addLayout(form)
        self.name=QLineEdit();self.origin=QLineEdit();self.step=QLineEdit()
        form.addRow('Nombre de salida',self.name);form.addRow('Origen del eje',self.origin);form.addRow('Paso del eje',self.step)
        self.origin.setToolTip('Primer índice entero en discreto; primer instante en continuo.')
        self.step.setToolTip('Discreta: 1 índice por fila. Continua: separación positiva en segundos entre filas.')
        for field in (self.name,self.origin,self.step):field.textChanged.connect(self._fields_changed)
        self.commit_button=QPushButton('Aplicar edición');self.commit_button.clicked.connect(self._commit_clicked);left.addWidget(self.commit_button)
        note=QLabel('Editá Real e Imaginaria y aplicá la edición. En Resultado podés ver, exportar o enviar la señal. La entrada original se conserva.');note.setWordWrap(True);left.addWidget(note);left.addStretch()
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);root.addWidget(scroll,1)
        right=QWidget();layout=QVBoxLayout(right);root.addWidget(right,2)
        self.status=QLabel('Abrí una señal para ver sus muestras.');self.status.setWordWrap(True);layout.addWidget(self.status)
        self.tabs=ActiveTabs();layout.addWidget(self.tabs,1);edit=QWidget();editor=QVBoxLayout(edit);editor.setContentsMargins(0,0,0,0)
        self.table=QTableWidget(0,3);self.table.setHorizontalHeaderLabels(['Eje','Real','Imaginaria']);self.table.itemChanged.connect(self.edit_cell);self.table.setMinimumHeight(230);editor.addWidget(self.table,1)
        bar=QHBoxLayout();self.previous=QPushButton('← Anterior');self.next=QPushButton('Siguiente →');self.page_label=QLabel()
        self.previous.clicked.connect(lambda:self.change_page(-1));self.next.clicked.connect(lambda:self.change_page(1));bar.addWidget(self.previous);bar.addWidget(self.page_label,1);bar.addWidget(self.next);editor.addLayout(bar)
        self.tabs.addTab(edit,'Muestras');self.output=ResultView();self.result_tab=self.tabs.addTab(self.output,'Resultado');self.tabs.setTabVisible(self.result_tab,False)
        self.update_buttons()

    @property
    def source(self):return self.sources.currentWidget()

    def update_buttons(self):
        active=self.current is not None
        self.name.setEnabled(active);self.origin.setEnabled(active);self.step.setEnabled(active and self.current.domain!='discrete')
        self.commit_button.setEnabled(active and (self.pending or self.applied is None))
        self.previous.setEnabled(active and self.offset>0);self.next.setEnabled(active and self.offset+self.page_size<self.current.values.size)
        if active:
            domain='discreta' if self.current.domain=='discrete' else 'continua muestreada'
            state='Edición pendiente · Resultado conserva la última versión aplicada.' if self.pending and self.applied is not None else 'Edición pendiente · aplicá para obtener el resultado.' if self.pending else 'Resultado actualizado.' if self.applied is not None else 'Editá la tabla o aplicá para obtener el resultado.'
            self.status.setText(f'{self.current.name} · {domain} · eje en {self.current.units}\n{state}')

    def _fields_changed(self,*_):
        if self.current is not None and not self._setting_fields:self.pending=True;self.update_buttons()

    def receive(self,source,key=None):
        # Load an incoming result directly into the editable table.
        try:
            if source.domain not in ('discrete','continuous'):raise ValueError('El editor requiere una señal temporal discreta o continua.')
            self._prepare_source(source)
            if self.pending:self.commit()
            self.domain.setCurrentIndex(0 if source.domain=='discrete' else 1)
            self.source.set_source(source,key);self._open_source(source,key)
        except Exception as exc:QMessageBox.warning(self,'No se pudo abrir la señal',str(exc))

    def _prepare_source(self,source):
        regular_only(source,'Editar muestras');ensure_working_set(int(source.values.size),live_arrays=5)

    def load(self):
        try:
            source=self.source.read();self._prepare_source(source)
            if self.pending:self.commit()
            self._open_source(source,self.source.reference_id)
        except Exception as exc:QMessageBox.warning(self,'No se pudo abrir la señal',str(exc))

    def _open_source(self,source,key):
        self.current=source.copy_with();self.parent_id=key;self.pending=False
        self.changed_rows=set();self.offset=0;self.applied=None
        self._setting_fields=True
        try:self.name.setText(source.name);self.origin.setText(str(source.origin));self.step.setText(str(source.step))
        finally:self._setting_fields=False
        discrete=source.domain=='discrete'
        self.axis_form.labelForField(self.origin).setText('Primer índice n' if discrete else f'Primer instante t ({source.units})')
        self.axis_form.labelForField(self.step).setText('Paso entre índices' if discrete else f'Separación entre puntos ({source.units})')
        self.table.setHorizontalHeaderLabels(['Índice n' if discrete else f'Tiempo t ({source.units})','Real','Imaginaria'])
        self.tabs.setTabVisible(self.result_tab,False);self.tabs.setCurrentIndex(0);self.render()

    def render(self):
        if self.current is None:return
        start=self.offset;stop=min(start+self.page_size,self.current.values.size)
        self.table.blockSignals(True)
        try:
            self.table.setRowCount(stop-start)
            for row,index in enumerate(range(start,stop)):
                axis=int(self.current.origin)+index if self.current.domain=='discrete' else self.current.origin+index*self.current.step
                values=[str(axis),format(self.current.values[index].real,'.17g'),format(self.current.values[index].imag,'.17g')]
                for column,value in enumerate(values):
                    item=QTableWidgetItem(value)
                    if column==0:item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(row,column,item)
        finally:self.table.blockSignals(False)
        self.table.resizeColumnsToContents();self.page_label.setText(f'{start+1:,}–{stop:,} de {self.current.values.size:,}');self.update_buttons()

    def edit_cell(self,item):
        if self.current is None or item.column()==0:return
        index=self.offset+item.row()
        try:
            value=complex(real_field(self.table.item(item.row(),1)),real_field(self.table.item(item.row(),2)))
            if not np.isfinite(value):raise ValueError('La muestra debe ser un número complejo finito.')
            if value!=self.current.values[index]:self.current.values[index]=value;self.pending=True;self.changed_rows.add(index)
            self.update_buttons()
        except Exception as exc:QMessageBox.warning(self,'Muestra inválida',str(exc));self.render()

    def change_page(self,direction):
        if self.current is None:return
        target=self.offset+direction*self.page_size
        if 0<=target<self.current.values.size:self.offset=target;self.render()

    def _commit_clicked(self):
        try:self.commit(show=True)
        except Exception as exc:QMessageBox.warning(self,'No se pudo aplicar la edición',str(exc))

    def apply_axis(self):return self.commit()

    def commit(self,*,show=False):
        if self.current is None:return None
        if not self.pending and self.applied is not None:
            if show:self.tabs.setCurrentIndex(self.result_tab)
            return self.applied
        origin=integer_field(self.origin) if self.current.domain=='discrete' else real_field(self.origin)
        step=1 if self.current.domain=='discrete' else real_field(self.step)
        if step<=0:raise ValueError('El paso del eje debe ser positivo.')
        ensure_working_set(int(self.current.values.size),live_arrays=5)
        result=self.current.copy_with(origin=origin,step=step,name=self.name.text().strip() or self.current.name)
        if self.changed_rows or origin!=self.current.origin or step!=self.current.step:
            # A manually edited record no longer exactly represents its source formula.
            if result.expression:result.metadata['source_expression']=result.expression
            result.expression=''
        result.metadata={**result.metadata,'operation':'edit_samples_and_axis','edited_offsets':sorted(self.changed_rows)}
        key=self.window.publish(result,operation='Edición de muestras y eje',parents=[self.parent_id] if self.parent_id else [])
        self.parent_id=key;self.current=result.copy_with();self.applied=result;self.pending=False;self.changed_rows=set()
        self.render();self.output.show_result(result);self.tabs.setTabVisible(self.result_tab,True)
        if show:self.tabs.setCurrentIndex(self.result_tab)
        return result
