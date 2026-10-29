# SignalLab PC 0.99.10 · Fourier y búsqueda por variante

## Elegir el problema antes que el método

La herramienta Transformada de Fourier organiza sus opciones en Transformada, Dirección y Cálculo. La primera elección ofrece DTFT, DFT / FFT y Fourier continua. Directa e Inversa se presentan con los mismos nombres en los tres modelos. En DFT directa, el tercer campo se llama Estudio y permite Transformada o Ventanas y resolución. No se agregan rutas ni se duplica la herramienta en el explorador.

Esto corrige el salto de inversa a directa al cambiar entre discreta y continua: antes se comparaban etiquetas como DTFT inversa e Inversa como si fueran opciones diferentes. Ahora DTFT inversa algebraica pasa a Fourier continua inversa algebraica; al elegir DFT / FFT conserva Inversa, con el único cálculo numérico disponible para ese caso.

El selector común conserva primero las opciones posteriores más importantes, según su orden. Si quedan varias variantes equivalentes, recuerda el último modo visitado dentro de esa rama. Volver a DFT directa puede recuperar Ventanas y resolución. Cada vista conserva su borrador; si ya existía, la copia de una entrada compatible sigue siendo voluntaria. No se convierte una entrada temporal en coeficientes por cambiar de dirección.

## Buscar la variante correcta

La búsqueda compara los términos con una combinación válida de opciones y sus etiquetas, en lugar de reunir palabras de todos los casos de una familia. Por ejemplo, Diseñar filtro no aparece como una respuesta para FIR analógico; sí ofrece IIR analógico. El nombre exacto y el modelo pedido tienen prioridad: DFT abre la DFT del registro y FFT ventanas abre el estudio de ventanas. No se añade un resultado por cada variante al menú principal.

Cuando la consulta es general y varias variantes válidas coinciden, se conserva la selección recordada si es compatible. El tooltip de la pestaña del documento incluye el modelo, dirección y cálculo actuales, manteniendo el título corto del problema.

## Ayuda y datos

La ayuda existente de cada variante de Fourier incorpora un dibujo comparativo: DFT para N coeficientes de un registro, DTFT para una curva periódica en rad/muestra y Fourier continua con frecuencia en rad/s. Las flechas muestran Directa e Inversa. Explica que FFT es un algoritmo para calcular la DFT y que agregar ceros no mejora por sí solo la resolución física.

Se mantienen las ilustraciones específicas que ya tenía cada página. Los campos de ayuda describen qué transformada elegir y qué datos recibe la inversa. Cambiar hacia o desde IDFT explica la diferencia entre sus N coeficientes X[k] y un espectro X(ω), manteniendo independientes las entradas.

## Evidencia y alcance

Comprobaciones dirigidas de dirección preservada, recuerdo del estudio, borrador conservado, búsqueda DFT/IDFT/FFT/DTFT e incompatibilidad FIR analógico. Se recorrieron los controles reales, la apertura desde búsqueda, los tooltips y una ventana de 800 px. Se revisó la ilustración comparativa. No se ejecutó una batería general ni se repitieron cálculos de motores que no cambiaron.

El catálogo permanece en 31 problemas y 80 variantes, más la hoja CAS. Se conservan el estilo oscuro actual, la carga común y las mejoras matemáticas previas. Esta entrega mejora la organización y continúa hacia 1.0; no prueba por sí sola que todas las herramientas estén cerradas y verificadas.
