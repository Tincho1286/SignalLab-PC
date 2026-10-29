"""Orientación de herramientas compartida por menús, búsqueda y encabezados."""
DETAILS = {
 ('difference_equation',0): 'Coeficientes por retardos, f[n] e historial → solución algebraica y muestras de y[n].',
 ('random_model','model'): 'Modelo AR/MA/ARMA y ruido blanco → estadísticas teóricas, espectro y realización estacionaria.',
 ('random_model','fit'): 'Registro y orden p → modelo AR por Yule–Walker, espectro paramétrico y residuo.',
 ('state_space','analysis'): 'Matrices A, B, C y D → estabilidad, controlabilidad y observabilidad.',
 ('state_space','simulation'): 'Matrices y entradas u(t) → evolución de estados x(t) y salidas y(t).',
 ('state_space','frequency'): 'Matrices A, B, C y D → respuesta de cada canal según la frecuencia.',
 ('state_space','discretize'): 'Modelo continuo y período de muestreo → matrices de un modelo discreto.',
 ('state_space','transfer'): 'Matrices y par entrada/salida → función de transferencia de ese canal.',
 ('systems',0): 'Tipo de filtro, frecuencias y cantidad de coeficientes → filtro FIR.',
 ('systems',1): 'Frecuencia y factor Q → filtro digital de segundo orden.',
 ('systems',2): 'Resistencia y capacitancia → circuito RC y su transferencia.',
 ('systems',3): 'Numerador, denominador y dominio → definición de un sistema.',
 ('systems',4): 'Coeficientes del sistema y rango de frecuencias → módulo y fase.',
 ('systems',5): 'Sistema digital y entrada → señal filtrada o respuesta al impulso/escalón.',
 ('systems',6): 'Ceros, polos y ganancia → sistema y ubicación de sus raíces.',
 ('systems',7): 'Coeficientes de H(s) y período T → transferencia digital H(z).',
 ('systems',8): 'Frecuencia natural, amortiguamiento y ganancia → sistema de segundo orden.',
 ('systems',9): 'Sistema y entrada propia, escalón o impulso → respuesta temporal de estado cero.',
 ('systems',10): 'Coeficientes y ganancia → sistema con realimentación unitaria.',
 ('systems',11): 'Coeficientes y rango de ganancia → trayectoria de los polos.',
 ('sampling',0): 'Expresión continua y frecuencia de muestreo → muestras de la señal.',
 ('sampling',1): 'Frecuencias de señal y muestreo → interpretación del aliasing.',
 ('sampling',2): 'Secuencia y factor de cambio → nueva secuencia muestreada.',
 ('sampling',3): 'Muestras y método → aproximación de la señal entre muestras.',
 ('sampling',4): 'Señal y resolución → cuantización y relación señal/ruido.',
 ('sampling',5): 'Número, filtro o entrada → representación y ejecución con precisión finita.',
 ('basic','generate'): 'Fórmula o lista de valores → gráfico y tabla de muestras.',
 ('basic','dft'): 'Muestras temporales → espectro discreto de Fourier.',
 ('basic','idft'): 'Espectro discreto → muestras temporales.',
 ('basic','measures'): 'Secuencia finita → energía, potencia media y valor eficaz.',
 ('basic','shift'): 'Secuencia y desplazamiento → cambio del origen temporal.',
 ('basic','reverse'): 'Secuencia → inversión del eje temporal.',
 ('basic','scale'): 'Secuencia y factor → cambio de amplitud.',
 ('basic','parity'): 'Secuencia → descomposición en partes par e impar.',
}
KINDS = {
 'system_analysis':'Coeficientes exactos o numéricos → expresión algebraica y respuesta en frecuencia.',
 'signal_editor':'Ingresá o copiá muestras para editar sus valores y su eje.',
 'rational_resampling':'Secuencia y factores de tasa → remuestreo con filtro antialias.',
 'convolution_algebra':'Dos expresiones y sus intervalos → convolución algebraica.',
 'correlation_algebra':'Expresiones y sus intervalos → correlación algebraica.',
 'correlation':'Señales e intervalo de retardos → similitud según el desplazamiento.',
 'dtft_symbolic':'Expresión discreta → transformada de Fourier algebraica.',
 'fourier_symbolic':'Expresión e intervalo → transformada de Fourier o su inversa.',
 'expression_measures':'Expresión y alcance del cálculo → energía o potencia con sus condiciones.',
 'fourier':'Señal o coeficientes e intervalo → análisis o reconstrucción de Fourier.',
 'symbolic':'Expresiones y condiciones → resultado algebraico y alcance de validez.',
}
def describe_tool(item):
 _,kind,task,input_kind=item
 if (kind,task) in DETAILS:return DETAILS[kind,task]
 if kind in KINDS:return KINDS[kind]
 if input_kind in ('pair','continuous_pair'):return 'Dos señales definidas aquí → resultado de la operación elegida.'
 return 'Ingresá los datos en esta herramienta; reutilizar resultados anteriores es opcional.'

DETAILS[('random','generate')]='Distribución, parámetros y semilla → realización reproducible para analizar o filtrar.'
DETAILS[('random','statistics')]='Registro finito → media, varianza, RMS e histograma de amplitudes.'

DETAILS[('random_correlation',0)]='Registro y retardos → estimaciones de correlación o covarianza con divisor explícito.'

DETAILS[('time_transform',0)]='Señal continua y parámetros A, a, t₀ → amplitud, inversión, compresión, expansión y desplazamiento temporal.'

DETAILS[('interconnection',0)]='Dos transferencias del mismo dominio → sistema equivalente en cascada, paralelo o realimentación.'

DETAILS[("course_tools",'fft')]='Registro, ventana y NFFT independientes → DFT, DTFT, ventana y señal enventanada.'
DETAILS[("course_tools",'fir')]='Bandas y tolerancias → estimación Kaiser, FIR y evaluación de respuesta.'
DETAILS[("course_tools",'iir')]='Bandas y tolerancias → Butterworth, Chebyshev I/II o elíptico; también prototipo Butterworth convertido.'
DETAILS[("course_tools",'convert')]='H(s) o H(z) y T → conversión bilineal, inversa o invarianza al impulso.'
DETAILS[("course_tools",'gain')]='Sistema y frecuencia de referencia → módulo objetivo conservando polos y ceros.'
DETAILS[("course_tools",'phase')]='Transferencia discreta → reflexión de ceros, factor paso todo y clasificación FIR.'
DETAILS[("course_tools",'inverse_z')]='Transferencia y región de convergencia → muestras bilaterales por integración de contorno.'
DETAILS[("course_tools",'band')]='Espectro angular y banda → energía parcial por integración.'
DETAILS[("course_tools",'lines')]='Coeficientes de serie continua → pesos de líneas de PSD y potencia de Parseval.'
DETAILS[("course_tools",'mapping')]='Frecuencia angular y período → mapeo bilineal o ramas de aliasing.'

DETAILS[('frequency_filter',0)]='Definir H por tramos, ver su respuesta y aplicar el filtro a una señal.'

DETAILS[('fourier',6)]='Señal discreta, continua o espectro propio → densidad de energía y espectro exportables.'

DETAILS[('dsp_extensions','hilbert')]='Señal real → Hilbert, señal analítica y envolvente, con el mismo eje.'
DETAILS[('dsp_extensions','stft')]='Ventanas de una señal → espectrograma y espectros locales exportables.'
DETAILS[('dsp_extensions','blocks')]='Secuencias x[n] y h[n] → convolución completa por overlap-add u overlap-save.'

DETAILS[('course_tools','analog')]='Bandas en rad/s → Butterworth, Chebyshev o elíptico analógicos, comparables y reutilizables.'

DETAILS['course_tools','bandpass_sampling']='Banda en rad/s → intervalos de muestreo admisibles y evaluación de una tasa elegida.'

DETAILS['filter_lab',0]='Definir H(s)/H(z), diseñar FIR/IIR e ideales, editar polos y ceros, normalizar ganancia, convertir con ventanas y ver fase/retardo.'
DETAILS['transform_lab','z']='Directa e inversa algebraicas: x[n] y soporte → X(z); X(z) racional y ROC → x[n] y muestras.'
DETAILS['transform_lab','laplace']='Directa e inversa de Laplace por expresión, con interpretación unilateral o bilateral y región de convergencia.'

from .tool_groups import GROUPS
for _key,(_,_,_,_tabs) in GROUPS.items():DETAILS['tool_group',_key]='Opciones: '+ '; '.join(label for _,choices in _tabs for label,_ in choices)+'. Cada opción conserva sus entradas y resultados.'

DETAILS['inverse_dtft',0]='Recuperá x[n] desde un período de X(ω), en rad/muestra. La salida usa índices enteros, incluso negativos.'
DETAILS['dtft_symbolic',1]='Obtené la expresión de x[n] por propiedades o integración de un período, sin imponer causalidad.'

DETAILS['signal_product',0]='Multiplicar dos señales punto a punto: alineación de índices o instantes y salida reutilizable.'
DETAILS['fir_window',0]='Respuesta h[n] propia → ventana → FIR, respuesta en frecuencia, fase y retardo de grupo.'
