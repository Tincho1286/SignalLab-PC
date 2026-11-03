"""Readable scientific summaries, separate from stored values and provenance."""
from dataclasses import dataclass,field,is_dataclass,asdict
from .model import Signal

@dataclass
class Formula:
    expression:str
    text:str
    lines:list=field(default_factory=list)
    numeric:bool=False
@dataclass
class Section:
    title:str
    paragraphs:list=field(default_factory=list)
    rows:list=field(default_factory=list)
    formulas:list=field(default_factory=list)
@dataclass
class Summary:
    title:str
    sections:list
    def plain_text(self):
        blocks=[self.title]
        for section in self.sections:
            if section.title:blocks.append(section.title)
            blocks.extend(str(value) for value in section.paragraphs)
            blocks.extend(str(key)+': '+str(value) for key,value in section.rows)
            blocks.extend(formula.text for formula in section.formulas)
        return '\n\n'.join(blocks)

def number(value):
    if isinstance(value,int):return str(value)
    z=complex(value)
    if not z.imag:return format(z.real,'.12g')
    if not z.real:return format(z.imag,'.12g')+'i'
    return format(z.real,'.12g')+(' + ' if z.imag>=0 else ' − ')+format(abs(z.imag),'.12g')+'i'

OPERATIONS={
 'window_generation':'Generar ventana',
 'generate':'Crear una señal','measures':'Energía, potencia y RMS','shift':'Desplazar una secuencia','time_shift':'Desplazar una secuencia','reverse':'Invertir una secuencia','time_reversal':'Invertir una secuencia','scale':'Escalar amplitud','sum':'Suma de señales','parity':'Partes par e impar','even_odd_decomposition':'Partes par e impar','convolve':'Convolución lineal','linear_convolution':'Convolución lineal','circular':'Convolución circular','circular_convolution':'Convolución circular','correlate':'Correlación lineal','linear_cross_correlation':'Correlación lineal','correlation':'Correlación','continuous_convolve':'Convolución continua','continuous_convolution':'Convolución continua','continuous_correlation':'Correlación continua','continuous_time_transform':'Transformación temporal continua','dft':'DFT','DFT':'DFT','idft':'DFT inversa','IDFT':'DFT inversa',
 'dtft_expression':'DTFT algebraica','fourier_angular':'Fourier continua algebraica','inverse_fourier_angular':'Fourier inversa algebraica','inverse_dtft_expression':'DTFT inversa algebraica',
 'laplace':'Laplace directa','inverse_laplace':'Laplace inversa','z_expression':'Transformada Z','z_finite':'Transformada Z finita','z_inverse_expression':'Z inversa con región de convergencia','system_analysis':'Análisis de sistema','system_formula':'Definición de sistema','ode':'Ecuación diferencial'}
def operation_label(value):return OPERATIONS.get(str(value),str(value))

def measurement_summary(value,source=None):
    data=asdict(value) if is_dataclass(value) else value
    if not isinstance(data,dict) or not {'energy','average_power','rms','sample_count'}<=data.keys():return None
    count=int(data['sample_count']);continuous=data.get('domain')=='continuous';rows=[('Puntos del registro N' if continuous else 'Muestras N',str(count))]
    if continuous:
        start,stop=data['interval'];unit=data.get('axis_units','s');duration=data.get('duration') if data.get('duration') is not None else stop-start;rows.extend([('Intervalo temporal',number(start)+' a '+number(stop)+' '+unit),('Duración T',number(duration)+' '+unit)])
        formulas=[Formula('E = Integral(abs(x(t))^2,(t,a,a+T))','E = ∫ desde a hasta a+T de |x(t)|² dt'),Formula('P = E/T','P = E / T'),Formula('R = sqrt(P)','R = √P')]
        interpretation='Se interpola x(t) linealmente entre puntos y se integra |x(t)|² de ese modelo. En cada intervalo se usa Δt·(|x₀|² + Re(x₀·conj(x₁)) + |x₁|²)/3; no se aplica un trapecio a |x|². Es exacto para el modelo por tramos y una aproximación de la función original si ésta no era lineal entre muestras.'
    else:
        if source is not None:rows.append(('Índices del registro',str(source.origin)+' a '+str(source.origin+count-1)))
        formulas=[Formula('E = Sum(abs(x[n])^2,(n,a,a+N-1))','E = Σ desde n=a hasta a+N−1 de |x[n]|²'),Formula('P = E/N','P = E / N'),Formula('R = sqrt(P)','R = √P')]
        interpretation='a es el primer índice y N la cantidad de muestras. Se usa el módulo al cuadrado, también para valores complejos.'
    return Summary('Energía, potencia y RMS del registro',[
        Section('Resultados',rows=[('Energía E',number(data['energy'])),('Potencia media del registro P',number(data['average_power'])),('RMS R',number(data['rms']))]),
        Section('Definición',rows=rows,formulas=formulas),
        Section('Cómo interpretarlo',paragraphs=[interpretation,'P es el promedio del registro observado. No determina por sí solo la potencia límite de una señal infinita. Si el registro contiene un período completo y se repite, ese promedio corresponde a la señal periódica. Si se supone cero fuera del registro, la señal tiene energía finita y potencia límite cero.','Los resultados se presentan con hasta 12 cifras significativas; el cálculo conserva doble precisión. No se asignan joules o watts sin conocer las unidades físicas de amplitud y el modelo correspondiente.'])])

def signal_summary(value,operation=None):
    signals=value if isinstance(value,tuple) else (value,)
    if not signals or not all(isinstance(signal,Signal) for signal in signals):return None
    sections=[]
    for signal in signals:
        meta=signal.metadata;count=signal.values.size;last=int(signal.origin)+int(count)-1 if signal.domain=='discrete' else signal.origin+signal.step*(count-1)
        if signal.domain=='discrete':
            coefficient=signal.units in ('k','bin k') or meta.get('operation') in ('DFT','discrete_fourier_series','continuous_fourier_series')
            domain='Coeficientes de índice entero k' if coefficient else 'Secuencia discreta x[n]'
            axis='Índices k' if coefficient else 'Índices n'
            unit=''
        else:
            domain='Registro de una señal continua' if signal.domain=='continuous' else 'Respuesta o espectro en frecuencia'
            axis='Intervalo temporal' if signal.domain=='continuous' else 'Intervalo de frecuencia'
            unit=' '+signal.units
        rows=[('Dominio',domain),('Valores almacenados',str(count)),(axis,number(signal.origin)+' a '+number(last)+unit)]
        if signal.domain!='discrete':rows.append(('Separación entre puntos',number(signal.step)+unit))
        if 'N' in meta:rows.append(('Longitud N',str(meta['N'])))
        elif 'nfft' in meta:rows.append(('Puntos de DFT N',str(meta['nfft'])))
        if 'sample_rate_hz' in meta:rows.append(('Tasa de muestreo Fs',number(meta['sample_rate_hz'])+' muestras/s'))
        if 'time_start_s' in meta:rows.append(('Tiempo de la primera muestra',number(meta['time_start_s'])+' s'))
        sections.append(Section(signal.name,rows=rows))
        if signal.expression and signal.expression!='lista ingresada':sections.append(Section('Expresión de origen',paragraphs=['Las transformaciones posteriores se reflejan en los valores almacenados.'],formulas=[Formula(signal.expression,signal.expression)]))
        op=meta.get('operation','');reading=[];formulas=[]
        if op=='DFT' and signal.domain=='discrete':
            formulas=[Formula('X[k] = Sum(v[m]*exp(-2*pi*i*k*m/N),(m,0,N-1))','X[k] = Σ desde m=0 hasta N−1 de v[m]·exp(−j2πkm/N)')]
            reading=['v[m] son los valores en el orden almacenado. La DFT no divide por N y usa índices k desde cero; no incorpora el origen temporal original. La transformada inversa divide por N.']
        elif op=='DFT' and signal.domain=='frequency':reading=['La DFT se representa mediante muestras en frecuencia angular. No son puntos conectados de una función continua. El informe de FFT y ventanas conserva la normalización y la referencia de fase del cálculo.']
        elif op=='IDFT':
            formulas=[Formula('x[n] = Sum(X[k]*exp(2*pi*i*k*n/N),(k,0,N-1))/N','x[n] = (1/N)·Σ desde k=0 hasta N−1 de X[k]·exp(j2πkn/N)')]
            reading=['Los coeficientes se interpretan en orden desde k=0. El eje reconstruido comienza en n=0; no recupera automáticamente un origen temporal anterior.']
        elif op=='linear_convolution':
            formulas=[Formula('y[n] = Sum(x[m]*h[n-m],(m,-oo,oo))','y[n] = Σ sobre m de x[m]·h[n−m]')]
            reading=['Las entradas se consideran cero fuera de sus registros. La salida completa tiene Nx+Nh−1 muestras y su primer índice es la suma de los primeros índices de ambas entradas.']
        elif op=='circular_convolution':reading=['Se usan los valores en orden desde cero y se completan con ceros hasta la mayor longitud de entrada. El resultado representa un período de la convolución circular; los orígenes originales no se suman como en la convolución lineal.']
        elif op in ('linear_cross_correlation','correlation'):
            reading=['El eje es el retardo entero. Se conserva la conjugación de la segunda señal. El signo del retardo depende del orden de las entradas; intercambiarlas cambia esa interpretación.']
        elif op=='continuous_convolution':reading=['El resultado es una aproximación numérica. La parte regular de las entradas se interpola linealmente entre puntos y se considera nula fuera del intervalo almacenado. Los impulsos ideales se conservan por su posición y peso.']
        elif op=='continuous_correlation':reading=['El eje es el retardo temporal en segundos. La segunda señal se invierte y se conjuga antes de la convolución. La aproximación y su normalización dependen del modelo de los registros.']
        elif op=='sampling':reading=['El reloj es t = t₀ + (n−n₀)/Fs. La duración entre la primera y la última muestra es (N−1)/Fs. Muestrear no recupera información que se pierda por aliasing.']
        elif op=='reconstruction':reading=['Se reconstruye entre la primera y la última muestra, usando Fs y el tiempo inicial visibles al calcular. ZOH mantiene el valor; lineal une puntos; SINC utiliza el registro finito completo y supone cero fuera. No se recupera información perdida por aliasing ni se muestran colas SINC infinitas.']
        elif op=='resample_rational':
            rows=[('Multiplicador L',str(meta['up'])),('Divisor M',str(meta['down'])),('Fs de entrada',number(meta['input_rate_hz'])+' muestras/s'),('Coeficientes del filtro',str(meta['filter_taps']))]
            sections.append(Section('Conversión de tasa',rows=rows))
            reading=['Fs de salida = Fs de entrada × L/M. La salida conserva el instante de la primera muestra. Se aplica un FIR de transición finita y se compensa su retardo para procesamiento fuera de tiempo real; los extremos dependen de la extensión elegida.']
        elif op=='even_odd_decomposition':
            formulas=[Formula('p[n] = (x[n]+x[-n])/2','Parte par: p[n] = (x[n]+x[−n])/2'),Formula('q[n] = (x[n]-x[-n])/2','Parte impar: q[n] = (x[n]−x[−n])/2')]
            reading=['La señal se extiende con ceros fuera del registro; se conserva el soporte reflejado. La suma de ambas componentes recupera la señal sobre ese soporte.']
        if reading or formulas:sections.append(Section('Cómo leer el resultado',paragraphs=reading,formulas=formulas))
        from .distributions import dirac_terms
        terms=dirac_terms(signal)
        if terms:
            rows=[('Posición '+('ω' if signal.domain=='frequency' else 't')+' = '+number(t)+' '+signal.units,'Peso '+number(w)) for t,w in terms[:12]]
            sections.append(Section('Impulsos ideales',rows=rows,paragraphs=['La señal incluye '+str(len(terms))+' términos Dirac. Los valores de la tabla son la parte ordinaria. Los impulsos se conservan por posición y peso; no son muestras de altura finita. El panel Peso Dirac representa sus pesos. Las posiciones y pesos completos permanecen en los datos y en la exportación.']))
        if meta.get('excluded_dirac_positions'):sections.append(Section('Intervalo observado',paragraphs=[str(len(meta['excluded_dirac_positions']))+' posiciones Dirac quedaron fuera del intervalo elegido y no forman parte de este registro. Ampliá el intervalo para incluirlas.']))
    sections.append(Section('Lectura y exportación',paragraphs=['Los valores completos están en Valores y en la exportación de la señal. Los índices enteros se muestran completos; las demás coordenadas se presentan con hasta 12 cifras significativas y sus unidades.']))
    return Summary(operation_label(operation) if operation else 'Resumen del resultado',sections)

def calculation_summary(value):
    if isinstance(value,dict) and value.get('operation')=='result_comparison':
        from .result_comparison import summary
        return summary(value)
    if isinstance(value,dict) and value.get('request',{}).get('operation')=='ode':
        from .equation_checks import ode_summary
        return ode_summary(value['request'],value['result'])
    if isinstance(value,dict) and {'frequency_hz','sample_rate_hz','signed_alias_hz'}<=value.keys():return alias_summary(value)
    measured=measurement_summary(value)
    if measured is not None:return measured
    if not isinstance(value,dict) or not isinstance(value.get('result'),dict):return None
    result=value['result'];request=value.get('request',{});sections=[]
    if request.get('operation') in {'laplace','inverse_laplace','z_expression','z_inverse_expression','z_finite'}:return transform_summary(request,result)
    if request.get('operation')=='signal_measures_expression':return expression_measure_summary(request,result)
    name=operation_label(request.get('operation',result.get('operation','Resultado algebraico')))
    expression=result.get('transfer',result.get('result'))
    if isinstance(expression,str):sections.append(Section('Expresión obtenida',formulas=[Formula(expression,expression)]))
    for index,branch in enumerate(result.get('branches',[])):
        if isinstance(branch,dict):sections.append(Section('Rama '+str(index+1),rows=[('Condición',branch.get('condition','No indicada'))],formulas=[Formula(branch['expression'],branch['expression'])] if isinstance(branch.get('expression'),str) else []))
    labels={'convergence':'Convergencia','condition':'Condición','scope':'Alcance','roc':'Región de convergencia','roc_finite_plane':'ROC en el plano finito','causal_impulse':'Respuesta al impulso causal','Y(s)':'Salida Y(s)','parameters':'Parámetros por asignar','factored':'Forma factorizada'}
    rows=[]
    for key,label in labels.items():
        if key in result:rows.append((label,', '.join(map(str,result[key])) if isinstance(result[key],list) else str(result[key])))
    if rows:sections.append(Section('Condiciones e interpretación',rows=rows))
    if request.get('input_conditions'):sections.append(Section('Condiciones de la expresión de entrada',paragraphs=request['input_conditions']))
    if result.get('evaluated') is False:sections.insert(0,Section('Estado del cálculo',paragraphs=['El motor conserva términos sin resolver. El resultado no se presenta como una solución completamente evaluada.']))
    return Summary(name,sections) if sections else None

def transfer_summary(value):
    from .filters import Transfer
    if not isinstance(value,Transfer):return None
    digital=value.domain=='digital';variable='z' if digital else 's'
    rows=[('Dominio','Discreto · H(z)' if digital else 'Continuo · H(s)'),('Numerador b',', '.join(number(v) for v in value.b)),('Denominador a',', '.join(number(v) for v in value.a))]
    if value.sample_period_s is not None:rows.append(('Período físico T (s)',number(value.sample_period_s)))
    if value.sos is not None:rows.append(('Realización','Cascada de '+str(len(value.sos))+' secciones de segundo orden'))
    if value.advance:rows.append(('Avance temporal conservado',str(value.advance)+' muestras; H(z)=z^('+str(value.advance)+') B(z^(-1))/A(z^(-1))'))
    if digital and value.roc is not None:
        mode=value.roc['mode'];rows.append(('ROC registrada',{'right':'Exterior a los polos no cancelados','left':'Interior a los polos no cancelados','radius':'Anillo que contiene r='+str(value.roc.get('radius',''))}[mode]))
    sections=[Section('Definición',rows=rows)]
    from .phase_summary import transfer_formula
    formula,compact=transfer_formula(value)
    sections.append(Section('Función de transferencia',formulas=[formula],paragraphs=['La suma finita usa los coeficientes b[k] y a[k] indicados, sin omitir términos.'] if compact else []))
    sections.append(Section('Cómo interpretarlo',paragraphs=['b y a están ordenados por potencias ascendentes de z⁻¹.' if digital else 'b y a están ordenados por potencias descendentes de s.','El informe presenta hasta 12 cifras significativas. La exportación conserva los coeficientes almacenados y las secciones, si existen. La transferencia sola no fija una región de convergencia ni demuestra la estabilidad interna de una realización con cancelaciones.']))
    from .system_conditions import section
    sections.insert(0,section(value))
    return Summary(value.name,sections)

def alias_summary(value):
    import math
    fs=value['sample_rate_hz'];original=value.get('frequency_rad_s',2*math.pi*value['frequency_hz']);alias=value.get('signed_alias_rad_s',2*math.pi*value['signed_alias_hz']);nyquist=math.pi*fs
    sections=[Section('Frecuencias',rows=[('Tono Ω',number(original)+' rad/s'),('Tasa de muestreo Fs',number(fs)+' muestras/s'),('Límite de Nyquist π·Fs',number(nyquist)+' rad/s'),('Alias firmado Ωa',number(alias)+' rad/s'),('Equivalente angular discreto ωa',number(alias/fs)+' rad/muestra')])]
    reading='El tono cumple |Ω| < π·Fs.' if value['strict_nyquist'] else 'El tono no cumple la condición estricta |Ω| < π·Fs.'
    if value.get('alias_at_nyquist',abs(alias)==nyquist):reading+=' En el borde de Nyquist, la fase puede hacer desaparecer las muestras de un seno.'
    sections.append(Section('Interpretación',paragraphs=[reading,'El representante firmado está en [−π·Fs, π·Fs). Para un seno o coseno real se puede usar |Ωa| con la fase correspondiente. Este cálculo analiza un tono; no demuestra que una señal arbitraria sea de banda limitada.'],formulas=[Formula('omega = Omega/Fs','ω = Ω / Fs, equivalente módulo 2π')]))
    return Summary('Nyquist y aliasing',sections)


def transform_summary(request,result):
    op=request['operation'];inverse=op in ('inverse_laplace','z_inverse_expression');z=op.startswith('z_')
    title={'laplace':'Laplace directa','inverse_laplace':'Laplace inversa causal','z_expression':'Transformada Z directa','z_inverse_expression':'Transformada Z inversa','z_finite':'Z de una secuencia finita'}[op]
    if not z and request.get('interpretation')=='bilateral':title='Laplace inversa bilateral' if inverse else 'Laplace directa bilateral'
    lhs='x[n]' if inverse and z else 'x(t)' if inverse else 'X(z)' if z else 'X(s)'
    sections=[]
    if request.get('expression'):
        sections.append(Section('Definición de entrada',formulas=[Formula(request['expression'],request['expression'])]))
    if op=='z_expression':sections.append(Section('Soporte de x[n]',rows=[('Primer índice',str(request.get('lower','0'))),('Último índice',str(request.get('upper','oo')))],paragraphs=['Fuera del soporte indicado se considera x[n]=0. Los límites son inclusivos.']))
    elif op=='z_finite':sections.append(Section('Registro de entrada',rows=[('Primer índice',str(request['origin'])),('Muestras',str(len(request['samples'])))],paragraphs=['Se considera cero fuera del registro. Los decimales representan los valores almacenados.']))
    branches=result.get('branches',[])
    if result.get('convergence_empty'):
        sections.append(Section('Sin región de convergencia',paragraphs=['Las condiciones de las colas temporales son incompatibles. '+('La suma bilateral' if z else 'La integral bilateral')+' no converge en una región abierta; la expresión de definición se conserva para identificar el cálculo.']))
    elif result.get('evaluated') is False:
        sections.append(Section('Cálculo pendiente',paragraphs=['El motor no obtuvo una expresión cerrada para este caso. La expresión siguiente conserva el cálculo sin resolver; no representa una solución evaluada.']))
    if result.get('boundary_dtft'):
        boundary='X(exp(i*w)) = '+result['boundary_dtft']
        sections.append(Section('DTFT sobre el círculo unitario',paragraphs=['Esta es la transformada de Fourier de la misma secuencia, no una transformada Z válida en una región abierta. Es 2π-periódica y en los saltos toma el promedio de los límites laterales. También podés calcularla y graficarla en Fourier → DTFT con soporte de −oo a oo.'],formulas=[Formula(boundary,boundary)]))
    if branches:
        for i,branch in enumerate(branches):
            expression=lhs+' = '+branch['expression']
            sections.append(Section('Resultado condicionado' if len(branches)==1 else 'Resultado: rama '+str(i+1),rows=[('Válido cuando',branch['condition'])],formulas=[Formula(expression,expression)]))
    else:
        expression=lhs+' = '+result.get('display_result',result['result'])
        terms=result.get('display_terms',[]);lines=[]
        if len(terms)>1:lines=[lhs+' = '+terms[0],*[(term if term.startswith('-') else '+'+term) for term in terms[1:]]]
        sections.append(Section(('Suma de definición' if z else 'Integral de definición') if result.get('convergence_empty') else 'Expresión numérica obtenida' if result.get('display_numeric') else 'Expresión obtenida' if result.get('evaluated',True) else 'Expresión sin resolver',paragraphs=['Vista redondeada a 6 cifras significativas para facilitar la lectura. Copiar texto y Guardar texto conservan al menos 17 cifras; este redondeo visual no interviene en los cálculos.' ] if result.get('display_numeric') else [],formulas=[Formula(expression,expression,lines,numeric=bool(result.get('display_numeric')))]))
    rows=([('Estado del cálculo',result['calculation_status']['label'])] if result.get('calculation_status') else [])+[('Dominio','Discreto · índices n enteros' if z else 'Continuo · tiempo t'),('Interpretación','Transformada inversa con ROC' if inverse and z else 'Suma sobre el soporte indicado' if z else 'Bilateral' if request.get('interpretation')=='bilateral' else 'Unilateral / causal')]
    for key,label in [('convergence','Convergencia'),('condition','Condición adicional'),('roc','Región de convergencia'),('roc_finite_plane','ROC en el plano finito')]:
        if key in result and result[key]!='True':
            displayed=result[key]
            if key=='convergence' and result.get('convergence_abscissa')=='-oo':displayed='Todo el plano s finito'
            elif key=='convergence' and result.get('convergence_abscissa')=='oo':displayed='No se obtuvo un semiplano finito de convergencia'
            rows.append((label,displayed))
    if 'infinity_included' in result:rows.append(('Incluye z=∞','Sí' if result['infinity_included'] else 'No'))
    if result.get('parameters'):rows.append(('Parámetros por asignar',', '.join(result['parameters'])))
    if rows:sections.append(Section('Condiciones',rows=rows))
    paragraphs=[result['scope']] if result.get('scope') else []
    if op=='z_inverse_expression':
        values=result.get('numeric_samples')
        if values:paragraphs.append('La tabla y la figura muestran sólo el intervalo de índices elegido, en doble precisión. La fórmula describe la secuencia completa. Otra ROC puede producir otra secuencia para la misma X(z).')
        elif result.get('parameters'):paragraphs.append('La expresión conserva parámetros. Asignales valores antes de obtener muestras numéricas.')
        else:paragraphs.append('Se obtuvo la expresión sin generar un registro numérico. Activá Graficar un intervalo si querés consultar muestras.')
    if paragraphs:sections.append(Section('Cómo interpretarlo',paragraphs=paragraphs))
    return Summary(title,sections)


def expression_measure_summary(request,result):
    discrete=request.get('domain')=='discrete';mode=request.get('mode','global');lhs='x[n]' if discrete else 'x(t)'
    titles={'global':'Energía y potencia de toda la señal','interval':'Medidas de un intervalo','periodic':'Medidas de una señal periódica'}
    sections=[Section('Definición de la señal',formulas=[Formula(lhs+' = '+request['expression'],lhs+' = '+request['expression'])])]
    rows=[]
    if mode=='interval':rows=[('Desde',request['lower']),('Hasta',request['upper'])]
    if mode=='periodic':rows=[('Período en muestras' if discrete else 'Período (s)',request['period'])]
    sections.append(Section('Alcance',rows=rows,paragraphs=[result['scope']]))
    states={'finite':'Finito','divergent':'Divergente (+∞)','conditional':'Sujeto a parámetros o condiciones','unevaluated':'Pendiente de evaluación','undetermined':'No determinado','undefined':'No definido'}
    quantities=[('Energía del intervalo' if mode=='interval' else 'Energía total','E',result['energy']),('Promedio cuadrático del intervalo' if mode=='interval' else 'Potencia media','P',result['mean_square']),('Valor eficaz','R',result['rms'])]
    if 'period_energy' in result:quantities.append(('Energía de un período','Ep',result['period_energy']))
    for title,symbol,data in quantities:
        rows=[('Estado',states.get(data['status'],data['status']))]
        if 'approximation' in data:rows.append(('Aproximación decimal',number(data['approximation'])))
        formula=symbol+' = '+data['exact'];sections.append(Section(title,rows=rows,formulas=[Formula(formula,formula)]))
    sections.append(Section('Interpretación',paragraphs=[result['classification']]))
    if result.get('parameters'):sections.append(Section('Parámetros por asignar',paragraphs=[', '.join(result['parameters'])]))
    if request.get('input_conditions'):sections.append(Section('Condiciones de la expresión de entrada',paragraphs=request['input_conditions']))
    return Summary(titles.get(mode,'Energía y potencia'),sections)
