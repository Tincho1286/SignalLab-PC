"""Predictable document shortcuts and focus within the active workspace."""
import weakref
from PySide6.QtCore import QObject,Qt,QPoint
from PySide6.QtGui import QAction,QKeySequence
from PySide6.QtWidgets import QApplication,QWidget,QScrollArea,QDialog,QVBoxLayout,QFormLayout,QLabel,QDialogButtonBox
from shiboken6 import isValid

SHORTCUTS=[('Ctrl+Enter','Calcular con los datos de la herramienta abierta'),('Ctrl+K','Buscar una herramienta'),('Ctrl+Tab / Ctrl+Shift+Tab','Cambiar de documento'),('Ctrl+W','Cerrar la pestaña; sus datos se conservan en esta sesión'),('Alt+1 / Alt+2','Ir a los datos de entrada o al resultado'),('Alt+G','Abrir el gráfico o ampliar la fórmula'),('Alt+R','Reutilizar el resultado'),('Alt+E','Exportar el resultado'),('Ctrl+Shift+C','Abrir la calculadora CAS'),('F1','Consultar la ayuda de la herramienta'),('F11','Ocultar o recuperar los paneles laterales')]


class DesktopKeys(QObject):
    def __init__(self,window):
        super().__init__(window);self.owner=window;self.last_focus=weakref.WeakKeyDictionary();self.commands={};self._help_dialog=None
        for name,sequences,callback in [('calculate',['Ctrl+Return','Ctrl+Enter'],window.calculate_active),('next',['Ctrl+Tab'],lambda:self.document(1)),('previous',['Ctrl+Shift+Tab'],lambda:self.document(-1)),('close',['Ctrl+W'],self.close_document),('inputs',['Alt+1'],lambda:self.focus_surface(False)),('results',['Alt+2'],lambda:self.focus_surface(True)),('graph',['Alt+G'],lambda:self.result_action('graph')),('reuse',['Alt+R'],lambda:self.result_action('reuse')),('export',['Alt+E'],lambda:self.result_action('export'))]:
            action=QAction(window);action.setShortcuts([QKeySequence(sequence) for sequence in sequences]);action.triggered.connect(lambda checked=False,run=callback:self.dispatch(run));window.addAction(action);self.commands[name]=action
        QApplication.instance().focusChanged.connect(self.remember_focus)

    def dispatch(self,callback):
        if QApplication.activeWindow() is self.owner:callback()

    def active_page(self):
        if not isValid(self.owner) or not isValid(self.owner.stack):return None
        view=self.owner.stack.currentWidget()
        return getattr(view,'active_page',None) or (view.widget() if isinstance(view,QScrollArea) else view)

    def workspace(self):return getattr(self.active_page(),'workspace',None)

    def remember_focus(self,old,current):
        space=self.workspace()
        if current is None or space is None or current.window() is not self.owner:return
        for surface in (space.inputs,space.results):
            if surface.isAncestorOf(current):self.last_focus[surface]=weakref.ref(current);return

    def reveal(self,widget):
        widget.setFocus(Qt.FocusReason.ShortcutFocusReason);parent=widget.parentWidget()
        while parent is not None:
            if isinstance(parent,QScrollArea):parent.ensureWidgetVisible(widget,12,20)
            parent=parent.parentWidget()

    def focus_surface(self,result):
        space=self.workspace()
        if space is None:
            page=self.active_page();widget=getattr(page,'text' if result else 'search',None)
            if isinstance(widget,QWidget):
                toggle=getattr(page,'topic_toggle',None)
                if toggle is not None:toggle.setChecked(not result)
                self.reveal(widget)
            return
        if space.compact:space.tabs.setCurrentIndex(1 if result else 0)
        surface=space.results if result else space.inputs;reference=self.last_focus.get(surface);widget=reference() if reference is not None else None
        if widget is None or not isValid(widget) or not widget.isVisibleTo(surface) or not widget.isEnabled():
            candidates=[child for child in surface.findChildren(QWidget) if child.window() is self.owner and child.isVisibleTo(surface) and child.isEnabled() and child.focusPolicy() & Qt.FocusPolicy.TabFocus]
            candidates.sort(key=lambda child:(child.mapTo(surface,QPoint()).y(),child.mapTo(surface,QPoint()).x()));widget=next(iter(candidates),surface)
        self.reveal(widget)

    def result_action(self,role):
        space=self.workspace();dock=getattr(space.results,'action_dock',None) if space is not None else None;bar=dock.current_bar() if dock is not None else None;button=bar.slots.get(role) if bar is not None else None
        if button is None or not button.isEnabled() or button.isHidden():return
        if space.compact:space.tabs.setCurrentIndex(1)
        self.reveal(button)
        if role!='graph' and button.menu() is not None:
            menu=button.menu();menu.popup(button.mapToGlobal(QPoint(0,button.height())));menu.setActiveAction(next((action for action in menu.actions() if action.isEnabled() and not action.isSeparator()),None))
        else:button.click()

    def document(self,offset):
        tabs=self.owner.documents
        if tabs.count()>1:tabs.setCurrentIndex((tabs.currentIndex()+offset)%tabs.count())

    def close_document(self):
        index=self.owner.documents.currentIndex()
        if index>=0:self.owner.close_document(index)

    def show_help(self):
        if self._help_dialog is None:
            dialog=QDialog(self.owner);dialog.setWindowTitle('Atajos de teclado');root=QVBoxLayout(dialog);scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QScrollArea.Shape.NoFrame);content=QWidget();form=QFormLayout(content);form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows);form.setVerticalSpacing(12);form.setHorizontalSpacing(24);scroll.setWidget(content);root.addWidget(scroll)
            for keys,meaning in SHORTCUTS:
                label=QLabel(meaning);label.setWordWrap(True);form.addRow(keys,label)
            close=QDialogButtonBox(QDialogButtonBox.StandardButton.Close);close.button(QDialogButtonBox.StandardButton.Close).setText('Cerrar');close.rejected.connect(dialog.reject);root.addWidget(close);available=self.owner.screen().availableGeometry();dialog.resize(min(700,available.width()-40),min(440,available.height()-40));self._help_dialog=dialog
        self._help_dialog.show();self._help_dialog.raise_();self._help_dialog.activateWindow()
