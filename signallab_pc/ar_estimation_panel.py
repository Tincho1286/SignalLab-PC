"""AR fit, order comparison, validation and residuals in one existing workflow."""
import csv,json,math
from copy import deepcopy
from PySide6.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QFormLayout,QLineEdit,QComboBox,QCheckBox,QLabel,QScrollArea,QPushButton,QTableView,QHeaderView,QMessageBox,QFileDialog
from . import ar_estimation as calc
from .numeric_input import integer_field,real_field
from .result_state import ResultState
from .system_result_actions import SystemResultActions
from .spectral_measurements_panel import Rows
from .atomic_file import atomic_text_file
from .auxiliary import optional


def details(source,row,options):
    system=calc.system(source,row);text=calc.report(row);outputs=[];diagnostic=None
    if options['diagnostic'] is not None:diagnostic,notice=optional('Diagnóstico residual',lambda:calc.diagnostics(source,row,options['diagnostic']))
    else:notice=options['diagnostic_notice']
    if diagnostic is not None:outputs.extend(diagnostic['signals']);text+='\n\n'+diagnostic['report']
    elif notice:text+='\n\n'+notice
    forecast=None
    if options['forecast'] is not None and options['forecast'][0]>0:forecast,notice=optional('Pronóstico',lambda:calc.forecast(source,row,*options['forecast']))
    else:notice=options['forecast_notice']
    if forecast is not None:outputs.extend(forecast['signals']);text+='\n\n'+forecast['report']
    elif notice:text+='\n\n'+notice
    def theory():
        if not row['stationary']:raise ValueError('El ajuste causal no es estacionario.')
        if row['near_exact']:raise ValueError('El residuo no permite estimar una varianza estadística fiable.')
        variance=row['innovation_variance']['value']
        if variance is None or variance<=0:raise ValueError('La varianza de innovación no se puede representar como una densidad float64 positiva.')
        from .random_models import analyze
        return analyze([1],row['a'],row['intercept'],math.sqrt(variance),max_lag=min(options['diagnostic'] or 0,row['nfit']-1),points=options['points'] or 3)
    model,notice=optional('Estadísticas estacionarias del modelo',theory) if options['points'] is not None or options['generation'] is not None else (None,options['points_notice'])
    if model is not None:
        if options['points'] is not None:outputs.extend(model.signals)
        text+='\n\nModelo estacionario condicionado al ajuste: media '+format(model.mean,'.12g')+', varianza '+format(model.variance,'.12g')+'. La PSD describe fluctuaciones y excluye la línea de media. No demuestra estacionariedad del registro.'
        if options['generation'] is not None:
            from .random_models import realization as generate_realization
            model.system.sample_period_s=system.sample_period_s
            realization,realization_notice=optional('Realización estacionaria',lambda:generate_realization(model,*options['generation']))
            if realization is not None:outputs.append(realization)
            elif realization_notice:text+='\n\n'+realization_notice
    elif notice:text+='\n\n'+notice
    if model is not None and options['points_notice']:text+='\n\n'+options['points_notice']
    if options['generation_notice']:text+='\n\n'+options['generation_notice']
    text+='\n\nH(z)=1/A(z⁻¹) representa el paso de innovaciones a x. La constante c se informa por separado; no forma parte de esa transferencia. Todas las opciones complementarias conservan el ajuste si no pueden calcularse.'
    return dict(fit=row,system=system,signals=outputs,diagnostic_rows=diagnostic['rows'] if diagnostic is not None else [],report=text)


class ARFitPanel(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window;self.calculation_title='Estimar modelo AR';self.result=None;self.comparison=None;self.curves=[];self.keys=[];self._accepted=None;self._selection=0
        from .toolbox import LocalInput,ResultView
        root=QHBoxLayout(self);controls=QWidget();left=QVBoxLayout(controls);self.source=LocalInput('Registro real x[n]','discrete');self.source.bind_project(window);left.addWidget(self.source)
        form=QFormLayout();form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows);left.addLayout(form)
        self.mode=QComboBox();self.mode.addItems(['Un orden elegido','Comparar órdenes']);form.addRow('Cálculo',self.mode)
        self.method=QComboBox();self.method.addItems(['Yule–Walker','Mínimos cuadrados condicionales']);form.addRow('Método',self.method)
        self.order=QLineEdit('2');form.addRow('Orden AR p (0: sólo media y ruido)',self.order)
        self.minimum=QLineEdit('0');self.maximum=QLineEdit('12');form.addRow('Desde el orden',self.minimum);form.addRow('Hasta el orden',self.maximum)
        self.criterion=QComboBox()
        for title,key in [('BIC: penaliza más los parámetros','bic'),('AIC: ajuste y cantidad de parámetros','aic'),('AICc: corrección para muestras cortas','aicc'),('Error en el tramo reservado','validation')]:self.criterion.addItem(title,key)
        form.addRow('Elegir inicialmente por',self.criterion)
        self.reserve=QLineEdit('0');form.addRow('Muestras finales reservadas (0: sin reserva)',self.reserve)
        self.lag=QLineEdit('20');self.horizon=QLineEdit('16');self.coverage=QLineEdit('95');self.points=QLineEdit('1025')
        form.addRow('Retardos del diagnóstico residual',self.lag);form.addRow('Muestras futuras (0: sin pronóstico)',self.horizon);form.addRow('Cobertura predictiva (%)',self.coverage);form.addRow('Puntos de la PSD del modelo',self.points)
        self.generate=QCheckBox('Generar una realización estacionaria');form.addRow(self.generate);self.count=QLineEdit('1024');self.seed=QLineEdit('12345');self.origin=QLineEdit('0')
        for label,field in [('Muestras de la realización',self.count),('Índice inicial de la realización',self.origin),('Semilla reproducible',self.seed)]:form.addRow(label,field)
        def generation_fields(*_):
            for field in (self.count,self.seed,self.origin):form.setRowVisible(field,self.generate.isChecked());field.setProperty('calculationInput',self.generate.isChecked())
        self.generate.toggled.connect(generation_fields);generation_fields()
        self.note=QLabel('La comparación usa mínimos cuadrados, constante y el mismo intervalo para todos los órdenes. La reserva no se utiliza para ajustar. Predecir un paso usa datos observados; pronosticar varios pasos reutiliza predicciones.');self.note.setWordWrap(True);left.addWidget(self.note)
        self.calculate_button=QPushButton('Estimar modelo AR');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);left.addWidget(self.calculate_button);left.addStretch()
        def configure(*_):
            comparing=self.mode.currentIndex()==1
            for field in (self.method,self.order):form.setRowVisible(field,not comparing);field.setProperty('calculationInput',not comparing)
            for field in (self.minimum,self.maximum,self.criterion):form.setRowVisible(field,comparing);field.setProperty('calculationInput',comparing)
        self.mode.currentIndexChanged.connect(configure);configure()
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);root.addWidget(scroll,1)
        output=QWidget();right=QVBoxLayout(output);right.setContentsMargins(0,0,0,0);root.addWidget(output,2)
        self.state=ResultState([self.mode,self.method,self.order,self.minimum,self.maximum,self.criterion,self.reserve,self.lag,self.horizon,self.coverage,self.points,self.generate,self.count,self.seed,self.origin],self.calculate_button,[self.source]);right.addWidget(self.state)
        self.view=ResultView();right.addWidget(self.view,1);self.report=self.view.text;self.tabs=self.view.views
        self.order_rows=Rows([('order','p'),('aic','AIC'),('aicc','AICc'),('bic','BIC'),('train_mse','MSE ajuste'),('validation_mse_text','MSE reserva'),('radius','Máx. |polo|'),('nfit','Filas comunes'),('error','Motivo / estado')]);self.diagnostic_rows=Rows([('lag','Retardo k'),('correlation','Correlación'),('Q','Ljung–Box Q'),('dof','Grados de libertad'),('p_value','Valor p')])
        for title,model,kind in [('Órdenes',self.order_rows,'orders'),('Residuos',self.diagnostic_rows,'diagnostics')]:
            page=QWidget();layout=QVBoxLayout(page);table=QTableView();table.setModel(model);table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows);table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents);layout.addWidget(table,1)
            if kind=='orders':
                self.order_table=table;table.clicked.connect(lambda index:self.choose_order(index.row()));note=QLabel('Elegí una fila para consultar ese ajuste. Las filas fallidas conservan su motivo y no ofrecen un modelo anterior.');note.setWordWrap(True);layout.addWidget(note)
            else:
                note=QLabel('Sólo residuos de entrenamiento. Un valor p grande no demuestra blancura ni independencia. Con k≤p, el valor p no está definido.');note.setWordWrap(True);layout.addWidget(note)
            export=QPushButton('Exportar tabla (CSV)…');export.clicked.connect(lambda checked=False,k=kind:self.export(k));layout.addWidget(export);self.tabs.addTab(page,title)
        page=QWidget();layout=QVBoxLayout(page);self.selector=QComboBox();layout.addWidget(self.selector);self.output=ResultView();layout.addWidget(self.output,1);self.tabs.addTab(page,'Curvas');self.selector.currentIndexChanged.connect(self.show_curve)
        self.actions=SystemResultActions(window);self.actions.reuse.setText('Usar modelo en…');self.actions.cas_button.setText('Modelo a CAS');self.actions.export_button.setText('Exportar modelo…');right.addWidget(self.actions)

    def options(self):
        lag,lag_notice=optional('Retardos del diagnóstico',lambda:integer_field(self.lag,minimum=0))
        def forecast_options():
            horizon=integer_field(self.horizon,minimum=0)
            return horizon,real_field(self.coverage,minimum=0,maximum=100) if horizon else 95
        forecast,forecast_notice=optional('Datos del pronóstico',forecast_options)
        points,points_notice=optional('Puntos de la PSD',lambda:integer_field(self.points,minimum=3))
        generation,generation_notice=optional('Datos de la realización',lambda:(integer_field(self.count,minimum=1),integer_field(self.seed,minimum=0),integer_field(self.origin))) if self.generate.isChecked() else (None,None)
        return dict(diagnostic=lag,diagnostic_notice=lag_notice,forecast=forecast,forecast_notice=forecast_notice,points=points,points_notice=points_notice,generation=generation,generation_notice=generation_notice)

    def calculate(self):
        try:
            original=self.source.read();source=original.copy_with(metadata=deepcopy(original.metadata));parent=self.source.reference_id;reserve=integer_field(self.reserve,minimum=0);comparing=self.mode.currentIndex()==1;options=self.options();snapshot=self.state.snapshot()
            if comparing:
                minimum=integer_field(self.minimum,minimum=0);maximum=integer_field(self.maximum,minimum=0);criterion=self.criterion.currentData()
                def compute():
                    comparison=calc.compare(source,maximum,minimum,validation=reserve,criterion=criterion);index=comparison['selected'];result=details(source,comparison['rows'][index],options) if index is not None else None
                    return dict(comparison=comparison,detail=result)
            else:
                order=integer_field(self.order,minimum=0);method='yw' if self.method.currentIndex()==0 else 'ols'
                def compute():
                    row=calc.fit(source,order,method=method,validation=reserve)
                    return dict(comparison=dict(rows=[row],selected=0,criterion=None,scope='Orden elegido por el usuario. La reserva queda fuera del ajuste.'),detail=details(source,row,options))
            def accept(data):
                self.comparison=data['comparison'];self._source=source;self._options=options;self._selection+=1;self._accepted=snapshot
                source_key=parent or self.window.publish(source,operation='Registro para estimación AR');self.source_key=source_key
                summary=dict(comparison=self.comparison,scope=self.comparison['scope']);self.comparison_key=self.window.publish(summary,title='Comparación de órdenes AR' if comparing else 'Ajuste AR',operation='Estimación AR',parents=[source_key])
                rows=[]
                for row in self.comparison['rows']:
                    rows.append(dict(row,train_mse=row.get('residual_mse',{}).get('text'),validation_mse_text=(row.get('validation_mse') or {}).get('text'),error=row.get('error') or 'Residuo casi nulo' if row.get('near_exact') else row.get('error') or ('No estacionario' if row.get('stationary') is False else 'Calculado')))
                self.order_rows.set_rows(rows);self._display(data['detail']);self.state.accept(snapshot)
                selected=self.comparison['selected']
                if selected is not None:self.order_table.selectRow(selected)
            self.window._run_operation('Ajustando y evaluando modelos AR…',compute,accept)
        except Exception as exc:QMessageBox.warning(self,'Estimar modelo AR',str(exc))

    def _display(self,data):
        self.result=data;self.curves=[];self.keys=[];self.actions.set_result(None);self.diagnostic_rows.set_rows([]);self.selector.clear();self.output.clear_result()
        if data is None:
            self.view.show_result(dict(report='No hay un criterio finito para elegir automáticamente. Consultá Órdenes y seleccioná un ajuste válido; las filas fallidas explican su motivo.',comparison=self.comparison));self.report.setPlainText('No hay un criterio finito para elegir automáticamente. Consultá Órdenes y seleccioná un ajuste válido.');self.view.result_ids=[self.comparison_key];return
        parent=[self.comparison_key];system_key=self.window.publish(data['system'],operation='Modelo AR estimado',parents=parent);self.actions.set_result(data['system'],system_key)
        keys=[self.window.publish(s,operation=s.name,parents=[system_key,self.comparison_key]) for s in data['signals']]
        payload=dict(fit=data['fit'],diagnostic_rows=data['diagnostic_rows'],report=data['report'],system={'result_id':system_key},curves=[{'result_id':key} for key in keys])
        record=self.window.publish(payload,title='Ajuste AR('+str(data['fit']['order'])+')',operation='Diagnóstico y predicción AR',parents=[system_key,*keys,self.comparison_key]);self.view.show_result(payload);self.view.result_ids=[record];self.report.setPlainText(self.comparison['scope']+'\n\n'+data['report']);self.diagnostic_rows.set_rows(data['diagnostic_rows'])
        signals=data['signals'];one_step=next((s for s in signals if s.metadata.get('operation')=='ar_one_step'),None)
        if one_step is not None:
            index=next(i for i,s in enumerate(signals) if s is one_step);self.curves.append((self._source,one_step));self.keys.append([self.source_key,keys[index]]);titles=['Observado y predicción a un paso']
        else:titles=[]
        forecast=[(s,k) for s,k in zip(signals,keys) if s.metadata.get('operation') in ('ar_forecast','ar_prediction_limit')]
        if forecast:self.curves.append(tuple(s for s,k in forecast));self.keys.append([k for s,k in forecast]);titles.append('Pronóstico e intervalo predictivo')
        for value,key in zip(signals,keys):self.curves.append(value);self.keys.append([key]);titles.append(value.name)
        self.selector.blockSignals(True);self.selector.addItems(titles);self.selector.blockSignals(False);self.show_curve()

    def choose_order(self,index):
        if self.comparison is None or not 0<=index<len(self.comparison['rows']):return
        row=self.comparison['rows'][index]
        self._selection+=1;ticket=self._selection
        if row.get('error'):
            self.result=None;self.actions.set_result(None);self.output.clear_result(row['error']);self.view.show_result(dict(report=row['error'],comparison=self.comparison));self.report.setPlainText(row['error']);self.view.result_ids=[self.comparison_key];self.diagnostic_rows.set_rows([]);self.curves=[];self.keys=[];self.selector.clear();return
        source=self._source;options=deepcopy(self._options)
        def accept(data):
            if ticket==self._selection:self._display(data)
        self.window._run_operation('Consultando el ajuste AR seleccionado…',lambda:details(source,row,options),accept)

    def show_curve(self,*_):
        index=self.selector.currentIndex()
        if 0<=index<len(self.curves):
            _,notice=optional('Vista de la curva',lambda:self.output.show_result(self.curves[index]))
            if notice:self.output.clear_result(notice)
            else:self.output.result_ids=self.keys[index]

    def export(self,kind):
        model=self.order_rows if kind=='orders' else self.diagnostic_rows
        if not model.rows:return
        path,_=QFileDialog.getSaveFileName(self,'Exportar tabla AR',kind+'.csv','CSV (*.csv)')
        if not path:return
        try:
            with atomic_text_file(path,newline='') as stream:
                fit=next((r for r in self.comparison['rows'] if not r.get('error')),None)
                meta=dict(scope=self.comparison['scope'],criterion=self.comparison['criterion'],fit_interval='training only',source_origin=int(self._source.origin),sample_rate_hz=self._source.metadata.get('sample_rate_hz'))
                if fit:meta.update(training_first_index=int(self._source.origin)+fit['fit_start'],training_last_index=int(self._source.origin)+fit['train']-1,reserved_samples=fit['validation'])
                stream.write('# '+json.dumps(meta,ensure_ascii=False)+'\n')
                columns=[key for key,_ in model.columns];writer=csv.DictWriter(stream,fieldnames=columns,extrasaction='ignore');writer.writeheader();writer.writerows(model.rows)
        except Exception as exc:QMessageBox.warning(self,'Exportar tabla AR',str(exc))
