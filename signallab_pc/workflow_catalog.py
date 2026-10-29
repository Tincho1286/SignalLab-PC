"""One public tool per problem; variants describe choices inside that tool."""
# title, summary, dimensions, [(route key, dimension values)]
FAMILIES=[
 ('Sumar o multiplicar señales','Combinar dos señales independientes, discretas o continuas.',('Operación',),[(('basic','sum'),('Suma',)),(('signal_product',0),('Producto',))]),
 ('Transformar una señal','Desplazamiento, inversión, amplitud y componentes par/impar.',('Dominio','Operación'),[
 (('basic','shift'),('Discreta','Desplazar')),(('basic','reverse'),('Discreta','Invertir')),(('basic','scale'),('Discreta','Amplitud')),(('basic','parity'),('Discreta','Par e impar')),(('time_transform',1),('Continua','Desplazar')),(('time_transform',2),('Continua','Invertir')),(('time_transform',3),('Continua','Amplitud')),(('time_transform',4),('Continua','Par e impar')),(('time_transform',0),('Continua','Transformación afín'))]),
 ('Energía, potencia y RMS','Medir registros o expresiones; alcance finito, global o periódico.',('Modelo','Alcance'),[
 (('basic','measures'),('Registro finito','Registro finito')),(('expression_measures','interval'),('Expresión analítica','Intervalo')),(('expression_measures','global'),('Expresión analítica','Todo el eje')),(('expression_measures','periodic'),('Expresión analítica','Periódica'))]),
 ('Convolución','Señales discretas o continuas; cálculo directo, por bloques o algebraico.',('Dominio','Método'),[
 (('basic','convolve'),('Discreta','Lineal')),(('basic','circular'),('Discreta','Circular')),(('dsp_extensions','blocks'),('Discreta','Por bloques FFT')),(('basic','continuous_convolve'),('Continua','Numérico')),(('convolution_algebra',0),('Continua','Algebraico'))]),
 ('Correlación y autocorrelación','Comparar señales por retardo, con las opciones de normalización de cada modelo.',('Dominio','Cálculo'),[
 (('correlation',0),('Discreta','Numérico')),(('correlation',1),('Continua','Numérico')),(('correlation_algebra',0),('Continua','Algebraico'))]),
 ('Espacio de estados','Analizar, simular, discretizar y obtener transferencias desde A, B, C y D.',('Estudio',),[
 (('state_space','analysis'),('Estructura y estabilidad',)),(('state_space','simulation'),('Respuesta temporal',)),(('state_space','frequency'),('Respuesta en frecuencia',)),(('state_space','discretize'),('Discretización',)),(('state_space','transfer'),('Función de transferencia',))]),
 ('Diseñar filtro','FIR e IIR: bandas, tolerancias, ventanas o coeficientes de segundo orden.',('Estructura','Dominio','Definir por'),[
 (('course_tools','fir'),('FIR','Digital','Bandas y tolerancias')),(('systems',0),('FIR','Digital','Cortes y longitud')),(('fir_window',0),('FIR','Digital','h[n] propia')),
 (('course_tools','iir'),('IIR','Digital','Bandas y tolerancias')),(('systems',1),('IIR','Digital','Sección biquad')),(('course_tools','analog'),('IIR','Analógico','Bandas y tolerancias'))]),
 ('Analizar un sistema','Frecuencia, raíces, realización con retardos/integradores y respuesta temporal.',('Respuesta',),[
 (('system_analysis',0),('Frecuencia y polos / ceros',)),(('systems',9),('Temporal',))]),
 ('Modelos de filtros','Modelos RC y de segundo orden desde sus parámetros físicos.',('Modelo',),[
 (('systems',2),('Circuito RC',)),(('systems',8),('Segundo orden',))]),
 ('Ajustar ganancia y fase','Normalizar ganancia, separar factores, compensar o reconstruir módulo/fase bajo hipótesis de fase mínima.',('Ajuste',),[
 (('course_tools','gain'),('Ganancia',)),(('course_tools','phase'),('Fase y compensación',))]),
 ('Transformada de Fourier','DFT/FFT, DTFT y Fourier continua; elegir transformada, dirección y cálculo.',('Transformada','Dirección','Cálculo'),[
 (('fourier',0),('DTFT','Directa','Numérico')),(('dtft_symbolic',0),('DTFT','Directa','Algebraico')),(('inverse_dtft',0),('DTFT','Inversa','Numérico')),(('dtft_symbolic',1),('DTFT','Inversa','Algebraico')),
 (('basic','dft'),('DFT / FFT','Directa','Transformada')),(('course_tools','fft'),('DFT / FFT','Directa','Ventanas y resolución')),(('basic','idft'),('DFT / FFT','Inversa','Numérico')),
 (('fourier',1),('Fourier continua','Directa','Numérico')),(('fourier_symbolic',0),('Fourier continua','Directa','Algebraico')),(('fourier',3),('Fourier continua','Inversa','Numérico')),(('fourier_symbolic',1),('Fourier continua','Inversa','Algebraico'))]),
 ('Series de Fourier y líneas espectrales','Coeficientes, síntesis periódica y potencia en armónicos.',('Estudio','Dominio'),[
 (('fourier',4),('Serie','Continua')),(('fourier',5),('Serie','Discreta')),(('course_tools','lines'),('Líneas de potencia','Continua'))]),
 ('Energía espectral','Densidad de energía desde una señal o energía integrada en una banda.',('Calcular',),[
 (('fourier',6),('Densidad de energía',)),(('course_tools','band'),('Energía en una banda',))]),
 ('Muestreo y aliasing','Muestrear expresiones y estudiar Nyquist o las tasas pasabanda.',('Estudio',),[
 (('sampling',0),('Muestrear señal',)),(('sampling',1),('Nyquist y aliasing',)),(('course_tools','bandpass_sampling'),('Tasas pasabanda',))]),
 ('Cambiar tasa de muestreo','Conversión racional con antialias y operaciones elementales sobre índices.',('Tratamiento',),[
 (('rational_resampling',0),('Conversión con antialias',)),(('sampling',2),('Diezmar / expandir / interpolar',))]),
 ('Cuantización y representación','Cuantización de amplitud, formatos, coeficientes y ejecución con precisión finita.',('Operación',),[
 (('sampling',4),('Cuantizar y medir SNR',)),(('sampling',5),('Formatos y ejecución',))]),
 ('Realizaciones y estadística','Generar registros, medir sus estadísticas y estimar autocorrelación o autocovarianza.',('Operación',),[
 (('random','generate'),('Generar realización',)),(('random','statistics'),('Estadísticas',)),(('random_correlation',0),('Autocorrelación',))]),
]

# Presentation metadata keeps a family's choices meaningful without new routes.
PRESENTATION={
 'Transformada de Fourier':{
    'dimension_labels':{(2,'DFT / FFT','Directa'):'Estudio'},
    'search_models':{'dtft':'DTFT','dft':'DFT / FFT','fft':'DFT / FFT','continua':'Fourier continua','ctft':'Fourier continua'},
    'model_tags':{'DTFT':'rad/muestra secuencia espectro periódico continuo','DFT / FFT':'rad/muestra coeficientes bins registro finito','Fourier continua':'rad/s tiempo segundos'},
    'variant_tags':{('basic','dft'):'numérico muestras',('course_tools','fft'):'numérico muestras',('fourier',0):'comparar superponer comparación'},

    'choice_hints':{
        'DTFT':'Transformada de una secuencia x[n]. X(ω) es continua y periódica cada 2π, en rad/muestra.',
        'DFT / FFT':'DFT de un registro finito: N coeficientes X[k]. FFT es un algoritmo para calcular esa misma DFT.',
        'Fourier continua':'Transformada de x(t). El eje angular Ω se expresa en rad/s.',
        'Directa':'De la señal a su transformada. La entrada de la inversa se conserva por separado.',
        'Inversa':'De la transformada a la señal. Para usar una salida ya calculada, elegila en Resultados.',
        'Transformada':'DFT de las muestras del registro; conserva N coeficientes complejos para su inversión.',
        'Ventanas y resolución':'Ventanas, relleno con ceros y comparación con DTFT; sigue calculando la DFT mediante FFT.',
    },
 },
}
