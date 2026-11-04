from .signal_plot import plot_samples
from .signal_plot import configure_signal_axis, is_discrete_plot
"""Selector de objetos con búsqueda y vista previa antes de reutilizar."""
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLineEdit,QListWidget,QLabel,QPushButton,QSplitter,QWidget,QComboBox
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from .model import Signal
from .filters import Transfer
from .report_view import ReportView
from .reuse_sources import source_info,compatible,temporal_expression

class ProjectPicker(QDialog):
    def __init__(self,window,kind,domains=None,*,variables=None,units=None,allow_advance=True,dft_input=False):
        super().__init__(window);self.project=window.project;self.kind=kind;self.domains=domains;self.selected_id=None;self._has_plot=False;self._narrow=None
        self.constraints=dict(domains=domains,variables=variables,units=units,allow_advance=allow_advance,dft_input=dft_input)
        self.setWindowTitle('Reutilizar un resultado');self.setMinimumSize(540,400)
        available=window.screen().availableGeometry();self.resize(min(960,available.width()-32),min(660,available.height()-48))
        root=QVBoxLayout(self);heading=QLabel({'signal':'Elegí una señal','system_source':'Cargar un sistema o una expresión H','temporal_expression':'Elegí una definición de señal','expression':'Elegí una expresión'}.get(kind,'Elegí un resultado para copiar'));heading.setObjectName('cardTitle');root.addWidget(heading)
        scope=QLabel(self.scope_text(variables,units));scope.setWordWrap(True);scope.setObjectName('muted');root.addWidget(scope)
        self.search=QLineEdit();self.search.setPlaceholderText('Buscar por nombre u operación…');self.search.setClearButtonEnabled(True);root.addWidget(self.search)
        split=QSplitter(Qt.Orientation.Horizontal);self.split=split;split.setChildrenCollapsible(False);root.addWidget(split,1);self.items=QListWidget();self.items.setMinimumSize(160,90);split.addWidget(self.items)
        preview=QWidget();box=QVBoxLayout(preview);split.addWidget(preview);split.setSizes([330,600])
        self.info=ReportView();self.info.setMaximumHeight(185);box.addWidget(self.info)
        self.plot_mode=QComboBox();self.plot_mode.addItems(['Módulo y fase','Parte real e imaginaria']);box.addWidget(self.plot_mode);self.plot_mode.currentIndexChanged.connect(lambda _:self.preview(self.items.currentRow()))
        self.figure=Figure(figsize=(6,3));self.canvas=FigureCanvasQTAgg(self.figure);self.canvas.setMinimumSize(0,150);box.addWidget(self.canvas,1)
        footer=QHBoxLayout();self.note=QLabel('');footer.addWidget(self.note,1);cancel=QPushButton('Cancelar');cancel.clicked.connect(self.reject);footer.addWidget(cancel)
        self.import_button=QPushButton('Importar archivo…');self.import_button.clicked.connect(self.import_file);footer.insertWidget(0,self.import_button)
        self.use=QPushButton('Cargar selección');self.use.setObjectName('primary');self.use.clicked.connect(self.accept_selection);footer.addWidget(self.use);root.addLayout(footer)
        headers=self.project.headers() if kind in ('system_source','temporal_expression','cas_source') else self.project.headers(kind)
        self.records=[];self.descriptions={};self.visible=[]
        for record in reversed(headers):
            info=source_info(self.project,record['id'],kind)
            if compatible(info,**self.constraints):self.records.append(record);self.descriptions[record['id']]=info
        self.search.textChanged.connect(self.filter);self.items.currentRowChanged.connect(self.preview);self.items.itemDoubleClicked.connect(lambda _:self.accept_selection());self.filter('')
    def import_file(self):
        from PySide6.QtWidgets import QMessageBox
        try:
            from .data_import import load_results
            key=load_results(self,self.kind,self.constraints)
            if not key:return
            self.selected_id=key;self.accept()
        except Exception as exc:QMessageBox.warning(self,'No se pudo importar',str(exc))
    def filter(self,text):
        import unicodedata
        norm=lambda s:''.join(c for c in unicodedata.normalize('NFKD',s.casefold()) if not unicodedata.combining(c))
        query=norm(text).split();selected=self.selected_id;self.items.blockSignals(True);self.items.clear();self.visible=[]
        for record in self.records:
            details=self.descriptions[record['id']];label=details.get('label','')
            if not all(word in norm(record['title']+' '+record['operation']+' '+label) for word in query):continue
            # Evitar copiar vectores al filtrar: los dominios se consultan en los metadatos de la instantánea.
            self.visible.append(record)
            suffix=f" · {details['count']:,} valores" if 'count' in details else ''
            self.items.addItem(record['title']+suffix+'\n'+(label+' · ' if label else '')+record['operation'])
        self.items.blockSignals(False);self.note.setText(f'{len(self.visible)} disponibles · más recientes primero');self.use.setEnabled(bool(self.visible))
        if self.visible:self.items.setCurrentRow(next((i for i,r in enumerate(self.visible) if r['id']==selected),0))
        else:self.preview(-1)
    def preview(self,row):
        self.selected_id=None;self.figure.clear();self._has_plot=False;self.use.setEnabled(0<=row<len(self.visible))
        if not 0<=row<len(self.visible):self.info.setPlainText('No hay resultados compatibles con esta búsqueda. Podés cargar datos propios en la herramienta.');self.adapt();return
        record=self.visible[row];self.selected_id=record['id'];value=self.project.get(self.selected_id)
        if self.kind=='temporal_expression':
            from .result_summary import Summary,Section,Formula
            expression=temporal_expression(self.project,self.selected_id);text=expression.numerical_source or expression.source
            self.info.set_readable(Summary('Definición de señal',[Section('Expresión',formulas=[Formula(text,text)]),Section('Condiciones y procedencia',paragraphs=list(expression.conditions))]));self.adapt();return
        if isinstance(value,Signal):
            self._has_plot=True
            domain={'discrete':'Secuencia discreta','continuous':'Tiempo continuo','frequency':'Espectro'}.get(value.domain,value.domain)
            self.info.setPlainText(f"{value.name}\n\n{value.values.size:,} muestras · {domain}\nOrigen {value.origin} · Paso {value.step} {value.units}")
            self.info.setMaximumHeight(185);self.plot_mode.show()
            axes=self.figure.subplots(2,1,sharex=True)
            from .ui import SignalLabWindow
            indices=SignalLabWindow._plot_indices(value.values)
            values=value.values[indices];polar=self.plot_mode.currentIndex()==0
            phase=np.full(values.size,np.nan);valid=np.abs(values)>0;phase[valid]=np.angle(values[valid])
            series=(np.abs(values),phase) if polar else (values.real,values.imag)
            labels=('Módulo','Fase (rad)') if polar else ('Real','Imaginaria')
            discrete=is_discrete_plot(value)
            for axis,data,label in zip(axes,series,labels):
                plot_samples(axis,value.axis[indices],data,label=label,discrete=discrete);axis.set_ylabel(label);axis.grid(alpha=.2)
            configure_signal_axis(axes[1],value)
            from .plot_view import prepare_figure
            prepare_figure(self.figure);self.canvas.show()
        else:
            self.plot_mode.hide()
            from .project import encode
            import json
            self.info.setMaximumHeight(16777215);self.canvas.hide()
            from .state_space import StateModel
            if isinstance(value,Transfer):
                from .result_summary import transfer_summary
                self.info.set_readable(transfer_summary(value))
            elif isinstance(value,StateModel):
                self.info.set_matrices(value.name+'\n'+('Continuo' if value.dt is None else 'Discreto · T = '+str(value.dt)+' s'),{name:getattr(value,name) for name in ('A','B','C','D')})
            elif isinstance(value,dict) and 'cas_answer' in value:
                from .library_result_view import show_cas_result
                show_cas_result(self.info,value)
            else:
                from .result_summary import calculation_summary
                summary=calculation_summary(value)
                if summary is not None:self.info.set_readable(summary)
                else:self.info.setPlainText(record['title']+'\n\n'+json.dumps(encode(value)[1],ensure_ascii=False,indent=2))
        self.adapt();self.canvas.draw_idle()
    def scope_text(self,variables,units):
        if self.kind=='system_source':
            domain='H(s) · continuo' if self.domains==['analog'] else 'H(z) · discreto' if self.domains==['digital'] else 'H(s) o H(z)'
            return domain+'. Las expresiones se interpretan como transferencias racionales con coeficientes numéricos. La carga no calcula el análisis.'
        if self.kind=='temporal_expression':return 'Se copia x(t) o x[n] con sus condiciones. En un informe de medidas se reutiliza la señal de entrada.'
        if variables is not None:return 'Expresiones en '+', '.join(v for v in variables if v is not None)+(' · '+', '.join(units) if units else '')+'. También se admiten constantes. Las condiciones acompañan a la expresión.'
        return 'Los datos se copian a esta herramienta. El resultado original se conserva; revisá las opciones y calculá.'
    def adapt(self):
        if not hasattr(self,'canvas'):return
        narrow=self.width()<760
        if narrow!=self._narrow:
            self._narrow=narrow;self.split.setOrientation(Qt.Orientation.Vertical if narrow else Qt.Orientation.Horizontal);self.split.setSizes([110,350] if narrow else [330,600])
        show_plot=self._has_plot and not narrow and self.height()>=580
        self.plot_mode.setVisible(show_plot);self.canvas.setVisible(show_plot);self.info.setMaximumHeight(185 if show_plot else 16777215)
    def resizeEvent(self,event):
        super().resizeEvent(event);self.adapt()
    def accept_selection(self):
        if self.selected_id:self.accept()
