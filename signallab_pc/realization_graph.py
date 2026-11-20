"""Editable SISO block diagrams and their exact zero-state transfer."""

from dataclasses import asdict, dataclass
import math


BLOCK_NAMES = {
    'input': 'Entrada', 'output': 'Salida', 'gain': 'Ganancia',
    'sum': 'Sumador', 'memory': 'Memoria',
}


@dataclass(frozen=True)
class Block:
    id: int
    kind: str
    x: float
    y: float
    gain: str = '1'


@dataclass(frozen=True)
class Wire:
    source: int
    target: int
    sign: int = 1


@dataclass(frozen=True)
class RealizationGraph:
    domain: str
    blocks: tuple[Block, ...]
    wires: tuple[Wire, ...]

    @classmethod
    def empty(cls, domain):
        return cls(domain, (Block(1, 'input', 0, 0), Block(2, 'output', 580, 0)), ())

    def to_document(self):
        return {
            'kind': 'signallab-realization', 'version': 1, 'domain': self.domain,
            'blocks': [asdict(block) for block in self.blocks],
            'wires': [asdict(wire) for wire in self.wires],
        }

    @classmethod
    def from_document(cls, document):
        try:
            if document['kind'] != 'signallab-realization' or document['version'] != 1:
                raise ValueError('Elegí un diagrama editable de SignalLab (JSON).')
            graph = cls(document['domain'], tuple(Block(**row) for row in document['blocks']),
                        tuple(Wire(**row) for row in document['wires']))
            graph.connections()
        except (KeyError, TypeError, AttributeError, OverflowError) as exc:
            raise ValueError('El archivo no contiene un diagrama de realización válido.') from exc
        return graph

    def connections(self):
        if self.domain not in ('analog', 'digital'):
            raise ValueError('Elegí un dominio continuo o discreto.')
        by_id = {}
        incoming = {}
        ports = []
        for block in self.blocks:
            if type(block.id) is not int or block.id < 1 or block.id in by_id or block.kind not in BLOCK_NAMES:
                raise ValueError('El diagrama contiene un bloque desconocido o repetido.')
            if any(not isinstance(value, (float, int)) or not math.isfinite(value) or abs(value) > 1e7
                   for value in (block.x, block.y)) or not isinstance(block.gain, str):
                raise ValueError('El diagrama contiene una posición o ganancia inválida.')
            if block.kind in ('input', 'output'):
                ports.append(block.kind)
            by_id[block.id] = block
            incoming[block.id] = []
        if sorted(ports) != ['input', 'output']:
            raise ValueError('El diagrama requiere una entrada x y una salida y.')

        connected = set()
        for wire in self.wires:
            if (type(wire.sign) is not int or wire.sign not in (-1, 1) or
                    type(wire.source) is not int or type(wire.target) is not int or
                    wire.source not in by_id or wire.target not in by_id):
                raise ValueError('Hay una conexión inválida entre bloques.')
            source, target = by_id[wire.source], by_id[wire.target]
            if source.kind == 'output' or target.kind == 'input':
                raise ValueError('La entrada x sólo emite señales y la salida y sólo las recibe.')
            pair = (source.id, target.id)
            if pair in connected:
                raise ValueError('Esos bloques ya están conectados en ese sentido.')
            if target.kind != 'sum' and incoming[target.id]:
                raise ValueError(f'Agregá un sumador antes de conectar varias señales al bloque {target.id}.')
            connected.add(pair)
            incoming[target.id].append(wire)
        return incoming

    def transfer(self):
        import sympy as sp
        from .resources import ensure_working_set
        from .scalar_expression import exact_constant
        from .symbolic import S, Z

        incoming = self.connections()
        input_id = next(block.id for block in self.blocks if block.kind == 'input')
        output_id = next(block.id for block in self.blocks if block.kind == 'output')
        nodes = [block for block in self.blocks if block.id != input_id]
        for block in nodes:
            if not incoming[block.id]:
                raise ValueError(f'Conectá una señal a {BLOCK_NAMES[block.kind].lower()} {block.id}.')

        # Keep autonomous feedback branches that feed y. Flag dangling branches
        # instead of silently treating an unfinished drawing as a transfer.
        visited, pending = {output_id}, [output_id]
        while pending:
            for wire in incoming[pending.pop()]:
                if wire.source not in visited:
                    visited.add(wire.source)
                    pending.append(wire.source)
        if input_id not in visited:
            raise ValueError('Conectá un camino desde la entrada x hasta la salida y.')
        if len(visited) < len(self.blocks):
            loose = next(block.id for block in self.blocks if block.id not in visited)
            raise ValueError(f'El bloque {loose} no tiene camino hacia la salida y.')

        # q is one unit delay (discrete) or one integration (continuous).
        # With q=0 only direct paths remain. They must uniquely define the
        # instantaneous signals before the state update can be performed.
        order = len(nodes)
        ensure_working_set(order * order, bytes_per_sample=256, live_arrays=8)
        q = sp.Dummy('q')
        indices = {block.id: row for row, block in enumerate(nodes)}
        entries = {(row, row): sp.S.One for row in range(order)}
        rhs = {}
        for row, block in enumerate(nodes):
            gain = q if block.kind == 'memory' else sp.S.One
            if block.kind == 'gain':
                try:
                    gain = exact_constant(block.gain)
                except (SyntaxError, TypeError, ValueError) as exc:
                    raise ValueError(f'Revisá la ganancia del bloque {block.id}: {exc}') from exc
            for wire in incoming[block.id]:
                term = wire.sign * gain
                if wire.source == input_id:
                    rhs[row, 0] = term
                else:
                    index = (row, indices[wire.source])
                    entries[index] = entries.get(index, 0) - term

        matrix = sp.SparseMatrix(order, order, entries)
        if sp.simplify(matrix.subs(q, 0).det()) == 0:
            raise ValueError('El lazo instantáneo no determina una salida única. Revisá los signos y ganancias del lazo o incorporá memoria donde corresponda.')
        solution, = sp.linsolve((matrix, sp.SparseMatrix(order, 1, rhs)))
        variable = Z if self.domain == 'digital' else S
        return sp.cancel(solution[indices[output_id]].subs(q, 1 / variable))


def graph_from_realization(value):
    """Convert the direct-form diagram already shown in the analysis results."""
    blocks, wires = [], []

    def block(kind, x, y, gain='1'):
        ident = len(blocks) + 1
        blocks.append(Block(ident, kind, x, y, gain))
        return ident

    def gain_text(value):
        real, imag = float(value.real), float(value.imag)
        return repr(real) if not imag else f'{real!r}+({imag!r})*i'

    previous = block('input', 0, 0)
    for index, stage in enumerate(value.stages):
        x = 160 + index * 720
        direct = previous
        if stage.order:
            direct = block('sum', x, 0)
            wires.append(Wire(previous, direct))
        taps = [direct]
        for k in range(1, stage.order + 1):
            memory = block('memory', x + 180, k * 100)
            wires.append(Wire(taps[-1], memory))
            taps.append(memory)
            feedback = block('gain', x, k * 100, gain_text(-stage.a[k]))
            wires.extend((Wire(memory, feedback), Wire(feedback, direct)))
        forward = [block('gain', x + 360, k * 100, gain_text(stage.b[k])) for k in range(stage.order + 1)]
        wires.extend(Wire(tap, gain) for tap, gain in zip(taps, forward))
        previous = forward[0]
        if stage.order:
            previous = block('sum', x + 540, 0)
            wires.extend(Wire(gain, previous) for gain in forward)
    output = block('output', 160 + len(value.stages) * 720, 0)
    wires.append(Wire(previous, output))
    return RealizationGraph(value.domain, tuple(blocks), tuple(wires))
