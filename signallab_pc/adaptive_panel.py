"""Configure, compare and reuse adaptive FIR results in the Workbench."""

from PySide6.QtWidgets import (QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QScrollArea, QTabWidget, QVBoxLayout, QWidget)

from .adaptive_filter import METHODS, adaptive_fir, compare_adaptive, store_adaptive, store_adaptive_comparison
from .estimation_panel import _value, _vector_text
from .numeric_input import integer_field, real_field
from .report_view import ReportView, report_panel
from .result_state import ResultState
from .result_summary import Section, Summary, number
from .scalar_expression import real_value
from .system_result_actions import SystemResultActions
from .validation import show_input_error


class AdaptivePanel(QWidget):
    def __init__(self, window):
        super().__init__()
        from .toolbox import LocalInput, ResultView
        self.window = window
        self.variants = []
        root = QHBoxLayout(self)
        controls = QWidget()
        self.form = QFormLayout(controls)
        self.form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.purpose, self.mode, self.method = QComboBox(), QComboBox(), QComboBox()
        for title, key in (('Identificar un sistema','identification'), ('Cancelar ruido con una referencia','cancellation'),
                           ('Predecir desde muestras anteriores','prediction')):
            self.purpose.addItem(title,key)
        for title, key in (('Un algoritmo','one'), ('Comparar LMS, NLMS y RLS','methods'),
                           ('Comparar valores de un parámetro','sweep')):
            self.mode.addItem(title,key)
        for method in METHODS:
            self.method.addItem(method.upper(),method)
        self.form.addRow('Objetivo',self.purpose)
        self.form.addRow('Estudio',self.mode)
        self.form.addRow('Algoritmo',self.method)
        self.drive = LocalInput('Entrada del FIR', 'discrete')
        self.target = LocalInput('Señal deseada', 'discrete')
        for source in (self.drive,self.target):
            source.bind_project(window)
            self.form.addRow(source)
        self.length = self._field('Cantidad de coeficientes', '4')
        self.delay = self._field('Retardo de entrada (muestras)', 'Automático')
        self.reserve = self._field('Muestras reservadas al final', '0')
        self.step = self._field('Paso de adaptación μ', 'Automático')
        self.floor = self._field('Piso de energía de la entrada', 'Automático')
        self.forgetting = self._field('Factor de olvido λ', '0,99')
        self.ridge = self._field('Regularización inicial', '1')
        self.sweep = self._field('Valores a comparar', 'Separados por comas')
        self.note = QLabel()
        self.note.setWordWrap(True)
        self.form.addRow(self.note)
        self.button = QPushButton('Calcular')
        self.button.setObjectName('primary')
        self.button.clicked.connect(self.calculate)
        self.form.addRow(self.button)
        self.state = ResultState([self.purpose,self.mode,self.method,self.length,self.delay,self.reserve,
                                  self.step,self.floor,self.forgetting,self.ridge,self.sweep],
                                 self.button,[self.drive,self.target])
        self.form.insertRow(0,self.state)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(controls)
        root.addWidget(scroll,1)
        results = QWidget()
        layout = QVBoxLayout(results)
        self.choice = QComboBox()
        self.choice.setAccessibleName('Configuración adaptativa del resultado')
        self.choice.setProperty('sessionTransient',True)
        layout.addWidget(self.choice)
        self.choice.hide()
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs,1)
        self.report = ReportView()
        self.tabs.addTab(report_panel(self.report),'Informe')
        self.output = ResultView()
        self.tabs.addTab(self.output,'Señales')
        self.tabs.setTabVisible(1,False)
        self.actions = SystemResultActions(window)
        layout.addWidget(self.actions)
        root.addWidget(results,2)
        for selector in (self.purpose,self.mode,self.method):
            selector.currentIndexChanged.connect(self.configure)
        self.choice.currentIndexChanged.connect(self.show_variant)
        self.configure()

    def _field(self,label,placeholder):
        widget = QLineEdit()
        widget.setPlaceholderText(placeholder)
        self.form.addRow(label,widget)
        return widget

    def configure(self):
        purpose, mode, method = (field.currentData() for field in (self.purpose,self.mode,self.method))
        self.drive.setTitle('Referencia de ruido' if purpose=='cancellation' else 'Registro observado' if purpose=='prediction' else 'Entrada del sistema')
        self.target.setTitle('Señal contaminada' if purpose=='cancellation' else 'Salida observada del sistema')
        for field, visible in ((self.target,purpose!='prediction'), (self.method,mode!='methods'),
                               (self.sweep,mode=='sweep'), (self.step,mode=='one' and method!='rls'),
                               (self.floor,mode!='methods' and method=='nlms'), (self.ridge,mode!='methods' and method=='rls'),
                               (self.forgetting,mode=='one' and method=='rls')):
            self.form.setRowVisible(field,visible)
            field.setProperty('calculationInput',visible)
        self.sweep.setPlaceholderText('Factores de olvido separados por comas' if method=='rls' else 'Pasos separados por comas')
        self.note.setText({
            'identification':'Usá una entrada conocida y la salida observada del sistema. El error de cada instante se calcula antes de actualizar los coeficientes.',
            'prediction':'El FIR recibe solo muestras anteriores del registro. Un retardo positivo indica cuántos pasos se predicen.',
            'cancellation':'La referencia debe estar correlacionada con el ruido de la señal contaminada. El residuo es la estimación de la señal limpia.',
        }[purpose])
        self.state.refresh()

    def _settings(self):
        mode, method = self.mode.currentData(), self.method.currentData()
        if mode == 'methods':
            return mode, [{'method':name} for name in METHODS]
        params = {'method':method}
        for name in ('step','floor','forgetting','ridge'):
            field = getattr(self,name)
            if field.property('calculationInput') and field.text().strip():
                params[name] = real_field(field,minimum=0,strict=True)
        if mode == 'one':
            return mode, params
        field = 'forgetting' if method=='rls' else 'step'
        return mode, [{**params,field:real_value(token.strip())} for token in self.sweep.text().split(',')]

    def calculate(self):
        try:
            purpose = self.purpose.currentData()
            fields = (self.drive,) if purpose=='prediction' else (self.drive,self.target)
            data = [field.read(register=False) for field in fields]
            inputs = []
            for field,value in zip(fields,data,strict=True):
                key,_,parents = field.input_registration(value)
                inputs.append((value,key,parents))
            drive, target = data[0], data[-1] if len(data)>1 else None
            settings = {'purpose':purpose,
                        'length':integer_field(self.length,minimum=1) if self.length.text().strip() else 4,
                        'delay':integer_field(self.delay,minimum=0) if self.delay.text().strip() else None,
                        'reserve':integer_field(self.reserve,minimum=0) if self.reserve.text().strip() else 0}
            mode, config = self._settings()
            snapshot = self.state.snapshot()

            def compute():
                if mode == 'one':
                    return (adaptive_fir(drive,target,**settings,**config),)
                return compare_adaptive(drive,target,config,**settings)

            self.window._run_operation('Adaptando coeficientes…',compute,
                                       lambda results:self.accept(results,inputs,mode,snapshot))
        except Exception as error:
            show_input_error(self,'Revisá las señales y el algoritmo',error)

    def accept(self,results,inputs,mode,snapshot):
        project = self.window.project
        journal = getattr(self.window,'_result_journal',None)
        tool = journal.origin if journal else None
        if journal is not None:
            journal.reported({'runs':[result.report for result in results]},outputs_registered=True)
        if mode == 'one':
            runs = [store_adaptive(project,results[0],inputs,tool=tool)]
        else:
            comparison = store_adaptive_comparison(project,results,inputs,tool=tool)
            self.window.register_publication(comparison['comparison'],project.get(comparison['comparison']))
            runs = comparison['runs']
        for key,(value,_,_) in zip(runs[0]['sources'],inputs,strict=True):
            self.window.register_publication(key,value)
        self.choice.blockSignals(True)
        self.choice.clear()
        self.variants = list(zip(results,runs,strict=True))
        for result,receipt in self.variants:
            self.window.register_publication(receipt['report'],result.report)
            for label in ('system','reference','estimate','error'):
                self.window.register_publication(receipt[label],getattr(result,label))
            method = result.report['method'].upper()
            params = result.report['settings']
            title = f"{method} · λ={number(params['forgetting'])}" if method=='RLS' else f"{method} · μ={number(params['step'])}"
            self.choice.addItem(title)
        self.choice.blockSignals(False)
        self.choice.setVisible(len(results)>1)
        self.tabs.setTabVisible(1,True)
        self.show_variant()
        self.state.accept(snapshot)

    def show_variant(self,*_):
        index = self.choice.currentIndex()
        if not 0 <= index < len(self.variants):
            return
        result,receipt = self.variants[index]
        labels = ['reference','estimate','error']
        self.output.show_result(tuple(getattr(result,label) for label in labels))
        self.output.result_ids = [receipt[label] for label in labels]
        self.actions.set_result(result.system,receipt['system'])
        details = result.report
        taps = details['coefficients']
        rows = [('Algoritmo',details['method'].upper()),
                ('Coeficientes finales',_vector_text(complex(re,im) for re,im in zip(taps['real'],taps['imag']))),
                ('Retardo inicial aplicado a los coeficientes',str(details['delay'])),
                ('MSE durante la adaptación',_value(details['training_mse']))]
        if details['validation_mse'] is not None:
            rows.append(('MSE con coeficientes congelados',_value(details['validation_mse'])))
        sections = [Section('Resultado',rows=rows,paragraphs=[details['scope']])]
        if len(self.variants)>1:
            comparison = []
            for position,(variant,_) in enumerate(self.variants):
                name = self.choice.itemText(position)
                data = variant.report
                value = 'Adaptación '+_value(data['training_mse'])
                if data['validation_mse'] is not None:
                    value += ' · Validación '+_value(data['validation_mse'])
                comparison.append((name,value))
            sections.append(Section('MSE por configuración',rows=comparison))
        self.report.set_readable(Summary('Filtrado adaptativo FIR',sections))
