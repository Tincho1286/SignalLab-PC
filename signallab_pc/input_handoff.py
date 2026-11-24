"""Context for an input brought from another document in the current session."""
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QToolButton, QVBoxLayout

from .design import icon
from .wrapping_row import WrappingRow


@dataclass(frozen=True)
class HandoffOrigin:
    document: tuple
    route: tuple | None
    record: str | None
    title: str
    result: bool


class InputHandoff(QFrame):
    def __init__(self, summary, title, back, show_record):
        super().__init__()
        self.setObjectName('inputHandoff')
        layout=QVBoxLayout(self);layout.setContentsMargins(9,7,9,7);layout.setSpacing(5)
        row=WrappingRow();layout.addWidget(row)
        if back is not None:
            button=QPushButton('Volver al origen');button.setIcon(icon('back'))
            button.setToolTip(title);button.clicked.connect(back);row.flow.addWidget(button)
        if show_record is not None:
            button=QPushButton('Ver en Resultados');button.clicked.connect(show_record);row.flow.addWidget(button)
        close=QToolButton();close.setText('×');close.setAccessibleName('Ocultar origen de la entrada');close.clicked.connect(self.hide);row.flow.addWidget(close)
        label=QLabel(summary if len(summary)<=176 else summary[:175]+'…');label.setTextFormat(Qt.TextFormat.PlainText);label.setWordWrap(True)
        label.setToolTip(summary)
        layout.insertWidget(0,label)
