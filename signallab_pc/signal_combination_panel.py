"""Common independent inputs for sum and pointwise product."""
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QComboBox,QScrollArea,QPushButton,QMessageBox,QTabWidget,QStackedWidget,QLabel
from .choice_buttons import ChoiceButtons
from .result_state import ResultState
from .result_summary import signal_summary,Section,Formula
from .windowing import multiply_signals
from .signal_combinations import sum_signals


class SignalProductPanel(QWidget):
    def __init__(self,window,operation='product'):
        super().__init__();self.window=window;self.result=None;self.operation=operation;product=operation=='product'
        from .toolbox import LocalInput,ResultView
        root=QHBoxLayout(self);root.setContentsMargins(6,6,6,6);controls=QWidget();layout=QVBoxLayout(controls);layout.setContentsMargins(4,4,4,4)
        self.domain=QComboBox();self.domain.addItems(['Discreta','Continua']);layout.addWidget(ChoiceButtons(self.domain))
        note=QLabel('El producto conserva el intervalo de x; la ventana o segunda señal se alinea con él y vale cero fuera de sus datos.' if product else 'La suma cubre ambos registros y sus huecos. Cada entrada vale cero fuera de sus datos. En continuo se interpola linealmente.');note.setWordWrap(True);layout.addWidget(note)
        self.inputs=[];self.input_tabs=[];self.input_stack=QStackedWidget();layout.addWidget(self.input_stack)
        for domain_index,kind in enumerate(('discrete','continuous')):
            tabs=QTabWidget();self.input_tabs.append(tabs);self.input_stack.addWidget(tabs)
            x=LocalInput('Primera señal x[n]' if kind=='discrete' else 'Primera señal x(t)',kind)
            second=LocalInput(('Ventana o señal w[n]' if kind=='discrete' else 'Ventana o señal w(t)') if product else ('Segunda señal v[n]' if kind=='discrete' else 'Segunda señal v(t)'),kind)
            for index,field in enumerate((x,second)):
                field.bind_project(window);field.layout().setContentsMargins(4,6,4,4);tabs.addTab(field,'Señal x' if index==0 else 'Señal w / ventana' if product else 'Señal v')
                field.sourceChanged.connect(lambda d=domain_index,i=index:self.reveal_loaded(d,i))
            if kind=='discrete':
                for field in (x,second):field.origin.setText('-16');field.count.setText('33')
                second.expression.setText('where(abs(n)<=8,0.5*(1+cos(pi*n/8)),0)' if product else 'sin(pi*n/4)')
            else:
                for field in (x,second):field.origin.setText('-1');field.count.setText('201');field.step.setText('0.01')
                x.expression.setText('cos(10*pi*t)');second.expression.setText('where(abs(t)<=0.5,0.5*(1+cos(2*pi*t)),0)' if product else 'sin(10*pi*t)')
            self.inputs.append((x,second))
        self.calculate_button=QPushButton('Multiplicar señales' if product else 'Sumar señales');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);layout.addWidget(self.calculate_button)
        self.state=ResultState([self.domain],self.calculate_button,[field for pair in self.inputs for field in pair]);layout.insertWidget(1,self.state)
        def change(*_):
            selected=self.domain.currentIndex();self.input_stack.setCurrentIndex(selected);self.first,self.second=self.inputs[selected]
            self.state.sources=[self.first,self.second];self.state.widgets=[self.domain]
            for field in self.state.sources:self.state.widgets.extend([field.mode,field.expression,field.samples,field.origin,field.count,field.step])
            self.state.refresh()
        self.domain.currentIndexChanged.connect(change);change()
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);root.addWidget(scroll,1)
        self.output=ResultView();root.addWidget(self.output,2);self.report=self.output.text
    def reveal_loaded(self,domain_index,input_index):
        if self.domain.currentIndex()==domain_index:self.input_tabs[domain_index].setCurrentIndex(input_index)
    def show_source(self,field):
        for domain_index,pair in enumerate(self.inputs):
            if field in pair:self.domain.setCurrentIndex(domain_index);self.input_tabs[domain_index].setCurrentIndex(pair.index(field));return
    def calculate(self):
        try:
            x=self.first.read();other=self.second.read();snapshot=self.state.snapshot();parents=[field.reference_id for field in (self.first,self.second) if field.reference_id];product=self.operation=='product'
            title='Multiplicación punto a punto' if product else 'Suma de señales';compute=multiply_signals if product else sum_signals
            def accept(value):
                self.result=value;key=self.window.publish(value,operation=title,parents=parents);self.output.show_result(value);self.output.result_ids=[key]
                symbol='n' if value.domain=='discrete' else 't';left='y[n]' if symbol=='n' else 'y(t)';a='x[n]' if symbol=='n' else 'x(t)';b=('w[n]' if symbol=='n' else 'w(t)') if product else ('v[n]' if symbol=='n' else 'v(t)');relation=left+' = '+a+('*' if product else '+')+b
                summary=signal_summary(value,title);summary.sections.insert(0,Section('Producto' if product else 'Suma',paragraphs=[value.metadata['scope']],formulas=[Formula(relation,relation)]));self.report.set_readable(summary);self.state.accept(snapshot)
            self.window._run_operation('Multiplicando señales…' if product else 'Sumando señales…',lambda:compute(x,other),accept)
        except Exception as exc:QMessageBox.warning(self,'Revisá las señales',str(exc))
