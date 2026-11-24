"""Optional settings that remain attached to the form they belong to."""
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QFormLayout, QScrollArea, QSizePolicy, QToolButton, QVBoxLayout, QWidget


class FieldSection(QWidget):
    def __init__(self, title):
        super().__init__()
        box = QVBoxLayout(self)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(6)
        self.toggle = QToolButton()
        self.toggle.setObjectName('fieldSectionToggle')
        self.toggle.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle.setCheckable(True)
        self.toggle.setText(title)
        box.addWidget(self.toggle)
        self.body = QWidget()
        self.body.setObjectName('fieldSectionBody')
        self.form = QFormLayout(self.body)
        self.form.setContentsMargins(10, 8, 10, 8)
        self.form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        box.addWidget(self.body)
        self.toggle.toggled.connect(self.show_fields)
        self.show_fields(False)

    def show_fields(self, expanded):
        self.toggle.setArrowType(Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow)
        self.body.setVisible(expanded)
        if expanded:
            QTimer.singleShot(0, self, self.reveal)

    def reveal(self):
        parent = self.parentWidget()
        while parent is not None and not isinstance(parent, QScrollArea):
            parent = parent.parentWidget()
        if parent is not None:
            parent.ensureWidgetVisible(self, 0, 10)
