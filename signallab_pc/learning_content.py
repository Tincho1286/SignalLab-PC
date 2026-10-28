"""Conceptos antes de procedimientos: lectura guiada según los programas de 2026."""
GLOSSARY={
'IEEE 754':'Estándar que define formatos y reglas para representar números en coma flotante. La palabra separa signo, exponente y fracción.',
'subnormal':'Número flotante pequeño que usa el exponente mínimo sin el uno inicial implícito de los números normales. Permite acercarse gradualmente a cero.',
'mantisa':'Nombre habitual de la parte significativa de un número flotante. La fracción almacenada y el bit inicial implícito determinan esa parte en los formatos binarios.',
'LTI':'Lineal e invariante en el tiempo: sumar entradas suma sus salidas, y retrasar una entrada retrasa la salida en la misma cantidad.',
'DTFT':'Transformada de Fourier de tiempo discreto: describe una secuencia con una función continua y periódica de la frecuencia.',
'DFT':'Transformada discreta de Fourier: entrega N valores de frecuencia a partir de N muestras.',
'FFT':'Algoritmo rápido para calcular la DFT; no es una transformada diferente.',
'CTFT':'Transformada de Fourier de tiempo continuo: relaciona x(t) con su espectro X(Ω).',
'FIR':'Filtro con respuesta al impulso de duración finita: su salida depende de un número finito de entradas.',
'IIR':'Filtro con respuesta al impulso que puede durar indefinidamente; suele usar valores anteriores de la salida.',
'PSD':'Densidad espectral de potencia: indica cómo se reparte la potencia entre frecuencias; la potencia de una banda se obtiene integrando.',
'RMS':'Valor eficaz: raíz del promedio del módulo al cuadrado. Incluye la media de la señal.',
'ROC':'Región de convergencia: valores de s o z donde existe la transformada. Una fórmula racional sola no siempre determina la señal.',
'BIBO':'Entrada acotada, salida acotada: una entrada de amplitud limitada no puede producir una salida ilimitada.',
'SOS':'Secciones de segundo orden: pequeños filtros conectados en cascada para reducir problemas de redondeo.',
'WSS':'Estacionario en sentido amplio: media constante y autocorrelación dependiente sólo de la separación temporal.',
'SNR':'Relación señal/ruido: cociente entre las potencias de la señal útil y del ruido.',
'ZOH':'Retención de orden cero: mantener cada muestra constante hasta la siguiente.',
'MIMO':'Sistema con varias entradas y varias salidas.',
'cuadratura':'Integración numérica: aproximar una integral a partir de valores de la función en puntos elegidos.',
'rejilla':'Conjunto de puntos donde se evalúa una función. Por ejemplo, al calcular 1025 frecuencias entre −π y π, se comprueba la respuesta en esos puntos y no en todos los valores intermedios.',
'soporte':'Parte del eje donde la señal puede ser distinta de cero. Indicar su soporte permite distinguir, por ejemplo, un pulso finito de una señal que continúa indefinidamente.',
'causal':'La salida actual depende del presente y del pasado de la entrada, no de su futuro.',
'aliasing':'Superposición de componentes distintas al muestrear: después no se pueden distinguir sólo con esas muestras.',
'ergodicidad':'Propiedad que permite obtener ciertos promedios del conjunto de realizaciones a partir de una realización suficientemente larga. Depende del promedio considerado.',
'varianza':'Promedio del módulo al cuadrado de la diferencia respecto de la media; mide dispersión.',
'sesgo':'Diferencia entre el promedio de un estimador y el valor verdadero que intenta estimar.'}

from .library_concepts import TOPICS


def concept_sections():
    topics=[dict(title=t,category='Conceptos · '+course,route=None,purpose=intro,usage=example,blocks=[('Idea principal',intro),('Relación matemática',formula),('Cómo interpretarlo',example),('Condiciones y alcance',limit)]) for t,course,intro,formula,example,limit in TOPICS]
    topics.insert(0,dict(title='Glosario: siglas y palabras frecuentes',category='Conceptos · Primeros pasos',route=None,purpose='Definiciones breves para leer fórmulas e informes.',usage=' '.join(GLOSSARY),blocks=[(term,meaning) for term,meaning in GLOSSARY.items()]))
    return topics

def concept_for(section):
    kind=section['route'][1];category=section.get('legacy_category',section['category'])
    if kind=='dsp_extensions':
        return [('Alcance','Estas herramientas trabajan con registros finitos. Hilbert usa extensión periódica; STFT analiza ventanas; la convolución por bloques usa extensión por ceros. Las condiciones de borde son parte del modelo.')]
    index=13 if kind=='state_space' else 1 if kind=='expression_measures' or section['route'][2]=='measures' else 4 if kind=='frequency_filter' else 7 if category=='Transformadas' else 6 if category=='Muestreo' else 10 if 'correlation' in kind else 9 if category=='Señales aleatorias' else 3 if category=='Fourier' else 8 if category=='Filtros y sistemas' else 2 if category in ('Control','Operaciones') else 0
    t,course,intro,formula,example,limit=TOPICS[index]
    return [('Concepto: '+t,intro),('Relación matemática',formula),('Ejemplo de interpretación',example),('Alcance del modelo',limit)]
