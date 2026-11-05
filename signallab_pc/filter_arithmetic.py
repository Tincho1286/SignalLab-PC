"""Finite precision DF-II transposed, using exact real arithmetic between casts.

Recurrence/order: scipy.signal.lfilter notes. Products are separate from sums;
no fused multiply-add is assumed. SOS keep their received order and scaling.
"""
from fractions import Fraction
import math
import numpy as np
from scipy import signal as scipy_signal
from .precision import Encoding,_rounded,ratio_text
from .filters import Transfer
from .model import Signal
from .resources import ensure_working_set
from .jobs import checkpoint


class Arithmetic:
    def __init__(self,encoding,guard_bits=0,overflow='saturate',operations=True,complex_values=False):
        if overflow not in ('saturate','wrap'):raise ValueError('Elegí saturación o complemento a dos cíclico.')
        if isinstance(guard_bits,bool) or int(guard_bits)!=guard_bits or guard_bits<0:raise ValueError('Los bits extra del acumulador deben ser enteros no negativos.')
        self.storage=encoding;self.accumulator=Encoding('fixed',encoding.integer_bits+int(guard_bits),encoding.fractional_bits,encoding.rounding) if encoding.kind=='fixed' else encoding
        self.overflow=overflow;self.operations=bool(operations);self.complex_values=complex_values
        self.stats={};self.index=None
    def cast_real(self,value,stage,accumulator=False):
        encoding=self.accumulator if accumulator else self.storage
        encoded=encoding.encode(value)
        if encoding.kind=='fixed' and self.overflow=='wrap' and stage not in ('coeficientes',):
            scale=1<<encoding.fractional_bits;scaled=value*scale;magnitude=abs(scaled)
            code=_rounded(magnitude,False) if encoding.rounding=='round' else magnitude.numerator//magnitude.denominator
            if scaled<0:code=-code
            limit=1<<(encoding.width-1);overflow=not -limit<=code<limit
            represented=Fraction((code+limit)%(2*limit)-limit,scale)
        else:
            represented=encoded['value'];overflow=encoded['saturated']
        if represented is None:raise ValueError(f'Desborde flotante en {stage}'+(f', índice {self.index}' if self.index is not None else '')+'. Aumentá el rango del formato o reducí la escala de entrada y estados.')
        row=self.stats.setdefault(stage,{'casts':0,'changed':0,'overflows':0})
        row['casts']+=1;row['changed']+=int(represented!=value);row['overflows']+=int(overflow)
        return represented
    def value(self,value):
        z=complex(value)
        if not math.isfinite(z.real) or not math.isfinite(z.imag):raise ValueError('La entrada, los estados y los coeficientes deben ser finitos.')
        return (Fraction.from_float(z.real),Fraction.from_float(z.imag)) if self.complex_values else Fraction.from_float(z.real)
    def cast(self,value,stage,accumulator=False):
        if self.complex_values:return tuple(self.cast_real(part,stage,accumulator) for part in value)
        return self.cast_real(value,stage,accumulator)
    def add_real(self,a,b):
        value=a+b
        return self.cast_real(value,'sumas',True) if self.operations else value
    def product_real(self,a,b):
        value=a*b
        return self.cast_real(value,'productos') if self.operations else value
    def add(self,a,b):
        return tuple(self.add_real(x,y) for x,y in zip(a,b)) if self.complex_values else self.add_real(a,b)
    def negative(self,value):return tuple(-part for part in value) if self.complex_values else -value
    def product(self,a,b):
        if not self.complex_values:return self.product_real(a,b)
        ar,ai=a;br,bi=b
        return self.add_real(self.product_real(ar,br),-self.product_real(ai,bi)),self.add_real(self.product_real(ar,bi),self.product_real(ai,br))
    def floating(self,value):
        parts=value if self.complex_values else (value,Fraction(0))
        try:converted=[float(part) for part in parts];result=complex(*converted)
        except OverflowError:raise ValueError('El valor exacto excede el rango de la salida numérica. Reducí los bits enteros o la escala.')
        if any(part and converted[index]==0 for index,part in enumerate(parts)):raise ValueError('Un valor exacto es menor que el rango de las tablas y figuras. Reducí los bits fraccionarios o aumentá la escala.')
        if not math.isfinite(result.real) or not math.isfinite(result.imag):raise ValueError('La salida excede el rango numérico de las tablas y figuras.')
        return result
    def exact_text(self,value):
        return {'real':ratio_text(value[0]),'imag':ratio_text(value[1])} if self.complex_values else {'real':ratio_text(value),'imag':'0'}


def simulate(system,source,encoding,*,preserve_sections=True,initial=(0,),tail=64,guard_bits=4,overflow='saturate',operations=True):
    if system.advance:raise ValueError('Esta simulación utiliza retardos causales y no admite un avance temporal. Consultá frecuencia o Z inversa con ROC para el sistema completo.')
    if system.domain!='digital' or source.domain!='discrete':raise ValueError('La ejecución de precisión finita requiere H(z) y una secuencia discreta.')
    if isinstance(tail,bool) or int(tail)!=tail or tail<0:raise ValueError('Los ceros agregados al final deben ser un entero no negativo.')
    from .system_conditions import require_causal_roc
    from .system_clock import input_metadata
    require_causal_roc(system)
    clock=input_metadata(system,source)
    tail=int(tail);count=source.values.size+tail
    limit=np.iinfo(np.int64)
    if source.origin+count-1>limit.max:raise ValueError('El intervalo excede los índices enteros de 64 bits.')
    sections=system.sos is not None and preserve_sections
    original_groups=[(row[:3],row[3:]) for row in system.sos] if sections else [(system.b,system.a)]
    orders=[max(len(b),len(a))-1 for b,a in original_groups];state_count=sum(orders)
    ensure_working_set(count,bytes_per_sample=16,live_arrays=18)
    ensure_working_set((state_count+sum(len(b)+len(a) for b,a in original_groups))*max(encoding.width,64),bytes_per_sample=4,live_arrays=12)
    initial=np.asarray(initial,dtype=complex).reshape(-1)
    if len(initial)==1:initial=np.repeat(initial,state_count)
    if len(initial)!=state_count:raise ValueError(f'Esta realización requiere {state_count} memorias: ingresá esa cantidad o un único valor para todas. En SOS se ordenan por sección, dos por sección.')
    complex_values=bool(np.any(source.values.imag) or np.any(initial.imag) or any(np.any(np.asarray(b).imag) or np.any(np.asarray(a).imag) for b,a in original_groups))
    machine=Arithmetic(encoding,guard_bits,overflow,operations,complex_values)
    zero=machine.value(0);one=machine.value(1);coefficient_rows=[];groups=[];stored_groups=[]
    def coefficient(value,label):
        original=machine.value(value);stored=machine.cast(original,'coeficientes')
        parts=zip(('real','imag'),original,stored) if complex_values else [('real',original,stored)]
        for component,before,after in parts:
            encoded=encoding.encode(before)
            coefficient_rows.append({'coefficient':label,'component':component,'original':float(before),'stored':float(after),'stored_exact':ratio_text(after),'error':float(after-before),'word':encoded['word'],'hex':encoded['hex'],'classification':encoded['classification'],'saturated':encoded['saturated']})
        return stored
    for index,((b,a),order) in enumerate(zip(original_groups,orders)):
        prefix=f'S{index+1} · ' if sections else ''
        bq=[coefficient(v,prefix+f'b[{k}]') for k,v in enumerate(b)]+[zero]*(order+1-len(b))
        aq=[one]+[coefficient(v,prefix+f'a[{k}]') for k,v in enumerate(a[1:],1)]+[zero]*(order+1-len(a))
        groups.append((bq,aq));stored_groups.append((np.array([machine.floating(v) for v in bq]),np.array([machine.floating(v) for v in aq])))
    if sections:
        stored_system=Transfer.from_sos(np.array([np.r_[b,a].real for b,a in stored_groups]),'Coeficientes de ejecución '+encoding.name,sample_period_s=system.sample_period_s)
    else:stored_system=Transfer(*stored_groups[0],'digital','Coeficientes de ejecución '+encoding.name,sample_period_s=system.sample_period_s)
    states=[machine.cast(machine.value(v),'memorias iniciales') for v in initial];initial_q=list(states)
    values=np.zeros(count,dtype=complex);input_values=np.pad(source.values,(0,tail));input_q=np.zeros(count,dtype=complex)
    cycle=None;anchor=None;power=1;length=0;zero_run=0;zero_start=None
    for offset,value in enumerate(input_values):
        if offset%32==0:checkpoint(offset/max(1,count))
        machine.index=source.origin+offset;x=machine.cast(machine.value(value),'entrada');input_q[offset]=machine.floating(x)
        if x==zero:
            if zero_run==0:anchor=tuple(states);power=1;length=0;cycle=None;zero_start=source.origin+offset
            zero_run+=1
        else:zero_run=0;cycle=None
        cursor=0
        for (b,a),order in zip(groups,orders):
            if order:
                y=machine.cast(machine.add(machine.product(b[0],x),states[cursor]),'salida')
                next_states=[]
                for k in range(order):
                    feedback=machine.negative(machine.product(a[k+1],y))
                    update=machine.add(machine.product(b[k+1],x),feedback)
                    if k+1<order:update=machine.add(update,states[cursor+k+1])
                    next_states.append(machine.cast(update,'memorias'))
                states[cursor:cursor+order]=next_states;cursor+=order
            else:y=machine.cast(machine.product(b[0],x),'salida')
            x=y
        values[offset]=machine.floating(x)
        if zero_run and state_count and cycle is None:
            length+=1;current=tuple(states)
            if current==anchor:
                cycle={'period':length,'detected_at':source.origin+offset,'nonzero_state':any(v!=zero for v in current),'zero_input_since':zero_start}
            elif length==power:anchor=current;power*=2;length=0
    # Two references separate input/coefficient/state storage from execution.
    # Both use the same DF-II transposed structure, state order and SOS order.
    def reference(groups,input_values,seed):
        data=input_values.copy();cursor=0
        with np.errstate(all='ignore'):
            for (b,a),order in zip(groups,orders):
                data,_=scipy_signal.lfilter(b,a,data,zi=np.asarray(seed[cursor:cursor+order],dtype=complex));cursor+=order
        data[~np.isfinite(data)]=complex(np.nan,np.nan)
        return data
    original_reference=reference(original_groups,input_values,initial)
    storage_reference=reference(stored_groups,input_q,[machine.floating(v) for v in initial_q])
    def error_metrics(reference):
        valid=np.isfinite(reference);scale=max(1.,float(np.max(abs(values.real),initial=0)),float(np.max(abs(values.imag),initial=0)),float(np.max(abs(reference[valid].real),initial=0)),float(np.max(abs(reference[valid].imag),initial=0)))
        error=values[valid]/scale-reference[valid]/scale
        def rms_of(values):
            peak=float(np.max(abs(values),initial=0))
            return peak*float(np.sqrt(np.mean(abs(values/peak)**2))) if peak else 0.
        rms=rms_of(error) if len(error) else None
        reference_rms=rms_of(reference[valid]/scale) if len(error) else None
        snr=20*(math.log10(reference_rms)-math.log10(rms)) if reference_rms and rms else None
        return {'scale':scale,'max_error_over_scale':float(np.max(abs(error))) if len(error) else None,'rms_error_over_scale':rms,'snr_db':snr,'zero_error':bool(len(error) and not np.any(error)),'finite_reference_samples':int(np.count_nonzero(valid))}
    total_metrics=error_metrics(original_reference);arithmetic_metrics=error_metrics(storage_reference)
    metadata={'operation':'finite_precision_filter','format':encoding.name,'structure':'SOS · DF-II transpuesta' if sections else 'DF-II transpuesta','initial_states': [machine.exact_text(v) for v in initial_q],'final_states':[machine.exact_text(v) for v in states],
        'rounding':encoding.rounding,'overflow':overflow,'quantize_operations':bool(operations),'accumulator_guard_bits':int(guard_bits) if encoding.kind=='fixed' else 0,'tail_zeros':tail,'cycle':cycle,'operation_counts':machine.stats,'total_error':total_metrics,'arithmetic_error':arithmetic_metrics,'source_system':system.to_document(),'coefficient_encoding':coefficient_rows,
        'scope':'Valores aritméticos redondeados por componente, sin FMA. El estudio flotante incluye subnormales y rechaza desbordes; no reproduce flags, modos de excepción ni el signo de cero de un procesador. Una repetición exacta del estado con entrada nula prueba periodicidad de esta realización; no encontrarla en el registro no prueba su ausencia.'}
    metadata.update({key:clock[key] for key in ('sample_rate_hz','time_start_s') if key in clock})
    result=Signal(values,source.origin,1,'n','Salida con precisión finita','discrete','',metadata)
    return {'simulation':True,'output':result,'source_signal':source,'source':system,'system':stored_system,'encoding':encoding,'sections':bool(sections),'rows':coefficient_rows,'input':input_q,'original_reference':original_reference,'storage_reference':storage_reference,'metrics':total_metrics,'arithmetic_metrics':arithmetic_metrics,'metadata':metadata}


def simulation_summary(data):
    from .result_summary import Summary,Section,Formula,number
    from .phase_summary import transfer_formula
    metadata=data['metadata'];formula,_=transfer_formula(data['system'],'Hq');counts=metadata['operation_counts'];cycle=metadata['cycle']
    cycle_text=('Se repitió un estado no nulo: ciclo de período '+str(cycle['period'])+' muestras.' if cycle['nonzero_state'] else 'El estado alcanzó el reposo (todas las memorias en cero).') if cycle else 'No se confirmó una repetición de estado en el tramo final de entrada nula.'
    if not metadata['final_states']:cycle_text='La realización no tiene memorias; no hay un estado interno que pueda sostener un ciclo.'
    def metrics(value):
        return [('Escala S',number(value['scale'])),('Máximo |error|/S',number(value['max_error_over_scale']) if value['max_error_over_scale'] is not None else 'Sin referencia finita'),('RMS del error / S',number(value['rms_error_over_scale']) if value['rms_error_over_scale'] is not None else 'Sin referencia finita'),('SNR del registro (dB)',number(value['snr_db']) if value['snr_db'] is not None else 'Sin error medido' if value['zero_error'] else 'No definida'),('Muestras de referencia finitas',value['finite_reference_samples'])]
    stages=[f'{name}: {row["casts"]} conversiones, {row["changed"]} cambios, {row["overflows"]} desbordes tratados.' for name,row in counts.items()]
    sections=[Section('Realización calculada',formulas=[formula],rows=[('Formato',metadata['format']),('Estructura',metadata['structure']),('Redondeo interno','Productos, sumas, salida y memorias' if metadata['quantize_operations'] else 'Salida y memorias'),('Bits extra de acumulador',metadata['accumulator_guard_bits']),('Desborde en ejecución','Saturación' if metadata['overflow']=='saturate' else 'Complemento a dos cíclico')],paragraphs=['Los coeficientes se convierten primero al formato elegido, con a[0]=1 implícito y saturación de coeficientes Q. La transferencia Hq describe ese almacenamiento; el filtrado con redondeos internos es una operación adicional que puede dejar de ser lineal.']),
        Section('Comparación total',rows=metrics(data['metrics']),paragraphs=['Se compara la salida con el filtro original, la entrada original y la memoria inicial solicitada, evaluados en doble precisión. S es la mayor componente real o imaginaria absoluta de salida y referencia, con mínimo uno. Las métricas usan sólo las muestras con referencia finita.']),
        Section('Error de ejecución',rows=metrics(data['arithmetic_metrics']),paragraphs=['Esta referencia usa los mismos coeficientes, entrada y memoria inicial ya cuantizados, pero calcula en doble precisión. Así se separa el efecto de los redondeos durante el filtrado del cambio inicial de almacenamiento. La SNR es una medida del registro; no supone ruido blanco independiente.']),
        Section('Conversiones y desbordes',paragraphs=stages),
        Section('Entrada nula y ciclos',rows=[('Cantidad de memorias',len(metadata['final_states'])),('Período confirmado',cycle['period'] if cycle else 'No confirmado'),('Índice de detección',cycle['detected_at'] if cycle else 'No corresponde')],paragraphs=[cycle_text,'Se añaden '+str(metadata['tail_zeros'])+' ceros al registro. La memoria se ordena desde d[0] y, en SOS, por sección. El detector compara estados exactos: un ciclo puede existir aunque no haya saturación. La duración del registro limita lo que se observa.']),
        Section('Qué se puede reutilizar',paragraphs=['Salida y permite exportar o enviar la secuencia a otra herramienta. Las acciones de filtro toman Hq y no trasladan los redondeos internos; para repetir esa ejecución hay que conservar sus formatos y memorias. El CSV de comparación incluye ambas referencias. El JSON de la salida conserva parámetros, contadores y estados exactos.',metadata['scope']])]
    return Summary('Filtrado con precisión finita',sections)
