"""Read the equations from the same ports and signs the solver uses."""
from collections import defaultdict

from .realization_graph import BLOCK_NAMES, signal_name
from .result_summary import Formula, Section, Summary


def signed_sum(terms):
    pieces = []
    for coefficient, signal in terms:
        if not coefficient:
            continue
        sign = (' + ' if coefficient > 0 else ' - ') if pieces else ('' if coefficient > 0 else '-')
        magnitude = abs(coefficient)
        pieces.append(sign + (f'{magnitude}*' if magnitude != 1 else '') + signal)
    return ''.join(pieces) or '0'


def summary(graph):
    domain = graph.domain
    variable = 'z' if domain == 'digital' else 's'
    title = f'Ecuaciones en {variable}'
    try:
        incoming = graph.connections()
    except ValueError as error:
        return Summary(title, [Section('Revisá las conexiones', paragraphs=[str(error)])])
    sections = [Section('', paragraphs=[
        f'Vᵢ({variable}) es la salida del bloque i. Para resolver H({variable}) con estado inicial nulo, elegí Usar diagrama y calculá el análisis.',
    ])]
    names = {block.id: signal_name(block, domain) for block in graph.blocks}
    ordered = sorted(graph.blocks, key=lambda block: (block.kind == 'output', block.id))
    for block in ordered:
        if block.kind == 'input':
            continue
        name = BLOCK_NAMES[block.kind]
        if block.kind == 'memory':
            name = 'Retardo unitario' if domain == 'digital' else 'Integrador'
        heading = name if block.kind == 'output' else f'{name} {block.id}'
        wires = incoming[block.id]
        if not wires:
            sections.append(Section(heading, paragraphs=['Falta conectar la entrada.']))
            continue
        terms = []
        signs = defaultdict(set)
        coefficients = defaultdict(int)
        for wire in sorted(wires, key=lambda wire: wire.sum_port) if block.kind == 'sum' else wires:
            sign = wire.sign_at(block)
            signs[wire.source].add(sign)
            coefficients[wire.source] += sign
            terms.append((sign, names[wire.source]))
        expression = signed_sum(terms)
        gain = {'transfer': block.formula, 'gain': block.gain,
                'memory': '1/z' if domain == 'digital' else '1/s'}.get(block.kind)
        if gain is not None:
            expression = f'({gain})*({expression})'
        signal = names[block.id]
        equation = f'{signal} = {expression}'
        notes = []
        feedback = block.kind == 'sum' and block.id in signs
        cancellation = any(len(values) == 2 for values in signs.values())
        if feedback:
            notes.append('La salida vuelve al mismo sumador. Al reunir sus términos se obtiene la segunda ecuación.')
        if cancellation:
            notes.append('La misma señal entra por ambos puertos con signos opuestos. Esos términos se cancelan.')
        formulas = [Formula(equation, equation)]
        if feedback or cancellation:
            left = signed_sum([(1 - coefficients.pop(block.id, 0), signal)])
            right = signed_sum((coefficient, names[source]) for source, coefficient in coefficients.items())
            reduced = f'{left} = {right}'
            formulas.append(Formula(f'Eq({left}, {right})', reduced))
        sections.append(Section(heading, paragraphs=notes, formulas=formulas))
    return Summary(title, sections)
