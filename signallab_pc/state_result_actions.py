"""Actions for the last calculated state model, shared with the result library."""
from pathlib import Path
from PySide6.QtWidgets import QWidget,QHBoxLayout,QPushButton,QMenu,QFileDialog,QMessageBox,QInputDialog
from .workspaces import ROUTES
from .state_space import StateModel


def read_model_results(path,continuous_only=False):
    from .project import Project
    project=Project();project.merge(path);models=[]
    for record in project.headers('state_space'):
        model=project.get(record['id'])
        if not continuous_only or model.dt is None:models.append((record['title'],model))
    if not models:raise ValueError('El archivo no contiene un modelo continuo.' if continuous_only else 'El archivo no contiene un modelo de estados.')
    return models


def install_model_import(button,owner,receiver,choose_model,continuous_only=False):
    menu=QMenu(button);button.setText('Cargar modelo…');button.setMenu(menu)
    menu.addAction('Usar un modelo de Resultados…',choose_model)
    def open_file():
        path,_=QFileDialog.getOpenFileName(owner,'Abrir modelo de estados','','Modelo o resultados SignalLab (*.json)')
        if not path:return
        try:
            models=read_model_results(path,continuous_only)
            if len(models)>1:
                labels=[str(index+1)+'. '+title+' · '+('Continuo' if model.dt is None else 'Discreto, T='+str(model.dt)+' s')+f' · {model.states} estados, {model.inputs} entradas, {model.outputs} salidas' for index,(title,model) in enumerate(models)]
                chosen,accepted=QInputDialog.getItem(owner,'Modelo del archivo','El archivo incluye varios modelos; elegí cuál cargar.',labels,len(labels)-1,False)
                if not accepted:return
                model=models[labels.index(chosen)][1]
            else:model=models[0][1]
            receiver(model)
            owner.statusBar().showMessage('Modelo cargado desde '+Path(path).name+'. Revisá sus datos y calculá.')
        except Exception as exc:QMessageBox.warning(owner,'No se pudo cargar el modelo',str(exc))
    menu.addAction('Abrir modelo JSON…',open_file)
    return menu


class StateModelResultActions(QWidget):
    def __init__(self,owner,source_action):
        super().__init__();self.owner=owner;self.source_action=source_action;self.model=None;self.key=None
        row=QHBoxLayout(self);row.setContentsMargins(0,0,0,0)
        self.reuse=QPushButton('Usar modelo calculado en…');self.reuse.setProperty('actionRole','reuse');self.menu=QMenu(self.reuse);self.reuse.setMenu(self.menu);self.menu.aboutToShow.connect(self.prepare_menu);row.addWidget(self.reuse)
        self.reuse.setToolTip('Copia el último modelo calculado, aunque hayas modificado los campos. El destino conserva su propio resultado hasta que calcules allí.')
        self.cas_button=QPushButton('Enviar a CAS');self.cas_button.setProperty('actionRole','cas')
        self.cas_button.clicked.connect(self.send_to_cas);row.addWidget(self.cas_button)
        self.export_button=QPushButton('Exportar modelo…');self.export_button.clicked.connect(self.export);row.addWidget(self.export_button);self.set_result(None)
    def set_result(self,model,key=None):
        self.model=model;self.key=key;self.setEnabled(model is not None)
    def send_to_cas(self):
        if self.model is not None:
            from .cas_transfer import send_to_cas
            send_to_cas(self.owner,self.key,value=self.model)

    def prepare_menu(self):
        self.menu.clear()
        if self.model is None:return
        for title,action in [('Estructura y estabilidad','analysis'),('Respuesta temporal','simulation'),('Respuesta en frecuencia','frequency'),('Obtener transferencia','transfer'),('Discretizar modelo','discretize')]:
            if action==self.source_action or (action=='discretize' and self.model.dt is not None):continue
            self.menu.addAction(title,lambda checked=False,destination=action:self.send_to(destination))
    def send_to(self,action):
        if self.model is not None:self.owner.send_model(self.model,self.key,ROUTES['state_space',action])
    def export(self):
        if self.model is None:return
        path,_=QFileDialog.getSaveFileName(self,'Exportar modelo calculado','modelo.json','Modelo SignalLab (*.json)')
        if not path:return
        if not Path(path).suffix:path+='.json'
        try:
            key=self.key or self.owner.publish(self.model,operation='Modelo calculado exportado')
            self.owner.project.export_record(key,path)
            self.owner.statusBar().showMessage('Modelo exportado: '+path)
        except Exception as exc:QMessageBox.warning(self,'No se pudo exportar el modelo',str(exc))
