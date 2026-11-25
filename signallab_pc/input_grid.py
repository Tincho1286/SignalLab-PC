"""An instant reading of the grid being entered, independent of the signal calculation."""

import math

from PySide6.QtCore import QObject, QTimer

from .engine import sequence_parts
from .numeric_input import integer_field, real_field
from .result_summary import number
from .validation import passive_fields


class InputGrid(QObject):
    def __init__(self, source):
        super().__init__(source)
        self.source = source
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(160)
        self.timer.timeout.connect(self.refresh)
        for field in (source.origin, source.step, source.count, source.samples):
            field.textChanged.connect(self.schedule)
        source.mode.currentIndexChanged.connect(self.schedule)
        if hasattr(source, 'frequency_units'):
            source.frequency_units.currentIndexChanged.connect(self.schedule)
        self.refresh()

    def schedule(self, *_):
        self.timer.start()

    @passive_fields()
    def refresh(self):
        source = self.source
        mode = source.mode.currentIndex()
        if mode == 2:
            return
        formula = mode == 0
        repeated = hasattr(source, 'repeat_period') and source.repeat_period.isChecked()
        try:
            if formula or repeated:
                count = integer_field(source.count, minimum=1)
            else:
                count = len(sequence_parts(source.samples.text()))
            if source.kind not in ('continuous', 'frequency'):
                first = integer_field(source.origin)
                last = first + count - 1
                if not -(1 << 63) <= first <= last < (1 << 63):
                    raise ValueError('El intervalo excede los índices enteros de 64 bits.')
                symbol = 'k' if getattr(source, 'dft_input', False) or getattr(source, 'role', None) == 'series_coefficients' else 'n'
                unit = ''
            else:
                first = real_field(source.origin)
                spacing = real_field(source.step, minimum=0, strict=True)
                last = first + (count - 1) * spacing
                if not math.isfinite(last) or count > 1 and first + spacing == first:
                    raise ValueError('Ajustá el inicio, el paso o la cantidad para distinguir los puntos del eje.')
                unit = source.frequency_units.currentText() if source.kind == 'frequency' else 's'
                symbol = {'rad/s': 'Ω', 'Hz': 'f'}.get(unit, 'ω') if source.kind == 'frequency' else 't'
        except (ValueError, OverflowError) as exc:
            source.range_note.setText('Revisá el eje · ' + str(exc).split(' Detalle:', 1)[0])
            return
        start, stop = number(first), number(last)
        if first != last and start == stop:
            start, stop = repr(first), repr(last)
        interval = f'{symbol} = {start}' if count == 1 else f'{symbol} de {start} a {stop}'
        quantity = '1 valor' if count == 1 else f'{count} valores'
        source.range_note.setText(f'{interval}{f" {unit}" if unit else ""} · {quantity}')
