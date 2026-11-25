"""Application boundary for one finite, forward DFT."""

from collections.abc import Callable
from dataclasses import asdict, dataclass
import math
from threading import Event
from time import monotonic

from . import jobs, operations
from .model import Signal
from .project import Project
from .resources import ResourceLimitError


@dataclass(frozen=True, slots=True)
class DFTRequest:
    signal: Signal
    length: int | None = None
    centered: bool = True
    phase_reference: str = 'sample_indices'


@dataclass(frozen=True, slots=True)
class DFTExecution:
    max_work_bytes: int | None = None
    deadline: float | None = None
    cancel: Event | None = None
    progress: Callable[[int], None] | None = None

    def __post_init__(self):
        if self.max_work_bytes is not None and (
            type(self.max_work_bytes) is not int or self.max_work_bytes < 1
        ):
            raise ValueError('El presupuesto de memoria debe ser un entero positivo en bytes.')
        if self.deadline is not None and not math.isfinite(self.deadline):
            raise ValueError('El plazo monotónico debe ser finito.')

    def checkpoint(self, percentage=None):
        jobs.checkpoint()
        if self.cancel is not None and self.cancel.is_set():
            raise jobs.OperationCancelled('Cálculo cancelado; se descartó el resultado.')
        if self.deadline is not None and monotonic() >= self.deadline:
            raise TimeoutError('Se agotó el plazo de ejecución de la DFT.')
        if percentage is not None:
            jobs.checkpoint(percentage / 100)
            if self.progress is not None:
                self.progress(percentage)
            self.checkpoint()


@dataclass(frozen=True, slots=True)
class DFTProvenance:
    length: int
    centered: bool
    phase_reference: str
    input_units: str
    input_origin: int
    input_length: int
    sample_rate_hz: float | None
    time_start_s: float | None


@dataclass(frozen=True, slots=True)
class DFTResult:
    spectrum: Signal
    provenance: DFTProvenance
    estimated_work_bytes: int


def calculate_dft(request: DFTRequest, execution: DFTExecution | None = None) -> DFTResult:
    execution = execution or DFTExecution()
    execution.checkpoint(0)
    if not isinstance(request.signal, Signal):
        raise TypeError('La DFT requiere una Signal.')
    if type(request.centered) is not bool:
        raise ValueError('El orden centrado debe ser un booleano.')
    length = operations.dft_length(request.signal, request.length)
    estimate = length * operations.DFT_WORK_BYTES_PER_BIN
    if execution.max_work_bytes is not None and estimate > execution.max_work_bytes:
        raise ResourceLimitError(
            f'La DFT estima {estimate} bytes de trabajo; el presupuesto es {execution.max_work_bytes}.'
        )
    execution.checkpoint()
    spectrum = operations.dft(request.signal, length, centered=request.centered,
                              phase_reference=request.phase_reference)
    clock = spectrum.metadata['input_clock']
    provenance = DFTProvenance(length, request.centered, request.phase_reference,
                               request.signal.units, spectrum.metadata['input_origin'],
                               spectrum.metadata['input_length'], clock.get('sample_rate_hz'),
                               clock.get('time_start_s'))
    spectrum.metadata['dft_provenance'] = {'schema': 1, 'operation': 'dft', **asdict(provenance)}
    execution.checkpoint(100)
    return DFTResult(spectrum, provenance, estimate)


def store_dft(project: Project, result: DFTResult, *, source_id=None, source=None,
              source_parents=(), source_operation='Entrada DFT', operation='DFT',
              tool=None, execution: DFTExecution | None = None) -> tuple[str | None, str]:
    """Publish a complete result and, when supplied, its new source together."""
    execution = execution or DFTExecution()
    execution.checkpoint()
    if source is not None and (source_id is not None or not isinstance(source, Signal)):
        raise ValueError('Indicá una señal nueva o el identificador de su registro existente.')
    with project.stage_records(before_commit=execution.checkpoint) as staged:
        if source is not None:
            source_id = staged.add(source, operation=source_operation, parents=source_parents, tool=tool)
        result_id = staged.add(result.spectrum, operation=operation,
                               parents=() if source_id is None else (source_id,), tool=tool)
    return source_id, result_id
