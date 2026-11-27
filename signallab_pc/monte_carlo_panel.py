"""Monte Carlo and bootstrap workflows for the Workbench."""

from pathlib import Path
import secrets

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QScrollArea, QTabWidget, QToolButton, QVBoxLayout, QWidget)

from .input_files import read_json
from .monte_carlo import (CampaignSpec, Scenario, campaign_spec, campaign_trajectory, export_campaign_csv,
                         load_campaign, run_campaign, store_campaign)
from .monte_carlo_bootstrap import bootstrap_record
from .numeric_input import integer_field, real_field
from .probability import Distribution, FAMILIES
from .random_panel import _PARAMETERS
from .report_view import ReportView, report_panel
from .result_state import ResultState
from .result_summary import Section, Summary, number
from .scalar_expression import integer_value, real_value
from .statistics_results import store_statistics
from .validation import invalid, show_input_error


_METRICS = {'mean':'Media','variance':'Varianza','probability':'Frecuencia del evento'}
_STATUS = {'incomplete':'Campaña interrumpida','max_replicas':'Se completaron todas las réplicas',
           'target_precision':'Se alcanzó el semiancho objetivo'}


def _interval_text(bounds):
    if bounds is None or any(value is None for value in bounds):
        return 'Indeterminado'
    return '['+', '.join(number(value) for value in bounds)+']'


class MonteCarloPanel(QWidget):
    def __init__(self,window,task):
        super().__init__()
        self.window, self.task = window, task
        self.campaign = None
        root = QHBoxLayout(self)
        controls = QWidget()
        self.form = QFormLayout(controls)
        self.form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.fields = []
        self.metric = QComboBox()
        for key,label in _METRICS.items():
            self.metric.addItem(label,key)
        self.form.addRow('Qué querés estimar',self.metric)
        self.fields.append(self.metric)
        self.low = self._line('Extremo inferior del evento')
        self.high = self._line('Extremo superior del evento')
        self.replicas = self._line('Réplicas', '128' if task=='campaign' else '1000')
        self.seed = self._line('Semilla', placeholder='Automática')
        self.confidence = self._line('Confianza (%)','95')
        sources = []
        if task=='campaign':
            self._campaign_controls()
        else:
            from .toolbox import LocalInput
            self.source = LocalInput('Registro observado','discrete')
            self.source.bind_project(window)
            self.form.addRow(self.source)
            self.block = self._line('Longitud del bloque de remuestreo','1')
            self.block.setToolTip('1 remuestrea observaciones individuales. Un bloque mayor conserva dependencia dentro de cada tramo.')
            sources.append(self.source)
        self.button = QPushButton('Simular' if task=='campaign' else 'Estimar incertidumbre')
        self.button.setObjectName('primary')
        self.button.clicked.connect(self.calculate)
        self.form.addRow(self.button)
        self.state = ResultState(self.fields,self.button,sources)
        self.form.insertRow(0,self.state)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(controls)
        root.addWidget(scroll,1)

        right = QWidget()
        layout = QVBoxLayout(right)
        root.addWidget(right,2)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs,1)
        self.report = ReportView()
        self.tabs.addTab(report_panel(self.report),'Informe')
        graph = QWidget()
        chart = QVBoxLayout(graph)
        self.figure = Figure(layout='constrained')
        self.canvas = FigureCanvasQTAgg(self.figure)
        chart.addWidget(NavigationToolbar2QT(self.canvas,graph))
        chart.addWidget(self.canvas,1)
        self.tabs.addTab(graph,'Convergencia' if task=='campaign' else 'Réplicas')
        self.tabs.setTabVisible(1,False)
        if task=='campaign':
            buttons = QHBoxLayout()
            for label, action in (('Reabrir campaña…',self.reopen),('Continuar',self.resume),('Guardar CSV…',self.export)):
                button = QPushButton(label)
                button.clicked.connect(action)
                buttons.addWidget(button)
                if action==self.export:
                    self.export_button=button
                    button.setProperty('resultExport',True)
                    button.setEnabled(False)
                if action==self.resume:
                    self.resume_button=button
                    button.setEnabled(False)
            layout.addLayout(buttons)
            self.family.currentIndexChanged.connect(self.configure_family)
            self.configure_family()
        self.metric.currentIndexChanged.connect(self.configure_metric)
        self.configure_metric()

    def _line(self,title,text='',*,placeholder='', form=None):
        field = QLineEdit(text)
        field.setPlaceholderText(placeholder)
        (self.form if form is None else form).addRow(title,field)
        self.fields.append(field)
        return field

    def _campaign_controls(self):
        self.family = QComboBox()
        for key,family in FAMILIES.items():
            self.family.addItem(family.label,key)
        self.family.setCurrentIndex(self.family.findData('normal'))
        self.form.addRow('Distribución',self.family)
        self.fields.append(self.family)
        self.parameters = {name:self._line(label,default) for name,(label,default) in _PARAMETERS.items()}
        self.samples = self._line('Muestras por réplica','128')
        self.directory = self._line('Carpeta de la campaña',placeholder='Elegí una carpeta para simular')
        folder_button = QPushButton('Elegir carpeta…')
        folder_button.clicked.connect(self.choose_directory)
        self.form.addRow(folder_button)
        advanced = QToolButton()
        advanced.setText('Barrido y opciones de ejecución')
        advanced.setCheckable(True)
        self.form.addRow(advanced)
        extra = QWidget()
        self.advanced = QFormLayout(extra)
        self.advanced.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.axis = QComboBox()
        self.advanced.addRow('Parámetro a variar',self.axis)
        self.fields.append(self.axis)
        self.axis_values = self._line('Valores del barrido',placeholder='Separados por comas',form=self.advanced)
        self.width = self._line('Semiancho objetivo',placeholder='Opcional',form=self.advanced)
        self.minimum_replicas = self._line('Réplicas mínimas','2',form=self.advanced)
        self.batch = self._line('Réplicas por bloque','16',form=self.advanced)
        self.common = QCheckBox('Usar números aleatorios comunes')
        self.fields.append(self.common)
        self.advanced.addRow(self.common)
        definition = QPushButton('Ejecutar definición JSON…')
        definition.clicked.connect(self.calculate_file)
        self.advanced.addRow(definition)
        self.form.addRow(extra)
        extra.hide()
        advanced.toggled.connect(extra.setVisible)

    def configure_family(self):
        definitions = {key:rule for key,_,rule in FAMILIES[self.family.currentData()].parameters}
        self.axis.clear()
        self.axis.addItem('Sin barrido',None)
        for key,field in self.parameters.items():
            shown = key in definitions
            self.form.setRowVisible(field,shown)
            field.setProperty('calculationInput',shown)
            if shown and definitions[key]!='vector':
                self.axis.addItem(_PARAMETERS[key][0],key)
        self.state.refresh()

    def configure_metric(self):
        event = self.metric.currentData()=='probability'
        for field in (self.low,self.high):
            self.form.setRowVisible(field,event)
            field.setProperty('calculationInput',event)
        self.state.refresh()

    def choose_directory(self):
        selected = QFileDialog.getExistingDirectory(self,'Carpeta de la campaña',self.directory.text())
        if selected:
            self.directory.setText(selected)
        return bool(selected)

    def _output_directory(self):
        if not self.directory.text().strip():
            invalid(self.directory,'elegí dónde guardar las réplicas para poder continuar la campaña.')
        return Path(self.directory.text().strip()).expanduser()

    def _recipe(self):
        family = self.family.currentData()
        rules = dict((key,rule) for key,_,rule in FAMILIES[family].parameters)
        parameters = {}
        for key,rule in rules.items():
            field = self.parameters[key]
            if rule=='vector':
                parameters[key] = [real_value(item.strip()) for item in field.text().split(',')]
            elif rule in ('integer','count','positive_count'):
                parameters[key] = integer_field(field)
            else:
                parameters[key] = real_field(field)
        axis = self.axis.currentData()
        if axis is None:
            return (Scenario(FAMILIES[family].label,Distribution(family,parameters)),)
        parser = integer_value if rules[axis] in ('integer','count','positive_count') else real_value
        values = [parser(item.strip()) for item in self.axis_values.text().split(',')]
        return tuple(Scenario(f'{_PARAMETERS[axis][0]} = {number(value)}',
                              Distribution(family,parameters|{axis:value})) for value in values)

    def _metrics(self):
        metric = self.metric.currentData()
        if not self.seed.text().strip():
            self.seed.setText(str(secrets.randbits(128)))
        return {'metric':metric,'seed':integer_field(self.seed,minimum=0),
                'replicas':integer_field(self.replicas,minimum=2),
                'confidence':real_field(self.confidence,minimum=0,strict=True)/100,
                'low':real_field(self.low) if metric=='probability' else None,
                'high':real_field(self.high) if metric=='probability' else None}

    def calculate(self):
        try:
            directory = self._output_directory() if self.task=='campaign' else None
            metrics = self._metrics()
            if self.task=='campaign':
                spec = CampaignSpec(self._recipe(),**metrics,samples=integer_field(self.samples,minimum=1),
                                    common_random_numbers=self.common.isChecked(),batch=integer_field(self.batch,minimum=1),
                                    minimum_replicas=integer_field(self.minimum_replicas,minimum=2),
                                    target_half_width=real_field(self.width) if self.width.text().strip() else None)
                snapshot = self.state.snapshot()
                self.window._run_operation('Simulando réplicas…',lambda:run_campaign(spec,directory),
                                           lambda result:self.accept_campaign(result,snapshot))
            else:
                source = self.source.read(register=False)
                key,_,parents = self.source.input_registration(source)
                block = integer_field(self.block,minimum=1)
                snapshot = self.state.snapshot()
                self.window._run_operation('Remuestreando el registro…',lambda:bootstrap_record(source,block_length=block,**metrics),
                                           lambda result:self.accept_bootstrap(result,(source,key,parents),snapshot))
        except Exception as error:
            show_input_error(self,'Revisá la configuración estadística',error)

    def calculate_file(self):
        path,_ = QFileDialog.getOpenFileName(self,'Cargar definición de Monte Carlo','','Configuración JSON (*.json)')
        if not path:
            return
        try:
            directory = self._output_directory()
            self.window._run_operation('Simulando desde la definición…',
                                       lambda:run_campaign(campaign_spec(read_json(path)),directory),self.accept_campaign)
        except Exception as error:
            show_input_error(self,'Revisá la carpeta de la campaña',error)

    def reopen(self):
        if not self.choose_directory():
            return
        directory = self._output_directory()
        self.window._run_view_operation('Verificando réplicas guardadas…',lambda:load_campaign(directory),self.show_campaign)

    def resume(self):
        current = self.campaign
        if current is not None:
            self.window._run_operation('Continuando la campaña…',lambda:run_campaign(current.spec,current.folder),
                                       self.accept_campaign)

    def export(self):
        current = self.campaign
        if current is None:
            return
        path,_ = QFileDialog.getSaveFileName(self,'Guardar réplicas CSV','replicas.csv','Datos CSV (*.csv)')
        if path:
            if not path.lower().endswith('.csv'):
                path += '.csv'
            self.window._run_view_operation('Guardando réplicas…',lambda:export_campaign_csv(current,path),
                                            lambda _:self.window.statusBar().showMessage('Réplicas exportadas.'))

    def _journal(self,payload):
        journal = getattr(self.window,'_result_journal',None)
        if journal is not None:
            journal.reported(payload,outputs_registered=True)
        return journal.origin if journal else None

    def accept_campaign(self,result,snapshot=None):
        project = self.window.project
        key = store_campaign(project,result,tool=self._journal(result.report))
        self.window.register_publication(key,project.get(key))
        self.show_campaign(result)
        if snapshot is not None:
            self.state.accept(snapshot)

    def show_campaign(self,result):
        self.campaign = result
        report = result.report
        self.resume_button.setEnabled(report['status']=='incomplete')
        self.export_button.setEnabled(bool(result.replicas))
        sections = [Section('Campaña',rows=[
            ('Estado',_STATUS[report['status']]),('Réplicas verificadas',str(len(result.replicas))),
            ('Semilla maestra',str(result.spec.seed)),('Carpeta',str(result.folder)),
        ],paragraphs=[report['scope']])]
        for row in report['summaries']:
            entries = [('Estimación',number(row['value'])),('Intervalo',_interval_text(row['interval']))]
            if row['theory']['value'] is not None:
                entries.append(('Referencia del modelo',number(row['theory']['value'])))
            if 'successes' in row:
                entries.append(('Eventos observados',f"{row['successes']} de {row['trials']} · "+row['evidence']))
            sections.append(Section(row['scenario'],rows=entries))
        for row in report['differences']:
            sections.append(Section(row['second']+' − '+row['first'],rows=[
                ('Diferencia estimada',number(row['value']) if row['value'] is not None else 'Fuera de rango'),
                ('Intervalo para la diferencia',_interval_text(row['interval'])),
            ],paragraphs=[row['pairing']]))
        self.report.set_readable(Summary('Simulación de Monte Carlo',sections))
        self.figure.clear()
        if result.replicas:
            axes = self.figure.add_subplot()
            counts, values = campaign_trajectory(result)
            for index,scenario in enumerate(result.spec.scenarios):
                axes.plot(counts,values[:,index],label=scenario.name)
            axes.set_xlabel('Réplicas acumuladas')
            axes.set_ylabel(_METRICS[result.spec.metric])
            axes.xaxis.set_major_locator(MaxNLocator(integer=True))
            self.figure.legend(loc='outside upper center',ncols=min(3,len(result.spec.scenarios)))
            axes.grid(alpha=.2)
        self.canvas.draw_idle()
        self.tabs.setTabVisible(1,bool(result.replicas))

    def accept_bootstrap(self,result,source,snapshot):
        project = self.window.project
        keys,record = store_statistics(project,result,[source],'Incertidumbre por bootstrap',tool=self._journal(result))
        self.window.register_publication(keys[0],source[0])
        self.window.register_publication(record,result)
        self.report.set_readable(Summary('Incertidumbre por bootstrap',[Section('Remuestreo',rows=[
            ('Estimación',number(result['estimate'])),('Intervalo percentil',_interval_text(result['interval'])),
            ('Error estándar bootstrap',number(result['standard_error'])),
            ('Sesgo observado en réplicas',number(result['replicate_bias'])),
            ('Longitud de bloque',str(result['block_length'])),('Semilla',str(result['seed'])),
        ],paragraphs=[result['scope']])]))
        self.figure.clear()
        axes = self.figure.add_subplot()
        axes.hist(np.asarray(result['replicate_estimates']),bins='auto')
        axes.set_xlabel(_METRICS[result['metric']])
        axes.set_ylabel('Réplicas')
        self.canvas.draw_idle()
        self.tabs.setTabVisible(1,True)
        self.state.accept(snapshot)
