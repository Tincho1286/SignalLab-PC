# SignalLab PC 0.70 — informes matemáticos y medidas de registros

## Presentación de resultados

El visor común muestra un resumen científico en lugar de usar los metadatos internos como informe principal. Se presentan dominio, cantidad de valores, intervalo, unidades y convenciones pertinentes. DFT/IDFT, convolución y correlación explican sus ejes, soporte y normalización. Las señales con términos Dirac distinguen pesos de alturas de muestras. Los metadatos adicionales siguen disponibles en Datos del cálculo cuando existen, y los valores completos permanecen en la tabla y la exportación.

Las medidas de registro muestran energía, potencia media y RMS con fórmulas de suma/integral y fracciones. La copia de texto usa notación legible y la exportación HTML incrusta las imágenes matemáticas. Las transferencias y ciertos cálculos algebraicos conservados en Resultados reciben una lectura matemática con sus condiciones. Los cálculos no evaluados se identifican expresamente. Se conserva la precisión de los datos; el informe presenta hasta 12 cifras significativas, salvo índices enteros, que se escriben completos.

La expresión asociada a una señal se presenta como expresión de origen: operaciones posteriores pueden haber cambiado los valores sin cambiar ese dato de procedencia. El resumen no la identifica como fórmula de una salida transformada.

Las acciones de exportación quedan disponibles también para resultados escalares. Se retiran las vistas de gráfico y valores cuando no corresponden, y no se muestran pestañas de metadatos vacías.

## Medidas continuas dentro de la misma herramienta

Registro finito ahora permite elegir secuencia discreta o registro continuo, sin agregar una herramienta pública. En discreto, E=Σ|x[n]|² y P=E/N. En continuo, se interpola x(t) linealmente entre puntos. Para cada intervalo se integra exactamente el modelo: Δt·(|x₀|²+Re(x₀·conj(x₁))+|x₁|²)/3. P divide por la duración del registro y RMS=√P. La integral no equivale a un trapecio de |x|². Es exacta para el modelo interpolado y una aproximación de una función original que no fuese lineal entre los puntos.

Los datos conservados incluyen dominio, intervalo, duración de cálculo y unidad del eje. Los ejes descendentes se interpretan sobre el mismo intervalo físico, sin energía negativa. Se rechazan registros sin duración, Dirac ideales y magnitudes fuera del rango representable. El informe distingue la potencia del registro de la potencia límite: una extensión periódica y una extensión nula fuera del registro tienen interpretaciones distintas.

## Estado y entrada de datos

Las operaciones básicas y el análisis general muestran si el resultado corresponde a los datos actuales. Al editar, el botón pasa a Recalcular y el resultado anterior se conserva con aviso. Si los datos cambian mientras se calcula, la llegada del resultado previo no lo marca como vigente. Se acortó el mensaje común y se conserva la explicación de exportación/reutilización en la ayuda emergente.

Se corrigió el regreso desde Biblioteca/Resultados, que podía mantener ocultos los selectores de variante. La escala de amplitud admite constantes como pi y 10^(-3). Tras incorporar k para expresiones de coeficientes, los campos escalares vuelven a rechazarlo como variable, en vez de evaluarlo accidentalmente en cero. Los campos reales también admiten π.

El modelo rechaza ejes continuos/frecuenciales cuyo extremo desborda o cuyo paso no distingue coordenadas en doble precisión. Los índices discretos conservan su rango entero de 64 bits.

## Comprobaciones dirigidas

- Registro complejo [1+j,-2j,3]: E=15, P=5, RMS=√5; fórmula renderizada y exportación de valores originales.
- Actualización, edición y llegada de un resultado después de editar: se conserva el aviso correcto.
- Consulta del cálculo guardado, DFT con normalización indicada, diseño FIR con tres ejes y escala por pi.
- Ejes no representables rechazados, índices de orden 10^18 escritos completos y k rechazado en constantes.
- Registros continuos: rampa [0,1] en [0,1], E=1/3; constante 2 durante una unidad, E=P=4; segmento complejo [1+j,-1+j], E=4/3; eje descendente, mismo resultado físico.
- Rechazo de Dirac y registro continuo de un punto; duración y unidad conservadas; envío de un registro continuo a Medidas y regreso desde la ayuda.
- Revisión visual del informe y del ancho de documento a 800×600 en los casos revisados.

Continúa el cierre dirigido hacia 1.0. Esta evidencia cubre estos recorridos y no certifica todas las expresiones simbólicas ni todas las combinaciones de parámetros.
