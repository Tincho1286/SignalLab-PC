"""User-facing locations: actions are indexed once, independently of their containers."""
import unicodedata
from .workspaces import ROUTES
AREAS=[
 ('signals','Señales','Crear, editar, transformar y medir señales.','signal'),
 ('systems','Sistemas LTI','Analizar H, obtener respuestas y conectar sistemas.','blocks'),
 ('filters','Diseño de filtros','Diseñar, ajustar y convertir filtros.','design'),
 ('spectra','Fourier y espectros','Transformadas, series, densidades y espectrogramas.','spectrum'),
 ('sampling','Muestreo y A/D','Muestrear, reconstruir, cambiar tasa y cuantizar.','sampling'),
 ('transforms','Laplace y Z','Expresiones, inversas y ecuaciones diferenciales.','zplane'),
 ('random','Señales aleatorias','Realizaciones, correlación, modelos AR/MA/ARMA y estimación de parámetros.','random'),
]
ENTRIES=[]
def add(area,section,key,title,summary,tags=''):
    ENTRIES.append(dict(area=area,section=section,key=key,route=ROUTES[key],title=title,summary=summary,tags=tags))
add('signals','Crear y editar',('basic','generate'),'Crear una señal','Fórmula, muestras o archivo; gráfico y tabla.','generar graficar impulso escalon seno coseno tramos matlab')
add('signals','Crear y editar',('signal_editor',0),'Editar muestras','Editar valores y eje; exportar o reutilizar la salida.','tabla datos continuo discreto')
for key,title,summary in [
 ('shift','Desplazar','Trasladar una secuencia en índices enteros.'),('reverse','Invertir','Reflejar una secuencia respecto de n = 0.'),('scale','Escalar amplitud','Multiplicar los valores por un factor.'),('parity','Partes par e impar','Separar las dos componentes de una secuencia.'),('sum','Sumar señales','Sumar dos señales discretas o continuas sobre su intervalo conjunto.')]:add('signals','Transformar',('basic',key),title,summary)
add('signals','Transformar',('time_transform',0),'Transformar señal continua','Escala y desplazamiento temporal; amplitud.','tiempo invertir')
for index,title,summary in [(1,'Desplazar señal continua','Cambiar el origen temporal con t₀ en segundos.'),(2,'Invertir señal continua','Reflejar x(t) alrededor de t=0.'),(3,'Escalar amplitud continua','Multiplicar los valores y pesos Dirac por A.'),(4,'Partes par e impar continuas','Descomponer x(t) en componentes simétrica y antisimétrica.')]:add('signals','Transformar',('time_transform',index),title,summary,'transformacion tiempo amplitud par impar simetria')
for key,title,summary in [
 (('basic','measures'),'Medir un registro','Energía, potencia y RMS de las muestras.'),
 (('expression_measures','interval'),'Medir en un intervalo','Energía de una expresión en límites definidos.'),
 (('expression_measures','global'),'Medir en todo el eje','Energía y potencia globales; condiciones de convergencia.'),
 (('expression_measures','periodic'),'Medir señal periódica','Energía por período y potencia media.')]:add('signals','Energía y potencia',key,title,summary,'energia potencia rms')
add('systems','Analizar y simular',('system_analysis',0),'Función de transferencia y análisis','H(s) o H(z): módulo/dB, fase, retardo, polos/ceros y realización.','bode logaritmico decibelios margenes frecuencia estabilidad grupo numerador denominador coeficientes formula polos ceros realizacion diagrama integradores retardos estados directa cascada')
add('systems','Analizar y simular',('systems',9),'Respuesta temporal','Impulso, escalón o entrada propia; condiciones iniciales.','filtrar convolucion diferencias simulacion')
add('systems','Analizar y simular',('interconnection',0),'Conectar sistemas','Cascada, paralelo o realimentación de bloques.','retroalimentacion feedback')
for key,title,summary in [
 (('basic','convolve'),'Convolución lineal','Dos secuencias; salida completa.'),
 (('basic','circular'),'Convolución circular','Secuencias con extensión periódica.'),
 (('dsp_extensions','blocks'),'Convolución por bloques','Overlap-add y overlap-save mediante FFT.'),
 (('basic','continuous_convolve'),'Convolución continua numérica','Señales continuas representadas por registros.'),
 (('convolution_algebra',0),'Convolución continua algebraica','Expresiones y soportes; integral simbólica.')]:add('systems','Convolución',key,title,summary)
for key,title,summary in [
 (('correlation',0),'Correlación discreta','Correlación y autocorrelación de secuencias.'),
 (('correlation',1),'Correlación continua','Registros continuos y casos periódicos.'),
 (('correlation_algebra',0),'Correlación algebraica','Expresiones y soportes continuos.')]:add('systems','Correlación',key,title,summary,'autocorrelacion normalizar retardos')
for task,title,summary in [
 ('analysis','Analizar modelo de estados','Estabilidad, controlabilidad y observabilidad.'),
 ('simulation','Simular estados y salidas','Evolución del modelo con una entrada propia.'),
 ('frequency','Frecuencia de modelo MIMO','Respuesta por canal de entrada y salida.'),
 ('discretize','Discretizar modelo de estados','Convertir las matrices con un período de muestreo.'),
 ('transfer','Estados a transferencia','Obtener H para un par entrada/salida.')]:add('systems','Espacio de estados',('state_space',task),title,summary,'matrices abcd')
for key,title,summary in [
 (('course_tools','fir'),'FIR por especificaciones','Bandas, tolerancias y ventana.'),
 (('course_tools','iir'),'IIR por especificaciones','Butterworth, Chebyshev o elíptico digitales.'),
 (('course_tools','analog'),'Analógico por especificaciones','Familias analógicas con bordes en rad/s.'),
 (('systems',6),'Diseñar por polos y ceros','Ubicar raíces con el mouse o por coordenadas.'),
 (('systems',0),'FIR por ventana','Tipo, frecuencia de corte y cantidad de coeficientes.'),
 (('systems',1),'Sección IIR biquad','Configurar un filtro de segundo orden.'),
 (('systems',2),'Circuito RC','Modelo de primer orden a partir de R y C.'),
 (('systems',8),'Modelo de segundo orden','Frecuencia natural, amortiguamiento y ganancia.')]:add('filters','Diseñar',key,title,summary,'sintesis filtro')
add('filters','Ideales y conversión',('frequency_filter',0),'Filtros ideales y por tramos','Definir H, analizar su respuesta y filtrar.','ideal funcion partes frecuencia')
add('filters','Ideales y conversión',('course_tools','convert'),'Convertir analógico / digital','Bilineal, invarianza y FIR por ventana para ideales.','conversion discretizar')
add('filters','Ajustar un filtro',('course_tools','gain'),'Normalizar ganancia','Fijar el módulo en una frecuencia elegida.','ajuste amplitud')
add('filters','Ajustar un filtro',('course_tools','phase'),'Fase y compensación','Factorizar, compensar o reconstruir módulo y fase con hipótesis explícitas.','lineal reflejar ceros compensador ecualizar igualar modulo retardo reconstruccion cepstrum hilbert fase minima')
for key,title,summary in [
 (('fourier',0),'DTFT y comparación con DFT','Curva DTFT y muestras DFT superpuestas.'),
 (('basic','dft'),'DFT','Transformar una secuencia finita.'),
 (('basic','idft'),'DFT inversa','Recuperar la secuencia desde X[k].'),
 (('course_tools','fft'),'FFT y ventanas','Longitud observada, resolución y comparación espectral.'),
 (('dtft_symbolic',0),'DTFT algebraica','Expresión de la secuencia y soporte de suma.')]:add('spectra','Fourier discreta',key,title,summary,'transformada frecuencia')
for key,title,summary in [
 (('fourier',1),'Fourier continua numérica','Transformar un registro temporal.'),
 (('fourier',3),'Fourier continua inversa','Recuperar la señal desde un espectro propio.'),
 (('fourier_symbolic',0),'Fourier continua algebraica','Transformar una expresión temporal.'),
 (('fourier_symbolic',1),'Fourier inversa algebraica','Recuperar la expresión temporal.')]:add('spectra','Fourier continua',key,title,summary,'transformada')
for key,title,summary in [
 (('fourier',4),'Serie continua','Coeficientes y aproximación de una señal periódica.'),
 (('fourier',5),'Serie discreta','Coeficientes de una secuencia periódica.'),
 (('course_tools','lines'),'Potencia y líneas espectrales','Pesos espectrales desde coeficientes de serie.')]:add('spectra','Series de Fourier',key,title,summary,'armonicos')
for key,title,summary in [
 (('fourier',6),'Densidad de energía','Desde una señal propia o un espectro.'),
 (('course_tools','band'),'Energía en una banda','Integrar |X|² entre frecuencias elegidas.'),
 (('fourier',7),'Densidad de potencia','Periodograma o estimación de Welch.')]:add('spectra','Densidades espectrales',key,title,summary,'psd espectral energia')
add('spectra','Otras representaciones',('dsp_extensions','hilbert'),'Hilbert y señal analítica','Componentes en cuadratura y envolvente.')
add('spectra','Otras representaciones',('dsp_extensions','stft'),'STFT y espectrograma','Evolución del espectro por ventanas temporales.','tiempo frecuencia')
for key,title,summary,section in [
 (('sampling',0),'Muestrear una expresión','Señal continua y tasa de muestreo.','Muestrear y reconstruir'),
 (('sampling',1),'Nyquist y aliasing','Explorar la superposición de réplicas.','Muestrear y reconstruir'),
 (('course_tools','bandpass_sampling'),'Muestreo pasabanda','Tasas admisibles para una banda limitada.','Muestrear y reconstruir'),
 (('sampling',3),'Reconstruir una señal','Aproximar la señal continua desde sus muestras.','Muestrear y reconstruir'),
 (('rational_resampling',0),'Cambiar tasa con antialias','Conversión racional por L/M.','Cambiar tasa'),
 (('sampling',2),'Diezmar, expandir o interpolar','Operaciones discretas sobre el índice.','Cambiar tasa'),
 (('course_tools','mapping'),'Relacionar frecuencias y período','Correspondencia entre Ω, ω y T.','Frecuencias y período'),
 (('sampling',4),'Cuantizar y medir SNR','Niveles de amplitud y error de cuantización.','Cuantización'),
 (('sampling',5),'Precisión numérica','Punto fijo, IEEE 754, coeficientes y ejecución: redondeo, saturación, acumuladores, memorias y ciclos límite.','Cuantización')]:add('sampling',section,key,title,summary)
add('transforms','Transformadas',('transform_lab','laplace'),'Transformada de Laplace','Directa e inversa, unilateral o bilateral con ROC.','unilateral bilateral causal inversa s roc izquierda derecha')
add('transforms','Transformadas',('transform_lab','z'),'Transformada Z','Directa, inversa con ROC y muestras finitas.','region convergencia bilateral secuencia inversa')
add('transforms','Ecuaciones',('symbolic',4),'Ecuaciones diferenciales','Solución algebraica y condiciones iniciales.','edo')
for key,title,summary in [
 (('random','generate'),'Generar realización','Distribución y semilla.'),
 (('random','statistics'),'Estadísticas e histograma','Media, varianza, RMS e histograma.'),
 (('random_correlation',0),'Correlación y covarianza','Auto y cruzada: estimaciones a partir de uno o dos registros.')]:add('random','Generación y análisis',key,title,summary)
add('random','Modelos',('random_model','model'),'Analizar modelo AR, MA o ARMA','Media, varianza, correlación y PSD teóricas; realización estacionaria.','proceso estocastico autorregresivo promedio movil ruido blanco filtrado lyapunov')
add('random','Modelos',('random_model','fit'),'Estimar modelo AR','Yule–Walker desde un registro; innovación y espectro paramétrico.','yule walker estimacion parametros identificacion espectral autoregresivo')
add('spectra','Fourier discreta',('inverse_dtft',0),'DTFT inversa numérica','Obtener x[n] desde un período de X(ω) en rad/muestra.','inversa idtft periodo bilateral muestras')
add('spectra','Fourier discreta',('dtft_symbolic',1),'DTFT inversa algebraica','Recuperar la expresión de x[n] por propiedades o integración.','inversa idtft expresion propiedades bilateral')
add('signals','Transformar',('signal_product',0),'Multiplicar señales','Producto punto a punto para enventanar señales discretas o continuas.','multiplicacion producto ventana enventanado dos señales')
add('filters','Diseñar',('fir_window',0),'FIR desde h[n] propia y ventana','Cargar h[n], aplicar una ventana y obtener el FIR.','enventanar respuesta impulso propia coeficientes ventana')
# Operations have one canonical home, regardless of their historical routes.
for entry in ENTRIES:
    if entry['key'] in (('basic','sum'),('signal_product',0)):entry['section']='Combinar y comparar'
    if entry['section'] in ('Convolución','Correlación'):
        entry['area']='signals';entry['section']='Combinar y comparar'
    if entry['key']==('frequency_filter',0):
        entry['area']='filters';entry['section']='Ideales y conversión'
        entry['title']='Filtro ideal o definido en frecuencia'
        entry['summary']='Definir H por fórmula o tramos, ver su respuesta y filtrar una entrada.'
# Keep the detailed operation index for contextual help and precise searches.
DETAIL_ENTRIES=ENTRIES
DETAILS_BY_KEY={entry['key']:entry for entry in DETAIL_ENTRIES}
from .workflow_catalog import FAMILIES,PRESENTATION
_members={key for _,_,_,variants in FAMILIES for key,_ in variants}
if sum(len(variants) for _,_,_,variants in FAMILIES)!=len(_members):raise RuntimeError('Una variante pertenece a más de una herramienta.')
ENTRIES=[];_family_for={}
for title,summary,dimensions,variants in FAMILIES:
    first=DETAILS_BY_KEY[variants[0][0]]
    entry=dict(first,title=title,summary=summary,dimensions=dimensions,variants=variants)
    entry.update(PRESENTATION.get(title,{}))
    if title=='Transformada de Fourier':entry['section']='Transformadas'
    entry['tags']=' '.join(' '.join((DETAILS_BY_KEY[key]['title'],DETAILS_BY_KEY[key]['summary'],DETAILS_BY_KEY[key]['tags'],*values)) for key,values in variants)
    for key,_ in variants:_family_for[key]=entry
for detail in DETAIL_ENTRIES:
    entry=_family_for.get(detail['key'],dict(detail,dimensions=(),variants=[(detail['key'],())]))
    if entry not in ENTRIES:ENTRIES.append(entry)
_section_order={'signals':['Crear y editar','Transformar','Combinar y comparar','Energía y potencia'],'systems':['Analizar y simular','Espacio de estados'],'filters':['Diseñar','Ajustar un filtro','Ideales y conversión']}
_area_order={area[0]:i for i,area in enumerate(AREAS)}
def _order(entry):
    sections=_section_order.get(entry['area'],[])
    return (_area_order[entry['area']],sections.index(entry['section']) if entry['section'] in sections else len(sections))
ENTRIES.sort(key=_order)
BY_KEY={key:entry for entry in ENTRIES for key,_ in entry['variants']}
AREA_BY_ID={area[0]:area for area in AREAS}

def normalize(text):return ''.join(c for c in unicodedata.normalize('NFKD',text.casefold()) if not unicodedata.combining(c))
def _variant_search_record(entry,key,values):
    detail=DETAILS_BY_KEY[key]
    extra=' '.join((*values,entry.get('variant_tags',{}).get(key,''),entry.get('model_tags',{}).get(values[0] if values else '', '')))
    return dict(detail,title=entry['title']+' '+detail['title'],tags=detail['tags']+' '+extra)


def matches(entry,query):
    if entry.get('variants'):
        # Match one valid combination, rather than words from unrelated variants.
        return any(matches(_variant_search_record(entry,key,values),query) for key,values in entry['variants'])
    text=normalize(' '.join((entry['title'],entry['section'],entry['summary'],entry['tags'],AREA_BY_ID[entry['area']][1])))
    return all(word in text for word in normalize(query).split())


def search_variant(entry,query,current_key=None):
    import re
    words=set(re.findall(r'\w+',normalize(query)))
    desired=next((model for token,model in entry.get('search_models',{}).items() if token in words),None)
    candidates=[]
    for key,values in entry['variants']:
        if not matches(_variant_search_record(entry,key,values),query):continue
        title_words=set(re.findall(r'\w+',normalize(DETAILS_BY_KEY[key]['title'])))
        score=(words==title_words,bool(desired and values and values[0]==desired),key==current_key,len(words & title_words))
        candidates.append((score,key))
    if not candidates:return None
    # max by score alone keeps catalog order as the final, predictable default.
    return max(candidates,key=lambda candidate:candidate[0])[1]

def normalized_key(item):
    key=tuple(item[1:3])
    from .filter_lab import ALIASES
    from .navigation import TRANSFORM_ALIASES
    key=ALIASES.get(key,key)
    if key in TRANSFORM_ALIASES:key=TRANSFORM_ALIASES[key][1:3]
    if key==('systems',10):key=('interconnection',0)
    return key
def locate(item):return BY_KEY.get(normalized_key(item))
def detail_for(item):return DETAILS_BY_KEY.get(normalized_key(item))

def compact_destinations(items):
    candidates={normalized_key(item):item for item in items}
    result=[]
    for entry in ENTRIES:
        compatible=[key for key,_ in entry['variants'] if key in candidates]
        if compatible:
            key=entry['key'] if entry['key'] in compatible else compatible[0]
            result.append((entry,candidates[key]))
    return result


def destination_label(entry,item):
    return entry.get('destination_labels',{}).get(normalized_key(item),entry['title'])
