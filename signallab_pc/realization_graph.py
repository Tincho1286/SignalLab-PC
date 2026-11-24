"""Editable SISO block diagrams and their exact zero-state transfer."""

from dataclasses import asdict, dataclass
import math


BLOCK_NAMES = {
    'input': 'Entrada', 'output': 'Salida', 'gain': 'Ganancia',
    'sum': 'Sumador', 'memory': 'Memoria', 'transfer': 'Transferencia',
}
LEFT_INPUT = 1
LOWER_INPUT = 2
DEFAULT_SUM_SIGNS = (1, -1)


@dataclass(frozen=True)
class Block:
    id: int
    kind: str
    x: float
    y: float
    gain: str = '1'
    formula: str = '1'
    sample_period_s: float | None = None
    input_signs: tuple[int, int] = DEFAULT_SUM_SIGNS


@dataclass(frozen=True)
class Wire:
    source: int
    target: int
    sign: int = 1
    target_port: int | None = None

    @property
    def sum_port(self):
        if self.target_port is not None:
            return self.target_port
        return LEFT_INPUT if self.sign > 0 else LOWER_INPUT

    def sign_at(self, target):
        return target.input_signs[self.sum_port - 1] if target.kind == 'sum' else self.sign


@dataclass(frozen=True)
class RealizationGraph:
    domain: str
    blocks: tuple[Block, ...]
    wires: tuple[Wire, ...]

    @classmethod
    def empty(cls, domain):
        return cls(domain, (Block(1, 'input', 0, 0), Block(2, 'output', 580, 0)), ())

    def to_document(self):
        blocks = []
        has_transfer = False
        custom_signs = False
        for block in self.blocks:
            row = asdict(block)
            if block.kind == 'transfer':
                has_transfer = True
            else:
                del row['formula'], row['sample_period_s']
            if block.input_signs == DEFAULT_SUM_SIGNS:
                del row['input_signs']
            else:
                custom_signs = True
                row['input_signs'] = list(block.input_signs)
            blocks.append(row)
        wires = []
        for wire in self.wires:
            row = asdict(wire)
            if wire.target_port is None:
                del row['target_port']
            else:
                custom_signs = True
            wires.append(row)
        return {
            'kind': 'signallab-realization', 'version': 3 if custom_signs else 2 if has_transfer else 1,
            'domain': self.domain,
            'blocks': blocks,
            'wires': wires,
        }

    @classmethod
    def from_document(cls, document):
        try:
            if document['kind'] != 'signallab-realization' or document['version'] not in (1, 2, 3):
                raise ValueError('Elegí un diagrama editable de SignalLab (JSON).')
            blocks = tuple(Block(**{**row, 'input_signs': tuple(row.get('input_signs', DEFAULT_SUM_SIGNS))})
                           for row in document['blocks'])
            graph = cls(document['domain'], blocks,
                        tuple(Wire(**row) for row in document['wires']))
            graph.connections()
        except (KeyError, TypeError, AttributeError, OverflowError) as exc:
            raise ValueError('El archivo no contiene un diagrama de realización válido.') from exc
        return graph

    @property
    def sample_period_s(self):
        from .system_clock import common_period

        return common_period(*self.blocks)

    def connections(self):
        from .system_clock import validate_period

        if self.domain not in ('analog', 'digital'):
            raise ValueError('Elegí un dominio continuo o discreto.')
        by_id = {}
        incoming = {}
        ports = []
        for block in self.blocks:
            if type(block.id) is not int or block.id < 1 or block.id in by_id or block.kind not in BLOCK_NAMES:
                raise ValueError('El diagrama contiene un bloque desconocido o repetido.')
            if any(not isinstance(value, (float, int)) or not math.isfinite(value) or abs(value) > 1e7
                   for value in (block.x, block.y)):
                raise ValueError('El diagrama contiene una posición inválida.')
            if not isinstance(block.gain, str) or not isinstance(block.formula, str):
                raise ValueError(f'La definición del bloque {block.id} debe ser una fórmula.')
            if (len(block.input_signs) != 2 or any(type(sign) is not int or sign not in (-1, 1)
                                                   for sign in block.input_signs)
                    or block.kind != 'sum' and block.input_signs != DEFAULT_SUM_SIGNS):
                raise ValueError(f'Los signos de entrada del bloque {block.id} no son válidos.')
            if block.sample_period_s is not None:
                if block.kind != 'transfer' or not isinstance(block.sample_period_s, (float, int)):
                    raise ValueError(f'El reloj del bloque {block.id} no es válido.')
                validate_period(block.sample_period_s, self.domain)
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
            if wire.target_port is not None and (target.kind != 'sum' or type(wire.target_port) is not int
                                                 or wire.target_port not in (LEFT_INPUT, LOWER_INPUT)):
                raise ValueError('El puerto de destino del sumador no es válido.')
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

    def connections_for_transfer(self):
        incoming = self.connections()
        _ = self.sample_period_s  # Imported discrete blocks must use a common clock.
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
        return incoming, input_id, output_id, nodes

    def transfer(self):
        import sympy as sp
        from .resources import ensure_working_set
        from .scalar_expression import exact_constant
        from .symbolic import S, Z

        incoming, input_id, output_id, nodes = self.connections_for_transfer()

        # q is one unit delay (discrete) or one integration (continuous).
        # With q=0 only direct paths remain. They must uniquely define the
        # instantaneous signals before the state update can be performed.
        order = len(nodes)
        ensure_working_set(order * order, bytes_per_sample=256, live_arrays=8)
        q = sp.Dummy('q')
        variable = Z if self.domain == 'digital' else S
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
            elif block.kind == 'transfer':
                try:
                    gain = sp.cancel(_transfer_expression(block.formula, self.domain).subs(variable, 1 / q))
                except (SyntaxError, TypeError, ValueError) as exc:
                    raise ValueError(f'Revisá la transferencia del bloque {block.id}: {exc}') from exc
            for wire in incoming[block.id]:
                term = wire.sign_at(block) * gain
                if wire.source == input_id:
                    rhs[row, 0] = term
                else:
                    index = (row, indices[wire.source])
                    entries[index] = entries.get(index, 0) - term

        matrix = sp.SparseMatrix(order, order, entries)
        if sp.simplify(matrix.subs(q, 0).det()) == 0:
            raise ValueError('El lazo instantáneo no determina una salida única. Revisá los signos y ganancias del lazo o incorporá memoria donde corresponda.')
        solution, = sp.linsolve((matrix, sp.SparseMatrix(order, 1, rhs)))
        return sp.cancel(solution[indices[output_id]].subs(q, 1 / variable))


def _transfer_expression(source, domain):
    import sympy as sp
    from .symbolic import S, Z, parse

    variable = Z if domain == 'digital' else S
    raw = parse(source)
    if not isinstance(raw, sp.Expr) or raw.free_symbols - {variable}:
        raise ValueError(f'Usá {variable} y coeficientes constantes en la transferencia.')
    expression = sp.cancel(raw)
    if expression.has(sp.nan, sp.zoo, sp.oo, -sp.oo) or not expression.is_rational_function(variable):
        raise ValueError(f'Ingresá una transferencia racional en {variable}, con denominador no nulo.')
    numerator, denominator = sp.fraction(expression)
    if sp.degree(numerator, variable) > sp.degree(denominator, variable):
        reason = 'contiene un avance de muestras' if domain == 'digital' else 'necesita un derivador ideal'
        raise ValueError(f'El bloque {reason}. Ingresá una transferencia propia en {variable}.')
    return expression


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
