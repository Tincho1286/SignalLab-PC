"""Pointwise products and windowing of an arbitrary finite impulse response."""
from dataclasses import dataclass
import math
import numpy as np
from scipy.signal import get_window
from .model import Signal
from .filters import Transfer
from .resources import ensure_working_set
from .operations import _finite_output,shift

def validate_discrete_clocks(x,w):
    rates=[]
    for source in (x,w):
        rate=source.metadata.get('sample_rate_hz')
        if rate is not None:
            rate=float(rate)
            if not math.isfinite(rate) or rate<=0:raise ValueError('La tasa de muestreo registrada debe ser positiva y finita.')
        start=source.metadata.get('time_start_s')
        if start is not None and not math.isfinite(float(start)):raise ValueError('El inicio del reloj debe ser finito.')
        rates.append(rate)
    if all(rate is not None for rate in rates):
        if not np.isclose(rates[0],rates[1],rtol=1e-12,atol=0):raise ValueError('Las entradas tienen distintas tasas de muestreo. Cambiá la tasa antes de combinarlas.')
        a=x.metadata.get('time_start_s');b=w.metadata.get('time_start_s')
        if a is not None and b is not None:
            expected=float(a)+(int(w.origin)-int(x.origin))/rates[0]
            if not math.isfinite(expected):raise ValueError('La alineación del reloj excede el rango numérico.')
            tolerance=max(1e-9/rates[0],8*math.ulp(expected))
            if not math.isfinite(float(b)) or abs(float(b)-expected)>tolerance:raise ValueError('Los tiempos físicos registrados no corresponden a los mismos índices. Revisá los orígenes de las entradas.')

def multiply_signals(x,w):
    if x.domain!=w.domain or x.domain not in ('discrete','continuous'):raise ValueError('Las dos entradas deben ser discretas o las dos continuas.')
    ensure_working_set(len(x.values)+len(w.values),live_arrays=8)
    if x.domain=='discrete':
        validate_discrete_clocks(x,w)
        start=max(int(x.origin),int(w.origin));stop=min(int(x.origin)+len(x.values),int(w.origin)+len(w.values))
        values=np.zeros(len(x.values),dtype=complex)
        if stop>start:
            a=start-int(x.origin);b=start-int(w.origin);size=stop-start
            values[a:a+size]=x.values[a:a+size]*w.values[b:b+size]
        scope='Producto punto a punto, alineado por n. Se conserva el intervalo de la primera señal; la segunda vale cero fuera de su registro. No se conjugan valores ni se realiza convolución.'
    else:
        from .distributions import regular_only
        regular_only(x,'El producto de muestras');regular_only(w,'El producto de muestras')
        if x.step<=0 or w.step<=0:raise ValueError('Los registros continuos deben tener un paso positivo.')
        if x.units!=w.units:raise ValueError('Los ejes temporales deben usar las mismas unidades.')
        axis=x.axis;other=w.axis
        sampled=np.interp(axis,other,w.values.real,left=0,right=0)+1j*np.interp(axis,other,w.values.imag,left=0,right=0)
        values=x.values*sampled
        scope='Producto evaluado en los instantes de la primera señal. La segunda se interpola linealmente y vale cero fuera de su intervalo. El registro resultante aproxima el producto continuo entre sus muestras.'
    metadata={k:x.metadata[k] for k in ('sample_rate_hz','time_start_s') if k in x.metadata}
    metadata.update(operation='signal_product',input_names=[x.name,w.name],input_x_expression=x.expression,input_w_expression=w.expression,scope=scope,second_origin=w.origin,second_step=w.step)
    return Signal(_finite_output(values,'El producto'),x.origin,x.step,x.units,'Producto punto a punto',x.domain,'',metadata)

@dataclass
class WindowedFir:
    original:Signal
    window:Signal
    windowed:Signal
    impulse:Signal
    system:Transfer
    delay:int
    window_name:str

def window_impulse(h,window='hamming',beta=8.6,retard=True,custom=None,*,length=None,start=None):
    if h.domain!='discrete':raise ValueError('La respuesta h[n] debe ser una secuencia discreta.')
    if custom is not None and custom.domain!='discrete':raise ValueError('La ventana propia debe ser una secuencia discreta.')
    size=len(custom.values) if custom is not None else len(h.values) if length is None else length
    origin=custom.origin if custom is not None else h.origin if start is None else start
    if int(size)!=size or size<1:raise ValueError('La longitud L de la ventana debe ser un entero positivo.')
    if int(origin)!=origin:raise ValueError('El primer índice de la ventana debe ser entero.')
    size=int(size);origin=int(origin);ensure_working_set(size,live_arrays=10)
    if custom is None:
        if window not in ('boxcar','hann','hamming','blackman','kaiser','bartlett'):raise ValueError('Elegí una ventana disponible.')
        beta=float(beta)
        if window=='kaiser' and (not math.isfinite(beta) or beta<0):raise ValueError('β de Kaiser debe ser finito y no negativo.')
        values=get_window(('kaiser',beta) if window=='kaiser' else window,size,fftbins=False)
        window_name=window+(' (β='+str(beta)+')' if window=='kaiser' else '')
        metadata={'operation':'fir_window','window':window,'symmetric':True,'length':size,'start':origin,'scope':'Ventana simétrica de longitud L elegida independientemente del registro de h[n].'}
        if window=='kaiser':metadata['beta']=beta
        rate=h.metadata.get('sample_rate_hz')
        if rate is not None:
            rate=float(rate)
            if not math.isfinite(rate) or rate<=0:raise ValueError('El reloj registrado de h[n] debe tener una tasa positiva y finita.')
            metadata['sample_rate_hz']=rate
            if 'time_start_s' in h.metadata:metadata['time_start_s']=float(h.metadata['time_start_s'])+(origin-h.origin)/rate
        taper=Signal(values,origin,1,'n','Ventana '+window_name,'discrete','',metadata)
    else:taper=custom;window_name='propia: '+custom.name
    raw=multiply_signals(taper,h).copy_with(name='h[n] enventanada')
    if 'sample_rate_hz' not in raw.metadata and 'sample_rate_hz' in h.metadata:
        rate=float(h.metadata['sample_rate_hz']);raw.metadata['sample_rate_hz']=rate
        if 'time_start_s' in h.metadata:raw.metadata['time_start_s']=float(h.metadata['time_start_s'])+(origin-h.origin)/rate
    raw.metadata.update(input_names=[h.name,taper.name],input_x_expression=h.expression,input_w_expression=taper.expression,window_start=origin,window_length=size)
    delay=max(0,-int(raw.origin)) if retard else 0
    impulse=shift(raw,delay) if delay else raw
    if delay:impulse.name='h[n] del FIR causal'
    impulse.metadata.update(operation='windowed_impulse',window=window_name,added_delay=delay,original_origin=int(h.origin),window_start=origin,window_length=size,scope='h_w[n]=h[n]·w[n] sobre el intervalo de la ventana elegida. Fuera del registro de h se usa cero. El retardo agregado es '+str(delay)+' muestras; no se normaliza automáticamente la ganancia.')
    if custom is None and window=='kaiser':impulse.metadata['window_beta']=beta
    origin=int(impulse.origin)
    if origin>0:
        ensure_working_set(origin+size,live_arrays=5);b=np.pad(impulse.values,(origin,0));advance=0
    else:b=impulse.values;advance=-origin
    rate=impulse.metadata.get('sample_rate_hz');period=1/float(rate) if rate is not None else None
    system=Transfer(b,[1],'digital','FIR desde h[n] · '+window_name,advance=advance,sample_period_s=period)
    return WindowedFir(h,taper,raw,impulse,system,delay,window_name)
