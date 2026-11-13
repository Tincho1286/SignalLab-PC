# Catálogo de herramientas

[← Documentación](README.md)

Las operaciones se agrupan por el problema que resuelven. Una herramienta puede reunir variantes de cálculo, pero cada definición mantiene sus propios datos. Después de calcular, el área de resultados ofrece el informe y las acciones de gráfico, exportación y reutilización adecuadas para ese objeto.

## Señales

Permite crear secuencias y registros mediante fórmulas, tramos o muestras, y generar ventanas simétricas rectangular, Hann, Hamming, Blackman, Bartlett y Kaiser. Las operaciones incluyen desplazamiento, inversión, amplitud, componentes par e impar, suma, producto punto a punto, convolución, correlación y medidas de energía, potencia y RMS.

El producto punto a punto sirve para enventanar una señal. Las entradas se alinean por sus índices o coordenadas; al reutilizarlas se conservan el origen y el reloj disponibles. El resultado puede enviarse a Fourier, Z u otras operaciones compatibles, o exportarse como registro.

## Sistemas LTI

El análisis admite H(s) y H(z) por fórmula o coeficientes, así como respuestas definidas directamente en frecuencia. Reúne módulo lineal o en dB, fase, retardo de grupo y, cuando el modelo es racional, polos, ceros y realizaciones. Las conexiones en serie, paralelo o realimentación y el espacio de estados permiten estudiar modelos relacionados.

La respuesta temporal utiliza la entrada y las condiciones iniciales elegidas. Su interpretación depende de la causalidad y la región de convergencia del sistema. Una fórmula general no se transforma automáticamente en un cociente de polinomios ni en una realización finita; los informes indican qué análisis permite su representación.

H(s) y H(z) también pueden explorarse en el plano complejo mediante mallas de parte real/imaginaria o módulo/ángulo. Esta vista se distingue de la respuesta en frecuencia, evaluada sobre el eje imaginario o el círculo unitario.

## Diseño y análisis de filtros

El diseño reúne FIR e IIR por bandas y tolerancias, FIR por cortes y longitud, enventanado de una h[n] propia, ubicación interactiva de polos y ceros, secciones de segundo orden y modelos RC. Los resultados muestran la definición obtenida y permiten analizar, exportar o reutilizar el filtro. Los filtros ideales se cargan como funciones por tramos en frecuencia y pueden producir una fórmula de su respuesta al impulso cuando la inversa se reconoce.

En FIR por bandas, la selección automática busca la primera longitud que supera la comprobación numérica de tolerancias. En Kaiser, **Longitud L=0** activa esa búsqueda; una longitud positiva fija el número de coeficientes para comprobar el diseño resultante. Las otras ventanas utilizan la búsqueda automática. El informe distingue la estimación inicial de la longitud utilizada y muestra mínimos y máximos de las bandas, con sus frecuencias y límites.

Las tolerancias pueden expresarse en amplitud absoluta, relativa o dB. Un rechazabanda FIR admite amplitudes distintas en sus dos bandas de paso; las familias IIR clásicas conservan una ganancia común. La [guía de convenciones](conventions.md) define los intervalos de tolerancia y la relación L=M+1.

El ajuste de fase informa el sistema obtenido y la relación con el original. Las conversiones analógico/digital utilizan el método elegido y conservan el período de muestreo disponible. Las condiciones de causalidad, estabilidad y convergencia siguen formando parte del resultado.

## Fourier y espectros

Incluye DFT/FFT, DTFT, Fourier continua e inversas numéricas o algebraicas según la entrada. También permite estudiar series, síntesis, densidad de energía, potencia periódica, periodograma, Welch, Hilbert, señal analítica y STFT.

La DFT ofrece coeficientes discretos con eje en rad/muestra o índices k centrados. La DTFT es continua en frecuencia y puede superponerse sobre esos mismos puntos usando un origen y unas coordenadas compatibles. Agregar ceros a una FFT densifica su muestreo frecuencial, pero no aumenta la duración observada de la señal.

Un espectro complejo conserva la información necesaria para una inversa; su módulo o su densidad de energía no contienen por sí solos la fase. Las herramientas de reutilización distinguen estas salidas para evitar tratarlas como objetos equivalentes.

## Muestreo y precisión numérica

Permite explorar muestreo, aliasing, tasas pasabanda, reconstrucción, diezmado, expansión y conversión racional de tasa. Las operaciones elementales de diezmado y expansión aplican su definición; la conversión racional incorpora el tratamiento antialias indicado por su método.

Las herramientas de precisión estudian cuantización, SNR, formatos numéricos y efectos sobre los coeficientes y la aritmética de filtros. Los informes distinguen una representación almacenada de la simulación de una realización concreta. La [matriz de cobertura](scope/sys-i-ii.md) detalla las realizaciones y los modelos de error disponibles.

## Laplace, Z y ecuaciones

Las transformadas directas e inversas conservan la definición, el soporte y las condiciones de convergencia. Z directa admite expresiones y registros finitos; la inversa separa la expresión completa de las muestras elegidas para el gráfico. El soporte finito completo corresponde a polinomios de Laurent; una secuencia infinita requiere un intervalo finito para representarse numéricamente.

Las ecuaciones diferenciales y en diferencias lineales con coeficientes constantes reúnen la solución, las condiciones iniciales y las muestras disponibles. Una transferencia con condiciones iniciales nulas se distingue de una solución que incorpora memoria anterior. La [guía de Z](z-transforms.md) explica cómo el soporte elegido cambia el cálculo de una sinc.

## Señales aleatorias

Incluye generación de realizaciones, estadísticas de registros, correlación y covarianza. Los modelos discretos estacionarios AR/MA/ARMA permiten consultar momentos y espectros teóricos; el ajuste AR mediante Yule–Walker obtiene un modelo estimado desde un registro.

Las propiedades teóricas de un proceso y las estimaciones de una realización finita se presentan por separado. Los modelos conocidos admitidos son reales, causales y estables; la [cobertura de Señales Aleatorias](scope/random-signals.md) explica sus convenciones y los temas todavía pendientes.

## Calculadora CAS

La hoja simbólica permite operar con expresiones, ecuaciones, matrices y supuestos, y referenciar resultados para continuar un cálculo. Incluye simplificación, sustitución, álgebra, cálculo, funciones trigonométricas e hiperbólicas y conversiones como `exp2trig` y `trig2exp`. `assume` permite declarar hipótesis utilizadas en operaciones compatibles.

Las expresiones importadas conservan las condiciones registradas en su procedencia; eso no equivale a convertir automáticamente todas ellas en supuestos nuevos de la hoja. Cuando el motor deja una operación pendiente, el informe mantiene ese estado. [Criterios de fiabilidad](mathematical-reliability.md).


## Ampliaciones de la 1.8.1

La [guía de análisis interactivo](interactive-analysis.md) explica las comparaciones FIR, la elección visual de ROC, los inspectores de ecuaciones en diferencias y convolución y las medidas espectrales de ventanas. Estas funciones corresponden a los paquetes de la [1.8.1](releases/v1.8.1.md); las descargas de la 1.8.0 conservan su contenido original.
