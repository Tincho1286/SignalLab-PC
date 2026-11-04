"""Muestreo y conversión: convenciones numéricas del código HP 5.0."""
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
import math

import numpy as np
from scipy.signal import fftconvolve

from .engine import evaluate_expression
from .model import Signal
from .operations import _discrete, _finite_output
from .resources import ensure_working_set


def positive_integer(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value < 1:
        raise ValueError(f"{label} debe ser un entero positivo.")
    return int(value)


def positive_finite(value, label):
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{label} debe ser real, finito y positivo.")
    return value


def sample_expression(expression, start, rate, count, name="x[n]"):
    from .continuous_expression import has_dirac
    if has_dirac(expression):raise ValueError('Una Dirac ideal tiene peso, no un valor puntual finito. Para muestrear, definí un pulso de duración finita o una señal ordinaria; impulse(n) se usa directamente como secuencia discreta.')
    rate = positive_finite(rate, "Fs")
    count = positive_integer(count, "N")
    start = float(start)
    if not math.isfinite(start):
        raise ValueError("El tiempo inicial debe ser finito.")
    ensure_working_set(count, live_arrays=8)
    time = start + np.arange(count, dtype=float) / rate
    if not np.all(np.isfinite(time)) or (count > 1 and np.any(np.diff(time) <= 0)):
        raise ValueError("La rejilla temporal no se distingue con precisión float64; ajustá t0, Fs o N.")
    return Signal(evaluate_expression(expression, time), 0, 1, "n", name, "discrete", expression,
                  {"operation": "sampling", "sample_rate_hz": rate, "time_start_s": start,
                   "time_mapping": "t = time_start_s + (n-origin)/sample_rate_hz"})


def alias_frequency(frequency, rate):
    """Representante firmado en [-Fs/2,Fs/2); no prueba banda limitada."""
    rate = positive_finite(rate, "Fs")
    frequency = float(frequency)
    if not math.isfinite(frequency):
        raise ValueError("La frecuencia debe ser finita.")
    remainder = math.remainder(frequency, rate)
    alias = -rate / 2 if remainder == rate / 2 else remainder
    return {"frequency_hz": frequency, "sample_rate_hz": rate,
            "nyquist_hz": rate / 2, "signed_alias_hz": alias,
            "real_sinusoid_alias_hz": abs(alias),
            "strict_nyquist": abs(frequency) < rate / 2,
            "at_nyquist": abs(frequency) == rate / 2}


def alias_angular_frequency(omega, rate):
    """Signed angular representative; Fs stays a sample rate in samples/s."""
    rate=positive_finite(rate,'Fs');omega=float(omega)
    if not math.isfinite(omega):raise ValueError('La frecuencia angular debe ser finita.')
    nyquist=math.pi*rate;period=2*nyquist
    if not math.isfinite(period) or not period:raise ValueError('La frecuencia angular de muestreo no es representable.')
    remainder=math.remainder(omega,period);alias=-nyquist if remainder==nyquist else remainder
    return dict(frequency_rad_s=omega,sample_rate_hz=rate,nyquist_rad_s=nyquist,signed_alias_rad_s=alias,real_sinusoid_alias_rad_s=abs(alias),digital_alias_rad_sample=alias/rate,
        frequency_hz=omega/(2*math.pi),signed_alias_hz=alias/(2*math.pi),nyquist_hz=rate/2,real_sinusoid_alias_hz=abs(alias)/(2*math.pi),strict_nyquist=abs(omega)<nyquist,at_nyquist=abs(omega)==nyquist,alias_at_nyquist=abs(alias)==nyquist)


def resample(x, factor, method, phase=0):
    """fase local al registro, salida de interpolación (N-1)L+1.

    Diezmado reindexa desde cero; conserva el tiempo de la primera muestra
    cuando existe Fs. No aplica filtro antialias de manera implícita.
    """
    _discrete(x)
    factor = positive_integer(factor, "Factor")
    metadata = dict(x.metadata)
    metadata.update(operation="resample", method=method, factor=factor,
                    input_origin=int(x.origin), input_length=int(x.values.size))
    rate = metadata.get("sample_rate_hz")
    if method == "decimate":
        if isinstance(phase, bool) or not isinstance(phase, (int, np.integer)) or not 0 <= phase < factor:
            raise ValueError("La fase debe ser un entero de 0 a M-1.")
        if phase >= x.values.size:
            raise ValueError("La fase deja el registro sin muestras.")
        count = (x.values.size - 1 - phase) // factor + 1
        ensure_working_set(count, live_arrays=4)
        values = x.values[phase::factor]
        origin = 0
        metadata.update(phase=int(phase), antialias_filter=False,
                        index_mapping="input n = input_origin + phase + factor * output n")
        if rate is not None:
            rate = positive_finite(rate, "Fs de entrada")
            metadata["sample_rate_hz"] = positive_finite(rate / factor, "Fs de salida")
            metadata["time_start_s"] = float(metadata.get("time_start_s", 0)) + phase / rate
    else:
        if method not in {"expand", "linear", "zoh", "sinc"}:
            raise ValueError("Método de remuestreo desconocido.")
        count = (x.values.size - 1) * factor + 1
        ensure_working_set(count, live_arrays=30 if method == "sinc" else 8)
        origin = int(x.origin) * factor
        limit = np.iinfo(np.int64)
        if origin < limit.min or origin + count - 1 > limit.max:
            raise ValueError("El eje de salida excede los índices enteros de 64 bits.")
        if method in {"expand", "sinc"}:
            values = np.zeros(count, dtype=complex)
            values[::factor] = x.values
            if method == "sinc" and count > 1 and factor > 1:
                radius = count - 1
                lag = np.arange(-radius, radius + 1, dtype=np.int64)
                kernel = np.sinc(lag / factor)
                kernel[(lag % factor == 0) & (lag != 0)] = 0
                values = fftconvolve(values, kernel, mode="full")[radius:radius + count]
                values[::factor] = x.values
        elif method == "zoh":
            values = x.values[np.arange(count, dtype=np.int64) // factor]
        else:
            positions = np.arange(count, dtype=np.int64)
            left = positions // factor
            weight = (positions % factor) / factor
            values = (1-weight)*x.values[left] + weight*x.values[np.minimum(left+1, x.values.size-1)]
        if rate is not None:
            metadata["sample_rate_hz"] = positive_finite(float(rate)*factor, "Fs de salida")
        metadata["support"] = "Finite input, zero outside; output ends at last original sample"
    return Signal(_finite_output(values, "El remuestreo"), origin, 1, x.units,
                  f"{x.name}_{method}", "discrete", "", metadata)


def reconstruct(x, rate, start, factor, method):
    """Reconstrucción sobre el intervalo almacenado, con L subdivisiones/Ts."""
    _discrete(x)
    rate = positive_finite(rate, "Fs")
    factor = positive_integer(factor, "Subdivisiones")
    start = float(start)
    if not math.isfinite(start):
        raise ValueError("t0 debe ser finito.")
    if method not in {"zoh", "linear", "sinc"}:
        raise ValueError("Elegí ZOH, lineal o SINC.")
    from copy import copy
    # Interpolation is local to the record. Its physical axis is set below.
    local=copy(x)
    local.origin=0
    local.metadata={}
    interpolated = resample(local, factor, method)
    step = 1 / rate / factor
    end = start + (interpolated.values.size - 1)*step
    if not math.isfinite(end) or step <= 0 or start+step == start or end-step == end:
        raise ValueError("La resolución temporal excede la precisión disponible.")
    return Signal(interpolated.values, start, step, "s", f"{x.name}_{method}(t)", "continuous", "",
                  {"operation": "reconstruction", "method": method, "source_rate_hz": rate,
                   "model": "Finite input; SINC includes all input samples, no window or renormalization",
                   "display_window": "first through last stored sample; infinite SINC tails omitted"})


@dataclass
class QuantizationResult:
    signal: Signal
    error: Signal
    step: float
    levels: int
    effective_min: float
    effective_max: float
    clipped_samples: int
    snr_db: float | None
    selected_samples: int


def _log_energy(values):
    scale = float(np.max(np.abs(values), initial=0))
    if scale == 0:
        return -math.inf
    return 2*math.log10(scale) + math.log10(float(np.sum((values/scale)**2)))


def quantize(x, bits, low, high, method="round", align_zero=False, first=0, last=None):
    bits = positive_integer(bits, "Bits")
    # La salida usa float64: más de 52 bits no distingue todos los códigos.
    if bits > 52:
        raise ValueError("La cuantización numérica admite hasta 52 bits por precisión float64.")
    if np.any(x.values.imag != 0):
        raise ValueError("La cuantización requiere muestras reales.")
    low, high = float(low), float(high)
    if not math.isfinite(low) or not math.isfinite(high) or high <= low:
        raise ValueError("El rango debe tener extremos finitos y máximo mayor que mínimo.")
    if method not in {"round", "floor"}:
        raise ValueError("Elegí redondeo o nivel inferior.")
    if align_zero and not low <= 0 <= high:
        raise ValueError("Alinear cero requiere que el rango incluya cero.")
    levels = 1 << bits
    span=high-low
    wide=not math.isfinite(span)
    step=high/(levels-1)-low/(levels-1) if wide else span/(levels-1)
    if not math.isfinite(step) or step <= 0:
        raise ValueError("El paso de cuantización queda fuera del rango numérico.")
    kzero = min(levels-1, max(0, math.floor(-low/step + .5))) if align_zero else 0
    if align_zero:
        low, high = -kzero*step, (levels-1-kzero)*step
    if low+step == low or high-step == high:
        raise ValueError("Los niveles no se distinguen en float64 con ese rango y cantidad de bits.")
    ensure_working_set(int(x.values.size), live_arrays=14)
    original = x.values.real
    clipped = np.clip(original, low, high)
    if align_zero:
        codes=clipped/step+kzero
    elif wide:
        scale=max(-low,high)
        codes=(clipped/scale-low/scale)/(step/scale)
    else:
        codes=(clipped-low)/step
    codes = np.floor(codes+.5) if method == "round" else np.floor(codes)
    codes = np.clip(codes, 0, levels-1)
    if align_zero:
        values=(codes-kzero)*step
    elif wide:
        fraction=codes/(levels-1)
        values=(1-fraction)*low+fraction*high
    else:
        values=low+codes*step
    error = _finite_output(values-original, "El error de cuantización")
    last = x.values.size-1 if last is None else last
    if any(isinstance(v, bool) or not isinstance(v, (int, np.integer)) for v in (first, last)) or not 0 <= first <= last < x.values.size:
        raise ValueError("El intervalo SNR debe contener filas válidas, con ambos extremos incluidos.")
    # Escala común antes de restar evita overflow en energías; error firmado se conserva.
    signal_energy = _log_energy(original[first:last+1])
    error_energy = _log_energy(error.real[first:last+1])
    snr = None if signal_energy == error_energy == -math.inf else 10*(signal_energy-error_energy)
    metadata = {**x.metadata, "operation": "quantization", "bits": bits, "step": step,
                "method": method, "zero_aligned": bool(align_zero), "effective_range": [low, high],
                "snr_rows_inclusive": [int(first), int(last)],
                "snr_db": snr if snr is None or math.isfinite(snr) else str(snr),
                "convention": "Endpoints; floor is lower level, not truncation toward zero"}
    result = Signal(values, x.origin, x.step, x.units, f"{x.name}_q", x.domain, "", metadata)
    residual = Signal(error, x.origin, x.step, x.units, f"error_{x.name}", x.domain, "",
                      {"operation": "quantization_error", "convention": "xq-x"})
    return QuantizationResult(result, residual, step, levels, low, high,
                              int(np.count_nonzero(original != clipped)), snr, int(last-first+1))


def fixed_point(value, integer_bits, fractional_bits, method="round"):
    """Q firmado exacto, sin tope HP de 32 bits; salida binaria complemento a dos."""
    integer_bits = positive_integer(integer_bits, "Bits enteros (incluyen signo)")
    if isinstance(fractional_bits, bool) or not isinstance(fractional_bits, int) or fractional_bits < 0:
        raise ValueError("Los bits fraccionarios deben ser un entero no negativo.")
    if method not in {"round", "truncate"}:
        raise ValueError("Método de punto fijo desconocido.")
    width = integer_bits+fractional_bits
    ensure_working_set(width, bytes_per_sample=1, live_arrays=32)
    decimal = Decimal(str(value))
    if not decimal.is_finite():
        raise ValueError("El valor debe ser real y finito.")
    source = Fraction(decimal)
    scale = 1 << fractional_bits
    low_code, high_code = -(1 << (width-1)), (1 << (width-1))-1
    scaled = source*scale
    clipped = min(Fraction(high_code), max(Fraction(low_code), scaled))
    absolute = abs(clipped)
    code = absolute.numerator // absolute.denominator
    if method == "round" and 2*(absolute.numerator % absolute.denominator) >= absolute.denominator:
        code += 1
    if clipped < 0:
        code = -code
    represented = Fraction(code, scale)
    return {"format": f"Q({integer_bits},{fractional_bits})", "input": str(source),
            "represented_exact": str(represented), "signed_code": str(code),
            "binary_twos_complement": format(code % (1 << width), f"0{width}b"),
            "lsb_exact": str(Fraction(1, scale)), "minimum_exact": str(Fraction(low_code, scale)),
            "maximum_exact": str(Fraction(high_code, scale)), "total_error_exact": str(source-represented),
            "saturation_error_exact": str(source-clipped/scale),
            "conversion_error_exact": str(clipped/scale-represented), "rounding": method}

def resample_rational(x, up, down, *, rate=None, start=None, half_width=10, beta=5.0, boundary='zero'):
    """Conversión L/M con FIR polifásico simétrico, alineado al primer instante.

    Fuente: scipy.signal.resample_poly. La extensión fuera del registro es
    explícita; la compensación de retardo corresponde a procesamiento offline.
    """
    from scipy.signal import resample_poly, firwin
    from .jobs import checkpoint
    _discrete(x)
    up=positive_integer(up,'L');down=positive_integer(down,'M');half_width=positive_integer(half_width,'Semilongitud por fase')
    divisor=math.gcd(up,down);up//=divisor;down//=divisor
    if boundary not in ('zero','line'):raise ValueError('Elegí extensión nula o lineal.')
    if boundary=='line' and x.values.size<2:raise ValueError('La extensión lineal requiere al menos dos muestras.')
    beta=float(beta)
    if not math.isfinite(beta) or beta<0:raise ValueError('Beta Kaiser debe ser finito y no negativo.')
    rate=positive_finite(rate if rate is not None else x.metadata.get('sample_rate_hz',0),'Fs de entrada')
    output_rate=positive_finite(rate*(up/down),'Fs de salida')
    start=float(x.metadata.get('time_start_s',0) if start is None else start)
    if not math.isfinite(start):raise ValueError('El tiempo inicial debe ser finito.')
    count=(int(x.values.size)*up+down-1)//down
    taps=1 if up==down else 2*half_width*max(up,down)+1
    ensure_working_set(count+int(x.values.size)+taps,live_arrays=16)
    if count>1 and (start+1/output_rate==start or not math.isfinite(start+(count-1)/output_rate)):
        raise ValueError('El reloj de salida excede la resolución o el rango numérico.')
    checkpoint()
    if up==down:values=x.values.copy()
    else:
        kernel=firwin(taps,1/max(up,down),window=('kaiser',beta))
        values=resample_poly(x.values,up,down,window=kernel,padtype='constant' if boundary=='zero' else 'line')
    checkpoint()
    metadata=dict(x.metadata)
    metadata.update(operation='resample_rational',up=up,down=down,input_rate_hz=rate,sample_rate_hz=output_rate,time_start_s=start,
        input_origin=int(x.origin),input_length=int(x.values.size),antialias_filter=up!=down,filter_taps=taps,kaiser_beta=beta,
        boundary=boundary,delay='linear-phase FIR delay compensated; offline processing',
        time_mapping='t = time_start_s + n / sample_rate_hz',
        output_length_rule='ceil(input_length * up / down)',
        scope='Finite FIR transition band; no guarantee of ideal band limitation. Edges depend on the chosen extension.')
    return Signal(_finite_output(values,'El cambio de tasa racional'),0,1,'n',f'{x.name}_{up}_{down}','discrete','',metadata)
