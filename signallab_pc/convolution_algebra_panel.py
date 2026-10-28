from .report_view import ReportView,report_panel
from .expression_editor import ExpressionEditor
"""Convolución de expresiones con soporte y convergencia explícitos."""
from PySide6.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QFormLayout,QLineEdit,QComboBox,QPushButton,QPlainTextEdit,QLabel,QMessageBox,QScrollArea
from .symbolic_process import run_request

class ConvolutionAlgebraPanel(QWidget):
    def __init__(self,window,correlation=False):
        super().__init__();self.window=window;self.correlation=correlation;root=QHBoxLayout(self)
        controls=QWidget();form=QFormLayout(controls);form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.left=ExpressionEditor('exp(-t^2)' if correlation else 'exp(-t)',symbolic=True);self.right=ExpressionEditor('exp(-t^2)' if correlation else 'exp(-2*t)',symbolic=True)
        form.addRow('x(t)',self.left);form.addRow('y(t)' if correlation else 'h(t)',self.right)
        self.support=QComboBox();self.support.addItems(['Entradas causales: cero para t < 0','Bilateral: soporte incluido en las expresiones']);form.addRow('Soporte',self.support)
        if correlation:form.setRowVisible(self.support,False)
        self.period=QLineEdit('')
        if correlation:form.addRow('Periodo (vacío = integral bilateral)',self.period)
        note=QLabel('R(tau) = ∫ x(t) conjugada(y(t−tau)) dt. Si indicás un periodo, ambas expresiones deben ser periódicas con ese periodo; no se normaliza la integral.' if correlation else 'En modo causal, las fórmulas valen para t ≥ 0. En modo bilateral, incluí los escalones o tramos que definan el soporte.');note.setWordWrap(True);form.addRow(note)
        self.calculate_button=QPushButton('Calcular correlación algebraica' if correlation else 'Calcular convolución algebraica');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);form.addRow(self.calculate_button)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);root.addWidget(scroll,1)
        self.report=ReportView();self.report.setReadOnly(True);root.addWidget(report_panel(self.report),2)
        self.report.setPlainText('El resultado algebraico y sus condiciones quedarán guardados en el proyecto. Si el motor no resuelve la integral, se mostrará como pendiente de evaluación.')
        from .result_state import ResultState
        self.result_state=ResultState([self.left,self.right,self.support,self.period],self.calculate_button);form.insertRow(0,self.result_state)
    def calculate(self):
        request=dict(operation='continuous_correlation' if self.correlation else 'continuous_convolution',left=self.left.text(),right=self.right.text(),causal=self.support.currentIndex()==0)
        if self.correlation:request["period"]=self.period.text().strip()
        calculated_inputs=self.result_state.snapshot()
        def accept(result):
            self.window.publish({'request':request,'result':result},title='Correlación algebraica' if self.correlation else 'Convolución algebraica',operation=request['operation'])
            self.result_state.accept(calculated_inputs)
            self.report.setPlainText(('R(tau) = ' if self.correlation else 'y(t) = ')+result['result']+'\n\n'+result['scope']+'\n\n'+('Integral evaluada.' if result['evaluated'] else 'El motor dejó la integral sin evaluar.'))
        self.window._run_operation('Calculando integral algebraica…',lambda:run_request(request),accept)
