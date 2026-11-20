# Catálogo de herramientas

[← Documentación](README.md)

Elegí un área según lo que quieras calcular. Cada herramienta conserva sus datos al cambiar de variante. Al terminar el cálculo, podés consultar el informe, abrir una figura o reutilizar la salida en otra operación. Para ver qué significa un campo o cómo se obtuvo un resultado, presioná **F1**.

## Señales

Permite crear secuencias y registros mediante fórmulas, tramos o muestras, y generar ventanas simétricas rectangular, Hann, Hamming, Blackman, Bartlett y Kaiser. Las operaciones incluyen desplazamiento, inversión, amplitud, componentes par e impar, suma, producto punto a punto, convolución, correlación y medidas de energía, potencia y RMS.

En **Crear una señal**, activá **Repetir un período en todo el eje** para extender una fórmula o una lista de muestras. En continuo, el paso fija la distancia entre puntos de la lista y el programa interpola hasta el primer punto del período siguiente. La definición periódica queda en Resultados junto a la ventana dibujada. También podés escribir `Repeat`, `RepeatSamples`, `PulseTrain` e `ImpulseTrain` en las fórmulas. En **Ajustar amplitud**, usá **B** para desplazar la señal verticalmente. Dejá **A = 1** si querés conservar su escala.

`RepeatSamples(n,-1,(2,0,3))` repite los valores 2, 0 y 3 desde n = −1. `RepeatSamples(t,0,(0,1),1)` repite una señal triangular de período 2 s, que sube durante el primer segundo y baja durante el segundo.

El producto punto a punto sirve para enventanar una señal. Las entradas se alinean por sus índices o coordenadas; al reutilizarlas se conservan el origen y el reloj disponibles. El resultado puede enviarse a Fourier, Z u otras operaciones compatibles, o exportarse como registro.

**Medir un registro** calcula energía, potencia media y RMS en el intervalo elegido. También muestra dónde se concentra la energía y dónde la señal alcanza un nivel, y permite guardar la media compleja y la componente alterna. [Guía de medidas de registros](record-measurements.md).

Podés pegar una tabla de muestras y revisar sus columnas antes de incorporarla. El editor permite deshacer cambios o guardar un tramo como señal independiente. En suma y producto, **Operación por muestra** muestra qué valores de cada entrada se alinean en cada posición. [Guía de herramientas básicas](basic-usability.md).

## Sistemas LTI

El análisis acepta H(s) y H(z) por fórmula o coeficientes, y respuestas definidas directamente en frecuencia. También podés armar un diagrama con bloques de transferencia y obtener la H equivalente con estado inicial nulo. Los bloques admiten transferencias racionales propias en un dominio común y permiten conectarlas en cascada, paralelo o realimentación. El análisis reúne módulo lineal o en dB, fase, retardo de grupo y, cuando el modelo es racional, polos, ceros y realizaciones.

La respuesta temporal utiliza la entrada y las condiciones iniciales elegidas. Su interpretación depende de la causalidad y la región de convergencia del sistema. Una fórmula general no se transforma automáticamente en un cociente de polinomios ni en una realización finita; los informes indican qué análisis permite su representación.

H(s) y H(z) también pueden explorarse en el plano complejo mediante mallas de parte real/imaginaria o módulo/ángulo. Esta vista se distingue de la respuesta en frecuencia, evaluada sobre el eje imaginario o el círculo unitario.

**Espacio de estados** permite analizar las matrices, cambiar coordenadas con su condición inicial y buscar equilibrios. En la simulación podés ver por separado qué aporta la entrada y qué aporta el estado inicial. **Paso a paso** muestra cómo se calculó la salida o el siguiente estado. [Guía de espacio de estados](state-studies.md).

## Diseño y análisis de filtros

El diseño reúne FIR e IIR por bandas y tolerancias, FIR por cortes y longitud, enventanado de una h[n] propia, ubicación interactiva de polos y ceros, secciones de segundo orden y modelos RC. Los resultados muestran la definición obtenida y permiten analizar, exportar o reutilizar el filtro. Los filtros ideales se cargan como funciones por tramos en frecuencia y pueden producir una fórmula de su respuesta al impulso cuando la inversa se reconoce.

En FIR por bandas, la selección automática busca la primera longitud que supera la comprobación numérica de tolerancias. En Kaiser, **Longitud L=0** activa esa búsqueda; una longitud positiva fija el número de coeficientes para comprobar el diseño resultante. Las otras ventanas utilizan la búsqueda automática. El informe distingue la estimación inicial de la longitud utilizada y muestra mínimos y máximos de las bandas, con sus frecuencias y límites.

Las tolerancias pueden expresarse en amplitud absoluta, relativa o dB. Un rechazabanda FIR admite amplitudes distintas en sus dos bandas de paso; las familias IIR clásicas conservan una ganancia común. La [guía de convenciones](conventions.md) define los intervalos de tolerancia y la relación L=M+1.

El ajuste de fase informa el sistema obtenido y la relación con el original. Las conversiones analógico/digital utilizan el método elegido y conservan el período de muestreo disponible. Las condiciones de causalidad, estabilidad y convergencia siguen formando parte del resultado.

Para medir un filtro o sistema ya calculado, abrí **Medidas** en el análisis LTI. Podés leer frecuencias concretas, buscar cruces de nivel y comprobar límites por banda. La tabla se puede exportar a CSV. [Guía de medidas de frecuencia](frequency-measurements.md).

## Fourier y espectros

Incluye DFT/FFT, DTFT, Fourier continua e inversas numéricas o algebraicas según la entrada. También permite estudiar series, densidad de energía, potencia periódica, periodogramas, Welch, Hilbert y señal analítica.

La STFT permite inspeccionar cómo cambia el espectro en el tiempo y reconstruir la señal a partir de los tramos. Sus ejes y escalas se describen en la [guía de ventanas temporales](time-frequency.md).

**Medir un espectro** reúne las medidas de bandas, picos, centro, ancho RMS y distribución acumulada. La guía explica cómo cambian estas medidas según se trabaje con energía, potencia o la respuesta de un sistema. [Guía de medidas espectrales](spectral-measurements.md).

La DFT ofrece coeficientes discretos con eje en rad/muestra o índices k centrados. La DTFT es continua en frecuencia y puede superponerse sobre esos mismos puntos usando un origen y unas coordenadas compatibles. Agregar ceros a una FFT densifica su muestreo frecuencial, pero no aumenta la duración observada de la señal.

Un espectro complejo conserva la información necesaria para una inversa; su módulo o su densidad de energía no contienen por sí solos la fase. Las herramientas de reutilización distinguen estas salidas para evitar tratarlas como objetos equivalentes.

## Muestreo y precisión numérica

Permite explorar muestreo, aliasing, tasas pasabanda, reconstrucción, diezmado, expansión y conversión racional de tasa. Las operaciones elementales de diezmado y expansión aplican su definición; la conversión racional incorpora el tratamiento antialias indicado por su método.

**Reconstruir una señal** compara retención constante, interpolación lineal y SINC usando el mismo reloj. Podés contrastar las curvas con una referencia, comprobar qué pasa en las muestras originales y ver cuánto aporta cada una en el instante elegido. [Guía de reconstrucción](reconstruction-studies.md).

Las herramientas de precisión estudian cuantización, SNR, formatos numéricos y efectos sobre los coeficientes y la aritmética de filtros. Los informes distinguen una representación almacenada de la simulación de una realización concreta. La [matriz de cobertura](scope/sys-i-ii.md) detalla las realizaciones y los modelos de error disponibles.

## Laplace, Z y ecuaciones

Las transformadas directas e inversas conservan la definición, el soporte y las condiciones de convergencia. Z directa admite expresiones y registros finitos; la inversa separa la expresión completa de las muestras elegidas para el gráfico. El soporte finito completo corresponde a polinomios de Laurent; una secuencia infinita requiere un intervalo finito para representarse numéricamente.

Las ecuaciones diferenciales y en diferencias lineales con coeficientes constantes reúnen la solución, las condiciones iniciales y las muestras disponibles. Una transferencia con condiciones iniciales nulas se distingue de una solución que incorpora memoria anterior. La [guía de Z](z-transforms.md) explica cómo el soporte elegido cambia el cálculo de una sinc.

## Señales aleatorias

Podés generar realizaciones y medir sus estadísticas, correlación y covarianza. Con un modelo AR, MA o ARMA conocido, podés consultar sus momentos y su espectro teórico. Si partís de un registro, el ajuste AR permite comparar órdenes, validar un modelo y pronosticar muestras. [Guía de estimación AR](ar-estimation.md).

Las propiedades teóricas de un proceso y las estimaciones de una realización finita se presentan por separado. Los modelos conocidos admitidos son reales, causales y estables; la [cobertura de Señales Aleatorias](scope/random-signals.md) explica sus convenciones y los temas todavía pendientes.

## Calculadora CAS

La hoja simbólica permite operar con expresiones, ecuaciones, matrices y supuestos, y referenciar resultados para continuar un cálculo. Incluye simplificación, sustitución, álgebra, cálculo, funciones trigonométricas e hiperbólicas y conversiones como `exp2trig` y `trig2exp`. `assume` permite declarar hipótesis utilizadas en operaciones compatibles.

Las expresiones importadas conservan las condiciones registradas en su procedencia; eso no equivale a convertir automáticamente todas ellas en supuestos nuevos de la hoja. Cuando el motor deja una operación pendiente, el informe mantiene ese estado. [Criterios de fiabilidad](mathematical-reliability.md).


## Ampliaciones de la 1.8.1

La [guía de análisis interactivo](interactive-analysis.md) explica las comparaciones FIR, la elección visual de ROC, los inspectores de ecuaciones en diferencias y convolución y las medidas espectrales de ventanas. Estas funciones corresponden a los paquetes de la [1.8.1](releases/v1.8.1.md); las descargas de la 1.8.0 conservan su contenido original.


## Mediciones y diferencias desde la 1.8.2

La [guía de gráficos](cursors.md) explica las lecturas A/B de mapas, la vista B−A y el CSV de comparación, incluidas las señales con Dirac. También describe cómo ampliar el espectro de una ventana para consultar sus muestras originales. Son mejoras de las herramientas existentes y mantienen sus condiciones de soporte, reloj y frecuencia.


## Continuar cálculos desde los resultados

En **Cambiar tasa con antialias**, podés elegir la frecuencia de salida y consultar el FIR aplicado. El filtro usa el reloj intermedio y la señal convertida conserva su propio reloj de salida. En el CAS, **Operar resultado** aplica una operación a la referencia seleccionada y conserva el texto que estás escribiendo.
