"""Compare saved objects on explicit common coordinates, without realignment."""
import numpy as np
from .model import Signal
from .filters import Transfer


def compatible(a,b):
    if isinstance(a,Signal) and isinstance(b,Signal):
        return (a.domain,a.units,a.data_kind)==(b.domain,b.units,b.data_kind)
    return isinstance(a,Transfer) and isinstance(b,Transfer) and a.domain==b.domain


def _project(value,top=(),bottom=()):
    import math
    if value==0:return 0.
    mantissa,exponent=math.frexp(value)
    for factor in top:
        part,shift=math.frexp(float(factor));mantissa*=part;exponent+=shift
    for factor in bottom:
        part,shift=math.frexp(float(factor));mantissa/=part;exponent-=shift
    try:result=math.ldexp(mantissa,exponent)
    except OverflowError:return None
    return result if np.isfinite(result) and result!=0 else None


def _divide(values,scale):
    # Divide real components separately: complex division by subnormal reals
    # can overflow its reciprocal even when the normalized values are finite.
    result=np.empty_like(values,dtype=complex)
    result.real=values.real/scale;result.imag=values.imag/scale
    return result


def errors(a,b):
    a=np.asarray(a,dtype=complex);b=np.asarray(b,dtype=complex)
    finite=np.isfinite(a)&np.isfinite(b);a=a[finite];b=b[finite]
    if not a.size:return {'count':0,'relative_max':None,'absolute_max':None,'rms':None}
    scale=float(max(np.max(abs(a.real)),np.max(abs(a.imag)),np.max(abs(b.real)),np.max(abs(b.imag))))
    if scale==0:return {'count':int(a.size),'relative_max':0.,'absolute_max':0.,'rms':0.}
    with np.errstate(over='ignore',invalid='ignore',under='ignore'):delta=b-a
    if np.isfinite(delta).all():
        delta_scale=float(max(np.max(abs(delta.real)),np.max(abs(delta.imag))))
        if delta_scale==0:return {'count':int(a.size),'relative_max':0.,'absolute_max':0.,'rms':0.}
        delta=_divide(delta,delta_scale)
    else:
        delta_scale=scale;delta=_divide(b,scale)-_divide(a,scale)
    size=abs(delta);maximum=float(size.max());rms=float(np.sqrt(np.mean(size**2)))
    reference=float(max(abs(_divide(a,scale)).max(),abs(_divide(b,scale)).max()))
    return {'count':int(a.size),'relative_max':_project(maximum,(delta_scale,),(scale,reference)),
            'absolute_max':_project(maximum,(delta_scale,)),'rms':_project(rms,(delta_scale,))}


def _physical_axis(source):
    from .system_clock import validate_clock_resolution
    from .sampling import positive_finite
    rate=source.metadata.get('sample_rate_hz');start=source.metadata.get('time_start_s')
    if rate is None or start is None:raise ValueError('Para comparar en segundos, ambas entradas deben registrar Fs y el instante de la primera muestra.')
    rate=positive_finite(rate,'Fs registrada')
    validate_clock_resolution(start,rate,source.values.size)
    return float(start)+np.arange(source.values.size,dtype=float)/rate


def compare(a,b,start=0.,stop=np.pi,count=2001,*,alignment='index'):
    if not compatible(a,b):raise ValueError('Elegí resultados de la misma clase, dominio y unidades, o dos sistemas del mismo dominio.')
    from .resources import ensure_working_set
    if isinstance(a,Signal):
        ensure_working_set(a.values.size+b.values.size,live_arrays=12)
        a,b=a.copy_with(),b.copy_with()
        clock_note=None
        if alignment not in ('index','physical') or alignment=='physical' and a.domain!='discrete':
            raise ValueError('La comparación por reloj físico requiere dos secuencias discretas.')
        if a.domain=='discrete' and alignment=='index':
            from .windowing import validate_discrete_clocks
            try:validate_discrete_clocks(a,b)
            except ValueError as exc:clock_note=str(exc)+' Las diferencias calculadas aquí corresponden sólo a los índices n.'
            low=max(a.origin,b.origin);high=min(a.origin+a.values.size-1,b.origin+b.values.size-1)
            n=max(0,int(high-low+1));coordinates=np.arange(n,dtype=np.int64)+low;one=a.values[low-a.origin:low-a.origin+n];two=b.values[low-b.origin:low-b.origin+n]
        else:
            axes=(_physical_axis(a),_physical_axis(b)) if alignment=='physical' else (a.axis,b.axis)
            coordinates,i,j=np.intersect1d(*axes,assume_unique=False,return_indices=True);one=a.values[i];two=b.values[j]
        metrics=errors(one,two)
        from .comparison_trace import capture
        from .signal_plot import is_discrete_plot
        unit='s' if alignment=='physical' else a.units
        label='Tiempo físico (s)' if alignment=='physical' else 'Índice k' if a.units in ('k','bin k') else 'Índice n' if a.domain=='discrete' else 'Coordenada ('+a.units+')'
        trace=capture(coordinates,one,two,units=unit,label=label,discrete=is_discrete_plot(a),index=a.domain=='discrete' and alignment=='index')
        from .distributions import dirac_terms
        impulses=None
        if a.domain in ('continuous','frequency'):
            left=dict(dirac_terms(a));right=dict(dirac_terms(b))
            positions=sorted(left.keys() | right.keys())
            if positions:
                from itertools import islice
                weights_a=np.array([left.get(position,0j) for position in positions])
                weights_b=np.array([right.get(position,0j) for position in positions])
                impulses={'metrics':errors(weights_a,weights_b),'terms_a':len(left),'terms_b':len(right),
                          'different_positions':sum(left.get(t,0j)!=right.get(t,0j) for t in positions),
                          'first_differences':[[t,[float(u.real),float(u.imag)],[float(v.real),float(v.imag)]]
                                               for t,u,v in islice((item for item in zip(positions,weights_a,weights_b)
                                                                    if item[1]!=item[2]),12)]}
        return {'trace':trace,'metrics':metrics,'signals':(a,b),'alignment':alignment,'clock_note':clock_note,'impulses':impulses,'scope':'Se comparan sólo coordenadas almacenadas exactamente coincidentes. Se conservan origen, amplitud y fase; no se interpola, desplaza ni rellena con ceros. Una ausencia de puntos comunes no significa igualdad.','units':a.units,'domain':a.domain}
    from .frequency_analysis import frequency_grid
    from .system_conditions import record
    w=frequency_grid(start,stop,count);one=a.response(w);two=b.response(w)
    from .comparison_trace import capture
    unit='rad/muestra' if a.domain=='digital' else 'rad/s'
    trace=capture(w,one,two,units=unit,label='Frecuencia angular ('+unit+')')
    return {'trace':trace,'metrics':errors(one,two),'omega':w,'frequency_interval':[float(start),float(stop)],'frequency_count':int(count),'responses':(one,two),'systems':(a,b),'conditions':(record(a),record(b)),'units':'rad/muestra' if a.domain=='digital' else 'rad/s','domain':'frequency','scope':'Ambas fórmulas se evalúan en las mismas frecuencias. La interpretación como respuesta de Fourier depende de la ROC de cada sistema. Las métricas excluyen puntos no finitos y no prueban máximos entre frecuencias.'}


def summary(data):
    from .result_summary import Summary,Section,Formula,number
    m=data['metrics']
    physical=data.get('alignment')=='physical'
    rows=[('Coordenadas comunes finitas',str(m['count']))]
    if data.get('domain')=='discrete':rows.insert(0,('Alineación','Instantes físicos (s)' if physical else 'Índices n'))
    for key,label in [('absolute_max','Máximo |B−A|'),('rms','RMS de B−A'),('relative_max','Máximo relativo a la mayor amplitud de A/B')]:rows.append((label,number(m[key]) if m[key] is not None else 'Fuera de rango float64' if m['count'] else 'No disponible'))
    sections=[Section('Diferencias sobre coordenadas comunes',rows=rows,formulas=[Formula('e = B-A','e = B − A')]),Section('Interpretación',paragraphs=[data['scope'],'La fase se compara en la diferencia compleja, conservando su referencia. RMS es el promedio sobre los puntos comparados; no una integral temporal.'])]
    if data.get('clock_note'):sections.append(Section('Reloj físico',paragraphs=[data['clock_note']]))
    impulses=data.get('impulses')
    if impulses:
        maximum=impulses['metrics']['absolute_max']
        differences=impulses['first_differences']
        details=[(number(t)+' '+data['units'],'A = '+number(complex(*a))+' · B = '+number(complex(*b))) for t,a,b in differences]
        sections.append(Section('Impulsos de Dirac',rows=[
            ('Impulsos en A',str(impulses['terms_a'])),('Impulsos en B',str(impulses['terms_b'])),
            ('Posiciones con pesos distintos',str(impulses['different_positions'])),
            ('Máxima diferencia de peso',number(maximum) if maximum is not None else 'Fuera de rango'),*details],
            paragraphs=['Se comparan los pesos en la unión de las posiciones de A y B. Las métricas de muestras de arriba corresponden a la parte ordinaria. Se listan hasta doce posiciones con diferencias.']))
    trace=data.get('trace')
    if trace is not None:
        sections.append(Section('Diferencia y exportación',rows=[('Coordenadas almacenadas comunes',str(len(trace['coordinates']))),('Pares no definidos',str(trace['undefined_count'])),('Restas fuera de rango float64',str(trace['overflow_count']))],paragraphs=['La figura Diferencia B−A y el CSV utilizan estas coordenadas comunes, conservando signo y fase. No se completan huecos ni se interpola. El CSV distingue entradas no definidas y diferencias fuera de rango; una métrica positiva no representable no se presenta como cero.']))
    for index,condition in enumerate(data.get('conditions',())):sections.append(Section('Sistema '+('A' if index==0 else 'B'),rows=[('ROC',condition['roc']),('Causalidad',condition['causality']),('BIBO',condition['bibo_stability'])],paragraphs=[condition['frequency_interpretation']]))
    return Summary('Comparación de resultados',sections)


def open_comparison(window):
    dialog=getattr(window,'_result_comparison',None)
    if dialog is None:dialog=ComparisonDialog(window);window._result_comparison=dialog
    dialog.refresh();dialog.show();dialog.raise_();dialog.activateWindow()


from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QComboBox,QPushButton,QFormLayout,QLineEdit,QTabWidget,QWidget,QLabel,QMessageBox,QFileDialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT
from .report_view import ReportView,report_panel


class ComparisonDialog(QDialog):
    def __init__(self,window):
        super().__init__(window);self.owner=window;self.data=None;self.setWindowTitle('Comparar resultados · SignalLab');self.resize(850,660)
        root=QVBoxLayout(self);form=QFormLayout();root.addLayout(form);self.a=QComboBox();self.b=QComboBox();form.addRow('Resultado A',self.a);form.addRow('Resultado B',self.b)
        self.alignment=QComboBox();self.alignment.addItems(['Índices n','Tiempo físico (s)'])
        self.alignment_label=QLabel('Alineación de muestras');form.addRow(self.alignment_label,self.alignment)
        self.alignment.hide();self.alignment_label.hide()
        self.frequency_box=QWidget();row=QHBoxLayout(self.frequency_box);row.setContentsMargins(0,0,0,0);self.start=QLineEdit('0');self.stop=QLineEdit('pi');self.count=QLineEdit('2001');self.unit=QLabel()
        for name,field in [('Desde',self.start),('Hasta',self.stop),('Puntos',self.count)]:field.setAccessibleName(name);row.addWidget(QLabel(name));row.addWidget(field)
        row.addWidget(self.unit);form.addRow('Frecuencias comunes',self.frequency_box);self.frequency_label=form.labelForField(self.frequency_box)
        row=QHBoxLayout();self.mode=QComboBox();self.mode.addItems(['Parte real e imaginaria','Módulo y fase']);self.calculate_button=QPushButton('Comparar');self.calculate_button.setObjectName('primary');row.addStretch();row.addWidget(self.calculate_button);root.addLayout(row)
        from .result_state import ResultState
        self.state=ResultState([self.a,self.b,self.start,self.stop,self.count,self.alignment],self.calculate_button);root.addWidget(self.state)
        bar=QHBoxLayout();bar.addStretch();self.export_button=QPushButton('Exportar comparación CSV…');self.export_button.setEnabled(False);self.export_button.clicked.connect(self.export_comparison);bar.addWidget(self.export_button);root.addLayout(bar)
        self.tabs=QTabWidget();root.addWidget(self.tabs,1);self.report=ReportView();self.tabs.addTab(report_panel(self.report),'Informe');plot=QWidget();layout=QVBoxLayout(plot);self.figure=Figure();self.canvas=FigureCanvasQTAgg(self.figure);self.toolbar=NavigationToolbar2QT(self.canvas,plot);layout.addWidget(self.toolbar);layout.addWidget(self.canvas,1);self.tabs.addTab(plot,'Gráfico')
        self.trace_mode=QComboBox();self.trace_mode.addItems(['Superponer A y B','Diferencia B−A']);self.trace_mode.currentIndexChanged.connect(self.draw)
        controls=QWidget();options=QFormLayout(controls);options.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        options.addRow('Vista',self.trace_mode);options.addRow('Componentes',self.mode)
        layout.insertWidget(0,controls);self.canvas._signallab_plot_controls=controls
        from .plot_view import install_enlarge
        install_enlarge(self.toolbar)
        self.a.currentIndexChanged.connect(self.choose_b);self.mode.currentIndexChanged.connect(self.draw);self.calculate_button.clicked.connect(self.calculate)
        self.report.setPlainText('Elegí dos resultados compatibles. Las señales conservan sus índices y los sistemas usan las mismas frecuencias.')

    def refresh(self):
        selected=self.a.currentData();self.descriptions={};self.titles={};self.a.blockSignals(True);self.a.clear()
        for record in self.owner.project.headers():
            if record['kind'] not in ('signal','system'):continue
            self.descriptions[record['id']]=self.owner.project.describe(record['id']);self.titles[record['id']]=record['title'];self.a.addItem(record['title'],record['id'])
        index=self.a.findData(selected);self.a.setCurrentIndex(index if index>=0 else 0);self.a.blockSignals(False);self.choose_b()

    def choose_b(self,*_):
        selected=self.b.currentData();self.b.clear();key=self.a.currentData();a=self.descriptions.get(key,{})
        for candidate,b in self.descriptions.items():
            if candidate!=key and a.get('kind')==b['kind'] and a.get('domain')==b['domain'] and (b['kind']=='system' or (a.get('units'),a.get('data_kind'))==(b['units'],b['data_kind'])):self.b.addItem(self.titles[candidate],candidate)
        index=self.b.findData(selected)
        if index>=0:self.b.setCurrentIndex(index)
        discrete=a.get('domain')=='discrete'
        self.alignment.setVisible(discrete);self.alignment_label.setVisible(discrete)
        self.alignment.setProperty('calculationInput',discrete)
        systems=a.get('kind')=='system';self.frequency_box.setVisible(systems);self.frequency_label.setVisible(systems);self.calculate_button.setEnabled(self.b.count()>0)
        for field in (self.start,self.stop,self.count):field.setProperty('calculationInput',systems)
        if systems:
            digital=a['domain']=='digital';self.unit.setText('rad/muestra' if digital else 'rad/s')
            if getattr(self,'_digital',None)!=digital:self.stop.setText('pi' if digital else '10');self._digital=digital
        if not self.b.count():self.state.setText('Guardá al menos dos señales con igual dominio/unidades o dos sistemas del mismo dominio.')

    def calculate(self):
        try:
            ka,kb=self.a.currentData(),self.b.currentData();a,b=self.owner.project.get(ka),self.owner.project.get(kb)
            from .numeric_input import real_field,integer_field
            start,stop,count=(real_field(self.start),real_field(self.stop),integer_field(self.count,minimum=2)) if isinstance(a,Transfer) else (0.,1.,2)
            from .validation import ordered_interval
            if isinstance(a,Transfer):ordered_interval(self.start,self.stop,start,stop)
            alignment='physical' if isinstance(a,Signal) and a.domain=='discrete' and self.alignment.currentIndex()==1 else 'index'
            snapshot=self.state.snapshot()
            def accept(data):
                captured=data.pop('input_snapshots',None)
                self.data={**data,**({'signals':tuple(Signal(**values) for values in captured)} if captured is not None else {'systems':(a,b)})};self.export_button.setEnabled(bool(len(data['trace']['coordinates'])));self.report.set_readable(summary(data));self.state.accept(snapshot);self.draw()
                saved={k:v for k,v in data.items() if k not in ('signals','systems','omega','responses','trace')};saved.update(operation='result_comparison',report=summary(data).plain_text(),source_ids=[ka,kb])
                saved['calculated_data']={k:v for k,v in saved.items() if k!='report'}
                self.owner.publish(saved,title='Comparación A / B',operation='Comparación de resultados',parents=[ka,kb])
                journal=getattr(self.owner,'_result_journal',None)
                if journal is not None:journal.reported(data)
                self.tabs.setCurrentIndex(0)
            def compute():
                data=compare(a,b,start,stop,count,alignment=alignment)
                captured=data.pop('signals',None)
                if captured is not None:data['input_snapshots']=[dict(vars(value)) for value in captured]
                data.pop('systems',None)
                return data
            self.owner._run_operation('Comparando resultados…',compute,accept)
        except (ValueError,KeyError) as exc:QMessageBox.warning(self,'Revisá la comparación',str(exc))

    def export_comparison(self):
        if self.data is None:return
        path,_=QFileDialog.getSaveFileName(self,'Exportar puntos comunes y diferencia','comparacion.csv','CSV (*.csv)')
        if not path:return
        try:
            from .comparison_trace import export_csv
            export_csv(path,self.data['trace'])
        except (OSError,ValueError) as exc:QMessageBox.warning(self,'No se pudo exportar',str(exc))

    def draw(self,*_):
        if self.data is None:return
        from .signal_plot import plot_samples,configure_signal_axis,configure_axis,is_discrete_plot
        from .ui import SignalLabWindow
        self.figure.clear();axes=self.figure.subplots(2,1,sharex=True);polar=self.mode.currentIndex()==1
        if self.trace_mode.currentIndex()==1:
            trace=self.data['trace'];values=trace['error'];coordinates=trace['coordinates']
            for axis,curve in zip(axes,(abs(values),np.where(abs(values)>0,np.angle(values),np.nan)) if polar else (values.real,values.imag)):
                plot_samples(axis,coordinates,curve,discrete=trace['discrete'],label='B−A',phase=polar and axis is axes[1])
                configure_axis(axis,discrete_index=trace['index'],units=trace['units'],label=trace['label'],index_symbol='k' if trace['units'] in ('k','bin k') else 'n')
            if not len(coordinates):axes[0].text(.5,.5,'Sin coordenadas almacenadas comunes',ha='center',transform=axes[0].transAxes)
            elif not np.isfinite(values).all():axes[0].set_title('Sólo diferencias finitas · consultá el informe para los puntos omitidos',fontsize=9)
        elif 'signals' in self.data:
            physical=self.data.get('alignment')=='physical'
            for letter,source in zip(('A','B'),self.data['signals']):
                ids=SignalLabWindow._plot_indices(source.values);v=source.values[ids];phase=np.where(abs(v)>0,np.angle(v),np.nan)
                for axis,values,component in zip(axes,(abs(v),phase) if polar else (v.real,v.imag),('magnitude','phase') if polar else ('real','imag')):
                    coordinates=_physical_axis(source) if physical else source.axis
                    plot_samples(axis,coordinates[ids],values,discrete=is_discrete_plot(source),label=letter+' · '+source.name,
                                 phase=component=='phase',source=None if physical else source,component=component)
            if physical:configure_axis(axes[-1],units='s',label='Tiempo físico (s)')
            else:configure_signal_axis(axes[-1],self.data['signals'][0])
        else:
            for letter,values,system in zip(('A','B'),self.data['responses'],self.data['systems']):
                phase=np.where(np.isfinite(values)&(abs(values)>0),np.angle(values),np.nan)
                for axis,curve in zip(axes,(abs(values),phase) if polar else (values.real,values.imag)):plot_samples(axis,self.data['omega'],curve,label=letter+' · '+system.name,phase=polar and axis is axes[1])
            configure_axis(axes[-1],units=self.data['units'],label='Frecuencia angular ('+self.data['units']+')')
        for axis,label in zip(axes,('Módulo','Fase (rad)') if polar else ('Parte real','Parte imaginaria')):axis.set_ylabel(label);axis.grid(alpha=.25);axis.legend()
        self.canvas.draw_idle()
