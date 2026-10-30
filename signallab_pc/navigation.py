"""Rutas públicas de herramientas, independientes de Qt."""
# title, panel kind, task index, input kind
MENUS={
 'Señales': [('Tabla y edición de muestras','signal_editor',0,None),('Generar y graficar','basic','generate','discrete'),('Energía, potencia y RMS','basic','measures','discrete'),('Desplazar una secuencia','basic','shift','discrete'),('Invertir el eje','basic','reverse','discrete'),('Escalar amplitud','basic','scale','discrete'),('Partes par e impar','basic','parity','discrete')],
 'Operaciones': [('Convolución continua numérica','basic','continuous_convolve','continuous_pair'),('Convolución continua algebraica','convolution_algebra',0,None),('Correlación continua','basic','continuous_correlate','continuous_pair'),('Correlación continua normalizada','basic','continuous_normalized','continuous_pair'),('Autocorrelación continua','basic','continuous_auto','continuous'),('Convolución lineal','basic','convolve','pair'),('Correlación lineal','basic','correlate','pair'),('Sumar dos señales','basic','sum','pair'),('Convolución circular','basic','circular','pair')],
 'Fourier': [('DTFT inversa numérica','inverse_dtft',0,'frequency'),('DTFT inversa algebraica','dtft_symbolic',1,None),('DTFT algebraica','dtft_symbolic',0,None),('Fourier continua algebraica','fourier_symbolic',0,None),('Fourier inversa algebraica','fourier_symbolic',1,None),('DFT','basic','dft','discrete'),('DFT inversa','basic','idft','discrete'),('DTFT y comparación con DFT','fourier',0,'discrete'),('Fourier continua','fourier',1,'continuous'),('Fourier continua inversa','fourier',3,'import'),('Serie de Fourier continua','fourier',4,'import'),('Serie de Fourier discreta','fourier',5,'discrete'),('Densidad de energía espectral','fourier',6,'import'),('PSD y Welch','fourier',7,'discrete')],
 'Filtros y sistemas': [('Análisis numérico y algebraico','system_analysis',0,None),('Filtro FIR','systems',0,None),('Filtro IIR biquad','systems',1,None),('Circuito RC','systems',2,None),('Función de transferencia','systems',3,None),('Respuesta en frecuencia','systems',4,None),('Filtrado, impulso y escalón','systems',5,'discrete'),('Diseñar por polos y ceros','systems',6,None),('Transformación bilineal','systems',7,None)],
 'Control': [('Análisis en espacio de estados','state_space','analysis',None),('Simulación en espacio de estados','state_space','simulation',None),('Frecuencia de sistema MIMO','state_space','frequency',None),('Discretizar modelo de estados','state_space','discretize',None),('Estados a función de transferencia','state_space','transfer',None),('Sistema de segundo orden','systems',8,None),('Respuesta temporal','systems',9,None),('Realimentación','systems',10,None),('Lugar de raíces','systems',11,None)],
 'Muestreo': [('Cambio racional de tasa con antialias','rational_resampling',0,None),('Muestrear una expresión','sampling',0,None),('Nyquist y aliasing','sampling',1,None),('Cambiar tasa de muestreo','sampling',2,'discrete'),('Reconstrucción','sampling',3,'discrete'),('Cuantización y SNR','sampling',4,'discrete'),('Precisión numérica','sampling',5,None)],
 'Transformadas': [('Laplace directa','symbolic',0,None),('Laplace inversa','symbolic',1,None),('Transformada Z finita','symbolic',2,'discrete'),('Z inversa racional','symbolic',3,None),('Ecuaciones diferenciales','symbolic',4,None),('Ecuaciones en diferencias','difference_equation',0,None)],
}

MENUS['Operaciones']=[('Correlación continua algebraica','correlation_algebra',0,None),('Correlación discreta y autocorrelación','correlation',0,None),('Correlación continua y periódica','correlation',1,None)]+[item for item in MENUS['Operaciones'] if item[2] not in ('correlate','continuous_correlate','continuous_normalized','continuous_auto')]


MENUS['Señales'].insert(1,('Generar ventanas','window_signal',0,None))
MENUS['Señales'][2:2]=[('Energía algebraica por intervalo','expression_measures','interval',None),('Energía y potencia globales','expression_measures','global',None),('Energía y potencia periódicas','expression_measures','periodic',None)]

MENUS['Señales aleatorias']=[('Generar ruido y realizaciones','random','generate',None),('Estadísticas e histograma','random','statistics','discrete')]

MENUS['Señales aleatorias'].append(('Correlación y covarianza de registros','random_correlation',0,'discrete'))
MENUS['Señales aleatorias'] += [('Analizar modelo AR, MA o ARMA','random_model','model',None),('Estimar modelo AR desde un registro','random_model','fit','discrete')]

MENUS['Señales'].insert(2,('Transformar una señal continua','time_transform',0,'continuous'))
MENUS['Señales'] += [(title,'time_transform',index,'continuous') for index,title in [(1,'Desplazar señal continua'),(2,'Invertir señal continua'),(3,'Escalar amplitud continua'),(4,'Partes par e impar continuas')]]

MENUS['Filtros y sistemas'].insert(1,('Conectar sistemas','interconnection',0,None))

MENUS['Fourier'] += [('Ventanas, FFT y resolución espectral','course_tools','fft','discrete'),('Energía espectral por banda','course_tools','band','frequency'),('Potencia periódica y líneas espectrales','course_tools','lines','discrete')]
MENUS['Filtros y sistemas'] += [('FIR por especificaciones','course_tools','fir',None),('IIR por especificaciones','course_tools','iir',None),('Convertir sistema analógico / digital','course_tools','convert',None),('Normalizar ganancia','course_tools','gain',None),('Fase mínima y fase lineal','course_tools','phase',None)]
MENUS['Transformadas'] += [('Z inversa con región de convergencia','course_tools','inverse_z',None)]
MENUS['Muestreo'] += [('Mapeo de frecuencias y período','course_tools','mapping',None)]

MENUS['Filtros y sistemas'].insert(0,('Filtros ideales y por tramos','frequency_filter',0,None))

MENUS['Fourier'] += [('Hilbert y señal analítica','dsp_extensions','hilbert','discrete'),('STFT y espectrograma','dsp_extensions','stft','discrete')]
MENUS['Operaciones'] += [('Convolución por bloques','dsp_extensions','blocks','discrete')]

MENUS['Filtros y sistemas'].append(('Filtro analógico por especificaciones','course_tools','analog',None))

MENUS['Muestreo'].append(('Tasas de muestreo pasabanda','course_tools','bandpass_sampling',None))


MENUS['Señales'].append(('Multiplicar señales','signal_product',0,None))
MENUS['Filtros y sistemas'].append(('FIR desde h[n] propia y ventana','fir_window',0,'discrete'))

FILTER_ROUTE=('Filtros y sistemas','filter_lab',0,None)
LAPLACE_ROUTE=('Transformada de Laplace','transform_lab','laplace',None)
Z_ROUTE=('Transformada Z','transform_lab','z',None)
FILTER_KEYS={item[1:3] for item in MENUS['Filtros y sistemas'] if item[1]!='interconnection'}|{('systems',8),('systems',9),('systems',11)}
TRANSFORM_ALIASES={('symbolic',0):LAPLACE_ROUTE,('symbolic',1):LAPLACE_ROUTE,('symbolic',2):Z_ROUTE,('symbolic',3):Z_ROUTE,('course_tools','inverse_z'):Z_ROUTE}
MENUS['Filtros y sistemas'].append(FILTER_ROUTE)
MENUS['Transformadas'] += [LAPLACE_ROUTE,Z_ROUTE]

from .tool_groups import GROUPS,GROUP_ROUTES
for _key,(_area,_,_,_) in GROUPS.items():MENUS.setdefault(_area,[]).append(GROUP_ROUTES[_key])

# Old destinations remain callable, but duplicated help entries are retired.
RETIRED_KEYS={('systems',3),('systems',4),('systems',5),('systems',7),('systems',10),('systems',11)}|set(TRANSFORM_ALIASES)
