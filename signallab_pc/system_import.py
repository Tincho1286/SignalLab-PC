"""One compact file/result import action, shared by transfer-based tools."""
import json
import warnings
from pathlib import Path
from PySide6.QtWidgets import QMenu,QFileDialog,QMessageBox
from .filters import Transfer
from .resources import ensure_working_set


def load_transfer(path):
    path=Path(path);ensure_working_set(path.stat().st_size,bytes_per_sample=1,live_arrays=8)
    try:document=json.loads(path.read_text(encoding='utf-8-sig'))
    except json.JSONDecodeError as exc:raise ValueError(f'JSON inválido en línea {exc.lineno}, columna {exc.colno}.') from exc
    return Transfer.from_document(document)


class SystemImporter:
    def __init__(self,button,window,receive,choose,domains=None,allow_advance=True):
        self.button=button;self.window=window;self.receive=receive;self.domains=domains;self.allow_advance=allow_advance
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',RuntimeWarning)
            try:button.clicked.disconnect()
            except RuntimeError:pass
        button.setText('Cargar sistema…');button.setToolTip('Abrir un sistema JSON o reutilizar sistemas y expresiones H(s)/H(z) guardados en Resultados.');menu=QMenu(button);button.setMenu(menu);self.menu=menu
        menu.addAction('Usar un resultado o importar archivo compatible…',lambda checked=False:self.choose_result());menu.addAction('Abrir archivo de sistema JSON…',lambda:self.open_file())
        button._system_importer=self
    def constraints(self):
        domains=self.domains() if callable(self.domains) else self.domains
        advance=self.allow_advance() if callable(self.allow_advance) else self.allow_advance
        return domains,advance
    def validate(self,system):
        domains,advance=self.constraints()
        if domains is not None and system.domain not in domains:raise ValueError('El dominio no corresponde a esta operación. No se convierte automáticamente entre continuo y discreto.')
        if system.advance and not advance:raise ValueError('La definición conserva un avance temporal. Esta operación necesita una realización causal; usá Análisis de sistemas o Transformada Z inversa.')
    def receive_result(self,system,key,expression=None):
        self.validate(system)
        if self.receive(system,key) is False:return
        # Keep the selected expression visible while preserving its converted
        # coefficients and physical clock. Editing it invalidates the cache.
        editor=getattr(self.receive,'__self__',None)
        if expression and editor is not None and all(hasattr(editor,name) for name in ('definition_mode','transfer_formula','domain')):
            editor.transfer_formula.setText(expression);editor.definition_mode.setCurrentIndex(1)
            editor._preserved_system=system;editor._preserved_formula=(editor.transfer_formula.text(),editor.domain.currentIndex())
        self.window.statusBar().showMessage('Sistema cargado desde Resultados. Revisá sus opciones y calculá en esta herramienta.')
    def choose_result(self):
        domains,advance=self.constraints()
        key=self.window.choose_record('system_source',domains=domains,allow_advance=advance)
        if key:self.load_result(key)
    def load_result(self,key):
        try:
            source=self.window.project.get(key)
            if isinstance(source,Transfer):self.receive_result(source,key);return
            from .result_expressions import expression_result
            from .transfer_input import formula_system
            expression=expression_result(source)
            editor=getattr(self.receive,'__self__',None)
            allowed=('s','z','w') if getattr(editor,'accepts_system_expressions',False) else ('s','z')
            if expression is None or expression.variable not in allowed:raise ValueError('Este destino requiere una transferencia H(s) o H(z). Las respuestas H(w) se analizan en Análisis de sistemas.')
            if getattr(editor,'accepts_system_expressions',False):
                editor.load_expression(expression,key,source);self.window.statusBar().showMessage('Fórmula cargada con sus condiciones. Calculá el análisis.');return
            text=expression.source;domain='analog' if expression.variable=='s' else 'digital';domains,advance=self.constraints()
            if domains is not None and domain not in domains:raise ValueError('La expresión corresponde a otro dominio. No se transforma automáticamente entre s y z.')
            def convert():
                system=formula_system(text,domain,'H('+expression.variable+') desde expresión',allow_advance=advance)
                if domain=='digital':
                    system.sample_period_s=self.window.project.sample_period(key)
                from .transform_context import result_roc
                system.roc=result_roc(source)
                return system
            def accept(system):
                self.validate(system)
                result_id=self.window.publish(system,operation='Expresión interpretada como transferencia',parents=[key])
                self.receive_result(system,result_id,text)
            self.window._run_operation('Preparando la expresión como sistema…',convert,accept)
        except (ValueError,TypeError,KeyError,MemoryError,OverflowError) as exc:QMessageBox.warning(self.button,'No se pudo cargar el sistema',str(exc))
    def open_file(self,path=None):
        if path is None:path,_=QFileDialog.getOpenFileName(self.button,'Abrir sistema','','Sistema SignalLab (*.json)')
        if not path:return
        try:
            path=Path(path);ensure_working_set(path.stat().st_size,bytes_per_sample=1,live_arrays=8)
            document=json.loads(path.read_text(encoding='utf-8-sig'))
            if not isinstance(document,dict):raise ValueError('El archivo de sistema debe contener un objeto JSON.')
            if document.get('format')=='signallab-project':
                editor=getattr(self.receive,'__self__',None)
                if not getattr(editor,'accepts_system_expressions',False):raise ValueError('Este archivo conserva una definición por expresión. Abrilo en Análisis de sistemas o Resultados; este destino requiere coeficientes b/a.')
                from .project import Project
                from .result_expressions import expression_result
                staging=Project();staging.merge(path);headers=staging.headers();index=None
                for position in range(len(headers)-1,-1,-1):
                    value=staging.get(headers[position]['id']);expression=expression_result(value)
                    if isinstance(value,Transfer) or expression is not None and expression.variable in ('s','z','w'):index=position;break
                if index is None:raise ValueError('El archivo no contiene una definición en s o z.')
                before=len(self.window.project.headers());self.window.project.merge(path);imported=self.window.project.headers()[before+index]['id']
                key=self.window.publish(self.window.project.get(imported),operation='Importación de definición de sistema',parents=[imported]);self.load_result(key);return
            system=load_transfer(path);self.validate(system)
            key=self.window.publish(system,operation='Importación JSON de sistema')
            if self.receive(system,key) is False:return
            self.window.statusBar().showMessage('Sistema cargado desde '+Path(path).name+'. Revisá sus datos y calculá.')
        except (ValueError,TypeError,OSError,MemoryError,OverflowError) as exc:QMessageBox.warning(self.button,'No se pudo cargar el sistema',str(exc))


def install_system_import(button,window,receive,choose,domains=None,allow_advance=True):
    return SystemImporter(button,window,receive,choose,domains,allow_advance)
