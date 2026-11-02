from .numeric_input import real_field,integer_field,constant_value
"""Menús de calculadoras independientes, con entradas y resultados locales."""
from dataclasses import asdict
import json
import hashlib
import weakref
import numpy as np
from PySide6.QtCore import Qt, QThreadPool, Signal as QtSignal
from PySide6.QtWidgets import (QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,
    QLabel,QPushButton,QLineEdit,QComboBox,QGroupBox,QFormLayout,QScrollArea,
    QStackedWidget,QTabWidget,QPlainTextEdit,QFileDialog,QMessageBox,QButtonGroup,QInputDialog,QListWidget,QSplitter,QTabBar,QMenu,QCheckBox)
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT
from .ui import SignalLabWindow
from .design import configure_theme,STYLE,icon,action_title
from .engine import sequence_from_expression,sequence_from_values,evaluate_expression
from .model import Signal
from .storage import load_json,save_json,save_csv
from .atomic_file import write_json
from . import operations as ops
from . import continuous
from .systems_panel import SystemsPanel,parse_list
from .filters import Transfer
from .sampling_panel import SamplingPanel
from .fourier_panel import FourierPanel
from .symbolic_panel import SymbolicPanel
from .theory_panel import TheoryPanel
from .project import Project,encode
from .state_space import StateModel

from .navigation import MENUS
from . import __version__
from .tool_descriptions import describe_tool
from .report_view import ReportView,report_panel
from .expression_editor import ExpressionEditor
from .result_summary import operation_label
from .signal_plot import plot_samples
from .signal_plot import configure_signal_axis, is_discrete_plot, validate_overlay

def signal_destinations(value,items):
    return [item for item in items if (item[1:3]==('transform_lab','z') and value.domain=='discrete') or (item[1]=='basic' and item[2] in ('generate','measures') and value.domain in {'continuous','discrete'}) or (item[1]=='dsp_extensions' and item[2] in ('hilbert','stft') and value.domain in {'continuous','discrete'}) or (item[1]=='frequency_filter' and value.domain in {'discrete','continuous','frequency'} and (value.domain!='frequency' or value.units in {'rad/s','rad/muestra'})) or item[3] in ({'discrete','pair'} if value.domain=='discrete' else {'continuous','continuous_pair'} if value.domain=='continuous' else set()) or (item[1]=='systems' and item[2]==9 and value.domain in {'discrete','continuous'}) or (item[1]=='course_tools' and item[2]=='band' and value.domain=='frequency' and value.units in {'rad/s','rad/muestra'}) or (item[1]=='correlation' and value.domain==('continuous' if item[2] else 'discrete')) or (item[1]=='signal_editor' and value.domain in {'discrete','continuous'}) or (item[1]=='rational_resampling' and value.domain=='discrete') or (item[1:3]==('sampling',5) and value.domain=='discrete') or (item[1:3]==('fourier',6) and value.domain in {'discrete','continuous','frequency'}) or (item[1]=='fourier' and item[2] in (3,6) and value.domain=='frequency' and (item[2]!=3 or value.units=='rad/s')) or (item[1]=='inverse_dtft' and value.domain=='frequency' and value.units=='rad/muestra') or ((item[1]=='signal_product' or item[1:3]==('basic','sum')) and value.domain in {'discrete','continuous'}) or (item[1:3]==('state_space','simulation') and value.domain in {'discrete','continuous'})]

def system_destinations(value,items):
    keys={('system_analysis',0),('interconnection',0),('systems',9),('systems',6),('course_tools','convert'),('course_tools','gain')}
    if value.domain=='digital':keys|={('course_tools','phase'),('course_tools','inverse_z'),('sampling',5),('random_model','model')}
    if value.advance:keys={('system_analysis',0),('systems',6),('course_tools','inverse_z'),('course_tools','gain'),('interconnection',0)}
    return [item for item in items if item[1:3] in keys]


class LocalInput(QGroupBox):
    sourceChanged=QtSignal()
    def __init__(self,title,kind='discrete'):
        super().__init__(title);self.kind=kind;self.loaded=None;self.project_window=None;self.reference_id=None;self.loaded_reference_id=None;self.fingerprint=None
        form=QFormLayout(self);form.setProperty('stackFields',True);form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.mode=QComboBox();self.mode.addItems(['Definir una fórmula','Ingresar muestras','Usar archivo o resultado anterior'])
        self.expression=ExpressionEditor('exp(-w^2)' if kind=='frequency' else 'cos(2*pi*t)' if kind=='continuous' else 'cos(pi*n/4)')
        self.samples=QLineEdit('1, 2, 1');self.samples.setToolTip('Pegá valores separados por coma, punto y coma o salto de línea. Se admiten pi, fracciones, 10^(-3) y complejos.');self.origin=QLineEdit('0');self.count=QLineEdit('64');self.step=QLineEdit('0.01')
        from .choice_buttons import ChoiceButtons
        from .source_selector import SourceSelector
        self.entry_modes=SourceSelector(self.mode);form.addRow(self.entry_modes);form.addRow('X(ω), usar w como variable' if kind=='frequency' else 'x(t)' if kind=='continuous' else 'x[n]',self.expression);form.addRow('Valores separados por coma',self.samples)
        interval=QWidget();self.interval=interval;row=QHBoxLayout(interval);row.setContentsMargins(0,0,0,0);row.setSpacing(8)
        fields=[('Inicio',self.origin),('Cantidad',self.count)]
        if kind in ('continuous','frequency'):fields.append(('Paso angular' if kind=='frequency' else 'Paso (s)',self.step))
        axis_widgets={};self.coordinate_labels={}
        for title,field in fields:
            container=QWidget();column=QVBoxLayout(container);column.setContentsMargins(0,0,0,0);column.setSpacing(4);coordinate_label=QLabel(title);self.coordinate_labels[field]=coordinate_label;column.addWidget(coordinate_label);field.setMaximumWidth(180);column.addWidget(field);row.addWidget(container);axis_widgets[field]=container
        form.addRow(interval)
        if kind=='frequency':
            self.frequency_units=QComboBox();self.frequency_units.addItems(['rad/s','rad/muestra']);form.addRow('Unidad del eje de frecuencia',self.frequency_units)
        if kind=='continuous':self.expression.setToolTip('Usá t en segundos. DiracDelta(t-a), dirac(t-a) e impulse(t-a) conservan posición y peso, incluso entre puntos. La última coordenada es inicio+(cantidad−1)·paso; los impulsos fuera de ese intervalo se informan aparte.')
        self.origin.setToolTip('Primer índice o coordenada del registro; no es la cantidad de valores.')
        self.count.setToolTip('Cantidad entera positiva. Última coordenada = inicio + (cantidad−1)·paso.')
        self.step.setToolTip('Separación positiva entre puntos. No es la frecuencia de muestreo.')
        self.file_note=QLabel('Abrí JSON, CSV o MATLAB (.mat / .m). Podés elegir las variables, columnas y el eje de los datos externos.');self.file_note.setWordWrap(True);form.addRow(self.file_note)
        load=QPushButton('Elegir archivo…');load.clicked.connect(self.open_file);form.addRow(load)
        def update(index):
            form.setRowVisible(self.expression,index==0);form.setRowVisible(self.samples,index==1)
            form.setRowVisible(interval,index!=2);form.setRowVisible(self.file_note,index==2)
            if hasattr(self,'frequency_units'):form.setRowVisible(self.frequency_units,index!=2)
            axis_widgets[self.count].setVisible(index==0);form.setRowVisible(load,index==2)
            if hasattr(self,'recent'):form.setRowVisible(self.recent,index==2 and self.entry_modes.view==3);form.setRowVisible(self.browse_results,index==2 and self.entry_modes.view==3)
        self.entry_modes.viewChanged.connect(lambda:update(self.mode.currentIndex()))
        self.mode.currentIndexChanged.connect(update);self.mode.setCurrentIndex(2 if kind=='import' else 0);update(self.mode.currentIndex())
    def set_role(self,role):
        if self.kind!='discrete':return
        coefficients=role=='series_coefficients'
        self.layout().labelForField(self.expression).setText('c[k]' if coefficients else 'x[n]')
        self.layout().labelForField(self.samples).setText('c[k₀], c[k₀+1], …' if coefficients else 'Valores separados por coma')
        self.coordinate_labels[self.origin].setText('Primer armónico k₀' if coefficients else 'Inicio')
        self.coordinate_labels[self.count].setText('Coeficientes' if coefficients else 'Cantidad')
    def open_file(self):
        try:
            from .data_import import load_signal
            value=load_signal(self,self.kind)
            if value is not None:self.set_source(value)
        except Exception as exc:QMessageBox.warning(self,'No se pudo importar',str(exc))
    def set_source(self,source,reference_id=None):
        if self.kind in ('continuous','discrete','frequency') and source.domain!=self.kind:
            raise ValueError('Esta entrada requiere '+('un espectro.' if self.kind=='frequency' else 'una señal continua.' if self.kind=='continuous' else 'una secuencia discreta.'))
        self.reference_id=reference_id;self.loaded_reference_id=reference_id;self.fingerprint=None
        self.loaded=source;self.entry_modes.select(3 if reference_id is not None else 2);self.mode.setCurrentIndex(2);self.file_note.setText(f'{source.name}\n{source.values.size:,} muestras · '+{'continuous':'Tiempo continuo','discrete':'Secuencia discreta','frequency':'Espectro'}.get(source.domain,source.domain));self.file_note.setObjectName('loadedSignal');self.file_note.style().unpolish(self.file_note);self.file_note.style().polish(self.file_note)
        self.source_revision=getattr(self,'source_revision',0)+1
        self.sourceChanged.emit()
    def bind_project(self,window):
        self.project_window=window
        self.recent=QComboBox();self.recent.setAccessibleName('Señales recientes compatibles');self.recent.activated.connect(self.use_recent);self.layout().addRow('Reutilizar señal',self.recent)
        button=QPushButton('Explorar resultados o importar…');self.browse_results=button;button.clicked.connect(self.choose_project);self.layout().addRow(button)
        self.layout().setRowVisible(self.recent,self.mode.currentIndex()==2 and self.entry_modes.view==3);self.layout().setRowVisible(button,self.mode.currentIndex()==2 and self.entry_modes.view==3)
        self.refresh_recent()
    def refresh_recent(self):
        if not hasattr(self,'recent'):return
        self.recent.blockSignals(True);self.recent.clear();self.recent.addItem('Elegir una señal reciente…',None)
        records=reversed(self.project_window.project.headers('signal'))
        for record in records:
            info=self.project_window.project.describe(record['id'])
            if self.kind in ('continuous','discrete','frequency') and info['domain']!=self.kind:continue
            self.recent.addItem(f"{record['title']} · {info['count']:,} muestras",record['id'])
            self.recent.setItemData(self.recent.count()-1,record['operation'],Qt.ItemDataRole.ToolTipRole)
            if self.recent.count()>20:break
        self.recent.setEnabled(self.recent.count()>1);self.recent.blockSignals(False)
    def use_recent(self,index):
        key=self.recent.itemData(index)
        if key:self.set_source(self.project_window.project.get(key),key)

    def choose_project(self):
        key=self.project_window.choose_record('signal',domains=[self.kind] if self.kind in ('continuous','discrete','frequency') else None)
        if key:self.set_source(self.project_window.project.get(key),key)
    def read(self):
        value=self._read()
        origin=getattr(self,'_expression_origin',None)
        if self.mode.currentIndex()==0 and origin and origin[0]==self.expression.text() and getattr(self,'_expression_conditions',()):
            value.metadata['source_conditions']=list(self._expression_conditions)
        if self.project_window:
            if self.mode.currentIndex()==2 and self.loaded_reference_id:
                self.reference_id=self.loaded_reference_id;return value
            header=json.dumps(dict(origin=value.origin,step=value.step,units=value.units,name=value.name,domain=value.domain,expression=value.expression,metadata=value.metadata),sort_keys=True,allow_nan=False)
            signature=(header,hashlib.sha256(value.values.tobytes()).digest())
            if signature!=self.fingerprint:
                origin=getattr(self,'_expression_origin',None)
                parents=[origin[1]] if self.mode.currentIndex()==0 and origin and origin[1] and origin[0]==self.expression.text() else []
                self.reference_id=self.project_window.publish(value,operation='Entrada: '+self.title(),parents=parents)
                self.fingerprint=signature
                if self.mode.currentIndex()==2:self.loaded_reference_id=self.reference_id
        return value
    def _read(self):
        mode=self.mode.currentIndex()
        if mode==2:
            if self.loaded is None:raise ValueError('Abrí los datos de entrada dentro de esta herramienta.')
            return self.loaded
        if self.kind in ('continuous','frequency'):
            origin=real_field(self.origin);step=real_field(self.step)
            if step<=0:raise ValueError('El paso del eje debe ser positivo.')
            if mode==0:
                count=integer_field(self.count)
                from .resources import ensure_working_set
                ensure_working_set(count)
                if count<1:raise ValueError('La cantidad debe ser positiva.')
                from .continuous_expression import sample_continuous,has_dirac
                if self.kind=='continuous':return sample_continuous(self.expression.text(),origin,step,count)
                if has_dirac(self.expression.text()):raise ValueError('Un impulso en frecuencia es una distribución. Usá Fourier algebraica o sus series; esta entrada numérica requiere valores ordinarios de X(ω).')
                values=evaluate_expression(self.expression.text(),origin+step*np.arange(count))
            else:values=sequence_from_values(self.samples.text(),0).values
            return Signal(values,origin,step,self.frequency_units.currentText() if self.kind=='frequency' else 's','X(ω)' if self.kind=='frequency' else 'x(t)',self.kind,self.expression.text() if mode==0 else '')
        return (sequence_from_expression(self.expression.text(),integer_field(self.origin),integer_field(self.count)) if mode==0 else sequence_from_values(self.samples.text(),integer_field(self.origin)))

class ResultView(QWidget):
    def __init__(self,details=True):
        super().__init__();self.result=None;self.result_ids=[];self.details=details;layout=QVBoxLayout(self);root=layout
        from .active_stack import ActiveTabs
        self.views=ActiveTabs();layout.addWidget(self.views,1);plot=QWidget();layout=QVBoxLayout(plot);self.views.addTab(plot,'Gráfico')
        bar=QHBoxLayout();self.label=QLabel('El resultado aparecerá aquí.');bar.addWidget(self.label,1)
        self.send=QPushButton('Usar en otra herramienta…');self.send.setProperty('actionRole','reuse');self.send.setEnabled(False);self.send_menu=QMenu(self.send);self.send.setMenu(self.send_menu);self.send_menu.aboutToShow.connect(self.prepare_send);bar.addWidget(self.send)
        self.save=QPushButton('Exportar datos…');self.save.setEnabled(False);self.save.clicked.connect(self.export);bar.addWidget(self.save);self.actions=QWidget();self.actions.setLayout(bar);bar.setContentsMargins(0,0,0,0);root.insertWidget(0,self.actions)
        self.plot_mode=QComboBox();self.plot_mode.addItems(['Módulo y fase','Parte real e imaginaria']);self.plot_mode.setAccessibleName('Representación del resultado');self.plot_mode.currentIndexChanged.connect(self.draw_signal);layout.addWidget(self.plot_mode)
        self.figure=Figure(figsize=(7,3));empty=self.figure.add_subplot(111);empty.set_axis_off();empty.text(.5,.5,'Completá las entradas y presioná Calcular',ha='center',color='#8194ae',transform=empty.transAxes);self.canvas=FigureCanvasQTAgg(self.figure);self.canvas.setMinimumHeight(260);layout.addWidget(NavigationToolbar2QT(self.canvas,self));layout.addWidget(self.canvas,1)
        self.text=ReportView();self.views.addTab(report_panel(self.text),'Informe');self.views.setTabVisible(1,details)
        from .result_table import ResultTable
        self.table_view=ResultTable();self.table_index=self.views.addTab(self.table_view,'Valores');self.views.setTabVisible(self.table_index,False)
        self.details_view=ReportView();self.details_index=self.views.addTab(report_panel(self.details_view),'Datos del cálculo');self.views.setTabVisible(self.details_index,False)
        if not details:self.views.tabBar().hide()
        self.empty=QLabel('El resultado aparecerá después de calcular.');self.empty.setObjectName('muted');self.empty.setWordWrap(True);root.insertWidget(0,self.empty);self.views.hide();self.actions.hide()
    def show_content(self):
        self.empty.hide();self.views.show();self.actions.show()
    def show_result(self,result,*,source=None,operation=None):
        candidates=result if isinstance(result,tuple) else (result,)
        if all(isinstance(value,Signal) for value in candidates):validate_overlay(candidates)
        self.show_content();self.result=result;self.save.setEnabled(True);self.figure.clear()
        signals=result if isinstance(result,tuple) else (result,)
        numeric=all(isinstance(value,Signal) for value in signals);self.table_view.set_signals(signals if numeric else ());self.views.setTabVisible(self.table_index,numeric)
        self.views.setTabVisible(0,numeric);self.views.setTabVisible(1,self.details or not numeric);self.views.setTabVisible(self.details_index,self.details and numeric and any(signal.metadata for signal in signals));self.views.tabBar().show()
        window=self.window();self.result_ids=[window.published_signal_id(value) if isinstance(value,Signal) and hasattr(window,'published_signal_id') else None for value in signals]
        from .cas_transfer import can_send
        reusable=(isinstance(signals[0],Signal) and hasattr(window,'send_signal')) or (hasattr(window,'open_cas') and can_send(result))
        self.send.setEnabled(reusable);self.send.setVisible(reusable)
        if isinstance(signals[0],Signal):
            domain=signals[0].domain
            if getattr(self,'_shown_domain',None)!=domain:
                self.plot_mode.blockSignals(True);self.plot_mode.setCurrentIndex(0 if domain=='frequency' else 1);self.plot_mode.blockSignals(False)
            self._shown_domain=domain
            self.draw_signal()
            self.label.setText(f'Resultado · {signals[0].values.size:,} valores')
            from .result_summary import signal_summary
            self.text.set_readable(signal_summary(result,operation));self.details_view.setPlainText('\n\n'.join(f'{x.name}\n'+json.dumps(x.metadata,ensure_ascii=False,indent=2) for x in signals))
        else:
            from dataclasses import is_dataclass
            from .result_summary import measurement_summary,calculation_summary
            payload=asdict(result) if is_dataclass(result) else result
            summary=measurement_summary(payload,source) or calculation_summary(payload)
            if summary is not None:self.text.set_readable(summary)
            else:self.text.setPlainText(json.dumps(payload,ensure_ascii=False,indent=2))
            self.details_view.setPlainText(json.dumps(payload,ensure_ascii=False,indent=2));self.label.setText('Resultado del cálculo');self.views.setCurrentIndex(1)
        if numeric and self.details and self.views.currentIndex()==0:self.views.setCurrentIndex(1)
        self.canvas.draw_idle()
    def draw_signal(self,*_):
        if self.result is None:return
        signals=self.result if isinstance(self.result,tuple) else (self.result,)
        if not isinstance(signals[0],Signal):return
        self.figure.clear();polar=self.plot_mode.currentIndex()==0
        delay_view=polar and all(v.metadata.get('operation')=='frequency_filter' for v in signals)
        from .distributions import dirac_terms
        ideal_view=any(dirac_terms(source) for source in signals)
        axes=self.figure.subplots(2+int(delay_view)+int(ideal_view),1,sharex=True)
        density=all(source.metadata.get('operation') in {'spectral_density','energy_density'} for source in signals)
        self.plot_mode.setItemText(0,'Densidad y dB' if density else 'Módulo y fase')
        for index,source in enumerate(signals):
            shown=SignalLabWindow._plot_indices(source.values);values=source.values[shown];x=source.axis[shown]
            name=('Par' if index==0 else 'Impar') if len(signals)>1 else source.name
            discrete=is_discrete_plot(source)
            if polar and density:
                first=values.real;second=np.full(values.size,np.nan);valid=first>0;second[valid]=10*np.log10(first[valid])
            elif polar:
                first=np.abs(values);second=np.full(values.size,np.nan);valid=first!=0;second[valid]=np.angle(values[valid])
            else:first=values.real;second=values.imag
            plot_samples(axes[0],x,first,discrete=discrete,label=name)
            valid=np.isfinite(second)
            if np.any(valid):plot_samples(axes[1],x[valid] if discrete else x,second[valid] if discrete else second,discrete=discrete,label=name,phase=polar and not density)
            elif polar:axes[1].text(.5,.5,'Densidad nula: dB = −∞' if density else 'Fase no definida: módulo nulo',ha='center',transform=axes[1].transAxes,color='#95a9bf')
            if delay_view:
                delay=np.full(source.values.size,np.nan);valid_full=np.abs(source.values)>0
                for segment in np.split(np.flatnonzero(valid_full),np.flatnonzero(np.diff(np.flatnonzero(valid_full))>1)+1):
                    if segment.size>2:delay[segment[1:-1]]=-np.gradient(np.unwrap(np.angle(source.values[segment])),source.step)[1:-1]
                axes[2].plot(source.axis[shown],delay[shown],label=name);axes[2].set_ylabel('Retardo aprox. (muestras)' if source.units=='rad/muestra' else 'Retardo aprox. (s)')
                axes[2].set_title('Derivada numérica de fase; no definida en ceros o discontinuidades',fontsize=8)
            from .distributions import dirac_terms
            impulses=dirac_terms(source)
            if impulses:
                positions=np.array([position for position,weight in impulses]);weights=np.array([weight for position,weight in impulses])
                weight_axis=axes[-1]
                plot_samples(weight_axis,positions,weights.real,discrete=True,label=name+' · peso real')
                if np.any(weights.imag):plot_samples(weight_axis,positions,weights.imag,discrete=True,label=name+' · peso imaginario')
                weight_axis.set_ylabel('Peso Dirac');weight_axis.set_title('Impulsos ideales · peso (área)',fontsize=9)
                axes[0].set_title('Parte ordinaria · los impulsos se muestran por separado',fontsize=9)
        if any(SignalLabWindow._plot_indices(v.values).size<v.values.size for v in signals):axes[0].set_title('Vista reducida: consultá Valores o exportá para ver todas las muestras',fontsize=9)
        axes[0].set_ylabel('Densidad' if polar and density else 'Módulo' if polar else 'Parte real');axes[1].set_ylabel('Densidad (dB)' if polar and density else 'Fase (rad)' if polar else 'Parte imaginaria');configure_signal_axis(axes[-1],signals[0])
        for axis in axes:
            axis.grid(alpha=.2)
            if axis.get_legend_handles_labels()[0]:axis.legend()
        if polar:axes[1].set_title('10 log10 de la densidad; cero → −∞, no trazado' if density else 'Fase principal; no se dibuja donde el módulo es cero',fontsize=9)
        self.figure.tight_layout();self.canvas.draw_idle()
    def prepare_send(self):
        self.send_menu.clear();self.send_menu_refs=[];self.send_action_refs=[];window=self.window()
        signals=self.result if isinstance(self.result,tuple) else (self.result,)
        from .cas_transfer import send_to_cas,can_send
        if not all(isinstance(value,Signal) for value in signals):
            if can_send(self.result):self.send_menu.addAction('Calculadora CAS',lambda:send_to_cas(window,value=self.result))
            return
        for index,value in enumerate(signals):
            if not isinstance(value,Signal):continue
            root=self.send_menu.addMenu('Parte par' if index==0 else 'Parte impar') if len(signals)>1 else self.send_menu
            self.send_menu_refs.append(root)
            root.addAction('Calculadora CAS',lambda checked=False,v=value:send_to_cas(window,window.published_signal_id(v),value=v))
            root.addSeparator()
            from .tool_catalog import compact_destinations,AREA_BY_ID,destination_label
            groups={}
            candidates=signal_destinations(value,[item for items in MENUS.values() for item in items])
            for entry,item in compact_destinations(candidates):
                area=entry['area']
                if area not in groups:groups[area]=root.addMenu(AREA_BY_ID[area][1]);self.send_menu_refs.append(groups[area])
                self.send_action_refs.append(groups[area].addAction(destination_label(entry,item),lambda checked=False,it=item,v=value,key=self.result_ids[index]:window.send_signal(v,key,it)))
            self.send_action_refs.extend(root.actions())
        self.send_action_refs.extend(self.send_menu.actions())
    def export(self):
        path,selected_filter=QFileDialog.getSaveFileName(self,'Exportar este resultado','resultado','SignalLab JSON (*.json);;Tabla CSV (*.csv)' if isinstance(self.result,(Signal,tuple)) else 'JSON (*.json)')
        if not path:return
        try:
            from pathlib import Path
            if not Path(path).suffix:path+=('.csv' if 'CSV' in selected_filter else '.json')
            save=save_csv if Path(path).suffix.lower()=='.csv' else save_json
            if isinstance(self.result,Signal):save(self.result,path)
            else:
                from pathlib import Path
                if isinstance(self.result,tuple):
                    base=Path(path)
                    for label,source in zip(['par','impar'],self.result):save(source,base.with_name(base.stem+'_'+label+base.suffix))
                else:
                    from dataclasses import is_dataclass
                    write_json(path,asdict(self.result) if is_dataclass(self.result) else self.result)
        except Exception as exc:QMessageBox.warning(self,'No se pudo guardar',str(exc))

class LocalContext:
    def __init__(self,window,source,output):
        self.window=window;self.source=source;self.output=output;self.result=None;self.saved=[];self.tool_title="";self.parents=[];self.ready=False;self.system_id=None
        self.tabs=self;self.sampling_tab=0;self.prepare_system=lambda panel:None
    @property
    def signal(self):return self.source.read() if self.source else None
    def setCurrentIndex(self,index):pass  # Los paneles antiguos no cambian la navegación del menú.
    def _run_operation(self,message,function,callback):
        parents=[self.source.reference_id] if self.source and self.source.reference_id else []
        if self.system_id:parents.append(self.system_id)
        state=getattr(self,'result_state',None);snapshot=state.snapshot() if state is not None else None
        def accept(result):
            self.parents=parents;self._receiving=True
            try:callback(result)
            finally:self._receiving=False
            if state is not None:state.accept(snapshot)
        return self.window._run_operation(message,function,accept)
    def _remember_signal(self,result):
        self.saved.append(result);self.result=result
        self.window.publish(result,operation=self.tool_title,parents=self.parents)
    def _remember_system(self,system):
        if self.ready:
            self.system_id=self.window.publish(system,operation=self.tool_title,parents=self.parents)
            self.last_system=system;self.last_system_id=self.system_id
    def _remember_calculation(self,result):
        if hasattr(self,'result_state') and not getattr(self,'_receiving',False):self.result_state.accept(self.result_state.snapshot())
        self.window.publish(result,title=self.tool_title,operation=self.tool_title,parents=self.parents)
    def _set_signal(self,result):
        self._remember_signal(result);self.output.show_result(result);self.output.show()
        if hasattr(self,'on_result'):self.on_result()
    _plot_indices=staticmethod(SignalLabWindow._plot_indices)

class ToolPage(QWidget):
    def __init__(self,window,item):
        super().__init__();self.tool_item=item;title,kind,index,input_kind=item;self.context=None
        root=QVBoxLayout(self);root.setContentsMargins(0,0,0,0)
        help_button=QPushButton("Ayuda de esta herramienta");help_button.setIcon(icon("book"));help_button.clicked.connect(lambda:window.show_tool_help(item));help_button.hide()
        if kind=='tool_group':
            from .grouped_tool import GroupedTool
            self.panel=GroupedTool(window,index);root.addWidget(self.panel);return
        if kind=='filter_lab':
            from .filter_lab import FilterLab
            self.panel=FilterLab(window);root.addWidget(self.panel);return
        if kind=='transform_lab':
            from .transform_lab import TransformLab
            self.panel=TransformLab(window,index);root.addWidget(self.panel);return
        if kind=='dsp_extensions':
            from .dsp_extensions_panel import DspExtensionsPanel
            self.panel=DspExtensionsPanel(window,index);root.addWidget(self.panel);return
        if kind=='inverse_dtft':
            from .inverse_dtft_panel import InverseDtftPanel
            self.panel=InverseDtftPanel(window);root.addWidget(self.panel);return
        if kind=='fourier' and index==6:
            from .energy_density_panel import EnergyDensityPanel
            self.panel=EnergyDensityPanel(window);root.addWidget(self.panel);return
        if kind=='frequency_filter':
            from .frequency_filter_panel import FrequencyFilterPanel
            self.panel=FrequencyFilterPanel(window);root.addWidget(self.panel);return
        if kind=='course_tools':
            from .course_tools_panel import CourseToolsPanel
            self.panel=CourseToolsPanel(window,index);root.addWidget(self.panel);return
        if kind=='interconnection':
            from .interconnection_panel import InterconnectionPanel
            self.panel=InterconnectionPanel(window);root.addWidget(self.panel);return
        if kind=='basic' and index in ('shift','reverse','scale','parity'):
            from .signal_transform_panel import SignalTransformPanel
            self.panel=SignalTransformPanel(window,'discrete',index);root.addWidget(self.panel);return
        if kind=='basic' and index=='sum':
            from .signal_product_panel import SignalProductPanel
            self.panel=SignalProductPanel(window,'sum');root.addWidget(self.panel);return
        if kind=='signal_product':
            from .signal_product_panel import SignalProductPanel
            self.panel=SignalProductPanel(window);root.addWidget(self.panel);return
        if kind=='fir_window':
            from .fir_window_panel import FirWindowPanel
            self.panel=FirWindowPanel(window);root.addWidget(self.panel);return
        if kind=='time_transform':
            from .time_transform_panel import TimeTransformPanel
            self.panel=TimeTransformPanel(window,index);root.addWidget(self.panel);return
        if kind=='window_signal':
            from .window_signal_panel import WindowSignalPanel
            self.panel=WindowSignalPanel(window);root.addWidget(self.panel);return
        if kind=='difference_equation':
            from .difference_panel import DifferencePanel
            self.panel=DifferencePanel(window);root.addWidget(self.panel);return
        if kind=='random_model':
            from .random_model_panel import RandomModelPanel
            self.panel=RandomModelPanel(window,index);root.addWidget(self.panel);return
        if kind=='random_correlation':
            from .random_correlation_panel import RandomCorrelationPanel
            self.panel=RandomCorrelationPanel(window);root.addWidget(self.panel);return
        if kind=='random':
            from .random_panel import RandomPanel
            self.panel=RandomPanel(window,index);root.addWidget(self.panel);return
        if kind=='systems' and index==9:
            from .temporal_panel import TemporalPanel
            self.panel=TemporalPanel(window);root.addWidget(self.panel);return
        if kind=='expression_measures':
            from .expression_measures_panel import ExpressionMeasuresPanel
            self.panel=ExpressionMeasuresPanel(window,index);root.addWidget(self.panel);return
        if kind=='state_space':
            from .state_space_panel import StateSpacePanel
            self.panel=StateSpacePanel(window,index);root.addWidget(self.panel);return
        if kind=='signal_editor':
            from .signal_editor_panel import SignalEditorPanel
            self.panel=SignalEditorPanel(window);root.addWidget(self.panel);return
        if kind=='correlation':
            from .correlation_panel import CorrelationPanel
            self.panel=CorrelationPanel(window,temporal=bool(index));root.addWidget(self.panel);return
        if kind in ('fourier_symbolic','dtft_symbolic'):
            from .symbolic_fourier_panel import SymbolicFourierPanel
            self.panel=SymbolicFourierPanel(window,inverse=bool(index),discrete=kind=="dtft_symbolic");root.addWidget(self.panel);return
        if kind=='sampling' and index==5:
            from .precision_panel import PrecisionPanel
            self.panel=PrecisionPanel(window);root.addWidget(self.panel);return
        if kind=='rational_resampling':
            from .rational_resampling_panel import RationalResamplingPanel
            self.panel=RationalResamplingPanel(window);root.addWidget(self.panel);return
        if kind in ('convolution_algebra','correlation_algebra'):
            from .convolution_algebra_panel import ConvolutionAlgebraPanel
            self.panel=ConvolutionAlgebraPanel(window,correlation=kind=="correlation_algebra");root.addWidget(self.panel);return
        if kind=='system_analysis':
            from .system_analysis_panel import SystemAnalysisPanel
            self.panel=SystemAnalysisPanel(window);root.addWidget(self.panel);return
        if kind=='basic':self.build_basic(window,root,index,input_kind);return
        self.output=ResultView(details=False);self.output.hide()
        # Entradas locales y controles se desplazan juntos para ventanas pequeñas.
        body=QWidget();box=QVBoxLayout(body);box.setContentsMargins(0,0,0,0)
        if kind=='fourier' and index in (3,6):input_kind='frequency'
        if kind=='fourier' and index==4:input_kind='discrete'
        source=LocalInput('Espectro de entrada' if input_kind=='frequency' else 'Datos de entrada de esta herramienta',input_kind) if input_kind else None
        if source:source.bind_project(window)
        self.context=LocalContext(window,source,self.output);self.context.tool_title=title
        cls={'fourier':FourierPanel,'sampling':SamplingPanel,'systems':SystemsPanel,'symbolic':SymbolicPanel}[kind]
        self.panel=cls(self.context);self.panel.setParent(self);self.panel.hide()
        selector=self.panel.operation if kind=='symbolic' else self.panel.task_selector
        selector.setCurrentIndex(index);form=selector.parentWidget().layout();form.setRowVisible(selector,False)
        if source:
            if kind=='fourier' and index==4:
                source.setTitle('Coeficientes c[k] para síntesis');source.mode.setCurrentIndex(1);source.samples.setText('0.5, 0, 0.5');source.origin.setText('-1')
            form.insertRow(0,source)
        # Guardado disponible junto al cálculo de cada herramienta.
        for button in self.panel.findChildren(QPushButton):
            if button.text().startswith(('Guardar','Exportar')):
                try:form.setRowVisible(button,True)
                except TypeError:pass
        if kind=='systems' and index in (4,5,7,9,10,11):
            form.setRowVisible(self.panel.transfer_preview,True)
            for field in (self.panel.domain,self.panel.b,self.panel.a):form.setRowVisible(field,True)
            if index in (7,9,10,11):self.panel._accept_system(Transfer([1],[1,1],'analog'))
            for field in reversed((self.panel.domain,self.panel.b,self.panel.a)):
                taken=form.takeRow(field)
                label=taken.labelItem.widget() if taken.labelItem else QLabel('')
                form.insertRow(0,label,field)
            def prepare_system(panel):
                from .transfer_input import read_system
                system=read_system(panel,digital_index=0)
                old=self.context.system_id
                if old is None or encode(window.project.get(old))!=encode(system):
                    self.context.system_id=window.publish(system,operation='Entrada: '+title,parents=[old] if old else [])
                panel.system=system
            self.context.prepare_system=prepare_system
        if kind=='systems' and index in (4,5,7,10,11):
            allowed_domains=['digital'] if index==5 else ['analog'] if index==7 else None
            if allowed_domains:
                self.panel.domain.setCurrentIndex(0 if index==5 else 1)
                self.panel.domain.setEnabled(False)
                self.panel.domain.setToolTip('Esta operación requiere un sistema '+('discreto.' if index==5 else 'continuo.'))
            button=QPushButton('Copiar un sistema anterior (opcional)…')
            def choose_system():
                key=window.choose_record('system',domains=allowed_domains)
                if key:
                    self.context.ready=False
                    self.panel._accept_system(window.project.get(key))
                    self.context.ready=True;self.context.system_id=key
            button.clicked.connect(choose_system);form.insertRow(0,button)
        if kind=='systems' and index in (0,1,2):
            fields=self.panel.fields
            if index in (0,1):
                guidance=QLabel('Frecuencia angular en rad/muestra: ω = 2πf/Fs. Nyquist corresponde a π. Podés escribir pi/4 o 0.25*pi.');guidance.setWordWrap(True);form.insertRow(0,guidance)
            if index==0:
                def update_fir_fields(*_):
                    band=self.panel.kind.currentIndex()>=2
                    form.setRowVisible(fields['f2'],band);form.setRowVisible(fields['beta'],self.panel.window.currentIndex()==4)
                    form.labelForField(fields['f1']).setText('Frecuencia inferior (rad/muestra)' if band else 'Frecuencia de corte (rad/muestra)')
                    form.labelForField(fields['f2']).setText('Frecuencia superior (rad/muestra)')
                self.panel.kind.currentIndexChanged.connect(update_fir_fields);self.panel.window.currentIndexChanged.connect(update_fir_fields);update_fir_fields()
            elif index==1:
                form.labelForField(fields['f1']).setText('Frecuencia angular ω₀ (rad/muestra)')
                form.labelForField(fields['q']).setText('Factor de calidad Q (> 0)')
                fields['q'].setToolTip('Controla la resonancia o el ancho de banda. En el pasabanda implementado, la ganancia de pico es Q.')
            else:
                self.panel.kind.removeItem(3);self.panel.kind.removeItem(2)
                task_note=form.parentWidget().findChild(QLabel,'taskDescription')
                if task_note is not None:form.setRowVisible(task_note,False)
                rc_mode=QComboBox();self.panel.rc_mode=rc_mode;rc_mode.addItems(['Conozco R y C','Quiero calcular un componente desde la frecuencia de corte']);form.insertRow(0,'Cómo definir el circuito',rc_mode)
                rc_note=QLabel();rc_note.setWordWrap(True);form.insertRow(1,rc_note)
                rc_buttons=self.panel.findChildren(QPushButton)
                def update_rc_fields(*_):
                    solve=rc_mode.currentIndex()==1;known_r=self.panel.known.currentIndex()==0
                    form.setRowVisible(fields['r'],not solve or known_r);form.setRowVisible(fields['c'],not solve or not known_r)
                    form.setRowVisible(fields['fc'],solve);form.setRowVisible(self.panel.known,solve);form.setRowVisible(fields['stages'],not solve)
                    for field,used in ((fields['r'],not solve or known_r),(fields['c'],not solve or not known_r),(fields['fc'],solve),(self.panel.known,solve),(fields['stages'],not solve)):
                        field.setProperty('calculationInput',used)
                    for button in rc_buttons:
                        if action_title(button)=='Diseñar RC':form.setRowVisible(button,not solve);button.setProperty('primaryAction',not solve)
                        elif action_title(button)=='Calcular componente RC desde fc':form.setRowVisible(button,solve);button.setProperty('primaryAction',solve)
                    rc_note.setText('Calculá el componente faltante para una etapa RC. fc = 1 / (2πRC). Capacitancia en faradios; 1 µF = 0,000001 F.' if solve else 'Definí resistencia y capacitancia. Varias etapas representan la cascada ideal sin carga entre ellas. Capacitancia en faradios; 1 µF = 0,000001 F.')
                rc_mode.currentIndexChanged.connect(update_rc_fields);self.panel.known.currentIndexChanged.connect(update_rc_fields);update_rc_fields()
        if kind=='fourier' and index in (4,5):
            operation=QComboBox();operation.addItems(['Obtener coeficientes de una señal','Reconstruir desde coeficientes']);form.insertRow(0,'Operación',operation)
            series_buttons=self.panel.findChildren(QPushButton)
            def series_mode(mode):
                synthesis=mode==1
                if index==4:
                    form.setRowVisible(source,synthesis);form.setRowVisible(self.panel.expression,not synthesis);form.setRowVisible(self.panel.harmonics,not synthesis);form.setRowVisible(self.panel.t1,synthesis)
                source.setTitle('Coeficientes c[k] · manuales o importados' if synthesis else 'Un período de la señal');source.set_role('series_coefficients' if synthesis else 'time')
                for button in series_buttons:
                    direct='Serie continua de la expresión' if index==4 else 'Serie discreta: registro = un periodo'
                    inverse='Reconstruir serie continua cargada' if index==4 else 'Reconstruir serie discreta cargada'
                    if action_title(button)==direct:form.setRowVisible(button,not synthesis);button.setProperty('primaryAction',not synthesis)
                    elif action_title(button)==inverse:form.setRowVisible(button,synthesis);button.setProperty('primaryAction',synthesis)
                    elif action_title(button) in ('Serie continua de la expresión','Serie discreta: registro = un periodo','Reconstruir serie continua cargada','Reconstruir serie discreta cargada'):form.setRowVisible(button,False);button.setProperty('primaryAction',False)
            operation.currentIndexChanged.connect(series_mode);series_mode(0)
        self.context.ready=True
        if kind=='symbolic':
            if index==1:self.panel.expression.setText('1/(s+1)')
            if index==3:self.panel.expression.setText('z/(z-1/2)')
        if kind=='fourier' and source:
            use=QPushButton('Usar el último resultado como entrada');use.clicked.connect(lambda:self.reuse(source));form.insertRow(1,use)
        # Sólo los controles desplazan; los resultados ocupan el alto disponible.
        controls=next(scroll for scroll in self.panel.findChildren(QScrollArea) if scroll.widget() is selector.parentWidget())
        split=QSplitter(Qt.Orientation.Horizontal);split.setChildrenCollapsible(False);split.addWidget(controls);controls.setMinimumWidth(300)
        self.result_tabs=QTabWidget();split.addWidget(self.result_tabs);split.setStretchFactor(1,1);split.setSizes([350,740]);root.addWidget(split,1)
        report=self.panel.report;report.setMaximumHeight(16777215)
        if hasattr(self.panel,'canvas'):
            plot=QWidget();plot_box=QVBoxLayout(plot);plot_box.setContentsMargins(0,0,0,0)
            toolbar=self.panel.findChild(NavigationToolbar2QT)
            if kind=='fourier':plot_box.addWidget(self.panel.plot_mode)
            if toolbar:plot_box.addWidget(toolbar)
            self.panel.canvas.setMinimumHeight(420 if kind=='systems' else 320);plot_box.addWidget(self.panel.canvas,1)
            self.result_tabs.addTab(plot,'Gráfico');self.result_tabs.addTab(report_panel(report),'Informe')
            signal_tab=self.result_tabs.addTab(self.output,'Señal de salida');self.result_tabs.setTabVisible(signal_tab,False)
            def reveal():self.result_tabs.setTabVisible(signal_tab,True);self.result_tabs.setCurrentIndex(signal_tab)
        else:
            self.result_tabs.addTab(self.output,'Gráfico');self.result_tabs.addTab(report_panel(report),'Informe');self.output.show()
            def reveal():self.result_tabs.setCurrentIndex(0)
            if kind=='symbolic' or kind=='sampling' and index in (1,5):self.result_tabs.setCurrentIndex(1)
        self.context.on_result=reveal
        if kind=='sampling' and index==1:
            from .alias_view import AliasView
            alias_view=AliasView();self.result_tabs.removeTab(0);self.result_tabs.insertTab(0,alias_view,'Comparación visual')
            def show_alias(value):alias_view.show_alias(value);self.result_tabs.setCurrentIndex(0)
            self.context.on_alias=show_alias
        if kind=='systems' and index in (0,1,2,3,6,7,8,10):
            for legacy_button in form.parentWidget().findChildren(QPushButton):
                if action_title(legacy_button).strip().rstrip('.…') in ('Guardar filtro','Cargar filtro','Exportar respuesta CSV'):
                    form.setRowVisible(legacy_button,False)
            from .coefficient_editor import CoefficientRows
            from PySide6.QtWidgets import QTableView,QAbstractItemView,QHeaderView
            result_bar=QHBoxLayout();result_note=QLabel('Completá el diseño para ver el resultado y sus coeficientes.');result_note.setWordWrap(True);result_note.hide();result_bar.addWidget(result_note,1)
            from .system_result_actions import SystemResultActions
            self.system_actions=SystemResultActions(window);result_bar.addWidget(self.system_actions);self.system_actions.hide()
            if index!=6:
                export_button=self.system_actions.export_button;export_button.clicked.disconnect();export_button.setText('Exportar…')
                export_menu=QMenu(export_button);export_button.setMenu(export_menu);self.design_export_menu=export_menu
                export_menu.addAction('Filtro JSON…',lambda:window.export_transfer(self.system_actions.system) if self.system_actions.system is not None else None)
                self.design_response_export=export_menu.addAction('Respuesta en frecuencia CSV…',self.panel.export_response);self.design_response_export.setEnabled(False)
            send_filter=self.system_actions.reuse;export_filter=self.system_actions.export_button
            root.insertLayout(0,result_bar)
            coefficient_tabs=QTabWidget();self.design_rows={}
            for name,title in [('b','Numerador b'),('a','Denominador a')]:
                model=CoefficientRows(self);model.values=[];self.design_rows[name]=model
                table=QTableView();table.setModel(model);table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers);table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                table.setAccessibleName(title+' del filtro diseñado');coefficient_tabs.addTab(table,title)
            self.result_tabs.addTab(coefficient_tabs,'Coeficientes')
            def designed(system,show_plot=True):
                from .systems_panel import list_text
                for name,model in self.design_rows.items():
                    model.beginResetModel();model.digital=system.domain=='digital';model.values=[list_text([v]) for v in getattr(system,name)];model.endResetModel()
                result_note.show()
                if index!=6:self.design_response_export.setEnabled(self.panel.last_response is not None)
                result_note.setText(f'{system.name} listo · {len(system.b)} coeficientes b · {len(system.a)} coeficientes a')
                self.system_actions.set_result(system,getattr(self.context,'last_system_id',None));self.system_actions.show();send_filter.setEnabled(True);export_filter.setEnabled(True);self.result_tabs.setCurrentIndex(1 if show_plot else self.result_tabs.count()-1)
            self.context.on_design_dirty=lambda: (self.system_actions.setEnabled(False),send_filter.setEnabled(False),export_filter.setEnabled(False),result_note.setText('Diseño modificado: actualizá el sistema para reutilizarlo.'))
            self.context.on_system_designed=designed
            self.context.on_system_loaded=lambda system:designed(system,False)
            if index==6:
                import_button=QPushButton('Cargar sistema…');form.insertRow(0,import_button)
                from .system_import import install_system_import
                from .workspaces import ROUTES
                def receive_design(value,key=None):
                    self.context.parents=[key] if key else [];window.send_system(value,key,ROUTES['systems',6])
                def choose_design():
                    key=window.choose_record('system')
                    if key:receive_design(window.project.get(key),key)
                self.system_import=install_system_import(import_button,window,receive_design,choose_design)
                for button in controls.findChildren(QPushButton):
                    if button.text().strip().rstrip('.…') in ('Guardar filtro','Exportar respuesta CSV','Plano de polos y ceros'):
                        form.removeWidget(button);button.hide();button.setParent(self.panel)
                from .pole_zero_editor import PoleZeroEditor
                from .design_frequency import DesignFrequency
                self.design_frequency=DesignFrequency(window,'digital' if self.panel.domain.currentIndex()==0 else 'analog');self.panel.design_frequency=self.design_frequency
                self.system_actions.reuse_excluded.add(('systems',6))
                frequency_tab=self.result_tabs.addTab(self.design_frequency,'Respuesta en frecuencia');self.result_tabs.setTabText(0,'Plano de diseño')
                self.result_tabs.currentChanged.connect(lambda index:self.design_frequency.open_plot() if index==frequency_tab else None)
                self.pole_editor=PoleZeroEditor(self.panel,self.context);plot_box.insertWidget(0,self.pole_editor)
                from .root_entry import RootEntry
                self.root_entry=RootEntry(self.pole_editor);self.panel.root_entry=self.root_entry
                entry_row,_=form.getWidgetPosition(self.panel.fields['zeros'])
                form.insertRow(entry_row,self.root_entry)
                for key in ('zeros','poles'):form.setRowVisible(self.panel.fields[key],False)
                def ready_roots(system):
                    selected=self.result_tabs.currentWidget();designed(system);self.result_tabs.setCurrentWidget(selected);self.pole_editor.redraw();self.pole_editor.note.setText('Sistema actualizado. Respuesta en frecuencia muestra módulo, fase y retardo; Usar filtro en permite llevarlo a Análisis de sistemas.')
                def dirty_roots():
                    self.system_actions.setEnabled(False);send_filter.setEnabled(False);export_filter.setEnabled(False);result_note.setText('Diseño editado: calculá para usar la nueva definición.')
                    self.design_frequency.mark_dirty()
                def loaded_roots(system):
                    selected=self.result_tabs.currentWidget();designed(system,False);self.result_tabs.setCurrentWidget(selected);self.design_frequency.clear_result(system)
                self.context.on_system_loaded=loaded_roots
                self.context.on_system_designed=ready_roots;self.context.on_design_dirty=dirty_roots
        if kind=='sampling':
            from .tool_guide import ToolGuide
            descriptions={
                0:('Tomá muestras de una expresión continua. Fs determina la separación temporal y N la cantidad de valores.',('Expresión x(t)','Muestrear','Secuencia x[n]')),
                1:('Compará la frecuencia de un tono con Fs para conocer su frecuencia aparente después del muestreo.',('Tono','Muestreo Fs','Alias')),
                2:('Cambiá la cantidad de muestras de una secuencia con el método indicado.',('Secuencia','Cambio de tasa','Nueva secuencia')),
                3:('Estimá valores entre muestras. La reconstrucción usa el registro finito y no recupera información perdida por aliasing.',('Muestras','Interpolación','Señal estimada')),
                4:('Aproximá las amplitudes a niveles discretos y medí el error de cuantización.',('Amplitudes','Cuantizar','Niveles y SNR')),
                5:('Distribuí los bits entre signo, parte entera y fraccionaria para representar un número.',('Número','Formato Q','Valor y error')),
            }
            purpose,stages=descriptions[index];form.insertRow(0,ToolGuide(purpose,stages))
            if index==0:
                form.labelForField(self.panel.rate).setText('Frecuencia de muestreo Fs (muestras/s)')
                timing=QLabel();timing.setWordWrap(True);form.addRow(timing)
                def update_timing(*_):
                    try:
                        rate=real_field(self.panel.rate);count=integer_field(self.panel.count);start=real_field(self.panel.start)
                        if rate<=0 or count<1 or not np.isfinite([rate,start]).all():raise ValueError()
                        end=start+(count-1)/rate
                        if not np.isfinite(end):raise ValueError()
                        timing.setText(f'Intervalo entre muestras: {1/rate:.6g} s.\nPrimera muestra: {start:.6g} s · última: {end:.6g} s.\nEl intervalo entre la primera y la última muestra es (N − 1) / Fs.')
                    except (ValueError,OverflowError):timing.setText('Ingresá Fs positiva, un inicio finito y una cantidad entera de muestras mayor que cero.')
                for field in (self.panel.rate,self.panel.count,self.panel.start):field.textChanged.connect(update_timing)
                update_timing()
            elif index==2:
                rate_note=QLabel();rate_note.setWordWrap(True);form.addRow(rate_note)
                def update_rate_method(*_):
                    down=self.panel.rate_method.currentIndex()==0
                    form.setRowVisible(self.panel.phase,down);form.labelForField(self.panel.factor).setText('Factor de reducción M' if down else 'Factor de expansión L')
                    rate_note.setText('Se conserva una muestra de cada M. La fase elige la primera dentro del bloque. Este método no filtra: para reducir aliasing, usá Cambio racional de tasa con antialias.' if down else 'Se aumenta la tasa por L. Expandir con ceros inserta valores nulos; los métodos de interpolación estiman los valores intermedios.')
                self.panel.rate_method.currentIndexChanged.connect(update_rate_method);update_rate_method()
            elif index==3:
                form.labelForField(self.panel.factor).setText('Puntos por intervalo entre muestras (L)')
                for position,title in enumerate(['Mantener cada valor (ZOH)','Unir con rectas (lineal)','Interpolación SINC']):self.panel.reconstruction.setItemText(position,title)
        if kind=='sampling' and index==0:
            for button in controls.findChildren(QPushButton):
                if button.text().startswith('Leer Fs'):form.setRowVisible(button,False)

        if kind=='sampling' and index==3:
            from .input_clock import bind_clock
            form.insertRow(0,bind_clock(source,self.panel.rate,self.panel.start))
        from .result_state import ResultState
        source_widgets=set(source.findChildren(QWidget)) if source is not None else set()
        tracked=[]
        for field in controls.findChildren(QWidget):
            if field in source_widgets:continue
            if isinstance(field,(QLineEdit,QComboBox,QCheckBox)) or (hasattr(field,'textChanged') and callable(getattr(field,'text',None))):tracked.append(field)
        if kind=='systems' and index==6:tracked=[self.panel.domain,*[self.panel.fields[key] for key in ('zeros','poles','gain')]]
        for action in controls.findChildren(QPushButton):action.setProperty('actionTitle',action.property('actionTitle') or action.text())
        button=next((action for action in controls.findChildren(QPushButton) if action.objectName()=='primary' or action.property('primaryAction')),None)
        if button is not None:
            self.result_state=ResultState(tracked,button,[source] if source is not None else []);self.context.result_state=self.result_state;form.insertRow(0,self.result_state)

    def reuse(self,source):
        result=self.context.result
        if result is None:QMessageBox.information(self,'Sin resultado','Calculá un resultado en esta herramienta o abrí un archivo de entrada.');return
        source.set_source(result)
    def build_basic(self,window,root,operation,input_kind):
        body=QWidget();layout=QHBoxLayout(body);controls=QWidget();box=QVBoxLayout(controls);layout.addWidget(controls,1)
        continuous_input=input_kind in ('continuous','continuous_pair')
        self.first=LocalInput('Entrada x(t)' if continuous_input else 'Entrada x[n]','continuous' if continuous_input else 'discrete' if input_kind=='pair' else input_kind);box.addWidget(self.first)
        if continuous_input:
            note=QLabel('Modelo numérico: interpolación lineal entre puntos y cero fuera del intervalo. Ambas entradas deben tener el mismo paso en segundos.');note.setWordWrap(True);box.insertWidget(0,note)
        self.second=None
        if input_kind in ('pair','continuous_pair'):
            self.second=LocalInput('Entrada h(t)' if continuous_input else 'Entrada h[n]','continuous' if continuous_input else 'discrete');self.second.mode.setCurrentIndex(1);box.addWidget(self.second)
        if operation=='idft':
            self.first.setTitle('Coeficientes del espectro X[k]')
            self.first.samples.setText('1, 1, 1, 1');self.first.mode.setCurrentIndex(1)
            self.first.layout().labelForField(self.first.expression).setText('X[k] · usar n como índice k')
            self.first.layout().labelForField(self.first.samples).setText('X[0], X[1], …, X[N−1]')
            self.first.origin.setText('0');self.first.origin.parentWidget().hide()
            guidance=QLabel('Ingresá los coeficientes en orden desde k = 0. Se admiten complejos, por ejemplo 1+2i. La cantidad ingresada define N. La salida empieza en n = 0 y usa normalización 1/N. También podés copiar un resultado de DFT.');guidance.setWordWrap(True);box.addWidget(guidance)
        self.first.bind_project(window)
        if operation in ('generate','measures'):
            from .choice_buttons import ChoiceButtons
            self.discrete_source=self.first;self.continuous_source=LocalInput('Entrada x(t)','continuous');self.continuous_source.bind_project(window);box.addWidget(self.continuous_source);self.continuous_source.hide()
            self.source_domain=QComboBox();self.source_domain.addItems(['Discreta · x[n]','Continua · x(t)']);self.source_domains=ChoiceButtons(self.source_domain);box.insertWidget(0,self.source_domains)
            def change_source(index):
                self.first=self.discrete_source if index==0 else self.continuous_source
                self.discrete_source.setVisible(index==0);self.continuous_source.setVisible(index==1)
            self.source_domain.currentIndexChanged.connect(change_source)
        if self.second:self.second.bind_project(window)
        self.parameter=QLineEdit('2' if operation=='scale' else '1')
        if operation in ('scale','shift'):box.addWidget(QLabel('Factor de amplitud' if operation=='scale' else 'Desplazamiento k'));box.addWidget(self.parameter)
        button=QPushButton('Calcular');button.setObjectName('primary');box.insertWidget(0,button);box.addStretch()
        result=ResultView();layout.addWidget(result,2)
        from .result_state import ResultState
        tracked=[self.parameter] if operation in ('scale','shift') else []
        sources=[field for field in (self.first,self.second,getattr(self,'continuous_source',None)) if field is not None]
        if hasattr(self,'source_domain'):tracked.append(self.source_domain)
        self.result_state=ResultState(tracked,button,sources);box.insertWidget(1,self.result_state)
        def calculate():
            try:
                x=self.first.read();h=self.second.read() if self.second else None
                parameter=constant_value(self.parameter.text()) if operation=='scale' else integer_field(self.parameter) if operation=='shift' else None
                functions={'continuous_convolve':lambda:continuous.convolution(x,h),'continuous_correlate':lambda:continuous.correlation(x,h),'continuous_normalized':lambda:continuous.correlation(x,h,normalized=True),'continuous_auto':lambda:continuous.correlation(x),'generate':lambda:x,'measures':lambda:ops.finite_measures(x),'shift':lambda:ops.shift(x,parameter),'scale':lambda:ops.scale_amplitude(x,parameter),'reverse':lambda:ops.reverse(x),'parity':lambda:ops.even_odd_parts(x),'convolve':lambda:ops.linear_convolution(x,h),'correlate':lambda:ops.linear_correlation(x,h),'sum':lambda:ops.add_sequences(x,h),'circular':lambda:ops.circular_convolution(x,h),'dft':lambda:ops.dft(x),'idft':lambda:ops.idft(x)}
                parents=[entry.reference_id for entry in (self.first,self.second) if entry and entry.reference_id]
                calculated_inputs=self.result_state.snapshot()
                def accept(value):
                    for part in value if isinstance(value,tuple) else (value,):
                        window.publish(part if isinstance(part,Signal) else asdict(part),title=operation_label(operation) if not isinstance(part,Signal) else None,operation=operation_label(operation),parents=parents)
                    result.show_result(value,source=x,operation=operation);self.result_state.accept(calculated_inputs)
                window._run_operation('Calculando…',functions[operation],accept)
            except Exception as exc:QMessageBox.warning(self,'Revisá los datos',str(exc))
        button.clicked.connect(calculate)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);scroll.setMinimumWidth(300)
        split=QSplitter(Qt.Orientation.Horizontal);split.setChildrenCollapsible(False);split.addWidget(scroll);split.addWidget(result);split.setSizes([350,740]);split.setStretchFactor(1,1);root.addWidget(split,1)

class ToolboxWindow(SignalLabWindow):
    def __init__(self):
        QMainWindow.__init__(self);self.setWindowTitle('SignalLab PC · Herramientas');self.resize(1380,850);self.setMinimumSize(1000,650)
        self.project=Project();self._published_signals={};self._workers=[];self._thread_pool=QThreadPool(self);self._thread_pool.setMaxThreadCount(1);self.pages={};self.category='Inicio'
        configure_theme();root=QWidget();root.setObjectName('appRoot');layout=QHBoxLayout(root);layout.setContentsMargins(0,0,0,0)
        sidebar=QWidget();sidebar.setObjectName('sidebar');sidebar.setFixedWidth(185);nav=QVBoxLayout(sidebar);nav.setContentsMargins(10,14,10,12)
        brand=QLabel('SignalLab.');brand.setObjectName('brand');brand.setStyleSheet('font-size:16pt');brand_row=QHBoxLayout();logo=QLabel();logo.setPixmap(icon('wave','#53cbb6').pixmap(30,30));logo.setAccessibleName('SignalLab');brand_row.addWidget(logo);brand_row.addWidget(brand);nav.addLayout(brand_row);note=QLabel('LABORATORIO');note.setObjectName('eyebrow');nav.addWidget(note);nav.addSpacing(12)
        self.nav=QButtonGroup(self);self.nav.setExclusive(True)
        for category in ['Inicio',*MENUS,'Proyecto','Biblioteca']:
            button=QPushButton(category);button.setIcon(icon({'Inicio':'wave','Señales':'wave','Operaciones':'math','Fourier':'fourier','Filtros y sistemas':'filter','Control':'filter','Muestreo':'sample','Transformadas':'math','Proyecto':'folder','Biblioteca':'book'}.get(category,'wave')));button.setObjectName('navButton');button.setCheckable(True);self.nav.addButton(button);button.setProperty('route',category);button.setText('Resultados' if category=='Proyecto' else category);nav.addWidget(button)
            button.clicked.connect(lambda checked=False,c=category:self.show_menu(c))
            if category=='Inicio':button.setChecked(True)
        nav.addStretch();note=QLabel('Elegí qué querés calcular.\nCada herramienta tiene sus datos.');note.setWordWrap(True);note.setObjectName('muted');nav.addWidget(note);nav.addWidget(QLabel('SignalLab PC · '+__version__.replace('.0.dev0',' dev')));layout.addWidget(sidebar)
        work=QWidget();work.setObjectName('workspace');box=QVBoxLayout(work);box.setContentsMargins(14,12,14,10)
        self.back=QPushButton('← Volver al menú');self.back.clicked.connect(lambda:self.show_menu(self.category));box.addWidget(self.back,0,Qt.AlignmentFlag.AlignLeft)
        self.title=QLabel();self.title.setObjectName('pageTitle');box.addWidget(self.title)
        self.subtitle=QLabel();self.subtitle.setObjectName('muted');self.subtitle.setWordWrap(True);box.addWidget(self.subtitle)
        self.documents=QTabBar();self.documents.setExpanding(False);self.documents.setUsesScrollButtons(True);self.documents.setDocumentMode(True);self.documents.setTabsClosable(True);self.documents.tabCloseRequested.connect(self.close_document);self.documents.currentChanged.connect(self.activate_document);self.documents.tabBarClicked.connect(self.activate_document);box.addWidget(self.documents)
        self.stack=QStackedWidget();box.addWidget(self.stack,1);layout.addWidget(work,1);self.setCentralWidget(root)
        self.cancel_button=QPushButton('Cancelar cálculo');self.cancel_button.clicked.connect(self._cancel_operations);self.cancel_button.hide();self.statusBar().addPermanentWidget(self.cancel_button)
        self.setStyleSheet(STYLE)
        self.tool_menus={}
        start=self.menuBar().addMenu('Inicio');self.tool_menus['Inicio']=start
        start.addAction('Ver todas las herramientas',lambda:self.show_menu('Inicio'))
        find_tool=start.addAction('Buscar herramienta',self.focus_tool_search);find_tool.setShortcut('Ctrl+K')
        for category,items in MENUS.items():
            menu=self.menuBar().addMenu(category);self.tool_menus[category]=menu
            for item in items:
                menu.addAction(item[0],lambda checked=False,it=item:self.open_tool(it))
        self.menu_actions=self.menuBar().actions()
        self.show_menu('Inicio')
    def show_menu(self,category):
        self.category=category
        for button in self.nav.buttons():button.setChecked(button.property('route')==category)
        self.title.setText('Resultados anteriores' if category=='Proyecto' else category);self.subtitle.setText('Elegí una herramienta. Ingresás los datos y obtenés el resultado en su propia pantalla.');self.back.hide()
        key=('menu',category)
        if key not in self.pages:
            if category=='Inicio':page=self.build_home_page()
            elif category=='Proyecto':page=self.build_project_page()
            elif category=='Biblioteca':page=TheoryPanel(self.open_tool)
            else:
                content=QWidget();grid=QGridLayout(content);grid.setContentsMargins(0,20,0,0);grid.setSpacing(16)
                for i,item in enumerate(MENUS[category]):
                    button=QPushButton(item[0]+'  →');button.setObjectName('toolTile');button.setMinimumHeight(48)
                    button.clicked.connect(lambda checked=False,it=item:self.open_tool(it));grid.addWidget(button,2*i,0)
                    description=QLabel(describe_tool(item));description.setWordWrap(True);description.setObjectName('muted');grid.addWidget(description,2*i+1,0)
                grid.setRowStretch(2*len(MENUS[category]),1)
                page=QScrollArea();page.setWidgetResizable(True);page.setWidget(content)
            self.pages[key]=page;self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.pages[key]);self.statusBar().showMessage('Elegí una herramienta para empezar · guardar la sesión es opcional')
    def build_home_page(self):
        page=QWidget();layout=QVBoxLayout(page);layout.setContentsMargins(0,16,0,0)
        heading=QLabel('¿Qué querés hacer?');heading.setObjectName('cardTitle');layout.addWidget(heading)
        note=QLabel('Abrí directamente el cálculo que necesitás. Cada herramienta incluye sus propias entradas.');note.setWordWrap(True);note.setObjectName('muted');layout.addWidget(note)
        search=QLineEdit();self.tool_search=search;search.setPlaceholderText('Buscar herramienta · Ctrl+K · FFT, respuesta temporal, condiciones iniciales…');search.setClearButtonEnabled(True);layout.addWidget(search)
        content=QWidget();grid=QGridLayout(content);grid.setContentsMargins(0,12,0,0);grid.setSpacing(12)
        descriptions={
            'Señales':'Graficar, editar muestras y medir energía',
            'Señales aleatorias':'Generar ruido, medir estadísticas e histogramas',
            'Operaciones':'Convolución, correlación y suma',
            'Fourier':'Espectros, series, DFT y PSD',
            'Filtros y sistemas':'Diseñar filtros y analizar transferencias',
            'Control':'Respuestas, realimentación y espacio de estados',
            'Muestreo':'Muestrear, reconstruir y cuantizar',
            'Transformadas':'Laplace, Z y ecuaciones diferenciales',
        }
        quick_title=QLabel('Accesos directos');quick_title.setObjectName('cardTitle');grid.addWidget(quick_title,0,0,1,2)
        routes=[('systems',9),('course_tools','fft'),('course_tools','fir'),('course_tools','iir'),('systems',6),('correlation',0)]
        for index,route in enumerate(routes):
            item=next(item for items in MENUS.values() for item in items if item[1:3]==route)
            button=QPushButton(item[0]);button.setObjectName('toolTile');button.setMinimumHeight(46);button.setToolTip(describe_tool(item));button.clicked.connect(lambda checked=False,it=item:self.open_tool(it));grid.addWidget(button,1+index//2,index%2)
        categories=QLabel('Todas las áreas');categories.setObjectName('cardTitle');grid.addWidget(categories,4,0,1,2)
        self.home_cards=[]
        for index,(category,description) in enumerate(descriptions.items()):
            button=QPushButton(category+'\n'+description);button.setObjectName('toolTile');button.setMinimumHeight(64)
            button.clicked.connect(lambda checked=False,c=category:self.show_menu(c));grid.addWidget(button,5+index//2,index%2);self.home_cards.append(button)
        grid.setRowStretch(9,1)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(content);layout.addWidget(scroll,1)
        matches=QListWidget();matches.setAccessibleName('Herramientas encontradas');matches.hide();layout.addWidget(matches,1)
        import unicodedata
        def normalized(text):return ''.join(c for c in unicodedata.normalize('NFD',text.casefold()) if not unicodedata.combining(c))
        aliases={('systems',9):'entrada propia condiciones iniciales estado cero entrada cero impulso escalon respuesta natural forzada',('course_tools','fft'):'zero padding relleno con ceros resolucion espectral enventanado fuga leakage kaiser',('course_tools','fir'):'kaiser orden longitud tolerancias ventanas pasabajos pasaaltos pasabanda rechazabanda',('course_tools','iir'):'butterworth tolerancias orden invarianza impulso bilineal',('course_tools','inverse_z'):'roc causal anticausal bilateral estable',('systems',6):'plano z raices diseno mouse raton',('course_tools','gain'):'normalizar amplitud ganancia referencia',('course_tools','phase'):'fase minima paso todo allpass retardo grupo simetria',('interconnection',0):'cascada serie paralelo realimentacion bloques'}
        search_entries=[(category,item,normalized(category+' '+item[0]+' '+describe_tool(item)+' '+aliases.get(item[1:3],''))) for category,items in MENUS.items() for item in items]
        def filter_tools(query):
            query=normalized(query.strip());matches.clear();scroll.setVisible(not query);matches.setVisible(bool(query))
            for category,item,searchable in search_entries:
                if query and all(word in searchable for word in query.split()):
                    matches.addItem(item[0]+'  ·  '+category);matches.item(matches.count()-1).setData(Qt.ItemDataRole.UserRole,item)
            if query and not matches.count():
                matches.addItem('No hay coincidencias. Probá con otro nombre.');matches.item(0).setFlags(Qt.ItemFlag.NoItemFlags)
        def activate(item):
            tool=item.data(Qt.ItemDataRole.UserRole)
            if tool:self.open_tool(tuple(tool))
        search.textChanged.connect(filter_tools);matches.itemClicked.connect(activate);matches.itemActivated.connect(activate)
        search.returnPressed.connect(lambda:activate(matches.item(0)) if matches.count()==1 else matches.setFocus())
        return page

    def focus_tool_search(self):
        self.show_menu('Inicio');self.tool_search.setFocus();self.tool_search.selectAll()

    def close_document(self,index):
        key=self.documents.tabData(index)
        active=key is not None and self.stack.currentWidget() is self.pages.get(tuple(key))
        self.documents.blockSignals(True);self.documents.removeTab(index);self.documents.blockSignals(False)
        if active:
            if self.documents.count():self.activate_document(self.documents.currentIndex())
            else:self.show_menu(self.category)
        self.statusBar().showMessage('Pestaña cerrada. Sus entradas y resultados se conservan en esta sesión.')

    def show_tool_help(self,item):
        self.show_menu("Biblioteca");self.pages[("menu","Biblioteca")].select_tool(item)

    def activate_document(self,index):
        item=self.documents.tabData(index)
        if item:self.open_tool(tuple(item))
    def open_tool(self,item):
        key=tuple(item)
        if key not in self.pages:
            page=ToolPage(self,item);self.pages[key]=page;self.stack.addWidget(page)
            self._configure_readable_layouts()
        self.category=next((category for category,items in MENUS.items() if item in items),self.category)
        for button in self.nav.buttons():button.setChecked(button.property('route')==self.category)
        if not any(self.documents.tabData(i)==tuple(item) for i in range(self.documents.count())):
            self.documents.blockSignals(True);tab=self.documents.addTab(item[0]);self.documents.setTabData(tab,tuple(item));self.documents.blockSignals(False)
        self.documents.blockSignals(True)
        self.documents.setCurrentIndex(next(i for i in range(self.documents.count()) if self.documents.tabData(i)==tuple(item)))
        self.documents.blockSignals(False)
        self.title.setText(item[0]);self.subtitle.setText(describe_tool(item));self.back.setText('← Volver al menú');self.back.show();self.stack.setCurrentWidget(self.pages[key])

    def publish(self,value,*,title=None,operation='',parents=()):
        journal=getattr(self,'_result_journal',None)
        if journal:
            value=journal.enrich(value)
            if isinstance(value,dict) and 'calculated_data' in value:parents=list(dict.fromkeys([*parents,*journal.references,*journal.records]))
        route=getattr(self,'current_operation',None)
        tool=journal.origin if journal else {'title':route[0],'route':list(route)} if route else None
        key=self.project.add(value,title=title,operation=operation,parents=parents,tool=tool)
        if journal:journal.published(key,value)
        if isinstance(value,(Signal,Transfer,StateModel)):
            objects=getattr(self,'_published_values',{})
            self._published_values={identity:entry for identity,entry in objects.items() if entry[0]() is not None}
            self._published_values[id(value)]=(weakref.ref(value),key)
        if isinstance(value,Signal):
            self._published_signals={identity:entry for identity,entry in self._published_signals.items() if entry[0]() is not None}
            self._published_signals[id(value)]=(weakref.ref(value),key)
        if journal is None:self.refresh_project()
        return key
    def published_value_id(self,value):
        entry=getattr(self,'_published_values',{}).get(id(value))
        return entry[1] if entry and entry[0]() is value else None
    def published_signal_id(self,value):
        entry=self._published_signals.get(id(value))
        return entry[1] if entry and entry[0]() is value else None
    def send_signal(self,value,key,item):
        self.open_tool(item)
        if item[1:3] in (('transform_lab','z'),('symbolic',2)):
            if value.domain!='discrete':raise ValueError('La Z finita requiere una secuencia discreta.')
            panel=self.stack.currentWidget().panel;panel.use_finite_input()
            if key is None:key=self.publish(value,operation='Secuencia enviada a Z finita')
            panel.source.set_source(self.project.get(key),key)
            self.statusBar().showMessage('Secuencia cargada en Z directa, conservando todos sus índices.');return
        if item[1]=='frequency_filter':
            panel=self.stack.currentWidget().panel
            if value.domain=='frequency':panel.receive_response(value)
            else:
                panel.domain.setCurrentIndex(0 if value.domain=='discrete' else 1);panel.operation.setCurrentIndex(1)
                (panel.xd if value.domain=='discrete' else panel.xc).set_source(value,key)
            return
        if item[1:3]==('sampling',5):self.stack.currentWidget().panel.study.setCurrentIndex(2)
        if item[1]=='systems' and item[2]==9:
            panel=self.stack.currentWidget().panel
            panel.domain.setCurrentIndex(1 if value.domain=='discrete' else 0)
            panel.stimulus.setCurrentIndex(2)
        active=getattr(self.stack.currentWidget(),'active_page',self.stack.currentWidget())
        fields=[field for field in active.findChildren(LocalInput) if field.kind=='import' or field.kind==value.domain]
        if not fields:return
        target=fields[0]
        if len(fields)>1:
            choices=[field.title() for field in fields]
            chosen,accepted=QInputDialog.getItem(self,'Destino de la señal','Usar como entrada',choices,0,False)
            if not accepted:return
            target=fields[choices.index(chosen)]
        if key is None:key=self.publish(value,operation='Resultado enviado a otra herramienta')
        target.set_source(self.project.get(key),key)
        self.statusBar().showMessage('Señal cargada en '+target.title()+'. Revisá los parámetros y calculá.')
    def export_transfer(self,value):
        from pathlib import Path
        path,_=QFileDialog.getSaveFileName(self,'Exportar sistema calculado','sistema.json','Sistema SignalLab (*.json)')
        if not path:return
        if not Path(path).suffix:path+='.json'
        try:
            write_json(path,value.to_document())
            self.statusBar().showMessage('Sistema calculado exportado: '+path)
        except Exception as exc:QMessageBox.warning(self,'No se pudo exportar',str(exc))

    def send_model(self,value,key,item):
        if not isinstance(value,StateModel) or item[1]!='state_space':raise ValueError('El destino requiere un modelo de estados.')
        if item[2]=='discretize' and value.dt is not None:raise ValueError('Discretizar requiere un modelo continuo.')
        self.open_tool(item);page=self.pages.get(tuple(item),self.stack.currentWidget());panel=page.panel
        if key is None:key=self.publish(value,operation='Modelo enviado a otro estudio')
        panel.set_model(self.project.get(key),key)
        self.statusBar().showMessage('Modelo cargado con su dominio y período. Revisá los datos y calculá en el destino.')
    def send_system(self,value,key,item):
        from .systems_panel import list_text
        self.open_tool(item);page=self.stack.currentWidget();panel=page.panel
        if item[1] in ('course_tools','random_model') or item[1:3]==('sampling',5):
            panel.set_system(value,key)
            self.statusBar().showMessage('Sistema copiado. Revisá los parámetros y calculá.');return
        if item[1]=='interconnection':
            options=['H₁ · Primer bloque / camino directo','H₂ · Segundo bloque / retorno']
            choice,accepted=QInputDialog.getItem(self,'Conectar sistemas','Usar el sistema como',options,0,False)
            if not accepted:return
            if panel.receive(value,key,options.index(choice)):
                self.statusBar().showMessage('Sistema copiado. Completá la conexión y calculá.')
            return
        if item[1:3]==('sampling',5):self.stack.currentWidget().panel.study.setCurrentIndex(2)
        if item[1]=='systems' and item[2]==9:
            panel.set_system(value,key)
        else:
            page.context.ready=False
            try:panel._accept_system(value)
            finally:page.context.ready=True
            page.context.system_id=key
        self.statusBar().showMessage('Filtro copiado a '+item[0]+'. Revisá las entradas y calculá.')

    def choose_record(self,kind,domains=None,**constraints):
        from .project_picker import ProjectPicker
        picker=ProjectPicker(self,kind,domains,**constraints)
        return picker.selected_id if picker.exec() else None
    def build_project_page(self):
        page=QWidget();layout=QVBoxLayout(page)
        note=QLabel('Los resultados de todas las herramientas se guardan aquí al calcular. Seleccioná uno para consultarlo, exportarlo o usarlo en otra herramienta. Las expresiones conservan su fórmula y sus condiciones.');note.setWordWrap(True);layout.addWidget(note)
        from PySide6.QtWidgets import QGridLayout
        bar=QGridLayout()
        self.view_selection=QPushButton('Abrir resultado');self.view_selection.setEnabled(False);self.view_selection.clicked.connect(self.open_selected_signal);bar.addWidget(self.view_selection,0,0)
        self.export_selection_button=QPushButton('Exportar selección…');self.export_selection_button.setEnabled(False);self.export_selection_button.clicked.connect(self.export_selected);bar.addWidget(self.export_selection_button,1,0)
        sessions=QPushButton('Sesión…');session_menu=QMenu(sessions);session_menu.addAction('Guardar sesión…',self.save_project);session_menu.addAction('Abrir sesión…',self.import_project);sessions.setMenu(session_menu);bar.addWidget(sessions,1,1)
        layout.addLayout(bar)
        filters=QHBoxLayout();self.result_search=QLineEdit();self.result_search.setPlaceholderText('Buscar un resultado por nombre u operación…');self.result_search.setClearButtonEnabled(True);filters.addWidget(self.result_search,1)
        self.result_kind=QComboBox()
        for label,kind in [('Todos los tipos',None),('Señales','signal'),('Sistemas','system'),('Modelos de estados','state_space'),('Expresiones','expression'),('Cálculos e informes','calculation')]:self.result_kind.addItem(label,kind)
        filters.addWidget(self.result_kind);layout.addLayout(filters)
        self.result_search.textChanged.connect(self.refresh_project);self.result_kind.currentIndexChanged.connect(self.refresh_project)
        self.result_count=QLabel();self.result_count.setObjectName('muted');layout.addWidget(self.result_count)
        self.reuse_selection=QPushButton('Usar selección en…');self.reuse_selection.setEnabled(False);self.reuse_menu=QMenu(self.reuse_selection);self.reuse_selection.setMenu(self.reuse_menu);self.reuse_menu.aboutToShow.connect(self.prepare_selected_reuse);bar.addWidget(self.reuse_selection,0,1)
        self.include_inputs=QCheckBox('Mostrar también las entradas utilizadas');self.include_inputs.toggled.connect(self.refresh_project);layout.addWidget(self.include_inputs)
        self.project_list=QListWidget();layout.addWidget(self.project_list,2)
        self.result_origin=QLabel();self.result_origin.setWordWrap(True);self.result_origin.setObjectName('muted');layout.addWidget(self.result_origin)
        self.project_details=ReportView();self.project_details.setReadOnly(True);layout.addWidget(self.project_details,1)
        self.project_list.currentRowChanged.connect(self.show_record);self.project_list.itemDoubleClicked.connect(lambda *_:self.open_selected_signal());self.refresh_project();return page
    def refresh_project(self):
        for field in self.findChildren(LocalInput):field.refresh_recent()
        if not hasattr(self,'project_list'):return
        import unicodedata
        def normalized(value):return ''.join(c for c in unicodedata.normalize('NFKD',value.casefold()) if not unicodedata.combining(c))
        previous=getattr(self,'visible_records',[]);row=self.project_list.currentRow()
        selected=previous[row]['id'] if 0<=row<len(previous) else None
        query=normalized(self.result_search.text()).split();kind=self.result_kind.currentData()
        self.project_list.blockSignals(True);self.project_list.clear()
        self.visible_records=[r for r in reversed(self.project.headers())
            if (self.include_inputs.isChecked() or not r['operation'].startswith(('Entrada:','Modelo de entrada:','Entrada de simulación')))
            and (kind is None or r['kind']==kind or kind=='expression' and self.project.expression(r['id']) is not None)
            and all(word in normalized(r['title']+' '+r['operation']) for word in query)]
        for r in self.visible_records:
            label={'signal':'Señal','system':'Sistema','calculation':'Cálculo','state_space':'Espacio de estados'}[r['kind']]
            if self.project.expression(r['id']) is not None:label='Expresión'
            self.project_list.addItem(f"{label} · {r['title']}  —  {operation_label(r['operation'])}")
        index=next((i for i,r in enumerate(self.visible_records) if r['id']==selected),0) if self.visible_records else -1
        self.project_list.setCurrentRow(index);self.project_list.blockSignals(False)
        self.result_count.setText(f'{len(self.visible_records)} resultados · más recientes primero')
        self.show_record(index)
    def show_record(self,index):
        records=self.visible_records
        available=0<=index<len(records);self.export_selection_button.setEnabled(available)
        self.view_selection.setEnabled(available)
        self.reuse_selection.setEnabled(available and (records[index]['kind'] in ('signal','system','state_space') or self.project.expression(records[index]['id']) is not None))
        if not available:
            self.result_origin.clear()
            self.project_details.setPlainText('No hay resultados que coincidan. Cambiá la búsqueda o el tipo seleccionado.' if self.project.headers() else 'Todavía no hay resultados. Abrí una herramienta, ingresá sus datos y calculá; el resultado aparecerá aquí automáticamente.');return
        record=records[index];parents={r['id']:r['title'] for r in self.project.headers()}
        origin=(record.get('tool') or {}).get('title',record['operation'])
        self.result_origin.setText('Origen: '+origin+' · '+str(len(record['parents']))+' resultados vinculados')
        details={'Nombre':record['title'],'Operación':record['operation'],'Herramienta':(record.get('tool') or {}).get('title','No registrada')}
        details['entradas']=[parents[p] for p in record['parents']]
        value=self.project.get(record['id'])
        from .cas_transfer import can_send
        if can_send(value):self.reuse_selection.setEnabled(True)
        if isinstance(value,dict) and 'cas_answer' in value:
            from .library_result_view import show_cas_result
            show_cas_result(self.project_details,value);return
        if isinstance(value,Signal):
            from .result_summary import signal_summary
            self.project_details.set_readable(signal_summary(value,record['operation']));return
        elif isinstance(value,Transfer):
            from .result_summary import transfer_summary
            self.project_details.set_readable(transfer_summary(value));return
        elif isinstance(value,StateModel):
            self.project_details.set_matrices(record['title']+'\n\nOperación: '+record['operation']+'\nDominio: '+('Continuo' if value.dt is None else 'Discreto · T = '+str(value.dt)+' s'),{name:getattr(value,name) for name in ('A','B','C','D')});return
        elif isinstance(value,dict) and isinstance(value.get('report'),str):
            self.project_details.setPlainText(record['title']+'\n\n'+value['report']);return
        else:
            from .result_summary import calculation_summary
            summary=calculation_summary(value)
            if summary is not None:self.project_details.set_readable(summary);return
            details['objeto']=value
        self.project_details.setPlainText(json.dumps(details,ensure_ascii=False,indent=2))
    def open_selected_signal(self):
        row=self.project_list.currentRow()
        if not 0<=row<len(self.visible_records):return
        record=self.visible_records[row]
        if record['kind'] not in ('signal','system','state_space','calculation'):return
        key=('saved_signal_view',record['id'])
        if key not in self.pages:
            source=self.project.get(record['id']);page=QWidget();layout=QVBoxLayout(page);layout.setContentsMargins(0,0,0,0)
            note=QLabel('Resultado conservado · '+record['operation']);note.setWordWrap(True);note.setObjectName('muted');layout.addWidget(note)
            self.pages[key]=page;self.stack.addWidget(page)
            if isinstance(source,Signal):
                viewer=ResultView();layout.addWidget(viewer,1);viewer.show_result(source);viewer.result_ids=[record['id']]
            else:
                report=ReportView();layout.addWidget(report_panel(report),1)
                content=source['report'] if isinstance(source,dict) and isinstance(source.get('report'),str) else json.dumps(source,ensure_ascii=False,indent=2) if isinstance(source,dict) else ''
                from .result_summary import calculation_summary
                if isinstance(source,Transfer):
                    from .result_summary import transfer_summary
                    report.set_readable(transfer_summary(source))
                elif isinstance(source,StateModel):report.set_matrices(source.name,{name:getattr(source,name) for name in ('A','B','C','D')})
                elif isinstance(source,dict) and 'cas_answer' in source:
                    from .library_result_view import show_cas_result
                    show_cas_result(report,source)
                else:
                    summary=calculation_summary(source)
                    if summary is not None:report.set_readable(summary)
                    else:report.setPlainText(record['title']+'\n\n'+content)
        self.category='Proyecto';self.title.setText(record['title']);self.subtitle.setText('Consultá el resultado guardado sin repetir el cálculo. Las señales pueden exportarse y reutilizarse; los informes pueden copiarse o guardarse con formato.')
        self.back.setText('← Volver a Resultados');self.back.show();self.stack.setCurrentWidget(self.pages[key])
        self.statusBar().showMessage('Vista del resultado almacenado; no se generó un cálculo nuevo.')

    def prepare_selected_reuse(self):
        self.reuse_menu.clear();self.reuse_groups=[];self.reuse_actions=[]
        row=self.project_list.currentRow()
        if not 0<=row<len(self.visible_records):return
        key=self.visible_records[row]['id'];value=self.project.get(key)
        from .tool_catalog import compact_destinations,AREA_BY_ID,destination_label
        items=[item for entries in MENUS.values() for item in entries]
        expression=self.project.expression(key)
        if expression is not None:
            from .result_expressions import expression_destinations,send_expression
            for label,destination in expression_destinations(expression):
                def send_expression_action(checked=False,destination=destination):
                    try:send_expression(self,key,destination)
                    except Exception as exc:QMessageBox.warning(self,'No se pudo cargar la expresión',str(exc))
                self.reuse_actions.append(self.reuse_menu.addAction(label,send_expression_action))
            return
        from .cas_transfer import can_send,send_to_cas
        if can_send(value):
            self.reuse_actions.append(self.reuse_menu.addAction('Calculadora CAS',lambda checked=False:send_to_cas(self,key)))
            self.reuse_menu.addSeparator()
        if isinstance(value,Signal):candidates=signal_destinations(value,items)
        elif isinstance(value,Transfer):candidates=system_destinations(value,items)
        elif isinstance(value,StateModel):candidates=[item for item in items if item[1]=='state_space' and (item[2]!='discretize' or value.dt is None)]
        else:candidates=[]
        groups={}
        for entry,item in compact_destinations(candidates):
            area=entry['area']
            if area not in groups:groups[area]=self.reuse_menu.addMenu(AREA_BY_ID[area][1]);self.reuse_groups.append(groups[area])
            def send(checked=False,destination=item):
                if isinstance(value,Signal):self.send_signal(value,key,destination)
                elif isinstance(value,Transfer):self.send_system(value,key,destination)
                else:
                    self.send_model(value,key,destination)
            available={tuple(route[1:3]):route for route in candidates}
            variants=[(available[candidate],labels) for candidate,labels in entry['variants'] if candidate in available]
            if len(variants)>1:
                submenu=groups[area].addMenu(entry['title']);self.reuse_groups.append(submenu)
                for destination,labels in variants:
                    self.reuse_actions.append(submenu.addAction(' · '.join(labels),lambda checked=False,destination=destination,send=send:send(destination=destination)))
            else:self.reuse_actions.append(groups[area].addAction(destination_label(entry,item),send))

    def export_selected(self):
        from pathlib import Path
        records=self.visible_records;index=self.project_list.currentRow()
        if not 0<=index<len(records):return
        record=records[index];value=self.project.get(record['id'])
        path,selected=QFileDialog.getSaveFileName(self,'Exportar resultado seleccionado','resultado','SignalLab JSON (*.json);;Tabla CSV (*.csv)' if isinstance(value,Signal) else 'SignalLab JSON (*.json)')
        if not path:return
        if not Path(path).suffix:path+=('.csv' if 'CSV' in selected else '.json')
        try:
            if isinstance(value,Signal):(save_csv if Path(path).suffix.lower()=='.csv' else save_json)(value,path)
            elif isinstance(value,Transfer):
                write_json(path,value.to_document())
            else:
                self.project.export_record(record['id'],path)
            self.statusBar().showMessage('Resultado exportado: '+path)
        except Exception as exc:QMessageBox.warning(self,'No se pudo exportar',str(exc))
    def save_project(self):
        path,_=QFileDialog.getSaveFileName(self,'Guardar resultados de la sesión','sesion.signallab.json','Sesión SignalLab (*.json)')
        if not path:return False
        try:
            from .signal_editor_panel import SignalEditorPanel
            for editor in self.findChildren(SignalEditorPanel):
                if editor.pending:editor.commit()
            self.project.save(path)
            self.statusBar().showMessage('Resultados de la sesión guardados: '+path)
            return True
        except Exception as exc:
            QMessageBox.warning(self,'No se pudo guardar',str(exc))
            return False
    def import_project(self):
        path,_=QFileDialog.getOpenFileName(self,'Abrir e incorporar sesión','','Sesión SignalLab (*.json)')
        if path:
            try:
                count=self.project.merge(path);self.refresh_project();self.statusBar().showMessage(f'{count} elementos incorporados a esta sesión.')
            except Exception as exc:QMessageBox.warning(self,'No se pudo abrir',str(exc))
    def closeEvent(self,event):
        from .signal_editor_panel import SignalEditorPanel
        if self._workers:
            QMessageBox.information(self,'Cálculo en curso','Cancelá el cálculo y esperá a que termine antes de cerrar.')
            event.ignore();return
        editors=self.findChildren(SignalEditorPanel)
        if self.project.dirty or any(editor.pending for editor in editors):
            answer=QMessageBox.question(self,'Guardar resultados antes de salir','Hay resultados o muestras editadas sin guardar. ¿Querés guardarlos antes de salir?',QMessageBox.StandardButton.Save|QMessageBox.StandardButton.Discard|QMessageBox.StandardButton.Cancel,QMessageBox.StandardButton.Save)
            if answer==QMessageBox.StandardButton.Cancel:
                event.ignore();return
            if answer==QMessageBox.StandardButton.Save:
                if not self.save_project() or self.project.dirty or any(editor.pending for editor in editors):
                    event.ignore();return
        event.accept()
