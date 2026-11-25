"""Operaciones discretas portadas y auditadas contra contratos de SignalLab 5.0."""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from scipy import signal as scipy_signal

from .model import Signal
from .resources import ensure_working_set
from .spectral_scaling import bounded, range_status, restore_scalar


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
    energy_status: str = "ok"
    power_status: str = "ok"
    rms_status: str = "ok"

    def text(self, field):
        status = self.power_status if field == 'average_power' else getattr(self, field+'_status')
        return measure_text(getattr(self, field), status)


def measure_text(value, status):
    if status == 'underflow':
        return "Por debajo del rango de float64"
    return format(value, '.12g')


def measure_scaled(total, divisor, exponent, *, measure=1.0):
    power_normalized = total / divisor
    energy = restore_scalar(total, 2 * exponent, measure)
    power = restore_scalar(power_normalized, 2 * exponent)
    rms = restore_scalar(math.sqrt(power_normalized), exponent)
    statuses = [range_status(value, total) for value in (energy, power, rms)]
    if 'overflow' in statuses:
        raise FloatingPointError("La energía o la potencia excede el rango numérico finito de float64.")
    return dict(energy=energy, average_power=power, rms=rms,
                energy_status=statuses[0], power_status=statuses[1], rms_status=statuses[2])


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
    ensure_working_set(x.values.size, live_arrays=5)
    normalized, exponent = bounded(x.values, normalize=True)
    total = float(np.sum(normalized.real**2 + normalized.imag**2))
    return FiniteMeasures(**measure_scaled(total, x.values.size, exponent),
                          sample_count=int(x.values.size))


def _clock_for_index_transform(x, new_origin, operation):
    metadata=dict(x.metadata,operation=operation,input_origin=int(x.origin),input_expression=x.expression)
    from .system_clock import CLOCK_MAPPING, common_rate, validate_clock_resolution
    rate = common_rate(x)
    start = metadata.get('time_start_s')
    if start is not None and rate is not None:
        new_start = float(start) + (int(new_origin)-int(x.origin))/rate
        validate_clock_resolution(new_start, rate, x.values.size)
        metadata.update(time_start_s=new_start,time_mapping=CLOCK_MAPPING,
                        clock_convention='Se conserva el instante asociado a n=0.')
    elif new_origin != x.origin:
        metadata.pop('time_start_s', None)
        metadata.pop('time_mapping', None)
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


def scale_amplitude(x: Signal, factor: complex, *, offset: complex = 0) -> Signal:
    _discrete(x)
    factor, offset = complex(factor), complex(offset)
    if not np.isfinite(factor) or not np.isfinite(offset):
        raise ValueError('El factor y el desplazamiento vertical deben ser finitos.')
    ensure_working_set(x.values.size, live_arrays=3)
    with np.errstate(over='ignore', invalid='ignore'):
        values = _finite_output(x.values * factor + offset, 'El ajuste de amplitud')
    return x.copy_with(values=values, expression='', metadata=dict(
        x.metadata, operation='scale', amplitude=[factor.real, factor.imag],
        vertical_offset=[offset.real, offset.imag], input_expression=x.expression))


def add_sequences(x: Signal, h: Signal) -> Signal:
    """Suma alineando índices; los huecos se consideran cero dentro del soporte."""
    _discrete(x); _discrete(h)
    if x.units != h.units:
        raise ValueError("Los ejes de las dos señales deben usar las mismas unidades.")
    start = min(int(x.origin), int(h.origin))
    stop = max(int(x.origin) + x.values.size, int(h.origin) + h.values.size)
    count = stop - start
    from .system_clock import combined_clock
    clock = combined_clock(x, h, start, count, mode='sum')
    ensure_working_set(count, live_arrays=5)
    out = np.zeros(count, dtype=np.complex128)
    x0 = int(x.origin) - start
    h0 = int(h.origin) - start
    out[x0:x0 + x.values.size] += x.values
    out[h0:h0 + h.values.size] += h.values
    return Signal(_finite_output(out, "La suma"), start, 1, x.units,
                  f"{x.name}+{h.name}", "discrete", "",
                  {**clock, "operation": "sum", "inputs": [x.name, h.name],
                   "input_x_expression": x.expression, "input_h_expression": h.expression,
                   "scope": "Suma por índices enteros. Cada entrada vale cero fuera de su intervalo."})


def _half_sum(first,second,sign=1):
    """Average finite complex values without overflowing a finite result."""
    def component(a,b):
        with np.errstate(over='ignore',invalid='ignore',under='ignore'):
            value=(a+sign*b)/2;fallback=a/2+sign*(b/2)
        return np.where(np.isfinite(value),value,fallback)
    return component(first.real,second.real)+1j*component(first.imag,second.imag)

def even_odd_parts(x: Signal) -> tuple[Signal, Signal]:
    """Recurre a la definición completa o extiende el registro por cero al reflejarlo."""
    _discrete(x)
    start = min(int(x.origin), -(int(x.origin) + x.values.size - 1))
    stop = max(int(x.origin) + x.values.size - 1, -int(x.origin)) + 1
    count = stop - start
    ensure_working_set(count, live_arrays=7)
    if x.full_definition:
        from .engine import evaluate_expression

        original = evaluate_expression(x.full_definition, np.arange(count, dtype=np.int64) + start)
        reflected = original[::-1]
        scope = 'Se evalúa la fórmula completa en n y en −n sobre una ventana simétrica.'
    else:
        original = np.zeros(count, dtype=np.complex128)
        reflected = np.zeros(count, dtype=np.complex128)
        xstart = int(x.origin) - start
        rstart = -(int(x.origin) + x.values.size - 1) - start
        original[xstart:xstart + x.values.size] = x.values
        reflected[rstart:rstart + x.values.size] = x.values[::-1]
        scope = 'Descomposición sin conjugación alrededor de n=0. Fuera del registro de entrada se usa cero.'
    even = _half_sum(original,reflected)
    odd = _half_sum(original,reflected,-1)
    metadata = _clock_for_index_transform(x,start,"even_odd_decomposition")
    metadata.update(input=x.name,scope=scope)
    return (
        Signal(even, start, 1, x.units, f"{x.name}_par", "discrete", "", dict(metadata)),
        Signal(odd, start, 1, x.units, f"{x.name}_impar", "discrete", "", dict(metadata)),
    )


def convolution_clock(x,h):
    """Share the physical output clock across linear-convolution algorithms."""
    from .system_clock import combined_clock
    return combined_clock(x, h, x.origin+h.origin, x.values.size+h.values.size-1, mode='convolution')


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
    from .system_clock import combined_clock
    from .spectral_scaling import bounded,restore_scale
    start = int(x.origin) - int(h.origin) - (h.values.size - 1)
    clock = combined_clock(x, h, start, count, mode='correlation')
    a,ea=bounded(x.values);b,eb=bounded(h.values)
    r=restore_scale(scipy_signal.correlate(a,b,mode="full",method="auto"),ea+eb)
    return Signal(_finite_output(r, "La correlación"), start, 1, x.units,
                  f"r_{x.name}{h.name}", "discrete", "",
                  {**clock,
                   "operation": "linear_cross_correlation", "inputs": [x.name, h.name],
                   "convention": "r[l]=sum_n x[n] conjugate(h[n-l]); zero outside support"})


def dft(x: Signal, length: int | None = None, *, centered: bool = False,
        phase_reference: str = 'record_offset') -> Signal:
    """DFT sin normalizar, con fase según los índices o las posiciones del registro."""
    from .fourier_phase import DFT_REFERENCES, bin_frequency, dft_values

    _discrete(x)
    if not isinstance(phase_reference, str) or phase_reference not in DFT_REFERENCES:
        raise ValueError('Elegí una referencia de fase válida para la DFT.')
    n = x.values.size if length is None else length
    if isinstance(n, bool) or not isinstance(n, (int, np.integer)) or int(n) < 1:
        raise ValueError("N debe ser un entero positivo.")
    n = int(n)
    ensure_working_set(n, bytes_per_sample=16, live_arrays=8)
    use_indices = phase_reference == 'sample_indices'
    values = dft_values(x.values, n, x.origin if use_indices else 0)
    values = _finite_output(values, "La DFT")
    action = "unchanged" if n == x.values.size else ("zero padded" if n > x.values.size else "truncated at N")
    metadata = {"operation": "DFT", "input_length": int(x.values.size), "N": n,
                "input_action": action,"input_origin":int(x.origin),
                "input_clock":{key:x.metadata[key] for key in ('sample_rate_hz','time_start_s') if key in x.metadata},
                "dft_phase_reference": phase_reference,
                "convention": ("sum x[n] exp(-2*pi*i*k*n/N), n starts at input_origin; no forward normalization"
                               if use_indices else "sum x[m] exp(-2*pi*i*k*m/N), m is stored offset from 0; no forward normalization")}
    if centered:
        metadata["dft_order"] = "centered"
        origin = bin_frequency(-(n//2), n)
        return Signal(np.fft.fftshift(values), origin, 2*np.pi/n, "rad/muestra",
                      "DFT X[k]", "frequency", "", metadata)
    return Signal(values, 0, 1, "bin k", "X[k]", "discrete", "", metadata)


def is_centered_dft(X: Signal) -> bool:
    return X.domain == "frequency" and X.units == "rad/muestra" and X.metadata.get("dft_order") == "centered"


def idft(X: Signal, *, restore_origin=False) -> Signal:
    """IDFT con división por N y restauración opcional de los índices de origen."""
    from .fourier_phase import dft_reference

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
    source_meta = X.metadata
    reference = dft_reference(X) if source_meta.get('operation') == 'DFT' else 'record_offset'
    if reference is None:
        raise ValueError('La referencia de fase de la DFT no es válida.')
    initial = source_meta.get('input_origin', source_meta.get('source_origin')) if source_meta.get('operation') == 'DFT' else None
    if initial is not None and type(initial) is not int:
        raise ValueError('El índice original de la DFT debe ser entero.')
    if reference == 'sample_indices' and (initial is None or (not centered and (source_meta.get('N') != n or X.origin != 0))):
        raise ValueError('La DFT con fase en n requiere el origen y sus N bins completos en la rejilla original.')
    coefficients = np.fft.ifftshift(X.values) if centered else X.values
    from .spectral_scaling import fft_values
    values = _finite_output(fft_values(coefficients,inverse=True), "La IDFT")
    if reference == 'sample_indices' and initial % n:
        # The cyclic shift is undone even when only the output axis is relabeled at zero.
        values = np.roll(values, -(initial % n))
    metadata={"operation":"IDFT","N":n,
              "input_dft_phase_reference": reference,
              "convention":("(1/N) sum X[k] exp(+2*pi*i*k*(input_origin+m)/N)"
                            if reference == 'sample_indices' else "(1/N) sum X[k] exp(+2*pi*i*k*m/N), m is stored output offset from 0")}
    origin=0
    if X.metadata.get('operation')=='DFT':
        if initial is not None:
            metadata['original_origin']=initial
            if restore_origin:origin=initial
        clock=source_meta.get('input_clock',{})
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
    from .system_clock import combined_clock
    from .spectral_scaling import bounded,restore_scale
    clock=combined_clock(x,h,0,n,mode='convolution')
    a,ea=bounded(x.values);b,eb=bounded(h.values)
    values=restore_scale(np.fft.ifft(np.fft.fft(a,n)*np.fft.fft(b,n)),ea+eb)
    return Signal(_finite_output(values, "La convolución circular"), 0, 1, x.units,
                  f"{x.name}*c{h.name}", "discrete", "",
                  {**clock,
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
    from .system_clock import combined_clock
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
            values, _ = bounded(signal.values, normalize=True)
            norm = np.sqrt(np.sum(np.abs(values) ** 2))
            if norm == 0:
                raise ValueError("La correlación normalizada no está definida para energía cero.")
            return signal.copy_with(values=values / norm)
        left, right = unit_energy(x), unit_energy(h)
    if circular:
        n = x.values.size
        from .spectral_scaling import restore_scale
        clock = combined_clock(x,h,0,n,mode='periodic_correlation')
        a,ea=bounded(left.values);b,eb=bounded(right.values)
        factor=1/n if normalization=="mean" else 1.
        values=restore_scale(np.fft.ifft(np.fft.fft(a)*np.conj(np.fft.fft(b))),ea+eb,factor)
        values = np.roll(values, (int(x.origin) - int(h.origin)) % n)
        result = Signal(_finite_output(values, "La correlación circular"), 0, 1, "retardo",
                        f"r_{x.name}{h.name}", "discrete", metadata=clock)
    else:
        result = linear_correlation(left, right)
    result.metadata = {**result.metadata, "operation": "correlation", "circular": circular,
        "normalization": normalization, "inputs": [x.name, h.name],
        "convention": "sum x[n] conj(h[n-l]); no mean subtraction; no overlap correction",
        "period": int(x.values.size) if circular else None}
    return result
