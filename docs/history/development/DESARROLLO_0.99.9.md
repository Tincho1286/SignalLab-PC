# SignalLab PC 0.99.9 · entrada continua y pesos Dirac

La carga común de señales continuas interpreta DiracDelta(t-a), dirac(t-a) e impulse(t-a) como impulsos por posición y peso, separados de las muestras de la parte ordinaria. No se crea otro menú. En discreto, impulse(n-a) conserva su significado de muestra unitaria.

## Cargar y entender el resultado

Un impulso puede estar entre puntos de la rejilla. Su peso no depende del paso temporal. Se aplica δ(a*t+b)=δ(t+b/a)/|a| y la evaluación del factor ordinario en la posición del impulso. Por ejemplo, 3*dirac(2*t-1) aporta peso 1.5 en 0.5 s. Los términos con igual posición se suman; si se cancelan, no queda un impulso ficticio.

El resultado presenta la parte ordinaria y un panel Peso Dirac sobre el mismo eje en segundos. Los tallos de ese panel indican peso (área), no altura finita. El informe enumera posiciones y pesos; la tabla avisa que sus filas son la parte ordinaria. La ayuda de funciones contiene un dibujo de colores que distingue ambos componentes y explica los límites. Se conservan la paleta, la navegación y las ventanas externas de gráficos.

La ventana ordinaria va de la primera a la última coordenada almacenada, inicio+(cantidad−1)*paso. Se informa cuántos impulsos quedaron fuera. En una serie continua se usa un período [inicio,inicio+T), incluyendo el borde izquierdo y excluyendo el derecho para evitar contarlo dos veces. Las áreas se suman por separado de la cuadratura de la parte ordinaria.

## Cálculo y reutilización

Fourier continua incorpora los términos peso*exp(-j*ω*posición); las series incorporan peso/T por armónico con su fase. Los consumidores existentes de convolución, suma, transformaciones temporales y respuesta de transferencias propias continúan usando posiciones y pesos. Un impulso no obliga a alinearlo con una muestra ni a convertirlo en una altura.

JSON y CSV nativos conservan los metadatos. El envío al CAS conserva la matriz de muestras ordinarias y las posiciones/pesos ideales por separado. El cambio compatible de Fourier numérica a algebraica prepara una definición finita que conserva los impulsos de los extremos sin multiplicarlos por una ventana ambigua. No se atribuye exactitud analítica a los coeficientes numéricos ni a una cuadratura finita.

## Alcance declarado

La carga por pesos admite sumas finitas, argumentos lineales en t de escala real no nula e impulsos de orden cero. Se rechazan productos de Dirac, funciones o recíprocos de impulsos, factores discontinuos en su posición y selecciones ambiguas en bordes de tramos. KroneckerDelta no se convierte en una Dirac continua. Derivadas y argumentos no lineales permanecen en las herramientas algebraicas.

El muestreo de un impulso ideal como valor puntual y las medidas de energía/RMS ordinarias se rechazan con una explicación; para eso hace falta un pulso de amplitud y duración finitas. Una respuesta en frecuencia formada por distribuciones no se introduce como una tabla ordinaria de H(ω), ni se convierte silenciosamente por bilineal o invarianza. Las inversas numéricas de muestras conservan su límite frente a distribuciones en frecuencia.

## Evidencia dirigida

Se comprobó un impulso fuera de rejilla, escalado del argumento, factor exponencial, Fourier, un período con impulsos en ambos extremos, respuesta de un primer orden y paso directo, rechazo de modelos ambiguos y conservación del impulso discreto. Se recorrieron la carga común, el informe, los tres paneles y la ayuda ilustrada, además de intercambio nativo y envío al CAS. No se hizo una batería general ni una campaña del portable.

Se integra y revisa el trabajo Dirac108 antes preparado aparte, rebasado sobre 0.99.8 sin deshacer las mejoras de CAS ni conversión de filtros. El catálogo sigue agrupado por problemas; no se suman familias ni variantes. Esta entrega continúa hacia 1.0 y no demuestra por sí sola el cierre de toda la meta estable.
