# SignalLab PC 0.71 — navegación directa y carga de datos

## Organización de las herramientas

Se reemplaza el árbol de tres niveles por seis áreas visibles y una lista plana de herramientas del área elegida. Inicio permite abrir las herramientas directamente. La búsqueda es global e identifica el área y la variante coincidente, por ejemplo DFT, FIR o polos. Se retira el menú Operaciones duplicado del encabezado y el menú superior ya no agrega un nivel por sección. Recorrer áreas utiliza una sola pestaña Herramientas; los problemas abiertos conservan sus documentos y datos independientes.

| Área | Ubicación de los problemas |
|---|---|
| Señales | Crear, editar, transformar, sumar, convolucionar, correlacionar y medir energía/potencia. |
| Sistemas LTI | Analizar un sistema, conectar bloques, definir filtros ideales/en frecuencia y trabajar en espacio de estados. |
| Diseño de filtros | Diseñar FIR/IIR, diseñar por polos y ceros, modelos físicos, ajustes y conversión. |
| Fourier y espectros | Transformada de Fourier, series, densidades, Hilbert y espectrograma. |
| Muestreo y A/D | Muestreo/aliasing, reconstrucción, cambio de tasa, cuantización y relación de frecuencias. |
| Laplace y Z | Transformadas directas/inversas y ecuaciones diferenciales. |

Analizar un sistema reúne Frecuencia y polos / ceros y Temporal. Cambiar de respuesta copia la definición compatible de H, incluida la fórmula o la realización en secciones preservada. No calcula automáticamente ni interpreta una señal como si fuese de otro dominio. Los filtros ideales están en análisis; ubicar polos y ceros para diseñar continúa en diseño.

Diseñar filtro reúne FIR e IIR, con dominio y modo de definición según corresponda: especificaciones, cortes/longitud o biquad. Se conservan los cálculos y resultados de cada variante. El selector de variantes forma parte del documento desplazable para dejar espacio a los datos en ventanas pequeñas.

## Entrada y resultados

Las entradas de señales distinguen Fórmula, Muestras, Archivo y Resultado. Archivo abre MATLAB/CSV/JSON; Resultado muestra las señales compatibles ya calculadas. Los campos de señal usan el ancho disponible, con etiquetas encima. Las listas admiten constantes como pi, fracciones, 10^(-3), notación científica y complejos sin reemplazar la i de pi. Se rechazan variables en muestras constantes. Se conservan los controles de funciones por tramos.

Respuesta temporal ofrece coeficientes o fórmula directamente, sin un botón previo para habilitar la edición. Los informes comunes se muestran al calcular y las figuras siguen abriéndose en ventanas independientes. Exportar y reutilizar permanecen junto a los resultados. F1 abre la ayuda de la variante activa; la biblioteca y las ayudas de navegación se actualizaron.

## Correcciones de recorridos y convenciones

Reconstrucción y conversión racional completan Fs y el tiempo inicial al copiar una señal con reloj registrado. Ambos campos siguen siendo editables y determinan el cálculo. Nyquist/aliasing utiliza frecuencia de tono en rad/s, con Fs en muestras/s; su informe distingue el representante firmado y el caso límite de Nyquist.

Correlación muestra el significado del retardo, la referencia, la conjugación y la escala. La normalización energética continua elimina el paso temporal antes de las operaciones para evitar escalas intermedias extremas. La correlación de registros trasladados por un mismo origen grande conserva sus retardos. El promedio periódico usa una expresión independiente del paso temporal. No se modifica la interpretación de distribuciones ni se declara soporte universal para ellas.

El estado del resultado sigue la acción activa, aunque su botón pase a Recalcular. Cambiar entre análisis/síntesis de series o entre los dos modos RC mantiene la acción correcta.

## Comprobación limitada

Apertura de los problemas públicos, ubicación única de 72 variantes, navegación por área, búsqueda de polos, FIR/IIR y dominio dentro del mismo documento, fórmula compartida entre análisis y respuesta temporal, cálculo temporal y entrada de muestras con constantes. Revisión de los recorridos modificados a 1366×850, 800×600 y 640×480; el documento permite desplazamiento vertical en pantallas pequeñas. Regreso desde ayuda comprobado. No se ejecutó una campaña general de pruebas del programa.

Comprobaciones matemáticas dirigidas: correlación compleja frente a suma directa; correlación continua constante y normalizada con pasos 1, 0.001 y 1e-300; promedio periódico; invariancia ante origen común grande; rechazo de energía cero; reloj de reconstrucción/cambio de tasa; alias de 140*pi rad/s con Fs=100; compatibilidad del cálculo anterior en Hz. La evidencia cubre estos contratos, no toda combinación de parámetros.

Continúa como versión de desarrollo hacia 1.0. Laplace/Z y sus condiciones de convergencia permanecen en el cierre dirigido pendiente.
