"""Edit or reuse a transfer function inside a diagram block."""

from dataclasses import replace

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QLineEdit, QPushButton, QVBoxLayout


class TransferBlockDialog(QDialog):
    accepts_system_expressions = True

    def __init__(self, block, domain, owner, parent):
        super().__init__(parent)
        self.block = block
        self.domain = domain
        self.variable = 'z' if domain == 'digital' else 's'
        self.sample_period_s = block.sample_period_s
        self.setWindowTitle(f'Transferencia del bloque {block.id}')
        self.resize(480, 160)
        layout = QVBoxLayout(self)
        label = QLabel(f'H{block.id}({self.variable})')
        layout.addWidget(label)
        self.formula = QLineEdit(block.formula)
        self.formula.setPlaceholderText('Ejemplo: 1/(1-0.5*z^(-1))' if domain == 'digital' else 'Ejemplo: 1/(s+1)')
        self.formula.setAccessibleName('Fórmula de transferencia')
        self.formula.selectAll()
        label.setBuddy(self.formula)
        layout.addWidget(self.formula)

        if owner is not None:
            from .system_import import SystemImporter

            load = QPushButton('Cargar sistema…')
            self.importer = SystemImporter(load, owner, self.receive_system, None, domains=[domain], allow_advance=False)
            layout.addWidget(load)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        use = buttons.button(QDialogButtonBox.StandardButton.Ok)
        use.setText('Usar transferencia')
        use.setObjectName('primary')
        use.setEnabled(bool(self.formula.text().strip()))
        self.formula.textChanged.connect(lambda text: use.setEnabled(bool(text.strip())))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('Cancelar')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def receive_system(self, system, key=None):
        from .filters import Transfer
        from .phase_summary import transfer_formula
        from .system_conditions import require_causal_roc

        if system.domain != self.domain:
            raise ValueError(f'Este bloque requiere una transferencia en {self.variable}.')
        require_causal_roc(system, operation='El diagrama usa bloques causales.')
        def formula(value):
            return transfer_formula(value, digits=17)[0].text.partition('=')[2].strip()

        if system.sos is not None:
            expression = '*'.join(f'({formula(Transfer(row[:3], row[3:]))})' for row in system.sos)
        else:
            expression = formula(system)
        self.formula.setText(expression)
        self.sample_period_s = system.sample_period_s

    def load_expression(self, expression, key=None, record=None):
        from .transform_context import result_period, result_roc

        if expression.variable != self.variable:
            raise ValueError(f'Este bloque requiere una transferencia en {self.variable}.')
        roc = result_roc(record)
        if roc and roc['mode'] != 'right':
            raise ValueError('La región de convergencia guardada no es derecha. Usá un bloque causal en el diagrama.')
        self.sample_period_s = result_period(record)
        self.formula.setText(expression.source)

    def definition(self):
        return replace(self.block, formula=self.formula.text().strip(), sample_period_s=self.sample_period_s)
