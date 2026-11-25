"""Errors tied to the editable field; entered text is never discarded."""
from contextlib import contextmanager
from contextvars import ContextVar
from weakref import ref

_PASSIVE=ContextVar('passive_field_validation',default=False)


@contextmanager
def passive_fields():
    """Live hints may parse drafts, but must not select text or steal focus."""
    token=_PASSIVE.set(True)
    try:yield
    finally:_PASSIVE.reset(token)


class FieldError(ValueError):
    def __init__(self, message, field=None):
        super().__init__(message)
        self.field_ref = ref(field) if field is not None else None

    def field(self):
        return self.field_ref() if self.field_ref is not None else None


def clear_field(widget):
    if not widget.property('inputError'):
        return
    widget.setProperty('inputError', False)
    widget.setToolTip(getattr(widget, '_input_help_tip', widget.toolTip()))
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()
    issue = getattr(widget, '_input_issue_ref', None)
    issue = issue() if issue is not None else None
    if issue is not None and issue.field() is widget:
        issue.clear()


def mark_field(widget, message):
    if not getattr(widget, '_input_clear_bound', False):
        for name in ('textChanged', 'currentIndexChanged', 'valueChanged', 'toggled'):
            signal = getattr(widget, name, None)
            if signal is not None:
                signal.connect(lambda *_: clear_field(widget))
                widget._input_clear_bound = True
                break
    if not widget.property('inputError'):
        widget._input_help_tip = widget.toolTip()
    widget.setToolTip(message)
    widget.setProperty('inputError', True)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


def reveal_field(widget):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QScrollArea
    target = widget.focusProxy() or widget
    target.setFocus(Qt.FocusReason.OtherFocusReason)
    if hasattr(target, 'selectAll'):
        target.selectAll()
    parent = widget.parentWidget()
    while parent is not None:
        if isinstance(parent, QScrollArea):
            parent.ensureWidgetVisible(widget, 12, 24)
        parent = parent.parentWidget()


def invalid(widget, detail, expected='', name=None):
    from .numeric_input import field_name
    label = (name or field_name(widget)).strip().rstrip(':')
    message = label+': '+detail+(' '+expected if expected else '')
    # Parsing may also be used without a GUI or by a calculation worker.
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QThread
    app = QApplication.instance()
    active = not _PASSIVE.get() and widget is not None and app is not None and QThread.currentThread()==app.thread()
    if active:
        mark_field(widget, message)
        if widget.isVisible():
            reveal_field(widget)
    raise FieldError(message, widget if active else None)


def show_input_error(parent, title, error):
    """Use the originating form for data errors and the normal dialog elsewhere."""
    from PySide6.QtWidgets import QMessageBox, QWidget
    window = QWidget.window(parent)
    keys = getattr(window, 'desktop_keys', None)
    workspace = keys.workspace() if keys is not None else None
    field = error.field() if isinstance(error, FieldError) else None
    if isinstance(error, ValueError) and workspace is not None:
        belongs = workspace.inputs.isAncestorOf(parent) or workspace.parentWidget() is parent
        page = keys.active_page()
        if belongs or page is parent or getattr(page, 'panel', None) is parent:
            workspace.show_input_issue(str(error), field)
            return
    QMessageBox.warning(parent, title, str(error))


def ordered_interval(start_widget,stop_widget,start,stop,*,logarithmic=False):
    if stop<=start:invalid(stop_widget,'debe ser mayor que el inicio.',f'El inicio actual es {start:.12g}; ingresá un intervalo creciente.')
    if logarithmic and start<=0:invalid(start_widget,'debe ser mayor que cero para una escala logarítmica.','Usá una frecuencia positiva o elegí escala lineal.')
