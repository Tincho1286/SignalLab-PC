"""Familias de correlación accesibles sin perder las escalas del modelo HP."""
from PySide6.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QFormLayout,QComboBox,QLabel,QPushButton,QScrollArea,QMessageBox
from . import operations,continuous
import numpy as np

class CorrelationPanel(QWidget):
    def __init__(self,window,temporal=False):
        super().__init__();self.window=window;self.temporal=temporal
        from .toolbox import LocalInput,ResultView
        root=QHBoxLayout(self);controls=QWidget();layout=QVBoxLayout(controls);form=QFormLayout();layout.addLayout(form)
        self.kind=QComboBox();self.kind.addItems(['Autocorrelación de x','Correlación cruzada: x con referencia y']);form.addRow('Entradas',self.kind)
        self.model=QComboBox();self.model.addItems(['Registro finito','Un periodo continuo' if temporal else 'Circular: un periodo']);form.addRow('Modelo',self.model)
        self.normalization=QComboBox();self.normalization.addItems(['Integral' if temporal else 'Suma','Coeficiente por energía','Promedio por periodo']);form.addRow('Escala',self.normalization)
        self.note=QLabel();self.note.setWordWrap(True);layout.addWidget(self.note)
        self.left=LocalInput('Entrada x(t)' if temporal else 'Entrada x[n]','continuous' if temporal else 'discrete');self.left.bind_project(window);layout.addWidget(self.left)
        self.right=LocalInput('Referencia y(t)' if temporal else 'Referencia y[n]','continuous' if temporal else 'discrete');self.right.bind_project(window);layout.addWidget(self.right)
        self.calculate_button=QPushButton('Calcular correlación');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);layout.insertWidget(0,self.calculate_button)
        self.kind.currentIndexChanged.connect(self.update_options);self.model.currentIndexChanged.connect(self.update_options);self.normalization.currentIndexChanged.connect(self.update_options);self.update_options()
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);root.addWidget(scroll,1)
        self.result=ResultView();root.addWidget(self.result,2)
        from .result_state import ResultState
        self.result_state=ResultState([self.kind,self.model,self.normalization],self.calculate_button,[self.left,self.right]);layout.insertWidget(1,self.result_state)
    def update_options(self):
        periodic=self.model.currentIndex()==1;self.right.setVisible(self.kind.currentIndex()==1)
        self.normalization.model().item(2).setEnabled(periodic)
        if not periodic and self.normalization.currentIndex()==2:self.normalization.setCurrentIndex(0)
        if self.temporal:
            self.note.setText('Un periodo contiene N puntos sin repetir el extremo. T = N × paso. Se interpola linealmente, incluido el cierre del periodo.' if periodic else 'Interpolación lineal dentro de cada intervalo y cero fuera. Se requiere el mismo paso temporal en ambas entradas.')
        else:self.note.setText('Ambas entradas deben tener la misma longitud de periodo. Los orígenes se respetan módulo N.' if periodic else 'Secuencias finitas, cero fuera del soporte. El eje del resultado representa el retardo.')
        if self.normalization.currentIndex()==1:self.note.setText(self.note.text()+' Escala adimensional por energía; no se restan las medias.')
        elif self.normalization.currentIndex()==2:self.note.setText(self.note.text()+' El promedio divide la correlación por la longitud del período.')
    def calculate(self):
        try:
            left=self.left.read();auto=self.kind.currentIndex()==0;right=None if auto else self.right.read()
            parents=[self.left.reference_id]
            if not auto:parents.append(self.right.reference_id)
            parents=[key for key in parents if key]
            calculated_inputs=self.result_state.snapshot()
            periodic=self.model.currentIndex()==1;normalization=['sum','energy','mean'][self.normalization.currentIndex()]
            def compute():
                if not self.temporal:return operations.correlation(left,right,circular=periodic,normalization=normalization)
                if periodic:return continuous.periodic_correlation(left,right,normalization=normalization)
                return continuous.correlation(left,right,normalized=normalization=='energy')
            def accept(result):
                result.metadata['autocorrelation']=auto
                magnitudes=abs(result.values);peak=int(np.argmax(magnitudes));lag=float(result.axis[peak]) if self.temporal else int(result.axis[peak]);result.metadata['peak_magnitude_lag']=lag
                result.metadata['peak_magnitude']=float(magnitudes[peak])
                self.window.publish(result,operation='Correlación continua' if self.temporal else 'Correlación discreta',parents=parents);self.result.show_result(result)
                from .result_summary import Summary,Section,Formula,number
                labels={'sum':'Integral' if self.temporal else 'Suma','energy':'Coeficiente normalizado por energía','mean':'Promedio de un período'}
                sections=[Section('Modelo',rows=[('Entradas','Autocorrelación de x' if auto else 'Señal x y referencia y'),('Soporte','Un período; retardos equivalentes módulo el período' if periodic else 'Registro finito; cero fuera del intervalo'),('Escala',labels[normalization])])]
                rows=[('Retardo del máximo módulo',number(lag)+(' s' if self.temporal else ' muestras')),('Valor en ese retardo',number(result.values[peak]))]
                if not np.any(magnitudes):rows=[('Correlación','Nula en todos los retardos calculados')]
                if auto:
                    zero=int(np.argmin(abs(result.axis)));rows.append(('Rxx en retardo cero',number(result.values[zero])))
                sections.append(Section('Resultado',rows=rows))
                formula=Formula('R(l) = Integral(x(t)*conjugate(y(t-l)),(t,-oo,oo))','Rxy(τ) = ∫ x(t)·conj(y(t−τ)) dt') if self.temporal else Formula('R[l] = Sum(x[n]*conjugate(y[n-l]),(n,-oo,oo))','Rxy[l] = Σ x[n]·conj(y[n−l])')
                explanation='Para un retardo positivo de una señal recibida respecto de una referencia, usá la recibida como x y la referencia como y. Se informa el primer máximo del módulo; máximos repetidos, periodicidad, ecos y ruido pueden hacer ambigua esa estimación.'
                if auto:explanation='En autocorrelación se usa y=x. Rxx(0) corresponde a la energía o a la potencia por período según la escala elegida; la autocorrelación no identifica por sí sola un retardo absoluto.'
                if auto and normalization=='energy':explanation='En autocorrelación se usa y=x. La normalización por energía da Rxx(0)=1 para un registro no nulo; no identifica por sí sola un retardo absoluto.'
                scale_note='No se resta la media ni se aplica una corrección por la cantidad de pares de cada retardo.'
                if normalization=='energy':scale_note+=' Se divide por √(Ex·Ey); no es el coeficiente de Pearson con medias restadas. Un registro de energía cero no admite esta normalización.'
                elif normalization=='mean':scale_note+=' Se divide por '+('T, la duración del período.' if self.temporal else 'N, las muestras del período.')
                sections.append(Section('Convención',paragraphs=[explanation,scale_note],formulas=[formula]))
                from .temporal_formula import sections as temporal_sections
                sections.extend(temporal_sections(result))
                self.result.text.set_readable(Summary('Correlación y retardo',sections));self.result_state.accept(calculated_inputs)
            self.window._run_operation('Calculando correlación…',compute,accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá las entradas',str(exc))
