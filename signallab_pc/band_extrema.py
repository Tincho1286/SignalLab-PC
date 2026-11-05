"""Numerical band extrema with edge, pole-neighbourhood and local refinement."""
import numpy as np
from scipy.optimize import minimize_scalar
from scipy import signal
from .jobs import checkpoint


def intervals(wp, ws, kind, end):
    if kind == 'lowpass':return [(0., wp[0])], [(ws[0], end)]
    if kind == 'highpass':return [(wp[0], end)], [(0., ws[0])]
    if kind == 'bandpass':return [(wp[0], wp[1])], [(0., ws[0]), (ws[1], end)]
    return [(0., wp[0]), (wp[1], end)], [(ws[0], ws[1])]


def fir_magnitude(system):
    """Fast single-frequency magnitude for FIR extremum refinement."""
    taps = system.b
    indices = np.arange(len(taps), dtype=float)
    if not np.any(taps.imag) and np.array_equal(taps, taps[::-1]):
        centered = indices-(len(taps)-1)/2
        real = taps.real.copy()

        def magnitude(omega):
            return abs(float(np.dot(real,np.cos(omega*centered))))
    else:
        def magnitude(omega):
            return abs(np.dot(taps,np.exp(-1j*omega*indices)))
    return magnitude


def measure(system, wp, ws, kind):
    analog = system.domain == 'analog'; edges = np.r_[wp, ws].astype(float)
    scale = float(np.sqrt(edges.min())*np.sqrt(edges.max()))
    passing, stopping = intervals(wp, ws, kind, np.inf if analog else np.pi)
    # A compact coordinate includes the analog endpoint at infinity explicitly.
    def to_u(w):return np.asarray(w)/(scale+np.asarray(w)) if analog else np.asarray(w)/np.pi
    def from_u(u):return scale*u/(1-u) if analog else np.pi*u
    if analog:
        b = np.trim_zeros(system.b, 'f'); a = np.trim_zeros(system.a, 'f')
        infinity = 0. if not len(b) or len(b)<len(a) else float(abs(b[0]/a[0])) if len(b)==len(a) else np.inf
        base = np.unique(np.r_[0., to_u(np.geomspace(edges.min()/100, edges.max()*100, 32769)), 1.])
        finite = base < 1
        h = np.empty(base.size);h[finite] = abs(system.response(from_u(base[finite])));h[~finite] = infinity
    else:
        base = np.linspace(0., 1., 32769)
        # Retain the FFT path for long FIRs; explicit frequencies are used below.
        if system.sos is None:
            _, response = signal.freqz(system.b, system.a, worN=32769, include_nyquist=True)
            h = abs(response)
        else:h = abs(system.response(base*np.pi))
    seeds = list(to_u(edges))
    if len(system.a)>1:
        # Resonances much narrower than the regular mesh get their own seeds.
        from .transfer_plane import effective_plane_system,plane_poles
        poles = plane_poles(effective_plane_system(system))
        for pole in poles:
            center = float(pole.imag) if analog else float(np.angle(pole))
            width = abs(float(pole.real)) if analog else abs(1-float(abs(pole)))
            for offset in (-8., -1., 0., 1., 8.):
                w = center+offset*width
                if w>=0 and (analog or w<=np.pi):seeds.append(float(to_u(w)))
    seeds = np.unique(seeds)
    seeds = seeds[(seeds>=0)&(seeds<1 if analog else seeds<=1)]
    if len(seeds):
        values = abs(system.response(from_u(seeds)))
        order = np.argsort(np.r_[base, seeds]);base = np.r_[base, seeds][order];h = np.r_[h, values][order]
        base, indices = np.unique(base, return_index=True);h = h[indices]
    failures = 0
    fast_fir = fir_magnitude(system) if not analog and system.sos is None and len(system.a)==1 else None
    def value(u):
        if analog and u>=1:return infinity
        w = from_u(u)
        if fast_fir is not None:
            return fast_fir(w)
        return float(abs(system.response(np.array([w]))[0]))
    def band(lo, hi):
        nonlocal failures
        low, high = float(to_u(lo)), (1. if np.isinf(hi) else float(to_u(hi)))
        select = (base>=low)&(base<=high)
        x = np.r_[low, base[select], high];y = np.r_[value(low), h[select], value(high)]
        x, ids = np.unique(x, return_index=True);y = y[ids]
        if not np.isfinite(y).all():raise ValueError('La respuesta no es finita en una banda exigida; no se declara válido el diseño.')
        points = [(float(y.min()), float(x[y.argmin()])), (float(y.max()), float(x[y.argmax()]))]
        for sign, slot in ((1., 0), (-1., 1)):
            # Strict on at least one side: constant responses need no searches.
            q = sign*y
            noise = 64*np.finfo(float).eps*np.maximum(np.maximum(abs(q[:-2]), abs(q[2:])), np.finfo(float).tiny)
            candidates = np.flatnonzero((q[1:-1]<=q[:-2])&(q[1:-1]<=q[2:])&((q[:-2]-q[1:-1]>noise)|(q[2:]-q[1:-1]>noise)))+1
            for index in candidates:
                checkpoint()
                left, right = float(x[index-1]), float(x[index+1])
                # Normalize each bracket to avoid absolute frequency tolerances.
                def objective(t):
                    result = value(left+t*(right-left))
                    if not np.isfinite(result):raise ValueError('La búsqueda de extremos encontró una singularidad en la banda.')
                    return sign*result
                fit = minimize_scalar(objective, bounds=(0., 1.), method='bounded', options={'xatol':1e-11, 'maxiter':100})
                if not fit.success:failures += 1;continue
                u = left+float(fit.x)*(right-left);v = value(u)
                if sign*v < sign*points[slot][0]:points[slot] = (v, u)
        def frequency(u):return float('inf') if analog and u>=1 else float(from_u(u))
        return {'minimum':points[0][0], 'minimum_at':frequency(points[0][1]), 'maximum':points[1][0], 'maximum_at':frequency(points[1][1])}
    pass_values = [band(*item) for item in passing];stop_values = [band(*item) for item in stopping]
    return {'passing':pass_values, 'stopping':stop_values, 'failed_refinements':failures,
            'scope':'Estimación numérica con rejilla, bordes exactos, vecindades de polos y refinamiento local de extremos. En analógico se incluye el límite en infinito. No es una certificación global ni prueba un orden mínimo.'}


def evaluate(system, spec):
    try:metrics = measure(system, spec['wp'], spec['ws'], spec['kind'])
    except ValueError as exc:return False, str(exc)
    unit = 'rad/s' if system.domain=='analog' else 'rad/muestra'
    def at(w):return '∞' if np.isinf(w) else format(w, '.12g')
    rows = ['Los extremos corresponden al módulo |H| en amplitud lineal, dentro de cada banda exigida. Las bandas de transición no se incluyen.'];excess = -np.inf
    passing, stopping = intervals(spec['wp'], spec['ws'], spec['kind'], np.inf if system.domain=='analog' else np.pi)
    def extrema(label, index, bounds, values, requirement):
        lo, hi = bounds
        rows.extend([
            f'{label} {index+1} · {at(lo)} ≤ ω ≤ {at(hi)} {unit}. {requirement}',
            f'Mínimo |H| = {values["minimum"]:.12g}, en ω = {at(values["minimum_at"])} {unit}.',
            f'Máximo |H| = {values["maximum"]:.12g}, en ω = {at(values["maximum_at"])} {unit}.'])
    for index, (v, low, high, amplitude, bounds) in enumerate(zip(metrics['passing'], spec['pass_lower'], spec['pass_upper_bands'], spec['amplitudes'], passing)):
        excess = max(excess, low-v['minimum'], v['maximum']-high)
        extrema('Paso', index, bounds, v, f'Objetivo {amplitude:.12g}; permitido [{low:.12g}, {high:.12g}].')
    for index, (v, bounds) in enumerate(zip(metrics['stopping'], stopping)):
        excess = max(excess, v['maximum']-spec['stop_upper'])
        extrema('Rechazo', index, bounds, v, f'Permitido [0, {spec["stop_upper"]:.12g}].')
    accepted = excess<=0 and not metrics['failed_refinements']
    scale = max(*spec['pass_upper_bands'], spec['stop_upper'])
    verdict = 'dentro de tolerancias.' if accepted else 'al límite numérico; no se declara cumplimiento estricto.' if 0<excess<=1e-10*scale else 'fuera de tolerancias o con extremos pendientes de resolver; revisá el diseño.'
    rows.extend([f'Margen mínimo respecto de los límites: {-excess:.12g} en amplitud (positivo: holgura; negativo: exceso).', 'Comprobación con extremos refinados: '+verdict, metrics['scope']])
    if metrics['failed_refinements']:rows.append(f'Búsquedas locales sin convergencia: {metrics["failed_refinements"]}; no se declara válido el diseño.')
    return bool(accepted), '\n'.join(rows)
