# Alcance académico y camino a la primera versión estable

Revisión del 25/10/2026. Se contrastan los contenidos de los programas aportados y la implementación actual. «Disponible» significa que existe una herramienta pertinente, no que todos los ejercicios de ese tema estén certificados. «Parcial» indica una limitación concreta. No se calcula un porcentaje a partir de títulos de menús.

## Fuentes y alcance de la comparación

Programas locales: Programa SyS1.pdf, Programa SyS2.pdf y Programa Señales Aleatorias.pdf. Se utilizaron sus contenidos analíticos, las páginas renderizadas y la extracción disponible. Esta matriz es temática, no una auditoría ejercicio por ejercicio ni una certificación de todas las propiedades numéricas.

Marco bibliográfico:

- Oppenheim, Willsky y Nawab, *Signals and Systems*: representaciones temporales y frecuenciales, LTI, muestreo y transformadas. Referencia bibliográfica en [MIT 6.011](https://ocw.mit.edu/courses/6-011-signals-systems-and-inference-spring-2018/pages/readings/).
- Oppenheim, Schafer y Buck, *Discrete-Time Signal Processing*, y Proakis–Manolakis, *Digital Signal Processing*: DSP, Fourier discreta, ventanas y filtros. La [guía de lecturas MIT 2.161](https://ocw.mit.edu/courses/2-161-signal-processing-continuous-and-discrete-fall-2008/pages/readings/) vincula estos textos con sus temas y complementa filtrado analógico con apuntes sobre prototipos y realizaciones activas.
- Oppenheim y Verghese, *Signals, Systems and Inference*: procesos, estimación y detección. [Programa de lecturas MIT 6.011](https://ocw.mit.edu/courses/6-011-signals-systems-and-inference-spring-2018/pages/readings/).

No se dispuso de ejemplares completos proporcionados por el usuario ni se atribuye la validación de un algoritmo a haber leído íntegramente estos libros. Se usan como marco temático y de convenciones, con referencias públicas verificadas.

## Matriz de cobertura

| Tema | Situación | Herramientas y límites |
|---|---|---|
| SyS I: señales, tramos y transformaciones | Disponible, validación pendiente | Fórmulas, muestras, tramos, inversión, desplazamiento, escalado, partes par/impar. Los registros numéricos son finitos. |
| Energía y potencia | Disponible con límites | Medidas de registros y medidas algebraicas; distingue intervalo finito de análisis global. La densidad puede partir de una señal local desde 0.50. |
| LTI, convolución y correlación | Disponible con límites | Cálculos continuos numéricos/algebraicos y discretos; la cuadratura depende del paso y soporte. No demuestra automáticamente linealidad o invariancia de un sistema arbitrario. |
| Laplace, Z y ecuaciones | Parcial | Laplace unilateral, inversa causal, Z finita, inversa racional derecha y contornos numéricos con ROC. No es un resolvedor general de todas las transformadas bilaterales. |
| Series y transformadas de Fourier | Disponible con límites | Directa/inversa, series, DTFT/DFT y expresiones algebraicas. Síntesis admite coeficientes manuales. Distribuciones no se representan como alturas finitas. |
| Hilbert y señal analítica | Falta herramienta dedicada | Una explicación o composición manual no equivale a una operación disponible. |
| Polos, ceros, respuesta y estabilidad | Disponible con límites | Definición numérica y por mouse, respuesta temporal/frecuencial, realimentación y estados. La estabilidad externa no reemplaza la interna. |
| Filtrado analógico y realización | Parcial | RC, transferencia general, segundo orden y prototipos de conversiones. Faltan diseño analógico general por especificaciones y realización completa con componentes/topologías activas. |
| SyS II eje 1: A/D, D/A y cuantificación | Parcial | Muestreo, reconstrucción, cuantización, SNR y punto fijo. No simula de forma completa aritmética de punto flotante ni ruido de coeficientes en estructuras de filtros. |
| Eje 2: diezmado/interpolación | Disponible con límites | Factores enteros y racionales, antialias y tratamientos de extremos. No es un sistema de procesamiento continuo en tiempo real. |
| Eje 3: DFT y convolución | Parcial | DFT/IDFT, comparación DTFT y convolución lineal/circular. Faltan herramientas explícitas de overlap-add y overlap-save con visualización de bloques. |
| Eje 4: densidades y correlación | Disponible con límites | Densidad de energía, PSD/Welch, líneas de potencia periódica y correlación. No equivale a resolver detectores óptimos en ruido. |
| Eje 5: análisis espectral | Parcial | FFT, ventanas, relleno con ceros, referencias y Welch. Faltan STFT/espectrograma y exploración tiempo-frecuencia. |
| Eje 6: fase y filtros | Parcial | Retardo, fase mínima/paso todo, clasificación FIR, filtros ideales y raíces. Relaciones de reconstrucción módulo/fase y diseños especializados requieren ampliación. |
| Eje 7: diseño FIR | Parcial | Ventanas rectangular, Hann, Hamming, Blackman y Kaiser, longitud y búsqueda por tolerancias. Bartlett no figura entre las ventanas de diseño actuales. La búsqueda no demuestra un mínimo global. |
| Eje 8: diseño IIR | Disponible con límites | Butterworth, Chebyshev I/II, elíptico digitales y conversiones Butterworth. Faltan una experiencia unificada para prototipos analógicos de todas las familias y su realización física. |
| Aleatorias: estadística y realizaciones | Parcial | Gaussiana, uniforme, Bernoulli, histograma, media, varianza, autocorrelación y autocovarianza de registros. Faltan análisis por conjuntos y pruebas de estacionariedad/ergodicidad. |
| Aleatorias: sistemas con entradas aleatorias | Parcial | Es posible filtrar realizaciones y estimar espectros. No hay un flujo completo de propagación analítica de estadísticas. |
| Modelos AR/MA/ARMA y estimación paramétrica | Falta herramienta dedicada | Filtrar ruido con una transferencia no cubre identificación, Yule–Walker ni comparación de modelos. |
| Markov, Poisson y procesos puntuales | Falta herramienta dedicada | No se cubren con la generación de ruido disponible. |
| Detección MAP/Bayes/Neyman–Pearson | Falta herramienta dedicada | Correlación no equivale a un diseñador y evaluador de detectores. |
| MMSE, Wiener, Kalman e innovaciones | Falta herramienta dedicada | El módulo de espacio de estados no incorpora esos estimadores. |
| Calidad e intervalos de estimadores | Parcial | Hay estadísticos muestrales; faltan flujos específicos de sesgo, consistencia, eficiencia e inferencia. |

## Independencia de las tareas

Cada operación conserva sus propios formularios y resultados. Cambiar de tarea no toma automáticamente la salida de otra. Reutilizar copia una entrada de forma explícita; calcular y exportar siguen siendo acciones separadas.

Cambios concretos de 0.50:

1. Densidad de energía permite x[n], x(t) o X(ω), definidos en el mismo lugar. Una señal se transforma y se eleva al cuadrado del módulo en una sola acción.
2. La síntesis de series permite introducir coeficientes manualmente, sin exigir un objeto producido antes por otra herramienta.
3. Las 76 operaciones quedan agrupadas en 18 áreas de trabajo, conservando el estado local de cada operación.
4. La ayuda interactiva reside en la biblioteca: recorrido entrada/cálculo/resultado, selección de parámetros, exploración de bandas de filtros y ejemplos de energía y muestreo.

## Criterios antes de llamar estable a la 1.0

- Cerrar los errores de flujo reproducibles: entradas propias, etiquetas correctas, resultados actuales y reutilización/exportación inequívocas.
- Consolidar todos los formularios bajo el nuevo diseño; esta entrega cambia navegación, disposición y ayuda, pero conserva varios editores y paneles internos anteriores.
- Verificar un conjunto pequeño de casos de referencia por familia, con identidades analíticas cuando existan, en lugar de repetir baterías indiscriminadas.
- Comprobar guardado/apertura, cancelación, errores de entrada y exportación sin pérdida de datos.
- Revisar tamaños de ventana y escalas de pantalla reales. La revisión fuera de pantalla no certifica todas las configuraciones de Windows.
- Declarar expresamente el alcance académico de 1.0. Estabilidad y cobertura completa de tres asignaturas son objetivos distintos.

Prioridad propuesta: consolidación de SyS I/II, luego Hilbert, procesamiento por bloques, espectrograma y diseño analógico; después ampliar Aleatorias. No agregar temas nuevos antes de cerrar los problemas de uso encontrados en esta interfaz.
