"""Composición de dos sistemas LTI con resultado reutilizable."""
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QComboBox,QPushButton,QLabel,QTabWidget,QScrollArea,QMessageBox,QAbstractItemView
from .coefficient_editor import CoefficientEditor,TransferPreview
from .systems_panel import parse_list,list_text
from .filters import Transfer
from .control import interconnect
from .tool_guide import ToolGuide
from .report_view import ReportView,report_panel
from .navigation import MENUS

class InterconnectionPanel(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window;self.result=None;self.result_id=None;self.parents=[None,None];self.preserved_inputs=[None,None]
        self.definitions=[];self.importers=[]
        root=QHBoxLayout(self);controls=QWidget();layout=QVBoxLayout(controls)
        layout.addWidget(ToolGuide('Conectá dos sistemas y obtené una transferencia equivalente para analizarla en otros menús.',('H₁ y H₂','Conexión','H equivalente')))
        form=QFormLayout();form.setProperty('stackFields',True);layout.addLayout(form)
        self.domain=QComboBox();self.domain.addItems(['Continuo · H(s)','Discreto · H(z)']);form.addRow('Dominio común',self.domain)
        self.connection=QComboBox();self.connection.addItems(['Cascada: H₁ · H₂','Paralelo: H₁ + H₂','Realimentación negativa: H₁ / (1 + H₁H₂)','Realimentación positiva: H₁ / (1 − H₁H₂)']);form.addRow('Conexión',self.connection)
        self.diagram=QLabel();self.diagram.setWordWrap(True);layout.addWidget(self.diagram)
        tabs=QTabWidget();self.input_tabs=tabs;layout.addWidget(tabs);self.inputs=[];self.previews=[]
        for index in range(2):
            panel=QWidget();fields=QFormLayout(panel);fields.setProperty('stackFields',True);b=CoefficientEditor('1');a=CoefficientEditor('1, 1')
            preview=TransferPreview(b,a);fields.addRow(preview);fields.addRow('Numerador',b);fields.addRow('Denominador',a)
            choose=QPushButton('Copiar un sistema anterior…');choose.clicked.connect(lambda checked=False,i=index:self.choose(i));fields.addRow(choose)
            panel.domain=self.domain;panel.b=b;panel.a=a;panel.preview=preview
            from .transfer_input import install_formula_editor
            install_formula_editor(panel,fields);self.definitions.append(panel)
            from .system_import import install_system_import
            self.importers.append(install_system_import(choose,window,lambda value,key,i=index:self.receive(value,key,i),lambda i=index:self.choose(i),domains=lambda:[('analog','digital')[self.domain.currentIndex()]] if self.edited else None))
            self.inputs.append((b,a));self.previews.append(preview);tabs.addTab(panel,'Sistema H'+str(index+1))
            b.textChanged.connect(self.dirty);a.textChanged.connect(self.dirty)
            panel.transfer_formula.textChanged.connect(self.dirty);panel.definition_mode.currentIndexChanged.connect(self.dirty)
        note=QLabel('En realimentación, H₁ está en el camino directo y H₂ en el retorno. Los cálculos suponen condiciones iniciales nulas. No se cancelan polos y ceros por aproximación.');note.setWordWrap(True);layout.addWidget(note)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);left=QWidget();left_layout=QVBoxLayout(left);left_layout.addWidget(scroll,1)
        calculate=QPushButton('Obtener sistema equivalente');self.calculate_button=calculate;calculate.setObjectName('primary');calculate.clicked.connect(self.calculate);left_layout.addWidget(calculate);root.addWidget(left,1)
        right=QWidget();out=QVBoxLayout(right);self.status=QLabel('Definí los dos sistemas y calculá la conexión.');self.status.setWordWrap(True);out.addWidget(self.status)
        self.output_b=CoefficientEditor('1');self.output_a=CoefficientEditor('1');self.equivalent=TransferPreview(self.output_b,self.output_a);out.addWidget(self.equivalent)
        results=QTabWidget();self.report=ReportView();results.addTab(report_panel(self.report),'Informe')
        for title,editor in [('Numerador',self.output_b),('Denominador',self.output_a)]:
            editor.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            for button in editor.findChildren(QPushButton):button.hide()
            results.addTab(editor,title)
        out.addWidget(results,1);self.equivalent.hide()
        from .system_result_actions import SystemResultActions
        self.system_actions=SystemResultActions(window);self.system_actions.reuse_excluded.add(('interconnection',0));self.system_actions.reuse.setText('Usar sistema en…');self.system_actions.export_button.setText('Exportar sistema…');out.addWidget(self.system_actions)
        self.actions=[self.system_actions.analysis,self.system_actions.reuse,self.system_actions.export_button]
        root.addWidget(right,2)
        self.domain.currentIndexChanged.connect(self.change_domain);self.connection.currentIndexChanged.connect(self.change_connection);self.change_domain();self.change_connection();self.edited=False
        from .result_state import ResultState
        tracked=[self.domain,self.connection]
        for editor in self.definitions:tracked.extend([editor.b,editor.a,editor.definition_mode,editor.transfer_formula])
        self.result_state=ResultState(tracked,calculate);left_layout.insertWidget(1,self.result_state)
    def dirty(self,*_):
        self.edited=True
        if hasattr(self,'status') and self.result is not None:self.status.setText('Entradas modificadas. Calculá otra vez para obtener el sistema actualizado.')
    def change_domain(self,*_):
        digital=self.domain.currentIndex()==1
        for (b,a),preview in zip(self.inputs,self.previews):b.set_domain(digital);a.set_domain(digital);preview.schedule()
        self.dirty()
    def change_connection(self,*_):
        self.diagram.setText(['x → H₁ → H₂ → y. La salida de H₁ entra en H₂.','La misma entrada x llega a H₁ y H₂; sus salidas se suman.','e = x − H₂{y}; y = H₁{e}. Se resta la señal de retorno.','e = x + H₂{y}; y = H₁{e}. Se suma la señal de retorno.'][self.connection.currentIndex()]);self.dirty()
    def choose(self,index):
        key=self.window.choose_record('system')
        if not key:return
        self.receive(self.window.project.get(key),key,index)
    def receive(self,value,key,index):
        domain='digital' if self.domain.currentIndex()==1 else 'analog'
        if value.domain!=domain and not self.edited:
            self.domain.setCurrentIndex(1 if value.domain=='digital' else 0);domain=value.domain
        if value.domain!=domain:
            QMessageBox.warning(self,'Dominio diferente','Los sistemas de esta conexión tienen otro dominio. Cambiá el dominio común y revisá ambos bloques antes de copiar el sistema.');return False
        b,a=self.inputs[index];b.setText(list_text(value.b));a.setText(list_text(value.a));self.parents[index]=key;self.input_tabs.setCurrentIndex(index)
        from .transfer_input import remember_system
        remember_system(self.definitions[index],value)
        self.preserved_inputs[index]=(value,(b.text(),a.text(),self.domain.currentIndex()))
        self.status.setText('Sistema copiado a H'+str(index+1)+'. Completá el otro bloque y calculá la conexión.');return True
    def send(self,task):
        from .workspaces import ROUTES
        destination=ROUTES['systems',9] if task==9 else ROUTES['system_analysis',0]
        self.window.send_system(self.result,self.result_id,destination)
    def calculate(self):
        try:
            domain='digital' if self.domain.currentIndex()==1 else 'analog';index=self.connection.currentIndex()
            systems=[]
            from .transfer_input import read_system
            for i,editor in enumerate(self.definitions):systems.append(read_system(editor,name='H'+str(i+1),allow_advance=True))
            snapshot=self.result_state.snapshot()
            keys=[self.window.publish(value,operation='Definición local de '+value.name,parents=[parent] if parent else []) for value,parent in zip(systems,self.parents)]
            mode=['cascade','parallel','negative_feedback','positive_feedback'][index]
            relation=['H = H₁ · H₂','H = H₁ + H₂','H = H₁ / (1 + H₁H₂)','H = H₁ / (1 − H₁H₂)'][index]
            def accept(value):
                self.result=value;self.result_id=self.window.publish(value,operation=value.name,parents=keys)
                for editor,coefficients in [(self.output_b,value.b),(self.output_a,value.a)]:editor.set_domain(value.domain=='digital');editor.setText(list_text(coefficients))
                self.equivalent.schedule();self.equivalent.setVisible(not value.advance);self.status.setText(value.name+' · Sistema equivalente calculado')
                for button in self.actions:button.setEnabled(True)
                from .result_summary import transfer_summary,Section
                summary=transfer_summary(value)
                summary.sections.insert(0,Section('Conexión calculada',paragraphs=[relation,'Se combina la relación racional completa, incluidos retardos y avances. La transferencia equivalente no demuestra estabilidad interna ni realizabilidad causal de todos los bloques. No se cancelan raíces por proximidad.']))
                self.report.set_readable(summary);self.system_actions.set_result(value,self.result_id);self.result_state.accept(snapshot)
            self.window._run_operation('Conectando sistemas…',lambda:interconnect(*systems,mode),accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá los sistemas',str(exc))
