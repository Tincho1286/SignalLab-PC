# SignalLab PC 0.99.6 · variantes con entradas coherentes

La entrega conecta los métodos de las herramientas existentes sin ampliar el catálogo: 31 problemas y 80 variantes. Cada variante conserva sus datos y su último resultado. En la primera apertura se prepara una copia compatible; al volver a una vista ya usada, la copia sigue siendo voluntaria mediante el enlace existente.

## Fourier numérica y algebraica

Se incorpora un contrato explícito entre DTFT numérica/algebraica, DFT/FFT con la misma señal, DTFT inversa y Fourier continua directa/inversa. La operación y el dominio deben coincidir. Cambiar de directa a inversa no copia x como si fuera X; cambiar de continuo a discreto no supone un muestreo implícito.

De fórmula numérica a DTFT algebraica se conserva el soporte finito por índice inicial y cantidad. De DTFT algebraica al método numérico se convierte la definición con sus escalones/tramos y su soporte; unos extremos enteros finitos fijan el registro completo. Para soporte infinito se conserva la ventana de observación de destino, que debe revisarse.

En Fourier continua, pasar de fórmula numérica a algebraica limita la definición al intervalo de entrada efectivamente indicado: inicio a inicio+(cantidad−1)·paso. En la inversa, ese intervalo es de frecuencia en rad/s, no de tiempo. Se integra la fórmula dentro de él; el cálculo numérico usa una cuadratura de las muestras y no tiene por qué coincidir exactamente a resolución finita. Pasar de una definición algebraica al método numérico conserva la rejilla de entrada del destino y explica qué intervalo revisar.

La DTFT inversa copia X(ω) y los índices de salida; conserva la rejilla numérica de un período. No convierte rad/s en rad/muestra. Los registros cargados como muestras o archivos no se convierten en una supuesta fórmula analítica única. Un impulse evaluado como un valor de una rejilla continua no se reinterpreta automáticamente como Dirac con área ideal.

## Funciones por tramos

La traducción entre las expresiones del CAS y el lector numérico trabaja sobre el árbol matemático, sin ejecutar código. Convierte Piecewise, where y expresiones condicionales también cuando aparecen anidadas dentro de una suma, producto u otro tramo. Se conservan condiciones compuestas, igualdades, unidad imaginaria y los nombres de funciones admitidas por cada motor.

Este traductor se usa también al enviar expresiones desde Resultados a señales y herramientas numéricas. No añade funciones especiales que los motores no admiten ni afirma que cualquier integral tenga solución cerrada.

## Independencia y fórmulas de sistemas

Copiar una entrada cargada produce una copia de sus valores y metadatos; no comparte el objeto mutable con la otra vista. Se conservan la referencia al resultado original y las condiciones disponibles. Una fórmula copiada desde una variante aún no calculada no inventa un identificador de resultado como padre.

Al copiar un sistema entre vistas, la realización preservada se copia independientemente y se mantiene el modo Fórmula H cuando era el elegido. Antes, recordar el sistema podía volver a Coeficientes y ocultar la fórmula que el usuario estaba utilizando. Se conserva el período físico y se evita volver a redondear el sistema almacenado.

## Evidencia puntual

Se comprobó un cambio real de Numérico a Algebraico desde el selector de DTFT, acuerdo de una suma finita con evaluación directa, copia a DFT, traducción de tramos anidados, máscaras de tiempo/frecuencia continuas, separación directa/inversa, independencia de una entrada cargada y conservación de fórmula/caché/reloj entre análisis y respuesta temporal. No se ejecutó una batería general ni una campaña de portabilidad.

Sigue siendo una versión de desarrollo hacia la primera estable. La mejora organiza y conecta funciones existentes; no declara finalizada la revisión general de la aplicación.
