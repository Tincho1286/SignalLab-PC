"""Filtros y sistemas LTI: convenciones de SSFIR, SSBiquad y SSDiffEq HP 5.0."""
from dataclasses import dataclass

import numpy as np
from scipy import signal as sp

from .model import Signal
from .resources import ensure_working_set


def validate_roc(specification,domain='digital'):
    from copy import deepcopy
    if specification is None:return None
    modes=('right','left','radius') if domain=='digital' else ('right','left','line')
    if not isinstance(specification,dict) or specification.get('mode') not in modes:raise ValueError('Región de convergencia incompatible con el dominio del sistema.')
    result=deepcopy(specification)
    if result['mode'] in ('radius','line'):
        key='radius' if domain=='digital' else 'sigma';value=result.get(key)
        if type(value) not in (int,float) or not np.isfinite(value) or key=='radius' and value<=0:raise ValueError('El radio de la ROC debe ser positivo y finito.' if key=='radius' else 'La parte real σ debe ser un número real finito, interior a la ROC.')
    return result


def coefficients(values):
    result = np.asarray(values, dtype=np.complex128).reshape(-1)
    if not result.size or not np.all(np.isfinite(result)):
        raise ValueError("Los coeficientes deben formar una lista finita no vacía.")
    return result.copy()


def positive_integer(value, label="N"):
    if isinstance(value, bool) or int(value) != value or value < 1:
        raise ValueError(f"{label} debe ser un entero positivo.")
    return int(value)


def shifted_roots(zeros,poles,advance):
    if advance:
        at_origin=np.flatnonzero(poles==0);cancel=min(advance,len(at_origin))
        poles=np.delete(poles,at_origin[:cancel]);zeros=np.r_[zeros,np.zeros(advance-cancel)]
    return zeros,poles


@dataclass
class Transfer:
    b: np.ndarray
    a: np.ndarray
    domain: str = "digital"
    name: str = "H"
    sos: np.ndarray | None = None
    advance: int = 0
    sample_period_s: float | None = None
    roc: dict | None = None

    def __post_init__(self):
        self.roc=validate_roc(self.roc,self.domain)
        from .system_clock import validate_period
        self.sample_period_s=validate_period(self.sample_period_s,self.domain)
        if isinstance(self.advance,bool) or int(self.advance)!=self.advance or self.advance<0 or self.domain!='digital' and self.advance:raise ValueError('El avance debe ser un entero no negativo de un sistema discreto.')
        self.advance=int(self.advance)
        if self.sos is not None:
            sections=np.asarray(self.sos,dtype=complex)
            if self.domain!='digital' or sections.ndim!=2 or sections.shape[1]!=6 or not len(sections):
                raise ValueError('Las secciones requieren un sistema digital y seis coeficientes por fila.')
            if not np.all(np.isfinite(sections)) or np.any(sections.imag) or np.any(sections[:,3]==0):
                raise ValueError('Las secciones deben ser reales, finitas y tener a0 distinto de cero.')
            self.sos=sections.real.copy()/sections[:,3].real[:,None]
            if not np.all(np.isfinite(self.sos)):raise ValueError('Las secciones exceden el rango numérico.')
            self.b,self.a=sp.sos2tf(self.sos)
            self.b=np.trim_zeros(self.b,'b') if np.any(self.b) else np.array([0.])
            self.a=np.trim_zeros(self.a,'b')
        self.b, self.a = coefficients(self.b), coefficients(self.a)
        if self.domain not in {"digital", "analog"}:
            raise ValueError("Dominio: digital o analog.")
        if self.domain == "analog":
            self.a = np.trim_zeros(self.a, "f")
        if not self.a.size or self.a[0] == 0:
            raise ValueError("El primer coeficiente de a debe ser distinto de cero.")
        a0 = self.a[0]
        original_b,original_a=self.b,self.a
        with np.errstate(over='ignore',under='ignore',invalid='ignore'):
            self.b, self.a = self.b / a0, self.a / a0
        if np.any((original_b!=0)&(self.b==0)) or np.any((original_a!=0)&(self.a==0)):
            raise ValueError('Normalizar por a0 elimina coeficientes no nulos por falta de rango numérico. Reescalá los coeficientes.')
        if not np.all(np.isfinite(self.b)) or not np.all(np.isfinite(self.a)):
            raise ValueError("Normalizar por a0 excede el rango numérico finito.")
        if self.advance and self.sos is not None:
            changed=False
            for row in self.sos:
                if not np.any(row[:3]):self.advance=0;break
                while self.advance and row[0]==0:
                    row[:3]=[row[1],row[2],0];self.advance-=1;changed=True
            if changed:
                self.b,self.a=sp.sos2tf(self.sos)
                self.b=np.trim_zeros(self.b,'b') if np.any(self.b) else np.array([0.])
                self.a=np.trim_zeros(self.a,'b')
                self.b,self.a=coefficients(self.b),coefficients(self.a)
        if self.advance and self.sos is None:
            if not np.any(self.b):self.advance=0
            else:
                leading=int(np.flatnonzero(self.b)[0]);cancel=min(leading,self.advance)
                self.b=self.b[cancel:];self.advance-=cancel

    @classmethod
    def from_sos(cls,sections,name='Filtro en secciones',*,sample_period_s=None):
        return cls([1],[1],'digital',name,sections,sample_period_s=sample_period_s)

    def to_document(self):
        result={'format':'signallab-transfer','version':5 if self.domain=='analog' and self.roc is not None else 4 if self.roc is not None else 3 if self.sample_period_s is not None else 2 if self.advance else 1,'domain':self.domain,'name':self.name,
                'b':[[float(v.real),float(v.imag)] for v in self.b],
                'a':[[float(v.real),float(v.imag)] for v in self.a]}
        if self.roc is not None:result['roc']=dict(self.roc)
        if self.sos is not None:result['sos']=self.sos.tolist()
        if self.advance or self.sample_period_s is not None or self.roc is not None:result['advance']=self.advance
        if self.sample_period_s is not None:result['sample_period_s']=self.sample_period_s
        return result

    @classmethod
    def from_document(cls,document):
        """Validate the complete transfer document before touching an editor."""
        if not isinstance(document,dict) or document.get('format')!='signallab-transfer':raise ValueError('El archivo no es una función de transferencia SignalLab.')
        version=document.get('version')
        if type(version) is not int or version not in (1,2,3,4,5):raise ValueError('Versión de archivo de sistema no compatible; se admiten 1 a 5.')
        advance=document.get('advance',0)
        if version in (2,3,4,5) and 'advance' not in document:raise ValueError('Los formatos 2 y 3 deben indicar advance; no se supone que el avance sea cero.')
        if type(advance) is not int or advance<0 or version==1 and advance:raise ValueError('El avance debe ser un entero no negativo y requiere formato 2 o 3 si es distinto de cero.')
        domain=document.get('domain');name=document.get('name','Sistema importado')
        if domain not in ('digital','analog') or domain=='analog' and advance:raise ValueError('El dominio debe ser analog o digital; un avance sólo corresponde a un sistema digital.')
        if not isinstance(name,str):raise ValueError('El nombre del sistema debe ser texto.')
        def vector(key):
            values=document.get(key)
            if not isinstance(values,list) or not values:raise ValueError('El campo '+key+' debe contener coeficientes [real, imaginaria].')
            ensure_working_set(len(values),live_arrays=8)
            if any(not isinstance(pair,list) or len(pair)!=2 or any(type(part) not in (int,float) for part in pair) for pair in values):raise ValueError('Cada coeficiente de '+key+' debe ser un par numérico [real, imaginaria].')
            try:result=np.asarray(values,dtype=float)
            except (ValueError,OverflowError):raise ValueError('Los coeficientes de '+key+' exceden el rango numérico.')
            if not np.isfinite(result).all():raise ValueError('Los coeficientes de '+key+' deben ser finitos.')
            return result[:,0]+1j*result[:,1]
        period=document.get('sample_period_s')
        if version==3 and type(period) not in (int,float):raise ValueError('El formato 3 debe registrar sample_period_s como número positivo y finito.')
        if version not in (3,4,5) and period is not None:raise ValueError('El período de un archivo de transferencia requiere formato 3.')
        roc=document.get('roc')
        if version in (4,5) and roc is None:raise ValueError('Los formatos 4 y 5 deben incluir la definición de ROC.')
        if version not in (4,5) and roc is not None:raise ValueError('La ROC requiere formato 4 (digital) o 5 (analógico).')
        if roc is not None and (version==4 and domain!='digital' or version==5 and domain!='analog'):raise ValueError('El formato 4 corresponde a ROC digital y el formato 5 a ROC analógica.')
        b,a=vector('b'),vector('a');sos=document.get('sos')
        if sos is None:return cls(b,a,domain,name,advance=advance,sample_period_s=period,roc=roc)
        if not isinstance(sos,list) or not sos or any(not isinstance(row,list) or len(row)!=6 or any(type(value) not in (int,float) for value in row) for row in sos):raise ValueError('SOS requiere seis números reales por sección.')
        ensure_working_set(len(sos)*6,live_arrays=8)
        reference=cls(b,a,domain,name);stored=cls(b,a,domain,name,sos)
        for key in ('b','a'):
            one,two=getattr(reference,key),getattr(stored,key)
            one=np.trim_zeros(one,'b');two=np.trim_zeros(two,'b');size=max(len(one),len(two))
            one=np.pad(one,(0,size-len(one)));two=np.pad(two,(0,size-len(two)))
            scale=max(float(np.max(abs(one.real),initial=0)),float(np.max(abs(one.imag),initial=0)),float(np.max(abs(two.real),initial=0)),float(np.max(abs(two.imag),initial=0)))
            if scale and np.max(abs(one/scale-two/scale),initial=0)>1e-11:raise ValueError('Los coeficientes '+key+' no coinciden con las SOS del archivo. No se elige una definición contradictoria.')
        return cls(b,a,domain,name,sos,advance,sample_period_s=period,roc=roc)

    def poles_zeros(self):
        if self.sos is not None:
            zeros=[];poles=[]
            for row in self.sos:
                b=np.trim_zeros(row[:3],'b');a=np.trim_zeros(row[3:],'b')
                degree=max(len(b),len(a))
                zeros.extend(np.roots(np.pad(b,(0,degree-len(b)))))
                poles.extend(np.roots(np.pad(a,(0,degree-len(a)))))
            return shifted_roots(np.asarray(zeros,dtype=complex),np.asarray(poles,dtype=complex),self.advance)
        b, a = self.b, self.a
        # El cálculo de raíces usa una matriz compañera: el costo de memoria es cuadrático.
        order = max(len(a), len(b))-1
        ensure_working_set(order*order, live_arrays=4)
        if self.domain == "digital":
            degree = max(len(a), len(b))
            b = np.pad(b, (0, degree-len(b)))
            a = np.pad(a, (0, degree-len(a)))
        zeros,poles=np.roots(np.trim_zeros(b, "f")),np.roots(a)
        return shifted_roots(zeros,poles,self.advance)

    def causal_pole_stability(self, poles=None):
        """Sin cancelaciones aproximadas: informa polos sobre la frontera aparte."""
        if poles is None:
            _, poles = self.poles_zeros()
        metric = abs(poles) - 1 if self.domain == "digital" else poles.real
        if np.any(metric > 0):
            return "Inestable"
        if np.any(metric == 0):
            return "Frontera de estabilidad; no BIBO estable"
        return "Estable (polos estrictamente dentro de la región estable)"

    def stability(self,poles=None):
        """BIBO classification with an explicit ROC, otherwise a labelled hypothesis."""
        from .system_conditions import record
        if self.roc is not None or not np.any(self.b):
            status=record(self)['bibo_stability']
            return ('Estable: '+status if status.startswith('Sí:') else 'Inestable: '+status if status.startswith('No:') or status.startswith('No BIBO') else status)
        if self.domain=='analog' and len(np.trim_zeros(self.b,'f'))>len(self.a):
            return 'Inestable BIBO: transferencia analógica impropia; la ubicación de polos no basta.'
        return self.causal_pole_stability(poles)+'; criterio bajo hipótesis causal. Falta especificar la ROC.'

    def response(self, omega):
        """Frequency response; poles and values outside numerical range are N/D."""
        omega=np.asarray(omega,dtype=float)
        if not np.isfinite(omega).all():raise ValueError('La frecuencia debe ser finita.')
        ensure_working_set(int(omega.size),live_arrays=10)
        digital=self.domain=='digital'
        point=np.exp(-1j*omega) if digital else 1j*omega
        if digital:point=np.where(omega==0,1+0j,point);point=np.where(abs(omega)==np.pi,-1+0j,point)
        if self.sos is not None:
            if any(not np.any(row[:3]) for row in self.sos):return np.zeros(omega.shape,dtype=complex)
            result=np.ones(omega.shape,dtype=complex)
            with np.errstate(all='ignore'):
                for row in self.sos:result*=Transfer(row[:3],row[3:]).response(omega)
            mask=~np.isfinite(result)|(result==0)
        else:
            if not np.any(self.b):return np.zeros(omega.shape,dtype=complex)
            b,a=(self.b[::-1],self.a[::-1]) if digital else (self.b,self.a)
            with np.errstate(all='ignore'):
                numerator=np.polyval(b,point);denominator=np.polyval(a,point)
                bound=np.polyval(abs(a),abs(point));result=numerator/denominator
                uncertain=abs(denominator)<=(32+8*len(a))*np.finfo(float).eps*bound
            mask=~np.isfinite(result)|(result==0)|uncertain|~np.isfinite(bound)
        from .rational_frequency import repair
        result=repair(self,point,result,mask)
        with np.errstate(all='ignore'):
            if self.advance:result=result*np.exp(1j*omega*self.advance)
        return np.where(np.isfinite(result),result,complex(np.nan,np.nan))

    def group_delay(self, omega):
        """Analytic logarithmic derivative with exact exceptional-point repair."""
        omega=np.asarray(omega,dtype=float)
        if not np.isfinite(omega).all():raise ValueError('La frecuencia debe ser finita.')
        ensure_working_set(int(omega.size+len(self.b)+len(self.a)),live_arrays=10)
        digital=self.domain=='digital';point=np.exp(-1j*omega) if digital else 1j*omega
        if digital:point=np.where(omega==0,1+0j,point);point=np.where(abs(omega)==np.pi,-1+0j,point)
        if self.sos is not None:
            if any(not np.any(row[:3]) for row in self.sos):return np.full(omega.shape,np.nan)
            result=np.zeros(omega.shape,dtype=float);roundoff=np.zeros(omega.shape,dtype=float)
            with np.errstate(all='ignore'):
                for row in self.sos:
                    stage=Transfer(row[:3],row[3:]).group_delay(omega);result+=stage;roundoff+=abs(stage)
            result-=self.advance;roundoff=32*np.finfo(float).eps*(roundoff+self.advance)
        else:
            if not np.any(self.b):return np.full(omega.shape,np.nan)
            if len(self.b)==len(self.a)==1:return np.full(omega.shape,-float(self.advance))
            def logarithmic(coeff):
                scale=max(float(np.max(abs(coeff.real))),float(np.max(abs(coeff.imag))))
                if scale==0:return np.full(omega.shape,complex(np.nan,np.nan))
                coeff=coeff/scale;polynomial=coeff[::-1] if digital else coeff
                weighted=(np.arange(len(coeff))*coeff)[::-1] if digital else np.polyder(coeff)
                with np.errstate(all='ignore'):
                    value=np.polyval(polynomial,point);derivative=np.polyval(weighted,point)
                    bound=np.polyval(abs(polynomial),abs(point))
                    valid=np.isfinite(value)&np.isfinite(derivative)&np.isfinite(bound)&(abs(value)>(32+8*len(polynomial))*np.finfo(float).eps*bound)
                    quotient=np.full(omega.shape,complex(np.nan,np.nan));np.divide(derivative,value,out=quotient,where=valid)
                return quotient
            with np.errstate(all='ignore'):
                one,two=logarithmic(self.b),logarithmic(self.a)
                result=np.asarray((one-two).real*(1 if digital else -1))-self.advance
                roundoff=32*np.finfo(float).eps*(abs(one)+abs(two)+self.advance)
        from .rational_frequency import repair
        result=repair(self,point,result,~np.isfinite(result)|(result==0)|(abs(result)<=roundoff),delay=True)
        if digital and self.sos is None and not np.any(self.a[1:]) and np.all(self.b.imag==0):
            if np.array_equal(self.b,self.b[::-1]) or np.array_equal(self.b,-self.b[::-1]):result=np.where(np.isfinite(result),(len(self.b)-1)/2-self.advance,np.nan)
        return np.where(np.isfinite(result),result,np.nan)

    def apply(self, x: Signal, previous_inputs=(), previous_outputs=()):
        """Reposo inicial por defecto; historiales desde la muestra más reciente."""
        if self.advance:raise ValueError('El sistema contiene un avance temporal. Esta recurrencia es causal; analizá su frecuencia o usá Z inversa con ROC para obtener su respuesta bilateral.')
        if self.domain != "digital":
            raise ValueError("La ecuación en diferencias requiere coeficientes digitales.")
        from .system_conditions import require_causal_roc
        require_causal_roc(self)
        from .system_clock import input_metadata
        clock=input_metadata(self,x)
        clock.pop('excitation',None)
        ensure_working_set(int(x.values.size), live_arrays=5)
        has_history = bool(np.any(previous_inputs) or np.any(previous_outputs))
        from .transfer_plane import causal_sections, effective_system
        sections = causal_sections(self) if self.sos is not None and not has_history else None
        model = effective_system(self) if sections is None and not has_history else self
        if sections is not None:
            result = sp.sosfilt(sections, x.values)
        elif has_history:
            initial = sp.lfiltic(model.b, model.a, previous_outputs, previous_inputs)
            result = sp.lfilter(model.b, model.a, x.values, zi=initial)
        else:
            result = sp.lfilter(model.b, model.a, x.values)
        if isinstance(result, tuple):
            result = result[0]
        if not np.all(np.isfinite(result)):
            raise FloatingPointError("La respuesta excede el rango numérico finito.")
        return Signal(result, x.origin, x.step, x.units, f"{self.name}({x.name})",
                      x.domain, "", {**clock, "operation": "difference_equation",
                      "b": [[v.real, v.imag] for v in model.b], "a": [[v.real, v.imag] for v in model.a],
                      "initial_rest": not has_history, "input_name": x.name,
                      "previous_inputs": [[float(complex(v).real),float(complex(v).imag)] for v in previous_inputs],
                      "previous_outputs": [[float(complex(v).real),float(complex(v).imag)] for v in previous_outputs],
                      "realization": "second_order_sections" if sections is not None else "polynomial",
                      "sos": sections.tolist() if sections is not None else None})

    def excitation_response(self, count, kind="impulse"):
        count = positive_integer(count)
        if kind not in {"impulse", "step"}:
            raise ValueError("Excitación: impulse o step.")
        ensure_working_set(count, live_arrays=6)
        values = np.zeros(count) if kind == "impulse" else np.ones(count)
        values[0] = 1
        result=self.apply(Signal(values,name=kind))
        result.metadata['excitation']=kind
        return result


def fir(kind, taps, f1, f2=None, window="hamming", beta=8.6):
    """Frecuencias en ciclos/muestra; no normaliza la ganancia, como SSFIR."""
    taps = positive_integer(taps, "Cantidad de coeficientes")
    if kind not in {"lowpass", "highpass", "bandpass", "bandstop"}:
        raise ValueError("Tipo FIR desconocido.")
    if kind in {"highpass", "bandstop"} and taps % 2 == 0:
        raise ValueError("Pasa altos y rechaza banda requieren longitud impar.")
    if not np.isfinite(f1) or not 0 < f1 < 0.5:
        raise ValueError("f1 debe estar entre 0 y 0,5 ciclos/muestra.")
    if kind in {"bandpass", "bandstop"} and (f2 is None or not f1 < f2 < 0.5):
        raise ValueError("Para una banda: 0 < f1 < f2 < 0,5.")
    if window not in {"boxcar", "hann", "hamming", "blackman", "kaiser", "bartlett"}:
        raise ValueError("Ventana desconocida.")
    if not np.isfinite(beta) or beta < 0:
        raise ValueError("Beta debe ser finito y no negativo.")
    ensure_working_set(taps, live_arrays=7)
    m = np.arange(taps) - (taps-1)/2
    low = 2*f1*np.sinc(2*f1*m)
    delta = (m == 0).astype(float)
    if kind == "lowpass":
        h = low
    elif kind == "highpass":
        h = delta-low
    else:
        band = 2*f2*np.sinc(2*f2*m)-low
        h = band if kind == "bandpass" else delta-band
    w = sp.get_window(("kaiser", beta) if window == "kaiser" else window,
                      taps, fftbins=False)
    return Transfer(h*w, [1], name=f"FIR {kind}",roc={"mode":"right"})


def biquad(kind, f0, q):
    """SSBiquad: pasabanda de ganancia de pico Q (falda constante)."""
    if not np.isfinite(f0) or not 0 < f0 < 0.5 or not np.isfinite(q) or q <= 0:
        raise ValueError("Se requiere 0 < f0 < 0,5 ciclos/muestra y Q > 0.")
    c, s = np.cos(2*np.pi*f0), np.sin(2*np.pi*f0)
    alpha = s/(2*q)
    numerators = {"lowpass": [(1-c)/2, 1-c, (1-c)/2],
                  "highpass": [(1+c)/2, -(1+c), (1+c)/2],
                  "bandpass": [s/2, 0, -s/2], "bandstop": [1, -2*c, 1]}
    if kind not in numerators:
        raise ValueError("Tipo biquad desconocido.")
    return Transfer(numerators[kind], [1+alpha, -2*c, 1-alpha], name=f"Biquad {kind}")


def rc(kind, resistance, capacitance, stages=1):
    stages = positive_integer(stages, "Etapas")
    if not np.isfinite(resistance) or not np.isfinite(capacitance) or resistance <= 0 or capacitance <= 0:
        raise ValueError("R y C deben ser positivos y finitos.")
    if kind not in {"lowpass", "highpass"}:
        raise ValueError("RC admite pasa bajos o pasa altos.")
    ensure_working_set(stages+1, live_arrays=5)
    tau = resistance*capacitance
    b, a = np.array([1.]), np.array([1.])
    for _ in range(stages):
        a = np.convolve(a, [tau, 1])
        if kind == "highpass":
            b = np.convolve(b, [tau, 0])
    return Transfer(b, a, "analog", f"RC {kind}")


def bilinear(system: Transfer, period):
    if system.domain != "analog" or not np.isfinite(period) or period <= 0:
        raise ValueError("La bilineal requiere H(s) analógica y T > 0.")
    if np.any(system.b.imag) or np.any(system.a.imag):
        raise ValueError("La bilineal numérica requiere coeficientes reales.")
    from .bilinear_mapping import convert
    return convert(system,period)[0]


def rc_design(kind, cutoff_hz, known, value):
    """Calcula el componente faltante con fc=1/(2πRC), como UIAnalogRCDesign."""
    if not np.isfinite(cutoff_hz) or cutoff_hz <= 0 or not np.isfinite(value) or value <= 0:
        raise ValueError("La frecuencia y el componente conocido deben ser positivos y finitos.")
    if known == "resistance":
        resistance, capacitance = value, 1/(2*np.pi*cutoff_hz*value)
    elif known == "capacitance":
        resistance, capacitance = 1/(2*np.pi*cutoff_hz*value), value
    else:
        raise ValueError("Componente conocido: resistance o capacitance.")
    return rc(kind, resistance, capacitance), resistance, capacitance


def from_poles_zeros(zeros, poles, gain=1, domain="digital"):
    zeros, poles = np.asarray(zeros, dtype=complex), np.asarray(poles, dtype=complex)
    if not np.all(np.isfinite(zeros)) or not np.all(np.isfinite(poles)) or not np.isfinite(gain):
        raise ValueError("Polos, ceros y ganancia deben ser finitos.")
    b, a = gain*np.atleast_1d(np.poly(zeros)), np.atleast_1d(np.poly(poles))
    if domain == "digital":
        b = np.pad(b, (max(0,len(a)-len(b)), 0))
    return Transfer(b, a, domain, "Diseño polos/ceros",advance=max(0,int(zeros.size-poles.size)) if domain=='digital' else 0)
