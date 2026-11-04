"""Physical sampling context, independent of digital frequency in rad/sample."""
from copy import deepcopy
import math

UNSET=object()

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
    step=1/rate;end=start+(count-1)*step
    if not math.isfinite(end) or count>1 and (start+step==start or end-step==end or step<max(math.ulp(start),math.ulp(end))):
        raise ValueError('El reloj de salida excede la resolución o el rango numérico.')


def common_period(*systems):
    periods=[system.sample_period_s for system in systems if system.sample_period_s is not None]
    if not periods:return None
    if any(not math.isclose(period,periods[0],rel_tol=1e-12,abs_tol=0) for period in periods):raise ValueError('Los sistemas registran distintos períodos de muestreo. Igualá su reloj antes de conectarlos; no se cambia la tasa automáticamente.')
    return periods[0]

def input_metadata(system,source):
    if source.domain!='discrete':raise ValueError('La entrada del filtro discreto debe ser una secuencia.')
    from .signal_semantics import require_temporal
    require_temporal(source)
    metadata=dict(source.metadata);rate=metadata.get('sample_rate_hz');period=system.sample_period_s
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
