"""Sequential DSP demonstration with one project commit."""

from dataclasses import dataclass, replace

from .dft_application import DFTRequest, DFTResult, calculate_dft
from .dsp_application import (
    FIRRequest, PSDRequest, ResampleRequest, ResampleResult, apply_fir,
    estimate_psd, resample,
)
from .execution import ExecutionContext
from .filters import Transfer
from .model import Signal
from .project import Project


@dataclass(frozen=True, slots=True)
class DSPPipelineRequest:
    conversion: ResampleRequest
    fir: Transfer
    fir_mode: str = 'same'
    dft_length: int | None = None
    psd_method: str = 'welch'
    psd_segment: int | None = None
    psd_overlap: int | None = None
    psd_window: str = 'hann'
    amplitude_units: str | None = None


@dataclass(frozen=True, slots=True)
class DSPPipelineResult:
    resampled: ResampleResult
    filtered: Signal
    dft: DFTResult
    psd: Signal


@dataclass(frozen=True, slots=True)
class PipelineRecords:
    source: str
    filter: str
    resampled: str
    filtered: str
    dft: str
    psd: str
    antialias: str | None


class PipelineStageError(ValueError):
    def __init__(self, stage, error):
        self.stage = stage
        super().__init__(f'{stage}: {error}')


def _stage(ctx, index, name, operation):
    ctx.checkpoint()

    def update(percentage):
        ctx.progress(index * 25 + percentage // 4)

    child = replace(ctx, progress=update if ctx.progress is not None else None)
    try:
        return operation(child)
    except (ValueError, FloatingPointError) as error:
        raise PipelineStageError(name, error) from error


def run_pipeline(request: DSPPipelineRequest, execution: ExecutionContext | None = None) -> DSPPipelineResult:
    ctx = execution or ExecutionContext()
    ctx.checkpoint()
    source = request.conversion.signal
    if request.amplitude_units is not None and source.metadata.get('amplitude_units') != request.amplitude_units:
        raise PipelineStageError('Entrada', 'La unidad de amplitud no coincide con la requerida.')
    converted = _stage(ctx, 0, 'Resampling', lambda child: resample(request.conversion, child))
    filtered = _stage(ctx, 1, 'FIR', lambda child: apply_fir(
        FIRRequest(converted.signal, request.fir, request.fir_mode), child))
    dft = _stage(ctx, 2, 'DFT', lambda child: calculate_dft(DFTRequest(filtered, request.dft_length), child))
    segment = request.psd_segment if request.psd_segment is not None else min(256, int(filtered.values.size))
    overlap = request.psd_overlap if request.psd_overlap is not None else segment // 2
    psd = _stage(ctx, 3, 'PSD', lambda child: estimate_psd(PSDRequest(
        filtered, method=request.psd_method, segment=segment, overlap=overlap, window=request.psd_window), child))
    ctx.checkpoint()
    return DSPPipelineResult(converted, filtered, dft, psd)


def store_pipeline(project: Project, request: DSPPipelineRequest, result: DSPPipelineResult, *,
                   source_id=None, filter_id=None, execution: ExecutionContext | None = None) -> PipelineRecords:
    ctx = execution or ExecutionContext()
    ctx.checkpoint()
    with project.stage_records(before_commit=ctx.checkpoint) as staged:
        if source_id is None:
            source_id = staged.add(request.conversion.signal, operation='Entrada del flujo DSP')
        if filter_id is None:
            filter_id = staged.add(request.fir, operation='Filtro del flujo DSP')
        antialias = None
        parents = (source_id,)
        if result.resampled.antialias is not None:
            antialias = staged.add(result.resampled.antialias, operation='FIR antialias', parents=parents)
            parents += (antialias,)
        converted = staged.add(result.resampled.signal, operation='Cambio de tasa', parents=parents)
        filtered = staged.add(result.filtered, operation='Aplicar FIR', parents=(converted, filter_id))
        dft = staged.add(result.dft.spectrum, operation='DFT', parents=(filtered,))
        psd = staged.add(result.psd, operation='PSD', parents=(filtered,))
    return PipelineRecords(source_id, filter_id, converted, filtered, dft, psd, antialias)
