"""Public documents and the operations they contain; no implicit data sharing."""
GROUPS={
'signals':('Señales','Señales','signal',[
 ('Crear y editar', [('Generar y graficar',('basic','generate')),('Generar ventana',('window_signal',0)),('Editar muestras',('signal_editor',0))]),
 ('Transformar', [('Desplazar secuencia',('basic','shift')),('Invertir secuencia',('basic','reverse')),('Escalar amplitud',('basic','scale')),('Partes par e impar',('basic','parity')),('Transformar señal continua',('time_transform',0)),('Desplazar señal continua',('time_transform',1)),('Invertir señal continua',('time_transform',2)),('Escalar amplitud continua',('time_transform',3)),('Partes par e impar continuas',('time_transform',4)),('Sumar señales',('basic','sum')),('Multiplicar señales',('signal_product',0))])]),
'measures':('Señales','Energía, potencia y RMS','measure',[
 ('Medidas', [('Registro de muestras',('basic','measures')),('Expresión en un intervalo',('expression_measures','interval')),('Expresión en todo el eje',('expression_measures','global')),('Expresión periódica',('expression_measures','periodic'))])]),
'convolution':('Sistemas','Convolución','convolution',[
 ('Discreta', [('Lineal',('basic','convolve')),('Circular',('basic','circular')),('Por bloques FFT',('dsp_extensions','blocks'))]),
 ('Continua', [('Numérica',('basic','continuous_convolve')),('Algebraica',('convolution_algebra',0))])]),
'correlation':('Sistemas','Correlación y autocorrelación','correlation',[
 ('Correlación', [('Discreta',('correlation',0)),('Continua y periódica',('correlation',1)),('Continua algebraica',('correlation_algebra',0))])]),
'fourier':('Espectros','Fourier y FFT','spectrum',[
 ('Discreta', [('DTFT y comparación con DFT',('fourier',0)),('DFT',('basic','dft')),('DFT inversa',('basic','idft')),('FFT, ventanas y resolución',('course_tools','fft')),('DTFT algebraica',('dtft_symbolic',0)),('DTFT inversa numérica',('inverse_dtft',0)),('DTFT inversa algebraica',('dtft_symbolic',1))]),
 ('Continua', [('Transformada numérica',('fourier',1)),('Inversa numérica',('fourier',3)),('Transformada algebraica',('fourier_symbolic',0)),('Inversa algebraica',('fourier_symbolic',1))])]),
'series':('Espectros','Series de Fourier','harmonics',[
 ('Series', [('Continua',('fourier',4)),('Discreta',('fourier',5)),('Potencia y líneas espectrales',('course_tools','lines'))])]),
'densities':('Espectros','Densidades espectrales','density',[
 ('Densidades', [('Densidad de energía',('fourier',6)),('Energía por banda',('course_tools','band')),('Densidad de potencia: periodograma y Welch',('fourier',7))])]),
'local_spectra':('Espectros','Hilbert y tiempo-frecuencia','spectrum',[
 ('Análisis', [('Hilbert y señal analítica',('dsp_extensions','hilbert')),('STFT y espectrograma',('dsp_extensions','stft'))])]),
'sampling':('Muestreo','Muestreo y reconstrucción','sampling',[
 ('Muestrear', [('Muestrear expresión',('sampling',0)),('Nyquist y aliasing',('sampling',1)),('Muestreo pasabanda',('course_tools','bandpass_sampling'))]),
 ('Reconstruir', [('Reconstrucción',('sampling',3))]),
 ('Cambiar tasa', [('Conversión racional con antialias',('rational_resampling',0)),('Diezmar, expandir e interpolar',('sampling',2)),('Relacionar frecuencias y período',('course_tools','mapping'))])]),
'quantize':('Muestreo','Cuantización y punto fijo','quantize',[
 ('Representación', [('Cuantización y SNR',('sampling',4)),('Precisión numérica y ejecución',('sampling',5))])]),
'states':('Sistemas','Espacio de estados','states',[
 ('Modelo', [('Analizar estabilidad y estructura',('state_space','analysis')),('Simular estados y salidas',('state_space','simulation')),('Respuesta en frecuencia MIMO',('state_space','frequency')),('Discretizar modelo',('state_space','discretize')),('Obtener función de transferencia',('state_space','transfer'))])]),
'laplace':('Transformadas','Laplace y ecuaciones','laplace',[
 ('Operación', [('Transformada directa e inversa',('transform_lab','laplace')),('Resolver ecuación diferencial',('symbolic',4)),('Resolver ecuación en diferencias',('difference_equation',0))])]),
'random':('Aleatorias','Realizaciones y estadística','random',[
 ('Operación', [('Generar realización',('random','generate')),('Estadísticas e histograma',('random','statistics')),('Correlación y covarianza',('random_correlation',0)),('Modelo AR / MA / ARMA',('random_model','model')),('Estimar modelo AR',('random_model','fit'))])]),
}
GROUP_ROUTES={key:(title,'tool_group',key,None) for key,(_,title,_,_) in GROUPS.items()}
GROUP_FOR={operation:GROUP_ROUTES[key] for key,(_,_,_,tabs) in GROUPS.items() for _,choices in tabs for _,operation in choices}
def members(group):return [key for _,choices in GROUPS[group][3] for _,key in choices]
