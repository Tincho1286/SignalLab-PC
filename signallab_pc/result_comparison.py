"""Compare saved objects on explicit common coordinates, without realignment."""
import numpy as np
from .model import Signal
from .filters import Transfer


def compatible(a,b):
    return isinstance(a,Signal) and isinstance(b,Signal) and a.domain==b.domain and a.units==b.units or isinstance(a,Transfer) and isinstance(b,Transfer) and a.domain==b.domain


def errors(a,b):
    finite=np.isfinite(a)&np.isfinite(b);a=a[finite];b=b[finite]
    if not a.size:return {'count':0,'relative_max':None,'absolute_max':None,'rms':None}
    scale=max(np.max(abs(a.real)),np.max(abs(a.imag)),np.max(abs(b.real)),np.max(abs(b.imag)))
    if scale==0:return {'count':int(a.size),'relative_max':0.,'absolute_max':0.,'rms':0.}
    aa=a/scale;bb=b/scale;delta=bb-aa;size=np.abs(delta)
    maximum=float(size.max());rms=float(np.sqrt(np.mean(size**2)))
    def absolute(v):
        with np.errstate(over='ignore'):result=v*scale
        return float(result) if np.isfinite(result) else None
    return {'count':int(a.size),'relative_max':maximum/float(max(abs(aa).max(),abs(bb).max())),'absolute_max':absolute(maximum),'rms':absolute(rms)}


def compare(a,b,start=0.,stop=np.pi,count=2001):
    if not compatible(a,b):raise ValueError('Elegí dos señales del mismo dominio y unidades, o dos sistemas del mismo dominio.')
    from .resources import ensure_working_set
    if isinstance(a,Signal):
        ensure_working_set(a.values.size+b.values.size,live_arrays=12)
        if a.domain=='discrete':
            low=max(a.origin,b.origin);high=min(a.origin+a.values.size-1,b.origin+b.values.size-1)
            n=max(0,int(high-low+1));one=a.values[low-a.origin:low-a.origin+n];two=b.values[low-b.origin:low-b.origin+n]
        else:
            common,i,j=np.intersect1d(a.axis,b.axis,assume_unique=False,return_indices=True);one=a.values[i];two=b.values[j]
        metrics=errors(one,two)
        return {'metrics':metrics,'signals':(a,b),'scope':'Se comparan sólo coordenadas almacenadas exactamente coincidentes. Se conservan origen, amplitud y fase; no se interpola, desplaza ni rellena con ceros. Una ausencia de puntos comunes no significa igualdad.','units':a.units,'domain':a.domain}
    from .frequency_analysis import frequency_grid
    from .system_conditions import record
    w=frequency_grid(start,stop,count);one=a.response(w);two=b.response(w)
    return {'metrics':errors(one,two),'omega':w,'frequency_interval':[float(start),float(stop)],'frequency_count':int(count),'responses':(one,two),'systems':(a,b),'conditions':(record(a),record(b)),'units':'rad/muestra' if a.domain=='digital' else 'rad/s','domain':'frequency','scope':'Ambas fórmulas se evalúan en las mismas frecuencias. La interpretación como respuesta de Fourier depende de la ROC de cada sistema. Las métricas excluyen puntos no finitos y no prueban máximos entre frecuencias.'}


def summary(data):
    from .result_summary import Summary,Section,Formula,number
    m=data['metrics']
    rows=[('Coordenadas comunes finitas',str(m['count']))]
    for key,label in [('absolute_max','Máximo |B−A|'),('rms','RMS de B−A'),('relative_max','Máximo relativo a la mayor amplitud de A/B')]:rows.append((label,number(m[key]) if m[key] is not None else 'No disponible'))
    sections=[Section('Diferencias sobre coordenadas comunes',rows=rows,formulas=[Formula('e = B-A','e = B − A')]),Section('Interpretación',paragraphs=[data['scope'],'La fase se compara en la diferencia compleja, conservando su referencia. RMS es el promedio sobre los puntos comparados; no una integral temporal.'])]
    for index,condition in enumerate(data.get('conditions',())):sections.append(Section('Sistema '+('A' if index==0 else 'B'),rows=[('ROC',condition['roc']),('Causalidad',condition['causality']),('BIBO',condition['bibo_stability'])],paragraphs=[condition['frequency_interpretation']]))
    return Summary('Comparación de resultados',sections)


def open_comparison(window):
    dialog=getattr(window,'_result_comparison',None)
    if dialog is None:dialog=ComparisonDialog(window);window._result_comparison=dialog
    dialog.refresh();dialog.show();dialog.raise_();dialog.activateWindow()


from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QComboBox,QPushButton,QFormLayout,QLineEdit,QTabWidget,QWidget,QLabel,QMessageBox
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT
from .report_view import ReportView,report_panel


class ComparisonDialog(QDialog):
    def __init__(self,window):
        super().__init__(window);self.owner=window;self.data=None;self.setWindowTitle('Comparar resultados · SignalLab');self.resize(850,660)
        root=QVBoxLayout(self);form=QFormLayout();root.addLayout(form);self.a=QComboBox();self.b=QComboBox();form.addRow('Resultado A',self.a);form.addRow('Resultado B',self.b)
        self.frequency_box=QWidget();row=QHBoxLayout(self.frequency_box);row.setContentsMargins(0,0,0,0);self.start=QLineEdit('0');self.stop=QLineEdit('pi');self.count=QLineEdit('2001');self.unit=QLabel()
        for name,field in [('Desde',self.start),('Hasta',self.stop),('Puntos',self.count)]:field.setAccessibleName(name);row.addWidget(QLabel(name));row.addWidget(field)
        row.addWidget(self.unit);form.addRow('Frecuencias comunes',self.frequency_box)
        row=QHBoxLayout();self.mode=QComboBox();self.mode.addItems(['Parte real e imaginaria','Módulo y fase']);self.calculate_button=QPushButton('Comparar');self.calculate_button.setObjectName('primary');row.addWidget(self.mode);row.addStretch();row.addWidget(self.calculate_button);root.addLayout(row)
        from .result_state import ResultState
        self.state=ResultState([self.a,self.b,self.start,self.stop,self.count],self.calculate_button);root.addWidget(self.state)
        self.tabs=QTabWidget();root.addWidget(self.tabs,1);self.report=ReportView();self.tabs.addTab(report_panel(self.report),'Informe');plot=QWidget();layout=QVBoxLayout(plot);self.figure=Figure();self.canvas=FigureCanvasQTAgg(self.figure);self.toolbar=NavigationToolbar2QT(self.canvas,plot);layout.addWidget(self.toolbar);layout.addWidget(self.canvas,1);self.tabs.addTab(plot,'Gráfico')
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
            if candidate!=key and a.get('kind')==b['kind'] and a.get('domain')==b['domain'] and (b['kind']=='system' or a.get('units')==b['units']):self.b.addItem(self.titles[candidate],candidate)
        index=self.b.findData(selected)
        if index>=0:self.b.setCurrentIndex(index)
        systems=a.get('kind')=='system';self.frequency_box.setVisible(systems);self.calculate_button.setEnabled(self.b.count()>0)
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
            snapshot=self.state.snapshot()
            def accept(data):
                self.data={**data,**({'signals':(a,b)} if isinstance(a,Signal) else {'systems':(a,b)})};self.report.set_readable(summary(data));self.state.accept(snapshot);self.draw()
                saved={k:v for k,v in data.items() if k not in ('signals','systems','omega','responses')};saved.update(operation='result_comparison',report=summary(data).plain_text(),source_ids=[ka,kb])
                self.owner.publish(saved,title='Comparación A / B',operation='Comparación de resultados',parents=[ka,kb])
                journal=getattr(self.owner,'_result_journal',None)
                if journal is not None:journal.reported(data)
                self.tabs.setCurrentIndex(0)
            def compute():
                data=compare(a,b,start,stop,count)
                data.pop('signals',None);data.pop('systems',None)
                return data
            self.owner._run_operation('Comparando resultados…',compute,accept)
        except (ValueError,KeyError) as exc:QMessageBox.warning(self,'Revisá la comparación',str(exc))

    def draw(self,*_):
        if self.data is None:return
        from .signal_plot import plot_samples,configure_signal_axis,configure_axis,is_discrete_plot
        from .ui import SignalLabWindow
        self.figure.clear();axes=self.figure.subplots(2,1,sharex=True);polar=self.mode.currentIndex()==1
        if 'signals' in self.data:
            for letter,source in zip(('A','B'),self.data['signals']):
                ids=SignalLabWindow._plot_indices(source.values);v=source.values[ids];phase=np.where(abs(v)>0,np.angle(v),np.nan)
                for axis,values,component in zip(axes,(abs(v),phase) if polar else (v.real,v.imag),('magnitude','phase') if polar else ('real','imag')):
                    plot_samples(axis,source.axis[ids],values,discrete=is_discrete_plot(source),label=letter+' · '+source.name,phase=component=='phase',source=source,component=component)
            configure_signal_axis(axes[-1],self.data['signals'][0])
        else:
            for letter,values,system in zip(('A','B'),self.data['responses'],self.data['systems']):
                phase=np.where(abs(values)>0,np.angle(values),np.nan)
                for axis,curve in zip(axes,(abs(values),phase) if polar else (values.real,values.imag)):plot_samples(axis,self.data['omega'],curve,label=letter+' · '+system.name,phase=polar and axis is axes[1])
            configure_axis(axes[-1],units=self.data['units'],label='Frecuencia angular ('+self.data['units']+')')
        for axis,label in zip(axes,('Módulo','Fase (rad)') if polar else ('Parte real','Parte imaginaria')):axis.set_ylabel(label);axis.grid(alpha=.25);axis.legend()
        self.canvas.draw_idle()
