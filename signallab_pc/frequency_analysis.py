"""Frequency data and local crossover estimates of a rational loop transfer."""
from dataclasses import dataclass
import math
import numpy as np
from scipy.optimize import brentq,minimize_scalar
from .jobs import checkpoint
from .resources import ensure_working_set


def frequency_grid(start,stop,count,logarithmic=False):
    if not np.isfinite([start,stop]).all() or stop<=start or int(count)!=count or count<2:
        raise ValueError('Indicá un intervalo finito creciente y al menos dos puntos.')
    if logarithmic and start<=0:
        raise ValueError('En escala logarítmica, Desde debe ser mayor que cero. Para incluir cero o frecuencias negativas usá escala lineal.')
    ensure_working_set(int(count),live_arrays=16)
    result=np.geomspace(start,stop,int(count)) if logarithmic else np.linspace(start,stop,int(count))
    if not np.isfinite(result).all() or np.any(np.diff(result)<=0):
        raise ValueError('La precisión numérica no permite distinguir todas las frecuencias de ese intervalo. Cambiá el rango o reducí los puntos.')
    return result


@dataclass
class FrequencyData:
    system:object
    omega:np.ndarray
    response:np.ndarray
    magnitude:np.ndarray
    db:np.ndarray
    phase:np.ndarray
    delay:np.ndarray
    logarithmic:bool
    advance:int=0
    margins:dict|None=None

    @property
    def units(self):return 'rad/muestra' if self.system.domain=='digital' else 'rad/s'


def analyze_frequency(system,omega,*,advance=0,logarithmic=False,margins=False):
    response=system.response(omega)*np.exp(1j*omega*advance)
    with np.errstate(all='ignore'):magnitude=np.abs(response);db=20*np.log10(magnitude)
    phase=np.full(response.shape,np.nan);valid=np.isfinite(response)&np.isfinite(magnitude)&(magnitude>0)
    indices=np.flatnonzero(valid)
    for segment in np.split(indices,np.flatnonzero(np.diff(indices)>1)+1):
        if segment.size:phase[segment]=np.unwrap(np.angle(response[segment]))
    delay=system.group_delay(omega)-advance
    result=FrequencyData(system,omega,response,magnitude,db,phase,delay,logarithmic,int(advance+system.advance))
    if margins:result.margins=crossover_margins(system,omega,response,advance=advance)
    return result


def _crossings(omega,values,function,*,eligible=None,tolerance=1e-8):
    """Bracket sign changes, refine local touches, reject poles by residual."""
    finite=np.isfinite(values);near=finite&(np.abs(values)<=tolerance)
    eligible=np.ones(omega.size,dtype=bool) if eligible is None else eligible
    # A run numerically indistinguishable from zero does not define isolated roots.
    flat=np.zeros(omega.size,dtype=bool)
    adjacent=near[:-1]&near[1:]
    flat[:-1]|=adjacent;flat[1:]|=adjacent
    nonisolated=bool(np.any(flat&eligible));roots=[];rejected=0

    def add(value):
        nonlocal rejected
        residual=function(value)
        if not np.isfinite(residual) or abs(residual)>tolerance:
            rejected+=1;return
        if value>0 and not any(math.isclose(value,old,rel_tol=1e-8,abs_tol=0) for old in roots):roots.append(float(value))

    for index in np.flatnonzero(near&~flat):add(omega[index])
    pairs=np.flatnonzero(finite[:-1]&finite[1:]&~flat[:-1]&~flat[1:]&(np.signbit(values[:-1])!=np.signbit(values[1:])))
    for number,index in enumerate(pairs):
        if number%32==0:checkpoint()
        lo,hi=omega[index:index+2]
        # Normalize the solving coordinate, including very small/large frequency ranges.
        use_log=lo>0
        def coordinate(t):return math.exp((1-t)*math.log(lo)+t*math.log(hi)) if use_log else (1-t)*lo+t*hi
        try:
            root=brentq(lambda t:function(coordinate(t)),0.,1.,xtol=8*np.finfo(float).eps,rtol=8*np.finfo(float).eps,maxiter=100)
            add(coordinate(root))
        except (ValueError,RuntimeError,OverflowError):rejected+=1
    # A tangency can have no sign change. Refine sampled local minima of |f|.
    absolute=np.abs(values)
    extrema=np.flatnonzero(finite[1:-1]&finite[:-2]&finite[2:]&~flat[1:-1]&
        (absolute[1:-1]<absolute[:-2])&(absolute[1:-1]<absolute[2:]))+1
    for number,index in enumerate(extrema):
        if number%32==0:checkpoint()
        if values[index-1]*values[index+1]<=0:continue
        lo,hi=omega[index-1],omega[index+1]
        use_log=lo>0
        def coordinate(t):return math.exp((1-t)*math.log(lo)+t*math.log(hi)) if use_log else (1-t)*lo+t*hi
        try:
            minimum=minimize_scalar(lambda t:abs(function(coordinate(t))),bounds=(0.,1.),method='bounded',options={'xatol':1e-13})
            if minimum.success and minimum.fun<=tolerance:add(coordinate(minimum.x))
        except (ValueError,RuntimeError,OverflowError):rejected+=1
    return sorted(roots),nonisolated,rejected


def crossover_margins(system,omega,response,*,advance=0):
    """Finite-interval estimates; absence of crossings never implies infinity."""
    result={'available':False,'gain_crossings':[],'phase_crossings':[],
        'convention':'L se interpreta como transferencia de lazo abierto con realimentación negativa unitaria.',
        'scope':'Cruces aproximados dentro del intervalo evaluado; no se garantiza detectar todos los cruces entre puntos ni fuera de él. No certifica estabilidad del lazo cerrado.'}
    if np.any(system.b.imag) or np.any(system.a.imag):
        result['reason']='Los márgenes convencionales requieren coeficientes reales. La respuesta compleja sigue disponible.';return result
    if advance or system.advance:
        result['reason']='La fórmula contiene un avance temporal; no se interpreta como lazo causal para calcular márgenes.';return result
    selected=(omega>=0)&((omega<=np.pi) if system.domain=='digital' else True)
    w=omega[selected];h=response[selected]
    if w.size<2:
        result['reason']='Se requieren al menos dos frecuencias no negativas; en digital se usa sólo 0 ≤ ω ≤ π rad/muestra.';return result
    result.update(available=True,interval=[float(w[0]),float(w[-1])],grid_points=int(w.size),
        units='rad/muestra' if system.domain=='digital' else 'rad/s')
    with np.errstate(all='ignore'):
        magnitude=np.abs(h)
        gain=np.where(magnitude<=1,magnitude-1,1-1/magnitude)
        phase=np.imag(h)/np.maximum(1,magnitude)
    finite=np.isfinite(h)&np.isfinite(magnitude)
    gain=np.where(finite,gain,np.nan);phase=np.where(finite&(magnitude>0),phase,np.nan)

    def evaluate(frequency):return complex(system.response(np.array([frequency]))[0])
    def gain_function(frequency):
        value=evaluate(frequency)
        with np.errstate(all='ignore'):magnitude=float(np.abs(value))
        if not np.isfinite(value) or not np.isfinite(magnitude):return np.nan
        return magnitude-1 if magnitude<=1 else 1-1/magnitude
    def phase_function(frequency):
        value=evaluate(frequency)
        with np.errstate(all='ignore'):magnitude=float(np.abs(value))
        if not np.isfinite(value) or not np.isfinite(magnitude) or magnitude==0:return np.nan
        return value.imag/max(1,magnitude)

    wg,flat_gain,bad_gain=_crossings(w,gain,gain_function,tolerance=1e-10)
    wp,flat_phase,bad_phase=_crossings(w,phase,phase_function,eligible=np.real(h)<0,tolerance=1e-9)
    for frequency in wg:
        value=evaluate(frequency)
        # Signed shortest angular distance to an odd multiple of pi, in [-pi,pi).
        pm=float(np.angle(value)%(2*np.pi)-np.pi)
        result['gain_crossings'].append({'frequency':frequency,'phase_margin_rad':pm})
    for frequency in wp:
        value=evaluate(frequency)
        if value.real>=0:continue
        with np.errstate(all='ignore'):gm=1/float(np.abs(value))
        if not np.isfinite(gm) or gm<=0:continue
        result['phase_crossings'].append({'frequency':frequency,'gain_margin':float(gm),'gain_margin_db':20*math.log10(gm)})
    result.update(nonisolated_gain=flat_gain,nonisolated_phase=flat_phase,rejected_intervals=bad_gain+bad_phase)
    return result


def frequency_summary(exact,data):
    from .result_summary import Summary,Section,Formula,number
    sections=[Section('Definición',paragraphs=[exact['scope']],formulas=[Formula('H = '+exact['transfer'],'H = '+exact['transfer'])])]
    if exact.get('factored')!=exact['transfer']:sections.append(Section('Forma factorizada',formulas=[Formula(exact['factored'],exact['factored'])]))
    if 'causal_impulse' in exact:sections.append(Section('Respuesta causal al impulso',formulas=[Formula('h(t) = '+exact['causal_impulse'],'h(t) = '+exact['causal_impulse'])]))
    if data is None:
        sections.append(Section('Vista numérica pendiente',paragraphs=['Asigná valores a '+', '.join(exact.get('parameters',[]))+'.']))
        return Summary('Análisis del sistema',sections)
    sections.append(Section('Respuesta en frecuencia',rows=[('Intervalo',number(data.omega[0])+' a '+number(data.omega[-1])+' '+data.units),
        ('Frecuencias evaluadas',str(data.omega.size)),('Distribución','Logarítmica' if data.logarithmic else 'Lineal'),
        ('Respuesta no finita',str(int(np.count_nonzero(~np.isfinite(data.response))))),
        ('Retardo de grupo','Muestras' if data.system.domain=='digital' else 'Segundos')],
        paragraphs=['En la figura podés alternar módulo lineal o dB sin recalcular. La fase y las frecuencias angulares se muestran en radianes. En ceros de H, fase y retardo no están definidos; el módulo en dB es −∞. Se evalúa la fórmula sobre el eje imaginario o el círculo unidad; su interpretación como transformada de Fourier exige que ese eje o círculo pertenezca a la ROC.'],
        formulas=[Formula('M = 20*log(abs(H))/log(10)','M = 20 log10 |H|')]))
    if data.advance:sections.append(Section('Avance temporal',paragraphs=[f'La representación conserva un factor z elevado a {data.advance}. Se incluye en la respuesta, fase, retardo, exportación y reutilización para análisis; no se sustituye por un retardo causal. Una ROC sigue siendo necesaria para determinar la secuencia bilateral.']))
    margins=data.margins
    if margins is not None:
        sections.append(Section('Márgenes de lazo abierto',paragraphs=[margins['convention'],margins['scope']]))
        if not margins['available']:sections.append(Section('Alcance',paragraphs=[margins['reason']]))
        else:
            sections.append(Section('Intervalo de búsqueda',rows=[('Frecuencia',number(margins['interval'][0])+' a '+number(margins['interval'][1])+' '+margins['units'])],paragraphs=['Se excluye el cruce estático en frecuencia cero. En digital no se repiten cruces fuera de 0…π.']))
            if margins['gain_crossings']:
                rows=[('ωg = '+number(row['frequency'])+' '+data.units,'MF = '+number(row['phase_margin_rad'])+' rad') for row in margins['gain_crossings'][:20]]
                sections.append(Section('Cruces de ganancia · |L| = 1',rows=rows,paragraphs=['MF es la distancia angular con signo al eje real negativo, en [−π, π). Un valor positivo representa el margen de fase convencional para el caso usual de fase decreciente.']))
            else:sections.append(Section('Cruces de ganancia',paragraphs=['No se detectaron cruces aislados |L| = 1 en el intervalo. No se asigna un margen de fase infinito.']))
            if margins['phase_crossings']:
                rows=[('ωp = '+number(row['frequency'])+' '+data.units,'MG = '+number(row['gain_margin'])+' · '+number(row['gain_margin_db'])+' dB') for row in margins['phase_crossings'][:20]]
                sections.append(Section('Cruces de fase · L real negativo',rows=rows,formulas=[Formula('MG = 1/abs(L)','MG = 1 / |L| en el cruce de fase')]))
            else:sections.append(Section('Cruces de fase',paragraphs=['No se detectaron cruces aislados de fase impar·π en el intervalo. No se declara un margen de ganancia infinito.']))
            if margins['nonisolated_gain'] or margins['nonisolated_phase']:
                sections.append(Section('Cruces no aislados',paragraphs=['Hay tramos indistinguibles del nivel crítico con esta precisión numérica. No se asigna una lista de cruces únicos a esos tramos.']))
            if margins['rejected_intervals']:sections.append(Section('Intervalos no resueltos',paragraphs=[str(margins['rejected_intervals'])+' candidatos no cumplieron la tolerancia o no pudieron resolverse; revisá singularidades y resolución.']))
            if max(len(margins['gain_crossings']),len(margins['phase_crossings']))>20:
                sections.append(Section('Lista parcial',paragraphs=['Se muestran hasta 20 cruces de cada tipo; la exportación JSON conserva todos los detectados.']))
    return Summary('Análisis del sistema',sections)


def export_frequency(data,path):
    from pathlib import Path
    from .atomic_file import atomic_text_file,write_json
    if Path(path).suffix.lower()=='.json':
        def numbers(values):return [float(value) if np.isfinite(value) else None for value in values]
        write_json(path,dict(format='signallab-frequency-analysis',version=1,frequency_units=data.units,
            domain=data.system.domain,distribution='logarithmic' if data.logarithmic else 'linear',
            frequency=numbers(data.omega),response_real=numbers(data.response.real),response_imag=numbers(data.response.imag),
            magnitude=numbers(data.magnitude),magnitude_db=numbers(data.db),phase_rad=numbers(data.phase),group_delay=numbers(data.delay),
            undefined='null marks non-finite values; magnitude zero implies magnitude_db = -infinity',advance=data.advance,margins=data.margins))
        return
    import csv
    unit='rad_muestra' if data.system.domain=='digital' else 'rad_s';delay='muestras' if data.system.domain=='digital' else 's'
    with atomic_text_file(path,encoding='utf-8-sig',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(['frecuencia_'+unit,'H_real','H_imag','modulo','modulo_dB','fase_rad','retardo_'+delay])
        for row in zip(data.omega,data.response.real,data.response.imag,data.magnitude,data.db,data.phase,data.delay):
            writer.writerow([format(float(value),'.17g') if np.isfinite(value) else '-inf' if np.isneginf(value) else '' for value in row])
