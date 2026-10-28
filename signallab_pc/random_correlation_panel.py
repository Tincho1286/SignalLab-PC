from .numeric_input import real_field,integer_field
"""Estimación explícita de autocorrelación y autocovarianza."""
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QLineEdit,QComboBox,QCheckBox,QPushButton,QLabel,QScrollArea,QMessageBox
from .tool_guide import ToolGuide
from .random_signals import autocorrelation

class RandomCorrelationPanel(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window
        from .toolbox import LocalInput,ResultView
        root=QHBoxLayout(self);controls=QWidget();layout=QVBoxLayout(controls)
        layout.addWidget(ToolGuide('Estimá la dependencia de un registro respecto de versiones desplazadas de sí mismo.',('Registro x[n]','Retardos k','R[k] o C[k]')))
        self.source=LocalInput('Registro de entrada');self.source.bind_project(window);layout.addWidget(self.source)
        form=QFormLayout();layout.addLayout(form)
        self.mean=QCheckBox('Restar la media del registro (autocovarianza)');form.addRow(self.mean)
        self.lag=QLineEdit();self.lag.setPlaceholderText('Automático: hasta 50 o N−1');form.addRow('Retardo máximo (muestras)',self.lag)
        self.divisor=QComboBox();self.divisor.addItems(['N: longitud completa','N−|k|: pares disponibles en cada retardo']);form.addRow('Divisor de la suma',self.divisor)
        self.normalized=QCheckBox('Dividir por el valor a retardo cero');form.addRow(self.normalized)
        note=QLabel('Se incluyen retardos positivos y negativos. Sin restar la media, el valor en cero estima el valor cuadrático medio; al restarla, estima la varianza con divisor N. Con N−|k| los extremos tienen menos pares y pueden ser más variables.');note.setWordWrap(True);layout.addWidget(note)
        button=QPushButton('Estimar correlación');button.setObjectName('primary');button.clicked.connect(self.calculate);layout.addWidget(button);layout.addStretch()
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);root.addWidget(scroll,1)
        self.output=ResultView();root.addWidget(self.output,2)
    def calculate(self):
        try:
            source=self.source.read();parent=self.source.reference_id
            args=(source,integer_field(self.lag) if self.lag.text().strip() else None,self.mean.isChecked(),'N' if self.divisor.currentIndex()==0 else 'overlap',self.normalized.isChecked())
            def accept(result):
                self.window.publish(result,operation=result.name,parents=[parent] if parent else []);self.output.show_result(result)
                zero=result.values[-int(result.origin)].real
                self.output.text.setPlainText(result.name+f'\n\nMuestras de entrada: {source.values.size}\nRetardos: {result.origin:g} a {result.axis[-1]:g}\nValor a retardo cero: {zero:.12g}\nDivisor: '+result.metadata['denominator']+'\n\n'+result.metadata['scope']+'\n\nLa gráfica inicial muestra parte real e imaginaria, conservando el signo de la correlación. También podés elegir módulo y fase. La normalización por el valor en cero no está definida si éste es nulo. No se infiere estacionariedad ni independencia a partir de este gráfico.')
            self.window._run_operation('Estimando correlación del registro…',lambda:autocorrelation(*args),accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá las entradas',str(exc))
