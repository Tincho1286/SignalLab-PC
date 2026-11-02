"""Typed expression input from local files or previously calculated results."""
from PySide6.QtWidgets import QToolButton,QMessageBox


def install_expression_import(editor,window,variables,units=None,receiver=None):
    if getattr(editor,'_expression_import',None) is not None:return editor._expression_import
    button=QToolButton();button.setText('Cargar…');button.setToolTip('Usar una expresión de Resultados o importar un archivo compatible. Las muestras no se convierten en fórmulas infinitas.')
    editor.method_buttons.layout().addWidget(button);editor._expression_import=button
    def choose():
        try:
            allowed=variables() if callable(variables) else variables
            axis_units=units() if callable(units) else units
            key=window.choose_record('expression',variables=[*allowed,None],units=axis_units)
            if not key:return
            value=window.project.expression(key)
            if receiver is not None:receiver(value,key)
            else:
                from .expression_dialects import to_numeric
                text=value.source if editor.symbolic else to_numeric(value.numerical_source or value.source)
                editor.setText(text);editor._import_origin=(editor.text(),key,tuple(value.conditions))
                editor.setToolTip('Condiciones de origen: '+'; '.join(value.conditions) if value.conditions else 'Expresión cargada conservando su variable y coeficientes.')
        except Exception as exc:QMessageBox.warning(editor,'No se pudo cargar la expresión',str(exc))
    button.clicked.connect(choose);return button


def expression_context(*editors):
    parents=[];conditions=[]
    for editor in editors:
        origin=getattr(editor,'_import_origin',None)
        if origin and origin[0]==editor.text():
            if origin[1]:parents.append(origin[1])
            conditions.extend(origin[2])
    return list(dict.fromkeys(parents)),list(dict.fromkeys(conditions))
