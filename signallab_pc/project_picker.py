"""Selector de objetos con búsqueda y vista previa antes de reutilizar."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog,QVBoxLayout,QLineEdit,QListWidget,QLabel,QPushButton,QSplitter
from .active_stack import ActiveStack
from .model import Signal
from .filters import Transfer
from .report_view import ReportView
from .reuse_sources import source_info,compatible,temporal_expression
from .wrapping_row import WrappingRow

class ProjectPicker(QDialog):
    def __init__(self,window,kind,domains=None,*,variables=None,units=None,allow_advance=True,dft_input=False,data_kinds=None,cross_domain_kinds=()):
        super().__init__(window);self.project=window.project;self.kind=kind;self.domains=domains;self.selected_id=None;self._narrow=None
        self.constraints=dict(domains=domains,variables=variables,units=units,allow_advance=allow_advance,dft_input=dft_input,data_kinds=data_kinds,cross_domain_kinds=cross_domain_kinds)
        self.setWindowTitle('Reutilizar un resultado');self.setMinimumSize(540,400)
        available=window.screen().availableGeometry();self.resize(min(960,available.width()-32),min(660,available.height()-48))
        root=QVBoxLayout(self);heading=QLabel({'signal':'Elegí una señal','system_source':'Cargar un sistema o una expresión H','temporal_expression':'Elegí una definición de señal','expression':'Elegí una expresión'}.get(kind,'Elegí un resultado para copiar'));heading.setObjectName('cardTitle');root.addWidget(heading)
        scope=QLabel(self.scope_text(variables,units));scope.setWordWrap(True);scope.setObjectName('muted');root.addWidget(scope)
        self.search=QLineEdit();self.search.setPlaceholderText('Buscar por nombre u operación…');self.search.setAccessibleName('Buscar resultados');self.search.setClearButtonEnabled(True);root.addWidget(self.search)
        split=QSplitter(Qt.Orientation.Horizontal);self.split=split;split.setChildrenCollapsible(False);root.addWidget(split,1);self.items=QListWidget();self.items.setMinimumSize(160,90);split.addWidget(self.items)
        self.preview_stack=ActiveStack();split.addWidget(self.preview_stack);split.setSizes([330,600])
        self.info=ReportView();self.preview_stack.addWidget(self.info);self.signal_preview=None
        footer=WrappingRow();self.note=QLabel('');cancel=QPushButton('Cancelar');cancel.clicked.connect(self.reject)
        self.import_button=QPushButton('Importar archivo…');self.import_button.clicked.connect(self.import_file)
        self.use=QPushButton('Cargar selección');self.use.setObjectName('primary');self.use.setDefault(True);self.use.clicked.connect(self.accept_selection)
        for widget in (self.use,cancel,self.import_button,self.note):footer.flow.addWidget(widget)
        root.addWidget(footer)
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
        self.items.blockSignals(False)
        count=len(self.visible)
        self.note.setText('1 resultado disponible' if count==1 else f'{count} resultados disponibles')
        self.use.setEnabled(bool(count))
        if self.visible:self.items.setCurrentRow(next((i for i,r in enumerate(self.visible) if r['id']==selected),0))
        else:self.preview(-1)
    def preview(self,row):
        self.selected_id=None;self.use.setEnabled(0<=row<len(self.visible))
        if not 0<=row<len(self.visible):
            self.preview_stack.setCurrentWidget(self.info)
            self.info.setPlainText('No hay resultados compatibles con esta búsqueda.')
            return
        record=self.visible[row];self.selected_id=record['id'];value=self.project.get(self.selected_id)
        if self.kind=='temporal_expression':
            self.preview_stack.setCurrentWidget(self.info)
            from .result_summary import Summary,Section,Formula
            expression=temporal_expression(self.project,self.selected_id);text=expression.numerical_source or expression.source
            self.info.set_readable(Summary('Definición de señal',[Section('Expresión',formulas=[Formula(text,text)]),Section('Condiciones y procedencia',paragraphs=list(expression.conditions))]));return
        if isinstance(value,Signal):
            if self.signal_preview is None:
                from .signal_inspector import SignalInspector
                self.signal_preview=SignalInspector()
                self.preview_stack.addWidget(self.signal_preview)
            self.signal_preview.set_signal(value, record['operation'])
            self.preview_stack.setCurrentWidget(self.signal_preview)
        else:
            self.preview_stack.setCurrentWidget(self.info)
            from .project import encode
            import json
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
    def scope_text(self,variables,units):
        if self.kind=='system_source':
            domain='H(s) · continuo' if self.domains==['analog'] else 'H(z) · discreto' if self.domains==['digital'] else 'H(s) o H(z)'
            return domain+'. Las expresiones se interpretan como transferencias racionales con coeficientes numéricos. La carga no calcula el análisis.'
        if self.kind=='temporal_expression':return 'Se copia x(t) o x[n] con sus condiciones. En un informe de medidas se reutiliza la señal de entrada.'
        if variables is not None:return 'Expresiones en '+', '.join(v for v in variables if v is not None)+(' · '+', '.join(units) if units else '')+'. También se admiten constantes. Las condiciones acompañan a la expresión.'
        if self.kind=='signal':
            return 'Revisá el eje y los valores antes de cargar una entrada.'
        return 'Elegí el resultado que querés usar en esta herramienta.'
    def adapt(self):
        if not hasattr(self,'split'):return
        narrow=self.width()<760
        if narrow!=self._narrow:
            self._narrow=narrow;self.split.setOrientation(Qt.Orientation.Vertical if narrow else Qt.Orientation.Horizontal);self.split.setSizes([110,350] if narrow else [330,600])
    def resizeEvent(self,event):
        super().resizeEvent(event);self.adapt()
    def accept_selection(self):
        if self.selected_id:self.accept()
