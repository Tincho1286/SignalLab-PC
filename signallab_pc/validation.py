"""Errors tied to the editable field; entered text is never discarded."""


class FieldError(ValueError):
    pass


def invalid(widget, detail, expected='', name=None):
    from .numeric_input import field_name
    label = (name or field_name(widget)).strip().rstrip(':')
    message = label+': '+detail+(' '+expected if expected else '')
    # Parsing may also be used without a GUI or by a calculation worker.
    from PySide6.QtWidgets import QApplication,QScrollArea
    from PySide6.QtCore import QThread
    app = QApplication.instance()
    if widget is not None and app is not None and QThread.currentThread()==app.thread():
        if not hasattr(widget, '_validation_original'):
            widget._validation_original = (widget.styleSheet(),widget.toolTip())
            def clear(*_):
                original = getattr(widget, '_validation_original', None)
                if original:
                    widget.setStyleSheet(original[0]);widget.setToolTip(original[1]);widget.setProperty('inputError',False)
            signal = getattr(widget,'textChanged',None)
            if signal is not None:signal.connect(clear)
        original = widget._validation_original
        widget.setStyleSheet(original[0]+'\nQLineEdit {border:1px solid #ee8b8b;}')
        widget.setToolTip(message);widget.setProperty('inputError',True);widget.setFocus()
        if hasattr(widget,'selectAll'):widget.selectAll()
        parent = widget.parentWidget()
        while parent is not None:
            if isinstance(parent,QScrollArea):parent.ensureWidgetVisible(widget,12,24)
            parent = parent.parentWidget()
    raise FieldError(message)


def ordered_interval(start_widget,stop_widget,start,stop,*,logarithmic=False):
    if stop<=start:invalid(stop_widget,'debe ser mayor que el inicio.',f'El inicio actual es {start:.12g}; ingresá un intervalo creciente.')
    if logarithmic and start<=0:invalid(start_widget,'debe ser mayor que cero para una escala logarítmica.','Usá una frecuencia positiva o elegí escala lineal.')
