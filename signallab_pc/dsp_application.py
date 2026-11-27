"""Typed adapters for existing DSP motors; no presentation dependencies."""

from dataclasses import dataclass, field
from math import gcd

import numpy as np

from . import filters, fourier, operations, sampling
from .execution import ExecutionContext
from .model import Signal
from .operation_provenance import content_digest, encoded_digest, scientific_metadata, verify_inputs
from .project import Project


def _finish_signal(result, inputs, expected, ctx, *, auxiliary=None):
    output = content_digest(result, ctx.checkpoint)
    auxiliary_digest = None if auxiliary is None else content_digest(auxiliary, ctx.checkpoint)
    ctx.checkpoint(100)
    verify_inputs(inputs, expected, ctx.checkpoint)
    result._core_verification = (output, expected, auxiliary_digest)
    return result


def verify_dsp_signal(value):
    proof = getattr(value, '_core_verification', None)
    if proof is None:
        raise ValueError('El resultado DSP carece de procedencia válida. Volvé a calcular.')
    return proof


@dataclass(frozen=True, slots=True)
class IDFTRequest:
    spectrum: Signal
    restore_origin: bool = True


@dataclass(frozen=True, slots=True)
class IDFTParameters:
    bins: int
    centered: bool
    restore_origin: bool
    phase_reference: str


def calculate_idft(request: IDFTRequest, execution: ExecutionContext | None = None) -> Signal:
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    source = request.spectrum
    expected = (content_digest(source, ctx.checkpoint),)
    result = ctx.run(lambda: operations.idft(source, restore_origin=request.restore_origin),
                     work_bytes=int(source.values.size) * operations.DFT_WORK_BYTES_PER_BIN)
    provenance = source.metadata.get('dft_provenance')
    if isinstance(provenance, dict) and isinstance(units := provenance.get('input_units'), str) and units:
        result.units = units
    if isinstance(units := source.metadata.get('amplitude_units'), str):
        result.metadata['amplitude_units'] = units
    spec = IDFTParameters(int(source.values.size), operations.is_centered_dft(source),
                          request.restore_origin, result.metadata['input_dft_phase_reference'])
    result.metadata['core_provenance'] = scientific_metadata('idft', spec)
    return _finish_signal(result, (source,), expected, ctx)


@dataclass(frozen=True, slots=True)
class FIRDesignRequest:
    kind: str
    taps: int
    f1: float
    f2: float | None = None
    window: str = 'hamming'
    beta: float = 8.6
    sample_period_s: float | None = None


@dataclass(frozen=True, slots=True)
class FIRDesignResult:
    transfer: filters.Transfer
    specification: FIRDesignRequest
    _verification: tuple[str, str] | None = field(default=None, repr=False, compare=False)


def design_fir(request: FIRDesignRequest, execution: ExecutionContext | None = None) -> FIRDesignResult:
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    taps = filters.positive_integer(request.taps, 'Cantidad de coeficientes')
    model = ctx.run(lambda: filters.fir(request.kind, taps, request.f1, request.f2,
                                        request.window, request.beta),work_bytes=taps * 112)
    if request.sample_period_s is not None:
        model = filters.Transfer(model.b, model.a, name=model.name, roc=model.roc,
                                 sample_period_s=request.sample_period_s)
    spec = FIRDesignRequest(request.kind, taps, float(request.f1),
                            float(request.f2) if request.kind in ('bandpass','bandstop') else None,
                            request.window, float(request.beta), model.sample_period_s)
    ctx.checkpoint(100)
    definition = scientific_metadata('fir_design', spec)
    return FIRDesignResult(model, spec, (content_digest(model, ctx.checkpoint),
                                         encoded_digest('calculation', definition, ctx.checkpoint)))


@dataclass(frozen=True, slots=True)
class FIRRequest:
    signal: Signal
    transfer: filters.Transfer
    mode: str = 'same'


@dataclass(frozen=True, slots=True)
class FIRParameters:
    mode: str
    taps: int
    input_origin: int
    input_length: int


def fir_output_count(model, mode, n):
    if not is_causal_fir(model):
        raise ValueError('La aplicación FIR requiere un filtro digital causal en coeficientes.')
    if mode not in {'same', 'full'}:
        raise ValueError('El modo FIR debe ser same o full.')
    return n if mode == 'same' else n + len(model.b) - 1


def is_causal_fir(transfer):
    return (transfer.domain == 'digital' and not transfer.advance
            and transfer.sos is None and not np.any(transfer.a[1:]))


def apply_fir(request: FIRRequest, execution: ExecutionContext | None = None) -> Signal:
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    source = request.signal
    count = fir_output_count(request.transfer, request.mode, int(source.values.size))
    from .signal_semantics import require_temporal
    require_temporal(source)
    if source.domain != 'discrete':
        raise ValueError('El filtro FIR requiere una secuencia discreta.')
    from .resources import ensure_working_set
    ensure_working_set(count + len(request.transfer.b), live_arrays=8)
    inputs = (source, request.transfer)
    expected = tuple(content_digest(value, ctx.checkpoint) for value in inputs)

    def filter_record():
        working = source
        if count != source.values.size:
            working = source.copy_with(values=np.pad(source.values, (0, count - source.values.size)))
        return request.transfer.apply(working)

    result = ctx.run(filter_record,work_bytes=(count + len(request.transfer.b)) * 128)
    spec = FIRParameters(request.mode, len(request.transfer.b), source.origin, int(source.values.size))
    result.metadata['core_provenance'] = scientific_metadata('fir_apply', spec)
    if isinstance(units := source.metadata.get('amplitude_units'), str):
        result.metadata['amplitude_units'] = units
    return _finish_signal(result, inputs, expected, ctx)


@dataclass(frozen=True, slots=True)
class ResampleRequest:
    signal: Signal
    up: int
    down: int
    rate: float | None = None
    start: float | None = None
    half_width: int = 10
    beta: float = 5.0
    boundary: str = 'zero'
    override_clock: bool = False
    return_filter: bool = False


@dataclass(frozen=True, slots=True)
class ResampleParameters:
    up: int
    down: int
    input_rate_hz: float
    half_width: int
    beta: float
    boundary: str
    override_clock: bool
    input_origin: int
    time_start_s: float | None


@dataclass(frozen=True, slots=True)
class ResampleResult:
    signal: Signal
    antialias: filters.Transfer | None = None
    warning: str | None = None


def resample_size(request):
    up = sampling.positive_integer(request.up, 'L')
    down = sampling.positive_integer(request.down, 'M')
    width = sampling.positive_integer(request.half_width, 'Semilongitud por fase')
    common = gcd(up, down)
    up, down = up // common, down // common
    n = int(request.signal.values.size)
    length = (n * up + down - 1) // down
    taps = 1 if up == down else 2 * width * max(up, down) + 1
    return up, down, width, length, (length + n + taps) * 256


def resample(request: ResampleRequest, execution: ExecutionContext | None = None) -> ResampleResult:
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    up, down, width, _, estimate = resample_size(request)
    inputs = (request.signal,)
    expected = (content_digest(request.signal, ctx.checkpoint),)
    value = ctx.run(lambda: sampling.resample_rational(
        request.signal, up, down, rate=request.rate, start=request.start, half_width=width,
        beta=request.beta, boundary=request.boundary, override_clock=request.override_clock,
        return_filter=request.return_filter),work_bytes=estimate)
    result = ResampleResult(*value) if request.return_filter else ResampleResult(value)
    meta = result.signal.metadata
    spec = ResampleParameters(up, down, meta['input_rate_hz'], width, meta['kaiser_beta'],
                              request.boundary, request.override_clock,
                              request.signal.origin, meta.get('time_start_s'))
    meta['core_provenance'] = scientific_metadata('resample', spec)
    if isinstance(units := request.signal.metadata.get('amplitude_units'), str):
        meta['amplitude_units'] = units
    _finish_signal(result.signal, inputs, expected, ctx, auxiliary=result.antialias)
    return result


@dataclass(frozen=True, slots=True)
class PSDRequest:
    signal: Signal
    rate: float | None = None
    method: str = 'welch'
    segment: int = 256
    overlap: int = 128
    window: str = 'hann'
    beta: float = 5.0
    remove_mean: bool = False
    sidedness: str = 'two-sided'
    maximum_lag: int | None = None
    nfft: int | None = None
    time_bandwidth: float | None = None
    tapers: int | None = None
    ar_order: int | None = None


@dataclass(frozen=True, slots=True)
class PSDParameters:
    method: str
    segment: int
    overlap: int
    sample_rate_hz: float
    window: str
    beta: float
    remove_mean: bool
    sidedness: str


def estimate_psd(request: PSDRequest, execution: ExecutionContext | None = None) -> Signal:
    ctx = execution or ExecutionContext()
    ctx.checkpoint(0)
    source = request.signal
    rate = request.rate if request.rate is not None else source.metadata.get('sample_rate_hz')
    if rate is None:
        raise ValueError('Indicá Fs para estimar la densidad espectral.')
    if request.sidedness not in {'two-sided', 'one-sided'}:
        raise ValueError('Elegí una PSD unilateral o bilateral.')
    if request.sidedness == 'one-sided' and (request.method == 'legacy' or np.any(source.values.imag)):
        raise ValueError('La PSD unilateral requiere una señal real y una normalización de densidad.')
    advanced = request.method in ('blackman_tukey','multitaper','ar')
    if (request.maximum_lag is not None and request.method != 'blackman_tukey'
            or (request.time_bandwidth is not None or request.tapers is not None) and request.method != 'multitaper'
            or request.ar_order is not None and request.method != 'ar'
            or request.nfft is not None and not advanced):
        raise ValueError('Un parámetro espectral no corresponde al estimador seleccionado.')
    if advanced:
        from .statistical_spectra import advanced_density
        expected = (content_digest(source,ctx.checkpoint),)
        result = advanced_density(source,method=request.method,rate=rate,nfft=request.nfft,max_lag=request.maximum_lag,
                                  bandwidth=request.time_bandwidth,tapers=request.tapers,order=request.ar_order,
                                  remove_mean=request.remove_mean,execution=ctx)
        if request.sidedness == 'one-sided':
            result=_fold_density(result)
        specification={key:result.metadata[key] for key in ('nfft','sample_rate_hz','sidedness','remove_mean',
            'max_lag','lag_window','time_bandwidth','tapers','ar_order') if key in result.metadata}
        result.metadata['core_provenance']={'schema':1,'operation':'psd','method':request.method,**specification}
        return _finish_signal(result,(source,),expected,ctx)
    segmented = request.method in ('welch','bartlett')
    segment = sampling.positive_integer(request.segment, 'Longitud de segmento') if segmented else int(source.values.size)
    expected = (content_digest(source, ctx.checkpoint),)
    result = ctx.run(lambda: fourier.spectral_density(
        source, rate, method=request.method, segment=segment, overlap=request.overlap,
        window=request.window, beta=request.beta, remove_mean=request.remove_mean),work_bytes=segment * 256)
    metadata = result.metadata
    if request.sidedness == 'one-sided':
        result=_fold_density(result)
    amplitude_units = source.metadata.get('amplitude_units')
    if isinstance(amplitude_units, str) and amplitude_units:
        metadata['density_units'] = f'{amplitude_units}²' + ('/Hz' if request.method != 'legacy' else '')
    spec = PSDParameters(request.method, metadata['segment'], metadata['overlap'], float(rate),
                         metadata['window'], 0. if request.method=='bartlett' else float(request.beta),
                         request.remove_mean, request.sidedness)
    metadata['core_provenance'] = scientific_metadata('psd', spec)
    return _finish_signal(result, (source,), expected, ctx)


def _fold_density(result):
    size=len(result.values)
    bins=np.fft.ifftshift(result.values).real[:size//2+1].copy()
    bins[1:(None if size%2 else -1)] *= 2
    if not np.isfinite(bins).all():
        raise FloatingPointError('La PSD unilateral excede el rango finito.')
    result.metadata['sidedness']='one-sided, power folded'
    return Signal(bins,0.,result.step,result.units,result.name,'frequency',metadata=result.metadata)


def stage_signal(project: Project, value: Signal, *, parents=(), execution: ExecutionContext) -> str:
    """Add verified signal data to an open project transaction."""
    execution.checkpoint()
    parents = tuple(parents)
    verification = None
    if 'core_provenance' in value.metadata or hasattr(value, '_core_verification'):
        output, expected, auxiliary = verify_dsp_signal(value)
        if auxiliary is not None:
            expected += (auxiliary,)
        if parents and len(parents) != len(expected):
            raise ValueError('Indicá todos los orígenes utilizados, en orden de cálculo.')
        if parents:
            unique = {}
            for key, digest in zip(parents, expected, strict=True):
                if key in unique and unique[key] != digest:
                    raise ValueError('Un origen repetido debe representar los mismos datos.')
                unique[key] = digest
            parents, expected = tuple(unique), tuple(unique.values())
        verification = (output, expected if parents else (), execution.checkpoint)
    return project.add(value, operation=value.metadata.get('operation', ''), parents=parents, verification=verification)


def store_signal(project: Project, value: Signal, *, parents=(), execution=None) -> str:
    ctx = execution or ExecutionContext()
    with project.stage_records(before_commit=ctx.checkpoint) as staged:
        return stage_signal(staged, value, parents=parents, execution=ctx)


def store_fir_design(project: Project, design: FIRDesignResult, *, execution=None) -> tuple[str, str]:
    ctx = execution or ExecutionContext()
    ctx.checkpoint()
    proof = design._verification
    if proof is None:
        raise ValueError('El diseño FIR carece de procedencia válida. Volvé a calcular.')
    with project.stage_records(before_commit=ctx.checkpoint) as staged:
        model_digest, spec_digest = proof
        model = staged.add(design.transfer, operation='Diseño FIR', verification=(model_digest, (), ctx.checkpoint))
        spec = staged.add(scientific_metadata('fir_design', design.specification), operation='Especificación FIR',
                          parents=(model,), verification=(spec_digest, (model_digest,), ctx.checkpoint))
    return model, spec
