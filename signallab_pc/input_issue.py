"""A dismissible diagnostic next to the inputs of the affected tool."""

from weakref import ref

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QToolButton, QVBoxLayout
from shiboken6 import isValid

from .validation import clear_field, mark_field, reveal_field


class InputIssue(QFrame):
    def __init__(self, workspace):
        super().__init__()
        self.workspace = workspace
        self.field_ref = None
        self.setObjectName('inputIssue')
        box = QVBoxLayout(self)
        box.setContentsMargins(9, 6, 9, 7)
        box.setSpacing(4)
        heading = QHBoxLayout()
        title = QLabel('Revisá los datos')
        title.setObjectName('inputIssueTitle')
        heading.addWidget(title, 1)
        close = QToolButton()
        close.setText('×')
        close.setAccessibleName('Cerrar aviso de entrada')
        close.setToolTip('Cerrar aviso')
        close.clicked.connect(self.clear)
        heading.addWidget(close)
        box.addLayout(heading)
        self.message = QLabel()
        self.message.setTextFormat(Qt.TextFormat.PlainText)
        self.message.setWordWrap(True)
        self.message.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        box.addWidget(self.message)
        self.edit = QPushButton('Ir al campo')
        self.edit.clicked.connect(self.go_to_field)
        box.addWidget(self.edit, 0, Qt.AlignmentFlag.AlignLeft)
        self.hide()

    def field(self):
        field = self.field_ref() if self.field_ref is not None else None
        return field if field is not None and isValid(field) else None

    def show_issue(self, message, field, reveal):
        self.clear()
        if field is not None and isValid(field) and self.workspace.inputs.isAncestorOf(field):
            self.field_ref = ref(field)
            field._input_issue_ref = ref(self)
            mark_field(field, message)
        self.edit.setVisible(self.field() is not None)
        display = message if len(message) <= 520 else message[:518] + '…'
        self.message.setText(display or 'Revisá los parámetros de esta operación.')
        self.message.setToolTip(message)
        self.show()
        if reveal:
            self.go_to_field()
        else:
            self.workspace.show_inputs()

    def go_to_field(self):
        self.workspace.show_inputs()
        field = self.field()
        if field is not None and field.isVisible():
            reveal_field(field)

    def clear(self):
        field = self.field()
        self.field_ref = None
        self.hide()
        if field is not None:
            clear_field(field)
