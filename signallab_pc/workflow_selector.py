"""Choose a complete tool variant while keeping every document's draft."""

from itertools import groupby

from PySide6.QtCore import Qt
from PySide6.QtGui import QActionGroup
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMenu, QToolButton, QWidget

from .tool_catalog import detail_for, normalized_key
from .validation import passive_fields
from .workflow_choices import variant_title
from .workflow_inputs import prepare_inputs


class WorkflowSelector(QWidget):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.entry = None
        self.current_key = None
        self.memory = {}
        self.options = {}
        self.copy_source = None
        self.setObjectName('workflowSelector')

        row = QHBoxLayout(self)
        row.setContentsMargins(24, 0, 24, 8)
        row.setSpacing(8)
        self.caption = QLabel('Variante')
        self.caption.setObjectName('variantCaption')
        row.addWidget(self.caption)

        self.button = QToolButton()
        self.button.setObjectName('variantMenuButton')
        self.button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu = QMenu(self.button)
        self.menu.setObjectName('variantMenu')
        self.menu.setToolTipsVisible(True)
        self.menu.aboutToShow.connect(self.focus_current_variant)
        self.choices = QActionGroup(self.menu)
        self.button.setMenu(self.menu)
        row.addWidget(self.button)

        self.copy_button = QToolButton()
        self.copy_button.setObjectName('variantCopyButton')
        self.copy_button.setText('Copiar entrada')
        self.copy_button.clicked.connect(self.copy_previous_input)
        self.copy_button.hide()
        row.addWidget(self.copy_button)
        row.addStretch(1)
        self.hide()

    def set_entry(self, entry, item):
        key = normalized_key(item)
        self.memory[entry['key']] = key
        if self.entry is not entry or self.current_key != key:
            self.clear_copy()
        if self.entry is not entry:
            self.entry = entry
            self.build_menu()
        self.current_key = key
        changed = len(self.options) > 1
        if changed:
            self.options[key].setChecked(True)
            self.fit_title()
        self.setVisible(changed)

    def build_menu(self):
        self.menu.clear()
        self.options.clear()
        variants = self.entry['variants']
        if len(variants) == 1:
            return
        if len(self.entry['dimensions']) > 1:
            sections = [(group, list(options)) for group, options in groupby(variants, key=lambda pair: pair[1][0])]
        else:
            sections = [('', variants)]
        for index, (section, options) in enumerate(sections):
            heading = bool(section and len(options) > 1)
            if heading:
                # Fusion displays native titled separators as rules under a stylesheet.
                self.menu.addAction(section).setEnabled(False)
            elif index > 0:
                self.menu.addSeparator()
            for key, _ in options:
                route = self.window.route_for_key(key)
                action = self.menu.addAction(variant_title(self.entry, key, omit_group=heading))
                action.setCheckable(True)
                action.setToolTip(detail_for(route)['summary'])
                action.triggered.connect(lambda checked=False, chosen=key: self.select(chosen))
                self.choices.addAction(action)
                self.options[key] = action

    def fit_title(self):
        if self.current_key not in self.options:
            return
        title = variant_title(self.entry, self.current_key)
        row = self.layout()
        margins = row.contentsMargins()
        available = self.width() - margins.left() - margins.right() - self.caption.sizeHint().width() - row.spacing()
        if not self.copy_button.isHidden():
            available -= self.copy_button.sizeHint().width() + row.spacing()
        self.button.setText(self.button.fontMetrics().elidedText(title, Qt.TextElideMode.ElideRight, max(90, available - 40)))
        self.button.setAccessibleName('Cambiar variante. Actual: ' + title)
        self.button.setToolTip(title + '\nCambiar variante · Alt+V')

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_title()

    def open_menu(self):
        if self.isVisible():
            self.button.showMenu()

    def focus_current_variant(self):
        if self.current_key in self.options:
            self.menu.setActiveAction(self.options[self.current_key])

    def select(self, key):
        if key == self.current_key:
            return
        previous = variant_title(self.entry, self.current_key)
        source = self.window.pages.get(self.window.current_operation)
        route = self.window.route_for_key(key)
        existed = route in self.window.pages
        self.window.open_tool(route)
        target = self.window.pages.get(route)
        if source is None or target is None or source is target:
            return
        with passive_fields():
            plan = prepare_inputs(source, target)
            if not existed:
                self.window.statusBar().showMessage(plan.apply(), 10000)
            elif plan.actions:
                self.copy_source = source
                self.copy_button.setToolTip(f'Reemplazar los datos compatibles con los de «{previous}».')
                self.copy_button.show()
                self.fit_title()
            else:
                self.window.statusBar().showMessage(plan.note, 10000)

    def copy_previous_input(self):
        target = self.window.pages.get(self.window.current_operation)
        if self.copy_source is not None and target is not None:
            with passive_fields():
                note = prepare_inputs(self.copy_source, target).apply()
            workspace = getattr(target, 'workspace', None)
            if workspace is not None:
                workspace.show_inputs()
            self.window.statusBar().showMessage(note, 10000)
            self.clear_copy()
            self.fit_title()

    def clear_copy(self):
        self.copy_source = None
        self.copy_button.hide()

    def reset(self):
        self.clear_copy()
        self.memory.clear()
        self.menu.clear()
        self.options.clear()
        self.entry = self.current_key = None
        self.hide()
