"""Auto/cross correlation and covariance estimates in one independent tool."""
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QLineEdit,QComboBox,QCheckBox,QPushButton,QLabel,QScrollArea,QMessageBox
from .numeric_input import integer_field
from .random_signals import autocorrelation
from .random_cross_correlation import cross_correlation
from .result_state import ResultState


class RandomCorrelationPanel(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window
        from .toolbox import LocalInput,ResultView
        root=QHBoxLayout(self);controls=QWidget();layout=QVBoxLayout(controls)
        self.mode=QComboBox();self.mode.addItems(['Autocorrelación: un registro','Correlación cruzada: dos registros']);layout.addWidget(self.mode)
        self.source=LocalInput('Registro x[n]','discrete');self.source.bind_project(window);layout.addWidget(self.source)
        self.second=LocalInput('Registro y[n]','discrete');self.second.bind_project(window);layout.addWidget(self.second)
        form=QFormLayout();layout.addLayout(form)
        self.mean=QCheckBox('Restar la media (calcular covarianza)');form.addRow(self.mean)
        self.lag=QLineEdit();self.lag.setPlaceholderText('Automático: hasta 50 o N−1');form.addRow('Retardo máximo (muestras)',self.lag)
        self.divisor=QComboBox();self.divisor.addItems(['N: longitud observada','N−|k|: pares disponibles']);form.addRow('Divisor de la suma',self.divisor)
        self.normalized=QCheckBox();form.addRow(self.normalized)
        self.note=QLabel();self.note.setWordWrap(True);layout.addWidget(self.note)
        self.button=QPushButton('Estimar correlación');self.button.setObjectName('primary');self.button.clicked.connect(self.calculate);layout.addWidget(self.button)
        self.state=ResultState([self.mode,self.mean,self.lag,self.divisor,self.normalized],self.button,[self.source,self.second]);layout.insertWidget(0,self.state)
        def configure(*_):
            cross=self.mode.currentIndex()==1;self.second.setVisible(cross);self.second.setProperty('calculationInput',cross)
            self.normalized.setText('Dividir por √(Px·Py)' if cross else 'Dividir por el valor en retardo cero')
            self.note.setText('Rxy[k] compara x[n+k] con y[n]. Se usa sólo el intervalo observado en ambos registros; N es su longitud. La normalización usa las potencias (o varianzas, al restar las medias) de ese intervalo. Un retardo positivo corresponde a x desplazada a la derecha respecto de y.' if cross else 'Se incluyen retardos positivos y negativos. En cero se estima el valor cuadrático medio o, al restar la media, la varianza con divisor N. Los retardos grandes tienen menos pares.')
        self.mode.currentIndexChanged.connect(configure);configure();layout.addStretch()
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);root.addWidget(scroll,1)
        self.output=ResultView();root.addWidget(self.output,2)

    def calculate(self):
        try:
            cross=self.mode.currentIndex()==1;source=self.source.read();second=self.second.read() if cross else None
            lag=integer_field(self.lag) if self.lag.text().strip() else None
            if lag is not None and lag<0:raise ValueError('El retardo máximo debe ser no negativo.')
            options=(lag,self.mean.isChecked(),'N' if self.divisor.currentIndex()==0 else 'overlap',self.normalized.isChecked())
            parents=[field.reference_id for field in ([self.source,self.second] if cross else [self.source]) if field.reference_id]
            snapshot=self.state.snapshot()
            def accept(result):
                key=self.window.publish(result,operation=result.name,parents=parents);self.output.show_result(result);self.output.result_ids=[key]
                meta=result.metadata
                interval=('\nIntervalo común: '+str(meta['common_origin'])+' a '+str(meta['common_last_index'])) if cross else ''
                text=result.name+'\n\nMuestras observadas: '+str(meta['input_samples'])+interval+'\nRetardos: '+str(result.origin)+' a '+str(result.axis[-1])+'\nDivisor: '+meta['denominator']+'\n\n'+meta['scope']
                text+='\n\nConvención: Rxy[k]=Σ x[n+k]·conj(y[n]) / divisor. Para autocorrelación y=x. La covarianza resta las medias antes de multiplicar. Una estimación finita no demuestra estacionariedad ni independencia.'
                self.output.text.setPlainText(text);self.state.accept(snapshot)
            job=(lambda:cross_correlation(source,second,*options)) if cross else (lambda:autocorrelation(source,*options))
            self.window._run_operation('Estimando correlación del registro…',job,accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá las entradas',str(exc))
