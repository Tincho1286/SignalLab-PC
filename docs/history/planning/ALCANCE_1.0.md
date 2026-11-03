# Alcance de SignalLab PC 1.0

La primera estable reúne las herramientas implementadas para Sistemas y Señales I y II. Conserva las funciones existentes de Señales Aleatorias; su ampliación queda para una etapa posterior. Modulación y demodulación no forman parte del alcance acordado.

## Modelo de trabajo

Hay 29 problemas agrupados y 80 variantes, además del CAS. Cada vista conserva entradas y resultados propios. Un cálculo no requiere preparar antes una señal global. La biblioteca de Resultados sirve para reutilizar opcionalmente señales, sistemas, expresiones, estados y datos calculados compatibles.

Las fórmulas de señales y los archivos MATLAB.m admiten los subconjuntos documentados; no ejecutan Python o MATLAB arbitrario..mat admite las variables y formatos numéricos soportados por el importador. JSON/CSV nativos preservan los metadatos de intercambio indicados en la ayuda.

## Convenciones

- DFT sin normalización hacia adelante e IDFT con 1/N, sobre el orden almacenado desde cero. FFT es un algoritmo para calcular la DFT.
- DTFT en rad/muestra; Fourier continua en rad/s. Los índices discretos se representan con muestras independientes. Los relojes físicos se conservan cuando están disponibles; no se inventa un período de muestreo.
- Transformadas inversas con la ROC y las condiciones correspondientes. Una expresión pendiente o condicionada se conserva como tal; las aproximaciones numéricas se identifican.
- Las ventanas finitas, interpolaciones y cuadraturas representan modelos de registro. Agregar ceros no aumenta la duración observada ni mejora por sí solo la resolución física.
- La longitud FIR es cantidad de coeficientes; el orden es longitud menos uno. h[n] propia puede enventanarse con una longitud elegida, independiente del registro cargado.
- Una Dirac continua se guarda por posición y peso, separada de las muestras ordinarias. La carga numérica por pesos admite sumas finitas de orden cero con argumentos lineales; no asigna una altura finita al impulso.
- Editar entradas no cambia el resultado anterior. Reutilizar o exportar trabaja con la última salida calculada, cuya vigencia se indica en la herramienta.

## Límites que se mantienen

La cobertura detallada está en COBERTURA_SYS_I_II_ACTUAL.md. Las transformadas simbólicas no son universales para toda función trascendente. Una realización con estados, integradores o retardos tiene las restricciones de causalidad y propiedad indicadas por el método. Los sistemas con avances pueden estudiarse donde el análisis y la ROC los admiten.

Los márgenes y cruces evaluados en una rejilla no certifican todos los cruces ni la estabilidad global. Las inversas numéricas de espectros finitos y las respuestas ideales enventanadas son aproximaciones declaradas. Las medidas ordinarias no asignan energía/RMS finitos a una Dirac ideal.

No se incluye una emulación completa de hardware, todas las realizaciones de aritmética finita ni la cobertura avanzada de procesos aleatorios. Guardado y recuperación de sesiones no son requisito de esta primera estable; los controles existentes no sustituyen la exportación de resultados.

## Mantenimiento

La 1.0 fija esta base funcional y su organización. Las correcciones posteriores se publican como versiones de mantenimiento, con notas y sin reinterpretar resultados anteriores ni reemplazar los portables históricos.
