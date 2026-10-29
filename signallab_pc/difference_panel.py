"""Input, closed solution and sample window for a discrete recurrence."""
from PySide6.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QFormLayout,QLineEdit,QCheckBox,QPushButton,QScrollArea,QLabel,QTabWidget,QMessageBox,QMenu
from .expression_editor import ExpressionEditor
from .coefficient_editor import split_coefficients
from .numeric_input import integer_field,constant_value
from .result_state import ResultState
from .report_view import ReportView,report_panel
from .symbolic_process import run_request
from .model import Signal


class DifferencePanel(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window;self.result=None;self.result_key=None;self.transfer_key=None
        from .toolbox import ResultView
        root=QHBoxLayout(self);root.setContentsMargins(6,6,6,6);controls=QWidget();form=QFormLayout(controls);form.setProperty('stackFields',True)
        note=QLabel('a₀·y[n] + a₁·y[n−1] + … + aₚ·y[n−p] = f[n]');note.setWordWrap(True);form.addRow(note)
        self.coefficients=QLineEdit('1, -0.5');form.addRow('Coeficientes a₀, a₁, …, aₚ',self.coefficients)
        self.coefficients.setToolTip('Orden por retardos: a₀ multiplica y[n], a₁ multiplica y[n−1]. Se admiten pi, fracciones y 10^(-3). a₀ debe ser distinto de cero.')
        self.expression=ExpressionEditor('1');self.expression.symbolic=True;form.addRow('Entrada f[n]',self.expression)
        self.start=QLineEdit('0');form.addRow('Resolver desde n₀',self.start)
        self.rest=QCheckBox('Reposo antes de n₀');self.rest.setChecked(True);form.addRow(self.rest)
        self.initial=QLineEdit('0');form.addRow('Valores anteriores de y',self.initial)
        self.initial_note=QLabel();self.initial_note.setWordWrap(True);form.addRow(self.initial_note)
        self.count=QLineEdit('64');form.addRow('Muestras para gráfico y tabla',self.count)
        self.count.setToolTip('Desde n₀ hasta n₀+N−1. Este número no limita ni trunca la solución algebraica.')
        self.button=QPushButton('Resolver ecuación en diferencias');self.button.setObjectName('primary');self.button.clicked.connect(self.calculate);form.addRow(self.button)
        self.state=ResultState([self.coefficients,self.expression,self.start,self.rest,self.initial,self.count],self.button);form.insertRow(0,self.state)
        def configure(*_):
            rest=self.rest.isChecked();form.setRowVisible(self.initial,not rest);self.initial.setProperty('calculationInput',not rest)
            try:
                start=integer_field(self.start);coefficients=split_coefficients(self.coefficients.text())
                while len(coefficients)>1:
                    try:
                        if constant_value(coefficients[-1])!=0:break
                    except ValueError:break
                    coefficients.pop()
                order=len(coefficients)-1
                indices=', '.join('y['+str(start-k)+']' for k in range(1,min(order,4)+1))+(', …' if order>4 else '')
                self.initial_note.setText('Se toman '+str(max(0,order))+' valores anteriores iguales a cero.' if rest else 'Cargá '+str(max(0,order))+' valores en este orden: '+indices+'. El primero es el más cercano a n₀.')
            except ValueError:self.initial_note.setText('Indicá coeficientes y un índice inicial entero.')
        self.rest.toggled.connect(configure);self.start.textChanged.connect(configure);self.coefficients.textChanged.connect(configure);configure()
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);root.addWidget(scroll,1)
        right=QWidget();box=QVBoxLayout(right);box.setContentsMargins(0,0,0,0);root.addWidget(right,2)
        self.tabs=QTabWidget();box.addWidget(self.tabs,1);self.report=ReportView();self.tabs.addTab(report_panel(self.report),'Solución')
        self.output=ResultView();self.tabs.addTab(self.output,'Muestras de y[n]');self.tabs.setTabVisible(1,False)
        self.use_button=QPushButton('Usar expresión en…');self.use_button.setEnabled(False);box.addWidget(self.use_button)
        self.use_menu=QMenu(self.use_button);self.use_button.setMenu(self.use_menu);self.use_menu.aboutToShow.connect(self.prepare_reuse)

    def prepare_reuse(self):
        self.use_menu.clear()
        if self.result is None:return
        from .result_expressions import expression_result,expression_destinations,send_expression
        for title,key in [('Solución y[n]',self.result_key),('H(z) · condiciones iniciales nulas',self.transfer_key)]:
            if key is None:continue
            expression=expression_result(self.window.project.get(key))
            if expression:
                menu=self.use_menu.addMenu(title)
                for label,destination in expression_destinations(expression):
                    menu.addAction(label,lambda checked=False,target=destination,record=key:send_expression(self.window,record,target))

    def calculate(self):
        try:
            request={'operation':'difference_equation','expression':self.expression.text(),'coefficients':split_coefficients(self.coefficients.text()),'initial':split_coefficients(self.initial.text()) if not self.rest.isChecked() else [],'rest':self.rest.isChecked(),'start':integer_field(self.start),'count':integer_field(self.count)}
            snapshot=self.state.snapshot()
            def accept(result):
                from .difference_equations import summary
                self.result={'request':request,'result':result};self.result_key=self.window.publish(self.result,title='Solución de ecuación en diferencias',operation='Ecuación en diferencias')
                transfer={'request':{'operation':'difference_equation_transfer','domain':'digital'},'result':{'operation':'Transferencia de ecuación en diferencias','result':result['system_expression'],'output_variable':'z','evaluated':True,'scope':'Transferencia desde f[n] hacia y[n] bajo condiciones iniciales nulas; no incluye la respuesta del historial.'}}
                self.transfer_key=self.window.publish(transfer,title='H(z) de ecuación en diferencias',operation='Transferencia desde f[n]',parents=[self.result_key])
                self.report.set_readable(summary(request,result));self.use_button.setEnabled(True)
                values=result.get('numeric_samples');self.tabs.setTabVisible(1,values is not None)
                if values is not None:
                    signal=Signal([complex(*v) for v in values],result['origin'],1,'n','Solución y[n] de ecuación en diferencias','discrete',result['display_result'],{'operation':'difference_equation_samples','equation_start':result['origin'],'source_condition':result['condition'],'scope':result['scope']})
                    key=self.window.publish(signal,operation='Muestras de solución en diferencias',parents=[self.result_key]);self.output.show_result(signal);self.output.result_ids=[key]
                self.tabs.setCurrentIndex(0);self.state.accept(snapshot)
            self.window._run_operation('Resolviendo ecuación en diferencias…',lambda:run_request(request),accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá la ecuación en diferencias',str(exc))
