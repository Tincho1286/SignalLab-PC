"""Reading guidance tied to the tool's current configuration."""

from dataclasses import dataclass

from PySide6.QtWidgets import QComboBox, QFormLayout, QLineEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox


@dataclass(frozen=True)
class GuideContext:
    label: str
    instructions: str
    diagram: str = ''


def configured_guide(route, panel):
    if panel is None:
        return None
    kind, task = route[1:3]
    if kind == 'transform_lab':
        inverse = panel.mode.currentIndex() == 1
        if task == 'z':
            if inverse:
                return GuideContext(
                    'Inversa · X(z) → x[n]',
                    'Ingresá X(z) y elegí su región de convergencia. Si pedís muestras, el intervalo sólo determina qué índices se evalúan. La fórmula describe la secuencia completa.',
                    'Cómo elegir la región de convergencia',
                )
            if panel.direct_input.currentIndex() == 1:
                return GuideContext('Directa · Secuencia finita',
                                    'Cargá los valores y su primer índice. La suma Z incluye cada muestra en su índice n y toma cero fuera del registro.')
            return GuideContext('Directa · Expresión x[n]',
                                'Escribí la fórmula en n e indicá los extremos que incluye la suma. Usá -oo u oo para un soporte infinito.')
        bilateral = panel.interpretation.currentIndex() == 1
        label = ('Inversa' if inverse else 'Directa') + (' · Bilateral' if bilateral else ' · Unilateral')
        if inverse and bilateral:
            return GuideContext(label, 'Ingresá X(s) y elegí una franja de convergencia. Los polos a su izquierda producen términos hacia t positivo y los de su derecha hacia t negativo.', 'ROC y soporte temporal')
        if inverse:
            return GuideContext(label, 'Ingresá X(s). La inversa unilateral se expresa para t positivo y conserva los impulsos de Dirac, incluido el origen.')
        if bilateral:
            return GuideContext(label, 'Definí x(t) para todo el eje. Usá tramos o escalones si sólo existe a uno de los lados.')
        return GuideContext(label, 'Ingresá x(t). El cálculo unilateral integra desde 0− y conserva el impulso en el origen.')
    if kind == 'course_tools' and task in ('fir', 'iir', 'analog'):
        editor = panel.band_edges
        units = 'rad/s' if task == 'analog' else 'rad/muestra'
        band = editor.kind.currentText()
        tolerance = panel.fields['tolerance_units'].currentText()
        method = 'FIR' if task == 'fir' else 'IIR analógico' if task == 'analog' else 'IIR digital'
        return GuideContext(f'{method} · {band}',
                            f'Cargá los bordes numerados en {units}, en orden creciente. La unidad de tolerancia seleccionada es {tolerance}. Verde indica paso, ámbar rechazo y gris transición.',
                            band)
    if (kind, task) == ('system_analysis', 0):
        mode = panel.definition_mode.currentIndex()
        digital = panel.domain.currentIndex() == 1
        domain = 'H(z)' if digital else 'H(s)'
        instructions = (
            'Numerador y denominador se escriben en potencias de z⁻¹, empezando en la constante.' if digital
            else 'Numerador y denominador se escriben en potencias descendentes de s.',
            f'Ingresá una expresión en {"z" if digital else "s"}. Asigná valores a los parámetros si necesitás evaluar un gráfico.',
            f'Ingresá la respuesta en w, en {"rad/muestra" if digital else "rad/s"}. Podés usar condiciones por tramos.',
            'Agregá bloques y conectá sus puertos desde x hasta y. Los signos de los sumadores se aplican a cada entrada. Consultá Ecuaciones para comprobar el circuito antes de calcular.',
        )
        labels = ('Coeficientes', 'Fórmula', 'Respuesta en frecuencia', 'Diagrama')
        if 0 <= mode < len(labels):
            return GuideContext(f'{domain} · {labels[mode]}', instructions[mode])
    if (kind, task) == ('systems', 9):
        digital = panel.domain.currentIndex() == 1
        mode = panel.stimulus.currentIndex()
        variable = 'n' if digital else 't'
        starts = ('Usá el escalón unitario desde ' + variable + '=0.',
                  'En discreto se aplica una muestra unitaria en n=0.' if digital else 'El impulso continuo se representa por su área de Dirac.',
                  'Definí una entrada propia. Su primer punto fija el inicio de la simulación.')
        if 0 <= mode < len(starts):
            return GuideContext(('H(z)' if digital else 'H(s)') + ' · ' + panel.stimulus.currentText(),
                                starts[mode] + ' La salida y corresponde a la entrada aplicada y a las condiciones iniciales elegidas.')
    return None


def field_in_focus(page, focus):
    """Return the visible label of an editor before the workspace changes."""
    if page is None or focus is None or not page.isAncestorOf(focus):
        return ''
    workspace = getattr(page, 'workspace', None)
    if workspace is not None and not workspace.inputs.isAncestorOf(focus):
        return ''
    editors = (QComboBox, QLineEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox)
    if not isinstance(focus, editors):
        return ''
    widget = focus
    while widget is not None and widget is not page:
        if widget.accessibleName():
            return widget.accessibleName()
        parent = widget.parentWidget()
        layout = parent.layout() if parent is not None else None
        if isinstance(layout, QFormLayout):
            label = layout.labelForField(widget)
            if label is not None and hasattr(label, 'text'):
                return label.text()
        widget = parent
    return 'Campos de entrada'
