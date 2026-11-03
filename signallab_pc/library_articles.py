"""Authored explanations, separate from the field reference and release history."""
ARTICLES={}

def add(keys,purpose,load,result,conditions):
    if isinstance(keys[0],str):keys=[keys]
    for key in keys:ARTICLES[key]=[('Qué podés hacer',purpose),('Cómo preparar el cálculo',load),('Cómo interpretar la salida',result),('Qué tener en cuenta',conditions)]

add(('signal_editor',0),
'Esta herramienta permite modificar las muestras de una señal y la posición que ocupan en su eje. La edición produce una nueva salida, por lo que podés conservar la señal de entrada.',
'Elegí una señal discreta o continua muestreada y cargala desde una fórmula, una lista, un archivo o un resultado. Abrí la tabla para cambiar las partes real e imaginaria. Si necesitás cambiar el eje, completá también el origen y, en continuo, el paso temporal.',
'Aplicar edición confirma juntos los valores, el nombre y el eje. La pestaña Resultado muestra la versión aplicada y permite exportarla o enviarla a otra herramienta.',
'Si seguís editando, esos cambios quedan pendientes hasta volver a aplicar. Los impulsos Dirac tienen posición y peso propios: no se editan como muestras de altura finita.')
add(('basic','generate'),
'Podés crear una señal a partir de su fórmula o de una lista de valores. El eje indica dónde está cada valor y forma parte de la definición de la señal.',
'Elegí tiempo discreto para escribir una expresión en n, o tiempo continuo para usar t. Luego indicá el inicio y cuántos valores querés obtener; en continuo, completá el paso. Para una función por tramos, escribí el valor y la condición en cada fila.',
'Al calcular obtenés una señal con gráfico y tabla. Por ejemplo, cos(pi*n/4), con inicio 0 y cantidad 9, genera las muestras n=0,…,8. Esa salida se puede reutilizar sin volver a escribir la fórmula.',
'Cantidad es el número de valores, no el último índice. El registro generado describe el intervalo elegido; no determina por sí solo qué ocurre fuera de él.')
add(('time_transform',0),
'Podés desplazar, invertir, comprimir o expandir una señal continua, y cambiar su amplitud mediante y(t)=A·x(a·(t−t₀)).',
'Cargá x(t) y elegí A, a y t₀. A multiplica las amplitudes; a cambia la escala temporal y, si es negativo, invierte el eje. Después de ese cambio de escala, t₀ desplaza la señal.',
'Por ejemplo, para obtener x(2t−4), usá a=2 y t₀=2. Cada punto ubicado en τ pasa a τ/a+t₀. Las pestañas de entrada y salida permiten comparar ambos ejes.',
'a debe ser distinto de cero. La transformación conserva el intervalo disponible y no inventa valores fuera de él. Cuando hay Dirac, se transforma también su peso.')
add(('basic','measures'),
'Esta opción mide energía, potencia media y valor eficaz de un registro. Las tres medidas se basan en el módulo al cuadrado, por lo que también sirven para señales complejas.',
'Cargá las muestras y calculá. En discreto, la energía es la suma de |x[n]|²; la potencia media del registro divide esa suma por N, y el valor eficaz o RMS es su raíz cuadrada.',
'El informe indica el intervalo o los índices usados. En un registro continuo, se integra el modelo lineal entre muestras en lugar de tratar cada valor como una muestra discreta sin duración.',
'Estas medidas corresponden al registro cargado. Para conocer la potencia de una señal periódica completa, el registro debe representar períodos completos; para estudiar todo el eje, usá las medidas por expresión.')
for task,scope in [('interval','el intervalo que elijas'),('global','todo el eje'),('periodic','un período de la señal')]:
    add(('expression_measures',task),
    'Podés medir energía o potencia directamente desde una expresión, sin reducirla primero a una tabla de muestras. Esta opción trabaja sobre '+scope+'.',
    'Elegí el dominio y definí la señal por fórmula o tramos. Para un intervalo, indicá sus extremos; para una señal periódica, indicá un período positivo. En el análisis global, incluí el soporte de la señal en la expresión.',
    'Leé la medida junto con las condiciones que devuelve el cálculo. Si se ofrece una aproximación numérica, sirve para contrastar la expresión en una ventana finita.',
    'Una integral o suma pendiente no equivale a una respuesta cerrada. Tampoco se demuestra convergencia en todo el eje observando sólo una ventana numérica.')
add(('basic','shift'),'Un desplazamiento cambia los índices de la señal sin cambiar sus amplitudes. Para y[n]=x[n−k], un k positivo mueve la señal hacia índices mayores.',
'Cargá la secuencia y el desplazamiento entero k. El programa conserva la lista de valores y cambia su origen.',
'Compará el primer y el último índice de entrada y salida. Por ejemplo, una señal que comienza en n=−2 pasa a comenzar en n=1 si k=3.',
'Si la señal tiene un reloj físico registrado, el inicio temporal también se ajusta en k/Fs. El desplazamiento se interpreta respecto de n=0.')
add(('basic','reverse'),'La inversión temporal produce y[n]=x[−n]. Cambia el orden de los valores y refleja sus posiciones respecto de n=0.',
'Cargá la secuencia y calculá. No necesitás reordenar manualmente las muestras ni cambiar su origen antes de hacerlo.',
'Una muestra que estaba en n=3 aparece en n=−3. Por eso, para interpretar la salida, mirá sus índices además de la lista de amplitudes.',
'Si existe un reloj físico, el instante asociado a n=0 puede ser distinto de t=0. El programa conserva esa referencia al reflejar el eje.')
add(('basic','scale'),'El cambio de amplitud multiplica una señal por un factor A y produce y=A·x.',
'Cargá la señal y escribí el factor. Un valor negativo invierte el signo; un factor complejo también puede cambiar la fase.',
'La salida conserva el eje de la entrada. Por ejemplo, A=2 duplica todas las amplitudes sin adelantar ni retrasar la señal.',
'Esta operación cambia amplitudes, no la escala temporal. Para comprimir o expandir el tiempo, usá la transformación temporal.')
add(('basic','parity'),'Toda secuencia puede separarse en una parte par, simétrica respecto de cero, y una parte impar, que cambia de signo al reflejarla.',
'Cargá x[n] y calculá. El programa combina x[n] con x[−n]: la semisuma da la parte par y la semidiferencia da la impar.',
'Al sumar las dos salidas se recupera la señal de entrada. Sus gráficos permiten reconocer qué rasgos son simétricos y cuáles son antisimétricos.',
'Para el registro finito se usa cero fuera de los índices cargados. Esa extensión influye en la descomposición cerca de sus extremos.')
add(('basic','sum'),'Esta operación suma dos señales respetando sus posiciones en el eje.',
'Definí las dos entradas por separado. En discreto, el programa alinea los índices y usa cero donde sólo una de las señales tiene muestras.',
'La amplitud de la salida en cada índice es la suma de las amplitudes presentes en ese índice. Dos listas iguales con orígenes distintos pueden producir una suma diferente.',
'Antes de comparar o combinar señales, revisá que sus dominios, pasos y unidades sean compatibles.')
add(('basic','convolve'),'La convolución lineal permite obtener la salida de un sistema LTI desde reposo cuando conocés su entrada x[n] y su respuesta al impulso h[n].',
'Cargá x y h con sus índices correctos. El cálculo combina sus productos desplazados y devuelve la convolución completa.',
'Si las longitudes son N y M, la salida tiene N+M−1 valores. Su origen es la suma de los orígenes de las entradas, de modo que los retardos se conservan.',
'Se supone cero fuera de ambos registros. Esta salida no incluye una respuesta debida a condiciones iniciales no nulas del sistema.')
add(('basic','circular'),'La convolución circular combina dos secuencias como si se repitieran con un período común. Los valores que sobrepasan el final vuelven al comienzo.',
'Cargá las dos listas. La herramienta completa la más corta con ceros hasta la longitud de la mayor y usa esa longitud como período.',
'La salida tiene un período de valores y comienza en índice cero. Comparala con la convolución lineal para reconocer los términos que se suman al volver al inicio.',
'La repetición circular puede superponer términos que estarían separados en la convolución lineal. Por eso ambas operaciones no son intercambiables sin completar adecuadamente con ceros.')
add(('basic','continuous_convolve'),'Esta opción aproxima la convolución de dos señales continuas a partir de registros muestreados.',
'Definí x(t) y h(t) con el mismo paso temporal. Completá los intervalos de ambas señales para incluir las partes que intervienen en la integral.',
'La salida aproxima y(t)=∫x(τ)h(t−τ)dτ. El informe explica el modelo usado entre muestras y el tratamiento de los extremos.',
'Se usa cero fuera de los registros disponibles. Reducir el paso o ampliar los intervalos permite estudiar la aproximación; los impulsos ideales se tratan por posición y peso cuando están presentes.')
add(('convolution_algebra',0),'Esta opción busca una expresión de la convolución continua, en lugar de evaluarla sólo sobre una tabla de puntos.',
'Ingresá x(t) y h(t). Elegí soporte causal si ambas señales son cero para t<0; si elegís cálculo bilateral, incluí los tramos del soporte en las expresiones.',
'El resultado relaciona la salida con el tiempo t y puede incluir condiciones de validez. Luego podés generar un registro numérico para representar una expresión resuelta.',
'Si el motor conserva una integral sin resolver, el cálculo queda indicado como pendiente. El intervalo usado para graficar no reemplaza los límites de la integral original.')
for task,domain in [(0,'discreta'),(1,'continua')]:
    add(('correlation',task),'La correlación '+domain+' permite comparar dos señales mientras una se desplaza respecto de la otra. Su eje de salida es el retardo.',
    'Cargá ambas señales, elegí los retardos que querés estudiar y la normalización disponible. Para una autocorrelación, usá la misma señal en las dos entradas.',
    'Un valor grande en cierto retardo indica una coincidencia fuerte con el desplazamiento definido por la convención del informe. En señales complejas se conjuga uno de los factores.',
    'El signo del retardo depende del orden de las entradas. Cerca de los extremos hay menos valores superpuestos; revisá el divisor y la extensión elegidos antes de comparar alturas.')
add(('correlation_algebra',0),'La correlación algebraica busca una expresión de la coincidencia entre dos señales continuas según el retardo τ.',
'Ingresá x(t) y h(t) con sus soportes. Dejá Período vacío para integrar en todo el eje, o indicá un período común positivo si ambas señales son periódicas.',
'Se integra x(t)·conj(h(t−τ)). El resultado depende de τ, no del tiempo de una señal de salida. En el caso periódico, la integral de un período no se divide automáticamente por su duración.',
'Leé las condiciones de convergencia y cualquier integral pendiente. No confundas esta integral con una correlación normalizada a un máximo de uno.')
add(('dsp_extensions','blocks'),'La convolución por bloques calcula la misma convolución lineal completa, procesando grupos de muestras mediante FFT.',
'Cargá x[n] y h[n], elegí solapamiento-suma u overlap-add, o solapamiento-almacenamiento u overlap-save. Después indicá cuántas muestras nuevas procesar por bloque.',
'El informe describe cómo se combinan los bloques. La salida incluye la cola final de la convolución y debe representar el mismo resultado que el cálculo lineal directo.',
'El tamaño de bloque organiza el cálculo; no cambia el sistema definido por h[n]. Se usa extensión por ceros, no repetición periódica de la señal completa.')
add(('basic','dft'),'La DFT representa N muestras temporales mediante N coeficientes complejos de frecuencia. La FFT es una forma rápida de calcular esa misma transformada.',
'Cargá las N muestras en orden temporal y calculá. La transformada directa usa la suma sin dividir por N.',
'Los índices k=0,…,N−1 corresponden a frecuencias separadas por 2π/N rad/muestra. El módulo muestra amplitudes espectrales y la fase conserva la referencia temporal indicada por la herramienta.',
'Los coeficientes no son una curva continua de frecuencia. Para recuperar las muestras usá la DFT inversa, que aplica el factor 1/N.')
add(('basic','idft'),'La DFT inversa recupera una secuencia a partir de sus N coeficientes de frecuencia.',
'Ingresá X[0],…,X[N−1] en ese orden o copiá una DFT anterior. Podés escribir coeficientes complejos, como 1+2*i.',
'El cálculo aplica el factor 1/N y devuelve un período de N muestras desde n=0. Si los coeficientes pertenecen a una señal real, las pequeñas partes imaginarias residuales pueden deberse al redondeo.',
'Respetá el orden completo de los coeficientes. Ingresar sólo sus módulos pierde la información de fase y, en general, no permite recuperar la señal original.')
add(('fourier',0),'La DTFT describe una secuencia mediante una función continua de la frecuencia. Esta herramienta también permite superponer las muestras de una DFT sobre esa curva.',
'Cargá la secuencia con su índice inicial y elegí el intervalo de frecuencias en rad/muestra. Puntos determina cuántas evaluaciones dibujan la DTFT; la DFT usa sus propias frecuencias.',
'Al activar la superposición se conserva la DTFT del cálculo individual. La curva representa la DTFT y los tallos representan la DFT; ambas respetan el origen de la señal.',
'El espectro discreto es periódico cada 2π. Si el intervalo supera un período, las muestras espectrales se repiten. La fase desenrollada y el retardo de las vistas ampliadas corresponden a la DTFT.')
add(('dtft_symbolic',0),'Podés obtener una expresión de la DTFT de una secuencia, incluyendo secuencias definidas sobre infinitos índices cuando la suma converge.',
'Ingresá x[n] y los límites de su suma; se admiten −oo y oo. Después de obtener una expresión, elegí el intervalo de frecuencia y los puntos para verla como curva.',
'La expresión describe la frecuencia angular en rad/muestra. Las condiciones del resultado indican cuándo tiene sentido la suma o si el motor dejó parte del cálculo pendiente.',
'Los extremos usados para dibujar no cambian los límites de la suma. Una expresión pendiente o con distribuciones no debe interpretarse como una tabla ordinaria de amplitudes finitas.')
add(('fourier',1),'Esta herramienta aproxima el espectro de una señal continua a partir del registro temporal que cargues.',
'Definí la señal y su intervalo temporal. Luego elegí el rango de frecuencias en rad/s y la cantidad de evaluaciones del espectro.',
'El resultado aproxima la integral de Fourier sobre el registro disponible. Una ventana temporal más amplia puede incluir partes de la señal que un registro corto dejaba afuera.',
'La separación de los puntos temporales y el truncamiento influyen en el resultado. Los Dirac se incorporan mediante sus pesos y posiciones, no como picos de altura finita.')
add(('fourier',3),'La Fourier inversa continua reconstruye una aproximación temporal a partir de un espectro X(Ω).',
'Ingresá el espectro por fórmula en w o por muestras complejas. Indicá su origen y paso en rad/s y, después, el intervalo temporal que querés obtener.',
'Se aproxima la integral inversa con factor 1/(2π). La salida depende tanto de los valores del espectro como de la banda de frecuencia disponible.',
'Si faltan frecuencias, la reconstrucción puede cambiar aunque el intervalo temporal sea amplio. Una densidad de potencia o de energía no sustituye al espectro complejo X.')
for task,inverse in [(0,False),(1,True)]:
    add(('fourier_symbolic',task),
    'Esta opción busca una expresión de '+('la señal temporal a partir de su espectro.' if inverse else 'la transformada de Fourier continua.'),
    'Ingresá '+('X(w) usando w como frecuencia angular.' if inverse else 'x(t), incluyendo su soporte mediante tramos cuando corresponda.')+' Calculá primero la expresión. Los controles de inicio, final y cantidad permiten después generar un registro para graficarla.',
    'Leé la fórmula junto con sus condiciones. Un resultado puede incluir impulsos ideales o una operación que el motor no terminó de resolver.',
    'El intervalo de dibujo no es un límite de integración de la transformada. Los impulsos se interpretan por su posición y peso, y no como alturas finitas de una curva.')
for task,continuous in [(4,True),(5,False)]:
    add(('fourier',task),'La serie de Fourier describe una señal periódica mediante coeficientes de sus armónicos. El análisis obtiene esos coeficientes y la síntesis combina los disponibles para reconstruir la señal.',
    ('Para analizar, definí un período de x(t), su duración T, los puntos de evaluación y los armónicos deseados. Para sintetizar, cargá c[k] con sus índices y T, o copiá coeficientes anteriores.' if continuous else 'Para analizar, cargá un período completo de N muestras. Para sintetizar, cargá c[0],…,c[N−1] desde índice cero, o copiá una serie anterior con su origen registrado.'),
    ('El coeficiente k corresponde a la frecuencia k·2π/T. Si sintetizás con pocos armónicos, obtenés una aproximación que permite estudiar el efecto del truncamiento.' if continuous else 'Los coeficientes del análisis se dividen por N. La síntesis manual devuelve un período desde n=0; una serie importada conserva la referencia de origen que trae.'),
    'No hace falta calcular una serie antes de usar la síntesis: los coeficientes también se pueden cargar manualmente. Un conjunto incompleto de armónicos no contiene toda la información de la señal periódica original.')
add(('fourier',6),'La densidad espectral de energía muestra cómo se distribuye la energía de una señal entre las frecuencias. Se calcula como |X|² a partir de su espectro complejo.',
'Podés partir de una señal discreta, una señal continua o un espectro propio. Cargá aquí la fórmula o las muestras; para una señal, elegí también el intervalo de frecuencia y sus puntos. El cálculo obtiene X y su densidad en una sola operación.',
'El selector permite consultar y exportar ambos resultados. El informe integra la banda mostrada y, cuando corresponde, la compara con la energía temporal mediante Parseval.',
'En discreto, la integral de un período completo de 2π usa el factor 1/(2π). Para N muestras, usá al menos N+1 puntos al integrar la DTFT de ese período. Una DFT completa permite usar Σ|X[k]|²/N. No ingreses una densidad ya calculada ni pesos de Dirac como si fueran X.')
add(('fourier',7),'La densidad espectral de potencia, o PSD, estima cómo se reparte la potencia de un registro entre las frecuencias.',
'Cargá la señal y su tasa Fs. Elegí periodograma o Welch y una ventana; para Welch, indicá también el tamaño de segmento y su solapamiento. Quitar la media permite estudiar las fluctuaciones alrededor del promedio.',
'Welch promedia estimaciones de varios segmentos, lo que reduce sus fluctuaciones a costa de resolución en frecuencia. El informe indica las unidades del eje y la normalización de la densidad bilateral.',
'La potencia de una banda se obtiene integrando la densidad con la convención indicada, no leyendo una sola altura. La estimación de un registro no prueba que el proceso sea estacionario.')
add(('course_tools','fft'),'Esta herramienta reúne la FFT, las ventanas y la comparación con DTFT para analizar un registro discreto.',
'Definí la secuencia y elegí cuántas muestras observar con L. NFFT debe ser al menos L; si es mayor, el cálculo completa con ceros. Elegí la ventana y, si usás Kaiser, su parámetro β.',
'El selector muestra la señal, la ventana y los espectros. Al superponer DFT y DTFT, los tallos son muestras de frecuencia y la curva es la DTFT del mismo registro con su ventana. Podés conservar una curva de referencia para compararla con otro cálculo.',
'Completar con ceros agrega puntos al espectro, pero no información ni capacidad de separar tonos que el registro no resuelve. La FFT directa no se divide por N; el informe indica la comparación de energía usada.')
add(('course_tools','band'),'Esta opción calcula qué parte de la energía corresponde a una banda de frecuencias.',
'Ingresá el espectro complejo X o copiá una transformada anterior. Elegí dos extremos dentro del eje disponible; la entrada debe ser el espectro, no |X|² ni una PSD.',
'Se integra |X|²/(2π) entre esos extremos mediante trapecios. Una banda positiva no se duplica automáticamente para representar la banda negativa.',
'En discreto, un período completo de 2π permite comparar con la energía temporal. En continuo, una banda finita sólo contiene la energía de esa banda; no demuestra que fuera de ella la energía sea nula.')
add(('course_tools','lines'),'Una señal periódica concentra su potencia en líneas ubicadas en las frecuencias de sus armónicos.',
'Cargá los coeficientes c[k] de una serie continua con sus índices y período T, o copiá una serie calculada.',
'El resultado ubica cada línea en k·2π/T y le asigna el peso 2π|c[k]|². La suma Σ|c[k]|² da la potencia aportada por los armónicos cargados.',
'Los tallos representan pesos de impulsos ideales de frecuencia, no alturas finitas de una densidad ordinaria. Si cargás sólo algunos armónicos, su suma no es necesariamente la potencia total.')
add(('dsp_extensions','hilbert'),'La transformada de Hilbert permite construir la señal analítica de una entrada real. A partir de ella también se obtiene su envolvente.',
'Elegí el dominio y cargá una señal real. Calculá y usá el selector para consultar Hilbert, señal analítica o envolvente.',
'La señal analítica combina la entrada con su transformada de Hilbert como parte imaginaria. Su módulo es la envolvente; cada salida conserva el mismo eje temporal y se puede exportar.',
'El cálculo mediante FFT supone una extensión periódica del registro. Por eso los extremos pueden mostrar efectos que dependen de cómo termina y comienza la señal.')
add(('dsp_extensions','stft'),'La STFT muestra cómo cambia el contenido de frecuencia al recorrer una señal con ventanas temporales.',
'Cargá la señal y elegí longitud de ventana, solapamiento y cantidad de puntos FFT. Luego calculá el espectrograma.',
'Cada columna corresponde a una ventana temporal. Podés elegir una de ellas para consultar su espectro o exportar la STFT completa con sus valores complejos, ejes y parámetros.',
'Una ventana corta localiza mejor los cambios en el tiempo y una larga distingue mejor frecuencias cercanas. El nivel mostrado es relativo; no se presenta como una PSD calibrada.')
add(('frequency_filter',0),'Podés definir un filtro por su respuesta en frecuencia H, por ejemplo un pasa bajos ideal, sin convertirlo primero en coeficientes de una transferencia racional.',
'Elegí continuo o discreto y cargá los tramos con las columnas Valor y Cuando; w es la frecuencia angular. En discreto, definí un período entre −π y π. En continuo, elegí una banda que represente el soporte del modelo.',
'Calcular muestra H y una aproximación de su respuesta al impulso h. Para obtener la salida de una señal, activá Aplicar a una señal y cargá esa entrada. El selector permite consultar H, h, X, Y e y.',
'Un corte ideal puede exigir una respuesta temporal infinita y no causal. La inversión numérica y el tramo de h mostrado no convierten ese modelo en un FIR o IIR finito exacto.')
add(('system_analysis',0),'Esta herramienta reúne las distintas formas de estudiar una misma transferencia: expresión, respuesta en frecuencia, polos y ceros, y realización con integradores o retardos.',
'Elegí H(s) para continuo o H(z) para discreto. Ingresá la fórmula o los coeficientes; en continuo se ordenan por potencias descendentes de s, y en discreto por 1,z⁻¹,z⁻²,… Luego elegí el intervalo de frecuencia: rad/s para continuo o rad/muestra para discreto.',
'Después de analizar, las pestañas muestran módulo, fase, retardo, raíces y realización del mismo resultado. La realización puede enviar sus matrices a Espacio de estados. Usar sistema en permite continuar con otra herramienta sin volver a cargar la definición.',
'Los parámetros libres necesitan valores para las vistas numéricas. Un avance de H(z) se conserva en módulo, fase, retardo, raíces y exportación del sistema, y se puede enviar a Z inversa para elegir una ROC. Una cadena causal de retardos no realiza ese avance y una H(s) impropia necesita derivadores. La evaluación algebraica en el círculo unidad es una respuesta DTFT cuando la ROC contiene ese círculo. Los márgenes opcionales estudian cruces locales bajo las hipótesis indicadas y no certifican por sí solos estabilidad.')
add(('interconnection',0),'Podés obtener la transferencia equivalente de dos sistemas conectados en cascada, en paralelo o mediante realimentación.',
'Elegí un dominio común y cargá H₁ y H₂ en sus pestañas. Cada bloque admite fórmula racional, coeficientes o Cargar sistema para abrir un JSON o copiar un resultado anterior. En la realimentación, H₁ representa el camino directo y H₂ el retorno. La conexión negativa usa H₁/(1+H₁H₂); la positiva cambia ese signo por menos.',
'La salida es la transferencia entre la entrada y la salida externas de la conexión. Podés analizarla o exportarla y, si es causal, simularla. Las potencias positivas y negativas de z se conservan al combinar los bloques. Una cascada digital conserva las secciones SOS recibidas. Si editás los datos, el resultado anterior permanece disponible hasta que calcules otra vez.',
'Se suponen estados iniciales nulos. La estabilidad de la transferencia externa no siempre muestra todos los modos internos. Un denominador idénticamente nulo no define un sistema; el cálculo también informa si una representación pierde precisión.')
add(('systems',0),'Podés diseñar un FIR eligiendo sus cortes y la cantidad de coeficientes. La ventana suaviza el truncamiento de la respuesta ideal.',
'Elegí pasa bajos, pasa altos, pasa banda o rechaza banda. Ingresá los cortes entre 0 y π rad/muestra, la longitud y la ventana; Kaiser requiere además β.',
'El resultado contiene los coeficientes y la respuesta del filtro. Compará su transición y sus ondulaciones al cambiar longitud o ventana.',
'Los cortes no son los límites garantizados de las bandas de paso y rechazo. Si querés cargar tolerancias y bordes de esas bandas, usá la variante FIR por especificaciones del mismo diseño de filtros.')
add(('systems',1),'Una sección biquad es un filtro digital de segundo orden que se define mediante pocos parámetros.',
'Elegí su tipo, una frecuencia ω₀ entre 0 y π rad/muestra y un factor Q positivo. Luego calculá la sección.',
'La transferencia y su respuesta permiten ver cómo Q cambia la forma alrededor de ω₀. Podés reutilizar la sección como cualquier otro filtro digital.',
'La definición de ganancia depende del tipo elegido. En el pasabanda implementado, la ganancia de pico es Q; no se supone un pico unitario para todos los tipos.')
add(('systems',2),'Esta herramienta relaciona los componentes de un circuito RC ideal con su respuesta pasa bajos o pasa altos.',
'Elegí si conocés R y C o si querés obtener uno a partir de la frecuencia de corte. Ingresá resistencia en ohmios y capacitancia en faradios, respetando la unidad indicada para la frecuencia.',
'La salida muestra el valor calculado y la transferencia del modelo. Cuando se permiten varias etapas, se interpretan como etapas ideales en cascada.',
'El cálculo de un componente a partir del corte corresponde a una etapa. La cascada ideal no modela el efecto de carga que un circuito físico puede introducir entre etapas.')
add(('systems',8),'El modelo de segundo orden permite estudiar cómo la frecuencia natural y el amortiguamiento cambian la respuesta de un sistema.',
'Ingresá ωn en rad/s, el amortiguamiento ζ y la ganancia K. La transferencia usada es K·ωn²/(s²+2ζωn·s+ωn²).',
'El resultado se puede enviar a respuesta temporal para comparar oscilaciones y tiempo de establecimiento, o al análisis para estudiar frecuencia y polos.',
'La frecuencia natural no coincide necesariamente con la frecuencia del máximo de resonancia. El modelo describe la transferencia indicada, sin incluir dinámicas adicionales del sistema físico.')
add(('systems',6),'Podés diseñar un sistema ubicando sus polos y ceros en el plano s o z y eligiendo la ganancia.',
'Elegí el dominio. A la izquierda, Agregar polo o cero permite elegir el tipo de raíz y cargarla en forma binómica (parte real e imaginaria) o polar (módulo y ángulo en radianes). Agregar a la lista incorpora el punto y su conjugado si esa opción está marcada. La tabla muestra cada raíz por separado: doble clic corrige su expresión y Quitar seleccionados elimina sólo las filas elegidas. Calcular actualiza H y la respuesta en frecuencia. El plano conserva las acciones con el mouse y su propio selector de coordenadas, independiente del formato de carga.',
'Al actualizar el diseño se calculan la transferencia, el plano y la pestaña Respuesta en frecuencia, con módulo lineal o dB, fase y retardo de grupo. Podés cambiar el intervalo y exportar la respuesta sin salir del diseño. Los gráficos se abren aparte y se actualizan al editar puntos. Usar filtro en incluye Análisis de sistemas para continuar con la misma definición.',
'El modo de pares conjugados ayuda a mantener coeficientes reales. Más ceros que polos en H(z) puede requerir avances: el diseño los conserva mediante un factor z^m y permite analizarlo, sin añadir polos artificiales en el origen ni convertirlo en un retardo. La estabilidad y la secuencia bilateral dependen también de la región de convergencia. Para obtener muestras no causales, enviá el sistema a Transformada Z inversa y elegí la ROC.')
add(('course_tools','fir'),'El diseño por especificaciones busca un FIR que deje pasar ciertas bandas y atenúe otras dentro de las tolerancias que indiques.',
'Elegí el tipo de filtro y completá los bordes siguiendo el dibujo de izquierda a derecha, con un valor por casilla entre 0 y π rad/muestra. δp indica el error permitido en paso y δs el máximo permitido en rechazo; ambos son amplitudes lineales, no dB.',
'La respuesta se compara con las bandas originales. Kaiser estima la longitud usando la menor tolerancia y el menor ancho de transición, no el ancho de la banda de paso. Cada corte se ubica en el centro de su transición.',
'La estimación puede necesitar ajuste: revisá el cumplimiento informado. Una búsqueda de longitud devuelve la primera que cumple en los puntos evaluados para esa familia y esos cortes; no demuestra un mínimo global ni garantiza lo que ocurre entre puntos. Las transiciones no tienen restricciones de amplitud en esta especificación.')
add(('course_tools','iir'),'Podés diseñar un IIR que cumpla bandas y tolerancias, y comparar Butterworth, Chebyshev I, Chebyshev II y elíptico.',
'Completá los bordes en orden creciente entre 0 y π rad/muestra y las tolerancias lineales δp y δs. Elegí una familia o la comparación de las cuatro. Las conversiones de un prototipo analógico de esta variante corresponden a Butterworth.',
'Butterworth no tiene ondulación; Chebyshev I la permite en paso, Chebyshev II en rechazo y el elíptico en ambas bandas. Compará también fase y retardo, además del orden. El filtro seleccionado determina qué se exporta o se envía.',
'Las familias digitales conservan secciones de segundo orden para mejorar el cálculo numérico. La invarianza al impulso puede introducir aliasing y debe comprobarse contra las tolerancias digitales. La evaluación en una rejilla no garantiza el máximo entre todos sus puntos.')
add(('course_tools','analog'),'Esta variante diseña filtros analógicos a partir de sus bandas de paso y rechazo.',
'Elegí el tipo y completá los bordes positivos en rad/s siguiendo el dibujo. Cargá las tolerancias como amplitudes lineales y elegí una familia o la comparación.',
'El informe distingue el prototipo del filtro transformado y muestra el orden de cada diseño. En pasabanda o rechazabanda el orden puede duplicarse respecto del prototipo.',
'El sistema elegido se puede exportar o convertir a digital. Las tolerancias de amplitud no determinan por sí solas la fase ni la respuesta temporal; conviene estudiar esas vistas del resultado.')
add(('course_tools','convert'),'Esta herramienta relaciona un modelo analógico y uno digital mediante un método de conversión y un período T.',
'Definí o copiá el sistema y elegí el método compatible con su dominio. Para una respuesta ideal definida en frecuencia, usá sus tramos y los parámetros de ventana que solicita esa modalidad.',
'La bilineal usa s=(2/T)(z−1)/(z+1), por lo que cambia la correspondencia entre frecuencias. La invarianza al impulso usa h[n]=T·hc(nT) y puede sumar réplicas espectrales. El resultado calculado se puede analizar y reutilizar.',
'No se predeforma automáticamente un borde en esta conversión. La invarianza racional exige un sistema estrictamente propio. Su inversa no es única: los candidatos dependen de la rama y la opción implementada rechaza, entre otros casos, polos múltiples o nulos. Una respuesta ideal aproximada por ventana no se convierte en un filtro ideal finito exacto.')
add(('course_tools','gain'),'Esta opción escala un sistema para que alcance un módulo elegido en una frecuencia de referencia.',
'Cargá H, la frecuencia y el módulo objetivo. Usá rad/s para continuo o rad/muestra para discreto; el objetivo es una amplitud lineal.',
'El numerador se multiplica por objetivo/|H| en esa frecuencia. La operación cambia la ganancia y conserva la ubicación de los polos y ceros finitos no degenerados.',
'No es posible obtener una ganancia no nula en un cero mediante un factor finito, ni normalizar sobre una singularidad. Revisá el resto de la banda: ajustar un punto no garantiza una respuesta plana.')
add(('course_tools','phase'),'Esta herramienta reúne tres estudios: separar factores de H(z), compensar su respuesta con un FIR y reconstruir módulo/fase bajo una hipótesis de fase mínima. Los dos primeros usan una transferencia conocida; la reconstrucción parte de datos propios y no exige cargar H.',
'En Reconstruir elegí módulo lineal, módulo en dB o fase desenrollada. La fórmula o lista cubre −π…π con ambos extremos; para archivos se acepta un período completo de 2π o datos 0…π si indicás simetría de un sistema real. Un desplazamiento positivo agrega retardo y uno negativo agrega avance. Si partís de la fase, indicá además un módulo conocido en frecuencia cero para fijar la escala.',
'El logaritmo de la respuesta relaciona módulo y fase cuando su cepstrum es causal: sus coeficientes son la transformada inversa del logaritmo del espectro. El estudio construye ese modelo y entrega H compleja y una aproximación temporal. Un piso positivo evita logaritmos de cero, pero modifica los datos: el informe lo cuenta. Las figuras muestran fase desenrollada y retardo del modelo; el CSV conserva las curvas y H se puede usar en filtros definidos en frecuencia.',
'El módulo no revela retardos ni factores paso todo, y la fase sola no fija la ganancia. Otra banda parcial no basta sin hipótesis adicionales; la resolución y el modelo de interpolación importan. El registro h[n] tiene aliasing temporal y no se presenta como un FIR exacto. Factorizar y compensar siguen disponibles; esta opción numérica discreta no equivale a una reconstrucción analógica general.')
add(('systems',9),'Esta herramienta calcula cómo responde un sistema a un impulso, un escalón o una entrada propia.',
'Definí H por fórmula o coeficientes y elegí el tipo de entrada. Para una entrada propia, su eje fija el intervalo de salida. En continuo elegí cómo se interpola entre muestras; para impulso o escalón completá la duración o cantidad solicitada.',
'Las pestañas permiten comparar entrada y salida. En discreto también podés cargar valores anteriores de x e y para separar respuesta total, de estado cero y de entrada cero.',
'Sin historial, el sistema parte del reposo al inicio del registro, que no tiene por qué ser t=0. Si necesitás ver la cola, extendé la entrada con ceros. Una Dirac continua se carga por peso; el impulso discreto es una muestra unitaria.')
for task,explanation,load,reading in [
('analysis','estudiar la estabilidad interna y qué estados se pueden alcanzar o distinguir','Completá las matrices y elegí el dominio','El rango de controlabilidad indica cuántas direcciones del estado pueden alcanzarse desde las entradas. El de observabilidad indica cuántas pueden distinguirse a partir de las salidas'),
('simulation','obtener la evolución de estados y salidas','Completá matrices, estado inicial y una entrada por canal, separadas por punto y coma; elegí además el paso temporal','La simulación conserva entradas, estados y salidas. En continuo, la entrada se mantiene constante entre puntos, como una retención de orden cero'),
('frequency','evaluar cada canal entrada/salida según la frecuencia','Completá matrices, dominio, intervalo de frecuencia en rad/s y cantidad de puntos; en discreto indicá también T','Cada canal relaciona una entrada con una salida. En discreto se evalúa z=exp(iΩT), por lo que el eje físico está en rad/s, no en rad/muestra'),
('discretize','obtener un modelo discreto a partir de uno continuo','Cargá A, B, C y D continuas, un período T positivo en segundos y el método','ZOH supone entrada constante durante cada intervalo. Tustin aplica la transformación bilineal; también están disponibles los métodos Euler indicados en el selector'),
('transfer','obtener la transferencia entre una entrada y una salida','Cargá el modelo y elegí los números de entrada y salida desde 1','La transferencia obtenida describe ese canal externo y se puede reutilizar como H(s) o H(z)')]:
    add(('state_space',task),'El modelo de estados describe la evolución interna con A y B, y forma las salidas con C y D. Esta opción permite '+explanation+'.',load+'. A es estados×estados, B estados×entradas, C salidas×estados y D salidas×entradas.',reading+'.','El orden de las filas define el orden del estado inicial. Los rangos y coeficientes calculados son numéricos y pueden depender del redondeo; una transferencia de un canal puede ocultar modos internos del modelo.')
add(('rational_resampling',0),'El cambio racional de tasa convierte una secuencia para que su nueva tasa sea Fs·L/M, usando un filtro para limitar aliasing.',
'Cargá la secuencia y los enteros positivos L y M. Elegí el filtro y el tratamiento de los extremos disponibles.',
'La interpolación, el filtrado y la reducción se combinan para obtener la nueva secuencia. El informe conserva la relación entre las tasas.',
'Cambiar la tasa no agrega información que no estaba en la entrada. La extensión elegida puede afectar los valores cercanos a los extremos.')
add(('sampling',0),'Muestrear toma valores de una expresión continua cada T=1/Fs segundos.',
'Ingresá x(t), la tasa Fs en muestras/s, el instante inicial t₀ y la cantidad N. Por ejemplo, cos(2*pi*10*t) representa un tono de 10 Hz.',
'La salida es una secuencia con N muestras. La primera corresponde a t₀ y la última a t₀+(N−1)/Fs; ese reloj permite relacionar sus índices con el tiempo físico.',
'El muestreo no aplica por sí solo un filtro previo. Si la señal contiene frecuencias que se superponen después de muestrear, sus muestras pueden presentar aliasing.')
add(('sampling',1),'El aliasing hace que tonos continuos distintos produzcan las mismas muestras. Esta opción muestra esa ambigüedad para un tono.',
'Ingresá la frecuencia angular Ω del tono en rad/s y Fs en muestras/s. El límite de Nyquist en esas unidades es π·Fs rad/s.',
'El resultado muestra la frecuencia equivalente y una comparación con un coseno de fase cero. Los puntos discretos coinciden aunque las curvas continuas puedan ser diferentes.',
'La ilustración explica el caso de un tono. No demuestra que una señal cualquiera sea de banda limitada ni que pueda reconstruirse sólo por elegir una tasa alta.')
add(('sampling',2),'Estas operaciones cambian la posición o cantidad de muestras de forma elemental.',
'Cargá la secuencia y elegí el método y su factor entero. Diezmar toma una muestra de cada M con la fase local elegida; expandir inserta ceros; interpolar estima valores intermedios.',
'Compará el eje de salida con el de entrada para ver qué índices se conservan o se agregan.',
'La reducción elemental no filtra antes de eliminar muestras. Para una conversión con antialias, usá Cambiar tasa con antialias dentro de la misma familia de operaciones.')
add(('sampling',3),'Reconstruir permite estimar una señal continua entre sus muestras mediante una retención, rectas o interpolación SINC.',
'Cargá las muestras, Fs y el instante inicial. Puntos por intervalo controla cuántos valores se muestran entre dos muestras consecutivas.',
'La retención mantiene el valor hasta la próxima muestra; las rectas unen valores vecinos; SINC usa una combinación de funciones seno cardinal.',
'La reconstrucción se calcula entre la primera y la última muestra. Un registro finito y sus extremos influyen en la aproximación, y ningún interpolador recupera por sí solo la información perdida por aliasing.')
add(('sampling',4),'La cuantización reemplaza amplitudes por valores de un conjunto finito de niveles.',
'Cargá la señal y elegí bits, rango y regla de cuantización. Si querés medir la SNR sobre parte del registro, indicá el tramo permitido por la herramienta.',
'La salida incluye señal cuantizada, error, saturaciones y relación señal/ruido. Esto permite distinguir el efecto del paso entre niveles del error por superar el rango.',
'El error utilizado incluye la saturación y no se le resta automáticamente su media. Por eso la SNR debe interpretarse junto con el rango y las muestras evaluadas.')
add(('sampling',5),'Esta herramienta reúne la representación de números, el almacenamiento de coeficientes y el filtrado con precisión finita. Los tres estudios comparten formato, pero responden preguntas distintas: qué valor queda guardado, cómo cambia H(z) y qué ocurre al redondear durante la ejecución.',
'Elegí el estudio y el formato. Q usa bits enteros contando el signo, bits fraccionarios y redondeo o truncamiento. Los formatos flotantes ofrecen binary16/32/64 y empates al par. Para filtros, cargá H(z) por fórmula, coeficientes o un resultado anterior. Al filtrar, definí además x[n], las memorias iniciales y los ceros que querés añadir para observar la cola.',
'Representar un número entrega palabra, valor y error. Coeficientes compara Hq con H, sus polos y su frecuencia. Filtrar simula la forma II transpuesta, con SOS conservadas si existen. Compara la salida con el cálculo original y con otra referencia que ya tiene entrada, coeficientes y memoria cuantizados. Esa segunda comparación permite distinguir el error de ejecución del almacenamiento inicial. La salida se puede exportar o usar en otro menú.',
'En ejecución elegís redondear productos y sumas o sólo salida y memorias. Los bits extra amplían el rango del acumulador Q. Podés saturar o aplicar complemento a dos cíclico; los coeficientes Q se almacenan siempre con saturación y a[0]=1 es implícito. Un ciclo se confirma al repetirse exactamente el estado con entrada nula; un registro sin repeticiones no demuestra que no exista. El modelo flotante redondea valores y subnormales, pero no reproduce flags ni signo de cero de un procesador. Los desbordes flotantes detienen el cálculo conservando el último resultado válido.')
add(('course_tools','mapping'),'Esta opción relaciona la frecuencia analógica, la digital y el período de muestreo según el método elegido.',
'Elegí qué dato querés obtener y completá los restantes. Ω usa rad/s, ω usa rad/muestra y T usa segundos positivos.',
'La bilineal relaciona Ω=(2/T)tan(ω/2). En muestreo, ω coincide con ΩT módulo 2π, por lo que al invertir esa relación hay que elegir una rama entera.',
'Las ramas representan distintas frecuencias analógicas que producen la misma frecuencia discreta. Esta relación de ejes no convierte una respuesta ideal no racional en una transferencia finita exacta.')
add(('course_tools','bandpass_sampling'),'Una señal pasabanda puede admitir tasas de muestreo menores que las exigidas por su frecuencia más alta, si las réplicas de sus bandas no se superponen.',
'Cargá ΩL y ΩH, los extremos positivos de la banda en rad/s. El modelo supone una señal real, con otra banda reflejada en frecuencias negativas. Si querés evaluar una tasa, ingresá Ωs=2π·Fs.',
'La tabla y el gráfico muestran los intervalos admisibles y clasifican la tasa consultada. Cuando tiene margen, podés copiarla a Muestrear una expresión sin reemplazar la señal de ese destino.',
'Los extremos teóricos no dejan margen para transiciones de filtros reales. Cambiar los bordes requiere recalcular antes de exportar o reutilizar los nuevos intervalos.')
add(('symbolic',4),'Esta herramienta resuelve una ecuación diferencial lineal en la forma a₀y+a₁y′+…=f(t).',
'En Expresión ingresá sólo f(t), no la ecuación completa. Cargá los coeficientes en orden ascendente de derivadas y las condiciones y(0), y′(0),… que correspondan.',
'Por ejemplo, la lista 1,2,1 representa y+2y′+y″. La solución se muestra con las condiciones y el estado de evaluación del cálculo.',
'Este orden es distinto del de los polinomios de H(s). Si falta una condición, pueden quedar constantes libres; si el motor no resuelve una parte, se indica como pendiente.')
add(('transform_lab','laplace'),'Laplace relaciona una señal continua x(t) con X(s). La herramienta reúne la directa y la inversa, con interpretación unilateral o bilateral dentro del mismo formulario.',
'Elegí la operación y la interpretación. En la directa bilateral, escribí la señal completa con sus escalones o tramos. En la inversa bilateral, ingresá X(s) racional, opcionalmente multiplicada por exp(-d*s), y elegí una región de convergencia.',
'La ROC es la zona del plano s donde converge la integral. Una línea vertical dentro de ella permite decidir el soporte de cada término: los polos que quedan a su izquierda generan términos derechos y los de su derecha generan términos izquierdos. El programa calcula los bordes reales de la región a partir de esos polos. El dibujo muestra un caso con ambos soportes.',
'La fórmula obtenida incluye los coeficientes y los escalones. Un desplazamiento global mueve también los impulsos y sus derivadas. La misma X(s) con otra ROC puede describir otra señal. Una región vacía no constituye una transformada válida; un cálculo sin resolver se identifica como pendiente. Los modos de grado alto muestran los números evaluados dentro de la expresión y conservan la descomposición algebraica exacta. Copiar a la inversa conserva la ROC cuando se pudo determinar; Resultados permite reutilizar la expresión con sus condiciones.')
add(('transform_lab','z'),'La transformada Z relaciona una secuencia con una expresión en z. Para recuperar la secuencia, la expresión debe acompañarse de una región de convergencia.',
'En la directa podés usar una expresión con su soporte o un registro finito con sus índices. En la inversa racional, cargá X(z) y elegí la región que corresponde a la señal.',
'Una región exterior, interior o intermedia puede dar secuencias distintas para la misma fracción. La región se expresa mediante |z|; los controles de índices sólo eligen qué parte de la secuencia se muestra.',
'La descomposición racional conserva las raíces algebraicas para el cálculo. Cuando sus formas exactas serían demasiado largas, la fórmula muestra directamente los valores numéricos de polos y coeficientes, con al menos 17 cifras significativas. Los pares conjugados de una secuencia real se agrupan como senos y cosenos. La fórmula describe toda la secuencia; el intervalo elegido sólo controla las muestras que se muestran. Los parámetros sin asignar se conservan como símbolos.')
add(('course_tools','inverse_z'),'La inversa Z por contorno aproxima muestras de una secuencia a partir de su expresión racional y de una región de convergencia.',
'Cargá H(z) y elegí un contorno exterior, interior, sobre el círculo unidad o de radio manual. Indicá los índices de salida y los puntos de integración.',
'El cálculo evalúa H sobre un círculo y obtiene las muestras por integración numérica. Elegir otro anillo puede cambiar la secuencia aunque la fórmula sea igual.',
'El radio no puede atravesar polos. Para estudiar la aproximación, aumentá los puntos y compará radios dentro de la misma región. Esta opción no devuelve una fórmula algebraica exacta; para eso está la otra modalidad de la Transformada Z.')
add(('random','generate'),'Un proceso aleatorio describe muchas señales posibles; esta herramienta genera una de ellas, llamada realización.',
'Elegí distribución, cantidad de muestras y semilla. Gaussiana y uniforme usan media y desviación estándar; Bernoulli usa la probabilidad de obtener uno.',
'La salida es un registro que podés medir, filtrar o comparar. Usar la misma semilla y los mismos parámetros permite repetirlo.',
'La media y varianza medidas de un registro finito pueden diferir de los parámetros teóricos. Esa fluctuación no implica, por sí sola, un error de generación.')
add(('random','statistics'),'Esta opción resume las amplitudes de un registro mediante media, varianza, RMS e histograma.',
'Cargá la secuencia y elegí la componente del histograma y su cantidad de intervalos. Para datos complejos, distinguí parte real, imaginaria y módulo.',
'La varianza mide el promedio de |x−media|². El histograma agrupa amplitudes y estima una densidad: el área representa probabilidad, por lo que una altura puede superar uno.',
'La corrección con N−1 presupone muestras independientes e idénticamente distribuidas. Las medidas del registro y su histograma no prueban normalidad, estacionariedad ni independencia.')
add(('random_correlation',0),'La autocorrelación estima cómo se relaciona un registro con versiones desplazadas de sí mismo. Al restar su media, se estudia la autocovarianza.',
'Cargá el registro y elegí el retardo máximo y el divisor: N o la cantidad de pares N−|k|. Normalizar por el valor en cero cambia la escala del resultado.',
'En datos complejos se utiliza la conjugación indicada en el informe. Los retardos grandes usan menos pares, de modo que sus estimaciones suelen fluctuar más.',
'Dividir por el número de pares no garantiza eliminar el sesgo si la media también se estimó con el mismo registro. La curva finita no demuestra estacionariedad ni independencia del proceso.')

add(('random_model','model'),'Un modelo AR, MA o ARMA relaciona una entrada de ruido blanco con un proceso cuya evolución depende de coeficientes conocidos. Esta herramienta obtiene las estadísticas del modelo y permite generar una realización gaussiana estacionaria.',
'Elegí AR, MA o ARMA y cargá los coeficientes por potencias de z⁻¹. Para AR, b es 1; para MA, a es 1. Definí la media y la desviación del ruido, los retardos de interés y la rejilla espectral. También podés cargar un sistema digital desde archivo o Resultados.',
'El informe muestra la recurrencia, H(z), media, varianza y potencia del proceso. El selector ofrece autocovarianza, autocorrelación, densidad de potencia y la realización opcional. Cada salida se guarda por separado en Resultados; H(z) puede analizarse como cualquier otro sistema.',
'Se requiere un modelo real causal y estable. La inicialización usa la covarianza estacionaria, no reposo. El espectro continuo representa x−media; una media no nula agrega una línea ideal en cero que no se representa como una muestra finita.')
add(('random_model','fit'),'La estimación AR busca un modelo autorregresivo de orden elegido a partir de un registro. Permite describir su dependencia temporal y obtener un espectro paramétrico.',
'Cargá un registro discreto real y elegí p, menor que su cantidad de muestras. El cálculo resta la media muestral, estima la autocovarianza con divisor N y resuelve las ecuaciones de Yule–Walker. Las opciones de generación crean una realización nueva del modelo estimado.',
'La salida incluye H(z), los coeficientes AR, la varianza estimada de innovación, la autocorrelación y la densidad teóricas del modelo. También entrega el residuo válido: se omiten los primeros p índices porque no tienen todos sus antecedentes observados.',
'El orden elegido cambia el resultado. Las curvas son las del modelo ajustado; no son la densidad exacta del proceso desconocido. La varianza de innovación de Yule–Walker y el promedio cuadrático del residuo pueden diferir en un registro finito. No se certifican blancura ni independencia.')
add(('random_correlation',0),'Esta herramienta estima la relación de un registro con sí mismo o de dos registros entre sí. Al restar sus medias se obtiene covarianza en lugar de correlación.',
'Elegí Auto o Cruzada. En cruzada cargá x[n] e y[n] con sus índices reales: se usa el intervalo observado en ambos. Luego elegí retardo máximo, divisor N o N−|k| y normalización opcional. El programa no inventa datos en regiones sin observación.',
'Se representa Rxy[k]=promedio de x[n+k]·conj(y[n]). Un k positivo compara una muestra posterior de x con y. La autocorrelación en cero estima potencia; al centrar, varianza. La cruzada en cero no es una potencia y puede ser compleja; tampoco tiene por qué ser par.',
'La normalización cruzada divide por √(Px·Py) del intervalo común, o por el producto de desviaciones si se restaron medias. Con divisor N−|k|, la magnitud normalizada puede superar 1 en retardos grandes. No se demuestra independencia ni estacionariedad a partir de una curva finita.')

add(('difference_equation',0),'Esta herramienta resuelve ecuaciones lineales en diferencias de coeficientes constantes. En lugar de derivadas usa valores anteriores de la salida: a₀y[n]+a₁y[n−1]+…+aₚy[n−p]=f[n].',
'Cargá los coeficientes por retardos y escribí f[n] como fórmula o por tramos. Elegí el primer índice n₀. Si el sistema no estaba en reposo, desactivá Reposo y cargá y[n₀−1], y[n₀−2], …: son p valores anteriores, no las primeras p salidas que debe calcular el programa.',
'El informe presenta la solución en función de n y separa entrada cero de estado cero. La tabla y el gráfico muestran N valores desde n₀; aumentar N no cambia la fórmula. La solución y su transferencia con condiciones nulas quedan en Resultados y pueden enviarse al CAS u otras herramientas.',
'Se impone la ecuación sólo desde n₀ y no se inventa una historia infinita anterior. Para entradas polinómicas, exponenciales, senoidales y sus tramos de intervalos se utilizan propiedades de la Z unilateral. Cuando no se obtiene una forma cerrada para la entrada, se conserva la solución exacta como una suma finita de convolución y se informa ese alcance. Los parámetros sin asignar permiten conservar una fórmula, pero impiden generar muestras numéricas.')

add(('window_signal',0),'Podés generar las ventanas del diseño FIR como señales independientes. Así se puede estudiar su forma, su DTFT, su DFT o su transformada Z sin tener que crear primero un filtro.',
'En Señales → Crear una señal elegí Ventana. Seleccioná el tipo y la longitud L, que es la cantidad total de muestras. Definí el índice inicial o activá Centrar alrededor de cero. Kaiser agrega el parámetro β. No se necesita una señal previa ni una respuesta al impulso h[n].',
'La salida muestra tallos discretos, tabla e informe con la definición y el intervalo. Exportar guarda las muestras e índices en JSON/CSV. Usar en otra herramienta permite llevarla a Fourier o Transformada Z; en Z se abre Muestras finitas con el registro ya cargado. También podés elegirla desde Resultados para multiplicarla por otra señal o usarla como ventana propia de un FIR.',
'Se generan ventanas simétricas, como las de filtros FIR. No se añade una normalización de ganancia ni una repetición periódica. Desplazar el origen modifica la fase de la DTFT, pero mantiene su módulo. Con longitud par, el centro puede estar entre índices y el pico muestreado puede ser menor que uno. L=1 produce una sola muestra de valor uno. Los valores numéricos conservan la precisión disponible.')

def article_blocks(route):
    # Missing authorship is an error during development, not generic prose in UI.
    blocks=list(ARTICLES[tuple(route[1:3])])
    from .tool_catalog import locate
    entry=locate(route)
    if entry and len(entry['variants'])>1:blocks.insert(2,('Cambiar de vista','Cada variante conserva su entrada y su último resultado. La primera vez puede prepararse una copia compatible de la vista anterior. Al volver, tus datos se conservan; el enlace Copiar entrada permite reemplazarlos cuando lo elegís. Copiar datos no recalcula ni modifica una salida ya obtenida.'))
    blocks.append(('Biblioteca de resultados','Al calcular, la salida queda registrada en Resultados junto con su herramienta de origen. Allí podés consultarla, exportarla o usarla en un destino compatible. Una expresión se conserva como fórmula con sus condiciones: no necesitás convertirla primero en una función de transferencia. Las muestras, los sistemas y los modelos de estados conservan sus propios tipos.'))
    return blocks


add([('inverse_dtft',0),('dtft_symbolic',1)],
'La DTFT inversa recupera una secuencia x[n] a partir de un período de su espectro X(ω). La frecuencia es continua y periódica, pero la salida se define en índices enteros.',
'En Numérico cargá una fórmula, tramos, valores, archivo o espectro de Resultados que cubra 2π en rad/muestra. En Algebraico escribí X(w); el motor aplica propiedades o integra de −π a π. Para ver un registro elegí un primer índice y una cantidad: se admiten índices negativos.',
'Cada muestra es un coeficiente de Fourier de X(ω), con el factor 1/(2π). Por ejemplo, una banda ideal |ω|≤π/3 produce x[0]=1/3 y x[n]=sin(πn/3)/(πn) para n distinto de cero. La fórmula y las muestras se guardan en Resultados para consultarlas o reutilizarlas.',
'La DTFT inversa integra un espectro periódico; la DFT inversa parte de un conjunto finito de coeficientes y produce un bloque periódico. La aproximación numérica usa muestras de frecuencia y puede tener aliasing temporal: más índices de salida no agregan información. En la forma algebraica no se asume causalidad, y una integral no resuelta se conserva explícitamente.')


add(('signal_product',0),
'Multiplicar señales combina sus valores en el mismo índice o instante. Sirve para aplicar una ventana a una señal, entre otros productos punto a punto.',
'Elegí discreta o continua y definí las dos entradas de forma independiente. La primera fija el eje de salida. Podés ingresar una fórmula, una lista, un archivo o un resultado en cada entrada.',
'Cada salida es y[n]=x[n]·w[n], o su equivalente temporal. Una ventana corta conserva sólo la parte de la primera señal donde esa ventana tiene valores distintos de cero. La salida se guarda en Resultados y puede exportarse o reutilizarse.',
'Fuera de la segunda señal se usa cero. Para registros continuos se interpola linealmente la segunda sobre los instantes de la primera; el producto entre muestras sigue siendo una aproximación. Los impulsos Dirac ideales requieren otro tratamiento y los relojes discretos registrados deben coincidir.')
add(('fir_window',0),
'Esta opción permite diseñar un FIR a partir de una respuesta h[n] propia, en lugar de elegir sólo un tipo de filtro y sus frecuencias de corte.',
'Cargá h[n] y su intervalo. Elegí una ventana estándar, cuyo largo se toma del registro, o una señal w[n] propia. El producto se obtiene alineando ambos por índice. El retardo opcional lleva a cero un inicio negativo.',
'La transferencia representa la h[n] final, incluidos sus índices. El documento muestra su módulo, fase y retardo de grupo, además de las secuencias intermedias. Todas las salidas quedan en Resultados; Analizar permite consultar también polos y ceros y otros estudios compatibles.',
'Se trabaja sobre el intervalo de h[n] cargado. Si viene de una fórmula infinita, el resto no se evalúa. El producto no normaliza automáticamente la ganancia. Agregar D muestras de retardo cambia la fase y el retardo de grupo, pero no el módulo. Si conservás índices negativos, la transferencia puede contener avances y no se simula mediante una realización causal.')


add(('state_space','simulation'),
'La simulación obtiene los estados y las salidas de un modelo A, B, C, D a partir de sus entradas y un estado inicial.',
'Definí las matrices y elegí cada canal u1, u2, etc. En cada canal podés escribir una fórmula o tramos, pegar muestras, abrir un archivo o reutilizar un resultado. Todos deben compartir su eje. El estado inicial se interpreta en el primer índice o instante del registro, aunque no sea cero.',
'En discreto, x[n+1]=Ax[n]+Bu[n] e y[n]=Cx[n]+Du[n]. Las fórmulas se evalúan en n entero y el período T sólo describe el reloj físico. En continuo se aplica una entrada constante entre muestras (ZOH) y se propaga el estado mediante la exponencial matricial. Entradas, estados y salidas quedan en la biblioteca de resultados con el eje conservado.',
'No se recortan, interpolan ni remuestrean canales automáticamente. Si una señal registra una tasa distinta de 1/T, hay que corregir T o cambiar su tasa antes de simular. Una condición inicial al comienzo del registro no determina la historia anterior del sistema.')
add(('state_space','frequency'),
'La respuesta en frecuencia de un modelo de estados permite estudiar cada salida frente a cada entrada.',
'Cargá las matrices y el rango de frecuencia. En continuo el eje es Ω en rad/s; en discreto es ω en rad/muestra, como en el análisis de H(z). Los borradores de ambos rangos se conservan al cambiar de dominio.',
'Se evalúa C(sI−A)⁻¹B+D en s=iΩ, o C(zI−A)⁻¹B+D en z=exp(iω). Cada par salida/entrada tiene su espectro y puede reutilizarse desde Resultados. El selector permite ver cualquier canal; el CSV conserva todos.',
'Los puntos singulares se indican como no disponibles. El período T corresponde al modelo discreto y no transforma las unidades del eje mostrado. Una respuesta de un canal puede ocultar modos internos no controlables u observables.')
add(('fir_window',0),
'Esta opción obtiene un FIR multiplicando una respuesta h[n] propia por una ventana de longitud y ubicación elegidas.',
'Elegí la ventana y su longitud L en muestras; es independiente del tamaño del registro de h[n]. Podés centrarla o fijar su primer índice n_w. Si h es una fórmula se evalúa en n_w…n_w+L−1; si son datos cargados, se usa cero fuera de su registro. Una ventana propia define su longitud y ubicación mediante sus datos.',
'Por ejemplo, un registro h[n] de 101 muestras puede enventanarse con una Hann de L=31 para obtener 31 muestras. El orden nominal es M=L−1=30. El retardo opcional lleva el comienzo negativo a cero. El informe muestra el intervalo, la longitud y el retardo; la respuesta incluye módulo, fase y retardo de grupo. Las salidas quedan en Resultados.',
'L significa cantidad total de muestras, no orden ni semilongitud. Con L par el centro de una ventana simétrica es semientero; no se desplaza automáticamente h para imponerle otra simetría. La ganancia no se normaliza. Si hay extremos nulos o desplazamientos, el orden efectivo de H puede diferir de L−1.')


add(('state_space','transfer'),
'Esta opción obtiene la transferencia entre una entrada y una salida de un modelo de estados y permite continuar su análisis desde el mismo resultado.',
'Cargá A, B, C y D, elegí el dominio y el par de canales, numerados desde 1. Podés reutilizar un modelo de Resultados o abrir un JSON nativo desde Cargar modelo. Calculá para ver H(s) o H(z) en notación matemática.',
'Analizar abre polos y ceros, frecuencia o respuesta temporal con la transferencia obtenida. Usar filtro en permite cargarla en otras herramientas y Exportar filtro guarda sus coeficientes. El resultado también queda en la biblioteca. En discreto, el informe conserva el período T del modelo.',
'La transferencia supone estado inicial nulo. Un canal puede ocultar estados que no se controlan u observan desde ese par de entrada y salida. Los coeficientes se calculan numéricamente y pueden contener residuos de redondeo. Si cambiás el modelo, las acciones siguen usando el último resultado hasta recalcular.')
add(('state_space','discretize'),
'Discretizar convierte un modelo continuo de estados en un modelo que avanza una muestra por cada período T.',
'Cargá A, B, C y D continuas, indicá T en segundos y elegí ZOH, Tustin o Euler. El resultado muestra las matrices discretas y queda en Resultados. La entrada continua se conserva para comparar otro período o método.',
'Usar modelo calculado en envía esas matrices, su dominio y T directamente a otro estudio de estados: estructura, respuesta temporal, frecuencia o transferencia. No hace falta buscarlas en la biblioteca ni escribirlas otra vez. Exportar modelo guarda un JSON que se abre desde Cargar modelo; si contiene varios modelos, se puede elegir cuál usar.',
'ZOH supone entrada constante por intervalo. Tustin y Euler usan otras aproximaciones y pueden cambiar la interpretación de los estados iniciales. Reutilizar o exportar conserva el último resultado calculado aunque se hayan editado los campos. Cambiar T requiere un nuevo cálculo.')


add(('basic','sum'),
'La suma combina los valores de dos señales en el mismo índice o instante. Está junto al producto dentro de Sumar o multiplicar señales.',
'Elegí el dominio y definí las dos entradas en las pestañas Señal x y Señal v. Cada una puede ser una fórmula, función por tramos, lista, archivo o resultado anterior. En discreto se alinean por n, aunque tengan diferentes orígenes o longitudes.',
'La salida y=x+v cubre ambos registros: fuera de cada entrada se usa cero. En continuo, las partes ordinarias se interpolan linealmente en un intervalo común, con una rejilla uniforme basada en el menor paso y ajustada a sus extremos. Los impulsos Dirac se suman mediante sus posiciones y pesos y permanecen separados de las muestras. El resultado se guarda en la biblioteca y puede exportarse o reutilizarse.',
'El eje discreto conserva su reloj si está registrado y es compatible. La suma continua entre muestras sigue siendo una aproximación. Suma y Producto conservan borradores propios; al volver a una operación no se reemplaza su entrada sin pedirlo mediante Copiar entrada. El producto conserva el intervalo de x, mientras que la suma cubre ambos registros.')
add(('signal_product',0),
'El producto punto a punto permite aplicar una ventana a una señal. Está junto a Suma dentro de Sumar o multiplicar señales.',
'Elegí Producto y el dominio. En Señal x cargá la señal, y en Señal w / ventana cargá la segunda. Ambas entradas son independientes y pueden venir de una fórmula, tramos, muestras, archivo o resultado anterior.',
'El resultado es y[n]=x[n]·w[n], o su equivalente temporal. Se conserva el intervalo de x y se usa cero fuera del registro de w. En continuo se interpola w linealmente sobre los instantes de x. El resultado queda disponible para exportar y reutilizar. Cambiar de pestaña de entrada conserva sus datos.',
'No se conjuga la segunda señal, no se realiza convolución y no se normaliza la ganancia. Los relojes discretos conocidos deben ser compatibles. Los productos generales de Dirac requieren otro tratamiento. Para elegir la longitud de una ventana independientemente de h[n] al obtener un FIR, usá Diseñar filtro → FIR → h[n] propia.')


add(('systems',9),
'La respuesta temporal aplica una entrada a H(s) o H(z) y muestra la salida sobre el registro elegido. La definición es local y puede reutilizarse desde otro resultado.',
'Cargá el sistema por fórmula, coeficientes, archivo o resultado anterior. Elegí impulso, escalón o una señal propia. En discreto podés indicar T en segundos; si el sistema viene de estados o una conversión con reloj conocido, se completa automáticamente. Dejar T vacío permite trabajar sólo en índices o utilizar el reloj de la entrada.',
'El gráfico discreto usa n entero. T relaciona esas muestras con el tiempo físico y se conserva en las salidas y al exportar el sistema. No multiplica el argumento de las fórmulas x[n] ni convierte ω a otra unidad: la frecuencia digital sigue en rad/muestra. Si una entrada registra una tasa diferente de 1/T, se pide corregir el reloj o cambiar la tasa antes de filtrar.',
'El reposo inicial se refiere al comienzo del registro. Los historiales permiten separar entrada cero y estado cero. No se simula automáticamente una cola fuera de la ventana. Editar T o las entradas no modifica las salidas anteriores hasta recalcular. Un H(z) sin período conocido no recibe un reloj arbitrario de un segundo.')


for kind,index,operation in [('basic','shift','shift'),('basic','reverse','reverse'),('basic','scale','scale'),('basic','parity','parity'),('time_transform',0,'affine'),('time_transform',1,'shift'),('time_transform',2,'reverse'),('time_transform',3,'scale'),('time_transform',4,'parity')]:
    explanation={'shift':'Desplazar cambia el lugar del registro sobre su eje. Un desplazamiento positivo lo lleva a la derecha; uno negativo, a la izquierda.','reverse':'Invertir refleja la señal alrededor de cero: x[n] pasa a x[−n], o x(t) a x(−t). No se invierte el signo de la amplitud.','scale':'Escalar amplitud multiplica cada valor por A y conserva su posición. A puede ser una constante real o compleja.','parity':'La descomposición par e impar expresa una señal como la suma de una parte simétrica y otra antisimétrica respecto de cero. No se conjugan los valores complejos.','affine':'La transformación afín combina amplitud, escala temporal, inversión y desplazamiento en y(t)=A·x(a·(t−t₀)).'}[operation]
    load='Cargá la señal por fórmula/tramos, muestras, archivo o resultado. Elegí el dominio y la operación dentro de Transformar una señal. En discreto los desplazamientos se indican como muestras enteras; en continuo, como segundos. Cada variante conserva su borrador al regresar.'
    reading='El informe muestra la relación matemática, el intervalo y el paso finales. La salida queda en Resultados y puede exportarse o enviarse a otra herramienta. Par e impar entrega dos señales; su suma recupera el registro sobre la rejilla usada. La pestaña Original se dibuja al abrirla para comparar sin generar otra figura en cada cálculo.'
    scope='Fuera del registro se considera cero. En continuo, Par e impar usa interpolación lineal sobre una rejilla simétrica; entre muestras sigue siendo una aproximación y los pesos Dirac se conservan aparte. Las otras transformaciones continuas cambian las coordenadas sin interpolar. Los parámetros son constantes y la escala temporal debe ser real no nula. Cambiar los campos no altera el resultado anterior hasta recalcular.'
    add((kind,index),explanation,load,reading,scope)


add(('transform_lab','z'),
 'Directa e Inversa reúnen los cálculos de Z. Las secuencias finitas son una forma de entrada de la directa, sin un menú independiente.',
 'En Directa elegí Expresión o Secuencia finita; cada registro conserva su primer índice. En Inversa cargá X(z), elegí una ROC y pedí un intervalo o el soporte finito completo cuando X sea un polinomio de Laurent.',
 'Enviar a CAS conserva el resultado activo: X(z) en la directa y x[n] en la inversa. Analizar X(z) como H(z) usa la transformada, conserva el reloj disponible y traslada una ROC cuando puede determinarse.',
 'La ROC decide la secuencia. Una lista finita no se prolonga periódicamente ni se convierte en una señal infinita. El soporte completo se refiere al intervalo entre el primer y último coeficiente no nulo; los ceros exteriores no se pueden deducir de X(z).')
add(('course_tools','fir'),
 'Diseñá un FIR por bandas, amplitudes y tolerancias. Un rechazabanda puede conservar las frecuencias bajas con amplitud 1 y las altas con amplitud 2.',
 'Ingresá los bordes en orden y una amplitud positiva por banda de paso. Elegí tolerancias absolutas, relativas o en dB. En relativas y rechazo en dB, Aref es la mayor amplitud de paso.',
 'El ideal, los límites y el filtro calculado aparecen juntos. El informe muestra h_ideal[n], la ventana, h[n], longitud y evaluación de cada banda. Las dos bandas del rechazabanda se construyen con sus ganancias propias antes de aplicar la ventana.',
 'Kaiser estima la longitud, pero no garantiza cumplimiento. Si la respuesta queda fuera de tolerancias, se indica expresamente. La búsqueda de longitud usa la familia y la rejilla elegidas; no demuestra un mínimo universal.')
add(('system_analysis',0),
 'Analizá H(s) o H(z) sin confundir la función racional del plano complejo con su respuesta en frecuencia.',
 'Ingresá fórmula o coeficientes. En digital elegí también la ROC: secuencia derecha, izquierda, anillo por radio o no especificada. Los sistemas importados conservan su ROC registrada.',
 'Función de transferencia muestra H(s) o H(z) mediante dos mallas seleccionables: módulo/ángulo o parte real/imaginaria. Sus ejes horizontales recorren el plano complejo; la altura representa una componente de H. La respuesta en frecuencia tiene su propia figura y el mismo selector de componentes, junto al retardo de grupo.',
 'La expresión racional puede evaluarse fuera de la ROC sin que esa evaluación sea la transformada convergente de h[n]. La fórmula sola no define una ROC. Los bordes con polos están excluidos y una raíz numéricamente sobre el círculo impide certificar su inclusión.')

ARTICLES['systems',6].append(('Edición y escala en la ventana del gráfico','La ventana del plano tiene su propio selector para agregar polos, agregar ceros, mover o quitar puntos. Se sincroniza con los controles del diseño. La rueda amplía o reduce alrededor del mouse; Acercar y Alejar modifican el alcance visible, y Ajustar a raíces vuelve a encuadrar todas las raíces. Alejá la vista para colocar, por ejemplo, un cero en 2. La escala elegida se conserva al agregar puntos y al actualizar el sistema. El círculo unitario es una referencia, no un límite de edición.'))
ARTICLES['transform_lab','z'].append(('Continuidad, pares y convergencia','Completar una muestra por continuidad no basta para transformar una suma: también hay que reconocer el resto de la secuencia. Se separan esas muestras y se aplican pares y propiedades antes de la suma general. sin(pi*n)/(pi*n), completada con 1 en n=0, es el impulso unitario para n entero: su transformada Z es 1. En cambio, una sinc bilateral de corte menor que pi puede tener un pulso como DTFT y no tener una ROC abierta para Z. El informe distingue esos casos y muestra la DTFT cuando reconoce el par sinc/rectángulo. Para una señal causal usá soporte de 0 a oo; para toda la secuencia, de -oo a oo.'))
ARTICLES['dtft_symbolic',0].append(('Sinc y pulso en frecuencia','Para un pasabajos ideal con corte wc entre 0 y pi usá sin(wc*n)/(pi*n), reemplazando wc por su valor, y soporte de -oo a oo. En n=0 se utiliza wc/pi. La DTFT vale 1 dentro de la banda, 0 fuera y 1/2 en los bordes; se repite cada 2*pi. Si wc=pi, la secuencia es un impulso y el espectro vale 1 en todo el período. Un soporte de 0 a oo describe otra señal y produce otra transformada.'))

for _sections in ARTICLES.values():
    if not any(title=="Indeterminaciones y valores por continuidad" for title,_ in _sections):_sections.append(("Indeterminaciones y valores por continuidad",'Una expresión como sin(n)/n no define su valor en n=0. SignalLab la completa por continuidad si los límites reales por izquierda y derecha coinciden y son finitos: en este caso se utiliza 1. En una secuencia discreta esto es una convención de carga, no un valor impuesto por el índice; si necesitás otro valor, definilo en Por tramos. Un valor finito ya definido se conserva. Los polos, las divergencias y los límites laterales diferentes mantienen su restricción. Cuando se aplica el criterio, el informe muestra los puntos y valores en Levantamiento de indeterminaciones; el detalle se conserva en Resultados y al copiar o guardar el informe. sinc(0)=1 ya pertenece a la definición de la función y no cuenta como una indeterminación reparada.'))
