"""Operaciones discretas portadas y auditadas contra contratos de SignalLab 5.0."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import signal as scipy_signal

from .model import Signal
from .resources import ensure_working_set


@dataclass(frozen=True)
class FiniteMeasures:
    energy: float
    average_power: float
    rms: float
    sample_count: int
    interpretation: str = "Ventana finita almacenada; no clasifica por sí sola la señal infinita."
    domain: str = "discrete"
    interval: tuple | None = None
    integration: str | None = None
    duration: float | None = None
    axis_units: str = "n"


def _discrete(signal: Signal, *, temporal=True) -> None:
    if temporal:
        from .signal_semantics import require_temporal
        require_temporal(signal)
    if signal.domain != "discrete" or signal.step != 1 or not float(signal.origin).is_integer():
        raise ValueError("La operación requiere una secuencia discreta con índices enteros y paso 1.")


def _finite_output(values: np.ndarray, description: str) -> np.ndarray:
    result = np.asarray(values, dtype=np.complex128).reshape(-1)
    if not np.all(np.isfinite(result)):
        raise FloatingPointError(f"{description} excede el rango numérico finito de float64.")
    return result


def finite_measures(x: Signal) -> FiniteMeasures:
    """Medidas de un registro discreto o de su modelo continuo por tramos."""
    if x.domain=="continuous":
        from .continuous import finite_measures as continuous_measures
        return continuous_measures(x)
    _discrete(x)
    magnitudes = np.abs(x.values)
    if not np.all(np.isfinite(magnitudes)):
        raise FloatingPointError("La magnitud de una muestra excede el rango de float64.")
    scale = float(np.max(magnitudes, initial=0.0))
    if scale == 0.0:
        energy = 0.0
    else:
        normalized_sum = float(np.sum((magnitudes / scale) ** 2, dtype=np.float64))
        if scale > np.sqrt(np.finfo(np.float64).max / max(normalized_sum, 1.0)):
            raise FloatingPointError("La energía excede el rango numérico finito de float64.")
        energy = (scale * scale) * normalized_sum
        if energy == 0.0:
            raise FloatingPointError("La energía queda por debajo del rango representable de float64.")
    power = energy / x.values.size
    if energy and power==0:raise FloatingPointError("La potencia media queda por debajo del rango representable de float64.")
    rms = float(np.sqrt(power))
    return FiniteMeasures(float(energy), float(power), rms, int(x.values.size))


def _clock_for_index_transform(x, new_origin, operation):
    metadata=dict(x.metadata,operation=operation,input_origin=int(x.origin),input_expression=x.expression)
    if 'sample_rate_hz' in metadata:
        rate=float(metadata['sample_rate_hz']);start=float(metadata.get('time_start_s',0))
        if not np.isfinite(rate) or rate<=0 or not np.isfinite(start):raise ValueError('El reloj de la señal debe tener Fs positiva y tiempo inicial finito.')
        # Keep the instant associated with index zero; move the finite support.
        new_start=start+(int(new_origin)-int(x.origin))/rate
        end=new_start+(x.values.size-1)/rate
        if not np.isfinite(new_start) or not np.isfinite(end) or (x.values.size>1 and (new_start+1/rate==new_start or end-1/rate==end)):
            raise ValueError('El eje temporal transformado excede la resolución numérica del reloj.')
        metadata.update(time_start_s=new_start,time_mapping='t = time_start_s + (n-origin)/sample_rate_hz',
                        clock_convention='Se conserva el instante asociado a n=0; inversión discreta alrededor de ese índice.')
    return metadata


def shift(x: Signal, samples: int) -> Signal:
    """x[n-k] desplaza el origen +k y mantiene las muestras almacenadas."""
    _discrete(x)
    if isinstance(samples, bool) or not isinstance(samples, (int, np.integer)):
        raise ValueError("El desplazamiento debe ser un índice entero.")
    origin=int(x.origin)+int(samples)
    return x.copy_with(origin=origin,metadata=_clock_for_index_transform(x,origin,'time_shift'),expression='')


def reverse(x: Signal) -> Signal:
    """Refleja el eje n a -n: nuevo origen = -(n0 + N - 1)."""
    _discrete(x)
    ensure_working_set(x.values.size, live_arrays=2)
    return Signal(x.values[::-1], -(int(x.origin) + x.values.size - 1), 1,
                  x.units, f"{x.name}[-n]", "discrete", "",
                  _clock_for_index_transform(x,-(int(x.origin)+x.values.size-1),"time_reversal"))


def scale_amplitude(x: Signal, factor: complex) -> Signal:
    _discrete(x)
    if not np.isfinite(factor):
        raise ValueError("El factor debe ser finito.")
    ensure_working_set(x.values.size, live_arrays=3)
    return x.copy_with(values=_finite_output(x.values * factor, "El escalado"),expression="",metadata=dict(x.metadata,operation="scale",amplitude=[float(complex(factor).real),float(complex(factor).imag)],input_expression=x.expression))


def add_sequences(x: Signal, h: Signal) -> Signal:
    """Suma alineando índices; los huecos se consideran cero dentro del soporte."""
    _discrete(x); _discrete(h)
    start = min(int(x.origin), int(h.origin))
    stop = max(int(x.origin) + x.values.size, int(h.origin) + h.values.size)
    count = stop - start
    ensure_working_set(count, live_arrays=5)
    out = np.zeros(count, dtype=np.complex128)
    x0 = int(x.origin) - start
    h0 = int(h.origin) - start
    out[x0:x0 + x.values.size] += x.values
    out[h0:h0 + h.values.size] += h.values
    return Signal(_finite_output(out, "La suma"), start, 1, x.units,
                  f"{x.name}+{h.name}", "discrete", "",
                  {"operation": "sum", "inputs": [x.name, h.name]})


def _half_sum(first,second,sign=1):
    """Average finite complex values without overflowing a finite result."""
    def component(a,b):
        with np.errstate(over='ignore',invalid='ignore',under='ignore'):
            value=(a+sign*b)/2;fallback=a/2+sign*(b/2)
        return np.where(np.isfinite(value),value,fallback)
    return component(first.real,second.real)+1j*component(first.imag,second.imag)

def even_odd_parts(x: Signal) -> tuple[Signal, Signal]:
    """Extiende por cero el soporte reflejado y devuelve partes par e impar."""
    _discrete(x)
    start = min(int(x.origin), -(int(x.origin) + x.values.size - 1))
    stop = max(int(x.origin) + x.values.size - 1, -int(x.origin)) + 1
    count = stop - start
    ensure_working_set(count, live_arrays=7)
    original = np.zeros(count, dtype=np.complex128)
    reflected = np.zeros(count, dtype=np.complex128)
    xstart = int(x.origin) - start
    rstart = -(int(x.origin) + x.values.size - 1) - start
    original[xstart:xstart + x.values.size] = x.values
    reflected[rstart:rstart + x.values.size] = x.values[::-1]
    even = _half_sum(original,reflected)
    odd = _half_sum(original,reflected,-1)
    metadata = _clock_for_index_transform(x,start,"even_odd_decomposition")
    metadata.update(input=x.name,scope="Descomposición sin conjugación alrededor de n=0. Fuera del registro de entrada se usa cero.")
    return (
        Signal(even, start, 1, x.units, f"{x.name}_par", "discrete", "", dict(metadata)),
        Signal(odd, start, 1, x.units, f"{x.name}_impar", "discrete", "", dict(metadata)),
    )


def convolution_clock(x,h):
    """Share the physical output clock across linear-convolution algorithms."""
    clock = {}
    from .system_clock import common_rate,validate_clock_resolution
    rate=common_rate(x,h)
    if rate is not None:
        clock['sample_rate_hz']=rate
        if 'time_start_s' in x.metadata and 'time_start_s' in h.metadata:
            start_s=float(x.metadata['time_start_s'])+float(h.metadata['time_start_s'])
            validate_clock_resolution(start_s,rate,x.values.size+h.values.size-1)
            clock.update(time_start_s=start_s,time_mapping='t = time_start_s + (n-origin)/sample_rate_hz')
    return clock


def linear_convolution(x: Signal, h: Signal) -> Signal:
    """Convolución lineal completa y[n]=sum x[k]h[n-k], incluidos índices negativos."""
    _discrete(x); _discrete(h)
    clock = convolution_clock(x,h)
    count = x.values.size + h.values.size - 1
    ensure_working_set(count, live_arrays=7)
    from .spectral_scaling import bounded,restore_scale
    a,ea=bounded(x.values);b,eb=bounded(h.values)
    y=restore_scale(scipy_signal.convolve(a,b,mode="full",method="auto"),ea+eb)
    start = int(x.origin) + int(h.origin)
    result = Signal(_finite_output(y, "La convolución"), start, 1, x.units,
                  f"{x.name}*{h.name}", "discrete", "",
                  {**clock, "operation": "linear_convolution", "inputs": [x.name, h.name],
                   "convention": "full; zero outside each finite support"})
    from .quality_steps import convolution
    result.metadata['derivation']=convolution(x,h,result)
    result.metadata['derivation_operation']=result.metadata['operation']
    return result


def linear_correlation(x: Signal, h: Signal) -> Signal:
    """r_xh[l]=sum_n x[n] conjugate(h[n-l]); igual a Conv(x, conj(reverse(h)))."""
    _discrete(x); _discrete(h)
    count = x.values.size + h.values.size - 1
    ensure_working_set(count, live_arrays=7)
    from .system_clock import common_rate
    from .spectral_scaling import bounded,restore_scale
    rate=common_rate(x,h)
    a,ea=bounded(x.values);b,eb=bounded(h.values)
    r=restore_scale(scipy_signal.correlate(a,b,mode="full",method="auto"),ea+eb)
    start = int(x.origin) - int(h.origin) - (h.values.size - 1)
    return Signal(_finite_output(r, "La correlación"), start, 1, x.units,
                  f"r_{x.name}{h.name}", "discrete", "",
                  {**({'sample_rate_hz':rate} if rate is not None else {}),
                   "operation": "linear_cross_correlation", "inputs": [x.name, h.name],
                   "convention": "r[l]=sum_n x[n] conjugate(h[n-l]); zero outside support"})


def dft(x: Signal, length: int | None = None, *, centered: bool = False) -> Signal:
    """DFT sin normalizar sobre el orden almacenado; ignora el origen global del eje."""
    _discrete(x)
    n = x.values.size if length is None else length
    if isinstance(n, bool) or not isinstance(n, (int, np.integer)) or int(n) < 1:
        raise ValueError("N debe ser un entero positivo.")
    n = int(n)
    ensure_working_set(n, bytes_per_sample=16, live_arrays=8)
    # La convención NumPy es sum x[n] exp(-2*pi*i*k*n/N), sin normalizar hacia delante.
    values = np.fft.fft(x.values, n=n)
    values = _finite_output(values, "La DFT")
    action = "unchanged" if n == x.values.size else ("zero padded" if n > x.values.size else "truncated at N")
    metadata = {"operation": "DFT", "input_length": int(x.values.size), "N": n,
                "input_action": action,"input_origin":int(x.origin),
                "input_clock":{key:x.metadata[key] for key in ('sample_rate_hz','time_start_s') if key in x.metadata},
                "convention": "sum x[m] exp(-2*pi*i*k*m/N), m is stored offset from 0; no forward normalization"}
    if centered:
        from .fourier_phase import bin_frequency

        metadata["dft_order"] = "centered"
        origin = bin_frequency(-(n//2), n)
        return Signal(np.fft.fftshift(values), origin, 2*np.pi/n, "rad/muestra",
                      "DFT X[k]", "frequency", "", metadata)
    return Signal(values, 0, 1, "bin k", "X[k]", "discrete", "", metadata)


def is_centered_dft(X: Signal) -> bool:
    return X.domain == "frequency" and X.units == "rad/muestra" and X.metadata.get("dft_order") == "centered"


def idft(X: Signal, *, restore_origin=False) -> Signal:
    """IDFT con división por N y restauración opcional de los índices de origen."""
    n = X.values.size
    centered = is_centered_dft(X)
    if centered:
        spacing = 2*np.pi/n
        if (X.metadata.get("N") != n or not np.isclose(X.step, spacing, rtol=1e-12, atol=0)
                or not np.isclose(X.origin, -(n//2)*spacing, rtol=1e-12, atol=0)):
            raise ValueError("La DFT centrada requiere sus N bins completos en la rejilla original.")
    else:
        _discrete(X,temporal=False)
        if X.data_kind=='harmonics':raise ValueError('Para coeficientes de serie usá la síntesis de Fourier, que emplea otra normalización.')
    ensure_working_set(n, bytes_per_sample=16, live_arrays=8)
    coefficients = np.fft.ifftshift(X.values) if centered else X.values
    values = _finite_output(np.fft.ifft(coefficients), "La IDFT")
    metadata={"operation":"IDFT","N":n,
              "convention":"(1/N) sum X[k] exp(+2*pi*i*k*m/N), m is stored output offset from 0"}
    origin=0
    if X.metadata.get('operation')=='DFT':
        initial=X.metadata.get('input_origin',X.metadata.get('source_origin'))
        if initial is not None:
            if type(initial) is not int:raise ValueError('El índice original de la DFT debe ser entero.')
            metadata['original_origin']=initial
            if restore_origin:origin=initial
        clock=X.metadata.get('input_clock',{})
        if not isinstance(clock,dict):raise ValueError('El reloj de origen de la DFT no es válido.')
        from .sampling import positive_finite
        if 'sample_rate_hz' in clock:
            metadata['sample_rate_hz']=positive_finite(clock['sample_rate_hz'],'Fs de origen')
        if 'time_start_s' in clock:
            t0=float(clock['time_start_s'])
            if not np.isfinite(t0):raise ValueError('El tiempo de origen de la DFT debe ser finito.')
            metadata['time_start_s']=t0
            if 'sample_rate_hz' in metadata:
                from .system_clock import validate_clock_resolution
                validate_clock_resolution(t0,metadata['sample_rate_hz'],n)
                metadata['time_mapping']='t = time_start_s + (n-origin)/sample_rate_hz'
    return Signal(values,origin,1,'n','x_idft[n]','discrete',metadata=metadata)


def circular_convolution(x: Signal, h: Signal) -> Signal:
    """Convención HP: N=max(Nx,Nh), relleno con ceros, orden almacenado."""
    _discrete(x); _discrete(h)
    n = max(x.values.size, h.values.size)
    ensure_working_set(n, live_arrays=10)
    from .system_clock import common_rate
    from .spectral_scaling import bounded,restore_scale
    rate=common_rate(x,h)
    a,ea=bounded(x.values);b,eb=bounded(h.values)
    values=restore_scale(np.fft.ifft(np.fft.fft(a,n)*np.fft.fft(b,n)),ea+eb)
    return Signal(_finite_output(values, "La convolución circular"), 0, 1, x.units,
                  f"{x.name}*c{h.name}", "discrete", "",
                  {**({'sample_rate_hz':rate} if rate is not None else {}),
                   "operation": "circular_convolution", "period": int(n),
                   "convention": "stored offsets from zero; zero pad to max length",
                   "input_origins": [int(x.origin), int(h.origin)]})


def correlation(x: Signal, h: Signal | None = None, *, circular: bool = False,
                normalization: str = "sum") -> Signal:
    """Correlación HP: suma, coeficiente energético o promedio por longitud.

    Circular exige periodos de igual longitud y respeta los orígenes módulo N.
    No se resta la media ni se divide por el solapamiento de cada retardo.
    """
    if h is None:
        h = x
    _discrete(x); _discrete(h)
    from .system_clock import common_rate
    rate=common_rate(x,h)
    if normalization not in {"sum", "energy", "mean"}:
        raise ValueError("Escala desconocida: use sum, energy o mean.")
    if normalization == "mean" and not circular:
        raise ValueError("El promedio por periodo requiere el modelo circular.")
    if circular and x.values.size != h.values.size:
        raise ValueError("La correlación circular requiere periodos de igual longitud; no agrega ceros.")
    ensure_working_set(int(x.values.size + h.values.size), live_arrays=12)
    left, right = x, h
    if normalization == "energy":
        # Escalar primero evita desbordar Ex*Eh y admite amplitudes muy pequeñas.
        def unit_energy(signal):
            scale = max(float(np.max(np.abs(signal.values.real))),
                        float(np.max(np.abs(signal.values.imag))))
            if scale == 0:
                raise ValueError("La correlación normalizada no está definida para energía cero.")
            values = signal.values / scale
            norm = np.sqrt(np.sum(np.abs(values) ** 2))
            return signal.copy_with(values=values / norm)
        left, right = unit_energy(x), unit_energy(h)
    if circular:
        n = x.values.size
        from .spectral_scaling import bounded,restore_scale
        a,ea=bounded(left.values);b,eb=bounded(right.values)
        factor=1/n if normalization=="mean" else 1.
        values=restore_scale(np.fft.ifft(np.fft.fft(a)*np.conj(np.fft.fft(b))),ea+eb,factor)
        values = np.roll(values, (int(x.origin) - int(h.origin)) % n)
        result = Signal(_finite_output(values, "La correlación circular"), 0, 1, "retardo",
                        f"r_{x.name}{h.name}", "discrete")
    else:
        result = linear_correlation(left, right)
    result.metadata = {**({'sample_rate_hz':rate} if rate is not None else {}), "operation": "correlation", "circular": circular,
        "normalization": normalization, "inputs": [x.name, h.name],
        "convention": "sum x[n] conj(h[n-l]); no mean subtraction; no overlap correction",
        "period": int(x.values.size) if circular else None}
    return result
