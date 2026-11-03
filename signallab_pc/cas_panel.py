"""An independent, sequential mathematical worksheet in the existing desktop."""
import ast,html,re
from PySide6.QtCore import Qt,Signal,QTimer,QUrl
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QLabel,QPlainTextEdit,QToolBar,QToolButton,
    QMenu,QTreeWidget,QTreeWidgetItem,QMessageBox,QApplication,QDialog)
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
        self.commands=[];self.command_position=0;self.draft='';self._submitting=False;self._serial=0;self.math_size=17;self.formula_dialogs=[]
        root=QVBoxLayout(self);root.setContentsMargins(10,8,10,8);root.setSpacing(6)
        self.toolbar=QToolBar();self.toolbar.setObjectName('casToolbar');self.toolbar.setMovable(False);root.addWidget(self.toolbar)
        groups=[('Álgebra',[
            ('Simplificar','simplify(expr)'),('Desarrollar','expand(expr)'),('Factorizar','factor(expr)'),
            ('Unificar fracción','together(expr)'),('Fracciones parciales','apart(expr,x)'),('Sustituir','subst(expr,x,valor)'),
            ('Aproximar','approx(expr,15)'),('Proponer forma exacta','exact(expr)'),('Declarar supuesto','assume(x>0)'),('Exponenciales a trigonometría','exp2trig(expr)'),('Trigonometría a exponenciales','trig2exp(expr)')]),
            ('Cálculo',[('Derivar','diff(expr,x)'),('Integral','integrate(expr,x)'),('Integral definida','integrate(expr,x,a,b)'),
            ('Límite','limit(expr,x,0)'),('Serie','series(expr,x,0,6)'),('Sumatoria','sum(expr,n,a,b)'),('Producto','prod(expr,n,a,b)')]),
            ('Ecuaciones',[('Resolver en complejos','solve(expr,x)'),('Resolver en reales','solve_real(expr,x)'),
            ('Sistema de ecuaciones','solve([ecuacion1,ecuacion2],[x,y])'),('Sistema lineal','linsolve([ecuacion1,ecuacion2],[x,y])'),('Raíz numérica local','nsolve(expr,x,1)'),
            ('Ecuación diferencial','dsolve(expr,y(x))')]),
            ('Matrices',[('Crear matriz','matrix([[a,b],[c,d]])'),('Determinante','det(expr)'),('Inversa','inv(expr)'),
            ('Transpuesta','transpose(expr)'),('Rango','rank(expr)'),('Autovalores','eigenvalues(expr)'),('Forma escalonada reducida','rref(expr)')])]
        self.template_actions=[]
        for title,items in groups:
            button=QToolButton();button.setText(title);button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup);menu=QMenu(button);button.setMenu(menu);self.toolbar.addWidget(button)
            for label,template in items:self.template_actions.append(menu.addAction(label,lambda checked=False,t=template:self.insert_template(t)))
        button=QToolButton();button.setText('Resultado');button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup);menu=QMenu(button);button.setMenu(menu);self.toolbar.addWidget(button)
        menu.addAction('Ver resultado ampliado…',self.show_result);menu.addAction('Copiar resultado',self.copy_result);menu.addAction('Insertar referencia rN',self.insert_reference);menu.addSeparator()
        for title,destination in [('Usar como señal continua','continuous'),('Usar como secuencia discreta','discrete'),('Usar como H(s)','analog'),('Usar como H(z)','digital')]:menu.addAction(title,lambda checked=False,key=destination:self.send_result(key))
        sheet=QToolButton();sheet.setText('Hoja');sheet.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup);menu=QMenu(sheet);sheet.setMenu(menu);self.toolbar.addWidget(sheet)
        self.variables_button=menu.addAction('Variables y supuestos…',lambda:self.variables_dialog.show());menu.addSeparator()
        menu.addAction('Hoja con formato…',lambda:self.report.export_document(True));menu.addAction('Texto completo…',lambda:self.report.export_document(False));menu.addAction('Copiar hoja',lambda:QApplication.clipboard().setText(self.report.toPlainText()))
        menu.addSeparator();menu.addAction('Aumentar tamaño de fórmulas',lambda:self.change_math_size(2));menu.addAction('Reducir tamaño de fórmulas',lambda:self.change_math_size(-2));menu.addSeparator();self.new_button=menu.addAction('Nueva hoja…',self.new_sheet)
        self.variables_dialog=QDialog(self);self.variables_dialog.setWindowTitle('Variables y supuestos · CAS');self.variables_dialog.resize(520,250);self.variables_dialog.setMinimumSize(300,150)
        variable_layout=QVBoxLayout(self.variables_dialog);self.variables=QTreeWidget();self.variables.setColumnCount(2);self.variables.setHeaderLabels(['Nombre','Valor / definición']);self.variables.setRootIsDecorated(False);variable_layout.addWidget(self.variables)
        self.variables.itemDoubleClicked.connect(lambda item,*_:self.input.insertPlainText(item.text(0)))
        self.report=ReportView();self.report.anchorClicked.connect(self.follow_link);root.addWidget(self.report,1)
        self.selection_note=QLabel('Exacto · trigonometría en radianes · símbolos sin supuestos automáticos');self.selection_note.setObjectName('muted');self.selection_note.setWordWrap(True);root.addWidget(self.selection_note)
        self.input=CasInput();self.input.setObjectName('casInput');self.input.setPlaceholderText('Expresión o comando matemático');self.input.setMinimumHeight(56);self.input.setMaximumHeight(84);root.addWidget(self.input)
        self.input.evaluateRequested.connect(self.calculate);self.input.historyRequested.connect(self.recall)
        hint=QLabel('Enter: evaluar · Shift+Enter: nueva línea · Ctrl+↑/↓: historial · F1: ayuda');hint.setObjectName('muted');hint.setWordWrap(True);root.addWidget(hint)
        from PySide6.QtWidgets import QPushButton
        load=QPushButton('Cargar resultado o archivo…');load.clicked.connect(self.choose_source);root.addWidget(load)
        self.calculate_button=QPushButton('Evaluar');self.calculate_button.setObjectName('primary');self.calculate_button.clicked.connect(self.calculate);root.addWidget(self.calculate_button)
        self.timer=QTimer(self);self.timer.setInterval(200);self.timer.timeout.connect(self.check_pending);self.timer.start();self.render()

    def choose_source(self):
        if not self._ready():return
        key=self.window.choose_record('cas_source')
        if key:
            from .cas_transfer import send_to_cas
            send_to_cas(self.window,key)

    @staticmethod
    def _empty():return {'version':1,'variables':{},'functions':{},'results':{},'ans':None,'assumptions':{}}

    def insert_template(self,template):
        value=self.input.textCursor().selectedText() or self.input.toPlainText().strip()
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
        parents=self._parents(source)
        self.commands.append(source);self.command_position=len(self.commands);self.draft='';self.input.clear()
        self._submit({'operation':'cas_worksheet','source':source},source,parents)
    def import_result(self,payload,title,parent=None):
        if not self._ready():return
        self._submit({'operation':'cas_import','payload':payload},'Desde Resultados: '+title,[parent] if parent else [],imported=True)
    def _submit(self,request,source,parents,imported=False):
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
                saved={name:answer[name] for name in ('text','presentation','notices','expression','symbols','assumptions','calculation_notes','provenance') if name in answer}
                saved['encoded_value']=self.state['results'][str(cell)]
                entry['result_id']=self.window.publish({'cas_answer':saved,'source':source},title='CAS · '+source,operation='Resultado CAS',parents=parents)
                self.variables.clear()
                for name,value in answer['variables']+answer['functions']+[(name,'Supuesto: '+description) for name,description in answer.get('assumptions',[])]:
                    node=QTreeWidgetItem([name,value[:200]]);node.setToolTip(1,value);self.variables.addTopLevelItem(node)
                self.variables.resizeColumnToContents(0)
                if imported:
                    if not self.input.toPlainText().strip():self.input.setPlainText('r'+str(cell))
                    self.window.statusBar().showMessage('Resultado disponible en CAS como r'+str(cell)+'. Podés usar simplify, factor, expand o cualquier otra operación de la hoja.')
            self.render();self.input.setFocus()
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
        if url.scheme()=='cas-input':self.input.setPlainText('r'+str(cell) if entry.get('imported') and entry['status']=='done' else entry['source']);self.input.setFocus()
        elif url.scheme()=='cas-view':self.selected=cell;self.show_result()
        elif url.scheme()=='cas-result':self.selected=cell;self.update_selection();self.insert_reference()

    def update_selection(self):
        self.selection_note.setText('Exacto · radianes · '+(str(len(self.state.get('assumptions',{})))+' símbolos con supuestos' if self.state.get('assumptions') else 'sin supuestos declarados')+(' · Resultado: r'+str(self.selected) if self.selected is not None else ''))

    def selected_entry(self):
        return next((item for item in self.entries if item['cell']==self.selected and item['status']=='done'),None)

    def copy_result(self):
        entry=self.selected_entry()
        if entry:QApplication.clipboard().setText(entry['answer']['text'])

    def insert_reference(self):
        if self.selected_entry():self.input.insertPlainText('r'+str(self.selected));self.input.setFocus()

    def render(self,scroll=True):
        bar=self.report.verticalScrollBar();fraction=bar.value()/max(1,bar.maximum())
        parts=[];raw=[];width=max(180,self.report.viewport().width()-70)
        if not self.entries:parts=['<h2>Hoja CAS</h2><p>Escribí una expresión abajo y presioná Enter. Las entradas y sus resultados quedan en esta hoja. Los menús insertan comandos; F1 explica su sintaxis.</p>']
        for entry in self.entries:
            cell=entry['cell'];source=entry['source'];raw.append(f'Entrada {cell}: '+source)
            parts.append(f'<table width="100%" cellspacing="0" cellpadding="5"><tr><td width="55" valign="top"><a href="cas-input:{cell}" title="Editar entrada">[{cell}]</a></td><td style="font-family:Consolas">'+self.wrapped(source)+'</td></tr>')
            if entry['status']=='pending':parts.append('<tr><td></td><td style="color:'+C['muted']+'">Calculando…</td></tr></table>');continue
            if entry['status']=='error':parts.append('<tr><td></td><td style="color:'+C['amber']+'">'+html.escape(entry['error'])+'</td></tr></table>');raw.append('No aplicado: '+entry['error']);continue
            answer=entry['answer'];parts.append(f'<tr><td valign="top"><a href="cas-result:{cell}" title="Reutilizar resultado">r{cell}</a></td><td>'+self.present(answer['presentation'],width-65)+f'<p><a href="cas-view:{cell}">Ampliar resultado</a></p></td></tr>')
            for notice in answer['notices']:
                if not notice.startswith('Definición guardada:'):parts.append('<tr><td></td><td style="color:'+C['muted']+'">'+html.escape(notice)+'</td></tr>')
            parts.append('</table><p style="margin:0;color:'+C['rule']+'">────────────────────────</p>')
            raw.append('r'+str(cell)+' = '+answer['text']);raw.extend(answer['notices'])
        self.report.setHtml('<html><head><style>p {margin-top:2px;margin-bottom:2px;line-height:120%;}</style></head><body style="margin:10px">'+''.join(parts)+'</body></html>');self.report._raw='\n\n'.join(raw);self.update_selection()
        def position():
            bar=self.report.verticalScrollBar();bar.setValue(bar.maximum() if scroll else round(bar.maximum()*fraction))
        QTimer.singleShot(0,self,position)

    @staticmethod
    def wrapped(text):
        shown=str(text)[:12000];return '<br>'.join(html.escape(line[start:start+85]) for line in shown.splitlines() for start in range(0,max(1,len(line)),85))+('… (texto completo en Hoja → Texto completo)' if len(str(text))>12000 else '')

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
        self.state=self._empty();self.entries=[];self.selected=None;self._serial=0;self.commands=[];self.command_position=0;self.variables.clear();self.input.clear();self.render()

    def send_result(self,destination):
        entry=self.selected_entry()
        if entry is None:return
        answer=entry['answer'];expression=answer.get('expression')
        try:
            if not expression:raise ValueError('Seleccioná un resultado que sea una expresión escalar. Las listas, matrices y ecuaciones pueden copiarse desde Resultado.')
            symbols=answer.get('symbols',[])
            if len(symbols)>1:raise ValueError('Asigná valores a los parámetros antes de enviar una expresión de una sola variable.')
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
                    if isinstance(node.func,ast.Name):node.func.id={'Abs':'abs','Heaviside':'heaviside','conjugate':'conj'}.get(name,name)
                    return node
            tree=Rewrite().visit(ast.parse(expression,mode='eval'));ast.fix_missing_locations(tree);expression=ast.unparse(tree)
            from .workspaces import ROUTES
            if destination in ('continuous','discrete'):
                from .engine import _FUNCS
                unsupported={node.func.id for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id not in {*_FUNCS,'Piecewise','where'}}
                if unsupported:raise ValueError('La expresión conserva funciones no evaluables como señal: '+', '.join(sorted(unsupported))+'.')
                self.window.open_tool(ROUTES['basic','generate']);page=self.window.pages[self.window.current_operation];page.source_domain.setCurrentIndex(0 if destination=='discrete' else 1)
                source=page.first;source.mode.setCurrentIndex(0);source.expression.setText(expression)
            else:
                self.window.open_tool(ROUTES['system_analysis',0]);panel=self.window.pages[self.window.current_operation].panel;panel.domain.setCurrentIndex(0 if destination=='analog' else 1);panel.definition_mode.setCurrentIndex(1);panel.transfer_formula.setText(expression)
            self.window.statusBar().showMessage('Expresión CAS copiada. Revisá el intervalo y calculá en el destino.')
        except Exception as exc:QMessageBox.information(self,'Usar resultado CAS',str(exc))

