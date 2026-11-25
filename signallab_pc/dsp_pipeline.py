"""Sequential DSP demonstration with one project commit."""

from dataclasses import dataclass, field, fields, replace

from .dft_application import DFTRequest, DFTResult, calculate_dft, verify_dft_result
from .dsp_application import (
    FIRRequest, PSDRequest, ResampleRequest, ResampleResult, apply_fir,
    estimate_psd, fir_output_count, resample, resample_size, verify_dsp_signal,
)
from .execution import ExecutionContext
from .filters import Transfer
from .model import Signal
from .operations import DFT_WORK_BYTES_PER_BIN, dft_length
from .operation_provenance import content_digest, settings_digest, verify_inputs
from .project import Project
from .resources import ensure_working_set
from .sampling import positive_integer


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
    _verification: tuple[str, str | None] | None = field(default=None, repr=False, compare=False)


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


@dataclass(frozen=True, slots=True)
class PipelineMemory:
    input_bytes: int
    retained_bytes: int
    work_bytes: int

    @property
    def total_bytes(self):
        return self.input_bytes + self.retained_bytes + self.work_bytes


def _psd_segment(request, count):
    if request.psd_method != 'welch':
        return count
    return (positive_integer(request.psd_segment,'Longitud de segmento')
            if request.psd_segment is not None else min(256,count))


def estimate_pipeline_memory(request: DSPPipelineRequest) -> PipelineMemory:
    x = request.conversion.signal
    try:
        up, down, width, converted, resampling_work = resample_size(request.conversion)
    except ValueError as error:
        raise PipelineStageError('Resampling',error) from error
    try:
        filtered = fir_output_count(request.fir,request.fir_mode,converted)
    except ValueError as error:
        raise PipelineStageError('FIR',error) from error
    try:
        bins = dft_length(x,request.dft_length) if request.dft_length is not None else filtered
    except ValueError as error:
        raise PipelineStageError('DFT',error) from error
    try:
        segment = _psd_segment(request, filtered)
        if segment > filtered:
            raise ValueError('La longitud de segmento supera la señal filtrada.')
    except ValueError as error:
        raise PipelineStageError('PSD',error) from error
    taps = len(request.fir.b)
    aa = (1 if up==down else 2*width*max(up,down)+1) if request.conversion.return_filter else 0
    retained = 16*(converted+filtered+bins+segment+aa)
    scratch = max(resampling_work,(filtered+taps)*128,bins*DFT_WORK_BYTES_PER_BIN,segment*256)
    return PipelineMemory(int(x.values.nbytes + request.fir.b.nbytes),retained,scratch)


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
    memory = estimate_pipeline_memory(request)
    ensure_working_set(memory.total_bytes,bytes_per_sample=1,live_arrays=1)
    with ctx.reserve(memory.total_bytes):
        inputs = (source, request.fir)
        expected = tuple(content_digest(value, ctx.checkpoint) for value in inputs)
        settings = _request_digest(request)
        result = _run_stages(request, replace(ctx, pool=None))
        verify_inputs(inputs, expected, ctx.checkpoint)
        if settings != _request_digest(request):
            raise ValueError('Los parámetros del flujo cambiaron durante el cálculo.')
        return replace(result, _verification=(settings, result.resampled.warning))


def _run_stages(request, ctx):
    converted = _stage(ctx, 0, 'Resampling', lambda child: resample(request.conversion, child))
    filtered = _stage(ctx, 1, 'FIR', lambda child: apply_fir(
        FIRRequest(converted.signal, request.fir, request.fir_mode), child))
    dft = _stage(ctx, 2, 'DFT', lambda child: calculate_dft(DFTRequest(filtered, request.dft_length), child))
    segment = _psd_segment(request,int(filtered.values.size))
    overlap = request.psd_overlap if request.psd_overlap is not None else segment // 2
    psd = _stage(ctx, 3, 'PSD', lambda child: estimate_psd(PSDRequest(
        filtered, method=request.psd_method, segment=segment, overlap=overlap, window=request.psd_window), child))
    ctx.checkpoint()
    return DSPPipelineResult(converted, filtered, dft, psd)


def _request_digest(request):
    parameters = {f.name: getattr(request, f.name) for f in fields(request) if f.name not in {'conversion', 'fir'}}
    parameters['conversion'] = {f.name: getattr(request.conversion, f.name)
                                for f in fields(request.conversion) if f.name != 'signal'}
    return settings_digest(parameters)


def store_pipeline(project: Project, request: DSPPipelineRequest, result: DSPPipelineResult, *,
                   source_id=None, filter_id=None, execution: ExecutionContext | None = None) -> PipelineRecords:
    ctx = execution or ExecutionContext()
    ctx.checkpoint()
    if result._verification != (_request_digest(request), result.resampled.warning):
        raise ValueError('El resultado requiere los parámetros originales del flujo DSP.')
    converted_digest, (source_digest,), antialias_digest = verify_dsp_signal(result.resampled.signal)
    filtered_digest, filter_parents, _ = verify_dsp_signal(result.filtered)
    dft_parent, dft_digest = verify_dft_result(result.dft)
    psd_digest, psd_parents, _ = verify_dsp_signal(result.psd)
    if (result.resampled.antialias is None) != (antialias_digest is None):
        raise ValueError('El filtro antialias cambió después del cálculo.')
    if source_id is not None:
        verify_inputs((request.conversion.signal,), (source_digest,), ctx.checkpoint)
    if filter_id is not None:
        verify_inputs((request.fir,), filter_parents[1:], ctx.checkpoint)
    with project.stage_records(before_commit=ctx.checkpoint) as staged:
        if source_id is None:
            source_id = staged.add(request.conversion.signal, operation='Entrada del flujo DSP')
        if filter_id is None:
            filter_id = staged.add(request.fir, operation='Filtro del flujo DSP')
        antialias = None
        parents = (source_id,)
        converted_parents = (source_digest,)
        if result.resampled.antialias is not None:
            antialias = staged.add(result.resampled.antialias, operation='FIR antialias', parents=parents,
                                   verification=(antialias_digest, (source_digest,), ctx.checkpoint))
            parents += (antialias,)
            converted_parents += (antialias_digest,)
        converted = staged.add(result.resampled.signal, operation='Cambio de tasa', parents=parents,
                               verification=(converted_digest, converted_parents, ctx.checkpoint))
        filtered = staged.add(result.filtered, operation='Aplicar FIR', parents=(converted, filter_id),
                              verification=(filtered_digest, filter_parents, ctx.checkpoint))
        dft = staged.add(result.dft.spectrum, operation='DFT', parents=(filtered,),
                         verification=(dft_digest, (dft_parent,), ctx.checkpoint))
        psd = staged.add(result.psd, operation='PSD', parents=(filtered,),
                         verification=(psd_digest, psd_parents, ctx.checkpoint))
    return PipelineRecords(source_id, filter_id, converted, filtered, dft, psd, antialias)
