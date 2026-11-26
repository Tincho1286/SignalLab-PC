"""A single figure launcher in the header of each results/report area."""
import weakref
from shiboken6 import isValid
from PySide6.QtCore import Qt,QEvent,QSize
from PySide6.QtWidgets import (QToolButton,QMenu,QTabWidget,QAbstractButton,QDialog,QDialogButtonBox,
                               QFormLayout,QLabel,QMessageBox,QVBoxLayout)


def style_launcher(button):
    button.setText('Abrir gráfico');button.setObjectName('plotLauncher')
    button.setProperty('plotLauncher',True);button.setMinimumWidth(0)
    if isinstance(button,QToolButton):button.setAutoRaise(False)
    button.setAccessibleName('Abrir gráfico del resultado')


def install_result_button(tabs,button):
    """Tools that must sample a formula keep their original, validated action."""
    style_launcher(button);tabs._signallab_custom_plot_action=button
    bar=getattr(tabs,'result_action_bar',None)
    if bar is not None:bar.add_action(button,'graph')
    else:tabs.setCornerWidget(button,Qt.Corner.TopRightCorner)


def _alive(reference):
    value=reference()
    return value if value is not None and isValid(value) else None


class SplitPlotButton(QToolButton):
    def sizeHint(self):
        base=super().sizeHint();extra=36 if self.property('hasPlotChoices') else 0
        icon_width=self.iconSize().width()+4 if not self.icon().isNull() else 0
        return QSize(max(base.width(),self.fontMetrics().horizontalAdvance(self.text())+28+extra+icon_width),max(base.height(),self.fontMetrics().height()+14,32))

    def minimumSizeHint(self):return self.sizeHint()


class FormulaPlotButton(SplitPlotButton):
    """Sample the current result or configure its plotting interval."""
    def __init__(self, parent, description):
        super().__init__(parent)
        self.setProperty('hasPlotChoices', True)
        self.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.setToolTip('Abrí el gráfico con el intervalo actual. La flecha permite cambiar el intervalo y la resolución.')
        menu = QMenu(self)
        self.setMenu(menu)
        menu.addAction('Intervalo del gráfico…', self.open_settings)
        self.settings = QDialog(parent)
        self.settings.setWindowTitle('Intervalo del gráfico')
        self.settings.setMinimumWidth(345)
        root = QVBoxLayout(self.settings)
        note = QLabel(description)
        note.setWordWrap(True)
        root.addWidget(note)
        self.form = QFormLayout()
        self.form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        root.addLayout(self.form)
        actions = QDialogButtonBox()
        close = actions.addButton('Cerrar', QDialogButtonBox.ButtonRole.RejectRole)
        close.clicked.connect(self.settings.hide)
        plot = actions.addButton('Abrir gráfico', QDialogButtonBox.ButtonRole.ActionRole)
        plot.setObjectName('primary')
        plot.setDefault(True)
        plot.clicked.connect(self.click)
        root.addWidget(actions)
        self.setEnabled(False)

    def open_settings(self):
        self.settings.show()
        self.settings.raise_()
        self.settings.activateWindow()

    def invalid_interval(self, error):
        self.open_settings()
        QMessageBox.warning(self.settings, 'Revisá el intervalo del gráfico', str(error))

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.EnabledChange and not self.isEnabled() and hasattr(self, 'settings'):
            self.settings.hide()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.settings.hide()


class PlotLauncher(SplitPlotButton):
    def __init__(self,parent):
        super().__init__(parent);style_launcher(self);self.entries=[];self._refreshing=False
        self.setToolTip('Abrir la figura del resultado. La flecha permite elegir otra figura disponible.')
        self.menu=QMenu(self);self.setMenu(self.menu);self.menu.aboutToShow.connect(self.rebuild)
        self.clicked.connect(self.open_default);self.setEnabled(False)
    def register(self,canvas,routes,label):
        if any(_alive(entry[0]) is canvas for entry in self.entries):return
        self.entries.append((weakref.ref(canvas),[(weakref.ref(tabs),weakref.ref(page)) for tabs,page in routes],label))
        if isinstance(canvas,QAbstractButton):canvas.installEventFilter(self)
        for tabs,_ in routes:tabs.tabBar().installEventFilter(self)
        canvas._signallab_plot_action_refresh=self.refresh;self.refresh()
    def available(self):
        result=[]
        for entry in self.entries:
            canvas=_alive(entry[0])
            if canvas is None:
                continue
            ready = (canvas.isEnabled() if isinstance(canvas, QAbstractButton)
                     else getattr(canvas, '_signallab_has_plot_result', False)
                     or callable(getattr(canvas, '_signallab_prepare_plot', None)))
            if not ready:
                continue
            path=[]
            visible=True
            for tabs_ref,page_ref in entry[1]:
                tabs,page=_alive(tabs_ref),_alive(page_ref)
                if tabs is None or page is None:visible=False;break
                index=tabs.indexOf(page)
                if index<0 or not tabs.isTabVisible(index) or not tabs.isTabEnabled(index):visible=False;break
                path.append(index)
            if visible:result.append((tuple(reversed(path)), entry))
        return [entry for _, entry in sorted(result, key=lambda item: item[0])]
    def refresh(self):
        if self._refreshing:return
        self._refreshing=True
        try:
            entries=self.available();self.setEnabled(bool(entries))
            multiple=len(entries)>1
            if self.property('hasPlotChoices')!=multiple:
                self.setProperty('hasPlotChoices',multiple);self.style().unpolish(self);self.style().polish(self);self.updateGeometry()
            self.setMenu(self.menu if multiple else None)
            self.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup if multiple else QToolButton.ToolButtonPopupMode.DelayedPopup)
            for reference, _, _ in self.entries:
                canvas = _alive(reference)
                window = getattr(canvas, '_signallab_window', None)
                if window is not None and window.isVisible():
                    self.sync_window(canvas, entries)
        finally:self._refreshing=False
    def eventFilter(self,watched,event):
        if watched.property('resultGraphCaptured') and event.type() in (QEvent.Type.Show,QEvent.Type.ShowToParent):watched.hide()
        if event.type() in (QEvent.Type.Show,QEvent.Type.LayoutRequest,QEvent.Type.Resize,QEvent.Type.EnabledChange):self.refresh()
        return super().eventFilter(watched,event)
    def open_default(self):
        entries=self.available()
        if not entries:return
        selected=entries[0]
        for entry in entries:
            if entry[1] and all((tabs := _alive(ref)) is not None and tabs.currentWidget() is _alive(page)
                                for ref, page in entry[1]):
                selected=entry
                break
        self.open_entry(selected)
    def open_entry(self, entry, present=None):
        canvas=_alive(entry[0])
        if canvas is not None:
            if isinstance(canvas,QAbstractButton):canvas.click();return
            from .plot_view import enlarge_plot
            if present is None:
                present = lambda: enlarge_plot(canvas, self)
            prepare = getattr(canvas, '_signallab_prepare_plot', None)
            if prepare is None:
                present()
            else:
                prepare(present)

    def switch_figure(self, source, entry):
        canvas = _alive(entry[0])
        target = getattr(canvas, '_signallab_window', None)
        if target is None or target is source:
            return

        def replace():
            if not source.isVisible():
                return
            if not target.isVisible() and not source.isMaximized() and not target.isMaximized():
                target.setGeometry(source.geometry())
            target.focus_action.setChecked(source.focus_action.isChecked())
            from .plot_view import enlarge_plot
            enlarge_plot(canvas, self)
            source.hide()

        self.open_entry(entry, replace)

    def sync_window(self, canvas, entries=None):
        window = canvas._signallab_window
        options = []
        for entry, label in self.labeled_entries(self.available() if entries is None else entries):
            sibling = _alive(entry[0])
            if sibling is not None and getattr(sibling, '_signallab_window', None) is not None:
                options.append((entry, label, sibling is canvas))
        window.set_figure_choices(options, lambda entry: self.switch_figure(window, entry))

    @staticmethod
    def labeled_entries(entries):
        used = {}
        for entry in entries:
            label = entry[2] or 'Resultado'
            used[label] = used.get(label, 0) + 1
            yield entry, label if used[label] == 1 else label + ' · ' + str(used[label])

    def rebuild(self):
        self.menu.clear()
        for entry, label in self.labeled_entries(self.available()):
            self.menu.addAction(label,lambda checked=False,item=entry:self.open_entry(item))


def install_context_actions(surface,dock):
    """Diagrams share the figure launcher; their original handlers stay intact."""
    for button in surface.content.findChildren(QAbstractButton):
        label=button.property('resultGraphAction')
        if not label or button.property('resultGraphCaptured'):continue
        launcher=getattr(surface,'graph_launcher',None)
        if launcher is None:launcher=PlotLauncher(surface);surface.graph_launcher=launcher;dock.set_graph(launcher)
        routes=[];node=button.parentWidget()
        while node is not None and node is not surface:
            if isinstance(node,QTabWidget):
                for index in range(node.count()):
                    page=node.widget(index)
                    if page.isAncestorOf(button):routes.append((node,page));break
            node=node.parentWidget()
        button.setProperty('resultGraphCaptured',True);launcher.register(button,routes,label);button.hide()


def bind_canvas(canvas,origin):
    scope=origin
    while scope is not None and scope.objectName()!='resultSurface':scope=scope.parentWidget()
    if scope is not None and not hasattr(scope,'action_dock'):scope=None
    routes=[];ancestor=origin
    # Result tabs describe figures. Outer compact-layout tabs only host the
    # surface temporarily and are removed when the window becomes wide.
    while ancestor is not None and ancestor is not scope:
        if getattr(ancestor,'tool_item',None) is not None:break
        if isinstance(ancestor,QTabWidget):
            for index in range(ancestor.count()):
                page=ancestor.widget(index)
                if page is origin or page.isAncestorOf(origin):routes.append((ancestor,page));break
        ancestor=ancestor.parentWidget()
    custom=next((tabs._signallab_custom_plot_action for tabs,_ in routes if getattr(tabs,'_signallab_custom_plot_action',None) is not None),None)
    if custom is not None:
        canvas._signallab_plot_action_scope = custom
        canvas._signallab_explicit_plot = True
        return
    if scope is not None:
        launcher=getattr(scope,'graph_launcher',None)
        if launcher is None:launcher=PlotLauncher(scope);scope.graph_launcher=launcher;scope.action_dock.set_graph(launcher)
        label=' · '.join(tabs.tabText(tabs.indexOf(page)) for tabs,page in reversed(routes)) if routes else 'Resultado'
        for tabs,_ in routes:
            tabs._signallab_plot_actions=launcher
            if not hasattr(tabs,'result_action_bar'):tabs.result_action_bar=scope.action_dock.current_bar()
        canvas._signallab_explicit_plot = True
        canvas._signallab_plot_action_scope=launcher;launcher.register(canvas,routes,label);return
    if routes:
        tabs,page=routes[-1];launcher=getattr(tabs,'_signallab_plot_actions',None)
        if launcher is None:
            launcher=PlotLauncher(tabs);tabs._signallab_plot_actions=launcher
            bar=getattr(tabs,'result_action_bar',None)
            if bar is not None:bar.add_action(launcher,'graph')
            else:tabs.setCornerWidget(launcher,Qt.Corner.TopRightCorner)
        label=tabs.tabText(tabs.indexOf(page))
    else:
        launcher=getattr(origin,'_signallab_plot_actions',None)
        if launcher is None:
            launcher=PlotLauncher(origin);origin._signallab_plot_actions=launcher
            layout=origin.layout()
            if hasattr(layout,'insertWidget'):layout.insertWidget(0,launcher,0,Qt.AlignmentFlag.AlignRight)
            else:layout.addWidget(launcher)
        label='Resultado'
    canvas._signallab_plot_action_scope=launcher
    launcher.register(canvas,routes,label)
