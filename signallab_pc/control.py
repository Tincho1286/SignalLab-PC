"""Control y respuestas LTI: realimentación, segundo orden y lugar de raíces."""
import math
import numpy as np
from scipy import signal as sp
from scipy.optimize import linear_sum_assignment
from .filters import Transfer
from .model import Signal
from .operations import _finite_output
from .resources import ensure_working_set
from .sampling import positive_integer, positive_finite
from .jobs import checkpoint


def second_order(natural_frequency, damping, gain=1):
    wn = positive_finite(natural_frequency, "Frecuencia natural")
    damping, gain = float(damping), float(gain)
    if not math.isfinite(damping) or damping < 0 or not math.isfinite(gain):
        raise ValueError("ζ debe ser finito y no negativo; ganancia finita.")
    return Transfer([gain*wn*wn], [1, 2*damping*wn, wn*wn], "analog", "Segundo orden")


def feedback(system, gain=1, positive=False):
    gain = complex(gain)
    if not np.isfinite(gain): raise ValueError("K debe ser finito.")
    size = max(len(system.a), len(system.b))
    ensure_working_set(size, live_arrays=8)
    padding = lambda values: np.pad(values, (0, size-len(values)) if system.domain == "digital" else (size-len(values), 0))
    numerator = gain*padding(system.b)
    denominator = padding(system.a) + (-1 if positive else 1)*numerator
    if not np.any(denominator):
        raise ValueError("El lazo produce denominador idénticamente cero; no define una transferencia.")
    return Transfer(numerator, denominator, system.domain, f"Lazo {'positivo' if positive else 'negativo'} de {system.name}",sample_period_s=system.sample_period_s)


def analog_response(system, duration, count, kind="step"):
    if system.domain != "analog": raise ValueError("La respuesta temporal continua requiere H(s).")
    from .system_conditions import require_causal_roc
    require_causal_roc(system)
    duration = positive_finite(duration, "Duración")
    count = positive_integer(count, "Muestras")
    if count < 2 or kind not in {"step", "impulse"}: raise ValueError("Usá al menos dos puntos y excitación step o impulse.")
    b = np.trim_zeros(system.b, "f")
    if not len(b): b = np.array([0j])
    if len(b) > len(system.a):
        raise ValueError("H(s) impropia: la respuesta incluye derivadas de Dirac; este panel requiere una transferencia propia.")
    order = len(system.a)-1
    ensure_working_set(int(count*max(1, order)+order*order), live_arrays=10)
    time = np.linspace(0, duration, count)
    if np.any(np.diff(time) <= 0): raise ValueError("El paso temporal no se distingue.")
    direct = b[0]/system.a[0] if len(b) == len(system.a) else 0j
    if order == 0:
        values = np.full(count, direct if kind == "step" else 0j)
    else:
        checkpoint(0)
        a, bb, c, d = sp.tf2ss(b, system.a)
        if kind == "impulse":
            # Delta(t)*D se informa aparte; no se dibuja como una muestra finita.
            _, values = sp.impulse((a, bb, c, np.zeros_like(d)), T=time)
        else:
            _, values = sp.step((a, bb, c, d), T=time)
        checkpoint(1)
    metadata = {"operation": "analog_response", "excitation": kind, "initial_rest": True,
                "duration_s": duration, "finite_window": True}
    if kind == "impulse" and direct != 0:
        metadata["dirac_at_zero"] = [float(direct.real), float(direct.imag)]
        metadata["warning"] = "The plotted regular part excludes the ideal Dirac at t=0; its exact weight is recorded separately."
    return Signal(_finite_output(values, "La respuesta continua"), 0, float(time[1]), "s", f"{system.name}_{kind}", "continuous", "", metadata)


def root_locus(system, start, stop, count):
    count = positive_integer(count, "Cantidad de ganancias")
    start, stop = float(start), float(stop)
    if not math.isfinite(start) or not math.isfinite(stop) or start < 0 or stop <= start or count < 2:
        raise ValueError("Usá 0 ≤ K inicial < K final y al menos dos ganancias.")
    size = max(len(system.a), len(system.b))
    if size <= 1: raise ValueError("La transferencia estática no tiene ramas de polos.")
    ensure_working_set(int(count*(size-1)+size*size), live_arrays=12)
    padding = lambda values: np.pad(values, (0,size-len(values)) if system.domain == "digital" else (size-len(values),0))
    numerator, denominator = padding(system.b), padding(system.a)
    gains = np.linspace(start, stop, count)
    roots = np.full((count, size-1), np.nan+1j*np.nan)
    for index, gain in enumerate(gains):
        checkpoint(index/count)
        polynomial = denominator+gain*numerator
        current = np.roots(np.trim_zeros(polynomial, "f"))
        if len(current) == size-1 and index and np.all(np.isfinite(roots[index-1])):
            rows, cols = linear_sum_assignment(abs(roots[index-1, :, None]-current[None, :]))
            roots[index, rows] = current[cols]
        else:
            roots[index, :len(current)] = current[np.lexsort((current.imag,current.real))]
    checkpoint(1)
    return gains, roots, system.domain


def forced_response(system, source, interpolation="linear"):
    """Respuesta de estado cero desde el inicio del registro de entrada."""
    expected = "discrete" if system.domain == "digital" else "continuous"
    if source.domain != expected:
        raise ValueError("El dominio de la entrada debe coincidir con el del sistema.")
    from .system_conditions import require_causal_roc
    require_causal_roc(system)
    from .distributions import dirac_terms,attach_terms
    impulses=dirac_terms(source)
    if impulses and (system.domain!='analog' or any(t<source.origin or t>source.axis[-1] for t,_ in impulses)):
        raise ValueError('La entrada con impulsos requiere un sistema continuo y una ventana que incluya sus posiciones.')
    if system.domain == "digital":
        result = system.apply(source)
    else:
        if source.step <= 0 or source.values.size < 2:
            raise ValueError("La entrada continua requiere al menos dos puntos y paso positivo.")
        if interpolation not in {"linear", "hold"}:
            raise ValueError("Elegí interpolación lineal o retención constante.")
        b = np.trim_zeros(system.b, "f")
        if not b.size: b = np.array([0j])
        if len(b) > len(system.a):
            raise ValueError("Esta simulación requiere H(s) propia: grado del numerador ≤ grado del denominador.")
        count = source.values.size
        order = len(system.a)-1
        ensure_working_set(int(count*max(1,order)+order*order), live_arrays=12)
        time = source.step*np.arange(count)
        if not np.all(np.isfinite(time)) or np.any(np.diff(time)<=0):
            raise ValueError("El intervalo temporal excede la precisión numérica disponible.")
        if order == 0:
            values = (b[0]/system.a[0])*source.values
        else:
            checkpoint(0)
            a, bb, c, d = sp.tf2ss(b, system.a)
            _, values, _ = sp.lsim((a,bb,c,d), U=source.values, T=time, interp=interpolation=="linear")
            checkpoint(1)
        singular={}
        if impulses:
            values=np.asarray(values,dtype=complex).reshape(-1)
            if order:
                for position,weight in impulses:
                    relative=source.axis-position;selected=relative>=0
                    _,response=sp.impulse((a,bb,c,np.zeros_like(d)),T=relative[selected])
                    values[selected]+=weight*np.asarray(response).reshape(-1)
            direct=b[0]/system.a[0] if len(b)==len(system.a) else 0j
            attach_terms(singular,[(t,w*direct) for t,w in impulses])
            singular['input_dirac_terms']=[[t,[float(w.real),float(w.imag)]] for t,w in impulses]
        result = Signal(_finite_output(values,"La respuesta a la entrada"),source.origin,source.step,source.units,"Salida y(t)","continuous",metadata=singular)
    result.name = "Salida y[n]" if expected == "discrete" else "Salida y(t)"
    result.metadata = {
        **result.metadata,
        "operation":"forced_response", "initial_rest":True,
        "initial_rest_at":source.origin, "input_name":source.name,
        "input_interpolation":("discrete sequence" if expected=="discrete" else interpolation),
        "b":[[v.real,v.imag] for v in system.b],
        "a":[[v.real,v.imag] for v in system.a],
        "finite_window":True,
        "scope":"Estado inicial nulo al inicio del registro. No incluye la cola posterior a la ventana de entrada.",
    }
    return result


def interconnect(first, second, connection="cascade"):
    """Composición racional sin cancelaciones aproximadas de polos y ceros."""
    if first.domain != second.domain:
        raise ValueError("Ambos sistemas deben tener el mismo dominio.")
    if connection not in {"cascade","parallel","negative_feedback","positive_feedback"}:
        raise ValueError("Conexión desconocida.")
    from .system_clock import common_period
    period=common_period(first,second)
    size=sum(len(v) for v in (first.a,first.b,second.a,second.b))
    ensure_working_set(size,live_arrays=16)
    def add(left,right,sign=1):
        count=max(len(left),len(right))
        def pad(v):return np.pad(v,(0,count-len(v)) if first.domain=="digital" else (count-len(v),0))
        return pad(left)+sign*pad(right)
    checkpoint(0)
    # Joining existing biquads avoids the ill-conditioned expanded polynomial.
    if connection=='cascade' and first.domain=='digital' and (first.sos is not None or second.sos is not None):
        def sections(system):
            if system.sos is not None:return system.sos
            if max(len(system.b),len(system.a))<=3 and not np.any(system.b.imag) and not np.any(system.a.imag):
                return np.r_[np.pad(system.b.real,(0,3-len(system.b))),np.pad(system.a.real,(0,3-len(system.a)))][None,:]
            return None
        one,two=sections(first),sections(second)
        if one is not None and two is not None:
            result=Transfer([1],[1],'digital','Cascada H₁·H₂ en secciones',np.vstack((one,two)),first.advance+second.advance,sample_period_s=period);checkpoint(1);return result
    denominator=np.convolve(first.a,second.a)
    advance=0
    def delayed(values,count):
        ensure_working_set(int(len(values)+count),live_arrays=16)
        return np.pad(values,(count,0))
    if connection=="cascade":
        numerator=np.convolve(first.b,second.b);name="Cascada H₁·H₂"
        advance=first.advance+second.advance
    elif connection=="parallel":
        advance=max(first.advance,second.advance)
        numerator=add(delayed(np.convolve(first.b,second.a),advance-first.advance),delayed(np.convolve(second.b,first.a),advance-second.advance));name="Paralelo H₁+H₂"
    else:
        numerator=np.convolve(first.b,second.a)
        if first.domain=='digital':
            numerator=delayed(numerator,second.advance);denominator=delayed(denominator,first.advance+second.advance)
        denominator=add(denominator,np.convolve(first.b,second.b),1 if connection=="negative_feedback" else -1)
        name="Realimentación negativa" if connection=="negative_feedback" else "Realimentación positiva"
    numerator=_finite_output(numerator,"El numerador equivalente")
    denominator=_finite_output(denominator,"El denominador equivalente")
    if not np.any(denominator):raise ValueError("La conexión produce denominador cero: no define una función de transferencia.")
    if first.domain=="digital" and denominator[0]==0:
        leading=int(np.flatnonzero(denominator)[0]);denominator=denominator[leading:];advance+=leading
    checkpoint(1)
    result=Transfer(numerator,denominator,first.domain,name,advance=advance,sample_period_s=period)
    if first.sos is not None or second.sos is not None:
        # A polynomial equivalent must not silently discard the accuracy of SOS inputs.
        w=np.linspace(0,np.pi,2049);h1=first.response(w);h2=second.response(w)
        with np.errstate(all='ignore'):
            expected=h1*h2 if connection=='cascade' else h1+h2 if connection=='parallel' else h1/(1+(1 if connection=='negative_feedback' else -1)*h1*h2)
            actual=result.response(w);valid=np.isfinite(expected)
            mismatch=abs(actual[valid]-expected[valid])/np.maximum(1,abs(expected[valid]))
        if not np.any(valid) or not np.all(np.isfinite(mismatch)) or np.max(mismatch)>1e-6:
            raise ValueError('La transferencia polinómica equivalente pierde precisión respecto de los bloques en secciones. No se publica ese resultado. La cascada de filtros en secciones conserva su realización; esta conexión necesita otra representación o un orden menor.')
    return result


def discrete_response_parts(system,source,previous_inputs=(),previous_outputs=()):
    """Descompone una recurrencia causal desde el primer índice del registro."""
    if system.domain!='digital' or source.domain!='discrete':
        raise ValueError('La descomposición por historiales requiere sistema y señal discretos.')
    from .system_conditions import require_causal_roc
    require_causal_roc(system)
    previous_inputs=np.asarray(previous_inputs,dtype=complex).reshape(-1)
    previous_outputs=np.asarray(previous_outputs,dtype=complex).reshape(-1)
    if not np.all(np.isfinite(previous_inputs)) or not np.all(np.isfinite(previous_outputs)):
        raise ValueError('Los valores anteriores deben ser finitos.')
    if previous_inputs.size>len(system.b)-1 or previous_outputs.size>len(system.a)-1:
        raise ValueError(f'Ingresá como máximo {len(system.b)-1} entradas anteriores y {len(system.a)-1} salidas anteriores. Se completan con cero los valores omitidos.')
    ensure_working_set(int(source.values.size+len(system.a)+len(system.b)),live_arrays=16)
    checkpoint(0)
    # Una única realización en las tres componentes preserva la misma recurrencia.
    if system.sos is not None and (np.any(previous_inputs) or np.any(previous_outputs)):
        system=Transfer(system.b,system.a,system.domain,system.name,sample_period_s=system.sample_period_s)
    total=system.apply(source,previous_inputs,previous_outputs).copy_with(name='Respuesta total')
    checkpoint(.33)
    forced=system.apply(source).copy_with(name='Respuesta de estado cero')
    checkpoint(.66)
    natural=system.apply(source.copy_with(values=np.zeros(source.values.size)),previous_inputs,previous_outputs).copy_with(name='Respuesta de entrada cero')
    initial={'initial_index':source.origin,'previous_inputs':[[v.real,v.imag] for v in previous_inputs],
             'previous_outputs':[[v.real,v.imag] for v in previous_outputs],
             'history_order':'Más reciente primero: n0−1, n0−2, …; omitidos iguales a cero.',
             'scope':'Descomposición desde n0. La respuesta de entrada cero incluye la memoria de entradas y salidas anteriores. Sólo se calcula el intervalo del registro.'}
    for value,part in ((total,'total'),(forced,'zero_state'),(natural,'zero_input')):
        value.metadata={**value.metadata,'operation':'discrete_response_decomposition','component':part,**initial,
                        'initial_rest':part=='zero_state' or not (np.any(previous_inputs) or np.any(previous_outputs))}
    checkpoint(1)
    return total,forced,natural
