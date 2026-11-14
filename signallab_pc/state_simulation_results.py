"""Present and reuse the complete trajectories of one saved state simulation."""
import numpy as np
from PySide6.QtWidgets import QComboBox
from .model import Signal
from .result_summary import Summary,Section,Formula,number
from . import state_response_studies as calc


class StateSimulationResults:
    def __init__(self,panel,controls):
        self.panel=panel;self.run=None;self.signals={};self.ids={};self.summary=None
        self.family=QComboBox();self.family.addItem('Salidas y','outputs');self.family.addItem('Estados x','states');self.family.addItem('Entradas u','inputs');self.family.setAccessibleName('Variables de la simulación')
        self.component=QComboBox();self.component.setAccessibleName('Componente de respuesta');self.component.addItem('Total');controls.addWidget(self.family);controls.addWidget(self.component)
        self.family.currentIndexChanged.connect(self.show);self.component.currentIndexChanged.connect(self.show)
        from .state_steps_panel import StateStepsPanel
        self.steps=StateStepsPanel(panel.window);self.steps_index=panel.result_tabs.addTab(self.steps,'Paso a paso');panel.result_tabs.setTabVisible(self.steps_index,False);panel.result_tabs.currentChanged.connect(self.open_tab)
        self.steps.component.currentIndexChanged.connect(self.component.setCurrentIndex)
    def open_tab(self,index):
        if index==self.steps_index and self.steps.trace is None and self.run is not None:self.steps.build()
    def accept(self,run,model_id,parents,source_keys=()):
        panel=self.panel;window=panel.window;grid=run['grid'];model=run['model'];self.run=run;self.signals={};self.ids={};panel.last_simulation=(grid,run['components'][0]['output'],run['components'][0]['states'])
        original_ids=[source_keys[i] if i<len(source_keys) and source_keys[i] else window.publish(source,operation='Entrada cargada de estados',parents=parents) for i,source in enumerate(grid.sources)]
        transition_key=window.publish(run['transition'],operation='Propagación ZOH de estados',parents=[model_id]) if model.dt is None else model_id
        record=window.publish(dict(step_s=grid.step,count=len(grid.axis),first_coordinate=grid.origin,time_start_s=grid.time_start,initial_state=[[float(v.real),float(v.imag)] for v in run['initial']],domain=model.domain,input_hold='samplewise' if grid.discrete else 'ZOH',transition_model=transition_key,components=[c['name'] for c in run['components']]),title='Simulación de estados',operation='Simulación MIMO',parents=parents+original_ids+[transition_key])
        for index,component in enumerate(run['components']):
            for family,values,prefix in [('outputs',component['output'],'y'),('states',component['states'],'x'),('inputs',np.zeros_like(grid.values) if index==2 else grid.values,'u')]:
                signals=[];ids=[]
                for channel in range(values.shape[1]):
                    name=prefix+str(channel+1)+(' · '+component['name'] if len(run['components'])>1 else '')
                    signal=Signal(values[:,channel],grid.origin,1 if grid.discrete else grid.step,'n' if grid.discrete else 's',name,'discrete' if grid.discrete else 'continuous','',dict(operation='state_simulation_'+family,component=component['name'],sample_rate_hz=1/grid.step,time_start_s=grid.time_start,input_hold='samplewise' if grid.discrete else 'ZOH'))
                    if family=='inputs' and not grid.discrete:signal.metadata.update(operation='response_input',input_interpolation='hold')
                    ids.append(window.publish(signal,operation='Simulación: '+component['name']+' · '+family,parents=[record]));signals.append(signal)
                self.signals[index,family]=signals;self.ids[index,family]=ids
        self.component.blockSignals(True);self.component.clear();self.component.addItems([c['name'] for c in run['components']]);self.component.blockSignals(False);self.component.setVisible(len(run['components'])>1)
        equation='x[n+1] = A*x[n]+B*u[n]' if grid.discrete else 'dx/dt = A*x(t)+B*u(t)';output='y[n] = C*x[n]+D*u[n]' if grid.discrete else 'y(t) = C*x(t)+D*u(t)'
        sections=[Section('Registro calculado',rows=[('Puntos',str(len(grid.axis))),('Entradas / salidas / estados',f'{model.inputs} / {model.outputs} / {model.states}'),('Primera coordenada',str(grid.origin)),('Última coordenada',str(grid.axis[-1])),('Período / paso (s)',number(grid.step))]),Section('Modelo y estado inicial',formulas=[Formula(equation,equation),Formula(output,output)],rows=[('Estado al inicio','['+', '.join(number(v) for v in run['initial'])+']')],paragraphs=['La condición inicial se aplica al primer índice o instante cargado. No se presupone una historia anterior. En continuo la entrada se retiene entre puntos y la propagación utiliza Ad, Bd de ZOH, no Euler.']),Section('Vistas y reutilización',paragraphs=['La figura permite elegir entradas, estados o salidas y su componente de respuesta. Cada señal queda registrada y se puede reutilizar o enviar al CAS. Las entradas continuas utilizadas se representan como escalones; la definición original queda como resultado padre. Exportar canales conserva toda la vista elegida, aunque el gráfico limite la cantidad de trazas simultáneas. El inspector conserva la simulación aunque edites sus entradas.'])]
        if len(run['components'])>1:
            differences=[]
            for name,key in [('salidas','output'),('estados','states')]:
                a,b,c=[part[key] for part in run['components']]
                with np.errstate(all='ignore'):error=np.max(abs(a-b-c)) if a.size else 0.
                differences.append(('Mayor diferencia en '+name,number(error)))
            sections.append(Section('Total = estado cero + entrada cero',rows=differences,paragraphs=['Estado cero: entrada aplicada y estado inicial nulo. Entrada cero: entradas anuladas y memoria inicial conservada. Las tres trayectorias se calculan por separado con la misma realización; las diferencias pueden reflejar redondeo, no se corrigen alterando la salida total.']))
        self.summary=Summary('Simulación en espacio de estados',sections)
        references={str(key):[{'result_id':value} for value in ids] for key,ids in self.ids.items()}
        window.publish({'report':self.summary.plain_text(),'calculated_data':{'model':{'result_id':model_id},'transition':{'result_id':transition_key},'trajectories':references}},title=self.summary.title,operation='Informe de simulación de estados',parents=[record])
        journal=getattr(window,'_result_journal',None)
        if journal is not None:journal.reported(run,outputs_registered=True)
        self.steps.set_run(run);panel.result_tabs.setTabVisible(self.steps_index,True);panel.model_actions.set_result(model,model_id)
        self.family.model().item(1).setEnabled(model.states>0)
        if not model.states and self.family.currentIndex()==1:self.family.setCurrentIndex(0)
        self.show();panel.result_tabs.setCurrentIndex(1)
    def show(self,*_):
        if self.run is None:return
        panel=self.panel;grid=self.run['grid'];index=max(0,self.component.currentIndex());family=self.family.currentData();signals=self.signals[index,family];ids=self.ids[index,family]
        self.steps.component.setCurrentIndex(index)
        panel._simulation_formula_report=(self.summary,ids);panel._plot_signals=signals
        panel.set_channels(grid.axis,[v.values for v in signals],[v.name for v in signals],'Índice n' if grid.discrete else 't (s)',grid.discrete);panel.reuse_signal.setEnabled(bool(ids));panel.cas_signal.setEnabled(bool(ids));panel.show_simulation_formula()
