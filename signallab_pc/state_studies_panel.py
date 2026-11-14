"""Result-local state diagnostics, coordinate transformation and equilibrium."""
from copy import deepcopy
import numpy as np
from PySide6.QtCore import Qt,QAbstractTableModel
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QLineEdit,QComboBox,QTableView,QHeaderView,QFileDialog,QMessageBox,QScrollArea
from .matrix_editor import MatrixEditor
from .report_view import ReportView,report_panel
from .active_stack import ActiveTabs
from .result_state import ResultState
from .result_summary import number
from .state_result_actions import StateModelResultActions
from .atomic_file import atomic_text_file
from . import state_studies as calc


class ArrayValues(QAbstractTableModel):
    def __init__(self):super().__init__();self.values=np.empty((0,0),complex)
    def set_values(self,values):self.beginResetModel();self.values=values;self.endResetModel()
    def rowCount(self,parent=None):return 0 if parent is not None and parent.isValid() else self.values.shape[0]
    def columnCount(self,parent=None):return 0 if parent is not None and parent.isValid() else self.values.shape[1]
    def headerData(self,index,orientation,role=Qt.ItemDataRole.DisplayRole):return str(index+1) if role==Qt.ItemDataRole.DisplayRole else None
    def data(self,index,role=Qt.ItemDataRole.DisplayRole):
        if index.isValid() and role in (Qt.ItemDataRole.DisplayRole,Qt.ItemDataRole.ToolTipRole):return str(self.values[index.row(),index.column()]) if role==Qt.ItemDataRole.ToolTipRole else number(self.values[index.row(),index.column()])


class StateDiagnostics(QWidget):
    def __init__(self):
        super().__init__();layout=QVBoxLayout(self);self.choice=QComboBox();self.choice.addItems(['Controlabilidad: [B, AB, …]','Observabilidad: [C; CA; …]']);layout.addWidget(self.choice);self.note=QLabel();self.note.setWordWrap(True);layout.addWidget(self.note)
        self.data=None;self.model=ArrayValues();table=QTableView();table.setModel(self.model);table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents);layout.addWidget(table,1)
        self.export=QPushButton('Exportar matriz y valores singulares…');self.export.clicked.connect(self.save);layout.addWidget(self.export);self.choice.currentIndexChanged.connect(self.show_matrix);self.set_result(None)
    def set_result(self,data):self.data=data;self.export.setEnabled(data is not None);self.show_matrix()
    def show_matrix(self,*_):
        if self.data is None:self.model.set_values(np.empty((0,0)));self.note.setText('Analizá un modelo para consultar las matrices y el criterio de rango.');return
        key=('controllability','observability')[self.choice.currentIndex()];d=self.data;self.model.set_values(d[key]);singular=', '.join(format(v,'.6g') for v in d[key+'_singular']) or 'Sin estados'
        self.note.setText('Rango numérico: '+str(d[key+'_rank'])+'. Escala de la matriz para SVD: '+number(d[key+'_scale'])+'. Valores σ/escala: '+singular+'. Umbral sobre σ/escala: '+number(d[key+'_threshold'])+'. Se cuentan los valores mayores que ese umbral. La escala y las coordenadas pueden afectar el diagnóstico; no es un rango simbólico exacto.')
    def save(self):
        if self.data is None:return
        path,_=QFileDialog.getSaveFileName(self,'Exportar matriz de análisis','matriz_estados.csv','CSV (*.csv)')
        if not path:return
        try:
            import csv,json
            key=('controllability','observability')[self.choice.currentIndex()];d=self.data
            with atomic_text_file(path,newline='') as stream:
                stream.write('# '+json.dumps(dict(matrix=key,scale=d[key+'_scale'],scaled_singular=d[key+'_singular'].tolist(),scaled_threshold=d[key+'_threshold'],rank=d[key+'_rank']))+'\n');writer=csv.writer(stream);writer.writerows([[str(z) for z in row] for row in d[key]])
        except OSError as exc:QMessageBox.warning(self,'Exportar matriz',str(exc))


class StateStudy(QWidget):
    def __init__(self,window,mode):
        super().__init__();self.setProperty('keepLocalAction',True);self.window=window;self.mode=mode;self.model=None;self.parent_id=None;self.revision=0;self.result=None
        layout=QVBoxLayout(self);self.note=QLabel('El estudio utiliza el último modelo analizado.');self.note.setWordWrap(True);layout.addWidget(self.note)
        if mode=='coordinates':
            self.field=MatrixEditor('');layout.addWidget(self.field);self.note.setText('Cambio de coordenadas x = P q. P debe ser invertible. Es otra descripción del mismo estado físico, no un nuevo estado independiente.')
            self.initial=QLineEdit();layout.addWidget(QLabel('Estado original x₀ (vacío = ceros)'));layout.addWidget(self.initial)
        else:
            self.field=QLineEdit();layout.addWidget(QLabel('Entradas constantes uₑ, una por canal'));layout.addWidget(self.field);self.note.setText('Se busca un estado que permanezca constante para uₑ. El equilibrio puede ser único, una familia o no existir; no implica estabilidad.')
        if mode=='coordinates':
            controls=QWidget();fields=QVBoxLayout(controls)
            for _ in range(2):
                item=layout.takeAt(0)
                if item.widget() is not None:fields.addWidget(item.widget())
            scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);scroll.setMinimumHeight(180);scroll.setMaximumHeight(240);layout.insertWidget(0,scroll)
        self.calculate_button=QPushButton('Transformar coordenadas' if mode=='coordinates' else 'Calcular equilibrio');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);layout.addWidget(self.calculate_button)
        self.state=ResultState([self.field]+([self.initial] if mode=='coordinates' else []),self.calculate_button);layout.addWidget(self.state);self.report=ReportView();layout.addWidget(report_panel(self.report),1)
        self.actions=StateModelResultActions(window,'coordinates');layout.addWidget(self.actions);self.actions.setVisible(mode=='coordinates')
        self.simulation=QPushButton('Cargar modelo y q₀ en simulación' if mode=='coordinates' else 'Cargar equilibrio en simulación');self.simulation.clicked.connect(self.send_equilibrium);self.simulation.setEnabled(False);layout.addWidget(self.simulation);self.set_model(None)
    def set_model(self,model,key=None):
        self.revision+=1;self.model=deepcopy(model);self.parent_id=key;self.result=None;self.actions.set_result(None);self.simulation.setEnabled(False);self.calculate_button.setEnabled(model is not None);self.state.completed=None
        if model is not None:
            if self.mode=='coordinates':
                from .state_space_panel import matrix_text
                self.field.setText(matrix_text(np.eye(model.states)))
                self.initial.clear()
            else:self.field.setText(', '.join('0' for _ in range(model.inputs)))
        self.state.refresh();self.report.setPlainText('Calculá el estudio con el último modelo analizado. Modificar el formulario principal no cambia estas matrices hasta volver a analizarlo.')
    def calculate(self):
        if self.model is None or getattr(self.window,'_workers',[]):return
        try:
            from .state_space_panel import matrix
            from .systems_panel import parse_list
            argument=matrix(self.field.text()) if self.mode=='coordinates' else parse_list(self.field.text());model=self.model;parent=self.parent_id;revision=self.revision;snapshot=self.state.snapshot()
            initial=(parse_list(self.initial.text()) if self.initial.text().strip() else np.zeros(model.states,complex)) if self.mode=='coordinates' else None
            function=calc.change_coordinates if self.mode=='coordinates' else calc.equilibrium
            def accept(result):
                from .result_journal import snapshot as stored
                summary=calc.coordinates_summary(result) if self.mode=='coordinates' else calc.equilibrium_summary(result);key=None
                if result.get('model') is not None:key=self.window.publish(result['model'],operation='Cambio de coordenadas',parents=[parent] if parent else [])
                self.window.publish({**stored({k:v for k,v in result.items() if k!='model'},self.window),'report':summary.plain_text()},title=summary.title,operation='Estudio de estados',parents=([parent] if parent else [])+([key] if key else []))
                if revision!=self.revision:return
                self.result=result;self.result_key=key;self.report.set_readable(summary);self.state.accept(snapshot)
                if self.mode=='coordinates':self.actions.set_result(result['model'],key);self.simulation.setEnabled(result['model'] is not None and result['numeric_initial'] is not None)
                else:self.simulation.setEnabled(result.get('numeric_state') is not None)
            self.window._run_operation('Calculando el estudio del modelo…',lambda:function(model,argument,initial) if self.mode=='coordinates' else function(model,argument),accept)
        except Exception as exc:QMessageBox.warning(self,'Estudio de estados',str(exc))
    def send_equilibrium(self):
        if self.result is None:return
        initial=self.result.get('numeric_initial') if self.mode=='coordinates' else self.result.get('numeric_state')
        if initial is None:return
        from .workspaces import ROUTES
        from .systems_panel import list_text
        model,key=(self.result['model'],self.result_key) if self.mode=='coordinates' else (self.model,self.parent_id)
        if model is None:return
        route=ROUTES['state_space','simulation'];self.window.send_model(model,key,route);panel=self.window.pages[route].panel;panel.initial.setText(list_text(initial))
        if self.mode=='equilibrium':
            for index,value in enumerate(self.result['inputs']):
                source=panel.inputs.field(index);source.mode.setCurrentIndex(0);source.expression.setText(list_text([value]))
