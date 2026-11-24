"""An independent, sequential mathematical worksheet in the existing desktop."""
import ast,html,re
from PySide6.QtCore import Qt,Signal,QTimer,QUrl
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QLabel,QPlainTextEdit,QComboBox,QPushButton,
    QMenu,QTreeWidget,QTreeWidgetItem,QMessageBox,QApplication,QDialog,QLineEdit,QWidgetAction,QHBoxLayout)
from .vector_math import render_latex
from .report_view import ReportView
from .theme_tokens import COLORS as C
from .symbolic_process import run_request
from .jobs import OperationCancelled
from .cas_reference import CAS_ROUTE


def math_formula(latex,size=17):
    if len(latex)>1600:raise ValueError('Vista matemática extensa')
    return render_latex(latex,size=size,color=C['text'])



class CasInput(QPlainTextEdit):
    evaluateRequested=Signal();historyRequested=Signal(int)
    def keyPressEvent(self,event):
        if event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter) and not event.modifiers()&Qt.KeyboardModifier.ShiftModifier:
            self.evaluateRequested.emit();event.accept();return
        if event.modifiers()&Qt.KeyboardModifier.ControlModifier and event.key() in (Qt.Key.Key_Up,Qt.Key.Key_Down):
            self.historyRequested.emit(-1 if event.key()==Qt.Key.Key_Up else 1);event.accept();return
        super().keyPressEvent(event)


class CasWorksheet(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window;self.state=self._empty();self.entries=[];self.pending=None;self.selected=None
        self.commands=[];self.command_position=0;self.draft='';self._submitting=False;self._serial=0;self._automatic_reference=None;self.math_size=17;self.formula_dialogs=[]
        root=QVBoxLayout(self);root.setContentsMargins(10,8,10,8);root.setSpacing(6)
        from .wrapping_row import WrappingRow
        self.command_dialog = None
        button=QPushButton('Operar resultado');menu=QMenu(button);button.setMenu(menu);self.result_tools=button
        self.result_operations=[]
        for title,command in [('Simplificar resultado','simplify'),('Desarrollar resultado','expand'),('Factorizar resultado','factor'),('Fracciones parciales del resultado','apart'),('Aproximar resultado','approx')]:
            self.result_operations.append(menu.addAction(title,lambda checked=False,key=command:self.operate_result(key)))
        precision=QWidgetAction(menu);precision_row=QWidget();precision_layout=QHBoxLayout(precision_row);precision_layout.addWidget(QLabel('Cifras significativas'))
        self.result_digits=QLineEdit('15');self.result_digits.setAccessibleName('Cifras significativas');self.result_digits.setMaximumWidth(100);self.result_digits.setToolTip('Precisión de Aproximar resultado; no es la cantidad de decimales después de la coma.')
        settings=getattr(window,'settings',None)
        if settings is not None:
            self.result_digits.setText(str(settings.value('cas/result_digits','15')));self.result_digits.editingFinished.connect(lambda:settings.setValue('cas/result_digits',self.result_digits.text()))
        precision_layout.addWidget(self.result_digits);precision.setDefaultWidget(precision_row);menu.addAction(precision);menu.addSeparator()
        menu.addAction('Insertar referencia rN',self.insert_reference)
        sheet=QPushButton('Opciones de hoja');menu=QMenu(sheet);sheet.setMenu(menu)
        self.variables_button=menu.addAction('Variables y supuestos…',lambda:self.variables_dialog.show());menu.addSeparator()
        menu.addAction('Aumentar tamaño de fórmulas',lambda:self.change_math_size(2));menu.addAction('Reducir tamaño de fórmulas',lambda:self.change_math_size(-2));menu.addSeparator();self.new_button=menu.addAction('Nueva hoja…',self.new_sheet)
        self.variables_dialog=QDialog(self);self.variables_dialog.setWindowTitle('Variables y supuestos · CAS');self.variables_dialog.resize(520,250);self.variables_dialog.setMinimumSize(300,150)
        variable_layout=QVBoxLayout(self.variables_dialog);self.variables=QTreeWidget();self.variables.setColumnCount(2);self.variables.setHeaderLabels(['Nombre','Valor / definición']);self.variables.setRootIsDecorated(False);variable_layout.addWidget(self.variables)
        self.variables.itemDoubleClicked.connect(lambda item,*_:self.input.insertPlainText(item.text(0)))
        self.report=ReportView();self.report.anchorClicked.connect(self.follow_link)
        self.selection_note=QLabel();self.selection_note.setObjectName('muted');self.selection_note.setWordWrap(True)
        self.input=CasInput();self.input.setObjectName('casInput');self.input.setPlaceholderText('Expresión o comando matemático');self.input.setAccessibleName('Expresión o comando CAS');self.input.setMinimumHeight(120);self.input.setMaximumHeight(220)
        self.input.evaluateRequested.connect(self.calculate);self.input.historyRequested.connect(self.recall)
        hint=QLabel('Enter evalúa · Mayús+Enter agrega una línea · Ctrl+↑/↓ recorre entradas');hint.setObjectName('muted');hint.setWordWrap(True)
        load=QPushButton('Cargar resultado…');load.clicked.connect(self.choose_source)
        self.command_button=QPushButton('Comandos…');self.command_button.clicked.connect(self.open_commands)
        self.calculate_button=QPushButton('Evaluar');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate)
        controls=QWidget();left=QVBoxLayout(controls);left.setContentsMargins(0,0,0,0);left.setSpacing(12)
        input_actions=WrappingRow();input_actions.flow.addWidget(self.command_button);input_actions.flow.addWidget(load)
        left.addWidget(input_actions);left.addWidget(self.input);left.addWidget(hint);left.addWidget(self.calculate_button);left.addStretch()
        output=QWidget();right=QVBoxLayout(output);right.setContentsMargins(0,0,0,0);right.setSpacing(10)
        from .result_toolbar import ResultActionBar
        self.result_actions=ResultActionBar();right.addWidget(self.result_actions)
        self.enlarge_result=QPushButton('Ampliar fórmula');self.enlarge_result.setToolTip('Ver el resultado seleccionado en una ventana independiente.');self.enlarge_result.clicked.connect(self.show_result);self.result_actions.add_action(self.enlarge_result,'graph')
        self.reuse_result=QPushButton('Usar expresión en…');reuse=QMenu(self.reuse_result);self.reuse_result.setMenu(reuse)
        for title,destination in [('Señal continua','continuous'),('Secuencia discreta','discrete'),('Análisis de H(s)','analog'),('Análisis de H(z)','digital'),('Respuesta en frecuencia H(ω)','frequency')]:reuse.addAction(title,lambda checked=False,key=destination:self.send_result(key))
        self.result_actions.add_action(self.reuse_result,'reuse')
        export=QPushButton('Exportar hoja…');export_menu=QMenu(export);export.setMenu(export_menu);export_menu.addAction('Copiar texto de la hoja',lambda:QApplication.clipboard().setText(self.report.toPlainText()));export_menu.addAction('Hoja con formato (HTML)…',lambda:self.report.export_document(True));export_menu.addAction('Texto completo…',lambda:self.report.export_document(False));self.result_actions.add_action(export,'export')
        self.export_sheet=export
        self.result_actions.add_action(self.result_tools,'cas');self.copy_result_button=QPushButton('Copiar expresión');self.copy_result_button.clicked.connect(self.copy_result);self.result_actions.add_action(self.copy_result_button)
        self.result_actions.add_action(sheet)
        self.history = QComboBox()
        self.history.setAccessibleName('Ir a un cálculo de la hoja CAS')
        self.history.activated.connect(self.jump_to_cell)
        right.addWidget(self.history)
        right.addWidget(self.selection_note);self.report.setMinimumHeight(136);right.addWidget(self.report,1)
        from .tool_workspace import ToolWorkspace
        self.workspace=ToolWorkspace(controls,output,self,titles=('Expresión','Hoja CAS'),captions=('Ingresá una expresión o insertá un comando.','Resultados exactos y condiciones de cada cálculo.'));root.setContentsMargins(0,0,0,0);root.addWidget(self.workspace)
        self.timer=QTimer(self);self.timer.setInterval(200);self.timer.timeout.connect(self.check_pending);self.timer.start();self.render()

    def open_commands(self):
        if self.command_dialog is None:
            from .cas_commands import CasCommandDialog
            library = getattr(self.window, 'show_function_help', None)
            help_callback = (lambda: library('reference:cas-arguments')) if library is not None else None
            self.command_dialog = CasCommandDialog(self, self.insert_template, help_callback)
        self.command_dialog.open()

    def choose_source(self):
        if not self._ready():return
        key=self.window.choose_record('cas_source')
        if key:
            from .cas_transfer import send_to_cas
            send_to_cas(self.window,key)

    @staticmethod
    def _empty():return {'version':1,'variables':{},'functions':{},'results':{},'ans':None,'assumptions':{}}

    def insert_template(self,template):
        cursor = self.input.textCursor()
        selection = cursor.selectedText().replace('\u2029', '\n')
        if selection and 'expr' in template:
            cursor.insertText(template.replace('expr', selection, 1))
            self.input.setTextCursor(cursor)
            self.input.setFocus()
            return
        value=selection or self.input.toPlainText().strip()
        if not value and self.selected_entry() is not None and 'expr' in template:
            value='r'+str(self.selected);symbols=self.selected_entry()['answer'].get('symbols',[])
            if len(symbols)==1:template=re.sub(r'\bx\b',symbols[0],template)
        if 'expr' in template and value:template=template.replace('expr',value,1)
        self.input.setPlainText(template);cursor=self.input.textCursor()
        marker=re.search(r'\b(expr|ecuacion1|a)\b',template)
        if marker:
            cursor.setPosition(marker.start());cursor.setPosition(marker.end(),QTextCursor.MoveMode.KeepAnchor)
        else:cursor.movePosition(QTextCursor.MoveOperation.End)
        self.input.setTextCursor(cursor)
        self.input.setFocus()

    def _ready(self):
        if self.pending is not None or getattr(self.window,'_workers',[]):
            self.window.statusBar().showMessage('Esperá o cancelá el cálculo actual antes de evaluar otra entrada.');return False
        return True
    def _parents(self,source):
        cells={int(v) for v in re.findall(r'\br([0-9]+)\b',source)}
        if re.search(r'\bans\b',source) and self.state.get('ans') is not None:cells.add(self.state['ans'])
        parents=[entry['result_id'] for entry in self.entries if entry['cell'] in cells and entry.get('result_id')]
        origin=getattr(self,'_library_source',None)
        if origin and origin[0]==source and origin[1]:parents.append(origin[1])
        return list(dict.fromkeys(parents))
    def calculate(self):
        source=self.input.toPlainText().strip()
        if not source:self.input.setFocus();return
        if not self._ready():return
        self._automatic_reference=None
        parents=self._parents(source)
        self.commands.append(source);self.command_position=len(self.commands);self.draft='';self.input.clear()
        self._submit({'operation':'cas_worksheet','source':source},source,parents)
    def operate_result(self,command):
        if command not in ('simplify','expand','factor','apart','approx'):return
        entry=self.selected_entry()
        if entry is None or not self._ready():return
        reference='r'+str(entry['cell']);argument=reference
        if command=='approx':
            from .numeric_input import integer_field
            try:digits=integer_field(self.result_digits,minimum=1)
            except ValueError as exc:QMessageBox.information(self,'Precisión numérica',str(exc));return
            argument+=','+str(digits)
        elif command=='apart':
            answer=entry['answer']
            if not answer.get('expression'):
                QMessageBox.information(self,'Fracciones parciales','Elegí una expresión escalar.');return
            symbols=sorted(set(answer.get('symbols',[])))
            if len(symbols)>1:
                from PySide6.QtWidgets import QInputDialog
                variable,ok=QInputDialog.getItem(self,'Fracciones parciales','Variable de la descomposición:',symbols,0,False)
                if not ok:return
            else:variable=symbols[0] if symbols else 'x'
            argument+=','+variable
        source=command+'('+argument+')';self._automatic_reference=None
        self.commands.append(source);self.command_position=len(self.commands)
        self._submit({'operation':'cas_worksheet','source':source},source,self._parents(source))

    def import_result(self,payload,title,parent=None,*,on_loaded=None):
        if not self._ready():return
        self._submit({'operation':'cas_import','payload':payload},'Desde Resultados: '+title,[parent] if parent else [],imported=True,on_loaded=on_loaded)
    def _submit(self,request,source,parents,imported=False,on_loaded=None):
        self._serial+=1;cell=self._serial;entry={'cell':cell,'source':source,'status':'pending','imported':imported};self.entries.append(entry);self.pending=entry
        self.render();self._submitting=True;request.update(state=self.state,cell=cell)
        def compute():
            try:return run_request(request)
            except OperationCancelled:raise
            except Exception as exc:return {'error':str(exc)}
        def accept(answer):
            self.pending=None
            if 'error' in answer:entry.update(status='error',error=answer['error'])
            else:
                self.state=answer.pop('state');entry.update(status='done',answer=answer);self.selected=cell
                saved={name:answer[name] for name in ('text','presentation','notices','expression','symbols','assumptions','calculation_notes','provenance','frequency_units','frequency_condition','coordinate_variable','origin_conditions','context_rewrite','system_context','domain_condition','domain_symbols','domain_condition_implicit','domain_condition_analysis') if name in answer}
                saved['encoded_value']=self.state['results'][str(cell)]
                entry['result_id']=self.window.publish({'cas_answer':saved,'source':source},title='CAS · '+source,operation='Resultado CAS',parents=parents)
                self.variables.clear()
                for name,value in answer['variables']+answer['functions']+[(name,'Supuesto: '+description) for name,description in answer.get('assumptions',[])]:
                    node=QTreeWidgetItem([name,value[:200]]);node.setToolTip(1,value);self.variables.addTopLevelItem(node)
                self.variables.resizeColumnToContents(0)
                if imported:
                    current=self.input.toPlainText().strip()
                    if not current or current==self._automatic_reference:
                        self._automatic_reference='r'+str(cell)
                        self.input.setPlainText(self._automatic_reference)
                    self.window.statusBar().showMessage('Resultado disponible en CAS como r'+str(cell)+'. Podés usar simplify, factor, expand o cualquier otra operación de la hoja.')
                    if on_loaded is not None:on_loaded(cell)
            self.render()
            if self.workspace.compact:
                self.workspace.show_results()
                self.report.setFocus()
            else:
                self.input.setFocus()
        try:self.window._run_operation('Importando resultado al CAS…' if imported else 'Calculando en la hoja CAS…',compute,accept)
        finally:self._submitting=False

    def check_pending(self):
        busy=self.pending is not None;self.new_button.setEnabled(not busy)
        if busy and not self._submitting and not getattr(self.window,'_workers',[]):
            self.pending.update(status='error',error='Cálculo detenido. Se conservan las variables y el último resultado válido.');self.pending=None;self.render()

    def recall(self,direction):
        if not self.commands:return
        if self.command_position==len(self.commands):self.draft=self.input.toPlainText()
        self.command_position=max(0,min(len(self.commands),self.command_position+direction))
        self.input.setPlainText(self.draft if self.command_position==len(self.commands) else self.commands[self.command_position]);self.input.moveCursor(QTextCursor.MoveOperation.End)

    def follow_link(self,url):
        if url.scheme() not in ('cas-input','cas-result','cas-view') or not url.path().isdigit():return
        cell=int(url.path());entry=next((item for item in self.entries if item['cell']==cell),None)
        if entry is None:return
        if url.scheme()=='cas-input':self.input.setPlainText('r'+str(cell) if entry.get('imported') and entry['status']=='done' else entry['source']);self.focus_input()
        elif url.scheme()=='cas-view':self.selected=cell;self.update_selection();self.show_result()
        elif url.scheme()=='cas-result':self.selected=cell;self.update_selection();self.insert_reference()

    def jump_to_cell(self, index):
        cell = self.history.itemData(index)
        if cell is None:
            return
        entry = next((entry for entry in self.entries if entry['cell'] == cell), None)
        if entry is not None:
            self.selected = cell if entry['status'] == 'done' else None
            self.update_selection()
            self.history.setCurrentIndex(index)
            self.report.scrollToAnchor(f'cas-cell-{cell}')

    def update_selection(self):
        for action in self.result_operations:action.setEnabled(self.selected_entry() is not None and self.pending is None)
        if hasattr(self,'result_actions'):
            entry=self.selected_entry();ready=entry is not None and self.pending is None
            self.enlarge_result.setEnabled(ready);self.copy_result_button.setEnabled(ready);self.result_tools.setEnabled(ready);self.reuse_result.setEnabled(ready and bool(entry['answer'].get('expression')));self.export_sheet.setEnabled(bool(self.entries))
        self.selection_note.setText('Cálculo exacto · radianes · '+(str(len(self.state.get('assumptions',{})))+' símbolos con supuestos' if self.state.get('assumptions') else 'sin supuestos declarados')+(' · Seleccionado r'+str(self.selected) if self.selected_entry() is not None else ''))
        index = self.history.findData(self.selected)
        self.history.setCurrentIndex(max(0, index))

    def selected_entry(self):
        return next((item for item in self.entries if item['cell']==self.selected and item['status']=='done'),None)

    def copy_result(self):
        entry=self.selected_entry()
        if entry:QApplication.clipboard().setText(entry['answer']['text'])

    def insert_reference(self):
        if self.selected_entry():self.input.insertPlainText('r'+str(self.selected));self.focus_input()
    def focus_input(self):
        self.workspace.show_inputs()
        self.input.setFocus()

    def render(self,scroll=True):
        bar=self.report.verticalScrollBar();fraction=bar.value()/max(1,bar.maximum())
        parts=[];raw=[];width=max(180,self.report.viewport().width()-70)
        if not self.entries:parts=['<p>Las expresiones que evalúes y sus resultados aparecerán en esta hoja.</p>']
        for entry in self.entries:
            cell=entry['cell'];source=entry['source'];raw.append(f'Entrada {cell}: '+source)
            parts.append(f'<table width="100%" cellspacing="0" cellpadding="5"><tr><td width="55" valign="top"><a name="cas-cell-{cell}"></a><a href="cas-input:{cell}" title="Editar entrada">[{cell}]</a></td><td style="font-family:Consolas">'+self.wrapped(source)+'</td></tr>')
            if entry['status']=='pending':parts.append('<tr><td></td><td style="color:'+C['muted']+'">Calculando…</td></tr></table>');continue
            if entry['status']=='error':parts.append('<tr><td></td><td style="color:'+C['amber']+'">'+html.escape(entry['error'])+'</td></tr></table>');raw.append('No aplicado: '+entry['error']);continue
            answer=entry['answer'];parts.append(f'<tr><td valign="top"><a href="cas-result:{cell}" title="Reutilizar resultado">r{cell}</a></td><td>'+self.present(answer['presentation'],width-65)+f'<p><a href="cas-view:{cell}">Ampliar resultado</a></p></td></tr>')
            for notice in answer['notices']:
                if not notice.startswith('Definición guardada:'):parts.append('<tr><td></td><td style="color:'+C['muted']+'">'+html.escape(notice)+'</td></tr>')
            parts.append('</table><p style="margin:0;color:'+C['rule']+'">────────────────────────</p>')
            raw.append('r'+str(cell)+' = '+answer['text']);raw.extend(answer['notices'])
        self.report.setHtml('<html><head><style>p {margin-top:2px;margin-bottom:2px;line-height:120%;}</style></head><body style="margin:10px">'+''.join(parts)+'</body></html>');self.report._raw='\n\n'.join(raw)
        self.history.clear()
        self.history.addItem('Ir a un cálculo…')
        for entry in reversed(self.entries):
            cell = entry['cell']
            source = ' '.join(entry['source'].split())
            label = f'r{cell}' if entry['status'] == 'done' else f'Entrada {cell}'
            self.history.addItem(label + ' · ' + (source[:56] + '…' if len(source) > 56 else source), cell)
            self.history.setItemData(self.history.count() - 1, source, Qt.ItemDataRole.ToolTipRole)
        self.history.setVisible(bool(self.entries))
        self.update_selection()
        def position():
            bar=self.report.verticalScrollBar();bar.setValue(bar.maximum() if scroll else round(bar.maximum()*fraction))
        QTimer.singleShot(0,self,position)

    @staticmethod
    def wrapped(text):
        shown=str(text)[:12000];return '<br>'.join(html.escape(line[start:start+85]) for line in shown.splitlines() for start in range(0,max(1,len(line)),85))+('… (texto completo en Exportar hoja)' if len(str(text))>12000 else '')

    def present(self,value,width):
        from .cas_presentation import presentation_html
        return presentation_html(self.report,value,width,self.math_size)

    def change_math_size(self,delta):
        self.math_size=max(13,min(31,self.math_size+delta));self.render(scroll=False)

    def show_result(self):
        entry=self.selected_entry()
        if entry is None:return
        dialog=QDialog(self);dialog.setWindowTitle('Resultado r'+str(entry['cell'])+' · CAS');dialog.resize(900,500)
        root=QVBoxLayout(dialog);view=ReportView();root.addWidget(view)
        # present() registers mathematical images on the owning document.
        original=self.report;self.report=view
        try:view.setHtml(self.present(entry['answer']['presentation'],800).replace('Fórmula extensa · desplazamiento horizontal disponible; Ampliar resultado abre una vista aparte.','Fórmula extensa · usá la barra horizontal para recorrerla.'));view._raw=entry['answer']['text']
        finally:self.report=original
        from PySide6.QtWidgets import QPushButton
        copy=QPushButton('Copiar resultado completo');copy.clicked.connect(lambda:QApplication.clipboard().setText(entry['answer']['text']));root.addWidget(copy)
        self.formula_dialogs.append(dialog);dialog.finished.connect(lambda *_:self.formula_dialogs.remove(dialog) if dialog in self.formula_dialogs else None);dialog.show()

    def resizeEvent(self,event):
        super().resizeEvent(event)
        if hasattr(self,'report') and not getattr(self,'_resize_pending',False):
            self._resize_pending=True;QTimer.singleShot(0,self,self._resize_report)

    def _resize_report(self):self._resize_pending=False;self.render(scroll=False)

    def new_sheet(self):
        if self.pending:return
        if self.entries and QMessageBox.question(self,'Nueva hoja CAS','¿Vaciar la hoja y sus variables? Podés exportarla antes de continuar.',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.Cancel,QMessageBox.StandardButton.Cancel)!=QMessageBox.StandardButton.Yes:return
        self.state=self._empty();self.entries=[];self.selected=None;self._serial=0;self._automatic_reference=None;self.commands=[];self.command_position=0;self.variables.clear();self.input.clear();self.render()

    def send_result(self,destination):
        entry=self.selected_entry()
        if entry is None:return
        answer=entry['answer'];expression=answer.get('expression')
        origin=self.window.capture_handoff() if hasattr(self.window,'capture_handoff') else None
        try:
            if not expression:raise ValueError('Seleccioná un resultado que sea una expresión escalar. Las listas, matrices y ecuaciones pueden copiarse desde Resultado.')
            symbols=sorted(set(answer.get('symbols',[])) | set(answer.get('domain_symbols',[])))
            if len(symbols)>1:raise ValueError('Asigná valores a los parámetros antes de enviar una expresión de una sola variable.')
            if destination=='frequency':
                if symbols and symbols!=['w']:raise ValueError('Para analizar una respuesta en frecuencia usá w como variable en CAS.')
                if answer.get('context_rewrite') is False:raise ValueError('Las condiciones de este resultado deben resolverse en CAS antes de graficarlo.')
                from .result_expressions import ExpressionResult
                from .workspaces import ROUTES
                units=answer.get('frequency_units','')
                if units=='incompatible':raise ValueError('El resultado mezcla rad/s y rad/muestra. Revisá las unidades de origen antes de analizarlo.')
                if units not in ('rad/s','rad/muestra'):
                    from PySide6.QtWidgets import QInputDialog
                    units,ok=QInputDialog.getItem(self,'Unidad de w','Unidad de frecuencia de esta expresión:',['rad/muestra','rad/s'],0,False)
                    if not ok:return
                self.window.open_tool(ROUTES['system_analysis',0]);panel=self.window.pages[self.window.current_operation].panel
                key=entry.get('result_id');panel.load_expression(ExpressionResult(expression,'w',tuple(answer.get('notices',())),units),key,self.window.project.get(key) if key else None)
                self.finish_send(origin,entry,panel.transfer_formula);return
            from .result_expressions import check_cas_destination
            check_cas_destination(answer,destination)
            target=('t' if destination=='continuous' else 'n') if destination in ('continuous','discrete') else ('s' if destination=='analog' else 'z')
            if destination in ('analog','digital') and symbols and symbols[0] not in (target,'x'):
                raise ValueError('Para esta transferencia usá '+target+' como variable de la fórmula en CAS.')
            variable=symbols[0] if symbols else target
            class Rewrite(ast.NodeTransformer):
                def visit_Name(self,node):return ast.copy_location(ast.Name(id=target if node.id==variable else {'I':'i','E':'e'}.get(node.id,node.id),ctx=ast.Load()),node)
                def visit_Call(self,node):
                    name=node.func.id if isinstance(node.func,ast.Name) else '';node=self.generic_visit(node)
                    if name in ('Eq','Ne') and len(node.args)==2:return ast.Compare(left=node.args[0],ops=[ast.Eq() if name=='Eq' else ast.NotEq()],comparators=[node.args[1]])
                    if name in ('And','Or'):return ast.BoolOp(op=ast.And() if name=='And' else ast.Or(),values=node.args)
                    if isinstance(node.func,ast.Name):node.func.id={'abs':'abs','heaviside':'heaviside','step':'step','conjugate':'conj','dirac':'dirac','diracdelta':'dirac','impulse':'impulse'}.get(name.lower(),name)
                    return node
            tree=Rewrite().visit(ast.parse(expression,mode='eval'));ast.fix_missing_locations(tree);expression=ast.unparse(tree)
            from .workspaces import ROUTES
            if destination in ('continuous','discrete'):
                from .expression_dialects import to_numeric
                expression=to_numeric(expression);tree=ast.parse(expression,mode='eval')
                from .engine import _FUNCS
                unsupported={node.func.id for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id.lower() not in {*_FUNCS,'piecewise','where'}}
                if unsupported:raise ValueError('La expresión conserva funciones no evaluables como señal: '+', '.join(sorted(unsupported))+'.')
                self.window.open_tool(ROUTES['basic','generate']);page=self.window.pages[self.window.current_operation];page.source_domain.setCurrentIndex(0 if destination=='discrete' else 1)
                source=page.first;source.mode.setCurrentIndex(0);source.expression.setText(expression)
                source._expression_origin=(source.expression.text(),entry['result_id'])
            else:
                from .result_expressions import ExpressionResult
                self.window.open_tool(ROUTES['system_analysis',0]);panel=self.window.pages[self.window.current_operation].panel
                key=entry.get('result_id');panel.load_expression(ExpressionResult(expression,target,tuple(answer.get('notices',()))),key,self.window.project.get(key) if key else None)
                source=panel.transfer_formula
            self.finish_send(origin,entry,source)
        except Exception as exc:QMessageBox.information(self,'Usar resultado CAS',str(exc))

    def finish_send(self,origin,entry,field):
        if hasattr(self.window,'finish_handoff'):
            self.window.finish_handoff(origin,f'Expresión r{entry["cell"]} cargada desde CAS',entry.get('result_id'),field)
        else:
            self.window.statusBar().showMessage('Expresión CAS copiada. Revisá sus datos antes de calcular.')

