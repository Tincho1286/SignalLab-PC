"""Consistent independent inputs for continuous and discrete transformations."""
from PySide6.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QFormLayout,QLineEdit,QLabel,QPushButton,QScrollArea,QMessageBox,QTabWidget
from .numeric_input import constant_value,real_field,integer_field
from .result_state import ResultState
from .result_summary import signal_summary,Section,Formula,number
from .signal_transformations import transform_signal

TITLES={'shift':'Desplazar señal','reverse':'Invertir señal','scale':'Escalar amplitud','parity':'Obtener partes par e impar','affine':'Transformación afín'}

class SignalTransformPanel(QWidget):
    def __init__(self,window,domain,operation):
        super().__init__();self.window=window;self.domain_name=domain;self.operation=operation;self.result=None;self.input_result=None;self.input_key=None;self._original_shown=None
        from .toolbox import LocalInput,ResultView
        root=QHBoxLayout(self);root.setContentsMargins(6,6,6,6);controls=QWidget();layout=QVBoxLayout(controls);layout.setContentsMargins(4,4,4,4)
        self.source=LocalInput('Señal x[n]' if domain=='discrete' else 'Señal x(t)',domain);self.source.bind_project(window);layout.addWidget(self.source)
        form=QFormLayout();form.setProperty('stackFields',True);layout.addLayout(form);self.amplitude=QLineEdit('1');self.scale=QLineEdit('1');self.delay=QLineEdit('0');fields=[]
        if operation in ('scale','affine'):form.addRow('Factor de amplitud A',self.amplitude);fields.append(self.amplitude)
        if operation=='affine':form.addRow('Escala temporal a',self.scale);fields.append(self.scale)
        if operation in ('shift','affine'):form.addRow('Desplazamiento m (muestras enteras)' if domain=='discrete' else 'Desplazamiento t₀ (s)',self.delay);fields.append(self.delay)
        self.explanation=QLabel();self.explanation.setWordWrap(True);layout.addWidget(self.explanation)
        for field in fields:field.textChanged.connect(self.explain)
        self.explain()
        self.calculate_button=QPushButton(TITLES[operation]);self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);layout.addWidget(self.calculate_button)
        self.result_state=ResultState(fields,self.calculate_button,[self.source]);layout.insertWidget(0,self.result_state)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);root.addWidget(scroll,1)
        self.tabs=QTabWidget();self.output=ResultView();self.original=ResultView();self.tabs.addTab(self.output,'Partes par e impar' if operation=='parity' else 'Señal transformada');self.tabs.addTab(self.original,'Señal original');root.addWidget(self.tabs,2)
        self.tabs.currentChanged.connect(self.show_original)
    def parameters(self):
        amplitude=constant_value(self.amplitude.text()) if self.operation in ('scale','affine') else 1
        scale=real_field(self.scale) if self.operation=='affine' else 1
        if scale==0:raise ValueError('La escala temporal a debe ser distinta de cero.')
        delay=(integer_field(self.delay) if self.domain_name=='discrete' else real_field(self.delay)) if self.operation in ('shift','affine') else 0
        return amplitude,scale,delay
    def explain(self,*_):
        try:
            amplitude,scale,delay=self.parameters();unit='muestras' if self.domain_name=='discrete' else 's'
            if self.operation=='shift':text='Sin desplazamiento.' if delay==0 else 'Desplaza '+number(abs(delay))+' '+unit+' hacia la '+('derecha.' if delay>0 else 'izquierda.')
            elif self.operation=='reverse':text='Refleja el registro alrededor de '+('n=0.' if self.domain_name=='discrete' else 't=0.')+' Los valores conservan su amplitud.'
            elif self.operation=='scale':text='Multiplica los valores por A y conserva su eje. A puede ser real o complejo.'
            elif self.operation=='parity':text='x = x_par + x_impar. Se refleja alrededor de cero, sin conjugación, y se considera cero fuera del registro.'
            else:text='y(t)=A·x(a·(t−t₀)). '+('Invierte y ' if scale<0 else '')+('comprime' if abs(scale)>1 else 'expande' if abs(scale)<1 else 'conserva')+' el tiempo; después aplica el desplazamiento t₀.'
            self.explanation.setText(text)
        except ValueError as exc:self.explanation.setText(str(exc))
    def show_original(self,*_):
        if self.tabs.currentIndex()==1 and self.input_result is not None and self._original_shown is not self.input_result:
            self.original.show_result(self.input_result);self.original.result_ids=[self.input_key];self._original_shown=self.input_result
    def calculate(self):
        try:
            source=self.source.read();parent=self.source.reference_id;amplitude,scale,delay=self.parameters();snapshot=self.result_state.snapshot();operation=self.operation;discrete=self.domain_name=='discrete';explanation=self.explanation.text()
            def accept(result):
                self.result=result;self.input_result=source;self.input_key=parent;self._original_shown=None
                values=result if isinstance(result,tuple) else (result,)
                keys=[self.window.publish(value,operation=TITLES[operation],parents=[parent] if parent else []) for value in values]
                self.output.show_result(result);self.output.result_ids=keys
                if operation=='parity':relations=['x_e[n] = (x[n]+x[-n])/2','x_o[n] = (x[n]-x[-n])/2'] if discrete else ['x_e(t) = (x(t)+x(-t))/2','x_o(t) = (x(t)-x(-t))/2']
                elif operation=='shift':relations=['y[n] = x[n-('+str(delay)+')]'] if discrete else ['y(t) = x(t-('+str(delay)+'))']
                elif operation=='reverse':relations=['y[n] = x[-n]'] if discrete else ['y(t) = x(-t)']
                elif operation=='scale':relations=['y[n] = ('+number(amplitude)+')*x[n]'] if discrete else ['y(t) = ('+number(amplitude)+')*x(t)']
                else:relations=['y(t) = ('+number(amplitude)+')*x(('+number(scale)+')*(t-('+number(delay)+')))']
                summary=signal_summary(result,TITLES[operation]);summary.sections.insert(0,Section('Transformación aplicada',formulas=[Formula(value,value) for value in relations]))
                summary.sections.append(Section('Interpretación',paragraphs=[explanation,values[0].metadata.get('scope','Los intervalos no almacenados se consideran cero. La salida conserva sus índices o instantes.')]))
                self.output.text.set_readable(summary);self.tabs.setCurrentIndex(0);self.result_state.accept(snapshot)
            self.window._run_operation('Transformando señal…',lambda:transform_signal(source,operation,amplitude=amplitude,time_scale=scale,delay=delay),accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá la transformación',str(exc))
