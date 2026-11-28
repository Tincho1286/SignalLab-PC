"""Diseño analógico por tolerancias de amplitud y bordes angulares."""
import numpy as np
from scipy.optimize import brentq
from scipy import signal as sp
from .filters import Transfer
from .resources import ensure_working_set
from .jobs import checkpoint
from .communications_data import integer

FAMILIES={'butter':'Butterworth','cheby1':'Chebyshev I','cheby2':'Chebyshev II','ellip':'Elíptico'}
BESSEL_NORMALIZATIONS = {
    'phase': 'Fase: Ωn fija el punto medio de la transición de fase del prototipo.',
    'delay': 'Retardo: el prototipo pasabajos tiene τg(0) = 1/Ωn.',
    'mag': 'Magnitud: el prototipo tiene |H(jΩn)| = 1/√2.',
}
MAX_BESSEL_ORDER = 25
_BESSEL_ROUTING = {
    'lowpass': sp.lp2lp_zpk, 'highpass': sp.lp2hp_zpk,
    'bandpass': sp.lp2bp_zpk, 'bandstop': sp.lp2bs_zpk,
}


def _checked_transfer(zpk, name, grid):
    z, p, k = zpk
    b, a = sp.zpk2tf(z, p, k)
    system = Transfer(b, a, 'analog', name, roc={'mode': 'right'})
    _, reference = sp.freqs_zpk(z, p, k, worN=grid)
    response = system.response(grid)
    if not np.isfinite(response).all() or not np.isfinite(reference).all():
        raise ValueError('Respuesta no finita: revisá escala de frecuencias, orden y tolerancias.')
    disagreement = float(np.max(abs(response-reference)/np.maximum(1, abs(reference))))
    if disagreement > 1e-5:
        raise ValueError('Los coeficientes expandidos pierden precisión para este diseño. Relajá tolerancias o escala.')
    return system, disagreement


def _checked_bessel_zpk(builder, *args, **kwargs):
    try:
        with np.errstate(over='raise', invalid='raise', divide='raise', under='ignore'):
            return builder(*args, **kwargs)
    except (OverflowError, FloatingPointError) as exc:
        raise ValueError('El escalado de Bessel excede la representación numérica.') from exc


def bessel_prototype(order, characteristic_rad_s, *, kind='lowpass', normalization='phase'):
    """Design a fixed-order analog Bessel filter with an explicitly normalized prototype."""
    order = integer(order, 'Orden del prototipo', minimum=1, maximum=MAX_BESSEL_ORDER)
    if kind not in _BESSEL_ROUTING or normalization not in BESSEL_NORMALIZATIONS:
        raise ValueError('Elegí un tipo de filtro y una normalización Bessel válidos.')
    edge = np.asarray(characteristic_rad_s)
    size = 2 if kind in ('bandpass', 'bandstop') else 1
    valid_shape = edge.shape == (size,) or (size == 1 and edge.ndim == 0)
    if edge.dtype.kind not in 'fiu' or not valid_shape:
        raise ValueError(f'Indicá {size} frecuencia(s) característica(s) real(es) en rad/s.')
    edge = np.asarray(edge, dtype=float).reshape(-1)
    if not np.isfinite(edge).all() or np.any(edge <= 0) or np.any(np.diff(edge) <= 0):
        raise ValueError('Las frecuencias características deben ser positivas, finitas y crecientes.')
    lower, upper = edge[0] / 100, edge[-1] * 100
    if lower <= 0 or not np.isfinite(upper):
        raise ValueError('Las frecuencias características exceden el rango numérico del diseño.')
    final_order = order * size
    ensure_working_set(final_order**2 + 4099, live_arrays=10)
    zpk = _checked_bessel_zpk(sp.bessel, order, edge if size == 2 else edge[0], btype=kind,
                              analog=True, output='zpk', norm=normalization)
    grid = np.unique(np.r_[0, np.geomspace(lower, upper, 4097), edge])
    system, error = _checked_transfer(zpk, 'Bessel analógico', grid)
    report = [
        'Diseño analógico Bessel', '',
        BESSEL_NORMALIZATIONS[normalization],
        'La normalización se define sobre el prototipo. Para otras bandas se aplica la transformación analógica correspondiente.',
        f'Orden del prototipo: {order}', f'Orden del denominador: {final_order}',
        'Frecuencias características (rad/s): ' + ', '.join(f'{value:.12g}' for value in edge),
        f'Diferencia de representación: {error:.3g}',
    ]
    if len(edge) == 2:
        center = np.sqrt(edge[0])*np.sqrt(edge[1])
        report.extend((f'Centro geométrico: {center:.12g} rad/s',
                       f'Anchura entre frecuencias características: {edge[1]-edge[0]:.12g} rad/s'))
    checkpoint()
    return {'report': '\n'.join(report), 'signals': [], 'systems': [system],
            'design_metadata': {'kind': kind, 'family': 'bessel', 'order': order, 'normalization': normalization,
                                'characteristic_rad_s': edge.tolist()}}


def _bessel_by_bands(wp, ws, dp, ds, kind):
    """Fix the pass-edge mapping, then find the first order that meets both bands."""
    if dp < 64*np.finfo(float).eps:
        raise ValueError('La tolerancia de paso queda por debajo de la resolución numérica de Bessel.')
    if kind == 'lowpass':
        stop_ratio = ws[0] / wp[0]
    elif kind == 'highpass':
        stop_ratio = wp[0] / ws[0]
    else:
        center = np.sqrt(wp[0]) * np.sqrt(wp[1])
        bandwidth = wp[1] - wp[0]
        with np.errstate(over='ignore', divide='ignore', invalid='ignore'):
            difference = np.abs(ws - center) * (1 + center/ws)
            ratio = difference / bandwidth if kind == 'bandpass' else bandwidth / difference
        stop_ratio = np.min(ratio)
    for order in range(1, MAX_BESSEL_ORDER + 1):
        checkpoint(order / MAX_BESSEL_ORDER)
        zpk = sp.besselap(order, norm='phase')
        _, poles, gain = zpk
        log_gain = np.log(abs(gain))

        def log_magnitude(angular):
            return log_gain - np.log(np.hypot(poles.real, angular - poles.imag)).sum()

        def crossing(target):
            def residual(log_w):
                magnitude = log_gain - order * log_w if log_w > 50 else log_magnitude(np.exp(log_w))
                return magnitude - target
            return brentq(residual, -40, 800, xtol=2e-14)

        log_pass = crossing(np.log1p(-dp))
        with np.errstate(over='ignore'):
            stop = log_magnitude(np.exp(log_pass) * stop_ratio)
        if stop <= np.log(ds) + 64*np.finfo(float).eps:
            # Choose a scale inside the admissible interval when both masks allow it.
            # A stop edge at exactly the bandstop centre is always attenuated.
            if np.isfinite(stop_ratio):
                log_stop = crossing(np.log(ds)) - np.log(stop_ratio)
                angular = np.exp((min(log_stop, log_pass) + log_pass) / 2)
            else:
                angular = np.exp(log_pass) / 2
            if kind == 'lowpass':
                transform = {'wo': wp[0] / angular}
            elif kind == 'highpass':
                transform = {'wo': wp[0] * angular}
            else:
                transform = {'wo': center, 'bw': bandwidth / angular if kind == 'bandpass' else bandwidth * angular}
            zeros, poles, gain = _checked_bessel_zpk(_BESSEL_ROUTING[kind], *zpk, **transform)
            # A few ulps of headroom keep the represented pass plateau below its upper bound.
            return order, (zeros, poles, gain * (1 - 8*np.finfo(float).eps))
    return None

def design(wp,ws,dp,ds,method):
    wp=np.asarray(wp,float);ws=np.asarray(ws,float)
    if wp.ndim!=1 or wp.shape!=ws.shape or wp.size not in (1,2) or not np.all(np.isfinite(np.r_[wp,ws])) or np.any(np.r_[wp,ws]<=0):raise ValueError('Usá uno o dos bordes por banda, positivos y finitos en rad/s.')
    if wp.size==1 and wp[0]!=ws[0]:kind='lowpass' if wp[0]<ws[0] else 'highpass'
    elif wp.size==2 and ws[0]<wp[0]<wp[1]<ws[1]:kind='bandpass'
    elif wp.size==2 and wp[0]<ws[0]<ws[1]<wp[1]:kind='bandstop'
    else:raise ValueError('Las bandas deben estar ordenadas y separadas por transiciones positivas.')
    if not 0<dp<1 or not 0<ds<1-dp:raise ValueError('Usá 0 < δp < 1 y 0 < δs < 1−δp.')
    methods=list(FAMILIES) if method in ('compare','compare_rf') else [method]
    if method=='compare_rf':methods.append('bessel')
    if any(m not in FAMILIES and m!='bessel' for m in methods):raise ValueError('Familia de filtro no admitida.')
    gpass=-20*np.log10(1-dp);gstop=-20*np.log10(ds);edges=np.r_[wp,ws];lo=float(edges.min()/100);hi=float(edges.max()*100)
    if lo<=0 or not np.isfinite(hi):raise ValueError('Los bordes exceden el rango numérico del diseño.')
    w=np.unique(np.r_[0,np.geomspace(lo,hi,32769),edges]);systems=[];reports=[];notes=[]
    orders={'butter':sp.buttord,'cheby1':sp.cheb1ord,'cheby2':sp.cheb2ord,'ellip':sp.ellipord}
    for index,family in enumerate(methods):
        checkpoint(index/len(methods))
        if family=='bessel':
            choice=_bessel_by_bands(wp,ws,dp,ds,kind)
            label='Bessel'
            if choice is None:
                reason=f'Bessel no cumple ambas tolerancias hasta orden {MAX_BESSEL_ORDER} con el mapeo fijado por la banda de paso.'
                if method=='bessel':raise ValueError(reason)
                notes.append(reason);continue
            notes.append('Bessel usa el prototipo normalizado en fase, reescalado dentro del intervalo que admiten ambas bandas.')
            order,zpk=choice
            final_order=int(order)*(2 if wp.size==2 else 1);ensure_working_set(final_order**2+len(w),live_arrays=10)
        else:
            label=FAMILIES[family]
            order,critical=orders[family](wp,ws,gpass,gstop,analog=True)
            final_order=int(order)*(2 if wp.size==2 else 1);ensure_working_set(final_order**2+len(w),live_arrays=10)
            kwargs=dict(N=int(order),Wn=critical,btype=kind,analog=True,output='zpk')
            if family in ('cheby1','ellip'):kwargs['rp']=gpass
            if family in ('cheby2','ellip'):kwargs['rs']=gstop
            zpk=getattr(sp,family)(**kwargs)
        try:
            system,disagreement=_checked_transfer(zpk,label+' analógico',w)
        except ValueError as exc:
            if method!='compare_rf' or family!='bessel':raise
            notes.append('Bessel omitido: '+str(exc));continue
        systems.append(system)
        from .band_extrema import evaluate
        count=2 if kind=='bandstop' else 1
        _,evaluation=evaluate(system,{'wp':wp,'ws':ws,'kind':kind,'amplitudes':[1.]*count,'pass_lower':[1-dp]*count,'pass_upper_bands':[1.]*count,'stop_upper':ds})
        reports.append(f'{label}\nOrden del prototipo: {order}\nOrden final: {final_order}\n'+evaluation+f'\nDiferencia de representación: {disagreement:.3g}')
    report='Diseño analógico por especificaciones\n\nFrecuencias en rad/s; sin límite de Nyquist.\n'+f'Paso permitido: [{1-dp:g}, 1]\nRechazo máximo: {ds:g}\nPérdida de paso: {gpass:.9g} dB\nAtenuación de rechazo: {gstop:.9g} dB\n\n'+'\n\n'.join(reports)+'\n\nOrden seleccionado dentro de cada familia. La comprobación refina extremos locales e incluye bordes, cero e infinito; no constituye una prueba global ni representa una realización física con componentes. Los coeficientes de H(s) se pueden exportar, convertir a digital o usar en respuesta temporal.'
    return {'report':report+'\n\n'+'\n'.join(notes),'design_notes':notes,'signals':[],'systems':systems,'comparison':len(systems)>1,'specifications':{'domain':'analog','kind':kind,'wp':wp.tolist(),'ws':ws.tolist(),'dp':dp,'ds':ds,'pass_upper':1,'plot_range':[float(edges.min()/10),float(edges.max()*10)]}}
