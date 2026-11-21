"""Physical sampling context, independent of digital frequency in rad/sample."""
from copy import deepcopy
import math

UNSET=object()
CLOCK_MAPPING = 't = time_start_s + (n-origin)/sample_rate_hz'

def validate_period(period,domain='digital'):
    if period is None:return None
    if isinstance(period,bool) or domain!='digital':raise ValueError('El período físico sólo corresponde a un sistema discreto y debe ser un número positivo.')
    period=float(period)
    if not math.isfinite(period) or period<=0:raise ValueError('El período T debe ser positivo y finito.')
    return period

def validate_clock_resolution(start,rate,count):
    start=float(start);rate=float(rate)
    if not math.isfinite(start) or not math.isfinite(rate) or rate<=0:
        raise ValueError('El reloj requiere un tiempo inicial finito y una tasa positiva.')
    validate_time_step(start,1/rate,count)


def validate_time_step(start,step,count):
    if not math.isfinite(start) or not math.isfinite(step) or step<=0:
        raise ValueError('El reloj requiere un inicio finito y un paso positivo.')
    from .model import validate_uniform_axis
    try:
        validate_uniform_axis(float(start), float(step), count)
    except ValueError as exc:
        raise ValueError('El reloj de salida excede la resolución o el rango numérico.') from exc


def common_period(*systems):
    periods=[system.sample_period_s for system in systems if system.sample_period_s is not None]
    if not periods:return None
    if any(not math.isclose(period,periods[0],rel_tol=1e-12,abs_tol=0) for period in periods):raise ValueError('Los sistemas registran distintos períodos de muestreo. Igualá su reloj antes de conectarlos; no se cambia la tasa automáticamente.')
    return periods[0]

def common_rate(*sources):
    from .sampling import positive_finite
    rates=[positive_finite(rate,'Fs registrada') for source in sources
           if (rate:=source.metadata.get('sample_rate_hz')) is not None]
    if not rates:return None
    if any(not math.isclose(rate,rates[0],rel_tol=1e-12,abs_tol=0) for rate in rates[1:]):
        raise ValueError('Las secuencias registran distintas tasas de muestreo. Igualá sus relojes antes de combinarlas.')
    return rates[0]

def _start(source):
    value = source.metadata.get('time_start_s')
    if value is not None:
        value = float(value)
        if not math.isfinite(value):
            raise ValueError('El inicio del reloj debe ser finito.')
    return value


def validate_discrete_clocks(first, second):
    """For index alignment, a shared index must map to the same time."""
    rate = common_rate(first, second)
    left, right = _start(first), _start(second)
    if any(source.metadata.get('sample_rate_hz') is None for source in (first, second)):
        return None
    if left is not None and right is not None:
        offset = (int(second.origin) - int(first.origin)) / rate
        interval = 1 / rate
        if not math.isfinite(offset) or not math.isfinite(interval):
            raise ValueError('La alineación del reloj excede el rango numérico.')
        error = abs(math.fsum((right, -left, -offset)))
        tolerance = min(interval / 4, max(interval * 1e-9, math.ulp(left)+math.ulp(right)))
        if error > tolerance:
            raise ValueError('Los tiempos físicos registrados no corresponden a los mismos índices. Revisá los orígenes de las entradas.')
    return rate


def combined_clock(first, second, origin, count, *, mode):
    """Propagate sampling context based on how the output is indexed."""
    if mode in ('sum', 'product'):
        rate = validate_discrete_clocks(first, second)
        if mode == 'product':
            # An index-defined mask applies to the first record's grid.
            rate = first.metadata.get('sample_rate_hz')
            start = _start(first)
        else:
            start = (_start(first) + (origin-first.origin)/rate
                     if rate is not None and all(_start(x) is not None for x in (first, second)) else None)
    else:
        rate = common_rate(first, second)
        left, right = _start(first), _start(second)
        if any(source.metadata.get('sample_rate_hz') is None for source in (first, second)):
            return {}
        start = None
        if left is not None and right is not None:
            if mode == 'convolution':
                start = left + right
            else:
                shift = origin - (first.origin-second.origin)
                if mode == 'periodic_correlation':
                    shift = shift % count
                start = math.fsum((left, -right, shift/rate))
    if rate is None:
        return {}
    clock = {'sample_rate_hz': float(rate)}
    if start is not None:
        validate_clock_resolution(start, rate, count)
        clock.update(time_start_s=start, time_mapping=CLOCK_MAPPING)
    return clock


def lag_clock(rate, origin, count):
    """A lag is a time difference with its zero fixed at equal sample indices."""
    if rate is None:
        return {}
    start = origin / rate
    validate_clock_resolution(start, rate, count)
    return dict(sample_rate_hz=rate, time_start_s=start, time_mapping=CLOCK_MAPPING)


def spectrum_clock(source,metadata=None):
    metadata=source.metadata if metadata is None else metadata
    return {'input_origin':int(source.origin),'input_clock':{
        key:metadata[key] for key in ('sample_rate_hz','time_start_s') if key in metadata}}


def inverse_spectrum_clock(spectrum,start,count):
    clock=spectrum.metadata.get('input_clock',{})
    if not isinstance(clock,dict):raise ValueError('El reloj de origen del espectro no es válido.')
    rate=clock.get('sample_rate_hz')
    if rate is None:
        period=spectrum.metadata.get('period_s') if spectrum.data_kind=='frequency_response' else None
        if period is None:return {}
        period=validate_period(period)
        rate=1/period
        clock={'time_start_s':0.}
        origin=0
    else:
        origin=spectrum.metadata.get('input_origin')
    from .sampling import positive_finite
    rate=positive_finite(rate,'Fs de origen del espectro')
    result={'sample_rate_hz':rate}
    if type(origin) is int and 'time_start_s' in clock:
        t0=float(clock['time_start_s'])+(start-origin)/rate
        validate_clock_resolution(t0,rate,count)
        result['time_start_s']=t0
    return result


def input_metadata(system,source):
    return input_period_metadata(system.sample_period_s,source)


def input_period_metadata(period,source):
    if source.domain!='discrete':raise ValueError('La entrada del filtro discreto debe ser una secuencia.')
    from .signal_semantics import require_temporal
    require_temporal(source)
    metadata=dict(source.metadata);rate=metadata.get('sample_rate_hz')
    if rate is not None:
        rate=float(rate)
        if not math.isfinite(rate) or rate<=0:raise ValueError('La entrada debe registrar una tasa de muestreo positiva y finita.')
        if period is not None and not math.isclose(1/rate,period,rel_tol=1e-12,abs_tol=0):raise ValueError('La tasa de la señal no coincide con el período T del sistema. Revisá el reloj o cambiá la tasa antes de filtrar.')
    elif period is not None:
        rate=1/period
        if not math.isfinite(rate):raise ValueError('La tasa 1/T excede el rango numérico disponible.')
        metadata['sample_rate_hz']=rate
    if period is not None and 'time_start_s' not in metadata:
        start=source.origin*period
        if not math.isfinite(start):raise ValueError('El inicio físico del registro excede el rango numérico.')
        metadata['time_start_s']=start
    if 'time_start_s' in metadata and not math.isfinite(float(metadata['time_start_s'])):raise ValueError('El inicio del reloj debe ser finito.')
    return metadata

def signature(editor):
    mode=getattr(editor,'definition_mode',None);formula=getattr(editor,'transfer_formula',None)
    return (editor.domain.currentIndex(),editor.b.text(),editor.a.text(),mode.currentIndex() if mode is not None else None,formula.text() if formula is not None else None)

def editor_period(editor):
    field=getattr(editor,'sample_period',None)
    if field is not None:
        if editor.domain.currentIndex()!=1:return UNSET
        if not field.text().strip():return None
        from .numeric_input import real_field
        return validate_period(real_field(field))
    if getattr(editor,'_clock_signature',None)==signature(editor):return editor._clock_period
    return UNSET

def remember_period(editor,period):
    field=getattr(editor,'sample_period',None)
    if field is not None:field.setText('' if period is None else repr(float(period)))
    elif getattr(editor,'action',None)=='convert' and period is not None:editor.fields['period'].setText(repr(float(period)))
    editor._clock_period=period;editor._clock_signature=signature(editor)

def apply_period(system,period):
    if system is None or system.domain!='digital' or period is UNSET or period==system.sample_period_s:return system
    result=deepcopy(system)
    result.sample_period_s=validate_period(period)
    return result
